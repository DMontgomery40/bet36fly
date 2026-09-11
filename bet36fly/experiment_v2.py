"""Frozen, resumable v2 matrix. Full LIF responses select and serve every neural model."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import gc
import hashlib
import json
from pathlib import Path
import shutil
import time

import numpy as np

from .brain import FlyBrain, simulate_windows
from .connectome import ROOT, digest
from .experiment import atomic_json, chronological_split, fit_scale, scale, utcnow, _sport_metrics
from .experiments import Registry, writer_lock
from .learning import fit_readout, metrics, probabilities

VARIANTS = (
    'bio-frozen-whole', 'bio-frozen-temporal',
    'bio-independent-whole', 'bio-independent-temporal',
    'bio-shared-whole', 'bio-shared-temporal',
    'null-frozen-temporal', 'null-shared-temporal',
)
GRAPH_FILES = ('counts.npy', 'signs.npy', 'plastic.npz', 'sensory.npy', 'ids.npy',
               'in_degree.npy', 'nodes.feather', 'mbon.npy', 'post.npy', 'indptr.npy', 'kc.npy')
NEURAL_FILES = ('brain.py', 'lif.cpp')
SPLIT_NAMES = ('train', 'validation', 'historical')


def json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def graph_hashes(path):
    return {name: digest(Path(path) / name) for name in GRAPH_FILES}


def array_hash(array):
    a = np.ascontiguousarray(array)
    return hashlib.sha256(memoryview(a).cast('B')).hexdigest()


def cache_identity(features, *, graph, gains, seed, layout=(0, 20, 40, 60, 80), code=None):
    return json_hash({'features': array_hash(features), 'shape': features.shape, 'dtype': str(features.dtype),
                      'graph': graph, 'gains': array_hash(gains), 'seed': seed, 'layout': layout,
                      'code': code or {f: digest(Path(__file__).with_name(f)) for f in NEURAL_FILES}})


def load_source(path):
    path = Path(path)
    with np.load(path / 'training-data.npz', allow_pickle=False) as saved:
        data = {k: saved[k].copy() for k in saved.files}
    games = json.loads((path / 'training-games.json').read_text())['games']
    x, y, sports = data['X'], data['y'], data['sport']
    if x.shape != (len(games), 16) or not np.isfinite(x).all() or len(set(g['id'] for g in games)) != len(games):
        raise ValueError('Frozen features and unique games must align.')
    masks = chronological_split(games)
    if not np.all(np.sum(masks, axis=0) == 1):
        raise ValueError('Frozen partitions must be disjoint and exhaustive.')
    for key, mask in zip(('train', 'validation', 'test'), masks):
        if not np.array_equal(data[key], mask):
            raise ValueError('Frozen split differs from chronological partition.')
    if not np.array_equal(sports, np.array([g['sport'] == 'baseball' for g in games])):
        raise ValueError('Sports disagree with frozen rows.')
    if np.any((y < 0) | (y > 2)) or np.any((sports == 1) & (y == 1)):
        raise ValueError('Invalid frozen outcomes.')
    return x, y, sports, dict(zip(SPLIT_NAMES, masks)), games


def simulation_cache(brain, features, directory, *, graph, gains, seed, workers=4, include_kc=False, progress=None):
    """Memory-mapped row checkpointing; every persisted count follows flushed arrays."""
    identity = cache_identity(features, graph=graph, gains=gains, seed=seed)
    path = Path(directory) / identity / ('initial' if include_kc else 'readout')
    path.mkdir(parents=True, exist_ok=True)
    metadata = path / 'progress.json'
    state = json.loads(metadata.read_text()) if metadata.exists() else {'completed': 0, 'identity': identity}
    shapes = {'windows': (len(features), 4, brain.output_dim), 'active': (len(features),), 'spikes': (len(features),)}
    if include_kc:
        shapes['kc_windows'] = (len(features), 4, len(brain.kc))
    arrays = {}
    for key, shape in shapes.items():
        file = path / (key + '.npy')
        if file.exists():
            arrays[key] = np.load(file, mmap_mode='r+')
            if arrays[key].shape != shape:
                raise ValueError('Cache dimensions changed.')
        else:
            if state['completed']:
                raise ValueError('Partial cache lost an array.')
            arrays[key] = np.lib.format.open_memmap(file, mode='w+', shape=shape,
                                                    dtype=np.int32 if key in ('active', 'spikes') else np.float32)
    completed = state['completed']
    if completed == len(features):
        if state.get('hashes') != {key: digest(path / (key + '.npy')) for key in shapes}:
            raise ValueError('Completed simulation cache hash mismatch.')
        if progress:
            progress(completed=completed, total=len(features), cache_hit=True)
        return arrays
    started, last = time.monotonic(), time.monotonic()

    def trial(row):
        return simulate_windows(brain, row, seed=seed, include_kc=include_kc)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for index, response in enumerate(pool.map(trial, features[completed:]), completed):
            for key in arrays:
                arrays[key][index] = response[key]
            now = time.monotonic()
            if now - last >= 5 or index + 1 == len(features):
                for array in arrays.values():
                    array.flush()
                state.update(completed=index + 1, total=len(features), updated_at=utcnow())
                if index + 1 == len(features):
                    state['hashes'] = {key: digest(path / (key + '.npy')) for key in shapes}
                atomic_json(metadata, state)
                if progress:
                    progress(completed=index + 1, total=len(features), elapsed_seconds=now - started,
                             cache_hit=False)
                last = now
    return arrays


def readout_features(windows, layout):
    return windows.mean(axis=1) if layout == 'whole' else windows.reshape(len(windows), -1)


def select_checkpoint(candidates):
    return min(candidates, key=lambda c: (c['validation_loss'], c['plastic_epoch'], c['selected_epoch']))


def select_architecture(jobs):
    groups = {}
    for job in jobs:
        if job['variant'].startswith('bio-') and job['status'] == 'complete':
            groups.setdefault(job['variant'], []).append(job)
    eligible = {name: rows for name, rows in groups.items() if len(rows) == 3}
    if not eligible:
        raise ValueError('No biological architecture has three completed seeds.')
    return min(eligible, key=lambda name: (np.mean([j['validation_loss'] for j in eligible[name]]),
                                          eligible[name][0]['active_parameters'], name))


def export_rows(games, y, p, *, mask, variant, seed, split):
    return [dict(game_id=g['id'], sport=g['sport'], start_time=g['start_time'], outcome=int(label),
                 probabilities=prob.tolist(), model=variant, seed=seed, split=split)
            for g, label, prob in zip([g for g, keep in zip(games, mask) if keep], y[mask], p)]


def paired_week_bootstrap(rows, *, seed=20260910, replicates=2000) -> dict:
    """Paired games, seed-averaged losses, whole ISO weeks including zero-game weeks."""
    output = {'method': 'Paired ISO calendar weeks within sport; matched-seed game losses averaged before resampling.',
              'limitation': 'Weekly blocks approximate, but do not eliminate, season/team dependence. '
                            'Three seeds are not independent game observations.',
              'replicates': replicates, 'seed': seed, 'comparisons': []}
    for split in sorted(set(row['split'] for row in rows)):
        for sport in ('soccer', 'baseball'):
            selected = [r for r in rows if r['split'] == split and r['sport'] == sport]
            by_model = {}
            for row in selected:
                by_model.setdefault(row['model'], {}).setdefault(row['game_id'], {})[row['seed']] = row
            names = sorted(by_model)
            pairs = [(name, 'feature-logistic') for name in names if name != 'feature-logistic'
                     and 'feature-logistic' in names]
            for arm in ('frozen', 'shared'):
                pair = (f'bio-{arm}-temporal', f'null-{arm}-temporal')
                if all(n in by_model for n in pair):
                    pairs.append(pair)
            for left, right in pairs:
                game_ids = sorted(set(by_model[left]) & set(by_model[right]))
                entries, spread = [], {}
                for game_id in game_ids:
                    a, b = by_model[left][game_id], by_model[right][game_id]
                    seeds = sorted(set(a) & set(b))
                    if not seeds:
                        continue
                    diffs = []
                    for matched_seed in seeds:
                        ar, br = a[matched_seed], b[matched_seed]
                        if ar['outcome'] != br['outcome'] or ar['start_time'] != br['start_time']:
                            raise ValueError('Paired rows disagree on game identity/outcome.')
                        label = ar['outcome']
                        difference = float(-np.log(max(ar['probabilities'][label], 1e-12))
                                           + np.log(max(br['probabilities'][label], 1e-12)))
                        diffs.append(difference)
                        spread.setdefault(matched_seed, []).append(difference)
                    date = datetime.fromisoformat(a[seeds[0]]['start_time'].replace('Z', '+00:00')).date()
                    entries.append((date - timedelta(days=date.weekday()), float(np.mean(diffs))))
                if not entries:
                    continue
                first, last = min(e[0] for e in entries), max(e[0] for e in entries)
                weeks = (last - first).days // 7 + 1
                totals, counts = np.zeros(weeks), np.zeros(weeks)
                for week, delta in entries:
                    index = (week - first).days // 7
                    totals[index] += delta
                    counts[index] += 1
                rng = np.random.default_rng(seed)
                indices = rng.integers(weeks, size=(replicates, weeks))
                denominators = counts[indices].sum(1)
                samples = totals[indices].sum(1)[denominators > 0] / denominators[denominators > 0]
                low, high = np.percentile(samples, [2.5, 97.5]).tolist()
                output['comparisons'].append(dict(split=split, sport=sport, left=left, right=right,
                    difference=float(np.mean([e[1] for e in entries])), interval=[low, high], n=len(entries),
                    calendar_weeks=weeks, empty_weeks=int((counts == 0).sum()),
                    seed_differences={str(k): float(np.mean(v)) for k, v in spread.items()},
                    decision='better on this development comparison' if high < 0 else
                             'worse on this development comparison' if low > 0 else 'uncertain'))
    return output


def fit_baselines(z, y, sports, splits):
    from sklearn.linear_model import LogisticRegression
    result, models = {}, {}
    for s in (0, 1):
        tr, val = splits['train'] & (sports == s), splits['validation'] & (sports == s)
        prior = np.bincount(y[tr], minlength=3).astype(float) + 1
        if s == 1:
            prior[1] = 0
        prior /= prior.sum()
        choices = []
        for strength in (.01, .1, 1.):
            model = LogisticRegression(C=strength, max_iter=1000).fit(z[tr], y[tr])
            p = np.zeros((val.sum(), 3))
            p[:, model.classes_] = model.predict_proba(z[val])
            choices.append((metrics(y[val], p)['log_loss'], strength, model))
        _, strength, model = min(choices, key=lambda item: (item[0], item[1]))
        models[str(s)] = dict(classes=model.classes_.tolist(), coefficient=model.coef_.tolist(),
                              intercept=model.intercept_.tolist(), C=strength, prior=prior.tolist())
        for split in ('validation', 'historical'):
            mask = splits[split]
            for name in ('frequency-prior', 'feature-logistic'):
                target = result.setdefault((name, split), np.zeros((mask.sum(), 3)))
                ix = sports[mask] == s
                if name == 'frequency-prior':
                    target[ix] = prior
                else:
                    p = np.zeros((ix.sum(), 3))
                    p[:, model.classes_] = model.predict_proba(z[mask & (sports == s)])
                    target[ix] = p
    return models, result


def baseline_probability(features, baseline):
    features = np.asarray(features, np.float32)
    z = scale(features, np.array(baseline['input_mean']), np.array(baseline['input_std']))
    model = baseline['models'][str(int(features[-1]))]
    logits = np.array(model['coefficient']) @ z + np.array(model['intercept'])
    if len(logits) == 1:
        home = 1 / (1 + np.exp(-logits[0]))
        values = np.array([1 - home, home])
    else:
        values = np.exp(logits - logits.max())
        values /= values.sum()
    p = np.zeros(3)
    p[model['classes']] = values
    return p


def save_candidate(directory, *, variant, seed, graph_path, graph, gains, layout,
                   input_mean, input_std, output_mean, output_std, head, protocol):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    arrays = directory / 'parameters.npz'
    np.savez_compressed(arrays, gains=gains, input_mean=input_mean, input_std=input_std,
                        output_mean=output_mean, output_std=output_std, weight=head['weight'], bias=head['bias'])
    metadata = dict(schema_version=2, variant=variant, seed=seed, graph_path=str(Path(graph_path).resolve()),
                    graph_hashes=graph, layout=layout, windows_ms=[0, 20, 40, 60, 80], duration_ms=80,
                    neural_source_hashes={f: digest(Path(__file__).with_name(f)) for f in NEURAL_FILES},
                    parameter_sha256=digest(arrays), protocol_sha256=json_hash(protocol),
                    selected_decoder_epoch=head['selected_epoch'])
    atomic_json(directory / 'bundle.json', metadata)
    return directory / 'bundle.json'


class Candidate:
    def __init__(self, bundle_path):
        path = Path(bundle_path)
        self.metadata = json.loads(path.read_text())
        meta = self.metadata
        if meta.get('schema_version') != 2 or meta.get('layout') not in ('whole', 'temporal'):
            raise ValueError('Unsupported candidate schema/layout.')
        arrays = path.parent / 'parameters.npz'
        if digest(arrays) != meta['parameter_sha256'] or graph_hashes(meta['graph_path']) != meta['graph_hashes']:
            raise ValueError('Candidate parameters or graph changed.')
        if meta['neural_source_hashes'] != {f: digest(Path(__file__).with_name(f)) for f in NEURAL_FILES}:
            raise ValueError('Candidate neural implementation changed.')
        with np.load(arrays, allow_pickle=False) as data:
            self.arrays = {key: data[key].copy() for key in data.files}
        if any(not np.isfinite(a).all() for a in self.arrays.values()):
            raise ValueError('Candidate contains nonfinite arrays.')
        for name in ('input_std', 'output_std'):
            if np.any(self.arrays[name] <= 0):
                raise ValueError('Candidate has invalid scaling.')
        self.brain = FlyBrain(Path(meta['graph_path']), gains=self.arrays['gains'])
        dimension = self.brain.output_dim * (4 if meta['layout'] == 'temporal' else 1)
        if self.arrays['weight'].shape != (2, 3, dimension):
            raise ValueError('Candidate decoder dimensions do not match layout.')

    def predict_proba(self, features):
        x = np.asarray(features, np.float32)
        if x.shape != (16,) or not np.isfinite(x).all() or x[-1] not in (0, 1):
            raise ValueError('Expected one unscaled finite 16-feature row including sport.')
        ck = self.arrays
        response = simulate_windows(self.brain, scale(x, ck['input_mean'], ck['input_std']),
                                    seed=self.metadata['seed'], include_kc=False)
        raw = response['whole'] if self.metadata['layout'] == 'whole' else response['windows'].reshape(-1)
        output = scale(np.log1p(raw)[None], ck['output_mean'], ck['output_std'])
        return probabilities(output, np.array([int(x[-1])]), ck['weight'], ck['bias'])[0]


def load_candidate(bundle_path):
    return Candidate(bundle_path)


TRAINING_FILES = ('brain.py', 'lif.cpp', 'learning.py', 'grouped_learning.py')


def record_execution(registry):
    """Keep the original source freeze and append each actual executing revision."""
    hashes = {p.name: digest(p) for p in Path(__file__).parent.iterdir() if p.suffix in ('.py', '.cpp')}
    frozen = registry.manifest['code_hashes']
    if any(hashes[name] != frozen[name] for name in TRAINING_FILES):
        raise ValueError('Training/neural implementation changed; existing fitted artifacts are incompatible.')
    execution_id = datetime.now().strftime('%Y%m%dT%H%M%S') + '-' + json_hash(hashes)[:10]
    directory = registry.directory / 'executions' / execution_id
    directory.mkdir(parents=True, exist_ok=True)
    code = directory / 'code'
    code.mkdir(exist_ok=True)
    for name in hashes:
        shutil.copy2(Path(__file__).with_name(name), code / name)
    record = dict(id=execution_id, started_at=utcnow(), code_hashes=hashes,
                  training_compatibility='Unchanged neural and fitting implementations; same frozen protocol and data.')
    atomic_json(directory / 'record.json', record)
    registry.manifest.setdefault('executions', []).append(record)
    registry.execution_id = execution_id
    registry.artifact(directory / 'record.json', label='Execution provenance ' + execution_id)
    registry.save()


def verify_completed_jobs(registry):
    """Validate normal resume skips and recover a committed result before registry publication."""
    for job in registry.manifest['jobs']:
        directory = registry.directory / 'runs' / job['id']
        path = directory / 'result.json'
        if job['status'] != 'complete' and not path.exists():
            continue
        if not path.exists():
            raise ValueError('Completed job lost its result artifact.')
        registered = next((a for a in registry.manifest.get('artifacts', {}).values()
                           if a['path'] == str(path.relative_to(registry.directory))), None)
        if registered and digest(path) != registered['sha256']:
            raise ValueError('Completed result artifact changed.')
        saved = json.loads(path.read_text())
        for relative, checksum in saved['artifact_hashes'].items():
            artifact = (directory / relative).resolve()
            if not artifact.is_relative_to(directory.resolve()) or digest(artifact) != checksum:
                raise ValueError('Completed run artifact changed.')
        for artifact in (path, directory / 'predictions.json', directory / 'candidate/bundle.json',
                         directory / 'candidate/parameters.npz'):
            registry.artifact(artifact, job=job['id'])
        job.update(saved, status='complete', phase='complete', error=None)
    if registry.manifest['status'] == 'complete':
        for artifact in registry.manifest.get('artifacts', {}).values():
            path = (registry.directory / artifact['path']).resolve()
            if not path.is_relative_to(registry.directory.resolve()) or digest(path) != artifact['sha256']:
                raise ValueError('Completed experiment artifact changed.')
    registry.save()


def _job_id(variant, seed):
    return f'{variant}-{seed}'


def prepare_experiment(root, protocol, resume):
    source = root / 'output/runs' / protocol['source_run_id']
    source_hashes = {f: digest(source / f) for f in ('training-data.npz', 'training-games.json')}
    graph = graph_hashes(root / 'data/brain')
    identity = json_hash(dict(protocol=protocol, source=source_hashes, graph=graph))
    experiment_id = 'v2-' + identity[:20]
    directory = root / 'output/experiments' / experiment_id
    if (directory / 'manifest.json').exists():
        if not resume:
            raise ValueError('Frozen experiment already exists; use --resume.')
        registry = Registry(directory)
        for name, checksum in registry.manifest['source_hashes'].items():
            if digest(directory / 'source' / name) != checksum:
                raise ValueError('Frozen source artifact changed.')
        if graph_hashes(directory / 'graphs/biological') != graph:
            raise ValueError('Frozen biological graph changed.')
        return registry, graph
    directory.mkdir(parents=True, exist_ok=True)
    frozen = directory / 'source'
    frozen.mkdir(exist_ok=True)
    for name in source_hashes:
        shutil.copy2(source / name, frozen / name)
    graph_path = directory / 'graphs/biological'
    graph_path.mkdir(parents=True, exist_ok=True)
    for name in (*GRAPH_FILES, 'manifest.json', 'source-lock.json'):
        shutil.copy2(root / 'data/brain' / name, graph_path / name)
    code = directory / 'source/code'
    code.mkdir(exist_ok=True)
    for path in sorted((root / 'bet36fly').glob('*')):
        if path.suffix in ('.py', '.cpp'):
            shutil.copy2(path, code / path.name)
    atomic_json(directory / 'protocol.json', protocol)
    _, _, _, splits, games = load_source(frozen)
    atomic_json(directory / 'split-manifest.json', {
        'scaling_fit_on': 'train only', 'source_hashes': source_hashes,
        'game_ids': {name: [g['id'] for g, keep in zip(games, mask) if keep] for name, mask in splits.items()},
        'labels': {'validation': 'July–December 2025 validation',
                   'historical': 'January–August 2026 historical development benchmark'},
    })
    jobs = []
    for seed in protocol['seeds']:
        for variant in VARIANTS:
            gains = 0 if 'frozen' in variant else 61210 if 'independent' in variant else 295
            temporal = variant.endswith('temporal')
            jobs.append(dict(id=_job_id(variant, seed), variant=variant, seed=seed, status='queued', phase='queued',
                             gain_parameters=gains, decoder_parameters=2982 if temporal else 750,
                             active_parameters=gains + (2485 if temporal else 625),
                             seeds={'stimulus': seed, 'minibatch': seed, 'head_initialization': seed},
                             completed=0, total=0))
    registry = Registry(directory, dict(id=experiment_id, schema_version=2, status='running', created_at=utcnow(),
                        identity=identity, protocol=protocol, protocol_sha256=json_hash(protocol), source_hashes=source_hashes,
                        graph_hashes=graph, code_hashes={p.name: digest(p) for p in code.iterdir()},
                        active_v1=json.loads((root / 'output/current-model.json').read_text()),
                        jobs=jobs, artifacts={}, selected_shadow=None))
    for path in (directory / 'protocol.json', directory / 'split-manifest.json'):
        registry.artifact(path)
    registry.save()
    return registry, graph


def _fit_neural_job(registry, job, protocol, x, y, sports, splits, games, initial, graph_path, graph,
                    input_mean, input_std):
    from .grouped_learning import build_gain_groups, fit_grouped_plasticity
    variant, seed = job['variant'], job['seed']
    directory = registry.directory / 'runs' / job['id']
    directory.mkdir(parents=True, exist_ok=True)
    result_path = directory / 'result.json'
    if result_path.exists():
        saved = json.loads(result_path.read_text())
        # All run artifacts are immutable once its final result is committed.
        for relative, checksum in saved['artifact_hashes'].items():
            if digest(directory / relative) != checksum:
                raise ValueError('Completed run artifact changed.')
        registry.update(job, **saved, status='complete', phase='complete')
        return
    started = time.monotonic()
    layout = 'temporal' if variant.endswith('temporal') else 'whole'
    train, val = splits['train'], splits['validation']
    tv = train | val
    tv_train, tv_val = train[tv], val[tv]
    z = scale(x, input_mean, input_std)
    brain = FlyBrain(graph_path)
    anatomy = brain.plastic.toarray()
    unity = np.ones_like(anatomy)

    last_progress = [0.0, None]
    def progress(phase, **fields):
        now = time.monotonic()
        if phase != last_progress[1] or now - last_progress[0] >= 5 or (fields.get('total') and fields.get('completed') == fields.get('total')):
            registry.update(job, phase=phase, wall_seconds=now - started, **fields)
            last_progress[:] = [now, phase]

    initial_raw = readout_features(initial['windows'], layout)
    plastic_curve, snapshots = [], {0: {'gains': unity, 'validation_loss': None}}
    if 'frozen' not in variant:
        checkpoint_file = directory / 'surrogate.json'
        if checkpoint_file.exists():
            surrogate = json.loads(checkpoint_file.read_text())
            plastic_curve = surrogate['curve']
            snapshots = {int(epoch): dict(info, gains=np.load(directory / f'gains-{epoch}.npy'))
                         for epoch, info in surrogate['checkpoints'].items()}
        else:
            group_ids, _ = build_gain_groups(brain.nodes, brain.kc, brain.mbon, anatomy, graph_ids=brain.ids)
            if 'independent' in variant:
                group_ids = np.full(anatomy.shape, -1, np.int64)
                group_ids[anatomy != 0] = np.arange(np.count_nonzero(anatomy))
            activity = initial['windows'] if layout == 'temporal' else initial['windows'].mean(1)[:, None, :]
            kc = initial['kc_windows'] if layout == 'temporal' else initial['kc_windows'].mean(1)[:, None, :]
            am, ast = fit_scale(np.log1p(activity[train]))
            km, kst = fit_scale(np.log1p(kc[train]))
            progress('surrogate', completed=0, total=protocol['plastic_epochs'])
            surrogate = fit_grouped_plasticity(anatomy, group_ids,
                scale(np.log1p(activity[train]), am, ast), scale(np.log1p(kc[train]), km, kst), y[train], sports[train],
                scale(np.log1p(activity[val]), am, ast), scale(np.log1p(kc[val]), km, kst), y[val], sports[val],
                epochs=protocol['plastic_epochs'], checkpoints=protocol['plastic_checkpoints'], seed=seed,
                head_seed=seed, minibatch_seed=seed, lr=protocol['plastic_lr'], gain_penalty=protocol['gain_penalty'],
                gain_log_bound=protocol['gain_log_bound'], gradient_clip=protocol['gradient_clip'],
                progress=lambda curve: progress('surrogate', completed=len(curve), total=protocol['plastic_epochs']))
            snapshots, plastic_curve = surrogate['checkpoints'], surrogate['curve']
            safe = {}
            for epoch, snapshot in snapshots.items():
                np.save(directory / f'gains-{epoch}.npy', snapshot['gains'])
                np.savez_compressed(directory / f'surrogate-{epoch}.npz',
                    **{k: v for k, v in snapshot.items() if isinstance(v, np.ndarray)})
                safe[str(epoch)] = {k: v for k, v in snapshot.items() if not isinstance(v, np.ndarray)}
            atomic_json(checkpoint_file, {'curve': plastic_curve, 'checkpoints': safe})
            del activity, kc
    del brain
    gc.collect()
    comparisons = []
    heads = {}
    for epoch, snapshot in snapshots.items():
        head_path = directory / f'decoder-{epoch}.npz'
        info_path = directory / f'checkpoint-{epoch}.json'
        if info_path.exists() and head_path.exists():
            info = json.loads(info_path.read_text())
            with np.load(head_path) as saved:
                heads[epoch] = {k: saved[k].copy() for k in saved.files}
            comparisons.append(info)
            continue
        gains = snapshot['gains']
        if epoch == 0:
            raw = initial_raw[tv]
        else:
            brain = FlyBrain(graph_path, gains=gains)
            simulated = simulation_cache(brain, z[tv], registry.directory / 'cache', graph=graph,
                gains=gains, seed=seed, workers=protocol['workers'],
                progress=lambda **fields: progress(f'full-simulator-epoch-{epoch}', **fields))
            raw = readout_features(simulated['windows'], layout)
            del brain, simulated
            gc.collect()
        om, ost = fit_scale(np.log1p(raw[tv_train]))
        output = scale(np.log1p(raw), om, ost)
        progress(f'decoder-epoch-{epoch}', completed=0, total=protocol['readout_epochs'])
        head = fit_readout(output[tv_train], y[train], sports[train], output[tv_val], y[val], sports[val],
                           epochs=protocol['readout_epochs'], seed=seed)
        heads[epoch] = dict(output_mean=om, output_std=ost, weight=head['weight'], bias=head['bias'])
        np.savez_compressed(head_path, **heads[epoch])
        info = dict(plastic_epoch=epoch, validation_loss=head['validation_loss'],
                    selected_epoch=head['selected_epoch'], curve=head['curve'],
                    surrogate_validation_loss=snapshot.get('validation_loss'),
                    surrogate_full_gap=(head['validation_loss'] - snapshot['validation_loss'])
                        if snapshot.get('validation_loss') is not None else None)
        atomic_json(info_path, info)
        comparisons.append(info)
    chosen = select_checkpoint(comparisons)
    epoch = chosen['plastic_epoch']
    head = heads[epoch]
    gains = snapshots[epoch]['gains']
    brain = FlyBrain(graph_path, gains=gains)
    predictions, measures, rows = {}, {}, []
    neural_stats = {}
    for split in ('validation', 'historical'):
        mask = splits[split]
        if epoch == 0:
            simulated = {k: v[mask] for k, v in initial.items() if k != 'kc_windows'}
        elif split == 'validation':
            cached = simulation_cache(brain, z[tv], registry.directory / 'cache', graph=graph,
                gains=gains, seed=seed, workers=protocol['workers'])
            simulated = {k: v[tv_val] for k, v in cached.items()}
        else:
            simulated = simulation_cache(brain, z[mask], registry.directory / 'cache', graph=graph,
                gains=gains, seed=seed, workers=protocol['workers'],
                progress=lambda **fields: progress('historical-development-benchmark', **fields))
        raw = readout_features(simulated['windows'], layout)
        output = scale(np.log1p(raw), head['output_mean'], head['output_std'])
        p = probabilities(output, sports[mask], head['weight'], head['bias'])
        predictions[split] = p
        measures[split] = _sport_metrics(y[mask], p, sports[mask])
        neural_stats[split] = dict(mean_active_neurons=float(simulated['active'].mean()),
                                  mean_spikes=float(simulated['spikes'].mean()),
                                  zero_channel_fraction=float((raw == 0).mean()),
                                  clipped_readout_fraction=float((abs(output) >= 8).mean()))
        rows.extend(export_rows(games, y, p, mask=mask, variant=variant, seed=seed, split=split))
    bundle = save_candidate(directory / 'candidate', variant=variant, seed=seed, graph_path=graph_path,
        graph=graph, gains=gains, layout=layout, input_mean=input_mean, input_std=input_std,
        output_mean=head['output_mean'], output_std=head['output_std'],
        head=dict(head, selected_epoch=chosen['selected_epoch']), protocol=protocol)
    # Real full-simulator round trip, including both sport heads.
    del brain
    gc.collect()
    loaded = load_candidate(bundle)
    for sport in (0, 1):
        index = np.flatnonzero(val & (sports == sport))[0]
        local_index = int(val[:index].sum())
        np.testing.assert_allclose(loaded.predict_proba(x[index]), predictions['validation'][local_index], atol=2e-6)
    del loaded
    gc.collect()
    atomic_json(directory / 'predictions.json', rows)
    support = anatomy != 0
    result = dict(validation_loss=chosen['validation_loss'], selected_plastic_epoch=epoch,
        selected_decoder_epoch=chosen['selected_epoch'], metrics=measures, checkpoints=comparisons,
        curve=chosen['curve'], plasticity_curve=plastic_curve, neural_statistics=neural_stats,
        gain_statistics=dict(minimum=float(gains[support].min()), maximum=float(gains[support].max()),
            changed_edges=int(np.count_nonzero(abs(gains[support] - 1) > 1e-6)),
            bound_fraction=float((abs(np.log(gains[support])) > .29).mean())),
        wall_seconds=time.monotonic() - started, completed_at=utcnow(), bundle=str(bundle),
        artifact_hashes={str(p.relative_to(directory)): digest(p) for p in directory.rglob('*') if p.is_file()})
    atomic_json(result_path, result)
    for path in (result_path, directory / 'predictions.json', bundle, bundle.parent / 'parameters.npz'):
        registry.artifact(path, job=job['id'])
    registry.update(job, **result, status='complete', phase='complete', completed=1, total=1, error=None)
    print(json.dumps({'job': job['id'], 'status': 'complete', 'validation_loss': result['validation_loss']}), flush=True)


def finalize(registry, protocol, baseline_rows, root):
    jobs = registry.manifest['jobs']
    pending = [j['id'] for j in jobs if j['status'] in ('queued', 'running', 'paused')]
    if pending:
        raise ValueError(f'Cannot finalize pending jobs: {pending}')
    rows = list(baseline_rows)
    for job in jobs:
        if job['status'] == 'complete':
            rows.extend(json.loads((registry.directory / 'runs' / job['id'] / 'predictions.json').read_text()))
    selected = select_architecture(jobs)
    selected_jobs = [j for j in jobs if j['variant'] == selected and j['status'] == 'complete']
    ensemble_rows = []
    for split in ('validation', 'historical'):
        grouped = {}
        for row in rows:
            if row['model'] == selected and row['split'] == split:
                grouped.setdefault(row['game_id'], []).append(row)
        for values in grouped.values():
            assert len(values) == 3
            p = np.mean([r['probabilities'] for r in values], axis=0)
            for seed in protocol['seeds']:
                ensemble_rows.append(dict(values[0], probabilities=p.tolist(), model='selected-ensemble', seed=seed))
    rows.extend(ensemble_rows)
    aggregate = []
    for variant in (*VARIANTS, 'frequency-prior', 'feature-logistic', 'selected-ensemble'):
        for split in ('validation', 'historical'):
            for sport in ('soccer', 'baseball'):
                found = [r for r in rows if (r['model'], r['split'], r['sport']) == (variant, split, sport)]
                if not found:
                    continue
                seeds = []
                for seed in protocol['seeds']:
                    subset = [r for r in found if r['seed'] == seed]
                    if subset:
                        seeds.append(dict(seed=seed, **metrics([r['outcome'] for r in subset],
                                                              [r['probabilities'] for r in subset])))
                aggregate.append(dict(variant=variant, sport=sport, split=split, seeds=seeds,
                    mean={key: float(np.mean([r[key] for r in seeds])) for key in ('log_loss', 'brier', 'accuracy', 'ece')},
                    seed_spread={key: [min(r[key] for r in seeds), max(r[key] for r in seeds)]
                                 for key in ('log_loss', 'brier', 'accuracy', 'ece')}))
    paired = paired_week_bootstrap(rows, seed=protocol['bootstrap_seed'], replicates=protocol['bootstrap_replicates'])
    decisions = [c for c in paired['comparisons'] if c['left'] == 'selected-ensemble']
    report = dict(id=registry.manifest['id'], completed_at=utcnow(), selected_architecture=selected,
        selection='Mean equal-sport validation log loss across three seeds; fewer active parameters, then variant ID break ties.',
        historical_label='Historical development benchmark; already informed the design, never used for candidate selection.',
        active_model='v1 remains active', comparison=aggregate, paired=paired, decisions=decisions,
        null_controls=registry.manifest.get('null_controls', {}),
        completion_scope=registry.manifest.get('completion_scope', 'original-matrix'),
        original_matrix_complete=all(j['status'] == 'complete' for j in jobs),
        execution_amendments=registry.manifest.get('execution_amendments', []),
        cancelled_jobs=[dict(id=j['id'], reason=j['cancellation_reason']) for j in jobs if j['status'] == 'cancelled'],
        failed_jobs=[dict(id=j['id'], error=j.get('error')) for j in jobs if j['status'] == 'failed'],
        limitations=['Fixed protocol; no added seeds, architectures, or hyperparameter searches.',
                     'Topology conclusions apply only to the named frozen-temporal and shared-temporal comparisons.',
                     'No result establishes intelligence, natural fly cognition, or profitable betting.',
                     'Prospective cohorts remain pending until 100 soccer and 1000 baseball eligible completed fixtures.'])
    if report['execution_amendments']:
        report['selection'] += ' Only architectures with all three completed seeds are eligible.'
        report['limitations'].extend([
            'The user stopped remaining temporal runs after observing their poor results. '
            'This is a curtailed development experiment, not a completed original matrix.',
            'Temporal and topology comparisons have incomplete seed coverage; intervals do not account '
            'for the result-dependent stopping decision. Underperformance alone does not establish an implementation bug.'])
        paired['limitation'] += ' Temporal runs were curtailed after results were observed; inspect matched seed counts.'
    atomic_json(registry.directory / 'report.json', report)
    atomic_json(registry.directory / 'all-predictions.json', rows)
    for name in ('report.json', 'all-predictions.json'):
        registry.artifact(registry.directory / name)
    pointer_path = root / 'output/v2-shadow.json'
    bundles = [{'path': j['bundle'], 'sha256': digest(Path(j['bundle'])), 'seed': j['seed'],
                'parameters_sha256': digest(Path(j['bundle']).parent / 'parameters.npz')} for j in selected_jobs]
    pointer = dict(schema_version=2, experiment_id=registry.manifest['id'], variant=selected,
                   bundles=bundles, baseline_path=str(registry.directory / 'baseline.json'),
                   baseline_sha256=digest(registry.directory / 'baseline.json'), activated_at=utcnow(),
                   thresholds={'soccer': 100, 'baseball': 1000})
    if pointer_path.exists():
        previous = json.loads(pointer_path.read_text())
        if previous['experiment_id'] == pointer['experiment_id']:
            pointer = previous
        else:
            raise ValueError('A different shadow candidate is already frozen; active candidate was preserved.')
    else:
        atomic_json(pointer_path, pointer)
    registry.manifest.update(status='complete', completed_at=utcnow(), selected_shadow=pointer,
                             comparison=aggregate, paired=paired, decisions=decisions)
    registry.save()
    return report


def run_v2(protocol_path, *, resume=True, root=ROOT) -> dict:
    from .null_graph import make_null_graph
    root = Path(root)
    protocol = json.loads(Path(protocol_path).read_text())
    if protocol['schema_version'] != 2 or protocol['duration_ms'] != 80 or protocol['window_ms'] != 20:
        raise ValueError('Unsupported v2 protocol.')
    with writer_lock(root / 'output/experiments'):
        registry, biological_hashes = prepare_experiment(root, protocol, resume)
        verify_completed_jobs(registry)
        if registry.manifest['status'] == 'complete':
            return json.loads((registry.directory / 'report.json').read_text())
        record_execution(registry)
        x, y, sports, splits, games = load_source(registry.directory / 'source')
        input_mean, input_std = fit_scale(x[splits['train']])
        z = scale(x, input_mean, input_std)
        models, baseline_predictions = fit_baselines(z, y, sports, splits)
        atomic_json(registry.directory / 'baseline.json', dict(schema_version=2, models=models,
                    input_mean=input_mean.tolist(), input_std=input_std.tolist()))
        baseline_rows = []
        for (variant, split), p in baseline_predictions.items():
            for seed in protocol['seeds']:
                baseline_rows.extend(export_rows(games, y, p, mask=splits[split], variant=variant, seed=seed, split=split))
        atomic_json(registry.directory / 'baseline-predictions.json', baseline_rows)
        registry.artifact(registry.directory / 'baseline.json')
        registry.artifact(registry.directory / 'baseline-predictions.json')
        for seed in protocol['seeds']:
            for graph_kind in ('bio', 'null'):
                jobs = [j for j in registry.manifest['jobs'] if j['seed'] == seed
                        and j['variant'].startswith(graph_kind) and j['status'] != 'cancelled']
                if all(j['status'] == 'complete' for j in jobs):
                    continue
                initial_job = next(j for j in jobs if j['status'] != 'complete')
                graph_path = registry.directory / ('graphs/biological' if graph_kind == 'bio' else f'graphs/null-{seed}')
                try:
                    if graph_kind == 'null':
                        registry.update(initial_job, status='running', phase='generating-null-graph', started_at=utcnow())
                        report_path = graph_path / 'invariant-report.json'
                        control = make_null_graph(
                            registry.directory / 'graphs/biological', graph_path, seed=seed, sweeps=protocol['null_sweeps'])
                        registry.manifest.setdefault('null_controls', {})[str(seed)] = control
                        registry.artifact(report_path)
                        registry.save()
                        if not control['valid']:
                            raise ValueError('Null control has no changed edges or plastic edges; excluded from topology conclusions.')
                    graph = biological_hashes if graph_kind == 'bio' else graph_hashes(graph_path)
                    brain = FlyBrain(graph_path)
                    gains = np.ones(brain.plastic.shape, np.float32)
                    registry.update(initial_job, status='running', phase='initial-full-simulator', started_at=utcnow(),
                                    execution_id=registry.execution_id)
                    initial = simulation_cache(brain, z, registry.directory / 'cache', graph=graph, gains=gains,
                        seed=seed, workers=protocol['workers'], include_kc=True,
                        progress=lambda **fields: registry.update(initial_job, phase='initial-full-simulator', **fields))
                    del brain
                    gc.collect()
                except Exception as exc:
                    for job in jobs:
                        if job['status'] != 'complete':
                            registry.update(job, status='failed', phase='graph-initialization', error=str(exc),
                                            error_type=type(exc).__name__)
                    if graph_kind == 'bio':
                        raise
                    continue
                for job in jobs:
                    if job['status'] == 'complete':
                        continue
                    registry.update(job, status='running', phase='starting', started_at=utcnow(), error=None,
                                    execution_id=registry.execution_id)
                    try:
                        _fit_neural_job(registry, job, protocol, x, y, sports, splits, games, initial,
                                        graph_path, graph, input_mean, input_std)
                    except BaseException as exc:
                        registry.update(job, status='failed', error=str(exc), error_type=type(exc).__name__)
                        raise
                del initial
                gc.collect()
        return finalize(registry, protocol, baseline_rows, root)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', default='configs/experiment-v2.json')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    result = run_v2(args.protocol, resume=args.resume)
    print(json.dumps({'id': result['id'], 'selected_architecture': result['selected_architecture']}), flush=True)
