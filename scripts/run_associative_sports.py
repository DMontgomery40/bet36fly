"""Stage 4: chronological online associative learning through one MLB season, per arm.

Usage: run_associative_sports.py --protocol configs/associative-sports-01.json --arm plastic [--learning-rate 2e-5]
Each (protocol, arm, learning rate) produces its own immutable identity under output/associative/.
Evaluation across arms is a separate step (--evaluate) that only reads saved rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly import associative_sports as sp  # noqa: E402
from bet36fly.associative import build_circuit  # noqa: E402
from bet36fly.connectome import ROOT  # noqa: E402
from bet36fly.associative import atomic_json  # noqa: E402


def load_season(root, protocol, games_path=None):
    games = json.loads((root / (games_path or protocol['games'])).read_text())
    history = [g for g in games if g['season'] in protocol['history_seasons']]
    season = [g for g in games if g['season'] == protocol['season']]
    rows, x, y = sp.season_rows(history + season, protocol['season'])
    if not np.isin(y, [0, 2]).all():
        raise ValueError('Season rows must all be final home/away results.')
    return rows, x, y


def arm_identity(protocol_raw, arm, learning_rate):
    return 'associative-sports-' + hashlib.sha256(protocol_raw + f'|{arm}|{learning_rate!r}'.encode()).hexdigest()[:20]


def run_arm(protocol_path, arm, learning_rate, root=ROOT, day_limit=None):
    raw = protocol_path.read_bytes()
    protocol = json.loads(raw)
    circuit_protocol = json.loads((root / protocol['circuit']).read_text())
    identity = arm_identity(raw, arm, learning_rate)
    out = root / 'output/associative' / identity
    if out.exists():
        raise ValueError('Refusing an existing sports arm identity.')
    out.mkdir(parents=True)
    (out / 'protocol.json').write_bytes(raw)
    candidate = sp.load_candidate(root, protocol)
    rows, x, y = load_season(root, protocol)
    innate = sp.innate_features(x, candidate)
    circuit = build_circuit(root, circuit_protocol)
    permutation = None
    if arm == 'shuffled':
        permutation = sp.within_week_permutation([g['start_time'] for g in rows], protocol['shuffle_seed'])
    outcomes = (y == 0).astype(int) * 1 + (y == 2).astype(int) * 2  # 1 home, 2 away
    labels = np.where(y == 0, 1, 2)
    learner = sp.SeasonLearner(circuit, circuit_protocol, arm=arm, games=rows, features=x, innate=innate,
                               outcomes=labels, week_permutation=permutation, out_dir=out, learning_rate=learning_rate)
    manifest = dict(identity=identity, arm=arm, learning_rate=learning_rate, status='running', season=protocol['season'],
                    games=len(rows), anatomy=circuit['anatomy'], calls=0, days=[], started=time.time())
    start = time.monotonic()

    def progress(state):
        manifest.update(calls=state.calls, reinforcements=state.reinforcements, days=state.days,
                        cache=dict(hits=state.cache.hits, misses=state.cache.misses), wall_seconds=time.monotonic() - start)
        atomic_json(out / 'manifest.json', manifest)
        if state.calls > protocol['call_cap_per_arm'] or time.monotonic() - start > protocol['wall_cap_seconds_per_arm']:
            raise RuntimeError('Declared per-arm budget exhausted.')

    atomic_json(out / 'manifest.json', manifest)
    try:
        learner.run(progress=progress, day_limit=day_limit)
        atomic_json(out / 'rows.json', learner.rows)
        manifest.update(status='completed', rows_sha256=hashlib.sha256((out / 'rows.json').read_bytes()).hexdigest(),
                        final_gains_sha256=learner.engine.gains_sha256(), outcomes=int(outcomes.sum()))
    except Exception as exc:
        manifest.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        manifest['wall_seconds'] = time.monotonic() - start
        atomic_json(out / 'manifest.json', manifest)
    return manifest


def evaluate(protocol_path, arm_ids, root=ROOT, learning_rate=None):
    raw = protocol_path.read_bytes()
    protocol = json.loads(raw)
    candidate = sp.load_candidate(root, protocol)
    rows, x, y = load_season(root, protocol)
    arms = {}
    manifests = {}
    for arm, identity in arm_ids.items():
        directory = root / 'output/associative' / identity
        manifest = json.loads((directory / 'manifest.json').read_text())
        # Arm keys may carry a ':label' suffix (e.g. 'plastic:baseline') to include a comparator arm of another protocol.
        if manifest['status'] != 'completed' or manifest['arm'] != arm.split(':')[0]:
            raise ValueError(f'Arm {arm} is not a completed run.')
        saved = json.loads((directory / 'rows.json').read_text())
        if [r['game_id'] for r in saved] != [g['id'] for g in rows]:
            raise ValueError('Saved rows do not match the season games.')
        arms[arm] = np.array([r['innate'] + r['learned'] for r in saved], float)
        manifests[arm] = manifest
    yy = (y == 0).astype(int)
    dates = [g['start_time'] for g in rows]
    split = np.array([sp._parse(d) < sp._parse(protocol['readout_split']) for d in dates])
    wins = sp.delayed_cumulative_wins(rows, y)
    result = sp.evaluate_arms(arms, x, wins, yy, dates, split, candidate, ~split, protocol['readout_C'])
    identity = 'associative-sports-evaluation-' + hashlib.sha256(
        raw + json.dumps(arm_ids, sort_keys=True).encode()).hexdigest()[:20]
    out = root / 'output/associative' / identity
    out.mkdir(parents=True, exist_ok=True)
    payload = dict(identity=identity, arms=arm_ids, learning_rate=learning_rate, season=protocol['season'],
                   readout_split=protocol['readout_split'], training_games=int(split.sum()),
                   evaluation_games=int((~split).sum()), evaluation=result['evaluation'], readouts=result['readouts'],
                   arm_manifests={k: {f: v.get(f) for f in ('identity', 'calls', 'reinforcements', 'wall_seconds', 'final_gains_sha256')}
                                  for k, v in manifests.items()})
    atomic_json(out / 'evaluation.json', payload)
    with (out / 'predictions.csv').open('w') as f:
        names = list(result['predictions'])
        f.write(','.join(['game_id', 'start_time', 'home', 'away', 'home_win', 'training_row'] + names) + '\n')
        for i, g in enumerate(rows):
            f.write(','.join([g['id'], g['start_time'], g['home'], g['away'], str(int(yy[i])), str(int(split[i]))]
                             + [repr(float(result['predictions'][n][i])) for n in names]) + '\n')
    print(json.dumps({k: v for k, v in result['evaluation'].items() if k in ('metrics', 'paired_loss', 'accuracy_interval',
                                                                             'plasticity_contributes', 'goal_passed')}, indent=2))
    return payload


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, default=ROOT / 'configs/associative-sports-01.json')
    parser.add_argument('--arm', choices=['plastic', 'frozen', 'shuffled'])
    parser.add_argument('--learning-rate', type=float, default=None)
    parser.add_argument('--day-limit', type=int, default=None)
    parser.add_argument('--evaluate', type=str, default=None, help='JSON mapping arm -> run identity')
    args = parser.parse_args()
    if args.evaluate:
        evaluate(args.protocol, json.loads(args.evaluate), learning_rate=args.learning_rate)
    else:
        run_arm(args.protocol, args.arm, args.learning_rate, day_limit=args.day_limit)
