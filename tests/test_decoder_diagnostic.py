import json

import numpy as np
import pytest
from scipy.sparse import csr_matrix, save_npz

from bet36fly import decoder_diagnostic as diagnostic
from bet36fly.connectome import digest
from bet36fly.experiment import atomic_json, fit_scale, scale
from bet36fly.experiment_v2 import cache_identity, json_hash


def test_transform_order_window_order_and_training_only_scaling():
    windows = np.ones((8, 4, 124), np.float32)
    windows[:, 1] *= 9
    windows[:4, :, 0] *= np.arange(1, 5)[:, None]
    windows[4:, :, 0] = 1e20
    training = np.arange(8) < 4
    sports = np.tile([0, 1], 4)
    transformed = diagnostic.representations(windows)
    assert transformed['whole'].shape == (8, 124)
    assert transformed['temporal'].shape == (8, 496)
    np.testing.assert_allclose(transformed['whole'], np.log1p(windows.mean(1)))
    np.testing.assert_allclose(transformed['temporal'][:, 124:248], np.log1p(windows[:, 1]))
    assert not np.allclose(transformed['whole'], np.log1p(windows).mean(1))
    _, checks, scalers = diagnostic.scaled_representations(windows, training, sports)
    changed = windows.copy()
    changed[~training] *= 3
    _, _, revised = diagnostic.scaled_representations(changed, training, sports)
    for key in scalers:
        np.testing.assert_array_equal(scalers[key], revised[key])
    for representation in ('whole', 'temporal'):
        assert checks[representation]['train']['all']['clipped_fraction'] == 0
        assert checks[representation]['validation']['all']['clipped_fraction'] > 0
        assert checks[representation]['train']['all']['constant_channels'] > 0
    for bad in (windows[:, :3], np.full_like(windows, np.nan), -windows):
        with pytest.raises(ValueError):
            diagnostic.representations(bad)


@pytest.fixture
def frozen_cache(tmp_path, monkeypatch):
    experiment = tmp_path / 'experiment'
    source, graph = experiment / 'source', experiment / 'graphs/biological'
    (source / 'code').mkdir(parents=True)
    graph.mkdir(parents=True)
    for name in diagnostic.NEURAL_FILES:
        (source / 'code' / name).write_text('frozen simulator; never executed')
    rng = np.random.default_rng(42)
    n = 54
    sports = np.tile([0, 1], n // 2)
    x = rng.normal(size=(n, 16)).astype(np.float32)
    x[:, -1] = sports
    y = np.tile([0, 2, 1, 0, 2, 2], 9)
    masks = dict(train=np.arange(n) < 30, validation=(np.arange(n) >= 30) & (np.arange(n) < 42), test=np.arange(n) >= 42)
    games = [dict(id=str(i), sport='baseball' if sports[i] else 'soccer',
                  start_time=('2025-01-01' if i < 30 else '2025-08-01' if i < 42 else '2026-02-01') + 'T00:00:00Z') for i in range(n)]
    np.savez(source / 'training-data.npz', X=x, y=y, sport=sports, **masks)
    atomic_json(source / 'training-games.json', {'games': games})
    save_npz(graph / 'plastic.npz', csr_matrix(np.ones((2, 3), np.float32)))
    np.save(graph / 'kc.npy', np.arange(3))
    monkeypatch.setattr(diagnostic, 'graph_hashes', lambda path: {'fixture': 'graph'})
    protocol = {'schema_version': 2}
    atomic_json(experiment / 'protocol.json', protocol)
    manifest = dict(id='fixture', protocol=protocol, protocol_sha256=json_hash(protocol),
        source_hashes={name: digest(source / name) for name in ('training-data.npz', 'training-games.json')},
        graph_hashes={'fixture': 'graph'}, code_hashes={name: digest(source / 'code' / name) for name in diagnostic.NEURAL_FILES}, artifacts={})
    atomic_json(experiment / 'split-manifest.json', dict(source_hashes=manifest['source_hashes'],
        game_ids={('historical' if split == 'test' else split): [g['id'] for g, keep in zip(games, mask) if keep]
                  for split, mask in masks.items()}))
    mean, std = fit_scale(x[masks['train']])
    key = cache_identity(scale(x, mean, std), graph=manifest['graph_hashes'], gains=np.ones((2, 3), np.float32),
                         seed=42, code=manifest['code_hashes'])
    cache = experiment / 'cache' / key / 'initial'
    cache.mkdir(parents=True)
    arrays = dict(windows=rng.poisson(3, (n, 4, 124)).astype(np.float32),
                  kc_windows=np.zeros((n, 4, 3), np.float32), active=np.ones(n, np.int32), spikes=np.ones(n, np.int32))
    for name, a in arrays.items():
        np.save(cache / (name + '.npy'), a)
    atomic_json(cache / 'progress.json', dict(identity=key, completed=n, total=n,
        hashes={name: digest(cache / (name + '.npy')) for name in arrays}))
    baseline = []
    for model in ('bio-frozen-whole', 'bio-frozen-temporal', 'frequency-prior', 'feature-logistic'):
        rows = [dict(model=model, seed=42, split='validation', game_id=g['id'], sport=g['sport'],
                     outcome=int(y[i]), start_time=g['start_time'], probabilities=[.4, .2, .4] if sports[i] == 0 else [.5, 0, .5])
                for i, g in enumerate(games) if masks['validation'][i]]
        if model.startswith('bio-'):
            path = experiment / 'runs' / (model + '-42') / 'predictions.json'
            atomic_json(path, rows)
            manifest['artifacts'][model] = dict(path=str(path.relative_to(experiment)), sha256=digest(path))
        else:
            baseline.extend(rows)
    path = experiment / 'baseline-predictions.json'
    atomic_json(path, baseline)
    manifest['artifacts']['baselines'] = dict(path=path.name, sha256=digest(path))
    atomic_json(experiment / 'manifest.json', manifest)
    return experiment, cache


@pytest.mark.parametrize('fault', ['missing', 'incomplete', 'identity', 'array', 'row_order'])
def test_required_cache_fails_closed_without_simulating(frozen_cache, fault):
    experiment, cache = frozen_cache
    progress = cache / 'progress.json'
    state = json.loads(progress.read_text())
    if fault == 'missing':
        progress.unlink()
    elif fault in ('incomplete', 'identity'):
        state['completed' if fault == 'incomplete' else 'identity'] = 1 if fault == 'incomplete' else 'wrong'
        atomic_json(progress, state)
    elif fault == 'array':
        (cache / 'windows.npy').write_bytes(b'changed')
    else:
        path = experiment / 'split-manifest.json'
        split = json.loads(path.read_text())
        split['game_ids']['train'].reverse()
        atomic_json(path, split)
    with pytest.raises((ValueError, FileNotFoundError)):
        diagnostic.verified_inputs(experiment)


def test_actual_decoder_grid_uses_same_validation_games_and_preserves_inputs(frozen_cache, tmp_path):
    experiment, _ = frozen_cache
    before = {str(p): digest(p) for p in experiment.rglob('*') if p.is_file()}
    output = tmp_path / 'diagnostic'
    report = diagnostic.run_diagnostic(experiment, output)
    assert len(report['fits']) == 12 and report['all_solvers_converged']
    assert len(report['saved_validation_comparisons']) == 8
    assert all(r['validation']['n'] == 6 and r['train']['n'] == 15 for r in report['fits'])
    predictions = json.loads((output / 'predictions.json').read_text())
    assert {r['split'] for r in predictions} == {'train', 'validation'}
    assert not {r['game_id'] for r in predictions} & set(report['provenance']['split_ids']['historical'])
    assert before == {str(p): digest(p) for p in experiment.rglob('*') if p.is_file()}
    assert not (tmp_path / 'output/current-model.json').exists()
    assert not (tmp_path / 'output/v2-shadow.json').exists()
    # Changing held-out labels and cached held-out responses cannot affect any fit or selected C.
    data_path = experiment / 'source/training-data.npz'
    with np.load(data_path) as data:
        arrays = {key: data[key].copy() for key in data.files}
    arrays['y'][arrays['test']] = 0
    np.savez(data_path, **arrays)
    manifest = json.loads((experiment / 'manifest.json').read_text())
    manifest['source_hashes']['training-data.npz'] = digest(data_path)
    atomic_json(experiment / 'manifest.json', manifest)
    split = json.loads((experiment / 'split-manifest.json').read_text())
    split['source_hashes'] = manifest['source_hashes']
    atomic_json(experiment / 'split-manifest.json', split)
    _, cache = frozen_cache
    windows = np.load(cache / 'windows.npy')
    windows[arrays['test']] = 1e20
    np.save(cache / 'windows.npy', windows)
    state = json.loads((cache / 'progress.json').read_text())
    state['hashes']['windows'] = digest(cache / 'windows.npy')
    atomic_json(cache / 'progress.json', state)
    changed = diagnostic.run_diagnostic(experiment, tmp_path / 'changed-historical')
    assert changed['fits'] == report['fits']
    assert changed['best_validation'] == report['best_validation']


@pytest.mark.parametrize('fault', [None, 'mismatch', 'nonfinite', 'unconverged', 'wrong_C'])
def test_stronger_l2_gate_checks_all_scores_and_convergence(fault):
    from bet36fly import decoder_stronger_l2 as extension
    fits = [dict(sport=sport, representation=rep, C=.01, converged=True,
                 validation={'log_loss': value + .5e-6}) for (sport, rep), value in extension.EXPECTED.items()]
    if fault == 'mismatch':
        fits[-1]['validation']['log_loss'] += 2e-6
    elif fault == 'nonfinite':
        fits[-1]['validation']['log_loss'] = np.nan
    elif fault == 'unconverged':
        fits[-1]['converged'] = False
    elif fault == 'wrong_C':
        fits[-1]['C'] = .001
    assert extension.reproduction_gate({'fits': fits})['passed'] is (fault is None)


def test_stronger_l2_failed_reproduction_stops_before_extension_and_existing_output_rejected(tmp_path, monkeypatch):
    from bet36fly import decoder_stronger_l2 as extension
    calls = []
    def run(*args):
        calls.append(diagnostic.C_GRID)
        return {'fits': [dict(sport=sport, representation=rep, C=.01, converged=True,
                              validation={'log_loss': value + .01}) for (sport, rep), value in extension.EXPECTED.items()]}
    monkeypatch.setattr(diagnostic, 'run_diagnostic', run)
    original = diagnostic.C_GRID
    output = tmp_path / 'new-output'
    with pytest.raises(ValueError, match='reproduction failed'):
        extension.run_extension(tmp_path / 'experiment', output)
    assert calls == [(.01,)] and diagnostic.C_GRID == original
    assert json.loads((output / 'status.json').read_text())['status'] == 'stopped'
    assert not (output / 'stronger-settings').exists()
    with pytest.raises(FileExistsError):
        extension.run_extension(tmp_path / 'experiment', output)
    assert len(calls) == 1


def test_actual_stronger_l2_extension_reuses_reference_and_preserves_originals(frozen_cache, tmp_path, monkeypatch):
    from bet36fly import decoder_stronger_l2 as extension
    experiment, _ = frozen_cache
    reference_path = tmp_path / 'original-diagnostic'
    with extension.fixed_grid((.01,)):
        reference = diagnostic.run_diagnostic(experiment, reference_path)
    monkeypatch.setattr(extension, 'EXPECTED', {(r['sport'], r['representation']): r['validation']['log_loss']
                                               for r in reference['fits']})
    before = {str(p): digest(p) for root in (experiment, reference_path) for p in root.rglob('*') if p.is_file()}
    output = tmp_path / 'stronger'
    report = extension.run_extension(experiment, output)
    assert len(report['fits']) == 16 and report['reproduction']['passed']
    assert report['settings']['C_grid'] == list(extension.GRID)
    assert report['all_solvers_converged'] and not any(r['warnings'] for r in report['fits'])
    assert len(report['matched_C_differences']) == 8
    assert report['saved_validation_comparisons'] == reference['saved_validation_comparisons']
    assert report['preprocessing'] == reference['preprocessing']
    assert sorted((r['sport'], r['representation'], r['C']) for r in report['fits']) == sorted(
        (sport, rep, c) for sport in ('soccer', 'baseball') for rep in ('whole', 'temporal') for c in extension.GRID)
    assert all(digest(output / name) == sha for name, sha in report['artifact_hashes'].items())
    assert before == {str(p): digest(p) for root in (experiment, reference_path) for p in root.rglob('*') if p.is_file()}
    assert diagnostic.C_GRID == (.01, .1, 1.)
