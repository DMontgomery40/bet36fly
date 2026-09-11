from copy import deepcopy
import hashlib
import json

import numpy as np
import pytest

from scripts.analyze_draws import analyze_rows, build_report, summarize, wilson


def fixtures(probabilities, odds=None):
    picks, games = [], []
    for i, p in enumerate(probabilities):
        common = dict(sport='soccer', start_time=f'2026-01-{i+1:02}T12:00:00Z',
                      home='A', away='B', outcome=i % 3)
        games.append(dict(id=str(i), **common, odds=odds))
        chosen = int(np.argmax(p))
        picks.append(dict(game_id=str(i), **common, probabilities=p,
                          pick=chosen, correct=chosen == common['outcome']))
    return picks, games


def test_all_bin_boundaries_and_unit_probability_count_once():
    p = [[1 - i / 10, i / 10, 0] for i in range(11)]
    result, rows = analyze_rows(*fixtures(p, [2, 4, 4]))
    bins = result['draw_probability_bins']
    assert [b['n'] for b in bins] == [1] * 9 + [2]
    assert sum(b['draws'] for b in bins) == result['all_soccer_test']['draws']
    assert result['all_soccer_test']['mean_predicted_draw'] == pytest.approx(.5)
    assert result['historical_odds_comparison']['mean_normalized_b365_draw'] == .25
    assert len(rows) == 11


@pytest.mark.parametrize('bad', [[.5, .5], [-.1, .5, .6], [0, 0, 0], [0, 1.1, 0],
                                [0, float('nan'), 1], [0, float('inf'), 0]])
def test_invalid_probability_family_is_rejected(bad):
    picks, games = fixtures([[.3, .4, .3]])
    picks[0]['probabilities'] = bad
    with pytest.raises(ValueError, match='probabilities'):
        analyze_rows(picks, games)


@pytest.mark.parametrize('odds', [None, [], [2, None, 4], [2, 1, 3], [2, float('inf'), 3],
                                  [2, 'missing', 3], [2, float('nan'), 3]])
def test_incomplete_odds_never_change_model_sample_or_become_zero(odds):
    result, rows = analyze_rows(*fixtures([[.3, .4, .3]], odds))
    assert result['all_soccer_test']['n'] == 1
    assert result['historical_odds_comparison']['n_with_complete_odds'] == 0
    assert result['historical_odds_comparison']['mean_normalized_b365_draw'] is None
    assert rows[0]['normalized_b365_draw'] is None


def test_quoted_comparison_uses_matching_rows_only():
    picks, games = fixtures([[.2, .6, .2], [.45, .1, .45]])
    games[0]['odds'] = [2, 4, 4]
    result, _ = analyze_rows(picks, games)
    assert result['all_soccer_test']['mean_predicted_draw'] == pytest.approx(.35)
    assert result['historical_odds_comparison']['matched_fly_and_outcomes']['mean_predicted_draw'] == .6


@pytest.mark.parametrize('field,value', [('outcome', 1), ('sport', 'baseball'), ('home', 'C'),
                                        ('away', 'C'), ('start_time', '2027-01-01T00:00:00Z')])
def test_frozen_join_metadata_and_labels_must_match(field, value):
    picks, games = fixtures([[.3, .4, .3]])
    games[0][field] = value
    with pytest.raises(ValueError, match='fixture and label'):
        analyze_rows(picks, games)


def test_missing_duplicate_or_extra_rows_are_rejected():
    picks, games = fixtures([[.3, .4, .3]])
    for p, g in [(picks * 2, games), (picks, games * 2), ([], games), (picks, []), ([], [])]:
        with pytest.raises(ValueError):
            analyze_rows(p, g)
    extra = deepcopy(games[0])
    extra['id'] = 'extra'
    with pytest.raises(ValueError):
        analyze_rows(picks, games + [extra])


@pytest.mark.parametrize('field,value', [('pick', 0), ('correct', True)])
def test_saved_decision_contract_is_checked(field, value):
    picks, games = fixtures([[.3, .4, .3]])
    picks[0][field] = value
    with pytest.raises(ValueError, match='inconsistent'):
        analyze_rows(picks, games)


def test_empty_groups_and_observed_frequency_intervals():
    assert summarize([])['actual_draw_rate'] is None
    assert wilson(0, 0) is None
    assert wilson(6, 16) == pytest.approx([.1848123256, .6135895945])
    for hits, n in [(0, 1), (1, 1), (5, 10)]:
        lo, hi = wilson(hits, n)
        assert 0 <= lo <= hits / n <= hi <= 1


def frozen_run(tmp_path):
    run = tmp_path / 'test-run'
    run.mkdir()
    picks, games = fixtures([[.3, .4, .3]] * 3, [2, 4, 4])
    (run / 'training-games.json').write_text(json.dumps({'games': games}))
    (run / 'backtest-picks.json').write_text(json.dumps({
        'run_id': run.name, 'mode': 'retrospective_backtest', 'picks': picks[-1:]}))
    (run / 'checkpoint.npz').write_bytes(b'opaque-checkpoint-for-hashing-only')
    data = dict(y=np.arange(3), sport=np.zeros(3, dtype=int),
                train=np.array([True, False, False]), validation=np.array([False, True, False]),
                test=np.array([False, False, True]))
    np.savez(run / 'training-data.npz', **data)
    return run, data


def test_frozen_run_end_to_end_is_repeatable_and_hashes_sources(tmp_path):
    run, _ = frozen_run(tmp_path)
    report, rows = build_report(run)
    assert (report, rows) == build_report(run)
    assert report['all_soccer_test']['n'] == 1
    assert report['soccer_split_draw_rates']['validation']['draw_rate'] == 1
    for name, digest in report['source_sha256'].items():
        assert digest == hashlib.sha256((run / name).read_bytes()).hexdigest()
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize('mutation', ['overlap', 'gap', 'mask_length', 'mask_dtype', 'labels', 'sports'])
def test_misaligned_or_invalid_frozen_partitions_are_rejected(tmp_path, mutation):
    run, data = frozen_run(tmp_path)
    if mutation == 'overlap':
        data['test'][0] = True
    elif mutation == 'gap':
        data['test'][:] = False
    elif mutation == 'mask_length':
        data['test'] = data['test'][:1]
    elif mutation == 'mask_dtype':
        data['test'] = data['test'].astype(int)
    elif mutation == 'labels':
        data['y'][0] = 2
    else:
        data['sport'][0] = 1
    np.savez(run / 'training-data.npz', **data)
    with pytest.raises(ValueError):
        build_report(run)
