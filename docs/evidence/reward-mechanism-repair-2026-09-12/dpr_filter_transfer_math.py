"""Analytic linear-response audit; this is not a BET36FLY plasticity rule.

The motivating source is Gkanias et al. 2022, doi:10.7554/eLife.75611.
These formulas describe unclipped, continuous, unit-area impulse filters.
They omit the source's signed MBON feedback and discrete weight update.
"""

from __future__ import annotations

import math


def _positive(value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("expected a positive finite value")
    return value


def pole_time_constant(step_seconds: float, tau_samples: float) -> float:
    """Match a discrete recurrence pole, without claiming full model parity."""
    step_seconds = _positive(step_seconds)
    tau_samples = _positive(tau_samples)
    if tau_samples <= 1:
        raise ValueError("a positive continuous pole requires tau_samples > 1")
    return -step_seconds / math.log1p(-1 / tau_samples)


def pair_area(dan_minus_kc_seconds: float, kc_tau: float,
              short_tau: float, long_tau: float) -> float:
    """Integral of K(t) * (D_long(t) - D_short(t)) for unit-area impulses.

    Positive lag means DAN occurs after KC. This is the derivative at eta=0
    of continuous DPR starting at resting weight, not its finite-eta outcome.
    """
    lag = float(dan_minus_kc_seconds)
    if not math.isfinite(lag):
        raise ValueError("lag must be finite")
    k, s, ell = map(_positive, (kc_tau, short_tau, long_tau))
    if lag >= 0:
        return math.exp(-lag / k) * (1 / (ell + k) - 1 / (s + k))
    return math.exp(lag / ell) / (ell + k) - math.exp(lag / s) / (s + k)


def backward_zero(kc_tau: float, short_tau: float, long_tau: float) -> float:
    """DAN lead duration at the unique pair-area sign reversal, if long>short."""
    k, s, ell = map(_positive, (kc_tau, short_tau, long_tau))
    if ell <= s:
        raise ValueError("requires long_tau > short_tau")
    return math.log1p((ell - s) / (s + k)) / (1 / s - 1 / ell)


def delta_area_until(seconds: float, short_tau: float, long_tau: float) -> float:
    """Finite integral after a unit-area DAN impulse at zero; full limit is 0."""
    t = float(seconds)
    s, ell = map(_positive, (short_tau, long_tau))
    if not math.isfinite(t) or t < 0:
        raise ValueError("seconds must be finite and nonnegative")
    return math.exp(-t / s) - math.exp(-t / ell)
