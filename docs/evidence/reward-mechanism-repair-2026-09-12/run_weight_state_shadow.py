"""Freeze/execute one output-only 32-history weight-state rejection screen."""

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import signal
import time

import numpy as np

from weight_dependent_shadow import shadow
from weight_state_guard_reference import allowance_totals, classify_box, f32_trial_totals, point_guard

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent
EVIDENCE = ROOT / "docs/evidence/reward-mechanism-repair-2026-09-12"
CAP = (
    ROOT
    / "output/collaboration/reward-mechanism-repair/onset-history-captures/onset-history-capture-4343c21535c43f42"
)
PLAN = HERE / "weight-state-shadow-frozen-2026-09-13.json"
WALL_CAP = 1200
GAIN_ALLOWANCE = 1e-11
AREA_ALLOWANCE = 2e-11


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def binding(path, root=ROOT):
    path = Path(path)
    return dict(path=str(path.relative_to(root)), bytes=path.stat().st_size, sha256=sha(path))


def verify_bindings(bindings, root=ROOT, guard=lambda: None):
    seen = set()
    for item in bindings:
        guard()
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts or str(relative) in seen:
            raise ValueError("Escaping or duplicate bound source path")
        seen.add(str(relative))
        path = root / relative
        if any((root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
            raise ValueError("Bound source cannot be a symbolic link")
        if path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            raise ValueError(f"Frozen source changed: {relative}")
        guard()


def json_value(value):
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def write_json(path, value):
    # Serialize before exclusive creation, so invalid numerical values leave no success file.
    encoded = json.dumps(value, indent=2, allow_nan=False, default=json_value) + "\n"
    with Path(path).open("x") as stream:
        stream.write(encoded)


def study_id(identity):
    return (
        "weight-state-shadow-"
        + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:20]
    )


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


def audit_edges(maps):
    return [
        int(
            np.flatnonzero(maps["plastic_groups"] == group)[
                np.count_nonzero(maps["plastic_groups"] == group) // 2
            ]
        )
        for group in (0, 1, 2, 4)
    ]


def guard_summary(rows, selectors):
    if len(rows) != 32 or len(selectors) != 2:
        raise ValueError("Complete two-panel, two-noise, two-channel matrix required")
    validate_rows(rows)
    result = {}
    for panel in (0, 1):
        for noise in ("base", "alt"):
            subset = [r for r in rows if r["panel"] == panel and r["seed_set"] == noise]
            if len(subset) != 8:
                raise ValueError("Exactly eight trials in each fixed panel/noise cell required")
            for channel, selector in zip(("home", "away"), selectors):
                published = np.stack([r["gains"][selector] for r in subset])
                centers = np.stack([r["double_gains"][selector] for r in subset])
                ticks = f32_trial_totals(published)
                lower, upper = allowance_totals(centers, GAIN_ALLOWANCE)
                values = np.array(ticks, dtype=float) / 2**24
                result[f"{panel}/{noise}/{channel}"] = dict(
                    ticks=ticks,
                    lower_ticks=lower,
                    upper_ticks=upper,
                    point_pass=point_guard(ticks),
                    mean=float(values.mean()),
                    sample_sd=float(values.std(ddof=1)),
                    limit=float(0.5 * values.std(ddof=1)),
                    conditional=classify_box(lower, upper),
                )
    return result


def prepare():
    capture = json.loads((CAP / "summary.json").read_text())
    if capture["status"] != "complete" or len(capture["rows"]) != 32:
        raise ValueError("Complete preserved original capture required")
    with np.load(EVIDENCE / "onset-capture-preregistration.samples.npz", allow_pickle=False) as archive:
        maps = {key: archive[key] for key in archive.files}
    validate_maps(maps)
    names = [
        "run_weight_state_shadow.py",
        "test_run_weight_state_shadow.py",
        "weight_dependent_shadow.py",
        "test_weight_dependent_shadow.py",
        "weight_state_reference.py",
        "test_weight_state_reference.py",
        "weight_state_guard_reference.py",
        "test_weight_state_guard_reference.py",
        "test_weight_state_helper_independent.py",
        "test_weight_state_independent_review.py",
        "weight-state-shadow-preregistration-2026-09-13.md",
        "weight-state-reference-contract-2026-09-13.md",
        "weight-state-exact-guard-contract-2026-09-13.md",
        "weight-dependent-helper-preparation-2026-09-13.md",
        "weight-state-shadow-prerun-review-2026-09-13.json",
        "weight-state-helper-independent-review-final-2026-09-13.json",
        "weight-state-exact-guard-reading-and-freeze-receipt-2026-09-13.json",
        "weight-dependent-helper-reading-and-freeze-receipt-2026-09-13.json",
        "weight-state-evidence-ui-pure-review-2026-09-13.json",
        "audit_weight_state_shadow.py",
        "test_audit_weight_state_shadow.py",
    ]
    paths = [HERE / name for name in names]
    paths += [
        EVIDENCE / name
        for name in (
            "dopamine-weight-state-decision-2026-09-13.md",
            "onset-capture-preregistration.json",
            "onset-capture-preregistration.samples.npz",
        )
    ]
    paths += [CAP / name for name in ("summary.json", "capture-receipt.json")]
    paths += [CAP / f"fine_{i:02d}.npz" for i in range(32)]
    paths += [ROOT / "bet36fly/reward_lif.cpp", ROOT / "docs/connectome-source-lock.json"]
    bindings = [binding(path) for path in paths]
    rows = [
        dict(panel=i // 16, **{k: row[k] for k in ("run_id", "game", "seed_set", "seed")})
        for i, row in enumerate(capture["rows"])
    ]
    validate_rows(rows)
    identity = dict(
        analysis="weight-state-shadow-v1",
        bindings=bindings,
        rows=rows,
        wall_cap_seconds=WALL_CAP,
        helper_evaluations=32,
        circuit_calls=0,
        network_requests=0,
        gain_allowance=GAIN_ALLOWANCE,
        weighted_area_allowance=AREA_ALLOWANCE,
        independent_audit_edges=audit_edges(maps),
        independent_audit_evaluations=128,
        independent_audit_wall_cap_seconds=1200,
    )
    plan = dict(
        identity=identity, run_id=study_id(identity), prepared_at=datetime.now(timezone.utc).isoformat()
    )
    verify_bindings(bindings)
    write_json(PLAN, plan)
    print(
        json.dumps(
            dict(
                run_id=plan["run_id"],
                source_files=len(bindings),
                audit_edges=identity["independent_audit_edges"],
            )
        )
    )


def execute():
    started = time.monotonic()
    plan = json.loads(PLAN.read_text())
    identity, sid = plan["identity"], plan["run_id"]
    if (
        study_id(identity) != sid
        or identity["wall_cap_seconds"] != WALL_CAP
        or identity["helper_evaluations"] != 32
    ):
        raise ValueError("Frozen identity/cap mismatch")
    validate_rows(identity["rows"])
    output = HERE / sid
    output.mkdir(exist_ok=False)
    write_json(output / "identity.json", plan)
    rows, attempted, saved = [], 0, []

    def deadline(*_):
        raise TimeoutError("Fixed 1200-second shadow cap reached")

    def guard():
        if time.monotonic() - started >= WALL_CAP - 10:
            raise TimeoutError("Stopped with ten-second terminal-record reserve")

    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, WALL_CAP - (time.monotonic() - started)))
    status, error = "incomplete", None
    try:
        verify_bindings(identity["bindings"], guard=guard)
        with np.load(EVIDENCE / "onset-capture-preregistration.samples.npz", allow_pickle=False) as archive:
            maps = {key: archive[key] for key in archive.files}
        selectors = validate_maps(maps)
        capture = json.loads((CAP / "summary.json").read_text())
        capture_rows = [
            dict(panel=i // 16, **{key: row[key] for key in ("run_id", "game", "seed_set", "seed")})
            for i, row in enumerate(capture["rows"])
        ]
        validate_rows(capture_rows)
        if capture_rows != identity["rows"]:
            raise ValueError("Identity does not describe the original capture selectors")
        with (output / "attempts.jsonl").open("x") as journal:
            for i, meta in enumerate(identity["rows"]):
                guard()
                path = CAP / f"fine_{i:02d}.npz"
                stored = capture["saved"][i + 1]
                if stored["file"] != path.name or stored["sha256"] != sha(path):
                    raise ValueError("Capture receipt order or hash mismatch")
                with np.load(path, allow_pickle=False) as archive:
                    trace, original = archive["trace"], archive["gains"]
                    if (
                        trace.shape != (2000, 4774)
                        or trace.dtype.kind not in "iu"
                        or not np.isin(trace, (0, 1)).all()
                    ):
                        raise ValueError("Invalid complete captured raster")
                    if (
                        original.shape != (8866,)
                        or original.dtype != np.dtype(np.float32)
                        or not np.isfinite(original).all()
                    ):
                        raise ValueError("Invalid original comparison gains")
                    if len(archive["pulse_times_ms"]) or len(archive["pulse_dan_indices"]):
                        raise ValueError("Untaught histories cannot contain imposed teaching")
                    np.testing.assert_array_equal(trace.sum(0), archive["counts"][maps["sample"]])
                    np.testing.assert_array_equal(trace[:, maps["dan_columns"]].sum(0), archive["dan_counts"])
                journal.write(
                    json.dumps(
                        dict(event="attempt", index=i, source=path.name, elapsed=time.monotonic() - started)
                    )
                    + "\n"
                )
                journal.flush()
                attempted += 1
                value = shadow(
                    trace[:, maps["kc_columns"]],
                    trace[:, maps["dan_columns"]],
                    maps["plastic_kc_indices"],
                    maps["plastic_compartments"],
                    maps["dan_compartments"],
                    maps["plastic_mask"],
                    maps["plastic_groups"],
                    guard=guard,
                )
                guard()
                active = maps["plastic_mask"].astype(bool)
                np.testing.assert_array_equal(value["publication_counts"], active.astype(np.int64) * 1501)
                np.testing.assert_array_equal(
                    value["gains"][~active], np.ones(np.count_nonzero(~active), np.float32)
                )
                if np.any(value["phases"][:, ~active]) or np.any(
                    value["conditional_bound_counts"][:, ~active]
                ):
                    raise ValueError("Excluded-edge accounting changed")
                if (
                    not np.isfinite(value["double_gains"]).all()
                    or np.any(value["double_gains"] < 0.5)
                    or np.any(value["double_gains"] > 1.5)
                ):
                    raise ValueError("Computed gain left the continuous law's bounds")
                np.testing.assert_allclose(
                    value["phases"][:, :, 3].sum(0), value["double_gains"] - 1, atol=GAIN_ALLOWANCE, rtol=0
                )
                np.testing.assert_allclose(
                    value["phases"][:, :, :2].sum((0, 2)),
                    value["double_gains"] - 1,
                    atol=2 * AREA_ALLOWANCE,
                    rtol=0,
                )
                np.testing.assert_array_equal(
                    value["phases"][:, :, 4].sum(0), value["gains"].astype(float) - 1
                )
                arrays = {key: item for key, item in value.items() if isinstance(item, np.ndarray)}
                arrays["original_gains"] = original
                target = output / f"shadow_{i:02d}.npz"
                with target.open("xb") as stream:
                    np.savez_compressed(stream, **arrays)
                saved.append(binding(target))
                row = dict(**meta, gains=value["gains"], double_gains=value["double_gains"])
                details = dict(
                    **meta,
                    index=i,
                    fields=value["fields"],
                    actual_bound_contacts=int(value["phases"][:, :, 5:7].sum()),
                    conditional_bound_contacts=int(value["conditional_bound_counts"].sum()),
                    rounding_ambiguous_publications=int(value["rounding_ambiguous"].sum()),
                    max_estimated_integration_error=value["estimated_integration_error"].max(axis=1).tolist(),
                    accepted_substeps=value["accepted_substeps"],
                    attempted_substeps=value["attempted_substeps"],
                    original_published_totals=[
                        float((original[s].astype(float) - 1).sum()) for s in selectors
                    ],
                    published_totals=[float((value["gains"][s].astype(float) - 1).sum()) for s in selectors],
                    elapsed_seconds=time.monotonic() - started,
                )
                write_json(output / f"row_{i:02d}.json", details)
                journal.write(
                    json.dumps(
                        dict(
                            event="complete", index=i, artifact=saved[-1], elapsed=time.monotonic() - started
                        )
                    )
                    + "\n"
                )
                journal.flush()
                rows.append(row)
                print(
                    json.dumps(dict(index=i, completed=len(rows), published=details["published_totals"])),
                    flush=True,
                )
        guards = guard_summary(rows, selectors)
        verify_bindings(identity["bindings"], guard=guard)
        guard()
        details = [json.loads((output / f"row_{i:02d}.json").read_text()) for i in range(32)]
        contacts = sum(r["conditional_bound_contacts"] for r in details)
        states = [r["conditional"]["classification"] for r in guards.values()]
        screen = (
            "reject"
            if "all_fail" in states or contacts
            else ("permits_circuit_consideration" if set(states) == {"all_pass"} else "inconclusive")
        )
        status = "complete"
        result = dict(
            guards=guards,
            conditional_possible_bound_contacts=contacts,
            screen=screen,
            numerical_audit="pending independent 128-edge reference and complete artifact audit",
            qualification="not qualified; only frozen untaught histories evaluated",
        )
    except (Exception, KeyboardInterrupt) as exc:
        status = "budget_stopped" if isinstance(exc, TimeoutError) else "failed"
        error = f"{type(exc).__name__}: {exc}"
        result = dict(screen="invalid_or_incomplete", qualification="not qualified")
    elapsed = time.monotonic() - started
    if elapsed >= WALL_CAP:
        status, error = "budget_stopped", error or "Whole-study cap exceeded"
        result["screen"] = "invalid_or_incomplete"
    summary = dict(
        run_id=sid,
        status="computed" if status == "complete" else status,
        error=error,
        attempted=attempted,
        completed=len(rows),
        saved=saved,
        elapsed_seconds=elapsed,
        circuit_calls=0,
        native_calls=0,
        network_requests=0,
        **result,
    )
    try:
        write_json(output / "summary.json", summary)
        if time.monotonic() - started >= WALL_CAP:
            raise TimeoutError("Cap crossed during summary persistence")
        completion = dict(
            run_id=sid,
            status=status,
            summary_sha256=sha(output / "summary.json"),
            elapsed_through_summary_seconds=time.monotonic() - started,
            attempted=attempted,
            completed=len(rows),
        )
        write_json(output / "completion.json", completion)
        if time.monotonic() - started >= WALL_CAP:
            raise TimeoutError("Cap crossed during completion persistence")
    except (Exception, KeyboardInterrupt) as exc:
        status = "budget_stopped" if isinstance(exc, TimeoutError) else "failed"
        # A terminal error invalidates any previously written completion receipt.
        result["screen"] = "invalid_or_incomplete"
        write_json(
            output / "terminal-error.json",
            dict(
                run_id=sid,
                status=status,
                error=f"{type(exc).__name__}: {exc}",
                elapsed_seconds=time.monotonic() - started,
            ),
        )
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    print(
        json.dumps(
            dict(
                run_id=sid,
                status=status,
                attempted=attempted,
                completed=len(rows),
                elapsed_seconds=time.monotonic() - started,
                screen=result["screen"],
            )
        )
    )
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    else:
        raise SystemExit(execute())
