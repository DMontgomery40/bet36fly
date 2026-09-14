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
