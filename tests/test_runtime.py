from datetime import datetime, timezone
import numpy as np
import pytest

from bet36fly.runtime import upcoming_games, feature_identity, probability_payload


def test_upcoming_games_excludes_started_finished_and_postponed_and_filters_sport():
    now = datetime(2026, 9, 10, 12, tzinfo=timezone.utc)
    games = [dict(id=str(i), start_time=t, status=status, sport=sport)
             for i, (t, status, sport) in enumerate([
                 ('2026-09-10T13:00:00Z', 'scheduled', 'soccer'),
                 ('2026-09-10T11:00:00Z', 'scheduled', 'soccer'),
                 ('2026-09-10T13:00:00Z', 'postponed', 'soccer'),
                 ('2026-09-10T14:00:00Z', 'scheduled', 'baseball'),
                 ('2026-09-10T15:00:00Z', 'final', 'baseball'),
             ])]
    assert [g['id'] for g in upcoming_games(games, now=now)] == ['0', '3']
    assert [g['id'] for g in upcoming_games(games, now=now, sport='soccer')] == ['0']


def test_feature_hash_changes_with_inputs_and_readout_labels_are_not_quotes():
    assert feature_identity(np.zeros(16)) != feature_identity(np.ones(16))
    g = {'sport': 'soccer', 'home': 'A', 'away': 'B'}
    p = probability_payload(g, np.array([.2, .5, .3]))
    assert p['pick'] == 'draw' and p['pick_label'] == 'Draw' and p['fair_odds'] == 2
    assert sum(p['probabilities'].values()) == 1


def test_probability_payload_rejects_bad_model_output():
    import pytest
    for values in [[.2, .2, .2], [1, -1, 1], [float('nan'), 0, 1]]:
        with pytest.raises(ValueError):
            probability_payload({'sport': 'soccer', 'home': 'A', 'away': 'B'}, np.array(values))


@pytest.mark.parametrize('change, reusable', [
    ({'source_fetched_at': '2026-09-11T00:00:00Z'}, True),
    ({'start_time': '2099-09-20T14:00:00+02:00'}, True),
    ({'start_time': '2099-09-20T20:00:00Z'}, False),
    ({'start_time': '2099-09-21T12:00:00Z'}, False),
    ({'home': 'Corrected home'}, False),
    ({'away': 'Corrected away'}, False),
])
def test_upcoming_predictions_require_current_fixture_revision(tmp_path, change, reusable):
    from bet36fly.runtime import Runtime
    runtime = Runtime(tmp_path)
    fixture = dict(id='g1', sport='soccer', home='A', away='B', status='scheduled',
                   start_time='2099-09-20T12:00:00Z', source_fetched_at='2026-09-10T00:00:00Z')
    runtime.model_pointer = {'run_id': 'r1'}
    runtime.features = {'g1': np.zeros(16)}
    runtime.ledger.add(dict(fixture, game_id='g1', run_id='r1',
                            feature_hash=feature_identity(np.zeros(16)), created_at='2026-09-10T12:00:00Z'))
    runtime.snapshot['games'] = [dict(fixture, **change)]
    assert ('prediction' in runtime.games()[0]) == reusable
    # Feature changes independently invalidate an otherwise current fixture.
    runtime.features['g1'] = np.ones(16)
    assert 'prediction' not in runtime.games()[0]
