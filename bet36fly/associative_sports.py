"""Stage 4: chronological online associative learning around the frozen sensory pipeline.

The circuit learns only from outcomes that would have been available (48-hour delay,
UTC-day batches, the same rule as the pregame features). Prediction probes never learn.
Probe responses are cached only under a key that includes the exact gain hash, so any
synaptic change invalidates the cache.
"""
from __future__ import annotations

from datetime import datetime, time as dtime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

from .associative import (array_sha256, drive_schedule, load_checkpoint, odor_schedule, save_checkpoint,
                          team_odor_types)
from .associative import atomic_json as _atomic_json
from .features import build_features
from .sensory_backtest import (_fit, encoder_probability, metrics, neural_features, paired_evaluation,
                               quality_keys, readout_probability, team_vectors, week_ids)

PROBE_SEED = 3001
DELAY_HOURS = 48


def _parse(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)


class ProbeCache:
    """Responses keyed by (cue key, gains hash, seed, schedule hash); a gain change invalidates."""

    def __init__(self):
        self.store = {}
        self.hits = 0
        self.misses = 0

    @staticmethod
    def key(team_key, gains_sha256, seed, schedule_sha256):
        return f'{team_key}|{gains_sha256}|{seed}|{schedule_sha256}'

    def get(self, key):
        value = self.store.get(key)
        self.hits += value is not None
        self.misses += value is None
        return value

    def put(self, key, value):
        self.store[key] = value


class SeasonLearner:
    """Runs one arm (plastic | frozen | shuffled) through a season chronologically."""

    def __init__(self, circuit, protocol, *, arm, games, features, innate, outcomes, week_permutation=None,
                 out_dir=None, learning_rate=None):
        self.circuit = circuit
        self.engine = circuit['engine']
        self.protocol = protocol
        self.arm = arm
        self.games = games
        self.features = features
        self.innate = innate
        self.outcomes = np.asarray(outcomes)
        self.out_dir = Path(out_dir) if out_dir else None
        if self.out_dir is not None:
            self.out_dir.mkdir(parents=True, exist_ok=True)
        code = protocol['odor_code']
        self.teams = sorted({g['home_key'] for g in games} | {g['away_key'] for g in games})
        self.odors = {t: team_odor_types(t, circuit['orn_types'], code['width'], code['salt']) for t in self.teams}
        self.timing = protocol['timing']
        self.outputs = circuit['outputs']
        self.sample = np.unique(np.concatenate(self.outputs))
        self.out_pos = [np.searchsorted(self.sample, o) for o in self.outputs]
        self.cache = ProbeCache()
        self.calls = 0
        self.reinforcements = 0
        self.rows = []
        self.days = []
        self.learning_rate = protocol['learning_rate'] if learning_rate is None else learning_rate
        self.engine.learning_rate = float(self.learning_rate)
        self.plastic = arm in ('plastic', 'shuffled')
        self.labels = self.outcomes.copy()
        if arm == 'shuffled':
            if week_permutation is None:
                raise ValueError('The shuffled arm needs a within-week permutation.')
            self.labels = self.outcomes[week_permutation]
        self.probe_schedule_sha256 = hashlib.sha256(json.dumps(self.timing, sort_keys=True).encode()).hexdigest()[:16]

    def _reinforce(self, index):
        """Winner's cue then the reinforcer; the loser receives nothing (measured null in Stage 3)."""
        game = self.games[index]
        winner = game['home_key'] if self.labels[index] == 1 else game['away_key']
        t = self.timing
        rates = odor_schedule(self.circuit, self.odors[winner], bins=t['reinforcement_bins'], start_bin=t['cue_bins'][0],
                              end_bin=t['cue_bins'][1], hz=self.protocol['odor_code']['hz'])
        drive = drive_schedule(self.circuit, bins=t['reinforcement_bins'], start_bin=t['us_bins'][0],
                               end_bin=t['us_bins'][1], hz=self.protocol['reinforcer']['hz'])
        seed = int(hashlib.sha256(f'reinforce:{game["id"]}'.encode()).hexdigest()[:8], 16)
        result = self.engine.run(rates, drive=drive, bin_ms=t['bin_ms'], seed=seed, plasticity=True)
        self.calls += 1
        self.reinforcements += 1
        return dict(game_id=game['id'], winner=winner, seed=seed, gains_before=result['gains_sha256_before'],
                    gains_after=result['gains_sha256_after'], changed_edges=int((result['gain_delta'] != 0).sum()),
                    reward_dan_spikes=int(result['counts'][self.engine.dan_indices].sum()),
                    bound_contacts=float(result['comp_bins'][:, :, 4:6].sum()), tail_spikes=int(result['population'][-5:].sum()))

    def _probe(self, team_key):
        gains_sha = self.engine.gains_sha256()
        key = ProbeCache.key(team_key, gains_sha, PROBE_SEED, self.probe_schedule_sha256)
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        t = self.timing
        rates = odor_schedule(self.circuit, self.odors[team_key], bins=t['probe_bins'], start_bin=t['cue_bins'][0],
                              end_bin=t['cue_bins'][1], hz=self.protocol['odor_code']['hz'])
        result = self.engine.run(rates, bin_ms=t['bin_ms'], seed=PROBE_SEED, sample=self.sample)
        self.calls += 1
        if result['gains_sha256_after'] != gains_sha:
            raise RuntimeError('A prediction probe changed synaptic gains.')
        lo, hi = t['cue_bins']
        window = result['trace'][lo:hi]
        response = [int(window[:, p].sum()) for p in self.out_pos]
        value = dict(response=response, gains_sha256=gains_sha, tail_spikes=int(result['population'][-5:].sum()))
        self.cache.put(key, value)
        return value

    def run(self, *, progress=None, cancelled=lambda: False, day_limit=None, resume_after=None, resume_gains=None,
            resume_rows=None, resume_days=None):
        """Chronological pass. Resume: skip days <= resume_after, starting from that day's saved gains/rows."""
        starts = [_parse(g['start_time']) for g in self.games]
        pending = []
        day_indices = {}
        for i, s in enumerate(starts):
            day_indices.setdefault(s.date(), []).append(i)
        if resume_after is not None:
            if resume_gains is None or resume_rows is None or resume_days is None:
                raise ValueError('Resume needs the saved gains, rows and day log.')
            self.engine.set_gains(np.asarray(resume_gains, np.float32))
            self.rows = list(resume_rows)
            self.days = list(resume_days)
            self.calls = self.days[-1]['calls'] if self.days else 0
            self.reinforcements = sum(d['reinforced'] for d in self.days)
        for day_number, day in enumerate(sorted(day_indices)):
            if day_limit is not None and day_number >= day_limit:
                break
            day_start = datetime.combine(day, dtime.min, timezone.utc)
            if resume_after is not None and day.isoformat() <= resume_after:
                # Replay only the availability bookkeeping; no native call, no gain change.
                pending = [i for i in pending if starts[i] + timedelta(hours=DELAY_HOURS) > day_start]
                pending.extend(day_indices[day])
                continue
            if cancelled():
                raise RuntimeError('Cancelled.')
            ready = [i for i in pending if starts[i] + timedelta(hours=DELAY_HOURS) <= day_start]
            pending = [i for i in pending if starts[i] + timedelta(hours=DELAY_HOURS) > day_start]
            applied = []
            if self.plastic:
                for i in sorted(ready, key=lambda k: (starts[k], self.games[k]['id'])):
                    applied.append(self._reinforce(i))
            gains_sha = self.engine.gains_sha256()
            for i in day_indices[day]:
                game = self.games[i]
                home = self._probe(game['home_key'])
                away = self._probe(game['away_key'])
                learned = [float(np.log1p(h) - np.log1p(a)) for h, a in zip(home['response'], away['response'])]
                self.rows.append(dict(index=i, game_id=game['id'], start_time=game['start_time'], home=game['home_key'],
                                      away=game['away_key'], outcome=int(self.outcomes[i]), learned=learned,
                                      home_response=home['response'], away_response=away['response'],
                                      innate=[float(x) for x in self.innate[i]], gains_sha256=gains_sha))
            pending.extend(day_indices[day])
            self.days.append(dict(day=day.isoformat(), reinforced=len(applied), games=len(day_indices[day]),
                                  gains_sha256=gains_sha, calls=self.calls,
                                  bound_contacts=float(sum(a['bound_contacts'] for a in applied)),
                                  reward_dan_spikes=int(sum(a['reward_dan_spikes'] for a in applied)),
                                  changed_edges=int(sum(a['changed_edges'] for a in applied))))
            if self.out_dir is not None:
                save_checkpoint(self.out_dir / f'checkpoint-{self.arm}-{day.isoformat()}.npz', self.engine,
                                identity=f'{self.arm}:{day.isoformat()}', note=f'end of UTC day {day.isoformat()}')
                _atomic_json(self.out_dir / 'rows.partial.json', dict(rows=self.rows, days=self.days))
            if progress is not None:
                progress(self)
        return self

    def matrix(self):
        z = np.array([r['innate'] + r['learned'] for r in self.rows], float)
        y = np.array([1 if r['outcome'] == 0 else 0 for r in self.rows])
        dates = [r['start_time'] for r in self.rows]
        return z, y, dates


def delayed_cumulative_wins(games, outcomes):
    """Per-game (home wins so far, away wins so far) under the same 48-hour/UTC-day availability rule."""
    starts = [_parse(g['start_time']) for g in games]
    wins = {}
    pending = []
    values = np.zeros((len(games), 2))
    days = {}
    for i, s in enumerate(starts):
        days.setdefault(s.date(), []).append(i)
    for day in sorted(days):
        day_start = datetime.combine(day, dtime.min, timezone.utc)
        ready = [i for i in pending if starts[i] + timedelta(hours=DELAY_HOURS) <= day_start]
        pending = [i for i in pending if starts[i] + timedelta(hours=DELAY_HOURS) > day_start]
        for i in ready:
            winner = games[i]['home_key'] if outcomes[i] == 0 else games[i]['away_key']
            wins[winner] = wins.get(winner, 0) + 1
        for i in days[day]:
            values[i] = [wins.get(games[i]['home_key'], 0), wins.get(games[i]['away_key'], 0)]
        pending.extend(days[day])
    return values


def within_week_permutation(dates, seed):
    weeks = week_ids(dates)
    rng = np.random.default_rng(seed)
    permutation = np.arange(len(dates))
    for w in np.unique(weeks):
        members = np.flatnonzero(weeks == w)
        permutation[members] = members[rng.permutation(len(members))]
    return permutation


def fit_arm_readout(z, y, train_mask, c=0.01):
    scales = np.maximum(z[train_mask].std(axis=0), 1e-8)
    model = _fit(z[train_mask] / scales, y[train_mask], c, False)
    return dict(C=c, scales=scales.tolist(), coef=model.coef_[0].tolist(), intercept=0.0)


def same_information_readout(x, wins, y, train_mask, c=0.01):
    home, away = team_vectors(x)
    delta = np.concatenate([home - away, (wins[:, :1] - wins[:, 1:]) / 10.0], axis=1)
    scales = np.maximum(delta[train_mask].std(axis=0), 1e-8)
    model = _fit(delta[train_mask] / scales, y[train_mask], c, True)
    from scipy.special import expit
    return expit(delta / scales @ model.coef_[0] + model.intercept_[0]), dict(C=c, scales=scales.tolist(),
                                                                              coef=model.coef_[0].tolist(),
                                                                              intercept=float(model.intercept_[0]))


def evaluate_arms(arms, x, wins, y, dates, train_mask, candidate, eval_mask, c=0.01):
    """Fixed readout procedure for every arm; returns per-arm probabilities and paired evaluation."""
    predictions = {}
    readouts = {}
    for name, z in arms.items():
        readouts[name] = fit_arm_readout(z, y, train_mask, c)
        predictions[name] = readout_probability(z, readouts[name])
    predictions['encoder_only'] = encoder_probability(x, candidate['encoder'])
    predictions['same_information'], readouts['same_information'] = same_information_readout(x, wins, y, train_mask, c)
    predictions['uniform'] = np.full(len(y), 0.5)
    predictions['prior'] = np.full(len(y), float(candidate['training_prior']))
    subset = {k: v[eval_mask] for k, v in predictions.items()}
    subset['neural'] = subset['plastic']
    evaluation = paired_evaluation(y[eval_mask], subset, np.asarray(dates)[eval_mask])
    evaluation['metrics'].pop('neural', None)
    evaluation['paired_loss'].pop('plastic', None)
    shuffled = None
    if 'shuffled' in arms:
        control = dict(subset, neural=subset['shuffled'])
        shuffled = paired_evaluation(y[eval_mask], control, np.asarray(dates)[eval_mask])['paired_loss']['frozen']
        evaluation['shuffled_minus_frozen'] = shuffled
    # Plasticity contributes only if the plastic circuit beats its matched frozen twin (upper bound below
    # zero) while the reinforcement-shuffled twin does not.
    evaluation['plasticity_contributes'] = bool(evaluation['paired_loss']['frozen']['interval'][1] < 0
                                                 and (shuffled is None or shuffled['interval'][1] >= 0))
    evaluation['training_metrics'] = {k: metrics(y[train_mask], v[train_mask]) for k, v in predictions.items()}
    return dict(predictions={k: v.tolist() for k, v in predictions.items()}, readouts=readouts, evaluation=evaluation)


def innate_features(x, candidate):
    keys = quality_keys(x, candidate['encoder'])
    return neural_features(keys, candidate['mean_outputs'])


def load_candidate(root, protocol):
    candidate = json.loads((Path(root) / protocol['sensory_candidate']).read_text())
    if hashlib.sha256((Path(root) / protocol['sensory_candidate']).read_bytes()).hexdigest() != protocol['sensory_candidate_sha256']:
        raise ValueError('Frozen sensory candidate changed.')
    return candidate


def season_rows(all_games, season):
    built = build_features(all_games)
    games = built['games']
    keep = np.array([g['season'] == season for g in games])
    return [g for g, k in zip(games, keep) if k], built['X'][keep], built['y'][keep]


def resume_state(out_dir, arm):
    """Latest saved day checkpoint for deterministic resume."""
    files = sorted(Path(out_dir).glob(f'checkpoint-{arm}-*.npz'))
    if not files:
        return None
    gains, meta = load_checkpoint(files[-1])
    return dict(path=str(files[-1]), gains=gains, meta=meta, day=files[-1].stem.split('-', 2)[2])


__all__ = ['SeasonLearner', 'ProbeCache', 'delayed_cumulative_wins', 'within_week_permutation', 'evaluate_arms',
           'innate_features', 'load_candidate', 'season_rows', 'resume_state', 'array_sha256']
