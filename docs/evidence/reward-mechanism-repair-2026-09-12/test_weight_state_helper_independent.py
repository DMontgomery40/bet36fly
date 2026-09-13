"""Independent scalar/vector comparisons of the separate efficient helper.

Synthetic states only. The full-tail oracle uses exp(-elapsed/100), a
different coordinate from the helper and frozen event reference.
"""

import math

import numpy as np
import pytest

import weight_dependent_shadow as helper
from weight_state_reference import integrate_products


STATES = [
    (0.0, 0.0, 0.0, 0.0),
    (0.01, 0.2, 0.0, 0.5),
    (0.0, 0.5, 0.02, 0.1),
    (0.02, 0.2, 0.03, 0.8),
    (0.2, 2.0, 0.4, 4.0),
]


def independent_interval(states, initial, duration):
    rk, ek, rd, ed = states
    if math.isinf(duration):

        def products(z):
            v = 1 - z
            if v == 0:
                return 0.0, 0.0
            slow = v**0.2
            # t=-100 log(v): Jacobian is100/v, already cancelled below.
            return (
                96 * rk * (ed * slow + 125 * rd * (slow - v)),
                96 * rd * (ek * slow + 125 * rk * (slow - v)),
            )

        return integrate_products(products, (0.0, 1.0), initial)

    def products(t):
        fast = math.exp(-t / 100)
        slow = math.exp(-t / 500)
        kr, dr = rk * fast, rd * fast
        ke = ek * slow + 125 * rk * (slow - fast)
        de = ed * slow + 125 * rd * (slow - fast)
        return 0.96 * de * kr, 0.96 * ke * dr

    return integrate_products(products, (0.0, duration), initial)


@pytest.mark.parametrize("states", STATES)
@pytest.mark.parametrize("initial", [0.5, 0.7, 1.0, 1.3, 1.5])
@pytest.mark.parametrize("duration", [0.0, 0.2, 3.0, math.inf])
def test_all_interval_products_and_gain_match_independent_continuous_oracle(states, initial, duration):
    actual = helper.interval(*states, initial, duration)
    expected = independent_interval(states, initial, duration)
    for key in ("gain", "positive", "negative"):
        assert abs(float(actual[key]) - expected[key]) <= (1e-11 if key == "gain" else 2e-11)
    if math.isinf(duration):
        assert all(float(x) == 0 for x in actual["state"])
    else:
        rk, ek, rd, ed = states
        fast = math.exp(-duration / 100)
        slow = math.exp(-duration / 500)
        expected_states = (
            rk * fast,
            ek * slow + 125 * rk * (slow - fast),
            rd * fast,
            ed * slow + 125 * rd * (slow - fast),
        )
        np.testing.assert_allclose(actual["state"], expected_states, atol=2e-14, rtol=0)


@pytest.mark.parametrize("initial", [0.5, 0.7, 1.0, 1.3, 1.5])
@pytest.mark.parametrize("positive", [True, False])
def test_pure_branch_infinite_tail_has_exact_exposure_solution(initial, positive):
    states = (0.02, 0.1, 0.0, 0.7) if positive else (0.0, 0.7, 0.02, 0.1)
    actual = helper.interval(*states, initial, math.inf)
    exposure = 0.96 * 0.02 * 0.7 / 0.012
    bound = 1.5 if positive else 0.5
    expected = bound + (initial - bound) * math.exp(-0.001 * exposure)
    assert abs(float(actual["gain"]) - expected) <= 1e-11
    assert abs(float(actual["positive"] + actual["negative"]) - (expected - initial)) <= 2e-11


@pytest.mark.parametrize("duration", [0.2, math.inf])
def test_vector_broadcast_and_permutation_match_independent_scalar_oracles(duration):
    states = np.array(STATES).T
    initial = np.array([0.5, 0.7, 1.0, 1.3, 1.5])
    actual = helper.interval(*states, initial, duration)
    expected = [independent_interval(s, g, duration) for s, g in zip(STATES, initial)]
    for key in ("gain", "positive", "negative"):
        np.testing.assert_allclose(actual[key], [x[key] for x in expected], atol=2e-11, rtol=0)
    order = np.array([4, 1, 3, 0, 2])
    permuted = helper.interval(*states[:, order], initial[order], duration)
    for key in ("gain", "positive", "negative"):
        np.testing.assert_array_equal(actual[key][order], permuted[key])
