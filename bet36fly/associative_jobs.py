"""Explicit training-job state, cancellation, deterministic resume and checkpoint inference.

One writer at a time: a process-wide lock plus a lock file under output/associative/jobs.
Jobs never touch the frozen sensory evidence, the v1 pointer or the legacy registries.
Inference loads an immutable checkpoint into a separate engine; it never updates gains.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import threading
import time
import traceback

import numpy as np

from .associative import atomic_json

STATES = ('queued', 'running', 'completed', 'failed', 'cancelled', 'budget_stopped')


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return default


class JobManager:
    """Filesystem-backed registry of associative training jobs."""

    def __init__(self, root):
        self.root = Path(root)
        self.directory = self.root / 'output/associative/jobs'
        self.lock = threading.Lock()
        self.running = None
        self.thread = None

    # ---- registry -------------------------------------------------------------------------
    def list(self):
        jobs = []
        if self.directory.exists():
            for path in sorted(self.directory.glob('*/manifest.json')):
                manifest = read_json(path)
                if isinstance(manifest, dict) and manifest.get('id') == path.parent.name:
                    jobs.append(self._summary(manifest))
        return sorted(jobs, key=lambda j: j['created_at'], reverse=True)

    def read(self, job_id):
        if not job_id.replace('-', '').replace('_', '').isalnum():
            raise LookupError('Invalid job identifier.')
        manifest = read_json(self.directory / job_id / 'manifest.json')
        if not isinstance(manifest, dict) or manifest.get('id') != job_id:
            raise LookupError('Unknown job.')
        return manifest

    @staticmethod
    def _summary(manifest):
        keys = ('id', 'kind', 'status', 'arm', 'learning_rate', 'protocol', 'created_at', 'updated_at', 'progress',
                'error', 'run_identity', 'resumed_from', 'checkpoints')
        return {k: manifest.get(k) for k in keys}

    def _write(self, manifest):
        manifest['updated_at'] = utcnow()
        atomic_json(self.directory / manifest['id'] / 'manifest.json', manifest)

    # ---- control --------------------------------------------------------------------------
    def start(self, *, protocol, arm, learning_rate=None, day_limit=None, resume=None):
        if arm not in ('plastic', 'frozen', 'shuffled'):
            raise ValueError('Unknown arm.')
        protocol_path = self.root / protocol
        if not protocol_path.is_relative_to(self.root / 'configs') or not protocol_path.is_file():
            raise ValueError('Protocol must be a file under configs/.')
        with self.lock:
            if self.running is not None:
                raise RuntimeError(f'Job {self.running} is already running; one training job at a time.')
            lock_file = self.directory / 'writer.lock'
            self.directory.mkdir(parents=True, exist_ok=True)
            if lock_file.exists():
                holder = read_json(lock_file, {})
                if isinstance(holder, dict) and holder.get('pid') and _pid_alive(holder['pid']):
                    raise RuntimeError('Another process holds the associative writer lock.')
                lock_file.unlink()
            payload = dict(protocol=protocol, arm=arm, learning_rate=learning_rate, day_limit=day_limit, resume=resume,
                           created=utcnow())
            job_id = 'job-' + hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
            if (self.directory / job_id).exists():
                job_id = job_id + '-' + hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:6]
            (self.directory / job_id).mkdir(parents=True)
            manifest = dict(id=job_id, kind='associative-sports-arm', status='queued', protocol=protocol, arm=arm,
                            learning_rate=learning_rate, day_limit=day_limit, created_at=utcnow(),
                            progress=dict(days=0, calls=0, reinforcements=0, cache_hits=0, cache_misses=0),
                            checkpoints=[], resumed_from=resume, error=None)
            self._write(manifest)
            atomic_json(lock_file, dict(pid=os.getpid(), job=job_id))
            self.running = job_id
            self.thread = threading.Thread(target=self._run, args=(manifest,), daemon=True, name=f'assoc-{job_id}')
            self.thread.start()
            return manifest

    def cancel(self, job_id):
        manifest = self.read(job_id)
        if manifest['status'] in ('queued', 'running'):
            (self.directory / job_id / 'cancel').write_text(utcnow())
            return dict(id=job_id, cancellation_requested=True)
        return dict(id=job_id, cancellation_requested=False, status=manifest['status'])

    def wait(self, timeout=None):
        if self.thread is not None:
            self.thread.join(timeout)
        return self.running is None

    # ---- execution ------------------------------------------------------------------------
    def _run(self, manifest):
        job_dir = self.directory / manifest['id']
        cancel_file = job_dir / 'cancel'
        try:
            manifest.update(status='running', started_at=utcnow())
            self._write(manifest)
            result = self._execute(manifest, job_dir, cancelled=cancel_file.exists)
            manifest.update(status='completed', result=result)
        except _Cancelled:
            manifest['status'] = 'cancelled'
        except _BudgetStopped as exc:
            manifest.update(status='budget_stopped', error=str(exc))
        except Exception as exc:  # noqa: BLE001 - any failure is recorded, never hidden
            manifest.update(status='failed', error=f'{type(exc).__name__}: {exc}', traceback=traceback.format_exc()[-4000:])
        finally:
            manifest['finished_at'] = utcnow()
            self._write(manifest)
            with self.lock:
                self.running = None
                lock_file = self.directory / 'writer.lock'
                if lock_file.exists():
                    lock_file.unlink()

    def _execute(self, manifest, job_dir, *, cancelled):
        """Runs one sports arm through the SeasonLearner; heavy imports happen here only."""
        from . import associative_sports as sp
        from .associative import build_circuit, load_checkpoint

        root = self.root
        protocol_path = root / manifest['protocol']
        raw = protocol_path.read_bytes()
        protocol = json.loads(raw)
        circuit_protocol = json.loads((root / protocol['circuit']).read_text())
        identity = 'associative-sports-' + hashlib.sha256(
            raw + f"|{manifest['arm']}|{manifest['learning_rate']!r}".encode()).hexdigest()[:20]
        out = root / 'output/associative' / identity
        resume = None
        if manifest.get('resumed_from'):
            previous = read_json(self.directory / manifest['resumed_from'] / 'manifest.json', {})
            if not previous or previous.get('run_identity') != identity:
                raise ValueError('Resume source is not a job of this exact protocol/arm/learning rate.')
            partial = read_json(out / 'rows.partial.json')
            if not partial or not partial['days']:
                raise ValueError('No completed day to resume from.')
            last_day = partial['days'][-1]['day']
            gains, meta = load_checkpoint(out / f"checkpoint-{manifest['arm']}-{last_day}.npz")
            resume = dict(after=last_day, gains=gains, rows=partial['rows'], days=partial['days'], meta=meta)
        elif out.exists():
            raise ValueError('Refusing an existing sports arm identity; resume the job that created it instead.')
        else:
            out.mkdir(parents=True)
            (out / 'protocol.json').write_bytes(raw)
        manifest['run_identity'] = identity
        self._write(manifest)
        candidate = sp.load_candidate(root, protocol)
        games = json.loads((root / protocol['games']).read_text())
        history = [g for g in games if g['season'] in protocol['history_seasons']]
        season = [g for g in games if g['season'] == protocol['season']]
        rows, x, y = sp.season_rows(history + season, protocol['season'])
        innate = sp.innate_features(x, candidate)
        circuit = build_circuit(root, circuit_protocol)
        permutation = None
        if manifest['arm'] == 'shuffled':
            permutation = sp.within_week_permutation([g['start_time'] for g in rows], protocol['shuffle_seed'])
        labels = np.where(y == 0, 1, 2)
        learner = sp.SeasonLearner(circuit, circuit_protocol, arm=manifest['arm'], games=rows, features=x, innate=innate,
                                   outcomes=labels, week_permutation=permutation, out_dir=out,
                                   learning_rate=manifest['learning_rate'])
        run_manifest = read_json(out / 'manifest.json', {}) or dict(identity=identity, arm=manifest['arm'],
                                                                    learning_rate=manifest['learning_rate'],
                                                                    season=protocol['season'], games=len(rows),
                                                                    anatomy=circuit['anatomy'], jobs=[])
        run_manifest.setdefault('jobs', []).append(manifest['id'])
        run_manifest['status'] = 'running'
        start = time.monotonic()

        def progress(state):
            manifest['progress'] = dict(days=len(state.days), calls=state.calls, reinforcements=state.reinforcements,
                                        cache_hits=state.cache.hits, cache_misses=state.cache.misses,
                                        last_day=state.days[-1]['day'] if state.days else None,
                                        gains_sha256=state.engine.gains_sha256())
            manifest['checkpoints'] = [dict(day=d['day'], gains_sha256=d['gains_sha256'],
                                            path=f"output/associative/{identity}/checkpoint-{manifest['arm']}-{d['day']}.npz")
                                       for d in state.days[-5:]]
            self._write(manifest)
            run_manifest.update(calls=state.calls, reinforcements=state.reinforcements, days=state.days,
                                cache=dict(hits=state.cache.hits, misses=state.cache.misses),
                                wall_seconds=time.monotonic() - start)
            atomic_json(out / 'manifest.json', run_manifest)
            if state.calls > protocol['call_cap_per_arm'] or time.monotonic() - start > protocol['wall_cap_seconds_per_arm']:
                raise _BudgetStopped('Declared per-arm budget exhausted.')

        atomic_json(out / 'manifest.json', run_manifest)

        def check_cancel():
            if cancelled():
                raise _Cancelled()
            return False

        try:
            learner.run(progress=progress, cancelled=check_cancel, day_limit=manifest.get('day_limit'),
                        **({} if resume is None else dict(resume_after=resume['after'], resume_gains=resume['gains'],
                                                          resume_rows=resume['rows'], resume_days=resume['days'])))
            atomic_json(out / 'rows.json', learner.rows)
            run_manifest.update(status='completed', rows_sha256=hashlib.sha256((out / 'rows.json').read_bytes()).hexdigest(),
                                final_gains_sha256=learner.engine.gains_sha256())
        except _Cancelled:
            run_manifest['status'] = 'cancelled'
            raise
        except _BudgetStopped as exc:
            run_manifest.update(status='budget_stopped', error=str(exc))
            raise
        except Exception as exc:
            run_manifest.update(status='failed', error=f'{type(exc).__name__}: {exc}')
            raise
        finally:
            run_manifest['wall_seconds'] = time.monotonic() - start
            atomic_json(out / 'manifest.json', run_manifest)
        return dict(run_identity=identity, rows=len(learner.rows), calls=learner.calls,
                    final_gains_sha256=learner.engine.gains_sha256())


class _Cancelled(Exception):
    pass


class _BudgetStopped(Exception):
    pass


def _pid_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


class CheckpointInference:
    """Probe two team cues against one immutable checkpoint. Never learns, never consumes outcomes."""

    def __init__(self, root):
        self.root = Path(root)
        self.lock = threading.Lock()
        self.circuit = None
        self.circuit_protocol_path = None

    def _circuit(self, circuit_protocol_path):
        from .associative import build_circuit
        if self.circuit is None or self.circuit_protocol_path != circuit_protocol_path:
            self.circuit = build_circuit(self.root, json.loads((self.root / circuit_protocol_path).read_text()))
            self.circuit_protocol_path = circuit_protocol_path
        return self.circuit

    def predict(self, *, checkpoint, home, away, circuit_protocol='configs/associative-circuit-01.json',
                readout=None):
        from .associative import load_checkpoint, odor_schedule, team_odor_types
        path = (self.root / checkpoint).resolve()
        if not path.is_relative_to((self.root / 'output/associative').resolve()) or path.suffix != '.npz':
            raise ValueError('Checkpoint must be an .npz file under output/associative.')
        gains, meta = load_checkpoint(path)
        with self.lock:
            circuit = self._circuit(circuit_protocol)
            engine = circuit['engine']
            protocol = json.loads((self.root / circuit_protocol).read_text())
            engine.set_gains(gains)
            timing = protocol['timing']
            sample = np.unique(np.concatenate(circuit['outputs']))
            positions = [np.searchsorted(sample, o) for o in circuit['outputs']]
            responses = {}
            for side, key in (('home', home), ('away', away)):
                odor = team_odor_types(key, circuit['orn_types'], protocol['odor_code']['width'], protocol['odor_code']['salt'])
                rates = odor_schedule(circuit, odor, bins=timing['probe_bins'], start_bin=timing['cue_bins'][0],
                                      end_bin=timing['cue_bins'][1], hz=protocol['odor_code']['hz'])
                result = engine.run(rates, bin_ms=timing['bin_ms'], seed=3001, sample=sample)
                if result['gains_sha256_after'] != meta['gains_sha256']:
                    raise RuntimeError('Inference changed gains.')
                window = result['trace'][timing['cue_bins'][0]:timing['cue_bins'][1]]
                responses[side] = dict(team=key, odor_types=odor, response=[int(window[:, p].sum()) for p in positions],
                                       tail_spikes=int(result['population'][-5:].sum()), wall_seconds=result['wall_seconds'])
            learned = [float(np.log1p(h) - np.log1p(a)) for h, a in zip(responses['home']['response'], responses['away']['response'])]
            probability = None
            if readout is not None:
                z = np.asarray(readout['innate'] + learned, float)
                from scipy.special import expit
                probability = float(expit(z / np.asarray(readout['scales']) @ np.asarray(readout['coef'])))
            return dict(checkpoint=str(path.relative_to(self.root)), checkpoint_meta=meta, home=responses['home'],
                        away=responses['away'], learned_differences=learned, plasticity=False, outcomes_consumed=False,
                        gains_sha256=meta['gains_sha256'], probability_home=probability,
                        note='Learned MBON05/MBON01 differences from one immutable checkpoint; a probability requires a '
                             'fitted arm readout plus the frozen innate features and is only returned when supplied.')
