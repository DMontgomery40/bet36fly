"""Read-only evidence plus explicit job control for the associative learning stage.

GET routes read stored manifests only; they never import the engine. Job start, cancel,
resume and checkpoint inference are refused in verification (read-only) mode.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .associative_jobs import CheckpointInference, JobManager, read_json

CONTRACT = 'docs/EXPERIMENT_ASSOCIATIVE.md'


def _manifests(root, prefix):
    base = Path(root) / 'output/associative'
    rows = []
    if base.exists():
        for path in sorted(base.glob(f'{prefix}*/manifest.json')):
            if path.is_symlink() or path.parent.is_symlink():
                continue
            manifest = read_json(path)
            rows.append(dict(identity=path.parent.name, valid=isinstance(manifest, dict)
                             and manifest.get('identity') == path.parent.name, manifest=manifest))
    return rows


def conditioning_summary(row):
    m = row['manifest'] if row['valid'] else {}
    verdicts = m.get('verdicts', {}) if isinstance(m, dict) else {}
    acquisition = verdicts.get('acquisition') or {}
    return dict(identity=row['identity'], valid=row['valid'], status=m.get('status'), error=m.get('error'),
                calls=len(m.get('calls', [])) if isinstance(m.get('calls'), list) else None,
                wall_seconds=m.get('wall_seconds'), odors=m.get('odors'),
                entry_gate=(m.get('entry_gate') or {}).get('checks'), entry_gate_passed=(m.get('entry_gate') or {}).get('passed'),
                summary=m.get('summary'), audit=m.get('audit'),
                acquisition=dict(all_passed=acquisition.get('all_passed'), criteria=acquisition.get('criteria'),
                                 readout=acquisition.get('readout'), null_arms=acquisition.get('null_arms'),
                                 null_response_scale=acquisition.get('null_response_scale'),
                                 null_gain_scale=acquisition.get('null_gain_scale'),
                                 arms={k: {f: v.get(f) for f in ('contrast', 'mean_contrast', 'a_edge_mean_gain_change',
                                                                 'b_edge_mean_gain_change', 'changed_edges',
                                                                 'max_abs_gain_change', 'bytes_identical_to_unit')}
                                       for k, v in (acquisition.get('arms') or {}).items()}),
                retention=verdicts.get('retention'), reversal={k: (verdicts.get('reversal') or {}).get(k)
                                                               for k in ('all_passed', 'criteria', 'contingency_swap_descriptive')},
                probes=m.get('probes'), protocol_sha256=_sha(Path(row['path']).with_name('protocol.json')) if row.get('path') else None)


def _sha(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def build_evidence(root):
    root = Path(root)
    links = [dict(identity=r['identity'], valid=r['valid'], status=(r['manifest'] or {}).get('status'),
                  checks=(r['manifest'] or {}).get('checks'),
                  links={k: {f: v.get(f) for f in ('total_spikes', 'kc_active', 'tail_spikes', 'dan_spikes_by_type',
                                                   'mbon_spikes_by_type', 'drive_events', 'dan_spikes')}
                         for k, v in ((r['manifest'] or {}).get('links') or {}).items() if k != 'odor_code'},
                  odor_code={k: v for k, v in (((r['manifest'] or {}).get('links') or {}).get('odor_code') or {}).items()
                             if k != 'rows'})
             for r in _manifests(root, 'associative-links-')]
    conditioning = []
    for r in _manifests(root, 'associative-conditioning-'):
        r['path'] = str(root / 'output/associative' / r['identity'] / 'manifest.json')
        conditioning.append(conditioning_summary(r))
    sports = []
    for r in _manifests(root, 'associative-sports-'):
        m = r['manifest'] or {}
        if r['identity'].startswith('associative-sports-evaluation-'):
            continue
        sports.append(dict(identity=r['identity'], valid=r['valid'], status=m.get('status'), arm=m.get('arm'),
                           learning_rate=m.get('learning_rate'), season=m.get('season'), games=m.get('games'),
                           calls=m.get('calls'), reinforcements=m.get('reinforcements'), days=len(m.get('days', [])),
                           wall_seconds=m.get('wall_seconds'), final_gains_sha256=m.get('final_gains_sha256'),
                           error=m.get('error'), jobs=m.get('jobs'),
                           checkpoints=sorted(p.name for p in (root / 'output/associative' / r['identity']).glob('checkpoint-*.npz'))))
    evaluations = []
    base = root / 'output/associative'
    if base.exists():
        for path in sorted(base.glob('associative-sports-evaluation-*/evaluation.json')):
            payload = read_json(path)
            valid = isinstance(payload, dict) and payload.get('identity') == path.parent.name
            evaluation = (payload or {}).get('evaluation') or {}
            evaluations.append(dict(identity=path.parent.name, valid=valid, arms=(payload or {}).get('arms'),
                                    season=(payload or {}).get('season'), readout_split=(payload or {}).get('readout_split'),
                                    training_games=(payload or {}).get('training_games'),
                                    evaluation_games=(payload or {}).get('evaluation_games'),
                                    metrics=evaluation.get('metrics'), paired_loss=evaluation.get('paired_loss'),
                                    shuffled_minus_frozen=evaluation.get('shuffled_minus_frozen'),
                                    accuracy_interval=evaluation.get('accuracy_interval'),
                                    plasticity_contributes=evaluation.get('plasticity_contributes'),
                                    goal_passed=evaluation.get('goal_passed'), readouts=(payload or {}).get('readouts'),
                                    predictions_csv=str(path.with_name('predictions.csv').relative_to(root))
                                    if path.with_name('predictions.csv').exists() else None))
    stress = []
    for r in _manifests(root, 'associative-stress-'):
        m = r['manifest'] or {}
        summary = m.get('summary') or {}
        stress.append(dict(identity=r['identity'], valid=r['valid'], status=m.get('status'), arm=m.get('arm'), rho=m.get('rho'),
                           calls=m.get('calls'), wall_seconds=m.get('wall_seconds'), error=m.get('error'),
                           lower_bound_occupancy=summary.get('lower_bound_occupancy'),
                           upper_bound_occupancy=summary.get('upper_bound_occupancy'), above_rest=summary.get('above_rest'),
                           total_recovery=summary.get('total_recovery'), total_bound_contacts=summary.get('total_bound_contacts'),
                           memory_by_cycle=summary.get('memory_by_cycle'), post_history=summary.get('post_history'),
                           occupancy=[{k: v for k, v in o.items() if k != 'gains_sha256'} for o in m.get('occupancy', [])]))
    contract = root / CONTRACT
    qualified = [c for c in conditioning if c['valid'] and (c.get('summary') or {}).get('all_passed') is True]
    return dict(contract=dict(path=CONTRACT, sha256=_sha(contract), exists=contract.exists()),
                circuit=dict(path='configs/associative-circuit-01.json', sha256=_sha(root / 'configs/associative-circuit-01.json')),
                links=links, conditioning=conditioning, sports=sports, evaluations=evaluations, stress=stress,
                mechanism_qualified=bool(qualified), qualified_conditioning=[c['identity'] for c in qualified],
                sensory_confirmation_unchanged='sensory-confirmation-4887cb8c17f6281d8166',
                note='Missing or failed evidence stays missing or failed here. Passing conditioning qualifies the '
                     'mechanism in this simulator only; sports usefulness is a separate evaluation entry.')


class StartJob(BaseModel):
    protocol: str = 'configs/associative-sports-01.json'
    arm: str
    learning_rate: float | None = None
    day_limit: int | None = None
    resume: str | None = None


class PredictRequest(BaseModel):
    checkpoint: str
    home: str
    away: str
    circuit_protocol: str = 'configs/associative-circuit-01.json'


def associative_router(root, *, read_only=False):
    router = APIRouter(prefix='/api/associative')
    manager = JobManager(root)
    inference = CheckpointInference(root)

    def writable():
        if read_only:
            raise HTTPException(405, 'Verification mode is read-only; training and inference are disabled.')

    @router.get('/evidence')
    def evidence():
        return build_evidence(root)

    @router.get('/jobs')
    def jobs():
        return dict(jobs=manager.list(), running=manager.running)

    @router.get('/jobs/{job_id}')
    def job(job_id: str):
        try:
            return manager.read(job_id)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc

    @router.post('/jobs')
    def start(request: StartJob):
        writable()
        try:
            return manager.start(protocol=request.protocol, arm=request.arm, learning_rate=request.learning_rate,
                                 day_limit=request.day_limit, resume=request.resume)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(409, str(exc)) from exc

    @router.post('/jobs/{job_id}/cancel')
    def cancel(job_id: str):
        writable()
        try:
            return manager.cancel(job_id)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc

    @router.get('/checkpoints')
    def checkpoints():
        base = Path(root) / 'output/associative'
        rows = []
        if base.exists():
            for path in sorted(base.glob('associative-*/checkpoint-*.npz')):
                rows.append(dict(path=str(path.relative_to(root)), run=path.parent.name, name=path.name, bytes=path.stat().st_size))
        return dict(checkpoints=rows)

    @router.post('/predict')
    def predict(request: PredictRequest):
        writable()
        try:
            return inference.predict(checkpoint=request.checkpoint, home=request.home, away=request.away,
                                     circuit_protocol=request.circuit_protocol)
        except (ValueError, OSError) as exc:
            raise HTTPException(422, str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(500, str(exc)) from exc

    router.manager = manager
    router.inference = inference
    return router


__all__ = ['associative_router', 'build_evidence', 'JobManager', 'CheckpointInference', 'json']
