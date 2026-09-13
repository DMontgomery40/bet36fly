"""Exact float32 publication/untaught-guard arithmetic, synthetic preparation.

No I/O, simulator, history selection or scientific threshold adjustment.
Intervals are conditional on the caller's declared numerical enclosure; the
subsequent rational arithmetic and rounding decisions are exact.
"""

from fractions import Fraction
import itertools

import numpy as np

TICKS = 2**24
LOW, HIGH = Fraction(1, 2), Fraction(3, 2)


def _integers(values):
    values = tuple(values)
    if len(values) != 8 or any(type(v) is not int for v in values):
        raise ValueError("Exactly eight Python integer totals required")
    return values


def point_guard(totals):
    """Exact |mean| <= 0.5*sample_SD; equality is a pass."""
    totals = _integers(totals)
    n = len(totals)
    summed = sum(totals)
    squares = sum(t * t for t in totals)
    return (5 * n - 4) * summed * summed <= n * n * squares


def round_f32_ticks(value):
    """Exact nearest/ties-to-even F32 quantization on [0.5,1.5].

    Returns integer ticks of 2^-24 without an intermediate rounded double.
    Below 1 every tick is representable; from 1 upward only even ticks are.
    """
    value = Fraction(value)
    if not LOW <= value <= HIGH:
        raise ValueError("Gain outside exact continuous bounds")
    step = 1 if value < 1 else 2
    scaled = value * TICKS / step
    floor, remainder = divmod(scaled.numerator, scaled.denominator)
    comparison = 2 * remainder - scaled.denominator
    if comparison > 0 or comparison == 0 and floor % 2:
        floor += 1
    return int(step * floor)


def _initial_ticks(initial):
    initial = float(initial)
    if not np.isfinite(initial) or not 0.5 <= initial <= 1.5:
        raise ValueError("Initial gain must be finite and inside bounds")
    if float(np.float32(initial)) != initial:
        raise ValueError("Initial checkpoint must be exactly float32 representable")
    return int(Fraction(initial) * TICKS)


def _shape(array):
    if array.ndim != 2 or array.shape[0] != 8 or not array.shape[1]:
        raise ValueError("Eight trials and a nonempty eligible-edge axis required")


def f32_trial_totals(gains, *, initial=1.0):
    """Exact per-trial sums of selected F32 gain deltas in common integer ticks."""
    gains = np.asarray(gains)
    _shape(gains)
    if (
        gains.dtype != np.dtype(np.float32)
        or not np.isfinite(gains).all()
        or (gains < 0.5).any()
        or (gains > 1.5).any()
    ):
        raise ValueError("Finite float32 published gains inside [0.5,1.5] required")
    baseline = _initial_ticks(initial)
    ticks = (gains.astype(np.float64) * TICKS).astype(np.int64)
    return tuple(sum(int(x) - baseline for x in row) for row in ticks)


def allowance_totals(double_gains, allowance, *, initial=1.0):
    """Conservative integer total box from exact center +/- declared allowance.

    Centers and allowances are interpreted as their exact stored binary values.
    Endpoint addition/subtraction and F32 quantization use Fraction arithmetic.
    Continuous [0.5,1.5] is intersected, without clamping the computed center.
    A scalar zero allowance permits exact inactive/checkpoint singleton cases.
    """
    values = np.asarray(double_gains)
    _shape(values)
    errors = np.asarray(allowance)
    if values.dtype.kind != "f" or errors.dtype.kind not in "fiu":
        raise ValueError("Floating centers and numeric nonnegative allowances required")
    if not np.isfinite(values).all() or not np.isfinite(errors).all() or (errors < 0).any():
        raise ValueError("Finite centers and finite nonnegative allowances required")
    try:
        errors = np.broadcast_to(errors, values.shape)
    except ValueError as exc:
        raise ValueError("Allowance does not broadcast to the gain array") from exc
    baseline = _initial_ticks(initial)
    lows, highs = [], []
    for row, error_row in zip(values, errors):
        lo = hi = 0
        for center, error in zip(row, error_row):
            c = Fraction(*center.as_integer_ratio())
            radius = (
                Fraction(int(error)) if errors.dtype.kind in "iu" else Fraction(*error.as_integer_ratio())
            )
            lower, upper = max(LOW, c - radius), min(HIGH, c + radius)
            if lower > upper:
                raise ValueError("Declared gain enclosure has no overlap with continuous bounds")
            lo += round_f32_ticks(lower) - baseline
            hi += round_f32_ticks(upper) - baseline
        lows.append(lo)
        highs.append(hi)
    return tuple(lows), tuple(highs)


def _variance(values):
    n = len(values)
    return (sum(x * x for x in values) - Fraction(sum(values) ** 2, n)) / (n - 1)


def _minimum_variance(lower, upper):
    """Exact convex distance from a box to the line of constant vectors."""
    boundaries = sorted(set(lower + upper))
    candidates = {Fraction(x) for x in boundaries}
    for left, right in zip(boundaries, boundaries[1:]):
        midpoint = Fraction(left + right, 2)
        active = [Fraction(h) for h in upper if h < midpoint]
        active += [Fraction(lo) for lo in lower if lo > midpoint]
        if active:
            root = sum(active) / len(active)
            if left <= root <= right:
                candidates.add(root)
        else:
            candidates.add(midpoint)
    best = None
    for center in candidates:
        witness = tuple(max(Fraction(lo), min(Fraction(h), center)) for lo, h in zip(lower, upper))
        distance = sum((x - center) ** 2 for x in witness)
        entry = distance, center, witness
        if best is None or entry < best:
            best = entry
    _, center, witness = best
    # Global optimum obeys center == mean(witness); assert the exact certificate.
    if center != sum(witness) / len(witness):
        raise ArithmeticError("Box-to-constant-line optimum failed its exact mean certificate")
    return _variance(witness), witness


def classify_box(lower, upper):
    """Sufficient universal pass/fail bounds; all other boxes are inconclusive.

    The box may contain unattainable continuous totals; enlarging the actual
    integer set is conservative. No particular scientific weights are chosen.
    """
    lower, upper = _integers(lower), _integers(upper)
    if any(lo > h for lo, h in zip(lower, upper)):
        raise ValueError("Ordered per-trial integer intervals required")
    mean_low, mean_high = Fraction(sum(lower), 8), Fraction(sum(upper), 8)
    maximum_mean_squared = max(mean_low * mean_low, mean_high * mean_high)
    minimum_mean_squared = (
        Fraction(0) if mean_low <= 0 <= mean_high else min(mean_low * mean_low, mean_high * mean_high)
    )
    minimum_variance, witness = _minimum_variance(lower, upper)
    maximum_variance = max(_variance(v) for v in itertools.product(*zip(lower, upper)))
    if 4 * maximum_mean_squared <= minimum_variance:
        classification = "all_pass"
    elif 4 * minimum_mean_squared > maximum_variance:
        classification = "all_fail"
    else:
        classification = "inconclusive"
    return dict(
        classification=classification,
        mean_interval=(mean_low, mean_high),
        minimum_mean_squared=minimum_mean_squared,
        maximum_mean_squared=maximum_mean_squared,
        minimum_variance=minimum_variance,
        maximum_variance=maximum_variance,
        minimum_variance_witness=witness,
        scope="Conservative universal classification conditional on the declared numerical enclosure; scientific guard unchanged",
    )
