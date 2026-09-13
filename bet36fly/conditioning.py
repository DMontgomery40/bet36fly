"""Frozen protocol and fail-closed evaluators for full-CNS conditioning.

This is an engineered test around the MaleCNS circuit. It does not claim that
the artificial cues or teaching schedules are natural fly stimuli.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
from itertools import combinations
from fractions import Fraction
from typing import Any

import numpy as np

ACQUISITION_ARMS = ("paired", "shuffled", "timing-unpaired", "untaught", "frozen")
REVERSAL_BRANCHES = (
    "continued-acquisition",
    "ordinary-contingency-swap",
    "backward-erasure-plus-swap",
    "untaught-exposure",
    "frozen-retention",
)
FAMILIES = {"AB": ("A", "B"), "CD": ("C", "D")}
CHANNELS = ("home", "away")
FIRST_LATE = (610, 630, 650, 670)
SECOND_LATE = (690, 710, 730, 750)
EARLY = (110, 130, 150, 170)
ACQUISITION_TEACHING = (310, 330, 350, 370)


@dataclass(frozen=True)
class CallSpec:
    id: str
    stage: str
    kind: str
    family: str
    panel: int | None
    arm: str | None
    branch: str | None
    checkpoint: str
    cue: str | None
    seed: int
    duration_ms: int
    cue_window: tuple[int, int] | None
    plasticity: bool
    teaching: tuple[tuple[int, str], ...] = ()
    exposure: int | None = None
    replay_of: str | None = None

    def json(self) -> dict:
        return asdict(self)


def conditioning_spec() -> dict:
    alternating = [-1.5 if i % 2 == 0 else 1.5 for i in range(16)]
    return {
        "schema_version": 1,
        "kind": "dopamine-conditioning",
        "cues": {
            "A": [-1.5] * 16,
            "B": [1.5] * 16,
            "C": alternating,
            "D": [-x for x in alternating],
        },
        "families": FAMILIES,
        "acquisition_arms": ACQUISITION_ARMS,
        "reversal_branches": REVERSAL_BRANCHES,
        "hard_call_limit": 1640,
        "planned_calls": 1632,
        "hard_wall_seconds": 1200,
        "effect_ratio": 3.0,
        "max_between_jaccard": 0.5,
    }


def _identifier(parts: tuple[Any, ...]) -> str:
    return "-".join("none" if value is None else str(value).replace("_", "-") for value in parts)


def _with_replay(rows: list[CallSpec], original: CallSpec) -> None:
    rows.append(replace(original, id=original.id + "-replay", replay_of=original.id))


def _acquisition_teaching(arm: str, cue_index: int, exposure: int, *, blank: bool) -> tuple:
    if arm == "paired" and not blank:
        population = CHANNELS[cue_index]
    elif arm == "shuffled" and not blank:
        population = ("home", "home", "away", "away")[exposure % 4]
    elif arm == "timing-unpaired" and blank:
        population = CHANNELS[cue_index]
    else:
        return ()
    return tuple((time_ms, population) for time_ms in ACQUISITION_TEACHING)


def _add_acquisition(rows: list[CallSpec], family: str, stage: str) -> None:
    cues = FAMILIES[family]
    for seed in range(2_000_042, 2_000_046):
        for cue in cues:
            rows.append(
                CallSpec(
                    _identifier((stage, "unit", cue, seed)),
                    stage,
                    "unit-probe",
                    family,
                    None,
                    None,
                    None,
                    "unit",
                    cue,
                    seed,
                    400,
                    (0, 300),
                    False,
                )
            )
    for panel in (0, 1_000_000):
        for arm in ACQUISITION_ARMS:
            for exposure in range(24):
                cue = cues[(0, 1, 1, 0)[exposure % 4]]
                cue_index = 0 if cue == cues[0] else 1
                seed = 42 + panel + 2 * exposure
                cue_row = CallSpec(
                    _identifier((stage, panel, arm, exposure, "cue")),
                    stage,
                    "train-cue",
                    family,
                    panel,
                    arm,
                    None,
                    f"after-{exposure}",
                    cue,
                    seed,
                    400,
                    (0, 300),
                    arm != "frozen",
                    _acquisition_teaching(arm, cue_index, exposure, blank=False),
                    exposure,
                )
                blank_row = CallSpec(
                    _identifier((stage, panel, arm, exposure, "blank")),
                    stage,
                    "train-blank",
                    family,
                    panel,
                    arm,
                    None,
                    f"after-{exposure}",
                    None,
                    seed + 1,
                    400,
                    None,
                    arm != "frozen",
                    _acquisition_teaching(arm, cue_index, exposure, blank=True),
                    exposure,
                )
                rows.extend((cue_row, blank_row))
                if arm == "paired" and exposure == 0:
                    _with_replay(rows, cue_row)
                    _with_replay(rows, blank_row)
                if exposure in (7, 15):
                    checkpoint = "block-2" if exposure == 7 else "block-4"
                    for probe_cue in cues:
                        rows.append(
                            CallSpec(
                                _identifier((stage, panel, arm, checkpoint, probe_cue)),
                                stage,
                                "interim-probe",
                                family,
                                panel,
                                arm,
                                None,
                                checkpoint,
                                probe_cue,
                                2_001_042,
                                400,
                                (0, 300),
                                False,
                            )
                        )
            for seed in range(2_000_042, 2_000_046):
                for cue in cues:
                    probe = CallSpec(
                        _identifier((stage, panel, arm, "endpoint", cue, seed)),
                        stage,
                        "endpoint-probe",
                        family,
                        panel,
                        arm,
                        None,
                        "endpoint",
                        cue,
                        seed,
                        400,
                        (0, 300),
                        False,
                    )
                    rows.append(probe)
                    if arm == "paired" and seed == 2_000_042:
                        _with_replay(rows, probe)


def _reversal_teaching(branch: str, cue_index: int) -> tuple:
    old, new = CHANNELS[cue_index], CHANNELS[1 - cue_index]
    if branch == "continued-acquisition":
        return tuple((t, old) for t in FIRST_LATE + SECOND_LATE)
    if branch == "ordinary-contingency-swap":
        return tuple((t, new) for t in FIRST_LATE + SECOND_LATE)
    if branch == "backward-erasure-plus-swap":
        return tuple((t, old) for t in EARLY) + tuple((t, new) for t in FIRST_LATE)
    return ()


def _add_reversal(rows: list[CallSpec]) -> None:
    stage, family, cues = "reversal", "AB", FAMILIES["AB"]
    for seed in range(5_000_042, 5_000_046):
        for cue in cues:
            probe = CallSpec(
                _identifier((stage, "unit", cue, seed)),
                stage,
                "unit-probe",
                family,
                None,
                None,
                None,
                "unit-800ms",
                cue,
                seed,
                800,
                (300, 600),
                False,
            )
            rows.append(probe)
            if seed == 5_000_042:
                _with_replay(rows, probe)
    for panel in (3_000_000, 4_000_000):
        for seed in range(5_000_042, 5_000_046):
            for cue in cues:
                rows.append(
                    CallSpec(
                        _identifier((stage, panel, "parent", cue, seed)),
                        stage,
                        "parent-probe",
                        family,
                        panel,
                        None,
                        None,
                        "acquired-parent",
                        cue,
                        seed,
                        800,
                        (300, 600),
                        False,
                    )
                )
    # Both acquired parents must pass matched-schedule probes before any branch trains.
    for panel in (3_000_000, 4_000_000):
        for branch in REVERSAL_BRANCHES:
            for exposure in range(24):
                cue = cues[(0, 1, 1, 0)[exposure % 4]]
                cue_index = 0 if cue == cues[0] else 1
                trial = CallSpec(
                    _identifier((stage, panel, branch, exposure)),
                    stage,
                    "train-reversal",
                    family,
                    panel,
                    None,
                    branch,
                    f"after-{exposure}",
                    cue,
                    42 + panel + exposure,
                    800,
                    (300, 600),
                    branch != "frozen-retention",
                    _reversal_teaching(branch, cue_index),
                    exposure,
                )
                rows.append(trial)
                if exposure == 0:
                    _with_replay(rows, trial)
                if exposure in (7, 15):
                    checkpoint = "block-2" if exposure == 7 else "block-4"
                    for probe_cue in cues:
                        rows.append(
                            CallSpec(
                                _identifier((stage, panel, branch, checkpoint, probe_cue)),
                                stage,
                                "interim-probe",
                                family,
                                panel,
                                None,
                                branch,
                                checkpoint,
                                probe_cue,
                                5_001_042,
                                800,
                                (300, 600),
                                False,
                            )
                        )
            for seed in range(5_000_042, 5_000_046):
                for cue in cues:
                    probe = CallSpec(
                        _identifier((stage, panel, branch, "endpoint", cue, seed)),
                        stage,
                        "endpoint-probe",
                        family,
                        panel,
                        None,
                        branch,
                        "endpoint",
                        cue,
                        seed,
                        800,
                        (300, 600),
                        False,
                    )
                    rows.append(probe)
                    if branch == "backward-erasure-plus-swap" and seed == 5_000_042:
                        _with_replay(rows, probe)


def build_call_plan(spec: dict | None = None) -> list[CallSpec]:
    spec = conditioning_spec() if spec is None else spec
    if json.dumps(spec, sort_keys=True) != json.dumps(conditioning_spec(), sort_keys=True):
        raise ValueError("Conditioning specification differs from the frozen addendum.")
    rows: list[CallSpec] = []
    _add_acquisition(rows, "AB", "acquisition-primary")
    _add_acquisition(rows, "CD", "acquisition-challenge")
    _add_reversal(rows)
    return rows


def validate_call_plan(plan: list[CallSpec], dan_population_sizes=(2, 22)) -> dict:
    if tuple(dan_population_sizes) != (2, 22):
        raise ValueError("Conditioning requires the frozen two-home/22-away DAN populations.")
    expected = build_call_plan()
    if not isinstance(plan, list) or len(plan) != len(expected):
        raise ValueError("Conditioning call plan is incomplete or contains extra calls.")
    for index, (actual, wanted) in enumerate(zip(plan, expected)):
        if not isinstance(actual, CallSpec) or json.dumps(actual.json(), sort_keys=True) != json.dumps(
            wanted.json(), sort_keys=True
        ):
            raise ValueError(f"Conditioning ordered call contract differs at position {index}.")
    return {
        "calls": len(plan),
        "hard_call_limit": 1640,
        "hard_wall_seconds": 1200,
        "by_stage": {
            stage: sum(r.stage == stage for r in plan)
            for stage in ("acquisition-primary", "acquisition-challenge", "reversal")
        },
        "selected_replays": sum(row.replay_of is not None for row in plan),
    }


def _jaccard(left: np.ndarray, right: np.ndarray) -> float:
    union = left | right
    return float(np.count_nonzero(left & right) / np.count_nonzero(union)) if union.any() else 1.0


def partition_kcs(kc_counts, plastic_kc_indices, plastic_compartments, plastic_mask) -> dict:
    counts = np.asarray(kc_counts)
    pk = np.asarray(plastic_kc_indices)
    pc = np.asarray(plastic_compartments)
    mask = np.asarray(plastic_mask)
    if (
        counts.ndim != 3
        or counts.shape[:2] != (4, 2)
        or counts.dtype.kind not in "iu"
        or not np.isfinite(counts).all()
        or np.any(counts < 0)
        or pk.ndim != 1
        or pc.shape != pk.shape
        or mask.shape != pk.shape
        or pk.dtype.kind not in "iu"
        or pc.dtype.kind not in "iu"
        or mask.dtype.kind not in "iub"
        or np.any(pk < 0)
        or np.any(pk >= counts.shape[2])
        or not np.isin(mask, (0, 1)).all()
        or not np.isin(pc, (0, 1)).all()
    ):
        raise ValueError("KC partition inputs must match four seeds, two cues and existing plastic edges.")
    contrast = counts[:, 0].mean(0) - counts[:, 1].mean(0)
    preference = np.sign(contrast).astype(np.int8)
    active = counts > 0
    within = [
        [_jaccard(active[a, cue], active[b, cue]) for a, b in combinations(range(4), 2)] for cue in (0, 1)
    ]
    between = [_jaccard(active[a, 0], active[b, 1]) for a in range(4) for b in range(4)]
    channels = {}
    nonempty = True
    for channel, compartment in zip(CHANNELS, (0, 1)):
        eligible = mask.astype(bool) & (pc == compartment)
        first = np.flatnonzero(eligible & (preference[pk] > 0))
        second = np.flatnonzero(eligible & (preference[pk] < 0))
        tied = np.flatnonzero(eligible & (preference[pk] == 0))
        channels[channel] = {"first": first, "second": second, "tied": tied}
        nonempty &= bool(first.size and second.size)
    first_mean, second_mean, between_mean = map(
        float, (np.mean(within[0]), np.mean(within[1]), np.mean(between))
    )
    passed = bool(
        nonempty and first_mean > between_mean and second_mean > between_mean and between_mean <= 0.5
    )
    return {
        "passed": passed,
        "preference": preference,
        "channels": channels,
        "source_counts": counts.copy(),
        "plastic_kc_indices": pk.copy(),
        "plastic_compartments": pc.copy(),
        "plastic_mask": mask.copy(),
        "jaccard": {
            "within_first": within[0],
            "within_second": within[1],
            "between": between,
            "within_first_mean": first_mean,
            "within_second_mean": second_mean,
            "between_mean": between_mean,
        },
    }


def array_identity(value) -> dict:
    array = np.asarray(value)
    if array.dtype.kind not in "biufc" or not np.isfinite(array).all():
        raise ValueError("Numerical evidence must be finite.")
    return {
        "dtype": array.dtype.str,
        "shape": list(array.shape),
        "sha256": hashlib.sha256(array.tobytes()).hexdigest(),
    }


def _numeric_identities(value, path="", out=None):
    out = {} if out is None else out
    if path.rsplit(".", 1)[-1] == "wall_seconds":
        return out
    if isinstance(value, dict):
        for key in sorted(value):
            _numeric_identities(value[key], f"{path}.{key}" if path else str(key), out)
    elif isinstance(value, np.ndarray) or isinstance(value, (int, float, complex, np.number, bool)):
        out[path] = array_identity(value)
    elif isinstance(value, (list, tuple)):
        array = np.asarray(value)
        if array.dtype.kind in "biufc":
            out[path] = array_identity(array)
        else:
            for index, item in enumerate(value):
                _numeric_identities(item, f"{path}.{index}", out)
    return out


def compare_numeric_results(first: dict, second: dict, *, schema=None) -> dict:
    if schema is None:
        raise ValueError("Replay requires the complete independently specified engine-result schema.")
    validate_numeric_result(first, schema)
    validate_numeric_result(second, schema)
    left, right = _numeric_identities(first), _numeric_identities(second)
    differences = sorted(key for key in set(left) | set(right) if left.get(key) != right.get(key))

    def metadata(x):
        return {
            k: v
            for k, v in x.items()
            if not isinstance(v, np.ndarray) and k not in ("instrumentation", "wall_seconds")
        }

    if metadata(first) != metadata(second):
        differences.append("metadata")
    return {"passed": not differences, "differences": differences, "first": left, "second": right}


def _endpoint(value, n_gains=None, *, probe_contract=None):
    if not isinstance(value, dict):
        raise ValueError("Endpoint evidence must be a mapping.")
    responses = np.asarray(value.get("responses"), dtype=float)
    gains = np.asarray(value.get("gains"))
    hits = value.get("bound_hits")
    if (
        responses.shape != (4, 2, 2)
        or not np.isfinite(responses).all()
        or np.any(responses < 0)
        or gains.ndim != 1
        or gains.dtype != np.float32
        or not np.isfinite(gains).all()
        or (n_gains is not None and len(gains) != n_gains)
        or isinstance(hits, (bool, np.bool_))
        or not isinstance(hits, (int, np.integer))
        or hits < 0
    ):
        raise ValueError("Endpoint responses, gains or bound evidence are malformed.")
    if np.any(gains <= 0.5) or np.any(gains >= 1.5):
        raise ValueError("Endpoint gain reached or exceeded an inclusive bound.")
    actual = value.get("probe_contract")
    if not isinstance(actual, dict) or set(actual) != {"family", "duration_ms", "cue_window", "seeds"}:
        raise ValueError("Complete matched probe identity is required.")
    if actual["family"] not in FAMILIES:
        raise ValueError("Unknown conditioning cue family.")
    if probe_contract is None:
        duration = actual["duration_ms"]
        expected = dict(
            family=actual["family"],
            duration_ms=duration,
            cue_window=[0, 300] if duration == 400 else [300, 600],
            seeds=list(range(2_000_042, 2_000_046)) if duration == 400 else list(range(5_000_042, 5_000_046)),
        )
        if (
            type(duration) is not int
            or duration not in (400, 800)
            or (duration == 800 and actual["family"] != "AB")
        ):
            raise ValueError("Invalid frozen probe duration/family.")
    else:
        expected = probe_contract
    if json.dumps(actual, sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise ValueError("Probe schedule, seed or family mismatch.")
    if "response_counts" in value or "response_populations" in value:
        counts = np.asarray(value.get("response_counts"))
        pop = np.asarray(value.get("response_populations"))
        if (
            counts.shape != (4, 2, 2)
            or counts.dtype != np.int64
            or np.any(counts < 0)
            or pop.shape != (2,)
            or pop.dtype != np.int32
            or np.any(pop <= 0)
            or not np.array_equal(responses, counts / (pop * 0.3))
        ):
            raise ValueError("Response Hz does not derive from exact retained counts/populations.")
        responses = np.array([Fraction(int(x)) for x in counts.flat], dtype=object).reshape(counts.shape)
    return responses, gains, int(hits)


def _validated_partition(value):
    if not isinstance(value, dict):
        raise ValueError("KC specificity requires retained source counts and anatomy.")
    regenerated = partition_kcs(
        value["source_counts"],
        value["plastic_kc_indices"],
        value["plastic_compartments"],
        value["plastic_mask"],
    )
    if value.get("passed") is not regenerated["passed"]:
        raise ValueError("Stored KC specificity verdict differs from retained sources.")
    for key in ("preference", "plastic_kc_indices", "plastic_compartments", "plastic_mask"):
        if array_identity(value[key]) != array_identity(regenerated[key]):
            raise ValueError("Fixed KC preference or anatomy changed.")
    if value.get("jaccard") != regenerated["jaccard"]:
        raise ValueError("KC similarity accounting changed.")
    for channel in CHANNELS:
        for group in ("first", "second", "tied"):
            if array_identity(value["channels"][channel][group]) != array_identity(
                regenerated["channels"][channel][group]
            ):
                raise ValueError("Preferred eligible edge sets were altered.")
    return regenerated


def _fixed_thresholds(effect_ratio, replay_error):
    if (
        type(effect_ratio) not in (int, float)
        or effect_ratio != 3.0
        or type(replay_error) not in (int, float)
        or replay_error != 0.0
    ):
        raise ValueError("Only fixed3x and exact-zero numerical replay error are allowed.")


def _gain_invariants(gains, parent, partitions, *, frozen=False):
    mask = partitions["plastic_mask"].astype(bool)
    if gains.shape != mask.shape or parent.shape != mask.shape:
        raise ValueError("Gain/checkpoint anatomy shape differs.")
    if gains[~mask].tobytes() != parent[~mask].tobytes():
        raise ValueError("Masked gain bytes changed.")
    if frozen and gains.tobytes() != parent.tobytes():
        raise ValueError("Frozen gain bytes changed.")


def _mean_gain(gains, indices):
    selected = np.asarray(indices)
    if selected.ndim != 1 or selected.dtype.kind not in "iu" or not selected.size:
        raise ValueError("Every preferred eligible edge set must be nonempty.")
    if np.any(selected < 0) or np.any(selected >= len(gains)):
        raise ValueError("Preferred edge index is outside the gain vector.")
    # Published float32 checkpoints and their differences are dyadic rationals.
    # Sum Python integers/rationals before dividing by the actual eligible-edge count.
    return sum((Fraction(float(x)) for x in gains[selected]), Fraction(0)) / len(selected)


def evaluate_acquisition(unit, endpoints, partitions, *, effect_ratio=3.0, replay_error=0.0) -> dict:
    result = {"all_passed": False, "errors": [], "panels": {}}
    try:
        _fixed_thresholds(effect_ratio, replay_error)
        effect_ratio, replay_error = 3, 0
        partitions = _validated_partition(partitions)
        unit_response, unit_gains, unit_hits = _endpoint(unit)
        if (
            unit_hits
            or not np.array_equal(unit_gains, np.ones_like(unit_gains))
            or not partitions.get("passed")
        ):
            raise ValueError("Unit checkpoint or KC specificity gate failed.")
        if unit["probe_contract"]["duration_ms"] != 400:
            raise ValueError("Acquisition requires matched400ms unit probes.")
        if set(endpoints) != {"0", "1000000"}:
            raise ValueError("Acquisition requires both training panels exactly once.")
        for panel_name, arms in endpoints.items():
            if set(arms) != set(ACQUISITION_ARMS):
                raise ValueError("Acquisition arm matrix is incomplete.")
            for value in arms.values():
                _same_response_units(unit, value)
            parsed = {
                name: _endpoint(value, len(unit_gains), probe_contract=unit["probe_contract"])
                for name, value in arms.items()
            }
            for name, (_, gains, _) in parsed.items():
                _gain_invariants(gains, unit_gains, partitions, frozen=name == "frozen")
            if not np.array_equal(parsed["frozen"][0], unit_response):
                raise ValueError("Frozen responses differ from deterministic matched unit probes.")
            panel_result = {}
            for channel_index, channel in enumerate(CHANNELS):
                target, other = channel_index, 1 - channel_index
                target_edges = partitions["channels"][channel]["first" if target == 0 else "second"]
                other_edges = partitions["channels"][channel]["second" if target == 0 else "first"]
                contrasts = {}
                gain_contrasts = {}
                target_changes = {}
                target_gain_changes = {}
                for arm, (responses, gains, hits) in parsed.items():
                    if hits:
                        raise ValueError(f"{panel_name}/{arm} contains a bound observation.")
                    delta = responses - unit_response
                    per_seed = delta[:, target, channel_index] - delta[:, other, channel_index]
                    contrasts[arm] = per_seed
                    target_changes[arm] = delta[:, target, channel_index]
                    gain_contrasts[arm] = _mean_gain(
                        gains.astype(np.float64) - unit_gains, target_edges
                    ) - _mean_gain(gains.astype(np.float64) - unit_gains, other_edges)
                    target_gain_changes[arm] = _mean_gain(gains.astype(np.float64) - unit_gains, target_edges)
                nulls = ACQUISITION_ARMS[1:]
                response_limit = effect_ratio * max(abs(np.mean(contrasts[name])) for name in nulls)
                gain_limit = effect_ratio * max(abs(gain_contrasts[name]) for name in nulls)
                paired_response = np.mean(contrasts["paired"])
                paired_gain = gain_contrasts["paired"]
                target_response_error = max(replay_error, float(np.max(np.abs(target_changes["frozen"]))))
                target_gain_error = max(replay_error, abs(target_gain_changes["frozen"]))
                channel_result = {
                    "response_selectivity": float(paired_response)
                    / (
                        int(unit["response_populations"][channel_index]) * 0.3
                        if "response_counts" in unit
                        else 1.0
                    ),
                    "gain_selectivity": float(paired_gain),
                    "response_limit": float(response_limit)
                    / (
                        int(unit["response_populations"][channel_index]) * 0.3
                        if "response_counts" in unit
                        else 1.0
                    ),
                    "gain_limit": float(gain_limit),
                    "fresh_seed_signs_passed": bool(np.all(contrasts["paired"] < 0)),
                    "target_response_depressed": bool(
                        np.all(target_changes["paired"] < -target_response_error)
                    ),
                    "target_gain_depressed": bool(target_gain_changes["paired"] < -target_gain_error),
                }
                channel_result["passed"] = bool(
                    channel_result["fresh_seed_signs_passed"]
                    and paired_response < 0
                    and paired_gain < 0
                    and abs(paired_response) >= response_limit
                    and abs(paired_gain) >= gain_limit
                    and channel_result["target_response_depressed"]
                    and channel_result["target_gain_depressed"]
                )
                panel_result[channel] = channel_result
            result["panels"][panel_name] = panel_result
        result["all_passed"] = bool(
            all(channel["passed"] for panel in result["panels"].values() for channel in panel.values())
        )
    except (KeyError, TypeError, ValueError, IndexError, OverflowError) as exc:
        result["errors"].append(str(exc))
    return result


def _preference(responses, unit, channel):
    target, other = channel, 1 - channel
    return (responses[:, target, channel] - responses[:, other, channel]) - (
        unit[:, target, channel] - unit[:, other, channel]
    )


def evaluate_reversal(
    unit, parents, finals, partitions, starts, *, effect_ratio=3.0, replay_error=0.0
) -> dict:
    result = {"all_passed": False, "errors": [], "panels": {}, "classification": "failed"}
    ordinary_remapping = True
    try:
        _fixed_thresholds(effect_ratio, replay_error)
        effect_ratio, replay_error = 3, 0
        partitions = _validated_partition(partitions)
        unit_response, unit_gains, unit_hits = _endpoint(unit)
        if (
            unit_hits
            or not np.array_equal(unit_gains, np.ones_like(unit_gains))
            or not partitions.get("passed")
        ):
            raise ValueError("Reversal unit checkpoint or KC gate failed.")
        if unit["probe_contract"]["duration_ms"] != 800:
            raise ValueError("Reversal requires matched800ms unit probes.")
        expected_panels = {"3000000", "4000000"}
        if (
            set(parents) != expected_panels
            or set(finals) != expected_panels
            or set(starts) != expected_panels
        ):
            raise ValueError("Reversal requires both panels and parents exactly once.")
        for panel_name in sorted(expected_panels):
            _same_response_units(unit, parents[panel_name])
            parent_response, parent_gains, parent_hits = _endpoint(
                parents[panel_name], len(unit_gains), probe_contract=unit["probe_contract"]
            )
            branches = finals[panel_name]
            if parent_hits or set(branches) != set(REVERSAL_BRANCHES):
                raise ValueError("Reversal parent or branch matrix is invalid.")
            parent_hash = array_identity(parent_gains)["sha256"]
            for value in branches.values():
                _same_response_units(unit, value)
            parsed = {
                name: _endpoint(value, len(unit_gains), probe_contract=unit["probe_contract"])
                for name, value in branches.items()
            }
            _gain_invariants(parent_gains, unit_gains, partitions)
            for name, (_, gains, _) in parsed.items():
                _gain_invariants(gains, parent_gains, partitions, frozen=name == "frozen-retention")
            lineage = all(
                starts[panel_name].get(name) == parent_hash
                and branches[name].get("start_sha256") == parent_hash
                for name in REVERSAL_BRANCHES
            )
            panel_result = {"lineage_passed": lineage, "channels": {}}
            panel_passed = lineage
            strict_response, strict_gains, strict_hits = parsed["backward-erasure-plus-swap"]
            untaught_response, untaught_gains, untaught_hits = parsed["untaught-exposure"]
            frozen_response, frozen_gains, frozen_hits = parsed["frozen-retention"]
            continued_response = parsed["continued-acquisition"][0]
            if any(values[2] for values in parsed.values()):
                panel_passed = False
            if not np.array_equal(frozen_response, parent_response):
                raise ValueError("Frozen-retention responses differ from deterministic parent probes.")
            ordinary_response, ordinary_gains, _ = parsed["ordinary-contingency-swap"]
            frozen_exact = np.array_equal(frozen_gains, parent_gains)
            panel_passed &= frozen_exact and not strict_hits and not untaught_hits and not frozen_hits
            panel_remapping = True
            for channel_index, channel in enumerate(CHANNELS):
                old, new = channel_index, 1 - channel_index
                old_edges = partitions["channels"][channel]["first" if old == 0 else "second"]
                new_edges = partitions["channels"][channel]["second" if old == 0 else "first"]
                parent_preference = _preference(parent_response, unit_response, channel_index)
                strict_preference = _preference(strict_response, unit_response, channel_index)
                continued_preference = _preference(continued_response, unit_response, channel_index)
                parent_target = parent_response[:, old, channel_index] - unit_response[:, old, channel_index]
                parent_gain = _mean_gain(parent_gains, old_edges)
                parent_gate = bool(
                    np.all(parent_preference < 0) and np.all(parent_target < 0) and parent_gain < 1
                )
                response_move = (
                    strict_response[:, old, channel_index] - parent_response[:, old, channel_index]
                )
                null_move = untaught_response[:, old, channel_index] - parent_response[:, old, channel_index]
                frozen_move = frozen_response[:, old, channel_index] - parent_response[:, old, channel_index]
                response_recovery = bool(
                    np.all(response_move > 0)
                    and np.all(
                        response_move >= effect_ratio * np.maximum(np.abs(null_move), np.abs(frozen_move))
                    )
                    and np.all(
                        np.abs(strict_response[:, old, channel_index] - unit_response[:, old, channel_index])
                        < np.abs(
                            parent_response[:, old, channel_index] - unit_response[:, old, channel_index]
                        )
                    )
                )
                gain_move = _mean_gain(strict_gains, old_edges) - parent_gain
                null_gain_move = _mean_gain(untaught_gains, old_edges) - parent_gain
                frozen_gain_move = _mean_gain(frozen_gains, old_edges) - parent_gain
                gain_recovery = bool(
                    gain_move > 0
                    and gain_move
                    >= effect_ratio * max(abs(null_gain_move), abs(frozen_gain_move), replay_error)
                    and abs(_mean_gain(strict_gains, old_edges) - 1) < abs(parent_gain - 1)
                )
                strict_delta = strict_response - parent_response
                untaught_delta = untaught_response - parent_response
                frozen_delta = frozen_response - parent_response
                new_selectivity = strict_delta[:, new, channel_index] - strict_delta[:, old, channel_index]
                null_selectivity = max(
                    abs(
                        np.mean(untaught_delta[:, new, channel_index] - untaught_delta[:, old, channel_index])
                    ),
                    abs(np.mean(frozen_delta[:, new, channel_index] - frozen_delta[:, old, channel_index])),
                )
                new_response = bool(
                    np.all(new_selectivity < 0)
                    and abs(np.mean(new_selectivity)) >= effect_ratio * null_selectivity
                    and np.all(strict_delta[:, new, channel_index] < -replay_error)
                )
                gain_delta = strict_gains.astype(np.float64) - parent_gains
                untaught_gain_delta = untaught_gains.astype(np.float64) - parent_gains
                frozen_gain_delta = frozen_gains.astype(np.float64) - parent_gains
                new_gain_selectivity = _mean_gain(gain_delta, new_edges) - _mean_gain(gain_delta, old_edges)
                null_gain = max(
                    abs(
                        _mean_gain(untaught_gain_delta, new_edges)
                        - _mean_gain(untaught_gain_delta, old_edges)
                    ),
                    abs(_mean_gain(frozen_gain_delta, new_edges) - _mean_gain(frozen_gain_delta, old_edges)),
                    replay_error,
                )
                new_gain = bool(
                    new_gain_selectivity < 0
                    and abs(new_gain_selectivity) >= effect_ratio * null_gain
                    and _mean_gain(gain_delta, new_edges) < -replay_error
                )
                flip = bool(
                    np.all(parent_preference < 0)
                    and np.all(strict_preference > 0)
                    and np.all(continued_preference < 0)
                )
                panel_remapping &= bool(
                    parent_gate
                    and np.all(_preference(ordinary_response, unit_response, channel_index) > 0)
                    and np.all(
                        ordinary_response[:, old, channel_index] <= parent_response[:, old, channel_index]
                    )
                    and _mean_gain(ordinary_gains, old_edges) <= parent_gain
                    and np.all(
                        ordinary_response[:, new, channel_index] < parent_response[:, new, channel_index]
                    )
                    and _mean_gain(ordinary_gains, new_edges) < _mean_gain(parent_gains, new_edges)
                )
                channel_result = {
                    "parent_mapping_passed": parent_gate,
                    "response_recovery_passed": response_recovery,
                    "gain_recovery_passed": gain_recovery,
                    "new_response_passed": new_response,
                    "new_gain_passed": new_gain,
                    "preference_flip_passed": flip,
                }
                channel_result["passed"] = all(channel_result.values())
                panel_result["channels"][channel] = channel_result
                panel_passed &= channel_result["passed"]
            panel_result["frozen_retention_passed"] = frozen_exact
            panel_result["passed"] = bool(panel_passed)
            result["panels"][panel_name] = panel_result
            ordinary_remapping &= bool(panel_remapping and lineage and not any(x[2] for x in parsed.values()))
            panel_result["ordinary_remapping_without_erasure"] = bool(panel_remapping)
        result["all_passed"] = bool(all(panel["passed"] for panel in result["panels"].values()))
        result["classification"] = (
            "strict-reversal"
            if result["all_passed"]
            else "dual-channel-preference-remapping-without-erasure"
            if ordinary_remapping
            else "failed"
        )
    except (KeyError, TypeError, ValueError, IndexError, OverflowError) as exc:
        result["errors"].append(str(exc))
    return result


@dataclass(frozen=True)
class NumericSchema:
    neurons: int
    samples: int
    kcs: int
    dans: int
    edges: int
    groups: int
    bins: int
    steps: int
    duration_ms: int
    learning_rule: str
    record: bool
    plasticity: bool
    pulses: tuple[tuple[float, int], ...] = ()
    compartments: int = 2


def validate_numeric_result(result, schema):
    """Validate the complete actual RewardEngine return contract before replay/reduction."""
    if not isinstance(schema, NumericSchema) or not isinstance(result, dict):
        raise ValueError("Numerical result/schema must be explicit.")
    if (
        schema.learning_rule not in ("event", "rate-bridge-v1")
        or schema.duration_ms not in (400, 800)
        or schema.bins != schema.duration_ms // 10
        or schema.steps != schema.duration_ms * 5
        or schema.compartments != 2
        or type(schema.record) is not bool
        or type(schema.plasticity) is not bool
        or any(
            type(getattr(schema, k)) is not int or getattr(schema, k) < 1
            for k in ("neurons", "samples", "kcs", "dans", "edges", "groups", "bins", "steps")
        )
    ):
        raise ValueError("Invalid fixed numerical dimensions/rule.")
    n, b, d, c, g = schema.neurons, schema.bins, schema.dans, schema.compartments, schema.edges
    arrays = {
        "counts": ("int32", (n,)),
        "rates": ("float32", (n,)),
        "rates_hz": ("float32", (n,)),
        "voltage": ("float32", (n,)),
        "trace": ("int32", (b, schema.samples)),
        "population": ("int32", (b,)),
        "dan_counts": ("int32", (d,)),
        "compartment_dan_counts": ("int32", (c,)),
        "compartment_tonic_hz": ("float32", (c,)),
        "gains": ("float32", (g,)),
        "gain_delta": ("float32", (g,)),
        "pulse_times_ms": ("float32", (len(schema.pulses),)),
        "pulse_dan_indices": ("int32", (len(schema.pulses),)),
    }
    required = set(arrays) | {"duration_ms", "dt", "bin_ms", "wall_seconds", "instrumentation"}
    if set(result) != required:
        raise ValueError("Missing or extra numerical result fields.")

    def check(values, specs):
        for key, (dtype, shape) in specs.items():
            a = values[key]
            if (
                not isinstance(a, np.ndarray)
                or a.dtype != np.dtype(dtype)
                or a.shape != shape
                or not np.isfinite(a).all()
            ):
                raise ValueError(f"Invalid numerical field {key}.")

    check(result, arrays)
    for key in (
        "counts",
        "rates",
        "rates_hz",
        "trace",
        "population",
        "dan_counts",
        "compartment_dan_counts",
        "compartment_tonic_hz",
    ):
        if np.any(result[key] < 0):
            raise ValueError(f"Negative counts/rates in {key}.")
    if any(
        type(result[k]) not in (int, float) or not np.isfinite(result[k])
        for k in ("duration_ms", "dt", "bin_ms", "wall_seconds")
    ):
        raise ValueError("Invalid numerical timing scalar types.")
    if (
        result["duration_ms"] != schema.duration_ms
        or result["dt"] != 0.2
        or result["bin_ms"] != 10.0
        or isinstance(result["wall_seconds"], bool)
        or not np.isfinite(result["wall_seconds"])
        or result["wall_seconds"] < 0
    ):
        raise ValueError("Numerical timing fields differ.")
    for actual, expected in (
        (result["rates"], result["rates_hz"]),
        (result["rates"], result["counts"].astype(np.float32) * (1000 / schema.duration_ms)),
        (result["pulse_times_ms"], np.array([x[0] for x in schema.pulses], np.float32)),
        (result["pulse_dan_indices"], np.array([x[1] for x in schema.pulses], np.int32)),
    ):
        if not np.array_equal(actual, expected):
            raise ValueError("Numerical rates or pulse identities disagree.")
    if (
        np.any(result["counts"] > schema.steps)
        or np.any(result["dan_counts"] > schema.steps)
        or np.any(result["trace"] > 50)
        or np.any(result["population"] > schema.neurons * 50)
        or np.any(result["compartment_tonic_hz"] > 5000)
    ):
        raise ValueError("Spike count/rate exceeds the discrete per-cell step bound.")
    rec = result["instrumentation"]
    if not schema.record:
        if rec is not None:
            raise ValueError("Unrecorded call must have explicit absent instrumentation.")
        return
    if not isinstance(rec, dict):
        raise ValueError("Recorded call lacks instrumentation.")
    common = {
        "signal_bins": ("float64", (b, c, 4)),
        "kc_signal_bins": ("float64", (b, 2)),
        "step_signals": ("float32", (schema.steps, 1 + 2 * c)),
        "plastic_groups": ("int32", (g,)),
    }
    if schema.learning_rule == "rate-bridge-v1":
        specs = dict(
            common,
            bridge_signals=("float64", (schema.steps, c, 2)),
            bridge_kc_bins=("float64", (b, schema.kcs, 2)),
            bridge_kc_used=("float64", (schema.steps, schema.groups, 2)),
            bridge_rule=("float64", (schema.steps, schema.groups, 8)),
            bridge_tail=("float64", (schema.groups, 8)),
            plastic_compartments=("int32", (g,)),
        )
        if set(rec) != set(specs) | {
            "learning_rule",
            "layout_version",
            "event_rule_applicable",
            "layout",
            "config",
        }:
            raise ValueError("Incomplete bridge numerical result schema.")
        if (
            rec["learning_rule"] != "rate-bridge-v1"
            or rec["layout_version"] != "rate-bridge-v1/1"
            or rec["event_rule_applicable"] is not False
        ):
            raise ValueError("Bridge recording identity differs.")
        expected_config = dict(
            h_ms=0.2,
            tau_ms=500.0,
            rate_tau_ms=100.0,
            effective_eta=0.0005 if schema.plasticity else 0.0,
            normalization=0.96,
            tail="analytic_no_new_event_tail",
            checkpoint="float32; double remainder discarded",
        )
        if json.dumps(rec["config"], sort_keys=True) != json.dumps(expected_config, sort_keys=True):
            raise ValueError("Bridge configuration differs.")
    else:
        specs = dict(
            common,
            rule_bins=("float64", (b, schema.groups, 7)),
            kc_trace_bins=("float32", (b, schema.kcs)),
            step_rule=("float32", (schema.steps, schema.groups, 2)),
        )
        if set(rec) != set(specs) | {"layout"}:
            raise ValueError("Incomplete event numerical result schema.")
    check(rec, specs)
    nonnegative = (
        (
            "signal_bins",
            "kc_signal_bins",
            "step_signals",
            "bridge_signals",
            "bridge_kc_bins",
            "bridge_kc_used",
        )
        if schema.learning_rule == "rate-bridge-v1"
        else ("kc_signal_bins", "kc_trace_bins", "step_rule")
    )
    if any(np.any(rec[name] < 0) for name in nonnegative):
        raise ValueError("Negative rate, eligibility or spike signal.")
    if schema.learning_rule == "rate-bridge-v1":
        if (
            np.any(rec["step_signals"][:, 3:] != 0)
            or np.any(rec["signal_bins"][..., [1, 3]] != 0)
            or np.any(rec["kc_signal_bins"][:, 1] != 0)
        ):
            raise ValueError("Documented unused bridge fields must remain zero.")
        if not schema.plasticity and any(
            np.any(rec[k][..., :5] != 0) for k in ("bridge_rule", "bridge_tail")
        ):
            raise ValueError("Frozen eta0 must retain zero attempted/applied/published gain terms.")
    elif not schema.plasticity and np.any(rec["rule_bins"][..., :3] != 0):
        raise ValueError("Frozen event gain terms must remain zero.")
    if rec["layout"] != recording_layout(schema.learning_rule):
        raise ValueError("Complete instrumentation layout differs.")
    if (
        np.any(rec["plastic_groups"] < 0)
        or np.any(rec["plastic_groups"] >= schema.groups)
        or not isinstance(rec["layout"], dict)
        or not rec["layout"]
    ):
        raise ValueError("Invalid instrumentation layout/group identity.")


def recording_layout(rule):
    """Versioned public native recording labels; importing this never loads native code."""
    if rule == "rate-bridge-v1":
        fields = [
            "positive_integral",
            "negative_integral",
            "attempted",
            "double_applied",
            "published_applied",
            "bound_low",
            "bound_high",
            "q_used",
        ]
        return dict(
            bridge_signals=["dan_rate_after_injection", "dan_eligibility_prior"],
            bridge_kc_bins=["kc_rate_bin_end", "kc_eligibility_bin_end"],
            bridge_kc_used=["eligible_edge_kc_rate_mass", "eligible_edge_kc_eligibility_mass"],
            bridge_rule=fields,
            bridge_tail=fields,
            step_signals=["kc_spikes", "dan_mean_spikes per compartment", "unused zeros"],
            signal_bins=["dan_mean_spikes", "unused zero", "raw_dan_spikes", "zero_reference"],
            kc_signal_bins=["kc_spikes", "unused zero"],
        )
    if rule == "event":
        return dict(
            step_signals=[
                "kc_spikes",
                "dan_mean_spikes per compartment",
                "dan_trace_as_used per compartment",
            ],
            step_rule=["kc_impulses_on_eligible_edges", "kbar_mass_on_eligible_edges_as_used"],
            signal_bins=[
                "dan_mean_spikes",
                "dan_trace_end",
                "dan_signal_after_reference",
                "reference_per_step",
            ],
            kc_signal_bins=["kc_spikes", "kc_trace_mass_end"],
            rule_bins=[
                "term_dbar_k",
                "term_kbar_d",
                "applied",
                "clipped_low",
                "clipped_high",
                "kc_events_on_edges",
                "kbar_mass_on_edges_end",
            ],
        )
    raise ValueError("Unknown numerical recording rule.")


def validate_gain_evidence(result, before, schema, *, mask, groups, compartments):
    """Reconcile final bytes and independent group electrical/tail bound observations.

    Group observations originate in the separately tested native instrument. They
    do not reconstruct individual transient trajectories from group sums.
    """
    validate_numeric_result(result, schema)
    n = schema.edges
    for value, dtype in (
        (before, np.float32),
        (mask, np.uint8),
        (groups, np.int32),
        (compartments, np.int32),
    ):
        if not isinstance(value, np.ndarray) or value.shape != (n,) or value.dtype != dtype:
            raise ValueError("Gain evidence anatomy/checkpoint type or shape differs.")
    if (
        not np.isfinite(before).all()
        or not np.isin(mask, [0, 1]).all()
        or not np.isin(compartments, [0, 1]).all()
        or np.any(groups < 0)
        or np.any(groups >= schema.groups)
    ):
        raise ValueError("Invalid gain evidence anatomy values.")
    after = result["gains"]
    delta = after.astype(np.float64) - before
    if not np.array_equal(result["gain_delta"], after - before):
        raise ValueError("Returned gain delta differs from actual before/after bytes.")
    if np.any(before <= 0.5) or np.any(before >= 1.5) or np.any(after <= 0.5) or np.any(after >= 1.5):
        raise ValueError("Initial or final gain touches an inclusive bound.")
    if before[mask == 0].tobytes() != after[mask == 0].tobytes():
        raise ValueError("Masked gain bytes changed during call.")
    if not schema.plasticity and before.tobytes() != after.tobytes():
        raise ValueError("Frozen/probe gain bytes changed during call.")
    observed = {"electrical_bound_observations": 0, "tail_bound_observations": 0}
    if not schema.record:
        return observed
    rec = result["instrumentation"]
    if not np.array_equal(rec["plastic_groups"], groups):
        raise ValueError("Recorded group mapping differs.")
    if schema.learning_rule == "rate-bridge-v1":
        if not np.array_equal(rec["plastic_compartments"], compartments):
            raise ValueError("Recorded compartments differ.")
        electrical, tail = rec["bridge_rule"], rec["bridge_tail"]
        for values in (electrical, tail):
            if np.any(values[..., 0] < 0) or np.any(values[..., 1] > 0):
                raise ValueError("Signed bridge product areas differ.")
            if not np.allclose(values[..., 0] + values[..., 1], values[..., 2], rtol=1e-8, atol=1e-11):
                raise ValueError("Bridge integrated terms do not reconcile.")
        for values in (electrical, tail):
            if not np.allclose(values[..., 2], values[..., 3], rtol=1e-8, atol=1e-11):
                raise ValueError("Unbounded bridge attempted/double movement differs.")
            sizes = np.bincount(groups[mask.astype(bool)], minlength=schema.groups)
            if np.any(np.abs(values[..., 4] - values[..., 3]) > sizes * np.finfo(np.float32).eps * 2 + 1e-11):
                raise ValueError("Bridge publication exceeds per-group float32 rounding envelope.")
        counts = (electrical[..., 5:7], tail[..., 5:7])
        totals = electrical.sum(0)[:, 4] + tail[:, 4]
    else:
        electrical = rec["rule_bins"]
        counts = (electrical[..., 3:5], np.zeros((schema.groups, 2)))
        totals = electrical.sum(0)[:, 2]
    for key, values in zip(observed, counts):
        if np.any(values < 0) or not np.equal(values, np.rint(values)).all():
            raise ValueError("Malformed inclusive bound observations.")
        observed[key] = int(values.sum())
    for group in range(schema.groups):
        if delta[groups == group].sum() != totals[group]:
            raise ValueError("Per-group published gain changes disagree with actual endpoint bytes.")
    if any(observed.values()):
        raise ValueError("Native electrical or analytic-tail inclusive bound contact.")
    return observed


def evaluate_parent_mapping(unit, parents, partitions):
    """Whole-panel reversal entry gate, before any reversal training."""
    try:
        partition = _validated_partition(partitions)
        ur, ug, hits = _endpoint(unit)
        if (
            hits
            or not partition["passed"]
            or not np.array_equal(ug, np.ones_like(ug))
            or unit["probe_contract"]["duration_ms"] != 800
            or set(parents) != {"3000000", "4000000"}
        ):
            raise ValueError("Matched reversal baseline/parent matrix is invalid.")
        for parent in parents.values():
            _same_response_units(unit, parent)
            pr, pg, ph = _endpoint(parent, len(ug), probe_contract=unit["probe_contract"])
            _gain_invariants(pg, ug, partition)
            if ph:
                raise ValueError("Acquired parent has inclusive bound observations.")
            for ci, ch in enumerate(CHANNELS):
                edges = partition["channels"][ch]["first" if ci == 0 else "second"]
                if not (
                    np.all(_preference(pr, ur, ci) < 0)
                    and np.all(pr[:, ci, ci] < ur[:, ci, ci])
                    and _mean_gain(pg, edges) < 1
                ):
                    raise ValueError(
                        "Both acquired parents must retain the old mapping under matched800ms probes."
                    )
        return {"passed": True, "errors": []}
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        return {"passed": False, "errors": [str(exc)]}


def validate_fingerprints(value, schema):
    """Check complete retained numerical fingerprint structure; omitted raw traces are not reconstructed."""
    import re

    n, b, d, e = schema.neurons, schema.bins, schema.dans, schema.edges
    expected = {
        k: (dtype, list(shape))
        for k, dtype, shape in (
            ("counts", "<i4", (n,)),
            ("rates", "<f4", (n,)),
            ("rates_hz", "<f4", (n,)),
            ("voltage", "<f4", (n,)),
            ("trace", "<i4", (b, schema.samples)),
            ("population", "<i4", (b,)),
            ("dan_counts", "<i4", (d,)),
            ("compartment_dan_counts", "<i4", (2,)),
            ("compartment_tonic_hz", "<f4", (2,)),
            ("gains", "<f4", (e,)),
            ("gain_delta", "<f4", (e,)),
            ("pulse_times_ms", "<f4", (len(schema.pulses),)),
            ("pulse_dan_indices", "<i4", (len(schema.pulses),)),
            ("duration_ms", "<f8", ()),
            ("dt", "<f8", ()),
            ("bin_ms", "<f8", ()),
        )
    }
    if schema.record:
        t, g, k = schema.steps, schema.groups, schema.kcs
        specs = {
            "signal_bins": ("<f8", (b, 2, 4)),
            "kc_signal_bins": ("<f8", (b, 2)),
            "step_signals": ("<f4", (t, 5)),
            "plastic_groups": ("<i4", (e,)),
        }
        if schema.learning_rule == "rate-bridge-v1":
            specs.update(
                bridge_signals=("<f8", (t, 2, 2)),
                bridge_kc_bins=("<f8", (b, k, 2)),
                bridge_kc_used=("<f8", (t, g, 2)),
                bridge_rule=("<f8", (t, g, 8)),
                bridge_tail=("<f8", (g, 8)),
                plastic_compartments=("<i4", (e,)),
                event_rule_applicable=("|b1", ()),
            )
            specs.update(
                {
                    f"config.{name}": ("<f8", ())
                    for name in ("h_ms", "tau_ms", "rate_tau_ms", "effective_eta", "normalization")
                }
            )
        else:
            specs.update(
                rule_bins=("<f8", (b, g, 7)), kc_trace_bins=("<f4", (b, k)), step_rule=("<f4", (t, g, 2))
            )
        expected.update(
            {f"instrumentation.{key}": (dtype, list(shape)) for key, (dtype, shape) in specs.items()}
        )
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError("Incomplete numerical fingerprint family.")
    for key, (dtype, shape) in expected.items():
        meta = value[key]
        if (
            not isinstance(meta, dict)
            or set(meta) != {"dtype", "shape", "sha256"}
            or meta["dtype"] != dtype
            or meta["shape"] != shape
            or not isinstance(meta["sha256"], str)
            or not re.fullmatch("[0-9a-f]{64}", meta["sha256"])
        ):
            raise ValueError("Malformed numerical fingerprint: " + key)


def _same_response_units(unit, value):
    if ("response_counts" in unit) != ("response_counts" in value):
        raise ValueError("Mixed response count/Hz provenance.")
    if "response_counts" in unit and not np.array_equal(
        unit["response_populations"], value["response_populations"]
    ):
        raise ValueError("Response population denominator differs.")
