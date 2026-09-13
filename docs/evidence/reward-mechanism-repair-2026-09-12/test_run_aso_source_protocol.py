"""Toy schedules only: no numerical evaluation of the frozen 28-case source matrix."""

import copy
import importlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def api():
    assert importlib.util.find_spec("run_aso_source_protocol") is not None, "protocol runner not implemented"
    return importlib.import_module("run_aso_source_protocol")


def protocol(name="toy"):
    return dict(
        id=name,
        source="synthetic test fixture",
        duration_s=100,
        odor_a_intervals_s=[[1, 2]],
        odor_b_intervals_s=[[4, 5]],
        dan_intervals_s=[[1, 2], [4, 5], [7, 8]],
        test_windows_s=[[60, 100]],
    )


def pathway(name="both"):
    return dict(id=name, da_enabled=name in ("both", "da_only"), no_enabled=name in ("both", "no_only"))


def toy_plan(api):
    # Reading a frozen timing declaration is not executing any source case.
    p = api.load_frozen_plan(Path(__file__).with_name("aso-source-protocol-plan-2026-09-13.json"))
    p["protocols"] = [protocol(), protocol("toy_second")]
    p["expected_case_count"] = 8
    return p


def test_exact_stimulus_union_classes_and_finite_observations(api):
    p = protocol()
    saved = copy.deepcopy(p)
    a = api.calculate_case(p, pathway())
    np.testing.assert_array_equal(a["segment_times_s"], [0, 1, 2, 4, 5, 7, 8, 100])
    expected_kc = np.array(
        [[0, 0, 0, 0], [1, 0, 1, 0], [0, 0, 0, 0], [0, 1, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        bool,
    )
    np.testing.assert_array_equal(a["segment_inputs"][:, :, 0], expected_kc)
    np.testing.assert_array_equal(
        a["segment_inputs"][:, :, 1], np.repeat([[0], [1], [0], [1], [0], [1], [0]], 4, axis=1)
    )
    assert a["segment_inputs"].dtype == np.bool_
    assert a["segment_states"].shape == (8, 4, 4)
    np.testing.assert_array_equal(a["observation_times_s"], [[60, 70, 100]])
    np.testing.assert_array_equal(a["observation_segment_indices"], [[6, 6, 6]])
    assert a["observation_states"].shape == (1, 3, 4, 4)
    np.testing.assert_array_equal(a["segment_states"][:, 3, :], 0)
    d_at_2 = -np.expm1(-4.3 / 60)
    assert a["segment_states"][2, 0, 0] == pytest.approx(d_at_2)
    assert a["segment_states"][4, 0, 0] == pytest.approx(d_at_2 * np.exp(-0.26 / 60))
    assert a["segment_states"][4, 1, 0] == pytest.approx(d_at_2)
    assert a["segment_states"][-1, 2, 1] > a["segment_states"][-1, 2, 3] > 0
    np.testing.assert_array_equal(
        a["segment_weights"], (1 - a["segment_states"][..., 2]) * (1 + a["segment_states"][..., 3])
    )
    assert p == saved


def test_passive_query_insertion_does_not_change_trajectory_or_other_observations(api):
    p = protocol()
    first = api.calculate_case(p, pathway())
    p["test_windows_s"].insert(0, [20, 50])
    second = api.calculate_case(p, pathway())
    for key in ("segment_times_s", "segment_inputs", "segment_states", "segment_weights"):
        np.testing.assert_array_equal(first[key], second[key])
    np.testing.assert_array_equal(first["observation_states"], second["observation_states"][1:])


def test_boundary_and_duplicate_queries_use_continuous_state(api):
    p = protocol()
    p["test_windows_s"] = [[8, 38]]
    a = api.calculate_case(p, pathway())
    np.testing.assert_array_equal(a["observation_times_s"], [[8, 8, 38]])
    np.testing.assert_array_equal(a["observation_segment_indices"], [[6, 6, 6]])
    np.testing.assert_array_equal(a["observation_states"][0, 0], a["segment_states"][6])
    np.testing.assert_array_equal(a["observation_states"][0, 0], a["observation_states"][0, 1])


def test_all_pathways_factorize_and_neither_stays_resting(api):
    a = {
        name: api.calculate_case(protocol(), pathway(name))
        for name in ("both", "da_only", "no_only", "neither")
    }
    for key in ("segment_states", "observation_states"):
        np.testing.assert_array_equal(a["da_only"][key][..., [1, 3]], 0)
        np.testing.assert_array_equal(a["no_only"][key][..., [0, 2]], 0)
        np.testing.assert_array_equal(a["both"][key][..., [0, 2]], a["da_only"][key][..., [0, 2]])
        np.testing.assert_array_equal(a["both"][key][..., [1, 3]], a["no_only"][key][..., [1, 3]])
        np.testing.assert_array_equal(a["neither"][key], 0)
    np.testing.assert_array_equal(
        a["both"]["observation_weights"],
        a["da_only"]["observation_weights"] * a["no_only"]["observation_weights"],
    )


@pytest.mark.parametrize(
    "field", ["duration_s", "odor_a_intervals_s", "odor_b_intervals_s", "dan_intervals_s", "test_windows_s"]
)
@pytest.mark.parametrize("bad", [True, -1, float("nan"), float("inf"), "1"])
def test_timing_numeric_type_and_domain_family(api, field, bad):
    p = protocol()
    if field == "duration_s":
        p[field] = bad
    else:
        p[field][0][0] = bad
    with pytest.raises(ValueError):
        api.calculate_case(p, pathway())


@pytest.mark.parametrize(
    "field", ["odor_a_intervals_s", "odor_b_intervals_s", "dan_intervals_s", "test_windows_s"]
)
@pytest.mark.parametrize(
    "bad", [[[5, 4]], [[1, 1]], [[1, 101]], [[5, 6], [1, 2]], [[1, 4], [3, 5]], [[1]], True]
)
def test_interval_shape_order_and_overlap_family(api, field, bad):
    p = protocol()
    p[field] = bad
    with pytest.raises(ValueError):
        api.calculate_case(p, pathway())


def test_test_windows_are_passive_and_allow_exact_thirty_seconds(api):
    p = protocol()
    p["test_windows_s"] = [[60, 89]]
    with pytest.raises(ValueError):
        api.calculate_case(p, pathway())
    p["test_windows_s"] = [[0, 30]]
    with pytest.raises(ValueError):
        api.calculate_case(p, pathway())
    p["test_windows_s"] = [[60, 90]]
    a = api.calculate_case(p, pathway())
    assert a["observation_times_s"].tolist() == [[60, 60, 90]]


@pytest.mark.parametrize("field", ["da_enabled", "no_enabled"])
@pytest.mark.parametrize("bad", [1, 0.0, "true", None])
def test_pathway_flags_are_actual_booleans(api, field, bad):
    q = pathway()
    q[field] = bad
    with pytest.raises(ValueError):
        api.calculate_case(protocol(), q)


def test_pathway_id_is_bound_to_null_configuration(api):
    q = pathway("da_only")
    q["no_enabled"] = True
    with pytest.raises(ValueError):
        api.calculate_case(protocol(), q)


@pytest.mark.parametrize(
    "mutation",
    [
        "parameter",
        "bool_schema",
        "duration",
        "class_order",
        "missing_case",
        "duplicate_case",
        "pathway_order",
        "count_float",
    ],
)
def test_frozen_plan_acceptance_rejects_whole_contract_mutations_without_execution(api, tmp_path, mutation):
    p = api.load_frozen_plan(Path(__file__).with_name("aso-source-protocol-plan-2026-09-13.json"))
    if mutation == "parameter":
        p["parameters"]["A_D"] *= 2
    elif mutation == "bool_schema":
        p["schema"] = True
    elif mutation == "duration":
        p["protocols"][0]["duration_s"] += 1
    elif mutation == "class_order":
        p["kc_classes"].reverse()
    elif mutation == "missing_case":
        p["protocols"].pop()
    elif mutation == "duplicate_case":
        p["protocols"][1] = copy.deepcopy(p["protocols"][0])
    elif mutation == "pathway_order":
        p["pathways"].reverse()
    else:
        p["expected_case_count"] = 28.0
    f = tmp_path / "plan.json"
    f.write_text(json.dumps(p))
    with pytest.raises(ValueError):
        api.load_frozen_plan(f)


def test_frozen_json_rejects_duplicate_keys_and_nonfinite(api, tmp_path):
    for content in ('{"schema":1,"schema":1}', '{"schema":NaN}'):
        f = tmp_path / "bad.json"
        f.write_text(content)
        with pytest.raises(ValueError):
            api.load_frozen_plan(f)


def test_toy_execution_persists_order_complete_arrays_and_hashes_once(api, tmp_path):
    p = toy_plan(api)
    saved = copy.deepcopy(p)
    out = tmp_path / "result"
    status = api._run(p, out)
    assert status["status"] == "completed" and status["completed_case_count"] == 8
    assert [(r["protocol_id"], r["pathway_id"]) for r in status["cases"]] == [
        (q["id"], s["id"]) for q in p["protocols"] for s in p["pathways"]
    ]
    for row in status["cases"]:
        assert api.file_identity(out / row["file"]) == {k: row[k] for k in ("bytes", "sha256")}
        with np.load(out / row["file"], allow_pickle=False) as a:
            assert set(a.files) == set(api.calculate_case(protocol(), pathway()))
    assert p == saved
    before = {f.name: f.read_bytes() for f in out.iterdir()}
    with pytest.raises(FileExistsError):
        api._run(p, out)
    assert before == {f.name: f.read_bytes() for f in out.iterdir()}


@pytest.mark.parametrize(
    "failure",
    [
        "calculation",
        "npz_write",
        "truncated_npz",
        "invalid_state",
        "invalid_weight",
        "float_flags",
        "bad_shape",
    ],
)
def test_failure_preserves_prior_case_and_failed_disposition(api, tmp_path, monkeypatch, failure):
    p = toy_plan(api)
    original = api.calculate_case
    count = [0]

    def compute(*a, **kw):
        count[0] += 1
        if count[0] != 2:
            return original(*a, **kw)
        if failure == "calculation":
            raise ArithmeticError("synthetic failure")
        value = original(*a, **kw)
        if failure == "invalid_state":
            value["segment_states"][1, 0, 0] = float("nan")
        elif failure == "invalid_weight":
            value["observation_weights"][0, 0, 0] += 0.1
        elif failure == "float_flags":
            value["segment_inputs"] = value["segment_inputs"].astype(float)
        elif failure == "bad_shape":
            value["observation_states"] = value["observation_states"][:0]
        return value

    monkeypatch.setattr(api, "calculate_case", compute)
    if failure in ("npz_write", "truncated_npz"):
        old = api._write_npz

        def write(path, arrays):
            if path.name.startswith("01_"):
                if failure == "truncated_npz":
                    path.write_bytes(b"truncated archive")
                    return
                raise OSError("synthetic write failure")
            return old(path, arrays)

        monkeypatch.setattr(api, "_write_npz", write)
    out = tmp_path / "result"
    status = api._run(p, out)
    assert status["status"] == "failed" and status["completed_case_count"] == 1
    assert status["failed_case"] == 1 and status["error"]
    assert json.loads((out / "status.json").read_text())["status"] == "failed"
    assert (out / status["cases"][0]["file"]).exists()


def test_deadline_in_final_persistence_cannot_leave_completed_status(api, tmp_path, monkeypatch):
    now = [0.0]
    original = api._write_json

    def write(path, value):
        result = original(path, value)
        if path.name == "status.json" and value.get("status") == "completed":
            now[0] = 30.0
        return result

    monkeypatch.setattr(api, "_write_json", write)
    out = tmp_path / "result"
    status = api._run(toy_plan(api), out, clock=lambda: now[0])
    assert status["status"] == "failed"
    assert json.loads((out / "status.json").read_text())["status"] == "failed"


def test_input_identity_drift_is_failed_before_or_after_case(api, tmp_path, monkeypatch):
    p = toy_plan(api)
    calls = [0]
    original = api._input_identity

    def identity(*args):
        value = original(*args)
        calls[0] += 1
        if calls[0] > 1:
            value["helper_sha256"] = "0" * 64
        return value

    monkeypatch.setattr(api, "_input_identity", identity)
    status = api._run(p, tmp_path / "result")
    assert status["status"] == "failed" and status["error"]


def test_loaded_declaration_must_match_bound_plan_bytes_before_calculation(api, tmp_path, monkeypatch):
    path = Path(__file__).with_name("aso-source-protocol-plan-2026-09-13.json")
    p = api.load_frozen_plan(path)
    p["protocols"][0]["duration_s"] += 1

    def forbidden(*args, **kwargs):
        raise AssertionError("No source protocol calculation is authorized in this test")

    monkeypatch.setattr(api, "calculate_case", forbidden)
    with pytest.raises(ValueError):
        api._run(p, tmp_path / "result", plan_path=path)
    assert not (tmp_path / "result").exists()
