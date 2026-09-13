"""Independent writer checks on synthetic data only, using external oracle."""

import math

import numpy as np
import pytest

from rate_adaptation_reference_oracle import (
    AREA_ATOL, AREA_RTOL, C, STATE_ATOL, STATE_RTOL,
    finite_ode, tail_quadrature,
)
from rate_adaptation_shadow import interval, publish


def cases():
    fixed = [
        [0, 0, 0, 0, 0], [0.01, 0, 0, 0, 0], [0, 0, 0.01, 0, 0],
        [0.01, 0, 0.01, 0, 0], [0.3, 0, 0.1, 0.1, 0],
        [0.3, 200, 0.1, 0.1, 20], [0.3, 200, 0.1, np.nextafter(0.1, 0), 0],
        [0.3, 200, 0.1, np.nextafter(0.1, 1), 20],
        [5, 2500, 5, 0, 2500], [5, 2500, 5, 4, 2500],
    ]
    rng = np.random.default_rng(92861)
    # Numerical coverage, not source/response-fit parameters or real trial data.
    fixed += list(10.0 ** rng.uniform(-8, 1, size=(20, 5)))
    return [np.asarray(x, dtype=float) for x in fixed]


def assert_result(actual, expected):
    observed_state = np.asarray([np.asarray(x).item() for x in actual['state']])
    np.testing.assert_allclose(
        observed_state, expected.state, atol=STATE_ATOL, rtol=STATE_RTOL,
    )
    actual_areas = [actual['positive'], actual['negative'], actual['signed']]
    expected_areas = [expected.positive_area, expected.negative_area, expected.signed_area]
    np.testing.assert_allclose(actual_areas, expected_areas, atol=AREA_ATOL, rtol=AREA_RTOL)
    assert actual['positive'] >= 0
    assert actual['negative'] >= 0


@pytest.mark.parametrize("state", cases())
@pytest.mark.parametrize("duration", [1e-9, 0.2, 20.0, 250.0])
def test_finite_writer_against_independent_raw_ode(state, duration):
    assert_result(interval(*state, duration), finite_ode(state, duration))


@pytest.mark.parametrize("state", cases())
def test_writer_complete_tail_against_infinite_laplace_quadrature(state):
    assert_result(interval(*state, math.inf), tail_quadrature(state))


@pytest.mark.parametrize("duration", [1e-7, 0.2, 10.0])
@pytest.mark.parametrize("fraction", [1e-5, 0.5, 1.0, 1.00001])
def test_zero_crossing_just_before_at_and_after_interval_end(duration, fraction):
    d, r, e = 0.03, 0.01, 0.002
    a = r * d / (r-e)
    baseline = a * math.exp(-(r-e) * duration * fraction) - e*d/(r-e)
    state = [0.2, 20, d, baseline, 0]
    assert_result(interval(*state, duration), finite_ode(state, duration))


def test_vector_kcs_against_independent_scalar_oracles():
    k, u = np.array([0, 0.01, 5]), np.array([0, 2, 2500])
    d, baseline, v, h = 0.01, 0.005, 4, 150
    observed = interval(k, u, d, baseline, v, h)
    for j in range(len(k)):
        scalar = dict(observed)
        scalar['state'] = [observed['state'][0][j], observed['state'][1][j], *observed['state'][2:]]
        for key in ('positive', 'negative', 'signed'):
            scalar[key] = observed[key][j]
        assert_result(scalar, finite_ode([k[j], u[j], d, baseline, v], h))


@pytest.mark.parametrize("initial", [0.5, 1.0, 1.5])
def test_whole_tail_clamps_once_after_independent_integral(initial):
    state = [5, 2500, 5, 0, 0]
    reference = tail_quadrature(state)
    computed = interval(*state, math.inf)
    result = publish(
        np.array([initial]), np.array([initial], dtype=np.float32),
        np.array([C * computed['signed']]), np.array([True]),
    )
    expected = np.float32(np.clip(initial + reference.gain_delta, 0.5, 1.5))
    assert result[1][0].tobytes() == expected.tobytes()
    # An active/inactive tail split is mathematical only. Publishing at the
    # crossing is observably a different clipped update for this synthetic case.
    crossing = computed['crossing_ms']
    first = interval(*state, crossing)
    second = interval(*first['state'], math.inf)
    wrong = publish(
        np.array([initial]), np.array([initial], dtype=np.float32),
        np.array([C * first['signed']]), np.array([True]),
    )
    wrong = publish(wrong[0], wrong[1], np.array([C * second['signed']]), np.array([True]))
    assert wrong[1][0] != result[1][0]
