"""Output-only single-attempt KC local-state fixed-history rejection screen.

No engine, native library, optimizer or network client is imported. Selectors
and original-map validation are copied unchanged from run_weight_state_shadow;
its rejected weight-dependent learning law is deliberately not imported.
"""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import signal
import time
import zipfile

import numpy as np
from scipy.sparse import csr_matrix

from kc_local_state_evidence_ui import KCLocalState
from kc_weighted_bridge_replay import FIELDS, replay
from rate_adaptation_shadow import safe_npz
from weight_state_guard_reference import f32_trial_totals, point_guard

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent
EVIDENCE = ROOT / "docs/evidence/reward-mechanism-repair-2026-09-12"
CAP = HERE / "onset-history-captures/onset-history-capture-4343c21535c43f42"
MAP = EVIDENCE / "onset-capture-preregistration.samples.npz"
ANATOMY = HERE / "kc-local-anatomy-2026-09-13"
FIT = HERE / "kc-external-refit-992cef6fb05bfdb63d2b"
ATLAS = ROOT / "wiki/cells/data/neurons.csv"
FIT_AUDIT = HERE / "kc-external-refit-independent-audit-2026-09-13"
PLAN = HERE / "kc-local-shadow-frozen-2026-09-13.json"
WALL_CAP = 1200
KD_NAMES = ("tauKCdec", "tauinp", "tauadapt", "adaptscale")
WT_NAMES = ("tauinh", "inhfactor", "infp", "slf")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def binding(path):
    path = Path(path)
    return dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size, sha256=sha(path))


def verify_bindings(bindings, guard=lambda: None):
    seen = set()
    for item in bindings:
        guard()
        if (
            not isinstance(item, dict)
            or set(item) != {"path", "bytes", "sha256"}
            or not isinstance(item["path"], str)
            or type(item["bytes"]) is not int
            or item["bytes"] < 0
            or not isinstance(item["sha256"], str)
            or not re.fullmatch("[0-9a-f]{64}", item["sha256"])
        ):
            raise ValueError("Malformed source binding")
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts or str(relative) in seen:
            raise ValueError("Escaping or duplicate bound source")
        seen.add(str(relative))
        path = ROOT / relative
        if (
            any((ROOT / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1))
            or not path.is_file()
        ):
            raise ValueError("Bound sources must be regular files without symlink components")
        if path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            raise ValueError(f"Frozen source changed: {relative}")
        guard()


def strict_json(raw):
    def pairs(items):
        obj = {}
        for k, v in items:
            if k in obj:
                raise ValueError("Duplicate JSON key")
            obj[k] = v
        return obj

    def bad(value):
        raise ValueError("Nonfinite JSON token")

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)

    def finite(x):
        if isinstance(x, float) and not math.isfinite(x):
            raise ValueError("Nonfinite JSON number")
        if isinstance(x, dict):
            for v in x.values():
                finite(v)
        elif isinstance(x, list):
            for v in x:
                finite(v)

    finite(value)
    return value


def read_bytes(path, limit=128 * 1024 * 1024):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError("Invalid or oversized artifact before read")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Artifact grew beyond bounded read")
    return data


def read_json(path):
    return strict_json(read_bytes(path, 8 * 1024 * 1024))


def write_json(path, value):
    data = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()
    with Path(path).open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def write_npz(path, arrays):
    with Path(path).open("xb") as stream:
        np.savez_compressed(stream, **arrays)
        stream.flush()
        os.fsync(stream.fileno())


def study_id(identity):
    return (
        "kc-local-shadow-"
        + hashlib.sha256(json.dumps(identity, sort_keys=True, allow_nan=False).encode()).hexdigest()[:20]
    )


def validate_fit(parent, child, arrays):
    def duration(value):
        return type(value) in (int, float) and math.isfinite(value) and 0 <= value < 120

    if (
        parent.get("status") != "completed"
        or type(parent.get("exit_code")) is not int
        or parent["exit_code"] != 0
        or not duration(parent.get("elapsed_seconds"))
        or type(parent.get("hard_timeout_seconds")) is not int
        or parent["hard_timeout_seconds"] != 120
        or parent.get("no_restart") is not True
        or parent.get("bindings_unchanged") is not True
    ):
        raise ValueError("Parent fit watchdog did not attest a successful bounded single attempt")
    if (
        child.get("schema") != "external-kc-calcium-scipy-refit-v1"
        or child.get("status") != "completed"
        or child.get("stage") != "final_source_recheck"
        or not duration(child.get("elapsed_seconds"))
    ):
        raise ValueError("Fit child must finish and recheck sources within its cap")
    stages = child.get("stages", [])
    if (
        len(stages) != 4
        or [(s.get("stage"), s.get("population")) for s in stages[:2]]
        != [("decay_initialization", "KD"), ("decay_initialization", "WT")]
        or [s.get("stage") for s in stages[2:]] != ["KD", "WT"]
        or any(s.get("success") is not True for s in stages)
    ):
        raise ValueError("Complete ordered and converged fit stages required")
    for stage in stages[:2]:
        if type(stage.get("solver_status")) is not int or stage["solver_status"] not in (1, 2, 3, 4):
            raise ValueError("Invalid decay fit termination")
    for stage in stages[2:]:
        if (
            type(stage.get("solver_status")) is not int
            or stage["solver_status"] != 0
            or type(stage.get("actual_objective_calls")) is not int
            or not 1 <= stage["actual_objective_calls"] <= 3000
            or type(stage.get("iterations")) is not int
            or not 0 <= stage["iterations"] <= 500
            or type(stage.get("objective")) not in (int, float)
            or not math.isfinite(stage["objective"])
        ):
            raise ValueError("Optimizer must converge inside fixed limits")
    p = child.get("parameters", {})
    if set(p) != {"KD", "WT", "bline"} or set(p["KD"]) != set(KD_NAMES) or set(p["WT"]) != set(WT_NAMES):
        raise ValueError("Complete named fitted parameters required")
    params = dict(**p["KD"], **p["WT"], bline=p["bline"])
    # Validate source domain without processing any event or fitting anything.
    KCLocalState(params, csr_matrix((1, 1)))
    for name, keys, stage in [("kd_parameters", KD_NAMES, stages[2]), ("wt_parameters", WT_NAMES, stages[3])]:
        expected = np.array(
            [params[k] for k in keys] + ([params["bline"]] if name == "kd_parameters" else []), np.float64
        )
        actual = arrays.get(name)
        if (
            not isinstance(actual, np.ndarray)
            or actual.dtype != np.float64
            or actual.shape != expected.shape
            or not np.array_equal(actual, expected)
            or not np.array_equal(np.asarray(stage["parameters"]), expected[:4])
        ):
            raise ValueError("Fit metadata, stage and numerical artifact parameters disagree")
    return params


def expected_rows():
    games = (
        [4362, 4366, 4370, 4374, 4378, 4383, 4387, 4391],
        [4395, 4399, 4404, 4408, 4412, 4416, 4420, 4425],
    )
    runs = ("diag-rate-bridge-v1-maskgamma-de050d773763", "diag-rate-bridge-v1-maskgamma-dea14759e9ca")
    return [
        dict(
            panel=panel,
            run_id=runs[panel],
            game=game,
            seed_set=noise,
            seed=42 + game + 2000000 * panel + 1000000 * alt,
        )
        for panel in (0, 1)
        for game in games[panel]
        for alt, noise in enumerate(("base", "alt"))
    ]


def validate_rows(rows):
    if len(rows) != 32:
        raise ValueError("Exactly 32 original semantic selectors required")
    for row, expected in zip(rows, expected_rows()):
        if any(
            key not in row or type(row[key]) is not type(value) or row[key] != value
            for key, value in expected.items()
        ):
            raise ValueError("Original panel/run/game/noise/seed order changed")


def validate_maps(maps):
    shapes = dict(
        plastic_kc_indices=8866,
        plastic_compartments=8866,
        plastic_mask=8866,
        plastic_groups=8866,
        sample=4774,
        body_ids=4774,
        kc_indices=4064,
        dan_indices=24,
        sensory_indices=686,
        dan_compartments=24,
        kc_columns=4064,
        dan_columns=24,
        sensory_columns=686,
    )
    if set(maps) != set(shapes):
        raise ValueError("Complete original map fields required")
    for key, size in shapes.items():
        value = maps[key]
        if value.shape != (size,) or value.dtype.kind not in "iu" or np.any(value < 0):
            raise ValueError(f"Invalid map field {key}")
    pk, pc, mask, groups = (
        maps[k] for k in ("plastic_kc_indices", "plastic_compartments", "plastic_mask", "plastic_groups")
    )
    expected_groups = {0: 1585, 1: 316, 2: 2283, 4: 3239, 5: 1438, 6: 5}
    values, counts = np.unique(groups, return_counts=True)
    if (
        dict(zip(values.tolist(), counts.tolist())) != expected_groups
        or np.any(pk >= 4064)
        or not np.array_equal(pc, groups // 4)
    ):
        raise ValueError("Fixed anatomical edge/group/channel counts changed")
    if not np.array_equal(mask, (groups < 4) | (groups == 4)):
        raise ValueError("All home and only supported gamma away plasticity required")
    columns = np.concatenate([maps[f"{name}_columns"] for name in ("kc", "dan", "sensory")])
    if not np.array_equal(np.sort(columns), np.arange(4774)):
        raise ValueError("Sample columns must be a complete disjoint partition")
    if (
        len(np.unique(maps["sample"])) != 4774
        or len(np.unique(maps["body_ids"])) != 4774
        or np.any(maps["sample"] >= 166700)
    ):
        raise ValueError("Unique in-range sampled neuron identities required")
    for name in ("kc", "dan", "sensory"):
        if not np.array_equal(maps["sample"][maps[f"{name}_columns"]], maps[f"{name}_indices"]):
            raise ValueError("Sample/global neuron index correspondence changed")
    dc = maps["dan_compartments"]
    if np.count_nonzero(dc == 0) != 2 or np.count_nonzero(dc == 1) != 22:
        raise ValueError("Fixed 2/22 DAN populations required")
    if set(maps["body_ids"][maps["dan_columns"][dc == 0]].tolist()) != {11327, 11900}:
        raise ValueError("Home PPL101 bodies changed")
    return [(pc == c) & mask.astype(bool) for c in (0, 1)]


def load_adjacency(path):
    data = read_bytes(path, 16 * 1024 * 1024)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if sorted(z.namelist()) != ["data.npy", "format.npy", "indices.npy", "indptr.npy", "shape.npy"]:
            raise ValueError("Unexpected sparse archive members")
        member = z.getinfo("format.npy")
        if member.file_size > 256:
            raise ValueError("Oversized sparse format marker")
        marker = io.BytesIO(z.read(member))
        if np.lib.format.read_magic(marker) != (1, 0):
            raise ValueError("Unsupported sparse format marker")
        shape, _, dtype = np.lib.format.read_array_header_1_0(marker)
        if shape != () or dtype != np.dtype("S3") or marker.read() != b"csr":
            raise ValueError("Only scalar CSR format marker supported")
        numeric = io.BytesIO()
        with zipfile.ZipFile(numeric, "w") as out:
            for name in z.namelist():
                if name != "format.npy":
                    if z.getinfo(name).file_size > 16 * 1024 * 1024:
                        raise ValueError("Oversized sparse member")
                    out.writestr(name, z.read(name))
    a = safe_npz(numeric.getvalue())
    if (
        a["shape"].shape != (2,)
        or a["shape"].dtype.kind not in "iu"
        or not np.array_equal(a["shape"], [4064, 4064])
        or any(a[k].dtype.kind not in "iu" for k in ("indices", "indptr"))
    ):
        raise ValueError("Invalid full-KC sparse shape/index storage")
    matrix = csr_matrix((a["data"], a["indices"], a["indptr"]), shape=(4064, 4064))
    if matrix.nnz != 642932:
        raise ValueError("Complete fixed KC contact support required")
    return matrix


def load_classes(maps):
    with ATLAS.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    by_index = {
        int(r["graph_index"]): r for r in rows if r.get("kc_family") in ("gamma", "apbp", "ab", "other")
    }
    families = {"gamma": 0, "apbp": 1, "ab": 2, "other": 3}
    if len(by_index) != 4064:
        raise ValueError("Atlas must retain all 4064 distinct KCs")
    classes = []
    for index, body in zip(maps["kc_indices"], maps["body_ids"][maps["kc_columns"]]):
        row = by_index.get(int(index))
        if row is None or int(row["body_id"]) != int(body):
            raise ValueError("Atlas KC index/body identity mismatch")
        classes.append(families[row["kc_family"]])
    classes = np.array(classes, np.int8)
    if not np.array_equal(classes[maps["plastic_kc_indices"]], maps["plastic_groups"] % 4):
        raise ValueError("Subtype and original edge groups disagree")
    return classes


def validate_fit_audit(audit):
    if (
        audit.get("status") != "passed_fixed_parameter_source_reproduction"
        or audit.get("run_id") != FIT.name
        or audit.get("all_snapshot_bytes_unchanged") is not True
    ):
        raise ValueError("Successful independent fixed-parameter source reproduction required")
    snapshots = []
    allowed = (
        EVIDENCE / "kc-lateral-primary-source-2026-09-13",
        HERE / "kc-lateral-primary-source-2026-09-13",
        FIT,
    )
    singles = {
        HERE / "kc-local-calcium-candidate-contract-2026-09-13.md",
        HERE / "kc_external_calibration.py",
        HERE / "test_kc_external_calibration.py",
    }
    for item in audit.get("input_snapshot", []):
        path = Path(item["path"])
        if path not in singles and not any(path.is_relative_to(base) for base in allowed):
            raise ValueError("Audit snapshot outside approved source or fit inventory")
        snapshots.append(dict(item, path=str(path.relative_to(ROOT))))
    paths = {item["path"] for item in snapshots}
    required = {
        str((FIT / name).relative_to(ROOT))
        for name in (
            "plan.json",
            "execution.json",
            "result/status.json",
            "result/calibration.npz",
            "result/events.jsonl",
        )
    }
    if not required <= paths:
        raise ValueError("Independent audit did not bind all fit artifacts")
    comparison = audit.get("numeric_comparison", {})
    if comparison.get("path") != str((FIT_AUDIT / "comparison.npz").relative_to(ROOT)):
        raise ValueError("Wrong independent numerical comparison path")
    verify_bindings(snapshots + [comparison])
    return snapshots


def load_runtime(identity):
    # Paths are code-fixed, never selected by artifact-supplied arbitrary bindings.
    required = [
        MAP,
        ATLAS,
        CAP / "summary.json",
        CAP / "capture-receipt.json",
        ANATOMY / "audit.json",
        ANATOMY / "adjacency.npz",
        ANATOMY / "identities.npz",
        FIT / "plan.json",
        FIT / "execution.json",
        FIT / "result/status.json",
        FIT / "result/calibration.npz",
        FIT_AUDIT / "audit.json",
        FIT_AUDIT / "comparison.npz",
    ]
    required += [CAP / f"fine_{i:02d}.npz" for i in range(32)]
    required += [
        HERE / name
        for name in (
            "run_kc_local_shadow.py",
            "kc_local_state_evidence_ui.py",
            "kc_weighted_bridge_replay.py",
            "rate_adaptation_shadow.py",
            "weight_state_guard_reference.py",
            "kc-local-calcium-candidate-contract-2026-09-13.md",
        )
    ]
    bound = {b["path"] for b in identity.get("bindings", [])}
    if not {str(p.relative_to(ROOT)) for p in required} <= bound:
        raise ValueError("Frozen manifest omits consumed inputs or numerical implementations")
    validate_fit_audit(read_json(FIT_AUDIT / "audit.json"))
    parent_plan = read_json(FIT / "plan.json")
    parent = read_json(FIT / "execution.json")
    child = read_json(FIT / "result/status.json")
    if parent.get("run_id") != FIT.name or parent_plan.get("run_id") != FIT.name:
        raise ValueError("Fit identity mismatch")
    verify_bindings(parent_plan["identity"]["bindings"])
    params = validate_fit(parent, child, safe_npz(read_bytes(FIT / "result/calibration.npz")))
    maps = safe_npz(read_bytes(MAP))
    validate_maps(maps)
    audit = read_json(ANATOMY / "audit.json")
    verify_bindings(audit["source_files"] + [audit["implementation"]] + audit["saved"])
    ids = safe_npz(read_bytes(ANATOMY / "identities.npz"))
    if (
        set(ids) != {"kc_indices", "body_ids"}
        or not np.array_equal(ids["kc_indices"], maps["kc_indices"])
        or not np.array_equal(ids["body_ids"], maps["body_ids"][maps["kc_columns"]])
    ):
        raise ValueError("Local anatomy KC order differs from capture")
    adjacency = load_adjacency(ANATOMY / "adjacency.npz")
    KCLocalState(params, adjacency)
    capture = read_json(CAP / "summary.json")
    rows = [
        dict(panel=i // 16, **{k: row[k] for k in ("run_id", "game", "seed_set", "seed")})
        for i, row in enumerate(capture["rows"])
    ]
    validate_rows(rows)
    if capture.get("status") != "complete" or rows != identity["rows"]:
        raise ValueError("Complete captured selectors changed")
    return params, adjacency, maps, load_classes(maps), capture


def read_capture(index, maps, capture):
    path = CAP / f"fine_{index:02d}.npz"
    saved = capture["saved"][index + 1]
    data = read_bytes(path)
    if saved["file"] != path.name or saved["sha256"] != hashlib.sha256(data).hexdigest():
        raise ValueError("Capture receipt order/hash mismatch")
    a = safe_npz(data)
    trace, original = a["trace"], a["gains"]
    if trace.shape != (2000, 4774) or trace.dtype.kind not in "iu" or not np.isin(trace, [0, 1]).all():
        raise ValueError("Invalid complete captured raster")
    if (
        original.shape != (8866,)
        or original.dtype != np.float32
        or not np.isfinite(original).all()
        or np.any(original < 0.5)
        or np.any(original > 1.5)
    ):
        raise ValueError("Invalid original gain comparator")
    if a["pulse_times_ms"].size or a["pulse_dan_indices"].size:
        raise ValueError("Untaught capture includes imposed teaching")
    if not np.array_equal(trace.sum(0), a["counts"][maps["sample"]]) or not np.array_equal(
        trace[:, maps["dan_columns"]].sum(0), a["dan_counts"]
    ):
        raise ValueError("Captured spike counts disagree")
    return trace, original


def evaluate_history(trace, params, adjacency, maps, classes, guard=lambda: None):
    local = KCLocalState(params, adjacency)
    kc = trace[:, maps["kc_columns"]]
    if kc.shape != (2000, local.n_kc) or kc.dtype.kind not in "iub" or not np.isin(kc, [0, 1]).all():
        raise ValueError("Exactly 2000 binary KC frames required")
    weighted = np.empty(kc.shape, np.float64)
    states = [np.zeros((4, local.n_kc))]
    counts = []
    sus = [local.susceptibility]
    for step, event in enumerate(kc):
        if step % 50 == 0:
            guard()
        if (local.source_frames + 1) * 5000 <= local.native_step * 30:
            counts.append(local.pending_counts)
            local.advance_boundary()
            states.append(np.stack((local.calyx, local.lobe, local.adaptation, local.inhibition)))
            sus.append(local.susceptibility)
        weighted[step] = local.consume(event)
    counts.append(local.pending_counts)
    local.advance_boundary()
    states.append(np.stack((local.calyx, local.lobe, local.adaptation, local.inhibition)))
    sus.append(local.susceptibility)
    if local.native_step != 2000 or local.source_frames != 12 or local.pending_counts.any():
        raise ValueError("Incomplete rational-clock endpoint")
    dan = trace[:, maps["dan_columns"]]
    means = np.column_stack([dan[:, maps["dan_compartments"] == c].mean(axis=1) for c in (0, 1)])
    guard()
    result = replay(
        weighted,
        means,
        maps["plastic_kc_indices"],
        maps["plastic_compartments"],
        maps["plastic_mask"],
        maps["plastic_groups"],
    )
    guard()
    result.update(
        local_frame_states=np.array(states),
        source_frame_counts=np.array(counts),
        local_susceptibility=np.array(sus),
        kc_classes=classes.copy(),
        raw_event_totals=kc.sum(0, dtype=np.int64),
        weighted_event_totals=weighted.sum(0),
        weighted_post_onset_totals=weighted[500:].sum(0),
    )
    validate_result(result, maps)
    return result


def validate_result(value, maps):
    mask = maps["plastic_mask"].astype(bool)
    ne = len(mask)
    nk = len(maps["kc_columns"])
    shapes = dict(
        gains=(ne,),
        double_gains=(ne,),
        electrical_gains=(ne,),
        electrical_double_gains=(ne,),
        edge_phases=(4, ne, 8),
        group_phases=(4, 8, 8),
        bound_counts=(2, ne),
        publication_counts=(4, ne),
        endpoint_kc=(nk, 2),
        endpoint_dan=(2, 2),
        local_frame_states=(13, 4, nk),
        source_frame_counts=(12, nk),
        local_susceptibility=(13, nk),
        kc_classes=(nk,),
        raw_event_totals=(nk,),
        weighted_event_totals=(nk,),
        weighted_post_onset_totals=(nk,),
    )
    if set(value) != set(shapes):
        raise ValueError("Complete result array inventory required")
    for key, shape in shapes.items():
        x = value[key]
        expected = (
            np.float32
            if key in ("gains", "electrical_gains")
            else np.int64
            if key in ("bound_counts", "publication_counts", "source_frame_counts", "raw_event_totals")
            else np.int8
            if key == "kc_classes"
            else np.float64
        )
        if (
            not isinstance(x, np.ndarray)
            or x.shape != shape
            or x.dtype != expected
            or not np.isfinite(x).all()
        ):
            raise ValueError(f"Invalid result array: {key}")
    for key in ("gains", "double_gains", "electrical_gains", "electrical_double_gains"):
        if (
            np.any(value[key] < 0.5)
            or np.any(value[key] > 1.5)
            or not np.array_equal(value[key][~mask], np.ones(np.count_nonzero(~mask), value[key].dtype))
        ):
            raise ValueError("Gain bound or masked-byte invariant violated")
    phase = value["edge_phases"]
    if (
        phase[:, ~mask].any()
        or value["bound_counts"][:, ~mask].any()
        or np.any(phase[:, :, 0] < 0)
        or np.any(phase[:, :, 1] > 0)
    ):
        raise ValueError("Invalid masked/signed area evidence")
    expected = np.array([150, 850, 500, 1])[:, None] * mask.astype(np.int64)
    if (
        not np.array_equal(value["publication_counts"], expected)
        or np.any(value["bound_counts"] < 0)
        or not np.array_equal(phase[:, :, 5:7].sum(0).T, value["bound_counts"])
    ):
        raise ValueError("Publication/bound observations disagree")
    if not np.array_equal(phase[:, :, 4].sum(0), value["gains"].astype(float) - 1):
        raise ValueError("Published gain delta reconciliation failed")
    if not np.allclose(
        phase[:, :, 3].sum(0), value["double_gains"] - 1, atol=2e-12, rtol=0
    ) or not np.allclose(phase[:, :, 2], phase[:, :, :2].sum(2), atol=2e-12, rtol=2e-12):
        raise ValueError("Double integral reconciliation failed")
    for group in range(8):
        if not np.allclose(
            phase[:, maps["plastic_groups"] == group].sum(1),
            value["group_phases"][:, group],
            atol=2e-11,
            rtol=2e-12,
        ):
            raise ValueError("Per-group evidence differs from edge mapping")
    if (
        np.any(value["local_frame_states"] < 0)
        or np.any(value["local_frame_states"][:, 1] > value["local_frame_states"][:, 0])
        or np.any(value["source_frame_counts"] < 0)
        or np.any(value["local_susceptibility"] < 0)
        or np.any(value["local_susceptibility"] > 1)
        or np.any(value["weighted_event_totals"] > value["raw_event_totals"] + 1e-12)
    ):
        raise ValueError("Local-state domain evidence invalid")


def guard_summary(rows, maps):
    validate_rows(rows)
    selectors = [(maps["plastic_compartments"] == c) & maps["plastic_mask"].astype(bool) for c in (0, 1)]
    result = {}
    for panel in (0, 1):
        for noise in ("base", "alt"):
            subset = [row for row in rows if row["panel"] == panel and row["seed_set"] == noise]
            for channel, selector in zip(("home", "away"), selectors):
                ticks = f32_trial_totals(np.stack([r["gains"][selector] for r in subset]))
                values = np.asarray(ticks, dtype=float) / 2**24
                result[f"{panel}/{noise}/{channel}"] = dict(
                    ticks=ticks,
                    point_pass=point_guard(ticks),
                    mean=float(values.mean()),
                    sample_sd=float(values.std(ddof=1)),
                    limit=float(0.5 * values.std(ddof=1)),
                )
    return result


def prepare(*, review_paths=(), plan_path=PLAN):
    # Read-only checks and binding construction; creates only the new plan.
    capture = read_json(CAP / "summary.json")
    rows = [
        dict(panel=i // 16, **{k: row[k] for k in ("run_id", "game", "seed_set", "seed")})
        for i, row in enumerate(capture["rows"])
    ]
    validate_rows(rows)
    paths = [
        HERE / name
        for name in (
            "run_kc_local_shadow.py",
            "test_run_kc_local_shadow.py",
            "kc_local_state_evidence_ui.py",
            "test_kc_local_state_evidence_ui.py",
            "test_kc_local_clock_independent.py",
            "kc_weighted_bridge_replay.py",
            "test_kc_weighted_bridge_replay.py",
            "rate_adaptation_shadow.py",
            "weight_state_guard_reference.py",
            "kc_local_anatomy.py",
            "test_kc_local_anatomy.py",
            "test_kc_local_bridge_composition.py",
            "audit_kc_local_shadow.py",
            "test_audit_kc_local_shadow.py",
            "kc-local-shadow-independent-audit-contract-2026-09-13.md",
            "kc-local-calcium-candidate-contract-2026-09-13.md",
        )
    ]
    paths += [MAP, ATLAS, CAP / "summary.json", CAP / "capture-receipt.json"] + [
        CAP / f"fine_{i:02d}.npz" for i in range(32)
    ]
    paths += [ANATOMY / name for name in ("adjacency.npz", "identities.npz", "audit.json")]
    paths += [
        FIT / name
        for name in (
            "plan.json",
            "execution.json",
            "stdout.txt",
            "result/status.json",
            "result/events.jsonl",
            "result/calibration.npz",
        )
    ]
    paths += [
        ROOT / "bet36fly/reward_lif.cpp",
        ROOT / "docs/connectome-source-lock.json",
        FIT_AUDIT / "audit.json",
        FIT_AUDIT / "comparison.npz",
    ]
    if not review_paths:
        raise ValueError(
            "Independent fit and runner review receipts must be explicitly bound before preparation"
        )
    paths += [Path(p) for p in review_paths]
    initial = [binding(p) for p in paths]
    fit_plan = read_json(FIT / "plan.json")
    anatomy = read_json(ANATOMY / "audit.json")
    initial += fit_plan["identity"]["bindings"] + anatomy["source_files"] + [anatomy["implementation"]]
    initial += validate_fit_audit(read_json(FIT_AUDIT / "audit.json"))
    inventory = {}
    for b in initial:
        if b["path"] in inventory and inventory[b["path"]] != b:
            raise ValueError("Contradictory source bindings")
        inventory[b["path"]] = b
    bindings = list(inventory.values())
    verify_bindings(bindings)
    identity = dict(
        analysis="kc-local-shadow-v1",
        bindings=bindings,
        rows=rows,
        wall_cap_seconds=WALL_CAP,
        helper_evaluations=32,
        circuit_calls=0,
        network_requests=0,
        source_hz=30,
        native_hz=5000,
        fit_identity=FIT.name,
        phase_fields=list(FIELDS),
    )
    load_runtime(identity)
    for i in range(32):
        # Binding inspection only, not a candidate calculation or raster decode.
        saved = capture["saved"][i + 1]
        if saved["file"] != f"fine_{i:02d}.npz" or saved["sha256"] != sha(CAP / saved["file"]):
            raise ValueError("Captured inventory differs from saved receipt")
    verify_bindings(bindings)
    plan = dict(
        identity=identity, run_id=study_id(identity), prepared_at=datetime.now(timezone.utc).isoformat()
    )
    write_json(plan_path, plan)
    return plan


def execute_plan(plan, output, clock=time.monotonic):
    started = clock()
    identity = plan["identity"]
    sid = plan["run_id"]
    output = Path(output)
    if (
        study_id(identity) != sid
        or identity.get("analysis") != "kc-local-shadow-v1"
        or type(identity.get("wall_cap_seconds")) is not int
        or identity["wall_cap_seconds"] != 1200
        or identity.get("helper_evaluations") != 32
        or identity.get("circuit_calls") != 0
        or identity.get("network_requests") != 0
    ):
        raise ValueError("Frozen identity/caps differ")
    validate_rows(identity["rows"])
    output.mkdir(exist_ok=False)
    rows = []
    attempted = 0
    saved = []
    contacts = 0
    status = "failed"
    error = None
    result = dict(screen="invalid_or_incomplete", qualification="not qualified")

    def guard():
        if clock() - started >= WALL_CAP - 10:
            raise TimeoutError("Ten-second terminal-record reserve reached")

    def deadline(*_):
        raise TimeoutError("Whole-study 1200-second cap reached")

    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, WALL_CAP - (clock() - started)))
    try:
        write_json(output / "identity.json", plan)
        verify_bindings(identity["bindings"], guard)
        params, adjacency, maps, classes, capture = load_runtime(identity)
        guard()
        with (output / "attempts.jsonl").open("x") as journal:

            def event(value):
                journal.write(json.dumps(value, allow_nan=False) + "\n")
                journal.flush()
                os.fsync(journal.fileno())

            for i, meta in enumerate(identity["rows"]):
                guard()
                trace, original = read_capture(i, maps, capture)
                guard()
                event(dict(event="attempt", index=i, elapsed_seconds=clock() - started))
                guard()
                attempted += 1
                value = evaluate_history(trace, params, adjacency, maps, classes, guard=guard)
                guard()
                validate_result(value, maps)
                target = output / f"shadow_{i:02d}.npz"
                write_npz(
                    target,
                    dict(
                        **value,
                        original_gains=original,
                        plastic_mask=maps["plastic_mask"],
                        plastic_groups=maps["plastic_groups"],
                    ),
                )
                item = dict(file=target.name, bytes=target.stat().st_size, sha256=sha(target))
                saved.append(item)
                bound = int(value["bound_counts"].sum())
                detail = dict(
                    **meta,
                    index=i,
                    fields=list(FIELDS),
                    bound_contacts=bound,
                    local_source_frames=12,
                    subtypes={},
                )
                for name, c in [("gamma", 0), ("apbp", 1), ("ab", 2), ("other", 3)]:
                    select = classes == c
                    detail["subtypes"][name] = dict(
                        kcs=int(select.sum()),
                        raw_events=int(value["raw_event_totals"][select].sum()),
                        weighted_events=float(value["weighted_event_totals"][select].sum()),
                        min_susceptibility=float(value["local_susceptibility"][:, select].min())
                        if select.any()
                        else None,
                    )
                write_json(output / f"row_{i:02d}.json", detail)
                guard()
                event(dict(event="complete", index=i, artifact=item, elapsed_seconds=clock() - started))
                rows.append(dict(**meta, gains=value["gains"]))
                contacts += bound
                print(json.dumps(dict(index=i, completed=len(rows), bound_contacts=bound)), flush=True)
        guards = guard_summary(rows, maps)
        verify_bindings(identity["bindings"], guard)
        guard()
        result = dict(
            guards=guards,
            bound_contacts=contacts,
            screen="reject"
            if contacts or not all(g["point_pass"] for g in guards.values())
            else "permits_independent_audit_only",
            qualification="not qualified; fixed untaught histories only",
            numerical_audit="pending independent saved-artifact audit",
        )
        status = "complete"
    except (Exception, KeyboardInterrupt) as exc:
        status = "budget_stopped" if isinstance(exc, TimeoutError) else "failed"
        error = f"{type(exc).__name__}: {exc}"
    summary = dict(
        run_id=sid,
        status="computed" if status == "complete" else status,
        error=error,
        attempted=attempted,
        completed=len(rows),
        saved=saved,
        elapsed_seconds=clock() - started,
        native_calls=0,
        circuit_calls=0,
        network_requests=0,
        **result,
    )
    try:
        if clock() - started >= WALL_CAP:
            raise TimeoutError("Cap reached before terminal persistence")
        write_json(output / "summary.json", summary)
        if clock() - started >= WALL_CAP:
            raise TimeoutError("Cap crossed during summary persistence")
        write_json(
            output / "completion.json",
            dict(
                run_id=sid,
                status=status,
                summary_sha256=sha(output / "summary.json"),
                elapsed_through_summary_seconds=clock() - started,
                attempted=attempted,
                completed=len(rows),
            ),
        )
        if clock() - started >= WALL_CAP:
            raise TimeoutError("Cap crossed during completion persistence")
    except (Exception, KeyboardInterrupt) as exc:
        status = "budget_stopped" if isinstance(exc, TimeoutError) else "failed"
        result["screen"] = "invalid_or_incomplete"
        write_json(
            output / "terminal-error.json",
            dict(
                run_id=sid,
                status=status,
                error=f"{type(exc).__name__}: {exc}",
                elapsed_seconds=clock() - started,
            ),
        )
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    return dict(
        run_id=sid,
        status=status,
        attempted=attempted,
        completed=len(rows),
        elapsed_seconds=clock() - started,
        **result,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--plan", type=Path, default=PLAN)
    parser.add_argument("--review", action="append", type=Path, default=[])
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(prepare(review_paths=args.review, plan_path=args.plan)))
        return 0
    plan = read_json(args.plan)
    result = execute_plan(plan, HERE / plan["run_id"])
    print(json.dumps(result, allow_nan=False))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
