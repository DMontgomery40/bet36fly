"""Durable paper proposals. No stakes, orders, account access or execution."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sqlite3


class ReadOnlyDatabaseError(RuntimeError):
    """Stored verification evidence cannot be read without risking a write."""


def _read_only_sqlite(path: Path):
    path = Path(path)
    if path.is_symlink():
        raise ReadOnlyDatabaseError('Read-only ledger unavailable: symbolic links are not supported.')
    sidecars = [Path(str(path) + suffix) for suffix in ('-journal', '-wal', '-shm')]
    present = [item.name for item in sidecars if item.exists()]
    if present:
        raise ReadOnlyDatabaseError(
            f'Read-only ledger unavailable while SQLite sidecars exist: {", ".join(present)}'
        )
    try:
        with path.open('rb') as stream:
            header = stream.read(100)
    except OSError as exc:
        raise ReadOnlyDatabaseError(f'Read-only ledger unavailable: {exc}') from exc
    if len(header) < 100 or header[:16] != b'SQLite format 3\x00':
        raise ReadOnlyDatabaseError('Read-only ledger unavailable: invalid SQLite header.')
    if header[18:20] != b'\x01\x01':
        raise ReadOnlyDatabaseError('Read-only ledger unavailable: WAL-mode databases are not supported.')
    try:
        return sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=30)
    except sqlite3.Error as exc:
        raise ReadOnlyDatabaseError(f'Read-only ledger unavailable: {exc}') from exc


def fixture_identity(fixture):
    """Revision of the event itself, excluding transport fetch time and model inputs."""
    start = datetime.fromisoformat(fixture['start_time'].replace('Z', '+00:00'))
    if start.tzinfo is None:
        raise ValueError('Fixture kickoff must have a timezone.')
    identity = [fixture['sport'], fixture['home'], fixture['away'],
                start.astimezone(timezone.utc).isoformat()]
    return hashlib.sha256(json.dumps(identity).encode()).hexdigest()


class PickLedger:
    def __init__(self, path: Path, *, read_only=False):
        self.path = Path(path)
        self.read_only = read_only
        if read_only:
            return
        path = self.path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS picks '
                       '(id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL)')

    def _connect(self):
        if self.read_only:
            return _read_only_sqlite(self.path)
        return sqlite3.connect(self.path, timeout=30)

    def add(self, proposal: dict):
        if self.read_only:
            raise ReadOnlyDatabaseError('Read-only ledger cannot add paper picks.')
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
        if self.read_only and not self.path.exists():
            return []
        with self._connect() as db:
            try:
                rows = db.execute('SELECT payload FROM picks ORDER BY created_at DESC, id')
                return [json.loads(row[0]) for row in rows]
            except (sqlite3.Error, json.JSONDecodeError) as exc:
                if self.read_only:
                    raise ReadOnlyDatabaseError(f'Read-only ledger unavailable: {exc}') from exc
                raise

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
