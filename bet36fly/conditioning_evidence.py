"""Recompute conditioning verdicts from compact evidence and selected complete replays.

Responses derive from retained integer cue-window counts. Other raw traces were
fingerprinted and reduced by the separately tested runner; only the selected
original/replay results retain every raw numerical array. Native group bound
observations do not reconstruct individual transient synapse trajectories.
"""

from __future__ import annotations

from pathlib import Path

from . import conditioning as c
from .conditioning_artifacts import (
    binding,
    canonical,
    decode_result,
    digest,
    read_artifact,
    safe_npz,
    strict_json,
    verify_bindings,
)
from .conditioning_runner import (
    EvidenceState,
    STAGES,
    compact_result,
    numeric_schema,
    prepare_inputs,
    qualify,
    schedules,
    validate_call_result,
    validate_compact,
)
from .experiments import IDENTIFIER


NOTE = (
    "Responses and KC specificity are recomputed from retained integer cue-window counts. "
    "All numerical fields are fingerprinted; selected original/replay calls retain complete arrays. "
    "Bounds combine final per-edge bytes with separately tested native electrical/tail group observations, "
    "not reconstructed per-edge transient trajectories."
)


def _read_json(path, limit=64 * 1024 * 1024):
    path = Path(path)
    if path != path.resolve() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError("Missing, symlinked or oversized conditioning JSON.")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Oversized conditioning JSON.")
    return strict_json(data), dict(path=str(path), bytes=len(data), sha256=digest(data))


def validate_conditioning(root, experiment_id):
    """No engine calls. Stored booleans and generic registry completion never qualify."""
    result = dict(
        validation_status="invalid",
        evidence_status="unverified",
        all_passed=None,
        validated_calls=0,
        stages={},
        note=NOTE,
        error=None,
    )
    try:
        if not isinstance(experiment_id, str) or not IDENTIFIER.fullmatch(experiment_id):
            raise ValueError("Invalid conditioning identifier.")
        root = Path(root).resolve()
        directory = root / "output/experiments" / experiment_id
        if directory != directory.resolve():
            raise ValueError("Symlinked conditioning directory.")
        if not (directory / "identity.json").exists():
            return dict(
                result,
                validation_status="stored-only",
                error="No conditioning artifact contract is available.",
            )
        consumed = {}

        def consume(meta):
            data = read_artifact(directory, meta)
            old = consumed.setdefault(meta["path"], meta.copy())
            if old != meta:
                raise ValueError("Conflicting artifact identity for one path.")
            return data

        ledger, ledger_binding = _read_json(directory / "ledger.json")
        attempts, journal_binding = read_attempt_journal(directory / "attempts.jsonl")
        if ledger["status"] != "running" and canonical(attempts) != canonical(ledger["attempts"]):
            raise ValueError("Final ledger disagrees with durable invocation journal.")
        ledger["attempts"] = attempts
        identity = strict_json(consume(ledger["identity"]))
        if experiment_id != "conditioning-" + digest(canonical(identity))[:24]:
            raise ValueError("Conditioning identity digest differs.")
        if identity["schema"] != "conditioning-v1" or canonical(identity["spec"]) != canonical(
            c.conditioning_spec()
        ):
            raise ValueError("Frozen conditioning specification differs.")
        plan = c.build_call_plan()
        if canonical(identity["plan"]) != canonical([r.json() for r in plan]):
            raise ValueError("Ordered conditioning plan differs.")
        # Resolve the approved paths from the current independently verified pair.
        # Never read artifact-supplied arbitrary absolute source bindings.
        gate = qualify(root, identity["qualification"]["pair"]["pair_id"])
        if canonical(gate) != canonical(identity["qualification"]):
            raise ValueError("Qualification/source binding changed.")
        inputs = prepare_inputs(root, gate["scientific_identity"]["protocol"])
        arrays = safe_npz(consume(ledger["inputs"]))
        actual = dict(
            neurons=inputs["neurons"],
            learning_rule=inputs["learning_rule"],
            arrays={k: c.array_identity(v) for k, v in arrays.items()},
        )
        expected = dict(
            neurons=inputs["neurons"],
            learning_rule=inputs["learning_rule"],
            arrays={k: c.array_identity(v) for k, v in inputs["arrays"].items()},
        )
        if actual != expected or actual != identity["inputs"]:
            raise ValueError("Retained anatomy, mask or actual cue encodings differ.")
        inputs["arrays"] = arrays
        state = EvidenceState(inputs)
        state.plan = plan
        state.replay_ids = {r.replay_of for r in plan if r.replay_of}
        attempts = ledger["attempts"]
        if not isinstance(attempts, list) or len(attempts) > 1632:
            raise ValueError("Malformed or extra attempt matrix.")
        current = STAGES[0]
        partial = False
        for position, attempt in enumerate(attempts):
            row = plan[position]
            if (
                type(attempt["position"]) is not int
                or attempt["position"] != position
                or canonical(attempt["call"]) != canonical(row.json())
                or type(attempt["invoked"]) is not bool
            ):
                raise ValueError("Attempt order or typed call identity differs.")
            if attempt["status"] != "completed":
                if position != len(attempts) - 1 or ledger["status"] == "completed":
                    raise ValueError("Incomplete call occurs inside claimed complete evidence.")
                partial = True
                break
            if attempt["invoked"] is not True or attempt.get("returned") is not True:
                raise ValueError("Completed call lacks invocation/return evidence.")
            if row.stage != current:
                state.score(current)
                current = row.stage
            if (
                row.stage != "reversal"
                and row.kind == "train-cue"
                and row.panel == 0
                and row.arm == "paired"
                and row.exposure == 0
                and not row.replay_of
            ):
                state.unit_gate(row.stage)
            if position == 1258:
                state.parent_gate()
            before_archive = safe_npz(consume(attempt["before"]))
            if set(before_archive) != {"gains"}:
                raise ValueError("Before checkpoint schema differs.")
            before = before_archive["gains"]
            expected_before = state.before(row)
            if (
                c.array_identity(before) != c.array_identity(expected_before)
                or c.array_identity(before)["sha256"] != attempt["before_sha256"]
            ):
                raise ValueError("Canonical/probe/replay checkpoint ancestry differs.")
            rates, _ = schedules(row, inputs)
            if c.array_identity(rates)["sha256"] != attempt["rate_sha256"]:
                raise ValueError("Actual scheduled rates differ.")
            compact = decode_result(
                consume(attempt["compact"]),
                consume(attempt["compact_metadata"]),
            )
            validate_compact(row, inputs, before, compact)
            schema = numeric_schema(row, inputs)
            c.validate_fingerprints(attempt["fingerprints"], schema)
            for key in (
                "gains",
                "gain_delta",
                "dan_counts",
                "compartment_dan_counts",
                "compartment_tonic_hz",
                "pulse_times_ms",
                "pulse_dan_indices",
                "population",
            ):
                if c.array_identity(compact[key]) != attempt["fingerprints"][key]:
                    raise ValueError("Compact bytes disagree with complete numerical fingerprints.")
            if row.id in state.replay_ids or row.replay_of:
                raw = decode_result(consume(attempt["result"]), consume(attempt["metadata"]))
                validate_call_result(row, inputs, before, raw)
                if c._numeric_identities(raw) != attempt["fingerprints"]:
                    raise ValueError("Selected complete arrays disagree with fingerprints.")
                regenerated = compact_result(row, inputs, raw)
                if any(c.array_identity(v) != c.array_identity(compact[k]) for k, v in regenerated.items()):
                    raise ValueError("Selected raw-to-compact reduction differs.")
                if row.replay_of:
                    original_meta = state.originals[row.replay_of]["artifact"]
                    original = decode_result(
                        consume(original_meta["result"]),
                        consume(original_meta["metadata"]),
                    )
                    if not c.compare_numeric_results(original, raw, schema=schema)["passed"]:
                        raise ValueError("Selected full numerical replay differs.")
            state.accept(row, before, compact, attempt)
            result["validated_calls"] += 1
        if not partial:
            try:
                if len(attempts) in (8, 624):
                    state.unit_gate(current)
                if len(attempts) == 1258:
                    state.parent_gate()
                if len(attempts) in (616, 1232, 1632):
                    state.score(current)
            except ValueError as exc:
                state.verdicts.setdefault(
                    current, dict(all_passed=False, errors=[str(exc)], entry_gate_failed=True)
                )
        result["stages"] = state.verdicts
        complete = len(attempts) == 1632 and not partial and set(state.verdicts) == set(STAGES)
        criteria_passed = complete and all(v["all_passed"] for v in state.verdicts.values())
        wall = ledger["wall_seconds"]
        if type(wall) not in (int, float) or wall < 0:
            raise ValueError("Invalid wall accounting.")
        if ledger["status"] not in (
            "completed",
            "running",
            "failed",
            "cancelled",
            "budget_stopped",
            "gate_failed",
        ):
            raise ValueError("Unknown terminal execution disposition.")
        passed = criteria_passed and ledger["status"] == "completed" and wall < 1200
        if ledger["status"] == "completed" and (not criteria_passed or wall >= 1200):
            raise ValueError("Claimed completion lacks all criteria or violates fixed cap.")
        for meta in consumed.values():
            path = directory / meta["path"]
            if path.stat().st_size != meta["bytes"] or binding(path)["sha256"] != meta["sha256"]:
                raise ValueError("Consumed conditioning artifact changed during validation.")
        verify_bindings(gate["bindings"])
        if journal_binding != binding(directory / "attempts.jsonl") or ledger_binding != binding(
            directory / "ledger.json"
        ):
            raise ValueError("Conditioning ledger changed during validation.")
        return dict(
            result,
            validation_status="validated",
            evidence_status="passed"
            if passed
            else "failed"
            if ledger["status"] == "gate_failed" and any(not v["all_passed"] for v in state.verdicts.values())
            else "incomplete",
            all_passed=True
            if passed
            else False
            if ledger["status"] == "gate_failed" and state.verdicts
            else None,
        )
    except (ValueError, TypeError, KeyError, IndexError, OSError, OverflowError) as exc:
        return dict(result, error=str(exc))


def present_conditioning(root, manifest):
    """Sanitize stored registry metadata independently of scientific validation."""
    if manifest.get("kind") != "dopamine-conditioning":
        return manifest
    import math

    def text(value):
        return value if isinstance(value, str) else None

    def number(value):
        return value if type(value) in (int, float) and math.isfinite(value) else None

    def mapping(value):
        return value if isinstance(value, dict) else {}

    def strings(value):
        return [x for x in value if isinstance(x, str)] if isinstance(value, list) else []

    out = {
        key: text(manifest.get(key)) for key in ("id", "kind", "status", "error", "created_at", "updated_at")
    }
    out["id"] = out["id"] or "invalid-conditioning"
    stored = mapping(manifest.get("conditioning"))
    record = {}
    for key in (
        "configured_rule",
        "verified_rule",
        "configured_mask",
        "verified_mask",
        "protocol_sha256",
        "addendum_sha256",
        "status_reason",
    ):
        record[key] = text(stored.get(key))
    for key in ("wall_seconds", "wall_cap_seconds"):
        record[key] = number(stored.get(key))
    record["calls"] = {
        key: number(mapping(stored.get("calls")).get(key))
        for key in ("planned", "actual", "cap", "returned", "completed", "ambiguous")
    }
    record["prerequisite_run_ids"] = strings(stored.get("prerequisite_run_ids"))
    record["stages"] = []
    for item in stored.get("stages", []) if isinstance(stored.get("stages"), list) else []:
        item = mapping(item)
        stage = {
            key: text(item.get(key))
            for key in (
                "id",
                "status",
                "status_reason",
                "checkpoint_sha256",
                "parent_checkpoint_sha256",
                "classification",
            )
        }
        if not stage["id"]:
            continue
        stage["missing_criteria"] = strings(item.get("missing_criteria"))
        stage["criteria"] = {}
        for key, value in mapping(item.get("criteria")).items():
            value = mapping(value)
            stage["criteria"][key] = dict(
                passed=value.get("passed") if type(value.get("passed")) is bool else None,
                value=number(value.get("value")),
                limit=number(value.get("limit")),
            )
        record["stages"].append(stage)
    out["conditioning"] = record
    out["jobs"] = []
    out["artifacts"] = {}
    for job in manifest.get("jobs", []) if isinstance(manifest.get("jobs"), list) else []:
        job = mapping(job)
        if not text(job.get("id")):
            continue
        clean = {
            key: text(job.get(key))
            for key in ("id", "status", "phase", "variant", "error", "cancellation_reason")
        }
        clean.update(
            {
                key: number(job.get(key))
                for key in (
                    "completed",
                    "total",
                    "seed",
                    "gain_parameters",
                    "decoder_parameters",
                    "active_parameters",
                )
            }
        )
        out["jobs"].append(clean)
    for key, artifact in mapping(manifest.get("artifacts")).items():
        artifact = mapping(artifact)
        if text(artifact.get("url")) and text(artifact.get("label")):
            out["artifacts"][key] = {k: text(artifact.get(k)) for k in ("url", "label", "sha256", "job_id")}
    out["conditioning_validation"] = validate_conditioning(root, out["id"])
    return out


def read_attempt_journal(path):
    path = Path(path)
    limit = 64 * 1024 * 1024
    if path != path.resolve() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError("Missing/symlinked/oversized durable journal.")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Oversized journal.")
    attempts = []
    for line in data.splitlines():
        event = strict_json(line)
        if not isinstance(event, dict) or type(event.get("position")) is not int:
            raise ValueError("Malformed durable attempt.")
        pos = event["position"]
        if pos == len(attempts):
            if attempts and attempts[-1]["status"] != "completed":
                raise ValueError("Invocation follows an incomplete call.")
            if event["status"] != "prepared" or event["invoked"] is not False:
                raise ValueError("Missing durable pre-call intent.")
            attempts.append(event)
        elif pos == len(attempts) - 1:
            old = attempts[-1]
            if old["status"] in ("completed", "failed"):
                raise ValueError("Terminal attempt was rewritten.")
            for key in ("position", "call", "before", "before_sha256", "rate_sha256"):
                if canonical(old[key]) != canonical(event[key]):
                    raise ValueError("Durable call identity changed.")
            if old["invoked"] and not event["invoked"]:
                raise ValueError("Invocation accounting decreased.")
            if event["status"] not in ("prepared", "intent", "completed", "failed"):
                raise ValueError("Unknown attempt state.")
            attempts[-1] = event
        else:
            raise ValueError("Durable attempt order was changed.")
    return attempts, dict(path=str(path), bytes=len(data), sha256=digest(data))
