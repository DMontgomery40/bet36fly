"""Frozen protocol and fail-closed evaluators for full-CNS conditioning.

This is an engineered test around the MaleCNS circuit. It does not claim that
the artificial cues or teaching schedules are natural fly stimuli.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
from itertools import combinations
from typing import Any

import numpy as np

ACQUISITION_ARMS = ('paired', 'shuffled', 'timing-unpaired', 'untaught', 'frozen')
REVERSAL_BRANCHES = (
    'continued-acquisition', 'ordinary-contingency-swap', 'backward-erasure-plus-swap',
    'untaught-exposure', 'frozen-retention',
)
FAMILIES = {'AB': ('A', 'B'), 'CD': ('C', 'D')}
CHANNELS = ('home', 'away')
FIRST_LATE = (610, 630, 650, 670)
SECOND_LATE = (690, 710, 730, 750)
EARLY = (110, 130, 150, 170)
ACQUISITION_TEACHING = (310, 330, 350, 370)


@dataclass(frozen=True)
class CallSpec:
    id: str
    stage: str
    kind: str
    family: str
    panel: int | None
    arm: str | None
    branch: str | None
    checkpoint: str
    cue: str | None
    seed: int
    duration_ms: int
    cue_window: tuple[int, int] | None
    plasticity: bool
    teaching: tuple[tuple[int, str], ...] = ()
    exposure: int | None = None
    replay_of: str | None = None

    def json(self) -> dict:
        return asdict(self)


def conditioning_spec() -> dict:
    alternating = [-1.5 if i % 2 == 0 else 1.5 for i in range(16)]
    return {
        'schema_version': 1,
        'kind': 'dopamine-conditioning',
        'cues': {
            'A': [-1.5] * 16,
            'B': [1.5] * 16,
            'C': alternating,
            'D': [-x for x in alternating],
        },
        'families': FAMILIES,
        'acquisition_arms': ACQUISITION_ARMS,
        'reversal_branches': REVERSAL_BRANCHES,
        'hard_call_limit': 1640,
        'planned_calls': 1632,
        'hard_wall_seconds': 1200,
        'effect_ratio': 3.0,
        'max_between_jaccard': 0.5,
    }


def _identifier(parts: tuple[Any, ...]) -> str:
    return '-'.join('none' if value is None else str(value).replace('_', '-') for value in parts)


def _with_replay(rows: list[CallSpec], original: CallSpec) -> None:
    rows.append(replace(original, id=original.id + '-replay', replay_of=original.id))


def _acquisition_teaching(arm: str, cue_index: int, exposure: int, *, blank: bool) -> tuple:
    if arm == 'paired' and not blank:
        population = CHANNELS[cue_index]
    elif arm == 'shuffled' and not blank:
        population = ('home', 'home', 'away', 'away')[exposure % 4]
    elif arm == 'timing-unpaired' and blank:
        population = CHANNELS[cue_index]
    else:
        return ()
    return tuple((time_ms, population) for time_ms in ACQUISITION_TEACHING)


def _add_acquisition(rows: list[CallSpec], family: str, stage: str) -> None:
    cues = FAMILIES[family]
    for seed in range(2_000_042, 2_000_046):
        for cue in cues:
            rows.append(CallSpec(
                _identifier((stage, 'unit', cue, seed)), stage, 'unit-probe', family, None, None, None,
                'unit', cue, seed, 400, (0, 300), False,
            ))
    for panel in (0, 1_000_000):
        for arm in ACQUISITION_ARMS:
            for exposure in range(24):
                cue = cues[(0, 1, 1, 0)[exposure % 4]]
                cue_index = 0 if cue == cues[0] else 1
                seed = 42 + panel + 2 * exposure
                cue_row = CallSpec(
                    _identifier((stage, panel, arm, exposure, 'cue')), stage, 'train-cue', family, panel,
                    arm, None, f'after-{exposure}', cue, seed, 400, (0, 300), arm != 'frozen',
                    _acquisition_teaching(arm, cue_index, exposure, blank=False), exposure,
                )
                blank_row = CallSpec(
                    _identifier((stage, panel, arm, exposure, 'blank')), stage, 'train-blank', family,
                    panel, arm, None, f'after-{exposure}', None, seed + 1, 400, None, arm != 'frozen',
                    _acquisition_teaching(arm, cue_index, exposure, blank=True), exposure,
                )
                rows.extend((cue_row, blank_row))
                if arm == 'paired' and exposure == 0:
                    _with_replay(rows, cue_row)
                    _with_replay(rows, blank_row)
                if exposure in (7, 15):
                    checkpoint = 'block-2' if exposure == 7 else 'block-4'
                    for probe_cue in cues:
                        rows.append(CallSpec(
                            _identifier((stage, panel, arm, checkpoint, probe_cue)), stage,
                            'interim-probe', family, panel, arm, None, checkpoint, probe_cue, 2_001_042,
                            400, (0, 300), False,
                        ))
            for seed in range(2_000_042, 2_000_046):
                for cue in cues:
                    probe = CallSpec(
                        _identifier((stage, panel, arm, 'endpoint', cue, seed)), stage, 'endpoint-probe',
                        family, panel, arm, None, 'endpoint', cue, seed, 400, (0, 300), False,
                    )
                    rows.append(probe)
                    if arm == 'paired' and seed == 2_000_042:
                        _with_replay(rows, probe)


def _reversal_teaching(branch: str, cue_index: int) -> tuple:
    old, new = CHANNELS[cue_index], CHANNELS[1 - cue_index]
    if branch == 'continued-acquisition':
        return tuple((t, old) for t in FIRST_LATE + SECOND_LATE)
    if branch == 'ordinary-contingency-swap':
        return tuple((t, new) for t in FIRST_LATE + SECOND_LATE)
    if branch == 'backward-erasure-plus-swap':
        return tuple((t, old) for t in EARLY) + tuple((t, new) for t in FIRST_LATE)
    return ()


def _add_reversal(rows: list[CallSpec]) -> None:
    stage, family, cues = 'reversal', 'AB', FAMILIES['AB']
    for seed in range(5_000_042, 5_000_046):
        for cue in cues:
            probe = CallSpec(
                _identifier((stage, 'unit', cue, seed)), stage, 'unit-probe', family, None, None, None,
                'unit-800ms', cue, seed, 800, (300, 600), False,
            )
            rows.append(probe)
            if seed == 5_000_042:
                _with_replay(rows, probe)
    for panel in (3_000_000, 4_000_000):
        for seed in range(5_000_042, 5_000_046):
            for cue in cues:
                rows.append(CallSpec(
                    _identifier((stage, panel, 'parent', cue, seed)), stage, 'parent-probe', family,
                    panel, None, None, 'acquired-parent', cue, seed, 800, (300, 600), False,
                ))
        for branch in REVERSAL_BRANCHES:
            for exposure in range(24):
                cue = cues[(0, 1, 1, 0)[exposure % 4]]
                cue_index = 0 if cue == cues[0] else 1
                trial = CallSpec(
                    _identifier((stage, panel, branch, exposure)), stage, 'train-reversal', family, panel,
                    None, branch, f'after-{exposure}', cue, 42 + panel + exposure, 800, (300, 600),
                    branch != 'frozen-retention', _reversal_teaching(branch, cue_index), exposure,
                )
                rows.append(trial)
                if exposure == 0:
                    _with_replay(rows, trial)
                if exposure in (7, 15):
                    checkpoint = 'block-2' if exposure == 7 else 'block-4'
                    for probe_cue in cues:
                        rows.append(CallSpec(
                            _identifier((stage, panel, branch, checkpoint, probe_cue)), stage,
                            'interim-probe', family, panel, None, branch, checkpoint, probe_cue,
                            5_001_042, 800, (300, 600), False,
                        ))
            for seed in range(5_000_042, 5_000_046):
                for cue in cues:
                    probe = CallSpec(
                        _identifier((stage, panel, branch, 'endpoint', cue, seed)), stage,
                        'endpoint-probe', family, panel, None, branch, 'endpoint', cue, seed, 800,
                        (300, 600), False,
                    )
                    rows.append(probe)
                    if branch == 'backward-erasure-plus-swap' and seed == 5_000_042:
                        _with_replay(rows, probe)


def build_call_plan(spec: dict | None = None) -> list[CallSpec]:
    spec = conditioning_spec() if spec is None else spec
    if spec.get('planned_calls') != 1632 or spec.get('hard_call_limit') != 1640:
        raise ValueError('Conditioning call limits differ from the frozen addendum.')
    rows: list[CallSpec] = []
    _add_acquisition(rows, 'AB', 'acquisition-primary')
    _add_acquisition(rows, 'CD', 'acquisition-challenge')
    _add_reversal(rows)
    return rows


def validate_call_plan(plan: list[CallSpec], dan_population_sizes=(2, 22)) -> dict:
    if tuple(dan_population_sizes) != (2, 22):
        raise ValueError('Conditioning requires the frozen two-home/22-away DAN populations.')
    if len(plan) != 1632 or len({row.id for row in plan}) != len(plan):
        raise ValueError('Conditioning call plan is incomplete or has duplicate IDs.')
    originals = {row.id for row in plan if row.replay_of is None}
    if any(row.replay_of not in originals for row in plan if row.replay_of is not None):
        raise ValueError('A replay does not identify an original call.')
    by_stage = {stage: sum(row.stage == stage for row in plan)
                for stage in ('acquisition-primary', 'acquisition-challenge', 'reversal')}
    if by_stage != {'acquisition-primary': 616, 'acquisition-challenge': 616, 'reversal': 400}:
        raise ValueError('Conditioning stage arithmetic differs from the frozen addendum.')
    if any(row.seed < 0 or row.duration_ms not in (400, 800) for row in plan):
        raise ValueError('Invalid call timing or seed.')
    return {'calls': len(plan), 'hard_call_limit': 1640, 'hard_wall_seconds': 1200,
            'by_stage': by_stage, 'selected_replays': sum(row.replay_of is not None for row in plan)}


def _jaccard(left: np.ndarray, right: np.ndarray) -> float:
    union = left | right
    return float(np.count_nonzero(left & right) / np.count_nonzero(union)) if union.any() else 1.0


def partition_kcs(kc_counts, plastic_kc_indices, plastic_compartments, plastic_mask) -> dict:
    counts = np.asarray(kc_counts)
    pk = np.asarray(plastic_kc_indices)
    pc = np.asarray(plastic_compartments)
    mask = np.asarray(plastic_mask)
    if (counts.ndim != 3 or counts.shape[:2] != (4, 2) or not np.isfinite(counts).all()
            or np.any(counts < 0) or pk.ndim != 1 or pc.shape != pk.shape or mask.shape != pk.shape
            or pk.dtype.kind not in 'iu' or pc.dtype.kind not in 'iu' or mask.dtype.kind not in 'iub'
            or np.any(pk < 0) or np.any(pk >= counts.shape[2]) or not np.isin(mask, (0, 1)).all()
            or not np.isin(pc, (0, 1)).all()):
        raise ValueError('KC partition inputs must match four seeds, two cues and existing plastic edges.')
    contrast = counts[:, 0].mean(0) - counts[:, 1].mean(0)
    preference = np.sign(contrast).astype(np.int8)
    active = counts > 0
    within = [[_jaccard(active[a, cue], active[b, cue]) for a, b in combinations(range(4), 2)]
              for cue in (0, 1)]
    between = [_jaccard(active[a, 0], active[b, 1]) for a in range(4) for b in range(4)]
    channels = {}
    nonempty = True
    for channel, compartment in zip(CHANNELS, (0, 1)):
        eligible = mask.astype(bool) & (pc == compartment)
        first = np.flatnonzero(eligible & (preference[pk] > 0))
        second = np.flatnonzero(eligible & (preference[pk] < 0))
        tied = np.flatnonzero(eligible & (preference[pk] == 0))
        channels[channel] = {'first': first, 'second': second, 'tied': tied}
        nonempty &= bool(first.size and second.size)
    first_mean, second_mean, between_mean = map(float, (np.mean(within[0]), np.mean(within[1]), np.mean(between)))
    passed = bool(nonempty and first_mean > between_mean and second_mean > between_mean
                  and between_mean <= 0.5)
    return {'passed': passed, 'preference': preference, 'channels': channels,
            'jaccard': {'within_first': within[0], 'within_second': within[1], 'between': between,
                        'within_first_mean': first_mean, 'within_second_mean': second_mean,
                        'between_mean': between_mean}}


def array_identity(value) -> dict:
    array = np.ascontiguousarray(value)
    if array.dtype.kind not in 'biufc' or not np.isfinite(array).all():
        raise ValueError('Numerical evidence must be finite.')
    return {'dtype': array.dtype.str, 'shape': list(array.shape),
            'sha256': hashlib.sha256(array.tobytes()).hexdigest()}


def _numeric_identities(value, path='', out=None):
    out = {} if out is None else out
    if path.rsplit('.', 1)[-1] == 'wall_seconds':
        return out
    if isinstance(value, dict):
        for key in sorted(value):
            _numeric_identities(value[key], f'{path}.{key}' if path else str(key), out)
    elif isinstance(value, np.ndarray) or isinstance(value, (int, float, complex, np.number, bool)):
        out[path] = array_identity(value)
    elif isinstance(value, (list, tuple)):
        array = np.asarray(value)
        if array.dtype.kind in 'biufc':
            out[path] = array_identity(array)
        else:
            for index, item in enumerate(value):
                _numeric_identities(item, f'{path}.{index}', out)
    return out


def compare_numeric_results(first: dict, second: dict) -> dict:
    left, right = _numeric_identities(first), _numeric_identities(second)
    differences = sorted(key for key in set(left) | set(right) if left.get(key) != right.get(key))
    return {'passed': not differences, 'differences': differences, 'first': left, 'second': right}


def _endpoint(value, n_gains=None):
    if not isinstance(value, dict):
        raise ValueError('Endpoint evidence must be a mapping.')
    responses = np.asarray(value.get('responses'), dtype=float)
    gains = np.asarray(value.get('gains'))
    hits = value.get('bound_hits')
    if (responses.shape != (4, 2, 2) or not np.isfinite(responses).all() or np.any(responses < 0)
            or gains.ndim != 1 or gains.dtype != np.float32 or not np.isfinite(gains).all()
            or (n_gains is not None and len(gains) != n_gains)
            or isinstance(hits, (bool, np.bool_)) or not isinstance(hits, (int, np.integer)) or hits < 0):
        raise ValueError('Endpoint responses, gains or bound evidence are malformed.')
    return responses, gains, int(hits)


def _mean_gain(gains, indices):
    selected = np.asarray(indices)
    if selected.ndim != 1 or selected.dtype.kind not in 'iu' or not selected.size:
        raise ValueError('Every preferred eligible edge set must be nonempty.')
    if np.any(selected < 0) or np.any(selected >= len(gains)):
        raise ValueError('Preferred edge index is outside the gain vector.')
    return float(np.mean(gains[selected], dtype=np.float64))


def evaluate_acquisition(unit, endpoints, partitions, *, effect_ratio=3.0, replay_error=0.0) -> dict:
    result = {'all_passed': False, 'errors': [], 'panels': {}}
    try:
        unit_response, unit_gains, unit_hits = _endpoint(unit)
        if unit_hits or not np.array_equal(unit_gains, np.ones_like(unit_gains)) or not partitions.get('passed'):
            raise ValueError('Unit checkpoint or KC specificity gate failed.')
        if set(endpoints) != {'0', '1000000'}:
            raise ValueError('Acquisition requires both training panels exactly once.')
        for panel_name, arms in endpoints.items():
            if set(arms) != set(ACQUISITION_ARMS):
                raise ValueError('Acquisition arm matrix is incomplete.')
            parsed = {name: _endpoint(value, len(unit_gains)) for name, value in arms.items()}
            panel_result = {}
            for channel_index, channel in enumerate(CHANNELS):
                target, other = channel_index, 1 - channel_index
                target_edges = partitions['channels'][channel]['first' if target == 0 else 'second']
                other_edges = partitions['channels'][channel]['second' if target == 0 else 'first']
                contrasts = {}
                gain_contrasts = {}
                target_changes = {}
                target_gain_changes = {}
                for arm, (responses, gains, hits) in parsed.items():
                    if hits:
                        raise ValueError(f'{panel_name}/{arm} contains a bound observation.')
                    delta = responses - unit_response
                    per_seed = delta[:, target, channel_index] - delta[:, other, channel_index]
                    contrasts[arm] = per_seed
                    target_changes[arm] = delta[:, target, channel_index]
                    gain_contrasts[arm] = (_mean_gain(gains - unit_gains, target_edges)
                                           - _mean_gain(gains - unit_gains, other_edges))
                    target_gain_changes[arm] = _mean_gain(gains - unit_gains, target_edges)
                nulls = ACQUISITION_ARMS[1:]
                response_limit = effect_ratio * max(abs(float(np.mean(contrasts[name]))) for name in nulls)
                gain_limit = effect_ratio * max(abs(gain_contrasts[name]) for name in nulls)
                paired_response = float(np.mean(contrasts['paired']))
                paired_gain = gain_contrasts['paired']
                target_response_error = max(replay_error, float(np.max(np.abs(target_changes['frozen']))))
                target_gain_error = max(replay_error, abs(target_gain_changes['frozen']))
                channel_result = {
                    'response_selectivity': paired_response,
                    'gain_selectivity': paired_gain,
                    'response_limit': response_limit,
                    'gain_limit': gain_limit,
                    'fresh_seed_signs_passed': bool(np.all(contrasts['paired'] < 0)),
                    'target_response_depressed': bool(np.all(target_changes['paired'] < -target_response_error)),
                    'target_gain_depressed': bool(target_gain_changes['paired'] < -target_gain_error),
                }
                channel_result['passed'] = bool(
                    channel_result['fresh_seed_signs_passed'] and paired_response < 0 and paired_gain < 0
                    and abs(paired_response) >= response_limit and abs(paired_gain) >= gain_limit
                    and channel_result['target_response_depressed'] and channel_result['target_gain_depressed']
                )
                panel_result[channel] = channel_result
            result['panels'][panel_name] = panel_result
        result['all_passed'] = bool(all(channel['passed'] for panel in result['panels'].values()
                                           for channel in panel.values()))
    except (KeyError, TypeError, ValueError) as exc:
        result['errors'].append(str(exc))
    return result


def _preference(responses, unit, channel):
    target, other = channel, 1 - channel
    return ((responses[:, target, channel] - responses[:, other, channel])
            - (unit[:, target, channel] - unit[:, other, channel]))


def evaluate_reversal(unit, parents, finals, partitions, starts, *, effect_ratio=3.0,
                      replay_error=0.0) -> dict:
    result = {'all_passed': False, 'errors': [], 'panels': {}, 'classification': 'failed'}
    any_remapping = False
    try:
        unit_response, unit_gains, unit_hits = _endpoint(unit)
        if unit_hits or not np.array_equal(unit_gains, np.ones_like(unit_gains)) or not partitions.get('passed'):
            raise ValueError('Reversal unit checkpoint or KC gate failed.')
        expected_panels = {'3000000', '4000000'}
        if set(parents) != expected_panels or set(finals) != expected_panels or set(starts) != expected_panels:
            raise ValueError('Reversal requires both panels and parents exactly once.')
        for panel_name in sorted(expected_panels):
            parent_response, parent_gains, parent_hits = _endpoint(parents[panel_name], len(unit_gains))
            branches = finals[panel_name]
            if parent_hits or set(branches) != set(REVERSAL_BRANCHES):
                raise ValueError('Reversal parent or branch matrix is invalid.')
            parent_hash = array_identity(parent_gains)['sha256']
            parsed = {name: _endpoint(value, len(unit_gains)) for name, value in branches.items()}
            lineage = all(starts[panel_name].get(name) == parent_hash
                          and branches[name].get('start_sha256') == parent_hash for name in REVERSAL_BRANCHES)
            panel_result = {'lineage_passed': lineage, 'channels': {}}
            panel_passed = lineage
            strict_response, strict_gains, strict_hits = parsed['backward-erasure-plus-swap']
            untaught_response, untaught_gains, untaught_hits = parsed['untaught-exposure']
            frozen_response, frozen_gains, frozen_hits = parsed['frozen-retention']
            continued_response = parsed['continued-acquisition'][0]
            if any(values[2] for values in parsed.values()):
                panel_passed = False
            frozen_exact = np.array_equal(frozen_gains, parent_gains)
            panel_passed &= frozen_exact and not strict_hits and not untaught_hits and not frozen_hits
            strict_flip = True
            recovery_all = True
            for channel_index, channel in enumerate(CHANNELS):
                old, new = channel_index, 1 - channel_index
                old_edges = partitions['channels'][channel]['first' if old == 0 else 'second']
                new_edges = partitions['channels'][channel]['second' if old == 0 else 'first']
                parent_preference = _preference(parent_response, unit_response, channel_index)
                strict_preference = _preference(strict_response, unit_response, channel_index)
                continued_preference = _preference(continued_response, unit_response, channel_index)
                parent_target = parent_response[:, old, channel_index] - unit_response[:, old, channel_index]
                parent_gain = _mean_gain(parent_gains, old_edges)
                parent_gate = bool(np.all(parent_preference < 0) and np.all(parent_target < 0) and parent_gain < 1)
                response_move = strict_response[:, old, channel_index] - parent_response[:, old, channel_index]
                null_move = untaught_response[:, old, channel_index] - parent_response[:, old, channel_index]
                frozen_move = frozen_response[:, old, channel_index] - parent_response[:, old, channel_index]
                response_recovery = bool(
                    np.all(response_move > effect_ratio * np.maximum(np.abs(null_move), np.abs(frozen_move)))
                    and np.all(np.abs(strict_response[:, old, channel_index] - unit_response[:, old, channel_index])
                               < np.abs(parent_response[:, old, channel_index] - unit_response[:, old, channel_index]))
                )
                gain_move = _mean_gain(strict_gains, old_edges) - parent_gain
                null_gain_move = _mean_gain(untaught_gains, old_edges) - parent_gain
                frozen_gain_move = _mean_gain(frozen_gains, old_edges) - parent_gain
                gain_recovery = bool(
                    gain_move > effect_ratio * max(abs(null_gain_move), abs(frozen_gain_move), replay_error)
                    and abs(_mean_gain(strict_gains, old_edges) - 1) < abs(parent_gain - 1)
                )
                strict_delta = strict_response - parent_response
                untaught_delta = untaught_response - parent_response
                frozen_delta = frozen_response - parent_response
                new_selectivity = (strict_delta[:, new, channel_index] - strict_delta[:, old, channel_index])
                null_selectivity = np.maximum(
                    np.abs(untaught_delta[:, new, channel_index] - untaught_delta[:, old, channel_index]),
                    np.abs(frozen_delta[:, new, channel_index] - frozen_delta[:, old, channel_index]),
                )
                new_response = bool(np.all(new_selectivity < 0)
                                    and np.all(np.abs(new_selectivity) >= effect_ratio * null_selectivity)
                                    and np.all(strict_delta[:, new, channel_index] < -replay_error))
                gain_delta = strict_gains - parent_gains
                untaught_gain_delta = untaught_gains - parent_gains
                frozen_gain_delta = frozen_gains - parent_gains
                new_gain_selectivity = (_mean_gain(gain_delta, new_edges) - _mean_gain(gain_delta, old_edges))
                null_gain = max(abs(_mean_gain(untaught_gain_delta, new_edges)
                                    - _mean_gain(untaught_gain_delta, old_edges)),
                                abs(_mean_gain(frozen_gain_delta, new_edges)
                                    - _mean_gain(frozen_gain_delta, old_edges)), replay_error)
                new_gain = bool(new_gain_selectivity < 0
                                and abs(new_gain_selectivity) >= effect_ratio * null_gain
                                and _mean_gain(gain_delta, new_edges) < -replay_error)
                flip = bool(np.all(parent_preference < 0) and np.all(strict_preference > 0)
                            and np.all(continued_preference < 0))
                strict_flip &= flip
                recovery_all &= response_recovery and gain_recovery
                channel_result = {
                    'parent_mapping_passed': parent_gate,
                    'response_recovery_passed': response_recovery,
                    'gain_recovery_passed': gain_recovery,
                    'new_response_passed': new_response,
                    'new_gain_passed': new_gain,
                    'preference_flip_passed': flip,
                }
                channel_result['passed'] = all(channel_result.values())
                panel_result['channels'][channel] = channel_result
                panel_passed &= channel_result['passed']
            panel_result['frozen_retention_passed'] = frozen_exact
            panel_result['passed'] = bool(panel_passed)
            result['panels'][panel_name] = panel_result
            any_remapping |= bool(strict_flip and not recovery_all)
        result['all_passed'] = bool(all(panel['passed'] for panel in result['panels'].values()))
        result['classification'] = ('strict-reversal' if result['all_passed'] else
                                    'dual-channel-preference-remapping-without-erasure'
                                    if any_remapping else 'failed')
    except (KeyError, TypeError, ValueError) as exc:
        result['errors'].append(str(exc))
    return result
