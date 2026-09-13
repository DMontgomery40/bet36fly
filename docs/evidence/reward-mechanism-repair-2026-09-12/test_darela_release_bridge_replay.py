"""Finite release-mass bridge tests using only synthetic impulses."""

import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import quad

from darela_release_bridge_replay import replay

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "bet36fly/reward_lif.cpp").is_file())
OLD_PATH = ROOT / "docs/evidence/reward-mechanism-repair-2026-09-12/kc_weighted_bridge_replay.py"
spec = importlib.util.spec_from_file_location("_frozen_old_bridge", OLD_PATH)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)


def call(kc, dan, **kwargs):
    return replay(kc, dan, np.array([0]), np.array([0]), np.array([True]), np.array([0]), **kwargs)


def kernel(lag_ms):
    if lag_ms == 0:
        return 0.0
    return -0.0005 * math.copysign(1, lag_ms) * (math.exp(-abs(lag_ms) / 500) - math.exp(-abs(lag_ms) / 100))


@pytest.mark.parametrize("mass", [0.125, 1.0, 1.0000000000000002, 2.0, 100.0, float(2**32)])
@pytest.mark.parametrize("lag", [-250, 0, 250])
def test_release_mass_above_one_and_bound_match_complete_impulse_kernel(mass, lag):
    kc, dan = np.zeros((1300, 1)), np.zeros((1300, 1))
    kc[800], dan[800 + lag] = min(1.0, 1 / mass), mass
    result = call(kc, dan)
    expected = min(1.0, 1 / mass) * mass * kernel(lag * 0.2)
    assert result["edge_phases"][:, 0, 2].sum() == pytest.approx(expected, abs=1e-13)
    assert result["double_gains"][0] == pytest.approx(1 + expected, abs=1e-11)
    assert result["gains"][0] == np.float32(1 + expected)
    assert not result["bound_counts"].any()
    if mass > 1:
        with pytest.raises(ValueError):
            old.replay(kc, dan, np.array([0]), np.array([0]), np.array([True]), np.array([0]))


@pytest.mark.parametrize("seed", [11, 39, 72])
@pytest.mark.parametrize("learning", [False, True])
def test_every_result_is_byte_identical_to_old_helper_on_its_domain(seed, learning):
    rng = np.random.default_rng(seed)
    kc, dan = rng.random((1700, 3)), rng.random((1700, 2))
    pk, pc = np.array([0, 1, 2, 0, 1, 2]), np.array([0, 0, 0, 1, 1, 1])
    mask, groups = np.array([1, 0, 1, 1, 1, 0]), np.array([0, 1, 3, 4, 5, 7])
    initial = np.array([0.5, 0.75, 1, 1.25, 1.5, 0.75], dtype=np.float32)
    args = kc, dan, pk, pc, mask, groups
    before = [a.copy() for a in args] + [initial.copy()]
    a = replay(*args, initial=initial, learning=learning)
    b = old.replay(*args, initial=initial, learning=learning)
    assert a.keys() == b.keys()
    for key in a:
        assert a[key].dtype == b[key].dtype
        assert a[key].shape == b[key].shape
        assert a[key].tobytes() == b[key].tobytes()
    for actual, saved in zip((*args, initial), before, strict=True):
        np.testing.assert_array_equal(actual, saved)


def signal(t, events):
    rate, eligibility = 0.0, 0.0
    for at, mass in events:
        age = t - at
        if age >= 0:
            rate += mass * math.exp(-age / 100) / 100
            eligibility += mass * 1.25 * math.exp(-age / 500) * (-math.expm1(-age * 0.008))
    return rate, eligibility


def test_separate_large_release_product_areas_and_tail_match_independent_quadrature():
    kc, dan = np.zeros((1700, 1)), np.zeros((1700, 1))
    ks, ds = [(520, 0.25), (800, 0.5), (1520, 0.1)], [(540, 2.0), (850, 8.5), (1600, 3.25)]
    for step, mass in ks:
        kc[step] = mass
    for step, mass in ds:
        dan[step] = mass
    result = call(kc, dan)
    ke, de = [(t * 0.2, m) for t, m in ks], [(t * 0.2, m) for t, m in ds]
    for phase, (start, stop) in enumerate([(100, 130), (130, 300), (300, 340), (340, math.inf)]):
        cuts = sorted({start, stop} | {t for t, _ in ke + de if start < t < stop})
        for field, sign in [(0, 1), (1, -1)]:

            def integrand(t):
                kr, kel = signal(t, ke)
                dr, delig = signal(t, de)
                return 0.00048 * (kr * delig if sign == 1 else -kel * dr)

            expected = sum(
                quad(integrand, a, b, epsabs=1e-14, epsrel=1e-12)[0] for a, b in zip(cuts, cuts[1:])
            )
            assert result["edge_phases"][phase, 0, field] == pytest.approx(expected, abs=2e-13)
    np.testing.assert_array_equal(result["publication_counts"][:, 0], [150, 850, 200, 1])
    np.testing.assert_allclose(
        result["edge_phases"][..., 0] + result["edge_phases"][..., 1],
        result["edge_phases"][..., 2],
        atol=2e-13,
        rtol=0,
    )


def test_appended_silence_preserves_complete_release_tail_gain():
    kc, dan = np.zeros((800, 1)), np.zeros((800, 1))
    kc[650], dan[700] = 0.125, 12.0
    short = call(kc, dan)
    long = call(np.pad(kc, ((0, 1200), (0, 0))), np.pad(dan, ((0, 1200), (0, 0))))
    np.testing.assert_array_equal(short["gains"], long["gains"])
    np.testing.assert_allclose(short["double_gains"], long["double_gains"], atol=1e-11, rtol=0)
    np.testing.assert_allclose(
        short["edge_phases"].sum(0)[:, :3], long["edge_phases"].sum(0)[:, :3], atol=2e-13, rtol=0
    )
    assert short["edge_phases"][3, 0, 0] > long["edge_phases"][3, 0, 0]


@pytest.mark.parametrize("initial", [0.5, 1.0, 1.5])
@pytest.mark.parametrize("masked", [False, True])
def test_frozen_or_excluded_large_release_preserves_gain_bytes_and_bound_policy(initial, masked):
    kc, dan = np.ones((700, 1)), np.full((700, 1), float(2**32))
    checkpoint = np.array([initial], np.float32)
    result = replay(
        kc,
        dan,
        np.array([0]),
        np.array([0]),
        np.array([masked]),
        np.array([0]),
        initial=checkpoint,
        learning=False,
    )
    assert result["gains"].tobytes() == checkpoint.tobytes()
    assert result["double_gains"][0] == initial
    assert not result["edge_phases"][..., :5].any()
    assert result["publication_counts"].sum() == (201 if masked else 0)
    np.testing.assert_array_equal(
        result["bound_counts"][:, 0],
        [201 if masked and initial == 0.5 else 0, 201 if masked and initial == 1.5 else 0],
    )
    assert result["endpoint_dan"].sum() > 1


def test_active_excluded_edges_stay_unchanged_while_eligible_edge_uses_release():
    kc, dan = np.zeros((700, 1)), np.zeros((700, 2))
    kc[510], dan[520] = 0.5, [4.0, 8.0]
    initial = np.array([0.5, 1.0, 1.5, 1.0], np.float32)
    result = replay(
        kc,
        dan,
        np.array([0, 0, 0, 0]),
        np.array([0, 0, 1, 1]),
        np.array([0, 1, 0, 1]),
        np.array([0, 1, 4, 5]),
        initial=initial,
    )
    assert result["gains"][[0, 2]].tobytes() == initial[[0, 2]].tobytes()
    assert not result["edge_phases"][:, [0, 2]].any()
    assert not result["bound_counts"][:, [0, 2]].any()
    assert result["gains"][1] != initial[1]
    assert result["gains"][3] != initial[3]


def test_release_before_onset_remains_excluded_and_onset_is_inclusive():
    kc, dan = np.zeros((700, 1)), np.zeros((700, 1))
    kc[500], dan[499] = 0.25, 16.0
    result = call(kc, dan)
    assert not result["edge_phases"].any()
    assert not result["endpoint_dan"].any()
    dan[500], kc[501] = 8.0, 0.5
    expected = 4 * kernel(-0.2)
    assert call(kc, dan)["edge_phases"][:, 0, 2].sum() == pytest.approx(expected, abs=1e-13)


@pytest.mark.parametrize(
    "bad", [np.nan, np.inf, -np.inf, -1e-300, 2**32 + 1.0, np.nextafter(float(2**32), np.inf), 1e308]
)
def test_dan_mass_outside_finite_envelope_is_rejected_without_coercion(bad):
    kc, dan = np.zeros((600, 1)), np.zeros((600, 1))
    dan[550] = bad
    with pytest.raises(ValueError):
        call(kc, dan)


@pytest.mark.parametrize("bad", [np.nan, np.inf, -1e-300, np.nextafter(1.0, np.inf), 2.0, float(2**32)])
def test_kc_mass_domain_is_not_widened(bad):
    kc, dan = np.zeros((600, 1)), np.zeros((600, 1))
    kc[550] = bad
    with pytest.raises(ValueError):
        call(kc, dan)


@pytest.mark.parametrize("case", ["complex", "object", "string", "rank", "length", "channels"])
def test_release_shape_and_dtype_families_remain_rejected(case):
    kc, dan = np.zeros((600, 1)), np.zeros((600, 1))
    if case in ("complex", "object", "string"):
        dan = dan.astype({"complex": complex, "object": object, "string": str}[case])
    elif case == "rank":
        dan = dan[:, :, None]
    elif case == "length":
        dan = dan[:-1]
    else:
        dan = np.zeros((600, 3))
    with pytest.raises(ValueError):
        call(kc, dan)
