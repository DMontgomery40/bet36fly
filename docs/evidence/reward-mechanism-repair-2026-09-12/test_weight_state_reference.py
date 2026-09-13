"""Synthetic-only independent reference tests; no captured histories or native code.

Breaks caught: wrong branch scaling/state dependence, missing or truncated tail,
impulse/order mistakes, incorrect event amplitude, lost gain state, and invalid
input silently accepted. Analytic expectations do not call the implementation.
"""

import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture(scope="module")
def ref():
    path = Path(__file__).with_name("weight_state_reference.py")
    assert path.is_file(), "Independent reference has not been implemented"
    spec = importlib.util.spec_from_file_location("weight_state_reference", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("initial", [0.5, 0.6, 1.0, 1.4, 1.5])
@pytest.mark.parametrize(
    "p,n",
    [(0.0, 0.0), (3.0, 0.0), (0.0, 3.0), (2.0, 2.0), (0.5, 3.0), (100.0, 0.0), (0.0, 100.0), (90.0, 10.0)],
)
def test_constant_products_match_exact_relaxation_and_accounting(ref, initial, p, n):
    duration = 170.0
    result = ref.integrate_products(lambda t: (p, n), (0.0, duration), initial)
    target = 0.5 + p / (p + n) if p + n else initial
    expected = target + (initial - target) * math.exp(-0.001 * (p + n) * duration)
    assert abs(result["gain"] - expected) <= 1e-11
    if p + n:
        integral_gain = target * duration + (initial - target) * -math.expm1(-0.001 * (p + n) * duration) / (
            0.001 * (p + n)
        )
        assert abs(result["positive"] - 0.001 * p * (1.5 * duration - integral_gain)) <= 2e-11
        assert abs(result["negative"] + 0.001 * n * (integral_gain - 0.5 * duration)) <= 2e-11
    assert abs(result["gain"] - initial - result["positive"] - result["negative"]) <= 2e-11
    assert 0.5 - 1e-11 <= result["gain"] <= 1.5 + 1e-11
    assert result["positive"] >= -2e-11 and result["negative"] <= 2e-11


@pytest.mark.parametrize("initial", [0.5, 0.8, 1.0, 1.5])
@pytest.mark.parametrize("positive", [True, False])
def test_exponential_pure_branch_matches_integrated_exposure(ref, initial, positive):
    amp, decay, duration = 4.0, 0.007, 513.0

    def drive(t):
        value = amp * math.exp(-decay * t)
        return (value, 0.0) if positive else (0.0, value)

    result = ref.integrate_products(drive, (0.0, duration), initial)
    exposure = amp * -math.expm1(-decay * duration) / decay
    bound = 1.5 if positive else 0.5
    expected = bound + (initial - bound) * math.exp(-0.001 * exposure)
    assert abs(result["gain"] - expected) <= 1e-11


@pytest.mark.parametrize("initial", [0.5, 0.8, 1.0, 1.3, 1.5])
def test_coincident_unit_events_complete_tail_has_exact_balanced_contraction(ref, initial):
    result = ref.event_reference([0.0], [0.0], end_ms=0.0, initial_gain=initial)
    # Integral P = integral N = .4; x decays by exp(-4*eta*.4).
    expected = 1 + (initial - 1) * math.exp(-0.0008)
    assert abs(result["gain"] - expected) <= 1e-11
    assert abs(float(ref.mp_event_gain([0.0], [0.0], end_ms=0.0, initial_gain=initial)) - expected) <= 1e-14
    assert result["electrical_gain"] == initial
    correction = 0.5 * (initial - 1) * -math.expm1(-0.0008)
    assert abs(result["positive"] - (0.0002 - correction)) <= 2e-11
    assert abs(result["negative"] - (-0.0002 - correction)) <= 2e-11


@pytest.mark.parametrize("lag", [-500.0, -100.0, -0.2, 0.0, 0.2, 100.0, 500.0])
@pytest.mark.parametrize("initial", [0.5, 1.0, 1.5])
def test_event_order_tail_and_initial_state_match_seventy_digit_integrating_factor(ref, lag, initial):
    kc, dan = ([0.0], [lag]) if lag >= 0 else ([-lag], [0.0])
    end = max(kc + dan) + 13.7
    result = ref.event_reference(kc, dan, end_ms=end, initial_gain=initial)
    expected = ref.mp_event_gain(kc, dan, end_ms=end, initial_gain=initial)
    assert abs(result["gain"] - float(expected)) <= 1e-11
    exchange = ref.event_reference(dan, kc, end_ms=end, initial_gain=2 - initial)
    assert abs(result["gain"] + exchange["gain"] - 2) <= 1e-11
    assert abs(result["positive"] + exchange["negative"]) <= 2e-11
    if initial == 1.0 and lag:
        assert (result["gain"] - 1) * lag < 0
        additive = 0.0005 * math.copysign(1, lag) * (math.exp(-abs(lag) / 100) - math.exp(-abs(lag) / 500))
        assert abs(result["gain"] - 1) <= abs(additive) + 1e-11


@pytest.mark.parametrize("seed", [4, 19, 51])
def test_repeated_weighted_histories_and_tail_boundary_are_partition_invariant(ref, seed):
    rng = np.random.default_rng(seed)
    kc = np.sort(rng.choice(np.arange(0.0, 121.0, 10.0), 7, replace=False))
    dan = np.sort(rng.choice(np.arange(0.0, 121.0, 10.0), 6, replace=False))
    kw = rng.integers(1, 4, len(kc))
    dw = rng.integers(1, 4, len(dan)) / 2
    args = dict(kc_weights=kw, dan_weights=dw, initial_gain=0.83)
    near = ref.event_reference(kc, dan, end_ms=130.0, **args)
    far = ref.event_reference(kc, dan, end_ms=850.0, **args)
    exact = ref.mp_event_gain(kc, dan, end_ms=130.0, **args)
    assert abs(near["gain"] - float(exact)) <= 1e-11
    assert abs(near["gain"] - far["gain"]) <= 1e-11
    for name in ("positive", "negative"):
        assert abs(near[name] - far[name]) <= 2e-11
    assert abs(near["gain"] - 0.83 - near["positive"] - near["negative"]) <= 2e-11


def test_arbitrary_finite_interval_partition_preserves_state_and_areas(ref):
    def drive(t):
        return 0.7 + 0.2 * math.sin(t / 29), 1.4 + 0.3 * math.cos(t / 37)

    full = ref.integrate_products(drive, (0.0, 430.0), 0.71)
    left = ref.integrate_products(drive, (0.0, 173.25), 0.71)
    right = ref.integrate_products(drive, (173.25, 430.0), left["gain"])
    assert abs(full["gain"] - right["gain"]) <= 1e-11
    for field in ("positive", "negative"):
        assert abs(full[field] - left[field] - right[field]) <= 2e-11


@pytest.mark.parametrize("initial", [0.5, 1.0, 1.5])
@pytest.mark.parametrize("kc,dan", [([], []), ([0.0, 40.0], []), ([], [0.0, 40.0])])
def test_silence_and_one_input_preserve_gain(ref, initial, kc, dan):
    result = ref.event_reference(kc, dan, end_ms=100.0, initial_gain=initial)
    assert result["gain"] == initial
    assert result["positive"] == result["negative"] == 0.0


def test_duplicate_events_are_equivalent_to_impulse_mass_not_binary_coercion(ref):
    a = ref.event_reference([0.0, 0.0, 10.0], [5.0, 5.0], end_ms=20.0)
    b = ref.event_reference([0.0, 10.0], [5.0], kc_weights=[2.0, 1.0], dan_weights=[2.0], end_ms=20.0)
    for name in ("gain", "positive", "negative"):
        assert abs(a[name] - b[name]) <= 2e-11


@pytest.mark.parametrize("full_tail", [False, True])
def test_impulse_at_electrical_endpoint_belongs_to_tail_and_finite_mode_matches_mp(ref, full_tail):
    result = ref.event_reference([0.0], [20.0], end_ms=20.0, full_tail=full_tail)
    expected = ref.mp_event_gain([0.0], [20.0], end_ms=20.0, full_tail=full_tail)
    assert result["electrical_gain"] == 1.0
    assert result["electrical_positive"] == result["electrical_negative"] == 0.0
    assert abs(result["gain"] - float(expected)) <= 1e-11
    assert result["gain32"] == np.float32(result["gain"])
    if full_tail:
        assert result["gain"] < 1.0
    else:
        assert result["gain"] == 1.0


@pytest.mark.parametrize(
    "span,initial",
    [((1.0, 0.0), 1.0), ((0.0, np.inf), 1.0), ((np.nan, 1.0), 1.0), ((0.0, 1.0), np.nan), ((0.0, 1.0), 1.51)],
)
def test_malformed_continuous_interval_rejected(ref, span, initial):
    with pytest.raises(ValueError):
        ref.integrate_products(lambda t: (1.0, 1.0), span, initial)


@pytest.mark.parametrize("flag", [None, 1, "false"])
def test_ambiguous_tail_mode_is_rejected_by_both_oracles(ref, flag):
    for fn in (ref.event_reference, ref.mp_event_gain):
        with pytest.raises(ValueError):
            fn([0.0], [0.0], end_ms=0.0, full_tail=flag)


@pytest.mark.parametrize(
    "change",
    [
        "negative_time",
        "nonfinite_time",
        "future_event",
        "negative_mass",
        "wrong_mass_shape",
        "bad_initial",
        "bad_end",
    ],
)
def test_malformed_event_contract_fails_closed(ref, change):
    args = dict(kc_times=[0.0, 10.0], dan_times=[5.0], end_ms=20.0)
    if change == "negative_time":
        args["kc_times"] = [-1.0, 10.0]
    if change == "nonfinite_time":
        args["dan_times"] = [float("nan")]
    if change == "future_event":
        args["dan_times"] = [21.0]
    if change == "negative_mass":
        args["dan_weights"] = [-1.0]
    if change == "wrong_mass_shape":
        args["kc_weights"] = [1.0]
    if change == "bad_initial":
        args["initial_gain"] = 0.49
    if change == "bad_end":
        args["end_ms"] = float("inf")
    with pytest.raises(ValueError):
        ref.event_reference(**args)


@pytest.mark.parametrize("p,n", [(-1.0, 0.0), (0.0, -1.0), (np.nan, 0.0), (0.0, np.inf)])
def test_invalid_product_drives_are_rejected(ref, p, n):
    with pytest.raises(ValueError):
        ref.integrate_products(lambda t: (p, n), (0.0, 1.0), 1.0)
