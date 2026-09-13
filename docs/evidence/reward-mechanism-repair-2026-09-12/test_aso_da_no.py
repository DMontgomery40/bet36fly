"""Source-equation checks; no circuit, spike mapping, fit or source driver."""

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, localcontext
import importlib
import importlib.util
import itertools
import math

import mpmath as mp
import numpy as np
import pytest
from scipy.linalg import expm


@pytest.fixture
def api():
    assert importlib.util.find_spec("aso_da_no") is not None, "source component is not implemented"
    return importlib.import_module("aso_da_no")


def values(state):
    return np.array([state.d, state.n, state.D, state.N])


def matrix_reference(state, seconds, kc, dan, params):
    result = []
    for x, X, A, B, tau in (
        (state.d, state.D, params.A_D, params.B_D, params.tau_D),
        (state.n, state.N, params.A_N, params.B_N, params.tau_N),
    ):
        lam = (A if kc else B) if dan else 0
        matrix = np.array([[-lam, 0, lam if kc and dan else 0], [1 / tau, -1 / tau, 0], [0, 0, 0]])
        result.append((expm(matrix * seconds) @ [x, X, 1])[:2])
    return np.array([result[0][0], result[1][0], result[0][1], result[1][1]])


def high_precision_matrix_reference(state, seconds, kc, dan, params):
    # SciPy's F64 triangular expm loses precision at nearly repeated diagonal
    # entries. Keep an independently exponentiated matrix for this entire
    # family; do not relax the producer tolerance or share its exact formula.
    with mp.workdps(70):
        result = []
        for x, X, A, B, tau in (
            (state.d, state.D, params.A_D, params.B_D, params.tau_D),
            (state.n, state.N, params.A_N, params.B_N, params.tau_N),
        ):
            lam, mu = mp.mpf((A if kc else B) if dan else 0), 1 / mp.mpf(tau)
            matrix = mp.matrix([[-lam, 0, lam if kc and dan else 0], [mu, -mu, 0], [0, 0, 0]])
            result.append(mp.expm(matrix * mp.mpf(seconds)) * mp.matrix([x, X, 1]))
        return np.array([float(result[0][0]), float(result[1][0]), float(result[0][1]), float(result[1][1])])


@pytest.mark.parametrize("mode", list(itertools.product([False, True], repeat=2)))
@pytest.mark.parametrize("initial", [(0, 0, 0, 0), (0.2, 0.7, 0.8, 0.1), (1, 1, 1, 1)])
@pytest.mark.parametrize("seconds", [0, 0.4, 60, 1800])
def test_all_modes_match_independent_affine_matrix(api, mode, initial, seconds):
    state, params = api.SourceState(*initial), api.Parameters()
    result = api.advance(state, seconds, kc_active=mode[0], dan_active=mode[1])
    np.testing.assert_allclose(
        values(result), matrix_reference(state, seconds, *mode, params), atol=2e-13, rtol=2e-12
    )
    assert np.isfinite(values(result)).all() and np.all((values(result) >= 0) & (values(result) <= 1))
    assert 0 <= api.weight(result) <= 2
    assert values(state).tolist() == list(initial)
    assert result is not state


@pytest.mark.parametrize("seconds", [1e-12, 1e-9, 1e-6])
@pytest.mark.parametrize("resonance", [False, True])
def test_quadratic_onset_is_positive_and_relatively_accurate(api, seconds, resonance):
    params = api.Parameters() if not resonance else api.Parameters(A_D=1, A_N=1, tau_D=1, tau_N=1)
    result = api.advance(api.SourceState(), seconds, kc_active=True, dan_active=True, params=params)
    with localcontext() as ctx:
        ctx.prec = 100
        t = Decimal(str(seconds))
        for observed, rate, tau in (
            (result.D, params.A_D, params.tau_D),
            (result.N, params.A_N, params.tau_N),
        ):
            a, mu = Decimal(str(rate)), 1 / Decimal(str(tau))
            if a == mu:
                expected = 1 - (1 + a * t) * (-a * t).exp()
            else:
                expected = 1 + (a * (-mu * t).exp() - mu * (-a * t).exp()) / (mu - a)
            assert observed > 0
            assert observed == pytest.approx(float(expected), rel=3e-14, abs=0)


@pytest.mark.parametrize("epsilon", [-1e-6, -1e-10, -1e-15, 0, 1e-15, 1e-10, 1e-6])
@pytest.mark.parametrize("mode", [(True, True), (False, True)])
def test_equal_and_near_rates_have_continuous_nonzero_state_solution(api, epsilon, mode):
    params = api.Parameters(
        A_D=1 + epsilon, B_D=1 + epsilon, A_N=2 + epsilon, B_N=2 + epsilon, tau_D=1, tau_N=0.5
    )
    state = api.SourceState(0.2, 0.6, 0.9, 0.1)
    actual = api.advance(state, 1.7, kc_active=mode[0], dan_active=mode[1], params=params)
    np.testing.assert_allclose(
        values(actual), high_precision_matrix_reference(state, 1.7, *mode, params), atol=2e-14, rtol=2e-13
    )


@pytest.mark.parametrize(
    "scaled_rates", [(1e-12, 40), (0.01, 10), (0.01, 30), (0.49, 10), (0.49, 40), (0.5, 40)]
)
@pytest.mark.parametrize(
    "initial", [(1.0, np.nextafter(1.0, 0.0)), (np.nextafter(1.0, 0.0), 1.0), (1.0, 1.0)]
)
@pytest.mark.parametrize("mode", [(True, True), (False, True)])
def test_unit_cube_roundoff_uses_complement_without_projection(api, scaled_rates, initial, mode):
    rate, expression = scaled_rates
    params = api.Parameters(
        A_D=rate, A_N=rate, B_D=rate, B_N=rate, tau_D=1 / expression, tau_N=1 / expression
    )
    x, X = initial
    state = api.SourceState(x, x, X, X)
    actual = api.advance(state, 1.0, kc_active=mode[0], dan_active=mode[1], params=params)
    expected = high_precision_matrix_reference(state, 1.0, *mode, params)
    np.testing.assert_allclose(values(actual), expected, atol=2e-15, rtol=2e-15)
    assert np.all((values(actual) >= 0) & (values(actual) <= 1))


@pytest.mark.parametrize("mode", list(itertools.product([False, True], repeat=2)))
def test_split_time_has_no_implicit_reset(api, mode):
    state = api.SourceState(0.25, 0.75, 0.5, 0.125)
    single = api.advance(state, 101.25, kc_active=mode[0], dan_active=mode[1])
    split = state
    for t in [1e-6, 0.25, 1, 40, 59.999999]:
        split = api.advance(split, t, kc_active=mode[0], dan_active=mode[1])
    np.testing.assert_allclose(values(split), values(single), atol=2e-15, rtol=2e-14)


def test_source_minute_rates_and_repeated_acquisition_then_reversal(api):
    initial = api.SourceState()
    acquired = api.advance(initial, 60, kc_active=True, dan_active=True)
    assert acquired.d == pytest.approx(-math.expm1(-4.3), rel=1e-15)
    assert acquired.n == pytest.approx(-math.expm1(-0.96), rel=1e-15)
    repeated = api.advance(acquired, 60, kc_active=True, dan_active=True)
    assert repeated.d > acquired.d and repeated.n > acquired.n
    reverse = api.advance(acquired, 60, kc_active=False, dan_active=True)
    assert reverse.d == pytest.approx(acquired.d * math.exp(-0.26), rel=1e-15)
    assert reverse.n == pytest.approx(acquired.n * math.exp(-0.16), rel=1e-15)
    cold_dan = api.advance(initial, 60, kc_active=False, dan_active=True)
    assert values(cold_dan).tolist() == [0, 0, 0, 0]
    # Same DAN activity, different KC history: source does not collapse the two modes.
    assert not np.array_equal(values(reverse), values(repeated))


def test_quiet_limit_preserves_latent_memory_and_is_not_finite_reset(api):
    state = api.SourceState(0.7, 0.4, 0.2, 0.9)
    limit = api.quiet_limit(state)
    assert values(limit).tolist() == [0.7, 0.4, 0.7, 0.4]
    assert api.weight(limit) == (1 - 0.7) * (1 + 0.4)
    finite = api.advance(state, 600, kc_active=False, dan_active=False)
    assert finite.d == state.d and finite.n == state.n
    assert finite.N == pytest.approx(0.4 + 0.5 / math.e)
    np.testing.assert_allclose(
        values(api.advance(state, 1e6, kc_active=True, dan_active=False)), values(limit), atol=0, rtol=0
    )


@pytest.mark.parametrize("da,no", [(True, False), (False, True), (False, False)])
def test_source_null_branches_are_absent_from_start(api, da, no):
    result = api.advance(api.SourceState(), 60, kc_active=True, dan_active=True, da_enabled=da, no_enabled=no)
    if not da:
        assert result.d == result.D == 0
    if not no:
        assert result.n == result.N == 0
    assert api.weight(result) == (1 - result.D) * (1 + result.N)
    assert api.weight(result) < 1 if da else api.weight(result) >= 1
    limit = api.quiet_limit(result, da_enabled=da, no_enabled=no)
    assert limit.d == limit.D and limit.n == limit.N


@pytest.mark.parametrize(
    "field,flag", [("d", "da_enabled"), ("D", "da_enabled"), ("n", "no_enabled"), ("N", "no_enabled")]
)
def test_disabling_populated_branch_does_not_erase_memory(api, field, flag):
    state = api.SourceState(**{field: 0.1})
    with pytest.raises(ValueError):
        api.advance(state, 0, kc_active=False, dan_active=False, **{flag: False})
    with pytest.raises(ValueError):
        api.quiet_limit(state, **{flag: False})


@pytest.mark.parametrize("field", ["d", "n", "D", "N"])
@pytest.mark.parametrize("bad", [True, -0.01, 1.01, float("nan"), float("inf"), "0.5"])
def test_invalid_state_family_rejected(api, field, bad):
    with pytest.raises(ValueError):
        api.SourceState(**{field: bad})


@pytest.mark.parametrize("field", ["A_D", "A_N", "B_D", "B_N", "tau_D", "tau_N"])
@pytest.mark.parametrize("bad", [True, -0.1, float("nan"), float("inf"), "1"])
def test_invalid_parameters_rejected(api, field, bad):
    with pytest.raises(ValueError):
        api.Parameters(**{field: bad})


@pytest.mark.parametrize("bad", [True, -0.1, float("nan"), float("inf"), "1", 10**500])
def test_invalid_duration_rejected(api, bad):
    with pytest.raises(ValueError):
        api.advance(api.SourceState(), bad, kc_active=True, dan_active=True)


@pytest.mark.parametrize("field", ["kc_active", "dan_active", "da_enabled", "no_enabled"])
@pytest.mark.parametrize("bad", [0, 1.0, np.bool_(True), "true"])
def test_flags_do_not_accept_numeric_aliases(api, field, bad):
    flags = dict(kc_active=True, dan_active=True, da_enabled=True, no_enabled=True)
    flags[field] = bad
    with pytest.raises(ValueError):
        api.advance(api.SourceState(), 1, **flags)


def test_parameters_and_states_are_immutable_with_valid_zero_rate(api):
    p, s = api.Parameters(A_D=0, A_N=0, B_D=0, B_N=0), api.SourceState(0.2, 0.4, 0.2, 0.4)
    assert api.advance(s, 60, kc_active=True, dan_active=True, params=p) == s
    for name in ["tau_D", "tau_N"]:
        with pytest.raises(ValueError):
            replace(p, **{name: 0})
    with pytest.raises(FrozenInstanceError):
        s.d = 0
    with pytest.raises(FrozenInstanceError):
        p.A_D = 1


@pytest.mark.parametrize("mode", [(True, True), (False, True), (False, False)])
def test_large_finite_duration_and_rates_have_finite_limits(api, mode):
    p = api.Parameters(A_D=1e308, A_N=1e308, B_D=1e308, B_N=1e308, tau_D=1e-308, tau_N=1e-308)
    s = api.SourceState(0.2, 0.4, 0.6, 0.8)
    out = api.advance(s, 1e308, kc_active=mode[0], dan_active=mode[1], params=p)
    expected = [1, 1, 1, 1] if mode == (True, True) else ([0, 0, 0, 0] if mode[1] else [0.2, 0.4, 0.2, 0.4])
    assert values(out).tolist() == expected
