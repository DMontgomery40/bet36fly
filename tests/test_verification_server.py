from __future__ import annotations

import os
from pathlib import Path
import hashlib
import json
import sqlite3
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]


def _inventory(path: Path) -> list[str]:
    return sorted(str(item.relative_to(path)) for item in path.rglob('*'))


def _fingerprints(path: Path) -> dict[str, str]:
    return {
        str(item.relative_to(path)): hashlib.sha256(item.read_bytes()).hexdigest()
        for item in path.rglob('*') if item.is_file()
    }


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def _record() -> dict:
    return {
        'game_id': 'g1', 'run_id': 'stored-run', 'feature_hash': hashlib.sha256(bytes(64)).hexdigest(),
        'model_hash': 'model-sha', 'sport': 'soccer', 'home': 'Home', 'away': 'Away',
        'start_time': '2099-09-20T12:00:00Z', 'created_at': '2026-09-10T12:00:00Z',
        'pick': 'home', 'pick_label': 'Home', 'probabilities': {'home': .5, 'draw': .2, 'away': .3},
        'confidence': .5, 'fair_odds': 2., 'source_url': 'https://example.com/game',
        'source_fetched_at': '2026-09-10T12:00:00Z',
    }


def _verification_root(root: Path, *, ledger=True, shadow=True) -> dict:
    report = {'run_id': 'stored-run', 'measured': True, 'limitations': ['stored evidence']}
    _write_json(root / 'output/report.json', report)
    _write_json(root / 'output/current-model.json', {
        'run_id': 'stored-run', 'checkpoint': str(root / 'output/checkpoint.npz'),
        'checkpoint_sha256': 'not-loaded', 'report': str(root / 'output/report.json'),
    })
    _write_json(root / 'output/training-progress.json', {'status': 'complete', 'stage': 'stored'})
    _write_json(root / 'data/brain/manifest.json', {'stats': {'neurons': 166700, 'edges': 25280000}})
    _write_json(root / 'data/sports/games.json', {'games': [], 'sources': [], 'updated_at': '2026-09-12T00:00:00Z'})
    if ledger:
        from bet36fly.ledger import PickLedger
        PickLedger(root / 'data/picks.sqlite3').add(_record())
    if shadow:
        from bet36fly.shadow import ShadowLedger
        ShadowLedger(root / 'data/v2-shadow.sqlite3')
    return report


def test_server_import_and_verification_factory_are_side_effect_free(tmp_path):
    before = _inventory(tmp_path)
    program = r'''
import sqlite3
import sys
import threading
from pathlib import Path

import bet36fly.runtime as runtime_module

def forbidden(*args, **kwargs):
    raise AssertionError('startup side effect')

class ForbiddenRuntime:
    def __init__(self, *args, **kwargs):
        forbidden()

runtime_module.Runtime = ForbiddenRuntime
sqlite3.connect = forbidden
threading.Thread.start = forbidden

import bet36fly.server as server

app = server.create_verification_app(root=Path(sys.argv[1]))
assert 'runtime' not in app.state._state
assert callable(app.state.get_runtime)
'''
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run(
        [sys.executable, '-B', '-c', program, str(tmp_path)],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert _inventory(tmp_path) == before


def test_fresh_process_verification_lifespan_and_gets_leave_root_unchanged(tmp_path):
    before = _inventory(tmp_path)
    program = r'''
import sys
from pathlib import Path
from fastapi.testclient import TestClient
import bet36fly.runtime as runtime_module

class ForbiddenBrain:
    def __init__(self, *args, **kwargs):
        raise AssertionError('neural model loaded')

runtime_module.FlyBrain = ForbiddenBrain
import bet36fly.server as server
server.follow_sources = lambda *args: (_ for _ in ()).throw(AssertionError('sources followed'))

with TestClient(server.create_verification_app(root=Path(sys.argv[1]))) as client:
    assert client.get('/api/status').json()['verification_mode'] is True
    assert client.get('/api/training').json()['report'] is None
    assert client.get('/api/ledger').json() == {'picks': [], 'count': 0}
    assert client.post('/api/refresh').status_code == 405
'''
    result = subprocess.run(
        [sys.executable, '-B', '-c', program, str(tmp_path)],
        cwd=ROOT,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert _inventory(tmp_path) == before


def test_verification_lifespan_and_metadata_gets_are_read_only(tmp_path, monkeypatch):
    expected_report = _verification_root(tmp_path)
    from bet36fly import runtime as runtime_module
    from bet36fly import server as server_module

    class ForbiddenBrain:
        def __init__(self, *args, **kwargs):
            raise AssertionError('verification loaded the neural model')

    monkeypatch.setattr(runtime_module, 'FlyBrain', ForbiddenBrain)
    monkeypatch.setattr(server_module, 'follow_sources', lambda *args: pytest.fail('verification followed sources'))
    before_inventory, before_hashes = _inventory(tmp_path), _fingerprints(tmp_path)
    app = server_module.create_verification_app(root=tmp_path)
    assert 'runtime' not in app.state._state
    with TestClient(app) as client:
        runtime = app.state.runtime
        assert runtime.read_only is True
        status = client.get('/api/status')
        assert status.status_code == 200
        assert status.headers['X-BET36FLY-Verification'] == 'read-only'
        assert status.json()['verification_mode'] is True
        assert status.json()['model_ready'] is False
        assert status.json()['run_id'] is None
        assert status.json()['stored_run_id'] == 'stored-run'
        training = client.get('/api/training')
        assert training.json() == {
            'progress': {'status': 'complete', 'stage': 'stored'},
            'report': expected_report,
            'verification_mode': True,
            'evidence_mode': 'stored-metadata-only',
        }
        assert client.get('/api/ledger').json()['picks'][0]['game_id'] == 'g1'
        assert client.get('/api/ledger/export').text.startswith('id,game_id,')
        assert client.get('/api/games').json()['games'] == []
        assert client.get('/api/desk').status_code == 200
        assert client.get('/api/experiments').status_code == 200
        assert client.get('/api/reward-diagnostics').status_code == 200
        assert client.get('/api/methods').status_code == 200
        assert client.get('/api/brain').status_code == 503
    assert _inventory(tmp_path) == before_inventory
    assert _fingerprints(tmp_path) == before_hashes


@pytest.mark.parametrize('method', ['POST', 'PUT', 'PATCH', 'DELETE', 'TRACE', 'CONNECT'])
@pytest.mark.parametrize('path', ['/api/refresh', '/api/predict/g1', '/api/unknown', '/unknown'])
@pytest.mark.parametrize('origin', [None, 'http://testserver', 'https://unrelated.example'])
def test_verification_rejects_every_mutating_method_before_handlers(tmp_path, method, path, origin):
    from bet36fly.server import create_verification_app
    before = _inventory(tmp_path)
    app = create_verification_app(root=tmp_path)
    with TestClient(app) as client:
        runtime = app.state.runtime
        runtime.predict = lambda *args, **kwargs: pytest.fail('predict handler ran')
        runtime.refresh = lambda *args, **kwargs: pytest.fail('refresh handler ran')
        headers = {'Origin': origin} if origin else {}
        response = client.request(method, path, headers=headers, content=b'{bad json')
        assert response.status_code == 405
        assert response.json() == {'detail': 'Verification mode is read-only.'}
        assert response.headers['Allow'] == 'GET, HEAD, OPTIONS'
        assert response.headers['X-BET36FLY-Verification'] == 'read-only'
    assert _inventory(tmp_path) == before


def test_verification_missing_state_stays_missing_and_empty(tmp_path, monkeypatch):
    from bet36fly import ledger as ledger_module
    from bet36fly.server import create_verification_app
    before = _inventory(tmp_path)
    monkeypatch.setattr(ledger_module.sqlite3, 'connect', lambda *args, **kwargs: pytest.fail('missing DB connected'))
    with TestClient(create_verification_app(root=tmp_path)) as client:
        assert client.get('/api/ledger').json() == {'picks': [], 'count': 0}
        assert client.get('/api/ledger/export').text.startswith('id,game_id,')
        status = client.get('/api/status').json()
        assert status['stored_run_id'] is None and status['model_ready'] is False
        assert client.get('/api/training').json()['report'] is None
    assert _inventory(tmp_path) == before


@pytest.mark.parametrize('suffix', ['-journal', '-wal', '-shm'])
def test_read_only_ledger_rejects_sidecars_before_sqlite_open(tmp_path, monkeypatch, suffix):
    import bet36fly.ledger as ledger_module
    from bet36fly.ledger import PickLedger, ReadOnlyDatabaseError
    path = tmp_path / 'ledger #?.sqlite3'
    PickLedger(path)
    Path(str(path) + suffix).write_bytes(b'active')
    before = _fingerprints(tmp_path)
    monkeypatch.setattr(ledger_module.sqlite3, 'connect', lambda *args, **kwargs: pytest.fail('SQLite opened'))
    with pytest.raises(ReadOnlyDatabaseError, match='sidecars exist'):
        PickLedger(path, read_only=True).all()
    assert _fingerprints(tmp_path) == before


def test_read_only_ledger_rejects_corrupt_database_as_invalid_header(tmp_path):
    from bet36fly.ledger import PickLedger, ReadOnlyDatabaseError
    path = tmp_path / 'ledger.sqlite3'
    path.write_bytes(b'not a sqlite database')
    before = _fingerprints(tmp_path)
    with pytest.raises(ReadOnlyDatabaseError, match='invalid SQLite header'):
        PickLedger(path, read_only=True).all()
    assert _fingerprints(tmp_path) == before


def test_read_only_ledger_reads_rollback_database_with_uri_characters_and_blocks_add(tmp_path):
    from bet36fly.ledger import PickLedger, ReadOnlyDatabaseError
    path = tmp_path / 'folder with spaces' / 'ledger #?.sqlite3'
    writable = PickLedger(path)
    expected = writable.add(_record())
    before = _fingerprints(tmp_path)
    readonly = PickLedger(path, read_only=True)
    assert readonly.all() == [expected]
    assert readonly.latest('stored-run')['g1'] == expected
    assert expected['id'] in readonly.export_csv()
    with pytest.raises(ReadOnlyDatabaseError):
        readonly.add(_record())
    assert _fingerprints(tmp_path) == before


def test_read_only_ledger_rejects_symlinked_database(tmp_path):
    from bet36fly.ledger import PickLedger, ReadOnlyDatabaseError
    target = tmp_path / 'actual.sqlite3'
    PickLedger(target).add(_record())
    link = tmp_path / 'linked.sqlite3'
    link.symlink_to(target)
    before = _fingerprints(tmp_path)
    with pytest.raises(ReadOnlyDatabaseError, match='symbolic links'):
        PickLedger(link, read_only=True).all()
    assert _fingerprints(tmp_path) == before


@pytest.mark.parametrize('sidecar', [None, '-wal', '-shm'])
def test_read_only_ledger_rejects_valid_wal_header_with_or_without_sidecars(tmp_path, monkeypatch, sidecar):
    import bet36fly.ledger as ledger_module
    from bet36fly.ledger import PickLedger, ReadOnlyDatabaseError
    path = tmp_path / 'ledger.sqlite3'
    PickLedger(path)
    header = bytearray(path.read_bytes())
    header[18:20] = b'\x02\x02'
    path.write_bytes(header)
    if sidecar:
        Path(str(path) + sidecar).write_bytes(b'active')
    before = _fingerprints(tmp_path)
    monkeypatch.setattr(ledger_module.sqlite3, 'connect', lambda *args, **kwargs: pytest.fail('SQLite opened'))
    reason = 'sidecars exist' if sidecar else 'WAL-mode'
    with pytest.raises(ReadOnlyDatabaseError, match=reason):
        PickLedger(path, read_only=True).all()
    assert _fingerprints(tmp_path) == before


def test_verification_reads_existing_shadow_rows_without_loading_candidates(tmp_path):
    from bet36fly.shadow import ShadowLedger, model_identity
    from bet36fly.server import create_verification_app
    pointer = {
        'experiment_id': 'v2-test', 'variant': 'candidate', 'bundles': [{'seed': 1}],
        'baseline_sha256': 'baseline', 'activated_at': '2026-09-10T12:00:00+00:00',
    }
    _write_json(tmp_path / 'output/v2-shadow.json', pointer)
    ledger = ShadowLedger(tmp_path / 'data/v2-shadow.sqlite3')
    model = model_identity(pointer)
    row = {'id': 'saved-forecast', 'model': model, 'sport': 'soccer'}
    with ledger.connect() as db:
        db.execute('INSERT INTO forecasts VALUES (?,?,?,?)',
                   (row['id'], model, row['sport'], json.dumps(row)))
    before = _fingerprints(tmp_path)
    with TestClient(create_verification_app(root=tmp_path)) as client:
        prospective = client.get('/api/experiments').json()['prospective']
        assert prospective['status'] == 'active_shadow'
        assert prospective['forecasts'] == 1
        assert prospective['sports']['soccer']['eligible_completed'] == 0
    assert _fingerprints(tmp_path) == before


def test_verification_serves_stored_details_artifacts_and_frontend_without_changes(tmp_path):
    from bet36fly.experiments import Registry
    from bet36fly.server import create_verification_app
    registry = Registry(tmp_path / 'output/experiments/v2-safe', {'id': 'v2-safe', 'jobs': []})
    artifact = registry.directory / 'report.json'
    artifact.write_text('{"measured": true}')
    artifact_id = registry.artifact(artifact)
    registry.save()
    diagnostic = tmp_path / 'output/diagnostics/diag-safe'
    diagnostic.mkdir(parents=True)
    _write_json(diagnostic / 'summary.json', {
        'run_id': 'diag-safe', 'rule': 'candidate', 'criteria': {}, 'rows': [],
        'identity': {'protocol': {'dan_reference': 'none', 'away_plasticity_mask': 'gamma'}},
    })
    _write_json(diagnostic / 'attribution.json', {'run_id': 'diag-safe', 'stored': True})
    frontend = tmp_path / 'web/dist/index.html'
    frontend.parent.mkdir(parents=True)
    frontend.write_text('<h1>Stored frontend</h1>')
    before_inventory, before_hashes = _inventory(tmp_path), _fingerprints(tmp_path)
    with TestClient(create_verification_app(root=tmp_path)) as client:
        assert client.get('/api/experiments/v2-safe').json()['id'] == 'v2-safe'
        downloaded = client.get(f'/api/experiments/v2-safe/artifacts/{artifact_id}')
        assert downloaded.status_code == 200 and downloaded.json() == {'measured': True}
        detail = client.get('/api/reward-diagnostics/diag-safe').json()
        assert detail['summary']['run_id'] == 'diag-safe'
        assert detail['attribution'] == {'run_id': 'diag-safe', 'stored': True}
        assert client.get('/#training').text == '<h1>Stored frontend</h1>'
    assert _inventory(tmp_path) == before_inventory
    assert _fingerprints(tmp_path) == before_hashes


def test_read_only_shadow_and_runtime_mutators_fail_before_work(tmp_path):
    from bet36fly.ledger import ReadOnlyDatabaseError
    from bet36fly.runtime import Runtime
    from bet36fly.shadow import ShadowLedger
    before = _inventory(tmp_path)
    ledger = ShadowLedger(tmp_path / 'shadow.sqlite3', read_only=True)
    assert ledger.forecasts() == []
    with pytest.raises(ReadOnlyDatabaseError):
        ledger.capture({}, [], pointer={}, predict=None, baseline_predict=None, current_fixture=None)
    with pytest.raises(ReadOnlyDatabaseError):
        ledger.score([], model='model')
    runtime = Runtime(tmp_path, read_only=True)
    with pytest.raises(RuntimeError, match='read-only'):
        runtime.ensure_model()
    with pytest.raises(RuntimeError, match='read-only'):
        runtime.predict('g1')
    with pytest.raises(RuntimeError, match='read-only'):
        runtime.refresh()
    with pytest.raises(RuntimeError, match='read-only'):
        runtime.warm_picks()
    with pytest.raises(RuntimeError, match='read-only'):
        runtime.shadow.ensure()
    with pytest.raises(RuntimeError, match='read-only'):
        runtime.shadow.refresh(runtime)
    assert _inventory(tmp_path) == before


def test_verification_returns_unavailable_for_invalid_existing_ledger(tmp_path):
    from bet36fly.server import create_verification_app
    path = tmp_path / 'data/picks.sqlite3'
    path.parent.mkdir(parents=True)
    path.write_bytes(b'corrupt')
    before = _fingerprints(tmp_path)
    with TestClient(create_verification_app(root=tmp_path)) as client:
        response = client.get('/api/ledger')
        assert response.status_code == 503
        assert 'read-only ledger unavailable' in response.json()['detail'].lower()
    assert _fingerprints(tmp_path) == before


def test_verification_reports_invalid_stored_metadata_instead_of_loading_or_hiding_it(tmp_path):
    from bet36fly.server import create_verification_app
    outside = tmp_path.parent / 'outside-report.json'
    outside.write_text('{"secret": true}')
    _write_json(tmp_path / 'output/current-model.json', {'run_id': 'stored', 'report': str(outside)})
    before = _fingerprints(tmp_path)
    with TestClient(create_verification_app(root=tmp_path), raise_server_exceptions=False) as client:
        response = client.get('/api/training')
        assert response.status_code == 503
        assert response.headers['X-BET36FLY-Verification'] == 'read-only'
        assert response.json()['detail'] == 'Stored model report escapes the project root.'
    assert _fingerprints(tmp_path) == before


@pytest.mark.parametrize('pointer', [[], 'stored-run'])
@pytest.mark.parametrize('endpoint', ['/api/status', '/api/training'])
def test_verification_rejects_nonobject_current_model_pointer(tmp_path, pointer, endpoint):
    from bet36fly.server import create_verification_app
    _write_json(tmp_path / 'output/current-model.json', pointer)
    before = _fingerprints(tmp_path)
    with TestClient(create_verification_app(root=tmp_path), raise_server_exceptions=False) as client:
        response = client.get(endpoint)
        assert response.status_code == 503
        assert response.json()['detail'] == 'Stored current-model pointer has invalid shape.'
    assert _fingerprints(tmp_path) == before


def test_verification_rejects_nonobject_stored_report(tmp_path):
    from bet36fly.server import create_verification_app
    _write_json(tmp_path / 'output/report.json', ['not', 'a', 'report'])
    _write_json(tmp_path / 'output/current-model.json', {
        'run_id': 'stored-run', 'report': str(tmp_path / 'output/report.json'),
    })
    before = _fingerprints(tmp_path)
    with TestClient(create_verification_app(root=tmp_path), raise_server_exceptions=False) as client:
        response = client.get('/api/training')
        assert response.status_code == 503
        assert response.json()['detail'] == 'Stored training report has invalid shape.'
    assert _fingerprints(tmp_path) == before


@pytest.mark.parametrize('manifest', [[], {'stats': []}, {'stats': '166700 neurons'}])
def test_verification_rejects_invalid_brain_manifest_shape(tmp_path, manifest):
    from bet36fly.server import create_verification_app
    _write_json(tmp_path / 'data/brain/manifest.json', manifest)
    before = _fingerprints(tmp_path)
    with TestClient(create_verification_app(root=tmp_path), raise_server_exceptions=False) as client:
        response = client.get('/api/status')
        assert response.status_code == 503
        assert response.json()['detail'] == 'Stored brain manifest has invalid shape.'
    assert _fingerprints(tmp_path) == before


@pytest.mark.parametrize('database', ['picks.sqlite3', 'v2-shadow.sqlite3'])
def test_verification_rejects_valid_sqlite_with_wrong_schema(tmp_path, database):
    from bet36fly.server import create_verification_app
    path = tmp_path / 'data' / database
    path.parent.mkdir(parents=True)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE unrelated (value TEXT)')
    if database == 'v2-shadow.sqlite3':
        _write_json(tmp_path / 'output/v2-shadow.json', {
            'experiment_id': 'v2', 'variant': 'candidate', 'bundles': [],
            'baseline_sha256': 'baseline', 'activated_at': '2026-09-10T12:00:00+00:00',
        })
        endpoint = '/api/experiments'
    else:
        endpoint = '/api/ledger'
    before = _fingerprints(tmp_path)
    with TestClient(create_verification_app(root=tmp_path), raise_server_exceptions=False) as client:
        response = client.get(endpoint)
        assert response.status_code == 503
        assert 'unavailable' in response.json()['detail'].lower()
    assert _fingerprints(tmp_path) == before


def test_verification_factory_initializes_one_runtime_on_simultaneous_first_gets(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from bet36fly import server as server_module
    from bet36fly.runtime import Runtime
    created = []

    class CountingRuntime(Runtime):
        def __init__(self, *args, **kwargs):
            created.append(1)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(server_module, 'Runtime', CountingRuntime)
    app = server_module.create_verification_app(root=tmp_path)
    client = TestClient(app)
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(lambda _: client.get('/api/status'), range(24)))
    client.close()
    assert len(created) == 1
    assert all(response.status_code == 200 for response in responses)
    assert _inventory(tmp_path) == []


def test_separate_verification_lifespans_get_one_fresh_runtime_each(tmp_path, monkeypatch):
    from bet36fly import server as server_module
    from bet36fly.runtime import Runtime
    created = []

    class CountingRuntime(Runtime):
        def __init__(self, *args, **kwargs):
            created.append(self)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(server_module, 'Runtime', CountingRuntime)
    for _ in range(2):
        app = server_module.create_verification_app(root=tmp_path)
        with TestClient(app) as client:
            assert app.state.runtime is created[-1]
            assert client.get('/api/status').status_code == 200
    assert len(created) == 2
    assert created[0] is not created[1]
    assert _inventory(tmp_path) == []


def test_read_only_mode_overrides_conflicting_warm_flag(tmp_path, monkeypatch):
    from bet36fly import server as server_module
    monkeypatch.setattr(server_module, 'follow_sources', lambda *args: pytest.fail('read-only app followed sources'))
    with TestClient(server_module.create_app(root=tmp_path, warm_on_start=True, read_only=True)) as client:
        assert client.get('/api/status').json()['verification_mode'] is True
    assert _inventory(tmp_path) == []


def test_normal_app_still_starts_source_follower(tmp_path, monkeypatch):
    import threading
    from bet36fly import server as server_module
    called = threading.Event()
    monkeypatch.setattr(server_module, 'follow_sources', lambda *_args: called.set())
    with TestClient(server_module.create_app(root=tmp_path, warm_on_start=True)):
        assert called.wait(1)
