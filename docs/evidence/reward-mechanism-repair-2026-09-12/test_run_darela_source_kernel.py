"""Synthetic harness/reference tests; never imports the pinned DARELA package."""

import importlib.util
import json
import math
from pathlib import Path
import sys

import numpy as np
import pytest

P = Path(__file__).with_name("run_darela_source_kernel.py")
SPEC = importlib.util.spec_from_file_location("source_kernel_check", P)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def case(**updates):
    value = {
        "name": "synthetic",
        "bursts": [],
        "end_s": 1.0,
        "initial_H": [1.0, 1.0, 1.0],
        "expected_active_updates": 0,
        "p": [0.0105, -0.003, -0.0011],
        "tau_s": [7.5, 15.0, 900.0],
    }
    value.update(updates)
    return value


@pytest.mark.parametrize(
    "bursts,end,count",
    [([], 5, 0), ([0.34], 5, 31), ([0.34 + 5 * n for n in range(6)], 30, 186), ([0], 1, 31)],
)
def test_decimal_clock_inclusive_count(bursts, end, count):
    x = M.scalar_reference(case(bursts=bursts, end_s=end))
    assert int(x["mask"][:-1].sum()) == count
    assert x["time"][0] == 0 and x["time"][-1] == end


def test_clock_and_first_burst_endpoints():
    x = M.scalar_reference(case(bursts=[0.34], end_s=5))
    assert np.flatnonzero(x["mask"]).tolist() == list(range(17, 48))
    np.testing.assert_array_equal(x["H"][:18], np.ones((18, 3)))
    np.testing.assert_allclose(x["H"][18], 1 + np.array(case()["p"]), rtol=0, atol=1e-15)


@pytest.mark.parametrize("initial", [[1, 1, 1], [1.25, 0.75, 0.5], [0.4, 2, 3]])
def test_quiet_euler_closed_form(initial):
    c = case(initial_H=initial)
    x = M.scalar_reference(c)
    expected = 1 + (np.array(initial) - 1) * (1 - 0.02 / np.array(c["tau_s"])) ** 50
    np.testing.assert_allclose(x["H"][-1], expected, rtol=1e-12, atol=1e-12)


def test_source_active_euler_product_and_old_new_distinction():
    c = case(bursts=[0], end_s=0.4)
    x = M.scalar_reference(c)
    q = 1 + np.array(c["p"])
    np.testing.assert_allclose(x["H"][-1], q**20, rtol=1e-12, atol=1e-12)
    assert x["A_old"][0] == 1
    assert math.isclose(x["A_new"][0], math.prod(q), rel_tol=1e-15)
    assert x["A_new"][0] != x["A_old"][0]


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_comparison_rejects_nonfinite(bad):
    with pytest.raises(ValueError):
        M.compare(np.array([bad]), np.array([0.0]))


def test_comparison_tolerance_is_fixed_combined_envelope():
    M.compare(np.array([1.0 + 1.9e-12]), np.array([1.0]))
    with pytest.raises(ValueError):
        M.compare(np.array([1.0 + 2.1e-12]), np.array([1.0]))
    with pytest.raises(ValueError):
        M.compare(np.array([0.0]), np.array([[0.0]]))


def test_all_fixed_cases_have_expected_rows_and_no_concentration_fields():
    cases = M.fixed_cases()
    assert len(cases) == 8
    assert {tuple(c["tau_s"]) for c in cases} == {(7.5, 15, 900), (7.5, 12.5, 900)}
    assert all(c["p"] == [0.0105, -0.003, -0.0011] for c in cases)
    assert all(not {"DAp", "Vm", "Km"} & c.keys() for c in cases)


def test_hash_binding_detects_replaced_source(tmp_path):
    p = tmp_path / "source.py"
    p.write_text("original")
    r = M.record(p)
    M.check_bindings([r])
    p.write_text("changed")
    with pytest.raises(ValueError):
        M.check_bindings([r])


class FakeKernel:
    """Only a synthetic lifecycle double, not a source numerical reference."""

    def initialize(self, bursts, f, npulses, current):
        self.bursts, self.dt = bursts, 1 / f

    def _set_stimulation(self, end):
        r = M.scalar_reference(case(bursts=self.bursts, end_s=end))
        self.t, self.S = r["time"], r["mask"]

    def _set_kinetics(self):
        pass

    def _solve_kinetics(self, h, s):
        p = np.array([self.params[f"p{j}"] for j in (1, 2, 3)])
        tau = np.array([self.params[f"tau{j}"] for j in (1, 2, 3)])
        return h + self.dt * (50 * p * h * s + (1 - s) * (1 - h) / tau)


def fake_contract(tmp_path):
    binding = tmp_path / "binding.txt"
    binding.write_text("fixed")
    return {
        "run_id": "synthetic-only",
        "cases": [case()],
        "bindings": [M.record(binding)],
        "child_seconds": 28,
        "source_root": "unused",
        "dependency_root": "unused",
    }


def test_child_saves_complete_factor_arrays_and_hash_bound_terminal(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "load_kernel", lambda _: FakeKernel)
    out = tmp_path / "result"
    assert M.run_child(fake_contract(tmp_path), out) == 0
    final = json.loads((out / "completion.json").read_text())
    assert final["summary_sha256"] == M.record(out / "summary.json")["sha256"]
    assert not (out / "terminal-error.json").exists()
    with np.load(out / "case_00.npz", allow_pickle=False) as z:
        assert set(z.files) == {
            f"{side}_{key}"
            for side in ("source", "reference")
            for key in ("time", "mask", "H", "A_old", "A_new")
        }
        assert z["source_H"].shape == (51, 3)
    with pytest.raises(FileExistsError):
        M.run_child(fake_contract(tmp_path), out)


def test_failed_comparison_retains_arrays_and_stops(tmp_path, monkeypatch):
    class Wrong(FakeKernel):
        def _solve_kinetics(self, h, s):
            return h + 0.01

    monkeypatch.setattr(M, "load_kernel", lambda _: Wrong)
    out = tmp_path / "bad"
    contract = fake_contract(tmp_path)
    contract["cases"] *= 2
    assert M.run_child(contract, out) == 1
    row = json.loads((out / "case_00.json").read_text())
    assert row["passed"] is False and (out / "case_00.npz").exists()
    assert not (out / "case_01.npz").exists() and not (out / "completion.json").exists()
    err = json.loads((out / "terminal-error.json").read_text())
    assert err["completed_cases"] == 0 and err["attempted_cases"] == 1


def test_late_binding_change_invalidates_results(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "load_kernel", lambda _: FakeKernel)
    contract = fake_contract(tmp_path)
    original = M.evaluate_case

    def changed(*args):
        result = original(*args)
        Path(contract["bindings"][0]["path"]).write_text("changed")
        return result

    monkeypatch.setattr(M, "evaluate_case", changed)
    out = tmp_path / "changed"
    assert M.run_child(contract, out) == 1
    assert (out / "terminal-error.json").exists() and not (out / "completion.json").exists()


def test_contract_self_identity(tmp_path):
    p = tmp_path / "contract.json"
    body = {"schema": 1, "value": "fixed"}
    M.write_json(p, {"run_id": M.identity(body), "contract": body})
    assert M.read_contract(p)["run_id"] == M.identity(body)
    content = json.loads(p.read_text())
    content["contract"]["value"] = "changed"
    M.write_json(p, content)
    with pytest.raises(ValueError):
        M.read_contract(p)


@pytest.mark.parametrize("code,expected", [("print('synthetic')", 0), ("raise SystemExit(7)", 7)])
def test_external_supervisor_reaps_exit_and_preserves_streams(tmp_path, code, expected):
    command = [sys.executable, "-c", code]
    receipt = M.supervise(command, tmp_path, 3)
    assert receipt["exit_code"] == expected and receipt["reaped"]
    assert not receipt["timed_out"] and receipt["command"] == command
    assert (tmp_path / "stdout.txt").exists() and (tmp_path / "stderr.txt").exists()


def test_external_supervisor_kills_and_reaps_timeout(tmp_path):
    receipt = M.supervise([sys.executable, "-c", "import time; time.sleep(10)"], tmp_path, 0.03)
    assert receipt["timed_out"] and receipt["reaped"] and receipt["exit_code"] != 0


def test_child_deadline_after_completion_persistence_invalidates(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "load_kernel", lambda _: FakeKernel)
    contract = fake_contract(tmp_path)
    original = M.write_json
    expired = False

    def write(path, value):
        nonlocal expired
        original(path, value)
        if Path(path).name == "completion.json":
            expired = True

    def deadline(*_):
        if expired:
            raise TimeoutError("synthetic final-write expiry")

    monkeypatch.setattr(M, "write_json", write)
    monkeypatch.setattr(M, "check_deadline", deadline)
    out = tmp_path / "expired"
    assert M.run_child(contract, out) == 1
    assert (out / "completion.json").exists() and (out / "terminal-error.json").exists()


def test_parent_preserves_interpreter_invocation_and_rejects_child_failure(tmp_path, monkeypatch):
    contract = fake_contract(tmp_path)
    contract.pop("run_id")
    contract.update(interpreter="/synthetic/.venv/bin/python", parent_seconds=30)
    path = tmp_path / "contract.json"
    M.write_json(path, {"run_id": M.identity(contract), "contract": contract})
    commands = []

    def failed(command, out, seconds):
        commands.append(command)
        return {"exit_code": 7, "timed_out": False, "reaped": True, "seconds": 0.01}

    monkeypatch.setattr(M, "supervise", failed)
    out = tmp_path / "parent"
    assert M.run_parent(path, out) == 1
    assert commands[0][0] == "/synthetic/.venv/bin/python"
    assert (out / "terminal-error.json").exists() and not (out / "execution.json").exists()


@pytest.mark.parametrize(
    "fault",
    [
        "missing_completion",
        "missing_case",
        "failed_marker",
        "stale_identity",
        "stale_summary_hash",
        "summary_status",
        "summary_attempts",
        "truncated_rows",
        "wrong_index",
        "wrong_case",
        "failed_row",
        "changed_npz",
        "extra_case",
        "expired",
    ],
)
def test_saved_terminal_artifact_contract_family(tmp_path, monkeypatch, fault):
    monkeypatch.setattr(M, "load_kernel", lambda _: FakeKernel)
    contract = fake_contract(tmp_path)
    out = tmp_path / "result"
    assert M.run_child(contract, out) == 0
    M.validate_result(contract, out)
    summary = json.loads((out / "summary.json").read_text())
    completion = json.loads((out / "completion.json").read_text())
    if fault == "missing_completion":
        (out / "completion.json").unlink()
    elif fault == "missing_case":
        (out / "case_00.json").unlink()
    elif fault == "failed_marker":
        M.write_json(out / "terminal-error.json", {"status": "failed"})
    elif fault == "stale_identity":
        summary["run_id"] = "stale"
    elif fault == "stale_summary_hash":
        completion["summary_sha256"] = "0" * 64
    elif fault == "summary_status":
        summary["status"] = "failed"
    elif fault == "summary_attempts":
        summary["attempted_cases"] = 0
    elif fault == "truncated_rows":
        summary["rows"] = []
    elif fault in ("wrong_index", "wrong_case", "failed_row"):
        row = summary["rows"][0]
        row[{"wrong_index": "index", "wrong_case": "case", "failed_row": "passed"}[fault]] = {
            "wrong_index": 1,
            "wrong_case": {},
            "failed_row": False,
        }[fault]
        M.write_json(out / "case_00.json", row)
    elif fault == "changed_npz":
        (out / "case_00.npz").write_bytes(b"changed")
    elif fault == "extra_case":
        (out / "case_01.npz").write_bytes(b"extra")
    elif fault == "expired":
        completion["seconds_through_summary"] = contract["child_seconds"]
    M.write_json(out / "summary.json", summary)
    if fault != "stale_summary_hash":
        completion["summary_sha256"] = M.record(out / "summary.json")["sha256"]
    if fault != "missing_completion":
        M.write_json(out / "completion.json", completion)
    with pytest.raises((ValueError, FileNotFoundError)):
        M.validate_result(contract, out)


def test_parent_final_write_expiry_invalidates_earlier_completed_receipt(tmp_path, monkeypatch):
    contract = fake_contract(tmp_path)
    contract.pop("run_id")
    contract.update(interpreter="/synthetic/.venv/bin/python", parent_seconds=30)
    path = tmp_path / "contract.json"
    M.write_json(path, {"run_id": M.identity(contract), "contract": contract})
    monkeypatch.setattr(M, "load_kernel", lambda _: FakeKernel)

    def synthetic(command, out, seconds):
        assert M.run_child(M.read_contract(path), out / "result") == 0
        return {"exit_code": 0, "timed_out": False, "reaped": True, "seconds": 0.01}

    monkeypatch.setattr(M, "supervise", synthetic)
    write = M.write_json
    expired = False

    def late(path, value):
        nonlocal expired
        write(path, value)
        if Path(path).name == "execution.json":
            expired = True

    def deadline(*_):
        if expired:
            raise TimeoutError("synthetic parent receipt expiry")

    monkeypatch.setattr(M, "write_json", late)
    monkeypatch.setattr(M, "check_deadline", deadline)
    out = tmp_path / "parent"
    assert M.run_parent(path, out) == 1
    assert (out / "execution.json").exists() and (out / "terminal-error.json").exists()
