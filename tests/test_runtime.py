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


def test_neuron_categories_resolve_population_before_broad_labels():
    from bet36fly.runtime import neuron_category
    groups = dict(sensory={0}, kc={1, 2}, mbon={3})
    for index, label, expected in [(0, 'ALPN', 'alpn'), (1, 'KC', 'kc'), (2, 'KCg', 'kc'),
                                   (3, 'MBON01', 'mbon'), (4, 'other type', 'other'), (5, None, 'unknown')]:
        assert neuron_category(index, **groups, annotations={'type': label}) == expected


def test_geometry_reindexes_annotations_and_aligns_edge_metadata(tmp_path):
    import pandas as pd
    import pyarrow.feather as feather
    from bet36fly.runtime import brain_geometry
    np.save(tmp_path / 'ids.npy', [10, 20, 30, 40])
    for name, values in [('sensory', [0]), ('kc', [1]), ('mbon', [2]), ('indptr', [0, 1, 2, 3, 3]),
                         ('post', [1, 2, 3]), ('counts', [8, 6, 5]), ('signs', [1, 1, -1, 1])]:
        np.save(tmp_path / (name + '.npy'), values)
    feather.write_feather(pd.DataFrame(dict(bodyId=[40, 20, 10, 30], type=[None, 'KCg', 'ALPN', 'MBON01'],
        superclass=[None, 'KC', 'ALPN', 'MBON'], somaLocation=[[3, 0, 0], [1, 1, 0], [0, 0, 0], [2, 1, 0]])),
        tmp_path / 'nodes.feather')
    indices, payload = brain_geometry(tmp_path, sample_size=4)
    assert indices.tolist() == [0, 1, 2, 3]
    assert [n['id'] for n in payload['nodes']] == ['10', '20', '30', '40']
    assert [n['category'] for n in payload['nodes']] == ['alpn', 'kc', 'mbon', 'unknown']
    assert len(payload['edges']) == len(payload['edge_metadata']) == 3
    for (a, b), edge in zip(payload['edges'], payload['edge_metadata']):
        assert edge['plastic'] == (a == 1 and b == 2)
        assert edge['modeled_sign'] == (-1 if a == 2 else 1)
