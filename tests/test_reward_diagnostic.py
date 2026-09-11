import numpy as np
import pytest

from bet36fly.reward_diagnostic import (
    PHASES, compartment_sums, evaluate_cumulative, evaluate_panel, phase_sums,
)


def test_phase_sums_split_bins_at_onset_and_stimulus_offset():
    rule_bins = np.zeros((40, 2, 7))
    rule_bins[:, 0, 2] = 1.0            # one unit of applied change per bin in group 0
    rule_bins[35, 1, 3] = 2.0           # two low clips in the post-stimulus window, group 1

    phases = phase_sums(rule_bins, bin_ms=10.0, onset_ms=100.0, stimulus_ms=300.0)

    assert tuple(phases) == PHASES == ('pre_onset', 'stimulus_plastic', 'post_stimulus')
    assert phases['pre_onset'][0, 2] == 10 and phases['stimulus_plastic'][0, 2] == 20
    assert phases['post_stimulus'][0, 2] == 10
    assert phases['post_stimulus'][1, 3] == 2 and phases['stimulus_plastic'][1, 3] == 0
    assert sum(p[0, 2] for p in phases.values()) == rule_bins[:, 0, 2].sum()


def test_compartment_sums_use_gain_sums_not_means():
    delta = np.array([0.1, 0.1, -0.3, 0.0], np.float32)
    compartments = np.array([0, 0, 1, 1], np.int32)

    np.testing.assert_allclose(compartment_sums(delta, compartments, 2), [0.2, -0.3], atol=1e-7)


def panel(untaught_home, taught_home, *, untaught_away=0.0, taught_away=-1.0, leak=0.0, clipped=0, games=8):
    rows = []
    for seed_set in ('base', 'alt'):
        for game in range(games):
            u = np.array([untaught_home, untaught_away])
            rows.append(dict(game=game, seed_set=seed_set, condition='frozen', applied=np.zeros(2), clipped=0))
            rows.append(dict(game=game, seed_set=seed_set, condition='untaught', applied=u, clipped=clipped))
            rows.append(dict(game=game, seed_set=seed_set, condition='home', applied=u + [taught_home, leak], clipped=clipped))
            rows.append(dict(game=game, seed_set=seed_set, condition='away', applied=u + [leak, taught_away], clipped=clipped))
    return rows


def test_legacy_like_panel_fails_the_teaching_specific_criterion_for_home():
    # Untaught home drift +0.8 against home teaching totalling -1.4: effect -2.2 is not 3x the drift.
    result = evaluate_panel(panel(0.8, -2.2), expected_games=list(range(8)))

    assert result['criteria']['teaching_specific']['passed'] is False
    home_base = result['criteria']['teaching_specific']['evaluations']['home/base']
    assert home_base['mean_effect'] == pytest.approx(-2.2)
    assert home_base['mean_untaught'] == pytest.approx(0.8)
    assert home_base['passed'] is False
    assert result['criteria']['teaching_specific']['evaluations']['away/alt']['passed'] is True


def test_candidate_like_panel_passes_and_reports_every_game():
    rows = panel(0.01, -1.2, untaught_away=-0.01)
    for row in rows:                       # alternate the sign of the untaught noise across games
        if row['condition'] != 'frozen':
            row['applied'] = row['applied'] + (0.05 if row['game'] % 2 else -0.05)
    result = evaluate_panel(rows, expected_games=list(range(8)))

    assert result['criteria']['teaching_specific']['passed'] is True
    assert result['criteria']['untaught_guard']['passed'] is True
    assert result['criteria']['cross_compartment']['passed'] is True
    assert result['criteria']['no_bound_hits']['passed'] is True
    assert len(result['rows']) == 64 and {r['condition'] for r in result['rows']} == {'frozen', 'untaught', 'home', 'away'}
    assert all('effect' in r for r in result['rows'] if r['condition'] in ('home', 'away'))


def test_seed_sets_are_not_pooled():
    rows = panel(0.0, -1.2)
    for row in rows:                       # opposite systematic biases in the two seed sets
        if row['condition'] in ('untaught', 'home', 'away'):
            row['applied'] = row['applied'] + (0.6 if row['seed_set'] == 'base' else -0.6)
    result = evaluate_panel(rows, expected_games=list(range(8)))

    assert result['criteria']['untaught_guard']['passed'] is False
    assert result['criteria']['teaching_specific']['evaluations']['home/base']['passed'] is False


def test_cross_compartment_leak_and_bound_hits_fail_their_guards():
    leaky = evaluate_panel(panel(0.0, -1.0, leak=0.2), expected_games=list(range(8)))
    clipped = evaluate_panel(panel(0.0, -1.0, clipped=1), expected_games=list(range(8)))

    assert leaky['criteria']['cross_compartment']['passed'] is False
    assert leaky['criteria']['cross_compartment']['evaluations']['home_teaching_into_away/base']['leak'] == pytest.approx(0.2)
    assert clipped['criteria']['no_bound_hits']['passed'] is False


def test_cumulative_uses_compartment_gain_sums_on_both_sides():
    trajectory = np.cumsum(np.tile([[0.25, -0.1]], (16, 1)), axis=0)   # ends at +4.0 home, -1.6 away

    passing = evaluate_cumulative(trajectory, mean_effect=np.array([-1.2, -1.0]))
    failing = evaluate_cumulative(trajectory, mean_effect=np.array([-0.9, -1.0]))

    assert passing['passed'] is True and passing['per_compartment'][0]['limit'] == pytest.approx(4.8)
    assert failing['passed'] is False and failing['per_compartment'][0]['final_sum'] == pytest.approx(4.0)
    assert len(passing['trajectory']) == 16


# --- DIAG-001: the evaluator must refuse an incomplete or malformed predeclared matrix ---

from bet36fly.reward_diagnostic import PanelIncomplete, check_panel_complete  # noqa: E402


def test_complete_panel_passes_the_completeness_check():
    rows = panel(0.0, -1.0)
    report = check_panel_complete(rows, expected_games=list(range(8)))
    assert report == dict(games=8, seed_sets=['base', 'alt'], conditions=4, rows=64)


@pytest.mark.parametrize('mutate, reason', [
    (lambda rows: [r for r in rows if r['seed_set'] == 'base'], 'seed set'),
    (lambda rows: [r for r in rows if r['condition'] != 'away'], 'condition'),
    (lambda rows: [r for r in rows if r['game'] != 3], 'game'),
    (lambda rows: rows + [rows[0]], 'duplicate'),
    (lambda rows: [], 'empty'),
    (lambda rows: [dict(r, applied=[float('nan'), 0.0]) if r['condition'] == 'home' and r['game'] == 1 else r for r in rows], 'finite'),
    (lambda rows: [dict(r, applied=[0.0]) if r['condition'] == 'home' and r['game'] == 1 else r for r in rows], 'two'),
])
def test_incomplete_or_malformed_panels_are_rejected(mutate, reason):
    rows = mutate(panel(0.0, -1.0))
    with pytest.raises(PanelIncomplete, match=reason):
        check_panel_complete(rows, expected_games=list(range(8)))
    with pytest.raises(PanelIncomplete):
        evaluate_panel(rows, expected_games=list(range(8)))


def test_evaluate_panel_without_expected_games_is_marked_incomplete_not_passed():
    base_only = [r for r in panel(0.0, -1.0) if r['seed_set'] == 'base']
    result = evaluate_panel(base_only)
    assert result['complete'] is False
    assert result['criteria']['teaching_specific']['passed'] is False
    assert 'incomplete' in result['criteria']['teaching_specific']['note']


# --- DIAG-002: the panel protocol must follow the requested rule and mask, never inherited fields ---

from bet36fly.reward_diagnostic import panel_protocol  # noqa: E402


@pytest.mark.parametrize('inherited_mask', [None, 'all', 'gamma'])
@pytest.mark.parametrize('inherited_reference', [None, 'none', 'tonic-baseline'])
@pytest.mark.parametrize('rule, expected_reference', [('legacy', 'tonic-baseline'), ('candidate', 'none')])
@pytest.mark.parametrize('away_mask', ['all', 'gamma'])
def test_panel_protocol_overrides_inherited_rule_and_mask(inherited_mask, inherited_reference, rule, expected_reference, away_mask):
    base = {'seed': 42, 'tau_ms': 500.0}
    if inherited_mask is not None:
        base['away_plasticity_mask'] = inherited_mask
    if inherited_reference is not None:
        base['dan_reference'] = inherited_reference
    protocol = panel_protocol(base, rule, away_mask)

    assert protocol['dan_reference'] == expected_reference
    assert protocol['away_plasticity_mask'] == away_mask
    assert protocol['seed'] == 42 and protocol['tau_ms'] == 500.0
    assert 'away_plasticity_mask' not in base or base['away_plasticity_mask'] == inherited_mask   # input untouched


def test_panel_protocol_rejects_unknown_rule_or_mask():
    with pytest.raises(ValueError):
        panel_protocol({}, 'moving-average', 'all')
    with pytest.raises(ValueError):
        panel_protocol({}, 'candidate', 'alpha')
