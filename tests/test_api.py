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


def test_experiment_registry_downloads_and_prospective_panel(tmp_path):
    from bet36fly.experiments import Registry
    registry = Registry(tmp_path / 'output/experiments/v2-test', {'id': 'v2-test', 'jobs': []})
    report = registry.directory / 'report.json'
    report.write_text('{"measured": true}')
    key = registry.artifact(report)
    registry.save()
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        index = client.get('/api/experiments').json()
        assert index['experiments'][0]['id'] == 'v2-test'
        assert index['prospective']['sports']['soccer']['threshold'] == 100
        assert index['prospective']['sports']['baseball']['threshold'] == 1000
        assert client.get('/api/experiments/v2-test').json()['jobs'] == []
        assert client.get(f'/api/experiments/v2-test/artifacts/{key}').json() == {'measured': True}
        assert client.get('/api/experiments/v2-test/artifacts/report').status_code == 404
        assert client.get('/api/experiments/missing').status_code == 404
        outside = tmp_path / 'outside'
        outside.write_text('secret')
        report.unlink()
        report.symlink_to(outside)
        assert client.get(f'/api/experiments/v2-test/artifacts/{key}').status_code == 404


def _diagnostic(root, run_id, *, rule, created_at, complete=True, passed=False, attribution=True):
    import json
    directory = root / 'output/diagnostics' / run_id
    directory.mkdir(parents=True)
    criteria = {
        'teaching_specific': {'passed': True, 'evaluations': {'home/base': {'mean_effect': -2.3, 'mean_untaught': -0.29, 'required_magnitude': .87, 'passed': True}}},
        'untaught_guard': {'passed': passed, 'evaluations': {'home/base': {'mean': -.289, 'sd': .32, 'limit': .16, 'passed': passed}}},
        'cross_compartment': {'passed': True, 'evaluations': {}}, 'no_bound_hits': {'passed': True, 'clipped_total': 0},
        'cumulative': {'passed': True, 'per_compartment': [], 'trajectory': []},
        'bit_identical_repeat': {'passed': True, 'by_condition': {}}, 'sensory_noise_invariance': {'passed': True, 'by_trial': {}},
    }
    summary = dict(run_id=run_id, rule=rule, created_at=created_at, panel_complete=complete, all_passed=complete and passed,
                   panel_note='frozen v1.1 panel' if complete else 'INCOMPLETE debug panel; not a gate result',
                   identity={'protocol': {'dan_reference': 'none' if rule == 'candidate' else 'tonic-baseline', 'away_plasticity_mask': 'all'}},
                   native_binary={'path': '/x/reward-lif-abc.dylib', 'sha256': 'ab' * 32}, source_unchanged_during_run=True,
                   anatomy={'plastic_edges': 8866, 'eligible_edges': 8866, 'group_labels': ['home/gamma'], 'group_edges': [1585]},
                   criteria=criteria, rows=[{'game': 4362, 'seed_set': 'base', 'condition': 'untaught', 'applied': [-.05, 0.]}] * 64)
    (directory / 'summary.json').write_text(json.dumps(summary))
    (directory / 'trials.npz').write_bytes(b'not served')
    if attribution:
        (directory / 'attribution.json').write_text(json.dumps({'run_id': run_id, 'mean_applied_by_phase': {'post_offset': -.127}}))
    return summary


def test_reward_diagnostics_are_listed_newest_first_and_served_read_only(tmp_path):
    _diagnostic(tmp_path, 'diag-legacy-1111aaaa', rule='legacy', created_at='2026-09-11T15:30:00+00:00')
    _diagnostic(tmp_path, 'diag-candidate-2222bbbb', rule='candidate', created_at='2026-09-11T15:50:00+00:00')
    _diagnostic(tmp_path, 'diag-candidate-3333cccc-INCOMPLETE', rule='candidate', created_at='2026-09-11T15:55:00+00:00', complete=False, attribution=False)
    early = _diagnostic(tmp_path, 'diag-legacy-0000eeee', rule='legacy', created_at='2026-09-11T15:20:00+00:00')
    import json as _json
    early_path = tmp_path / 'output/diagnostics/diag-legacy-0000eeee/summary.json'
    for key in ('panel_complete', 'panel_note', 'all_passed'):
        early.pop(key)
    early['identity']['protocol'] = {}                  # schema-3 base protocol: no reference or mask fields
    early_path.write_text(_json.dumps(early))
    bad = tmp_path / 'output/diagnostics/diag-broken'
    bad.mkdir()
    (bad / 'summary.json').write_text('{not json')
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        listing = client.get('/api/reward-diagnostics').json()
        assert [d['run_id'] for d in listing['diagnostics']] == ['diag-candidate-3333cccc-INCOMPLETE', 'diag-candidate-2222bbbb', 'diag-legacy-1111aaaa', 'diag-legacy-0000eeee']
        oldest = listing['diagnostics'][3]
        assert oldest['panel_complete'] is None and oldest['all_passed'] is False       # not recorded by that script version
        assert oldest['dan_reference'] == 'tonic-baseline' and oldest['away_plasticity_mask'] == 'all'   # implied by rule / absence
        assert listing['diagnostics'][2]['dan_reference'] == 'tonic-baseline'
        entry = listing['diagnostics'][1]
        assert entry['rule'] == 'candidate' and entry['dan_reference'] == 'none' and entry['away_plasticity_mask'] == 'all'
        assert entry['panel_complete'] is True and entry['all_passed'] is False and entry['has_attribution'] is True
        assert entry['criteria'] == {'teaching_specific': True, 'untaught_guard': False, 'cross_compartment': True, 'no_bound_hits': True,
                                     'cumulative': True, 'bit_identical_repeat': True, 'sensory_noise_invariance': True}
        assert entry['untaught_guard']['home/base'] == {'mean': -.289, 'sd': .32, 'limit': .16, 'passed': False}
        assert entry['teaching_specific']['home/base']['mean_effect'] == -2.3
        assert entry['native_binary_sha256'] == 'ab' * 32 and entry['source_unchanged_during_run'] is True
        assert 'rows' not in entry
        assert listing['diagnostics'][0]['panel_complete'] is False and listing['diagnostics'][0]['has_attribution'] is False
        assert listing['evidence_note'] == 'docs/evidence/reward-repair-phase1.md'
        full = client.get('/api/reward-diagnostics/diag-candidate-2222bbbb').json()
        assert len(full['summary']['rows']) == 64 and full['attribution']['mean_applied_by_phase']['post_offset'] == -.127
        assert client.get('/api/reward-diagnostics/diag-candidate-3333cccc-INCOMPLETE').json()['attribution'] is None
        assert client.get('/api/reward-diagnostics/diag-missing').status_code == 404
        assert client.get('/api/reward-diagnostics/diag-broken').status_code == 404
        assert client.get('/api/reward-diagnostics/..%2Fsecret').status_code in (404, 422)
        assert client.get('/api/reward-diagnostics/diag-candidate-2222bbbb/trials.npz').status_code == 404


def test_reward_diagnostics_empty_and_absent_directories_are_explicit(tmp_path):
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        assert client.get('/api/reward-diagnostics').json() == {'diagnostics': [], 'evidence_note': 'docs/evidence/reward-repair-phase1.md'}
    (tmp_path / 'output/diagnostics').mkdir(parents=True)
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        assert client.get('/api/reward-diagnostics').json()['diagnostics'] == []
