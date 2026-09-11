from fastapi.testclient import TestClient

from bet36fly.server import create_app


def test_no_model_and_no_games_are_explicit(tmp_path):
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        state = client.get('/api/status').json()
        assert state['mode'] == 'paper' and not state['model_ready']
        assert client.get('/api/games').json()['games'] == []
        assert client.get('/api/training').json()['report'] is None
        assert client.post('/api/predict/missing').status_code == 503
        assert client.get('/api/games?sport=cricket').status_code == 422
        desk = client.get('/api/desk').json()
        assert desk['mode'] == 'forward_paper'
        assert desk['summary']['completed'] == 0 and desk['summary']['hit_rate'] is None
        assert client.get('/api/desk?sport=cricket').status_code == 422


def test_refresh_conflict_and_external_origin_are_rejected(tmp_path):
    app = create_app(root=tmp_path, warm_on_start=False)
    with TestClient(app) as client:
        app.state.runtime.refresh = lambda: False
        assert client.post('/api/refresh').status_code == 409
        assert client.post('/api/refresh', headers={'Origin': 'https://unrelated.example'}).status_code == 403


def test_ledger_export_is_real_csv_and_unknown_api_is_not_html(tmp_path):
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        response = client.get('/api/ledger/export')
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('text/csv')
        assert response.text.startswith('id,game_id,')
        assert client.get('/api/unknown').status_code == 404
        assert client.get('/api/ledger').json() == {'picks': [], 'count': 0}
