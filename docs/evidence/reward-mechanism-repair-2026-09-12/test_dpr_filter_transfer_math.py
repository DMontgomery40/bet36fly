"""Independent quadrature and analytic invariants, with no captured histories."""

import math

import numpy as np
import pytest
from scipy.integrate import quad

from dpr_filter_transfer_math import (
    backward_zero,
    delta_area_until,
    pair_area,
    pole_time_constant,
)


@pytest.mark.parametrize("step", [0.0002, 0.01, 0.015, 0.1])
@pytest.mark.parametrize("tau", [1.001, 100 / 3, 60, 104, 1e6])
def test_matched_pole_preserves_decay_across_multiple_steps(step, tau):
    physical_tau = pole_time_constant(step, tau)
    for n in (1, 2, 7, 100):
        assert math.exp(-n * step / physical_tau) == pytest.approx(
            (1 - 1 / tau) ** n, rel=2e-11, abs=2e-15
        )


@pytest.mark.parametrize("taus", [(0.5, 0.9, 1.56), (0.01, 0.002, 0.7),
                                 (2.0, 0.8, 0.4), (0.3, 0.5, 0.5)])
@pytest.mark.parametrize("lag", [-1.2, -0.4, -0.01, 0.0, 0.01, 0.4, 1.2])
def test_pair_area_agrees_with_direct_independent_improper_quadrature(taus, lag):
    k, s, ell = taus
    start = max(0, lag)

    def integrand(t):
        kc = math.exp(-t / k) / k
        short = math.exp(-(t - lag) / s) / s
        long = math.exp(-(t - lag) / ell) / ell
        return kc * (long - short)

    expected, error = quad(integrand, start, np.inf, epsabs=1e-12, epsrel=1e-12)
    assert error < 1e-10
    assert pair_area(lag, k, s, ell) == pytest.approx(expected, abs=1e-11, rel=1e-10)


@pytest.mark.parametrize("step", [0.01, 0.015])
def test_source_poles_do_not_give_backward_positive_linear_response_within_400ms(step):
    k, s, ell = [pole_time_constant(step, t) for t in (100 / 3, 60, 104)]
    zero = backward_zero(k, s, ell)
    assert zero > 0.4
    assert pair_area(-0.4, k, s, ell) < 0
    assert pair_area(0, k, s, ell) < 0
    assert pair_area(0.4, k, s, ell) < 0
    assert pair_area(-zero, k, s, ell) == pytest.approx(0, abs=1e-14)
    assert pair_area(-zero * 1.01, k, s, ell) > 0
    assert pair_area(-zero * 0.99, k, s, ell) < 0


@pytest.mark.parametrize("taus", [(0.6, 1.04), (0.9, 1.56), (0.2, 0.8)])
@pytest.mark.parametrize("t", [0, 0.1, 0.4, 1, 8])
def test_finite_delta_area_is_canceled_by_complete_tail(taus, t):
    s, ell = taus
    finite = delta_area_until(t, s, ell)
    tail, error = quad(lambda x: math.exp(-x / ell) / ell - math.exp(-x / s) / s,
                       t, np.inf, epsabs=1e-12, epsrel=1e-12)
    assert error < 1e-10
    assert finite + tail == pytest.approx(0, abs=1e-12)
    for initial_offset in (-0.4, 0, 0.8):
        for eta in (0.0005, 0.2, 1):
            intermediate = initial_offset * math.exp(eta * finite)
            assert intermediate * math.exp(eta * tail) == pytest.approx(
                initial_offset, abs=1e-12
            )


@pytest.mark.parametrize("bad", [0, -1, math.nan, math.inf, -math.inf])
def test_invalid_scale_family_rejected(bad):
    for fn, args in ((pole_time_constant, (bad, 60)),
                     (pole_time_constant, (0.015, bad)),
                     (pair_area, (0, bad, 1, 2)),
                     (pair_area, (0, 1, bad, 2)),
                     (pair_area, (0, 1, 2, bad)),
                     (backward_zero, (bad, 1, 2))):
        with pytest.raises(ValueError):
            fn(*args)


@pytest.mark.parametrize("args", [(0.015, 1), (0.015, 0.5)])
def test_zero_or_negative_discrete_pole_has_no_positive_exponential_embedding(args):
    with pytest.raises(ValueError):
        pole_time_constant(*args)


@pytest.mark.parametrize("short,long", [(1, 1), (2, 1)])
def test_backward_zero_requires_distinct_ordered_poles(short, long):
    with pytest.raises(ValueError):
        backward_zero(0.5, short, long)


@pytest.mark.parametrize("lag", [math.nan, math.inf, -math.inf])
def test_nonfinite_time_rejected(lag):
    with pytest.raises(ValueError):
        pair_area(lag, 0.5, 0.9, 1.56)
    with pytest.raises(ValueError):
        delta_area_until(lag, 0.9, 1.56)


def test_negative_integration_time_rejected():
    with pytest.raises(ValueError):
        delta_area_until(-0.01, 0.9, 1.56)
