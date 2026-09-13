"""Frozen-doc conditioning oracles; all numerical inputs are synthetic."""

from dataclasses import replace
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

from bet36fly import conditioning as c


def test_frozen_plan_matches_every_row_and_exact_stage_arithmetic():
    plan = c.build_call_plan()
    assert c.validate_call_plan(plan)["by_stage"] == {
        "acquisition-primary": 616,
        "acquisition-challenge": 616,
        "reversal": 400,
    }
    assert len(plan) == 1632 and sum(r.replay_of is not None for r in plan) == 32


@pytest.mark.parametrize("family", ["training", "probe", "replay", "frozen", "reversal"])
@pytest.mark.parametrize(
    "damage", ["seed", "window", "plasticity", "teaching", "checkpoint", "order", "identity"]
)
def test_complete_ordered_call_contract_rejects_mutation_families(family, damage):
    plan = c.build_call_plan()
    select = {
        "training": lambda r: r.kind == "train-cue" and r.replay_of is None,
        "probe": lambda r: r.kind == "endpoint-probe" and r.replay_of is None,
        "replay": lambda r: r.replay_of is not None,
        "frozen": lambda r: r.arm == "frozen",
        "reversal": lambda r: r.kind == "train-reversal" and r.replay_of is None,
    }[family]
    idx = next(i for i, r in enumerate(plan) if select(r))
    row = plan[idx]
    if damage == "seed":
        plan[idx] = replace(row, seed=row.seed + 1)
    if damage == "window":
        plan[idx] = replace(row, cue_window=(10, 310))
    if damage == "plasticity":
        plan[idx] = replace(row, plasticity=not row.plasticity)
    if damage == "teaching":
        plan[idx] = replace(row, teaching=() if row.teaching else ((310, "home"),))
    if damage == "checkpoint":
        plan[idx] = replace(row, checkpoint="unrelated-checkpoint")
    if damage == "order":
        plan[idx], plan[idx + 1] = plan[idx + 1], plan[idx]
    if damage == "identity":
        plan[idx] = replace(row, replay_of=plan[0].id if row.replay_of != plan[0].id else plan[1].id)
    with pytest.raises(ValueError):
        c.validate_call_plan(plan)


@pytest.mark.parametrize(
    "field,value",
    [("hard_wall_seconds", 1199), ("effect_ratio", 2.99), ("max_between_jaccard", 0.51), ("cues", {})],
)
def test_frozen_spec_rejects_all_configuration_changes(field, value):
    spec = c.conditioning_spec()
    spec[field] = value
    with pytest.raises(ValueError):
        c.build_call_plan(spec)


@pytest.mark.parametrize(
    "first,second",
    [
        ({}, {}),
        ({"counts": np.zeros(2, int)}, {"counts": np.zeros(2, int)}),
        ({"instrumentation": {}}, {"instrumentation": {}}),
    ],
)
def test_absent_or_partial_numerical_replay_evidence_never_passes(first, second):
    with pytest.raises(ValueError):
        c.compare_numeric_results(first, second)


def test_historical_draft_demonstrates_plan_and_replay_failures_without_modification():
    p = (
        Path(__file__).resolve().parents[1]
        / "docs/evidence/reward-mechanism-repair-2026-09-12/conditioning-paused-draft.py"
    )
    spec = importlib.util.spec_from_file_location("historical_conditioning_draft", p)
    old = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = old
    spec.loader.exec_module(old)
    plan = old.build_call_plan()
    damaged = [replace(r, teaching=()) for r in plan]
    assert old.validate_call_plan(damaged)["calls"] == 1632
    assert old.compare_numeric_results({}, {})["passed"] is True


def _probe_contract(family="AB", *, reversal=False):
    return dict(
        family=family,
        duration_ms=800 if reversal else 400,
        cue_window=[300, 600] if reversal else [0, 300],
        seeds=list(range(5_000_042, 5_000_046)) if reversal else list(range(2_000_042, 2_000_046)),
    )


def endpoint(responses, gains, *, family="AB", reversal=False, start=None, hits=0):
    return dict(
        responses=np.array(responses, float),
        gains=np.array(gains, np.float32),
        bound_hits=hits,
        probe_contract=_probe_contract(family, reversal=reversal),
        start_sha256=start,
    )


def acquisition_fixture(family="AB"):
    responses = np.array(
        [[[20, 30], [22, 32]], [[21, 31], [23, 33]], [[22, 32], [24, 34]], [[23, 33], [25, 35]]], float
    )
    counts = np.array([[[2, 1, 0, 0], [0, 0, 2, 1]]] * 4, np.int32)
    # Includes excluded edge6: every arm must retain its unit byte.
    partitions = c.partition_kcs(
        counts,
        np.array([0, 1, 2, 0, 2, 3, 1]),
        np.array([0, 0, 0, 1, 1, 1, 1]),
        np.array([1, 1, 1, 1, 1, 1, 0], np.uint8),
    )
    unit = endpoint(responses, np.ones(7), family=family)
    arms = {}
    for panel in ("0", "1000000"):
        arms[panel] = {name: endpoint(responses, np.ones(7), family=family) for name in c.ACQUISITION_ARMS}
        arms[panel]["paired"] = endpoint(
            responses + np.array([[[-3, 0], [0, -4]]] * 4), [0.7, 0.8, 1, 1, 0.75, 0.85, 1], family=family
        )
        arms[panel]["shuffled"] = endpoint(
            responses + np.array([[[-0.2, 0], [0, -0.2]]] * 4), [0.98, 1, 1, 1, 0.98, 1, 1], family=family
        )
    return unit, arms, partitions


@pytest.mark.parametrize("family", ["AB", "CD"])
def test_valid_acquisition_fixture_passes_all_channel_panel_seed_requirements(family):
    assert c.evaluate_acquisition(*acquisition_fixture(family))["all_passed"]


@pytest.mark.parametrize("panel", ["0", "1000000"])
@pytest.mark.parametrize("arm", c.ACQUISITION_ARMS)
@pytest.mark.parametrize(
    "damage",
    [
        "lower",
        "upper",
        "lower_exact",
        "upper_exact",
        "masked",
        "probe_seed",
        "probe_window",
        "probe_duration",
    ],
)
def test_acquisition_gain_and_probe_identity_families_override_stored_flags(panel, arm, damage):
    unit, endpoints, partitions = acquisition_fixture()
    value = endpoints[panel][arm]
    if damage in ("lower", "upper", "lower_exact", "upper_exact"):
        value["gains"][0] = {"lower": 0.49, "upper": 1.51, "lower_exact": 0.5, "upper_exact": 1.5}[damage]
    if damage == "masked":
        value["gains"][-1] = 0.9
    if damage == "probe_seed":
        value["probe_contract"]["seeds"][0] += 1
    if damage == "probe_window":
        value["probe_contract"]["cue_window"] = [300, 600]
    if damage == "probe_duration":
        value["probe_contract"]["duration_ms"] = 800
    assert not c.evaluate_acquisition(unit, endpoints, partitions)["all_passed"]


@pytest.mark.parametrize("panel", ["0", "1000000"])
@pytest.mark.parametrize("edge", range(7))
def test_frozen_gain_changes_fail_for_every_edge_even_without_bound_flags(panel, edge):
    unit, endpoints, partitions = acquisition_fixture()
    endpoints[panel]["frozen"]["gains"][edge] = 0.99
    assert not c.evaluate_acquisition(unit, endpoints, partitions)["all_passed"]


@pytest.mark.parametrize("damage", ["passed", "indices", "counts", "ratio", "epsilon"])
def test_partition_and_thresholds_cannot_be_asserted_or_repartitioned(damage):
    unit, endpoints, partitions = acquisition_fixture()
    kwargs = {}
    if damage == "passed":
        partitions = c.partition_kcs(
            np.zeros((4, 2, 4), np.int32),
            np.array([0, 1, 2, 0, 2, 3, 1]),
            np.array([0, 0, 0, 1, 1, 1, 1]),
            np.ones(7, np.uint8),
        )
        partitions["passed"] = True
    if damage == "indices":
        partitions["channels"]["home"]["first"] = np.array([2])
    if damage == "counts":
        partitions["source_counts"][:] = 0
    if damage == "ratio":
        kwargs["effect_ratio"] = 0
    if damage == "epsilon":
        kwargs["replay_error"] = -100
    assert not c.evaluate_acquisition(unit, endpoints, partitions, **kwargs)["all_passed"]


def reversal_fixture():
    from conditioning_independent_contract import clone_fixture

    f = clone_fixture()
    p = f["partitions"]
    f["partitions"] = c.partition_kcs(p["counts"], p["pk"], p["pc"], p["mask"])
    for endpoint in [
        f["unit"],
        *f["parents"].values(),
        *[v for panel in f["finals"].values() for v in panel.values()],
    ]:
        endpoint["probe_contract"] = _probe_contract(reversal=True)
    return f


def _reverse(f):
    return c.evaluate_reversal(f["unit"], f["parents"], f["finals"], f["partitions"], f["starts"])


def test_reversal_exact_threefold_positive_recovery_is_valid():
    assert _reverse(reversal_fixture())["all_passed"]


def test_reversal_new_response_ratio_uses_four_seed_mean_and_every_seed_sign():
    f = reversal_fixture()
    for branches in f["finals"].values():
        # Mean recovery control remains1, but first-seed new-association null contrast is4.
        branches["untaught-exposure"]["responses"][0, 1, 0] -= 3
        branches["untaught-exposure"]["responses"][1, 1, 0] += 3
    assert _reverse(f)["all_passed"]


def test_remapping_is_ordinary_swap_and_requires_both_panels():
    f = reversal_fixture()
    for branches in f["finals"].values():
        branches["backward-erasure-plus-swap"]["responses"] = branches["frozen-retention"]["responses"].copy()
    r = _reverse(f)
    assert not r["all_passed"] and r["classification"] == "dual-channel-preference-remapping-without-erasure"
    f["finals"]["4000000"]["ordinary-contingency-swap"]["responses"] = f["parents"]["4000000"][
        "responses"
    ].copy()
    assert _reverse(f)["classification"] == "failed"


@pytest.mark.parametrize("reversal", [False, True])
@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("cue,channel", [(0, 0), (0, 1), (1, 0), (1, 1)])
def test_frozen_response_disagreement_is_evidence_failure(reversal, seed, cue, channel):
    if reversal:
        f = reversal_fixture()
        f["finals"]["3000000"]["frozen-retention"]["responses"][seed, cue, channel] += 0.01
        assert not _reverse(f)["all_passed"]
    else:
        u, e, p = acquisition_fixture()
        e["0"]["frozen"]["responses"][seed, cue, channel] += 0.01
        assert not c.evaluate_acquisition(u, e, p)["all_passed"]


@pytest.mark.parametrize("value", [400.0, True, "400", None])
def test_probe_duration_requires_literal_integer(value):
    u, e, p = acquisition_fixture()
    u["probe_contract"]["duration_ms"] = value
    assert not c.evaluate_acquisition(u, e, p)["all_passed"]
