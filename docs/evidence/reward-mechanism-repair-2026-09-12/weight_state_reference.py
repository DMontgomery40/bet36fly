"""Independent scalar reference for the fixed weight-state engineering law.

No file I/O, simulator imports, native calls or saved-history runner. The ODE
method rebuilds rates/eligibilities by impulse superposition. Its entire tail
is mapped to a finite interval. The second method uses 70-digit integrating-
factor quadrature and independently rebuilt exponential coefficients.
"""

import math

import mpmath as mp
import numpy as np
from scipy.integrate import solve_ivp

GAIN_ATOL = 1e-11
WEIGHTED_AREA_ATOL = 2e-11
ODE_RTOL = 1e-13
ODE_ATOL = 2e-15
ETA = 0.0005
NORM = 0.96


def _initial(value):
    value = float(value)
    if not math.isfinite(value) or not 0.5 <= value <= 1.5:
        raise ValueError("Initial gain must be finite and in [0.5, 1.5]")
    return value


def _solve(products, start, end, initial_gain, max_step):
    initial_gain = _initial(initial_gain)
    if not np.isfinite([start, end]).all() or end < start:
        raise ValueError("Finite ordered integration interval required")

    def rhs(t, state):
        p, n = map(float, products(t))
        if not np.isfinite([p, n]).all() or min(p, n) < 0:
            raise ValueError("Product drives must be finite and nonnegative")
        plus = 2 * ETA * p * (1.5 - state[0])
        minus = -2 * ETA * n * (state[0] - 0.5)
        if not np.isfinite([plus, minus]).all():
            raise ValueError("Nonfinite weighted drive")
        return [plus + minus, plus, minus]

    rhs(start, [initial_gain, 0.0, 0.0])
    if start == end:
        return dict(gain=initial_gain, positive=0.0, negative=0.0)
    solution = solve_ivp(
        rhs,
        (start, end),
        [initial_gain, 0.0, 0.0],
        method="DOP853",
        rtol=ODE_RTOL,
        atol=ODE_ATOL,
        max_step=min(max_step, (end - start) / 8),
    )
    if not solution.success or not np.isfinite(solution.y).all():
        raise RuntimeError("Independent reference ODE did not complete")
    gain, positive, negative = map(float, solution.y[:, -1])
    if not 0.5 - GAIN_ATOL <= gain <= 1.5 + GAIN_ATOL:
        raise ArithmeticError("Reference violates continuous gain bounds")
    return dict(gain=gain, positive=positive, negative=negative)


def integrate_products(products, span, initial_gain):
    """Integrate supplied nonnegative P,N continuously, retaining signed areas."""
    start, end = map(float, span)
    return _solve(products, start, end, initial_gain, 0.5)


def _train(times, weights, end):
    raw = np.asarray(times)
    if raw.ndim != 1 or raw.dtype.kind not in "biuf":
        raise ValueError("One-dimensional numeric event times required")
    t = raw.astype(float)
    raw_weights = np.ones(len(t)) if weights is None else np.asarray(weights)
    if raw_weights.shape != t.shape or raw_weights.dtype.kind not in "biuf":
        raise ValueError("One finite nonnegative mass per event required")
    w = raw_weights.astype(float)
    if (
        not np.isfinite(t).all()
        or not np.isfinite(w).all()
        or (t < 0).any()
        or (t > end).any()
        or (w < 0).any()
    ):
        raise ValueError("Events must be finite, nonnegative and inside the electrical interval")
    return t, w


def _inputs(kc_times, dan_times, kc_weights, dan_weights, end_ms, initial_gain):
    end = float(end_ms)
    if not math.isfinite(end) or end < 0:
        raise ValueError("Finite nonnegative electrical endpoint required")
    initial = _initial(initial_gain)
    return _train(kc_times, kc_weights, end), _train(dan_times, dan_weights, end), end, initial


def _signals(train, now):
    times, weights = train
    present = times <= now
    age, mass = now - times[present], weights[present]
    rate = float(np.sum(mass * np.exp(-age / 100) / 100))
    eligibility = float(np.sum(mass * 1.25 * np.exp(-age / 500) * -np.expm1(-age * 0.008)))
    return rate, eligibility


def _products(kc, dan, now):
    rk, ek = _signals(kc, now)
    rd, ed = _signals(dan, now)
    return NORM * ed * rk, NORM * ek * rd


def event_reference(
    kc_times, dan_times, *, end_ms, initial_gain=1.0, kc_weights=None, dan_weights=None, full_tail=True
):
    """Scalar event-history reference, no cold-onset, mask or circuit wrapper.

    Callers pass only events at/after their chosen history boundary with times
    measured from that boundary. Events exactly at end_ms affect the tail.
    Gains are double during integration; gain32 is only final publication.
    """
    if type(full_tail) is not bool:
        raise ValueError("Explicit boolean full_tail required")
    kc, dan, end, gain = _inputs(kc_times, dan_times, kc_weights, dan_weights, end_ms, initial_gain)
    knots = sorted({0.0, end, *kc[0], *dan[0]})
    positive = negative = 0.0
    for left, right in zip(knots, knots[1:]):
        # Exclude a new impulse at the right boundary from left-limit RHS calls.
        k = tuple(v[kc[0] < right] for v in kc)
        d = tuple(v[dan[0] < right] for v in dan)
        part = integrate_products(lambda t: _products(k, d, t), (left, right), gain)
        gain = part["gain"]
        positive += part["positive"]
        negative += part["negative"]
    electrical = dict(gain=gain, positive=positive, negative=negative)
    tail = dict(gain=gain, positive=0.0, negative=0.0)
    if full_tail:
        rk, ek = _signals(kc, end)
        rd, ed = _signals(dan, end)

        def transformed_products(z):
            # u=exp(-elapsed/500), z=1-u. P*dt/dz is finite at u=0.
            u = 1 - float(z)
            if u == 0:
                return 0.0, 0.0
            u5 = u**5
            difference = u5 * -math.expm1(4 * math.log(u))
            p_over_u = NORM * rk * (ed * u5 + 125 * rd * difference)
            n_over_u = NORM * rd * (ek * u5 + 125 * rk * difference)
            return 500 * p_over_u, 500 * n_over_u

        tail = _solve(transformed_products, 0.0, 1.0, gain, 0.02)
        gain = tail["gain"]
    return dict(
        gain=gain,
        gain32=np.float32(gain),
        positive=positive + tail["positive"],
        negative=negative + tail["negative"],
        electrical_gain=electrical["gain"],
        electrical_positive=positive,
        electrical_negative=negative,
        tail_positive=tail["positive"],
        tail_negative=tail["negative"],
        tail_gain_change=gain - electrical["gain"],
    )


def mp_event_gain(
    kc_times, dan_times, *, end_ms, initial_gain=1.0, kc_weights=None, dan_weights=None, full_tail=True
):
    """Independent 70-digit integrating-factor gain oracle, including infinity.

    It does not call the double signal, product, tail or ODE implementations.
    Only input validation is shared. Return an mp.mpf containing 70-digit work.
    """
    if type(full_tail) is not bool:
        raise ValueError("Explicit boolean full_tail required")
    kc, dan, end, initial = _inputs(kc_times, dan_times, kc_weights, dan_weights, end_ms, initial_gain)
    with mp.workdps(70):
        eta, norm = mp.mpf("0.0005"), mp.mpf("0.96")
        lam, mu = mp.mpf(3) / 250, mp.mpf(1) / 50
        k = [(mp.mpf(float(t)), mp.mpf(float(w))) for t, w in zip(*kc)]
        d = [(mp.mpf(float(t)), mp.mpf(float(w))) for t, w in zip(*dan)]
        endpoint = mp.mpf(end)
        knots = sorted({mp.mpf(0), endpoint, *[t for t, w in k + d]})
        intervals = list(zip(knots, knots[1:]))
        if full_tail:
            intervals.append((endpoint, mp.inf))
        x = mp.mpf(initial) - 1
        for left, right in intervals:

            def coefficients(train):
                active = [(left - t, w) for t, w in train if t <= left]
                rate = sum((w * mp.exp(-age / 100) / 100 for age, w in active), mp.mpf(0))
                slow = sum((mp.mpf(5) / 4 * w * mp.exp(-age / 500) for age, w in active), mp.mpf(0))
                return rate, slow

            rk, sk = coefficients(k)
            rd, sd = coefficients(d)
            sum_slow = norm * (rk * sd + rd * sk)
            difference_slow = norm * (rk * sd - rd * sk)
            common = norm * 125 * rk * rd
            z = mp.mpf(0) if right == mp.inf else mp.exp(-lam * (right - left))
            power = mu / lam

            def remaining(u):
                return sum_slow * (u - z) / lam - 2 * common * (u**power - z**power) / mu

            damp = mp.exp(-2 * eta * remaining(mp.mpf(1)))
            if difference_slow:
                integral = mp.quad(lambda u: mp.exp(-2 * eta * remaining(u)), [z, 1])
                x = x * damp + eta * difference_slow / lam * integral
            else:
                x *= damp
        return +(1 + x)
