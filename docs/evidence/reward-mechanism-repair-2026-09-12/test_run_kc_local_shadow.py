"""Output-only runner boundaries; every numerical history here is synthetic."""

import importlib
import json
import socket

import numpy as np
import pytest
from scipy.sparse import csr_matrix


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network is outside these synthetic tests")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def module():
    return importlib.import_module("run_kc_local_shadow")


def fit_fixture():
    params = dict(
        tauKCdec=1.0,
        tauinp=0.2,
        tauadapt=2.0,
        adaptscale=0.1,
        tauinh=1.0,
        inhfactor=1.0,
        infp=0.5,
        slf=0.1,
        bline=0.0,
    )
    kd = [params[k] for k in ("tauKCdec", "tauinp", "tauadapt", "adaptscale")]
    wt = [params[k] for k in ("tauinh", "inhfactor", "infp", "slf")]
    parent = dict(
        status="completed",
        exit_code=0,
        elapsed_seconds=2.0,
        hard_timeout_seconds=120,
        no_restart=True,
        bindings_unchanged=True,
    )
    child = dict(
        schema="external-kc-calcium-scipy-refit-v1",
        status="completed",
        stage="final_source_recheck",
        elapsed_seconds=1.0,
        parameters=dict(
            KD=dict(zip(("tauKCdec", "tauinp", "tauadapt", "adaptscale"), kd)),
            WT=dict(zip(("tauinh", "inhfactor", "infp", "slf"), wt)),
            bline=0.0,
        ),
        stages=[
            dict(stage="decay_initialization", population=x, success=True, solver_status=2)
            for x in ("KD", "WT")
        ]
        + [
            dict(
                stage=x,
                success=True,
                solver_status=0,
                parameters=p,
                actual_objective_calls=20,
                iterations=3,
                objective=1.0,
            )
            for x, p in [("KD", kd), ("WT", wt)]
        ],
    )
    arrays = dict(kd_parameters=np.array(kd + [0.0]), wt_parameters=np.array(wt))
    return parent, child, arrays, params


def test_fit_valid_and_named_parameter_order():
    parent, child, arrays, params = fit_fixture()
    assert module().validate_fit(parent, child, arrays) == params


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "failed"),
        ("status", "timeout"),
        ("exit_code", 1),
        ("exit_code", False),
        ("elapsed_seconds", 120.0),
        ("elapsed_seconds", 121.0),
        ("elapsed_seconds", float("nan")),
        ("hard_timeout_seconds", 121),
        ("no_restart", False),
        ("bindings_unchanged", False),
    ],
)
def test_fit_parent_failure_family(field, value):
    parent, child, arrays, _ = fit_fixture()
    parent[field] = value
    with pytest.raises(ValueError):
        module().validate_fit(parent, child, arrays)


@pytest.mark.parametrize("stage", range(4))
@pytest.mark.parametrize("value", [False, 1, "true", None])
def test_every_fit_stage_must_really_converge(stage, value):
    parent, child, arrays, _ = fit_fixture()
    child["stages"][stage]["success"] = value
    with pytest.raises(ValueError):
        module().validate_fit(parent, child, arrays)


@pytest.mark.parametrize(
    "mutation",
    [
        "incomplete",
        "cap",
        "missing_stage",
        "wrong_order",
        "solver",
        "calls",
        "iterations",
        "nan_param",
        "npz_param",
        "npz_dtype",
        "negative_coefficient_time",
    ],
)
def test_fit_child_numeric_and_inventory_family(mutation):
    p, c, a, _ = fit_fixture()
    if mutation == "incomplete":
        c["status"] = "running"
    elif mutation == "cap":
        c["elapsed_seconds"] = 120
    elif mutation == "missing_stage":
        c["stages"].pop()
    elif mutation == "wrong_order":
        c["stages"].reverse()
    elif mutation == "solver":
        c["stages"][2]["solver_status"] = 1
    elif mutation == "calls":
        c["stages"][2]["actual_objective_calls"] = 3001
    elif mutation == "iterations":
        c["stages"][3]["iterations"] = 501
    elif mutation == "nan_param":
        c["parameters"]["WT"]["inhfactor"] = float("inf")
    elif mutation == "npz_param":
        a["kd_parameters"][0] = 2
    elif mutation == "npz_dtype":
        a["wt_parameters"] = a["wt_parameters"].astype("float32")
    else:
        c["parameters"]["KD"]["tauadapt"] = 0.001
    with pytest.raises(ValueError):
        module().validate_fit(p, c, a)


@pytest.mark.parametrize("index", range(32))
@pytest.mark.parametrize("field", ["panel", "run_id", "game", "seed_set", "seed"])
def test_every_selector_identity_mutation(index, field):
    r = module()
    rows = r.expected_rows()
    rows[index][field] = None
    with pytest.raises(ValueError):
        r.validate_rows(rows)


@pytest.mark.parametrize("mutation", ["short", "long", "reverse", "duplicate", "bool", "float"])
def test_matrix_order_and_typed_identity(mutation):
    r = module()
    rows = r.expected_rows()
    if mutation == "short":
        rows.pop()
    elif mutation == "long":
        rows.append(rows[-1])
    elif mutation == "reverse":
        rows.reverse()
    elif mutation == "duplicate":
        rows[1] = rows[0]
    elif mutation == "bool":
        rows[0]["panel"] = False
    else:
        rows[0]["seed"] = float(rows[0]["seed"])
    with pytest.raises(ValueError):
        r.validate_rows(rows)


def tiny_inputs():
    params = fit_fixture()[3]
    maps = dict(
        plastic_kc_indices=np.array([0, 1, 2]),
        plastic_compartments=np.array([0, 1, 1]),
        plastic_groups=np.array([0, 4, 5]),
        plastic_mask=np.array([1, 1, 0]),
        kc_columns=np.arange(3),
        dan_columns=np.array([3, 4]),
        dan_compartments=np.array([0, 1]),
    )
    return params, csr_matrix((3, 3)), maps, np.array([0, 1, 3], np.int8)


def test_local_endpoint_flush_and_subtype_retention():
    r = module()
    params, adj, maps, types = tiny_inputs()
    trace = np.zeros((2000, 5), np.uint8)
    trace[[0, 166, 167, 499, 1999], 0] = 1
    value = r.evaluate_history(trace, params, adj, maps, types)
    assert value["local_frame_states"].shape == (13, 4, 3)
    assert value["source_frame_counts"].shape == (12, 3)
    assert value["source_frame_counts"][:, 0].sum() == 5
    assert value["source_frame_counts"][0, 0] == 2
    assert value["source_frame_counts"][1, 0] == 1
    assert value["source_frame_counts"][-1, 0] == 1
    np.testing.assert_array_equal(value["weighted_event_totals"], trace[:, :3].sum(0))
    np.testing.assert_array_equal(value["kc_classes"], types)
    np.testing.assert_array_equal(value["gains"][2:], np.ones(1, np.float32))
    assert not value["edge_phases"][:, 2].any()


def test_inadmissible_source_row_fails_without_clipping():
    r = module()
    params, adj, maps, types = tiny_inputs()
    params["tauKCdec"] = 0.001
    trace = np.zeros((2000, 5), np.uint8)
    with pytest.raises(ValueError, match="coefficient"):
        r.evaluate_history(trace, params, adj, maps, types)


def setup_fake(monkeypatch, tmp_path):
    r = module()
    params, adj, maps, types = tiny_inputs()
    identity = dict(
        analysis="kc-local-shadow-v1",
        bindings=[],
        rows=r.expected_rows(),
        wall_cap_seconds=1200,
        helper_evaluations=32,
        circuit_calls=0,
        network_requests=0,
    )
    plan = dict(identity=identity, run_id=r.study_id(identity))
    out = tmp_path / plan["run_id"]
    monkeypatch.setattr(r, "load_runtime", lambda identity: (params, adj, maps, types, None))
    monkeypatch.setattr(
        r, "read_capture", lambda i, maps, capture: (np.zeros((2000, 5), np.uint8), np.ones(3, np.float32))
    )
    calls = []
    value = r.evaluate_history(np.zeros((2000, 5), np.uint8), params, adj, maps, types)

    def fake(*args, **kwargs):
        calls.append(len(calls))
        return {k: v.copy() for k, v in value.items()}

    monkeypatch.setattr(r, "evaluate_history", fake)
    return r, plan, out, calls


def test_complete_matrix_durable_and_no_overwrite(monkeypatch, tmp_path):
    r, plan, out, calls = setup_fake(monkeypatch, tmp_path)
    result = r.execute_plan(plan, out)
    assert result["status"] == "complete" and result["completed"] == 32 and len(calls) == 32
    assert len(result["guards"]) == 8
    assert len(list(out.glob("shadow_*.npz"))) == 32
    journal = [json.loads(x) for x in (out / "attempts.jsonl").read_text().splitlines()]
    assert [x["index"] for x in journal if x["event"] == "complete"] == list(range(32))
    with pytest.raises(FileExistsError):
        r.execute_plan(plan, out)
    assert len(calls) == 32


@pytest.mark.parametrize("failed_index", [0, 1, 15, 31])
def test_domain_failure_preserves_prefix_and_no_row_drop(monkeypatch, tmp_path, failed_index):
    r, plan, out, calls = setup_fake(monkeypatch, tmp_path)
    original = r.evaluate_history

    def fail(*args, **kwargs):
        if len(calls) == failed_index:
            raise ValueError("synthetic domain violation")
        return original(*args, **kwargs)

    monkeypatch.setattr(r, "evaluate_history", fail)
    result = r.execute_plan(plan, out)
    assert result["status"] == "failed" and result["screen"] == "invalid_or_incomplete"
    assert result["completed"] == failed_index and result["attempted"] == failed_index + 1
    assert len(calls) == failed_index


@pytest.mark.parametrize("name", ["row_00.json", "summary.json", "completion.json"])
def test_persistence_failure_never_claims_complete(monkeypatch, tmp_path, name):
    r, plan, out, calls = setup_fake(monkeypatch, tmp_path)
    real = r.write_json

    def fail(path, value):
        if path.name == name:
            raise OSError("synthetic disk failure")
        real(path, value)

    monkeypatch.setattr(r, "write_json", fail)
    result = r.execute_plan(plan, out)
    assert result["status"] == "failed" and result["screen"] == "invalid_or_incomplete"
    assert (out / "terminal-error.json").exists() or result["completed"] == 0


@pytest.mark.parametrize("raw", ['{"a":1,"a":2}', '{"a":NaN}', '{"a":1e400}'])
def test_strict_json(raw):
    with pytest.raises(ValueError):
        module().strict_json(raw)


@pytest.mark.parametrize("terminal", ["summary.json", "completion.json"])
@pytest.mark.parametrize("elapsed", [1199.999, 1200.0, 1201.0])
def test_terminal_clock_boundary(monkeypatch, tmp_path, terminal, elapsed):
    r, plan, out, calls = setup_fake(monkeypatch, tmp_path)
    now = [0.0]
    real = r.write_json

    def writer(path, value):
        real(path, value)
        if path.name == terminal:
            now[0] = elapsed

    monkeypatch.setattr(r, "write_json", writer)
    result = r.execute_plan(plan, out, clock=lambda: now[0])
    assert result["status"] == ("complete" if elapsed < 1200 else "budget_stopped")
    if elapsed >= 1200:
        assert result["screen"] == "invalid_or_incomplete"
        assert (out / "terminal-error.json").exists()


def test_source_hash_failure_before_any_evaluation(monkeypatch, tmp_path):
    r, plan, out, calls = setup_fake(monkeypatch, tmp_path)

    def changed(*args):
        raise ValueError("Source changed")

    monkeypatch.setattr(r, "verify_bindings", changed)
    result = r.execute_plan(plan, out)
    assert result["attempted"] == result["completed"] == 0 and not calls
    assert result["status"] == "failed"


def test_fit_audit_must_cover_exact_fit_artifacts(monkeypatch):
    r = module()
    audit = dict(
        status="passed_fixed_parameter_source_reproduction",
        run_id=r.FIT.name,
        all_snapshot_bytes_unchanged=True,
        input_snapshot=[],
        numeric_comparison={},
    )
    with pytest.raises(ValueError):
        r.validate_fit_audit(audit)


@pytest.mark.parametrize("shape,dtype", [((100000000,), "<f8"), ((), "<f8"), ((1,), "S3")])
def test_sparse_marker_declared_shape_rejects_before_numpy_load(tmp_path, monkeypatch, shape, dtype):
    import io
    import zipfile

    r = module()
    marker = io.BytesIO()
    np.lib.format.write_array_header_1_0(marker, dict(descr=dtype, fortran_order=False, shape=shape))
    path = tmp_path / "sparse.npz"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("format.npy", marker.getvalue())
        for name in ("data", "indices", "indptr", "shape"):
            z.writestr(name + ".npy", b"")

    def allocate(*args, **kwargs):
        raise AssertionError("No ndarray allocation before marker validation")

    monkeypatch.setattr(np, "load", allocate)
    with pytest.raises(ValueError):
        r.load_adjacency(path)
