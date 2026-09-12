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


GRAPH_FILES = ('counts.npy', 'ids.npy', 'in_degree.npy', 'indptr.npy', 'kc.npy',
               'mbon.npy', 'post.npy', 'sensory.npy', 'signs.npy')


def _integer(value, name, *, minimum=0, maximum=2**64 - 1):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or not minimum <= value <= maximum:
        raise ValueError(f'{name} must be an integer in [{minimum}, {maximum}].')
    return int(value)


def _indices(values, name):
    array = np.asarray(values)
    if array.ndim != 1 or array.dtype.kind not in 'iu' or not len(array) or np.any(array < 0):
        raise ValueError(f'{name} must be a nonempty vector of nonnegative integer IDs.')
    if len(np.unique(array)) != len(array):
        raise ValueError(f'{name} contains duplicate IDs.')
    return [int(x) for x in array]


def select_panel(inputs, *, seed, panel_offset=0, seed_offset=0, games=8,
                 cumulative_games=16, panel_kind=None):
    """Validate the complete frozen calibration source before selecting an outcome-blind panel."""
    panel_offset = _integer(panel_offset, 'panel_offset', maximum=15)
    seed_offset = _integer(seed_offset, 'seed_offset')
    seed = _integer(seed, 'seed')
    games = _integer(games, 'games', minimum=1, maximum=8)
    cumulative_games = _integer(cumulative_games, 'cumulative_games', minimum=1, maximum=16)
    required = {'X', 'source_indices', 'calibration_indices', 'input_mean', 'input_std'}
    if not required.issubset(inputs.keys()):
        raise ValueError(f'Missing diagnostic input arrays: {sorted(required - set(inputs.keys()))}')
    source = _indices(inputs['source_indices'], 'source_indices')
    calibration = _indices(inputs['calibration_indices'], 'calibration_indices')
    x, mean, std = (np.asarray(inputs[k]) for k in ('X', 'input_mean', 'input_std'))
    if (x.ndim != 2 or x.shape[0] != len(source) or not x.shape[1]
            or mean.shape != (x.shape[1],) or std.shape != mean.shape
            or any(a.dtype.kind not in 'fiu' or not np.isfinite(a).all() for a in (x, mean, std))
            or np.any(std <= 0)):
        raise ValueError('Features, finite mean and positive standard deviation must align with source IDs.')
    if len(calibration) != 16 or not set(calibration).issubset(source):
        raise ValueError('Exactly 16 unique calibration IDs must resolve in source_indices.')
    if panel_offset + games > len(calibration):
        raise ValueError('Panel selector extends past the calibration inputs.')
    _integer(seed + seed_offset + 1_000_000 + max(calibration), 'maximum trial seed')
    canonical = ('original' if (panel_offset, seed_offset, games, cumulative_games) == (0, 0, 8, 16)
                 else 'held-out' if (panel_offset, seed_offset, games, cumulative_games) == (8, 2_000_000, 8, 16)
                 else 'debug')
    if panel_kind is not None and (panel_kind not in ('original', 'held-out', 'debug')
                                   or panel_kind != 'debug' and panel_kind != canonical):
        raise ValueError('panel_kind does not match its preregistered selectors.')
    chosen = calibration[panel_offset:panel_offset + games]
    cumulative = calibration[:cumulative_games]
    return dict(panel_kind=panel_kind or canonical, panel_offset=panel_offset, seed_offset=seed_offset,
                alt_seed_offset=1_000_000, calibration_games=calibration, panel_games=chosen,
                cumulative_games=cumulative,
                expected_panel=[dict(game=g, seed_set=s, seed=seed + seed_offset + g + offset, condition=c)
                                for g in chosen for s, offset in (('base', 0), ('alt', 1_000_000))
                                for c in CONDITIONS],
                expected_cumulative=[dict(game=g, seed=seed + seed_offset + g) for g in cumulative])


def verify_graph_inputs(root, frozen_identity):
    """Bind every graph/annotation file actually consumed to the historical pilot's hashes."""
    from .reward_protocol import file_hash
    root = Path(root)
    try:
        expected = {f'data/brain/{name}': frozen_identity['graph_hashes'][name] for name in GRAPH_FILES}
        expected['data/brain/nodes.feather'] = frozen_identity['node_annotations_sha256']
        expected['data/raw/annotations.feather'] = frozen_identity['raw_annotations_sha256']
    except (KeyError, TypeError) as exc:
        raise ValueError('Frozen pilot is missing graph or annotation hashes.') from exc
    actual = {}
    for relative, reference in expected.items():
        if not isinstance(reference, str) or len(reference) != 64 or any(c not in '0123456789abcdef' for c in reference):
            raise ValueError(f'Invalid frozen hash for {relative}.')
        try:
            actual[relative] = file_hash(root / relative)
        except OSError as exc:
            raise ValueError(f'Missing graph input: {relative}.') from exc
        if actual[relative] != reference:
            raise ValueError(f'Graph input hash mismatch: {relative}.')
    return actual


def check_diagnostic_complete(rows, cumulative_rows, selection):
    """Check actual identities/counts and finite results, not requested CLI counts."""
    check_panel_complete(rows, expected_games=selection['panel_games'])
    fields = ('game', 'seed_set', 'seed', 'condition')
    try:
        for row in rows:
            _integer(row['clipped'], 'panel clipped')
        actual = [tuple(r[k] for k in fields) for r in rows]
        expected = [tuple(r[k] for k in fields) for r in selection['expected_panel']]
        if len(actual) != len(expected) or set(actual) != set(expected):
            raise PanelIncomplete('Panel rows disagree with preregistered source IDs or seeds.')
        actual_cumulative = [(r['game'], r['seed']) for r in cumulative_rows]
        expected_cumulative = [(r['game'], r['seed']) for r in selection['expected_cumulative']]
        if actual_cumulative != expected_cumulative or len(set(actual_cumulative)) != len(actual_cumulative):
            raise PanelIncomplete('Cumulative rows disagree with preregistered sequence or seeds.')
        for row in cumulative_rows:
            try:
                _integer(row['clipped'], 'cumulative clipped')
            except ValueError as exc:
                raise PanelIncomplete(str(exc)) from exc
            for field in ('applied', 'cumulative'):
                values = np.asarray(row[field], dtype=float)
                if values.shape != (2,) or not np.isfinite(values).all():
                    raise PanelIncomplete('Cumulative values must have two finite components.')
        # Compare the two independently recorded gain-sum views. This is a
        # numerical consistency tolerance, not a change to the scientific guard.
        running = np.cumsum([r['applied'] for r in cumulative_rows], axis=0, dtype=np.float64)
        if not np.allclose(running, [r['cumulative'] for r in cumulative_rows], rtol=0, atol=1e-6):
            raise PanelIncomplete('Cumulative values disagree with the applied running sum (atol=1e-6).')
    except (KeyError, TypeError) as exc:
        raise PanelIncomplete('Missing or malformed diagnostic row fields.') from exc
    return (selection['panel_kind'] in ('original', 'held-out') and len(rows) == 64
            and len(cumulative_rows) == 16)


def check_panel_complete(rows, *, expected_games, seed_sets=SEED_SETS, conditions=CONDITIONS):
    """Require every (game, seed set, condition) exactly once with finite two-component applied sums."""
    rows = list(rows)
    try:
        expected_games = _indices(expected_games, 'expected_games')
    except ValueError as exc:
        raise PanelIncomplete(str(exc)) from exc
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
        try:
            _integer(row.get('clipped', 0), 'clipped')
        except ValueError as exc:
            raise PanelIncomplete(str(exc)) from exc
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


def evaluate_bound_hits(panel_rows, cumulative_rows, final_gains, *, gain_bounds, plastic_mask):
    """No eligible at/beyond-bound observations in either panel, or in the saved final gains.

    For this native source version the historical ``clipped`` fields also include
    exact equality/dwelling. Counts are observations, not distinct edges or arrivals.
    """
    try:
        panel_count = sum(_integer(r['clipped'], 'panel clipped') for r in panel_rows)
        cumulative_count = sum(_integer(r['clipped'], 'cumulative clipped') for r in cumulative_rows)
    except (KeyError, TypeError) as exc:
        raise ValueError('Explicit bound evidence is required on every panel and cumulative row.') from exc
    gains, bounds, mask = np.asarray(final_gains), np.asarray(gain_bounds), np.asarray(plastic_mask)
    if (gains.ndim != 1 or bounds.shape != (2,) or mask.shape != gains.shape
            or not np.isfinite(gains).all() or not np.isfinite(bounds).all()
            or not 0 < bounds[0] <= bounds[1] or not np.isin(mask, [0, 1]).all()):
        raise ValueError('Bound check needs finite gains/bounds and an aligned binary eligibility mask.')
    eligible = gains[mask.astype(bool)]
    final_count = int(np.count_nonzero((eligible <= bounds[0]) | (eligible >= bounds[1])))
    return dict(passed=panel_count + cumulative_count + final_count == 0,
                clipped_total=panel_count + cumulative_count,
                panel_observations=panel_count, cumulative_observations=cumulative_count,
                final_eligible_edges_at_or_beyond_bounds=final_count,
                semantics='inclusive at-or-beyond-bound observations; exact equality and dwelling included')


def evaluate_cumulative(trajectory, *, mean_effect, ratio=4.0, expected_trials=16):
    """Criterion 4: |sum_c(g_after - g_initial)| <= ratio * |mean matched effect_c|, gain sums both sides."""
    path = np.asarray(trajectory, dtype=np.float64)
    effect = np.asarray(mean_effect, dtype=np.float64)
    expected_trials = _integer(expected_trials, 'expected_trials', minimum=1, maximum=16)
    if (path.shape != (expected_trials, 2) or effect.shape != (2,)
            or not np.isfinite(path).all() or not np.isfinite(effect).all()
            or not np.isfinite(ratio) or ratio <= 0):
        raise ValueError('trajectory must contain the expected finite two-compartment trials and effects.')
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
    rule = summary.get('rule')
    # Runs written before the fields existed: the rule implies the reference (legacy = tonic-baseline,
    # candidate = none), an absent mask field means every edge was eligible, and completeness is
    # reported as null ("not recorded") rather than guessed.
    complete = summary.get('panel_complete')
    return dict(
        run_id=summary['run_id'], rule=rule, created_at=summary.get('created_at'),
        dan_reference=protocol.get('dan_reference') or RULE_REFERENCE.get(rule),
        away_plasticity_mask=protocol.get('away_plasticity_mask') or 'all',
        panel_complete=None if complete is None else bool(complete), panel_note=summary.get('panel_note'),
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
