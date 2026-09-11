"""Atomic experiment registry and allowlisted, read-only artifact resolution."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import re

from .experiment import atomic_json, utcnow

IDENTIFIER = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}$')


def safe_directory(root, experiment_id):
    root = Path(root).resolve()
    if not IDENTIFIER.fullmatch(experiment_id):
        raise ValueError('Invalid experiment identifier.')
    path = (root / experiment_id).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError('Experiment escapes registry.')
    return path


def read_experiment(root, experiment_id: str) -> dict:
    path = safe_directory(root, experiment_id)
    manifest = path / 'manifest.json'
    if not manifest.resolve().is_relative_to(path):
        raise ValueError('Manifest escapes experiment.')
    result = json.loads(manifest.read_text())
    if result.get('id') != experiment_id:
        raise ValueError('Registry identity mismatch.')
    return result


def list_experiments(root) -> list[dict]:
    root = Path(root)
    if not root.exists():
        return []
    result = []
    for child in sorted(root.iterdir(), reverse=True):
        if child.is_dir() and IDENTIFIER.fullmatch(child.name):
            try:
                result.append(read_experiment(root, child.name))
            except (ValueError, OSError):
                continue
    return result


def resolve_artifact(root, experiment_id, artifact_id):
    if not IDENTIFIER.fullmatch(artifact_id):
        raise ValueError('Invalid artifact identifier.')
    manifest = read_experiment(root, experiment_id)
    artifact = manifest.get('artifacts', {}).get(artifact_id)
    if artifact is None:
        raise FileNotFoundError('Artifact is not registered.')
    directory = safe_directory(root, experiment_id)
    path = (directory / artifact['path']).resolve()
    if not path.is_relative_to(directory) or not path.is_file():
        raise ValueError('Artifact escapes experiment or is unavailable.')
    return path


@contextmanager
def writer_lock(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.runner.lock').open('a+') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('An experiment runner already owns this registry.') from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


class Registry:
    def __init__(self, directory, initial=None):
        self.directory = Path(directory)
        path = self.directory / 'manifest.json'
        self.manifest = json.loads(path.read_text()) if path.exists() else initial
        if self.manifest is None:
            raise FileNotFoundError(path)
        for job in self.manifest['jobs']:
            if job['status'] == 'running':
                job.update(status='queued', interrupted=True, error='Interrupted; cached work can resume.')
        self.save()

    def save(self):
        self.manifest['updated_at'] = utcnow()
        atomic_json(self.directory / 'manifest.json', self.manifest)

    def artifact(self, path, *, label=None, job=None):
        path = Path(path).resolve()
        relative = str(path.relative_to(self.directory.resolve()))
        key = 'a-' + hashlib.sha256(relative.encode()).hexdigest()[:20]
        with path.open('rb') as stream:
            checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
        self.manifest.setdefault('artifacts', {})[key] = {
            'path': relative, 'label': label or path.name, 'sha256': checksum,
            'bytes': path.stat().st_size, 'job_id': job,
            'url': f'/api/experiments/{self.manifest["id"]}/artifacts/{key}',
        }
        return key

    def update(self, job, **fields):
        job.update(fields, updated_at=utcnow())
        self.save()

    def cancel_jobs(self, job_ids, *, reason):
        """Record an explicit execution amendment while holding the writer lock."""
        requested = set(job_ids)
        known = {job['id'] for job in self.manifest['jobs']}
        if not reason.strip() or requested - known:
            raise ValueError('Cancellation needs a reason and known job IDs.')
        jobs = [j for j in self.manifest['jobs'] if j['id'] in requested
                and j['status'] not in ('complete', 'cancelled')]
        if not jobs:
            return
        amendment = dict(recorded_at=utcnow(), reason=reason, job_ids=[j['id'] for j in jobs],
                         kind='user-requested-cancellation', after_observing_results=True)
        for job in jobs:
            job.update(status='cancelled', phase='cancelled-by-user', cancellation_reason=reason,
                       cancelled_at=amendment['recorded_at'], error=None)
        self.manifest.setdefault('execution_amendments', []).append(amendment)
        self.manifest['completion_scope'] = 'user-curtailed'
        self.save()
