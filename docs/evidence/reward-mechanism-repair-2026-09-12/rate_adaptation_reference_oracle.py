"""Independent synthetic-only ODE/quadrature oracle; never reads neural artifacts.

State order: R_K, E_K, R_D, B_D, E_Dplus. Product areas are unscaled positive
magnitudes P=E_Dplus*R_K and N=E_K*max(R_D-B_D, 0). Gain change is C*(P-N).
This module imports no BET36FLY code and does not implement the writer's exact
finite-interval recurrence or any production gain loop.
"""

from dataclasses import dataclass
import math

import mpmath as mp
import numpy as np
from scipy.integrate import solve_ivp

R = 1.0 / 100.0
E = 1.0 / 500.0
C = 0.0005 * 0.96
STATE_ATOL = 2e-11
STATE_RTOL = 2e-10
AREA_ATOL = 2e-10
AREA_RTOL = 2e-10
DELTA_ATOL = 2e-12
DELTA_RTOL = 2e-10
ODE_RTOL = 2e-13
ODE_ATOL = 2e-15
MP_DPS = 70


@dataclass(frozen=True)
class OracleResult:
    state: np.ndarray
    positive_area: float
    negative_area: float
    method: str
    evaluations: int

    @property
    def signed_area(self):
        return self.positive_area - self.negative_area

    @property
    def gain_delta(self):
        return C * self.signed_area


def _state(values):
    x = np.asarray(values, dtype=np.float64)
    if x.shape != (5,) or not np.isfinite(x).all() or np.any(x < 0):
        raise ValueError("state must be five finite nonnegative scalars")
    return x


def finite_ode(state, duration_ms, *, kc_constant=0.0, dan_constant=0.0):
    """Numerically solve raw ODE and its P/N accumulators; no crossing formula.

    Nonzero constants are synthetic sustained-rate stimuli only. Real event
    intervals use the defaults after injecting impulses into the rate states.
    """
    x = _state(state)
    h = float(duration_ms)
    if not math.isfinite(h) or h < 0:
        raise ValueError("duration must be finite and nonnegative")
    for v in (kc_constant, dan_constant):
        if not math.isfinite(v) or v < 0:
            raise ValueError("constant inputs must be finite and nonnegative")
    if h == 0:
        return OracleResult(x.copy(), 0.0, 0.0, "DOP853", 0)

    def rhs(_, y):
        k, u, d, baseline, v = y[:5]
        rectified = max(d - baseline, 0.0)
        return [
            R * (kc_constant - k), k - E * u,
            R * (dan_constant - d), E * (d - baseline),
            rectified - E * v, v * k, u * rectified,
        ]

    result = solve_ivp(
        rhs, (0.0, h), np.r_[x, 0.0, 0.0], method="DOP853",
        rtol=ODE_RTOL, atol=ODE_ATOL, max_step=min(0.5, h / 8.0),
    )
    if not result.success or not np.isfinite(result.y).all():
        raise ArithmeticError(f"independent ODE failed: {result.message}")
    final = result.y[:, -1]
    return OracleResult(
        final[:5], float(final[5]), float(final[6]), "DOP853", result.nfev,
    )


def tail_quadrature(state):
    """Full infinite-tail P/N via independent high-precision Laplace quadrature.

    The root is numerically bisected, not evaluated with the writer's log1p
    formula. No finite-horizon truncation replaces the infinite tail.
    """
    x = _state(state)
    with mp.workdps(MP_DPS):
        k, u, d, baseline, v = map(lambda value: mp.mpf(float(value)), x)
        r, e = mp.mpf(1) / 100, mp.mpf(1) / 500
        delta, p = r - e, r + e

        def signed_signal(t):
            rd = d * mp.exp(-r * t)
            bd = baseline * mp.exp(-e * t)
            bd += e * d * (mp.exp(-e * t) - mp.exp(-r * t)) / delta
            return rd - bd

        evaluations = 0
        if d <= baseline:
            mr = me = mp.mpf(0)
        else:
            lower, upper = mp.mpf(0), mp.log(r / e) / delta + 1
            if signed_signal(upper) > 0:
                raise ArithmeticError("nonnegative-state crossing bracket failed")
            for _ in range(256):
                middle = (lower + upper) / 2
                if middle == lower or middle == upper:
                    break
                if signed_signal(middle) > 0:
                    lower = middle
                else:
                    upper = middle
                evaluations += 1
            crossing = (lower + upper) / 2

            def moment(lam):
                def integrand(t):
                    return mp.exp(-lam * t) * max(signed_signal(t), mp.mpf(0))
                return mp.quad(integrand, [0, crossing / 2, crossing])

            mr, me = moment(r), moment(e)
        positive = k * v / p + k * mr / p
        negative = u * me + k * (me - mr) / delta
        if positive < 0 or negative < 0:
            raise ArithmeticError("nonnegative tail integral became negative")
        return OracleResult(
            np.zeros(5), float(positive), float(negative),
            "70-digit Laplace-moment quadrature", evaluations,
        )


def zero_start_constant_states(kc_rate, dan_rate, duration_ms):
    """Independent closed-form constant-input states for synthetic ODE checks."""
    h = float(duration_ms)
    if min(kc_rate, dan_rate, h) < 0 or not all(
        math.isfinite(x) for x in (kc_rate, dan_rate, h)
    ):
        raise ValueError("constant-state inputs must be finite and nonnegative")
    with mp.workdps(MP_DPS):
        kappa, rho, t = map(mp.mpf, (kc_rate, dan_rate, h))
        r, e = mp.mpf(1) / 100, mp.mpf(1) / 500
        delta = r - e
        x, y = mp.exp(-r * t), mp.exp(-e * t)
        k = kappa * (1 - x)
        d = rho * (1 - x)
        baseline = rho * (1 - r * y / delta + e * x / delta)
        u = kappa * ((1 - y) / e - (y - x) / delta)
        v = rho * r / delta * (t * y - (y - x) / delta)
        return np.array(list(map(float, (k, u, d, baseline, v))))


def tail_gain_from_ode_split(state, split_ms):
    """Independent ODE prefix plus quadrature remainder, never writer recurrence."""
    prefix = finite_ode(state, split_ms)
    remainder = tail_quadrature(prefix.state)
    return OracleResult(
        np.zeros(5), prefix.positive_area + remainder.positive_area,
        prefix.negative_area + remainder.negative_area,
        "DOP853 prefix plus infinite Laplace quadrature", prefix.evaluations,
    )
