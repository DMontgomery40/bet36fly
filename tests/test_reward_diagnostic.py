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


@pytest.mark.parametrize('trajectory', [np.empty((0, 2)), np.zeros((1, 2)), np.zeros((15, 2)),
                                        np.zeros((17, 2)), np.full((16, 2), np.nan),
                                        np.full((16, 2), np.inf)])
def test_cumulative_rejects_short_empty_extra_or_nonfinite_trajectories(trajectory):
    with pytest.raises(ValueError):
        evaluate_cumulative(trajectory, mean_effect=[-1, -1])


@pytest.mark.parametrize('effect', [[np.nan, -1], [np.inf, -1], [], [[-1, -1]]])
def test_cumulative_rejects_malformed_effects(effect):
    with pytest.raises(ValueError):
        evaluate_cumulative(np.zeros((16, 2)), mean_effect=effect)


def diagnostic_inputs():
    return dict(X=np.arange(80, dtype=np.float32).reshape(20, 4),
                source_indices=np.arange(100, 120), calibration_indices=np.arange(102, 118),
                input_mean=np.zeros(4), input_std=np.ones(4))


def select_panel(**kwargs):
    from bet36fly import reward_diagnostic as diagnostic
    return diagnostic.select_panel(diagnostic_inputs(), seed=42, **kwargs)


def test_heldout_selection_uses_remaining_cues_and_predeclared_fresh_seeds():
    selection = select_panel(panel_offset=8, seed_offset=2_000_000)
    assert selection['panel_kind'] == 'held-out'
    assert selection['panel_games'] == list(range(110, 118))
    assert selection['cumulative_games'] == list(range(102, 118))
    assert len(selection['expected_panel']) == 64
    assert selection['expected_panel'][0] == dict(game=110, seed_set='base', seed=2_000_152, condition='frozen')
    assert selection['expected_panel'][4] == dict(game=110, seed_set='alt', seed=3_000_152, condition='frozen')
    assert selection['expected_cumulative'][0] == dict(game=102, seed=2_000_144)
    original = select_panel()
    assert original['panel_kind'] == 'original'
    assert not set(selection['panel_games']) & set(original['panel_games'])
    assert original['expected_panel'][0]['seed'] == 144


@pytest.mark.parametrize('kwargs', [dict(panel_offset=-1), dict(panel_offset=9), dict(panel_offset=0.5),
    dict(seed_offset=-1), dict(seed_offset=True), dict(seed_offset=2**64), dict(games=0),
    dict(games=9), dict(cumulative_games=0), dict(cumulative_games=17),
    dict(panel_kind='held-out'), dict(panel_kind='unknown')])
def test_panel_selectors_fail_early(kwargs):
    with pytest.raises(ValueError):
        select_panel(**kwargs)


@pytest.mark.parametrize('field,value', [
    ('calibration_indices', np.arange(102, 117)),
    ('calibration_indices', np.array([102] * 16)),
    ('calibration_indices', np.arange(103, 119).astype(float)),
    ('calibration_indices', np.arange(200, 216)),
    ('source_indices', np.array([100] * 20)),
    ('source_indices', np.arange(19)),
    ('X', np.full((20, 4), np.nan)), ('input_mean', np.zeros(3)),
    ('input_std', np.zeros(4)), ('input_std', np.full(4, np.inf)),
])
def test_panel_input_validation_rejects_incoherent_calibration(field, value):
    from bet36fly import reward_diagnostic as diagnostic
    inputs = diagnostic_inputs()
    inputs[field] = value
    with pytest.raises(ValueError):
        diagnostic.select_panel(inputs, seed=42)


def selected_rows(selection):
    return [dict(r, applied=[0, 0], clipped=0) for r in selection['expected_panel']]


def cumulative_rows(selection):
    return [dict(r, applied=[0, 0], cumulative=[0, 0], clipped=0) for r in selection['expected_cumulative']]


def test_completeness_depends_on_actual_matrix_and_cumulative_rows():
    from bet36fly import reward_diagnostic as diagnostic
    selection = select_panel(panel_offset=8, seed_offset=2_000_000)
    assert diagnostic.check_diagnostic_complete(selected_rows(selection), cumulative_rows(selection), selection)
    debug = select_panel(games=2, cumulative_games=3)
    assert debug['panel_kind'] == 'debug'
    assert not diagnostic.check_diagnostic_complete(selected_rows(debug), cumulative_rows(debug), debug)


@pytest.mark.parametrize('kind', ['short', 'empty', 'duplicate', 'wrong_game', 'wrong_seed', 'nonfinite', 'extra'])
def test_diagnostic_rejects_malformed_cumulative_rows(kind):
    from bet36fly import reward_diagnostic as diagnostic
    selection = select_panel()
    rows = cumulative_rows(selection)
    if kind == 'short':
        rows = rows[:-1]
    if kind == 'empty':
        rows = []
    if kind == 'duplicate':
        rows[-1] = rows[0]
    if kind == 'wrong_game':
        rows[0]['game'] = 999
    if kind == 'wrong_seed':
        rows[0]['seed'] += 1
    if kind == 'nonfinite':
        rows[0]['cumulative'] = [np.nan, 0]
    if kind == 'extra':
        rows.append(rows[0])
    with pytest.raises(PanelIncomplete):
        diagnostic.check_diagnostic_complete(selected_rows(selection), rows, selection)


@pytest.mark.parametrize('kind', ['short', 'duplicate', 'wrong_seed'])
def test_diagnostic_rejects_panel_rows_that_disagree_with_frozen_selection(kind):
    from bet36fly import reward_diagnostic as diagnostic
    selection = select_panel()
    rows = selected_rows(selection)
    if kind == 'short':
        rows = rows[:-1]
    if kind == 'duplicate':
        rows[-1] = rows[0]
    if kind == 'wrong_seed':
        rows[0]['seed'] += 1
    with pytest.raises(PanelIncomplete):
        diagnostic.check_diagnostic_complete(rows, cumulative_rows(selection), selection)


@pytest.mark.parametrize('games', [[], [0, 0], [0.0, 1.0]])
def test_panel_evaluator_rejects_malformed_expected_games(games):
    with pytest.raises(PanelIncomplete):
        check_panel_complete(panel(0, -1, games=2), expected_games=games)


def frozen_graph(root):
    from bet36fly import reward_diagnostic as diagnostic
    from bet36fly.reward_protocol import file_hash
    identity = dict(graph_hashes={})
    for name in diagnostic.GRAPH_FILES:
        path = root / 'data/brain' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
        identity['graph_hashes'][name] = file_hash(path)
    for relative, field in [('data/brain/nodes.feather', 'node_annotations_sha256'),
                            ('data/raw/annotations.feather', 'raw_annotations_sha256')]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(relative.encode())
        identity[field] = file_hash(path)
    return identity


@pytest.mark.parametrize('relative', ['data/brain/counts.npy', 'data/brain/nodes.feather', 'data/raw/annotations.feather'])
def test_graph_and_annotation_identity_requires_actual_frozen_hash_match(tmp_path, relative):
    from bet36fly import reward_diagnostic as diagnostic
    frozen = frozen_graph(tmp_path)
    before = diagnostic.verify_graph_inputs(tmp_path, frozen)
    assert len(before) == 11
    (tmp_path / relative).write_bytes(b'changed')
    with pytest.raises(ValueError, match='hash'):
        diagnostic.verify_graph_inputs(tmp_path, frozen)


def test_graph_identity_refuses_missing_manifest_hash(tmp_path):
    from bet36fly import reward_diagnostic as diagnostic
    frozen = frozen_graph(tmp_path)
    del frozen['graph_hashes']['counts.npy']
    with pytest.raises(ValueError):
        diagnostic.verify_graph_inputs(tmp_path, frozen)


def test_preregistration_is_frozen_before_neural_execution_and_never_overwritten(tmp_path):
    from scripts import reward_teaching_diagnostic as cli
    path = tmp_path / 'preregistered.json'
    identity = dict(selection=select_panel(), graph_hashes={'a': 'original'}, code_hashes={'b': 'version'})
    first = cli.freeze_preregistration(path, identity, 'diag-test')
    saved = path.read_bytes()
    assert first['status'] == 'preregistered-not-run'
    assert cli.freeze_preregistration(path, identity, 'diag-test') == first
    assert path.read_bytes() == saved
    with pytest.raises(ValueError):
        cli.freeze_preregistration(path, dict(identity, graph_hashes={'a': 'changed'}), 'diag-test')
    assert path.read_bytes() == saved


@pytest.mark.parametrize('missing', ['X', 'source_indices', 'calibration_indices', 'input_mean', 'input_std'])
def test_selection_requires_every_frozen_input_array(missing):
    from bet36fly import reward_diagnostic as diagnostic
    inputs = diagnostic_inputs()
    del inputs[missing]
    with pytest.raises(ValueError, match='Missing'):
        diagnostic.select_panel(inputs, seed=42)


def test_cli_preregister_only_binds_graph_selection_and_code_without_building(tmp_path, monkeypatch):
    import json
    from scripts import reward_teaching_diagnostic as cli
    from bet36fly.reward_protocol import file_hash
    frozen = frozen_graph(tmp_path)
    pilot = tmp_path / 'pilot'
    (pilot / 'source').mkdir(parents=True)
    (pilot / 'manifest.json').write_text(json.dumps({'identity': frozen}))
    (pilot / 'source/protocol.json').write_text(json.dumps(dict(seed=42)))
    np.savez(pilot / 'source/inputs.npz', **diagnostic_inputs())
    monkeypatch.setattr(cli, 'ROOT', tmp_path)
    def forbidden(*args, **kwargs):
        raise AssertionError('Preregistration must not build or run a neural circuit.')
    monkeypatch.setattr(cli, 'make_circuit', forbidden)
    receipt = tmp_path / 'heldout.json'
    out = tmp_path / 'diagnostics'
    args = ['--rule', 'candidate', '--away-mask', 'gamma', '--pilot', str(pilot),
            '--panel-kind', 'held-out', '--panel-offset', '8', '--seed-offset', '2000000',
            '--preregistration', str(receipt), '--preregister-only', '--out', str(out)]
    assert cli.main(args) == 0
    document = json.loads(receipt.read_text())
    assert document['identity']['selection']['panel_games'] == list(range(110, 118))
    assert document['identity']['graph_hashes']['data/brain/counts.npy'] == file_hash(tmp_path / 'data/brain/counts.npy')
    assert document['identity']['code_hashes']['reward_teaching_diagnostic.py'] == file_hash(cli.__file__)
    assert not out.exists()
    assert cli.main(args) == 0  # identical pre-execution receipt is idempotent
    (tmp_path / 'data/brain/counts.npy').write_bytes(b'different graph')
    with pytest.raises(ValueError, match='hash'):
        cli.main(args)
    assert json.loads(receipt.read_text()) == document


@pytest.mark.parametrize('clipped', [-1, 0.5, np.nan, np.inf, True])
def test_panel_rejects_invalid_bound_hit_counts(clipped):
    rows = panel(0, -1)
    rows[0]['clipped'] = clipped
    with pytest.raises(PanelIncomplete):
        check_panel_complete(rows, expected_games=list(range(8)))


@pytest.mark.parametrize('error', [-0.001, 0.001])
def test_cumulative_rows_must_reconcile_to_their_applied_running_sum(error):
    from bet36fly import reward_diagnostic as diagnostic
    selection = select_panel()
    rows = cumulative_rows(selection)
    for index, row in enumerate(rows):
        row['applied'] = [0.125, -0.25]
        row['cumulative'] = [(index + 1) * 0.125, -(index + 1) * 0.25]
    assert diagnostic.check_diagnostic_complete(selected_rows(selection), rows, selection)
    rows[7]['cumulative'][0] += error
    with pytest.raises(PanelIncomplete, match='running sum'):
        diagnostic.check_diagnostic_complete(selected_rows(selection), rows, selection)


@pytest.mark.parametrize('source', ['panel', 'cumulative', 'final_lower', 'final_upper'])
def test_overall_bound_guard_includes_cumulative_only_hits_and_saved_gain_equality(source):
    from bet36fly import reward_diagnostic as diagnostic
    rows = [dict(clipped=0)]
    cumulative = [dict(clipped=0)]
    gains = np.array([1.0, 1.0])
    if source == 'panel':
        rows[0]['clipped'] = 1
    elif source == 'cumulative':
        cumulative[0]['clipped'] = 1
    elif source == 'final_lower':
        gains[0] = 0.5
    else:
        gains[0] = 1.5
    result = diagnostic.evaluate_bound_hits(rows, cumulative, gains, gain_bounds=[0.5, 1.5],
                                           plastic_mask=np.array([1, 0]))
    assert result['passed'] is False


def test_bound_guard_ignores_excluded_final_edges_and_retains_finite_validation():
    from bet36fly import reward_diagnostic as diagnostic
    rows = [dict(clipped=0)]
    assert diagnostic.evaluate_bound_hits(rows, rows, [1, 0.5], gain_bounds=[0.5, 1.5],
                                         plastic_mask=[1, 0])['passed']
    for gains in ([np.nan, 1], [np.inf, 1]):
        with pytest.raises(ValueError):
            diagnostic.evaluate_bound_hits(rows, rows, gains, gain_bounds=[0.5, 1.5], plastic_mask=[1, 0])


@pytest.mark.parametrize('clipped', [-1, 0.5, np.nan, np.inf, True, None])
def test_cumulative_bound_counts_are_required_nonnegative_integers(clipped):
    from bet36fly import reward_diagnostic as diagnostic
    selection = select_panel()
    rows = cumulative_rows(selection)
    rows[0]['clipped'] = clipped
    with pytest.raises(PanelIncomplete):
        diagnostic.check_diagnostic_complete(selected_rows(selection), rows, selection)


@pytest.mark.parametrize('source', ['panel', 'cumulative'])
def test_complete_diagnostic_requires_explicit_bound_evidence_in_every_row(source):
    from bet36fly import reward_diagnostic as diagnostic
    selection = select_panel()
    rows, cumulative = selected_rows(selection), cumulative_rows(selection)
    del (rows if source == 'panel' else cumulative)[0]['clipped']
    with pytest.raises(PanelIncomplete):
        diagnostic.check_diagnostic_complete(rows, cumulative, selection)


@pytest.mark.parametrize('source', ['panel', 'cumulative'])
@pytest.mark.parametrize('value', ['missing', -1, 0.5, True, np.nan, np.inf])
def test_bound_evaluator_validates_evidence_without_completeness_helper(source, value):
    from bet36fly import reward_diagnostic as diagnostic
    rows, cumulative = [dict(clipped=0)], [dict(clipped=0)]
    target = rows if source == 'panel' else cumulative
    if value == 'missing':
        target[0] = {}
    else:
        target[0]['clipped'] = value
    with pytest.raises(ValueError):
        diagnostic.evaluate_bound_hits(rows, cumulative, [1], gain_bounds=[0.5, 1.5], plastic_mask=[1])
