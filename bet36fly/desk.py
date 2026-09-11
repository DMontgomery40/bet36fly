"""Score immutable pregame proposals against public final results, without wagering."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import math

from .ledger import fixture_identity

OUTCOMES = ('home', 'draw', 'away')


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Forward scoring requires timezone-aware timestamps.')
    return parsed.astimezone(timezone.utc)


def valid_prediction(row, now):
    try:
        p = [row['probabilities'][key] for key in OUTCOMES]
        return (row['mode'] == 'paper' and row['sport'] in ('soccer', 'baseball')
                and bool(row['id']) and bool(row['run_id']) and bool(row['model_hash'])
                and all(type(value) in (int, float) for value in p)
                and type(row['confidence']) in (int, float)
                and all(math.isfinite(value) and 0 <= value <= 1 for value in p)
                and math.isclose(sum(p), 1, abs_tol=1e-5)
                and (row['sport'] != 'baseball' or p[1] == 0)
                and row['pick'] == OUTCOMES[max(range(3), key=p.__getitem__)]
                and math.isclose(row['confidence'], max(p), abs_tol=1e-5)
                and timestamp(row['created_at']) <= now)
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def resolved_result(game, now):
    """Require consistent final scores and observation timing, not just a status label."""
    try:
        home, away = game['home_score'], game['away_score']
        if (type(home) is not int or type(away) is not int or min(home, away) < 0
                or not timestamp(game['start_time']) <= timestamp(game['source_fetched_at']) <= now):
            return None
        outcome = 0 if home > away else 2 if away > home else 1
        if game['outcome'] != outcome or (game['sport'] == 'baseball' and outcome == 1):
            return None
        return {'home_score': home, 'away_score': away, 'outcome': OUTCOMES[outcome],
                'observed_at': game['source_fetched_at'], 'source': game.get('source'),
                'source_url': game.get('source_url')}
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def summary(rows):
    counts = Counter(row['state'] for row in rows)
    completed = [row for row in rows if row['state'] in ('won', 'lost')]
    total, wins = len(completed), counts['won']
    expected = sum(row['prediction']['confidence'] for row in completed)
    losses = [-math.log(max(1e-12, row['prediction']['probabilities'][row['result']['outcome']]))
              for row in completed]
    return {'total': len(rows), 'upcoming': counts['upcoming'], 'pending': counts['pending'],
            'held': counts['held'], 'void': counts['void'], 'completed': total,
            'wins': wins, 'losses': counts['lost'], 'hit_rate': wins / total if total else None,
            'mean_pick_probability': expected / total if total else None,
            'log_loss': sum(losses) / total if total else None}


def build_desk(picks, games, *, now=None, sport='all'):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or sport not in ('all', 'soccer', 'baseball'):
        raise ValueError('Need aware time and a supported sport.')
    current = {game['id']: game for game in games}
    excluded, grouped, seen = Counter(), defaultdict(list), set()
    for row in picks:
        if sport != 'all' and row.get('sport') != sport:
            continue
        if not valid_prediction(row, now):
            excluded['invalid_or_nonforward_record'] += 1
            continue
        try:
            if timestamp(row['created_at']) >= timestamp(row['start_time']):
                excluded['at_or_after_kickoff'] += 1
                continue
            game = current.get(row['game_id'])
            if game and fixture_identity(row) != fixture_identity(game):
                excluded['replaced_fixture_revision'] += 1
                continue
        except (KeyError, ValueError, TypeError, AttributeError):
            excluded['invalid_or_nonforward_record'] += 1
            continue
        if row['id'] in seen:
            excluded['duplicate_record'] += 1
            continue
        seen.add(row['id'])
        grouped[row['game_id']].append(row)

    rows = []
    for game_id, proposals in grouped.items():
        proposals.sort(key=lambda row: (timestamp(row['created_at']), row['id']))
        pick = proposals[0]
        excluded['later_predictions_same_fixture'] += len(proposals) - 1
        game = current.get(game_id)
        state, reason, resolved = 'held', 'Fixture missing from the current source snapshot.', None
        if game:
            status = game.get('status')
            if status == 'cancelled':
                state, reason = 'void', 'Source reports the fixture cancelled. Not scored.'
            elif status == 'postponed':
                reason = 'Postponed. Awaiting a confirmed fixture; not scored.'
            elif status == 'final':
                resolved = resolved_result(game, now)
                if resolved:
                    state = 'won' if pick['pick'] == resolved['outcome'] else 'lost'
                    reason = 'Recorded pregame pick matched to the source final score.'
                else:
                    reason = 'Final result needs consistent scores and a valid observation time.'
            elif status == 'scheduled' and timestamp(game['start_time']) > now:
                state, reason = 'upcoming', 'First recorded pick for this fixture. Waiting for kickoff.'
            elif status in ('live', 'scheduled'):
                state, reason = 'pending', 'Awaiting a source-confirmed final result.'
            else:
                reason = 'Source status is unresolved. Not scored.'
        rows.append({'game_id': game_id, 'league': game.get('league', '') if game else '',
                     'prediction': pick, 'state': state, 'reason': reason,
                     'result': resolved, 'revision_count': len(proposals), 'can_run': state == 'upcoming'})
    rows.sort(key=lambda row: (timestamp(row['prediction']['start_time']), row['game_id']))
    cumulative, wins, expected = [], 0, 0.0
    for row in rows:
        if row['state'] not in ('won', 'lost'):
            continue
        wins += row['state'] == 'won'
        expected += row['prediction']['confidence']
        n = len(cumulative) + 1
        cumulative.append({'n': n, 'wins': wins, 'hit_rate': wins / n, 'expected_rate': expected / n,
                           'game_id': row['game_id'], 'start_time': row['prediction']['start_time']})
    return {'mode': 'forward_paper', 'as_of': now.isoformat(),
            'selection_rule': 'First valid pregame pick per current fixture revision; all model versions.',
            'summary': summary(rows),
            'by_sport': {s: summary([row for row in rows if row['prediction']['sport'] == s])
                         for s in ('soccer', 'baseball')},
            'rows': rows, 'curve': cumulative,
            'excluded': {key: value for key, value in excluded.items() if value},
            'first_recorded_at': min((row['prediction']['created_at'] for row in rows),
                                     key=timestamp, default=None)}
