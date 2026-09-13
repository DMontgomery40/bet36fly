"""Synthetic event-transfer tests; no source solver or saved raster imports."""

import math

import numpy as np
import pytest

from darela_release import release_events


def fixture(steps=2000):
    return np.zeros((steps, 24), dtype=np.int32), np.array([0] * 2 + [1] * 22, dtype=np.int32)


@pytest.mark.parametrize("steps", [0, 1, 499, 500, 501, 2000])
def test_silence_never_emits_and_preserves_rest(steps):
    spikes, compartments = fixture(steps)
    result = release_events(spikes, compartments)
    shapes = {
        "per_cell_release": (steps, 24),
        "pooled_release": (steps, 2),
        "state_before": (steps, 24, 3),
        "state_after": (steps, 24, 3),
        "endpoint_state": (24, 3),
    }
    assert set(result) == set(shapes)
    for name, shape in shapes.items():
        assert result[name].shape == shape
        assert result[name].dtype == np.float64
        np.testing.assert_array_equal(result[name], 0 if "release" in name else 1)


@pytest.mark.parametrize("cell", [0, 1, 2, 23])
@pytest.mark.parametrize("step", [0, 499, 500, 1999])
def test_first_actual_event_is_unit_mass_then_source_euler_kick(cell, step):
    spikes, compartments = fixture()
    spikes[step, cell] = 1
    result = release_events(spikes, compartments)
    assert result["per_cell_release"][step, cell] == 1.0
    assert np.count_nonzero(result["per_cell_release"]) == 1
    np.testing.assert_array_equal(result["state_before"][step, cell], [1, 1, 1])
    np.testing.assert_array_equal(result["state_after"][step, cell], [1.0105, 0.997, 0.9989])
    expected = 1 / (2 if cell < 2 else 22)
    assert result["pooled_release"][step, compartments[cell]] == expected
    assert result["pooled_release"][:, 1 - compartments[cell]].sum() == 0


@pytest.mark.parametrize("first,gap", [(0, 1), (0, 11), (17, 50), (499, 1), (400, 1100), (0, 1999)])
def test_exact_gap_seconds_and_pre_event_readout(first, gap):
    spikes, compartments = fixture()
    spikes[[first, first + gap], 0] = 1
    result = release_events(spikes, compartments)
    pre = np.array(
        [
            1 + p * math.exp(-gap / 5000 / tau)
            for p, tau in zip((0.0105, -0.003, -0.0011), (7.5, 15, 900), strict=True)
        ]
    )
    np.testing.assert_allclose(result["state_before"][first + gap, 0], pre, atol=2e-15, rtol=2e-15)
    assert result["per_cell_release"][first + gap, 0] == pytest.approx(math.prod(pre), abs=2e-15)
    # Literal source post-H amplitude divided by fixed prod(q) is the chosen pre-H mass.
    post = result["state_after"][first + gap, 0]
    assert math.prod(post) / math.prod((1.0105, 0.997, 0.9989)) == pytest.approx(math.prod(pre), abs=2e-15)
    endpoint = 1 + (post - 1) * np.exp(-((2000 - first - gap) / 5000) / np.array([7.5, 15, 900]))
    np.testing.assert_allclose(result["endpoint_state"][0], endpoint, atol=2e-15, rtol=2e-15)


def test_pre_onset_events_change_release_at_onset_without_new_tail_events():
    spikes, compartments = fixture()
    spikes[[0, 500], 0] = 1
    result = release_events(spikes, compartments)
    assert result["per_cell_release"][500, 0] > 1
    assert np.count_nonzero(result["per_cell_release"][501:]) == 0
    assert 1 < result["endpoint_state"][0, 0] < result["state_after"][500, 0, 0]
    assert result["state_after"][500, 0, 1] < result["endpoint_state"][0, 1] < 1


def test_per_cell_transform_cannot_be_replaced_by_transform_of_pooled_counts():
    repeated, compartments = fixture(12)
    alternating = repeated.copy()
    repeated[[0, 11], 0] = 1
    alternating[0, 0] = alternating[11, 1] = 1
    np.testing.assert_array_equal(repeated.sum(axis=1), alternating.sum(axis=1))
    a = release_events(repeated, compartments)
    b = release_events(alternating, compartments)
    assert b["pooled_release"][11, 0] == 0.5
    assert a["pooled_release"][11, 0] > b["pooled_release"][11, 0]
    np.testing.assert_array_equal(a["pooled_release"][:, 1], b["pooled_release"][:, 1])


def test_reset_deterministic_input_immutable_and_returned_state_not_shared():
    spikes, compartments = fixture(73)
    spikes[::11, 0] = spikes[1::7, 23] = 1
    saved_spikes, saved_compartments = spikes.copy(), compartments.copy()
    a = release_events(spikes, compartments)
    b = release_events(spikes, compartments)
    for key in a:
        np.testing.assert_array_equal(a[key], b[key])
        assert not np.shares_memory(a[key], b[key])
    a["endpoint_state"].fill(-1)
    c = release_events(spikes, compartments)
    for key in b:
        np.testing.assert_array_equal(b[key], c[key])
    np.testing.assert_array_equal(spikes, saved_spikes)
    np.testing.assert_array_equal(compartments, saved_compartments)


@pytest.mark.parametrize("seed", [4, 13, 98])
def test_body_permutation_carries_channel_and_state_and_simultaneous_events_commute(seed):
    spikes, compartments = fixture(151)
    rng = np.random.default_rng(seed)
    spikes[:] = rng.random(spikes.shape) < 0.1
    order = rng.permutation(24)
    a = release_events(spikes, compartments)
    b = release_events(spikes[:, order], compartments[order])
    np.testing.assert_array_equal(a["per_cell_release"][:, order], b["per_cell_release"])
    for key in ("state_before", "state_after"):
        np.testing.assert_array_equal(a[key][:, order], b[key])
    np.testing.assert_array_equal(a["endpoint_state"][order], b["endpoint_state"])
    np.testing.assert_allclose(a["pooled_release"], b["pooled_release"], rtol=2e-15, atol=2e-15)


def test_entire_2000_binary_event_extreme_is_positive_finite_without_clipping():
    spikes, compartments = fixture()
    spikes[:] = 1
    result = release_events(spikes, compartments)
    for value in result.values():
        assert np.isfinite(value).all()
        assert (value > 0).all()
    assert result["per_cell_release"][-1, 0] > 1000  # excludes saturation at one or a small arbitrary cap
    assert result["state_after"][-1, 0, 0] <= 1.0105**2000
    np.testing.assert_allclose(result["pooled_release"][:, 0], result["pooled_release"][:, 1], rtol=2e-15)


@pytest.mark.parametrize(
    "dtype", [bool, np.int8, np.int16, np.int64, np.uint32, np.float32, np.float64, complex, object]
)
def test_rejects_wrong_raster_width_or_non_integer_contract(dtype):
    spikes, compartments = fixture(1)
    with pytest.raises(ValueError):
        release_events(spikes.astype(dtype), compartments)


@pytest.mark.parametrize("shape", [(24,), (1, 23), (1, 25), (1, 24, 1), (2001, 24)])
def test_rejects_incomplete_or_out_of_domain_raster_shape(shape):
    with pytest.raises(ValueError):
        release_events(np.zeros(shape, dtype=np.int32), fixture(1)[1])


@pytest.mark.parametrize("value", [-1, 2, 2147483647])
def test_rejects_non_binary_actual_event_values(value):
    spikes, compartments = fixture(1)
    spikes[0, 0] = value
    with pytest.raises(ValueError):
        release_events(spikes, compartments)


@pytest.mark.parametrize(
    "case",
    ["list", "int64", "float", "bool", "short", "rank", "negative", "unknown", "one_home", "three_home"],
)
def test_rejects_bad_compartment_identity_or_population(case):
    spikes, compartments = fixture(1)
    if case == "list":
        compartments = compartments.tolist()
    elif case in ("int64", "float", "bool"):
        compartments = compartments.astype({"int64": np.int64, "float": float, "bool": bool}[case])
    elif case == "short":
        compartments = compartments[:-1]
    elif case == "rank":
        compartments = compartments[None, :]
    elif case == "negative":
        compartments[0] = -1
    elif case == "unknown":
        compartments[0] = 2
    elif case == "one_home":
        compartments[0] = 1
    else:
        compartments[2] = 0
    with pytest.raises(ValueError):
        release_events(spikes, compartments)


@pytest.mark.parametrize("name", ["p", "tau_s"])
@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        [1, 2],
        [[1, 2, 3]],
        [True, 2, 3],
        ["1", "2", "3"],
        [complex(1), 2, 3],
        [float("nan"), 2, 3],
        [float("inf"), 2, 3],
        [-float("inf"), 2, 3],
        [0, 0, 0],
    ],
)
def test_rejects_malformed_or_unfrozen_parameters(name, bad):
    spikes, compartments = fixture(1)
    with pytest.raises(ValueError):
        release_events(spikes, compartments, **{name: bad})


@pytest.mark.parametrize(
    "name,values",
    [
        ("p", [0.010500000000000002, -0.003, -0.0011]),
        ("tau_s", [7.5, 12.5, 900]),
        ("tau_s", [7500, 15000, 900000]),
    ],
)
def test_rejects_retuning_example_row_or_millisecond_tau(name, values):
    with pytest.raises(ValueError):
        release_events(*fixture(1), **{name: values})


def test_explicit_frozen_parameters_equal_default_and_no_label_argument():
    spikes, compartments = fixture(2)
    spikes[:] = 1
    a = release_events(spikes, compartments)
    b = release_events(spikes, compartments, p=[0.0105, -0.003, -0.0011], tau_s=np.array([7.5, 15.0, 900.0]))
    for key in a:
        np.testing.assert_array_equal(a[key], b[key])
    with pytest.raises(TypeError):
        release_events(spikes, compartments, teaching=True)
