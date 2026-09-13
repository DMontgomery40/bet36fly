import numpy as np
import pandas as pd
import pytest

from bet36fly.sensory import reconcile_cells, SensoryEngine


def source_tables():
    ids = [2**53 + i for i in (1, 3, 5, 7, 9)]
    types = ['LB3b', 'LB3c', 'LB3a', 'LB1a', 'MN9']
    nodes = pd.DataFrame(dict(bodyId=ids, type=types, **{'class': ['gustatory']*4+[None]}))
    grns = [dict(Connectome='maleCNS', Body_ID=str(i), Subtype=t, Type=t[:3])
            for i, t in zip(ids[:4], types[:4])]
    mns = [dict(Connectome='maleCNS', Body_ID=str(ids[4]), Type='MN9')]
    return nodes, grns, mns


def test_source_identity_is_exact_and_cross_specimen_ids_are_not_imported():
    nodes, grns, mns = source_tables()
    grns.append(dict(Connectome='FAFB – Flywire', Body_ID='720575940000001', Subtype='LB3b'))
    result = reconcile_cells(grns, mns, nodes.sample(frac=1, random_state=3))
    assert result['populations']['sweet'] == [2**53+1, 2**53+3]
    assert result['populations']['water'] == [2**53+5]
    assert result['populations']['bitter'] == [2**53+7]
    assert result['populations']['MN9'] == [2**53+9]


@pytest.mark.parametrize('case', ['duplicate', 'float_id', 'missing', 'mismatch', 'wrong_class', 'empty'])
def test_source_reconciliation_fails_closed(case):
    nodes, grns, mns = source_tables()
    if case == 'duplicate':
        grns.append(grns[0].copy())
    if case == 'float_id':
        grns[0]['Body_ID'] = '9007199254740993.0'
    if case == 'missing':
        nodes = nodes.iloc[1:]
    if case == 'mismatch':
        nodes.loc[0, 'type'] = 'LB3d'
    if case == 'wrong_class':
        nodes.loc[0, 'class'] = 'olfactory'
    if case == 'empty':
        grns = []
    with pytest.raises(ValueError):
        reconcile_cells(grns, mns, nodes)


def engine(weights=(40., -40.)):
    return SensoryEngine(np.array([0, 1, 2, 2], np.int64), np.array([2, 2], np.int32),
                         np.array(weights, np.float32), np.array([0, 1], np.int32))


def test_null_reset_reproducibility_and_delivered_input_units():
    e = engine()
    rates = np.tile([100., 0.], (10, 1))
    a = e.run(rates, bin_ms=100., sample=[0, 1, 2], seed=17)
    b = e.run(rates, bin_ms=100., sample=[0, 1, 2], seed=17)
    assert np.array_equal(a['counts'], b['counts'])
    assert np.array_equal(a['input_events'], b['input_events'])
    assert np.array_equal(a['trace'][:, :2], a['input_events'])
    assert 60 <= a['input_events'][:, 0].sum() <= 140  # 100 Hz for one second, not 100 per step.
    assert a['counts'][2] > 0
    assert not e.run(np.zeros_like(rates), bin_ms=100., sample=[0, 1, 2], seed=17)['counts'].any()


def test_saturation_is_explicit_and_negative_input_is_not_clipped():
    e = engine()
    r = e.run([[5000., 0.]], bin_ms=20., sample=[0, 1], seed=43)
    assert r['input_events'][0, 0] == r['counts'][0] == 100
    for rate in [-1., np.nan, np.inf, 5000.1]:
        with pytest.raises(ValueError):
            e.run([[rate, 0.]], bin_ms=20., sample=[0, 1], seed=43)


def test_inhibition_and_direction_affect_downstream_spikes():
    e = engine()
    exc = e.run(np.tile([200., 0.], (5, 1)), bin_ms=100., sample=[2], seed=43)
    inh = e.run(np.tile([200., 200.], (5, 1)), bin_ms=100., sample=[2], seed=43)
    assert inh['counts'][2] < exc['counts'][2]
    assert e.run(np.tile([0., 200.], (5, 1)), bin_ms=100., sample=[2], seed=43)['counts'][2] == 0


def test_matches_existing_frozen_engine_on_recurrence_and_refractory_cases():
    from bet36fly.reward_brain import RewardEngine
    ptr = np.array([0, 1, 3, 4], np.int64)
    post = np.array([1, 0, 2, 1], np.int32)
    weights = np.array([60., -25., 60., -35.], np.float32)
    sensory = np.array([0], np.int32)
    empty = np.array([], np.int32)
    old = RewardEngine(ptr, post, weights, sensory, empty, empty, empty,
        np.array([], np.int64), empty, empty, n_compartments=1)
    new = SensoryEngine(ptr, post, weights, sensory)
    for rate in (0., 40., 300., 5000.):
        schedule = np.full((4, 1), rate, np.float32)
        a = old.run(schedule, bin_ms=20., sample=[0, 1, 2], seed=101, plasticity=False)
        b = new.run(schedule, bin_ms=20., sample=[0, 1, 2], seed=101)
        assert np.array_equal(a['counts'], b['counts'])
        assert np.array_equal(a['trace'], b['trace'])
        np.testing.assert_allclose(a['voltage'], b['voltage'], atol=1e-5)


@pytest.mark.parametrize('kw', [dict(dt=.3), dict(bin_ms=.3), dict(sample=[3]),
    dict(sample=[1, 1]), dict(sample=[.5]), dict(seed=True), dict(seed=-1)])
def test_invalid_native_requests_are_rejected(kw):
    args = dict(bin_ms=20., sample=[0], seed=17)
    args.update(kw)
    with pytest.raises(ValueError):
        engine().run([[10., 0.]], **args)


def test_half_timestep_preserves_generator_hz_and_null_state():
    e = engine()
    for dt in (.1, .2):
        result = e.run(np.tile([100., 0.], (10, 1)), bin_ms=100., dt=dt, sample=[0, 2], seed=43)
        assert 60 <= result['input_events'][:, 0].sum() <= 140
        assert result['duration_ms'] == 1000
        assert not e.run([[0., 0.]], bin_ms=100., dt=dt, sample=[0, 2], seed=43)['counts'].any()


def test_response_gates_require_all_conditions_and_all_seed_response():
    from scripts.run_sensory_assay import response_gates
    rates = dict(null=0, water=4, sweet=10, bitter=0, mixed=5)
    rows = [dict(condition=k, MN9_stimulus_hz_mean=v) for k, v in rates.items() for _ in range(3)]
    assert response_gates(rows)['passed']
    assert not response_gates(rows[:-1])['passed']
    rows[6]['MN9_stimulus_hz_mean'] = 0
    assert not response_gates(rows)['gates']['sweet_activates']


def test_assay_identity_refuses_rerun_before_loading_or_running(tmp_path):
    import hashlib
    from scripts.run_sensory_assay import run, check_locked_files
    config = tmp_path / 'protocol.json'
    config.write_text('{}')
    directory = tmp_path / 'output/sensory' / ('sensory-'+hashlib.sha256(b'{}').hexdigest()[:20])
    directory.mkdir(parents=True)
    marker = directory / 'prior.txt'
    marker.write_text('protected')
    with pytest.raises(ValueError, match='Refusing'):
        run(config, root=tmp_path)
    assert marker.read_text() == 'protected'
    with pytest.raises(ValueError, match='differs'):
        check_locked_files({'file_sha256': {'protocol.json': 'wrong'}}, tmp_path)
