import json
import pytest
from bet36fly.experiment import atomic_json
from bet36fly.experiments import Registry, list_experiments, read_experiment, resolve_artifact, writer_lock


def test_atomic_resume_lock_and_json_error(tmp_path):
    with writer_lock(tmp_path):
        with pytest.raises(RuntimeError, match='already owns'):
            with writer_lock(tmp_path):
                pass
    registry = Registry(tmp_path / 'v2-test', {'id': 'v2-test', 'jobs': [{'status': 'running'}]})
    assert registry.manifest['jobs'][0]['status'] == 'queued'
    registry.update(registry.manifest['jobs'][0], status='failed', error=str(ValueError('invalid "value"\n')))
    assert read_experiment(tmp_path, 'v2-test')['jobs'][0]['error'] == 'invalid "value"\n'
    assert len(list_experiments(tmp_path)) == 1


def test_cancellation_preserves_completed_work_and_survives_idempotent_resume(tmp_path):
    jobs = [dict(id=status, status=status) for status in ('complete', 'running', 'queued', 'failed')]
    registry = Registry(tmp_path / 'v2-test', {'id': 'v2-test', 'jobs': jobs})
    registry.cancel_jobs([j['id'] for j in jobs], reason='User stopped temporal execution after seeing results.')
    saved = json.loads((registry.directory / 'manifest.json').read_text())
    assert saved['jobs'][0] == jobs[0]
    assert all(j['status'] == 'cancelled' for j in saved['jobs'][1:])
    assert saved['execution_amendments'][0]['job_ids'] == ['running', 'queued', 'failed']
    resumed = Registry(registry.directory)
    saved['updated_at'] = resumed.manifest['updated_at']
    resumed.cancel_jobs([j['id'] for j in jobs], reason='Same request')
    assert resumed.manifest == saved
    for ids, reason in [(['missing', 'complete'], 'Request'), (['complete'], '')]:
        with pytest.raises(ValueError):
            resumed.cancel_jobs(ids, reason=reason)
        assert resumed.manifest == saved


@pytest.mark.parametrize('identifier', ['../outside', '/absolute', 'a/b', '..', '', 'x\\y'])
def test_registry_rejects_path_traversal(tmp_path, identifier):
    with pytest.raises(ValueError):
        read_experiment(tmp_path, identifier)


def test_artifacts_require_manifest_allowlist_and_stay_inside_root(tmp_path):
    registry = Registry(tmp_path / 'v2-test', {'id': 'v2-test', 'jobs': []})
    report = registry.directory / 'report.json'
    atomic_json(report, {'real': True})
    key = registry.artifact(report)
    registry.save()
    assert resolve_artifact(tmp_path, 'v2-test', key) == report
    with pytest.raises(FileNotFoundError):
        resolve_artifact(tmp_path, 'v2-test', 'report')
    external = tmp_path / 'private.json'
    external.write_text('private')
    report.unlink()
    report.symlink_to(external)
    with pytest.raises(ValueError):
        resolve_artifact(tmp_path, 'v2-test', key)
    (tmp_path / 'escape').symlink_to(tmp_path.parent)
    with pytest.raises(ValueError):
        read_experiment(tmp_path, 'escape')
    assert json.loads((registry.directory / 'manifest.json').read_text())['artifacts'][key]['sha256']
