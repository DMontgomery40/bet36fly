"""Read saved source evidence using piecewise geometric H solutions; no solver."""

import hashlib
import json
from pathlib import Path

import numpy as np


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path.cwd()
    base = root / "output/collaboration/reward-mechanism-repair"
    contract_path = base / "darela-source-kernel-contract.json"
    envelope = json.loads(contract_path.read_text())
    contract = envelope["contract"]
    run_id = envelope["run_id"]
    identity = hashlib.sha256(
        json.dumps(contract, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()[:20]
    assert run_id == "darela-source-kernel-" + identity
    execution = base / (run_id + "-execution")
    result = execution / "result"
    parent = json.loads((execution / "execution.json").read_text())
    done = json.loads((result / "completion.json").read_text())
    summary = json.loads((result / "summary.json").read_text())
    assert not list(execution.rglob("terminal-error.json"))
    assert parent["status"] == done["status"] == "completed"
    assert summary["status"] == "computed"
    assert parent["exit_code"] == 0 and parent["reaped"] and not parent["timed_out"]
    assert parent["seconds_through_checks"] < contract["parent_seconds"] == 30
    assert done["seconds_through_summary"] < contract["child_seconds"] == 28
    assert parent["contract"]["sha256"] == digest(contract_path)
    assert parent["child_completion"]["sha256"] == digest(result / "completion.json")
    assert done["summary_sha256"] == digest(result / "summary.json")
    for item in (parent, done, summary):
        assert item["run_id"] == run_id
    for item in (done, summary):
        assert item["attempted_cases"] == item["completed_cases"] == 8
    assert len(summary["rows"]) == len(contract["cases"]) == 8
    for item in contract["bindings"]:
        path = Path(item["path"])
        assert path.stat().st_size == item["bytes"] and digest(path) == item["sha256"]
    rows, values, array_count = [], 0, 0
    for index, case in enumerate(contract["cases"]):
        record = summary["rows"][index]
        assert record == json.loads((result / f"case_{index:02d}.json").read_text())
        assert record["index"] == index and record["case"] == case and record["passed"]
        archive = result / f"case_{index:02d}.npz"
        assert digest(archive) == record["file"]["sha256"]
        n = int(case["end_s"] * 50)
        mask = np.zeros(n + 1)
        for start in case["bursts"]:
            first = round(start * 50)
            mask[first : first + 31] += 1
        assert int(mask[:-1].sum()) == case["expected_active_updates"]
        h = np.empty((n + 1, 3))
        h[0] = case["initial_H"]
        tau, q = np.array(case["tau_s"]), 1 + np.array(case["p"])
        edges = [0, *(np.flatnonzero(np.diff(mask[:-1])) + 1).tolist(), n]
        for a, b in zip(edges, edges[1:]):
            powers = np.arange(1, b - a + 1)[:, None]
            if mask[a] == 1:
                h[a + 1 : b + 1] = h[a] * q**powers
            else:
                assert mask[a] == 0
                h[a + 1 : b + 1] = 1 + (h[a] - 1) * (1 - 0.02 / tau) ** powers
        expected = dict(
            time=np.arange(n + 1) / 50, mask=mask, H=h, A_old=h[:-1].prod(axis=1), A_new=h[1:].prod(axis=1)
        )
        errors = {}
        with np.load(archive, allow_pickle=False) as saved:
            assert set(saved.files) == {
                f"{side}_{key}" for side in ("source", "reference") for key in expected
            }
            for name in saved.files:
                array, want = saved[name], expected[name.split("_", 1)[1]]
                assert array.dtype == np.float64 and array.shape == want.shape
                assert np.isfinite(array).all()
                np.testing.assert_allclose(array, want, atol=1e-12, rtol=1e-12)
                if name.endswith("mask"):
                    np.testing.assert_array_equal(array, want)
                errors[name] = float(np.max(np.abs(array - want)))
                array_count += 1
                values += array.size
        rows.append({"case": case["name"], "max_absolute_errors": errors})
    receipt = {
        "run_id": run_id,
        "status": "passed",
        "scope": "Independent saved-array review; no source imports or source/fit/neural execution",
        "oracle": "Piecewise geometric active H0*q^n and quiet 1+(H0-1)*(1-dt/tau)^n, inclusive integer-index masks",
        "atol": 1e-12,
        "rtol": 1e-12,
        "arrays_checked": array_count,
        "scalar_values_checked": values,
        "bindings_checked": len(contract["bindings"]),
        "maximum_absolute_error": max(max(r["max_absolute_errors"].values()) for r in rows),
        "rows": rows,
        "review_code_sha256": digest(Path(__file__)),
        "parent_execution_sha256": digest(execution / "execution.json"),
        "source_summary_sha256": digest(result / "summary.json"),
    }
    out = base / "darela-saved-kernel-root-review-2026-09-13.json"
    with out.open("x") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: value for key, value in receipt.items() if key != "rows"}))


if __name__ == "__main__":
    main()
