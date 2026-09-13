"""Finite source-equation protocols; no circuit, fit, behavioral PI or author-code run.

The CLI accepts only the frozen pre-execution plan. Internal pure case/matrix
functions also admit small synthetic schedules for tests. The parent owns the
external 30-second timeout and independent saved-result verification.
"""

import argparse
from dataclasses import asdict, astuple
from datetime import datetime, timezone
import hashlib
import json
import math
from numbers import Real
import os
from pathlib import Path
import re
import time

import numpy as np

import aso_da_no as model


PLAN_SHA256 = "55f9ad550052125e2715003eb44d90f509fa55014144b872ca48812ba60d67a4"
HELPER_SHA256 = "d43351281854ff2700c10b573a8c22a725f9fee226d083c6363e6436e1285111"
CLASSES = ["a_only", "b_only", "shared", "neither"]
COLUMNS = ["d", "n", "D", "N"]
PATHWAYS = [
    ("both", True, True),
    ("da_only", True, False),
    ("no_only", False, True),
    ("neither", False, False),
]
TIMEOUT_SECONDS = 30
FIELDS = {
    "segment_times_s",
    "segment_inputs",
    "segment_states",
    "segment_weights",
    "observation_times_s",
    "observation_states",
    "observation_weights",
    "observation_segment_indices",
}


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def file_identity(path):
    data = Path(path).read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate JSON field.")
        result[key] = value
    return result


def _no_constant(value):
    raise ValueError(f"Nonfinite JSON number: {value}")


def load_frozen_plan(path):
    path = Path(path)
    if path.stat().st_size > 100_000:
        raise ValueError("Plan exceeds the bounded source declaration size.")
    data = path.read_bytes()
    plan = json.loads(data, object_pairs_hook=_pairs, parse_constant=_no_constant)
    if hashlib.sha256(data).hexdigest() != PLAN_SHA256:
        raise ValueError("Plan differs from the frozen source protocol.")
    _validate_matrix(plan)
    return plan


def _number(value):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError("Timing requires finite numeric seconds, not Boolean aliases.")
    try:
        result = float(value)
    except (OverflowError, ValueError):
        raise ValueError("Timing is outside the finite domain.") from None
    if not math.isfinite(result) or result < 0:
        raise ValueError("Timing requires finite nonnegative seconds.")
    return result


def _intervals(value, duration, *, tests=False):
    if type(value) is not list or (tests and not value):
        raise ValueError("Intervals require a list; at least one test is required.")
    result = []
    for pair in value:
        if type(pair) is not list or len(pair) != 2:
            raise ValueError("Each interval requires exactly two endpoints.")
        start, end = map(_number, pair)
        if start >= end or end > duration or (result and start < result[-1][1]):
            raise ValueError("Intervals must be ordered, nonoverlapping and inside duration.")
        if tests and end - start < 30:
            raise ValueError("Test windows must contain their final30seconds.")
        result.append((start, end))
    return result


def _protocol(p):
    required = {
        "id",
        "source",
        "duration_s",
        "odor_a_intervals_s",
        "odor_b_intervals_s",
        "dan_intervals_s",
        "test_windows_s",
    }
    if type(p) is not dict or set(p) != required or not isinstance(p["source"], str) or not p["source"]:
        raise ValueError("Complete protocol declaration required.")
    if not isinstance(p["id"], str) or not re.fullmatch(r"[a-z0-9_]{1,80}", p["id"]):
        raise ValueError("Protocol identifier is not a safe declared label.")
    duration = _number(p["duration_s"])
    if duration == 0:
        raise ValueError("Protocol duration must be positive.")
    a, b, dan = [
        _intervals(p[name], duration)
        for name in ("odor_a_intervals_s", "odor_b_intervals_s", "dan_intervals_s")
    ]
    tests = _intervals(p["test_windows_s"], duration, tests=True)
    if any(max(start, lo) < min(end, hi) for start, end in tests for lo, hi in a + b + dan):
        raise ValueError("Test windows are passive and cannot overlap declared stimulation.")
    return duration, a, b, dan, tests


def _pathway(p):
    if type(p) is not dict or set(p) != {"id", "da_enabled", "no_enabled"}:
        raise ValueError("Complete pathway declaration required.")
    if type(p["da_enabled"]) is not bool or type(p["no_enabled"]) is not bool:
        raise ValueError("Pathway flags require actual Boolean values.")
    if (p["id"], p["da_enabled"], p["no_enabled"]) not in PATHWAYS:
        raise ValueError("Pathway label differs from its source-null configuration.")
    return {"da_enabled": p["da_enabled"], "no_enabled": p["no_enabled"]}


def _validate_matrix(plan):
    expected = {
        "schema": 1,
        "kind": "aso2019_source_equation_protocol",
        "unit": "seconds",
        "initial_state": [0, 0, 0, 0],
        "state_columns": COLUMNS,
        "kc_classes": CLASSES,
        "parameters": asdict(model.Parameters()),
        "pathways": [dict(id=i, da_enabled=d, no_enabled=n) for i, d, n in PATHWAYS],
        "test_observations": ["start", "last_30s_start", "end"],
    }
    if type(plan) is not dict or any(_json_bytes(plan.get(k)) != _json_bytes(v) for k, v in expected.items()):
        raise ValueError("Matrix changes source parameters, units, classes or null controls.")
    protocols = plan.get("protocols")
    if type(protocols) is not list or not protocols or len(protocols) > 7:
        raise ValueError("A bounded protocol matrix is required.")
    for p in protocols:
        _protocol(p)
    if len({p["id"] for p in protocols}) != len(protocols):
        raise ValueError("Duplicate protocol identifiers.")
    if type(plan.get("expected_case_count")) is not int or plan["expected_case_count"] != 4 * len(protocols):
        raise ValueError("Incomplete case matrix count.")


def _schedule(protocol):
    duration, a, b, dan, tests = _protocol(protocol)
    boundaries = np.array(sorted({0.0, duration, *(x for pair in a + b + dan for x in pair)}), np.float64)
    flags = np.zeros((len(boundaries) - 1, 4, 2), bool)
    for i, start in enumerate(boundaries[:-1]):
        on_a, on_b, on_d = [any(lo <= start < hi for lo, hi in intervals) for intervals in (a, b, dan)]
        flags[i, :, 0] = [on_a, on_b, on_a or on_b, False]
        flags[i, :, 1] = on_d
    observations = np.array([[start, end - 30, end] for start, end in tests], np.float64)
    indices = np.minimum(
        np.searchsorted(boundaries, observations, side="right") - 1, len(boundaries) - 2
    ).astype(np.int64)
    return boundaries, flags, observations, indices


def _evolve(states, seconds, flags, pathway):
    return np.array(
        [
            astuple(
                model.advance(
                    model.SourceState(*states[k]),
                    float(seconds),
                    kc_active=bool(flags[k, 0]),
                    dan_active=bool(flags[k, 1]),
                    **pathway,
                )
            )
            for k in range(4)
        ],
        np.float64,
    )


def calculate_case(protocol, pathway):
    """Four exposure classes; finite observations never feed back into evolution."""
    control = _pathway(pathway)
    times, flags, observations, indices = _schedule(protocol)
    states = np.zeros((len(times), 4, 4), np.float64)
    for i, duration in enumerate(np.diff(times)):
        states[i + 1] = _evolve(states[i], duration, flags[i], control)
    observed = np.empty((*observations.shape, 4, 4), np.float64)
    for where in np.ndindex(observations.shape):
        i = int(indices[where])
        observed[where] = _evolve(states[i], observations[where] - times[i], flags[i], control)
    return dict(
        segment_times_s=times,
        segment_inputs=flags,
        segment_states=states,
        segment_weights=(1 - states[..., 2]) * (1 + states[..., 3]),
        observation_times_s=observations,
        observation_states=observed,
        observation_weights=(1 - observed[..., 2]) * (1 + observed[..., 3]),
        observation_segment_indices=indices,
    )


def validate_arrays(arrays, protocol, pathway):
    control = _pathway(pathway)
    times, flags, observations, indices = _schedule(protocol)
    if type(arrays) is not dict or set(arrays) != FIELDS:
        raise ValueError("Incomplete case array inventory.")
    shapes = {
        "segment_times_s": times.shape,
        "segment_inputs": flags.shape,
        "segment_states": (len(times), 4, 4),
        "segment_weights": (len(times), 4),
        "observation_times_s": observations.shape,
        "observation_states": (*observations.shape, 4, 4),
        "observation_weights": (*observations.shape, 4),
        "observation_segment_indices": indices.shape,
    }
    for key, value in arrays.items():
        dtype = np.dtype(
            bool
            if key == "segment_inputs"
            else np.int64
            if key == "observation_segment_indices"
            else np.float64
        )
        if (
            not isinstance(value, np.ndarray)
            or value.dtype != dtype
            or value.shape != shapes[key]
            or not np.isfinite(value).all()
        ):
            raise ValueError(f"Invalid case array: {key}")
    for key, expected in [
        ("segment_times_s", times),
        ("segment_inputs", flags),
        ("observation_times_s", observations),
        ("observation_segment_indices", indices),
    ]:
        if not np.array_equal(arrays[key], expected):
            raise ValueError(f"Case schedule mismatch: {key}")
    if np.any(arrays["segment_states"][0] != 0):
        raise ValueError("Every independent case starts from zero.")
    for prefix in ("segment", "observation"):
        state = arrays[prefix + "_states"]
        weights = arrays[prefix + "_weights"]
        if (
            np.any(state < 0)
            or np.any(state > 1)
            or not np.array_equal(weights, (1 - state[..., 2]) * (1 + state[..., 3]))
        ):
            raise ValueError("Case state or source weight is invalid.")
        for enabled, columns in [(control["da_enabled"], [0, 2]), (control["no_enabled"], [1, 3])]:
            if not enabled and np.any(state[..., columns] != 0):
                raise ValueError("A source-null pathway is populated.")


def _write_json(path, value):
    temporary = path.with_suffix(".tmp")
    with temporary.open("wb") as f:
        f.write(_json_bytes(value) + b"\n")
        f.flush()
        os.fsync(f.fileno())
    temporary.replace(path)


def _write_npz(path, arrays):
    with path.open("xb") as f:
        np.savez_compressed(f, **arrays)
        f.flush()
        os.fsync(f.fileno())


def _input_identity(plan, plan_path=None):
    helper = file_identity(Path(model.__file__))
    if helper["sha256"] != HELPER_SHA256:
        raise ValueError("Frozen source helper changed.")
    plan_data = Path(plan_path).read_bytes() if plan_path else _json_bytes(plan)
    if plan_path and (
        hashlib.sha256(plan_data).hexdigest() != PLAN_SHA256
        or _json_bytes(json.loads(plan_data, object_pairs_hook=_pairs, parse_constant=_no_constant))
        != _json_bytes(plan)
    ):
        raise ValueError("Parsed declaration does not match frozen input plan bytes.")
    return dict(
        plan_path=str(Path(plan_path).resolve()) if plan_path else None,
        plan_sha256=hashlib.sha256(plan_data).hexdigest(),
        helper_path=str(Path(model.__file__).resolve()),
        helper_sha256=helper["sha256"],
        producer_path=str(Path(__file__).resolve()),
        producer_sha256=file_identity(Path(__file__))["sha256"],
    )


def _run(plan, output, *, plan_path=None, clock=time.monotonic):
    """Private toy-test seam; real CLI first enforces the frozen plan byte hash."""
    started = clock()
    _validate_matrix(plan)
    frozen_plan = _json_bytes(plan)
    identity = _input_identity(plan, plan_path)
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=False)
    status = dict(
        schema=1,
        kind="aso2019_source_equation_protocol",
        status="running",
        started_at=datetime.now(timezone.utc).isoformat(),
        elapsed_seconds=0.0,
        identity=identity,
        expected_case_count=plan["expected_case_count"],
        completed_case_count=0,
        cases=[],
        failed_case=None,
        error=None,
        kc_classes=CLASSES,
        state_columns=COLUMNS,
        observation_labels=plan["test_observations"],
        unit="seconds",
        parameters=plan["parameters"],
    )

    def guard():
        elapsed = _number(clock() - started)
        if elapsed >= TIMEOUT_SECONDS:
            raise TimeoutError("Finite source protocol exceeded its30second budget.")
        if _json_bytes(plan) != frozen_plan or _input_identity(plan, plan_path) != identity:
            raise ValueError("Source input identity changed during execution.")
        return elapsed

    try:
        with (directory / "plan.json").open("xb") as f:
            f.write(Path(plan_path).read_bytes() if plan_path else frozen_plan)
            f.flush()
            os.fsync(f.fileno())
        _write_json(directory / "status.json", status)
        guard()
        for p in plan["protocols"]:
            for q in plan["pathways"]:
                index = len(status["cases"])
                status["failed_case"] = index
                guard()
                arrays = calculate_case(p, q)
                validate_arrays(arrays, p, q)
                guard()
                name = f"{index:02d}_{p['id']}_{q['id']}.npz"
                _write_npz(directory / name, arrays)
                # Reopen the actual saved small payload: never count a truncated archive.
                with np.load(directory / name, allow_pickle=False) as saved:
                    retained = {k: saved[k] for k in saved.files}
                validate_arrays(retained, p, q)
                if any(not np.array_equal(arrays[k], retained[k]) for k in arrays):
                    raise ValueError("Saved numerical arrays differ from calculated values.")
                status["cases"].append(
                    dict(
                        index=index,
                        protocol_id=p["id"],
                        pathway_id=q["id"],
                        file=name,
                        **file_identity(directory / name),
                    )
                )
                status["completed_case_count"] = len(status["cases"])
                status["elapsed_seconds"] = guard()
                _write_json(directory / "status.json", status)
        for row in status["cases"]:
            if file_identity(directory / row["file"]) != {k: row[k] for k in ("bytes", "sha256")}:
                raise ValueError("Saved case bytes changed before completion.")
        if file_identity(directory / "plan.json")["sha256"] != identity["plan_sha256"]:
            raise ValueError("Saved input plan changed.")
        status.update(status="completed", failed_case=None, elapsed_seconds=guard())
        _write_json(directory / "status.json", status)
        guard()
    except Exception as exc:
        status.update(
            status="failed", error=f"{type(exc).__name__}: {exc}", elapsed_seconds=max(0.0, clock() - started)
        )
        try:
            _write_json(directory / "status.json", status)
        except OSError:
            # Parent exit/non-completed disposition remains authoritative if storage is unavailable.
            pass
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = _run(load_frozen_plan(args.plan), args.output, plan_path=args.plan)
    print(json.dumps({k: result[k] for k in ("status", "completed_case_count", "error")}, allow_nan=False))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
