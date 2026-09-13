"""Exact recorded-count and causal-prefix contracts, independent synthetic cases."""

import importlib.util
import struct
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    "dan_causal_prefix", Path(__file__).with_name("dan_causal_prefix.py")
)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def f32_fraction(k, n):
    return struct.unpack("f", struct.pack("f", float(Fraction(k, n))))[0]


@pytest.mark.parametrize("n", [1, 2, 3, 7, 22, 31, 127])
def test_every_representable_population_count_decodes_exactly(n):
    means = np.array([[f32_fraction(k, n)] for k in range(n + 1)], np.float32)
    expected = np.array([[k] for k in range(n + 1)], np.int64)
    np.testing.assert_array_equal(m.decode_pool(means, [n]), expected)


@pytest.mark.parametrize("n,k", [(2, 0), (2, 1), (2, 2), (22, 0), (22, 1), (22, 11), (22, 22)])
@pytest.mark.parametrize("direction", [-np.inf, np.inf])
def test_one_ulp_corruption_is_not_rounded_to_an_event_count(n, k, direction):
    a = np.array([[f32_fraction(k, n)]], np.float32)
    a[0, 0] = np.nextafter(a[0, 0], np.float32(direction))
    with pytest.raises(ValueError):
        m.decode_pool(a, [n])


@pytest.mark.parametrize(
    "a,p",
    [
        (np.zeros((3, 2)), [2, 22]),
        (np.zeros((0, 2), np.float32), [2, 22]),
        (np.zeros(2, np.float32), [2, 22]),
        (np.zeros((3, 2), np.float32), [2]),
        (np.zeros((3, 2), np.float32), [0, 22]),
        (np.zeros((3, 2), np.float32), [True, 22]),
        (np.zeros((3, 2), np.float32), [2.0, 22]),
        (np.zeros((3, 2), np.float32), [2, 65536]),
        (np.array([[np.nan]], np.float32), [2]),
        (np.array([[np.inf]], np.float32), [2]),
        (np.array([[-0.0]], np.float32), [2]),
        (np.array([[-0.5]], np.float32), [2]),
        (np.array([[1.5]], np.float32), [2]),
    ],
)
def test_malformed_count_or_population_family_fails_closed(a, p):
    with pytest.raises(ValueError):
        m.decode_pool(a, p)


def arguments(steps=12):
    return dict(
        untaught=np.zeros((steps, 2), np.float32),
        taught=np.zeros((steps, 2), np.float32),
        populations=[2, 22],
        first_pulse_step=4,
        kc_total_untaught=np.arange(steps, dtype=np.float32),
        kc_total_taught=np.arange(steps, dtype=np.float32),
        kc_used_untaught=np.ones((steps, 3, 2)),
        kc_used_taught=np.ones((steps, 3, 2)),
        rule_untaught=np.full((steps, 3, 8), 0.25),
        rule_taught=np.full((steps, 3, 8), 0.25),
    )


@pytest.mark.parametrize("j", [4, 5, 8, 11])
@pytest.mark.parametrize("channel", [0, 1])
def test_first_actual_difference_in_either_channel_is_inclusive_kc_boundary(j, channel):
    kw = arguments()
    kw["taught"][j, channel] = f32_fraction(1, [2, 22][channel])
    kw["rule_taught"][j:] += 1
    kw["kc_total_taught"][j + 1 :] += 1
    kw["kc_used_taught"][j + 1 :] += 1
    before = {k: v.copy() for k, v in kw.items() if isinstance(v, np.ndarray)}
    out = m.prefix_contrast(**kw)
    assert out["first_pool_difference_step"] == j
    assert out["kc_equal_through_step"] == j
    assert out["first_rule_difference_step"] == j
    assert out["first_kc_total_difference_step"] == (j + 1 if j + 1 < 12 else None)
    assert out["first_pool_count_difference"] == [int(channel == 0), int(channel == 1)]
    for key, original in before.items():
        np.testing.assert_array_equal(kw[key], original)


def test_rule_and_kc_can_diverge_only_later_or_never_after_changed_dan():
    kw = arguments()
    kw["taught"][6, 0] = 0.5
    out = m.prefix_contrast(**kw)
    assert out["first_rule_difference_step"] is None
    assert out["first_kc_total_difference_step"] is None
    assert out["first_kc_used_difference_step"] is None


@pytest.mark.parametrize("bad", ["kc_total_taught", "kc_used_taught", "rule_taught"])
@pytest.mark.parametrize("j", [4, 8])
def test_prefix_violation_fails_even_if_later_waveforms_look_valid(bad, j):
    kw = arguments()
    kw["taught"][j, 1] = f32_fraction(1, 22)
    # KC equality includes j; rule equality stops before j.
    kw[bad][j if bad != "rule_taught" else j - 1] += 1
    with pytest.raises(ValueError, match="prefix"):
        m.prefix_contrast(**kw)


@pytest.mark.parametrize("j", [0, 1, 3])
def test_actual_difference_before_first_scheduled_pulse_rejects_mismatched_inputs(j):
    kw = arguments()
    kw["taught"][j, 0] = 0.5
    with pytest.raises(ValueError, match="scheduled"):
        m.prefix_contrast(**kw)


def test_pooled_collision_preserves_current_bridge_prefix_not_per_cell_identity():
    kw = arguments()
    out = m.prefix_contrast(**kw)
    assert out["first_pool_difference_step"] is None
    assert out["kc_equal_through_step"] == 11
    assert out["per_cell_taught_history_established"] is False
    # Distinct cell histories can generate identical totals at every step.
    left = np.array([[1, 0], [0, 1]], np.int32)
    right = left[:, ::-1]
    assert not np.array_equal(left, right)
    np.testing.assert_array_equal(m.fine_pool(left, [0, 0], [2]), m.fine_pool(right, [0, 0], [2]))


@pytest.mark.parametrize("bad", ["kc_total_taught", "kc_used_taught", "rule_taught"])
def test_identical_pools_require_entire_current_bridge_and_kc_observations_equal(bad):
    kw = arguments()
    kw[bad][-1] += 1
    with pytest.raises(ValueError, match="prefix"):
        m.prefix_contrast(**kw)


@pytest.mark.parametrize("bad", ["untaught", "taught", "kc_total_taught", "kc_used_taught", "rule_taught"])
def test_shape_mismatch_cannot_broadcast_or_hide_unknown_steps(bad):
    kw = arguments()
    kw[bad] = kw[bad][:-1]
    with pytest.raises(ValueError):
        m.prefix_contrast(**kw)


@pytest.mark.parametrize(
    "bad",
    [
        "kc_total_untaught",
        "kc_total_taught",
        "kc_used_untaught",
        "kc_used_taught",
        "rule_untaught",
        "rule_taught",
    ],
)
def test_nonfinite_anywhere_is_invalid_even_outside_proven_prefix(bad):
    kw = arguments()
    kw["taught"][4, 0] = 0.5
    kw[bad][-1] = np.nan
    with pytest.raises(ValueError):
        m.prefix_contrast(**kw)


@pytest.mark.parametrize("pulse", [-1, 12, True, 4.0])
def test_invalid_pulse_boundary_is_not_silently_coerced(pulse):
    kw = arguments()
    kw["first_pulse_step"] = pulse
    with pytest.raises(ValueError):
        m.prefix_contrast(**kw)


def test_fine_pool_uses_explicit_compartment_map_with_permutation_invariance():
    events = np.array([[1, 0, 1, 1, 0], [0, 1, 1, 0, 1]], np.int32)
    comp = np.array([1, 0, 1, 0, 1])
    expected = np.array([[1, 2], [1, 2]], np.int64)
    np.testing.assert_array_equal(m.fine_pool(events, comp, [2, 3]), expected)
    order = [4, 2, 0, 3, 1]
    np.testing.assert_array_equal(m.fine_pool(events[:, order], comp[order], [2, 3]), expected)


@pytest.mark.parametrize(
    "events,comp,pops",
    [
        (np.array([[2, 0]]), [0, 0], [2]),
        (np.array([[-1, 1]]), [0, 0], [2]),
        (np.array([[1.0, 0.0]]), [0, 0], [2]),
        (np.zeros((2, 2), int), [0, 0], [1]),
        (np.zeros((2, 2), int), [0, 1], [2]),
        (np.zeros((2, 2), int), [0.0, 0.0], [2]),
        (np.zeros((2, 2), int), [False, False], [2]),
        (np.zeros((2, 2), int), [0], [2]),
    ],
)
def test_fine_pool_malformed_events_or_mapping_are_not_silently_assigned(events, comp, pops):
    with pytest.raises(ValueError):
        m.fine_pool(events, comp, pops)


def synthetic_identity():
    protocol = {"learning_rule": "rate-bridge-v1", "seed": 42}
    summaries, fine = {}, []
    for panel in ("original", "second"):
        games = [1, 2] if panel == "original" else [3, 4]
        rows = [
            dict(game=g, seed_set=s, condition=c, seed=g + (100 if s == "alt" else 0))
            for g in games
            for s in ("base", "alt")
            for c in ("frozen", "untaught", "home", "away")
        ]
        import copy

        summaries[panel] = dict(
            run_id=panel,
            panel_games=games,
            rows=rows,
            identity=dict(protocol=protocol.copy(), selection=dict(expected_panel=copy.deepcopy(rows))),
        )
        fine.extend(
            dict(game=r["game"], seed_set=r["seed_set"], seed=r["seed"], run_id=panel)
            for r in rows
            if r["condition"] == "untaught"
        )
    return fine, summaries, protocol


def test_complete_pairing_uses_run_game_noise_seed_and_active_condition():
    rows, summaries, protocol = synthetic_identity()
    assert m.matched_rows(rows, summaries, protocol) == rows


@pytest.mark.parametrize(
    "bad",
    [
        "missing_row",
        "duplicate_row",
        "wrong_seed",
        "unknown_condition",
        "missing_seed",
        "missing_fine",
        "reordered_fine",
        "wrong_run",
        "wrong_protocol",
        "missing_declared",
        "duplicate_game",
        "empty_panel",
        "seed_bool",
        "different_matched_seed",
    ],
)
def test_pair_matrix_identity_failures_stop_before_any_waveform_statistics(bad):
    rows, summaries, protocol = synthetic_identity()
    s = summaries["original"]
    if bad == "missing_row":
        s["rows"].pop()
    elif bad == "duplicate_row":
        s["rows"].append(s["rows"][0].copy())
    elif bad == "wrong_seed":
        s["rows"][0]["seed"] += 1
    elif bad == "unknown_condition":
        s["rows"][0]["condition"] = "unknown"
    elif bad == "missing_seed":
        del s["rows"][0]["seed"]
    elif bad == "missing_fine":
        rows.pop()
    elif bad == "reordered_fine":
        rows.reverse()
    elif bad == "wrong_run":
        s["run_id"] = "wrong"
    elif bad == "wrong_protocol":
        s["identity"]["protocol"]["seed"] = 43
    elif bad == "missing_declared":
        s["identity"]["selection"]["expected_panel"].pop()
    elif bad == "duplicate_game":
        s["panel_games"].append(1)
    elif bad == "empty_panel":
        s["panel_games"] = []
    elif bad == "seed_bool":
        s["rows"][0]["seed"] = True
    elif bad == "different_matched_seed":
        s["rows"][0]["seed"] += 2
        s["identity"]["selection"]["expected_panel"][0]["seed"] += 2
    with pytest.raises(ValueError):
        m.matched_rows(rows, summaries, protocol)


@pytest.mark.parametrize(
    "key,value", [("game", True), ("seed", True), ("game", 1.0), ("seed", 1.0), ("run_id", None)]
)
def test_fine_identity_requires_types_not_python_loose_numeric_equality(key, value):
    rows, summaries, protocol = synthetic_identity()
    rows[0][key] = value
    with pytest.raises(ValueError):
        m.matched_rows(rows, summaries, protocol)


@pytest.mark.parametrize("value", [True, 1.0, -1, None, "1"])
def test_panel_game_identity_rejects_boolean_float_negative_and_noninteger_aliases(value):
    rows, summaries, protocol = synthetic_identity()
    summaries["original"]["panel_games"][0] = value
    with pytest.raises(ValueError):
        m.matched_rows(rows, summaries, protocol)
