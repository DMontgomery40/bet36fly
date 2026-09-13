"""Runner contract/lifecycle fixtures are synthetic; no saved history is read."""

import copy
import importlib
import json
import socket
from pathlib import Path

import numpy as np
import pytest


def module():
    return importlib.import_module("run_darela_shadow")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No network in synthetic runner tests")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def inputs():
    m = dict(
        sample=np.arange(27, dtype=np.int32),
        body_ids=np.arange(100, 127, dtype=np.int64),
        kc_columns=np.array([0, 1], np.int32),
        dan_columns=np.arange(2, 26, dtype=np.int32),
        sensory_columns=np.array([26], np.int32),
        kc_indices=np.array([0, 1], np.int32),
        dan_indices=np.arange(2, 26, dtype=np.int32),
        sensory_indices=np.array([26], np.int32),
        dan_compartments=np.array([0] * 2 + [1] * 22, np.int32),
        plastic_kc_indices=np.array([0, 1, 0, 1], np.int32),
        plastic_compartments=np.array([0, 0, 1, 1], np.int32),
        plastic_groups=np.array([0, 1, 4, 5], np.int32),
        plastic_mask=np.array([1, 1, 1, 0], np.uint8),
    )
    return np.zeros((2000, 27), np.int32), np.ones(4, np.float32), np.zeros(4, np.float32), m


def plan(tmp_path):
    r = module()
    source = tmp_path / "synthetic-input.txt"
    source.write_text("immutable synthetic input")
    p = dict(
        schema=1,
        analysis=r.ANALYSIS,
        root=str(r.ROOT),
        output_root=str(tmp_path),
        wall_seconds_cap=1200,
        contract=copy.deepcopy(r.CONTRACT),
        expected_rows=r.reader.expected_rows(),
        capture_dir=str(tmp_path / "capture"),
        samples_path=str(tmp_path / "maps.npz"),
        run_dirs={name: str(tmp_path / name) for name in r.reader.RUNS},
        source_snapshot={},
        context_plan=str(source),
        preregistration=str(source),
        audit_contract=str(source),
        reviews=[str(source)],
        inputs=[r.binding(source)],
    )
    p["run_id"] = r.study_id(p)
    return p


def write_plan(tmp_path, p):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(p))
    out = tmp_path / p["run_id"] / "result"
    out.parent.mkdir()
    return path, out


def loader(p, store, guard):
    trace, original, delta, maps = inputs()

    def rows():
        for i, meta in enumerate(p["expected_rows"]):
            yield i, meta, trace.copy(), original.copy(), delta.copy(), None

    return maps, rows()


@pytest.fixture(scope="module")
def quiet_result():
    return module().evaluate_history(*inputs())


def quiet_evaluator(*args, invoke, **kwargs):
    # Runs the real frozen helpers on one synthetic history, then reuses its
    # arrays to exercise durable32-row orchestration without repeated numerics.
    data = quiet_evaluator.data
    invoke("release", lambda: None)
    invoke("bridge", lambda: None)
    return {k: v.copy() for k, v in data.items()}


@pytest.fixture
def ready_evaluator(quiet_result):
    quiet_evaluator.data = quiet_result
    return quiet_evaluator


@pytest.mark.parametrize("index", [0, 1, 15, 16, 30, 31])
@pytest.mark.parametrize("field", ["run_id", "game", "seed_set", "seed"])
def test_complete_selector_identity_family(tmp_path, index, field):
    r = module()
    p = plan(tmp_path)
    p["expected_rows"][index][field] = None
    p["run_id"] = r.study_id(p)
    with pytest.raises(ValueError):
        r.validate_plan(p)


@pytest.mark.parametrize(
    "change", ["short", "reverse", "duplicate", "float_seed", "cap", "parameters", "identity"]
)
def test_plan_order_typed_values_and_frozen_choices(tmp_path, change):
    r = module()
    p = plan(tmp_path)
    if change == "short":
        p["expected_rows"].pop()
    elif change == "reverse":
        p["expected_rows"].reverse()
    elif change == "duplicate":
        p["expected_rows"][1] = p["expected_rows"][0]
    elif change == "float_seed":
        p["expected_rows"][0]["seed"] = float(p["expected_rows"][0]["seed"])
    elif change == "cap":
        p["wall_seconds_cap"] = 1201
    elif change == "parameters":
        p["contract"]["tau_s"] = [7.5, 12.5, 900.0]
    p["run_id"] = r.study_id(p)
    if change == "identity":
        p["run_id"] += "wrong"
    with pytest.raises(ValueError):
        r.validate_plan(p)


def test_full_candidate_schema_and_unit_original_are_distinct():
    r = module()
    trace, original, delta, maps = inputs()
    trace[510, 0] = 1
    trace[550, 2:4] = 1
    original[0] = np.float32(0.9)
    delta = original - np.float32(1)
    value = r.evaluate_history(trace, original, delta, maps)
    r.validate_result(value, maps)
    assert value["gains"][0] != original[0]
    np.testing.assert_array_equal(value["original_gains"], original)
    np.testing.assert_array_equal(value["initial_gains"], np.ones(4, np.float32))
    assert value["per_cell_release"].shape == (2000, 24)
    assert value["state_before"].shape == (2000, 24, 3)
    assert value["endpoint_state"].shape == (24, 3)
    assert value["gains"][3].tobytes() == np.float32(1).tobytes()


@pytest.mark.parametrize(
    "key",
    [
        "gains",
        "state_before",
        "pooled_release",
        "edge_phases",
        "endpoint_dan",
        "bound_counts",
        "raw_dan_events",
    ],
)
@pytest.mark.parametrize("change", ["missing", "dtype", "nonfinite"])
def test_result_inventory_dtype_and_nonfinite_family(quiet_result, key, change):
    r = module()
    v = {k: x.copy() for k, x in quiet_result.items()}
    if change == "missing":
        v.pop(key)
    elif change == "dtype":
        v[key] = v[key].astype(np.float32 if v[key].dtype != np.float32 else np.float64)
    else:
        v[key] = v[key].astype(np.float64)
        v[key].flat[0] = np.nan
    with pytest.raises(ValueError):
        r.validate_result(v, inputs()[3])


@pytest.mark.parametrize(
    "change",
    [
        "silent_release",
        "negative_state",
        "phase_order",
        "pooling",
        "masked_gain",
        "published",
        "tail_count",
        "bound_count",
        "map",
        "original_delta",
    ],
)
def test_semantic_result_corruption_families(quiet_result, change):
    r = module()
    v = {k: x.copy() for k, x in quiet_result.items()}
    if change == "silent_release":
        v["per_cell_release"][500, 0] = 1
    elif change == "negative_state":
        v["state_before"][0, 0, 0] = -1
    elif change == "phase_order":
        v["state_after"][0, 0, 0] = 1.1
    elif change == "pooling":
        v["pooled_release"][0, 0] = 1
    elif change == "masked_gain":
        v["gains"][3] = np.nextafter(np.float32(1), np.float32(2))
    elif change == "published":
        v["edge_phases"][0, 0, 4] = 2**-24
    elif change == "tail_count":
        v["publication_counts"][3, 0] = 0
    elif change == "bound_count":
        v["bound_counts"][0, 0] = 1
    elif change == "map":
        v["map__body_ids"][0] += 1
    else:
        v["original_gain_delta"][0] = 0.1
    with pytest.raises(ValueError):
        r.validate_result(v, inputs()[3])


def test_helper_input_mutation_rejected(monkeypatch):
    r = module()
    real = r.release_events

    def mutate(spikes, comp):
        value = real(spikes, comp)
        spikes[0, 0] = 1
        return value

    monkeypatch.setattr(r, "release_events", mutate)
    with pytest.raises(ValueError, match="mutat"):
        r.evaluate_history(*inputs())


def test_complete32_cases_exact_guard_cells_and_no_overwrite(tmp_path, ready_evaluator):
    r = module()
    p = plan(tmp_path)
    path, out = write_plan(tmp_path, p)
    result = r.execute(path, out, _loader=loader, _evaluator=ready_evaluator, _check_runtime=False)
    assert result["status"] == "completed" and result["completed"] == 32
    assert result["invocations"] == {"release": 32, "bridge": 32}
    summary = r.validate_saved(out, p)
    assert len(summary["candidate_guards"]) == len(summary["original_guards"]) == 8
    assert all(x["passed"] for x in summary["candidate_guards"].values())
    assert summary["screen"] == "pending_independent_audit"
    with pytest.raises(FileExistsError):
        r.execute(path, out, _loader=loader, _check_runtime=False)


@pytest.mark.parametrize("stage", ["input", "row", "summary", "completion", "final_hash"])
def test_failure_preserves_partial_and_never_completes(tmp_path, ready_evaluator, monkeypatch, stage):
    r = module()
    p = plan(tmp_path)
    path, out = write_plan(tmp_path, p)
    real = r.reader.atomic_json
    if stage == "input":
        Path(p["inputs"][0]["path"]).write_text("changed")
    elif stage in ("row", "summary", "completion"):
        target = {"row": "case_01.json", "summary": "summary.json", "completion": "completion.json"}[stage]

        def fail(path, value):
            if Path(path).name == target:
                raise OSError("synthetic persistence failure")
            return real(path, value)

        monkeypatch.setattr(r.reader, "atomic_json", fail)
    else:
        original_verify = r.reader.BoundInputs.verify
        calls = [0]

        def fail_last(self):
            calls[0] += 1
            if calls[0] == 2:
                raise ValueError("final source mutation")
            return original_verify(self)

        monkeypatch.setattr(r.reader.BoundInputs, "verify", fail_last)
    value = r.execute(path, out, _loader=loader, _evaluator=ready_evaluator, _check_runtime=False)
    assert value["status"] != "completed"
    assert (out / "terminal-error.json").is_file()
    with pytest.raises(ValueError):
        r.validate_saved(out, p)
    if stage == "row":
        assert value["completed"] == 1 and (out / "case_00.npz").is_file()
    if stage == "input":
        assert value["invocations"] == {"release": 0, "bridge": 0}


@pytest.mark.parametrize("stage", ["before_call", "summary", "completion"])
def test_deadline_at_each_terminal_boundary_invalidates_success(
    tmp_path, ready_evaluator, monkeypatch, stage
):
    r = module()
    p = plan(tmp_path)
    path, out = write_plan(tmp_path, p)
    now = [0.0]
    real = r.reader.atomic_json

    def clock():
        return now[0]

    def advance(path, value):
        real(path, value)
        target = {"before_call": "status.json", "summary": "summary.json", "completion": "completion.json"}[
            stage
        ]
        if Path(path).name == target:
            now[0] = 1200.0

    monkeypatch.setattr(r.reader, "atomic_json", advance)
    value = r.execute(
        path, out, _loader=loader, _evaluator=ready_evaluator, _check_runtime=False, clock=clock
    )
    assert value["status"] == "budget_stopped"
    with pytest.raises(ValueError):
        r.validate_saved(out, p)
    if stage == "completion":
        error = json.loads((out / "terminal-error.json").read_text())
        assert error["invalidated_completion_sha256"] == r.reader.sha(out / "completion.json")


def test_saved_truncation_hash_and_missing_row_rejected(tmp_path, ready_evaluator):
    r = module()
    p = plan(tmp_path)
    path, out = write_plan(tmp_path, p)
    assert (
        r.execute(path, out, _loader=loader, _evaluator=ready_evaluator, _check_runtime=False)["status"]
        == "completed"
    )
    target = out / "case_00.npz"
    original = target.read_bytes()
    target.write_bytes(original[:50])
    with pytest.raises(ValueError):
        r.validate_saved(out, p)
    target.write_bytes(original)
    (out / "case_31.json").unlink()
    with pytest.raises(ValueError):
        r.validate_saved(out, p)


def test_guard_reports_trial_sum_units_and_sample_sd():
    r = module()
    m = inputs()[3]
    rows = []
    for i, meta in enumerate(r.reader.expected_rows()):
        candidate = np.ones(4, np.float32)
        candidate[:2] = np.float32(1 + (i // 2 % 8 - 3.5) / 32)
        rows.append(dict(metadata=meta, gains=candidate, original_gains=np.ones(4, np.float32)))
    guards = r.guard_summary(rows, m, "gains")
    key = f"{r.reader.RUNS[0]}/base/home"
    g = guards[key]
    expected = np.array([(i - 3.5) / 16 for i in range(8)])
    assert g["mean"] == float(expected.mean())
    assert g["sample_sd"] == float(expected.std(ddof=1))
    assert g["limit"] == float(expected.std(ddof=1)) * 0.5
    assert g["ticks"] == [int(x * 2**24) for x in expected]
    assert g["passed"] is True
    assert r.guard_summary(rows, m, "original_gains")[key]["ticks"] == [0] * 8


@pytest.mark.parametrize(
    "change",
    [
        "summary_status",
        "summary_count",
        "screen",
        "provisional",
        "completion_count",
        "journal_short",
        "journal_order",
        "journal_link",
    ],
)
def test_rehashed_false_completion_contract(tmp_path, ready_evaluator, change):
    r = module()
    p = plan(tmp_path)
    path, out = write_plan(tmp_path, p)
    assert (
        r.execute(path, out, _loader=loader, _evaluator=ready_evaluator, _check_runtime=False)["status"]
        == "completed"
    )
    completion = json.loads((out / "completion.json").read_text())
    if change.startswith("journal"):
        records = [json.loads(x) for x in (out / "attempts.jsonl").read_text().splitlines()]
        if change == "journal_short":
            records.pop()
        elif change == "journal_order":
            records[0], records[1] = records[1], records[0]
        else:
            records[4]["detail"]["sha256"] = "a" * 64
        (out / "attempts.jsonl").write_text("".join(json.dumps(x) + "\n" for x in records))
    elif change == "completion_count":
        completion["completed"] = 31
    else:
        summary = json.loads((out / "summary.json").read_text())
        field, value = {
            "summary_status": ("status", "failed"),
            "summary_count": ("completed", 31),
            "screen": ("screen", "passed_necessary_untaught_screen"),
            "provisional": ("provisional", "rejected_fixed_hypothesis"),
        }[change]
        if field == "provisional":
            field = "provisional_screen"
        summary[field] = value
        (out / "summary.json").write_text(json.dumps(summary))
    completion["bindings"] = [r.binding(x["path"]) for x in completion["bindings"]]
    (out / "completion.json").write_text(json.dumps(completion))
    with pytest.raises(ValueError):
        r.validate_saved(out, p)


def comparator_fixture():
    trace, original, delta, m = inputs()
    trace[501, 0] = 1
    trace[503, 2] = 1
    s = dict(steps=2000, coarse_steps=50, nk=2, nd=24, ns=1, n=27, ne=4, ng=8, populations=[2, 22])
    fine = dict(
        counts=trace.sum(0, dtype=np.int32),
        rates=np.zeros(27, np.float32),
        rates_hz=np.zeros(27, np.float32),
        voltage=np.zeros(27, np.float32),
        trace=trace,
        population=trace.sum(1, dtype=np.int32),
        dan_counts=trace[:, 2:26].sum(0, dtype=np.int32),
        compartment_dan_counts=np.array([1, 0], np.int32),
        compartment_tonic_hz=np.zeros(2, np.float32),
        gains=original,
        gain_delta=delta,
        pulse_times_ms=np.empty(0, np.float32),
        pulse_dan_indices=np.empty(0, np.int32),
    )
    bins = trace.reshape(40, 50, 27).sum(1, dtype=np.int32)
    signals = np.zeros((2000, 5), np.float32)
    signals[:, 0] = trace[:, :2].sum(1)
    signals[:, 1] = trace[:, 2:4].sum(1) / 2
    main = dict(
        step_signals=signals,
        dan_bins=bins[:, 2:26],
        sensory_bins=bins[:, 26:],
        gains=original.copy(),
        gain_delta=delta.copy(),
    )
    return fine, main, m, s


@pytest.mark.parametrize(
    "change",
    [
        None,
        "trace_dtype",
        "nonbinary",
        "map_width",
        "map_order",
        "original_ulp",
        "delta",
        "pulse",
        "fingerprint_counts",
        "population",
        "main_kc",
        "main_pool",
        "dan_bins",
        "sensory_bins",
        "unused",
    ],
)
def test_comparator_identity_dtype_count_and_gain_family(change):
    r = module()
    fine, main, m, s = comparator_fixture()
    if change == "trace_dtype":
        fine["trace"] = fine["trace"].astype(np.int64)
    elif change == "nonbinary":
        fine["trace"][0, 0] = 2
    elif change == "map_width":
        m["sample"] = m["sample"].astype(np.int64)
    elif change == "map_order":
        m["kc_columns"] = m["kc_columns"][::-1].copy()
    elif change == "original_ulp":
        main["gains"][0] = np.nextafter(np.float32(1), np.float32(2))
    elif change == "delta":
        fine["gain_delta"][0] = 0.01
    elif change == "pulse":
        fine["pulse_times_ms"] = np.array([310], np.float32)
    elif change == "fingerprint_counts":
        fine["counts"][0] += 1
    elif change == "population":
        fine["population"][0] = 1
    elif change == "main_kc":
        main["step_signals"][0, 0] = 1
    elif change == "main_pool":
        main["step_signals"][0, 1] = 0.5
    elif change == "dan_bins":
        main["dan_bins"][0, 0] = 1
    elif change == "sensory_bins":
        main["sensory_bins"][0, 0] = 1
    elif change == "unused":
        main["step_signals"][0, 3] = 1
    if change is None:
        r.validate_comparator(fine, main, m, s)
    else:
        with pytest.raises(ValueError):
            r.validate_comparator(fine, main, m, s)


def test_guard_rejection_still_persists_all32_trials(tmp_path):
    r = module()
    trace, original, delta, m = inputs()
    trace[510, 0] = 1
    trace[550, 2:4] = 1
    effect = r.evaluate_history(trace, original, delta, m)

    def evaluate(*args, invoke, **kwargs):
        invoke("release", lambda: None)
        invoke("bridge", lambda: None)
        return {k: v.copy() for k, v in effect.items()}

    p = plan(tmp_path)
    path, out = write_plan(tmp_path, p)
    result = r.execute(path, out, _loader=loader, _evaluator=evaluate, _check_runtime=False)
    assert result["completed"] == 32 and result["invocations"] == dict(release=32, bridge=32)
    summary = r.validate_saved(out, p)
    assert summary["provisional_screen"] == "rejected_fixed_hypothesis"
    assert sum(not x["passed"] for x in summary["candidate_guards"].values()) == 4
    assert len(list(out.glob("case_*.npz"))) == 32


@pytest.mark.parametrize(
    "target,field,value",
    [
        ("status", "invocations", dict(release=32.0, bridge=32)),
        ("status", "returned", dict(release=32, bridge=32.0)),
        ("status", "wall_seconds", False),
        ("completion", "elapsed_through_summary", False),
        ("summary", "native_calls", False),
        ("summary", "network_calls", 0.0),
        ("row", "index", False),
    ],
)
def test_terminal_scalars_preserve_types(tmp_path, ready_evaluator, target, field, value):
    r = module()
    p = plan(tmp_path)
    path, out = write_plan(tmp_path, p)
    assert (
        r.execute(path, out, _loader=loader, _evaluator=ready_evaluator, _check_runtime=False)["status"]
        == "completed"
    )
    name = {"row": "case_00", "status": "status", "completion": "completion", "summary": "summary"}[
        target
    ] + ".json"
    obj = json.loads((out / name).read_text())
    obj[field] = value
    (out / name).write_text(json.dumps(obj))
    if target == "row":
        records = [json.loads(x) for x in (out / "attempts.jsonl").read_text().splitlines()]
        records[4]["detail"] = r.binding(out / name)
        (out / "attempts.jsonl").write_text("".join(json.dumps(x) + "\n" for x in records))
    completion = json.loads((out / "completion.json").read_text())
    completion["bindings"] = [r.binding(x["path"]) for x in completion["bindings"]]
    (out / "completion.json").write_text(json.dumps(completion))
    with pytest.raises(ValueError):
        r.validate_saved(out, p)
