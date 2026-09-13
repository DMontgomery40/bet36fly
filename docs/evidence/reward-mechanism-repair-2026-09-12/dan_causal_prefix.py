"""Offline causal-prefix audit; no simulator import or neural execution.

This establishes a conditional equality prefix for the current pooled bridge,
not the complete per-cell taught history or behavior of a new nonlinear rule.
"""

import numpy as np


def _integers(values, name, *, low, high):
    try:
        items = list(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an integer vector") from exc
    if not items or any(
        isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, np.integer)) or not low <= int(v) <= high
        for v in items
    ):
        raise ValueError(f"{name} contains an invalid integer")
    return np.asarray(items, np.int64)


def decode_pool(means, populations):
    """Invert exactly float32(k/N), rejecting even adjacent float encodings."""
    a = np.asarray(means)
    p = _integers(populations, "populations", low=1, high=65535)
    if a.dtype != np.float32 or a.ndim != 2 or a.shape[0] == 0 or a.shape[1] != len(p):
        raise ValueError("pool must be nonempty float32[steps,populations]")
    if not np.isfinite(a).all() or np.any(a < 0) or np.any(a > 1):
        raise ValueError("pool contains invalid spike means")
    counts = np.rint(a.astype(np.float64) * p).astype(np.int64)
    encoded = (counts.astype(np.float64) / p).astype(np.float32)
    if not np.array_equal(a.view(np.uint32), encoded.view(np.uint32)):
        raise ValueError("pool is not an exact recorded float32 count fraction")
    return counts


def fine_pool(events, compartments, populations):
    """Pool actual individual binary events using an explicit cell-to-group map."""
    e = np.asarray(events)
    p = _integers(populations, "populations", low=1, high=65535)
    c = _integers(compartments, "compartments", low=0, high=len(p) - 1)
    if (
        e.ndim != 2
        or not e.shape[0]
        or e.shape[1] != len(c)
        or e.dtype.kind not in "iub"
        or not np.isin(e, (0, 1)).all()
        or not np.array_equal(np.bincount(c, minlength=len(p)), p)
    ):
        raise ValueError("fine events or population mapping are invalid")
    return np.stack([e[:, c == group].sum(axis=1, dtype=np.int64) for group in range(len(p))], axis=1)


def _first_difference(a, b):
    unequal = (a != b).reshape(len(a), -1).any(axis=1)
    indices = np.flatnonzero(unequal)
    return int(indices[0]) if indices.size else None


def _record_pair(a, b, name, steps, ndim, last=None, nonnegative=False):
    a, b = np.asarray(a), np.asarray(b)
    if (
        a.shape != b.shape
        or a.ndim != ndim
        or a.shape[0] != steps
        or not a.size
        or a.dtype.kind not in "fiu"
        or b.dtype.kind not in "fiu"
        or not np.isfinite(a).all()
        or not np.isfinite(b).all()
        or (last is not None and a.shape[-1] != last)
        or (nonnegative and (np.any(a < 0) or np.any(b < 0)))
    ):
        raise ValueError(f"{name} recording has invalid shape or values")
    return a, b


def prefix_contrast(
    untaught,
    taught,
    *,
    populations,
    first_pulse_step,
    kc_total_untaught,
    kc_total_taught,
    kc_used_untaught,
    kc_used_taught,
    rule_untaught,
    rule_taught,
):
    u, t = decode_pool(untaught, populations), decode_pool(taught, populations)
    if u.shape != t.shape:
        raise ValueError("pool shapes differ")
    steps = len(u)
    if (
        isinstance(first_pulse_step, (bool, np.bool_))
        or not isinstance(first_pulse_step, (int, np.integer))
        or not 0 <= first_pulse_step < steps
    ):
        raise ValueError("invalid first scheduled pulse step")
    ku, kt = _record_pair(kc_total_untaught, kc_total_taught, "KC totals", steps, 1, nonnegative=True)
    if np.any(ku != np.floor(ku)) or np.any(kt != np.floor(kt)):
        raise ValueError("KC totals must count integer events")
    eu, et = _record_pair(kc_used_untaught, kc_used_taught, "KC state", steps, 3, 2, True)
    ru, rt = _record_pair(rule_untaught, rule_taught, "rule", steps, 3, 8)
    if eu.shape[1] != ru.shape[1]:
        raise ValueError("KC and rule group maps differ")
    first = _first_difference(u, t)
    if first is not None and first < first_pulse_step:
        raise ValueError("pool diverges before first scheduled pulse")
    # Spike selection precedes the gain write: KC equality includes first.
    kc_stop = first + 1 if first is not None else steps
    rule_stop = first if first is not None else steps
    if not np.array_equal(ku[:kc_stop], kt[:kc_stop]) or not np.array_equal(eu[:kc_stop], et[:kc_stop]):
        raise ValueError("KC causal prefix contradicts the current-code assumptions")
    if not np.array_equal(ru[:rule_stop], rt[:rule_stop]):
        raise ValueError("rule causal prefix contradicts the current-code assumptions")
    return {
        "first_pool_difference_step": first,
        "first_pool_count_difference": (t[first] - u[first]).tolist() if first is not None else None,
        "untaught_counts_at_first_difference": u[first].tolist() if first is not None else None,
        "taught_counts_at_first_difference": t[first].tolist() if first is not None else None,
        "kc_equal_through_step": kc_stop - 1,
        "rule_equal_before_step": rule_stop,
        "first_rule_difference_step": _first_difference(ru, rt),
        "first_kc_total_difference_step": _first_difference(ku, kt),
        "first_kc_used_difference_step": _first_difference(eu, et),
        "total_compartment_count_difference": (t - u).sum(axis=0).tolist(),
        "per_cell_taught_history_established": False,
        "scope": "Current pooled bridge conditional prefix only; no new-rule trajectory or post-prefix KC equality.",
    }


def matched_rows(fine_rows, summaries, protocol):
    """Require the complete declared active comparison matrix and exact seeds."""
    if not isinstance(fine_rows, list) or not fine_rows:
        raise ValueError("empty fine row selector")
    for row in fine_rows:
        if (
            not isinstance(row, dict)
            or set(row) != {"game", "seed_set", "seed", "run_id"}
            or not isinstance(row["run_id"], str)
            or not row["run_id"]
            or row["seed_set"] not in ("base", "alt")
            or any(
                isinstance(row[key], bool) or not isinstance(row[key], int) or row[key] < 0
                for key in ("game", "seed")
            )
        ):
            raise ValueError("invalid fine row identity")
    expected = []
    seen = set()
    for run_id, summary in summaries.items():
        if summary.get("run_id") != run_id or summary.get("identity", {}).get("protocol") != protocol:
            raise ValueError("summary run or protocol identity mismatch")
        declared = summary.get("identity", {}).get("selection", {}).get("expected_panel", [])
        actual = summary.get("rows", [])

        def index(rows):
            result = {}
            for row in rows:
                try:
                    key = (row["game"], row["seed_set"], row["condition"])
                    seed = row["seed"]
                except (TypeError, KeyError) as exc:
                    raise ValueError("missing row identity") from exc
                if (
                    key in result
                    or isinstance(key[0], bool)
                    or not isinstance(key[0], int)
                    or key[1] not in ("base", "alt")
                    or key[2] not in ("frozen", "untaught", "home", "away")
                    or isinstance(seed, bool)
                    or not isinstance(seed, int)
                    or seed < 0
                ):
                    raise ValueError("invalid or duplicate row identity")
                result[key] = seed
            return result

        di, ai = index(declared), index(actual)
        games = summary.get("panel_games", [])
        if (
            not isinstance(games, list)
            or not games
            or any(isinstance(game, bool) or not isinstance(game, int) or game < 0 for game in games)
            or len(set(games)) != len(games)
        ):
            raise ValueError("invalid panel game identity")
        matrix = {
            (g, s, c) for g in games for s in ("base", "alt") for c in ("frozen", "untaught", "home", "away")
        }
        if set(di) != matrix or ai != di:
            raise ValueError("incomplete or mismatched declared panel")
        for game in games:
            for noise in ("base", "alt"):
                seeds = {di[game, noise, c] for c in ("frozen", "untaught", "home", "away")}
                if len(seeds) != 1:
                    raise ValueError("matched conditions have different seeds")
                row = dict(game=game, seed_set=noise, seed=seeds.pop(), run_id=run_id)
                identity = tuple(row.values())
                if identity in seen:
                    raise ValueError("duplicate fine selector")
                seen.add(identity)
                expected.append(row)
    if fine_rows != expected:
        raise ValueError("fine selector does not match complete ordered panel identity")
    return expected
