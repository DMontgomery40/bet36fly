"""Load a real checkpoint, simulate upcoming fixtures, and retain paper proposals."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import threading

import numpy as np

from .brain import FlyBrain
from .connectome import ROOT, digest
from .experiment import DURATION_MS, NEURAL_SEED, scale, utcnow
from .features import build_features
from .learning import probabilities
from .ledger import PickLedger, fixture_identity
from .desk import build_desk


def read_json(path, default):
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return default


def upcoming_games(games, *, now=None, sport='all'):
    now = now or datetime.now(timezone.utc)
    return sorted([g for g in games if g['status'] == 'scheduled'
                   and datetime.fromisoformat(g['start_time'].replace('Z', '+00:00')) > now
                   and (sport == 'all' or g['sport'] == sport)], key=lambda g: (g['start_time'], g['id']))


def feature_identity(features):
    return hashlib.sha256(np.asarray(features, np.float32).tobytes()).hexdigest()


def probability_payload(game, p):
    p = np.asarray(p, dtype=float)
    if p.shape != (3,) or not np.isfinite(p).all() or np.any(p < 0) or not np.isclose(p.sum(), 1):
        raise ValueError('Invalid model probability output.')
    if game['sport'] == 'baseball' and p[1] != 0:
        raise ValueError('Baseball model emitted a draw.')
    index = int(p.argmax())
    return {'pick': ['home', 'draw', 'away'][index],
            'pick_label': [game['home'], 'Draw', game['away']][index],
            'probabilities': dict(zip(['home', 'draw', 'away'], map(float, p))),
            'confidence': float(p[index]), 'fair_odds': 1.0 / float(p[index])}


def brain_geometry(path=ROOT / 'data/brain', sample_size=2500):
    import pyarrow.feather as feather
    nodes = feather.read_table(path / 'nodes.feather').to_pandas()
    valid = [i for i, xyz in enumerate(nodes.somaLocation) if xyz is not None and len(xyz) == 3]
    indices = np.array(valid, np.int32)[np.linspace(0, len(valid) - 1, min(sample_size, len(valid)), dtype=int)]
    coords = np.stack(nodes.somaLocation.iloc[indices]).astype(float)
    center = (coords.max(0) + coords.min(0)) / 2
    coords = (coords - center) / ((coords.max(0) - coords.min(0)).max() / 2)
    selected = nodes.iloc[indices]
    points = [{'id': str(row.bodyId), 'x': float(xyz[0]), 'y': float(xyz[1]), 'z': float(xyz[2]),
               'type': str(row.type or 'unassigned'), 'group': str(row.superclass)}
              for (_, row), xyz in zip(selected.iterrows(), coords)]
    ptr, post, counts = [np.load(path / (s + '.npy'), mmap_mode='r') for s in ('indptr', 'post', 'counts')]
    lookup = np.full(len(nodes), -1, np.int32)
    lookup[indices] = np.arange(len(indices))
    edges = []
    for pre_local, pre in enumerate(indices):
        lo, hi = ptr[pre:pre + 2]
        local = lookup[post[lo:hi]]
        for k in np.flatnonzero((local >= 0) & (counts[lo:hi] >= 5)):
            edges.append((float(counts[lo + k]), pre_local, int(local[k])))
    edges.sort(reverse=True)
    payload = {'dataset': 'MaleCNS v1.0', 'nodes': points, 'edges': [[a, b] for _, a, b in edges[:3500]],
               'displayed_neurons': len(points), 'total_neurons': len(nodes),
               'coordinate_note': 'Sampled actual soma positions in MaleCNS coordinates; normalized uniformly. '
                                  'Displayed connections are a strong-edge subset for readability. '
                                  'All retained neurons and connections participate in simulation.'}
    return indices, payload


class Runtime:
    def __init__(self, root=ROOT):
        self.root = root
        self.lock = threading.RLock()
        self.ledger = PickLedger(root / 'data/picks.sqlite3')
        self.brain = None
        self.checkpoint = None
        self.model_pointer = None
        self.report = None
        self.snapshot = {'games': [], 'sources': [], 'updated_at': None}
        self.features = {}
        self.refresh_state = {'status': 'idle', 'message': 'Public game sources ready.'}
        self.refresh_lock = threading.Lock()
        self.geometry_indices = None
        self.geometry = None
        self.reload_games()

    def reload_games(self):
        snapshot = read_json(self.root / 'data/sports/games.json', self.snapshot)
        built = build_features(snapshot['games'])
        with self.lock:
            self.snapshot = snapshot
            self.features = {g['id']: x for g, x in zip(built['games'], built['X'])}

    def ensure_model(self):
        pointer = read_json(self.root / 'output/current-model.json', None)
        if pointer is None:
            return False
        with self.lock:
            if self.model_pointer == pointer:
                return True
            checkpoint_path = Path(pointer['checkpoint'])
            if digest(checkpoint_path) != pointer['checkpoint_sha256']:
                raise ValueError('Checkpoint hash mismatch; refusing to load modified weights.')
            report = read_json(pointer['report'], {})
            manifest = read_json(self.root / 'data/brain/manifest.json', {})
            if report.get('source_hashes') != manifest.get('source_hashes'):
                raise ValueError('Checkpoint belongs to a different connectome dataset.')
            with np.load(checkpoint_path, allow_pickle=False) as data:
                ck = {key: data[key].copy() for key in data.files}
            if any(not np.isfinite(a).all() for a in ck.values()):
                raise ValueError('Checkpoint contains nonfinite parameters.')
            if np.any(ck['input_std'] <= 0) or np.any(ck['output_std'] <= 0):
                raise ValueError('Checkpoint contains invalid scaling.')
            brain = FlyBrain(self.root / 'data/brain', gains=ck['gains'])
            if ck['weight'].shape != (2, 3, brain.output_dim):
                raise ValueError('Readout dimension does not match the full neural graph.')
            self.brain, self.checkpoint, self.report, self.model_pointer = brain, ck, report, pointer
            return True

    def get_geometry(self):
        with self.lock:
            if self.geometry is None:
                self.geometry_indices, self.geometry = brain_geometry(self.root / 'data/brain')
            return self.geometry

    def sources(self):
        return [dict(s, name=s.get('name', s.get('id', 'Source')),
                     status='fresh' if s['status'] == 'ok' else s['status']) for s in self.snapshot['sources']]

    def games(self, sport='all'):
        with self.lock:
            run_id = self.model_pointer['run_id'] if self.model_pointer else None
            latest = self.ledger.latest(run_id) if run_id else {}
            result = []
            for g in upcoming_games(self.snapshot['games'], sport=sport):
                row = dict(g)
                pick = latest.get(g['id'])
                if (pick and pick['feature_hash'] == feature_identity(self.features[g['id']])
                        and fixture_identity(pick) == fixture_identity(g)):
                    row['prediction'] = pick
                result.append(row)
            return result

    def desk(self, sport='all'):
        with self.lock:
            result = build_desk(self.ledger.all(), self.snapshot['games'], sport=sport)
            result['sources_updated_at'] = self.snapshot['updated_at']
            result['sources'] = self.sources()
            result['refresh_interval_seconds'] = 900
            return result

    def predict(self, game_id, *, trace=True):
        if not self.ensure_model():
            raise RuntimeError('The real neural checkpoint is still training.')
        with self.lock:
            matches = [g for g in upcoming_games(self.snapshot['games']) if g['id'] == game_id]
            if not matches:
                raise LookupError('This fixture is no longer scheduled in the future. Refresh the games.')
            game = matches[0]
            x = self.features[game_id].copy()
            ck, brain, pointer = self.checkpoint, self.brain, self.model_pointer
            if trace:
                self.get_geometry()
            z = scale(x, ck['input_mean'], ck['input_std'])
            response = brain.simulate(z, seed=NEURAL_SEED, duration_ms=DURATION_MS,
                                       sample=self.geometry_indices if trace else None)
            output = scale(np.log1p(response['readout'])[None], ck['output_mean'], ck['output_std'])
            p = probabilities(output, np.array([game['sport'] == 'baseball'], np.int64),
                              ck['weight'], ck['bias'])[0]
            # Recheck immediately before proposing a pick; a fixture may start during inference.
            if not upcoming_games([game]):
                raise LookupError('Fixture started during inference; no new paper pick was recorded.')
            proposal = dict(probability_payload(game, p), game_id=game_id, sport=game['sport'],
                            home=game['home'], away=game['away'], start_time=game['start_time'],
                            run_id=pointer['run_id'], model_hash=pointer['checkpoint_sha256'],
                            feature_hash=feature_identity(x), created_at=utcnow(),
                            source_url=game['source_url'], source_fetched_at=game['source_fetched_at'])
            saved = self.ledger.add(proposal)
            result = {'game': game, 'prediction': saved}
            if trace:
                result['activity'] = {'rates': response['rates'][self.geometry_indices].tolist(),
                    'trace': response['trace'].tolist(), 'population': response['population'].tolist(),
                    'bin_ms': response['bin_ms'], 'duration_ms': response['duration_ms'],
                    'active_neurons': int((response['counts'] > 0).sum()),
                    'total_spikes': int(response['counts'].sum()), 'wall_seconds': response['wall_seconds'],
                    'seed': NEURAL_SEED}
            return result

    def warm_picks(self):
        if not self.ensure_model():
            return 0
        games = self.games()
        total = 0
        for game in games:
            if not game.get('prediction'):
                try:
                    self.predict(game['id'], trace=False)
                    total += 1
                except LookupError:
                    continue
        return total

    def refresh(self):
        if not self.refresh_lock.acquire(blocking=False):
            return False
        self.refresh_state = {'status': 'running', 'message': 'Fetching current public game sources.'}

        def work():
            try:
                from .sports import refresh_games
                refreshed = refresh_games(self.root / 'data/sports')
                self.reload_games()
                self.refresh_state['message'] = 'Running the fly on upcoming fixtures.'
                count = self.warm_picks()
                failed = [s for s in refreshed['sources'] if s['status'] in ('failed', 'stale')]
                self.refresh_state = {'status': 'complete' if not failed else 'failed',
                    'message': f'{count} new paper picks. ' + (f'{len(failed)} sources unavailable or stale.'
                                                             if failed else 'Public schedules refreshed.'),
                    'updated_at': utcnow()}
            except Exception as exc:
                self.refresh_state = {'status': 'failed', 'message': str(exc), 'updated_at': utcnow()}
            finally:
                self.refresh_lock.release()
        threading.Thread(target=work, daemon=True, name='fixture-refresh').start()
        return True

    def status(self):
        ready = self.ensure_model()
        manifest = read_json(self.root / 'data/brain/manifest.json', {'stats': {}})
        return {'app': 'BET36FLY', 'mode': 'paper', 'model_ready': ready,
                'run_id': self.model_pointer['run_id'] if ready else None, 'runtime': 'CPU',
                'brain': manifest['stats'], 'training': read_json(self.root / 'output/training-progress.json',
                                                                {'status': 'not_started', 'stage': 'not_started'}),
                'refresh': self.refresh_state, 'updated_at': self.snapshot['updated_at'], 'sources': self.sources()}
