"""Audit frozen soccer predictions without retraining, fetching or changing the model."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def unique_rows(rows, key):
    result = {row[key]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f'Duplicate {key} in audit input.')
    return result


def wilson(hits, n):
    """Descriptive 95% binomial interval; assumes independent Bernoulli observations."""
    if not n:
        return None
    z = 1.959963984540054
    p = hits / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return [max(0.0, center - radius), min(1.0, center + radius)]


def summarize(rows):
    n = len(rows)
    hits = sum(row['is_draw'] for row in rows)
    return {'n': n, 'draws': hits, 'actual_draw_rate': hits / n if n else None,
            'mean_predicted_draw': sum(row['p_draw'] for row in rows) / n if n else None,
            'observed_rate_wilson_95': wilson(hits, n)}


def analyze_rows(picks, games):
    """Require one-to-one soccer test coverage, with matching labels and fixture metadata."""
    pick_map, game_map = unique_rows(picks, 'game_id'), unique_rows(games, 'id')
    if not picks or pick_map.keys() != game_map.keys():
        raise ValueError('Need nonempty, complete one-to-one test coverage.')
    rows = []
    for pick in picks:
        game = game_map[pick['game_id']]
        if game['sport'] != 'soccer' or any(pick[k] != game[k] for k in
                ('sport', 'outcome', 'start_time', 'home', 'away')):
            raise ValueError('Prediction does not match the frozen soccer fixture and label.')
        p = np.asarray(pick['probabilities'], dtype=float)
        if (p.shape != (3,) or not np.isfinite(p).all() or np.any(p < 0) or np.any(p > 1)
                or not np.isclose(p.sum(), 1, rtol=0, atol=1e-6)):
            raise ValueError('Need finite normalized three-outcome probabilities.')
        if (pick['outcome'] not in (0, 1, 2) or pick['pick'] != int(p.argmax())
                or pick['correct'] != (pick['pick'] == pick['outcome'])):
            raise ValueError('Invalid outcome or inconsistent saved pick/correct flag.')
        market = None
        try:
            odds = np.asarray(game.get('odds'), dtype=float)
            if odds.shape == (3,) and np.isfinite(odds).all() and np.all(odds > 1):
                implied = 1 / odds
                market = float(implied[1] / implied.sum())
        except (ValueError, TypeError):
            pass
        rows.append({'game_id': game['id'], 'start_time': game['start_time'],
                     'home': game['home'], 'away': game['away'],
                     'p_home': float(p[0]), 'p_draw': float(p[1]), 'p_away': float(p[2]),
                     'pick': int(p.argmax()), 'outcome': int(game['outcome']),
                     'is_draw': int(game['outcome'] == 1),
                     'normalized_b365_draw': market})
    rows.sort(key=lambda row: (row['start_time'], row['game_id']))
    bins = []
    for index in range(10):
        group = [row for row in rows if min(9, int(row['p_draw'] * 10)) == index]
        bins.append({'lower': index / 10, 'upper': (index + 1) / 10,
                     'upper_inclusive': index == 9, **summarize(group)})
    selected = [row for row in rows if row['pick'] == 1]
    quoted = [row for row in rows if row['normalized_b365_draw'] is not None]
    return {'all_soccer_test': summarize(rows),
            'draw_selected': {**summarize(selected), 'fraction_of_games': len(selected) / len(rows)},
            'maximum_predicted_draw': max(row['p_draw'] for row in rows),
            'draw_probability_bins': bins,
            'historical_odds_comparison': {
                'n_with_complete_odds': len(quoted), 'n_missing_or_invalid_odds': len(rows) - len(quoted),
                'mean_normalized_b365_draw': (
                    sum(row['normalized_b365_draw'] for row in quoted) / len(quoted) if quoted else None),
                'matched_fly_and_outcomes': summarize(quoted),
                'method': '(1 / B365D) / (1 / B365H + 1 / B365D + 1 / B365A)',
                'limitation': 'Historical bookmaker price proxy, not human forecasts or verified executable quotes.'}}, rows


def build_report(run_dir):
    filenames = ['training-games.json', 'training-data.npz', 'backtest-picks.json', 'checkpoint.npz']
    paths = {name: run_dir / name for name in filenames}
    games = json.loads(paths['training-games.json'].read_text())['games']
    unique_rows(games, 'id')
    saved = json.loads(paths['backtest-picks.json'].read_text())
    if saved['run_id'] != run_dir.name or saved['mode'] != 'retrospective_backtest':
        raise ValueError('Expected a frozen retrospective run matching the directory.')
    with np.load(paths['training-data.npz'], allow_pickle=False) as data:
        y, sport = data['y'], data['sport']
        if (y.shape != (len(games),) or sport.shape != y.shape
                or not np.array_equal(y, [game['outcome'] for game in games])
                or not np.array_equal(sport, [game['sport'] == 'baseball' for game in games])):
            raise ValueError('Training arrays and frozen game rows are not aligned.')
        masks = [data[name] for name in ('train', 'validation', 'test')]
        if (any(mask.shape != y.shape or mask.dtype != bool for mask in masks)
                or not np.all(np.stack(masks).sum(0) == 1)):
            raise ValueError('Each game must belong to exactly one split.')
        split_rates = {}
        for name, mask in zip(('train', 'validation', 'test'), masks):
            selected = mask & (sport == 0)
            n, hits = int(selected.sum()), int((y[selected] == 1).sum())
            split_rates[name] = {'n': n, 'draws': hits, 'draw_rate': hits / n if n else None}
        test_games = [game for game, keep in zip(games, data['test'] & (sport == 0)) if keep]
    picks = [pick for pick in saved['picks'] if pick['sport'] == 'soccer']
    report, rows = analyze_rows(picks, test_games)
    report = {'run_id': saved['run_id'], 'mode': saved['mode'],
              'source_sha256': {name: hashlib.sha256(path.read_bytes()).hexdigest()
                                for name, path in paths.items()},
              'period': {'first_soccer_test_kickoff': rows[0]['start_time'],
                         'last_soccer_test_kickoff': rows[-1]['start_time']},
              'soccer_split_draw_rates': split_rates, **report,
              'limitations': [
                  'Post-hoc descriptive audit of one previously evaluated model and chronological test split.',
                  'Wilson intervals assume independent observations; teams and matchweeks can be correlated.',
                  'No human-forecast panel; historical prices lack verified point-in-time quote availability.',
                  'No stakes, fills, ROI, retraining or prospective validation are produced by this audit.']}
    return report, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=Path('output/runs/20260910T232621Z'))
    parser.add_argument('--output', type=Path, default=Path('docs/evidence/draw-audit-2026-09-10.json'))
    args = parser.parse_args()
    report, rows = build_report(args.run)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    with args.output.with_suffix('.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({key: report[key] for key in ('all_soccer_test', 'draw_selected',
                                                 'historical_odds_comparison')}, indent=2))


if __name__ == '__main__':
    main()
