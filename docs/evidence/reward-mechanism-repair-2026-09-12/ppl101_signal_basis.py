"""Offline full-tail linear basis for each PPL101 signal; no simulator imports."""

from __future__ import annotations

import itertools
import numpy as np

DT = 0.2
ONSET = 500
RATE_TAU = 100.0
ELIGIBILITY_TAU = 500.0
ETA = 0.0005
AREA_ATOL = 1e-10
GAIN_ADDITIONS = 1501
DOUBLE_UNIT_ROUNDOFF = 2**-53
DOUBLE_ACCUMULATION_ALLOWANCE = (
    GAIN_ADDITIONS * DOUBLE_UNIT_ROUNDOFF / (1 - GAIN_ADDITIONS * DOUBLE_UNIT_ROUNDOFF) * 1.5
)
PREFIX_MARGIN = 2 * AREA_ATOL + DOUBLE_ACCUMULATION_ALLOWANCE + 2**-24


def prefix_linear_applicability(maximum_absolute_area):
    """Conditional numerical guard, including double accumulation/F32 publication.

    AREA_ATOL is a declared integration allowance for each opposing product;
    canonical endpoint agreement is not a proof of arbitrary-prefix error.
    """
    if not np.isfinite(maximum_absolute_area) or maximum_absolute_area < 0:
        raise ValueError("Finite nonnegative absolute area required")
    return bool(maximum_absolute_area + PREFIX_MARGIN < 0.5)


def pair_areas(lag):
    """Integral of positive, negative and net bridge terms for one event pair.

    lag = DAN time minus KC time in ms. Both impulses start at/after the
    cold-history onset. Integration continues to infinity with no new events.
    The bridge's normalization cancels b²/(b²-a²) in the signed integral.
    """
    lag = np.asarray(lag, dtype=np.float64)
    if not np.isfinite(lag).all():
        raise ValueError("Finite lags required")
    a, b = RATE_TAU, ELIGIBILITY_TAU
    age = np.abs(lag)
    ra, rb = np.exp(-age / a), np.exp(-age / b)
    coefficient = ETA * (1 - (a / b) ** 2) * b / (b - a)
    smaller = coefficient * (b / (a + b) - 0.5) * ra
    larger = coefficient * (b / (a + b) * rb - 0.5 * ra)
    positive = np.where(lag >= 0, smaller, larger)
    negative = -np.where(lag >= 0, larger, smaller)
    net = ETA * np.sign(lag) * (ra - rb)
    return np.stack((positive, negative, net), axis=-1)


def signal_basis(kc, dan, onset=ONSET):
    """Return [KC,DAN,positive/negative/net] without channel normalization."""
    kc, dan = np.asarray(kc), np.asarray(dan)
    if (
        kc.ndim != 2
        or dan.ndim != 2
        or kc.shape[0] != dan.shape[0]
        or not kc.shape[0]
        or not kc.shape[1]
        or not dan.shape[1]
        or type(onset) is not int
        or not 0 <= onset <= len(kc)
        or kc.dtype.kind not in "biu"
        or dan.dtype.kind not in "biu"
        or not np.isin(kc, (0, 1)).all()
        or not np.isin(dan, (0, 1)).all()
    ):
        raise ValueError("Matching nonempty binary event matrices and valid onset required")
    times = np.arange(onset, len(kc), dtype=np.float64) * DT
    active = kc[onset:].astype(np.float64)
    out = np.zeros((kc.shape[1], dan.shape[1], 3), np.float64)
    for d in range(dan.shape[1]):
        event_times = np.flatnonzero(dan[onset:, d]) * DT + onset * DT
        if not len(event_times):
            continue
        weights = pair_areas(event_times[None, :] - times[:, None]).sum(axis=1)
        out[:, d] = active.T @ weights
    return out


def relaxed_guard_envelope(edge_basis):
    """Necessary exclusion test, deliberately wider than any fixed anatomy map.

    Independent edge- and trial-specific convex weights are allowed only for
    these mathematical bounds. No such outcome-selected mapping is constructed.
    Float32 final publication and integration tolerance expand both endpoints.
    A false exclusion result establishes no feasible or anatomically valid map.
    """
    u = np.asarray(edge_basis)
    if u.ndim != 3 or u.shape[0] != 8 or u.shape[2] != 2 or not u.shape[1]:
        raise ValueError("Exactly eight trials, eligible edges, and two DANs required")
    if u.dtype.kind != "f" or not np.isfinite(u).all():
        raise ValueError("Finite floating basis required")
    u = u.astype(np.float64)
    scale = max(1.0, float(np.max(np.max(np.abs(u), axis=2).sum(axis=1))))
    rho = AREA_ATOL * scale
    error = u.shape[1] * (2**-24 + AREA_ATOL + DOUBLE_ACCUMULATION_ALLOWANCE) + rho
    low = np.min(u, axis=2).sum(axis=1) - error
    high = np.max(u, axis=2).sum(axis=1) + error
    mean_low, mean_high = float(low.mean()), float(high.mean())
    min_abs_mean = 0.0 if mean_low <= 0 <= mean_high else min(abs(mean_low), abs(mean_high))
    vertices = np.array(list(itertools.product((0, 1), repeat=8)), dtype=bool)
    # Sample SD is a convex norm of the centered vector, so its maximum over
    # this box occurs at a vertex. This is an upper bound, not a fitted run.
    max_sd = float(np.std(np.where(vertices, high, low), axis=1, ddof=1).max())
    minimum_mean_lower = max(0.0, min_abs_mean - rho)
    maximum_sd_upper = max_sd + rho
    return dict(
        trial_low=low.tolist(),
        trial_high=high.tolist(),
        mean_interval=[mean_low, mean_high],
        minimum_absolute_mean=min_abs_mean,
        maximum_sample_sd=max_sd,
        minimum_absolute_mean_lower=minimum_mean_lower,
        maximum_sample_sd_upper=maximum_sd_upper,
        guard_limit_upper=0.5 * maximum_sd_upper,
        reduction_statistics_allowance=rho,
        publication_and_numeric_expansion_per_trial=error,
        all_convex_mappings_excluded=bool(minimum_mean_lower > 0.5 * maximum_sd_upper),
        scope="Loose necessary bound on fixed histories; no feasible anatomical mapping established",
    )
