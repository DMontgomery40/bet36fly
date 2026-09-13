"""One exclusive, externally bounded invocation of the reviewed offline audit."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--execution", type=Path, required=True)
    args = parser.parse_args()
    plan_path = args.plan.absolute()
    plan_bytes = plan_path.read_bytes()
    plan = json.loads(plan_bytes)
    root = Path(plan["root"])
    interpreter = root / ".venv/bin/python"  # Preserve pyvenv.cfg discovery.
    if not (root / ".venv/pyvenv.cfg").is_file() or not interpreter.is_file():
        raise ValueError("Repository Python environment missing")
    args.execution.mkdir(parents=False, exist_ok=False)
    command = [str(interpreter), str(Path(__file__).absolute().with_name("run_dan_causal_prefix.py")),
               "--plan", str(plan_path), "--out", str(args.execution.absolute() / "result")]
    with (args.execution / "stdout.txt").open("xb") as stdout, (args.execution / "stderr.txt").open("xb") as stderr:
        started = time.monotonic()
        timed_out = False
        try:
            child = subprocess.run(command, cwd=root, stdout=stdout, stderr=stderr, timeout=120, check=False)
            exit_code = child.returncode
        except subprocess.TimeoutExpired:
            # subprocess.run kills and reaps the child before raising.
            timed_out = True
            exit_code = None
        elapsed = time.monotonic() - started
    receipt = dict(command=command, run_id=plan["run_id"],
                   plan_sha256=hashlib.sha256(plan_bytes).hexdigest(),
                   wall_seconds_cap=120, wall_seconds=elapsed,
                   timed_out=timed_out, exit_code=exit_code, child_reaped=True)
    with (args.execution / "parent-result.json").open("x") as f:
        json.dump(receipt, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps(receipt), flush=True)
    return 0 if exit_code == 0 and not timed_out and elapsed < 120 else 1


if __name__ == "__main__":
    raise SystemExit(main())
