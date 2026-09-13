"""Independent saved-state checks for the frozen Aso source-equation matrix.

Only the separately authored70-digit reference supplies dynamics. No producer,
native circuit, source-author executable, fit or captured-history import.
"""

from copy import deepcopy
import argparse
from datetime import datetime
import hashlib
import io
import json
import math
import os
from pathlib import Path
import time
import zipfile

import numpy as np

from aso_da_no_reference import reference_advance


PLAN_SHA256 = "55f9ad550052125e2715003eb44d90f509fa55014144b872ca48812ba60d67a4"
HELPER_SHA256 = "d43351281854ff2700c10b573a8c22a725f9fee226d083c6363e6436e1285111"
REFERENCE_SHA256 = "9b162ab64f14ace56d10bbbb123219c7683a62c932e89996ca6e1018989d56d4"
ATOL = RTOL = 1e-12
PARAMETERS = dict(A_D=4.3 / 60, A_N=0.96 / 60, B_D=0.26 / 60, B_N=0.16 / 60, tau_D=30.0, tau_N=600.0)
EXACT_FIELDS = {"segment_times_s", "segment_inputs", "observation_times_s", "observation_segment_indices"}


def load_plan(path):
    if Path(path).stat().st_size > 100_000:
        raise ValueError("Source plan exceeds its bounded declaration size")
    raw = _bounded_bytes(path)
    if hashlib.sha256(raw).hexdigest() != PLAN_SHA256:
        raise ValueError("Plan is not the frozen, independently inspected source matrix")
    return json.loads(raw)


def case_specs(plan):
    """Schedule construction only; this performs no trajectory calculation."""
    result = []
    for protocol in plan["protocols"]:
        for pathway in plan["pathways"]:
            result.append(dict(index=len(result), protocol=deepcopy(protocol), pathway=deepcopy(pathway)))
    return result


def schedule(protocol):
    """Independent union of declared stimulus boundaries, never saved flags."""
    duration = protocol["duration_s"]
    intervals = [protocol[name] for name in ("odor_a_intervals_s", "odor_b_intervals_s", "dan_intervals_s")]
    boundaries = {0.0, float(duration)}
    for group in intervals:
        previous = -1.0
        for start, end in group:
            if not 0 <= start < end <= duration or start < previous:
                raise ValueError("Invalid declared source interval")
            previous = end
            boundaries.update((float(start), float(end)))
    times = np.asarray(sorted(boundaries), dtype=np.float64)
    inputs = np.zeros((len(times) - 1, 4, 2), dtype=np.bool_)
    for j, timestamp in enumerate(times[:-1]):
        a, b, dan = [any(start <= timestamp < end for start, end in group) for group in intervals]
        inputs[j, :, 0] = (a, b, a or b, False)
        inputs[j, :, 1] = dan
    observations = []
    for start, end in protocol["test_windows_s"]:
        if not 0 <= start <= end - 30 <= end <= duration:
            raise ValueError("Test windows must contain the declared last30-second start")
        observations.append((start, end - 30, end))
    observation_times = np.asarray(observations, dtype=np.float64).reshape(-1, 3)
    indices = np.minimum(np.searchsorted(times, observation_times, side="right") - 1, len(times) - 2).astype(
        np.int64
    )
    return times, inputs, observation_times, indices


def array_contract(protocol):
    times, inputs, observations, indices = schedule(protocol)
    n, tests = len(inputs), len(observations)
    return {
        "segment_times_s": (np.dtype("float64"), times.shape),
        "segment_inputs": (np.dtype("bool"), inputs.shape),
        "segment_states": (np.dtype("float64"), (n + 1, 4, 4)),
        "segment_weights": (np.dtype("float64"), (n + 1, 4)),
        "observation_times_s": (np.dtype("float64"), observations.shape),
        "observation_states": (np.dtype("float64"), (tests, 3, 4, 4)),
        "observation_weights": (np.dtype("float64"), (tests, 3, 4)),
        "observation_segment_indices": (np.dtype("int64"), indices.shape),
    }


def reference_case(
    protocol, pathway, *, initial_state=(0, 0, 0, 0), parameters=PARAMETERS, guard=lambda: None
):
    if parameters != PARAMETERS:
        raise ValueError("The frozen source parameters cannot be changed")
    times, inputs, observation_times, indices = schedule(protocol)
    states = np.empty((len(times), 4, 4), dtype=np.float64)
    states[0] = initial_state
    branches = {k: pathway[k] for k in ("da_enabled", "no_enabled")}
    for j, duration in enumerate(np.diff(times)):
        guard()
        for c in range(4):
            states[j + 1, c] = reference_advance(
                states[j, c],
                duration,
                bool(inputs[j, c, 0]),
                bool(inputs[j, c, 1]),
                parameters=parameters,
                **branches,
            )
    observations = np.empty((*observation_times.shape, 4, 4), dtype=np.float64)
    for index in np.ndindex(observation_times.shape):
        guard()
        segment, time = indices[index], observation_times[index]
        for c in range(4):
            observations[index][c] = reference_advance(
                states[segment, c],
                time - times[segment],
                bool(inputs[segment, c, 0]),
                bool(inputs[segment, c, 1]),
                parameters=parameters,
                **branches,
            )
    return dict(
        segment_times_s=times,
        segment_inputs=inputs,
        segment_states=states,
        segment_weights=(1 - states[..., 2]) * (1 + states[..., 3]),
        observation_times_s=observation_times,
        observation_states=observations,
        observation_weights=(1 - observations[..., 2]) * (1 + observations[..., 3]),
        observation_segment_indices=indices,
    )


def compare_case(
    protocol, pathway, arrays, *, initial_state=(0, 0, 0, 0), parameters=PARAMETERS, guard=lambda: None
):
    contract = array_contract(protocol)
    if set(arrays) != set(contract):
        raise ValueError("Exact saved array inventory required")
    for name, (dtype, shape) in contract.items():
        value = arrays[name]
        if not isinstance(value, np.ndarray) or value.dtype != dtype or value.shape != shape:
            raise ValueError(f"Invalid dtype or shape: {name}")
        if not np.isfinite(value).all():
            raise ValueError(f"Nonfinite value: {name}")
        if name.endswith("states") and np.any((value < 0) | (value > 1)):
            raise ValueError(f"State outside unit cube: {name}")
        if name.endswith("weights") and np.any((value < 0) | (value > 2)):
            raise ValueError(f"Weight outside source domain: {name}")
    expected = reference_case(
        protocol, pathway, initial_state=initial_state, parameters=parameters, guard=guard
    )
    checks = {}
    for name, value in arrays.items():
        exact = name in EXACT_FIELDS
        ok = (
            np.array_equal(value, expected[name])
            if exact
            else np.allclose(value, expected[name], atol=ATOL, rtol=RTOL)
        )
        checks[name] = dict(passed=bool(ok), exact=exact, values=int(value.size))
        if not exact:
            checks[name]["max_abs_error"] = float(np.max(np.abs(value - expected[name]), initial=0))
    for enabled, columns in ((pathway["da_enabled"], (0, 2)), (pathway["no_enabled"], (1, 3))):
        if not enabled:
            for name in ("segment_states", "observation_states"):
                if np.any(arrays[name][..., columns] != 0):
                    checks[name]["passed"] = False
                    checks[name]["null_branch_nonzero"] = True
    for prefix in ("segment", "observation"):
        value = arrays[prefix + "_states"]
        if not np.array_equal(arrays[prefix + "_weights"], (1 - value[..., 2]) * (1 + value[..., 3])):
            checks[prefix + "_weights"]["passed"] = False
            checks[prefix + "_weights"]["inconsistent_with_saved_states"] = True
    if not np.array_equal(arrays["segment_states"][0], np.broadcast_to(initial_state, (4, 4))):
        checks["segment_states"]["passed"] = False
        checks["segment_states"]["wrong_initial_state"] = True
    return dict(
        passed=all(x["passed"] for x in checks.values()),
        checked_values=sum(a.size for a in arrays.values()),
        checks=checks,
    ), expected


def read_case_npz(path, protocol, *, expected_binding=None):
    """Bespoke bounded NPY-header checks before NumPy allocates the known shapes."""
    contract = array_contract(protocol)
    raw_archive = _bounded_bytes(path)
    if expected_binding is not None and _bytes_identity(raw_archive) != expected_binding:
        raise ValueError("The exact consumed archive bytes do not match their binding")
    result = {}
    with zipfile.ZipFile(io.BytesIO(raw_archive)) as archive:
        names = archive.namelist()
        if len(names) != len(contract) or set(names) != {name + ".npy" for name in contract}:
            raise ValueError("Unexpected or duplicate NPZ members")
        for name, (dtype, shape) in contract.items():
            member = name + ".npy"
            payload_bytes = int(np.prod(shape)) * dtype.itemsize
            if archive.getinfo(member).file_size > payload_bytes + 4096:
                raise ValueError("Saved array exceeds declared payload envelope")
            raw = archive.read(member)
            stream = io.BytesIO(raw)
            version = np.lib.format.read_magic(stream)
            if version not in ((1, 0), (2, 0)):
                raise ValueError("Unsupported NPY version")
            reader = (
                np.lib.format.read_array_header_1_0
                if version == (1, 0)
                else np.lib.format.read_array_header_2_0
            )
            saved_shape, _, saved_dtype = reader(stream, max_header_size=4096)
            if saved_shape != shape or saved_dtype != dtype or len(raw) - stream.tell() != payload_bytes:
                raise ValueError("NPY declared shape/dtype/payload mismatch")
            result[name] = np.load(io.BytesIO(raw), allow_pickle=False)
    return result


def _bounded_bytes(path):
    path = Path(path)
    if path.stat().st_size > 1_000_000:
        raise ValueError("Source/checker artifact exceeds its one-megabyte bound")
    with path.open("rb") as stream:
        raw = stream.read(1_000_001)
    if len(raw) > 1_000_000:
        raise ValueError("Artifact grew beyond its bounded envelope")
    return raw


def _bytes_identity(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def file_identity(path):
    return _bytes_identity(_bounded_bytes(path))


def _json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON field")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError(f"Nonfinite JSON constant: {value}")

    raw = _bounded_bytes(path)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid), _bytes_identity(raw)


def validate_status(status, plan, expected_identity):
    count = len(case_specs(plan))
    if type(status.get("schema")) is not int or status["schema"] != 1:
        raise ValueError("Invalid producer schema")
    if status.get("kind") != "aso2019_source_equation_protocol" or status.get("status") != "completed":
        raise ValueError("Producer has no completed source-equation result")
    for key in ("expected_case_count", "completed_case_count"):
        if type(status.get(key)) is not int or status[key] != count:
            raise ValueError("Producer case count does not match the full matrix")
    if status.get("failed_case") is not None or status.get("error") is not None:
        raise ValueError("Producer retains a terminal error")
    elapsed = status.get("elapsed_seconds")
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or not 0 <= elapsed < 30:
        raise ValueError("Producer elapsed time is outside its finite30-second cap")
    if status.get("identity") != expected_identity:
        raise ValueError("Producer input identities differ from independently bound sources")
    for key, value in {
        "kc_classes": plan["kc_classes"],
        "state_columns": plan["state_columns"],
        "observation_labels": plan["test_observations"],
        "parameters": plan["parameters"],
        "unit": "seconds",
    }.items():
        if json.dumps(status.get(key), sort_keys=True) != json.dumps(value, sort_keys=True):
            raise ValueError(f"Producer declaration differs: {key}")
    if (
        type(status.get("started_at")) is not str
        or datetime.fromisoformat(status["started_at"]).tzinfo is None
    ):
        raise ValueError("Producer start time must be an explicit timezone-aware timestamp")
    rows = status.get("cases")
    if type(rows) is not list or len(rows) != count:
        raise ValueError("Incomplete producer case inventory")
    for row, case in zip(rows, case_specs(plan), strict=True):
        index, p, q = case["index"], case["protocol"]["id"], case["pathway"]["id"]
        if type(row) is not dict or set(row) != {
            "index",
            "protocol_id",
            "pathway_id",
            "file",
            "bytes",
            "sha256",
        }:
            raise ValueError("Incomplete case binding")
        if (
            type(row["index"]) is not int
            or row["index"] != index
            or row["protocol_id"] != p
            or row["pathway_id"] != q
        ):
            raise ValueError("Case ordering or source condition differs")
        if row["file"] != f"{index:02d}_{p}_{q}.npz":
            raise ValueError("Unexpected case artifact path")
        if type(row["bytes"]) is not int or not 0 < row["bytes"] <= 1_000_000:
            raise ValueError("Invalid case byte count")
        digest = row["sha256"]
        if type(digest) is not str or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("Invalid case SHA256")


def _write_json(path, value):
    temporary = path.with_suffix(".tmp")
    with temporary.open("w") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def audit_saved(
    plan, result, output, *, expected_identity, plan_bytes, verify_inputs=lambda: None, clock=time.monotonic
):
    """Real callers load the SHA-frozen plan; tests pass explicit toy schedules."""
    started = clock()
    result, output = Path(result), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    report = dict(
        schema=1,
        status="running",
        numerical_status=None,
        expected_case_count=len(case_specs(plan)),
        completed_case_count=0,
        rows=[],
        error=None,
        elapsed_seconds=0.0,
        input_identity=expected_identity,
        atol=ATOL,
        rtol=RTOL,
        scope="Independent source-equation saved-state verification; not behavioral or learning qualification",
    )

    def guard():
        elapsed = clock() - started
        if not math.isfinite(elapsed) or elapsed < 0 or elapsed >= 60:
            raise TimeoutError("Independent source checker exceeded its60-second cap")
        verify_inputs()
        return elapsed

    try:
        _write_json(output / "audit.json", report)
        guard()
        status, original_status = _json(result / "status.json")
        validate_status(status, plan, expected_identity)
        saved_plan = _bounded_bytes(result / "plan.json")
        if saved_plan != plan_bytes:
            raise ValueError("Saved plan differs from the frozen input bytes")
        names = {"status.json", "plan.json", *(r["file"] for r in status["cases"])}
        if {p.name for p in result.iterdir()} != names:
            raise ValueError("Unexpected or missing producer output files")
        snapshots = {"status.json": original_status, "plan.json": _bytes_identity(saved_plan)}
        for row, case in zip(status["cases"], case_specs(plan), strict=True):
            guard()
            path = result / row["file"]
            if path.resolve().parent != result.resolve():
                raise ValueError("Case artifact escapes its result directory")
            bound = {k: row[k] for k in ("bytes", "sha256")}
            if file_identity(path) != bound:
                raise ValueError("Producer case hash or length changed")
            arrays = read_case_npz(path, case["protocol"], expected_binding=bound)
            checked, reference = compare_case(
                case["protocol"],
                case["pathway"],
                arrays,
                initial_state=plan["initial_state"],
                parameters=plan["parameters"],
                guard=guard,
            )
            reference_name = f"reference_{case['index']:02d}.npz"
            with (output / reference_name).open("xb") as stream:
                np.savez_compressed(stream, **reference)
                stream.flush()
                os.fsync(stream.fileno())
            checked.update(
                index=case["index"],
                protocol_id=case["protocol"]["id"],
                pathway_id=case["pathway"]["id"],
                source_file=row["file"],
                source_binding=bound,
                reference_file=reference_name,
                reference_binding=file_identity(output / reference_name),
            )
            report["rows"].append(checked)
            report["completed_case_count"] += 1
            snapshots[row["file"]] = bound
            report["elapsed_seconds"] = guard()
            _write_json(output / "audit.json", report)

        def final_snapshot():
            guard()
            for name, identity in snapshots.items():
                if file_identity(result / name) != identity:
                    raise ValueError("Consumed producer bytes changed during the audit")
            for row in report["rows"]:
                if file_identity(output / row["reference_file"]) != row["reference_binding"]:
                    raise ValueError("Saved independent reference bytes changed")
            if {p.name for p in result.iterdir()} != names:
                raise ValueError("Producer output inventory changed")

        final_snapshot()
        report.update(
            status="completed",
            numerical_status="passed" if all(r["passed"] for r in report["rows"]) else "failed",
            elapsed_seconds=guard(),
            producer_snapshot=snapshots,
        )
        _write_json(output / "audit.json", report)
        final_snapshot()
    except Exception as exc:
        elapsed = clock() - started
        report.update(
            status="failed",
            numerical_status="failed",
            error=f"{type(exc).__name__}: {exc}",
            elapsed_seconds=elapsed if math.isfinite(elapsed) and elapsed >= 0 else None,
        )
        try:
            _write_json(output / "audit.json", report)
        except OSError:
            pass
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    plan = load_plan(args.plan)
    here = Path(__file__).resolve().parent
    helper, producer, reference = (
        here / name for name in ("aso_da_no.py", "run_aso_source_protocol.py", "aso_da_no_reference.py")
    )
    bindings = {p: file_identity(p) for p in (args.plan, helper, producer, reference, Path(__file__))}
    if bindings[helper]["sha256"] != HELPER_SHA256 or bindings[reference]["sha256"] != REFERENCE_SHA256:
        raise ValueError("Frozen source or independent reference changed")
    identity = dict(
        plan_path=str(args.plan.resolve()),
        plan_sha256=PLAN_SHA256,
        helper_path=str(helper.resolve()),
        helper_sha256=HELPER_SHA256,
        producer_path=str(producer.resolve()),
        producer_sha256=bindings[producer]["sha256"],
    )

    def verify():
        if any(file_identity(path) != value for path, value in bindings.items()):
            raise ValueError("Independent checker or declared source inputs changed")

    report = audit_saved(
        plan,
        args.result,
        args.output,
        expected_identity=identity,
        plan_bytes=_bounded_bytes(args.plan),
        verify_inputs=verify,
    )
    print(json.dumps({k: report[k] for k in ("status", "numerical_status", "completed_case_count", "error")}))
    return 0 if report["status"] == "completed" and report["numerical_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
