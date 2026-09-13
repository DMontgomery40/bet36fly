"""Independent synthetic mathematics review; never reads saved histories."""

from fractions import Fraction
import itertools

import mpmath as mp
import numpy as np
import pytest

import ppl101_signal_basis as basis


@pytest.mark.parametrize("lag", [-4000, -500, -100, -1, -0.2, -1e-8, 0, 1e-8, 0.2, 1, 100, 500, 4000])
def test_seventy_digit_improper_continuous_products(lag):
    with mp.workdps(70):
        ell = mp.mpf(str(lag))
        tk, td = (mp.mpf(0), ell) if ell >= 0 else (-ell, mp.mpf(0))
        start = max(tk, td)

        def rate(age):
            return mp.exp(-age / 100) / 100

        def eligibility(age):
            return mp.mpf(5) / 4 * (mp.exp(-age / 500) - mp.exp(-age / 100))

        scale = mp.mpf("0.00048")
        positive = mp.quad(
            lambda u: scale * eligibility(start + u - td) * rate(start + u - tk), [0, 100, 500, mp.inf]
        )
        negative = -mp.quad(
            lambda u: scale * eligibility(start + u - tk) * rate(start + u - td), [0, 100, 500, mp.inf]
        )
        expected = np.array([float(positive), float(negative), float(positive + negative)])
    np.testing.assert_allclose(basis.pair_areas(lag), expected, atol=2e-18, rtol=2e-13)


def exact_sd_squared(values):
    n = len(values)
    return sum((values[i] - values[j]) ** 2 for i in range(n) for j in range(i)) / (n * (n - 1))


@pytest.mark.parametrize("seed", [3, 9, 17])
def test_all_box_vertices_against_exact_rational_pairwise_variance(seed):
    rng = np.random.default_rng(seed)
    u = rng.integers(-128, 128, (8, 3, 2)).astype(float) / 4096
    result = basis.relaxed_guard_envelope(u)
    lows = [Fraction.from_float(x) for x in result["trial_low"]]
    highs = [Fraction.from_float(x) for x in result["trial_high"]]
    mean_lo, mean_hi = sum(lows) / 8, sum(highs) / 8
    exact_min_abs = Fraction(0) if mean_lo <= 0 <= mean_hi else min(abs(mean_lo), abs(mean_hi))
    variance_max = max(
        exact_sd_squared([highs[i] if bits[i] else lows[i] for i in range(8)])
        for bits in itertools.product((0, 1), repeat=8)
    )
    with mp.workdps(70):
        exact_sd = mp.sqrt(mp.mpf(variance_max.numerator) / variance_max.denominator)
        assert mp.mpf(result["maximum_sample_sd_upper"]) >= exact_sd
        assert (
            mp.mpf(result["minimum_absolute_mean_lower"])
            <= mp.mpf(exact_min_abs.numerator) / exact_min_abs.denominator
        )
    assert result["guard_limit_upper"] == 0.5 * result["maximum_sample_sd_upper"]


@pytest.mark.parametrize("dtype", [np.float16, np.float32, np.float64])
def test_storage_precision_does_not_change_internal_envelope_arithmetic(dtype):
    u = np.arange(8 * 23 * 2).reshape(8, 23, 2).astype(dtype) / dtype(2048)
    assert basis.relaxed_guard_envelope(u) == basis.relaxed_guard_envelope(u.astype(np.float64))


@pytest.mark.parametrize("direction", [-1, 1])
def test_prefix_margin_rejects_real_published_bound_contacts_without_mathematical_clipping(direction):
    area = 0.5 - 2**-27
    exact_gain = 1 + direction * area
    assert 0.5 < exact_gain < 1.5
    assert float(np.float32(exact_gain)) in (0.5, 1.5)
    assert not basis.prefix_linear_applicability(area)


def test_float32_rounding_bound_across_the_entire_admissible_gain_range():
    points = np.concatenate(
        (np.linspace(0.5, 1.5, 1001), 0.5 + np.arange(32) * 2**-28, 1.5 - np.arange(32) * 2**-28)
    )
    assert np.max(np.abs(points.astype(np.float32).astype(float) - points)) <= 2**-24


def test_accumulator_error_term_matches_exact_rational_upper_bound():
    n, unit = 1501, Fraction(1, 2**53)
    exact = n * unit / (1 - n * unit) * Fraction(3, 2)
    assert abs(Fraction.from_float(basis.DOUBLE_ACCUMULATION_ALLOWANCE) - exact) < Fraction(1, 10**27)
