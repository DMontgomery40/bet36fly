"""Durable paper proposals. No stakes, orders, account access or execution."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sqlite3


def fixture_identity(fixture):
    """Revision of the event itself, excluding transport fetch time and model inputs."""
    start = datetime.fromisoformat(fixture['start_time'].replace('Z', '+00:00'))
    if start.tzinfo is None:
        raise ValueError('Fixture kickoff must have a timezone.')
    identity = [fixture['sport'], fixture['home'], fixture['away'],
                start.astimezone(timezone.utc).isoformat()]
    return hashlib.sha256(json.dumps(identity).encode()).hexdigest()


class PickLedger:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS picks '
                       '(id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL)')

    def _connect(self):
        return sqlite3.connect(self.path, timeout=30)

    def add(self, proposal: dict):
        fixture_hash = fixture_identity(proposal)
        identity = [proposal['game_id'], proposal['run_id'], proposal['feature_hash'], fixture_hash]
        key = hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:24]
        record = dict(proposal, id=key, ledger_id=key, fixture_hash=fixture_hash, mode='paper', status='proposed')
        with self._connect() as db:
            db.execute('INSERT OR IGNORE INTO picks VALUES (?, ?, ?)',
                       (key, record['created_at'], json.dumps(record, allow_nan=False)))
            row = db.execute('SELECT payload FROM picks WHERE id=?', (key,)).fetchone()
        return json.loads(row[0])

    def all(self):
        with self._connect() as db:
            return [json.loads(row[0]) for row in db.execute('SELECT payload FROM picks ORDER BY created_at DESC, id')]

    def latest(self, run_id):
        result = {}
        for row in self.all():
            if row['run_id'] == run_id and row['game_id'] not in result:
                result[row['game_id']] = row
        return result

    def export_csv(self):
        stream = io.StringIO(newline='')
        columns = ['id', 'game_id', 'sport', 'home', 'away', 'start_time', 'created_at', 'pick',
                   'pick_label', 'confidence', 'fair_odds', 'run_id', 'model_hash', 'feature_hash', 'fixture_hash',
                   'mode', 'status', 'source_url', 'source_fetched_at']
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in self.all():
            safe = {}
            for key in columns:
                value = row.get(key, '')
                if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')):
                    value = "'" + value
                safe[key] = value
            writer.writerow(safe)
        return stream.getvalue()
