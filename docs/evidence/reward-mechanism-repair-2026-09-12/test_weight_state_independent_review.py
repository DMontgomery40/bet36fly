"""Separate reviewer: exact arithmetic, overflow, and ordered-trial boundaries.

Only synthetic arrays and scalar products. No study prepare/execute, native or
saved-history evaluation. Expectations do not call writer test helpers.
"""

from fractions import Fraction
import itertools
import socket

import numpy as np
import pytest

import weight_dependent_shadow as helper
import weight_state_guard_reference as guard
import run_weight_state_shadow as runner


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Review cannot perform network I/O")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.mark.parametrize("magnitude,duration", [(1e308, 1e5), (1e307, 1e7), (1e305, 1e9)])
@pytest.mark.parametrize("vector", [False, True])
def test_balanced_finite_inputs_cannot_publish_nonfinite_areas(magnitude, duration, vector):
    drive = np.array([magnitude, magnitude / 2]) if vector else magnitude
    gain = np.ones(2) if vector else 1.0
    with np.errstate(all="ignore"), pytest.raises(ArithmeticError):
        helper.integrate_products(lambda _: (drive, drive), duration, gain, max_step=duration)


@pytest.mark.parametrize("magnitude,duration", [(1e6, 20.0), (1e100, 1e-90), (1e200, 1e-190)])
def test_large_finite_balanced_controls_keep_exact_gain_and_finite_areas(magnitude, duration):
    result = helper.integrate_products(lambda _: (magnitude, magnitude), duration, 1.0, max_step=duration)
    assert result["gain"] == 1.0
    expected = 0.0005 * magnitude * duration
    assert np.isfinite(result["estimated_error"]).all()
    np.testing.assert_allclose([result["positive"], result["negative"]], [expected, -expected], rtol=1e-14)


def independent_point(values):
    mean = Fraction(sum(values), 8)
    variance = sum((Fraction(v) - mean) ** 2 for v in values) / 7
    return 4 * mean * mean <= variance


@pytest.mark.parametrize("seed", range(12))
def test_guard_rational_mean_variance_and_scale_invariance(seed):
    values = np.random.default_rng(seed).integers(-20, 21, size=8).tolist()
    for multiplier in (1, -1, 2**200 + 1):
        scaled = tuple(int(v) * multiplier for v in values)
        expected = independent_point(scaled)
        assert guard.point_guard(scaled) is expected
        result = guard.classify_box(scaled, scaled)
        assert result["classification"] == ("all_pass" if expected else "all_fail")


@pytest.mark.parametrize("seed", range(12))
def test_box_certificates_never_overclaim_any_discrete_member(seed):
    rng = np.random.default_rng(seed + 80)
    low = tuple(int(v) for v in rng.integers(-3, 4, size=8))
    high = tuple(v + int(d) for v, d in zip(low, rng.integers(0, 2, size=8)))
    actual = guard.classify_box(low, high)
    verdicts = [
        independent_point(v) for v in itertools.product(*(range(lo, hi + 1) for lo, hi in zip(low, high)))
    ]
    if actual["classification"] == "all_pass":
        assert all(verdicts)
    elif actual["classification"] == "all_fail":
        assert not any(verdicts)
    witness = actual["minimum_variance_witness"]
    mean = sum(witness) / 8
    assert actual["minimum_variance"] == sum((v - mean) ** 2 for v in witness) / 7
    for lo, hi, v in zip(low, high, witness):
        assert lo <= v <= hi
        assert v == max(Fraction(lo), min(Fraction(hi), mean))


@pytest.mark.parametrize("base", [0.5, 0.75, np.nextafter(np.float32(1), np.float32(0)), 1.0, 1.25])
def test_float32_midpoint_neighbors_remain_exact_rationals(base):
    lower = np.float32(base)
    upper = np.nextafter(lower, np.float32(np.inf))
    lo, hi = Fraction(float(lower)), Fraction(float(upper))
    midpoint = (lo + hi) / 2
    epsilon = Fraction(1, 2**100)
    assert guard.round_f32_ticks(midpoint - epsilon) == int(lo * 2**24)
    assert guard.round_f32_ticks(midpoint + epsilon) == int(hi * 2**24)
    # Tie chooses the representable index with even significand.
    step = int((hi - lo) * 2**24)
    low_index = int(lo * 2**24) // step
    assert guard.round_f32_ticks(midpoint) == int((lo if low_index % 2 == 0 else hi) * 2**24)


def canonical_rows():
    games = (
        (4362, 4366, 4370, 4374, 4378, 4383, 4387, 4391),
        (4395, 4399, 4404, 4408, 4412, 4416, 4420, 4425),
    )
    runs = ("diag-rate-bridge-v1-maskgamma-de050d773763", "diag-rate-bridge-v1-maskgamma-dea14759e9ca")
    rows = []
    for panel, selected in enumerate(games):
        for game in selected:
            for noise, extra in (("base", 0), ("alt", 1000000)):
                rows.append(
                    dict(
                        panel=panel,
                        run_id=runs[panel],
                        game=game,
                        seed_set=noise,
                        seed=game + 42 + panel * 2000000 + extra,
                        gains=np.ones(2, np.float32),
                        double_gains=np.ones(2),
                    )
                )
    return rows


@pytest.mark.parametrize(
    "mutation",
    ["duplicate", "wrong_game", "wrong_seed", "wrong_run", "float_seed", "bool_panel", "permutation"],
)
def test_ordered_full_selector_identity_cannot_be_relabelled(mutation):
    rows = canonical_rows()
    if mutation == "duplicate":
        rows[2] = rows[0].copy()
    elif mutation == "wrong_game":
        rows[0]["game"] += 1
    elif mutation == "wrong_seed":
        rows[0]["seed"] += 1
    elif mutation == "wrong_run":
        rows[0]["run_id"] = rows[16]["run_id"]
    elif mutation == "float_seed":
        rows[0]["seed"] = float(rows[0]["seed"])
    elif mutation == "bool_panel":
        rows[0]["panel"] = False
    else:
        rows[0], rows[2] = rows[2], rows[0]
    with pytest.raises(ValueError):
        runner.guard_summary(rows, [np.array([True, False]), np.array([False, True])])
