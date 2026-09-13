"""One immutable saved-history DARELA screen; no circuit or source solver imports.

Production uses only the fixed CLI. Underscored injected loader/evaluator options
exist for labeled synthetic persistence tests and are never serialized in a plan.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

import numpy as np

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "bet36fly/reward_lif.cpp").is_file())
CANON = ROOT / "docs/evidence/reward-mechanism-repair-2026-09-12"
# Only these frozen imports use the canonical directory. Restore module lookup
# afterward so an already copied launcher cannot shadow the current output one.
sys.path.insert(0, str(CANON))
try:
    import run_dan_causal_prefix_v2 as reader
    import weight_state_guard_reference as guard_ref
    from darela_release import release_events, WT1_P, WT1_TAU_S
    from darela_release_bridge_replay import replay, FIELDS
finally:
    sys.path.pop(0)

ANALYSIS = "darela-reset-release-shadow-v1"
CONTRACT = dict(
    steps=2000,
    dt_ms=0.2,
    onset_step=500,
    populations=[2, 22],
    p=[0.0105, -0.003, -0.0011],
    tau_s=[7.5, 15.0, 900.0],
    reset="unit H at t0; pre-H release then q kick",
    initial_gains="unit float32",
    rate_tau_ms=100.0,
    eligibility_tau_ms=500.0,
    eta=0.0005,
    normalization=0.96,
    bounds=[0.5, 1.5],
    tail="single full analytic bridge tail",
    expected_histories=32,
    expected_guard_cells=8,
    wall_seconds_cap=1200,
    native_calls=0,
    network_calls=0,
)
require, typed, equal = reader.require, reader.typed, reader.equal


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def study_id(plan):
    return (
        "darela-shadow-"
        + hashlib.sha256(canonical({k: v for k, v in plan.items() if k != "run_id"})).hexdigest()[:20]
    )


def binding(path, guard=lambda: None):
    p = Path(path).absolute()
    return dict(path=str(p), bytes=p.stat().st_size, sha256=reader.sha(p, guard))


def fingerprint(a):
    return dict(dtype=str(a.dtype), shape=list(a.shape), sha256=reader.array_hash(a))


def validate_plan(plan):
    require(type(plan) is dict and type(plan.get("schema")) is int and plan["schema"] == 1, "plan schema")
    require(
        plan.get("analysis") == ANALYSIS and reader.same_json(plan.get("contract"), CONTRACT),
        "frozen contract",
    )
    require(type(plan.get("wall_seconds_cap")) is int and plan["wall_seconds_cap"] == 1200, "wall cap")
    require(
        reader.same_json(plan.get("expected_rows"), reader.expected_rows()),
        "complete ordered typed selectors",
    )
    require(tuple(plan.get("run_dirs", {})) == reader.RUNS, "panel order")
    for k in [
        "root",
        "output_root",
        "capture_dir",
        "samples_path",
        "context_plan",
        "preregistration",
        "audit_contract",
    ]:
        require(
            type(plan.get(k)) is str and Path(plan[k]).is_absolute() and ".." not in Path(plan[k]).parts,
            "absolute " + k,
        )
    require(plan["root"] == str(ROOT), "repository identity")
    require(
        type(plan.get("reviews")) is list
        and plan["reviews"]
        and all(type(x) is str and Path(x).is_absolute() for x in plan["reviews"]),
        "review inventory",
    )
    reader.BoundInputs(plan.get("inputs"))
    require(plan.get("run_id") == study_id(plan), "plan identity")


def runtime_paths():
    return [
        Path(__file__).resolve(),
        Path(reader.__file__).resolve(),
        Path(reader.prefix.__file__).resolve(),
        Path(guard_ref.__file__).resolve(),
        CANON / "darela_release.py",
        CANON / "darela_release_bridge_replay.py",
        Path(__file__).with_name("test_run_darela_shadow.py"),
        Path(__file__).with_name("launch_darela_shadow.py"),
        Path(__file__).with_name("test_launch_darela_shadow.py"),
    ]


def validate_runtime(plan, store):
    for path in (
        runtime_paths()
        + [Path(plan[k]) for k in ["context_plan", "preregistration", "audit_contract"]]
        + [Path(x) for x in plan["reviews"]]
    ):
        store.path(path)
    context = store.json(plan["context_plan"])
    reader.validate_plan(context)
    for item in context["inputs"]:
        require(store.items.get(item["path"]) == item, "historical context binding changed or omitted")
    require(len(context["inputs"]) == 113, "complete historical context inventory")
    for key in ["root", "capture_dir", "samples_path", "run_dirs", "source_snapshot", "expected_rows"]:
        require(reader.same_json(plan[key], context[key]), "historical context field " + key)


def prepare(context_path, output_root, preregistration, audit_contract, reviews, additions=()):
    """Hash-only preparation: no raster load, release or bridge evaluation."""
    context_path = Path(context_path).absolute()
    context = reader.strict_json(context_path.read_bytes())
    reader.validate_plan(context)
    plan = {
        k: context[k]
        for k in ["root", "capture_dir", "samples_path", "run_dirs", "source_snapshot", "expected_rows"]
    }
    if "atlas_path" in context:
        plan["atlas_path"] = context["atlas_path"]
    plan.update(
        schema=1,
        analysis=ANALYSIS,
        output_root=str(Path(output_root).absolute()),
        wall_seconds_cap=1200,
        contract=CONTRACT,
        context_plan=str(context_path),
        preregistration=str(Path(preregistration).absolute()),
        audit_contract=str(Path(audit_contract).absolute()),
        reviews=[str(Path(x).absolute()) for x in reviews],
    )
    inventory = {item["path"]: item for item in context["inputs"]}
    for path in (
        runtime_paths()
        + [context_path, Path(preregistration), Path(audit_contract)]
        + [Path(x) for x in reviews]
        + [Path(x) for x in additions]
    ):
        item = binding(path)
        require(item["path"] not in inventory or inventory[item["path"]] == item, "preparation source drift")
        inventory[item["path"]] = item
    plan["inputs"] = list(inventory.values())
    plan["run_id"] = study_id(plan)
    validate_plan(plan)
    store = reader.BoundInputs(plan["inputs"])
    store.verify()
    validate_runtime(plan, store)
    return plan


def _maps_shape(m):
    require(type(m) is dict, "map dictionary")
    s = dict(
        steps=2000,
        coarse_steps=50,
        nk=len(m["kc_columns"]),
        nd=24,
        ns=len(m["sensory_columns"]),
        n=int(np.max(m["sample"])) + 1,
        ne=len(m["plastic_mask"]),
        ng=8,
        populations=[2, 22],
    )
    reader.validate_maps(m, s)
    return s


def validate_comparator(fine, main, m, s, sampled=None):
    """Exact untouched raw comparator and independently reduced count streams."""
    reader.validate_maps(m, s)
    reader.validate_fine(fine, m, s)
    t, b, ne = s["steps"], s["steps"] // s["coarse_steps"], s["ne"]
    x = typed(main["step_signals"], "float32", (t, 5), "main step signals")
    typed(x[:, 0], "float32", (t,), "main KC total", low=0, high=s["nk"], integer=True)
    require(not x[:, 3:].any(), "unused main signal columns")
    for role, size in [("dan", 24), ("sensory", s["ns"])]:
        typed(main[role + "_bins"], "int32", (b, size), role + " bins", low=0, high=50)
    for key in ["gains", "gain_delta"]:
        typed(main[key], "float32", (ne,), key)
        equal(main[key], fine[key], "fine/main original " + key)
    equal(fine["gain_delta"], fine["gains"] - np.float32(1), "original gain delta")
    require(np.all(fine["gains"][m["plastic_mask"] == 0] == np.float32(1)), "original masked gain")
    event = fine["trace"]
    pools = reader.prefix.fine_pool(event[:, m["dan_columns"]], m["dan_compartments"], [2, 22])
    equal(pools, reader.prefix.decode_pool(x[:, 1:3], [2, 22]), "fine/main pooled stream")
    equal(event[:, m["kc_columns"]].sum(1, dtype=np.int32).astype(np.float32), x[:, 0], "fine/main KC stream")
    bins = event.reshape(b, 50, event.shape[1]).sum(1, dtype=np.int32)
    for role in ["dan", "sensory"]:
        equal(bins[:, m[role + "_columns"]], main[role + "_bins"], "fine/main " + role + " bins")
    if "sampled_bins" in main:
        require(sampled is not None, "sample mapping absent")
        a = typed(main["sampled_bins"], "int32", (b, len(sampled)), "main sampled bins", low=0, high=50)
        columns = {int(v): i for i, v in enumerate(sampled)}
        equal(a[:, [columns[int(v)] for v in m["sample"]]], bins, "fine/main sampled count stream")


def _load_actual(plan, store, guard):
    m, summaries, outputs, saved = reader._identity_context(plan, store)
    s = reader.ACTUAL_SHAPE
    require(
        [int(np.sum((m["plastic_compartments"] == c) & (m["plastic_mask"] == 1))) for c in [0, 1]]
        == [4184, 3239]
        and int(np.sum(m["plastic_mask"] == 0)) == 1443,
        "fixed eligible edge counts",
    )

    def rows():
        archive = None
        active = None
        try:
            for i, meta in enumerate(plan["expected_rows"]):
                guard()
                rid = meta["run_id"]
                if active != rid:
                    if archive:
                        archive.__exit__()
                    archive = store.archive(Path(plan["run_dirs"][rid]) / "trials.npz")
                    active = rid
                    for key in [
                        "plastic_kc_indices",
                        "plastic_compartments",
                        "plastic_groups",
                        "plastic_mask",
                        "dan_compartments",
                    ]:
                        equal(archive.array(key), m[key], "main map " + key)
                    equal(archive.array("blank_gains"), np.ones(s["ne"], np.float32), "main initial gains")
                    sampled = archive.array("sampled")
                    reader.validate_main_sampled(sampled, outputs, m, s)
                name = f"fine_{i:02d}.npz"
                with store.archive(Path(plan["capture_dir"]) / name) as z:
                    fine = {k[:-4]: z.array(k[:-4]) for k in z.names}
                require(
                    {k: fingerprint(v) for k, v in fine.items()} == saved[name]["numeric_fingerprint"],
                    "complete fine numerical fingerprint",
                )
                prefix = f"{meta['game']}__{meta['seed_set']}__untaught__"
                keys = ["step_signals", "dan_bins", "sensory_bins", "gains", "gain_delta"]
                if meta["game"] == summaries[rid]["panel_games"][0]:
                    keys.append("sampled_bins")
                main = {k: archive.array(prefix + k) for k in keys}
                row = next(
                    x
                    for x in summaries[rid]["rows"]
                    if x["game"] == meta["game"]
                    and x["seed_set"] == meta["seed_set"]
                    and x["condition"] == "untaught"
                )
                require(
                    reader.array_hash(main["sensory_bins"]) == row["sensory_bins_sha256"],
                    "sensory summary hash",
                )
                validate_comparator(fine, main, m, s, sampled)
                electrical = (
                    archive.array(prefix + "electrical_gains")
                    if prefix + "electrical_gains.npy" in archive.names
                    else None
                )
                if electrical is not None:
                    typed(electrical, "float32", (s["ne"],), "original electrical gains", low=0.5, high=1.5)
                yield i, meta, fine["trace"], fine["gains"], fine["gain_delta"], electrical
        finally:
            if archive:
                archive.__exit__()

    return m, rows()


def _invoke(name, fn, *args, **kwargs):
    return fn(*args, **kwargs)


def evaluate_history(trace, original, delta, maps, *, original_electrical=None, invoke=_invoke):
    s = _maps_shape(maps)
    typed(trace, "int32", (2000, len(maps["sample"])), "binary raster", low=0, high=1)
    typed(original, "float32", (s["ne"],), "original gains", low=0.5, high=1.5)
    typed(delta, "float32", original.shape, "original delta")
    equal(delta, original - np.float32(1), "original delta/unit")
    kc = np.ascontiguousarray(trace[:, maps["kc_columns"]])
    dan = np.ascontiguousarray(trace[:, maps["dan_columns"]])
    watched = {**maps, "trace": trace, "kc": kc, "dan": dan, "original": original, "delta": delta}
    before = {k: fingerprint(v) for k, v in watched.items()}
    released = invoke("release", release_events, dan, maps["dan_compartments"])
    require(before == {k: fingerprint(v) for k, v in watched.items()}, "release helper input mutation")
    release_snapshot = {k: fingerprint(v) for k, v in released.items()}
    value = invoke(
        "bridge",
        replay,
        kc,
        released["pooled_release"],
        maps["plastic_kc_indices"],
        maps["plastic_compartments"],
        maps["plastic_mask"],
        maps["plastic_groups"],
        initial=np.ones(s["ne"], np.float32),
        learning=True,
    )
    require(before == {k: fingerprint(v) for k, v in watched.items()}, "bridge helper input mutation")
    require(
        release_snapshot == {k: fingerprint(v) for k, v in released.items()}, "bridge release input mutation"
    )
    value.update(released)
    value.update(
        initial_gains=np.ones(s["ne"], np.float32),
        original_gains=original.copy(),
        original_gain_delta=delta.copy(),
        raw_dan_events=dan.copy(),
        raw_kc_event_totals=kc.sum(0, dtype=np.int64),
        raw_dan_event_totals=dan.sum(0, dtype=np.int64),
        raw_compartment_event_counts=np.stack(
            [dan[:, maps["dan_compartments"] == c].sum(1, dtype=np.int64) for c in [0, 1]], 1
        ),
    )
    value.update({"map__" + k: v.copy() for k, v in maps.items()})
    if original_electrical is not None:
        value["original_electrical_gains"] = original_electrical.copy()
    validate_result(value, maps)
    return value


def close(a, b, name, atol=2e-11, rtol=1e-12):
    require(np.allclose(a, b, atol=atol, rtol=rtol), name)


def validate_result(v, m):
    s = _maps_shape(m)
    ne, nk = s["ne"], s["nk"]
    specs = {
        "gains": ("float32", (ne,)),
        "double_gains": ("float64", (ne,)),
        "electrical_gains": ("float32", (ne,)),
        "electrical_double_gains": ("float64", (ne,)),
        "edge_phases": ("float64", (4, ne, 8)),
        "group_phases": ("float64", (4, 8, 8)),
        "publication_counts": ("int64", (4, ne)),
        "bound_counts": ("int64", (2, ne)),
        "endpoint_kc": ("float64", (nk, 2)),
        "endpoint_dan": ("float64", (2, 2)),
        "per_cell_release": ("float64", (2000, 24)),
        "pooled_release": ("float64", (2000, 2)),
        "state_before": ("float64", (2000, 24, 3)),
        "state_after": ("float64", (2000, 24, 3)),
        "endpoint_state": ("float64", (24, 3)),
        "initial_gains": ("float32", (ne,)),
        "original_gains": ("float32", (ne,)),
        "original_gain_delta": ("float32", (ne,)),
        "raw_dan_events": ("int32", (2000, 24)),
        "raw_kc_event_totals": ("int64", (nk,)),
        "raw_dan_event_totals": ("int64", (24,)),
        "raw_compartment_event_counts": ("int64", (2000, 2)),
    }
    specs.update({"map__" + k: (str(a.dtype), a.shape) for k, a in m.items()})
    if "original_electrical_gains" in v:
        specs["original_electrical_gains"] = ("float32", (ne,))
    require(set(v) == set(specs), "complete result inventory")
    for k, (dtype, shape) in specs.items():
        typed(v[k], dtype, shape, k)
    for k, a in m.items():
        equal(v["map__" + k], a, "saved map identity")
    mask = m["plastic_mask"].astype(bool)
    equal(v["initial_gains"], np.ones(ne, np.float32), "unit checkpoint")
    equal(v["original_gain_delta"], v["original_gains"] - np.float32(1), "original delta")
    for k in ["gains", "double_gains", "electrical_gains", "electrical_double_gains", "original_gains"] + (
        ["original_electrical_gains"] if "original_electrical_gains" in v else []
    ):
        require(np.all((v[k] >= 0.5) & (v[k] <= 1.5)), "gain bounds")
        require(np.all(v[k][~mask] == 1), "masked gain bytes")
    for prefix in ["", "electrical_"]:
        equal(v[prefix + "gains"], v[prefix + "double_gains"].astype(np.float32), "float32 publication")
    events = v["raw_dan_events"]
    require(np.isin(events, [0, 1]).all(), "raw DAN binary")
    equal(v["raw_dan_event_totals"], events.sum(0, dtype=np.int64), "raw DAN reduction")
    require(np.all((v["raw_kc_event_totals"] >= 0) & (v["raw_kc_event_totals"] <= 2000)), "raw KC counts")
    cells = v["per_cell_release"]
    require(
        np.all((cells >= 0) & (cells <= 2**32))
        and np.all(cells[events == 0] == 0)
        and np.all(cells[events == 1] > 0),
        "release event support",
    )
    before, after = v["state_before"], v["state_after"]
    require(
        np.all(before > 0) and np.all(after > 0) and np.all(v["endpoint_state"] > 0),
        "positive release factors",
    )
    equal(before[0], np.ones((24, 3), np.float64), "reset H")
    close(
        after,
        before * np.where(events[:, :, None] == 1, 1 + np.array(WT1_P), 1),
        "pre/post event phase",
        1e-12,
    )
    close(before[1:], 1 + (after[:-1] - 1) * np.exp(-0.0002 / np.array(WT1_TAU_S)), "quiet recovery", 1e-12)
    close(
        v["endpoint_state"],
        1 + (after[-1] - 1) * np.exp(-0.0002 / np.array(WT1_TAU_S)),
        "endpoint recovery",
        1e-12,
    )
    close(cells, np.prod(before, axis=2) * events, "pre-H release", 1e-12)
    for c, pop in enumerate([2, 22]):
        selected = m["dan_compartments"] == c
        equal(v["pooled_release"][:, c], cells[:, selected].sum(1) / pop, "fixed population pooling")
        equal(
            v["raw_compartment_event_counts"][:, c],
            events[:, selected].sum(1, dtype=np.int64),
            "raw compartment reduction",
        )
    for k in ["endpoint_kc", "endpoint_dan"]:
        require(np.all(v[k] >= 0), "nonnegative bridge state")
    phase = v["edge_phases"]
    require(np.all(phase[:, ~mask, :] == 0), "masked phase")
    expected = np.array([150, 850, 500, 1], np.int64)[:, None] * mask[None, :]
    equal(v["publication_counts"], expected, "complete electrical and tail publications")
    require(np.all(phase[:, :, 0] >= 0) and np.all(phase[:, :, 1] <= 0), "signed product areas")
    close(phase[:, :, 2], phase[:, :, 0] + phase[:, :, 1], "attempted products")
    close(phase[:, :, 7], phase[:, :, 0] - phase[:, :, 1], "absolute product areas")
    counts = phase[:, :, 5:7]
    require(
        np.all((counts >= 0) & (counts == np.floor(counts)) & (counts <= expected[:, :, None])),
        "bound observation domain",
    )
    equal(v["bound_counts"], counts.sum(0).T.astype(np.int64), "bound observation reduction")
    for end, stop in [("", 4), ("electrical_", 3)]:
        equal(
            phase[:stop, :, 4].sum(0),
            v[end + "gains"].astype(np.float64) - 1,
            "exact published phase reconciliation",
        )
        close(phase[:stop, :, 3].sum(0), v[end + "double_gains"] - 1, "double phase reconciliation", 2e-12)
    for p in range(4):
        for col in range(8):
            expected_group = np.bincount(m["plastic_groups"], weights=phase[p, :, col], minlength=8)
            equal(v["group_phases"][p, :, col], expected_group, "group phase accounting")
    return v


def guard_summary(rows, m, key):
    result = {}
    for rid in reader.RUNS:
        for noise in ["base", "alt"]:
            selected = [
                r for r in rows if r["metadata"]["run_id"] == rid and r["metadata"]["seed_set"] == noise
            ]
            require(len(selected) == 8, "eight ordered guard trials")
            for channel, name in [(0, "home"), (1, "away")]:
                edges = (m["plastic_mask"] == 1) & (m["plastic_compartments"] == channel)
                values = np.stack([r[key][edges] for r in selected])
                totals = guard_ref.f32_trial_totals(values)
                means = np.array(totals, dtype=np.float64) / guard_ref.TICKS
                sd = float(np.std(means, ddof=1))
                result[f"{rid}/{noise}/{name}"] = dict(
                    ticks=list(totals),
                    edge_count=int(edges.sum()),
                    games=[r["metadata"]["game"] for r in selected],
                    mean=float(np.mean(means)),
                    sample_sd=sd,
                    limit=0.5 * sd,
                    passed=guard_ref.point_guard(totals),
                )
    return result


def _append(path, value):
    with Path(path).open("a") as f:
        f.write(canonical(value).decode() + "\n")
        f.flush()
        os.fsync(f.fileno())


def _save_npz(path, arrays):
    with Path(path).open("xb") as f:
        np.savez_compressed(f, **arrays)
        f.flush()
        os.fsync(f.fileno())


def execute(
    plan_path,
    out,
    *,
    _loader=_load_actual,
    _evaluator=evaluate_history,
    _check_runtime=True,
    clock=time.monotonic,
):
    started = clock()
    out = Path(out)
    out.mkdir(parents=False, exist_ok=False)
    state = dict(
        status="running",
        completed=0,
        attempted=0,
        invocations={"release": 0, "bridge": 0},
        returned={"release": 0, "bridge": 0},
        wall_seconds=0.0,
    )
    rows = []
    plan = {}
    old_alarm = None

    def guard(*, final=False):
        if clock() - started >= (1200 if final else 1190):
            raise TimeoutError("whole-study deadline/reserve")

    def persist():
        state["wall_seconds"] = clock() - started
        reader.atomic_json(out / "status.json", state)

    def invoke(name, fn, *args, **kwargs):
        guard()
        _append(out / "attempts.jsonl", dict(event="intent", index=state["completed"], helper=name))
        guard()
        state["invocations"][name] += 1
        answer = fn(*args, **kwargs)
        state["returned"][name] += 1
        guard()
        _append(out / "attempts.jsonl", dict(event="returned", index=state["completed"], helper=name))
        persist()
        guard()
        return answer

    try:
        if clock is time.monotonic:
            old_alarm = signal.getsignal(signal.SIGALRM)
            signal.signal(
                signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("hard child deadline"))
            )
            signal.setitimer(signal.ITIMER_REAL, 1200)
        p = Path(plan_path)
        require(p.stat().st_size <= 4_000_000, "bounded plan")
        plan_bytes = p.read_bytes()
        plan = reader.strict_json(plan_bytes)
        validate_plan(plan)
        require(
            out == Path(plan["output_root"]) / plan["run_id"] / "result", "exclusive identity output path"
        )
        reader.atomic_json(
            out / "identity.json",
            dict(run_id=plan["run_id"], plan_sha256=hashlib.sha256(plan_bytes).hexdigest(), plan=plan),
        )
        persist()
        guard()
        store = reader.BoundInputs(plan["inputs"], guard)
        store.verify()
        if _check_runtime:
            validate_runtime(plan, store)
        maps, iterator = _loader(plan, store, guard)
        _maps_shape(maps)
        for i, meta, trace, original, delta, electrical in iterator:
            guard()
            require(
                i == state["completed"] and i < 32 and reader.same_json(meta, plan["expected_rows"][i]),
                "row order/identity",
            )
            state["attempted"] += 1
            persist()
            guard()
            value = _evaluator(trace, original, delta, maps, original_electrical=electrical, invoke=invoke)
            validate_result(value, maps)
            guard()
            artifact = out / f"case_{i:02d}.npz"
            _save_npz(artifact, value)
            guard()
            detail = dict(
                index=i,
                metadata=meta,
                artifact=binding(artifact, guard),
                arrays={k: fingerprint(v) for k, v in value.items()},
                fields=list(FIELDS),
                original_electrical_available=electrical is not None,
                gain_bound_observations=int(value["bound_counts"].sum()),
            )
            reader.atomic_json(out / f"case_{i:02d}.json", detail)
            guard()
            _append(
                out / "attempts.jsonl",
                dict(event="complete", index=i, detail=binding(out / f"case_{i:02d}.json", guard)),
            )
            guard()
            rows.append(
                dict(
                    metadata=meta,
                    gains=value["gains"].copy(),
                    original_gains=value["original_gains"].copy(),
                    gain_bound_observations=detail["gain_bound_observations"],
                )
            )
            state["completed"] += 1
            persist()
            guard()
        require(
            state["completed"] == 32
            and state["attempted"] == 32
            and state["invocations"] == state["returned"] == dict(release=32, bridge=32),
            "complete32 helper accounting",
        )
        candidate = guard_summary(rows, maps, "gains")
        original = guard_summary(rows, maps, "original_gains")
        bounds = sum(r["gain_bound_observations"] for r in rows)
        store.verify()
        require(p.read_bytes() == plan_bytes, "plan bytes changed")
        guard(final=True)
        summary = dict(
            status="computed",
            run_id=plan["run_id"],
            screen="pending_independent_audit",
            completed=32,
            candidate_guards=candidate,
            original_guards=original,
            gain_bound_observations=bounds,
            provisional_screen="passed_necessary_untaught_screen"
            if all(x["passed"] for x in candidate.values()) and bounds == 0
            else "rejected_fixed_hypothesis",
            native_calls=0,
            network_calls=0,
            scope="Conditional fixed-spike rejection screen; no qualification or learning claim",
        )
        reader.atomic_json(out / "summary.json", summary)
        guard(final=True)
        state["status"] = "completed"
        persist()
        guard(final=True)
        completion = dict(
            status="complete",
            run_id=plan["run_id"],
            completed=32,
            elapsed_through_summary=clock() - started,
            bindings=[
                binding(out / name, lambda: guard(final=True))
                for name in ["identity.json", "status.json", "summary.json", "attempts.jsonl"]
            ],
        )
        reader.atomic_json(out / "completion.json", completion)
        guard(final=True)
        return state
    except BaseException as exc:
        state["status"] = "budget_stopped" if isinstance(exc, TimeoutError) else "failed"
        state["wall_seconds"] = clock() - started
        error = dict(
            status=state["status"],
            error_type=type(exc).__name__,
            error=str(exc),
            completed=state["completed"],
            wall_seconds=state["wall_seconds"],
        )
        if (out / "completion.json").is_file():
            error["invalidated_completion_sha256"] = reader.sha(out / "completion.json")
        try:
            reader.atomic_json(out / "terminal-error.json", error)
        finally:
            try:
                persist()
            except OSError:
                pass
        return state
    finally:
        if old_alarm is not None:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_alarm)


def validate_saved(out, plan, guard=lambda: None):
    """Container/schema proof, not the independent numerical reconstruction."""
    out = Path(out)
    require(not (out / "terminal-error.json").exists(), "terminal failure invalidates completion")

    def read(name):
        p = out / name
        require(p.is_file() and p.stat().st_size <= 32_000_000, "missing/bounded output JSON")
        guard()
        return reader.strict_json(p.read_bytes())

    completion = read("completion.json")
    state = read("status.json")
    identity = read("identity.json")
    summary = read("summary.json")
    require(
        completion["status"] == "complete"
        and state["status"] == "completed"
        and all(
            type(x) is int and x == 32
            for x in [state["completed"], state["attempted"], completion["completed"]]
        ),
        "terminal counts/status",
    )
    require(
        all(
            type(v) in (int, float) and 0 <= v < 1200
            for v in [state["wall_seconds"], completion["elapsed_through_summary"]]
        ),
        "terminal cap",
    )
    require(
        all(reader.same_json(state[k], dict(release=32, bridge=32)) for k in ["invocations", "returned"]),
        "helper counts",
    )
    require(
        reader.same_json(identity["plan"], plan)
        and all(x["run_id"] == plan["run_id"] for x in [identity, summary, completion]),
        "saved identity",
    )
    bound = reader.BoundInputs(completion["bindings"], guard)
    bound.verify()
    require(
        set(bound.items)
        == {str(out / n) for n in ["identity.json", "status.json", "summary.json", "attempts.jsonl"]},
        "terminal binding inventory",
    )
    require(
        len(list(out.glob("case_*.json"))) == len(list(out.glob("case_*.npz"))) == 32,
        "complete row/archive matrix",
    )
    records = [reader.strict_json(line) for line in (out / "attempts.jsonl").read_bytes().splitlines()]
    require(len(records) == 160, "complete invocation journal")
    require(
        summary.get("status") == "computed"
        and type(summary.get("completed")) is int
        and summary["completed"] == 32
        and summary.get("screen") == "pending_independent_audit",
        "summary disposition",
    )
    rows = []
    maps = None
    snapshots = []
    for i, meta in enumerate(plan["expected_rows"]):
        detail = read(f"case_{i:02d}.json")
        require(
            type(detail["index"]) is int
            and detail["index"] == i
            and reader.same_json(detail["metadata"], meta),
            "saved row identity",
        )
        detail_binding = binding(out / f"case_{i:02d}.json", guard)
        expected_journal = [
            dict(event=event, index=i, helper=helper)
            for helper in ["release", "bridge"]
            for event in ["intent", "returned"]
        ] + [dict(event="complete", index=i, detail=detail_binding)]
        require(
            reader.same_json(records[i * 5 : (i + 1) * 5], expected_journal),
            "ordered invocation journal/detail identity",
        )
        a = detail["artifact"]
        require(a["path"] == str(out / f"case_{i:02d}.npz"), "saved artifact path")
        snapshots.extend([a, detail_binding])
        store = reader.BoundInputs([a], guard)
        store.verify()
        with store.archive(a["path"]) as z:
            v = {k[:-4]: z.array(k[:-4]) for k in z.names}
        require({k: fingerprint(x) for k, x in v.items()} == detail["arrays"], "saved fingerprints")
        if maps is None:
            maps = {k[5:]: x for k, x in v.items() if k.startswith("map__")}
        validate_result(v, maps)
        require(
            type(detail["gain_bound_observations"]) is int
            and detail["gain_bound_observations"] == int(v["bound_counts"].sum()),
            "saved bound count",
        )
        rows.append(
            dict(
                metadata=meta,
                gains=v["gains"],
                original_gains=v["original_gains"],
                gain_bound_observations=int(v["bound_counts"].sum()),
            )
        )
    for label, key in [("candidate", "gains"), ("original", "original_gains")]:
        require(
            reader.same_json(summary[label + "_guards"], guard_summary(rows, maps, key)),
            "saved exact guard summary",
        )
    require(
        type(summary["gain_bound_observations"]) is int
        and summary["gain_bound_observations"] == sum(r["gain_bound_observations"] for r in rows),
        "saved bound total",
    )
    expected_screen = (
        "passed_necessary_untaught_screen"
        if all(x["passed"] for x in summary["candidate_guards"].values())
        and summary["gain_bound_observations"] == 0
        else "rejected_fixed_hypothesis"
    )
    require(
        summary.get("provisional_screen") == expected_screen
        and all(type(summary.get(k)) is int and summary[k] == 0 for k in ["native_calls", "network_calls"]),
        "provisional classification",
    )
    reader.BoundInputs(snapshots, guard).verify()
    bound.verify()
    require(not (out / "terminal-error.json").exists(), "late failure invalidates completion")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = execute(args.plan, args.out)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
