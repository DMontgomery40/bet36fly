"""Local spectator API and built frontend, with no wagering/account endpoints."""
from __future__ import annotations

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
from .experiments import list_experiments, read_experiment, resolve_artifact


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


def create_app(root=ROOT, warm_on_start=True):
    root = Path(root)
    runtime = Runtime(root)
    stop = threading.Event()

    @asynccontextmanager
    async def lifespan(app):
        if warm_on_start:
            threading.Thread(target=follow_sources, args=(runtime, stop), daemon=True,
                             name='public-source-followup').start()
        yield
        stop.set()

    app = FastAPI(title='BET36FLY', version='0.1.0', lifespan=lifespan)
    app.state.runtime = runtime
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', 'testserver'])

    @app.middleware('http')
    async def local_mutations(request: Request, call_next):
        origin = request.headers.get('origin')
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and origin:
            parsed = urlparse(origin)
            if parsed.scheme not in ('http', 'https') or parsed.netloc != request.headers.get('host'):
                return JSONResponse({'detail': 'Only this local app can request neural work.'}, status_code=403)
        response = await call_next(request)
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.get('/api/status')
    def status():
        try:
            return runtime.status()
        except (ValueError, OSError) as exc:
            raise HTTPException(503, str(exc)) from exc

    @app.get('/api/games')
    def games(sport: Literal['all', 'soccer', 'baseball'] = 'all'):
        return {'games': runtime.games(sport), 'updated_at': runtime.snapshot['updated_at'],
                'sources': runtime.sources()}

    @app.get('/api/brain')
    def brain():
        try:
            return runtime.get_geometry()
        except FileNotFoundError as exc:
            raise HTTPException(503, 'Official connectome data has not been prepared yet.') from exc

    @app.post('/api/predict/{game_id}')
    def predict(game_id: str):
        try:
            return runtime.predict(game_id)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(503, str(exc)) from exc

    @app.get('/api/training')
    def training():
        runtime.ensure_model()
        return {'progress': read_json(root / 'output/training-progress.json',
                                      {'status': 'not_started', 'stage': 'not_started'}),
                'report': runtime.report}

    @app.get('/api/experiments')
    def experiments():
        return {'experiments': list_experiments(root / 'output/experiments'),
                'active_v1': read_json(root / 'output/current-model.json', None),
                'prospective': runtime.shadow.status()}

    @app.get('/api/experiments/{experiment_id}')
    def experiment_detail(experiment_id: str):
        try:
            return dict(read_experiment(root / 'output/experiments', experiment_id),
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

    @app.get('/api/ledger')
    def ledger():
        picks = runtime.ledger.all()
        return {'picks': picks, 'count': len(picks)}

    @app.get('/api/ledger/export')
    def export():
        return Response(runtime.ledger.export_csv(), media_type='text/csv',
                        headers={'Content-Disposition': 'attachment; filename="bet36fly-paper-picks.csv"'})

    @app.get('/api/desk')
    def desk(sport: Literal['all', 'soccer', 'baseball'] = 'all'):
        return runtime.desk(sport)

    @app.post('/api/refresh')
    def refresh():
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


app = create_app()
