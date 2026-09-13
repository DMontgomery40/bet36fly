"""Independent DAN ODE + KC impulse-superposition reference, no file I/O.

Only supplied arrays are evaluated. Do not supply real saved histories until
root has frozen and executed their candidate screen. This module never imports
the writer calculator and does not reproduce its interval moment recurrence.
"""

from dataclasses import dataclass
import math

import numpy as np
from scipy.integrate import solve_ivp

from rate_adaptation_reference_oracle import E, ODE_ATOL, ODE_RTOL, R, tail_quadrature

DT = 0.2


@dataclass(frozen=True)
class DANReference:
    states: np.ndarray
    weighted_intervals: np.ndarray
    weighted_tail: np.ndarray
    evaluations: int


def integrate_dan_events(dan_mean_events):
    """Batch shape (trials, steps, channels); exact impulses, independent ODE.

    Weighted integrands are [E_Dplus*exp(-rt), H*exp(-et), H*exp(-rt)].
    States at each grid boundary precede that boundary's event injection.
    """
    events = np.asarray(dan_mean_events, dtype=float)
    if (events.ndim != 3 or min(events.shape) < 1 or not np.isfinite(events).all()
            or np.any(events < 0) or np.any(events > 1)):
        raise ValueError("DAN means must be finite nonnegative trial/step/channel arrays <=1")
    nb, steps, nc = events.shape
    if steps > 2000:
        raise ValueError("reference supports the fixed screen endpoint at most400ms")
    y = np.zeros((nb * nc, 6))
    states = np.zeros((nb, steps + 1, nc, 3))
    areas = np.zeros((nb, steps, nc, 3))
    evaluations = 0

    def rhs(t, flat):
        current = flat.reshape(nb * nc, 6)
        out = np.empty_like(current)
        d, baseline, v = current[:, 0], current[:, 1], current[:, 2]
        h = np.maximum(d - baseline, 0.0)
        out[:, 0] = -R * d
        out[:, 1] = E * (d - baseline)
        out[:, 2] = h - E * v
        out[:, 3] = v * math.exp(-R * t)
        out[:, 4] = h * math.exp(-E * t)
        out[:, 5] = h * math.exp(-R * t)
        return out.ravel()

    for i in range(steps):
        y[:, 0] += R * events[:, i, :].ravel()
        y[:, 3:] = 0
        solution = solve_ivp(
            rhs, (i * DT, (i + 1) * DT), y.ravel(), method="DOP853",
            rtol=ODE_RTOL, atol=ODE_ATOL, max_step=DT / 8,
        )
        if not solution.success or not np.isfinite(solution.y).all():
            raise ArithmeticError("independent DAN ODE failed")
        y = solution.y[:, -1].reshape(nb * nc, 6)
        states[:, i + 1] = y[:, :3].reshape(nb, nc, 3)
        areas[:, i] = y[:, 3:].reshape(nb, nc, 3)
        evaluations += solution.nfev

    # Two positive reference moments avoid subtracting nearly equal tail values.
    tail = np.zeros((nb, nc, 3))
    end = steps * DT
    for j in range(nb):
        for c in range(nc):
            d, baseline, v = states[j, -1, c]
            from_k = tail_quadrature([1, 0, d, baseline, 0])
            from_u = tail_quadrature([0, 1, d, baseline, 0])
            mr = (R + E) * from_k.positive_area
            me = from_u.negative_area
            tail[j, c] = [
                math.exp(-R * end) * (v + mr) / (R + E),
                math.exp(-E * end) * me,
                math.exp(-R * end) * mr,
            ]
    return DANReference(states, areas, tail, evaluations)


def kc_phase_products(kc_events, weighted_intervals, weighted_tail, boundaries):
    """All KC/channel P,N areas by finite phases plus full tail, before eta.

    Boundaries give onset and ordered finite phase ends in integer steps.
    No gain/mask/clipping/readout is involved; the caller maps anatomical edges.
    """
    kc = np.asarray(kc_events)
    intervals, tail = np.asarray(weighted_intervals), np.asarray(weighted_tail)
    if (kc.ndim != 2 or not np.isin(kc, [0, 1]).all()
            or intervals.ndim != 3 or intervals.shape[0] != kc.shape[0]
            or intervals.shape[-1] != 3 or tail.shape != intervals.shape[1:]
            or not np.isfinite(intervals).all() or not np.isfinite(tail).all()):
        raise ValueError("invalid KC raster or weighted integral shapes/values")
    boundaries = tuple(boundaries)
    if (len(boundaries) < 2 or any(type(x) is not int for x in boundaries)
            or boundaries[0] < 0 or boundaries[-1] != len(kc)
            or any(a >= b for a, b in zip(boundaries, boundaries[1:]))):
        raise ValueError("boundaries must give onset and strictly increasing phase ends")
    steps, nk = kc.shape
    nc = tail.shape[0]
    exp_r = np.exp(R * np.arange(steps) * DT)
    exp_e = np.exp(E * np.arange(steps) * DT)
    output = np.zeros((len(boundaries), nc, nk, 2))

    def map_moments(moments):
        wp = R * exp_r[:, None] * moments[:, :, 0]
        wn = R / (R - E) * (
            exp_e[:, None] * moments[:, :, 1] - exp_r[:, None] * moments[:, :, 2]
        )
        return np.stack((wp.T @ kc, wn.T @ kc), axis=-1)

    for phase, (start, end) in enumerate(zip(boundaries, boundaries[1:])):
        # Local reversed sums avoid subtraction of two large cumulative areas.
        suffix = np.concatenate((np.cumsum(intervals[start:end][::-1], axis=0)[::-1],
                                 np.zeros((1, nc, 3))), axis=0)
        lower = np.clip(np.arange(steps) - start, 0, end - start)
        output[phase] = map_moments(suffix[lower])
    output[-1] = map_moments(np.broadcast_to(tail, (steps, nc, 3)))
    return output


def kc_boundary_states(kc_events, boundary):
    """Direct convolution, prior events only; returns all KC [rate,eligibility]."""
    kc = np.asarray(kc_events)
    if kc.ndim != 2 or type(boundary) is not int or not 0 <= boundary <= len(kc):
        raise ValueError("invalid boundary/raster")
    lags = (boundary - np.arange(boundary)) * DT
    er, ee = np.exp(-R * lags), np.exp(-E * lags)
    return np.stack((R * er @ kc[:boundary], R / (R - E) * (ee - er) @ kc[:boundary]), axis=-1)
