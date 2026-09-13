"""Independent frozen-document oracle; synthetic evidence only, no engine imports.

Sources: conditioning-preregistration.md plus its conditioning-prerun-addendum.md.
The addendum's 1,632 calls and 1,640/1,200 caps supersede the older arithmetic.
Identifiers below are local oracle identifiers, never experiment identities.
"""

from __future__ import annotations

import copy
import hashlib
from collections import Counter
from dataclasses import asdict, is_dataclass
from itertools import combinations

import numpy as np

ARMS = ("paired", "shuffled", "timing-unpaired", "untaught", "frozen")
BRANCHES = (
    "continued-acquisition",
    "ordinary-contingency-swap",
    "backward-erasure-plus-swap",
    "untaught-exposure",
    "frozen-retention",
)
CALL_FIELDS = (
    "stage",
    "kind",
    "family",
    "panel",
    "arm",
    "branch",
    "checkpoint",
    "cue",
    "seed",
    "duration_ms",
    "cue_window",
    "plasticity",
    "teaching",
    "exposure",
)
STAGE_COUNTS = {"acquisition-primary": 616, "acquisition-challenge": 616, "reversal": 400}


def expected_calls():
    """Ordered calls, replay targets, and canonical/disposable checkpoint ancestry.

    Parent references identify required bytes; they are not merely trusted strings.
    A runtime spy must also prove nonaliasing and verify the actual supplied arrays.
    """
    out = []

    def emit(
        *,
        stage,
        kind,
        family,
        panel=None,
        arm=None,
        branch=None,
        checkpoint,
        cue,
        seed,
        duration_ms,
        cue_window,
        plasticity=False,
        teaching=(),
        exposure=None,
        parent="unit",
        result=None,
        replay=None,
    ):
        row = dict(
            id=f"oracle-{len(out):04d}",
            stage=stage,
            kind=kind,
            family=family,
            panel=panel,
            arm=arm,
            branch=branch,
            checkpoint=checkpoint,
            cue=cue,
            seed=seed,
            duration_ms=duration_ms,
            cue_window=cue_window,
            plasticity=plasticity,
            teaching=tuple(teaching),
            exposure=exposure,
            replay_of=None if replay is None else replay["id"],
            input_checkpoint=parent,
            output_checkpoint=result or parent,
        )
        out.append(row)
        return row

    def replay(row, *, parent=None, result=None):
        fields = {k: row[k] for k in CALL_FIELDS}
        return emit(
            **fields,
            parent=parent or row["input_checkpoint"],
            result=result or row["output_checkpoint"],
            replay=row,
        )

    # The same declarative exposure/label tables apply independently to each family.
    for family, stage, letters in (
        ("AB", "acquisition-primary", "AB"),
        ("CD", "acquisition-challenge", "CD"),
    ):
        common = dict(stage=stage, family=family, duration_ms=400, cue_window=(0, 300))
        for seed in range(2_000_042, 2_000_046):
            for cue in letters:
                emit(**common, kind="unit-probe", checkpoint="unit", cue=cue, seed=seed)
        for panel in (0, 1_000_000):
            for arm in ARMS:
                prefix = f"{family}/{panel}/{arm}"
                parent = "unit"
                for i, cue_index in enumerate((0, 1, 1, 0) * 6):
                    cue = letters[cue_index]
                    channel = ("home", "away")[cue_index]
                    teaching_channel = (
                        ("home", "home", "away", "away")[i % 4] if arm == "shuffled" else channel
                    )
                    pulse = tuple((t, teaching_channel) for t in (310, 330, 350, 370))
                    cue_pulse = pulse if arm in ("paired", "shuffled") else ()
                    blank_pulse = pulse if arm == "timing-unpaired" else ()
                    post_cue, post_blank = f"{prefix}/cue-{i}", f"{prefix}/blank-{i}"
                    cue_row = emit(
                        **common,
                        kind="train-cue",
                        panel=panel,
                        arm=arm,
                        checkpoint=f"after-{i}",
                        cue=cue,
                        seed=42 + panel + 2 * i,
                        plasticity=arm != "frozen",
                        teaching=cue_pulse,
                        exposure=i,
                        parent=parent,
                        result=post_cue,
                    )
                    blank_common = dict(common, cue_window=None)
                    blank_row = emit(
                        **blank_common,
                        kind="train-blank",
                        panel=panel,
                        arm=arm,
                        checkpoint=f"after-{i}",
                        cue=None,
                        seed=43 + panel + 2 * i,
                        plasticity=arm != "frozen",
                        teaching=blank_pulse,
                        exposure=i,
                        parent=post_cue,
                        result=post_blank,
                    )
                    if arm == "paired" and i == 0:
                        replay(cue_row, result=f"{prefix}/replay-cue-0")
                        replay(blank_row, parent=f"{prefix}/replay-cue-0", result=f"{prefix}/replay-blank-0")
                    parent = post_blank
                    if i in (7, 15):
                        for q in letters:
                            emit(
                                **common,
                                kind="interim-probe",
                                panel=panel,
                                arm=arm,
                                checkpoint=f"block-{2 if i == 7 else 4}",
                                cue=q,
                                seed=2_001_042,
                                parent=parent,
                            )
                for seed in range(2_000_042, 2_000_046):
                    for cue in letters:
                        row = emit(
                            **common,
                            kind="endpoint-probe",
                            panel=panel,
                            arm=arm,
                            checkpoint="endpoint",
                            cue=cue,
                            seed=seed,
                            parent=parent,
                        )
                        if arm == "paired" and seed == 2_000_042:
                            replay(row)
    common = dict(stage="reversal", family="AB", duration_ms=800, cue_window=(300, 600))
    for seed in range(5_000_042, 5_000_046):
        for cue in "AB":
            row = emit(**common, kind="unit-probe", checkpoint="unit-800ms", cue=cue, seed=seed)
            if seed == 5_000_042:
                replay(row)
    for panel, acquisition_panel in ((3_000_000, 0), (4_000_000, 1_000_000)):
        acquired = f"AB/{acquisition_panel}/paired/blank-23"
        for seed in range(5_000_042, 5_000_046):
            for cue in "AB":
                emit(
                    **common,
                    kind="parent-probe",
                    panel=panel,
                    checkpoint="acquired-parent",
                    cue=cue,
                    seed=seed,
                    parent=acquired,
                )
    # Both parent mappings are required before any branch can begin.
    # Root's pre-execution implementation clarification makes this barrier explicit.
    for panel, acquisition_panel in ((3_000_000, 0), (4_000_000, 1_000_000)):
        acquired = f"AB/{acquisition_panel}/paired/blank-23"
        for branch in BRANCHES:
            parent = acquired
            for i, cue_index in enumerate((0, 1, 1, 0) * 6):
                old, new = ("home", "away")[cue_index], ("away", "home")[cue_index]
                if branch in ("continued-acquisition", "ordinary-contingency-swap"):
                    channel = old if branch == "continued-acquisition" else new
                    teaching = tuple((t, channel) for t in (610, 630, 650, 670, 690, 710, 730, 750))
                elif branch == "backward-erasure-plus-swap":
                    teaching = tuple((t, old) for t in (110, 130, 150, 170)) + tuple(
                        (t, new) for t in (610, 630, 650, 670)
                    )
                else:
                    teaching = ()
                result = f"AB/{panel}/{branch}/trial-{i}"
                row = emit(
                    **common,
                    kind="train-reversal",
                    panel=panel,
                    branch=branch,
                    checkpoint=f"after-{i}",
                    cue="AB"[cue_index],
                    seed=42 + panel + i,
                    plasticity=branch != "frozen-retention",
                    teaching=teaching,
                    exposure=i,
                    parent=parent,
                    result=result,
                )
                if i == 0:
                    replay(row, result=f"AB/{panel}/{branch}/replay-0")
                parent = result
                if i in (7, 15):
                    for cue in "AB":
                        emit(
                            **common,
                            kind="interim-probe",
                            panel=panel,
                            branch=branch,
                            checkpoint=f"block-{2 if i == 7 else 4}",
                            cue=cue,
                            seed=5_001_042,
                            parent=parent,
                        )
            for seed in range(5_000_042, 5_000_046):
                for cue in "AB":
                    row = emit(
                        **common,
                        kind="endpoint-probe",
                        panel=panel,
                        branch=branch,
                        checkpoint="endpoint",
                        cue=cue,
                        seed=seed,
                        parent=parent,
                    )
                    if branch == "backward-erasure-plus-swap" and seed == 5_000_042:
                        replay(row)
    assert len(out) == 1632
    assert Counter(x["stage"] for x in out) == STAGE_COUNTS
    return out


def normalized_calls(rows):
    """Normalize only identifier spelling; preserve order, all semantics and types."""
    rows = [asdict(x) if is_dataclass(x) else dict(x) for x in rows]
    ids = [x["id"] for x in rows]
    if any(type(x) is not str or not x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("Invalid/duplicate call identity")
    positions = {name: i for i, name in enumerate(ids)}
    out = []
    for i, row in enumerate(rows):
        if type(row["plasticity"]) is not bool:
            raise ValueError("Plasticity must be boolean")
        for name in ("seed", "duration_ms"):
            if type(row[name]) is not int:
                raise ValueError("Integer call field has wrong type")
        for name in ("panel", "exposure"):
            if row[name] is not None and type(row[name]) is not int:
                raise ValueError("Nullable integer call field has wrong type")
        ref = row.get("replay_of")
        if ref is not None and (ref not in positions or positions[ref] >= i):
            raise ValueError("Replay original must already exist")
        fields = []
        for name in CALL_FIELDS:
            value = row[name]
            if name == "teaching":
                value = tuple(tuple(x) for x in value)
            elif name == "cue_window" and value is not None:
                value = tuple(value)
            fields.append(value)
        out.append(tuple(fields) + (None if ref is None else positions[ref],))
    return out


def assert_exact_plan(rows):
    if normalized_calls(rows) != normalized_calls(expected_calls()):
        raise ValueError("Ordered call plan differs from frozen documents")
    return True


def byte_identity(array):
    a = np.ascontiguousarray(array)
    return {"dtype": a.dtype.str, "shape": list(a.shape), "sha256": hashlib.sha256(a.tobytes()).hexdigest()}


def independent_partition(counts, pk, pc, mask):
    c, pk, pc, mask = map(np.asarray, (counts, pk, pc, mask))
    if c.shape[:2] != (4, 2) or c.ndim != 3 or c.dtype.kind not in "iu" or np.any(c < 0):
        raise ValueError("Four ordered integer spike-count probe pairs required")
    if (
        pk.ndim != 1
        or pc.shape != pk.shape
        or mask.shape != pk.shape
        or pk.dtype.kind not in "iu"
        or pc.dtype.kind not in "iu"
    ):
        raise ValueError("Invalid complete edge mapping")
    if (
        not np.isin(pc, [0, 1]).all()
        or not np.isin(mask, [0, 1]).all()
        or np.any(pk < 0)
        or np.any(pk >= c.shape[2])
    ):
        raise ValueError("Invalid complete edge mapping values")
    # Integer sums avoid introducing a new tolerance around exact ties.
    contrast = c[:, 0].sum(axis=0, dtype=np.int64) - c[:, 1].sum(axis=0, dtype=np.int64)
    preference = np.sign(contrast)
    active = [[set(np.flatnonzero(c[s, q])) for s in range(4)] for q in range(2)]

    def j(a, b):
        return len(a & b) / len(a | b) if a | b else 1.0

    within = [[j(active[q][a], active[q][b]) for a, b in combinations(range(4), 2)] for q in (0, 1)]
    between = [j(a, z) for a in active[0] for z in active[1]]
    sets = {}
    for channel, ci in (("home", 0), ("away", 1)):
        selected = (pc == ci) & mask.astype(bool)
        sets[channel] = {
            name: np.flatnonzero(selected & (preference[pk] == sign))
            for name, sign in (("first", 1), ("second", -1), ("tied", 0))
        }
    passed = all(len(sets[ch][kind]) for ch in sets for kind in ("first", "second"))
    passed = bool(
        passed and max(0.0, np.mean(between)) <= 0.5 and all(np.mean(w) > np.mean(between) for w in within)
    )
    return dict(
        passed=passed,
        channels=sets,
        preference=preference,
        jaccard=dict(within=within, between=between),
        counts=c,
        pk=pk,
        pc=pc,
        mask=mask,
    )


def synthetic_fixture():
    """Unequal edge-set sizes and unequal raw MBON baselines, all exactly representable."""
    counts = np.array([[[2, 1, 0, 0], [0, 0, 2, 1]]] * 4, dtype=np.int32)
    partition = independent_partition(counts, [0, 1, 2, 0, 2, 3], [0, 0, 0, 1, 1, 1], [1] * 6)
    response = np.array([[[20 + s, 40 + s], [30 + s, 50 + s]] for s in range(4)], dtype=np.float64)

    def endpoint(delta, gains, parent=None):
        return dict(
            responses=response + np.asarray(delta),
            gains=np.asarray(gains, dtype=np.float32),
            bound_hits=0,
            start_sha256=parent,
        )

    unit = endpoint(np.zeros((4, 2, 2)), np.ones(6))
    acquisition = {}
    for panel in ("0", "1000000"):
        arms = {}
        for arm in ARMS:
            amplitude = {
                "paired": 3.0,
                "shuffled": 1.0,
                "timing-unpaired": 0.5,
                "untaught": 0.25,
                "frozen": 0.0,
            }[arm]
            gain_amplitude = amplitude / 16
            delta = np.zeros((4, 2, 2))
            delta[:, 0, 0] = delta[:, 1, 1] = -amplitude
            g = np.ones(6)
            g[[0, 1, 4, 5]] -= gain_amplitude
            arms[arm] = endpoint(delta, g)
        acquisition[panel] = arms
    parents, finals, starts = {}, {}, {}
    for panel in ("3000000", "4000000"):
        delta = np.zeros((4, 2, 2))
        delta[:, 0, 0] = delta[:, 1, 1] = -4
        g = np.array([0.75, 0.75, 1.0, 1.0, 0.75, 0.75], np.float32)
        parents[panel] = endpoint(delta, g)
        identity = byte_identity(g)["sha256"]
        branches = {}
        # Exact 3x recovery boundary: +3 response versus +1 null;
        # +.1875 preferred mean gain versus +.0625 null.
        for branch, old_r, new_r, old_g, new_g in (
            (BRANCHES[0], -8.0, 0.0, 0.625, 1.0),
            (BRANCHES[1], -4.0, -6.0, 0.75, 0.625),
            (BRANCHES[2], -1.0, -6.0, 0.9375, 0.625),
            (BRANCHES[3], -3.0, 0.0, 0.8125, 1.0),
            (BRANCHES[4], -4.0, 0.0, 0.75, 1.0),
        ):
            d = np.empty((4, 2, 2))
            d[:, 0, 0] = d[:, 1, 1] = old_r
            d[:, 1, 0] = d[:, 0, 1] = new_r
            branches[branch] = endpoint(d, [old_g, old_g, new_g, new_g, old_g, old_g], identity)
        finals[panel] = branches
        starts[panel] = {x: identity for x in BRANCHES}
    return dict(
        unit=unit,
        acquisition=acquisition,
        partitions=partition,
        parents=parents,
        finals=finals,
        starts=starts,
    )


def _endpoint(value, n):
    response, gain = np.asarray(value["responses"]), np.asarray(value["gains"])
    hits = value["bound_hits"]
    if (
        response.shape != (4, 2, 2)
        or response.dtype.kind not in "iu f".replace(" ", "")
        or not np.isfinite(response).all()
        or np.any(response < 0)
    ):
        raise ValueError("Invalid raw response matrix")
    if gain.shape != (n,) or gain.dtype != np.float32 or not np.isfinite(gain).all():
        raise ValueError("Invalid gain vector")
    if type(hits) is not int or hits < 0 or hits or np.any(gain <= 0.5) or np.any(gain >= 1.5):
        raise ValueError("Missing/malformed/bound-touch evidence")
    return response, gain.astype(np.float64)


def score_acquisition(fixture):
    """Independent arithmetic oracle, assuming schedule/evidence bindings separately validate."""
    f = fixture
    unit = f["unit"]
    partition = f["partitions"]
    endpoints = f["acquisition"]
    checked = independent_partition(partition["counts"], partition["pk"], partition["pc"], partition["mask"])
    n = len(unit["gains"])
    ur, ug = _endpoint(unit, n)
    if not checked["passed"] or not np.array_equal(ug, np.ones(n)) or set(endpoints) != {"0", "1000000"}:
        return False
    for panel in endpoints.values():
        if set(panel) != set(ARMS):
            return False
        parsed = {name: _endpoint(value, n) for name, value in panel.items()}
        if byte_identity(panel["frozen"]["gains"]) != byte_identity(unit["gains"]):
            return False
        if byte_identity(panel["frozen"]["responses"]) != byte_identity(unit["responses"]):
            return False
        for ci, channel in enumerate(("home", "away")):
            target, other = ci, 1 - ci
            ti = checked["channels"][channel]["first" if ci == 0 else "second"]
            oi = checked["channels"][channel]["second" if ci == 0 else "first"]
            response_select, gain_select, rd, gd = {}, {}, {}, {}
            for name, (r, g) in parsed.items():
                rd[name] = r[:, target, ci] - ur[:, target, ci]
                response_select[name] = rd[name] - (r[:, other, ci] - ur[:, other, ci])
                gd[name] = np.mean(g[ti]) - 1
                gain_select[name] = gd[name] - (np.mean(g[oi]) - 1)
            pr, pg = response_select["paired"], gain_select["paired"]
            if not (
                np.all(pr < 0)
                and pg < 0
                and abs(np.mean(pr)) >= 3 * max(abs(np.mean(response_select[x])) for x in ARMS[1:])
                and abs(pg) >= 3 * max(abs(gain_select[x]) for x in ARMS[1:])
            ):
                return False
            if not (np.all(rd["paired"] < -np.abs(rd["frozen"])) and gd["paired"] < -abs(gd["frozen"])):
                return False
    return True


def score_reversal(fixture):
    """Exact 3x equality is allowed; positive movement/depression remains strict."""
    f = fixture
    p = f["partitions"]
    partition = independent_partition(p["counts"], p["pk"], p["pc"], p["mask"])
    n = len(f["unit"]["gains"])
    ur, ug = _endpoint(f["unit"], n)
    if not partition["passed"] or not np.array_equal(ug, np.ones(n)):
        return dict(passed=False, ordinary_remapping=False)
    passed, remapping = True, True
    if any(set(f[key]) != {"3000000", "4000000"} for key in ("parents", "finals", "starts")):
        return dict(passed=False, ordinary_remapping=False)
    for panel in ("3000000", "4000000"):
        parent = f["parents"][panel]
        pr, pg = _endpoint(parent, n)
        branches = f["finals"][panel]
        if set(branches) != set(BRANCHES) or set(f["starts"][panel]) != set(BRANCHES):
            return dict(passed=False, ordinary_remapping=False)
        parsed = {k: _endpoint(v, n) for k, v in branches.items()}
        ph = byte_identity(parent["gains"])["sha256"]
        if any(f["starts"][panel][k] != ph or branches[k]["start_sha256"] != ph for k in BRANCHES):
            return dict(passed=False, ordinary_remapping=False)
        if byte_identity(branches[BRANCHES[4]]["gains"]) != byte_identity(parent["gains"]):
            return dict(passed=False, ordinary_remapping=False)
        if byte_identity(branches[BRANCHES[4]]["responses"]) != byte_identity(parent["responses"]):
            return dict(passed=False, ordinary_remapping=False)
        sr, sg = parsed[BRANCHES[2]]
        nr, ng = parsed[BRANCHES[3]]
        fr, fg = parsed[BRANCHES[4]]
        cr, _ = parsed[BRANCHES[0]]
        ordinary_r, ordinary_g = parsed[BRANCHES[1]]
        for ci, channel in enumerate(("home", "away")):
            old, new = ci, 1 - ci
            oldi = partition["channels"][channel]["first" if ci == 0 else "second"]
            newi = partition["channels"][channel]["second" if ci == 0 else "first"]

            def pref(r):
                return (r[:, old, ci] - ur[:, old, ci]) - (r[:, new, ci] - ur[:, new, ci])

            parent_gate = (
                np.all(pref(pr) < 0) and np.all(pr[:, old, ci] < ur[:, old, ci]) and np.mean(pg[oldi]) < 1
            )
            movement = sr[:, old, ci] - pr[:, old, ci]
            limit = 3 * np.maximum(abs(nr[:, old, ci] - pr[:, old, ci]), abs(fr[:, old, ci] - pr[:, old, ci]))
            response_recovery = (
                np.all(movement > 0)
                and np.all(movement >= limit)
                and np.all(abs(sr[:, old, ci] - ur[:, old, ci]) < abs(pr[:, old, ci] - ur[:, old, ci]))
            )
            gain_move = np.mean(sg[oldi]) - np.mean(pg[oldi])
            gain_limit = 3 * max(
                abs(np.mean(ng[oldi]) - np.mean(pg[oldi])), abs(np.mean(fg[oldi]) - np.mean(pg[oldi]))
            )
            gain_recovery = (
                gain_move > 0
                and gain_move >= gain_limit
                and abs(np.mean(sg[oldi]) - 1) < abs(np.mean(pg[oldi]) - 1)
            )
            rd, nd, fd = sr - pr, nr - pr, fr - pr
            select = rd[:, new, ci] - rd[:, old, ci]
            select_limit = 3 * max(abs(np.mean(d[:, new, ci] - d[:, old, ci])) for d in (nd, fd))
            new_response = (
                np.all(select < 0)
                and abs(np.mean(select)) >= select_limit
                and np.all(rd[:, new, ci] < -abs(fd[:, new, ci]))
            )
            gain_select = np.mean((sg - pg)[newi]) - np.mean((sg - pg)[oldi])
            gain_select_limit = 3 * max(
                abs(np.mean((g - pg)[newi]) - np.mean((g - pg)[oldi])) for g in (ng, fg)
            )
            new_gain = (
                gain_select < 0
                and abs(gain_select) >= gain_select_limit
                and np.mean((sg - pg)[newi]) < -abs(np.mean((fg - pg)[newi]))
            )
            passed &= bool(
                parent_gate
                and response_recovery
                and gain_recovery
                and new_response
                and new_gain
                and np.all(pref(sr) > 0)
                and np.all(pref(cr) < 0)
            )
            ordinary_flip = np.all(pref(ordinary_r) > 0)
            ordinary_no_old_recovery = (
                np.all(ordinary_r[:, old, ci] <= pr[:, old, ci])
                and np.all(ordinary_r[:, old, ci] < ur[:, old, ci])
                and np.mean(ordinary_g[oldi]) <= np.mean(pg[oldi])
                and np.mean(ordinary_g[oldi]) < 1
            )
            ordinary_new_depression = np.all(ordinary_r[:, new, ci] < pr[:, new, ci]) and np.mean(
                ordinary_g[newi]
            ) < np.mean(pg[newi])
            # Sufficient no-recovery classification. Partial/mixed recovery needs
            # separate reporting and cannot be forced into an erasure claim.
            remapping &= bool(
                parent_gate and ordinary_flip and ordinary_no_old_recovery and ordinary_new_depression
            )
    return dict(passed=passed, ordinary_remapping=remapping)


def clone_fixture():
    return copy.deepcopy(synthetic_fixture())
