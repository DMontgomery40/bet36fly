"""Independent source-component comparisons; synthetic states, no source protocol.

The frozen 70-digit reference is unchanged. A separately formed 5x5 matrix
checks the two disputed near-resonance cases without SciPy's divided difference.
"""

from dataclasses import asdict, astuple
from itertools import product
import math

import mpmath as mp
import numpy as np
import pytest

import aso_da_no as writer
from aso_da_no_reference import reference_advance, quiet_limit


def _array(state):
    return np.asarray(astuple(state), dtype=np.float64)


def _matrix_reference(initial, seconds, params):
    """DAN-only 70-digit affine matrix, independently arranged as d,n,D,N,1."""
    with mp.workdps(70):
        matrix = mp.zeros(5)
        for j, (rate, tau) in enumerate(((params.B_D, params.tau_D), (params.B_N, params.tau_N))):
            lam, mu = mp.mpf(str(rate)), 1 / mp.mpf(str(tau))
            matrix[j, j] = -lam
            matrix[j + 2, j] = mu
            matrix[j + 2, j + 2] = -mu
        result = mp.expm(matrix * mp.mpf(seconds)) * mp.matrix([*initial, 1])
        return np.asarray([float(v) for v in result[:4]], dtype=np.float64)


@pytest.mark.parametrize("kc,dan", list(product((False, True), repeat=2)))
def test_source_modes_nonzero_and_unit_cube_boundaries(kc, dan):
    near_one = math.nextafter(1.0, 0.0)
    states = [
        (0.2, 0.6, 0.9, 0.1),
        *product((0.0, 1.0), repeat=4),
        (near_one,) * 4,
        (1.0, near_one, near_one, 1.0),
    ]
    for initial, seconds in product(states, (1e-12, 0.1, 1.0, 30.0, 600.0, 1e6)):
        got = _array(writer.advance(writer.SourceState(*initial), seconds, kc_active=kc, dan_active=dan))
        expected = reference_advance(initial, seconds, kc, dan)
        assert np.isfinite(got).all() and np.all((got >= 0) & (got <= 1))
        np.testing.assert_allclose(got, expected, atol=1e-12, rtol=1e-12)


@pytest.mark.parametrize("epsilon", [-1e-10, 1e-10])
def test_near_resonance_against_two_independent_high_precision_forms(epsilon):
    params = writer.Parameters(
        A_D=1 + epsilon, B_D=1 + epsilon, A_N=2 + epsilon, B_N=2 + epsilon, tau_D=1, tau_N=0.5
    )
    initial, seconds = (0.2, 0.6, 0.9, 0.1), 1.7
    got = _array(
        writer.advance(writer.SourceState(*initial), seconds, kc_active=False, dan_active=True, params=params)
    )
    closed = reference_advance(initial, seconds, False, True, parameters=asdict(params))
    matrix = _matrix_reference(initial, seconds, params)
    np.testing.assert_array_equal(closed, matrix)
    np.testing.assert_allclose(got, closed, atol=1e-12, rtol=1e-12)


def test_tiny_coactivity_preserves_second_order_expressed_response():
    params = writer.Parameters()
    leading = np.asarray([params.A_D / (2 * params.tau_D), params.A_N / (2 * params.tau_N)])
    for seconds in (1e-12, 1e-9, 1e-6):
        got = _array(writer.advance(writer.SourceState(), seconds, kc_active=True, dan_active=True))
        expected = reference_advance((0, 0, 0, 0), seconds, True, True)
        assert np.all(got > 0)
        np.testing.assert_allclose(got, expected, atol=0, rtol=3e-14)
        if seconds == 1e-12:
            np.testing.assert_allclose(got[2:] / seconds**2, leading, atol=0, rtol=1e-12)


def test_same_current_weight_different_latent_memory_diverges_during_quiet():
    first = writer.SourceState(0.8, 0.1, 0.25, 0.4)
    second = writer.SourceState(0.1, 0.8, 0.25, 0.4)
    assert writer.weight(first) == writer.weight(second)
    results = []
    for initial in (first, second):
        result = writer.advance(initial, 600, kc_active=False, dan_active=False)
        np.testing.assert_allclose(
            _array(result), reference_advance(astuple(initial), 600, False, False), atol=1e-12, rtol=1e-12
        )
        np.testing.assert_array_equal(_array(writer.quiet_limit(initial)), quiet_limit(astuple(initial)))
        assert result.d == initial.d and result.n == initial.n
        results.append(result)
    assert writer.weight(results[0]) < writer.weight(results[1])
    assert writer.weight(writer.quiet_limit(first)) < writer.weight(writer.quiet_limit(second))
