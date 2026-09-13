"""Independent 60-digit scalar reference; no producer/source/history imports.

The published WT1 decimal constants and exact rational seconds are declared
here. Z=exp(t/tau)*(H-1) is constant between events; each source-Euler jump
updates Z to q*Z+(q-1)*exp(t/tau). This differs from the producer's float64
last-event post-state anchoring. Output F64 conversion occurs only after
high-precision state/release computation. No learning or gain publication.
"""

from functools import lru_cache
import math

import mpmath as mp
import numpy as np

DECIMAL_P = ("0.0105", "-0.003", "-0.0011")
DECIMAL_TAU = ("7.5", "15", "900")


@lru_cache(maxsize=8)
def _clock(steps):
    with mp.workdps(60):
        return tuple(
            tuple(mp.exp(mp.mpf(t) / 5000 / mp.mpf(tau)) for tau in DECIMAL_TAU) for t in range(steps + 1)
        )


def scalar_reference(steps, event_steps):
    """All scalar-cell states at row time and exact T/5000 endpoint."""
    if type(steps) is not int or not 0 <= steps <= 2000:
        raise ValueError("steps outside finite binary domain")
    events = list(event_steps)
    if any(type(t) is not int or not 0 <= t < steps for t in events) or events != sorted(set(events)):
        raise ValueError("events must be unique strictly ordered integer steps")
    active = set(events)
    before = np.empty((steps, 3), np.float64)
    after = np.empty_like(before)
    release = np.zeros(steps, np.float64)
    with mp.workdps(60):
        q = tuple(1 + mp.mpf(p) for p in DECIMAL_P)
        z = [mp.mpf(0)] * 3
        exponent = _clock(steps)
        for t in range(steps):
            h = [1 + z[j] / exponent[t][j] for j in range(3)]
            before[t] = [float(v) for v in h]
            if t in active:
                release[t] = float(mp.fprod(h))
                z = [q[j] * z[j] + (q[j] - 1) * exponent[t][j] for j in range(3)]
            after[t] = [float(1 + z[j] / exponent[t][j]) for j in range(3)]
        endpoint = np.array([float(1 + z[j] / exponent[steps][j]) for j in range(3)])
    return dict(before=before, after=after, release=release, endpoint=endpoint)


def reference_events(spikes, compartments):
    """Synthetic complete 24-cell oracle with compensated scalar pooling."""
    if (
        type(spikes) is not np.ndarray
        or spikes.dtype != np.int32
        or spikes.ndim != 2
        or spikes.shape[1] != 24
        or not 0 <= len(spikes) <= 2000
        or np.any((spikes != 0) & (spikes != 1))
    ):
        raise ValueError("invalid synthetic binary raster")
    if (
        type(compartments) is not np.ndarray
        or compartments.dtype != np.int32
        or compartments.shape != (24,)
        or np.count_nonzero(compartments == 0) != 2
        or np.count_nonzero(compartments == 1) != 22
    ):
        raise ValueError("invalid synthetic channel map")
    memo, columns = {}, []
    for c in range(24):
        events = tuple(np.flatnonzero(spikes[:, c]).tolist())
        if events not in memo:
            memo[events] = scalar_reference(len(spikes), events)
        columns.append(memo[events])
    release = np.column_stack([c["release"] for c in columns])
    pooled = np.zeros((len(spikes), 2), np.float64)
    for t in range(len(spikes)):
        for c, population in [(0, 2), (1, 22)]:
            pooled[t, c] = math.fsum(release[t, compartments == c]) / population
    return dict(
        per_cell_release=release,
        pooled_release=pooled,
        state_before=np.stack([c["before"] for c in columns], axis=1),
        state_after=np.stack([c["after"] for c in columns], axis=1),
        endpoint_state=np.stack([c["endpoint"] for c in columns]),
    )
