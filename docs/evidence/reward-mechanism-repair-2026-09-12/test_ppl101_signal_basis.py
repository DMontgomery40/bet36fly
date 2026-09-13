"""Independent continuous-product and event-matrix checks, before saved data."""

import math
import numpy as np
import pytest
from scipy.integrate import quad

from ppl101_signal_basis import (
    pair_areas,
    signal_basis,
    relaxed_guard_envelope,
    prefix_linear_applicability,
    PREFIX_MARGIN,
)


@pytest.mark.parametrize("area", [0.0, 0.1, 0.49, 0.5 - 2 * PREFIX_MARGIN])
def test_prefix_guard_accepts_safe_interior(area):
    assert prefix_linear_applicability(area)


@pytest.mark.parametrize("area", [0.5 - PREFIX_MARGIN, 0.5, 0.6, 1.0])
def test_prefix_guard_rejects_contact_and_exterior(area):
    assert not prefix_linear_applicability(area)


@pytest.mark.parametrize("area", [-1.0, np.nan, np.inf, -np.inf])
def test_prefix_guard_rejects_invalid_areas(area):
    with pytest.raises(ValueError):
        prefix_linear_applicability(area)


def direct_product(lag, positive):
    tk, td = (0.0, lag) if lag >= 0 else (-lag, 0.0)

    def r(age):
        return math.exp(-age / 100) / 100

    def e(age):
        return 500 / 400 * (math.exp(-age / 500) - math.exp(-age / 100))

    def product(t):
        return 0.00048 * (e(t - td) * r(t - tk) if positive else -e(t - tk) * r(t - td))

    return quad(product, max(tk, td), np.inf, epsabs=1e-14, epsrel=1e-11)[0]


@pytest.mark.parametrize("lag", [-4000, -1000, -500, -100, -20, -0.2, 0, 0.2, 20, 100, 500, 1000, 4000])
def test_products_match_independent_improper_quadrature(lag):
    p, n, total = pair_areas(lag)
    assert p >= 0 and n <= 0
    np.testing.assert_allclose(
        [p, n], [direct_product(lag, True), direct_product(lag, False)], atol=1e-13, rtol=1e-10
    )
    assert math.isclose(p + n, total, abs_tol=1e-16)
    assert math.isclose(total, -pair_areas(-lag)[2], abs_tol=1e-16)


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("onset", [0, 4, 17, 40])
def test_dense_basis_matches_explicit_event_pairs_and_permutations(seed, onset):
    rng = np.random.default_rng(seed)
    kc = (rng.random((40, 5)) < 0.2).astype(np.uint8)
    dan = (rng.random((40, 2)) < 0.15).astype(np.uint8)
    actual = signal_basis(kc, dan, onset)
    expected = np.zeros_like(actual)
    for j in range(5):
        for d in range(2):
            for k in np.flatnonzero(kc[onset:, j]) + onset:
                for t in np.flatnonzero(dan[onset:, d]) + onset:
                    # Direct quadrature is independent of pair_areas and matrix reduction.
                    lag = (int(t) - int(k)) * 0.2
                    pos, neg = direct_product(lag, True), direct_product(lag, False)
                    expected[j, d] += [pos, neg, pos + neg]
    np.testing.assert_allclose(actual, expected, atol=2e-12, rtol=1e-10)
    np.testing.assert_allclose(signal_basis(kc[:, ::-1], dan[:, ::-1], onset), actual[::-1, ::-1], atol=2e-16)


@pytest.mark.parametrize("seed", range(12))
def test_relaxed_envelope_contains_fixed_and_trial_varying_convex_maps(seed):
    rng = np.random.default_rng(seed)
    u = rng.normal(0, 0.002, (8, 19, 2))
    bounds = relaxed_guard_envelope(u)
    for shape in ((1, 19), (8, 19)):
        for _ in range(20):
            a = rng.random(shape)
            values = (u[:, :, 0] * a + u[:, :, 1] * (1 - a)).sum(1)
            assert np.all(values >= bounds["trial_low"]) and np.all(values <= bounds["trial_high"])
            assert np.std(values, ddof=1) <= bounds["maximum_sample_sd"]
            if bounds["all_convex_mappings_excluded"]:
                assert abs(values.mean()) > 0.5 * np.std(values, ddof=1)


def test_identical_negative_signals_are_excluded_but_mixed_signs_are_not_proven_feasible():
    assert relaxed_guard_envelope(np.full((8, 7, 2), -0.01))["all_convex_mappings_excluded"]
    mixed = np.ones((8, 7, 2)) * 0.01
    mixed[:, :, 1] *= -1
    assert not relaxed_guard_envelope(mixed)["all_convex_mappings_excluded"]


@pytest.mark.parametrize("dtype", [np.float16, np.float32, np.float64])
def test_reduction_precision_is_independent_of_input_storage(dtype):
    value = np.full((8, 200, 2), 0.000125, dtype=dtype)
    expected = relaxed_guard_envelope(value.astype(np.float64))
    assert relaxed_guard_envelope(value) == expected


@pytest.mark.parametrize("damage", ["float", "negative", "two", "shape", "zero", "onset"])
def test_bad_event_family_rejected(damage):
    a = np.zeros((5, 2), np.int32)
    b = a.copy()
    onset = 0
    if damage == "float":
        a = a.astype(float)
    if damage == "negative":
        a[0, 0] = -1
    if damage == "two":
        b[1, 1] = 2
    if damage == "shape":
        b = b[:4]
    if damage == "zero":
        a = a[:, :0]
    if damage == "onset":
        onset = True
    with pytest.raises(ValueError):
        signal_basis(a, b, onset)
