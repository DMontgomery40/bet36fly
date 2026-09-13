"""Exclusive parent watchdog for the frozen offline DARELA screen."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import run_darela_shadow as runner


def supervise(command, cwd, output, timeout):
    """subprocess.run kills and reaps on expiry; there is no retry."""
    with (output / "stdout.txt").open("xb") as stdout, (output / "stderr.txt").open("xb") as stderr:
        try:
            child = subprocess.run(
                command, cwd=cwd, stdout=stdout, stderr=stderr, timeout=timeout, check=False
            )
            return dict(timed_out=False, exit_code=child.returncode, child_reaped=True)
        except subprocess.TimeoutExpired:
            return dict(timed_out=True, exit_code=None, child_reaped=True)


def execute(plan_path, execution, *, clock=time.monotonic):
    started = clock()
    execution = Path(execution).absolute()
    execution.mkdir(parents=False, exist_ok=False)
    receipt = dict(
        status="running", child_reaped=False, exit_code=None, timed_out=False, wall_seconds_cap=1200
    )

    def guard():
        if clock() - started >= 1200:
            raise TimeoutError("1200-second parent whole-study cap")

    try:
        p = Path(plan_path).absolute()
        runner.require(p.stat().st_size <= 4_000_000, "bounded plan")
        raw = p.read_bytes()
        plan = runner.reader.strict_json(raw)
        runner.validate_plan(plan)
        runner.require(execution == Path(plan["output_root"]) / plan["run_id"], "exclusive parent identity")
        interpreter = (
            runner.ROOT / ".venv/bin/python"
        )  # Never resolve this symlink: pyvenv.cfg discovery matters.
        runner.require(
            interpreter.is_file() and (runner.ROOT / ".venv/pyvenv.cfg").is_file(), "repository Python"
        )
        command = [
            str(interpreter),
            str(Path(__file__).absolute().with_name("run_darela_shadow.py")),
            "--plan",
            str(p),
            "--out",
            str(execution / "result"),
        ]
        receipt.update(command=command, run_id=plan["run_id"], plan_sha256=hashlib.sha256(raw).hexdigest())
        runner.reader.atomic_json(execution / "plan.json", plan)
        guard()
        remaining = 1200 - (clock() - started) - 10
        runner.require(remaining > 0, "parent terminal reserve exhausted")
        receipt.update(supervise(command, runner.ROOT, execution, remaining))
        guard()
        runner.require(
            type(receipt["exit_code"]) is int
            and receipt["exit_code"] == 0
            and receipt["timed_out"] is False
            and receipt["child_reaped"] is True,
            "child did not complete successfully",
        )
        summary = runner.validate_saved(execution / "result", plan, guard)
        runner.reader.BoundInputs(plan["inputs"], guard).verify()
        runner.require(p.read_bytes() == raw, "plan changed during child")
        guard()
        receipt.update(
            status="completed",
            screen=summary["screen"],
            provisional_screen=summary["provisional_screen"],
            child_completion=runner.binding(execution / "result/completion.json", guard)
            if (execution / "result/completion.json").is_file()
            else None,
            wall_seconds=clock() - started,
        )
        runner.reader.atomic_json(execution / "parent-result.json", receipt)
        guard()
        return receipt
    except BaseException as exc:
        receipt.update(
            status="failed", error_type=type(exc).__name__, error=str(exc), wall_seconds=clock() - started
        )
        if (execution / "parent-result.json").is_file():
            receipt["invalidated_parent_result_sha256"] = runner.reader.sha(execution / "parent-result.json")
        runner.reader.atomic_json(execution / "terminal-error.json", receipt)
        return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", required=True, type=Path)
    p.add_argument("--execution", required=True, type=Path)
    args = p.parse_args()
    result = execute(args.plan, args.execution)
    print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
