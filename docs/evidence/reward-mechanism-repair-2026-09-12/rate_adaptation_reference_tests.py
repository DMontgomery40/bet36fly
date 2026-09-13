"""Synthetic validation of the independent oracle; no saved neural data."""

import math

import numpy as np
import pytest

from rate_adaptation_reference_oracle import (
    AREA_ATOL, AREA_RTOL, C, E, R, STATE_ATOL, STATE_RTOL,
    finite_ode, tail_gain_from_ode_split, tail_quadrature,
    zero_start_constant_states,
)


def assert_areas(left, right):
    np.testing.assert_allclose(
        [left.positive_area, left.negative_area, left.signed_area],
        [right.positive_area, right.negative_area, right.signed_area],
        atol=AREA_ATOL, rtol=AREA_RTOL,
    )


@pytest.mark.parametrize("state", [
    [0, 0, 0, 0, 0], [R, 0, 0, 0, 0], [0, 0, R, 0, 0],
    [0.3, 40, 0, 0.1, 2], [0.1, 30, 0.02, 0.03, 4],
    [0.1, 30, 0.02, 0.02, 4], [0.1, 30, 0.02, 0, 4],
    [5, 2500, 5, 3, 500],
])
@pytest.mark.parametrize("duration", [0.0, 0.2, 250.0])
def test_full_tail_equals_independent_ode_prefix_plus_remainder(state, duration):
    assert_areas(tail_gain_from_ode_split(state, duration), tail_quadrature(state))


@pytest.mark.parametrize("duration", [1e-9, 0.2, 1.0, 100.0, 500.0])
@pytest.mark.parametrize("rates", [(0.0, 0.0), (0.0, 0.03), (0.02, 0.0), (0.02, 0.03)])
def test_repeated_exponent_constant_input_against_closed_form(duration, rates):
    observed = finite_ode(np.zeros(5), duration, kc_constant=rates[0], dan_constant=rates[1])
    expected = zero_start_constant_states(*rates, duration)
    np.testing.assert_allclose(observed.state, expected, atol=STATE_ATOL, rtol=STATE_RTOL)
    assert observed.positive_area >= 0
    assert observed.negative_area >= 0


@pytest.mark.parametrize("ratio", [0.0, 0.5, 1.0, 1.00000000000001, 2.0])
def test_baseline_step_from_equilibrium(ratio):
    baseline, target, h = 0.02, 0.02 * ratio, 500.0
    state = [0, 0, baseline, baseline, 0]
    result = finite_ode(state, h, dan_constant=target)
    difference = target - baseline
    signal = difference * R / (R - E) * (math.exp(-E * h) - math.exp(-R * h))
    assert result.state[2] - result.state[3] == pytest.approx(signal, abs=STATE_ATOL)
    if ratio <= 1:
        assert result.state[4] == 0
    else:
        assert result.state[4] >= 0


@pytest.mark.parametrize("h", [1e-9, 0.2, 100.0])
def test_zero_duration_near_and_exact_crossing(h):
    d = 0.02
    # Exact nonnegative baseline that places the analytic crossing at h/2.
    delta = R - E
    a = R * d / delta
    baseline = a * math.exp(-delta * h / 2) - E * d / delta
    if baseline < 0:
        pytest.fail("synthetic crossing construction became invalid")
    state = [0.1, 20, d, baseline, 0]
    assert_areas(tail_quadrature(state), tail_gain_from_ode_split(state, h))
    result = finite_ode(state, h)
    assert result.state[4] >= -STATE_ATOL


def test_inactive_tail_exact_and_one_sided_cases():
    state = [0.2, 50, 0.01, 0.02, 4]
    tail = tail_quadrature(state)
    assert tail.positive_area == pytest.approx(0.2 * 4 / (R + E), abs=1e-13)
    assert tail.negative_area == 0
    for one_sided in ([R, 0, 0, 0, 0], [0, 0, R, 0, 0], [0, 0, 0, 0, 0]):
        assert tail_quadrature(one_sided).gain_delta == 0


def test_positive_area_domination_for_one_pulse_and_initial_eligibility():
    state = [0.3, 20, 0.2, 0.01, 10]
    adapted = tail_quadrature(state)
    # Unadapted D decays at R; causal E_D obeys the same positive kernel.
    k, u, d, _, v = state
    p = R + E
    common = k * d / (2 * R * p)
    raw_p = k * v / p + common
    raw_n = u * d / p + common
    assert 0 <= adapted.positive_area <= raw_p
    assert 0 <= adapted.negative_area <= raw_n
    assert abs(adapted.gain_delta) <= C * (raw_p + raw_n)


@pytest.mark.parametrize("state", [
    [0, 0, 0, 0], [0, 0, 0, 0, -1], [0, 0, np.nan, 0, 0],
    [0, 0, np.inf, 0, 0], [0, 0, 0, 0, 0, 0],
])
def test_malformed_states_rejected(state):
    with pytest.raises(ValueError):
        finite_ode(state, 0.2)
    with pytest.raises(ValueError):
        tail_quadrature(state)


@pytest.mark.parametrize("duration", [-0.2, np.nan, np.inf])
def test_invalid_duration_rejected(duration):
    with pytest.raises(ValueError):
        finite_ode([0, 0, 0, 0, 0], duration)


def test_coincident_impulse_result_is_not_forced_to_old_antisymmetric_kernel():
    state = [R, 0, R, 0, 0]
    reference = tail_quadrature(state)
    assert_areas(reference, tail_gain_from_ode_split(state, 300))
    # This equation narrows the DAN signal relative to KC rate. Its coincident
    # response is allowed to differ from the old bridge; no zero is imposed.
    assert reference.positive_area > 0
    assert reference.negative_area > 0
    assert math.isfinite(reference.gain_delta)
