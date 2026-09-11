"""Read-only seed-42 cache diagnostic: alternate decoders, no simulation or gain fitting."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import warnings

import numpy as np
import sklearn
from scipy.sparse import load_npz
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

from .connectome import ROOT, digest
from .experiment import atomic_json, fit_scale, scale, utcnow
from .experiment_v2 import NEURAL_FILES, cache_identity, graph_hashes, json_hash, load_source
from .learning import metrics

C_GRID = (.01, .1, 1.)


def verified_inputs(experiment):
    """Derive the exact frozen biological initial-cache key; never create missing caches."""
    experiment = Path(experiment).resolve()
    manifest = json.loads((experiment / 'manifest.json').read_text())
    protocol = json.loads((experiment / 'protocol.json').read_text())
    if json_hash(protocol) != manifest['protocol_sha256'] or protocol != manifest['protocol']:
        raise ValueError('Frozen protocol identity mismatch.')
    for name, checksum in manifest['source_hashes'].items():
        if digest(experiment / 'source' / name) != checksum:
            raise ValueError(f'Frozen source changed: {name}')
    graph = experiment / 'graphs/biological'
    if graph_hashes(graph) != manifest['graph_hashes']:
        raise ValueError('Frozen biological graph changed.')
    code = {name: digest(experiment / 'source/code' / name) for name in NEURAL_FILES}
    if code != {name: manifest['code_hashes'][name] for name in NEURAL_FILES}:
        raise ValueError('Frozen neural source identity mismatch.')
    x, y, sports, splits, games = load_source(experiment / 'source')
    split_manifest = json.loads((experiment / 'split-manifest.json').read_text())
    ids = {name: [game['id'] for game, keep in zip(games, mask) if keep] for name, mask in splits.items()}
    if ids != split_manifest['game_ids'] or split_manifest['source_hashes'] != manifest['source_hashes']:
        raise ValueError('Frozen row order or split identity mismatch.')
    input_mean, input_std = fit_scale(x[splits['train']])
    gains = np.ones(load_npz(graph / 'plastic.npz').shape, np.float32)
    identity = cache_identity(scale(x, input_mean, input_std), graph=manifest['graph_hashes'],
                              gains=gains, seed=42, code=code)
    cache = experiment / 'cache' / identity / 'initial'
    progress = cache / 'progress.json'
    if not progress.is_file():
        raise FileNotFoundError(f'Required biological frozen seed-42 cache unavailable: {progress}; no simulation attempted.')
    state = json.loads(progress.read_text())
    if state.get('identity') != identity or state.get('completed') != len(x) or state.get('total') != len(x):
        raise ValueError(f'Required cache incomplete or mismatched: {progress}; no simulation attempted.')
    shapes = dict(windows=(len(x), 4, 124), kc_windows=(len(x), 4, len(np.load(graph / 'kc.npy'))),
                  active=(len(x),), spikes=(len(x),))
    if set(state.get('hashes', {})) != set(shapes):
        raise ValueError('Completed initial cache is missing array hashes.')
    for name, shape in shapes.items():
        file = cache / (name + '.npy')
        if not file.is_file() or digest(file) != state['hashes'][name]:
            raise ValueError(f'Cache array missing or altered: {file}')
        a = np.load(file, mmap_mode='r', allow_pickle=False)
        if a.shape != shape or a.dtype != (np.int32 if name in ('active', 'spikes') else np.float32):
            raise ValueError(f'Cache shape or dtype mismatch: {file}')
    windows = np.load(cache / 'windows.npy', mmap_mode='r', allow_pickle=False)
    if not np.isfinite(windows).all() or np.any(windows < 0):
        raise ValueError('Cached raw firing rates must be finite and nonnegative.')
    provenance = dict(experiment_id=manifest['id'], seed=42, graph='biological', gains='frozen ones',
        cache_path=str(cache), cache_identity=identity, cache_hashes=state['hashes'], rows=len(x),
        source_hashes=manifest['source_hashes'], graph_hashes=manifest['graph_hashes'], neural_code_hashes=code,
        row_alignment='Exact ordered frozen game IDs and partitions verified; cache key binds the ordered scaled input matrix.',
        split_ids=ids, historical_use='Identity and row alignment only; historical rows excluded before representations and fitting.')
    return windows, y, sports, splits, games, manifest, provenance


def representations(windows):
    if windows.ndim != 3 or windows.shape[1:] != (4, 124):
        raise ValueError('Expected raw windows with shape (rows, 4, 124).')
    if not np.isfinite(windows).all() or np.any(windows < 0):
        raise ValueError('Raw windows must be finite and nonnegative.')
    return {'whole': np.log1p(windows.mean(axis=1)),
            'temporal': np.log1p(windows).reshape(len(windows), 496)}


def scaled_representations(windows, training, sports):
    result, diagnostics, scalers = {}, {}, {}
    for name, values in representations(windows).items():
        mean, std = fit_scale(values[training])
        unbounded = (values - mean) / std
        result[name] = scale(values, mean, std)
        scalers[name + '_mean'], scalers[name + '_std'] = mean, std
        diagnostics[name] = {}
        for split, mask in [('train', training), ('validation', ~training)]:
            diagnostics[name][split] = {}
            for sport, sport_mask in [('all', np.ones(len(sports), bool)), ('soccer', sports == 0), ('baseball', sports == 1)]:
                ix = mask & sport_mask
                raw, scaled = values[ix], unbounded[ix]
                if not len(raw):
                    raise ValueError(f'Missing {sport} {split} rows.')
                diagnostics[name][split][sport] = dict(rows=int(ix.sum()), dimensions=raw.shape[1],
                    finite=bool(np.isfinite(raw).all() and np.isfinite(scaled).all()),
                    constant_channels=int(np.count_nonzero(np.ptp(raw, axis=0) == 0)),
                    channels_below_scale_floor=int(np.count_nonzero(raw.std(0) < .01)),
                    clipped_fraction=float((abs(scaled) > 8).mean()),
                    rows_with_clipping_fraction=float((abs(scaled) > 8).any(1).mean()),
                    maximum_absolute_before_clipping=float(abs(scaled).max()))
    return result, diagnostics, scalers


def compare_saved(experiment, manifest, games, y, sports, validation):
    expected = {game['id']: (i, game) for i, game in enumerate(games) if validation[i]}
    paths = [(name, experiment / 'runs' / f'{name}-42' / 'predictions.json')
             for name in ('bio-frozen-whole', 'bio-frozen-temporal')]
    paths += [(name, experiment / 'baseline-predictions.json') for name in ('frequency-prior', 'feature-logistic')]
    comparisons, provenance = [], {}
    for model, path in paths:
        artifact = next((a for a in manifest['artifacts'].values() if a['path'] == str(path.relative_to(experiment))), None)
        if artifact is None or digest(path) != artifact['sha256']:
            raise ValueError(f'Saved comparison artifact identity mismatch: {path}')
        rows = [r for r in json.loads(path.read_text()) if r['split'] == 'validation' and r['seed'] == 42 and r['model'] == model]
        if len(rows) != len(expected) or {r['game_id'] for r in rows} != set(expected):
            raise ValueError(f'Validation games differ for {model}.')
        for row in rows:
            i, game = expected[row['game_id']]
            if row['outcome'] != int(y[i]) or row['sport'] != game['sport'] or row['start_time'] != game['start_time']:
                raise ValueError(f'Validation labels or identity differ for {model}.')
        for sport in ('soccer', 'baseball'):
            selected = [r for r in rows if r['sport'] == sport]
            comparisons.append(dict(model=model, sport=sport, split='validation',
                                    **metrics(np.array([r['outcome'] for r in selected]),
                                              np.array([r['probabilities'] for r in selected]))))
        provenance[str(path)] = artifact['sha256']
    return comparisons, provenance


def run_diagnostic(experiment, output):
    experiment, output = Path(experiment).resolve(), Path(output).resolve()
    if output.is_relative_to(experiment):
        raise ValueError('Diagnostic output must be separate from the preserved experiment.')
    windows, y, sports, splits, games, manifest, provenance = verified_inputs(experiment)
    comparisons, comparison_hashes = compare_saved(experiment, manifest, games, y, sports, splits['validation'])
    # Only training and validation rows cross into decoder fitting or representation diagnostics.
    use = splits['train'] | splits['validation']
    training, labels, sport_ids = splits['train'][use], y[use], sports[use]
    selected_games = [g for g, keep in zip(games, use) if keep]
    values, diagnostics, parameters = scaled_representations(np.asarray(windows[use]), training, sport_ids)
    settings = dict(C_grid=list(C_GRID), solver='lbfgs', penalty='l2', max_iter=2000, tol=1e-4,
        scaling='Per representation, pooled original training rows across sports; std floor .01, clip to [-8,8], same as v2.',
        clipping='Fraction of entries strictly outside [-8,8] before clipping, reported per split and sport.',
        selection='Validation log loss within each sport and representation; lower C breaks ties. All C settings reported.')
    rows, predictions = [], []
    for representation, z in values.items():
        for sport_id, sport in enumerate(('soccer', 'baseball')):
            tr, val = training & (sport_ids == sport_id), ~training & (sport_ids == sport_id)
            for strength in C_GRID:
                with warnings.catch_warnings(record=True) as captured:
                    warnings.simplefilter('always')
                    model = LogisticRegression(C=strength, solver='lbfgs', max_iter=2000, tol=1e-4).fit(z[tr], labels[tr])
                converged = not any(issubclass(w.category, ConvergenceWarning) for w in captured) and int(model.n_iter_.max()) < 2000
                key = f'{representation}-{sport}-C{strength}'
                parameters[key + '_coefficient'] = model.coef_
                parameters[key + '_intercept'] = model.intercept_
                parameters[key + '_classes'] = model.classes_
                row = dict(representation=representation, sport=sport, C=strength, converged=converged,
                           n_iter=model.n_iter_.tolist(), warnings=[str(w.message) for w in captured])
                for split, mask in [('train', tr), ('validation', val)]:
                    p = np.zeros((mask.sum(), 3))
                    p[:, model.classes_] = model.predict_proba(z[mask])
                    row[split] = metrics(labels[mask], p)
                    for index, prob in zip(np.flatnonzero(mask), p):
                        predictions.append(dict(model=key, sport=sport, split=split,
                            game_id=selected_games[index]['id'], outcome=int(labels[index]), probabilities=prob.tolist()))
                rows.append(row)
    best, differences = {}, []
    for sport in ('soccer', 'baseball'):
        best[sport] = {}
        for representation in values:
            candidates = [r for r in rows if r['sport'] == sport and r['representation'] == representation and r['converged']]
            best[sport][representation] = min(candidates, key=lambda r: (r['validation']['log_loss'], r['C'])) if candidates else None
        for strength in C_GRID:
            pair = {r['representation']: r for r in rows if r['sport'] == sport and r['C'] == strength}
            differences.append(dict(sport=sport, C=strength,
                temporal_minus_whole_validation_loss=pair['temporal']['validation']['log_loss'] - pair['whole']['validation']['log_loss']))
    report = dict(schema_version=1, diagnostic='Frozen biological seed-42 decoder only', created_at=utcnow(),
        code_sha256=digest(Path(__file__)), numpy_version=np.__version__, sklearn_version=sklearn.__version__,
        provenance=provenance, comparison_hashes=comparison_hashes, settings=settings, preprocessing=diagnostics,
        fits=rows, best_validation=best, matched_C_differences=differences, saved_validation_comparisons=comparisons,
        all_solvers_converged=all(r['converged'] for r in rows),
        limitations=['One frozen biological seed; validation was used to choose C, so best-C scores are development results.',
            'This changes decoder optimization and regularization together; it does not identify a root cause.',
            'No new simulations, synaptic gains, historical evaluation, prospective tuning, or model-pointer changes.'])
    output.mkdir(parents=True, exist_ok=False)
    np.savez(output / 'decoders.npz', **parameters)
    atomic_json(output / 'predictions.json', predictions)
    report['artifact_hashes'] = {name: digest(output / name) for name in ('decoders.npz', 'predictions.json')}
    atomic_json(output / 'report.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment', required=True)
    parser.add_argument('--output', default=str(ROOT / 'output/diagnostics' / ('decoder-seed42-' + utcnow().replace(':', '-'))))
    args = parser.parse_args()
    result = run_diagnostic(args.experiment, args.output)
    print(json.dumps(dict(output=args.output, all_solvers_converged=result['all_solvers_converged'],
                          matched_C_differences=result['matched_C_differences'])), flush=True)
