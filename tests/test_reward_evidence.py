import json
from pathlib import Path

import pytest

from bet36fly.reward_evidence import (
    EVIDENCE_NOTE,
    canonical_pair_identity,
    list_reward_evidence,
)


ROOT = Path(__file__).resolve().parents[1]


def by_id(index):
    return {row['run_id']: row for row in index['diagnostics']}


def test_repository_mechanism_evidence_is_recomputed_and_never_promotes_stored_only_passes():
    index = list_reward_evidence(ROOT)
    panels = by_id(index)

    raw_original = panels['diag-candidate-maskgamma-29c766f95f82']
    raw_heldout = panels['diag-candidate-maskgamma-e3d8898dc68a']
    assert raw_original['stored_verdict'] == 'passed'
    assert raw_original['validation_status'] == 'stored-only'
    assert raw_original['evidence_status'] == 'unverified'
    assert set(raw_original['missing_validation']) == {'bit_identical_repeat', 'sensory_noise_invariance'}
    assert raw_heldout['stored_verdict'] == 'failed'
    assert raw_heldout['validation_status'] == 'stored-only'
    assert raw_heldout['evidence_status'] == 'unverified'
    assert raw_heldout['failed_criteria'] == ['untaught_guard']
    assert raw_heldout['untaught_guard']['home/base']['passed'] is False
    assert {k: raw_heldout['untaught_guard']['home/base'][k] for k in ('mean', 'sd', 'limit')} == pytest.approx({
        'mean': -0.5156228840351105,
        'sd': 0.9795557677547752,
        'limit': 0.4897778838773876,
    })

    bridge_original = panels['diag-rate-bridge-v1-maskgamma-de050d773763']
    bridge_heldout = panels['diag-rate-bridge-v1-maskgamma-dea14759e9ca']
    assert bridge_original['stored_verdict'] == bridge_original['evidence_status'] == 'passed'
    assert bridge_heldout['stored_verdict'] == bridge_heldout['evidence_status'] == 'failed'
    assert bridge_original['validation_status'] == bridge_heldout['validation_status'] == 'validated'
    assert bridge_heldout['failed_criteria'] == ['untaught_guard']
    assert bridge_heldout['untaught_guard']['home/base']['passed'] is False
    assert {k: bridge_heldout['untaught_guard']['home/base'][k] for k in ('mean', 'sd', 'limit')} == pytest.approx({
        'mean': -0.27264003455638885,
        'sd': 0.48169047084658934,
        'limit': 0.24084523542329467,
    })
    assert bridge_heldout['learning_rule'] == 'rate-bridge-v1'
    assert bridge_heldout['rate_tau_ms'] == 100.0
    assert bridge_heldout['tau_ms'] == 500.0
    assert bridge_heldout['bridge_normalization'] == 0.96
    assert bridge_heldout['bridge_tail'] == 'analytic_no_new_event_tail'
    assert bridge_heldout['bridge_layout'] == 'rate-bridge-v1/1'
    assert bridge_heldout['tail_evidence']['equation'] == 'eta * n * Q_end / (1/tau_r + 1/tau_e)'
    assert bridge_heldout['tail_evidence']['extends_neural_time'] is False
    assert bridge_heldout['tail_evidence']['tail_bound_observations'] == 0
    assert bridge_heldout['detail_url'].endswith(bridge_heldout['run_id'])

    pairs = {pair['learning_rule']: pair for pair in index['qualification_pairs']}
    assert pairs['rate-bridge-v1'] == {
        **pairs['rate-bridge-v1'],
        'original_run_id': bridge_original['run_id'],
        'heldout_run_id': bridge_heldout['run_id'],
        'validation_status': 'validated',
        'evidence_status': 'failed',
        'failed_criteria': ['untaught_guard'],
    }
    assert pairs['event']['validation_status'] == 'stored-only'
    assert pairs['event']['evidence_status'] == 'unverified'
    assert index['conditioning'] == {
        'status': 'not_run_gate_failed',
        'message': 'Conditioning not run: mechanism qualification is blocked.',
        'failed_diagnostic_ids': [bridge_heldout['run_id']],
    }
    assert index['evidence_note'] == EVIDENCE_NOTE


def _write_summary(root, run_id, *, complete=True, passed=True, rule='candidate', panel_kind='original'):
    directory = root / 'output/diagnostics' / run_id
    directory.mkdir(parents=True)
    identity = {
        'rule': rule,
        'panel_kind': panel_kind,
        'protocol': {'dan_reference': 'none', 'away_plasticity_mask': 'gamma'},
        'selection': {'panel_kind': panel_kind, 'panel_games': list(range(8)),
                      'expected_panel': [], 'expected_cumulative': []},
        'code_hashes': {'reward_lif.cpp': 'a' * 64},
    }
    summary = {
        'run_id': run_id, 'rule': rule, 'created_at': '2026-09-12T00:00:00Z',
        'panel_complete': complete, 'all_passed': passed, 'identity': identity,
        'criteria': {'untaught_guard': {'passed': passed, 'evaluations': {}}},
        'rows': [], 'cumulative_rows': [],
    }
    (directory / 'summary.json').write_text(json.dumps(summary))
    return directory, summary


def test_invalid_incomplete_and_legacy_evidence_remain_visible_without_a_pass(tmp_path):
    invalid = tmp_path / 'output/diagnostics/diag-invalid'
    invalid.mkdir(parents=True)
    (invalid / 'summary.json').write_text('{not json')
    _write_summary(tmp_path, 'diag-incomplete', complete=False)
    _write_summary(tmp_path, 'diag-legacy-stored', passed=True)

    panels = by_id(list_reward_evidence(tmp_path))
    assert panels['diag-invalid']['validation_status'] == 'invalid'
    assert panels['diag-invalid']['stored_verdict'] is None
    assert panels['diag-invalid']['evidence_status'] == 'unverified'
    assert panels['diag-incomplete']['validation_status'] == 'incomplete'
    assert panels['diag-incomplete']['evidence_status'] == 'incomplete'
    assert panels['diag-legacy-stored']['stored_verdict'] == 'passed'
    assert panels['diag-legacy-stored']['validation_status'] == 'stored-only'
    assert panels['diag-legacy-stored']['evidence_status'] == 'unverified'


def test_changed_or_missing_artifacts_fail_closed_instead_of_reusing_stored_pass(tmp_path):
    directory, summary = _write_summary(tmp_path, 'diag-rate-bridge-v1-tampered', rule='rate-bridge-v1')
    summary['identity']['protocol'].update({
        'learning_rule': 'rate-bridge-v1', 'rate_tau_ms': 100.0, 'tau_ms': 500.0,
        'bridge_normalization': 0.96, 'bridge_tail': 'analytic_no_new_event_tail',
        'bridge_layout': 'rate-bridge-v1/1',
    })
    summary['artifacts'] = {'trials.npz': {'sha256': '0' * 64, 'bytes': 1}}
    (directory / 'summary.json').write_text(json.dumps(summary))
    (directory / 'preregistration.json').write_text(json.dumps({'run_id': directory.name, 'identity': summary['identity']}))
    (directory / 'trials.npz').write_bytes(b'x')

    panel = by_id(list_reward_evidence(tmp_path))[directory.name]
    assert panel['stored_verdict'] == 'passed'
    assert panel['validation_status'] == 'invalid'
    assert panel['evidence_status'] == 'unverified'
    assert 'artifact' in panel['validation_error'].lower()


def test_pair_identity_excludes_only_declared_panel_selection_fields():
    identity = {
        'rule': 'candidate', 'panel_kind': 'original',
        'selection': {'panel_kind': 'original', 'panel_offset': 0, 'seed_offset': 0},
        'protocol': {'tau_ms': 500.0, 'learning_rate': 0.0005},
        'code_hashes': {'reward_lif.cpp': 'a' * 64}, 'inputs_sha256': 'b' * 64,
    }
    heldout = json.loads(json.dumps(identity))
    heldout['panel_kind'] = 'held-out'
    heldout['selection'] = {'panel_kind': 'held-out', 'panel_offset': 8, 'seed_offset': 2_000_000}
    assert canonical_pair_identity(identity) == canonical_pair_identity(heldout)
    heldout['protocol']['tau_ms'] = 499.0
    assert canonical_pair_identity(identity) != canonical_pair_identity(heldout)



@pytest.mark.parametrize('field', ['calibration_games', 'alt_seed_offset', 'extra_contract'])
def test_pair_identity_retains_shared_selector_contract(field):
    original = {'protocol': {'seed': 42}, 'selection': {'panel_kind': 'original', field: [1, 2]}}
    changed = json.loads(json.dumps(original))
    changed['selection'][field] = [3, 4]
    assert canonical_pair_identity(original) != canonical_pair_identity(changed)


def test_declared_artifact_failure_is_not_hidden_without_qualification_lock(tmp_path):
    directory, summary = _write_summary(tmp_path, 'diag-declared-broken')
    summary['artifacts'] = {'trials.npz': {'sha256': '0' * 64, 'bytes': 42}}
    (directory / 'summary.json').write_text(json.dumps(summary))
    panel = by_id(list_reward_evidence(tmp_path))[directory.name]
    assert panel['validation_status'] == 'invalid'
    assert panel['evidence_status'] == 'unverified'


def test_preregistered_directory_without_result_stays_visible_as_incomplete(tmp_path):
    directory, summary = _write_summary(tmp_path, 'diag-not-finished')
    (directory / 'preregistration.json').write_text(json.dumps({'run_id': directory.name, 'identity': summary['identity']}))
    (directory / 'summary.json').unlink()
    panel = by_id(list_reward_evidence(tmp_path))[directory.name]
    assert panel['validation_status'] == panel['evidence_status'] == 'incomplete'
    assert panel['stored_verdict'] is None


@pytest.mark.parametrize('mutation', ['dtype', 'shape', 'nan', 'count', 'excluded', 'delta'])
def test_bridge_reconciliation_rejects_recording_corruption_family(mutation):
    import numpy as np
    from bet36fly.reward_evidence import EvidenceInvalid, _bridge_reduction
    before = np.ones(2, dtype=np.float32)
    archive = {'t__gains': before.copy(), 't__bridge_rule': np.zeros((500, 8, 8)),
               't__bridge_tail': np.zeros((8, 8)), 't__gain_delta': np.zeros(2, dtype=np.float32)}
    row = dict(applied=[0, 0], clipped=0, electrical_bound_observations=0, tail_bound_observations=0)
    if mutation == 'dtype':
        archive['t__bridge_tail'] = archive['t__bridge_tail'].astype(np.float32)
    if mutation == 'shape':
        archive['t__gains'] = np.ones(3, dtype=np.float32)
    if mutation == 'nan':
        archive['t__bridge_tail'][0, 0] = np.nan
    if mutation == 'count':
        archive['t__bridge_tail'][0, 5] = .5
    if mutation == 'excluded':
        archive['t__gains'][1] = .9
    if mutation == 'delta':
        archive['t__gain_delta'][0] = .1
    with pytest.raises(EvidenceInvalid):
        _bridge_reduction(archive, 't', before, row, np.array([True, False]), np.array([0, 1]), np.array([0, 4]), 500)


def test_replay_dictionary_requires_every_recorded_numerical_array():
    from bet36fly.reward_evidence import EvidenceInvalid, _verify_replay
    incomplete = {condition: {'original': {}, 'repeat': {}} for condition in ('frozen', 'untaught', 'home', 'away')}
    with pytest.raises(EvidenceInvalid, match='fingerprint'):
        _verify_replay(incomplete)


@pytest.mark.parametrize('complete', [True, False])
def test_partial_and_complete_declared_corruption_stay_invalid(tmp_path, complete):
    directory, summary = _write_summary(tmp_path, 'diag-corrupt', complete=complete, panel_kind='held-out')
    summary['artifacts'] = {'trials.npz': {'sha256': '0' * 64, 'bytes': 1}}
    (directory / 'summary.json').write_text(json.dumps(summary))
    panel = by_id(list_reward_evidence(tmp_path))[directory.name]
    assert panel['validation_status'] == 'invalid'
    assert panel['selection_status'] is None


def test_reconciliation_cache_rehashes_changed_bytes_and_missing_files(tmp_path, monkeypatch):
    import os
    import shutil
    import bet36fly.reward_evidence as evidence
    run_id = 'diag-rate-bridge-v1-maskgamma-de050d773763'
    source = ROOT / 'output/diagnostics' / run_id
    directory = tmp_path / 'output/diagnostics' / run_id
    directory.mkdir(parents=True)
    for name in ('summary.json', 'preregistration.json', 'recording-layout.json', 'replay-evidence.json'):
        shutil.copyfile(source / name, directory / name)
    # Read-only hardlink avoids copying 337 MB. Mutations below unlink first.
    os.link(source / 'trials.npz', directory / 'trials.npz')
    dest = tmp_path / 'docs/evidence/reward-mechanism-repair-2026-09-12'
    dest.mkdir(parents=True)
    for name in ('bridge-residual-attribution.json', f'panel-{run_id}.json'):
        shutil.copyfile(ROOT / 'docs/evidence/reward-mechanism-repair-2026-09-12' / name, dest / name)
    calls = []
    original = evidence._verify_bridge
    def count(*args):
        calls.append(1)
        return original(*args)
    monkeypatch.setattr(evidence, '_verify_bridge', count)
    assert by_id(list_reward_evidence(tmp_path))[run_id]['evidence_status'] == 'passed'
    assert by_id(list_reward_evidence(tmp_path))[run_id]['evidence_status'] == 'passed'
    assert len(calls) == 1
    (directory / 'trials.npz').unlink()
    assert by_id(list_reward_evidence(tmp_path))[run_id]['validation_status'] == 'invalid'
    (directory / 'trials.npz').write_bytes(b'changed')
    assert by_id(list_reward_evidence(tmp_path))[run_id]['validation_status'] == 'invalid'
    os.remove(directory / 'trials.npz')
    (directory / 'trials.npz').symlink_to(source / 'trials.npz')
    assert by_id(list_reward_evidence(tmp_path))[run_id]['validation_status'] == 'invalid'


def test_symlink_run_is_not_listed_or_read(tmp_path):
    from bet36fly.reward_evidence import read_reward_evidence
    outside = tmp_path / 'outside'
    outside.mkdir()
    base = tmp_path / 'output/diagnostics'
    base.mkdir(parents=True)
    (base / 'diag-linked').symlink_to(outside, target_is_directory=True)
    assert list_reward_evidence(tmp_path)['diagnostics'] == []
    with pytest.raises((ValueError, OSError)):
        read_reward_evidence(tmp_path, 'diag-linked')


@pytest.mark.parametrize('replacement', ['summary', 'lock'])
def test_read_to_snapshot_replacement_cannot_cache_stale_parsed_evidence(tmp_path, monkeypatch, replacement):
    import bet36fly.reward_evidence as evidence
    directory, summary = _write_summary(tmp_path, 'diag-racing')
    original = evidence._artifact_snapshot
    replaced = False
    def snapshot(root, path):
        nonlocal replaced
        if not replaced:
            replaced = True
            if replacement == 'summary':
                summary['all_passed'] = False
                (directory / 'summary.json').write_text(json.dumps(summary))
            else:
                p = tmp_path / 'docs/evidence/reward-mechanism-repair-2026-09-12/bridge-residual-attribution.json'
                p.parent.mkdir(parents=True)
                p.write_text(json.dumps({'runs': {'changed': {'run_id': directory.name}}}))
        return original(root, path)
    monkeypatch.setattr(evidence, '_artifact_snapshot', snapshot)
    entry = by_id(list_reward_evidence(tmp_path))[directory.name]
    if replacement == 'summary':
        assert entry['stored_verdict'] == 'failed'
    else:
        assert entry['validation_status'] == 'invalid'
    assert by_id(list_reward_evidence(tmp_path))[directory.name] == entry


def test_detail_rejects_a_summary_replacement_during_index_validation(tmp_path, monkeypatch):
    import bet36fly.reward_evidence as evidence
    directory, summary = _write_summary(tmp_path, 'diag-detail-race')
    original = evidence.list_reward_evidence
    def replace(root):
        summary['all_passed'] = False
        (directory / 'summary.json').write_text(json.dumps(summary))
        return original(root)
    monkeypatch.setattr(evidence, 'list_reward_evidence', replace)
    with pytest.raises(evidence.EvidenceInvalid, match='changed'):
        evidence.read_reward_evidence(tmp_path, directory.name)


@pytest.mark.parametrize('kind', ['outside', 'exact', 'cancelled_groups', 'wrong_mapping'])
def test_bridge_trial_endpoint_and_group_reconciliation_reject_hidden_changes(kind):
    import numpy as np
    from bet36fly.reward_evidence import EvidenceInvalid, _bridge_reduction
    before = np.ones(2, dtype=np.float32)
    gains = np.array([.375, 1.625] if kind == 'outside' else [.5, 1.5] if kind == 'exact' else [.875, 1.125], dtype=np.float32)
    groups = np.array([0, 2], dtype=np.int32)
    tail = np.zeros((8, 8))
    if kind == 'wrong_mapping':
        groups = np.array([1, 2], dtype=np.int32)
        tail[0, 4], tail[2, 4] = -.125, .125
    archive = {'t__gains': gains, 't__gain_delta': gains-before,
               't__bridge_rule': np.zeros((500, 8, 8)), 't__bridge_tail': tail}
    row = dict(applied=[0, 0], clipped=0, electrical_bound_observations=0, tail_bound_observations=0)
    with pytest.raises(EvidenceInvalid):
        _bridge_reduction(archive, 't', before, row, np.ones(2, dtype=bool), np.zeros(2, dtype=np.int32), groups, 500)


def test_bridge_zero_effect_and_correct_group_publication_are_valid():
    import numpy as np
    from bet36fly.reward_evidence import _bridge_reduction
    before = np.ones(2, dtype=np.float32)
    for changes in ([0, 0], [-.125, .125]):
        gains = before + np.array(changes, dtype=np.float32)
        tail = np.zeros((8, 8))
        tail[0, 4], tail[2, 4] = changes
        archive = {'t__gains': gains, 't__gain_delta': gains-before,
                   't__bridge_rule': np.zeros((500, 8, 8)), 't__bridge_tail': tail}
        row = dict(applied=[0, 0], clipped=0, electrical_bound_observations=0, tail_bound_observations=0)
        assert _bridge_reduction(archive, 't', before, row, np.ones(2, dtype=bool),
                                 np.zeros(2, dtype=np.int32), np.array([0, 2]), 500)[4] == 0


@pytest.mark.parametrize('original,heldout,expected', [('failed', 'passed', ['original']), ('passed', 'failed', ['heldout']), ('failed', 'failed', ['heldout', 'original'])])
def test_conditioning_blockers_name_only_failed_members(original, heldout, expected):
    from bet36fly.reward_evidence import _failed_pair_members
    entries = [{'run_id': 'original', 'evidence_status': original, 'validation_status': 'validated'},
               {'run_id': 'heldout', 'evidence_status': heldout, 'validation_status': 'validated'}]
    pairs = [{'original_run_id': 'original', 'heldout_run_id': 'heldout', 'validation_status': 'validated', 'evidence_status': 'failed'}]
    assert _failed_pair_members(entries, pairs) == expected
