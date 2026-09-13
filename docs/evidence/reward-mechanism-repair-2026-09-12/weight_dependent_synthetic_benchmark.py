"""One parent-authorized synthetic size benchmark; never loads any saved history."""

import hashlib
import json
import signal
import time
from pathlib import Path

import numpy as np

import weight_dependent_shadow as helper


SEED = 20260913
CAP_SECONDS = 120
OUTPUT = Path(__file__).with_name("weight-dependent-synthetic-benchmark-2026-09-13.json")


def main():
    if OUTPUT.exists():
        raise FileExistsError("The single benchmark receipt already exists")
    started = time.monotonic()
    code = Path(helper.__file__)
    code_hash = hashlib.sha256(code.read_bytes()).hexdigest()
    record = {
        "kind": "synthetic preparation timing only",
        "seed": SEED,
        "helper_sha256": code_hash,
        "benchmark_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "wall_cap_seconds": CAP_SECONDS,
        "shape": {"steps": 2000, "kcs": 4064, "dans": 24, "edges": 8866},
        "home_edges": 4184,
        "away_edges": 4682,
        "eligible_home": 4184,
        "eligible_away": 3239,
        "generator": "NumPy default_rng; independent KC Bernoulli .01 and DAN Bernoulli .005; toy modulo KC/group maps; no anatomical or capture input",
        "calls_attempted": 0,
        "calls_completed": 0,
    }

    def guard(*unused):
        if time.monotonic() - started >= CAP_SECONDS:
            raise TimeoutError("Synthetic preparation timing cap reached")

    previous = signal.signal(signal.SIGALRM, guard)
    signal.setitimer(signal.ITIMER_REAL, CAP_SECONDS)
    try:
        rng = np.random.default_rng(SEED)
        kc = (rng.random((2000, 4064)) < 0.01).astype(np.uint8)
        dan = (rng.random((2000, 24)) < 0.005).astype(np.uint8)
        pk = np.arange(8866, dtype=np.int32) % 4064
        pc = np.r_[np.zeros(4184, np.int32), np.ones(4682, np.int32)]
        dc = np.r_[np.zeros(2, np.int32), np.ones(22, np.int32)]
        mask = np.r_[np.ones(4184 + 3239, np.uint8), np.zeros(1443, np.uint8)]
        groups = (4 * pc + np.arange(8866, dtype=np.int32) % 4).astype(np.int32)
        record["generated_input_sha256"] = {
            name: hashlib.sha256(value.tobytes()).hexdigest()
            for name, value in dict(kc=kc, dan=dan, pk=pk, pc=pc, dc=dc, mask=mask, groups=groups).items()
        }
        guard()
        record["calls_attempted"] = 1
        value = helper.shadow(kc, dan, pk, pc, dc, mask, groups, guard=guard)
        record["calls_completed"] = 1
        guard()
        record.update(
            status="completed",
            finite_gain=bool(np.isfinite(value["gains"]).all()),
            accepted_substeps=value["accepted_substeps"],
            attempted_substeps=value["attempted_substeps"],
            excluded_checkpoint_bytes_equal=bool(
                value["gains"][mask == 0].tobytes() == np.ones(1443, np.float32).tobytes()
            ),
            eligible_publications=[int(v) for v in np.unique(value["publication_counts"][mask == 1])],
        )
    except Exception as exc:
        record.update(status="failed", error_type=type(exc).__name__, error=str(exc))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        record["wall_seconds"] = time.monotonic() - started
        record["helper_unchanged"] = hashlib.sha256(code.read_bytes()).hexdigest() == code_hash
        with OUTPUT.open("x") as stream:
            json.dump(record, stream, indent=2, allow_nan=False)
            stream.write("\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
