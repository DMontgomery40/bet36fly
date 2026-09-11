"""Evaluation of the predeclared taught-versus-untaught diagnostic panel.

Criteria are the frozen section 5 of output/collaboration/reward-repair/evidence/
candidate-rule-spec-v1.1.md. All comparisons use compartment gain SUMS on both sides.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .experiments import IDENTIFIER, safe_directory

EVIDENCE_NOTE = 'docs/evidence/reward-repair-phase1.md'

PHASES = ('pre_onset', 'stimulus_plastic', 'post_stimulus')
COMPARTMENT_OF = {'home': 0, 'away': 1}
SEED_SETS = ('base', 'alt')
CONDITIONS = ('frozen', 'untaught', 'home', 'away')


RULE_REFERENCE = {'legacy': 'tonic-baseline', 'candidate': 'none'}
MASK_POLICIES = ('all', 'gamma')


def panel_protocol(base, rule, away_mask):
    """Protocol for one panel run: the requested rule and mask always win over inherited fields."""
    if rule not in RULE_REFERENCE:
        raise ValueError(f'rule must be one of {sorted(RULE_REFERENCE)}.')
    if away_mask not in MASK_POLICIES:
        raise ValueError(f'away_mask must be one of {MASK_POLICIES}.')
    return dict(base, dan_reference=RULE_REFERENCE[rule], away_plasticity_mask=away_mask)


class PanelIncomplete(ValueError):
    """The rows do not form the exact predeclared matrix; no criterion may be reported as passed."""


def check_panel_complete(rows, *, expected_games, seed_sets=SEED_SETS, conditions=CONDITIONS):
    """Require every (game, seed set, condition) exactly once with finite two-component applied sums."""
    rows = list(rows)
    if not rows:
        raise PanelIncomplete('empty panel')
    keys = [(r['game'], r['seed_set'], r['condition']) for r in rows]
    if len(set(keys)) != len(keys):
        raise PanelIncomplete('duplicate rows for the same game, seed set and condition')
    present_seed_sets = {k[1] for k in keys}
    present_conditions = {k[2] for k in keys}
    present_games = {k[0] for k in keys}
    if set(seed_sets) - present_seed_sets:
        raise PanelIncomplete(f'missing seed set {sorted(set(seed_sets) - present_seed_sets)}')
    if set(conditions) - present_conditions:
        raise PanelIncomplete(f'missing condition {sorted(set(conditions) - present_conditions)}')
    if set(expected_games) - present_games:
        raise PanelIncomplete(f'missing game {sorted(set(expected_games) - present_games)}')
    expected = {(g, s, c) for g in expected_games for s in seed_sets for c in conditions}
    if set(keys) != expected:
        raise PanelIncomplete('rows do not match the expected game x seed set x condition matrix')
    for row in rows:
        applied = np.asarray(row['applied'], dtype=np.float64)
        if applied.shape != (2,):
            raise PanelIncomplete('applied must have two components (home, away)')
        if not np.isfinite(applied).all():
            raise PanelIncomplete('non-finite applied values')
    return dict(games=len(expected_games), seed_sets=list(seed_sets), conditions=len(conditions), rows=len(rows))


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


def evaluate_panel(rows, *, expected_games=None, effect_ratio=3.0, guard_ratio=0.5, leak_ratio=0.05):
    """Evaluate criteria 1, 2, 3 and 5 on single-trial panel rows.

    Each row: game, seed_set, condition in {frozen, untaught, home, away}, applied (per-compartment
    gain sums), clipped (count of bound hits). Taught rows gain an 'effect' entry (taught - untaught
    for the same game and seed set). Without ``expected_games`` the panel is evaluated descriptively
    and every criterion is reported as not passed and incomplete; with it, the exact matrix is
    enforced by ``check_panel_complete`` before any criterion is computed.
    """
    rows = list(rows)
    complete = expected_games is not None
    if complete:
        check_panel_complete(rows, expected_games=expected_games)
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
    if not complete:
        for value in criteria.values():
            value['passed'] = False
            value['note'] = 'incomplete panel: evaluated descriptively without a declared matrix; not a gate result'
    overall_effect = [_mean([mean_effect[(label, s)] for s in seed_sets]) for label in COMPARTMENT_OF]
    return dict(rows=out_rows, games=games, seed_sets=seed_sets, complete=complete, criteria=criteria,
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


# --- read-only registry of stored diagnostic panels (served by the API; never the npz arrays) ---

def _load_summary(directory):
    summary = json.loads((directory / 'summary.json').read_text())
    if summary.get('run_id') != directory.name:
        raise ValueError('Diagnostic identity mismatch.')
    return summary


def _compact(summary, has_attribution):
    criteria = summary.get('criteria', {})
    protocol = summary.get('identity', {}).get('protocol', {})
    return dict(
        run_id=summary['run_id'], rule=summary.get('rule'), created_at=summary.get('created_at'),
        dan_reference=protocol.get('dan_reference'), away_plasticity_mask=protocol.get('away_plasticity_mask'),
        panel_complete=bool(summary.get('panel_complete', False)), panel_note=summary.get('panel_note'),
        all_passed=bool(summary.get('all_passed', False)),
        criteria={name: bool(value.get('passed', False)) for name, value in criteria.items()},
        untaught_guard={key: {k: value.get(k) for k in ('mean', 'sd', 'limit', 'passed')}
                        for key, value in criteria.get('untaught_guard', {}).get('evaluations', {}).items()},
        teaching_specific={key: {k: value.get(k) for k in ('mean_effect', 'mean_untaught', 'required_magnitude', 'passed')}
                           for key, value in criteria.get('teaching_specific', {}).get('evaluations', {}).items()},
        has_attribution=has_attribution,
        native_binary_sha256=summary.get('native_binary', {}).get('sha256'),
        source_unchanged_during_run=summary.get('source_unchanged_during_run'),
        plastic_edges=summary.get('anatomy', {}).get('plastic_edges'),
        eligible_edges=summary.get('anatomy', {}).get('eligible_edges'),
    )


def list_diagnostics(root):
    directory = Path(root) / 'output/diagnostics'
    if not directory.exists():
        return []
    entries = []
    for child in directory.iterdir():
        if not child.is_dir() or not IDENTIFIER.fullmatch(child.name):
            continue
        try:
            summary = _load_summary(child)
        except (ValueError, OSError):
            continue
        entries.append(_compact(summary, (child / 'attribution.json').is_file()))
    return sorted(entries, key=lambda e: (e['created_at'] or '', e['run_id']), reverse=True)


def read_diagnostic(root, run_id):
    directory = safe_directory(Path(root) / 'output/diagnostics', run_id)
    if not directory.is_dir():
        raise FileNotFoundError(run_id)
    summary = _load_summary(directory)
    attribution_path = directory / 'attribution.json'
    attribution = json.loads(attribution_path.read_text()) if attribution_path.is_file() else None
    return dict(summary=summary, attribution=attribution)
