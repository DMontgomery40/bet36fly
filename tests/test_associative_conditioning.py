"""Frozen conditioning plan and fail-closed evaluators (synthetic responses, no engine)."""
import json

import numpy as np
import pytest

from bet36fly import associative_conditioning as ac

TIMING = json.load(open('configs/associative-circuit-01.json'))['timing']


def test_plan_is_fixed_bounded_and_controls_are_matched():
    plan = ac.build_plan(TIMING)
    summary = ac.validate_plan(plan)
    assert summary['calls'] == 389 and summary['calls'] <= ac.conditioning_spec()['call_cap']
    assert summary['by_stage'] == {'entry': 6, 'train': 204, 'endpoint': 48, 'retention': 11, 'reversal': 120}
    train = [r for r in plan if r['stage'] == 'train']
    by_arm = {arm: [r for r in train if r['owner'] == arm] for arm in ac.ARMS}
    # Identical sensory noise: cue trials share seeds across arms.
    seeds = {arm: [r['seed'] for r in rows if r['cue']] for arm, rows in by_arm.items()}
    assert all(s == seeds['paired'] for s in seeds.values())
    reinforced = {arm: sum(r['schedule']['us'] is not None for r in rows) for arm, rows in by_arm.items()}
    assert reinforced == dict(paired=12, unpaired=12, backward=12, untaught=0, frozen=12, lesion=12, swap=12, order=12)
    assert all(r['schedule']['cue'] is None for r in by_arm['unpaired'] if r['schedule']['us'])
    assert all(r['schedule']['us'] == tuple(TIMING['backward_us_bins']) for r in by_arm['backward'] if r['schedule']['us'])
    assert all(not r['plasticity'] for r in by_arm['frozen'])
    assert all(not r['coupling'] for r in by_arm['lesion']) and all(r['coupling'] for r in by_arm['paired'])
    assert [r['cue'] for r in by_arm['order'][:4]] == ['B', 'A', 'A', 'B']
    assert all(r['cue'] == 'B' for r in by_arm['swap'] if r['schedule']['us'])
    assert all(not r['plasticity'] for r in plan if r['kind'] == 'probe')
    assert all(r.get('parent') == 'paired' for r in plan if r['stage'] == 'reversal' and r['kind'] == 'train')


def test_plan_validation_rejects_learning_probes_and_reinforced_untaught():
    plan = ac.build_plan(TIMING)
    broken = [dict(r) for r in plan]
    broken[0]['plasticity'] = True
    with pytest.raises(ValueError):
        ac.validate_plan(broken)
    broken = [dict(r, schedule=dict(r['schedule'], us=(25, 45))) if r['owner'] == 'untaught' else r for r in plan]
    with pytest.raises(ValueError):
        ac.validate_plan(broken)


def synthetic(paired=-20., swap=-20., order=-20., null=0.5, backward=2., unit=40., n_edges=10):
    unit_resp = np.full((3, 2, 2), unit)
    kc = np.zeros((3, 2, 4), np.int64)
    kc[:, 0, :2] = 5
    kc[:, 1, 2:] = 5
    partition = ac.partition_edges(kc, np.array([0, 1, 2, 3, 0, 1, 2, 3, 0, 1]), np.array([0] * 4 + [1] * 4 + [0, 0]),
                                   np.ones(n_edges, np.uint8))
    unit_gains = np.ones(n_edges, np.float32)

    def endpoint(a_delta, b_delta=0.0, a_gain=0.0, b_gain=0.0, gains=None):
        responses = unit_resp.copy()
        responses[:, 0, 0] += a_delta
        responses[:, 1, 0] += b_delta
        g = unit_gains.copy()
        for k in partition['edges']['0']['A']:
            g[k] += a_gain
        for k in partition['edges']['0']['B']:
            g[k] += b_gain
        return dict(responses=responses.tolist(), gains=g if gains is None else gains)

    endpoints = dict(paired=endpoint(paired, a_gain=-0.2), unpaired=endpoint(null, a_gain=-0.005),
                     backward=endpoint(backward, a_gain=0.01), untaught=endpoint(null), frozen=endpoint(0.0),
                     lesion=endpoint(0.0), swap=endpoint(0.0, swap, b_gain=-0.2), order=endpoint(order, a_gain=-0.2))
    return unit_resp.tolist(), endpoints, partition, unit_gains, endpoint


def test_acquisition_passes_only_with_selective_dopamine_dependent_depression():
    unit, endpoints, partition, unit_gains, endpoint = synthetic()
    verdict = ac.evaluate_acquisition(unit, endpoints, partition, unit_gains)
    assert verdict['all_passed'], verdict
    # Lesion that still changes gains fails causal dependence.
    endpoints['lesion'] = endpoint(-20., a_gain=-0.2)
    assert not ac.evaluate_acquisition(unit, endpoints, partition, unit_gains)['criteria']['frozen_and_lesion_bytes_identical']
    # A paired effect that is not 3x the null fails.
    unit, endpoints, partition, unit_gains, endpoint = synthetic(paired=-1.2, null=0.5)
    assert not ac.evaluate_acquisition(unit, endpoints, partition, unit_gains)['criteria']['acquisition_response']
    # Backward pairing that depresses as much as forward fails the timing criterion.
    unit, endpoints, partition, unit_gains, endpoint = synthetic(backward=-20.)
    assert not ac.evaluate_acquisition(unit, endpoints, partition, unit_gains)['criteria']['backward_not_depressing']
    # Loss of responsiveness fails.
    unit, endpoints, partition, unit_gains, endpoint = synthetic(paired=-40.)
    assert not ac.evaluate_acquisition(unit, endpoints, partition, unit_gains)['criteria']['no_loss_of_responsiveness']
    # Missing arm is an error, never a pass.
    del endpoints['swap']
    result = ac.evaluate_acquisition(unit, endpoints, partition, unit_gains)
    assert not result['all_passed'] and result['errors']


def test_retention_and_reversal_evaluators():
    unit, endpoints, partition, unit_gains, endpoint = synthetic()
    parent = endpoints['paired']
    assert ac.evaluate_retention(parent, dict(responses=parent['responses'], gains=parent['gains']))['passed']
    assert not ac.evaluate_retention(parent, dict(responses=parent['responses'], gains=unit_gains))['passed']
    parent_gains = np.asarray(parent['gains'], np.float32)

    def branch(a, b, a_gain, b_gain, gains=None):
        responses = np.asarray(parent['responses'], float).copy()
        responses[:, 0, 0] += a
        responses[:, 1, 0] += b
        g = parent_gains.copy()
        for k in partition['edges']['0']['A']:
            g[k] += a_gain
        for k in partition['edges']['0']['B']:
            g[k] += b_gain
        return dict(responses=responses.tolist(), gains=g if gains is None else gains)

    branches = {'contingency-swap': branch(0, -20, 0, -0.2), 'backward-erasure-plus-swap': branch(18, -20, 0.15, -0.2),
                'untaught-exposure': branch(0.5, 0.5, 0, 0), 'frozen-retention': branch(0, 0, 0, 0, gains=parent_gains)}
    verdict = ac.evaluate_reversal(unit, parent, branches, partition)
    assert verdict['all_passed'], verdict
    assert verdict['contingency_swap_descriptive']['b_depressed']
    branches['backward-erasure-plus-swap'] = branch(1.0, -20, 0.15, -0.2)
    assert not ac.evaluate_reversal(unit, parent, branches, partition)['criteria']['erasure_recovers_a']
    branches['frozen-retention'] = branch(0, 0, 0.01, 0)
    assert not ac.evaluate_reversal(unit, parent, branches, partition)['criteria']['frozen_retention_bytes_identical']


def test_partition_requires_seed_cue_kc_layout():
    with pytest.raises(ValueError):
        ac.partition_edges(np.zeros((3, 4)), [0], [0], [1])


def test_version_two_evaluation_options_are_validated_and_applied():
    spec = ac.conditioning_spec(dict(readout='sum', backward_rule='directional',
                                     null_arms=['unpaired', 'untaught', 'frozen', 'lesion'],
                                     probe_seeds=[3011, 3012, 3013], training_seed_base=20000))
    assert spec['readout'] == 'sum' and 'backward' not in spec['null_arms']
    plan = ac.build_plan(TIMING, spec)
    assert plan[0]['seed'] == 3011 and [r for r in plan if r['kind'] == 'train'][0]['seed'] == 20000
    with pytest.raises(ValueError):
        ac.conditioning_spec(dict(readout='sum', backward_rule='directional'))  # backward still in null set
    with pytest.raises(ValueError):
        ac.conditioning_spec(dict(readout='mean'))
    unit, endpoints, partition, unit_gains, endpoint = synthetic()
    # Under version 2 the backward arm's opposite-sign potentiation no longer sets the null scale.
    endpoints['backward'] = endpoint(20., a_gain=0.2)
    v1 = ac.evaluate_acquisition(unit, endpoints, partition, unit_gains)
    v2 = ac.evaluate_acquisition(unit, endpoints, partition, unit_gains, spec=spec)
    assert not v1['criteria']['acquisition_gain'] and v2['criteria']['acquisition_gain']
    assert v2['criteria']['backward_potentiates_gains'] and v2['readout'] == 'sum'
    endpoints['backward'] = endpoint(-1., a_gain=-0.01)
    assert not ac.evaluate_acquisition(unit, endpoints, partition, unit_gains, spec=spec)['criteria']['backward_potentiates_gains']


def test_stress_reinforcement_plan_retires_a_cue_without_changing_the_others():
    import importlib.util
    spec = importlib.util.spec_from_file_location('stress', 'scripts/run_associative_stress.py')
    stress = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stress)
    keys = ['a', 'b', 'c']
    full = stress.reinforcement_plan(keys, 4)
    assert full == [(c, k) for c in range(4) for k in keys]
    retired = stress.reinforcement_plan(keys, 4, 'a', 2)
    assert [k for c, k in retired if c < 2] == ['a', 'b', 'c', 'a', 'b', 'c']
    assert [k for c, k in retired if c >= 2] == ['b', 'c', 'b', 'c']
    assert stress.last_in_cycle(keys, 'a', 2, 1) == 'c' and stress.last_in_cycle(['b', 'a'], 'a', 2, 3) == 'b'
    with pytest.raises(ValueError):
        stress.reinforcement_plan(keys, 4, 'zz', 2)
    with pytest.raises(ValueError):
        stress.reinforcement_plan(keys, 4, 'a', None)
