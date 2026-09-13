"""Adversarial checks against the actual production validation API, no engine calls."""

import copy

import numpy as np
import pytest

from bet36fly.conditioning import compare_numeric_results, validate_gain_evidence, validate_numeric_result
from conditioning_independent_numeric_probes import numeric_fixture, review_cases


@pytest.mark.parametrize("case", review_cases(), ids=lambda x: x["case"])
def test_source_derived_valid_and_invalid_native_return_cases(case):
    assert case["actual_acceptance"] == case["expected_acceptance"], case


@pytest.mark.parametrize("duration", [400, 800])
@pytest.mark.parametrize("record", [False, True])
@pytest.mark.parametrize("plasticity", [False, True])
def test_valid_complete_return_variants(duration, record, plasticity):
    result, before, schema, kwargs = numeric_fixture(duration=duration, record=record, plasticity=plasticity)
    validate_numeric_result(result, schema)
    assert validate_gain_evidence(result, before, schema, **kwargs) == {
        "electrical_bound_observations": 0,
        "tail_bound_observations": 0,
    }
    duplicate = copy.deepcopy(result)
    duplicate["wall_seconds"] += 1
    assert compare_numeric_results(result, duplicate, schema=schema)["passed"]


ARRAYS = (
    "counts",
    "rates",
    "rates_hz",
    "voltage",
    "trace",
    "population",
    "dan_counts",
    "compartment_dan_counts",
    "compartment_tonic_hz",
    "gains",
    "gain_delta",
    "pulse_times_ms",
    "pulse_dan_indices",
)


@pytest.mark.parametrize("field", ARRAYS)
@pytest.mark.parametrize("damage", ["missing", "list", "dtype", "shape"])
def test_all_top_level_numeric_result_families_are_required_and_typed(field, damage):
    result, _, schema, _ = numeric_fixture()
    if damage == "missing":
        del result[field]
    elif damage == "list":
        result[field] = result[field].tolist()
    elif damage == "dtype":
        result[field] = result[field].astype(np.float64)
    else:
        result[field] = result[field].reshape((1,) + result[field].shape)
    with pytest.raises(ValueError):
        validate_numeric_result(result, schema)
    with pytest.raises(ValueError):
        compare_numeric_results(result, copy.deepcopy(result), schema=schema)


REC_ARRAYS = (
    "signal_bins",
    "kc_signal_bins",
    "step_signals",
    "bridge_signals",
    "bridge_kc_bins",
    "bridge_kc_used",
    "bridge_rule",
    "bridge_tail",
    "plastic_groups",
    "plastic_compartments",
)


@pytest.mark.parametrize("field", REC_ARRAYS)
@pytest.mark.parametrize("damage", ["missing", "object", "shape", "nonfinite"])
def test_every_recorded_numerical_family_is_complete(field, damage):
    result, _, schema, _ = numeric_fixture()
    rec = result["instrumentation"]
    if damage == "missing":
        del rec[field]
    elif damage == "object":
        rec[field] = rec[field].astype(object)
    elif damage == "shape":
        rec[field] = rec[field][:-1]
    elif rec[field].dtype.kind == "f":
        rec[field].flat[0] = np.inf
    else:
        rec[field] = rec[field].astype(float)
        rec[field].flat[0] = np.nan
    with pytest.raises(ValueError):
        validate_numeric_result(result, schema)


@pytest.mark.parametrize("phase", ["bridge_rule", "bridge_tail"])
@pytest.mark.parametrize("side", [5, 6])
@pytest.mark.parametrize("count", [1.0, 0.5, -1.0, np.nan, np.inf])
def test_all_electrical_tail_inclusive_bound_evidence_is_nonnegative_integral_and_zero_for_pass(
    phase, side, count
):
    result, before, schema, kwargs = numeric_fixture()
    array = result["instrumentation"][phase]
    row = array[10, 0] if array.ndim == 3 else array[0]
    row[side] = count
    with pytest.raises(ValueError):
        validate_gain_evidence(result, before, schema, **kwargs)


@pytest.mark.parametrize("when", ["before", "after"])
@pytest.mark.parametrize("edge", range(6))
@pytest.mark.parametrize("value", [0.5, 1.5, 0.49, 1.51])
def test_all_initial_and_final_edges_reject_inclusive_end_bounds(when, edge, value):
    result, before, schema, kwargs = numeric_fixture()
    target = before if when == "before" else result["gains"]
    target[edge] = value
    result["gain_delta"] = result["gains"] - before
    with pytest.raises(ValueError):
        validate_gain_evidence(result, before, schema, **kwargs)


@pytest.mark.parametrize("edge", range(6))
@pytest.mark.parametrize("frozen", [False, True])
def test_masked_or_frozen_byte_change_rejected_even_with_matching_endpoint_delta(edge, frozen):
    result, before, schema, kwargs = numeric_fixture(plasticity=not frozen)
    if not frozen:
        kwargs["mask"][edge] = 0
    result["gains"][edge] = np.nextafter(np.float32(1), np.float32(1.5))
    result["gain_delta"] = result["gains"] - before
    with pytest.raises(ValueError):
        validate_gain_evidence(result, before, schema, **kwargs)
