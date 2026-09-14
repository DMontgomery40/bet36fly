"""Frozen research delivery: all rows, corruption families, and no neural work."""
import hashlib
import json
from pathlib import Path
import shutil

import pytest
from fastapi.testclient import TestClient

from bet36fly.server import create_verification_app

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path('docs/evidence/sensory-backtest-goal-2026-09-13')


@pytest.fixture
def installed(tmp_path):
    for folder in [EVIDENCE, Path('configs')]:
        shutil.copytree(ROOT / folder, tmp_path / folder)
    return tmp_path


def test_real_confirmation_delivery_and_pagination():
    with TestClient(create_verification_app(ROOT)) as client:
        summary = client.get('/api/sensory/summary').json()
        assert summary['status'] == 'available'
        assert summary['identity'] == 'sensory-confirmation-4887cb8c17f6281d8166'
        assert summary['correct'] == 1362
        assert summary['evaluation']['metrics']['neural']['n'] == 2423
        ids = []
        for offset in range(0, 2423, 100):
            response = client.get('/api/sensory/games', params={'offset': offset, 'limit': 100})
            assert response.status_code == 200
            body = response.json()
            ids += [g['game_id'] for g in body['games']]
        assert len(ids) == len(set(ids)) == 2423
        detail = client.get('/api/sensory/games/' + ids[0]).json()
        assert detail['home']['contact_key'] == 9
        assert len(detail['home']['recruited_ids']) == 9
        assert detail['home']['requested_hz'] == 58.9
        assert detail['home']['outputs_hz'] == [0, 11 / 3, 6, 23 / 3]
        assert [c['body_id'] for c in detail['output_cells']] == [19480, 514625, 15321, 15734]
        for download in summary['downloads']:
            response = client.get(download['url'])
            assert response.status_code == 200
            assert hashlib.sha256(response.content).hexdigest() == download['sha256']
        assert client.get('/api/sensory/games/unknown').status_code == 404
        assert client.get('/api/sensory/downloads/unknown').status_code == 404


def test_filters_empty_dates_and_invalid_queries():
    with TestClient(create_verification_app(ROOT)) as client:
        filtered = client.get('/api/sensory/games?team=Atlanta%20Braves&start=2023-03-30&end=2023-03-30').json()
        assert filtered['total'] == 1
        assert filtered['summary']['n'] == 1
        assert filtered['summary']['accuracy'] == 1
        empty = client.get('/api/sensory/games?team=not-a-team').json()
        assert empty['games'] == [] and empty['summary']['accuracy'] is None
        for query in ['start=bad', 'start=2023-05-01&end=2023-04-01', 'limit=0', 'offset=-1']:
            assert client.get('/api/sensory/games?' + query).status_code == 422


@pytest.mark.parametrize('file', ['confirmation-predictions.csv', 'confirmation-manifest.json',
    'confirmation-evaluation.json', 'confirmation-integrity.json', 'frozen-candidate.json'])
@pytest.mark.parametrize('damage', ['missing', 'corrupt', 'symlink'])
def test_invalid_artifacts_never_serve_old_or_zero_results(installed, file, damage):
    target = installed / EVIDENCE / file
    if damage == 'missing':
        target.unlink()
    elif damage == 'corrupt':
        target.write_text('{}')
    else:
        target.unlink()
        target.symlink_to(ROOT / EVIDENCE / file)
    with TestClient(create_verification_app(installed)) as client:
        body = client.get('/api/sensory/summary').json()
        assert body['status'] in ['unavailable', 'invalid']
        assert 'evaluation' not in body
        assert client.get('/api/sensory/games').status_code == 503
        assert client.get('/api/sensory/downloads/predictions').status_code == 503


def test_changed_bytes_invalidate_previously_loaded_data(installed):
    with TestClient(create_verification_app(installed)) as client:
        assert client.get('/api/sensory/summary').json()['status'] == 'available'
        path = installed / EVIDENCE / 'confirmation-evaluation.json'
        value = json.loads(path.read_text())
        value['metrics']['neural']['accuracy'] = 1
        path.write_text(json.dumps(value))
        assert client.get('/api/sensory/summary').json()['status'] == 'invalid'


@pytest.mark.parametrize("read_only", [False, True])
def test_research_requests_do_not_construct_runtime_or_simulator(monkeypatch, read_only):
    import bet36fly.server as server
    monkeypatch.setattr(server, 'Runtime', lambda *a, **kw: pytest.fail('Legacy runtime constructed'))
    with TestClient(server.create_app(ROOT, warm_on_start=False, read_only=read_only)) as client:
        assert client.get('/api/sensory/summary').json()['status'] == 'available'
        assert client.get('/api/sensory/games').status_code == 200


def test_mounted_product_has_no_legacy_views_or_polling():
    import re
    source = (ROOT / 'web/src/App.tsx').read_text()
    assert not re.search(r'BrainView|DeskView|TrainingView|LedgerView|GamesView|pollExperiments|setInterval|/api/(status|games|brain|training|ledger|desk|experiments)', source)


@pytest.mark.parametrize('damage', ['empty', 'duplicate', 'nan', 'probability', 'bounds', 'key', 'response'])
def test_semantically_invalid_csv_is_rejected_even_with_consistent_file_hashes(installed, damage):
    import csv
    import io
    path = installed / EVIDENCE / 'confirmation-predictions.csv'
    rows = list(csv.DictReader(io.StringIO(path.read_text())))
    fields = list(rows[0])
    if damage == 'empty':
        rows = []
    elif damage == 'duplicate':
        rows[1] = rows[0].copy()
    elif damage == 'nan':
        rows[0]['home_quality'] = 'NaN'
    elif damage == 'probability':
        rows[0]['encoder_only'] = '1.1'
    elif damage == 'bounds':
        rows[0]['home_lo'] = '0.9'
    elif damage == 'key':
        rows[0]['home_contact_key'] = '8.5'
    else:
        rows[0]['neural_difference_0'] = '100'
    with path.open('w') as handle:
        writer = csv.DictWriter(handle, fields)
        writer.writeheader()
        writer.writerows(rows)
    manifest_path = installed / EVIDENCE / 'confirmation-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['artifact_sha256']['predictions.csv'] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    lock_path = installed / 'configs/sensory-application-lock.json'
    lock = json.loads(lock_path.read_text())
    for name in ['manifest', 'predictions']:
        item = lock['files'][name]
        item['sha256'] = hashlib.sha256((installed / item['path']).read_bytes()).hexdigest()
    lock_path.write_text(json.dumps(lock))
    with TestClient(create_verification_app(installed)) as client:
        assert client.get('/api/sensory/summary').json()['status'] == 'invalid'
        assert client.get('/api/sensory/games').status_code == 503
