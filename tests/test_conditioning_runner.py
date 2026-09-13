"""Deterministic fake-engine execution and a tiny non-MaleCNS schema fixture."""

from copy import deepcopy

import numpy as np
import pytest

from bet36fly import conditioning as c
from bet36fly import conditioning_runner as r
from bet36fly.conditioning_artifacts import strict_json


def inputs():
    a = dict(
        kc=np.arange(2, 6, dtype=np.int32),
        sensory=np.arange(2, dtype=np.int32),
        dans=np.arange(6, 30, dtype=np.int32),
        dcomp=np.array([0] * 2 + [1] * 22, np.int32),
        edges=np.arange(6, dtype=np.int64),
        pk=np.array([0, 1, 2, 0, 2, 3], np.int32),
        pc=np.array([0, 0, 0, 1, 1, 1], np.int32),
        mask=np.ones(6, np.uint8),
        groups=np.array([0, 0, 0, 4, 4, 4], np.int32),
        output_home=np.array([30], np.int32),
        output_away=np.array([31], np.int32),
        sample=np.arange(32, dtype=np.int32),
    )
    for i, key in enumerate("ABCD", 1):
        a["cue_" + key] = np.array([i, 0], np.float32)
    return dict(neurons=32, learning_rule="rate-bridge-v1", arrays=a)


def result_fixture(row, before, prepared, *, after=None):
    a = prepared["arrays"]
    schema = r.numeric_schema(row, prepared)
    b, t = schema.bins, schema.steps
    n = schema.neurons
    result = dict(
        counts=np.zeros(n, np.int32),
        rates=np.zeros(n, np.float32),
        rates_hz=np.zeros(n, np.float32),
        voltage=np.zeros(n, np.float32),
        trace=np.zeros((b, len(a["sample"])), np.int32),
        population=np.zeros(b, np.int32),
        dan_counts=np.zeros(24, np.int32),
        compartment_dan_counts=np.zeros(2, np.int32),
        compartment_tonic_hz=np.zeros(2, np.float32),
        gains=before.copy() if after is None else after.copy(),
        gain_delta=np.zeros(len(before), np.float32),
        pulse_times_ms=np.array([x[0] for x in schema.pulses], np.float32),
        pulse_dan_indices=np.array([x[1] for x in schema.pulses], np.int32),
        duration_ms=float(row.duration_ms),
        dt=0.2,
        bin_ms=10.0,
        wall_seconds=0.001,
        instrumentation=None,
    )
    if row.cue:
        qi = c.FAMILIES[row.family].index(row.cue)
        lo = row.cue_window[0] // 10
        result["trace"][lo, a["kc"][[0, 1] if qi == 0 else [2, 3]]] = [2, 1]
        for ci, ch in enumerate(c.CHANNELS):
            edges = ([0, 1] if qi == 0 else [2]) if ci == 0 else ([3] if qi == 0 else [4, 5])
            total = int(round(64 * np.mean(result["gains"][edges]))) + row.seed % 4
            result["trace"][lo, a["output_" + ch]] = min(total, 50)
            result["trace"][lo + 1, a["output_" + ch]] = max(total - 50, 0)
    result["counts"] = result["trace"].sum(0, dtype=np.int32)
    result["population"] = result["trace"].sum(1, dtype=np.int32)
    result["rates"] = result["counts"].astype(np.float32) * (1000 / row.duration_ms)
    result["rates_hz"] = result["rates"].copy()
    result["gain_delta"] = result["gains"] - before
    if schema.record:
        rec = dict(
            signal_bins=np.zeros((b, 2, 4), np.float64),
            kc_signal_bins=np.zeros((b, 2), np.float64),
            step_signals=np.zeros((t, 5), np.float32),
            plastic_groups=a["groups"].copy(),
            bridge_signals=np.zeros((t, 2, 2), np.float64),
            bridge_kc_bins=np.zeros((b, 4, 2), np.float64),
            bridge_kc_used=np.zeros((t, 8, 2), np.float64),
            bridge_rule=np.zeros((t, 8, 8), np.float64),
            bridge_tail=np.zeros((8, 8), np.float64),
            plastic_compartments=a["pc"].copy(),
            learning_rule="rate-bridge-v1",
            layout_version="rate-bridge-v1/1",
            event_rule_applicable=False,
            layout=c.recording_layout("rate-bridge-v1"),
            config=dict(
                h_ms=0.2,
                tau_ms=500.0,
                rate_tau_ms=100.0,
                effective_eta=0.0005 if row.plasticity else 0.0,
                normalization=0.96,
                tail="analytic_no_new_event_tail",
                checkpoint="float32; double remainder discarded",
            ),
        )
        for group in range(8):
            change = (result["gains"].astype(np.float64) - before)[a["groups"] == group].sum()
            rec["bridge_rule"][-1, group, :5] = [max(change, 0), min(change, 0), change, change, change]
        result["instrumentation"] = rec
    return result


class FakeEngine:
    def __init__(self, prepared, *, fail_at=None, corrupt_at=None):
        self.prepared = prepared
        self.rows = c.build_call_plan()
        self.calls = []
        self.gains = np.ones(6, np.float32)
        self.fail_at = fail_at
        self.corrupt_at = corrupt_at

    def run(self, rates, **kwargs):
        pos = len(self.calls)
        row = self.rows[pos]
        before = self.gains.copy()
        # Every disposable native input is independent of the retained before copy.
        self.calls.append(dict(position=pos, before=before, rates=rates.copy(), kwargs=deepcopy(kwargs)))
        if pos == self.fail_at:
            raise RuntimeError("synthetic native failure")
        after = before.copy()
        if row.kind.startswith("train-") and row.exposure == 23 and row.plasticity:
            if row.stage != "reversal":
                target = {
                    "paired": 0.8125,
                    "shuffled": 0.9375,
                    "timing-unpaired": 0.96875,
                    "untaught": 0.984375,
                }[row.arm]
                after[[0, 1, 4, 5]] = target
            else:
                old, new = {
                    "continued-acquisition": (0.71875, 1.0),
                    "ordinary-contingency-swap": (0.8125, 0.625),
                    "backward-erasure-plus-swap": (0.953125, 0.625),
                    "untaught-exposure": (0.859375, 1.0),
                }[row.branch]
                after[[0, 1, 4, 5]] = old
                after[[2, 3]] = new
        self.gains = after.copy()
        result = result_fixture(row, before, self.prepared, after=after)
        if pos == self.corrupt_at:
            result.pop("voltage")
        return result


def execute(tmp_path, **kwargs):
    prepared = inputs()
    engine = FakeEngine(prepared, **kwargs)
    manifest = r._execute(tmp_path, {"bindings": []}, prepared, lambda: engine)
    directory = tmp_path / "output/experiments" / manifest["id"]
    return manifest, strict_json((directory / "ledger.json").read_bytes()), engine, directory


def test_complete_fake_matrix_canonical_replay_and_gate_state_transitions(tmp_path):
    manifest, ledger, engine, directory = execute(tmp_path)
    assert manifest["status"] == "completed", manifest.get("error")
    assert manifest["conditioning"]["calls"]["actual"] == 1632
    assert len(engine.calls) == 1632 and len(ledger["attempts"]) == 1632
    assert [j["completed"] for j in manifest["jobs"]] == [616, 616, 400]
    assert all(v["all_passed"] for v in ledger["verdicts"].values())
    assert sum("result" in a for a in ledger["attempts"]) == 64
    assert sum(a["call"]["replay_of"] is not None for a in ledger["attempts"]) == 32
    assert all("fingerprints" in a and "compact" in a for a in ledger["attempts"])
    assert sum(p.stat().st_size for p in directory.iterdir()) < 50 * 1024 * 1024


@pytest.mark.parametrize("position", [0, 7, 8, 10, 615, 616, 1232, 1257, 1258, 1631])
@pytest.mark.parametrize("failure", ["exception", "malformed"])
def test_every_stage_call_failure_is_durable_counted_and_never_resumed(tmp_path, position, failure):
    manifest, ledger, engine, directory = execute(
        tmp_path, **{"fail_at" if failure == "exception" else "corrupt_at": position}
    )
    assert manifest["status"] == "failed"
    assert manifest["conditioning"]["calls"]["actual"] == position + 1
    assert ledger["attempts"][-1]["invoked"] is True and ledger["attempts"][-1]["status"] == "failed"
    assert len(engine.calls) == position + 1
    previous = (directory / "ledger.json").read_bytes()
    with pytest.raises(FileExistsError):
        execute(tmp_path)
    assert (directory / "ledger.json").read_bytes() == previous


def test_failed_real_pair_rejected_before_factory_or_input_preparation(monkeypatch, tmp_path):
    from bet36fly import reward_evidence

    monkeypatch.setattr(
        reward_evidence,
        "list_reward_evidence",
        lambda root: dict(
            qualification_pairs=[
                dict(pair_id="failed-pair", validation_status="validated", evidence_status="failed")
            ]
        ),
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Engine/preparation must not be reached")

    monkeypatch.setattr(r, "prepare_inputs", forbidden)
    with pytest.raises(r.GateFailed):
        r.run_conditioning(tmp_path, "failed-pair", engine_factory=forbidden)
    assert not (tmp_path / "output/experiments").exists()


@pytest.mark.parametrize("status", ["missing", "stored-only", "invalid", "failed", "mixed"])
def test_qualification_failure_family_never_constructs_engine(monkeypatch, tmp_path, status):
    from bet36fly import reward_evidence

    pairs = (
        []
        if status == "missing"
        else [dict(pair_id="pair", validation_status=status, evidence_status="passed")]
    )
    monkeypatch.setattr(reward_evidence, "list_reward_evidence", lambda _: dict(qualification_pairs=pairs))
    with pytest.raises(r.GateFailed):
        r.run_conditioning(tmp_path, "pair", engine_factory=lambda *_: pytest.fail("engine created"))


@pytest.mark.parametrize("after_calls", [0, 1, 8, 12])
@pytest.mark.parametrize("stop", ["cancelled", "budget_stopped"])
def test_pre_and_post_call_caps_and_cancellation_preserve_known_counts(tmp_path, after_calls, stop):
    prepared = inputs()
    engine = FakeEngine(prepared)

    def cancelled():
        return stop == "cancelled" and len(engine.calls) >= after_calls

    def clock():
        return 1200.0 if stop == "budget_stopped" and len(engine.calls) >= after_calls else 0.0

    result = r._execute(
        tmp_path, {"bindings": []}, prepared, lambda: engine, cancelled=cancelled, clock=clock, started=0.0
    )
    assert result["status"] == stop
    assert result["conditioning"]["calls"]["actual"] == after_calls
    assert result["conditioning"]["calls"]["returned"] == after_calls
    assert result["conditioning"]["calls"]["completed"] == max(0, after_calls - 1)
    assert len(engine.calls) == after_calls


def test_persistence_failure_before_invocation_is_not_counted_as_a_native_call(tmp_path, monkeypatch):
    append = r.append_attempt
    failed = False

    def fail_once(path, event):
        nonlocal failed
        value = strict_json(event)
        if value["status"] == "intent" and not value["invoked"] and not failed:
            failed = True
            raise OSError("synthetic durable intent failure")
        return append(path, event)

    monkeypatch.setattr(r, "append_attempt", fail_once)
    m, ledger, engine, _ = execute(tmp_path)
    assert m["status"] == "failed" and not engine.calls
    assert m["conditioning"]["calls"]["actual"] == 0 and m["conditioning"]["calls"]["ambiguous"] == 0
    assert ledger["attempts"][0]["status"] == "failed" and ledger["attempts"][0]["invoked"] is False


def test_probe_replay_buffers_are_nonaliasing_even_for_mutate_then_restore(tmp_path, monkeypatch):
    states = []
    original_init = r.EvidenceState.__init__
    original_run = FakeEngine.run

    def capture(state, prepared):
        original_init(state, prepared)
        states.append(state)

    def spy(engine, rates, **kwargs):
        state = states[0]
        retained = [state.unit, *state.canonical.values(), *[x["before"] for x in state.originals.values()]]
        snapshots = [v.tobytes() for v in retained]
        assert all(not np.shares_memory(engine.gains, v) for v in retained)
        old = engine.gains.copy()
        engine.gains[0] = 0.9
        assert [v.tobytes() for v in retained] == snapshots
        engine.gains[:] = old
        return original_run(engine, rates, **kwargs)

    monkeypatch.setattr(r.EvidenceState, "__init__", capture)
    monkeypatch.setattr(FakeEngine, "run", spy)
    m, _, engine, _ = execute(tmp_path, fail_at=12)
    assert len(engine.calls) == 13 and m["status"] == "failed"


@pytest.mark.parametrize("row_index", [0, 8, 1258, 1587])
def test_tiny_non_malecns_native_contract_and_exact_replay(row_index):
    from bet36fly.reward_brain import RewardEngine

    a = dict(
        kc=np.array([0, 1], np.int32),
        sensory=np.array([0, 1], np.int32),
        dans=np.array([2, 3], np.int32),
        dcomp=np.array([0, 1], np.int32),
        edges=np.array([0, 1], np.int64),
        pk=np.array([0, 1], np.int32),
        pc=np.array([0, 1], np.int32),
        mask=np.ones(2, np.uint8),
        groups=np.array([0, 4], np.int32),
        sample=np.arange(6, dtype=np.int32),
        output_home=np.array([4], np.int32),
        output_away=np.array([5], np.int32),
    )
    for key, rate in zip("ABCD", ([100, 0], [0, 100], [50, 0], [0, 50])):
        a["cue_" + key] = np.array(rate, np.float32)
    prepared = dict(neurons=6, learning_rule="rate-bridge-v1", arrays=a)
    engine = RewardEngine(
        np.array([0, 1, 2, 2, 2, 2, 2], np.int64),
        np.array([4, 5], np.int32),
        np.ones(2, np.float32),
        a["sensory"],
        a["kc"],
        a["dans"],
        a["dcomp"],
        a["edges"],
        a["pk"],
        a["pc"],
        n_compartments=2,
        tau_ms=500.0,
        learning_rate=0.0005,
        gain_bounds=(0.5, 1.5),
        plasticity_onset_ms=100.0,
        dan_baseline_window_ms=50.0,
        dan_reference="none",
        learning_rule="rate-bridge-v1",
        rate_tau_ms=100.0,
        plastic_mask=a["mask"],
    )
    row = c.build_call_plan()[row_index]
    rates, pulses = r.schedules(row, prepared)
    before = engine.gains.copy()
    results = []
    for _ in range(2):
        engine.gains = before.copy()
        result = engine.run(
            rates,
            bin_ms=10,
            teaching_pulses=pulses,
            seed=row.seed,
            plasticity=row.plasticity,
            sample=a["sample"],
            record=row.kind.startswith("train-"),
            plastic_groups=a["groups"],
            n_groups=8,
        )
        r.validate_call_result(row, prepared, before, result)
        r.validate_compact(row, prepared, before, r.compact_result(row, prepared, result))
        c.validate_fingerprints(c._numeric_identities(result), r.numeric_schema(row, prepared))
        results.append(result)
    assert c.compare_numeric_results(*results, schema=r.numeric_schema(row, prepared))["passed"]


@pytest.mark.parametrize(
    "stage,expected", [("acquisition-primary", 8), ("acquisition-challenge", 624), ("reversal", 1258)]
)
def test_entire_shared_unit_or_parent_gate_precedes_any_dependent_training(
    tmp_path, monkeypatch, stage, expected
):
    original = result_fixture

    def changed(row, before, prepared, **kwargs):
        result = original(row, before, prepared, **kwargs)
        if row.stage == stage:
            if stage != "reversal" and row.kind == "unit-probe":
                result["trace"][:, prepared["arrays"]["kc"]] = 0
                result["trace"][0, prepared["arrays"]["kc"]] = 1
            elif (
                stage == "reversal"
                and row.kind == "parent-probe"
                and row.panel == 4_000_000
                and row.seed == 5_000_045
            ):
                ci = c.FAMILIES["AB"].index(row.cue)
                ids = prepared["arrays"]["output_" + c.CHANNELS[ci]]
                lo = row.cue_window[0] // 10
                result["trace"][lo, ids] = 50
                result["trace"][lo + 1, ids] = 14 + row.seed % 4
            result["counts"] = result["trace"].sum(0, dtype=np.int32)
            result["population"] = result["trace"].sum(1, dtype=np.int32)
            result["rates"] = result["counts"].astype(np.float32) * (1000 / row.duration_ms)
            result["rates_hz"] = result["rates"].copy()
        return result

    monkeypatch.setattr(__import__(__name__), "result_fixture", changed)
    m, ledger, engine, _ = execute(tmp_path)
    assert m["status"] == "gate_failed", m
    assert len(engine.calls) == expected
    assert not any(
        x["call"]["stage"] == stage and x["call"]["kind"].startswith("train-") for x in ledger["attempts"]
    )
    for job in m["jobs"][list(r.STAGES).index(stage) + 1 :]:
        assert job["status"] == "not_run_gate_failed"


@pytest.mark.parametrize("boundary", ["ledger", "manifest"])
@pytest.mark.parametrize("stop", ["budget_stopped", "cancelled"])
def test_final_persistence_cap_or_cancellation_cannot_report_completion(
    tmp_path, monkeypatch, boundary, stop
):
    elapsed = [0.0]
    cancel = [False]
    original = r.atomic_json
    triggered = False

    def publish(path, data):
        nonlocal triggered
        original(path, data)
        if path.name == boundary + ".json" and data.get("status") == "completed" and not triggered:
            triggered = True
            if stop == "budget_stopped":
                elapsed[0] = 1200.0
            else:
                cancel[0] = True

    monkeypatch.setattr(r, "atomic_json", publish)
    prepared = inputs()
    engine = FakeEngine(prepared)
    result = r._execute(
        tmp_path,
        {"bindings": []},
        prepared,
        lambda: engine,
        clock=lambda: elapsed[0],
        cancelled=lambda: cancel[0],
        started=0.0,
    )
    assert triggered and len(engine.calls) == 1632 and result["status"] == stop, result
    directory = tmp_path / "output/experiments" / result["id"]
    ledger = strict_json((directory / "ledger.json").read_bytes())
    assert ledger["status"] == stop and result["conditioning"]["calls"]["actual"] == 1632
    if stop == "budget_stopped":
        assert ledger["wall_seconds"] >= 1200
    from bet36fly.conditioning_artifacts import binding

    artifact = next(x for x in result["artifacts"].values() if x["path"] == "ledger.json")
    assert artifact["sha256"] == binding(directory / "ledger.json")["sha256"]
