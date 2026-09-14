"""Associative evidence/job/inference API: read-only truthfulness, job state, no learning at inference."""
import json
from pathlib import Path
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient

from bet36fly.associative_api import build_evidence
from bet36fly.associative_jobs import JobManager
from bet36fly.server import create_app, create_verification_app

ROOT = Path(__file__).resolve().parents[1]


def test_evidence_reads_stored_manifests_only_and_never_invents_passes(tmp_path):
    empty = build_evidence(tmp_path)
    assert empty['links'] == [] and empty['conditioning'] == [] and empty['sports'] == [] and empty['evaluations'] == []
    assert empty['mechanism_qualified'] is False and empty['contract']['exists'] is False
    run = tmp_path / 'output/associative/associative-conditioning-abc'
    run.mkdir(parents=True)
    (run / 'manifest.json').write_text(json.dumps(dict(identity='associative-conditioning-abc', status='failed',
                                                       error='x', summary=dict(all_passed=False), calls=[], verdicts={})))
    broken = tmp_path / 'output/associative/associative-conditioning-broken'
    broken.mkdir()
    (broken / 'manifest.json').write_text('{not json')
    evidence = build_evidence(tmp_path)
    assert [c['identity'] for c in evidence['conditioning']] == ['associative-conditioning-abc', 'associative-conditioning-broken']
    assert evidence['conditioning'][0]['status'] == 'failed' and evidence['conditioning'][1]['valid'] is False
    assert evidence['mechanism_qualified'] is False
    (run / 'manifest.json').write_text(json.dumps(dict(identity='associative-conditioning-abc', status='completed',
                                                       summary=dict(all_passed=True), calls=[], verdicts={})))
    assert build_evidence(tmp_path)['qualified_conditioning'] == ['associative-conditioning-abc']


def test_verification_mode_serves_evidence_and_refuses_training_and_inference():
    with TestClient(create_verification_app(ROOT)) as client:
        evidence = client.get('/api/associative/evidence').json()
        assert evidence['contract']['exists'] and isinstance(evidence['conditioning'], list)
        assert client.get('/api/associative/jobs').json()['running'] is None
        assert client.get('/api/associative/checkpoints').status_code == 200
        for path, body in (('/api/associative/jobs', dict(arm='plastic')),
                           ('/api/associative/predict', dict(checkpoint='x.npz', home='mlb:1', away='mlb:2'))):
            assert client.post(path, json=body).status_code == 405


def test_job_manager_states_cancellation_and_single_writer(tmp_path, monkeypatch):
    manager = JobManager(tmp_path)
    (tmp_path / 'configs').mkdir()
    (tmp_path / 'configs/p.json').write_text('{}')
    events = []

    def fake_execute(manifest, job_dir, *, cancelled):
        for step in range(50):
            if cancelled():
                from bet36fly.associative_jobs import _Cancelled
                raise _Cancelled()
            manifest['progress']['days'] = step
            manager._write(manifest)
            events.append(step)
            time.sleep(0.02)
        return dict(done=True)

    monkeypatch.setattr(manager, '_execute', fake_execute)
    job = manager.start(protocol='configs/p.json', arm='plastic', learning_rate=1e-5)
    assert job['status'] in ('queued', 'running') and manager.running == job['id']
    with pytest.raises(RuntimeError):
        manager.start(protocol='configs/p.json', arm='frozen')
    time.sleep(0.1)
    assert manager.cancel(job['id'])['cancellation_requested'] is True
    assert manager.wait(5)
    final = manager.read(job['id'])
    assert final['status'] == 'cancelled' and final['progress']['days'] < 50
    assert manager.cancel(job['id'])['cancellation_requested'] is False
    assert manager.list()[0]['id'] == job['id']
    with pytest.raises(ValueError):
        manager.start(protocol='../etc/passwd', arm='plastic')
    with pytest.raises(LookupError):
        manager.read('nope')

    def failing(manifest, job_dir, *, cancelled):
        raise ValueError('boom')

    monkeypatch.setattr(manager, '_execute', failing)
    job = manager.start(protocol='configs/p.json', arm='frozen')
    manager.wait(5)
    assert manager.read(job['id'])['status'] == 'failed' and 'boom' in manager.read(job['id'])['error']


@pytest.mark.skipif(not list((ROOT / 'output/associative').glob('associative-conditioning-*/checkpoint-paired.npz')),
                    reason='needs a saved conditioning checkpoint')
def test_inference_against_an_immutable_checkpoint_never_changes_it():
    checkpoint = sorted((ROOT / 'output/associative').glob('associative-conditioning-*/checkpoint-paired.npz'))[0]
    before = checkpoint.read_bytes()
    with TestClient(create_app(ROOT, warm_on_start=False)) as client:
        body = dict(checkpoint=str(checkpoint.relative_to(ROOT)), home='mlb:147', away='mlb:121')
        first = client.post('/api/associative/predict', json=body)
        assert first.status_code == 200, first.text
        payload = first.json()
        assert payload['plasticity'] is False and payload['outcomes_consumed'] is False
        assert payload['gains_sha256'] == payload['checkpoint_meta']['gains_sha256']
        assert len(payload['learned_differences']) == 2 and payload['probability_home'] is None
        second = client.post('/api/associative/predict', json=body).json()
        assert second['home']['response'] == payload['home']['response']
        assert client.post('/api/associative/predict', json=dict(body, checkpoint='configs/x.npz')).status_code == 422
    assert checkpoint.read_bytes() == before
    with np.load(checkpoint) as data:
        assert data['gains'].dtype == np.float32


def test_evidence_lists_reserved_block_confirmations_without_inventing_verdicts(tmp_path):
    run = tmp_path / 'output/associative/associative-confirmation-abc'
    run.mkdir(parents=True)
    (run / 'manifest.json').write_text(json.dumps(dict(
        identity='associative-confirmation-abc', status='failed_confirmation', season=2018, attempt=1,
        source_url='https://example/2018', source_sha256='ab' * 32, frozen_candidate_sha256='cd' * 32,
        arms=dict(plastic=dict(calls=1, reinforcements=1, final_gains_sha256='x', days=1, bound_contacts=0.0)),
        evaluation=dict(metrics=dict(plastic=dict(n=10, accuracy=.6, log_loss=.67, brier=.24)),
                        paired_loss=dict(frozen=dict(mean=.001, interval=[.0001, .002])),
                        shuffled_minus_frozen=dict(mean=.0, interval=[-.1, .1]), baseline_minus_frozen=None,
                        accuracy_interval=[.55, .65], plasticity_contributes=False, goal_passed=True,
                        start='2018-03-29T00:00:00Z', end='2018-10-01T00:00:00Z', exclusions=dict(unplayed=1)))))
    (run / 'predictions.csv').write_text('game_id\n')
    evidence = build_evidence(tmp_path)
    [entry] = evidence['confirmations']
    assert entry['status'] == 'failed_confirmation' and entry['plasticity_contributes'] is False
    assert entry['better_than_chance'] is True and entry['games'] == 10 and entry['attempt'] == 1
    assert entry['predictions_csv'] == 'output/associative/associative-confirmation-abc/predictions.csv'
    # A runtime failure or an unfinished attempt carries no verdict fields, never a fabricated one.
    (run / 'manifest.json').write_text(json.dumps(dict(identity='associative-confirmation-abc', status='failed_runtime',
                                                       error='network', season=2018, attempt=1)))
    [entry] = build_evidence(tmp_path)['confirmations']
    assert entry['plasticity_contributes'] is None and entry['better_than_chance'] is None and entry['error'] == 'network'
    # The real installation reports the single 2018 attempt as recorded.
    real = build_evidence(ROOT)['confirmations']
    if real:
        assert all(c['season'] == 2018 and c['attempt'] == 1 for c in real)
        assert all(c['plasticity_contributes'] in (True, False) for c in real if c['status'] != 'failed_runtime')
