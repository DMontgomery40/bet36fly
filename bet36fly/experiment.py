"""Reproducible real-data experiment; final evaluation always uses full LIF spikes."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from .brain import FlyBrain
from .connectome import ROOT, digest
from .learning import fit_plasticity, fit_readout, probabilities, metrics

NEURAL_SEED = 42
DURATION_MS = 80


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.partial')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def chronological_split(games):
    dates = []
    for g in games:
        d = datetime.fromisoformat(g['start_time'].replace('Z', '+00:00'))
        if d.tzinfo is None:
            raise ValueError('Game timestamps must include timezone.')
        dates.append(d.astimezone(timezone.utc).isoformat())
    d = np.array(dates)
    return (d < '2025-07-01', (d >= '2025-07-01') & (d < '2026-01-01'),
            (d >= '2026-01-01') & (d < '2026-09-01'))


def fit_scale(x):
    return x.mean(0).astype(np.float32), np.maximum(x.std(0), 0.01).astype(np.float32)


def scale(x, mean, std):
    return np.clip((x - mean) / std, -8, 8).astype(np.float32)


def cache_identity(x, graph_hash, gain_hash, code_hash):
    h = hashlib.sha256(np.ascontiguousarray(x).tobytes())
    h.update(json.dumps([x.shape, str(x.dtype), graph_hash, gain_hash, code_hash,
                         NEURAL_SEED, DURATION_MS, 0.2]).encode())
    return h.hexdigest()


def simulate_dataset(brain, x, run_dir, stage, *, workers=4, progress=None):
    identity = cache_identity(x, digest(brain.path / 'source-lock.json'),
                              hashlib.sha256(brain.engine.weights.tobytes()).hexdigest(),
                              digest(Path(__file__).with_name('lif.cpp')) +
                              digest(Path(__file__).with_name('brain.py')))
    cache_dir = ROOT / 'data/neural-cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f'{identity}.npz'
    if path.exists():
        with np.load(path, allow_pickle=False) as saved:
            return {k: saved[k].copy() for k in saved.files}
    activity = np.empty((len(x), brain.output_dim), np.float32)
    kc = np.empty((len(x), len(brain.kc)), np.float32)
    active = np.empty(len(x), np.int32)
    spikes = np.empty(len(x), np.int32)

    def trial(row):
        r = brain.simulate(row, seed=NEURAL_SEED, duration_ms=DURATION_MS)
        return r['readout'], r['kc_rates'], int((r['counts'] > 0).sum()), int(r['counts'].sum())

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, result in enumerate(pool.map(trial, x)):
            activity[i], kc[i], active[i], spikes[i] = result
            if progress and (i % 64 == 0 or i + 1 == len(x)):
                elapsed = time.monotonic() - started
                progress(stage, completed=i + 1, total=len(x), elapsed_seconds=elapsed,
                         estimated_remaining_seconds=elapsed / (i + 1) * (len(x) - i - 1))
    result = dict(activity=activity, kc=kc, active=active, spikes=spikes)
    temp = path.with_suffix('.partial.npz')
    np.savez_compressed(temp, **result)
    temp.replace(path)
    atomic_json(run_dir / (stage + '-cache.json'), {'identity': identity, 'rows': len(x), 'path': str(path)})
    return result


def baseline_predictions(x, y, sport, train, val, test):
    from sklearn.linear_model import LogisticRegression
    prior = np.zeros((int(test.sum()), 3), np.float64)
    logistic = prior.copy()
    for s in (0, 1):
        tr, te = train & (sport == s), sport[test] == s
        frequency = np.bincount(y[tr], minlength=3).astype(float) + 1
        if s == 1:
            frequency[1] = 0
        prior[te] = frequency / frequency.sum()
        # Feature baseline uses the same standardized pregame observations.
        # Regularization chosen by validation only, independently by sport.
        candidates = []
        for strength in [.01, .1, 1.0]:
            model = LogisticRegression(C=strength, max_iter=1000).fit(x[tr], y[tr])
            v = np.zeros((int((val & (sport == s)).sum()), 3))
            v[:, model.classes_] = model.predict_proba(x[val & (sport == s)])
            candidates.append((metrics(y[val & (sport == s)], v)['log_loss'], model))
        model = min(candidates, key=lambda pair: pair[0])[1]
        p = np.zeros((int(te.sum()), 3))
        p[:, model.classes_] = model.predict_proba(x[test & (sport == s)])
        logistic[te] = p
    return prior, logistic


def _sport_metrics(y, p, sport):
    return {name: metrics(y[sport == index], p[sport == index])
            for index, name in enumerate(('soccer', 'baseball')) if np.any(sport == index)}


def run_experiment(*, workers=4, plastic_epochs=60, readout_epochs=180):
    started = time.monotonic()
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run_dir = ROOT / 'output/runs' / run_id
    run_dir.mkdir(parents=True)
    progress_path = ROOT / 'output/training-progress.json'

    def progress(stage, **values):
        payload = dict(run_id=run_id, status='running', stage=stage, updated_at=utcnow(), **values)
        atomic_json(progress_path, payload)
        print(json.dumps({k: v for k, v in payload.items() if k != 'curve'}), flush=True)

    progress('loading_data')
    source = json.loads((ROOT / 'data/sports/dataset-games.json').read_text())
    games = source['games'] if isinstance(source, dict) else source
    data = np.load(ROOT / 'data/sports/dataset.npz', allow_pickle=False)
    all_x, all_y = data['X'], data['y']
    if all_x.shape != (len(games), 16) or not np.isfinite(all_x).all():
        raise ValueError('Expected aligned 16-channel finite features and game rows.')
    valid = (all_y >= 0) & np.array([g['status'] == 'final' for g in games])
    games = [g for g, keep in zip(games, valid) if keep]
    x, y = all_x[valid], all_y[valid].astype(np.int64)
    train, val, test = chronological_split(games)
    used = train | val | test
    games = [g for g, keep in zip(games, used) if keep]
    x, y = x[used], y[used]
    train, val, test = chronological_split(games)
    sport = np.array([g['sport'] == 'baseball' for g in games], np.int64)
    np.savez_compressed(run_dir / 'training-data.npz', X=x, y=y, sport=sport,
                        train=train, validation=val, test=test)
    atomic_json(run_dir / 'training-games.json', {'games': games})
    for split in (train, val, test):
        for s in (0, 1):
            if int((split & (sport == s)).sum()) < 30:
                raise ValueError('Each chronological split needs at least 30 games per sport.')
    input_mean, input_std = fit_scale(x[train])
    z = scale(x, input_mean, input_std)
    splits = {name: {'n': int(mask.sum()), 'soccer': int((mask & (sport == 0)).sum()),
                      'baseball': int((mask & (sport == 1)).sum()),
                      'first': min(g['start_time'] for g, keep in zip(games, mask) if keep),
                      'last': max(g['start_time'] for g, keep in zip(games, mask) if keep)}
              for name, mask in [('train', train), ('validation', val), ('test', test)]}
    atomic_json(run_dir / 'split-manifest.json', {'splits': splits,
                'game_ids': {name: [g['id'] for g, keep in zip(games, mask) if keep]
                             for name, mask in [('train', train), ('validation', val), ('test', test)]},
                'feature_sha256': digest(ROOT / 'data/sports/dataset.npz'),
                'input_scaling_fit_on': 'train only'})
    brain = FlyBrain()
    progress('initial_full_brain', splits=splits)
    initial = simulate_dataset(brain, z, run_dir, 'initial_full_brain', workers=workers, progress=progress)
    log_activity, log_kc = np.log1p(initial['activity']), np.log1p(initial['kc'])
    amean, astd = fit_scale(log_activity[train])
    kmean, kstd = fit_scale(log_kc[train])
    a, k = scale(log_activity, amean, astd), scale(log_kc, kmean, kstd)
    # Frozen graph control trains its own head with the exact same partition.
    frozen = fit_readout(a[train], y[train], sport[train], a[val], y[val], sport[val], epochs=readout_epochs)
    progress('learning_anatomical_synapses', completed=0, total=plastic_epochs)
    plastic = fit_plasticity(brain.plastic.toarray(), a[train], k[train], y[train], sport[train],
                             a[val], k[val], y[val], sport[val], epochs=plastic_epochs,
                             progress=lambda curve: progress('learning_anatomical_synapses',
                                 completed=len(curve), total=plastic_epochs, curve=curve))
    if plastic['changed_synapses'] == 0:
        raise RuntimeError('Training did not modify anatomical synapses.')
    np.save(run_dir / 'learned-synaptic-gains.npy', plastic['gains'])
    progress('trained_full_brain', changed_synapses=plastic['changed_synapses'])
    trained_brain = FlyBrain(gains=plastic['gains'])
    changed = brain.engine.weights != trained_brain.engine.weights
    if int(changed.sum()) != plastic['changed_synapses']:
        # Float32 multiplication can round a sub-ULP gain; count actual changes separately.
        plastic['actual_changed_graph_edges'] = int(changed.sum())
    else:
        plastic['actual_changed_graph_edges'] = plastic['changed_synapses']
    if not np.array_equal(np.sign(brain.engine.weights), np.sign(trained_brain.engine.weights)):
        raise RuntimeError('Training changed biological transmitter signs.')
    learned = simulate_dataset(trained_brain, z, run_dir, 'trained_full_brain',
                                workers=workers, progress=progress)
    log_learned = np.log1p(learned['activity'])
    output_mean, output_std = fit_scale(log_learned[train])
    output = scale(log_learned, output_mean, output_std)
    final_head = fit_readout(output[train], y[train], sport[train], output[val], y[val], sport[val],
                             epochs=readout_epochs, progress=lambda curve: progress('fitting_spike_readout',
                                 completed=len(curve), total=readout_epochs, curve=curve))
    progress('held_out_evaluation')
    p = probabilities(output[test], sport[test], final_head['weight'], final_head['bias'])
    p_frozen = probabilities(a[test], sport[test], frozen['weight'], frozen['bias'])
    prior, feature_baseline = baseline_predictions(z, y, sport, train, val, test)
    # Readout-only permutation: the graph was already trained on true labels.
    # Epoch selection still uses true validation labels. This does not claim
    # to test a completely label-shuffled learning pipeline.
    shuffled_y = y[train].copy()
    rng = np.random.default_rng(991)
    for s in (0, 1):
        ix = np.flatnonzero(sport[train] == s)
        shuffled_y[ix] = rng.permutation(shuffled_y[ix])
    shuffled = fit_readout(output[train], shuffled_y, sport[train], output[val], y[val], sport[val],
                           epochs=readout_epochs)
    p_shuffled = probabilities(output[test], sport[test], shuffled['weight'], shuffled['bias'])
    # Causal wiring ablation: with all synapses zero, only externally driven ALPNs
    # spike. Those input cells are excluded from every readout channel.
    trained_brain.engine.weights.fill(0)
    ablated = trained_brain.simulate(z[0], seed=NEURAL_SEED, duration_ms=DURATION_MS)['readout']
    if np.any(ablated):
        raise RuntimeError('No-connectome control leaked externally driven inputs into the readout.')
    p_cut = probabilities(scale(np.zeros_like(output[test]), output_mean, output_std), sport[test],
                         final_head['weight'], final_head['bias'])
    # Checkpoint holds only arrays; no pickle or executable object deserialization.
    checkpoint = run_dir / 'checkpoint.npz'
    np.savez_compressed(checkpoint, gains=plastic['gains'], input_mean=input_mean, input_std=input_std,
                         output_mean=output_mean, output_std=output_std,
                         weight=final_head['weight'], bias=final_head['bias'])
    report = {
        'run_id': run_id, 'created_at': utcnow(), 'status': 'complete', 'runtime': 'CPU',
        'wall_seconds': time.monotonic() - started, 'dataset': brain.manifest['dataset'],
        'brain': brain.manifest['stats'], 'splits': splits, 'seed': NEURAL_SEED,
        'duration_ms': DURATION_MS, 'dt_ms': .2, 'stimulated_alpn_ports': 32,
        'neural_model': 'Full retained MaleCNS leaky integrate-and-fire network; Shiu et al. parameters.',
        'training_method': 'Bounded supervised rate-surrogate synaptic warm-up, then full LIF resimulation and final readout training.',
        'plasticity': {key: value for key, value in plastic.items() if key not in ('gains', 'curve')},
        'selected_epoch': final_head['selected_epoch'], 'curve': final_head['curve'],
        'plasticity_curve': plastic['curve'],
        'metrics': _sport_metrics(y[test], p, sport[test]),
        'controls': {
            'train_frequency_prior': _sport_metrics(y[test], prior, sport[test]),
            'pregame_feature_logistic': _sport_metrics(y[test], feature_baseline, sport[test]),
            'frozen_connectome_trained_readout': _sport_metrics(y[test], p_frozen, sport[test]),
            'shuffled_readout_labels_on_trained_wiring': _sport_metrics(y[test], p_shuffled, sport[test]),
            'silenced_connectome_fixed_readout': _sport_metrics(y[test], p_cut, sport[test]),
        },
        'control_protocols': {
            'shuffled_readout_labels_on_trained_wiring':
                'Only final readout training labels are shuffled within each sport. '
                'Synaptic gains remain trained on true training labels; epoch selection uses '
                'true validation labels. Not a whole-pipeline label permutation.',
        },
        'neural_evidence': {
            'mean_active_neurons': float(learned['active'].mean()),
            'mean_spikes_per_trial': float(learned['spikes'].mean()),
            'mean_absolute_readout_change_after_plasticity': float(abs(learned['activity'] - initial['activity']).mean()),
            'mean_probability_change_when_wiring_silenced': float(abs(p - p_cut).mean()),
            'anatomical_support_preserved': True, 'transmitter_signs_preserved': True,
        },
        'checkpoint_sha256': digest(checkpoint), 'source_hashes': brain.manifest['source_hashes'],
        'limitations': [
            'A wiring-derived experimental model, not a validated emulation of natural fly cognition.',
            'Sports numbers are injected through 32 explicitly artificial ALPN sensory ports.',
            'The learned artificial readout converts biological-network spikes into sports probabilities.',
            'The plasticity surrogate is an engineering learning rule, not a claim of biological dopamine learning.',
            'One seed, one chronological split and simple team-history features; no injuries or player prop data.',
            'Historical snapshots are retrospective; schedules/results may include later corrections.',
            'Silencing the full graph tests causal dependence, not predictive superiority of biological topology.',
            'Better than chance or changed weights do not establish profitable betting or biological validity.',
        ],
    }
    atomic_json(run_dir / 'report.json', report)
    # Every held-out pick is exported, not only wins or confident selections.
    test_games = [g for g, keep in zip(games, test) if keep]
    atomic_json(run_dir / 'backtest-picks.json', {'run_id': run_id, 'mode': 'retrospective_backtest',
        'picks': [dict(game_id=g['id'], sport=g['sport'], start_time=g['start_time'], home=g['home'],
                       away=g['away'], outcome=int(label), probabilities=prob.tolist(),
                       pick=int(prob.argmax()), correct=bool(prob.argmax() == label))
                  for g, label, prob in zip(test_games, y[test], p)]})
    atomic_json(ROOT / 'output/current-model.json', {'run_id': run_id, 'checkpoint': str(checkpoint),
                'report': str(run_dir / 'report.json'), 'checkpoint_sha256': report['checkpoint_sha256']})
    atomic_json(progress_path, {'run_id': run_id, 'status': 'complete', 'stage': 'complete',
                               'updated_at': utcnow(), 'report': str(run_dir / 'report.json')})
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--plastic-epochs', type=int, default=60)
    parser.add_argument('--readout-epochs', type=int, default=180)
    args = parser.parse_args()
    try:
        result = run_experiment(workers=args.workers, plastic_epochs=args.plastic_epochs,
                                readout_epochs=args.readout_epochs)
        print(json.dumps({'run_id': result['run_id'], 'metrics': result['metrics']}, indent=2))
    except Exception as exc:
        atomic_json(ROOT / 'output/training-progress.json',
                    {'status': 'failed', 'stage': 'failed', 'updated_at': utcnow(),
                     'error': str(exc), 'error_type': type(exc).__name__})
        raise
