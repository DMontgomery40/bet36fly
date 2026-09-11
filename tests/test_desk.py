from copy import deepcopy
from datetime import datetime, timezone

import pytest

from bet36fly.desk import build_desk

NOW = datetime(2026, 9, 11, 12, tzinfo=timezone.utc)


def sample(sport='soccer', outcome='home', state='final'):
    game = dict(id='g1', sport=sport, league='EPL' if sport == 'soccer' else 'MLB',
                home='Home', away='Away', start_time='2026-09-10T18:00:00Z', status=state,
                home_score=2, away_score=0, outcome=0, source='Public source',
                source_fetched_at='2026-09-10T21:00:00Z')
    p = {'home': .6, 'draw': .1, 'away': .3} if sport == 'soccer' else {'home': .6, 'draw': 0, 'away': .4}
    if outcome == 'away':
        p['home'], p['away'] = p['away'], p['home']
    if outcome == 'draw':
        p = {'home': .2, 'draw': .6, 'away': .2}
    pick = dict(id='p1', game_id='g1', sport=sport, home='Home', away='Away',
                start_time=game['start_time'], created_at='2026-09-10T17:00:00Z',
                mode='paper', run_id='r1', model_hash='hash', probabilities=p,
                pick=outcome, pick_label={'home': 'Home', 'away': 'Away', 'draw': 'Draw'}[outcome],
                confidence=.6)
    return pick, game


def result(picks, games):
    return build_desk(picks, games, now=NOW)


def test_empty_is_unmeasured_and_never_backfilled_from_historical_finals():
    _, game = sample()
    report = result([], [game])
    assert report['summary']['hit_rate'] is None
    assert report['summary']['total'] == 0 and report['curve'] == []


@pytest.mark.parametrize('sport', ['soccer', 'baseball'])
@pytest.mark.parametrize('pick_outcome,won', [('home', True), ('away', False)])
def test_actual_final_result_scores_both_sports(sport, pick_outcome, won):
    pick, game = sample(sport, pick_outcome)
    report = result([pick], [game])
    assert report['summary']['wins'] == won
    assert report['summary']['losses'] == (not won)
    assert report['summary']['hit_rate'] == float(won)
    assert report['curve'][0]['expected_rate'] == .6
    assert report['rows'][0]['result']['home_score'] == 2


def test_soccer_draw_can_win_but_baseball_tie_is_not_scored():
    for sport, choice in [('soccer', 'draw'), ('baseball', 'home')]:
        pick, game = sample(sport, choice)
        game.update(home_score=1, away_score=1, outcome=1)
        report = result([pick], [game])
        assert report['summary']['wins'] == (sport == 'soccer')
        assert report['summary']['held'] == (sport == 'baseball')


@pytest.mark.parametrize('created', ['2026-09-10T18:00:00Z', '2026-09-10T19:00:00Z'])
def test_at_or_after_kickoff_never_counts(created):
    pick, game = sample()
    pick['created_at'] = created
    report = result([pick], [game])
    assert report['summary']['total'] == 0
    assert report['excluded']['at_or_after_kickoff'] == 1


def test_first_prediction_stays_locked_across_features_and_model_revisions():
    first, game = sample(outcome='away')
    later, _ = sample()
    later.update(id='p2', run_id='r2', created_at='2026-09-10T17:30:00Z')
    original = deepcopy(first)
    a, b = result([later, first], [game]), result([first, later], [game])
    assert a == b
    assert a['summary']['losses'] == 1 and a['summary']['wins'] == 0
    assert a['rows'][0]['revision_count'] == 2
    assert first == original


def test_reschedules_and_offset_equivalence_use_fixture_identity():
    pick, game = sample()
    game['start_time'] = '2026-09-10T20:00:00+02:00'
    assert result([pick], [game])['summary']['wins'] == 1
    game['start_time'] = '2026-09-11T18:00:00Z'
    report = result([pick], [game])
    assert report['summary']['total'] == 0
    assert report['excluded']['replaced_fixture_revision'] == 1


@pytest.mark.parametrize('status,state', [('live', 'pending'), ('scheduled', 'pending'),
                                         ('postponed', 'held'), ('cancelled', 'void'), ('unknown', 'held')])
def test_unfinished_and_void_states_never_score(status, state):
    pick, game = sample(state=status)
    report = result([pick], [game])
    assert report['rows'][0]['state'] == state
    assert report['summary']['completed'] == 0


def test_upcoming_changes_to_pending_at_kickoff_and_missing_fixture_is_held():
    pick, game = sample(state='scheduled')
    game['start_time'] = pick['start_time'] = '2026-09-11T13:00:00Z'
    assert result([pick], [game])['summary']['upcoming'] == 1
    assert build_desk([pick], [game], now=datetime(2026, 9, 11, 13, tzinfo=timezone.utc))['summary']['pending'] == 1
    assert result([pick], [])['summary']['held'] == 1


@pytest.mark.parametrize('change', [dict(home_score=None), dict(home_score=-1), dict(home_score=1.5),
                                   dict(home_score=True), dict(outcome=2), dict(source_fetched_at=None),
                                   dict(source_fetched_at='2026-09-10T17:00:00Z'),
                                   dict(source_fetched_at='2026-09-12T00:00:00Z')])
def test_incomplete_inconsistent_or_badly_timed_finals_are_held(change):
    pick, game = sample()
    game.update(change)
    assert result([pick], [game])['summary']['held'] == 1


@pytest.mark.parametrize('change', [dict(mode='retrospective_backtest'), dict(model_hash=''),
                                   dict(confidence=.9), dict(confidence='0.6'), dict(confidence=True),
                                   dict(probabilities={'home': '0.6', 'draw': .1, 'away': .3}),
                                   dict(probabilities={'home': True, 'draw': 0, 'away': 0}), dict(pick='away'), dict(created_at='not-a-date'),
                                   dict(created_at='2026-09-10T17:00:00'),
                                   dict(probabilities={'home': float('nan'), 'draw': .1, 'away': .3}),
                                   dict(probabilities={'home': .9, 'draw': .2, 'away': -.1})])
def test_malformed_or_nonforward_predictions_are_excluded(change):
    pick, game = sample()
    pick.update(change)
    assert result([pick], [game])['summary']['total'] == 0


def test_deduplication_sport_filter_and_corrected_results_are_consistent():
    pick, game = sample()
    baseball, mlb = sample('baseball')
    baseball.update(id='p2', game_id='g2')
    mlb['id'] = 'g2'
    report = result([pick, pick, baseball], [game, mlb])
    assert report['summary']['wins'] == 2
    assert report['by_sport']['soccer']['wins'] == 1
    assert report['by_sport']['baseball']['wins'] == 1
    assert build_desk([pick, baseball], [game, mlb], now=NOW, sport='soccer')['summary']['total'] == 1
    game.update(home_score=0, away_score=1, outcome=2)
    corrected = result([pick], [game])
    assert corrected['summary']['wins'] == 0 and corrected['summary']['losses'] == 1
