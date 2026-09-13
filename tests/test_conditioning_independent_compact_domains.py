"""Necessary retained count constraints; no raw trajectory reconstruction."""

from copy import deepcopy
import numpy as np
import pytest
from bet36fly import conditioning as c, conditioning_runner as r
from test_conditioning_runner import inputs, result_fixture


def fixture():
    prepared = inputs()
    row = c.build_call_plan()[0]
    before = np.ones(6, np.float32)
    return row, prepared, before, r.compact_result(row, prepared, result_fixture(row, before, prepared))


@pytest.mark.parametrize(
    "damage",
    [
        "cue_steps",
        "trial_steps",
        "sample_population",
        "zero_population",
        "tonic_zero_dans",
        "population_bin_steps",
    ],
)
def test_contradictory_compact_counts_are_rejected(damage):
    row, prepared, before, value = fixture()
    a = prepared["arrays"]
    i = int(np.searchsorted(a["sample"], a["output_home"][0]))
    if damage == "cue_steps":
        value["cue_counts"][i] = 1501
        value["sample_counts"][i] = 1501
    if damage == "trial_steps":
        value["sample_counts"][i] = 2001
    if damage == "sample_population":
        value["sample_counts"][i] = 1000
    if damage == "zero_population":
        value["population"][:] = 0
    if damage == "tonic_zero_dans":
        value["compartment_tonic_hz"][:] = 100
    if damage == "population_bin_steps":
        value["population"][0] = prepared["neurons"] * 50 + 1
    with pytest.raises(ValueError):
        r.validate_compact(row, prepared, before, value)


@pytest.mark.parametrize("whole_steps", [1500, 2000])
@pytest.mark.parametrize("extra_unrecorded_spikes", [0, 1, 20])
def test_exact_count_ceiling_and_unrecorded_population_contributions_are_valid(
    whole_steps, extra_unrecorded_spikes
):
    row, prepared, before, value = fixture()
    for name in (
        "cue_counts",
        "sample_counts",
        "population",
        "dan_counts",
        "compartment_dan_counts",
        "compartment_tonic_hz",
    ):
        value[name][:] = 0
    i = int(np.searchsorted(prepared["arrays"]["sample"], prepared["arrays"]["output_home"][0]))
    value["cue_counts"][i] = 1500
    value["sample_counts"][i] = whole_steps
    value["population"][: whole_steps // 50] = 50
    if extra_unrecorded_spikes:
        # A separate input model samples only a strict subset of neurons.
        prepared = deepcopy(prepared)
        prepared["neurons"] += 1
        value["population"][-1] += extra_unrecorded_spikes
    assert r.validate_compact(row, prepared, before, value)["electrical_bound_observations"] == 0
