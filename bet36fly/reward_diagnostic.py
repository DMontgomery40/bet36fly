"""Evaluation of the predeclared taught-versus-untaught diagnostic panel.

Criteria are the frozen section 5 of output/collaboration/reward-repair/evidence/
candidate-rule-spec-v1.1.md. All comparisons use compartment gain SUMS on both sides.
"""
from __future__ import annotations

import numpy as np

PHASES = ('pre_onset', 'stimulus_plastic', 'post_stimulus')
COMPARTMENT_OF = {'home': 0, 'away': 1}
SEED_SETS = ('base', 'alt')


def phase_sums(rule_bins, *, bin_ms, onset_ms, stimulus_ms):
    """Sum recorded per-bin terms over the three trial phases; returns {phase: [groups, terms]}."""
    bins = np.asarray(rule_bins, dtype=np.float64)
    if bins.ndim != 3 or bin_ms <= 0 or not 0 <= onset_ms <= stimulus_ms <= bins.shape[0] * bin_ms:
        raise ValueError('phase_sums needs [bins, groups, terms] and 0 <= onset <= stimulus <= duration.')
    onset, offset = int(round(onset_ms / bin_ms)), int(round(stimulus_ms / bin_ms))
    return {'pre_onset': bins[:onset].sum(0), 'stimulus_plastic': bins[onset:offset].sum(0),
            'post_stimulus': bins[offset:].sum(0)}


def compartment_sums(gain_delta, plastic_compartments, n_compartments):
    delta = np.asarray(gain_delta, dtype=np.float64)
    compartments = np.asarray(plastic_compartments)
    if delta.shape != compartments.shape:
        raise ValueError('gain_delta and plastic_compartments must align.')
    return np.array([delta[compartments == c].sum() for c in range(int(n_compartments))])


def _mean(values):
    return float(np.mean(values)) if len(values) else float('nan')


def evaluate_panel(rows, *, effect_ratio=3.0, guard_ratio=0.5, leak_ratio=0.05):
    """Evaluate criteria 1, 2, 3 and 5 on single-trial panel rows.

    Each row: game, seed_set, condition in {frozen, untaught, home, away}, applied (per-compartment
    gain sums), clipped (count of bound hits). Taught rows gain an 'effect' entry (taught - untaught
    for the same game and seed set).
    """
    table = {}
    for row in rows:
        table[(row['game'], row['seed_set'], row['condition'])] = np.asarray(row['applied'], dtype=np.float64)
    out_rows = []
    for row in rows:
        entry = dict(row, applied=[float(x) for x in np.asarray(row['applied'], dtype=np.float64)])
        if row['condition'] in COMPARTMENT_OF:
            untaught = table[(row['game'], row['seed_set'], 'untaught')]
            entry['effect'] = [float(x) for x in np.asarray(row['applied'], dtype=np.float64) - untaught]
        out_rows.append(entry)
    seed_sets = sorted({row['seed_set'] for row in rows}, key=lambda s: (s not in SEED_SETS, s))
    games = sorted({row['game'] for row in rows})

    def series(seed_set, condition, compartment):
        return np.array([table[(g, seed_set, condition)][compartment] for g in games])

    teaching, guard, cross = {}, {}, {}
    mean_effect = {}
    for seed_set in seed_sets:
        for label, c in COMPARTMENT_OF.items():
            effects = series(seed_set, label, c) - series(seed_set, 'untaught', c)
            untaught = series(seed_set, 'untaught', c)
            m_eff, m_un = _mean(effects), _mean(untaught)
            mean_effect[(label, seed_set)] = m_eff
            teaching[f'{label}/{seed_set}'] = dict(
                mean_effect=m_eff, mean_untaught=m_un, sd_effect=float(np.std(effects, ddof=1)) if len(effects) > 1 else 0.0,
                effects=[float(x) for x in effects], negative_count=int(np.sum(effects < 0)),
                required_magnitude=effect_ratio * abs(m_un),
                passed=bool(m_eff < 0 and abs(m_eff) >= effect_ratio * abs(m_un)))
            sd = float(np.std(untaught, ddof=1)) if len(untaught) > 1 else 0.0
            guard[f'{label}/{seed_set}'] = dict(mean=m_un, sd=sd, limit=guard_ratio * sd,
                                                values=[float(x) for x in untaught],
                                                passed=bool(abs(m_un) <= guard_ratio * sd))
        for taught_label, other_label in (('home', 'away'), ('away', 'home')):
            other = COMPARTMENT_OF[other_label]
            leak = _mean(series(seed_set, taught_label, other) - series(seed_set, 'untaught', other))
            limit = leak_ratio * abs(mean_effect[(taught_label, seed_set)])
            cross[f'{taught_label}_teaching_into_{other_label}/{seed_set}'] = dict(
                leak=leak, limit=limit, passed=bool(abs(leak) <= limit))
    clipped_total = int(sum(int(row.get('clipped', 0)) for row in rows))
    criteria = dict(
        teaching_specific=dict(passed=all(v['passed'] for v in teaching.values()), evaluations=teaching),
        untaught_guard=dict(passed=all(v['passed'] for v in guard.values()), evaluations=guard),
        cross_compartment=dict(passed=all(v['passed'] for v in cross.values()), evaluations=cross),
        no_bound_hits=dict(passed=clipped_total == 0, clipped_total=clipped_total),
    )
    overall_effect = [_mean([mean_effect[(label, s)] for s in seed_sets]) for label in COMPARTMENT_OF]
    return dict(rows=out_rows, games=games, seed_sets=seed_sets, criteria=criteria,
                mean_effect_by_compartment=overall_effect)


def evaluate_cumulative(trajectory, *, mean_effect, ratio=4.0):
    """Criterion 4: |sum_c(g_after - g_initial)| <= ratio * |mean matched effect_c|, gain sums both sides."""
    path = np.asarray(trajectory, dtype=np.float64)
    effect = np.asarray(mean_effect, dtype=np.float64)
    if path.ndim != 2 or path.shape[1] != effect.shape[0]:
        raise ValueError('trajectory must be [trials, compartments] aligned with mean_effect.')
    per = []
    for c in range(path.shape[1]):
        final, limit = float(path[-1, c]), float(ratio * abs(effect[c]))
        per.append(dict(compartment=c, final_sum=final, limit=limit, passed=bool(abs(final) <= limit)))
    return dict(passed=all(p['passed'] for p in per), per_compartment=per,
                trajectory=[[float(x) for x in row] for row in path])
