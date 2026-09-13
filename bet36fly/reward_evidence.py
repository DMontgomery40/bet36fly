"""Read-only, fail-closed presentation validation for stored reward diagnostics.

This module never imports or runs the neural engine.  It distinguishes a verdict
written by an experiment from criteria that can be independently reconstructed
from the immutable stored artifacts available in this checkout.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import zipfile
from pathlib import Path

import numpy as np

from .experiments import IDENTIFIER, safe_directory
from .reward_diagnostic import (
    RULE_REFERENCE,
    check_diagnostic_complete,
    evaluate_bound_hits,
    evaluate_cumulative,
    evaluate_panel,
    select_panel,
)


EVIDENCE_NOTE = 'docs/evidence/reward-mechanism-repair-2026-09-12/index.md'
CRITERIA = (
    'teaching_specific',
    'untaught_guard',
    'cross_compartment',
    'no_bound_hits',
    'cumulative',
    'bit_identical_repeat',
    'sensory_noise_invariance',
)
BRIDGE_FIELDS = (
    'positive_integral', 'negative_integral', 'attempted', 'double_applied',
    'published_applied', 'bound_low', 'bound_high', 'q_used',
)
TAIL_EQUATION = 'eta * n * Q_end / (1/tau_r + 1/tau_e)'


class EvidenceInvalid(ValueError):
    """A stored panel cannot support the verdict it advertises."""


def _digest(path):
    if Path(path).is_symlink():
        raise EvidenceInvalid(f'Symlink artifact is not permitted: {Path(path).name}.')
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _array_digest(value):
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def _json(path):
    if Path(path).is_symlink():
        raise EvidenceInvalid(f'Symlink artifact is not permitted: {Path(path).name}.')
    value = json.loads(Path(path).read_text(), parse_constant=lambda value: (_ for _ in ()).throw(EvidenceInvalid(f'Nonfinite JSON value: {value}')))
    if not isinstance(value, dict):
        raise EvidenceInvalid(f'{Path(path).name} must contain a JSON object.')
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
        elif isinstance(item, float) and not math.isfinite(item):
            raise EvidenceInvalid('Nonfinite JSON number, including numeric overflow.')
    return value


def canonical_pair_identity(identity):
    """Hash the full experiment identity except its predeclared panel selector."""
    if not isinstance(identity, dict):
        raise EvidenceInvalid('Diagnostic identity must be an object.')
    value = copy.deepcopy(identity)
    selection = value.get('selection')
    if isinstance(selection, dict):
        for field in ('panel_kind', 'panel_offset', 'seed_offset', 'panel_games',
                      'expected_panel', 'expected_cumulative'):
            selection.pop(field, None)
    value.pop('panel_kind', None)
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _stored_verdict(summary):
    complete = summary.get('panel_complete')
    passed = summary.get('all_passed')
    if complete is not True or not isinstance(passed, bool):
        return None
    return 'passed' if passed else 'failed'


def _criteria(summary, missing=()):
    source = summary.get('criteria')
    if not isinstance(source, dict):
        source = {}
    return {
        name: None if name in missing else (
            source.get(name, {}).get('passed')
            if isinstance(source.get(name), dict) and isinstance(source[name].get('passed'), bool)
            else None
        )
        for name in CRITERIA
    }


def _guard(summary):
    source = summary.get('criteria')
    source = source.get('untaught_guard', {}) if isinstance(source, dict) else {}
    source = source.get('evaluations', {}) if isinstance(source, dict) else {}
    if not isinstance(source, dict):
        return {}
    out = {}
    for key, value in source.items():
        if isinstance(key, str) and isinstance(value, dict):
            out[key] = {name: value.get(name) for name in ('mean', 'sd', 'limit', 'passed')}
    return out


def _teaching(summary):
    source = summary.get('criteria')
    source = source.get('teaching_specific', {}) if isinstance(source, dict) else {}
    source = source.get('evaluations', {}) if isinstance(source, dict) else {}
    if not isinstance(source, dict):
        return {}
    out = {}
    for key, value in source.items():
        if isinstance(key, str) and isinstance(value, dict):
            out[key] = {name: value.get(name) for name in (
                'mean_effect', 'mean_untaught', 'required_magnitude', 'passed')}
    return out


def _compact(directory, summary):
    identity = summary.get('identity') if isinstance(summary.get('identity'), dict) else {}
    protocol = identity.get('protocol') if isinstance(identity.get('protocol'), dict) else {}
    selection = identity.get('selection') if isinstance(identity.get('selection'), dict) else {}
    rule = summary.get('rule') if isinstance(summary.get('rule'), str) else identity.get('rule')
    recorded_rule = protocol.get('learning_rule')
    learning_rule = recorded_rule if recorded_rule in ('event', 'rate-bridge-v1') else (
        'event' if rule in ('legacy', 'candidate') else None)
    role = identity.get('panel_kind') or selection.get('panel_kind')
    role = role if role in ('original', 'held-out', 'debug') else None
    stored = _stored_verdict(summary)
    failed = [name for name, passed in _criteria(summary).items() if passed is False]
    bridge_contract = identity.get('bridge_contract') if isinstance(identity.get('bridge_contract'), dict) else None
    for source, fields in ((summary, ('created_at', 'panel_note')), (protocol, ('dan_reference', 'away_plasticity_mask', 'bridge_tail', 'bridge_layout'))):
        for name in fields:
            if source.get(name) is not None and not isinstance(source[name], str):
                raise EvidenceInvalid(f'{name} must be a string or null.')
    for name in ('panel_complete', 'all_passed', 'source_unchanged_during_run'):
        if summary.get(name) is not None and type(summary[name]) is not bool:
            raise EvidenceInvalid(f'{name} must be a boolean or null.')
    native = summary.get('native_binary')
    hashes = identity.get('code_hashes')
    if native is not None and not isinstance(native, dict):
        raise EvidenceInvalid('Native binary metadata must be an object.')
    if hashes is not None and not isinstance(hashes, dict):
        raise EvidenceInvalid('Source code hashes must be an object.')
    recorded_hashes = list((hashes or {}).values())
    if isinstance(native, dict) and native.get('sha256') is not None:
        recorded_hashes.append(native['sha256'])
    if any(not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value) for value in recorded_hashes):
        raise EvidenceInvalid('Recorded source/native hashes must be SHA256 strings.')
    if summary.get('created_at') is not None and not isinstance(summary['created_at'], str):
        raise EvidenceInvalid('created_at must be a string or null.')
    for name in ('tau_ms', 'learning_rate', 'rate_tau_ms', 'bridge_normalization'):
        if protocol.get(name) is not None and type(protocol[name]) not in (int, float):
            raise EvidenceInvalid(f'{name} must be a finite number or null.')
    if identity.get('bridge_contract') is not None:
        if (not isinstance(bridge_contract, dict) or not isinstance(bridge_contract.get('config'), dict)
                or not isinstance(bridge_contract.get('documents'), dict)
                or any(type(bridge_contract['config'].get(k)) not in (int, float)
                       for k in ('h_ms', 'tau_ms', 'rate_tau_ms', 'eta', 'normalization'))
                or any(not isinstance(bridge_contract.get(k), str) for k in ('layout', 'tail', 'state'))):
            raise EvidenceInvalid('Bridge contract presentation metadata is incomplete.')
    return {
        'run_id': directory.name,
        'rule': rule,
        'learning_rule': learning_rule,
        'learning_rule_source': 'recorded' if recorded_rule in ('event', 'rate-bridge-v1') else (
            'historical-rule-mapping' if learning_rule else None),
        'created_at': summary.get('created_at'),
        'dan_reference': protocol.get('dan_reference') or RULE_REFERENCE.get(rule),
        'away_plasticity_mask': protocol.get('away_plasticity_mask') or 'all',
        'panel_role': role,
        'selection_status': None,
        'panel_complete': summary.get('panel_complete') if isinstance(summary.get('panel_complete'), bool) else None,
        'stored_verdict': stored,
        'validation_status': 'stored-only' if stored else 'incomplete',
        'evidence_status': 'unverified' if stored else 'incomplete',
        'validation_error': None,
        'failed_criteria': failed,
        'missing_validation': list(CRITERIA),
        'criteria': _criteria(summary, CRITERIA),
        'untaught_guard': _guard(summary),
        'teaching_specific': _teaching(summary),
        'detail_url': f'/api/reward-diagnostics/{directory.name}',
        'tau_ms': protocol.get('tau_ms'),
        'learning_rate': protocol.get('learning_rate'),
        'rate_tau_ms': protocol.get('rate_tau_ms'),
        'bridge_normalization': protocol.get('bridge_normalization'),
        'bridge_tail': protocol.get('bridge_tail'),
        'bridge_layout': protocol.get('bridge_layout'),
        'bridge_contract': bridge_contract,
        'tail_evidence': None,
        'native_binary_sha256': (summary.get('native_binary', {}).get('sha256')
                                 if isinstance(summary.get('native_binary'), dict) else None),
        'source_unchanged_during_run': summary.get('source_unchanged_during_run'),
        '_pair_identity': None,
        'all_passed': summary.get('all_passed') if isinstance(summary.get('all_passed'), bool) else None,
        'has_attribution': (directory / 'attribution.json').is_file(),
        'panel_note': summary.get('panel_note'),
        'source_code_hashes': identity.get('code_hashes'),
        'preregistration_sha256': _digest(directory / 'preregistration.json') if (directory / 'preregistration.json').is_file() else None,
    }


def _evidence_locks(root):
    path = Path(root) / 'docs/evidence/reward-mechanism-repair-2026-09-12/bridge-residual-attribution.json'
    if not path.is_file():
        return {}
    document = _json(path)
    runs = document.get('runs')
    if not isinstance(runs, dict):
        raise EvidenceInvalid('Evidence lock registry has no runs object.')
    out = {}
    for value in runs.values():
        if not isinstance(value, dict) or not isinstance(value.get('run_id'), str):
            raise EvidenceInvalid('Evidence lock registry contains a malformed run.')
        out[value['run_id']] = value
    return out


def _verify_selector(identity):
    selection = identity['selection']
    calibration = selection['calibration_games']
    # Reconstruct the immutable selector, not a selection from observed outcomes.
    expected = select_panel(dict(X=np.zeros((len(calibration), 1)), source_indices=calibration,
                                 calibration_indices=calibration, input_mean=np.zeros(1), input_std=np.ones(1)),
                            seed=identity['protocol']['seed'], panel_offset=selection['panel_offset'],
                            seed_offset=selection['seed_offset'], games=identity['games'],
                            cumulative_games=identity['cumulative_games'], panel_kind=identity['panel_kind'])
    if any(selection.get(k) != v for k, v in expected.items()):
        raise EvidenceInvalid('Selector differs from its frozen source/seed contract.')
    required = {'protocol', 'rule', 'pilot', 'inputs_sha256', 'pilot_manifest_sha256',
                'pilot_protocol_sha256', 'graph_hashes', 'code_hashes', 'alt_seed_offset'}
    if not required.issubset(identity) or not identity['graph_hashes'] or not identity['code_hashes']:
        raise EvidenceInvalid('Scientific pair identity is incomplete.')


def _verify_identity_and_locks(root, directory, summary, lock):
    _verify_selector(summary['identity'])
    prereg = _json(directory / 'preregistration.json')
    expected_criteria = dict(teaching_effect_ratio=3.0, untaught_sd_ratio=0.5,
                             cross_compartment_ratio=0.05, cumulative_effect_ratio=4.0,
                             no_bound_hits=True, bit_identical_repeat=True, sensory_noise_invariance=True)
    if prereg.get('criteria') != expected_criteria or prereg.get('status') != 'preregistered-not-run':
        raise EvidenceInvalid('Preregistration criteria/status differ from the frozen contract.')
    if prereg.get('run_id') != directory.name or prereg.get('identity') != summary.get('identity'):
        raise EvidenceInvalid('Preregistration and measured identity differ.')
    summary_copy = Path(root) / 'docs/evidence/reward-mechanism-repair-2026-09-12' / f'panel-{directory.name}.json'
    if not summary_copy.is_file() or _digest(summary_copy) != _digest(directory / 'summary.json'):
        raise EvidenceInvalid('Measured summary does not match its immutable evidence copy.')
    if not isinstance(lock, dict):
        raise EvidenceInvalid('No immutable artifact lock is recorded for this panel.')
    if lock.get('summary_sha256') != _digest(directory / 'summary.json'):
        raise EvidenceInvalid('Summary hash disagrees with the immutable evidence lock.')
    if lock.get('trials_sha256') != _digest(directory / 'trials.npz'):
        raise EvidenceInvalid('Trial artifact hash disagrees with the immutable evidence lock.')
    if lock.get('measured_code_hashes') != summary.get('identity', {}).get('code_hashes'):
        raise EvidenceInvalid('Measured code identity disagrees with the immutable evidence lock.')
    if summary.get('source_unchanged_during_run') is not True:
        raise EvidenceInvalid('Source stability was not recorded as true.')


def _verify_declared_artifacts(directory, summary, required):
    artifacts = summary.get('artifacts')
    if not isinstance(artifacts, dict) or set(artifacts) != set(required):
        raise EvidenceInvalid(f'Expected exactly these artifact records: {sorted(required)}.')
    for name in required:
        meta = artifacts.get(name)
        path = directory / name
        if (not isinstance(meta, dict) or not path.is_file()
                or meta.get('sha256') != _digest(path) or meta.get('bytes') != path.stat().st_size):
            raise EvidenceInvalid(f'Artifact hash or byte count mismatch: {name}.')


def _recompute_common(summary, archive):
    identity = summary.get('identity')
    selection = identity.get('selection') if isinstance(identity, dict) else None
    rows, cumulative = summary.get('rows'), summary.get('cumulative_rows')
    if not isinstance(selection, dict) or not isinstance(rows, list) or not isinstance(cumulative, list):
        raise EvidenceInvalid('Complete selection, panel rows and cumulative rows are required.')
    try:
        if not check_diagnostic_complete(rows, cumulative, selection):
            raise EvidenceInvalid('Diagnostic matrix is incomplete or debug-only.')
        panel = evaluate_panel(rows, expected_games=selection['panel_games'])
        cumulative_result = evaluate_cumulative(
            [row['cumulative'] for row in cumulative],
            mean_effect=panel['mean_effect_by_compartment'],
        )
        bounds = evaluate_bound_hits(
            rows, cumulative, archive['cumulative_final_gains'],
            gain_bounds=identity['protocol']['gain_bounds'], plastic_mask=archive['plastic_mask'],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EvidenceInvalid(str(exc)) from exc
    recomputed = {name: value['passed'] for name, value in panel['criteria'].items()}
    recomputed['cumulative'] = cumulative_result['passed']
    recomputed['no_bound_hits'] = bounds['passed']
    return rows, cumulative, panel, recomputed, bounds


def _verify_raw(directory, summary, lock):
    _verify_identity_and_locks(directory.parents[2], directory, summary, lock)
    with np.load(directory / 'trials.npz', allow_pickle=False) as archive:
        rows, cumulative, _panel, recomputed, bounds = _recompute_common(summary, archive)
        try:
            compartments = archive['plastic_compartments']
            blank = archive['blank_gains']
            final = archive['cumulative_final_gains']
            for row in rows:
                prefix = f"{row['game']}__{row['seed_set']}__{row['condition']}"
                delta = archive[prefix + '__gain_delta'].astype(np.float64)
                actual = [float(delta[compartments == c].sum()) for c in (0, 1)]
                np.testing.assert_allclose(actual, row['applied'], rtol=0, atol=1e-6)
            final_sums = [float((final.astype(np.float64) - blank)[compartments == c].sum()) for c in (0, 1)]
            np.testing.assert_allclose(final_sums, cumulative[-1]['cumulative'], rtol=0, atol=1e-6)
        except (KeyError, ValueError, AssertionError) as exc:
            raise EvidenceInvalid(f'Raw archive reconciliation failed: {exc}') from exc
    stored = {name: value.get('passed') for name, value in summary['criteria'].items()
              if isinstance(value, dict)}
    for name, value in recomputed.items():
        if stored.get(name) is not value:
            raise EvidenceInvalid(f'Recomputed {name} disagrees with the stored verdict.')
    missing = ('bit_identical_repeat', 'sensory_noise_invariance')
    return recomputed, bounds, missing, None


def _bridge_reduction(archive, prefix, before, row, mask, compartments, groups, steps):
    gains = archive[prefix + '__gains']
    rule = archive[prefix + '__bridge_rule']
    tail = archive[prefix + '__bridge_tail']
    delta = archive[prefix + '__gain_delta'] if prefix + '__gain_delta' in archive else gains - before
    if (gains.shape != before.shape or gains.dtype != np.float32 or delta.shape != before.shape
            or not np.array_equal(delta, gains - before)
            or rule.shape != (steps, 8, 8) or tail.shape != (8, 8)
            or rule.dtype != np.float64 or tail.dtype != np.float64
            or not np.isfinite(rule).all() or not np.isfinite(tail).all()
            or not np.isfinite(gains).all()):
        raise EvidenceInvalid(f'Invalid bridge array layout for {prefix}.')
    if (groups.shape != before.shape or compartments.shape != before.shape or mask.shape != before.shape
            or groups.dtype.kind not in 'iu' or compartments.dtype.kind not in 'iu'
            or np.any(groups < 0) or np.any(groups >= 8)
            or not np.array_equal(groups // 4, compartments)):
        raise EvidenceInvalid(f'Invalid bridge group/compartment mapping for {prefix}.')
    eligible = gains[mask]
    if np.any(eligible < .5) or np.any(eligible > 1.5):
        raise EvidenceInvalid(f'Eligible trial checkpoint lies outside bridge bounds for {prefix}.')
    onset = int(round(100.0 / 0.2))
    if onset <= steps and np.any(rule[:onset]):
        raise EvidenceInvalid(f'Bridge writes before learning onset for {prefix}.')
    if not np.array_equal(gains[~mask], before[~mask]):
        raise EvidenceInvalid(f'Ineligible gains changed for {prefix}.')
    for values in (rule, tail):
        if not np.allclose(values[..., 0] + values[..., 1], values[..., 2], rtol=1e-8, atol=1e-11):
            raise EvidenceInvalid(f'Bridge term decomposition failed for {prefix}.')
        counts = values[..., 5:7]
        if np.any(counts < 0) or not np.equal(counts, np.rint(counts)).all():
            raise EvidenceInvalid(f'Bridge bound observations are malformed for {prefix}.')
    total = rule.sum(0) + tail
    actual_delta = gains.astype(np.float64) - before.astype(np.float64)
    group_delta = np.array([actual_delta[groups == g].sum() for g in range(8)])
    if not np.allclose(group_delta, total[:, 4], rtol=0, atol=1e-6):
        raise EvidenceInvalid(f'Bridge group publication does not reconcile for {prefix}.')
    for group in range(8):
        endpoint_count = np.count_nonzero(mask & (groups == group) & ((gains <= .5) | (gains >= 1.5)))
        if endpoint_count > total[group, 5:7].sum():
            raise EvidenceInvalid(f'Eligible endpoint bound observations are missing for {prefix}.')
    actual = np.array([actual_delta[compartments == c].sum() for c in (0, 1)])
    recorded = np.array([total[np.arange(8) // 4 == c, 4].sum() for c in (0, 1)])
    if not np.allclose(actual, recorded, rtol=0, atol=1e-6):
        raise EvidenceInvalid(f'Bridge publication does not reconcile for {prefix}.')
    if not np.allclose(actual, row['applied'], rtol=0, atol=1e-6):
        raise EvidenceInvalid(f'Bridge applied sums do not reconcile for {prefix}.')
    counts = int(rule[..., 5:7].sum() + tail[:, 5:7].sum())
    if (counts != row.get('clipped')
            or int(rule[..., 5:7].sum()) != row.get('electrical_bound_observations')
            or int(tail[:, 5:7].sum()) != row.get('tail_bound_observations')):
        raise EvidenceInvalid(f'Bridge bound counts do not reconcile for {prefix}.')
    return gains, actual, rule, tail, counts, float(np.abs(actual - recorded).max())


def _verify_replay(replay):
    names = {'counts', 'rates', 'rates_hz', 'voltage', 'trace', 'population', 'dan_counts',
             'compartment_dan_counts', 'compartment_tonic_hz', 'gains', 'gain_delta',
             'pulse_times_ms', 'pulse_dan_indices'}
    names.update('instrumentation/' + name for name in (
        'bridge_signals', 'bridge_kc_bins', 'bridge_kc_used', 'bridge_rule', 'bridge_tail',
        'plastic_groups', 'plastic_compartments', 'step_signals', 'signal_bins', 'kc_signal_bins'))
    if set(replay) != {'frozen', 'untaught', 'home', 'away'}:
        raise EvidenceInvalid('Bridge replay fingerprints have an incomplete condition matrix.')
    for value in replay.values():
        if not isinstance(value, dict) or set(value) != {'original', 'repeat'}:
            raise EvidenceInvalid('Malformed replay fingerprint record.')
        original = value['original']
        if not isinstance(original, dict) or set(original) != names or original != value['repeat']:
            raise EvidenceInvalid('Bridge replay fingerprints are incomplete or differ.')
        for fingerprint in original.values():
            if (not isinstance(fingerprint, list) or len(fingerprint) != 3
                    or fingerprint[0] not in ('int32', 'float32', 'float64')
                    or not isinstance(fingerprint[1], list)
                    or any(type(n) is not int or n < 0 for n in fingerprint[1])
                    or not isinstance(fingerprint[2], str) or not re.fullmatch('[0-9a-f]{64}', fingerprint[2])):
                raise EvidenceInvalid('Malformed replay array fingerprint.')


def _verify_bridge(directory, summary, lock):
    _verify_declared_artifacts(directory, summary, ('trials.npz', 'recording-layout.json', 'replay-evidence.json'))
    _verify_identity_and_locks(directory.parents[2], directory, summary, lock)
    protocol = summary['identity']['protocol']
    expected = {
        'learning_rule': 'rate-bridge-v1', 'rate_tau_ms': 100.0, 'tau_ms': 500.0,
        'learning_rate': 0.0005, 'bridge_normalization': 0.96, 'gain_bounds': [.5, 1.5],
        'bridge_tail': 'analytic_no_new_event_tail', 'bridge_layout': 'rate-bridge-v1/1',
    }
    if any(protocol.get(key) != value for key, value in expected.items()):
        raise EvidenceInvalid('Bridge rule metadata differs from the frozen contract.')
    layout = _json(directory / 'recording-layout.json')
    if (layout.get('layout_version') != 'rate-bridge-v1/1'
            or layout.get('config', {}).get('tail') != 'analytic_no_new_event_tail'
            or layout.get('layout', {}).get('bridge_rule') != list(BRIDGE_FIELDS)
            or layout.get('layout', {}).get('bridge_tail') != list(BRIDGE_FIELDS)):
        raise EvidenceInvalid('Bridge recording layout metadata is incomplete or incompatible.')
    replay = _json(directory / 'replay-evidence.json')
    _verify_replay(replay)

    steps = int(round(protocol['duration_ms'] / 0.2))
    max_error = 0.0
    totals = np.zeros(5)
    total_bounds = 0
    sensory = {}
    with np.load(directory / 'trials.npz', allow_pickle=False) as archive:
        rows, cumulative, _panel, recomputed, bounds = _recompute_common(summary, archive)
        compartments = archive['plastic_compartments']
        groups = archive['plastic_groups']
        mask = archive['plastic_mask'].astype(bool)
        classes = archive['kc_classes']
        blank = archive['blank_gains']
        if (groups.shape != compartments.shape or classes.shape != compartments.shape
                or not np.array_equal(groups, compartments * 4 + classes)
                or not np.array_equal(mask, (compartments == 0) | (classes == 0))
                or not np.array_equal(blank, np.ones_like(blank))):
            raise EvidenceInvalid('Bridge eligibility mask or unit checkpoint is inconsistent.')
        first_game = summary['identity']['selection']['panel_games'][0]
        for row in rows:
            prefix = f"{row['game']}__{row['seed_set']}__{row['condition']}"
            gains, _actual, rule, tail, count, error = _bridge_reduction(
                archive, prefix, blank, row, mask, compartments, groups, steps)
            totals += (rule.sum(0) + tail)[:, :5].sum(0)
            total_bounds += count
            max_error = max(max_error, error)
            if row['condition'] == 'frozen' and not np.array_equal(gains, blank):
                raise EvidenceInvalid(f'Frozen gains changed for {prefix}.')
            sensory_bins = archive[prefix + '__sensory_bins']
            digest = _array_digest(sensory_bins)
            if digest != row.get('sensory_bins_sha256'):
                raise EvidenceInvalid(f'Sensory history hash mismatch for {prefix}.')
            sensory.setdefault((row['game'], row['seed_set']), []).append(digest)
            if row['game'] == first_game and row['seed_set'] == 'base':
                arrays = {'gains': gains, 'gain_delta': archive[prefix + '__gain_delta'],
                          'trace': archive[prefix + '__sampled_bins'],
                          'instrumentation/bridge_rule': rule, 'instrumentation/bridge_tail': tail,
                          'instrumentation/bridge_signals': archive[prefix + '__bridge_signals'],
                          'instrumentation/bridge_kc_bins': archive[prefix + '__bridge_kc_bins'],
                          'instrumentation/bridge_kc_used': archive[prefix + '__bridge_kc_used']}
                fingerprints = replay[row['condition']]['original']
                for name, array in arrays.items():
                    if fingerprints.get(name) != [str(array.dtype), list(array.shape), _array_digest(array)]:
                        raise EvidenceInvalid(f'Replay fingerprint mismatch for {row["condition"]}/{name}.')
        before = blank
        for row in cumulative:
            prefix = f"cumulative_{row['game']}"
            before, _actual, _rule, _tail, count, error = _bridge_reduction(
                archive, prefix, before, row, mask, compartments, groups, steps)
            totals += (_rule.sum(0) + _tail)[:, :5].sum(0)
            total_bounds += count
            max_error = max(max_error, error)
            actual_cumulative = [float((before.astype(np.float64) - blank)[compartments == c].sum())
                                 for c in (0, 1)]
            if not np.allclose(actual_cumulative, row['cumulative'], rtol=0, atol=1e-6):
                raise EvidenceInvalid(f'Cumulative checkpoint mismatch for {prefix}.')
        if not np.array_equal(before, archive['cumulative_final_gains']):
            raise EvidenceInvalid('Final cumulative checkpoint is not the last saved checkpoint.')
    recomputed['bit_identical_repeat'] = True
    recomputed['sensory_noise_invariance'] = all(len(values) == 4 and len(set(values)) == 1
                                                  for values in sensory.values())
    recomputed['no_bound_hits'] = bounds['passed'] and total_bounds == 0
    stored = {name: value.get('passed') for name, value in summary['criteria'].items()
              if isinstance(value, dict)}
    if {name: recomputed.get(name) for name in CRITERIA} != {name: stored.get(name) for name in CRITERIA}:
        raise EvidenceInvalid('Recomputed criterion matrix disagrees with the stored verdict.')
    if all(recomputed.values()) != summary.get('all_passed'):
        raise EvidenceInvalid('Recomputed overall verdict disagrees with the stored verdict.')
    tail = {
        'totals': dict(zip(('positive_integral', 'negative_integral', 'attempted', 'double_applied', 'published_applied'), totals.tolist())),
        'clipping_discrepancy': float(totals[3] - totals[2]),
        'final_rounding_discrepancy': float(totals[4] - totals[3]),
        'equation': TAIL_EQUATION,
        'extends_neural_time': False,
        'electrical_bound_observations': sum(int(row['electrical_bound_observations'])
                                             for row in summary['rows'] + summary['cumulative_rows']),
        'tail_bound_observations': sum(int(row['tail_bound_observations'])
                                       for row in summary['rows'] + summary['cumulative_rows']),
        'max_publication_reconciliation_error': max_error,
    }
    return recomputed, bounds, (), tail


def _validate_uncached(root, directory, summary, entry, locks):
    lock = locks.get(directory.name)
    try:
        # Declared files must be internally valid even without an independent evidence lock.
        if 'artifacts' in summary:
            required = ('trials.npz', 'recording-layout.json', 'replay-evidence.json') if entry['learning_rule'] == 'rate-bridge-v1' else tuple(summary['artifacts'])
            if any(name not in ('trials.npz', 'recording-layout.json', 'replay-evidence.json') for name in required):
                raise EvidenceInvalid('Unexpected artifact name.')
            _verify_declared_artifacts(directory, summary, required)
        if summary.get('panel_complete') is not True:
            entry.update(validation_status='incomplete', evidence_status='incomplete')
            return entry
        if lock is None:
            return entry
        if entry['learning_rule'] == 'rate-bridge-v1':
            recomputed, _bounds, missing, tail = _verify_bridge(directory, summary, lock)
        else:
            recomputed, _bounds, missing, tail = _verify_raw(directory, summary, lock)
    except (EvidenceInvalid, OSError, json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError, zipfile.BadZipFile) as exc:
        entry.update(validation_status='invalid', evidence_status='unverified', validation_error=str(exc))
        return entry
    entry['selection_status'] = 'previously-frozen' if entry['panel_role'] == 'held-out' else None
    entry['_pair_identity'] = canonical_pair_identity(dict(summary['identity'], native_binary_sha256=entry['native_binary_sha256']))
    entry['criteria'] = {name: None if name in missing else recomputed.get(name) for name in CRITERIA}
    entry['missing_validation'] = list(missing)
    entry['tail_evidence'] = tail
    if missing:
        entry.update(validation_status='stored-only', evidence_status='unverified')
    else:
        passed = all(entry['criteria'].get(name) is True for name in CRITERIA)
        entry.update(validation_status='validated', evidence_status='passed' if passed else 'failed')
    return entry


_VALIDATION_CACHE = {}


def _artifact_snapshot(root, directory):
    evidence = Path(root) / 'docs/evidence/reward-mechanism-repair-2026-09-12'
    paths = [directory / name for name in ('summary.json', 'preregistration.json', 'trials.npz',
             'recording-layout.json', 'replay-evidence.json', 'attribution.json')]
    paths += [evidence / f'panel-{directory.name}.json', evidence / 'bridge-residual-attribution.json']
    return tuple((str(path), _digest(path) if path.exists() or path.is_symlink() else None) for path in paths)


def _validate(root, directory, summary, entry, locks):
    # Hash bytes on every read; cache only the costly NPZ reconciliation. A removed,
    # changed, or relinked artifact cannot reuse a prior scientific verdict.
    try:
        snapshot = _artifact_snapshot(root, directory)
        summary = _load_panel_summary(directory)
        locks = _evidence_locks(root)
        entry = _compact(directory, summary)
        key = str(directory.resolve())
        cached = _VALIDATION_CACHE.get(key)
        if cached and cached[0] == snapshot:
            result = copy.deepcopy(cached[1])
        else:
            result = _validate_uncached(root, directory, summary, entry, locks)
        if snapshot != _artifact_snapshot(root, directory):
            raise EvidenceInvalid('Artifacts changed during validation; retry a stable snapshot.')
        if len(_VALIDATION_CACHE) >= 128:
            _VALIDATION_CACHE.clear()
        _VALIDATION_CACHE[key] = (snapshot, copy.deepcopy(result))
        return result
    except (EvidenceInvalid, OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return dict(entry, validation_status='invalid', evidence_status='unverified', validation_error=str(exc))


def _qualification_pairs(entries):
    groups = {}
    for entry in entries:
        key = entry.get('_pair_identity')
        role = entry.get('panel_role')
        if key and role in ('original', 'held-out'):
            groups.setdefault(key, {}).setdefault(role, []).append(entry)
    pairs = []
    for key, roles in groups.items():
        if len(roles.get('original', ())) != 1 or len(roles.get('held-out', ())) != 1:
            continue
        original, heldout = roles['original'][0], roles['held-out'][0]
        statuses = {original['validation_status'], heldout['validation_status']}
        if statuses == {'validated'}:
            evidence = 'failed' if 'failed' in (original['evidence_status'], heldout['evidence_status']) else 'passed'
            validation = 'validated'
        else:
            evidence = 'unverified'
            validation = 'invalid' if 'invalid' in statuses else 'stored-only'
        failed = sorted(set(original['failed_criteria'] + heldout['failed_criteria']))
        pairs.append({
            'pair_id': key[:16], 'learning_rule': original['learning_rule'],
            'original_run_id': original['run_id'], 'heldout_run_id': heldout['run_id'],
            'validation_status': validation, 'evidence_status': evidence,
            'failed_criteria': failed,
        })
    return sorted(pairs, key=lambda pair: (pair['learning_rule'] or '', pair['pair_id']))


def _failed_pair_members(entries, pairs):
    failed = {entry['run_id'] for entry in entries
              if entry['validation_status'] == 'validated' and entry['evidence_status'] == 'failed'}
    members = {pair[field] for pair in pairs
               if pair['validation_status'] == 'validated' and pair['evidence_status'] == 'failed'
               for field in ('original_run_id', 'heldout_run_id')}
    return sorted(failed & members)


def _load_panel_summary(directory):
    if not (directory / 'summary.json').exists() and (directory / 'preregistration.json').is_file():
        summary = dict(_json(directory / 'preregistration.json'), panel_complete=False, all_passed=None)
    else:
        summary = _json(directory / 'summary.json')
    if summary.get('run_id') != directory.name:
        raise EvidenceInvalid('Diagnostic identity mismatch.')
    return summary


def list_reward_evidence(root):
    root = Path(root)
    directory = root / 'output/diagnostics'
    entries = []
    try:
        locks = _evidence_locks(root)
    except (EvidenceInvalid, OSError, json.JSONDecodeError):
        locks = {}
    if directory.is_dir():
        for child in directory.iterdir():
            if child.is_symlink() or not child.is_dir() or not IDENTIFIER.fullmatch(child.name):
                continue
            try:
                summary = _load_panel_summary(child)
                entry = _compact(child, summary)
                entries.append(_validate(root, child, summary, entry, locks))
            except (EvidenceInvalid, OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
                entries.append({
                    'run_id': child.name, 'rule': None, 'learning_rule': None,
                    'learning_rule_source': None, 'created_at': None, 'dan_reference': None,
                    'away_plasticity_mask': None, 'panel_role': None, 'selection_status': None,
                    'panel_complete': None, 'stored_verdict': None, 'validation_status': 'invalid',
                    'evidence_status': 'unverified', 'validation_error': str(exc),
                    'failed_criteria': [], 'missing_validation': list(CRITERIA),
                    'criteria': {name: None for name in CRITERIA}, 'untaught_guard': {},
                    'teaching_specific': {}, 'detail_url': f'/api/reward-diagnostics/{child.name}',
                    'tau_ms': None, 'learning_rate': None, 'rate_tau_ms': None,
                    'bridge_normalization': None, 'bridge_tail': None, 'bridge_layout': None,
                    'bridge_contract': None, 'tail_evidence': None,
                    'native_binary_sha256': None, 'source_unchanged_during_run': None,
                    '_pair_identity': None,
                })
    entries.sort(key=lambda entry: (entry.get('created_at') or '', entry['run_id']), reverse=True)
    pairs = _qualification_pairs(entries)
    failed = _failed_pair_members(entries, pairs)
    conditioning = ({
        'status': 'not_run_gate_failed',
        'message': 'Conditioning not run: mechanism qualification is blocked.',
        'failed_diagnostic_ids': failed,
    } if failed else {
        'status': 'not_run', 'message': 'No conditioning manifest registered.',
        'failed_diagnostic_ids': [],
    })
    for entry in entries:
        entry.pop('_pair_identity', None)
    return {'diagnostics': entries, 'qualification_pairs': pairs,
            'conditioning': conditioning, 'evidence_note': EVIDENCE_NOTE}


def read_reward_evidence(root, run_id):
    directory = safe_directory(Path(root) / 'output/diagnostics', run_id)
    if not directory.is_dir():
        raise FileNotFoundError(run_id)
    snapshot = _artifact_snapshot(root, directory)
    summary = _load_panel_summary(directory)
    index = list_reward_evidence(root)
    validation = next((row for row in index['diagnostics'] if row['run_id'] == run_id), None)
    if validation is None:
        raise FileNotFoundError(run_id)
    attribution_path = directory / 'attribution.json'
    attribution = _json(attribution_path) if attribution_path.is_file() else None
    if snapshot != _artifact_snapshot(root, directory):
        raise EvidenceInvalid('Artifacts changed while reading diagnostic detail; retry.')
    return {'summary': summary, 'attribution': attribution, 'validation': validation}
