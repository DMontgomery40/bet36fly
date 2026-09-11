import json
from types import SimpleNamespace
import numpy as np
import pytest

from bet36fly import experiment_v2 as v2
from bet36fly.experiment import atomic_json, fit_scale


def test_cache_identity_invalidates_every_simulator_input():
    x = np.zeros((2, 16), np.float32)
    args = dict(graph={'ids': 'a'}, gains=np.ones((2, 3)), seed=42, code={'brain': 'a'})
    first = v2.cache_identity(x, **args)
    for changed in ({'graph': {'ids': 'b'}}, {'gains': np.ones((2, 3)) * 1.1}, {'seed': 137},
                    {'layout': (0, 40, 80)}, {'code': {'brain': 'b'}}):
        assert first != v2.cache_identity(x, **dict(args, **changed))
    assert first != v2.cache_identity(x + 1, **args)


def test_simulation_cache_resumes_only_flushed_rows_and_verifies_hashes(tmp_path, monkeypatch):
    calls = []
    def simulate(brain, row, **kwargs):
        calls.append(int(row[0]))
        return dict(windows=np.ones((4, 3)) * row[0], kc_windows=np.ones((4, 2)), active=2, spikes=4)
    monkeypatch.setattr(v2, 'simulate_windows', simulate)
    brain = SimpleNamespace(output_dim=3, kc=np.arange(2))
    x = np.repeat(np.arange(4, dtype=np.float32)[:, None], 16, axis=1)
    args = dict(graph={'a': 'b'}, gains=np.ones((2, 2)), seed=42, include_kc=True, workers=1)
    result = v2.simulation_cache(brain, x, tmp_path, **args)
    assert calls == [0, 1, 2, 3]
    np.testing.assert_array_equal(result['windows'][:, 0, 0], x[:, 0])
    v2.simulation_cache(brain, x, tmp_path, **args)
    assert len(calls) == 4
    metadata = next(tmp_path.rglob('progress.json'))
    state = json.loads(metadata.read_text())
    state['completed'] = 2
    atomic_json(metadata, state)
    v2.simulation_cache(brain, x, tmp_path, **args)
    assert calls[-2:] == [2, 3]
    result['windows'][0] = 99
    result['windows'].flush()
    with pytest.raises(ValueError, match='hash mismatch'):
        v2.simulation_cache(brain, x, tmp_path, **args)


def test_partition_isolation_and_training_only_scaling(tmp_path):
    games = [dict(id=str(i), sport='soccer', start_time=date) for i, date in enumerate([
        '2025-06-01T00:00:00Z', '2025-06-02T00:00:00Z', '2025-07-01T00:00:00Z', '2026-01-01T00:00:00Z'])]
    atomic_json(tmp_path / 'training-games.json', {'games': games})
    x = np.repeat(np.array([1, 3, 1000, -1000], np.float32)[:, None], 16, axis=1)
    arrays = dict(X=x, y=np.array([0, 2, 1, 2]), sport=np.zeros(4, int),
                  train=np.array([1, 1, 0, 0], bool), validation=np.array([0, 0, 1, 0], bool),
                  test=np.array([0, 0, 0, 1], bool))
    np.savez(tmp_path / 'training-data.npz', **arrays)
    loaded, _, _, splits, _ = v2.load_source(tmp_path)
    mean, std = fit_scale(loaded[splits['train']])
    assert np.all(mean == 2) and np.all(std == 1)
    arrays['validation'][0] = True
    np.savez(tmp_path / 'training-data.npz', **arrays)
    with pytest.raises(ValueError, match='split differs'):
        v2.load_source(tmp_path)


def test_checkpoint_and_architecture_selection_ignore_benchmark_labels():
    rng = np.random.default_rng(21)
    candidates = [dict(plastic_epoch=e, selected_epoch=3, validation_loss=loss,
                       historical={'labels': [0, 1, 2], 'loss': -e}) for e, loss in [(16, .6), (4, .6)]]
    jobs = [dict(variant=variant, seed=s, status='complete', active_parameters=params,
                 validation_loss=loss, historical={'labels': [0, 1, 2]})
            for variant, params, loss in [('bio-shared-whole', 920, .6), ('bio-frozen-whole', 625, .6),
                                          ('bio-shared-temporal', 2780, .7)] for s in (42, 137, 2026)]
    for _ in range(12):
        for item in candidates + jobs:
            item['historical']['labels'] = rng.permutation([0, 1, 2]).tolist()
        assert v2.select_checkpoint(candidates)['plastic_epoch'] == 4
        assert v2.select_architecture(jobs) == 'bio-frozen-whole'


def test_paired_week_bootstrap_keeps_seeds_games_empty_weeks_and_sports():
    rows = []
    for sport in ('soccer', 'baseball'):
        for index, date in enumerate(('2026-01-05T12:00:00Z', '2026-01-26T12:00:00Z')):
            for seed in (42, 137, 2026):
                for name, p in [('bio-shared-temporal', [.8, 0, .2]), ('null-shared-temporal', [.4, 0, .6]),
                                ('feature-logistic', [.5, 0, .5])]:
                    rows.append(dict(game_id=f'{sport}{index}', sport=sport, start_time=date, seed=seed,
                                     probabilities=p, outcome=0, model=name, split='historical'))
    a = v2.paired_week_bootstrap(rows, replicates=100)
    assert a == v2.paired_week_bootstrap(rows, replicates=100)
    topology = [r for r in a['comparisons'] if r['right'].startswith('null')]
    assert len(topology) == 2
    for row in topology:
        assert row['n'] == 2 and row['calendar_weeks'] == 4 and row['empty_weeks'] == 2
        assert len(row['seed_differences']) == 3 and row['interval'][1] < 0
        assert row['difference'] == pytest.approx(-np.log(2))


@pytest.mark.parametrize('layout', ['whole', 'temporal'])
def test_candidate_round_trip_uses_full_windows_and_rejects_tampering(tmp_path, monkeypatch, layout):
    graph = tmp_path / 'graph'
    graph.mkdir()
    for name in v2.GRAPH_FILES:
        (graph / name).write_bytes(b'graph')
    monkeypatch.setattr(v2, 'FlyBrain', lambda *a, **k: SimpleNamespace(output_dim=3))
    windows = np.arange(12, dtype=np.float32).reshape(4, 3)
    calls = []
    def simulate(brain, features, **kwargs):
        calls.append((features.copy(), kwargs))
        return dict(windows=windows, whole=windows.mean(0))
    monkeypatch.setattr(v2, 'simulate_windows', simulate)
    dimension = 3 if layout == 'whole' else 12
    rng = np.random.default_rng(42)
    head = dict(weight=rng.normal(size=(2, 3, dimension)), bias=np.zeros((2, 3)), selected_epoch=4)
    path = v2.save_candidate(tmp_path / 'bundle', variant='bio-frozen-' + layout, seed=137,
        graph_path=graph, graph=v2.graph_hashes(graph), gains=np.ones((1, 2)), layout=layout,
        input_mean=np.ones(16), input_std=np.full(16, 2), output_mean=np.zeros(dimension),
        output_std=np.ones(dimension), head=head, protocol={'schema_version': 2})
    candidate = v2.load_candidate(path)
    for sport in (0, 1):
        x = np.zeros(16, np.float32)
        x[-1] = sport
        raw = windows.mean(0) if layout == 'whole' else windows.reshape(-1)
        expected = v2.probabilities(np.log1p(raw)[None], np.array([sport]), head['weight'], head['bias'])[0]
        np.testing.assert_allclose(candidate.predict_proba(x), expected)
        np.testing.assert_array_equal(calls[-1][0], (x - 1) / 2)
        assert calls[-1][1]['seed'] == 137
    (graph / 'signs.npy').write_bytes(b'changed')
    with pytest.raises(ValueError, match='changed'):
        v2.load_candidate(path)


def test_complete_plastic_job_exports_checkpoints_and_resumes_immutable_result(tmp_path, monkeypatch):
    import pandas as pd
    from scipy.sparse import csr_matrix
    from bet36fly.experiments import Registry
    class TinyBrain:
        def __init__(self, path, gains=None):
            self.path, self.output_dim = path, 3
            self.kc, self.mbon, self.ids = np.array([0, 1]), np.array([2]), np.array([10, 20, 30])
            self.nodes = pd.DataFrame({'bodyId': self.ids, 'type': ['KC', 'KCg', 'MBON']})
            self.plastic = csr_matrix([[1., 2.]])
            self.gains = np.ones((1, 2)) if gains is None else gains
    def simulate(brain, row, **kwargs):
        windows = np.tile(np.abs(row[:3]) * (1 + brain.gains.mean()), (4, 1)).astype(np.float32)
        windows *= np.arange(1, 5, dtype=np.float32)[:, None]
        return dict(windows=windows, whole=windows.mean(0), kc_windows=np.tile(np.abs(row[:2]), (4, 1)),
                    active=3, spikes=10)
    monkeypatch.setattr(v2, 'FlyBrain', TinyBrain)
    monkeypatch.setattr(v2, 'simulate_windows', simulate)
    monkeypatch.setattr(v2, 'graph_hashes', lambda path: {'test': 'graph'})
    protocol = json.loads(open('configs/experiment-v2.json').read())
    protocol.update(plastic_epochs=2, plastic_checkpoints=[1, 2], readout_epochs=4, workers=1)
    rng = np.random.default_rng(42)
    x = rng.normal(size=(48, 16)).astype(np.float32)
    sports = np.tile([0, 1], 24)
    x[:, -1] = sports
    y = rng.integers(0, 3, 48)
    y[(sports == 1) & (y == 1)] = 2
    splits = dict(train=np.arange(48) < 24, validation=(np.arange(48) >= 24) & (np.arange(48) < 36),
                  historical=np.arange(48) >= 36)
    games = [dict(id=str(i), sport='baseball' if sports[i] else 'soccer', start_time='2025-08-01T00:00:00Z')
             for i in range(48)]
    mean, std = fit_scale(x[splits['train']])
    initial_brain = TinyBrain(tmp_path)
    responses = [simulate(initial_brain, row) for row in v2.scale(x, mean, std)]
    initial = {key: np.array([r[key] for r in responses]) for key in ('windows', 'kc_windows', 'active', 'spikes')}
    job = dict(id='bio-shared-temporal-42', variant='bio-shared-temporal', seed=42, status='queued',
               active_parameters=77)
    registry = Registry(tmp_path / 'v2-small', {'id': 'v2-small', 'jobs': [job], 'artifacts': {}})
    args = (registry, job, protocol, x, y, sports, splits, games, initial, tmp_path, {'test': 'graph'}, mean, std)
    v2._fit_neural_job(*args)
    assert job['status'] == 'complete' and len(job['checkpoints']) == 2
    assert {c['plastic_epoch'] for c in job['checkpoints']} == {1, 2}
    directory = registry.directory / 'runs' / job['id']
    surrogate = json.loads((directory / 'surrogate.json').read_text())
    assert len(surrogate['checkpoints']) == 2
    assert (directory / 'surrogate-1.npz').exists()
    predictions = json.loads((directory / 'predictions.json').read_text())
    assert len(predictions) == 24
    first_hash = v2.digest(directory / 'result.json')
    y[splits['historical']] = 0  # Completed work is reused, never silently refitted against new benchmark labels.
    v2._fit_neural_job(*args)
    assert v2.digest(directory / 'result.json') == first_hash
    # Refit in a fresh registry with changed benchmark outcomes, rather than relying on cache reuse.
    revised_job = dict(id=job['id'], variant=job['variant'], seed=42, status='queued', active_parameters=77)
    revised = Registry(tmp_path / 'v2-revised-labels', {'id': 'v2-revised-labels', 'jobs': [revised_job], 'artifacts': {}})
    v2._fit_neural_job(revised, revised_job, *args[2:])
    assert revised_job['selected_plastic_epoch'] == job['selected_plastic_epoch']
    assert revised_job['selected_decoder_epoch'] == job['selected_decoder_epoch']
    assert revised_job['validation_loss'] == job['validation_loss']


def test_normal_resume_validates_completed_jobs_and_recovers_artifact_registration(tmp_path, monkeypatch):
    from bet36fly.experiments import Registry
    directory = tmp_path / 'experiment'
    run = directory / 'runs/bio-frozen-whole-42'
    (run / 'candidate').mkdir(parents=True)
    for name in ('predictions.json', 'candidate/bundle.json', 'candidate/parameters.npz'):
        (run / name).write_text('immutable bytes')
    saved = {'artifact_hashes': {name: v2.digest(run / name) for name in
                                ('predictions.json', 'candidate/bundle.json', 'candidate/parameters.npz')}}
    atomic_json(run / 'result.json', saved)
    job = {'id': 'bio-frozen-whole-42', 'status': 'running'}
    registry = Registry(directory, {'id': 'experiment', 'status': 'complete', 'jobs': [job], 'artifacts': {}})
    atomic_json(directory / 'report.json', {'id': 'experiment'})
    registry.artifact(directory / 'report.json')
    registry.save()
    protocol = tmp_path / 'protocol.json'
    atomic_json(protocol, dict(schema_version=2, duration_ms=80, window_ms=20))
    monkeypatch.setattr(v2, 'prepare_experiment', lambda *args: (registry, {}))
    assert v2.run_v2(protocol, root=tmp_path)['id'] == 'experiment'
    assert registry.manifest['jobs'][0]['status'] == 'complete'
    assert len(registry.manifest['artifacts']) == 5
    (run / 'candidate/parameters.npz').write_text('tampered')
    with pytest.raises(ValueError, match='artifact changed'):
        v2.run_v2(protocol, root=tmp_path)


def test_execution_revisions_preserve_freeze_and_enforce_training_compatibility(tmp_path):
    from bet36fly.experiments import Registry
    hashes = {p.name: v2.digest(p) for p in v2.Path(v2.__file__).parent.iterdir() if p.suffix in ('.py', '.cpp')}
    registry = Registry(tmp_path / 'v2-test', {'id': 'v2-test', 'status': 'running', 'jobs': [], 'code_hashes': hashes})
    before = dict(hashes)
    v2.record_execution(registry)
    assert registry.manifest['code_hashes'] == before
    record = registry.manifest['executions'][0]
    assert record['code_hashes'] == before and (registry.directory / 'executions' / record['id'] / 'code/experiment_v2.py').exists()
    registry.manifest['code_hashes']['learning.py'] = 'incompatible'
    with pytest.raises(ValueError, match='incompatible'):
        v2.record_execution(registry)


def test_resume_skips_cancelled_graphs_and_jobs_but_runs_remaining_work(tmp_path, monkeypatch):
    from bet36fly.experiments import Registry
    jobs = [dict(id=f'{variant}-{seed}', variant=variant, seed=seed,
                 status='cancelled' if 'temporal' in variant else 'complete' if seed != 2026 else 'queued')
            for seed in (42, 137, 2026) for variant in v2.VARIANTS]
    registry = Registry(tmp_path / 'v2-test', {'id': 'v2-test', 'status': 'running', 'jobs': jobs})
    protocol = tmp_path / 'protocol.json'
    atomic_json(protocol, dict(schema_version=2, duration_ms=80, window_ms=20, seeds=[42, 137, 2026], workers=1))
    monkeypatch.setattr(v2, 'prepare_experiment', lambda *args: (registry, {}))
    monkeypatch.setattr(v2, 'verify_completed_jobs', lambda *args: None)
    monkeypatch.setattr(v2, 'record_execution', lambda r: setattr(r, 'execution_id', 'test'))
    monkeypatch.setattr(v2, 'load_source', lambda *args: (np.zeros((2, 16)), None, None,
                                                       {'train': np.ones(2, bool)}, []))
    monkeypatch.setattr(v2, 'fit_baselines', lambda *args: ({}, {}))
    monkeypatch.setattr(v2, 'FlyBrain', lambda path: SimpleNamespace(plastic=np.ones((2, 2))))
    monkeypatch.setattr(v2, 'simulation_cache', lambda *args, **kwargs: {})
    fitted = []
    def fit(registry, job, *args):
        fitted.append(job['id'])
        registry.update(job, status='complete')
    monkeypatch.setattr(v2, '_fit_neural_job', fit)
    monkeypatch.setattr(v2, 'finalize', lambda *args: {'fitted': fitted})
    assert v2.run_v2(protocol, root=tmp_path)['fitted'] == [
        'bio-frozen-whole-2026', 'bio-independent-whole-2026', 'bio-shared-whole-2026']
    assert sum(j['status'] == 'cancelled' for j in jobs) == 15


def test_curtailed_finalization_selects_complete_architectures_and_reports_cancellations(tmp_path):
    from bet36fly.experiments import Registry
    jobs, baseline = [], []
    directory = tmp_path / 'output/experiments/v2-small'
    for seed in (42, 137, 2026):
        job = dict(id=f'bio-frozen-whole-{seed}', variant='bio-frozen-whole', seed=seed,
                   status='complete', validation_loss=.5, active_parameters=625)
        run = directory / 'runs' / job['id']
        candidate = run / 'candidate'
        candidate.mkdir(parents=True)
        (candidate / 'bundle.json').write_text('{}')
        (candidate / 'parameters.npz').write_bytes(b'test')
        job['bundle'] = str(candidate / 'bundle.json')
        rows = [dict(model=job['variant'], seed=seed, split=split, sport=sport,
                     game_id=sport+split, start_time='2026-01-01T00:00:00Z', outcome=0,
                     probabilities=[.7, 0, .3]) for sport in ('soccer', 'baseball')
                for split in ('validation', 'historical')]
        atomic_json(run / 'predictions.json', rows)
        baseline.extend(dict(row, model='feature-logistic', probabilities=[.6, 0, .4]) for row in rows)
        jobs.append(job)
    jobs.append(dict(id='bio-shared-temporal-42', variant='bio-shared-temporal', seed=42,
                     status='queued', validation_loss=.01, active_parameters=2780))
    registry = Registry(directory, dict(id='v2-small', status='running', jobs=jobs))
    protocol = dict(seeds=[42, 137, 2026], bootstrap_seed=42, bootstrap_replicates=20)
    with pytest.raises(ValueError, match='pending jobs'):
        v2.finalize(registry, protocol, baseline, tmp_path)
    registry.cancel_jobs(['bio-shared-temporal-42'], reason='User stopped temporal runs after results.')
    atomic_json(directory / 'baseline.json', {})
    report = v2.finalize(registry, protocol, baseline, tmp_path)
    assert report['selected_architecture'] == 'bio-frozen-whole'
    assert report['completion_scope'] == 'user-curtailed'
    assert report['original_matrix_complete'] is False
    assert len(report['cancelled_jobs']) == 1 and not report['failed_jobs']
    assert report['execution_amendments'][0]['after_observing_results']
    pointer = json.loads((tmp_path / 'output/v2-shadow.json').read_text())
    assert len(pointer['bundles']) == 3
