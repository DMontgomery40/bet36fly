"""Frozen plan and fail-closed evaluators for associative cue learning (Stage 3).

Pure functions: no engine import. The runner (scripts/run_associative_conditioning.py)
executes the plan on the actual circuit and passes measured probes back here.
"""
from __future__ import annotations

from fractions import Fraction
import json

import numpy as np

ARMS = ('paired', 'unpaired', 'backward', 'untaught', 'frozen', 'lesion', 'swap', 'order')
NULL_ARMS = ('unpaired', 'backward', 'untaught', 'frozen', 'lesion')
REVERSAL_BRANCHES = ('contingency-swap', 'backward-erasure-plus-swap', 'untaught-exposure', 'frozen-retention')
CUES = ('A', 'B')
EFFECT_RATIO = 3


def conditioning_spec(protocol=None):
    """Version 1 (conditioning-01) defaults; a protocol may declare the version-2 evaluation fields."""
    spec = dict(schema='associative-conditioning-1', cues=CUES, arms=ARMS, null_arms=NULL_ARMS,
                reversal_branches=REVERSAL_BRANCHES, exposures_per_cue=12, order=('A', 'B', 'B', 'A'),
                probe_seeds=[3001, 3002, 3003], training_seed_base=10_000, retention_blank_trials=5,
                effect_ratio=EFFECT_RATIO, call_cap=420, wall_cap_seconds=1800,
                readout='compartment0', backward_rule='null')
    if protocol:
        for key in ('probe_seeds', 'training_seed_base', 'readout', 'backward_rule', 'null_arms', 'effect_ratio'):
            if key in protocol:
                spec[key] = protocol[key]
        spec['null_arms'] = tuple(spec['null_arms'])
        if spec['readout'] not in ('compartment0', 'sum') or spec['backward_rule'] not in ('null', 'directional'):
            raise ValueError('Unknown readout or backward rule.')
        if spec['backward_rule'] == 'directional' and 'backward' in spec['null_arms']:
            raise ValueError('A directional backward control cannot also be a null arm.')
        if spec['backward_rule'] == 'null' and 'backward' not in spec['null_arms']:
            raise ValueError('Version-1 evaluation keeps backward in the null set.')
    return spec


def _trial(timing, *, cue, forward, backward, us_alone, blank=False):
    """Schedule description in bins for one trial."""
    if blank:
        return dict(bins=timing['reinforcement_bins'], cue=None, us=None)
    if us_alone:
        return dict(bins=timing['reinforcement_bins'], cue=None, us=tuple(timing['us_bins']))
    if backward:
        return dict(bins=timing['reinforcement_bins'], cue=tuple(timing['backward_cue_bins']),
                    us=tuple(timing['backward_us_bins']))
    if forward:
        return dict(bins=timing['reinforcement_bins'], cue=tuple(timing['cue_bins']), us=tuple(timing['us_bins']))
    return dict(bins=timing['reinforcement_bins'], cue=tuple(timing['cue_bins']), us=None)


def _probe(timing):
    return dict(bins=timing['probe_bins'], cue=tuple(timing['cue_bins']), us=None)


def build_plan(timing, spec=None):
    """Ordered list of calls. Each call names its stage, arm/branch, cue, seed, schedule and plasticity."""
    spec = conditioning_spec() if spec is None else spec
    rows = []
    seeds = spec['probe_seeds']
    base = spec['training_seed_base']

    def probes(stage, owner, checkpoint):
        for seed in seeds:
            for cue in CUES:
                rows.append(dict(id=f'{stage}-{owner}-probe-{cue}-{seed}', stage=stage, owner=owner, kind='probe',
                                 cue=cue, seed=seed, schedule=_probe(timing), plasticity=False, coupling=True,
                                 checkpoint=checkpoint))

    probes('entry', 'unit', 'unit')
    exposures = spec['exposures_per_cue'] * 2
    for arm in ARMS:
        order = spec['order'] if arm != 'order' else tuple('B' if c == 'A' else 'A' for c in spec['order'])
        position = 0
        for exposure in range(exposures):
            cue = order[exposure % 4]
            seed = base + exposure
            taught = cue == ('B' if arm == 'swap' else 'A')
            forward = taught and arm in ('paired', 'frozen', 'lesion', 'swap', 'order')
            backward = taught and arm == 'backward'
            rows.append(dict(id=f'train-{arm}-{exposure:02d}-{cue}', stage='train', owner=arm, kind='train', cue=cue,
                             seed=seed, schedule=_trial(timing, cue=cue, forward=forward, backward=backward,
                                                        us_alone=False),
                             plasticity=arm != 'frozen', coupling=arm != 'lesion', checkpoint=arm, exposure=exposure))
            position += 1
            if arm == 'unpaired' and taught:
                rows.append(dict(id=f'train-{arm}-{exposure:02d}-US', stage='train', owner=arm, kind='train', cue=None,
                                 seed=base + 500 + exposure, schedule=_trial(timing, cue=None, forward=False,
                                                                            backward=False, us_alone=True),
                                 plasticity=True, coupling=True, checkpoint=arm, exposure=exposure))
        probes('endpoint', arm, arm)
    for k in range(spec['retention_blank_trials']):
        rows.append(dict(id=f'retention-blank-{k}', stage='retention', owner='paired', kind='blank', cue=None,
                         seed=base + 900 + k, schedule=_trial(timing, cue=None, forward=False, backward=False,
                                                              us_alone=False, blank=True),
                         plasticity=True, coupling=True, checkpoint='paired'))
    probes('retention', 'paired', 'paired')
    for branch in REVERSAL_BRANCHES:
        for exposure in range(exposures):
            cue = spec['order'][exposure % 4]
            seed = base + 1000 + exposure
            forward = (cue == 'B') and branch in ('contingency-swap', 'backward-erasure-plus-swap', 'frozen-retention')
            backward = (cue == 'A') and branch == 'backward-erasure-plus-swap'
            rows.append(dict(id=f'reversal-{branch}-{exposure:02d}-{cue}', stage='reversal', owner=branch, kind='train',
                             cue=cue, seed=seed, schedule=_trial(timing, cue=cue, forward=forward, backward=backward,
                                                                 us_alone=False),
                             plasticity=branch != 'frozen-retention', coupling=True, checkpoint=f'reversal-{branch}',
                             exposure=exposure, parent='paired'))
        probes('reversal', branch, f'reversal-{branch}')
    return rows


def validate_plan(rows, spec=None):
    spec = conditioning_spec() if spec is None else spec
    if len(rows) > spec['call_cap']:
        raise ValueError('Plan exceeds the declared call cap.')
    ids = [r['id'] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate call identities.')
    probes = [r for r in rows if r['kind'] == 'probe']
    if any(r['plasticity'] for r in probes):
        raise ValueError('Probes must never learn.')
    reinforced = {r['owner'] for r in rows if r['kind'] == 'train' and r['schedule']['us'] is not None}
    if 'untaught' in reinforced or 'untaught-exposure' in reinforced:
        raise ValueError('Untaught arms must not receive the reinforcer.')
    return dict(calls=len(rows), probes=len(probes), by_stage={s: sum(r['stage'] == s for r in rows)
                                                                for s in ('entry', 'train', 'endpoint', 'retention', 'reversal')})


def partition_edges(unit_kc_counts, plastic_kc, plastic_compartments, plastic_mask):
    """A-preferring / B-preferring eligible edges per compartment from unit-gain KC counts [seed][cue][kc]."""
    counts = np.asarray(unit_kc_counts)
    if counts.ndim != 3 or counts.shape[1] != 2:
        raise ValueError('Unit KC counts must be [seed][cue][kc].')
    preference = np.sign(counts[:, 0].mean(0) - counts[:, 1].mean(0)).astype(np.int8)
    pk, pc, mask = (np.asarray(x) for x in (plastic_kc, plastic_compartments, plastic_mask))
    result = {}
    for c in sorted(set(pc.tolist())):
        eligible = mask.astype(bool) & (pc == c)
        result[str(c)] = dict(A=np.flatnonzero(eligible & (preference[pk] > 0)).tolist(),
                              B=np.flatnonzero(eligible & (preference[pk] < 0)).tolist(),
                              tied=np.flatnonzero(eligible & (preference[pk] == 0)).tolist())
    active = counts > 0
    jaccard = [float(np.count_nonzero(active[s, 0] & active[t, 1]) / max(1, np.count_nonzero(active[s, 0] | active[t, 1])))
               for s in range(len(counts)) for t in range(len(counts))]
    return dict(preference=preference.tolist(), edges=result, between_jaccard_mean=float(np.mean(jaccard)),
                between_jaccard_max=float(max(jaccard)))


def _mean(values, indices):
    if not len(indices):
        raise ValueError('Empty preferred edge set.')
    return sum((Fraction(float(v)) for v in np.asarray(values)[list(indices)]), Fraction(0)) / len(indices)


def _readout(values, readout):
    """Response scalar per [seed][cue]: compartment 0 alone (version 1) or the summed learned MBONs."""
    values = np.asarray(values, float)
    return values[:, :, 0] if readout == 'compartment0' else values.sum(axis=2)


def _contrast(responses, unit, readout='compartment0'):
    """[seed] contrast ΔA − ΔB of the readout relative to unit probes."""
    delta = _readout(responses, readout) - _readout(unit, readout)
    return delta[:, 0] - delta[:, 1]


def evaluate_acquisition(unit, endpoints, partition, unit_gains, effect_ratio=EFFECT_RATIO, spec=None):
    """unit: responses [seed][cue][compartment]; endpoints: arm -> dict(responses, gains)."""
    spec = conditioning_spec() if spec is None else spec
    readout, null_arms = spec['readout'], tuple(spec['null_arms'])
    verdict = dict(all_passed=False, errors=[], arms={}, criteria={}, readout=readout, null_arms=list(null_arms),
                   backward_rule=spec['backward_rule'])
    try:
        if set(endpoints) != set(ARMS):
            raise ValueError('Endpoint arm matrix is incomplete.')
        unit_gains = np.asarray(unit_gains, np.float32)
        edges_a = partition['edges']['0']['A']
        edges_b = partition['edges']['0']['B']
        contrasts, gain_moves, target_changes = {}, {}, {}
        for arm, value in endpoints.items():
            gains = np.asarray(value['gains'], np.float32)
            if gains.shape != unit_gains.shape:
                raise ValueError('Gain vector shape differs.')
            contrasts[arm] = _contrast(value['responses'], unit, readout)
            delta_gain = gains.astype(np.float64) - unit_gains
            gain_moves[arm] = float(_mean(delta_gain, edges_a) - _mean(delta_gain, edges_b))
            target_changes[arm] = (_readout(value['responses'], readout) - _readout(unit, readout))[:, 0]
            verdict['arms'][arm] = dict(contrast=contrasts[arm].tolist(), mean_contrast=float(contrasts[arm].mean()),
                                        gain_selectivity=gain_moves[arm],
                                        a_edge_mean_gain_change=float(_mean(delta_gain, edges_a)),
                                        b_edge_mean_gain_change=float(_mean(delta_gain, edges_b)),
                                        changed_edges=int((gains != unit_gains).sum()),
                                        max_abs_gain_change=float(np.abs(delta_gain).max()),
                                        bytes_identical_to_unit=gains.tobytes() == unit_gains.tobytes(),
                                        min_mbon05_after=float(np.asarray(value['responses'], float)[:, :, 0].min()))
        null_response = max(abs(contrasts[a].mean()) for a in null_arms)
        null_gain = max(abs(gain_moves[a]) for a in null_arms)
        paired = contrasts['paired']
        c = verdict['criteria']
        c['acquisition_response'] = bool(np.all(paired < 0) and abs(paired.mean()) >= effect_ratio * null_response)
        c['acquisition_gain'] = bool(gain_moves['paired'] < 0 and abs(gain_moves['paired']) >= effect_ratio * null_gain)
        c['acquisition_target_depressed'] = bool(np.all(target_changes['paired'] < 0))
        c['frozen_and_lesion_bytes_identical'] = bool(verdict['arms']['frozen']['bytes_identical_to_unit']
                                                      and verdict['arms']['lesion']['bytes_identical_to_unit'])
        c['backward_not_depressing'] = bool(contrasts['backward'].mean() >= 0
                                            or abs(contrasts['backward'].mean()) < abs(paired.mean()) / effect_ratio)
        if spec['backward_rule'] == 'directional':
            # Dopamine before the cue is predicted to potentiate the A edges (opposite sign to paired).
            c['backward_potentiates_gains'] = bool(verdict['arms']['backward']['a_edge_mean_gain_change'] > 0)
        swap = -contrasts['swap']  # mirror: ΔB − ΔA
        c['swap_mirror'] = bool(np.all(swap < 0) and abs(swap.mean()) >= effect_ratio * null_response
                                and gain_moves['swap'] > 0)
        order = contrasts['order']
        c['order_matches_paired'] = bool(np.all(order < 0) and abs(order.mean()) >= effect_ratio * null_response)
        c['no_loss_of_responsiveness'] = all(v['min_mbon05_after'] > 0 for v in verdict['arms'].values())
        c['max_gain_change_bounded'] = all(v['max_abs_gain_change'] < 0.4 for v in verdict['arms'].values())
        verdict.update(null_response_scale=float(null_response), null_gain_scale=float(null_gain),
                       untaught_total_abs_gain_change=float(np.abs(np.asarray(endpoints['untaught']['gains'], np.float32)
                                                                   .astype(np.float64) - unit_gains).sum()))
        verdict['all_passed'] = all(c.values())
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        verdict['errors'].append(str(exc))
    return verdict


def evaluate_retention(endpoint, retention):
    passed = (np.asarray(endpoint['gains'], np.float32).tobytes() == np.asarray(retention['gains'], np.float32).tobytes()
              and np.array_equal(np.asarray(endpoint['responses']), np.asarray(retention['responses'])))
    return dict(passed=bool(passed))


def evaluate_reversal(unit, parent, branches, partition, effect_ratio=EFFECT_RATIO, spec=None):
    spec = conditioning_spec() if spec is None else spec
    readout = spec['readout']
    verdict = dict(all_passed=False, errors=[], branches={}, criteria={}, readout=readout)
    try:
        if set(branches) != set(REVERSAL_BRANCHES):
            raise ValueError('Reversal branch matrix is incomplete.')
        parent_gains = np.asarray(parent['gains'], np.float32)
        parent_pref = _contrast(parent['responses'], unit, readout)
        edges_a = partition['edges']['0']['A']
        edges_b = partition['edges']['0']['B']
        moves = {}
        for name, value in branches.items():
            gains = np.asarray(value['gains'], np.float32)
            responses = np.asarray(value['responses'], float)
            delta = _readout(responses, readout) - _readout(parent['responses'], readout)
            moves[name] = dict(pref=_contrast(responses, unit, readout), a_move=delta[:, 0], b_move=delta[:, 1],
                               a_gain=float(_mean(gains.astype(np.float64) - parent_gains, edges_a)),
                               b_gain=float(_mean(gains.astype(np.float64) - parent_gains, edges_b)),
                               bytes_identical_to_parent=gains.tobytes() == parent_gains.tobytes())
            verdict['branches'][name] = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in moves[name].items()}
        null_a = max(abs(moves['untaught-exposure']['a_move']).max(), abs(moves['frozen-retention']['a_move']).max())
        null_b = max(abs(moves['untaught-exposure']['b_move']).max(), abs(moves['frozen-retention']['b_move']).max())
        erase = moves['backward-erasure-plus-swap']
        c = verdict['criteria']
        c['parent_preference_negative'] = bool(np.all(parent_pref < 0))
        c['erasure_flips_preference'] = bool(np.all(erase['pref'] > 0))
        c['erasure_recovers_a'] = bool(np.all(erase['a_move'] > 0) and erase['a_move'].mean() >= effect_ratio * max(null_a, 1e-9)
                                       and erase['a_gain'] > 0)
        c['erasure_depresses_b'] = bool(np.all(erase['b_move'] < 0) and abs(erase['b_move'].mean()) >= effect_ratio * max(null_b, 1e-9)
                                        and erase['b_gain'] < 0)
        c['frozen_retention_bytes_identical'] = moves['frozen-retention']['bytes_identical_to_parent']
        swap = moves['contingency-swap']
        verdict['contingency_swap_descriptive'] = dict(b_depressed=bool(np.all(swap['b_move'] < 0)),
                                                       a_unchanged=bool(np.all(swap['a_move'] == 0)),
                                                       pref=swap['pref'].tolist())
        verdict['all_passed'] = all(c.values())
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        verdict['errors'].append(str(exc))
    return verdict


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
