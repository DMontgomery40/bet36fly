"""One externally bounded independent saved-result audit, no retry."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

import audit_darela_shadow as audit


def supervise(command, root, directory, timeout):
    env = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE="1",
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        VECLIB_MAXIMUM_THREADS="1",
    )
    with (directory / "stdout.txt").open("xb") as stdout, (directory / "stderr.txt").open("xb") as stderr:
        try:
            child = subprocess.run(
                command, cwd=root, env=env, stdout=stdout, stderr=stderr, timeout=timeout, check=False
            )
            return dict(exit_code=child.returncode, timed_out=False, child_reaped=True)
        except subprocess.TimeoutExpired:
            # subprocess.run kills and waits for its direct child before raising.
            return dict(exit_code=None, timed_out=True, child_reaped=True)


def validate_result(directory, run_id, guard=lambda: None):
    if (directory / "terminal-error.json").exists():
        raise ValueError("Audit terminal error invalidates completion")

    def read(name):
        return audit.reader.strict_json(
            audit.checked_bytes(directory / name, audit.binding(directory / name, guard), 32 * 1024 * 1024)
        )

    completed, report, status = [read(n) for n in ["completion.json", "audit.json", "status.json"]]
    if (
        completed["status"] != "complete"
        or report["status"] != "completed"
        or status["status"] != "completed"
        or any(r["run_id"] != run_id for r in [completed, report, status])
        or report != status
        or any(type(r["completed"]) is not int or r["completed"] != 32 for r in [completed, report, status])
        or report["attempted"] != 32
        or not 0 <= report["wall_seconds"] < 600
        or not 0 <= completed["elapsed_seconds"] < 600
    ):
        raise ValueError("Complete consistent audit terminal/count/cap conjunction")
    store = audit.Store(completed["bindings"], guard)
    store.verify()
    expected = {str(directory / n) for n in ["audit.json", "status.json"]} | {
        str(directory / f"{prefix}_{i:02d}.{ext}")
        for i in range(32)
        for prefix, ext in [("row", "json"), ("reference", "npz")]
    }
    if set(store.items) != expected or completed["audit"] != store.items[str(directory / "audit.json")]:
        raise ValueError("Complete audit binding inventory")
    if len(report["rows"]) != 32:
        raise ValueError("Complete numerical row reports")
    for i, row in enumerate(report["rows"]):
        guard()
        saved = store.json(directory / f"row_{i:02d}.json")
        if (
            row != saved
            or type(row["index"]) is not int
            or row["index"] != i
            or row["reference_artifact"] != store.items[str(directory / f"reference_{i:02d}.npz")]
        ):
            raise ValueError("Audit row/reference artifact identity")
    if report["numerical_status"] not in ["passed", "unresolved"] or report["screen"] not in [
        "passed_necessary_untaught_screen",
        "rejected_fixed_hypothesis",
        "invalid_or_unresolved",
    ]:
        raise ValueError("Known audit classification")
    if report["numerical_status"] == "unresolved" and report["screen"] != "invalid_or_unresolved":
        raise ValueError("Unresolved numerical evidence cannot qualify")
    return report


def execute(plan_path, producer_result, execution, *, clock=time.monotonic):
    started = clock()
    execution = Path(execution).absolute()
    execution.mkdir(parents=False, exist_ok=False)
    receipt = dict(
        status="running", wall_seconds_cap=600, child_reaped=False, timed_out=False, exit_code=None
    )

    def guard():
        if clock() - started >= 600:
            raise TimeoutError("600-second whole audit parent cap")

    try:
        plan_path = Path(plan_path).absolute()
        plan_binding = audit.binding(plan_path, guard)
        plan = audit.reader.strict_json(audit.checked_bytes(plan_path, plan_binding, 4 * 1024 * 1024))
        audit.validate_plan(plan)
        interpreter = audit.ROOT / ".venv/bin/python"  # Keep venv path unresolved.
        command = [
            str(interpreter),
            str(Path(__file__).absolute().with_name("audit_darela_shadow.py")),
            "--plan",
            str(plan_path),
            "--producer-result",
            str(Path(producer_result).absolute()),
            "--output",
            str(execution / "result"),
        ]
        receipt.update(run_id=plan["run_id"], command=command, plan=plan_binding)
        guard()
        receipt.update(supervise(command, audit.ROOT, execution, 600 - (clock() - started)))
        guard()
        if receipt["exit_code"] != 0 or receipt["timed_out"] or not receipt["child_reaped"]:
            raise ValueError("Audit child did not complete successfully")
        report = validate_result(execution / "result", plan["run_id"], guard)
        audit.Store(plan["inputs"], guard).verify()
        if audit.binding(plan_path, guard) != plan_binding:
            raise ValueError("Plan changed during audit")
        guard()
        receipt.update(
            status="completed",
            numerical_status=report["numerical_status"],
            screen=report["screen"],
            child_completion=audit.binding(execution / "result/completion.json", guard),
            wall_seconds=clock() - started,
        )
        audit.write_json(execution / "parent-result.json", receipt)
        guard()
        return receipt
    except BaseException as exc:
        receipt.update(status="failed", error=f"{type(exc).__name__}: {exc}", wall_seconds=clock() - started)
        if (execution / "parent-result.json").exists():
            receipt["invalidated_parent_result"] = audit.binding(execution / "parent-result.json")
        audit.write_json(execution / "terminal-error.json", receipt)
        return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--producer-result", type=Path, required=True)
    p.add_argument("--execution", type=Path, required=True)
    args = p.parse_args()
    r = execute(args.plan, args.producer_result, args.execution)
    print(json.dumps(r, allow_nan=False), flush=True)
    return 0 if r["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
