"""Synthetic algebra only; no captured histories, candidate or circuit execution.

The bridge checks compare an independently derived pair kernel against direct
quadrature of its four impulse signals. Gradient identities use exact fractions.
Neither the toy error topology nor a local cellular mechanism is instantiated.
"""

from fractions import Fraction as F
import math

import numpy as np
import pytest
from scipy.integrate import quad

ETA = 0.0005
TR, TE, NORM = 100.0, 500.0, 0.96
QUAD_ATOL = 1e-13


def pair_kernel(lag):
    if lag == 0:
        return 0.0
    return -ETA * math.copysign(1.0, lag) * (math.exp(-abs(lag) / TE) - math.exp(-abs(lag) / TR))


def impulse(age):
    if age < 0:
        return 0.0, 0.0
    return math.exp(-age / TR) / TR, TE / (TE - TR) * math.exp(-age / TE) * (
        -math.expm1(-age * (1 / TR - 1 / TE))
    )


def pair_integrand(t, lag):
    k, d = max(-lag, 0.0), max(lag, 0.0)
    rk, ek = impulse(t - k)
    rd, ed = impulse(t - d)
    return ETA * NORM * (ed * rk - ek * rd)


@pytest.mark.parametrize("lag", [-1000.0, -250.0, -50.0, -0.2, 0.0, 0.2, 50.0, 250.0, 1000.0])
def test_pair_kernel_against_independent_signal_quadrature(lag):
    value, error = quad(lambda t: pair_integrand(t, lag), abs(lag), np.inf, epsabs=1e-15, epsrel=1e-12)
    assert error < QUAD_ATOL
    assert abs(value - pair_kernel(lag)) < QUAD_ATOL


@pytest.mark.parametrize("lag", [0.2, 10.0, 100.0, 300.0])
@pytest.mark.parametrize("tail_start", [400.0, 800.0])
def test_full_tail_completes_cutpoint_independent_pair_area(lag, tail_start):
    left, _ = quad(lambda t: pair_integrand(t, lag), lag, tail_start, epsabs=1e-15)
    rk, ek = impulse(tail_start)
    rd, ed = impulse(tail_start - lag)
    tail = ETA * NORM * (ed * rk - ek * rd) / (1 / TR + 1 / TE)
    assert abs(left + tail - pair_kernel(lag)) < QUAD_ATOL


@pytest.mark.parametrize("scale", [0.1, 1.0, 3.0])
def test_proportional_finite_train_has_exact_pair_antisymmetry(scale):
    times = [0.0, 0.2, 17.0, 290.0]
    total = sum(scale * pair_kernel(d - k) for k in times for d in times)
    assert abs(total) < 1e-18


def test_equal_mean_counts_do_not_imply_zero_null_drift():
    # One endogenous delayed pair, equal event totals: a counterexample to
    # neutrality from equal mean counts, without assigning physiological cause.
    assert pair_kernel(10.0) < 0
    assert pair_kernel(-10.0) == -pair_kernel(10.0)


def test_reset_omits_cross_call_pairs_instead_of_completing_them():
    separated_calls = 0.0  # KC alone, then DAN alone: neither call has a pair.
    concatenated = pair_kernel(10.0)
    assert separated_calls != concatenated
    assert abs(pair_kernel(15000.0)) < 1e-16


def test_population_mean_is_linear_for_fixed_unclipped_histories():
    k = [0.0, 5.0, 18.0]
    dan1 = [3.0, 7.0]
    dan2 = [2.0, 20.0]
    first = sum(pair_kernel(d - t) for t in k for d in dan1)
    second = sum(pair_kernel(d - t) for t in k for d in dan2)
    pooled = sum(0.5 * pair_kernel(d - t) for t in k for d in dan1 + dan2)
    assert abs(pooled - (first + second) / 2) < 1e-18


@pytest.mark.parametrize(
    "values", [(1, 0, 0, 0, 0, 0, 0, 0), (5, 3, 1, -1, 0, 0, 0, 0), (-3, -2, -1, 0, 1, 2, 3, 4)]
)
@pytest.mark.parametrize("scale", [2, 7, 100])
def test_positive_rescaling_cannot_change_exact_eight_trial_guard(values, scale):
    def margins(v):
        return 16 * sum(x * x for x in v) - 9 * sum(v) ** 2

    assert margins(tuple(scale * x for x in values)) == scale**2 * margins(values)


@pytest.mark.parametrize("gain", [F(1, 2), F(3, 4), F(1), F(5, 4), F(3, 2)])
@pytest.mark.parametrize("p,n", [(F(0), F(0)), (F(2), F(0)), (F(0), F(3)), (F(2), F(2)), (F(2), F(3))])
def test_weight_state_law_is_damped_antisymmetric_drive(gain, p, n):
    x = gain - 1
    headroom = 2 * p * (F(3, 2) - gain) - 2 * n * (gain - F(1, 2))
    decomposed = (p - n) - 2 * (p + n) * x
    assert headroom == decomposed
    if p == n:
        assert headroom == -4 * p * x


@pytest.mark.parametrize("error", [F(-3), F(-1, 2), F(0), F(1, 2), F(3)])
@pytest.mark.parametrize("kc", [(F(1),), (F(1), F(2)), (F(0), F(3), F(1, 4))])
def test_opponent_gradient_topology_has_error_fixed_point_and_descent(error, kc):
    # Abstract source-motivated linear prediction m=(wplus-wminus).k.
    # Unit eta here means dividing both sides by eta; no parameter is selected.
    plus = [error * k for k in kc]
    minus = [-error * k for k in kc]
    prediction_derivative = sum((a - b) * k for a, b, k in zip(plus, minus, kc))
    error_derivative = -prediction_derivative
    loss_derivative = error * error_derivative
    assert loss_derivative == -2 * error**2 * sum(k * k for k in kc)
    assert loss_derivative <= 0
    if error == 0:
        assert all(v == 0 for v in plus + minus)


@pytest.mark.parametrize("background", [F(0), F(1), F(4)])
@pytest.mark.parametrize("error", [F(-3), F(-1, 2), F(0), F(1, 2), F(3)])
def test_opponent_decoding_rectification_limit_is_explicit(background, error):
    positive = max(F(0), background + error)
    negative = max(F(0), background - error)
    decoded = (positive - negative) / 2
    assert decoded * error >= 0
    if background >= abs(error):
        assert decoded == error
    if error == 0:
        assert decoded == 0
    if background < abs(error):
        assert decoded != error
