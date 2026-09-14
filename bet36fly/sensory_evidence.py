"""Read-only presentation of a pinned confirmation. No engine, fit, or source fetch."""
from __future__ import annotations

import csv
from datetime import date, datetime
from functools import lru_cache
import hashlib
import io
import json
import math
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

IDENTITY = 'sensory-confirmation-4887cb8c17f6281d8166'
METHODS = ('neural', 'encoder_only', 'same_information', 'uniform', 'prior', 'circuit_silenced')
DOWNLOADS = {
    'predictions': 'All confirmation predictions (CSV)',
    'evaluation': 'Evaluation and confidence intervals',
    'manifest': 'Confirmation manifest',
    'integrity': 'Recorded independent integrity check',
    'candidate': 'Frozen encoder, response cache and readout',
    'result': 'Research result and limitations',
    'confirmation': 'Predeclared confirmation protocol',
    'cells': 'Output cell identities',
    'responses': 'Recorded sensory probes',
}


class EvidenceError(ValueError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def _read(root, relative):
    path = root / relative
    if Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise EvidenceError('invalid', 'Artifact path is outside the evidence installation.')
    if any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
        raise EvidenceError('invalid', 'Symbolic-link evidence is not supported.')
    try:
        return path.read_bytes()
    except OSError as exc:
        raise EvidenceError('unavailable', f'Required evidence is unavailable: {Path(relative).name}.') from exc


def _json(raw):
    def invalid(value):
        raise ValueError(f'Non-finite JSON value: {value}')
    return json.loads(raw, parse_constant=invalid)


def _metric(rows, field):
    n = len(rows)
    if not n:
        return dict(n=0, correct=0, accuracy=None, log_loss=None, brier=None)
    correct = sum((r[field] >= .5) == r['home_win'] for r in rows)
    loss = sum(-math.log(max(1e-12, r[field] if r['home_win'] else 1-r[field])) for r in rows) / n
    return dict(n=n, correct=correct, accuracy=correct/n, log_loss=loss,
                brier=sum((r[field]-r['home_win'])**2 for r in rows)/n)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


@lru_cache(maxsize=2)
def _parse(blobs):
    raw = dict(blobs)
    data = {k: _json(v) for k, v in raw.items() if k not in ('predictions', 'result')}
    manifest, evaluation, candidate = (data[k] for k in ('manifest', 'evaluation', 'candidate'))
    _require(manifest['identity'] == IDENTITY and manifest['status'] == 'passed_confirmation', 'Confirmation is incomplete or has another identity.')
    _require(manifest['evaluation'] == evaluation and evaluation['goal_passed'] is True, 'Evaluation disagrees with confirmation.')
    _require(manifest['candidate_sha256'] == hashlib.sha256(raw['candidate']).hexdigest(), 'Candidate identity mismatch.')
    for key, name in [('predictions', 'predictions.csv'), ('evaluation', 'evaluation.json'), ('confirmation', 'protocol.json')]:
        _require(hashlib.sha256(raw[key]).hexdigest() == manifest['artifact_sha256'][name], 'Manifest artifact mismatch.')
    _require(data['integrity']['status'] == 'passed' and manifest['new_neural_calls'] == 0
             and manifest['fitted_parameters_changed'] is False, 'Confirmation integrity is incomplete.')
    cache = candidate['mean_outputs']
    _require(len(cache) == 36 and all(len(r) == 4 and all(math.isfinite(x) and x >= 0 for x in r) for r in cache), 'Invalid response cache.')
    _require(data['responses']['status'] == 'passed' and data['responses']['mean_outputs'] == cache, 'Response evidence disagrees with frozen cache.')
    _require(data['responses']['output_ids'] == [c['body_id'] for c in data['cells']['cells']], 'Output cells are misaligned.')
    order = data['opportunities']['recruitment_order']
    _require(len(set(order)) == 34 and set(order) == set(data['assay']['populations']['sweet']), 'Recruitment identity mismatch.')
    rows = []
    for rawrow in csv.DictReader(io.StringIO(raw['predictions'].decode())):
        row = {k: rawrow[k] for k in ['game_id', 'start_time', 'home', 'away']}
        for k, v in rawrow.items():
            if k not in row:
                row[k] = float(v)
                _require(math.isfinite(row[k]), 'Non-finite prediction field.')
        _require(row['home_win'] in (0, 1) and all(0 <= row[k] <= 1 for k in METHODS), 'Invalid outcome or probability.')
        _require(datetime.fromisoformat(row['start_time'].replace('Z', '+00:00')).year == 2023, 'Unexpected confirmation year.')
        for side in ('home', 'away'):
            q, lo, hi = [row[side + suffix] for suffix in ['_quality', '_lo', '_hi']]
            _require(0 <= lo <= q <= hi <= 1, 'Invalid quality interval.')
            key = row[side+'_contact_key']
            _require(key == (35 if hi < .2 else math.floor(q*34+.5)), 'Quality and contact key disagree.')
            row[side+'_contact_key'] = int(key)
        delta = [math.log1p(h)-math.log1p(a) for h, a in zip(cache[row['home_contact_key']], cache[row['away_contact_key']])]
        _require(all(math.isclose(x, row[f'neural_difference_{i}'], abs_tol=1e-12) for i, x in enumerate(delta)), 'Neural differences do not reproduce.')
        logit = sum(x/s*c for x, s, c in zip(delta, candidate['readout']['scales'], candidate['readout']['coef']))
        _require(math.isclose(1/(1+math.exp(-logit)), row['neural'], abs_tol=1e-12), 'Frozen readout does not reproduce.')
        row['home_win'] = int(row['home_win'])
        row['correct'] = (row['neural'] >= .5) == row['home_win']
        rows.append(row)
    _require(len(rows) == len({r['game_id'] for r in rows}) == evaluation['metrics']['neural']['n'] == data['integrity']['n'], 'Incomplete or duplicated confirmation games.')
    _require(_metric(rows, 'neural')['correct'] == data['integrity']['correct'], 'Correct count mismatch.')
    for method in METHODS:
        measured = _metric(rows, method)
        _require(all(math.isclose(measured[k], v, abs_tol=1e-12) for k, v in evaluation['metrics'][method].items()), 'CSV and recorded metrics disagree.')
    rows.sort(key=lambda r: (r['start_time'], r['game_id']))
    data['games'] = rows
    return data


class SensoryEvidence:
    def __init__(self, root):
        self.root = Path(root)

    def load(self):
        try:
            lock = _json(_read(self.root, 'configs/sensory-application-lock.json'))
            _require(lock['schema'] == 1 and lock['identity'] == IDENTITY, 'Unsupported application evidence identity.')
            blobs = {}
            for key, entry in lock['files'].items():
                raw = _read(self.root, entry['path'])
                if hashlib.sha256(raw).hexdigest() != entry['sha256']:
                    raise EvidenceError('invalid', f'Frozen evidence failed its hash check: {Path(entry["path"]).name}.')
                blobs[key] = raw
            return _parse(tuple(sorted(blobs.items()))), lock, blobs
        except EvidenceError:
            raise
        except (ValueError, KeyError, TypeError, IndexError, OverflowError, ZeroDivisionError) as exc:
            raise EvidenceError('invalid', 'Frozen evidence is incomplete or inconsistent.') from exc

    def summary(self):
        try:
            data, lock, _ = self.load()
        except EvidenceError as exc:
            return dict(status=exc.status, message=str(exc), identity=IDENTITY)
        return dict(status='available', identity=IDENTITY, evaluation=data['evaluation'],
                    correct=data['integrity']['correct'], teams=sorted({r[s] for r in data['games'] for s in ['home', 'away']}),
                    source={k: data['manifest'][k] for k in ['source_url', 'source_fetched_at', 'created_at']},
                    candidate=data['candidate']['selected_id'],
                    splits={'training': {'years': '2019–2021', 'n': sum(s['eligible'] for s in data['development_source']['sources'] if s['year'] <= 2021)}, 'development': {'years': '2022', 'n': data['development']['metrics']['neural']['n']}, 'confirmation': {'years': '2023', 'n': len(data['games'])}},
                    output_cells=data['cells']['cells'],
                    downloads=[dict(id=k, label=v, url=f'/api/sensory/downloads/{k}', sha256=lock['files'][k]['sha256']) for k, v in DOWNLOADS.items()])

    def detail(self, game_id):
        data, _, _ = self.load()
        row = next((r for r in data['games'] if r['game_id'] == game_id), None)
        if row is None:
            raise HTTPException(404, 'Confirmation game not found.')
        sides = {}
        for side in ['home', 'away']:
            key = row[side+'_contact_key']
            bitter = key == 35
            ids = data['assay']['populations']['bitter'] if bitter else data['opportunities']['recruitment_order'][:key]
            measurement = data['assay']['source_measurements']['bitter' if bitter else 'sweet']
            probes = [r for r in data['responses']['rows'] if r['phase'] == 'ladder' and r['recruitment_key'] == key]
            sides[side] = dict(team=row[side], quality=row[side+'_quality'], interval=[row[side+'_lo'], row[side+'_hi']],
                contact_key=key, condition='Bitter probe' if bitter else 'Sweet contact probe', recruited_ids=ids,
                requested_hz=measurement['mean_hz'] if ids else 0, source_measurement=measurement,
                outputs_hz=data['candidate']['mean_outputs'][key],
                seeds=[r['seed'] for r in probes], outputs_by_seed=[r['output_hz'] for r in probes])
        return dict(identity=IDENTITY, game=row, **sides, output_cells=data['cells']['cells'],
                    stimulus_window_ms=[data['assay']['onset_ms'], data['assay']['onset_ms'] + data['assay']['stimulus_ms']],
                    duration_ms=sum(data['assay'][k] for k in ['onset_ms', 'stimulus_ms', 'recovery_ms']), bin_ms=data['assay']['bin_ms'],
                    evidence_mode='frozen-cache-lookup', achieved_input_hz=None,
                    achieved_input_note='Per-cell achieved input rates are not delivered by this adapter. Requested rates are generator settings; output rates are recorded simulation measurements.',
                    trace_note='Each matchup looks up previously simulated probes. Output rates average three seeds over the one-second stimulus; no new simulation or continuous live activity.')


def sensory_router(root):
    router = APIRouter(prefix='/api/sensory')
    reader = SensoryEvidence(root)

    def available():
        try:
            return reader.load()
        except EvidenceError as exc:
            raise HTTPException(503, str(exc)) from exc

    @router.get('/summary')
    def summary():
        return reader.summary()

    @router.get('/games')
    def games(team: str = '', start: date | None = None, end: date | None = None,
              offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
        if start and end and start > end:
            raise HTTPException(422, 'Start date must be on or before end date.')
        data, _, _ = available()
        rows = [r for r in data['games'] if (not team or team in (r['home'], r['away']))
                and (start is None or r['start_time'][:10] >= start.isoformat())
                and (end is None or r['start_time'][:10] <= end.isoformat())]
        return dict(identity=IDENTITY, total=len(rows), offset=offset, limit=limit,
                    summary=_metric(rows, 'neural'), games=rows[offset:offset+limit])

    @router.get('/games/{game_id}')
    def detail(game_id: str):
        try:
            return reader.detail(game_id)
        except EvidenceError as exc:
            raise HTTPException(503, str(exc)) from exc

    @router.get('/downloads/{artifact}')
    def download(artifact: str):
        if artifact not in DOWNLOADS:
            raise HTTPException(404, 'Unknown sensory artifact.')
        _, lock, blobs = available()
        filename = Path(lock['files'][artifact]['path']).name
        media = 'text/csv' if filename.endswith('.csv') else 'text/markdown' if filename.endswith('.md') else 'application/json'
        # Serve the exact bytes just validated, never reopen a potentially changed file.
        return Response(blobs[artifact], media_type=media,
                        headers={'Content-Disposition': f'attachment; filename="{filename}"'})

    return router
