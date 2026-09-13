"""Output-only numerical preparation; no file I/O, simulator import or execution CLI.

The fixed engineered equation uses changing double gains at every RK substage.
Adaptive RK4 step doubling is independent of the DOP853/high-precision oracle.
Error estimates are numerical diagnostics, not rigorous interval bounds.
"""

import math

import numpy as np


ETA, NORMALIZATION, RATE, ELIGIBILITY = 0.0005, 0.96, 0.01, 0.002
DT = 0.2
ABS_TOL, REL_INCREMENT_TOL = 2e-15, 2e-14
MAX_ATTEMPTS = 20000


def _numeric(value, name):
    raw = np.asarray(value)
    if raw.dtype.kind not in "fiu" or raw.ndim > 1:
        raise ValueError(f"{name} must be a scalar or vector of real numbers")
    result = raw.astype(np.float64)
    if not np.isfinite(result).all():
        raise ValueError(f"{name} must be finite")
    return result


class _OutsideTrial(ArithmeticError):
    pass


def integrate_products(products, duration, initial_gain, *, max_step=DT, guard=None):
    """Vectorized finite-interval integration, retaining eta-scaled signed areas.

    The callable returns continuous nonnegative P,N including normalization0.96.
    No gain is frozen within a substep, clipped or published by this function.
    """
    gain = _numeric(initial_gain, "Initial gain")
    if np.any(gain < 0.5) or np.any(gain > 1.5) or gain.size == 0:
        raise ValueError("Initial gains must be within inclusive fixed bounds")
    if (
        isinstance(duration, (bool, str))
        or not np.isscalar(duration)
        or not math.isfinite(duration)
        or duration < 0
        or isinstance(max_step, (bool, str))
        or not np.isscalar(max_step)
        or not math.isfinite(max_step)
        or max_step <= 0
    ):
        raise ValueError("Finite nonnegative duration and positive numerical step required")
    state = np.stack((gain.copy(), np.zeros_like(gain), np.zeros_like(gain)))
    estimate = np.zeros_like(state)

    def rhs(t, value):
        p, n = products(t)
        p, n = np.broadcast_arrays(_numeric(p, "Positive product"), _numeric(n, "Negative product"))
        try:
            p, n = np.broadcast_to(p, gain.shape), np.broadcast_to(n, gain.shape)
        except ValueError as exc:
            raise ValueError("Products must broadcast to exactly the gain shape") from exc
        if np.any(p < 0) or np.any(n < 0):
            raise ValueError("Products must remain nonnegative")
        if np.any(value[0] < 0.5) or np.any(value[0] > 1.5):
            raise _OutsideTrial("Numerical stage left continuous gain bounds")
        plus = 2 * ETA * p * (1.5 - value[0])
        minus = -2 * ETA * n * (value[0] - 0.5)
        result = np.stack((plus + minus, plus, minus))
        if not np.isfinite(result).all():
            raise ArithmeticError("Nonfinite weighted derivative")
        return result

    def rk4(t, value, h):
        a = rhs(t, value)
        b = rhs(t + h / 2, value + (h / 2) * a)
        c = rhs(t + h / 2, value + (h / 2) * b)
        d = rhs(t + h, value + h * c)
        return value + (h / 6) * (a + 2 * b + 2 * c + d)

    rhs(0.0, state)
    now, step, accepted, attempts = 0.0, min(float(max_step), float(duration)), 0, 0
    while now < duration:
        attempts += 1
        if attempts > MAX_ATTEMPTS:
            raise ArithmeticError("Numerical integration work limit exceeded")
        if guard is not None and attempts % 50 == 1:
            guard()
        h = min(step, duration - now)
        if now + h == now:
            raise ArithmeticError("Numerical refinement cannot advance time")
        try:
            coarse = rk4(now, state, h)
            half = rk4(now, state, h / 2)
            fine = rk4(now + h / 2, half, h / 2)
            difference = (fine - coarse) / 15
            proposed = fine + difference
            error = np.abs(difference)
            tolerance = ABS_TOL + REL_INCREMENT_TOL * np.maximum(np.abs(proposed - state), 1e-3)
            ratio = float(np.max(error / tolerance))
            outside = (
                np.any(proposed[0] < 0.5)
                or np.any(proposed[0] > 1.5)
                or np.any(proposed[1] < state[1])
                or np.any(proposed[2] > state[2])
            )
        except _OutsideTrial:
            outside, ratio = True, math.inf
        if outside or ratio > 1:
            step = h * 0.5
            continue
        state = proposed
        estimate += error
        now += h
        accepted += 1
        step = min(float(max_step), h * (2 if ratio < 0.03 else 1))
    return dict(
        gain=state[0],
        positive=state[1],
        negative=state[2],
        estimated_error=estimate,
        accepted_substeps=accepted,
        attempted_substeps=attempts,
    )


def interval(rk, ek, rd, ed, gain, duration, *, guard=None):
    """Analytic signal evolution with continuously changing gain; infinity is a full tail."""
    gain = _numeric(gain, "Gain")
    signals = [_numeric(v, "Signal") for v in (rk, ek, rd, ed)]
    if any(np.any(v < 0) for v in signals):
        raise ValueError("Signal states must be nonnegative")
    try:
        rk, ek, rd, ed = [np.broadcast_to(v, gain.shape) for v in signals]
    except ValueError as exc:
        raise ValueError("Signals must broadcast to exactly the gain shape") from exc
    if isinstance(duration, (bool, str)) or not np.isscalar(duration) or math.isnan(duration) or duration < 0:
        raise ValueError("Interval must be nonnegative or positive infinity")

    def states(t):
        ar, ae = math.exp(-RATE * t), math.exp(-ELIGIBILITY * t)
        coupling = -math.expm1(-(RATE - ELIGIBILITY) * t) / (RATE - ELIGIBILITY)
        return rk * ar, ae * (ek + rk * coupling), rd * ar, ae * (ed + rd * coupling)

    if math.isinf(duration):

        def products(z):
            u = 1.0 - z
            common = 125 * rk * rd * (u**5) * (1 - u) * (1 + u + u**2 + u**3)
            return (
                500 * NORMALIZATION * (rk * ed * u**5 + common),
                500 * NORMALIZATION * (rd * ek * u**5 + common),
            )

        result = integrate_products(products, 1.0, gain, max_step=0.02, guard=guard)
        result["state"] = tuple(np.zeros_like(gain) for _ in range(4))
    else:

        def products(t):
            kr, ke, dr, de = states(t)
            return NORMALIZATION * de * kr, NORMALIZATION * ke * dr

        result = integrate_products(products, float(duration), gain, guard=guard)
        result["state"] = states(float(duration))
    return result


def shadow(kc, dan, pk, pc, dc, mask, groups, *, initial=None, learning=True, guard=None):
    """Pure fixed 400ms shadow, cold signal admission at100ms, no spike feedback.

    Only a float32 gain checkpoint enters/leaves calls. Gain stays double inside
    the call; 1500 full electrical publications and one full-tail publication
    cannot feed rounding back into gain or signals. No files are read/written.
    """
    kc, dan = np.asarray(kc), np.asarray(dan)
    if (
        kc.ndim != 2
        or dan.ndim != 2
        or kc.shape[0] != 2000
        or dan.shape[0] != 2000
        or min(kc.shape[1], dan.shape[1]) < 1
        or kc.dtype.kind not in "biu"
        or dan.dtype.kind not in "biu"
        or not np.isin(kc, [0, 1]).all()
        or not np.isin(dan, [0, 1]).all()
    ):
        raise ValueError("Exactly2000 binary KC/DAN time rows required")
    pk, pc, dc, mask, groups = [np.asarray(v) for v in (pk, pc, dc, mask, groups)]
    if (
        dc.shape != (dan.shape[1],)
        or dc.dtype.kind not in "iu"
        or np.any(dc < 0)
        or set(dc.tolist()) not in ({0}, {0, 1})
    ):
        raise ValueError("Every fixed contiguous DAN channel must be represented")
    ne, nc = pk.size, int(dc.max()) + 1
    if (
        ne == 0
        or any(v.shape != (ne,) or v.dtype.kind not in "iu" for v in (pk, pc, groups))
        or np.any(pk < 0)
        or np.any(pk >= kc.shape[1])
        or np.any(pc < 0)
        or np.any(pc >= nc)
        or np.any(groups < 0)
        or np.any(groups >= 8)
        or np.any(groups // 4 != pc)
        or mask.shape != (ne,)
        or mask.dtype.kind not in "biu"
        or not np.isin(mask, [0, 1]).all()
        or type(learning) is not bool
    ):
        raise ValueError("Invalid edge/group/channel/mask/learning mapping")
    checkpoint = np.ones(ne, np.float32) if initial is None else np.asarray(initial)
    if (
        checkpoint.shape != (ne,)
        or checkpoint.dtype != np.dtype(np.float32)
        or not np.isfinite(checkpoint).all()
        or np.any(checkpoint < 0.5)
        or np.any(checkpoint > 1.5)
    ):
        raise ValueError("Checkpoint must be a finite bounded float32 gain vector")
    published, double = checkpoint.copy(), checkpoint.astype(np.float64)
    fields = (
        "positive",
        "negative",
        "attempted",
        "double_applied",
        "published_applied",
        "bound_low",
        "bound_high",
        "rounding_ambiguous",
    )
    phases = np.zeros((4, ne, len(fields)))
    endpoints = np.tile(double, (4, 1))
    error = np.zeros((3, ne))
    publications = np.zeros(ne, np.int64)
    conditional_bounds = np.zeros((2, ne), np.int64)
    active = np.flatnonzero(mask.astype(bool) & learning)
    accepted = attempts = 0
    if active.size:
        rk, ek, rd, ed = [np.zeros(active.size) for _ in range(4)]
        mean_dan = np.column_stack(
            [dan[:, dc == c].sum(axis=1, dtype=float) / np.count_nonzero(dc == c) for c in range(nc)]
        )

        def advance(duration, phase):
            nonlocal rk, ek, rd, ed, accepted, attempts
            before, old = double[active].copy(), published[active].copy()
            value = interval(rk, ek, rd, ed, before, duration, guard=guard)
            rk, ek, rd, ed = value["state"]
            double[active] = value["gain"]
            published[active] = value["gain"].astype(np.float32)
            # Conditional comparison allowance, not a hidden clamp or formal error bound.
            lower = np.maximum(np.nextafter(value["gain"] - 1e-11, -np.inf), 0.5)
            upper = np.minimum(np.nextafter(value["gain"] + 1e-11, np.inf), 1.5)
            ambiguous = lower.astype(np.float32) != upper.astype(np.float32)
            conditional_bounds[0, active] += (lower <= 0.5) | (lower.astype(np.float32) <= 0.5)
            conditional_bounds[1, active] += (upper >= 1.5) | (upper.astype(np.float32) >= 1.5)
            plus, minus = value["positive"], value["negative"]
            phases[phase, active] += np.column_stack(
                (
                    plus,
                    minus,
                    plus + minus,
                    value["gain"] - before,
                    published[active].astype(float) - old.astype(float),
                    (value["gain"] <= 0.5) | (published[active] <= 0.5),
                    (value["gain"] >= 1.5) | (published[active] >= 1.5),
                    ambiguous,
                )
            )
            error[:, active] += value["estimated_error"]
            publications[active] += 1
            accepted += value["accepted_substeps"]
            attempts += value["attempted_substeps"]

        for step in range(500, 2000):
            if guard is not None and step % 50 == 0:
                guard()
            rk += kc[step, pk[active]] * RATE
            rd += mean_dan[step, pc[active]] * RATE
            phase = 0 if step < 650 else 1 if step < 1500 else 2
            advance(DT, phase)
            if step in (649, 1499, 1999):
                endpoints[phase] = double
        advance(math.inf, 3)
        endpoints[3] = double
    grouped = np.zeros((4, 8, len(fields)))
    for phase in range(4):
        np.add.at(grouped[phase], groups, phases[phase])
    allowance = np.zeros(ne)
    allowance[active] = 1e-11
    return dict(
        gains=published,
        double_gains=double,
        electrical_gains=endpoints[2].astype(np.float32),
        electrical_double_gains=endpoints[2],
        phase_end_double_gains=endpoints,
        gain_lower=np.where(
            allowance > 0, np.maximum(np.nextafter(double - allowance, -np.inf), 0.5), double
        ),
        gain_upper=np.where(allowance > 0, np.minimum(np.nextafter(double + allowance, np.inf), 1.5), double),
        gain_interval_basis="Conditional fixed1e-11 numerical allowance; no formal interval proof",
        phases=phases,
        fields=fields,
        grouped=grouped,
        publication_counts=publications,
        conditional_bound_counts=conditional_bounds,
        estimated_integration_error=error,
        accepted_substeps=accepted,
        attempted_substeps=attempts,
        rounding_ambiguous=phases[:, :, 7].sum(axis=0).astype(np.int64),
    )
