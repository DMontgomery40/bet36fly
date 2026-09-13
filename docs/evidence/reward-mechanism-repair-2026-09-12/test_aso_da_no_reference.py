"""Independent equation checks only; no source protocol, fit or MaleCNS input."""

import numpy as np
import pytest
from scipy.linalg import expm

from aso_da_no_reference import reference_advance, quiet_limit, weight


DEFAULT = dict(A_D=4.3 / 60, A_N=0.96 / 60, B_D=0.26 / 60, B_N=0.16 / 60, tau_D=30, tau_N=600)


def matrix_reference(state, t, kc, dan, params=DEFAULT):
    # Independent affine 5x5 matrix exponential, different from oracle formula.
    matrix = np.zeros((5, 5))
    for j, name in enumerate(["D", "N"]):
        rate = params["A_" + name] if kc and dan else params["B_" + name] if dan else 0
        matrix[j, j] = -rate
        matrix[j, 4] = rate if kc and dan else 0
        matrix[j + 2, j] = 1 / params["tau_" + name]
        matrix[j + 2, j + 2] = -1 / params["tau_" + name]
    return (expm(matrix * t) @ np.r_[state, 1])[:4]


@pytest.mark.parametrize("kc,dan", [(False, False), (True, False), (False, True), (True, True)])
@pytest.mark.parametrize("state,t", [([0, 0, 0, 0], 60), ([0.2, 0.8, 0.9, 0.1], 37), ([1, 1, 1, 1], 600)])
def test_every_mode_nonzero_state_matrix_reference(state, t, kc, dan):
    result = reference_advance(state, t, kc, dan)
    np.testing.assert_allclose(result, matrix_reference(state, t, kc, dan), atol=1e-12, rtol=1e-12)
    assert np.all((result >= 0) & (result <= 1)) and 0 <= weight(result) <= 2


@pytest.mark.parametrize("rate", [1 / 32, np.nextafter(1 / 32, 0), np.nextafter(1 / 32, 1)])
def test_resonant_and_neighboring_rates(rate):
    params = dict(DEFAULT, A_D=rate, A_N=1 / 512, tau_D=32, tau_N=512)
    result = reference_advance([0.3, 0.6, 0.1, 0.4], 49, True, True, parameters=params)
    np.testing.assert_allclose(
        result, matrix_reference([0.3, 0.6, 0.1, 0.4], 49, True, True, params), atol=1e-12, rtol=1e-12
    )


@pytest.mark.parametrize("kc,dan", [(False, False), (True, False), (False, True), (True, True)])
def test_split_time_is_same_continuous_solution(kc, dan):
    state = [0.31, 0.71, 0.52, 0.18]
    whole = reference_advance(state, 61, kc, dan)
    parts = reference_advance(reference_advance(state, 17, kc, dan), 44, kc, dan)
    np.testing.assert_allclose(whole, parts, atol=1e-12, rtol=1e-12)


@pytest.mark.parametrize("t", [0, 1e-12, 1e6])
def test_tiny_zero_long_interval_preserves_domain(t):
    state = [0.25, 0.75, 0.75, 0.25]
    result = reference_advance(state, t, True, True)
    assert np.all((result >= 0) & (result <= 1))
    if t == 0:
        np.testing.assert_array_equal(result, state)
    elif t == 1e-12:
        np.testing.assert_allclose(result, state, atol=1e-12, rtol=0)
    else:
        np.testing.assert_array_equal(result, np.ones(4))


@pytest.mark.parametrize("state", [[0, 0, 0, 0], [0.3, 0.7, 0.9, 0.1]])
def test_quiet_tail_tends_to_latent_memory_not_zero(state):
    expected = [state[0], state[1], state[0], state[1]]
    np.testing.assert_array_equal(quiet_limit(state), expected)
    np.testing.assert_allclose(reference_advance(state, 1e6, False, False), expected, atol=1e-12, rtol=0)
    assert weight(expected) == pytest.approx((1 - state[0]) * (1 + state[1]), abs=1e-15)


@pytest.mark.parametrize("da,no", [(False, True), (True, False), (False, False)])
def test_null_branch_controls_begin_and_remain_absent(da, no):
    result = reference_advance([0, 0, 0, 0], 60, True, True, da_enabled=da, no_enabled=no)
    if not da:
        assert result[0] == result[2] == 0
    if not no:
        assert result[1] == result[3] == 0


@pytest.mark.parametrize(
    "state,kwargs",
    [
        ([0.1, 0, 0, 0], dict(da_enabled=False)),
        ([0, 0, 0.1, 0], dict(da_enabled=False)),
        ([0, 0.1, 0, 0], dict(no_enabled=False)),
        ([0, 0, 0, 0.1], dict(no_enabled=False)),
    ],
)
def test_midstream_disable_cannot_erase_populated_branch(state, kwargs):
    with pytest.raises(ValueError):
        reference_advance(state, 1, False, False, **kwargs)


def test_shared_DAN_different_KC_history_and_hidden_state_persistence():
    trained = reference_advance([0, 0, 0, 0], 60, True, True)
    unpaired = reference_advance([0, 0, 0, 0], 60, False, True)
    assert trained[0] > 0 and trained[1] > 0
    np.testing.assert_array_equal(unpaired, np.zeros(4))
    repeated = reference_advance(trained, 60, True, True)
    assert repeated[0] > trained[0] and repeated[1] > trained[1]
    recovery = reference_advance(repeated, 1e6, False, True)
    np.testing.assert_allclose(recovery, np.zeros(4), atol=1e-12, rtol=0)
    assert weight(recovery) == 1
