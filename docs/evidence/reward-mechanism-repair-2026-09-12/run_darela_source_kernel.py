"""Bounded literal DARELA factor-kernel check, not a concentration solver."""

import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from decimal import Decimal, ROUND_HALF_EVEN

import numpy as np

ATOL = RTOL = 1e-12
KEYS = ("time", "mask", "H", "A_old", "A_new")


def write_json(path, value):
    with Path(path).open("w") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def record(path):
    path = Path(path).absolute()
    content = path.read_bytes()
    return {"path": str(path), "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def check_bindings(bindings):
    for expected in bindings:
        if record(expected["path"]) != expected:
            raise ValueError(f"changed binding: {expected['path']}")


def identity(body):
    content = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "darela-source-kernel-" + hashlib.sha256(content.encode()).hexdigest()[:20]


def read_contract(path):
    envelope = json.loads(Path(path).read_text())
    body = envelope["contract"]
    if envelope["run_id"] != identity(body):
        raise ValueError("contract identity mismatch")
    return {**body, "run_id": envelope["run_id"]}


def fixed_cases():
    cases = []
    for row, tau2 in (("manuscript_wt1", 15.0), ("shipped_example_tau", 12.5)):
        for name, bursts, end, initial, count in (
            ("quiet", [], 5.0, [1.0, 1.0, 1.0], 0),
            ("single", [0.34], 5.0, [1.0, 1.0, 1.0], 31),
            ("repeated", [0.34 + 5 * n for n in range(6)], 30.0, [1.0, 1.0, 1.0], 186),
            ("nonunit", [0.34], 5.0, [1.25, 0.75, 0.5], 31),
        ):
            cases.append(
                {
                    "name": f"{row}_{name}",
                    "parameter_row": row,
                    "bursts": bursts,
                    "end_s": end,
                    "initial_H": initial,
                    "expected_active_updates": count,
                    "p": [0.0105, -0.003, -0.0011],
                    "tau_s": [7.5, tau2, 900.0],
                }
            )
    return cases


def products(times, mask, h):
    return {
        "time": times,
        "mask": mask,
        "H": h,
        "A_old": np.array([math.prod(row) for row in h[:-1]]),
        "A_new": np.array([math.prod(row) for row in h[1:]]),
    }


def scalar_reference(case):
    """Independent exact decimal clock and scalar forward-Euler recurrence."""
    dt = Decimal("0.02")
    end = Decimal(str(case["end_s"]))
    n = int(end / dt)
    if n * dt != end:
        raise ValueError("reference contract requires integral 20 ms intervals")
    ticks = [j * dt for j in range(n + 1)]
    starts = [Decimal(str(start)) for start in case["bursts"]]
    cent = Decimal("0.01")
    mask = np.array(
        [
            sum(
                (t - start).quantize(cent, rounding=ROUND_HALF_EVEN) >= 0
                and (start + Decimal("0.6") - t).quantize(cent, rounding=ROUND_HALF_EVEN) >= 0
                for start in starts
            )
            for t in ticks
        ],
        dtype=np.float64,
    )
    h = np.empty((n + 1, 3), dtype=np.float64)
    h[0] = case["initial_H"]
    for j in range(n):
        s = float(mask[j])
        for k, (p, tau) in enumerate(zip(case["p"], case["tau_s"], strict=True)):
            old = float(h[j, k])
            h[j + 1, k] = old * (1 + p * s) + 0.02 * (1 - s) * (1 - old) / tau
    return products(np.array([float(t) for t in ticks]), mask, h)


def compare(observed, reference):
    x, y = np.asarray(observed), np.asarray(reference)
    if x.shape != y.shape or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("shape or nonfinite comparison failure")
    error = np.abs(x - y)
    if np.any(error > ATOL + RTOL * np.abs(y)):
        raise ValueError(f"numerical comparison failure: max error {float(error.max())}")
    return float(error.max(initial=0))


def load_kernel(contract):
    sys.dont_write_bytecode = True
    sys.path[:0] = [contract["source_root"], contract["dependency_root"]]
    module = importlib.import_module("darela.models")
    expected = Path(contract["source_root"]) / "darela/models.py"
    if Path(module.__file__).absolute() != expected.absolute():
        raise ValueError("unexpected DARELA import path")
    return module.SUR


def evaluate_case(kernel, case):
    model = kernel()
    model.initialize(case["bursts"], 50, 30, 0.4)
    model.params = {"ktypes": ["F", "D", "L"]}
    for k, (p, tau) in enumerate(zip(case["p"], case["tau_s"], strict=True), 1):
        model.params[f"p{k}"], model.params[f"tau{k}"] = p, tau
    model._set_stimulation(case["end_s"])
    model._set_kinetics()
    h = np.empty((len(model.t), 3), dtype=np.float64)
    h[0] = case["initial_H"]
    for j in range(1, len(h)):
        h[j] = model._solve_kinetics(h[j - 1], model.S[j - 1])
    return (products(np.asarray(model.t), np.asarray(model.S), h), scalar_reference(case))


def check_deadline(start, seconds):
    if time.monotonic() - start >= seconds:
        raise TimeoutError("bounded child deadline exceeded")


def run_child(contract, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    start, attempted, rows = time.monotonic(), 0, []
    try:
        write_json(out / "identity.json", contract)
        check_bindings(contract["bindings"])
        kernel = load_kernel(contract)
        for index, case in enumerate(contract["cases"]):
            check_deadline(start, contract["child_seconds"])
            attempted += 1
            source, reference = evaluate_case(kernel, case)
            filename = f"case_{index:02d}.npz"
            np.savez_compressed(
                out / filename,
                **{f"source_{k}": source[k] for k in KEYS},
                **{f"reference_{k}": reference[k] for k in KEYS},
            )
            row = {"index": index, "case": case, "file": record(out / filename), "passed": False}
            try:
                row["max_absolute_errors"] = {k: compare(source[k], reference[k]) for k in KEYS}
                if not np.array_equal(source["mask"], reference["mask"]):
                    raise ValueError("source mask not exactly equal")
                active = int(source["mask"][:-1].sum())
                if active != case["expected_active_updates"] or np.any(source["H"] <= 0):
                    raise ValueError("fixed source count/positive-factor invariant failed")
                row.update(
                    passed=True,
                    active_updates=active,
                    kernel_updates=len(source["H"]) - 1,
                    final_H=source["H"][-1].tolist(),
                    maximum_old_new_product_difference=float(np.abs(source["A_new"] - source["A_old"]).max()),
                )
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
                write_json(out / f"case_{index:02d}.json", row)
                raise
            write_json(out / f"case_{index:02d}.json", row)
            rows.append(row)
        check_bindings(contract["bindings"])
        check_deadline(start, contract["child_seconds"])
        summary = {
            "run_id": contract["run_id"],
            "status": "computed",
            "rows": rows,
            "attempted_cases": attempted,
            "completed_cases": len(rows),
            "kernel_updates": sum(row["kernel_updates"] for row in rows),
            "bindings_unchanged": True,
            "source_scope": "factor kernel only",
        }
        write_json(out / "summary.json", summary)
        check_deadline(start, contract["child_seconds"])
        write_json(
            out / "completion.json",
            {
                "run_id": contract["run_id"],
                "status": "completed",
                "summary_sha256": record(out / "summary.json")["sha256"],
                "completed_cases": len(rows),
                "attempted_cases": attempted,
                "seconds_through_summary": time.monotonic() - start,
            },
        )
        check_deadline(start, contract["child_seconds"])
        return 0
    except Exception as exc:
        write_json(
            out / "terminal-error.json",
            {
                "run_id": contract["run_id"],
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "attempted_cases": attempted,
                "completed_cases": len(rows),
                "seconds": time.monotonic() - start,
            },
        )
        return 1


def supervise(command, out, seconds):
    """External timeout with unconditional kill/reap on expiry; never resumes."""
    start = time.monotonic()
    with (out / "stdout.txt").open("wb") as stdout, (out / "stderr.txt").open("wb") as stderr:
        process = subprocess.Popen(
            command, stdout=stdout, stderr=stderr, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        )
        timed_out = False
        try:
            process.wait(timeout=max(0, seconds - (time.monotonic() - start)))
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            process.wait()
    return {
        "command": command,
        "exit_code": process.returncode,
        "timed_out": timed_out,
        "reaped": process.poll() is not None,
        "seconds": time.monotonic() - start,
    }


def validate_result(contract, result):
    if (result / "terminal-error.json").exists():
        raise ValueError("terminal error invalidates child completion")
    completion = json.loads((result / "completion.json").read_text())
    summary = json.loads((result / "summary.json").read_text())
    count = len(contract["cases"])
    if (
        not count
        or completion["status"] != "completed"
        or summary["status"] != "computed"
        or completion["run_id"] != contract["run_id"]
        or summary["run_id"] != contract["run_id"]
        or completion["summary_sha256"] != record(result / "summary.json")["sha256"]
        or any(
            item[key] != count
            for item in (summary, completion)
            for key in ("completed_cases", "attempted_cases")
        )
        or not 0 <= completion["seconds_through_summary"] < contract["child_seconds"]
        or summary["bindings_unchanged"] is not True
        or len(summary["rows"]) != count
    ):
        raise ValueError("source child terminal identity/count/status invalid")
    for index, (case, row) in enumerate(zip(contract["cases"], summary["rows"], strict=True)):
        stem = f"case_{index:02d}"
        saved_row = json.loads((result / f"{stem}.json").read_text())
        if (
            row != saved_row
            or row["index"] != index
            or row["case"] != case
            or row["passed"] is not True
            or row["file"] != record(result / f"{stem}.npz")
        ):
            raise ValueError("saved source case identity/hash/status invalid")
    for suffix in ("npz", "json"):
        expected = {f"case_{index:02d}.{suffix}" for index in range(count)}
        if {path.name for path in result.glob(f"case_*.{suffix}")} != expected:
            raise ValueError("unexpected or missing case artifact")
    return completion


def run_parent(contract_path, out):
    start = time.monotonic()
    contract = read_contract(contract_path)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    try:
        check_bindings(contract["bindings"])
        command = [
            contract["interpreter"],
            "-B",
            str(Path(__file__).absolute()),
            "--contract",
            str(Path(contract_path).absolute()),
            "--out",
            str((out / "result").absolute()),
        ]
        receipt = supervise(command, out, max(0, contract["parent_seconds"] - (time.monotonic() - start)))
        receipt["run_id"] = contract["run_id"]
        receipt["contract"] = record(contract_path)
        result = out / "result"
        if receipt["exit_code"] != 0 or receipt["timed_out"] or not receipt["reaped"]:
            raise ValueError("source child did not complete its fixed contract")
        validate_result(contract, result)
        check_bindings(contract["bindings"])
        check_deadline(start, contract["parent_seconds"])
        receipt.update(
            status="completed",
            seconds_through_checks=time.monotonic() - start,
            child_completion=record(result / "completion.json"),
        )
        write_json(out / "execution.json", receipt)
        check_deadline(start, contract["parent_seconds"])
        return 0
    except Exception as exc:
        write_json(
            out / "terminal-error.json",
            {
                "run_id": contract["run_id"],
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "seconds": time.monotonic() - start,
                "child_process": locals().get("receipt"),
            },
        )
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--parent", action="store_true")
    args = parser.parse_args()
    sys.exit(
        run_parent(args.contract, args.out)
        if args.parent
        else run_child(read_contract(args.contract), args.out)
    )
