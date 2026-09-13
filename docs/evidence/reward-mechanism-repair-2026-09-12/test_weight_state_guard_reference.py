"""Exact arithmetic and synthetic-only guard tests; no saved histories.

Mutations caught: incorrect mean/SD algebra, float/int overflow, ddof mismatch,
ties-to-even or double-rounding mistakes, inward allowance rounding, and false
universal verdicts for a numerical enclosure.
"""

from fractions import Fraction
import itertools

import numpy as np
import pytest

import weight_state_guard_reference as guard


def independent_variance(values):
    n = len(values)
    return sum((Fraction(values[i]) - Fraction(values[j])) ** 2 for i in range(n) for j in range(i)) / (
        n * (n - 1)
    )


def test_one_nonzero_trial_passes_and_rejects_the_original_wrong_algebra():
    values = (1, 0, 0, 0, 0, 0, 0, 0)
    assert guard.point_guard(values)
    assert not 29 * sum(values) ** 2 <= 8 * sum(v * v for v in values)


def test_all_three_level_eight_trial_vectors_against_direct_mean_and_pairwise_sd():
    for values in itertools.product((-1, 0, 1), repeat=8):
        mean = Fraction(sum(values), 8)
        expected = 4 * mean**2 <= independent_variance(values)
        assert guard.point_guard(values) == expected


@pytest.mark.parametrize("scale", [1, -1, 2**70, -(2**91)])
@pytest.mark.parametrize("last,expected", [(0, True), (1, False), (-1, True)])
def test_exact_equality_and_one_tick_neighbors_with_arbitrary_size_integers(scale, last, expected):
    values = [5, 3, 1, -1, 0, 0, 0, last]
    assert guard.point_guard([scale * x for x in values]) == expected


@pytest.mark.parametrize(
    "lower,upper,expected",
    [
        ([-6] * 4 + [4] * 4, [-4] * 4 + [6] * 4, "all_pass"),
        ([10] * 8, [11] * 8, "all_fail"),
        ([0] * 8, [0] * 8, "all_pass"),
        ([5, 3, 1, -1, 0, 0, 0, 0], [5, 3, 1, -1, 0, 0, 0, 1], "inconclusive"),
    ],
)
def test_proven_pass_fail_zero_and_mixed_boundary_boxes(lower, upper, expected):
    assert guard.classify_box(lower, upper)["classification"] == expected


@pytest.mark.parametrize("seed", range(16))
def test_box_verdict_is_sound_for_every_integer_point_in_small_boxes(seed):
    rng = np.random.default_rng(seed)
    lower = rng.integers(-4, 5, 8).tolist()
    upper = (np.array(lower) + rng.integers(0, 2, 8)).tolist()
    result = guard.classify_box(lower, upper)
    verdicts = [
        guard.point_guard(x) for x in itertools.product(*[range(a, b + 1) for a, b in zip(lower, upper)])
    ]
    if result["classification"] == "all_pass":
        assert all(verdicts)
    if result["classification"] == "all_fail":
        assert not any(verdicts)
    actual_min = min(
        independent_variance(x) for x in itertools.product(*[range(a, b + 1) for a, b in zip(lower, upper)])
    )
    assert result["minimum_variance"] <= actual_min


@pytest.mark.parametrize("seed", range(24))
def test_exact_continuous_minimum_has_a_global_convex_kkt_certificate(seed):
    rng = np.random.default_rng(seed + 100)
    lower = rng.integers(-10, 11, 8).tolist()
    upper = (np.array(lower) + rng.integers(0, 8, 8)).tolist()
    result = guard.classify_box(lower, upper)
    witness = result["minimum_variance_witness"]
    mean = sum(witness) / 8
    assert all(Fraction(lo) <= x <= Fraction(h) for x, lo, h in zip(witness, lower, upper))
    assert independent_variance(witness) == result["minimum_variance"]
    for x, lo, h in zip(witness, lower, upper):
        if lo == h:
            continue
        if x == lo:
            assert x >= mean
        elif x == h:
            assert x <= mean
        else:
            assert x == mean
    vertices = itertools.product(*[(lo, h) for lo, h in zip(lower, upper)])
    assert result["maximum_variance"] == max(independent_variance(x) for x in vertices)


@pytest.mark.parametrize(
    "base",
    [
        0.5,
        float(np.nextafter(np.float32(0.5), np.float32(1))),
        0.75,
        float(np.nextafter(np.float32(1), np.float32(0))),
        1.0,
        float(np.nextafter(np.float32(1), np.float32(2))),
        1.25,
    ],
)
def test_exact_f32_midpoint_neighbors_and_even_tie_across_binade_boundary(base):
    left = np.float32(base)
    right = np.nextafter(left, np.float32(2))
    a, b = Fraction(float(left)), Fraction(float(right))
    midpoint = (a + b) / 2
    tiny = Fraction(1, 2**100)
    left_ticks = int(a * 2**24)
    right_ticks = int(b * 2**24)
    assert guard.round_f32_ticks(midpoint - tiny) == left_ticks
    assert guard.round_f32_ticks(midpoint + tiny) == right_ticks
    tie = left_ticks if left.view(np.uint32) % 2 == 0 else right_ticks
    assert guard.round_f32_ticks(midpoint) == tie


@pytest.mark.parametrize("base", [0.5, 0.75, 1.0, 1.25])
def test_allowance_is_not_lost_when_endpoint_arithmetic_is_below_double_resolution(base):
    left = np.float32(base)
    right = np.nextafter(left, np.float32(2))
    midpoint = (float(left) + float(right)) / 2
    centers = np.full((8, 1), midpoint, np.float64)
    lower, upper = guard.allowance_totals(centers, 2.0**-100)
    assert lower == (int(Fraction(float(left)) * 2**24) - 2**24,) * 8
    assert upper == (int(Fraction(float(right)) * 2**24) - 2**24,) * 8
    single_low, single_high = guard.allowance_totals(centers, 0.0)
    assert single_low == single_high


def test_f32_totals_match_fraction_sums_with_large_cancellation():
    rng = np.random.default_rng(818)
    values = rng.uniform(0.5, 1.5, (8, 4184)).astype(np.float32)
    got = guard.f32_trial_totals(values)
    expected = tuple(sum(int((Fraction(float(v)) - 1) * 2**24) for v in row) for row in values)
    assert got == expected
    lo, hi = guard.allowance_totals(values.astype(float), 0.0)
    assert lo == hi == got


@pytest.mark.parametrize(
    "center,error,expected",
    [(0.5, 1e-11, 0.5), (1.5, 1e-11, 1.5), (0.5 - 1e-12, 1e-11, 0.5), (1.5 + 1e-12, 1e-11, 1.5)],
)
def test_continuous_bound_intersection_preserves_permitted_published_values(center, error, expected):
    lo, hi = guard.allowance_totals(np.full((8, 1), center), error)
    assert lo == hi == (int((Fraction(expected) - 1) * 2**24),) * 8


@pytest.mark.parametrize(
    "values", [[0] * 7, [0] * 9, [0] * 7 + [True], [0] * 7 + [1.0], [0] * 7 + [np.int64(1)]]
)
def test_point_guard_requires_exact_python_integer_eight_trial_contract(values):
    with pytest.raises(ValueError):
        guard.point_guard(values)


@pytest.mark.parametrize("kind", ["shape", "dtype", "nan", "out_of_bounds", "empty"])
def test_invalid_published_gain_family_rejected(kind):
    values = np.ones((8, 2), np.float32)
    if kind == "shape":
        values = values[:7]
    if kind == "dtype":
        values = values.astype(float)
    if kind == "nan":
        values[0, 0] = np.nan
    if kind == "out_of_bounds":
        values[0, 0] = 1.6
    if kind == "empty":
        values = values[:, :0]
    with pytest.raises(ValueError):
        guard.f32_trial_totals(values)


@pytest.mark.parametrize(
    "kind", ["negative_error", "nan_error", "wrong_shape", "no_bound_overlap", "bad_initial"]
)
def test_invalid_numerical_enclosures_rejected(kind):
    centers = np.ones((8, 2))
    error = 1e-11
    initial = 1.0
    if kind == "negative_error":
        error = -1.0
    if kind == "nan_error":
        error = np.nan
    if kind == "wrong_shape":
        error = np.ones((3,))
    if kind == "no_bound_overlap":
        centers[0, 0] = 2.0
    if kind == "bad_initial":
        initial = 1.0 + 1e-12
    with pytest.raises(ValueError):
        guard.allowance_totals(centers, error, initial=initial)


def test_reversed_trial_interval_is_invalid():
    with pytest.raises(ValueError):
        guard.classify_box([1] * 8, [0] * 8)


def test_integer_allowance_does_not_round_away_a_valid_intersection():
    # The exact lower endpoint is 1. Converting the odd integer radius to a
    # double first changes it to 2 and would falsely reject the whole interval.
    center = float(2**53 + 2)
    radius = np.uint64(2**53 + 1)
    lo, hi = guard.allowance_totals(np.full((8, 1), center), radius)
    assert lo == (0,) * 8
    assert hi == (2**23,) * 8
