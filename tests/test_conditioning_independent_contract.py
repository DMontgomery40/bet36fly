"""Synthetic contract fixtures, derived without production/draft expected helpers."""

import copy
from dataclasses import replace
from bet36fly import conditioning as production
from collections import Counter

import numpy as np
import pytest

from conditioning_independent_contract import (
    ARMS,
    BRANCHES,
    CALL_FIELDS,
    assert_exact_plan,
    clone_fixture,
    expected_calls,
    independent_partition,
    score_acquisition,
    score_reversal,
)


PLAN = expected_calls()
REPRESENTATIVES = {}
for i, row in enumerate(PLAN):
    key = (row["stage"], row["kind"], row["arm"], row["branch"], row["replay_of"] is not None)
    REPRESENTATIVES.setdefault(key, i)


def plan_mutation(row, field):
    row = copy.deepcopy(row)
    if field == "stage":
        row[field] = "reversal" if row[field] != "reversal" else "acquisition-primary"
    elif field == "kind":
        row[field] = "train-cue" if row[field] != "train-cue" else "train-blank"
    elif field == "family":
        row[field] = "CD" if row[field] == "AB" else "AB"
    elif field in ("panel", "exposure", "seed"):
        row[field] = 1 if row[field] is None else row[field] + 1
    elif field == "arm":
        row[field] = "paired" if row[field] != "paired" else "untaught"
    elif field == "branch":
        row[field] = BRANCHES[0] if row[field] != BRANCHES[0] else BRANCHES[3]
    elif field == "checkpoint":
        row[field] = "wrong-checkpoint"
    elif field == "cue":
        row[field] = "B" if row[field] == "A" else "A"
    elif field == "duration_ms":
        row[field] = 800 if row[field] == 400 else 400
    elif field == "cue_window":
        row[field] = (10, 310)
    elif field == "plasticity":
        row[field] = not row[field]
    elif field == "teaching":
        row[field] = ((311, "home"),)
    return row


def test_exact_call_arithmetic_and_selected_replay_families():
    assert assert_exact_plan(PLAN)
    assert assert_exact_plan([row.json() for row in production.build_call_plan()])
    originals = [x for x in PLAN if x["replay_of"] is None]
    replays = [x for x in PLAN if x["replay_of"] is not None]
    assert len(originals) == 1600 and len(replays) == 32
    assert Counter(x["kind"] for x in originals) == {
        "unit-probe": 24,
        "train-cue": 480,
        "train-blank": 480,
        "interim-probe": 120,
        "endpoint-probe": 240,
        "parent-probe": 16,
        "train-reversal": 240,
    }
    assert Counter(x["kind"] for x in replays) == {
        "train-cue": 4,
        "train-blank": 4,
        "endpoint-probe": 12,
        "unit-probe": 2,
        "train-reversal": 10,
    }


@pytest.mark.parametrize("index", list(REPRESENTATIVES.values()))
@pytest.mark.parametrize("field", CALL_FIELDS)
def test_every_semantic_field_across_call_families_is_required(index, field):
    mutated = list(PLAN)
    mutated[index] = plan_mutation(PLAN[index], field)
    with pytest.raises(ValueError):
        assert_exact_plan(mutated)
    actual = production.build_call_plan()
    actual[index] = replace(actual[index], **{field: mutated[index][field]})
    with pytest.raises(ValueError):
        production.validate_call_plan(actual)


@pytest.mark.parametrize(
    "damage",
    [
        "omit",
        "duplicate",
        "extra",
        "swap",
        "wrong-replay",
        "forward-replay",
        "bool-seed",
        "numeric-plasticity",
    ],
)
def test_order_completeness_replay_and_types(damage):
    rows = copy.deepcopy(PLAN)
    if damage == "omit":
        rows.pop(30)
    elif damage == "duplicate":
        rows[30] = copy.deepcopy(rows[31])
    elif damage == "extra":
        rows.append(dict(rows[-1], id="unexpected"))
    elif damage == "swap":
        rows[30], rows[31] = rows[31], rows[30]
    elif damage == "wrong-replay":
        next(x for x in rows if x["replay_of"] is not None)["replay_of"] = rows[0]["id"]
    elif damage == "forward-replay":
        next(x for x in rows if x["replay_of"] is not None)["replay_of"] = rows[-1]["id"]
    elif damage == "bool-seed":
        rows[0]["seed"] = True
    else:
        rows[0]["plasticity"] = 0
    with pytest.raises(ValueError):
        assert_exact_plan(rows)


def test_disposable_replay_ancestry_and_acquired_parent_mapping():
    originals = {x["id"]: x for x in PLAN if x["replay_of"] is None}
    for row in PLAN:
        if row["replay_of"] is not None:
            original = originals[row["replay_of"]]
            if row["kind"] == "train-blank":
                assert row["input_checkpoint"].endswith("/replay-cue-0")
                assert original["input_checkpoint"].endswith("/cue-0")
            else:
                assert row["input_checkpoint"] == original["input_checkpoint"]
        if row["kind"] == "train-reversal" and row["exposure"] == 0:
            expected_panel = 0 if row["panel"] == 3_000_000 else 1_000_000
            assert row["input_checkpoint"] == f"AB/{expected_panel}/paired/blank-23"


def test_all_parent_and_unit_gates_precede_dependent_training():
    reversal_parent = [i for i, row in enumerate(PLAN) if row["kind"] == "parent-probe"]
    reversal_train = [i for i, row in enumerate(PLAN) if row["kind"] == "train-reversal"]
    assert len(reversal_parent) == 16
    assert max(reversal_parent) == 1257 and min(reversal_train) == 1258
    for stage in ("acquisition-primary", "acquisition-challenge"):
        unit = [i for i, row in enumerate(PLAN) if row["stage"] == stage and row["kind"] == "unit-probe"]
        training = [i for i, row in enumerate(PLAN) if row["stage"] == stage and row["kind"] == "train-cue"]
        assert len(unit) == 8 and max(unit) < min(training)


@pytest.mark.parametrize("duration,window", [(400, (0, 300)), (800, (300, 600))])
def test_raw_population_response_uses_exact_half_open_cue_window(duration, window):
    # Two sampled cells, one spike each at both included boundary-adjacent bins.
    # Excluded silent/pre/post spikes cannot change cue-window mean population Hz.
    trace = np.zeros((duration // 10, 2), dtype=np.int32)
    start, stop = window[0] // 10, window[1] // 10
    trace[start, :] = 1
    trace[stop - 1, :] = 1
    trace[stop, :] = 100
    if start:
        trace[start - 1, :] = 100
    expected = 4 / (2 * 0.3)
    observed = trace[start:stop, :].sum() / (2 * ((window[1] - window[0]) / 1000))
    assert observed == expected


@pytest.mark.parametrize("family", ["AB", "CD"])
@pytest.mark.parametrize("panel", [0, 1_000_000])
def test_acquisition_scalar_pulses_and_seed_extents(family, panel):
    for arm in ARMS:
        rows = [
            x
            for x in PLAN
            if x["family"] == family
            and x["panel"] == panel
            and x["arm"] == arm
            and x["kind"].startswith("train-")
            and x["replay_of"] is None
        ]
        assert len(rows) == 48
        assert [x["seed"] for x in rows] == list(range(42 + panel, 90 + panel))
        impulses = Counter()
        for x in rows:
            for _, pop in x["teaching"]:
                impulses[pop] += {"home": 2, "away": 22}[pop]
        assert impulses == ({"home": 96, "away": 1056} if arm in ARMS[:3] else {})


@pytest.mark.parametrize("panel", [3_000_000, 4_000_000])
def test_reversal_scalar_population_balance_and_per_cue_difference(panel):
    for branch in BRANCHES:
        rows = [
            x
            for x in PLAN
            if x["panel"] == panel
            and x["branch"] == branch
            and x["kind"] == "train-reversal"
            and x["replay_of"] is None
        ]
        assert len(rows) == 24
        assert [x["seed"] for x in rows] == list(range(42 + panel, 66 + panel))
        impulses = Counter()
        for x in rows:
            for _, pop in x["teaching"]:
                impulses[pop] += {"home": 2, "away": 22}[pop]
        assert impulses == ({"home": 192, "away": 2112} if branch in BRANCHES[:3] else {})
        if branch in BRANCHES[:3]:
            first = sum({"home": 2, "away": 22}[p] for _, p in rows[0]["teaching"])
            assert first == {BRANCHES[0]: 16, BRANCHES[1]: 176, BRANCHES[2]: 96}[branch]


def test_valid_acquisition_and_exact_threefold_strict_reversal_controls():
    f = clone_fixture()
    assert score_acquisition(f)
    assert score_reversal(f) == {"passed": True, "ordinary_remapping": True}


@pytest.mark.parametrize("panel", ["0", "1000000"])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("damage", ["wrong-sign", "target-unchanged", "nonfinite"])
def test_acquisition_per_seed_channel_panel_failures(panel, channel, seed, damage):
    f = clone_fixture()
    paired = f["acquisition"][panel]["paired"]
    unit = f["unit"]["responses"]
    paired["responses"][seed, channel, channel] = unit[seed, channel, channel] + (
        1 if damage == "wrong-sign" else 0
    )
    if damage == "nonfinite":
        paired["responses"][seed, channel, channel] = np.nan
        with pytest.raises(ValueError):
            score_acquisition(f)
    else:
        assert not score_acquisition(f)


@pytest.mark.parametrize("panel", ["0", "1000000"])
@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("bound", [0.5, 1.5, 0.49, 1.51])
def test_all_arms_and_panels_reject_exact_or_exceeded_end_bounds(panel, arm, bound):
    f = clone_fixture()
    f["acquisition"][panel][arm]["gains"][0] = bound
    with pytest.raises(ValueError):
        score_acquisition(f)


@pytest.mark.parametrize("null", ARMS[1:])
def test_each_acquisition_null_can_independently_break_ratio(null):
    f = clone_fixture()
    f["acquisition"]["0"][null]["responses"][:, 0, 0] = f["unit"]["responses"][:, 0, 0] - 1.00001
    assert not score_acquisition(f)


def test_response_ratio_uses_four_seed_mean_but_preserves_every_seed_sign():
    f = clone_fixture()
    f["acquisition"]["0"]["shuffled"]["responses"][:, 0, 0] = f["unit"]["responses"][:, 0, 0] - [
        2.0,
        0.0,
        0.0,
        0.0,
    ]
    assert score_acquisition(f)


@pytest.mark.parametrize("panel", ["3000000", "4000000"])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize(
    "damage", ["parent-lost", "recovery-zero", "farther-from-unit", "new-target-unchanged", "continued-flip"]
)
def test_reversal_every_seed_channel_panel_and_distinct_requirements(panel, channel, seed, damage):
    f = clone_fixture()
    old, new = channel, 1 - channel
    sr = f["finals"][panel][BRANCHES[2]]["responses"]
    pr = f["parents"][panel]["responses"]
    ur = f["unit"]["responses"]
    if damage == "parent-lost":
        pr[seed, old, channel] = ur[seed, old, channel]
    elif damage == "recovery-zero":
        sr[seed, old, channel] = pr[seed, old, channel]
    elif damage == "farther-from-unit":
        sr[seed, old, channel] = ur[seed, old, channel] + 5
    elif damage == "new-target-unchanged":
        sr[seed, new, channel] = pr[seed, new, channel]
    else:
        f["finals"][panel][BRANCHES[0]]["responses"][seed, old, channel] = ur[seed, old, channel] + 1
    assert not score_reversal(f)["passed"]


@pytest.mark.parametrize(
    "damage",
    ["response-only", "gain-only", "null-just-over", "wrong-parent", "frozen-byte", "ordinary-independent"],
)
def test_reversal_gain_lineage_boundary_and_independent_ordinary_classification(damage):
    f = clone_fixture()
    panel = "3000000"
    strict = f["finals"][panel][BRANCHES[2]]
    parent = f["parents"][panel]
    if damage == "response-only":
        strict["gains"] = parent["gains"].copy()
    elif damage == "gain-only":
        strict["responses"] = parent["responses"].copy()
    elif damage == "null-just-over":
        f["finals"][panel][BRANCHES[3]]["responses"][:, 0, 0] += 0.00001
    elif damage == "wrong-parent":
        strict["start_sha256"] = "0" * 64
    elif damage == "frozen-byte":
        f["finals"][panel][BRANCHES[4]]["gains"][0] = np.nextafter(np.float32(0.75), np.float32(1.0))
    else:
        # The strict branch can fail independently; ordinary remapping remains its own result.
        strict["responses"] = parent["responses"].copy()
        strict["gains"] = parent["gains"].copy()
        assert score_reversal(f)["ordinary_remapping"]
    assert not score_reversal(f)["passed"]


def test_partition_unweighted_counts_ties_and_empty_union():
    f = clone_fixture()
    p = f["partitions"]
    assert p["channels"]["home"]["first"].tolist() == [0, 1]
    assert p["channels"]["home"]["second"].tolist() == [2]
    assert all(x == 1 for rows in p["jaccard"]["within"] for x in rows)
    assert len(p["jaccard"]["between"]) == 16
    zeros = independent_partition(np.zeros((4, 2, 4), np.int32), p["pk"], p["pc"], p["mask"])
    assert not zeros["passed"] and zeros["jaccard"]["between"] == [1.0] * 16


def test_partition_pass_flag_is_not_evidence_and_shared_means_cannot_mask_weak_cue():
    f = clone_fixture()
    f["partitions"]["counts"][:] = 0
    f["partitions"]["passed"] = True
    assert not score_acquisition(f)
    assert not score_reversal(f)["passed"]


def test_unequal_preferred_edge_counts_use_means_not_sums():
    f = clone_fixture()
    # Target two edges decline .125 each; other one declines .1875.
    # Target sum -.25 is more negative; target mean -.125 is less negative and fails.
    f["acquisition"]["0"]["paired"]["gains"][:3] = [0.875, 0.875, 0.8125]
    assert not score_acquisition(f)


@pytest.mark.parametrize("stage", ["acquisition", "reversal"])
@pytest.mark.parametrize("panel_index", [0, 1])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("cue", [0, 1])
@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("direction", [-1, 1])
def test_frozen_same_seed_responses_are_exact_not_an_adjustable_tolerance(
    stage, panel_index, channel, cue, seed, direction
):
    f = clone_fixture()
    if stage == "acquisition":
        panel = ("0", "1000000")[panel_index]
        response = f["acquisition"][panel]["frozen"]["responses"]
    else:
        panel = ("3000000", "4000000")[panel_index]
        response = f["finals"][panel][BRANCHES[4]]["responses"]
    response[seed, cue, channel] = np.nextafter(
        response[seed, cue, channel], np.inf if direction == 1 else -np.inf
    )
    if stage == "acquisition":
        assert not score_acquisition(f)
    else:
        assert not score_reversal(f)["passed"]


@pytest.mark.parametrize("old_edges", [[0.6875, 0.8125], [0.875, 0.5625]])
def test_ordinary_remapping_allows_further_depression_and_heterogeneous_old_edges(old_edges):
    f = clone_fixture()
    for panel in f["finals"]:
        ordinary = f["finals"][panel][BRANCHES[1]]
        for ci in (0, 1):
            ordinary["responses"][:, ci, ci] = f["unit"]["responses"][:, ci, ci] - [5, 4, 6, 4.5]
            ordinary["responses"][:, 1 - ci, ci] = f["unit"]["responses"][:, 1 - ci, ci] - 8
        ordinary["gains"][[0, 1]] = old_edges
        ordinary["gains"][[4, 5]] = old_edges
    assert score_reversal(f)["ordinary_remapping"]


@pytest.mark.parametrize("panel", ["3000000", "4000000"])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("seed", range(4))
def test_partial_old_response_recovery_does_not_force_no_recovery_remapping_label(panel, channel, seed):
    f = clone_fixture()
    f["finals"][panel][BRANCHES[1]]["responses"][seed, channel, channel] += 0.125
    assert not score_reversal(f)["ordinary_remapping"]
