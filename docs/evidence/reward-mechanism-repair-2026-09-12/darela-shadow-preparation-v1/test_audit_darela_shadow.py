"""Independent shadow-audit tests; generated inputs only, no saved histories."""

from fractions import Fraction
import math

import numpy as np
import pytest
from scipy.integrate import quad

from audit_darela_shadow import bridge_reference, compare_endpoints, guard_cell
from darela_release_bridge_replay import replay


def data(steps=700, nk=2):
    return np.zeros((steps, nk), np.float64), np.zeros((steps, 2), np.float64)


def maps():
    return (np.array([0, 1, 0, 1]), np.array([0, 0, 1, 1]), np.array([1, 0, 1, 1]), np.array([0, 1, 4, 6]))


def kernel(lag):
    return -0.0005 * np.sign(lag) * (np.exp(-abs(lag) / 500) - np.exp(-abs(lag) / 100))


@pytest.mark.parametrize("lag", [-100, 0, 100])
@pytest.mark.parametrize("mass", [0.25, 1.0, 8.0, 10000.0])
def test_full_pair_and_finite_tail_from_independent_formula(lag, mass):
    kc, dan = data(900)
    kc[650, 0] = min(1.0, 1 / mass)
    dan[650 + lag, 0] = mass
    r = bridge_reference(kc, dan, *maps())
    expected = min(1.0, 1 / mass) * mass * kernel(lag * 0.2)
    assert r["unconstrained_pair"][0] == pytest.approx(expected, abs=2e-13)
    assert r["double_gains"][0] == pytest.approx(1 + expected, abs=1e-11)
    assert r["edge_phases"][:, 0, 2].sum() == pytest.approx(expected, abs=2e-13)
    assert r["gains"][0] == np.float32(1 + expected)
    assert not r["bound_counts"].any()


@pytest.mark.parametrize("seed", [7, 23, 51])
@pytest.mark.parametrize("learning", [True, False])
def test_all_bridge_fields_against_separately_frozen_producer(seed, learning):
    kc, dan = data(1601)
    rng = np.random.default_rng(seed)
    kc[:] = (rng.random(kc.shape) < 0.03) * rng.random(kc.shape)
    dan[:] = (rng.random(dan.shape) < 0.04) * 3
    initial = np.array([0.5, 0.75, 1.0, 1.5], np.float32)
    args = (*maps(),)
    before = [a.copy() for a in (kc, dan, *args, initial)]
    a = bridge_reference(kc, dan, *args, initial=initial, learning=learning)
    p = replay(kc, dan, *args, initial=initial, learning=learning)
    for name in p:
        assert a[name].shape == p[name].shape and a[name].dtype == p[name].dtype
        if name in ["publication_counts", "bound_counts", "gains", "electrical_gains"]:
            np.testing.assert_array_equal(a[name], p[name])
        elif "double_gains" in name:
            np.testing.assert_allclose(a[name], p[name], atol=1e-11, rtol=0)
        else:
            np.testing.assert_allclose(a[name], p[name], atol=2e-11, rtol=1e-12)
    for original, saved in zip((kc, dan, *args, initial), before, strict=True):
        np.testing.assert_array_equal(original, saved)


@pytest.mark.parametrize("where", ["none", "before", "at"])
def test_quiet_no_dan_and_cold_onset(where):
    kc, dan = data(501)
    kc[:] = 1
    if where != "none":
        dan[499 if where == "before" else 500] = 2
    r = bridge_reference(kc, dan, *maps())
    np.testing.assert_array_equal(r["gains"], 1)
    if where != "at":
        assert not r["edge_phases"][..., :5].any()
        assert not r["endpoint_dan"].any()
    else:
        assert r["edge_phases"][..., 0].sum() > 0
    np.testing.assert_array_equal(r["publication_counts"][:, 0], [1, 0, 0, 1])
    assert not r["edge_phases"][:, 1].any()


@pytest.mark.parametrize("initial", [0.5, 1.0, 1.5])
@pytest.mark.parametrize("learning", [False, True])
def test_bound_contacts_and_frozen_checkpoint_policy(initial, learning):
    kc, dan = data(520)
    checkpoint = np.full(4, initial, np.float32)
    r = bridge_reference(kc, dan, *maps(), initial=checkpoint, learning=learning)
    assert r["gains"].tobytes() == checkpoint.tobytes()
    for edge in [0, 2, 3]:
        np.testing.assert_array_equal(
            r["bound_counts"][:, edge], [21 * (initial == 0.5), 21 * (initial == 1.5)]
        )
    assert not r["bound_counts"][:, 1].any()


def test_clipping_uses_interval_accumulator_not_pair_gain():
    kc, dan = data(700)
    kc[510, 0] = 1
    dan[520, 0] = 2**32
    r = bridge_reference(kc, dan, *maps())
    assert r["unconstrained_pair"][0] < -0.5
    assert r["double_gains"][0] == 0.5
    assert r["bound_counts"][0, 0] > 0
    assert r["gains"][1] == 1
    np.testing.assert_allclose(r["edge_phases"][:, :, 3].sum(0), r["double_gains"] - 1, atol=1e-11, rtol=0)
    np.testing.assert_array_equal(r["edge_phases"][:, :, 4].sum(0), r["gains"].astype(float) - 1)


def test_separate_phase_areas_match_direct_event_quadrature():
    kc, dan = data(1600)
    ke, de = [(510, 0.5), (900, 1.0), (1520, 0.25)], [(530, 2.0), (1300, 3.0), (1599, 4.0)]
    for t, x in ke:
        kc[t, 0] = x
    for t, x in de:
        dan[t, 0] = x
    r = bridge_reference(kc, dan, *maps())

    def signals(t, events):
        rr = ee = 0.0
        for step, x in events:
            age = t - step * 0.2
            if age >= 0:
                rr += x * math.exp(-age / 100) / 100
                ee += 1.25 * x * math.exp(-age / 500) * (-math.expm1(-0.008 * age))
        return rr, ee

    for phase, (start, end) in enumerate([(100, 130), (130, 300), (300, 320), (320, math.inf)]):
        cuts = sorted({start, end} | {t * 0.2 for t, _ in ke + de if start < t * 0.2 < end})
        for field in (0, 1):

            def f(t):
                kr, kk = signals(t, ke)
                dr, dd = signals(t, de)
                return 0.00048 * (kr * dd if field == 0 else -kk * dr)

            expected = sum(quad(f, a, b, epsabs=1e-14, epsrel=1e-12)[0] for a, b in zip(cuts, cuts[1:]))
            assert r["edge_phases"][phase, 0, field] == pytest.approx(expected, abs=2e-12)
    np.testing.assert_array_equal(r["publication_counts"][:, 0], [150, 850, 100, 1])


@pytest.mark.parametrize("sign", [-1, 1])
@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_exact_guard_boundary_and_neighbor_ticks(sign, offset):
    # S=16,Q=144 gives exact equality; both signs and a two-tick neighbor.
    ticks = [sign * t for t in [10, 6, 2, -2, 0, 0, 0, 0]]
    ticks[-1] += 2 * offset
    gains = np.array([[1 + t / 2**24] for t in ticks], np.float32)
    result = guard_cell(gains)
    actual = [int((Fraction(float(x)) - 1) * 2**24) for x in gains[:, 0]]
    n = len(actual)
    s = sum(actual)
    q = sum(x * x for x in actual)
    mean = Fraction(s, n)
    variance = Fraction(q, n - 1) - Fraction(s * s, n * (n - 1))
    assert result["ticks"] == actual
    assert result["point_pass"] == (4 * mean * mean <= variance)
    if offset == 0:
        assert 4 * mean * mean == variance and result["point_pass"]


@pytest.mark.parametrize("ticks", [[0] * 8, list(range(-7, 8, 2)), [10] * 8, [0] * 7 + [100]])
def test_guard_sign_permutation_and_zero_invariants(ticks):
    # Use even ticks so both sides of unit are exactly representable.
    gains = np.array([[1 + 2 * t / 2**24] for t in ticks], np.float32)
    a = guard_cell(gains)
    assert guard_cell(gains[::-1])["point_pass"] == a["point_pass"]
    assert guard_cell(2 - gains)["point_pass"] == a["point_pass"]


@pytest.mark.parametrize("case", ["dtype", "count", "empty", "nan", "low", "high"])
def test_guard_malformed_family(case):
    x = np.ones((8, 2), np.float32)
    if case == "dtype":
        x = x.astype(np.float64)
    elif case == "count":
        x = x[:7]
    elif case == "empty":
        x = x[:, :0]
    else:
        x[0, 0] = {"nan": np.nan, "low": 0.4, "high": 1.6}[case]
    with pytest.raises(ValueError):
        guard_cell(x)


@pytest.mark.parametrize("direction", [-1, 1])
def test_endpoint_rounding_ambiguity_is_not_pass(direction):
    lo = float(np.float32(0.75))
    hi = float(np.nextafter(np.float32(0.75), np.float32(1)))
    center = (lo + hi) / 2
    reference = {
        "double_gains": np.array([center]),
        "gains": np.array([center], np.float32),
        "electrical_double_gains": np.array([center]),
        "electrical_gains": np.array([center], np.float32),
    }
    producer = {k: v.copy() for k, v in reference.items()}
    for n in ["double_gains", "electrical_double_gains"]:
        producer[n][0] += direction * 1e-12
        producer[n.replace("double_", "")] = producer[n].astype(np.float32)
    result = compare_endpoints(reference, producer)
    mismatch = any(not np.array_equal(producer[k], reference[k]) for k in ["gains", "electrical_gains"])
    assert result["status"] == ("rounding_ambiguous" if mismatch else "passed")


def test_endpoint_outside_fixed_allowance_fails_even_if_same_f32():
    r = {
        n: np.ones(2, np.float64 if "double" in n else np.float32)
        for n in ["double_gains", "gains", "electrical_double_gains", "electrical_gains"]
    }
    p = {k: v.copy() for k, v in r.items()}
    p["double_gains"][0] += 2e-11
    assert compare_endpoints(r, p)["status"] == "failed_double_comparison"


@pytest.fixture(scope="module")
def row_fixture():
    from darela_release import release_events

    kc = np.zeros((501, 2), np.int32)
    dan = np.zeros((501, 24), np.int32)
    kc[500, 0] = 1
    dan[0, 0] = 1
    dan[500, 0] = 1
    trace = np.column_stack((kc, dan, np.zeros((501, 1), np.int32)))
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
        plastic_kc_indices=maps()[0].astype(np.int32),
        plastic_compartments=maps()[1].astype(np.int32),
        plastic_mask=maps()[2].astype(np.uint8),
        plastic_groups=maps()[3].astype(np.int32),
    )
    release = release_events(dan, m["dan_compartments"])
    v = {**release, **replay(kc, release["pooled_release"], *maps())}
    v.update(
        initial_gains=np.ones(4, np.float32),
        original_gains=np.ones(4, np.float32),
        original_gain_delta=np.zeros(4, np.float32),
        raw_dan_events=dan.copy(),
        raw_kc_event_totals=kc.sum(0, dtype=np.int64),
        raw_dan_event_totals=dan.sum(0, dtype=np.int64),
        raw_compartment_event_counts=np.column_stack(
            [dan[:, :2].sum(1, dtype=np.int64), dan[:, 2:].sum(1, dtype=np.int64)]
        ),
    )
    v.update({"map__" + k: a.copy() for k, a in m.items()})
    return trace, m, v


def test_complete_synthetic_row_is_accepted(row_fixture):
    from audit_darela_shadow import audit_case

    trace, m, v = row_fixture
    report, ref = audit_case(
        trace, m, v, original=v["original_gains"], original_delta=v["original_gain_delta"]
    )
    assert report["status"] == "passed"
    assert len(ref) > 10 and report["release_values_checked"] == sum(
        v[k].size
        for k in ["per_cell_release", "pooled_release", "state_before", "state_after", "endpoint_state"]
    )


@pytest.mark.parametrize(
    "key",
    [
        "state_before",
        "state_after",
        "endpoint_state",
        "per_cell_release",
        "pooled_release",
        "endpoint_dan",
        "edge_phases",
        "group_phases",
    ],
)
def test_same_shape_false_measurement_family_is_not_accepted(row_fixture, key):
    from audit_darela_shadow import audit_case

    trace, m, saved = row_fixture
    v = {k: a.copy() for k, a in saved.items()}
    v[key].flat[-1] += 0.001
    report, _ = audit_case(
        trace, m, v, original=saved["original_gains"], original_delta=saved["original_gain_delta"]
    )
    assert report["status"] != "passed"


@pytest.mark.parametrize(
    "key",
    [
        "map__body_ids",
        "raw_dan_events",
        "raw_kc_event_totals",
        "raw_dan_event_totals",
        "raw_compartment_event_counts",
        "initial_gains",
        "original_gains",
        "original_gain_delta",
        "publication_counts",
        "bound_counts",
    ],
)
def test_discrete_identity_and_retained_accounting_family(row_fixture, key):
    from audit_darela_shadow import audit_case

    trace, m, saved = row_fixture
    v = {k: a.copy() for k, a in saved.items()}
    v[key].flat[-1] += 1
    with pytest.raises(ValueError):
        audit_case(trace, m, v, original=saved["original_gains"], original_delta=saved["original_gain_delta"])


@pytest.mark.parametrize("key", ["gains", "electrical_gains"])
def test_publication_forgery_is_failure_not_rounding_ambiguity(key):
    r = {
        n: np.ones(2, np.float64 if "double" in n else np.float32)
        for n in ["double_gains", "gains", "electrical_double_gains", "electrical_gains"]
    }
    p = {k: v.copy() for k, v in r.items()}
    p[key][0] = np.nextafter(np.float32(1), np.float32(2))
    assert compare_endpoints(r, p)["status"] == "failed_publication"


def test_bound_loader_valid_numeric_control(tmp_path):
    from audit_darela_shadow import load_bound_npz
    import hashlib

    p = tmp_path / "numbers.npz"
    np.savez(p, hello=np.arange(9, dtype=np.int32))
    raw = p.read_bytes()
    item = {"path": str(p), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    np.testing.assert_array_equal(load_bound_npz(p, item)["hello"], np.arange(9, dtype=np.int32))


@pytest.mark.parametrize(
    "kind",
    [
        "object",
        "extra_payload",
        "missing_payload",
        "huge_shape",
        "duplicate_member",
        "foreign_path",
        "wrong_hash",
        "negative_size",
        "float_size",
        "symlink",
    ],
)
def test_bound_loader_allocation_identity_and_path_family(tmp_path, kind):
    from audit_darela_shadow import load_bound_npz
    import hashlib
    import io
    import zipfile

    p = tmp_path / "numbers.npz"
    if kind in ["extra_payload", "missing_payload", "huge_shape"]:
        z = io.BytesIO()
        np.lib.format.write_array_header_1_0(
            z, dict(descr="<f8", fortran_order=False, shape=(2**40 if kind == "huge_shape" else 1,))
        )
        raw = z.getvalue() + (b"0" * 16 if kind == "extra_payload" else b"")
        with zipfile.ZipFile(p, "w") as f:
            f.writestr("a.npy", raw)
    elif kind == "object":
        np.savez(p, a=np.array([{}], object))
    elif kind == "duplicate_member":
        z = io.BytesIO()
        np.save(z, np.array([1.0]))
        with zipfile.ZipFile(p, "w") as f:
            f.writestr("a.npy", z.getvalue())
            f.writestr("a.npy", z.getvalue())
    else:
        np.savez(p, a=np.arange(2))
    raw = p.read_bytes()
    item = {"path": str(p), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    if kind == "foreign_path":
        item["path"] = str(tmp_path / "other.npz")
    elif kind == "wrong_hash":
        item["sha256"] = "0" * 64
    elif kind == "negative_size":
        item["bytes"] = -1
    elif kind == "float_size":
        item["bytes"] = float(len(raw))
    elif kind == "symlink":
        q = tmp_path / "alias.npz"
        q.symlink_to(p)
        p = q
        item["path"] = str(p)
    with pytest.raises(ValueError):
        load_bound_npz(p, item)


def synthetic_archive(tmp_path, row_fixture):
    import hashlib
    import json
    import audit_darela_shadow as a
    import run_dan_causal_prefix_v2 as reader

    trace, m, v = row_fixture

    def bound(p):
        return dict(path=str(p), bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())

    def write(p, x):
        p.write_text(json.dumps(x, sort_keys=True))

    src = tmp_path / "source.txt"
    src.write_text("SYNTHETIC fixture")
    plan = dict(
        schema=1,
        analysis="darela-reset-release-shadow-v1",
        root=str(a.ROOT),
        output_root=str(tmp_path),
        wall_seconds_cap=1200,
        contract=a.SCIENTIFIC_CONTRACT,
        expected_rows=reader.expected_rows(),
        capture_dir=str(tmp_path / "capture"),
        samples_path=str(tmp_path / "map.npz"),
        run_dirs={r: str(tmp_path / r) for r in reader.RUNS},
        source_snapshot={},
        context_plan=str(src),
        preregistration=str(src),
        audit_contract=str(src),
        reviews=[str(src)],
        inputs=[bound(src)],
    )
    plan["run_id"] = (
        "darela-shadow-"
        + hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:20]
    )
    pp = tmp_path / "plan.json"
    write(pp, plan)
    parent = tmp_path / plan["run_id"]
    out = parent / "result"
    out.mkdir(parents=True)
    write(out / "identity.json", dict(run_id=plan["run_id"], plan=plan, plan_sha256=bound(pp)["sha256"]))
    rows = []
    journal = []
    for i, meta in enumerate(plan["expected_rows"]):
        p = out / f"case_{i:02d}.npz"
        np.savez_compressed(p, **v)
        detail = dict(
            index=i,
            metadata=meta,
            artifact=bound(p),
            arrays={k: a.fingerprint(x) for k, x in v.items()},
            fields=[
                "positive",
                "negative",
                "attempted",
                "applied_double",
                "applied_published",
                "low_count",
                "high_count",
                "absolute_area",
            ],
            original_electrical_available=False,
            gain_bound_observations=0,
        )
        jp = out / f"case_{i:02d}.json"
        write(jp, detail)
        journal.extend(
            [dict(event=e, index=i, helper=h) for h in ["release", "bridge"] for e in ["intent", "returned"]]
        )
        journal.append(dict(event="complete", index=i, detail=bound(jp)))
        rows.append(dict(metadata=meta, gains=v["gains"], original_gains=v["original_gains"]))
    (out / "attempts.jsonl").write_text("".join(json.dumps(x) + "\n" for x in journal))
    write(
        out / "status.json",
        dict(
            status="completed",
            attempted=32,
            completed=32,
            invocations=dict(release=32, bridge=32),
            returned=dict(release=32, bridge=32),
            wall_seconds=1.0,
        ),
    )
    summary = dict(
        status="computed",
        run_id=plan["run_id"],
        screen="pending_independent_audit",
        completed=32,
        candidate_guards=a.guards_for_rows(rows, m, "gains"),
        original_guards=a.guards_for_rows(rows, m, "original_gains"),
        gain_bound_observations=0,
        provisional_screen="passed_necessary_untaught_screen",
        native_calls=0,
        network_calls=0,
    )
    write(out / "summary.json", summary)
    write(
        out / "completion.json",
        dict(
            status="complete",
            run_id=plan["run_id"],
            completed=32,
            elapsed_through_summary=1.0,
            bindings=[
                bound(out / n) for n in ["identity.json", "status.json", "summary.json", "attempts.jsonl"]
            ],
        ),
    )
    write(
        parent / "parent-result.json",
        dict(
            status="completed",
            run_id=plan["run_id"],
            plan_sha256=bound(pp)["sha256"],
            child_reaped=True,
            timed_out=False,
            exit_code=0,
            wall_seconds_cap=1200,
            wall_seconds=2.0,
            child_completion=bound(out / "completion.json"),
        ),
    )

    def loader(plan, store, guard):
        return m, (
            (i, meta, trace, v["original_gains"], v["original_gain_delta"], None)
            for i, meta in enumerate(plan["expected_rows"])
        )

    return pp, out, loader, bound


def test_full32_synthetic_artifact_audit_and_no_reuse(tmp_path, row_fixture):
    import audit_darela_shadow as a

    pp, source, loader, _ = synthetic_archive(tmp_path, row_fixture)
    out = tmp_path / "audit"
    result = a.audit(pp, source, out, _source_loader=loader, _check_runtime=False)
    assert result["status"] == "completed" and result["completed"] == 32
    import json

    assert json.loads((out / "status.json").read_text())["status"] == "completed"
    assert len(json.loads((out / "completion.json").read_text())["bindings"]) == 66
    assert result["numerical_status"] == "passed" and result["screen"] == "passed_necessary_untaught_screen"
    assert len(result["candidate_guards"]) == len(result["original_guards"]) == 8
    assert len(list(out.glob("reference_*.npz"))) == 32
    with pytest.raises(FileExistsError):
        a.audit(pp, source, out, _source_loader=loader, _check_runtime=False)


@pytest.mark.parametrize(
    "kind",
    [
        "parent_error",
        "child_error",
        "row_metadata",
        "missing_row",
        "archive_change",
        "descriptive_units",
        "unknown_screen",
        "helper_journal",
    ],
)
def test_terminal_identity_and_summary_failure_family(tmp_path, row_fixture, kind):
    import audit_darela_shadow as a
    import json

    pp, source, loader, bound = synthetic_archive(tmp_path, row_fixture)
    if kind == "parent_error":
        (source.parent / "terminal-error.json").write_text("{}")
    elif kind == "child_error":
        (source / "terminal-error.json").write_text("{}")
    elif kind == "missing_row":
        (source / "case_31.json").unlink()
    elif kind == "archive_change":
        (source / "case_00.npz").write_bytes(b"broken")
    else:
        path = source / (
            "case_00.json"
            if kind == "row_metadata"
            else "attempts.jsonl"
            if kind == "helper_journal"
            else "summary.json"
        )
        if kind == "helper_journal":
            path.write_text(path.read_text().replace('"helper": "bridge"', '"helper": "release"'))
        else:
            x = json.loads(path.read_text())
            if kind == "row_metadata":
                x["metadata"]["seed"] += 1
            elif kind == "descriptive_units":
                next(iter(x["candidate_guards"].values()))["mean"] = 123.0
            else:
                x["provisional_screen"] = "invented-success"
            path.write_text(json.dumps(x))
        if kind in ["descriptive_units", "unknown_screen", "helper_journal"]:
            completion = json.loads((source / "completion.json").read_text())
            completion["bindings"] = [
                bound(source / p) for p in ["identity.json", "status.json", "summary.json", "attempts.jsonl"]
            ]
            (source / "completion.json").write_text(json.dumps(completion))
            parent = json.loads((source.parent / "parent-result.json").read_text())
            parent["child_completion"] = bound(source / "completion.json")
            (source.parent / "parent-result.json").write_text(json.dumps(parent))
    result = a.audit(pp, source, tmp_path / "audit", _source_loader=loader, _check_runtime=False)
    assert result["status"] == "failed"
    assert (tmp_path / "audit/terminal-error.json").is_file()


@pytest.mark.parametrize("stage", ["work", "summary", "completion", "final_source"])
def test_audit_cap_and_finalization_preserve_failure(tmp_path, row_fixture, monkeypatch, stage):
    import audit_darela_shadow as a

    pp, source, loader, _ = synthetic_archive(tmp_path, row_fixture)
    now = [0.0]
    real = a.write_json

    def clock():
        return now[0]

    def write(path, value):
        real(path, value)
        if stage == "work" and path.name == "status.json":
            now[0] = 580.0
        elif stage == "summary" and path.name == "audit.json":
            now[0] = 600.0
        elif stage == "completion" and path.name == "completion.json":
            now[0] = 600.0
        elif stage == "final_source" and path.name == "row_31.json":
            (tmp_path / "source.txt").write_text("changed")

    monkeypatch.setattr(a, "write_json", write)
    result = a.audit(pp, source, tmp_path / "audit", _source_loader=loader, _check_runtime=False, clock=clock)
    assert result["status"] in ["failed", "budget_stopped"]
    assert (tmp_path / "audit/terminal-error.json").is_file()


def test_guard_descriptions_use_trial_sums_not_edge_means():
    import audit_darela_shadow as a
    import run_dan_causal_prefix_v2 as reader

    m = {"plastic_compartments": np.array([0, 0, 1, 1]), "plastic_mask": np.ones(4, np.uint8)}
    rows = [dict(metadata=r, gains=np.full(4, 0.75, np.float32)) for r in reader.expected_rows()]
    for v in a.guards_for_rows(rows, m, "gains").values():
        assert v["mean"] == -0.5 and v["edge_count"] == 2 and v["sample_sd"] == 0 and v["limit"] == 0


def test_parent_checks_every_reference_binding_and_status(tmp_path, row_fixture):
    import audit_darela_shadow as a
    import launch_audit_darela_shadow as parent

    pp, source, loader, _ = synthetic_archive(tmp_path, row_fixture)
    out = tmp_path / "audit"
    report = a.audit(pp, source, out, _source_loader=loader, _check_runtime=False)
    assert parent.validate_result(out, report["run_id"])["status"] == "completed"
    target = out / "reference_31.npz"
    target.write_bytes(target.read_bytes()[:20])
    with pytest.raises(ValueError):
        parent.validate_result(out, report["run_id"])


@pytest.mark.parametrize("returncode", [0, 7])
def test_supervisor_preserves_exit_and_single_thread_environment(tmp_path, monkeypatch, returncode):
    import launch_audit_darela_shadow as parent
    import subprocess

    seen = []

    def run(command, **kwargs):
        seen.append((command, kwargs))
        return subprocess.CompletedProcess(command, returncode)

    monkeypatch.setattr(subprocess, "run", run)
    value = parent.supervise(["synthetic-command"], tmp_path, tmp_path, 599.0)
    assert value == dict(exit_code=returncode, timed_out=False, child_reaped=True)
    assert len(seen) == 1 and seen[0][1]["timeout"] == 599.0
    assert all(
        seen[0][1]["env"][k] == "1"
        for k in ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]
    )


def test_supervisor_real_tiny_timeout_kills_and_reaps(tmp_path):
    import launch_audit_darela_shadow as parent
    import sys

    value = parent.supervise([sys.executable, "-c", "import time; time.sleep(5)"], tmp_path, tmp_path, 0.02)
    assert value == dict(exit_code=None, timed_out=True, child_reaped=True)
