"""Synthetic weighted-event bridge contracts; no circuit or captured history."""

import math

import numpy as np
import pytest
from scipy.integrate import quad

try:
    from kc_weighted_bridge_replay import replay
except ModuleNotFoundError:
    replay = None


def call(kc, dan, *, initial=None, learning=True, mask=None):
    assert callable(replay), "The weighted-event replay helper is not implemented."
    return replay(
        kc,
        dan,
        np.array([0]),
        np.array([0]),
        np.array([True]) if mask is None else mask,
        np.array([0]),
        initial=initial,
        learning=learning,
    )


def kernel(lag):
    return (
        0.0
        if lag == 0
        else -0.0005 * math.copysign(1, lag) * (math.exp(-abs(lag) / 500) - math.exp(-abs(lag) / 100))
    )


@pytest.mark.parametrize("lag_steps", [-250, 0, 250])
@pytest.mark.parametrize("mass", [(1.0, 1.0), (0.25, 0.75)])
def test_weighted_pair_sign_and_full_tail_match_closed_kernel(lag_steps, mass):
    kc, dan = np.zeros((1300, 1)), np.zeros((1300, 1))
    kc[800] = mass[0]
    dan[800 + lag_steps] = mass[1]
    result = call(kc, dan)
    expected = math.prod(mass) * kernel(lag_steps * 0.2)
    assert abs(result["edge_phases"][:, 0, 2].sum() - expected) < 1e-13
    assert abs(result["double_gains"][0] - (1 + expected)) < 1e-11
    assert result["gains"][0] == np.float32(1 + expected)
    assert result["bound_counts"].sum() == 0


def signals(t, events):
    r, e = 0.0, 0.0
    for at, mass in events:
        age = t - at
        if age >= 0:
            r += mass * math.exp(-age / 100) / 100
            e += mass * 1.25 * math.exp(-age / 500) * (-math.expm1(-age * 0.008))
    return r, e


def direct_area(k_events, d_events, start, stop, sign):
    def product(t):
        rk, ek = signals(t, k_events)
        rd, ed = signals(t, d_events)
        return 0.00048 * (ed * rk if sign > 0 else -ek * rd)

    points = sorted({start, stop} | {t for t, _ in k_events + d_events if start < t < stop})
    return sum(quad(product, a, b, epsabs=1e-15, epsrel=1e-12)[0] for a, b in zip(points, points[1:]))


def test_separate_product_phases_match_independent_impulse_quadrature():
    kc, dan = np.zeros((1600, 1)), np.zeros((1600, 1))
    ks, ds = [(520, 0.25), (800, 0.5), (1520, 0.1)], [(540, 0.3), (850, 0.8)]
    for at, mass in ks:
        kc[at] = mass
    for at, mass in ds:
        dan[at] = mass
    result = call(kc, dan)
    k_events, d_events = [(t * 0.2, m) for t, m in ks], [(t * 0.2, m) for t, m in ds]
    for phase, (a, b) in enumerate([(100, 130), (130, 300), (300, 320), (320, math.inf)]):
        for column, sign in [(0, 1), (1, -1)]:
            expected = direct_area(k_events, d_events, a, b, sign)
            assert abs(result["edge_phases"][phase, 0, column] - expected) < 1e-13
    np.testing.assert_allclose(
        result["edge_phases"][..., 0] + result["edge_phases"][..., 1],
        result["edge_phases"][..., 2],
        rtol=0,
        atol=1e-13,
    )
    np.testing.assert_array_equal(result["publication_counts"][:, 0], [150, 850, 100, 1])


def test_cold_onset_excludes_all_earlier_impulses_without_excluding_onset_event():
    kc, dan = np.zeros((800, 1)), np.zeros((800, 1))
    kc[499] = 1
    dan[501] = 1
    result = call(kc, dan)
    assert not result["edge_phases"].any()
    assert result["endpoint_kc"].sum() == 0
    kc[500] = 0.25
    expected = 0.25 * kernel(0.2)
    assert abs(call(kc, dan)["edge_phases"][:, 0, 2].sum() - expected) < 1e-13


@pytest.mark.parametrize("initial", [0.5, 1.0, 1.5])
@pytest.mark.parametrize("learning", [False, True])
def test_zero_events_preserve_checkpoint_and_native_inclusive_bound_observations(initial, learning):
    zero = np.zeros((700, 1))
    checkpoint = np.array([initial], np.float32)
    result = call(zero, zero, initial=checkpoint, learning=learning)
    np.testing.assert_array_equal(result["gains"], checkpoint)
    assert result["double_gains"][0] == initial
    assert result["bound_counts"][0, 0] == (201 if initial == 0.5 else 0)
    assert result["bound_counts"][1, 0] == (201 if initial == 1.5 else 0)
    assert np.count_nonzero(result["edge_phases"][..., :5]) == 0


def test_no_learning_retains_filters_but_no_areas_or_gain_change():
    kc, dan = np.zeros((800, 1)), np.zeros((800, 1))
    kc[600], dan[650] = 0.5, 0.75
    result = call(kc, dan, learning=False)
    assert result["endpoint_kc"].sum() > 0
    assert result["endpoint_dan"].sum() > 0
    assert not result["edge_phases"].any()
    assert result["gains"][0] == result["double_gains"][0] == 1


def test_excluded_edge_has_no_publication_or_bound_observation():
    kc, dan = np.ones((700, 1)), np.ones((700, 1))
    result = call(kc, dan, initial=np.array([0.5], np.float32), mask=np.array([False]))
    assert result["gains"][0] == 0.5
    assert not result["edge_phases"].any()
    assert not result["bound_counts"].any()
    assert not result["publication_counts"].any()


def test_double_accumulator_keeps_sub_float32_increments_and_inputs_unchanged():
    kc, dan = np.zeros((1100, 1)), np.zeros((1100, 1))
    kc[510:] = 0.005
    dan[500] = 0.01
    checkpoint = np.ones(1, np.float32)
    before = kc.copy(), dan.copy(), checkpoint.copy()
    expected = sum(0.00005 * kernel((500 - t) * 0.2) for t in range(510, 1100))
    result = call(kc, dan, initial=checkpoint)
    assert expected > np.spacing(np.float32(1))
    assert abs(result["double_gains"][0] - 1 - expected) < 1e-11
    assert result["gains"][0] == np.float32(1 + expected)
    for actual, original in zip((kc, dan, checkpoint), before):
        np.testing.assert_array_equal(actual, original)


@pytest.mark.parametrize("bound,first", [(0.5, "kc"), (1.5, "dan")])
def test_clipping_and_bound_counts_follow_each_step_then_one_tail(bound, first):
    kc, dan = np.zeros((600, 1)), np.zeros((600, 1))
    kc[500 if first == "kc" else 510] = 1
    dan[510 if first == "kc" else 500] = 1
    result = call(kc, dan, initial=np.array([bound], np.float32))
    assert result["double_gains"][0] == result["gains"][0] == bound
    assert result["bound_counts"][0 if bound == 0.5 else 1, 0] == 101
    assert result["edge_phases"][:, 0, 2].sum() != 0
    assert not result["edge_phases"][:, 0, 3:5].any()


def test_appended_silence_moves_area_to_electrical_time_without_losing_tail():
    kc, dan = np.zeros((800, 1)), np.zeros((800, 1))
    kc[650], dan[700] = 0.25, 0.75
    short = call(kc, dan)
    long = call(np.pad(kc, ((0, 1200), (0, 0))), np.pad(dan, ((0, 1200), (0, 0))))
    np.testing.assert_allclose(short["double_gains"], long["double_gains"], rtol=0, atol=1e-11)
    np.testing.assert_array_equal(short["gains"], long["gains"])
    np.testing.assert_allclose(
        short["edge_phases"].sum(0)[:, :3], long["edge_phases"].sum(0)[:, :3], rtol=0, atol=1e-13
    )
    assert short["edge_phases"][3, 0, 0] > long["edge_phases"][3, 0, 0]


def test_shared_kc_different_channels_groups_and_masks_use_correct_edge_signal():
    kc, dan = np.zeros((900, 2)), np.zeros((900, 2))
    kc[600, 0], kc[610, 1] = 0.25, 0.5
    dan[650, 0], dan[550, 1] = 0.75, 1
    pk, pc, groups = np.array([0, 0, 1, 1]), np.array([0, 1, 0, 1]), np.array([0, 4, 1, 5])
    result = replay(kc, dan, pk, pc, np.array([True, True, False, True]), groups)
    expected = [0.25 * 0.75 * kernel(10), 0.25 * kernel(-10), 0, 0.5 * kernel(-12)]
    np.testing.assert_allclose(result["edge_phases"][:, :, 2].sum(0), expected, rtol=0, atol=1e-13)
    for edge, group in enumerate(groups):
        np.testing.assert_array_equal(result["group_phases"][:, group], result["edge_phases"][:, edge])
    np.testing.assert_array_equal(result["publication_counts"].sum(0), [401, 401, 0, 401])


def test_unsigned_maps_and_duplicate_group_edges_remain_valid():
    kc, dan = np.zeros((700, 1), np.float32), np.zeros((700, 1), np.int16)
    kc[600], dan[550] = 0.5, 1
    mapping = np.array([0, 0], np.uint64)
    result = replay(kc, dan, mapping, mapping, np.array([1, 1], np.uint8), mapping)
    np.testing.assert_array_equal(result["edge_phases"][:, 0], result["edge_phases"][:, 1])
    np.testing.assert_allclose(result["group_phases"][:, 0], 2 * result["edge_phases"][:, 0], rtol=0, atol=0)


@pytest.mark.parametrize("side", ["low", "high"])
def test_published_equality_counts_before_double_accumulator_reaches_bound(side):
    kc, dan = np.zeros((650, 1)), np.zeros((650, 1))
    if side == "high":
        initial = np.array([np.nextafter(np.float32(1.5), np.float32(0))], np.float32)
        delta, lag = 9e-8, -10.0
        kc_at, dan_at, bound, axis = 550, 500, 1.5, 1
    else:
        initial = np.array([np.nextafter(np.float32(0.5), np.float32(1))], np.float32)
        delta, lag = -4e-8, 10.0
        kc_at, dan_at, bound, axis = 500, 550, 0.5, 0
    kc[kc_at], dan[dan_at] = delta / kernel(lag), 1
    result = call(kc, dan, initial=initial)
    assert result["gains"][0] == bound
    assert 0.5 < result["double_gains"][0] < 1.5
    assert result["bound_counts"][axis, 0] >= 1
    assert abs(result["double_gains"][0] - float(initial[0]) - delta) < 1e-11


@pytest.mark.parametrize("bad", [np.nan, np.inf, -0.01, 1.01])
@pytest.mark.parametrize("which", ["kc", "dan"])
def test_invalid_impulse_mass_is_rejected_before_replay(bad, which):
    kc, dan = np.zeros((600, 1)), np.zeros((600, 1))
    (kc if which == "kc" else dan)[550] = bad
    with pytest.raises(ValueError):
        call(kc, dan)


@pytest.mark.parametrize(
    "change", ["shape", "length", "complex", "pk", "pc", "mask", "groups", "gains", "learning"]
)
def test_malformed_input_families_fail_closed(change):
    args = [
        np.zeros((600, 1)),
        np.zeros((600, 1)),
        np.array([0]),
        np.array([0]),
        np.array([True]),
        np.array([0]),
    ]
    kwargs = {}
    if change == "shape":
        args[0] = args[0].ravel()
    if change == "length":
        args[1] = args[1][:-1]
    if change == "complex":
        args[0] = args[0].astype(complex)
    if change == "pk":
        args[2] = np.array([0.5])
    if change == "pc":
        args[3] = np.array([1])
    if change == "mask":
        args[4] = np.array([2])
    if change == "groups":
        args[5] = np.array([-1])
    if change == "gains":
        kwargs["initial"] = np.array([1.6], np.float32)
    if change == "learning":
        kwargs["learning"] = 1
    with pytest.raises(ValueError):
        replay(*args, **kwargs)
