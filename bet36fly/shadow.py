"""Prospective v2 forecasts in a separate ledger; fixed first cohorts, no promotion."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

import numpy as np

from .connectome import digest
from .desk import resolved_result, timestamp
from .ledger import fixture_identity
from .learning import metrics

THRESHOLDS = {'soccer': 100, 'baseball': 1000}


def ensemble_probability(values):
    a = np.asarray(values, float)
    if a.shape != (3, 3) or not np.isfinite(a).all() or np.any(a < 0) or not np.allclose(a.sum(1), 1):
        raise ValueError('Shadow ensemble needs three normalized probability vectors.')
    return a.mean(0)


def model_identity(pointer):
    value = [pointer['experiment_id'], pointer['variant'], pointer['bundles'], pointer['baseline_sha256']]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def eligible(game, now):
    return game['status'] == 'scheduled' and timestamp(game['start_time']) > now


class ShadowLedger:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS forecasts (id TEXT PRIMARY KEY, model TEXT, sport TEXT, payload TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS scores (id TEXT PRIMARY KEY, payload TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS cohorts (model TEXT, sport TEXT, payload TEXT, PRIMARY KEY(model,sport))')

    def connect(self):
        return sqlite3.connect(self.path, timeout=30)

    def forecasts(self, model=None):
        with self.connect() as db:
            rows = db.execute('SELECT payload FROM forecasts WHERE model=? ORDER BY id', (model,)) if model else db.execute(
                'SELECT payload FROM forecasts ORDER BY id')
            return [json.loads(r[0]) for r in rows]

    def capture(self, game, features, *, pointer, predict, baseline_predict, current_fixture,
                clock=lambda: datetime.now(timezone.utc), feature_timestamp=None):
        now = clock()
        if now < timestamp(pointer['activated_at']) or not eligible(game, now):
            return None
        model, revision = model_identity(pointer), fixture_identity(game)
        key = hashlib.sha256(json.dumps([game['id'], revision, model]).encode()).hexdigest()
        with self.connect() as db:
            existing = db.execute('SELECT payload FROM forecasts WHERE id=?', (key,)).fetchone()
        if existing:
            return json.loads(existing[0])
        x = np.asarray(features, np.float32)
        values = predict(x)
        p = ensemble_probability(values)
        baseline = np.asarray(baseline_predict(x), float)
        if (baseline.shape != (3,) or not np.isfinite(baseline).all() or np.any(baseline < 0)
                or not np.isclose(baseline.sum(), 1)):
            raise ValueError('Invalid frozen feature-logistic output.')
        if game['sport'] == 'baseball' and (p[1] != 0 or baseline[1] != 0):
            raise ValueError('Baseball forecast contains a draw.')
        current, now = current_fixture(game['id']), clock()
        if current is None or fixture_identity(current) != revision or not eligible(current, now):
            return None
        cutoff = min(timestamp(current['start_time']), timestamp(current.get('actual_start_time', current['start_time'])))
        source_time = game.get('source_fetched_at')
        feature_time = feature_timestamp or source_time
        if now >= cutoff or not source_time or not feature_time:
            return None
        if timestamp(source_time) > now or timestamp(feature_time) > now:
            return None
        record = dict(id=key, model=model, experiment_id=pointer['experiment_id'], variant=pointer['variant'],
            game_id=game['id'], sport=game['sport'], home=game['home'], away=game['away'], revision=revision,
            start_time=current['start_time'], saved_at=now.isoformat(), cutoff=cutoff.isoformat(),
            probabilities=p.tolist(), seed_probabilities=np.asarray(values).tolist(),
            feature_logistic=baseline.tolist(), source_fetched_at=source_time, feature_timestamp=feature_time,
            source_url=game.get('source_url'), feature_sha256=hashlib.sha256(x.tobytes()).hexdigest())
        with self.connect() as db:
            db.execute('INSERT OR IGNORE INTO forecasts VALUES (?,?,?,?)',
                       (key, model, game['sport'], json.dumps(record, allow_nan=False)))
            return json.loads(db.execute('SELECT payload FROM forecasts WHERE id=?', (key,)).fetchone()[0])

    def score(self, games, *, model, now=None, thresholds=None):
        now, thresholds = now or datetime.now(timezone.utc), thresholds or THRESHOLDS
        current = {g['id']: g for g in games}
        with self.connect() as db:
            previous_scores = {r[0]: json.loads(r[1]) for r in db.execute('SELECT id,payload FROM scores')}
        scored = []
        for row in self.forecasts(model):
            game = current.get(row['game_id'])
            item = dict(id=row['id'], sport=row['sport'], game_id=row['game_id'], status='held',
                        reason='Awaiting a consistent current fixture/result.')
            if game:
                if game['status'] == 'cancelled':
                    item.update(status='void', reason='Cancelled fixture; excluded.')
                elif fixture_identity(game) != row['revision']:
                    item.update(status='superseded', reason='Fixture revision changed; a new pregame forecast is required.')
                elif timestamp(row['saved_at']) >= min(timestamp(game['start_time']),
                        timestamp(game.get('actual_start_time', game['start_time']))):
                    item.update(status='late', reason='Forecast was not saved before the actual eligibility cutoff.')
                elif game['status'] == 'final':
                    result = resolved_result(game, now)
                    if result:
                        item.update(status='complete', reason='Eligible pregame forecast with confirmed final result.',
                                    outcome=('home', 'draw', 'away').index(result['outcome']),
                                    observed_at=result['observed_at'], probabilities=row['probabilities'],
                                    feature_logistic=row['feature_logistic'], start_time=row['start_time'])
                elif game['status'] in ('scheduled', 'live'):
                    item.update(status='pending', reason='Awaiting completion.')
            previous = previous_scores.get(item['id'], {})
            if previous.get('first_completed_at'):
                item['first_completed_at'] = previous['first_completed_at']
            elif item['status'] == 'complete':
                item['first_completed_at'] = item['observed_at']
            scored.append(item)
        with self.connect() as db:
            for item in scored:
                db.execute('INSERT OR REPLACE INTO scores VALUES (?,?)', (item['id'], json.dumps(item, allow_nan=False)))
            for sport, threshold in thresholds.items():
                completed = sorted([r for r in scored if r['sport'] == sport and r['status'] == 'complete'],
                                   key=lambda r: (timestamp(r['first_completed_at']), timestamp(r['start_time']), r['id']))
                if len(completed) >= threshold:
                    cohort = dict(frozen_at=now.isoformat(), threshold=threshold, rows=completed[:threshold])
                    db.execute('INSERT OR IGNORE INTO cohorts VALUES (?,?,?)', (model, sport, json.dumps(cohort)))
        return self.status(model, thresholds=thresholds)

    def status(self, model, *, thresholds=None):
        thresholds = thresholds or THRESHOLDS
        forecasts = self.forecasts(model)
        ids = {r['id'] for r in forecasts}
        with self.connect() as db:
            scores = [json.loads(r[1]) for r in db.execute('SELECT id,payload FROM scores') if r[0] in ids]
            cohorts = {r[0]: json.loads(r[1]) for r in db.execute('SELECT sport,payload FROM cohorts WHERE model=?', (model,))}
        result = {'model': model, 'forecasts': len(forecasts), 'sports': {},
                  'note': 'Interim results are descriptive. First fixed cohorts: 100 soccer and 1,000 baseball completed eligible fixtures.'}
        for sport, threshold in thresholds.items():
            completed = [r for r in scores if r['sport'] == sport and r['status'] == 'complete']
            cohort = cohorts.get(sport)
            # Membership is frozen; eligibility and corrected outcomes remain conservative.
            current_by_id = {r['id']: r for r in scores}
            cohort_ids = [r['id'] for r in cohort['rows']] if cohort else []
            evaluated = [current_by_id[key] for key in cohort_ids
                         if key in current_by_id and current_by_id[key]['status'] == 'complete'] if cohort else completed
            result['sports'][sport] = dict(threshold=threshold, eligible_completed=len(completed),
                status='frozen' if cohort else 'pending', frozen_at=cohort['frozen_at'] if cohort else None,
                cohort_ids=cohort_ids, cohort_eligible=len(evaluated) if cohort else None,
                cohort_invalidated=len(cohort_ids) - len(evaluated) if cohort else 0,
                metrics={name: metrics([r['outcome'] for r in evaluated], [r[key] for r in evaluated])
                         for name, key in [('shadow', 'probabilities'), ('feature_logistic', 'feature_logistic')]}
                         if evaluated else None,
                void=sum(r['sport'] == sport and r['status'] == 'void' for r in scores))
        return result


class ShadowRuntime:
    def __init__(self, root):
        self.root = Path(root)
        self.pointer = None
        self.candidates = []
        self.baseline = None
        self.ledger = ShadowLedger(self.root / 'data/v2-shadow.sqlite3')
        self.error = None

    def ensure(self):
        from .experiment_v2 import load_candidate
        path = self.root / 'output/v2-shadow.json'
        if not path.exists():
            return False
        pointer = json.loads(path.read_text())
        if pointer != self.pointer:
            for bundle in pointer['bundles']:
                if digest(Path(bundle['path'])) != bundle['sha256']:
                    raise ValueError('Shadow bundle identity changed.')
            if digest(Path(pointer['baseline_path'])) != pointer['baseline_sha256']:
                raise ValueError('Shadow baseline identity changed.')
            candidates = [load_candidate(bundle['path']) for bundle in pointer['bundles']]
            self.candidates, self.pointer = candidates, pointer
            self.baseline = json.loads(Path(pointer['baseline_path']).read_text())
        return True

    def refresh(self, runtime):
        from .experiment_v2 import baseline_probability
        try:
            if not self.ensure():
                return
            self.ledger.score(runtime.snapshot['games'], model=model_identity(self.pointer))
            fixtures = list(runtime.snapshot['games'])
            for game in fixtures:
                if not eligible(game, datetime.now(timezone.utc)):
                    continue
                feature = runtime.features.get(game['id'])
                if feature is None:
                    continue
                self.ledger.capture(game, feature, pointer=self.pointer,
                    predict=lambda x: [c.predict_proba(x) for c in self.candidates],
                    baseline_predict=lambda x: baseline_probability(x, self.baseline),
                    current_fixture=lambda game_id: next((g for g in runtime.snapshot['games'] if g['id'] == game_id), None),
                    feature_timestamp=runtime.snapshot.get('updated_at'))
            self.ledger.score(runtime.snapshot['games'], model=model_identity(self.pointer))
            self.error = None
        except Exception as exc:
            self.error = f'{type(exc).__name__}: {exc}'

    def status(self):
        path = self.root / 'output/v2-shadow.json'
        if not path.exists():
            return {'status': 'awaiting_candidate', 'error': self.error, 'sports': {
                sport: {'threshold': threshold, 'eligible_completed': 0, 'status': 'pending', 'metrics': None}
                for sport, threshold in THRESHOLDS.items()}}
        pointer = json.loads(path.read_text())
        return dict(self.ledger.status(model_identity(pointer)), status='active_shadow',
                    variant=pointer['variant'], activated_at=pointer['activated_at'], error=self.error)
