"""Local spectator API and built frontend, with no wagering/account endpoints."""
from __future__ import annotations

import json

from contextlib import asynccontextmanager
from pathlib import Path
import threading
from typing import Literal
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .connectome import ROOT
from .runtime import Runtime, read_json
from .ledger import ReadOnlyDatabaseError
from .experiments import list_experiments, read_experiment, resolve_artifact
from .conditioning_evidence import present_conditioning
from .reward_evidence import list_reward_evidence, read_reward_evidence


def follow_sources(runtime, stop, interval_seconds=900):
    """Warm real picks and keep public fixtures/results current while serving."""
    while not stop.is_set():
        try:
            if runtime.ensure_model():
                runtime.warm_picks()
                runtime.refresh()
                if stop.wait(interval_seconds):
                    return
                continue
        except Exception as exc:
            runtime.refresh_state = {'status': 'failed', 'message': str(exc)}
        stop.wait(10)


def create_app(root=ROOT, warm_on_start=True, *, read_only=False):
    root = Path(root)
    stop = threading.Event()
    runtime_lock = threading.Lock()

    def get_runtime():
        runtime = getattr(app.state, 'runtime', None)
        if runtime is None:
            with runtime_lock:
                runtime = getattr(app.state, 'runtime', None)
                if runtime is None:
                    runtime = Runtime(root, read_only=read_only)
                    app.state.runtime = runtime
        return runtime

    @asynccontextmanager
    async def lifespan(app):
        runtime = get_runtime()
        if warm_on_start and not read_only:
            threading.Thread(target=follow_sources, args=(runtime, stop), daemon=True,
                             name='public-source-followup').start()
        yield
        stop.set()

    app = FastAPI(title='BET36FLY', version='0.1.0', lifespan=lifespan)
    app.state.get_runtime = get_runtime
    app.state.verification_mode = read_only
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', 'testserver'])

    @app.exception_handler(ReadOnlyDatabaseError)
    async def read_only_database_unavailable(_request: Request, exc: ReadOnlyDatabaseError):
        return JSONResponse({'detail': str(exc)}, status_code=503)

    @app.middleware('http')
    async def local_mutations(request: Request, call_next):
        if read_only and request.method not in ('GET', 'HEAD', 'OPTIONS'):
            response = JSONResponse({'detail': 'Verification mode is read-only.'}, status_code=405)
            response.headers['Allow'] = 'GET, HEAD, OPTIONS'
        else:
            origin = request.headers.get('origin')
            if request.method not in ('GET', 'HEAD', 'OPTIONS') and origin:
                parsed = urlparse(origin)
                if parsed.scheme not in ('http', 'https') or parsed.netloc != request.headers.get('host'):
                    response = JSONResponse({'detail': 'Only this local app can request neural work.'}, status_code=403)
                else:
                    response = await call_next(request)
            else:
                response = await call_next(request)
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        if read_only:
            response.headers['X-BET36FLY-Verification'] = 'read-only'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.get('/api/status')
    def status():
        try:
            return get_runtime().status()
        except (ValueError, OSError) as exc:
            raise HTTPException(503, str(exc)) from exc

    @app.get('/api/games')
    def games(sport: Literal['all', 'soccer', 'baseball'] = 'all'):
        runtime = get_runtime()
        return {'games': runtime.games(sport), 'updated_at': runtime.snapshot['updated_at'],
                'sources': runtime.sources()}

    @app.get('/api/brain')
    def brain():
        try:
            return get_runtime().get_geometry()
        except FileNotFoundError as exc:
            raise HTTPException(503, 'Official connectome data has not been prepared yet.') from exc

    @app.post('/api/predict/{game_id}')
    def predict(game_id: str):
        try:
            return get_runtime().predict(game_id)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(503, str(exc)) from exc

    @app.get('/api/training')
    def training():
        try:
            return get_runtime().training_payload()
        except (ValueError, OSError) as exc:
            raise HTTPException(503, str(exc)) from exc

    @app.get('/api/experiments')
    def experiments():
        runtime = get_runtime()
        return {'experiments': [present_conditioning(root,m) for m in list_experiments(root / 'output/experiments')],
                'active_v1': read_json(root / 'output/current-model.json', None),
                'prospective': runtime.shadow.status()}

    @app.get('/api/experiments/{experiment_id}')
    def experiment_detail(experiment_id: str):
        try:
            runtime = get_runtime()
            return dict(present_conditioning(root,read_experiment(root / 'output/experiments', experiment_id)),
                        prospective=runtime.shadow.status())
        except (ValueError, OSError) as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.get('/api/experiments/{experiment_id}/artifacts/{artifact_id}')
    def experiment_artifact(experiment_id: str, artifact_id: str):
        try:
            path = resolve_artifact(root / 'output/experiments', experiment_id, artifact_id)
            return FileResponse(path, filename=path.name)
        except (ValueError, OSError) as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.get('/api/reward-diagnostics')
    def reward_diagnostics():
        return list_reward_evidence(root)

    @app.get('/api/reward-diagnostics/{run_id}')
    def reward_diagnostic(run_id: str):
        try:
            return read_reward_evidence(root, run_id)
        except (ValueError, FileNotFoundError, OSError, json.JSONDecodeError):
            raise HTTPException(404, 'Unknown diagnostic run.')

    @app.get('/api/ledger')
    def ledger():
        runtime = get_runtime()
        picks = runtime.ledger.all()
        return {'picks': picks, 'count': len(picks)}

    @app.get('/api/ledger/export')
    def export():
        runtime = get_runtime()
        return Response(runtime.ledger.export_csv(), media_type='text/csv',
                        headers={'Content-Disposition': 'attachment; filename="bet36fly-paper-picks.csv"'})

    @app.get('/api/desk')
    def desk(sport: Literal['all', 'soccer', 'baseball'] = 'all'):
        return get_runtime().desk(sport)

    @app.post('/api/refresh')
    def refresh():
        runtime = get_runtime()
        if not runtime.refresh():
            raise HTTPException(409, 'A fixture refresh is already running.')
        return {'status': 'running'}

    @app.get('/api/methods')
    def methods():
        card = root / 'docs/MODEL_CARD.md'
        return {'model_card': card.read_text() if card.exists() else 'Model card not installed.',
                'manifest': read_json(root / 'data/brain/manifest.json', {})}

    @app.get('/{path:path}')
    def frontend(path: str):
        if path == 'api' or path.startswith('api/'):
            raise HTTPException(404, 'Unknown API route.')
        dist = (root / 'web/dist').resolve()
        candidate = (dist / path).resolve()
        if candidate.is_relative_to(dist) and candidate.is_file():
            return FileResponse(candidate)
        index = dist / 'index.html'
        if index.exists():
            return FileResponse(index)
        return HTMLResponse('<h1>BET36FLY</h1><p>The real neural backend is running. '
                            'The spectator frontend has not been built yet.</p>', status_code=503)

    return app


def create_verification_app(root=ROOT):
    """Build the explicit read-only QA application without import-time work."""
    return create_app(root=root, warm_on_start=False, read_only=True)


app = create_app()
