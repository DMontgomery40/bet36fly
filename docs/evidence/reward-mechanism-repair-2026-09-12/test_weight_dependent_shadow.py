"""Synthetic contract tests for the engineered changing-gain helper."""

import math

import numpy as np
import pytest

import weight_dependent_shadow as candidate


@pytest.mark.parametrize("initial", [0.5, 0.7, 1.0, 1.3, 1.5])
@pytest.mark.parametrize("p,n", [(0.0, 0.0), (2.0, 0.0), (0.0, 3.0), (2.0, 2.0), (3.0, 2.0)])
def test_continuously_changing_gain_and_separate_areas_match_constant_drive_solution(initial, p, n):
    duration = 20.0
    result = candidate.integrate_products(lambda _: (p, n), duration, initial)
    if p + n == 0:
        expected, positive, negative = initial, 0.0, 0.0
    else:
        decay = 0.001 * (p + n)
        equilibrium = 0.5 + p / (p + n)
        exposure = -math.expm1(-decay * duration) / decay
        expected = equilibrium + (initial - equilibrium) * math.exp(-decay * duration)
        positive = 0.001 * p * ((1.5 - equilibrium) * duration - (initial - equilibrium) * exposure)
        negative = -0.001 * n * ((equilibrium - 0.5) * duration + (initial - equilibrium) * exposure)
    assert abs(float(result["gain"]) - expected) < 1e-11
    assert abs(float(result["positive"]) - positive) < 2e-11
    assert abs(float(result["negative"]) - negative) < 2e-11
    assert abs(float(result["gain"]) - initial - float(result["positive"] + result["negative"])) < 2e-12


@pytest.mark.parametrize("initial", [-1, 0.499, 1.501, math.nan, math.inf, True, "1"])
def test_invalid_gain_cannot_be_clamped_or_coerced(initial):
    with pytest.raises(ValueError):
        candidate.integrate_products(lambda _: (1.0, 1.0), 0.2, initial)


@pytest.mark.parametrize("products", [(-1, 1), (1, -1), (math.nan, 1), (1, math.inf), (True, 1), ("1", 1)])
def test_invalid_product_drive_fails_without_hidden_flooring(products):
    with pytest.raises(ValueError):
        candidate.integrate_products(lambda _: products, 0.2, 1.0)


def test_vector_states_agree_with_distinct_initial_gain_analytic_solutions():
    initial = np.array([0.5, 0.9, 1.2, 1.5])
    result = candidate.integrate_products(lambda _: (np.array([1, 2, 3, 4]), 2.0), 2.0, initial)
    equilibrium = 0.5 + np.array([1, 2, 3, 4]) / np.array([3, 4, 5, 6])
    expected = equilibrium + (initial - equilibrium) * np.exp(-0.001 * np.array([3, 4, 5, 6]) * 2)
    np.testing.assert_allclose(result["gain"], expected, atol=1e-11, rtol=0)


def event_helper(kc, dan, end, initial=1.0, kw=None, dw=None):
    rk = ek = rd = ed = 0.0
    gain, positive, negative = initial, 0.0, 0.0
    kw = np.ones(len(kc)) if kw is None else kw
    dw = np.ones(len(dan)) if dw is None else dw
    knots = sorted({0.0, end, *kc, *dan})
    for i, left in enumerate(knots):
        rk += sum(w * 0.01 for t, w in zip(kc, kw) if t == left)
        rd += sum(w * 0.01 for t, w in zip(dan, dw) if t == left)
        if i + 1 < len(knots):
            value = candidate.interval(rk, ek, rd, ed, gain, knots[i + 1] - left)
            rk, ek, rd, ed = value["state"]
            gain = value["gain"]
            positive += value["positive"]
            negative += value["negative"]
    tail = candidate.interval(rk, ek, rd, ed, gain, math.inf)
    return dict(
        gain=tail["gain"],
        positive=positive + tail["positive"],
        negative=negative + tail["negative"],
        electrical_gain=gain,
        tail_positive=tail["positive"],
        tail_negative=tail["negative"],
    )


@pytest.mark.parametrize("initial", [0.7, 1.0, 1.3])
@pytest.mark.parametrize(
    "kc,dan", [([], []), ([0], []), ([], [0]), ([0], [0]), ([0], [20]), ([20], [0]), ([0, 1, 17], [2, 5, 50])]
)
def test_event_intervals_and_entire_tail_match_independent_superposition_ode(initial, kc, dan):
    from weight_state_reference import event_reference

    actual = event_helper(kc, dan, 50.0, initial)
    expected = event_reference(kc, dan, end_ms=50.0, initial_gain=initial)
    for key in actual:
        assert abs(float(actual[key]) - expected[key]) < (1e-11 if "gain" in key else 2e-11)


@pytest.mark.parametrize("end", [20.0, 40.0, 100.0])
def test_full_tail_has_no_finite_cutoff_or_electrical_partition_dependence(end):
    from weight_state_reference import mp_event_gain

    value = event_helper([0, 7, 20], [1, 20], end, 0.8, [2, 0.5, 1], [0.5, 0.5])
    expected = mp_event_gain(
        [0, 7, 20], [1, 20], end_ms=end, initial_gain=0.8, kc_weights=[2, 0.5, 1], dan_weights=[0.5, 0.5]
    )
    assert abs(float(value["gain"]) - float(expected)) < 1e-11


@pytest.mark.parametrize("bad", [-1.0, math.nan, math.inf, True, "1"])
@pytest.mark.parametrize("field", range(4))
def test_invalid_signal_states_fail_without_changing_gain(field, bad):
    states = [0.01, 0.1, 0.02, 0.2]
    states[field] = bad
    with pytest.raises(ValueError):
        candidate.interval(*states, 1.0, 0.2)


def raster_fixture():
    kc, dan = np.zeros((2000, 2), np.uint8), np.zeros((2000, 24), np.uint8)
    kc[[50, 499, 500, 640, 800, 1999], 0] = 1
    kc[[20, 500, 777, 1500], 1] = 1
    dan[[1, 499, 600, 900, 1999], 0] = 1
    dan[[600, 1100], 1] = 1
    dan[[650, 1000], 2:] = 1
    return [
        kc,
        dan,
        np.array([0, 1, 0, 1]),
        np.array([0, 0, 1, 1]),
        np.array([0, 0] + [1] * 22),
        np.array([1, 1, 1, 0], np.uint8),
        np.array([0, 3, 4, 7]),
    ]


def test_cold_onset_channel_normalization_and_tail_wrapper_match_independent_reference():
    from weight_state_reference import event_reference

    args = raster_fixture()
    initial = np.array([0.8, 1.0, 1.2, 1.1], np.float32)
    result = candidate.shadow(*args, initial=initial)
    kc, dan, pk, pc, dc, mask, _ = args
    for edge in range(4):
        if not mask[edge]:
            assert result["gains"][edge].tobytes() == initial[edge].tobytes()
            assert not result["phases"][:, edge].any()
            continue
        kt = np.flatnonzero(kc[500:, pk[edge]]) * 0.2
        rows, _ = np.nonzero(dan[500:, dc == pc[edge]])
        expected = event_reference(
            kt,
            rows * 0.2,
            end_ms=300.0,
            initial_gain=float(initial[edge]),
            dan_weights=np.full(len(rows), 1 / np.count_nonzero(dc == pc[edge])),
        )
        assert abs(result["double_gains"][edge] - expected["gain"]) < 1e-11
        assert abs(result["electrical_double_gains"][edge] - expected["electrical_gain"]) < 1e-11
        assert result["gains"][edge] == np.float32(expected["gain"])
        assert abs(result["phases"][:, edge, 0].sum() - expected["positive"]) < 2e-11
        assert abs(result["phases"][:, edge, 1].sum() - expected["negative"]) < 2e-11
    assert result["publication_counts"].tolist() == [1501, 1501, 1501, 0]


@pytest.mark.parametrize("learning", [False, True])
@pytest.mark.parametrize("eligible", [False, True])
def test_off_and_masked_gains_preserve_exact_checkpoint_bytes_without_mutating_inputs(learning, eligible):
    args = raster_fixture()
    args[5][:] = eligible
    initial = np.array([0.8, 1.0, 1.2, 1.1], np.float32)
    before = [a.tobytes() for a in args] + [initial.tobytes()]
    result = candidate.shadow(*args, initial=initial, learning=learning)
    assert before == [a.tobytes() for a in args] + [initial.tobytes()]
    if not learning or not eligible:
        assert result["gains"].tobytes() == initial.tobytes()
        assert not result["phases"].any() and not result["publication_counts"].any()


def test_pre_onset_history_is_excluded_and_checkpoint_resets_all_signals():
    args = raster_fixture()
    first = candidate.shadow(*args)
    args[0][:500] = 1
    args[1][:500] = 1
    second = candidate.shadow(*args)
    assert first["phases"].tobytes() == second["phases"].tobytes()
    assert first["gains"].tobytes() == second["gains"].tobytes()
    args[0][:] = 0
    args[1][:] = 0
    inherited = candidate.shadow(*args, initial=first["gains"])
    assert inherited["gains"].tobytes() == first["gains"].tobytes()
    assert not inherited["phases"].any()


def test_inclusive_bound_observations_use_each_full_step_and_one_whole_tail():
    args = raster_fixture()
    args[0][:] = 0
    args[1][:] = 0
    args[5][:] = 1
    value = candidate.shadow(*args, initial=np.array([0.5, 1.5, 1.0, 1.0], np.float32))
    assert value["phases"][:, 0, 5].tolist() == [150, 850, 500, 1]
    assert value["phases"][:, 1, 6].tolist() == [150, 850, 500, 1]
    assert not value["phases"][:, 2:, 5:7].any()


@pytest.mark.parametrize(
    "mutation", ["steps", "raster", "mask", "group_channel", "missing_channel", "initial64", "learning"]
)
def test_wrapper_rejects_malformed_schedule_mapping_and_checkpoint_contract(mutation):
    args = raster_fixture()
    kwargs = {}
    if mutation == "steps":
        args[0] = args[0][:-1]
    elif mutation == "raster":
        args[1][600, 0] = 2
    elif mutation == "mask":
        args[5][0] = 2
    elif mutation == "group_channel":
        args[6][0] = 4
    elif mutation == "missing_channel":
        args[4][:] = 1
    elif mutation == "initial64":
        kwargs["initial"] = np.ones(4, np.float64)
    else:
        kwargs["learning"] = "false"
    with pytest.raises(ValueError):
        candidate.shadow(*args, **kwargs)


def test_declared_gain_allowance_is_enclosed_outward_not_rounded_inward():
    from fractions import Fraction

    args = raster_fixture()
    args[0][:] = 0
    args[1][:] = 0
    args[5][:] = 1
    value = candidate.shadow(*args, initial=np.array([0.7, 0.8, 1.2, 1.3], np.float32))
    allowance = Fraction(1, 10**11)
    for g, lower, upper in zip(value["double_gains"], value["gain_lower"], value["gain_upper"]):
        assert Fraction(float(lower)) <= Fraction(float(g)) - allowance
        assert Fraction(float(upper)) >= Fraction(float(g)) + allowance


@pytest.mark.parametrize("initial", [0.5, 1.0, 1.5])
def test_nonconstant_products_use_changing_gain_at_substages(initial):
    from weight_state_reference import integrate_products

    def fn(t):
        return 2 + math.sin(t / 3), 3 + math.cos(t / 2)

    actual = candidate.integrate_products(fn, 8.0, initial)
    expected = integrate_products(fn, (0.0, 8.0), initial)
    for key in ("gain", "positive", "negative"):
        assert abs(float(actual[key]) - expected[key]) < 1e-11


@pytest.mark.parametrize("duration", [0.0, 0.2, 7.0, math.inf])
def test_interval_partition_and_input_vectors_are_preserved(duration):
    states = [np.array([0.01, 0.03]), np.array([0.1, 0.2]), np.array([0.04, 0.02]), np.array([0.4, 0.1])]
    gain = np.array([0.8, 1.2])
    before = [v.tobytes() for v in states] + [gain.tobytes()]
    full = candidate.interval(*states, gain, duration)
    first_h = 0.1 if math.isinf(duration) else duration / 3
    first = candidate.interval(*states, gain, first_h)
    second = candidate.interval(*first["state"], first["gain"], duration - first_h)
    np.testing.assert_allclose(full["gain"], second["gain"], atol=1e-11, rtol=0)
    for key in ("positive", "negative"):
        np.testing.assert_allclose(full[key], first[key] + second[key], atol=2e-11, rtol=0)
    assert before == [v.tobytes() for v in states] + [gain.tobytes()]


def test_all_eight_groups_and_shared_kcs_are_invariant_to_edge_and_dan_order():
    args = raster_fixture()
    args[2] = np.array([0, 1, 0, 1, 0, 1, 0, 1])
    args[3] = np.repeat([0, 1], 4)
    args[5] = np.ones(8, np.uint8)
    args[6] = np.arange(8)
    initial = np.array([0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.4], np.float32)
    value = candidate.shadow(*args, initial=initial)
    order = np.array([7, 3, 0, 4, 2, 6, 1, 5])
    for i in (2, 3, 5, 6):
        args[i] = args[i][order]
    args[1], args[4] = args[1][:, ::-1], args[4][::-1]
    other = candidate.shadow(*args, initial=initial[order])
    assert value["gains"][order].tobytes() == other["gains"].tobytes()
    np.testing.assert_array_equal(value["phases"][:, order], other["phases"])
    np.testing.assert_array_equal(value["grouped"], other["grouped"])


def test_refinement_work_guard_and_callback_fail_closed(monkeypatch):
    monkeypatch.setattr(candidate, "MAX_ATTEMPTS", 1)
    with pytest.raises(ArithmeticError, match="work limit"):
        candidate.integrate_products(lambda _: (1.0, 1.0), 1.0, 1.0)

    def stop():
        raise RuntimeError("synthetic cancellation")

    with pytest.raises(RuntimeError, match="synthetic cancellation"):
        candidate.interval(0.01, 0.1, 0.02, 0.2, 1.0, math.inf, guard=stop)


@pytest.mark.parametrize("learning", [False, True])
@pytest.mark.parametrize("enabled", [False, True])
def test_conditional_bound_counters_every_publication_without_changing_phase_schema(
    monkeypatch, learning, enabled
):
    # Consumer fixture isolates exact, allowance-only, and interior publication cases.
    # None of these imposed trajectories is a measured circuit history.
    low_next = float(np.nextafter(np.float32(0.5), np.float32(np.inf)))
    high_previous = float(np.nextafter(np.float32(1.5), np.float32(-np.inf)))
    target = np.array(
        [
            0.5,
            (0.5 + low_next) / 2 + 5e-12,
            low_next,
            1.0,
            high_previous,
            (1.5 + high_previous) / 2 - 5e-12,
            1.5,
        ]
    )

    def synthetic_interval(rk, ek, rd, ed, gain, duration, *, guard=None):
        delta = target - gain
        return dict(
            gain=target.copy(),
            positive=np.maximum(delta, 0),
            negative=np.minimum(delta, 0),
            estimated_error=np.zeros((3, 7)),
            accepted_substeps=1,
            attempted_substeps=1,
            state=(rk, ek, rd, ed),
        )

    monkeypatch.setattr(candidate, "interval", synthetic_interval)
    value = candidate.shadow(
        np.zeros((2000, 1), np.uint8),
        np.zeros((2000, 1), np.uint8),
        np.zeros(7, np.int32),
        np.zeros(7, np.int32),
        np.zeros(1, np.int32),
        np.full(7, enabled, np.uint8),
        np.zeros(7, np.int32),
        learning=learning,
    )
    expected = np.array([[1, 1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1, 1]]) * (
        1501 if learning and enabled else 0
    )
    np.testing.assert_array_equal(value["conditional_bound_counts"], expected)
    assert value["conditional_bound_counts"].dtype == np.dtype(np.int64)
    assert value["phases"].shape == (4, 7, 8)
    if learning and enabled:
        np.testing.assert_array_equal(
            value["phases"][:, :, 5:7].sum(axis=0),
            np.array([[1501, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 1501]]),
        )


@pytest.mark.parametrize("magnitude,duration", [(1e100, 1e220), (1e200, 1e120), (1e300, 1e20)])
@pytest.mark.parametrize("vector", [False, True])
def test_finite_product_accumulation_overflow_cannot_return_nonfinite_areas(magnitude, duration, vector):
    initial = np.ones(3) if vector else 1.0
    with np.errstate(all="ignore"), pytest.raises(ArithmeticError):
        candidate.integrate_products(lambda t: (magnitude, magnitude), duration, initial, max_step=duration)


@pytest.mark.parametrize("magnitude", [1e100, 1e200, 1e300])
def test_extreme_finite_product_with_finite_integral_remains_valid(magnitude):
    value = candidate.integrate_products(
        lambda t: (magnitude, magnitude), 1 / magnitude, 1.0, max_step=1 / magnitude
    )
    assert float(value["gain"]) == 1.0
    assert float(value["positive"]) == pytest.approx(0.0005, abs=1e-17)
    assert float(value["negative"]) == pytest.approx(-0.0005, abs=1e-17)
    assert np.isfinite(value["estimated_error"]).all()
