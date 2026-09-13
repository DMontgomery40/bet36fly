"""Independent saved-output audit; execution requires explicit frozen-study paths.

No simulator or efficient candidate imports. The scalar reference rebuilds the
four fixed edges' event histories independently. All enclosures and scientific
decisions remain conditional on the preregistered numerical allowances.
"""

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import signal
import time

import numpy as np

from weight_state_guard_reference import allowance_totals, classify_box, f32_trial_totals, point_guard
from weight_state_reference import event_reference

ROOT = Path(__file__).resolve().parents[3]
GAIN_ATOL = 1e-11
AREA_ATOL = 2e-11
WALL_CAP = 1200
FIELDS = (
    "positive",
    "negative",
    "attempted",
    "double_applied",
    "published_applied",
    "bound_low",
    "bound_high",
    "rounding_ambiguous",
)
CAPTURE = Path(
    "output/collaboration/reward-mechanism-repair/onset-history-captures/"
    "onset-history-capture-4343c21535c43f42"
)
MAP = Path("docs/evidence/reward-mechanism-repair-2026-09-12/onset-capture-preregistration.samples.npz")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def binding(path, root=ROOT):
    path = Path(path)
    return dict(path=str(path.relative_to(root)), bytes=path.stat().st_size, sha256=sha(path))


def verify_bindings(items, root=ROOT, guard=lambda: None):
    seen = set()
    for item in items:
        guard()
        name = item["path"]
        path = Path(name)
        require(
            isinstance(name, str)
            and not path.is_absolute()
            and ".." not in path.parts
            and str(path) == name
            and name not in seen
            and name != ".",
            "Invalid bound path",
        )
        seen.add(name)
        require(type(item["bytes"]) is int and item["bytes"] >= 0, "Invalid bound byte count")
        for i in range(1, len(path.parts) + 1):
            require(not (root / Path(*path.parts[:i])).is_symlink(), "Symbolic bound source")
        actual = root / path
        require(
            actual.is_file() and actual.stat().st_size == item["bytes"] and sha(actual) == item["sha256"],
            f"Changed source {name}",
        )
        guard()


def json_default(value):
    if isinstance(value, Fraction):
        return dict(numerator=value.numerator, denominator=value.denominator)
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def normalized(value):
    return json.loads(json.dumps(value, default=json_default, allow_nan=False))


def write_json(path, value):
    encoded = json.dumps(value, indent=2, default=json_default, allow_nan=False) + "\n"
    with Path(path).open("x") as stream:
        stream.write(encoded)


def read_json(path):
    return json.loads(Path(path).read_text())


def study_id(identity):
    return (
        "weight-state-shadow-"
        + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:20]
    )


def bounded_clock(value):
    return type(value) in (int, float) and np.isfinite(value) and 0 <= value < WALL_CAP


def check_terminal(directory, plan, root=ROOT):
    directory = Path(directory)
    require(not (directory / "terminal-error.json").exists(), "Terminal failure invalidates completion")
    require(study_id(plan["identity"]) == plan["run_id"], "Study identity hash mismatch")
    require(read_json(directory / "identity.json") == plan, "Stored identity changed")
    expected = {"identity.json", "attempts.jsonl", "summary.json", "completion.json"}
    expected |= {
        f"{prefix}_{i:02d}.{suffix}"
        for i in range(32)
        for prefix, suffix in (("shadow", "npz"), ("row", "json"))
    }
    require({p.name for p in directory.iterdir()} == expected, "Incomplete or unexpected artifact inventory")
    require(all(p.is_file() and not p.is_symlink() for p in directory.iterdir()), "Nonregular artifact")
    summary = read_json(directory / "summary.json")
    completion = read_json(directory / "completion.json")
    for value, status in ((summary, "computed"), (completion, "complete")):
        require(
            value["run_id"] == plan["run_id"] and value["status"] == status,
            "Matching computed and complete statuses required",
        )
        require(
            type(value["attempted"]) is int
            and type(value["completed"]) is int
            and value["attempted"] == value["completed"] == 32,
            "Exactly 32 durable rows required",
        )
    require(summary["error"] is None, "Completed summary carries an error")
    require(
        all(
            type(summary[k]) is int and summary[k] == 0
            for k in ("circuit_calls", "native_calls", "network_requests")
        ),
        "Nonzero external calls",
    )
    require(completion["summary_sha256"] == sha(directory / "summary.json"), "Stale summary hash")
    require(
        bounded_clock(summary["elapsed_seconds"])
        and bounded_clock(completion["elapsed_through_summary_seconds"])
        and summary["elapsed_seconds"] <= completion["elapsed_through_summary_seconds"],
        "Incomplete or over-cap terminal timing",
    )
    saved = summary["saved"]
    require(len(saved) == 32, "Exactly 32 saved array bindings required")
    require(
        saved == [binding(directory / f"shadow_{i:02d}.npz", root) for i in range(32)],
        "Saved archive order, bytes or hashes changed",
    )
    journal = [json.loads(line) for line in (directory / "attempts.jsonl").read_text().splitlines()]
    require(len(journal) == 64, "Exactly 64 durable journal rows required")
    last = 0
    for j, item in enumerate(journal):
        i, completion_event = divmod(j, 2)
        require(
            type(item["index"]) is int
            and item["index"] == i
            and item["event"] == ("complete" if completion_event else "attempt"),
            "Journal order changed",
        )
        require(
            bounded_clock(item["elapsed"]) and last <= item["elapsed"] <= summary["elapsed_seconds"],
            "Invalid journal chronology",
        )
        last = item["elapsed"]
        require(
            item["artifact"] == saved[i] if completion_event else item["source"] == f"fine_{i:02d}.npz",
            "Journal source or artifact changed",
        )
    return summary


def expected_rows():
    # Independently expressed original cue/seed grid, not read from runner code.
    cues = (
        (4362, 4366, 4370, 4374, 4378, 4383, 4387, 4391),
        (4395, 4399, 4404, 4408, 4412, 4416, 4420, 4425),
    )
    ids = ("diag-rate-bridge-v1-maskgamma-de050d773763", "diag-rate-bridge-v1-maskgamma-dea14759e9ca")
    rows = []
    for panel in range(2):
        for game in cues[panel]:
            for alternate in range(2):
                rows.append(
                    dict(
                        panel=panel,
                        run_id=ids[panel],
                        game=game,
                        seed_set=("base", "alt")[alternate],
                        seed=42 + game + panel * 2000000 + alternate * 1000000,
                    )
                )
    return rows


def check_rows(rows):
    require(len(rows) == 32, "Complete row matrix required")
    for actual, expected in zip(rows, expected_rows()):
        require(
            all(type(actual.get(k)) is type(v) and actual.get(k) == v for k, v in expected.items()),
            "Fixed row identity changed",
        )


def select_edges(groups):
    result = []
    for group in (0, 1, 2, 4):
        indices = np.flatnonzero(groups == group)
        require(len(indices) > 0, "Missing eligible reference group")
        result.append(int(indices[len(indices) // 2]))
    return result


def check_maps(m):
    sizes = dict(
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
    require(set(m) == set(sizes), "Complete map fields required")
    for name, size in sizes.items():
        require(
            m[name].shape == (size,) and m[name].dtype.kind in "iu" and np.all(m[name] >= 0),
            f"Invalid map {name}",
        )
    groups, pc, mask = m["plastic_groups"], m["plastic_compartments"], m["plastic_mask"]
    values, counts = np.unique(groups, return_counts=True)
    require(
        dict(zip(values.tolist(), counts.tolist())) == {0: 1585, 1: 316, 2: 2283, 4: 3239, 5: 1438, 6: 5},
        "Anatomical group counts changed",
    )
    require(
        np.array_equal(pc, groups // 4) and np.all(m["plastic_kc_indices"] < 4064), "Invalid edge routing"
    )
    require(np.array_equal(mask, (groups < 4) | (groups == 4)), "Eligibility changed")
    all_columns = np.concatenate([m[f"{x}_columns"] for x in ("kc", "dan", "sensory")])
    require(np.array_equal(np.sort(all_columns), np.arange(4774)), "Columns not a disjoint partition")
    require(
        len(np.unique(m["sample"])) == len(np.unique(m["body_ids"])) == 4774 and np.all(m["sample"] < 166700),
        "Invalid sampled identities",
    )
    for kind in ("kc", "dan", "sensory"):
        require(
            np.array_equal(m["sample"][m[f"{kind}_columns"]], m[f"{kind}_indices"]),
            "Local/global mapping mismatch",
        )
    dc = m["dan_compartments"]
    require(np.count_nonzero(dc == 0) == 2 and np.count_nonzero(dc == 1) == 22, "DAN populations changed")
    require(set(m["body_ids"][m["dan_columns"][dc == 0]]) == {11327, 11900}, "Home DAN identities changed")
    return [(pc == c) & mask.astype(bool) for c in (0, 1)]


def close(a, b, tolerance, message):
    require(
        np.asarray(a).shape == np.asarray(b).shape
        and np.isfinite(a).all()
        and np.isfinite(b).all()
        and np.all(np.abs(np.asarray(a) - np.asarray(b)) <= tolerance),
        message,
    )


def check_arrays(a, mask, groups):
    n = len(mask)
    shape_types = {k: ((n,), np.float32) for k in ("gains", "electrical_gains", "original_gains")}
    shape_types.update(
        {
            k: ((n,), np.float64)
            for k in ("double_gains", "electrical_double_gains", "gain_lower", "gain_upper")
        }
    )
    shape_types.update(
        phase_end_double_gains=((4, n), np.float64),
        phases=((4, n, 8), np.float64),
        grouped=((4, 8, 8), np.float64),
        publication_counts=((n,), np.int64),
        conditional_bound_counts=((2, n), np.int64),
        estimated_integration_error=((3, n), np.float64),
        rounding_ambiguous=((n,), np.int64),
    )
    require(set(a) == set(shape_types), "Incomplete array fields")
    for key, (shape, dtype) in shape_types.items():
        require(
            a[key].shape == shape and a[key].dtype == np.dtype(dtype) and np.isfinite(a[key]).all(),
            f"Invalid array storage {key}",
        )
    active = np.asarray(mask, bool)
    require(groups.shape == (n,) and np.all((groups >= 0) & (groups < 8)), "Invalid group map")
    for key in (
        "gains",
        "double_gains",
        "electrical_gains",
        "electrical_double_gains",
        "phase_end_double_gains",
        "gain_lower",
        "gain_upper",
    ):
        require(np.all((a[key] >= 0.5) & (a[key] <= 1.5)), "Gain outside continuous bounds")
    for key in (
        "gains",
        "double_gains",
        "electrical_gains",
        "electrical_double_gains",
        "gain_lower",
        "gain_upper",
    ):
        require(np.all(a[key][~active] == 1), "Excluded checkpoint changed")
    phases, ends = a["phases"], a["phase_end_double_gains"]
    require(np.all(ends[:, ~active] == 1) and not np.any(phases[:, ~active]), "Excluded phase changed")
    for key in ("conditional_bound_counts", "estimated_integration_error"):
        require(np.all(a[key] >= 0) and not np.any(a[key][:, ~active]), "Invalid diagnostic domain/mask")
    require(
        np.array_equal(a["publication_counts"], active.astype(np.int64) * 1501), "Publication count changed"
    )
    counts = phases[:, :, 5:]
    require(
        np.all(counts == np.floor(counts))
        and np.all(counts >= 0)
        and np.all(counts <= np.array([150, 850, 500, 1])[:, None, None]),
        "Invalid phase counter domain",
    )
    require(
        np.array_equal(a["rounding_ambiguous"], counts[:, :, 2].sum(0).astype(np.int64)),
        "Ambiguity totals differ",
    )
    require(
        np.all(a["conditional_bound_counts"] <= 1501)
        and np.all(a["conditional_bound_counts"] >= counts[:, :, :2].sum(0).T),
        "Possible-bound totals invalid",
    )
    require(np.all(phases[:, :, 0] >= 0) and np.all(phases[:, :, 1] <= 0), "Signed branch areas invalid")
    close(phases[:, :, 2], phases[:, :, :2].sum(2), 2 * AREA_ATOL, "Attempted area mismatch")
    close(phases[:, :, 3], phases[:, :, 2], 2 * AREA_ATOL, "Gain/area mismatch")
    previous = np.vstack([np.ones(n), ends[:3]])
    close(phases[:, :, 3], ends - previous, GAIN_ATOL, "Phase gain delta mismatch")
    close(phases[:, :, 3].sum(0), a["double_gains"] - 1, GAIN_ATOL, "Complete double accounting mismatch")
    close(
        phases[:, :, :2].sum((0, 2)),
        a["double_gains"] - 1,
        2 * AREA_ATOL,
        "Complete signed area accounting mismatch",
    )
    require(
        np.array_equal(
            phases[:, :, 4], ends.astype(np.float32).astype(float) - previous.astype(np.float32).astype(float)
        ),
        "Exact phase float32 accounting mismatch",
    )
    require(
        np.array_equal(phases[:, :, 4].sum(0), a["gains"].astype(float) - 1),
        "Exact total float32 accounting mismatch",
    )
    for phase, double_name, float_name in (
        (2, "electrical_double_gains", "electrical_gains"),
        (3, "double_gains", "gains"),
    ):
        require(
            np.array_equal(ends[phase], a[double_name])
            and np.array_equal(ends[phase].astype(np.float32), a[float_name]),
            "Checkpoint publication mismatch",
        )
    rebuilt = np.zeros((4, 8, 8))
    for phase in range(4):
        for group in range(8):
            # Explicit original-edge accumulation, independent of helper np.add.at.
            for row in phases[phase, groups == group]:
                rebuilt[phase, group] += row
    require(np.array_equal(rebuilt, a["grouped"]), "Group accounting mismatch")
    # Validate exact rational containment, not approximate float64 endpoints.
    allowance = Fraction.from_float(GAIN_ATOL)
    for edge in np.flatnonzero(active):
        center = Fraction.from_float(float(a["double_gains"][edge]))
        require(
            Fraction.from_float(float(a["gain_lower"][edge])) <= max(Fraction(1, 2), center - allowance)
            and Fraction.from_float(float(a["gain_upper"][edge])) >= min(Fraction(3, 2), center + allowance),
            "Diagnostic enclosure rounded inward",
        )
    for phase in range(4):
        gain = ends[phase]
        low = np.maximum(np.nextafter(gain - GAIN_ATOL, -np.inf), 0.5)
        high = np.minimum(np.nextafter(gain + GAIN_ATOL, np.inf), 1.5)
        actual = (
            (gain <= 0.5) | (gain.astype(np.float32) <= 0.5),
            (gain >= 1.5) | (gain.astype(np.float32) >= 1.5),
        )
        for side in range(2):
            require(
                np.all(counts[phase, :, side][active] >= actual[side][active]), "Saved endpoint bound omitted"
            )
        # All four saved endpoints are different publications, so their lower count is additive.
        if phase == 0:
            possible_endpoint_counts = np.zeros((2, n), np.int64)
        possible_endpoint_counts[0] += active & ((low <= 0.5) | (low.astype(np.float32) <= 0.5))
        possible_endpoint_counts[1] += active & ((high >= 1.5) | (high.astype(np.float32) >= 1.5))
    require(
        np.all(a["conditional_bound_counts"] >= possible_endpoint_counts), "Possible endpoint bound omitted"
    )
    return dict(
        publications=int(a["publication_counts"].sum()),
        actual_bound_contacts=int(counts[:, :, :2].sum()),
        conditional_bound_contacts=int(a["conditional_bound_counts"].sum()),
        rounding_ambiguous_publications=int(a["rounding_ambiguous"].sum()),
    )


def edge_events(trace, maps, edge):
    column = maps["kc_columns"][maps["plastic_kc_indices"][edge]]
    channel = maps["plastic_compartments"][edge]
    dan_columns = maps["dan_columns"][maps["dan_compartments"] == channel]
    require(len(dan_columns) > 0, "Empty DAN population")
    k = np.flatnonzero(trace[500:, column]) * 0.2
    d = np.nonzero(trace[500:, dan_columns])[0] * 0.2
    return k, d, np.full(len(d), 1.0 / len(dan_columns))


def compare_reference(a, edge, ref):
    phases = a["phases"][:, edge]
    actual = dict(
        gain=float(a["double_gains"][edge]),
        electrical_gain=float(a["electrical_double_gains"][edge]),
        positive=float(phases[:, 0].sum()),
        negative=float(phases[:, 1].sum()),
        electrical_positive=float(phases[:3, 0].sum()),
        electrical_negative=float(phases[:3, 1].sum()),
        tail_positive=float(phases[3, 0]),
        tail_negative=float(phases[3, 1]),
    )
    errors = {k: abs(v - float(ref[k])) for k, v in actual.items()}
    require(np.isfinite(list(errors.values())).all(), "Nonfinite independent comparison")
    passed = all(
        v <= (GAIN_ATOL if k in ("gain", "electrical_gain") else AREA_ATOL) for k, v in errors.items()
    )
    return dict(
        passed=passed, actual=actual, reference={k: float(ref[k]) for k in actual}, absolute_errors=errors
    )


def recompute_guards(rows, selectors):
    require(
        len(rows) == 32 and len(selectors) == 2 and all(np.any(s) for s in selectors),
        "Incomplete guard matrix",
    )
    result = {}
    for panel in (0, 1):
        for noise in ("base", "alt"):
            selected = [r for r in rows if r["panel"] == panel and r["seed_set"] == noise]
            require(len(selected) == 8, "Exactly eight rows per guard required")
            for channel, selector in zip(("home", "away"), selectors):
                ticks = f32_trial_totals(np.stack([r["gains"][selector] for r in selected]))
                lo, hi = allowance_totals(
                    np.stack([r["double_gains"][selector] for r in selected]), GAIN_ATOL
                )
                values = np.array(ticks, dtype=float) / 2**24
                result[f"{panel}/{noise}/{channel}"] = dict(
                    ticks=ticks,
                    lower_ticks=lo,
                    upper_ticks=hi,
                    point_pass=point_guard(ticks),
                    mean=float(values.mean()),
                    sample_sd=float(values.std(ddof=1)),
                    limit=float(values.std(ddof=1) * 0.5),
                    conditional=classify_box(lo, hi),
                )
    return result


def screen_verdict(guards, contacts):
    states = [v["conditional"]["classification"] for v in guards.values()]
    require(
        len(states) == 8 and set(states) <= {"all_pass", "all_fail", "inconclusive"}, "Invalid guard states"
    )
    return (
        "reject"
        if contacts or "all_fail" in states
        else "permits_circuit_consideration"
        if set(states) == {"all_pass"}
        else "inconclusive"
    )


def audit_verdict(references, computed_shadow_screen):
    passed = bool(references) and all(r["passed"] for r in references)
    return dict(
        status="pass" if passed else "numerical_failure",
        screen=computed_shadow_screen if passed else "invalid_numerical_comparison",
        computed_shadow_screen=computed_shadow_screen,
    )


def persist_reference(output, journal, comparison, elapsed, references):
    index, edge = comparison["index"], comparison["edge"]
    write_json(output / f"reference_{index:02d}_{edge}.json", comparison)
    journal.write(json.dumps(dict(event="complete", index=index, edge=edge, elapsed=elapsed)) + "\n")
    journal.flush()
    # Only durable file + completion journal can advance the completed count.
    references.append(comparison)
    return len(references)


def check_trace(archive, maps):
    trace, original = archive["trace"], archive["gains"]
    require(
        trace.shape == (2000, 4774) and trace.dtype.kind in "iu" and np.isin(trace, (0, 1)).all(),
        "Invalid complete raster",
    )
    require(
        original.shape == (8866,) and original.dtype == np.float32 and np.isfinite(original).all(),
        "Invalid original gains",
    )
    require(
        archive["pulse_times_ms"].size == archive["pulse_dan_indices"].size == 0, "Untaught trace contains US"
    )
    require(
        np.array_equal(trace.sum(0), archive["counts"][maps["sample"]])
        and np.array_equal(trace[:, maps["dan_columns"]].sum(0), archive["dan_counts"]),
        "Raster count mismatch",
    )
    return trace, original


def execute(plan_path, result_directory, output_directory, root=ROOT):
    """Only invoke after root's explicit study and audit dispatch. No resume."""
    start = time.monotonic()
    output = Path(output_directory)
    output.mkdir(exist_ok=False)
    attempts = completed = 0
    failure = None
    rows, references, row_checks = [], [], []
    prior = None

    def alarm(*_):
        raise TimeoutError("Independent audit 1200-second cap")

    def guard():
        if time.monotonic() - start >= WALL_CAP - 10:
            raise TimeoutError("Independent audit terminal reserve")

    prior = signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, WALL_CAP - (time.monotonic() - start)))
    try:
        plan = read_json(plan_path)
        identity = plan["identity"]
        require(
            identity["analysis"] == "weight-state-shadow-v1"
            and identity["wall_cap_seconds"] == WALL_CAP
            and identity["helper_evaluations"] == 32
            and identity["independent_audit_evaluations"] == 128
            and identity["independent_audit_wall_cap_seconds"] == WALL_CAP
            and identity["gain_allowance"] == GAIN_ATOL
            and identity["weighted_area_allowance"] == AREA_ATOL
            and identity["circuit_calls"] == identity["network_requests"] == 0,
            "Fixed study contract changed",
        )
        verify_bindings(identity["bindings"], root, guard)
        bound_paths = {v["path"] for v in identity["bindings"]}
        needed = {str(MAP), str(CAPTURE / "summary.json"), str(CAPTURE / "capture-receipt.json")}
        needed |= {str(CAPTURE / f"fine_{i:02d}.npz") for i in range(32)}
        needed |= {
            str(Path(__file__).relative_to(root)),
            str(Path(__file__).with_name("test_audit_weight_state_shadow.py").relative_to(root)),
        }
        needed |= {
            str(Path(__file__).with_name(n).relative_to(root))
            for n in ("weight_state_reference.py", "weight_state_guard_reference.py")
        }
        require(needed <= bound_paths, "Missing frozen audit/reference/input bindings")
        directory = Path(result_directory)
        summary = check_terminal(directory, plan, root)
        before = [binding(p, root) for p in sorted(directory.iterdir())]
        frozen_plan = binding(Path(plan_path), root)
        write_json(
            output / "audit-inputs.json",
            dict(plan=frozen_plan, artifacts=before, source_bindings=identity["bindings"]),
        )
        with np.load(root / MAP, allow_pickle=False) as ar:
            maps = {k: ar[k] for k in ar.files}
        selectors = check_maps(maps)
        edges = select_edges(maps["plastic_groups"])
        require(edges == identity["independent_audit_edges"], "Predetermined reference edges changed")
        check_rows(identity["rows"])
        capture = read_json(root / CAPTURE / "summary.json")
        require(capture["status"] == "complete" and len(capture["rows"]) == 32, "Capture incomplete")
        capture_rows = [
            dict(panel=i // 16, **{k: r[k] for k in ("run_id", "game", "seed_set", "seed")})
            for i, r in enumerate(capture["rows"])
        ]
        require(capture_rows == identity["rows"], "Capture identity mismatch")
        with (output / "reference-attempts.jsonl").open("x") as journal:
            for index, meta in enumerate(identity["rows"]):
                guard()
                fine_path = root / CAPTURE / f"fine_{index:02d}.npz"
                require(
                    capture["saved"][index + 1]["file"] == fine_path.name
                    and capture["saved"][index + 1]["sha256"] == sha(fine_path),
                    "Capture receipt order/hash mismatch",
                )
                with np.load(fine_path, allow_pickle=False) as ar:
                    trace, original = check_trace(ar, maps)
                with np.load(directory / f"shadow_{index:02d}.npz", allow_pickle=False) as ar:
                    a = {k: ar[k] for k in ar.files}
                require(a["original_gains"].tobytes() == original.tobytes(), "Original gains changed")
                check = check_arrays(a, maps["plastic_mask"], maps["plastic_groups"])
                detail = read_json(directory / f"row_{index:02d}.json")
                require(
                    type(detail["index"]) is int
                    and detail["index"] == index
                    and all(type(detail.get(k)) is type(v) and detail.get(k) == v for k, v in meta.items()),
                    "Row-detail identity mismatch",
                )
                require(
                    tuple(detail["fields"]) == FIELDS
                    and all(
                        type(detail[k]) is int and detail[k] == v
                        for k, v in check.items()
                        if k != "publications"
                    ),
                    "Row-detail counter mismatch",
                )
                require(
                    np.array_equal(
                        detail["max_estimated_integration_error"],
                        a["estimated_integration_error"].max(axis=1),
                    ),
                    "Diagnostic error summary mismatch",
                )
                require(
                    type(detail["accepted_substeps"]) is int
                    and type(detail["attempted_substeps"]) is int
                    and 1501 <= detail["accepted_substeps"] <= detail["attempted_substeps"]
                    and bounded_clock(detail["elapsed_seconds"]),
                    "Invalid row diagnostic domain",
                )
                for name, gains in (
                    ("published_totals", a["gains"]),
                    ("original_published_totals", original),
                ):
                    require(
                        detail[name] == [float((gains[s].astype(float) - 1).sum()) for s in selectors],
                        "Published total mismatch",
                    )
                rows.append(dict(**meta, gains=a["gains"], double_gains=a["double_gains"]))
                row_checks.append(dict(index=index, **check))
                for edge in edges:
                    guard()
                    journal.write(
                        json.dumps(
                            dict(event="attempt", index=index, edge=edge, elapsed=time.monotonic() - start)
                        )
                        + "\n"
                    )
                    journal.flush()
                    attempts += 1
                    k, d, w = edge_events(trace, maps, edge)
                    ref = event_reference(k, d, end_ms=300.0, dan_weights=w)
                    guard()
                    comparison = dict(
                        index=index,
                        edge=edge,
                        group=int(maps["plastic_groups"][edge]),
                        kc_events=len(k),
                        dan_events=len(d),
                        **compare_reference(a, edge, ref),
                    )
                    completed = persist_reference(
                        output, journal, comparison, time.monotonic() - start, references
                    )
                print(
                    json.dumps(
                        dict(row=index, references=completed, elapsed_seconds=time.monotonic() - start)
                    ),
                    flush=True,
                )
        guards = recompute_guards(rows, selectors)
        require(normalized(guards) == summary["guards"], "Exact eight-cell guard accounting mismatch")
        contacts = sum(r["conditional_bound_contacts"] for r in row_checks)
        require(
            contacts == summary["conditional_possible_bound_contacts"]
            and screen_verdict(guards, contacts) == summary["screen"],
            "Screen decision mismatch",
        )
        require(attempts == completed == 128 and len(rows) == 32, "Incomplete independent comparison matrix")
        verify_bindings(identity["bindings"], root, guard)
        verify_bindings(before + [frozen_plan], root, guard)
        check_terminal(directory, plan, root)
        guard()
        audit_result = dict(
            run_id=plan["run_id"],
            **audit_verdict(references, summary["screen"]),
            attempted=attempts,
            completed=completed,
            rows=32,
            scalar_checks=1024,
            guards=guards,
            maximum_absolute_errors={
                k: max(r["absolute_errors"][k] for r in references) for k in references[0]["absolute_errors"]
            },
            row_checks=row_checks,
            reference_files=[f"reference_{r['index']:02d}_{r['edge']}.json" for r in references],
            gain_allowance=GAIN_ATOL,
            weighted_area_allowance=AREA_ATOL,
            limitations=[
                "Conditional numerical allowance, not a formal interval proof",
                "128 fixed edges independently integrated; all edges checked structurally and arithmetically",
                "Saved phase endpoints/counters do not reconstruct every intermediate bound or rounding event",
                "Fixed histories have no candidate gain feedback; this is not circuit or biological qualification",
            ],
        )
    except (Exception, KeyboardInterrupt) as exc:
        failure = f"{type(exc).__name__}: {exc}"
        audit_result = dict(
            status="budget_stopped" if isinstance(exc, TimeoutError) else "invalid_or_incomplete",
            attempted=attempts,
            completed=completed,
            error=failure,
        )
    try:
        audit_result.update(
            elapsed_seconds=time.monotonic() - start,
            circuit_calls=0,
            native_calls=0,
            network_requests=0,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        write_json(output / "summary.json", audit_result)
        require(time.monotonic() - start < WALL_CAP, "Cap exceeded during audit summary persistence")
        write_json(
            output / "completion.json",
            dict(
                status="complete" if failure is None else "failed",
                summary_sha256=sha(output / "summary.json"),
                elapsed_through_summary_seconds=time.monotonic() - start,
                attempted=attempts,
                completed=completed,
            ),
        )
        require(time.monotonic() - start < WALL_CAP, "Cap exceeded during audit completion persistence")
    except (Exception, KeyboardInterrupt) as exc:
        failure = f"{type(exc).__name__}: {exc}"
        write_json(
            output / "terminal-error.json", dict(error=failure, elapsed_seconds=time.monotonic() - start)
        )
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, prior)
    return 0 if failure is None and audit_result["status"] == "pass" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(execute(args.plan, args.result, args.output))
