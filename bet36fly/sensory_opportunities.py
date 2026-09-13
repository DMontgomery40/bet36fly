"""Engineered absolute-quality recruitment and external second-order comparison."""

import hashlib

import numpy as np


def recruitment_order(rows):
    groups = {s: [] for s in ["L", "R"]}
    for r in rows:
        if r["Connectome"] == "maleCNS" and r["Subtype"] in ["LB3b", "LB3c"]:
            side = r["Root_Side"]
            if side not in groups:
                raise ValueError("Sweet source side unresolved.")
            groups[side].append(int(r["Body_ID"]))
    if any(len(v) != 17 or len(set(v)) != 17 for v in groups.values()):
        raise ValueError("Sweet source population differs from frozen 17-per-side contract.")
    for side in groups:
        groups[side].sort(key=lambda body: hashlib.sha256(f"BET36FLY-contact-01:{body}".encode()).hexdigest())
    order = [body for pair in zip(groups["L"], groups["R"]) for body in pair]
    if len(set(order)) != 34:
        raise ValueError("Duplicate source identity across sides.")
    return order


def encode_quality(q, bounds, order):
    if (
        not np.isfinite([q, *bounds]).all()
        or len(bounds) != 2
        or not 0 <= bounds[0] <= q <= bounds[1] <= 1
        or len(order) != 34
        or len(set(order)) != 34
    ):
        raise ValueError("Invalid quality, uncertainty or recruitment order.")
    aversive = bounds[1] < 0.2
    n = 0 if aversive else int(np.floor(q * 34 + 0.5))
    return dict(
        quality=float(q),
        quality_interval=list(bounds),
        condition="bitter" if aversive else "sweet_recruitment",
        sweet_ids=order[:n],
        sweet_hz=58.9,
        bitter_hz=18.8 if aversive else 0.0,
        interpretation="Engineered contact recruitment; no within-match normalization or chemical dose inference.",
    )


def compare_outputs(home, away):
    home, away = np.asarray(home, float), np.asarray(away, float)
    if (
        home.shape != (4,)
        or away.shape != (4,)
        or not np.isfinite([home, away]).all()
        or np.any(home < 0)
        or np.any(away < 0)
    ):
        raise ValueError("Expected four finite nonnegative second-order rates per opportunity.")
    return float(np.log1p(home).mean() - np.log1p(away).mean())
