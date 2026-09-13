"""Independent 70-digit solution of Aso2019 phenomenological equations 1-3.

No author executable, production solver, capture or fitted-outcome import.
The four entries are d,n,D,N; time is seconds. Source-null branches must be
absent on entry. Quiet continuation preserves latent memory.
"""

import math

import mpmath as mp
import numpy as np


def _number(value):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValueError("A finite real number is required, not a Boolean alias")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("A finite real number is required")
    return result


def _state(state, da_enabled=True, no_enabled=True):
    if type(da_enabled) is not bool or type(no_enabled) is not bool:
        raise ValueError("Branch flags must be actual bool values")
    if len(state) != 4:
        raise ValueError("State order is d,n,D,N")
    result = [_number(v) for v in state]
    if any(not 0 <= v <= 1 for v in result):
        raise ValueError("Each state must lie in [0,1]")
    if (not da_enabled and (result[0] != 0 or result[2] != 0)) or (
        not no_enabled and (result[1] != 0 or result[3] != 0)
    ):
        raise ValueError("Null branches must be absent initially; midstream erasure is invalid")
    return result


def _parameters(parameters):
    names = {"A_D", "A_N", "B_D", "B_N", "tau_D", "tau_N"}
    if parameters is None:
        return dict(
            A_D=mp.mpf("4.3") / 60,
            A_N=mp.mpf(".96") / 60,
            B_D=mp.mpf(".26") / 60,
            B_N=mp.mpf(".16") / 60,
            tau_D=mp.mpf(30),
            tau_N=mp.mpf(600),
        )
    if type(parameters) is not dict or set(parameters) != names:
        raise ValueError("Exact source parameter field inventory required")
    result = {k: mp.mpf(str(_number(v))) for k, v in parameters.items()}
    if any(v <= 0 if k.startswith("tau") else v < 0 for k, v in result.items()):
        raise ValueError("Positive tau and nonnegative A/B required")
    return result


def reference_advance(
    state, seconds, kc_active, dan_active, *, parameters=None, da_enabled=True, no_enabled=True
):
    """Closed form at 70 digits, rounded once to F64 at the returned boundary."""
    initial = _state(state, da_enabled, no_enabled)
    if type(kc_active) is not bool or type(dan_active) is not bool:
        raise ValueError("Activity flags must be actual bool values")
    duration = _number(seconds)
    if duration < 0:
        raise ValueError("Nonnegative duration required")
    with mp.workdps(70):
        params = _parameters(parameters)
        t = mp.mpf(duration)
        result = [mp.mpf(v) for v in initial]
        for j, (name, enabled) in enumerate([("D", da_enabled), ("N", no_enabled)]):
            if not enabled:
                continue
            x, y = mp.mpf(initial[j]), mp.mpf(initial[j + 2])
            rate = (
                params["A_" + name]
                if dan_active and kc_active
                else params["B_" + name]
                if dan_active
                else mp.mpf(0)
            )
            target = mp.mpf(1 if dan_active and kc_active else 0)
            mu = 1 / params["tau_" + name]
            el, em = mp.exp(-rate * t), mp.exp(-mu * t)
            integral = mu * t * em if rate == mu else mu * (el - em) / (mu - rate)
            result[j] = target + (x - target) * el
            result[j + 2] = target + (y - target) * em + (x - target) * integral
        final = np.array([float(v) for v in result], dtype=np.float64)
    if not np.isfinite(final).all() or np.any(final < 0) or np.any(final > 1):
        raise ArithmeticError("Reference left the invariant state domain; no hidden clamp")
    return final


def quiet_limit(state, *, da_enabled=True, no_enabled=True):
    d, n, _, _ = _state(state, da_enabled, no_enabled)
    return np.array([d, n, d, n], dtype=np.float64)


def weight(state):
    _, _, D, N = _state(state)
    return (1 - D) * (1 + N)
