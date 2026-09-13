"""Synthetic archive/driver boundaries; never read actual stored spike histories."""

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("prefix_driver_v2", HERE / "run_dan_causal_prefix_v2.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def binding(p):
    a = p.read_bytes()
    return dict(path=str(p), bytes=len(a), sha256=hashlib.sha256(a).hexdigest())


def fixture():
    s = dict(steps=12, coarse_steps=3, nk=3, nd=3, ns=1, n=9, ne=4, ng=8, populations=[2, 1])
    maps = dict(
        sample=np.array([0, 1, 2, 3, 4, 5, 6], np.int32),
        body_ids=np.arange(100, 107, dtype=np.int64),
        kc_indices=np.array([0, 1, 2], np.int32),
        dan_indices=np.array([3, 4, 5], np.int32),
        sensory_indices=np.array([6], np.int32),
        kc_columns=np.array([0, 1, 2], np.int32),
        dan_columns=np.array([3, 4, 5], np.int32),
        sensory_columns=np.array([6], np.int32),
        dan_compartments=np.array([0, 0, 1], np.int32),
        plastic_kc_indices=np.array([0, 1, 2, 0], np.int32),
        plastic_compartments=np.array([0, 0, 1, 1], np.int32),
        plastic_groups=np.array([0, 1, 4, 5], np.int32),
        plastic_mask=np.array([1, 1, 1, 0], np.uint8),
    )
    fine = dict(
        trace=np.zeros((12, 7), np.int32),
        counts=np.zeros(9, np.int32),
        rates=np.zeros(9, np.float32),
        rates_hz=np.zeros(9, np.float32),
        voltage=np.full(9, -52, np.float32),
        population=np.zeros(12, np.int32),
        dan_counts=np.zeros(3, np.int32),
        compartment_dan_counts=np.zeros(2, np.int32),
        compartment_tonic_hz=np.zeros(2, np.float32),
        gains=np.ones(4, np.float32),
        gain_delta=np.zeros(4, np.float32),
        pulse_times_ms=np.zeros(0, np.float32),
        pulse_dan_indices=np.zeros(0, np.int32),
    )
    main = dict(
        step_signals=np.zeros((12, 5), np.float32),
        bridge_kc_used=np.zeros((12, 8, 2)),
        bridge_rule=np.zeros((12, 8, 8)),
        dan_bins=np.zeros((4, 3), np.int32),
        bridge_signals=np.zeros((12, 2, 2)),
        bridge_kc_bins=np.zeros((4, 3, 2)),
        sensory_bins=np.zeros((4, 1), np.int32),
        gains=np.ones(4, np.float32),
        gain_delta=np.zeros(4, np.float32),
    )
    return s, maps, fine, main


def test_quiet_and_nonzero_difference_are_distinct_complete_prefixes():
    s, maps, fine, u = fixture()
    t = {k: v.copy() for k, v in u.items()}
    quiet, a = m.contrast_arrays(fine, u, t, maps, s, first_pulse_step=4)
    assert quiet["first_pool_difference_step"] is None
    assert quiet["kc_equal_through_step"] == 11
    assert not a["dan_count_difference"].any()
    t["step_signals"][4, 1] = 0.5
    t["dan_bins"][1, 0] = 1
    r, a = m.contrast_arrays(fine, u, t, maps, s, first_pulse_step=4)
    assert r["first_pool_difference_step"] == 4 and r["whole_prefix_bins"] == 1
    assert a["dan_count_difference"][4].tolist() == [1, 0]
    assert a["kc_prefix_counts"].shape == (3,)
    assert not r["per_cell_taught_history_established"]


@pytest.mark.parametrize(
    "field",
    [
        "step_signals",
        "bridge_kc_used",
        "bridge_rule",
        "dan_bins",
        "bridge_signals",
        "bridge_kc_bins",
        "sensory_bins",
        "gains",
        "gain_delta",
    ],
)
@pytest.mark.parametrize("bad", ["shape", "dtype"])
def test_main_fixed_layout_cannot_broadcast_or_coerce(field, bad):
    s, _, _, a = fixture()
    a[field] = (
        a[field][:-1]
        if bad == "shape"
        else a[field].astype(np.float32 if a[field].dtype == np.float64 else np.float64)
    )
    with pytest.raises(ValueError):
        m.validate_main(a, s)


@pytest.mark.parametrize(
    "field", ["step_signals", "bridge_kc_used", "bridge_rule", "bridge_signals", "bridge_kc_bins", "gains"]
)
def test_nonfinite_outside_prefix_still_invalid(field):
    s, _, _, a = fixture()
    a[field].flat[-1] = np.nan
    with pytest.raises(ValueError):
        m.validate_main(a, s)


@pytest.mark.parametrize("value", [-1, 0.5, 4])
def test_kc_total_count_domain(value):
    s, _, _, a = fixture()
    a["step_signals"][0, 0] = value
    with pytest.raises(ValueError):
        m.validate_main(a, s)


def test_unused_columns_and_dan_population_bin_domains():
    s, _, _, a = fixture()
    a["step_signals"][0, 4] = 1
    with pytest.raises(ValueError):
        m.validate_main(a, s)
    a["step_signals"][0, 4] = 0
    a["dan_bins"][0, 0] = 4
    with pytest.raises(ValueError):
        m.validate_main(a, s)


@pytest.mark.parametrize("role", ["kc", "dan", "sensory"])
@pytest.mark.parametrize("bad", ["duplicate", "wrong_column", "wrong_global"])
def test_role_identity_is_not_inferred_from_shape(role, bad):
    s, maps, _, _ = fixture()
    if bad == "duplicate":
        maps[role + "_columns"][:] = maps[role + "_columns"][0]
    elif bad == "wrong_column":
        maps[role + "_columns"][0] = (maps[role + "_columns"][0] + 1) % 7
    else:
        maps[role + "_indices"][0] = 8
    # Single-element sensory cannot itself duplicate; cause cross-role overlap.
    if role == "sensory" and bad == "duplicate":
        maps["sensory_columns"][0] = 0
        maps["sensory_indices"][0] = 0
    with pytest.raises(ValueError):
        m.validate_maps(maps, s)


@pytest.mark.parametrize("name,value", [("trace", 2), ("trace", -1), ("counts", -1), ("population", -1)])
def test_fine_count_domains(name, value):
    s, maps, fine, _ = fixture()
    fine[name].flat[0] = value
    with pytest.raises(ValueError):
        m.validate_fine(fine, maps, s)


@pytest.mark.parametrize(
    "bad",
    [
        "pulse",
        "fine_pool",
        "fine_kc",
        "sensory",
        "dan_bins",
        "bridge_before",
        "kc_bin_prefix",
        "sampled_prefix",
    ],
)
def test_required_reconciliation_families_fail(bad):
    s, maps, fine, u = fixture()
    t = {k: v.copy() for k, v in u.items()}
    if bad == "pulse":
        fine["pulse_times_ms"] = np.array([1], np.float32)
    elif bad == "fine_pool":
        u["step_signals"][0, 1] = 0.5
    elif bad == "fine_kc":
        u["step_signals"][0, 0] = 1
    elif bad == "sensory":
        t["sensory_bins"][0, 0] = 1
    elif bad == "dan_bins":
        u["dan_bins"][0, 0] = 1
    elif bad == "bridge_before":
        t["bridge_signals"][0, 0, 0] = 1
    elif bad == "kc_bin_prefix":
        t["bridge_kc_bins"][0, 0, 0] = 1
    else:
        u["sampled_bins"] = np.zeros((4, 7), np.int32)
        t["sampled_bins"] = u["sampled_bins"].copy()
        t["sampled_bins"][0, 0] = 1
    with pytest.raises(ValueError):
        m.contrast_arrays(fine, u, t, maps, s, first_pulse_step=4, sampled=maps["sample"])


def test_straddling_bin_does_not_extend_prefix_or_claim_percell_dan_equality():
    s, maps, fine, u = fixture()
    t = {k: v.copy() for k, v in u.items()}
    t["step_signals"][4, 1] = 0.5
    t["dan_bins"][1, 0] = 1
    t["bridge_kc_bins"][1, 0, 0] = 1
    r, _ = m.contrast_arrays(fine, u, t, maps, s, first_pulse_step=4)
    assert r["whole_prefix_bins"] == 1


@pytest.mark.parametrize("mutation", ["missing", "changed", "bad_size", "bad_hash", "duplicate", "symlink"])
def test_bound_file_family(tmp_path, mutation):
    p = tmp_path / "a"
    p.write_bytes(b"ab")
    item = binding(p)
    items = [item]
    if mutation == "missing":
        p.unlink()
    elif mutation == "changed":
        p.write_bytes(b"cd")
    elif mutation == "bad_size":
        item["bytes"] = True
    elif mutation == "bad_hash":
        item["sha256"] = "x" * 64
    elif mutation == "duplicate":
        items.append(item.copy())
    else:
        q = tmp_path / "link"
        q.symlink_to(p)
        item["path"] = str(q)
    with pytest.raises((ValueError, OSError)):
        m.BoundInputs(items).verify()


@pytest.mark.parametrize("text", ['{"a":1,"a":2}', '{"a":NaN}', '{"a":1e400}'])
def test_strict_json(tmp_path, text):
    p = tmp_path / "bad.json"
    p.write_text(text)
    b = m.BoundInputs([binding(p)])
    with pytest.raises(ValueError):
        b.json(p)


def test_numeric_npz_roundtrip_and_declared_header_allocation_rejection(tmp_path):
    p = tmp_path / "a.npz"
    np.savez(p, x=np.arange(4, dtype=np.int32))
    b = m.BoundInputs([binding(p)])
    with b.archive(p) as z:
        np.testing.assert_array_equal(z.array("x"), np.arange(4))
    f = io.BytesIO()
    np.lib.format.write_array_header_1_0(f, dict(descr="<f8", fortran_order=False, shape=(100000000,)))
    p = tmp_path / "oversized.npz"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("x.npy", f.getvalue())
    with pytest.raises(ValueError):
        with m.BoundInputs([binding(p)]).archive(p):
            pass


def plan_fixture(tmp_path):
    data = tmp_path / "input"
    data.write_text("input")
    plan = dict(
        schema=1,
        root=str(tmp_path),
        capture_dir=str(tmp_path / "cap"),
        samples_path=str(data),
        run_dirs={"original": str(tmp_path / "original"), "second": str(tmp_path / "second")},
        inputs=[binding(data)],
        expected_rows=[
            dict(run_id=p, game=g, seed_set=s, seed=g)
            for p in ["original", "second"]
            for g in range(8)
            for s in ["base", "alt"]
        ],
        source_snapshot={},
        contract=dict(m.ACTUAL_CONTRACT),
        wall_seconds_cap=120,
    )
    plan["run_id"] = (
        "dan-causal-prefix-"
        + hashlib.sha256(
            json.dumps(plan, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()[:20]
    )
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    return path, data


def producer(plan, store, guard):
    for i in range(64):
        guard()
        yield (
            dict(
                index=i,
                first_pool_difference_step=None,
                first_pool_count_difference=None,
                total_compartment_count_difference=[0, 0],
                kc_equal_through_step=1999,
                condition="home" if i % 2 == 0 else "away",
                seed_set="base",
                run_id="original",
            ),
            dict(
                dan_count_difference=np.zeros((2, 2), np.int64),
                kc_prefix_counts=np.zeros(1, np.int64),
                kc_body_ids=np.ones(1, np.int64),
            ),
        )


def test_complete_exclusive_immutable_execution(tmp_path):
    path, data = plan_fixture(tmp_path)
    before = data.read_bytes()
    out = tmp_path / "result"
    r = m.execute(path, out, _producer=producer)
    assert r["status"] == "completed" and r["completed_contrasts"] == 64
    assert len(list(out.glob("contrast_*.npz"))) == 64 and data.read_bytes() == before
    previous = (out / "status.json").read_bytes()
    with pytest.raises(FileExistsError):
        m.execute(path, out, _producer=producer)
    assert (out / "status.json").read_bytes() == previous


@pytest.mark.parametrize(
    "failure", ["producer", "source_changed", "missing_row", "extra_row", "persist", "cap"]
)
def test_failure_retains_completed_observations_and_never_completes(tmp_path, monkeypatch, failure):
    path, data = plan_fixture(tmp_path)
    out = tmp_path / "result"
    clock = [0.0]

    def generate(plan, store, guard):
        for i, (row, arrays) in enumerate(producer(plan, store, guard)):
            if i == 2:
                if failure == "producer":
                    raise ValueError("synthetic row failure")
                if failure == "source_changed":
                    data.write_text("mutated")
                if failure == "missing_row":
                    return
                if failure == "cap":
                    clock[0] = 120
            yield row, arrays
        if failure == "extra_row":
            yield dict(index=64), {}

    if failure == "persist":
        original = m.atomic_json

        def fail(p, value):
            if Path(p).name == "contrast_002.json":
                raise OSError("synthetic persistence failure")
            original(p, value)

        monkeypatch.setattr(m, "atomic_json", fail)
    r = m.execute(path, out, _producer=generate, clock=lambda: clock[0])
    assert r["status"] == "failed"
    assert (out / "terminal-error.json").exists() and (out / "contrast_000.npz").exists()
    assert json.loads((out / "status.json").read_text())["status"] == "failed"


@pytest.mark.parametrize("stage", ["summary.json", "status.json", "completion.json"])
def test_final_persistence_cap_never_returns_completed(tmp_path, monkeypatch, stage):
    path, _ = plan_fixture(tmp_path)
    clock = [0.0]
    original = m.atomic_json

    def crossing(p, value):
        original(p, value)
        if Path(p).name == stage and (stage != "status.json" or value["status"] == "completed"):
            clock[0] = 120.0

    monkeypatch.setattr(m, "atomic_json", crossing)
    out = tmp_path / "out"
    r = m.execute(path, out, _producer=producer, clock=lambda: clock[0])
    assert r["status"] == "failed" and r["completed_contrasts"] == 64
    assert json.loads((out / "status.json").read_text())["status"] == "failed"
    assert "120-second" in (out / "terminal-error.json").read_text()
    if stage == "completion.json":
        marker = json.loads((out / "completion.json").read_text())
        assert marker["status_sha256"] != hashlib.sha256((out / "status.json").read_bytes()).hexdigest()
    else:
        assert not (out / "completion.json").exists()


@pytest.mark.parametrize("stage", ["summary.json", "completion.json"])
def test_final_persistence_failure_retains_all_observations(tmp_path, monkeypatch, stage):
    path, _ = plan_fixture(tmp_path)
    original = m.atomic_json

    def failing(p, value):
        if Path(p).name == stage:
            raise OSError("synthetic terminal write failure")
        original(p, value)

    monkeypatch.setattr(m, "atomic_json", failing)
    out = tmp_path / "out"
    r = m.execute(path, out, _producer=producer)
    assert r["status"] == "failed" and r["completed_contrasts"] == 64
    assert len(list(out.glob("contrast_*.json"))) == 64


def synthetic_archive_study(tmp_path, monkeypatch):
    """Complete 32-history metadata/IO shape, with tiny explicitly synthetic arrays."""
    import csv

    s, maps, fine, main = fixture()
    s["n"] = 13
    for k in ["counts", "rates", "rates_hz", "voltage"]:
        fine[k] = np.zeros(13, dtype=fine[k].dtype)
    monkeypatch.setattr(m, "ACTUAL_SHAPE", s)
    root = tmp_path / "repo"
    root.mkdir()
    cap = root / "capture"
    cap.mkdir()
    inputs = []

    def save_bytes(p, data):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        inputs.append(binding(p))
        return inputs[-1]

    def save_json(p, data):
        return save_bytes(p, json.dumps(data).encode())

    def save_npz(p, arrays):
        f = io.BytesIO()
        np.savez_compressed(f, **arrays)
        return save_bytes(p, f.getvalue())

    def save_npy(p, a):
        f = io.BytesIO()
        np.save(f, a)
        return save_bytes(p, f.getvalue())

    graph = {}
    for name, a in [
        ("ids", np.arange(100, 113, dtype=np.int64)),
        ("kc", maps["kc_indices"]),
        ("sensory", maps["sensory_indices"]),
        ("mbon", np.arange(7, 13, dtype=np.int32)),
    ]:
        rel = "data/brain/" + name + ".npy"
        graph[rel] = save_npy(root / rel, a)["sha256"]
    source = {}
    code = {}
    for rel in [
        "bet36fly/reward_lif.cpp",
        "bet36fly/reward_brain.py",
        "bet36fly/reward_protocol.py",
        "bet36fly/reward_encoder.py",
        "bet36fly/reward_diagnostic.py",
        "scripts/reward_teaching_diagnostic.py",
    ]:
        b = save_bytes(root / rel, b"synthetic source")
        copy = save_bytes(root / "snapshots" / rel, b"synthetic source")
        code[Path(rel).name] = b["sha256"]
        source[rel] = dict(path=copy["path"], sha256=copy["sha256"])
    native = save_bytes(root / "native", b"synthetic nonexecutable")
    pilot = root / "pilot"
    pilot_hash = {}
    for name, key in [
        ("manifest.json", "pilot_manifest_sha256"),
        ("source/inputs.npz", "inputs_sha256"),
        ("source/protocol.json", "pilot_protocol_sha256"),
    ]:
        pilot_hash[key] = save_bytes(pilot / name, b"synthetic locked prerequisite")["sha256"]
    sample = save_npz(root / "samples.npz", maps)
    atlas = root / "atlas.csv"
    fields = ["body_id", "graph_index", "type", "cell_class", "transmitter", "reward_fast_output_zeroed"]
    f = io.StringIO()
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for i in range(13):
        cell = (
            "PPL101"
            if i in [3, 4]
            else "PAM12"
            if i == 5
            else "MBON11"
            if i in [7, 8]
            else "MBON09"
            if i >= 9
            else "KC"
        )
        w.writerow(
            dict(
                body_id=100 + i,
                graph_index=i,
                type=cell,
                cell_class="DAN" if 3 <= i <= 5 else "MBON" if i >= 7 else "KC",
                transmitter="dopamine" if 3 <= i <= 5 else "acetylcholine",
                reward_fast_output_zeroed=int(3 <= i <= 5),
            )
        )
    save_bytes(atlas, f.getvalue().encode())
    rows = m.expected_rows()
    dirs = {rid: str(root / rid) for rid in m.RUNS}
    prior = {}
    main_summaries = {}
    layout = dict(
        layout_version="rate-bridge-v1/1",
        learning_rule="rate-bridge-v1",
        group_compartments=[0] * 4 + [1] * 4,
        config=dict(
            h_ms=0.2,
            tau_ms=500.0,
            rate_tau_ms=100.0,
            effective_eta=0.0005,
            normalization=0.96,
            tail="analytic_no_new_event_tail",
            checkpoint="float32; double remainder discarded",
        ),
        layout=dict(step_signals=["kc_spikes", "dan_mean_spikes per compartment", "unused zeros"]),
    )
    sampled = np.concatenate(
        [np.arange(7, 13, dtype=np.int64), maps["dan_indices"], maps["kc_indices"], maps["sensory_indices"]]
    )
    for panel, rid in enumerate(m.RUNS):
        base = Path(dirs[rid])
        arr = {
            k: maps[k]
            for k in [
                "plastic_kc_indices",
                "plastic_compartments",
                "plastic_groups",
                "plastic_mask",
                "dan_compartments",
            ]
        }
        arr.update(blank_gains=np.ones(4, np.float32), sampled=sampled)
        actual = []
        for r in [r for r in rows if r["run_id"] == rid]:
            for c in ["frozen", "untaught", "home", "away"]:
                actual.append(
                    dict(
                        game=r["game"],
                        seed_set=r["seed_set"],
                        seed=r["seed"],
                        condition=c,
                        sensory_bins_sha256=hashlib.sha256(main["sensory_bins"].tobytes()).hexdigest(),
                    )
                )
                for k, a in main.items():
                    arr[f"{r['game']}__{r['seed_set']}__{c}__{k}"] = a
                if r["game"] == m.GAMES[panel][0]:
                    arr[f"{r['game']}__{r['seed_set']}__{c}__sampled_bins"] = np.zeros((4, 13), np.int32)
        ab = save_npz(base / "trials.npz", arr)
        lb = save_json(base / "recording-layout.json", layout)
        summary = dict(
            run_id=rid,
            panel_complete=True,
            panel_games=m.GAMES[panel],
            native_binary={k: native[k] for k in ["path", "sha256"]},
            identity=dict(
                protocol=m.PROTOCOL,
                selection=dict(expected_panel=actual),
                code_hashes=code,
                graph_hashes=graph,
                **pilot_hash,
            ),
            rows=actual,
            artifacts={
                name: {k: b[k] for k in ["bytes", "sha256"]}
                for name, b in [("trials.npz", ab), ("recording-layout.json", lb)]
            },
        )
        prior[rid] = dict(summary_sha256=save_json(base / "summary.json", summary)["sha256"])
        main_summaries[rid] = summary
    saved = [dict(file="coarse.npz")]
    for i in range(32):
        b = save_npz(cap / f"fine_{i:02d}.npz", fine)
        saved.append(
            dict(
                file=Path(b["path"]).name,
                sha256=b["sha256"],
                bytes=b["bytes"],
                metadata=dict(dt=0.2, bin_ms=0.2, duration_ms=400.0, instrumentation=None),
                numeric_fingerprint={
                    k: dict(
                        dtype=str(a.dtype),
                        shape=list(a.shape),
                        sha256=hashlib.sha256(a.tobytes()).hexdigest(),
                    )
                    for k, a in fine.items()
                },
            )
        )
    identity = dict(
        protocol=m.PROTOCOL,
        rows=rows,
        graph_hashes=graph,
        native_binary={k: native[k] for k in ["path", "sha256"]},
        pilot=str(pilot),
        **pilot_hash,
        source_code=code,
        prior=prior,
        sample_arrays={
            k: dict(dtype=str(a.dtype), shape=list(a.shape), sha256=hashlib.sha256(a.tobytes()).hexdigest())
            for k, a in maps.items()
        },
        capture=dict(
            bin_ms=0.2,
            electrical_dt=0.2,
            coarse_bin_ms=10.0,
            schedule_repeat=50,
            record=False,
            plasticity=True,
            pulses=[],
            unit_initial_gains=True,
            raster_unit="actual binary spike events per .2ms interval; columns by stored global index",
        ),
    )
    rid = "onset-history-capture-4343c21535c43f42"
    receipt = dict(
        run_id=rid, identity=identity, samples_path=sample["path"], samples_sha256=sample["sha256"]
    )
    save_json(cap / "capture-receipt.json", receipt)
    save_json(
        cap / "summary.json",
        dict(run_id=rid, status="complete", calls=33, attempted_calls=33, identity=identity, saved=saved),
    )
    save_json(cap / "progress.json", dict(completed_calls=33, attempted_calls=33, saved=saved))
    inputs.extend([binding(Path(m.__file__)), binding(Path(m.prefix.__file__))])
    plan = dict(
        schema=1,
        root=str(root),
        capture_dir=str(cap),
        samples_path=sample["path"],
        atlas_path=str(atlas),
        run_dirs=dirs,
        expected_rows=rows,
        inputs=inputs,
        source_snapshot=source,
        contract=dict(m.ACTUAL_CONTRACT),
        wall_seconds_cap=120,
    )
    plan["run_id"] = (
        "dan-causal-prefix-"
        + hashlib.sha256(
            json.dumps(plan, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()[:20]
    )
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    return plan, path


def test_complete_synthetic_archive_io_and_identity_path(tmp_path, monkeypatch):
    plan, path = synthetic_archive_study(tmp_path, monkeypatch)
    # The fixed actual onset is outside tiny synthetic duration; only the numerical
    # helper onset argument is substituted. Actual metadata and IO remain exercised.
    original = m.contrast_arrays
    monkeypatch.setattr(m, "contrast_arrays", lambda *a, **kw: original(*a, **dict(kw, first_pulse_step=4)))
    r = m.execute(path, tmp_path / "out")
    assert r["status"] == "completed", r["error"]
    assert r["completed_contrasts"] == 64
    assert [x["fine_index"] for x in r["rows"]] == [i for i in range(32) for _ in range(2)]
    assert [x["condition"] for x in r["rows"]] == ["home", "away"] * 32


@pytest.mark.parametrize(
    "bad",
    [
        "source",
        "pilot",
        "capture_count",
        "mode",
        "fine_selector",
        "main_matrix",
        "main_seed",
        "layout",
        "sample_fingerprint",
        "DAN_atlas",
        "fine_fingerprint",
    ],
)
def test_synthetic_identity_and_archive_malformed_family(tmp_path, monkeypatch, bad):
    plan, path = synthetic_archive_study(tmp_path, monkeypatch)
    cap = Path(plan["capture_dir"])
    base = Path(next(iter(plan["run_dirs"].values())))
    target = cap / "capture-receipt.json"
    data = json.loads(target.read_text())
    if bad == "source":
        data["identity"]["source_code"]["reward_lif.cpp"] = "a" * 64
    elif bad == "pilot":
        data["identity"]["inputs_sha256"] = "a" * 64
    elif bad == "mode":
        data["identity"]["capture"]["plasticity"] = False
    elif bad == "fine_selector":
        data["identity"]["rows"][0]["seed"] += 1
    elif bad == "sample_fingerprint":
        data["identity"]["sample_arrays"]["kc_columns"]["sha256"] = "a" * 64
    elif bad == "capture_count":
        target = cap / "summary.json"
        data = json.loads(target.read_text())
        data["calls"] = 32
    elif bad in ["main_matrix", "main_seed"]:
        target = base / "summary.json"
        data = json.loads(target.read_text())
        if bad == "main_matrix":
            data["rows"].pop()
        else:
            data["rows"][0]["seed"] += 1
    elif bad == "layout":
        target = base / "recording-layout.json"
        data = json.loads(target.read_text())
        data["config"]["h_ms"] = 0.3
    elif bad == "DAN_atlas":
        target = Path(plan["atlas_path"])
        target.write_text(target.read_text().replace("PPL101", "PPL102"))
        data = None
    else:
        target = cap / "summary.json"
        data = json.loads(target.read_text())
        data["saved"][1]["numeric_fingerprint"]["trace"]["sha256"] = "a" * 64
    if data is not None:
        target.write_text(json.dumps(data))
    # Rebind changed outer bytes so rejection exercises internal identity, not
    # the already-tested top-level checksum boundary.
    plan["inputs"] = [binding(target) if x["path"] == str(target) else x for x in plan["inputs"]]
    plan.pop("run_id")
    plan["run_id"] = (
        "dan-causal-prefix-"
        + hashlib.sha256(
            json.dumps(plan, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()[:20]
    )
    path.write_text(json.dumps(plan))
    r = m.execute(path, tmp_path / "out")
    assert r["status"] == "failed" and r["completed_contrasts"] == 0


def source_sampled(maps):
    # Exact source operation: intp flatnonzero outputs on the pinned64bit platform,
    # then int32 engine DANs and retained KC/sensory arrays. Result is int64.
    outputs = np.flatnonzero(np.arange(13) >= 7)
    return outputs, np.concatenate(
        [outputs, maps["dan_indices"], maps["kc_indices"], maps["sensory_indices"]]
    )


def test_exact_source_int64_sampled_contract_passes():
    s, maps, _, _ = fixture()
    s["n"] = 13
    outputs, sampled = source_sampled(maps)
    assert sampled.dtype == np.dtype("int64")
    m.validate_main_sampled(sampled, outputs, maps, s)


@pytest.mark.parametrize(
    "bad",
    [
        "float32",
        "float64",
        "bool",
        "int32",
        "uint64",
        "missing",
        "extra",
        "duplicate",
        "order",
        "identity",
        "negative",
        "out_of_range",
    ],
)
def test_main_sampled_type_order_identity_family_is_strict(bad):
    s, maps, _, _ = fixture()
    s["n"] = 14
    outputs, a = source_sampled(maps)
    if bad in ["float32", "float64", "bool", "int32", "uint64"]:
        a = a.astype(bad)
    elif bad == "missing":
        a = a[:-1]
    elif bad == "extra":
        a = np.append(a, np.int64(13))
    elif bad == "duplicate":
        a[-1] = a[-2]
    elif bad == "order":
        a[[0, 1]] = a[[1, 0]]
    elif bad == "identity":
        a[0] = 13
    elif bad == "negative":
        a[-1] = -1
    else:
        a[-1] = 14
    with pytest.raises(ValueError):
        m.validate_main_sampled(a, outputs, maps, s)


@pytest.mark.parametrize("dtype", ["float32", "float64", "bool", "int64", "uint32"])
@pytest.mark.parametrize("role", ["kc", "sensory", "mbon"])
def test_retained_graph_indices_reject_dtype_coercion(role, dtype):
    original = np.array([0, 2], np.int32)
    m.validate_graph_indices(original, 2, 4, role)
    with pytest.raises(ValueError):
        m.validate_graph_indices(original.astype(dtype), 2, 4, role)


@pytest.mark.parametrize("bad", ["duplicate", "negative", "out_of_range", "missing", "matrix"])
def test_graph_index_shape_range_identity_family(bad):
    a = np.array([0, 2], np.int32)
    if bad == "duplicate":
        a[1] = 0
    elif bad == "negative":
        a[0] = -1
    elif bad == "out_of_range":
        a[1] = 4
    elif bad == "missing":
        a = a[:-1]
    else:
        a = a.reshape(1, 2)
    with pytest.raises(ValueError):
        m.validate_graph_indices(a, 2, 4, "synthetic")
