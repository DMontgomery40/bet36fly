"""Independent saved-shadow audit. No producer bridge or rejected model imports.

Only separately authorized CLI execution may read actual saved histories.
Pure functions use supplied arrays, direct impulse superposition and the
previously reviewed complete pair kernel, with fixed numerical comparisons.
"""

from fractions import Fraction
from functools import lru_cache
import math

import numpy as np
from scipy.sparse import csr_matrix

GAIN_ALLOWANCE = 1e-11
AREA_ATOL, AREA_RTOL = 2e-11, 1e-12


@lru_cache(maxsize=4)
def impulse_matrices(length):
    """Direct post-event states including one final quiet boundary."""
    age = (np.arange(length + 1)[:, None] - np.arange(length)[None, :]) * .2
    admitted = age >= 0
    age = np.maximum(age, 0)
    rate = np.where(admitted, np.exp(-age / 100) / 100, 0.)
    eligibility = np.where(admitted, 1.25 * np.exp(-age / 500) * -np.expm1(-.008 * age), 0.)
    return rate, eligibility


@lru_cache(maxsize=4)
def pair_matrix(length):
    """Pure formula from the frozen independent KC shadow pair audit."""
    lag = (np.arange(length)[None, :] - np.arange(length)[:, None]) * .2
    return -.0005 * np.sign(lag) * (np.exp(-abs(lag) / 500) - np.exp(-abs(lag) / 100))


def _bridge_inputs(kc, dan, pk, pc, mask, groups, initial, learning):
    kc, dan = np.asarray(kc), np.asarray(dan)
    if (kc.ndim != 2 or dan.ndim != 2 or len(kc) != len(dan) or not 500 < len(kc) <= 2000
        or kc.shape[1] < 1 or dan.shape[1] != 2 or kc.dtype.kind not in 'fiub' or dan.dtype.kind not in 'fiub'
        or not np.isfinite(kc).all() or not np.isfinite(dan).all()
        or (kc < 0).any() or (kc > 1).any() or (dan < 0).any() or (dan > 2**32).any()):
        raise ValueError('Invalid finite independent bridge inputs')
    pk, pc, mask, groups = map(np.asarray, (pk, pc, mask, groups))
    if (pk.ndim != 1 or not pk.size or any(a.shape != pk.shape for a in [pc, mask, groups])
        or any(a.dtype.kind not in 'iu' for a in [pk, pc, groups]) or mask.dtype.kind not in 'iub'
        or (pk < 0).any() or (pk >= kc.shape[1]).any() or not np.isin(pc, [0, 1]).all()
        or not np.isin(mask, [0, 1]).all() or not np.isin(groups, range(8)).all()
        or not np.array_equal(groups // 4, pc) or type(learning) is not bool):
        raise ValueError('Invalid exact edge/channel/mask mapping')
    initial = np.ones(pk.size, np.float32) if initial is None else np.asarray(initial)
    if (initial.shape != pk.shape or initial.dtype != np.float32 or not np.isfinite(initial).all()
        or (initial < .5).any() or (initial > 1.5).any()):
        raise ValueError('Invalid float32 checkpoint')
    return kc[500:].astype(float), dan[500:].astype(float), pk, pc, mask.astype(bool), groups, initial.copy()


def bridge_reference(kc, dan, pk, pc, mask, groups, *, initial=None, learning=True, guard=lambda: None):
    """Direct exponential superposition plus independently accumulated publications.

    Pair matrix checks attempted areas. Only the interval accumulator is a
    gain oracle when clipping occurs. No recurrence evolves the signal states.
    """
    kc, dan, pk, pc, mask, groups, initial = _bridge_inputs(kc, dan, pk, pc, mask, groups, initial, learning)
    length, ne = len(kc), pk.size
    kr, ke = impulse_matrices(length)
    sparse = csr_matrix(kc)
    rk = sparse.T.dot(kr.T).T
    ek = sparse.T.dot(ke.T).T
    rd, ed = kr @ dan, ke @ dan
    guard()
    phases = np.zeros((4, ne, 8))
    pubs = np.zeros((4, ne), np.int64)
    bounds = np.zeros((2, ne), np.int64)
    possible = np.zeros((2, ne), np.int64)
    gain, published = initial.astype(float), initial.copy()
    scale = .00048 if learning else 0.
    a = -math.expm1(-.012 * .2) / .012
    b = (a - (-math.expm1(-.02 * .2) / .02)) / .008
    electrical = electrical_double = None
    for t in range(length + 1):
        if t % 50 == 0: guard()
        phase = 3 if t == length else 0 if t < 150 else 1 if t < 1000 else 2
        aa, bb = (1 / .012, 1 / (.02 * .012)) if t == length else (a, b)
        r, k, d, h = rk[t, pk], ek[t, pk], rd[t, pc], ed[t, pc]
        common = bb * r * d
        pos = np.where(mask, scale * (aa * r * h + common), 0.)
        neg = np.where(mask, -scale * (aa * k * d + common), 0.)
        delta = np.where(mask, scale * aa * (r*h - k*d), 0.)
        proposed = gain + delta
        updated = np.where(mask, np.minimum(1.5, np.maximum(.5, proposed)), gain)
        next_published = np.where(mask, updated.astype(np.float32), published)
        low = mask & ((proposed <= .5) | (next_published <= .5))
        high = mask & ((proposed >= 1.5) | (next_published >= 1.5))
        phases[phase] += np.stack((pos, neg, delta, updated-gain,
                                   next_published.astype(float)-published.astype(float), low, high, pos-neg), axis=1)
        pubs[phase] += mask
        bounds += np.stack((low, high))
        radius = GAIN_ALLOWANCE if learning else 0.
        lower = np.nextafter(updated - radius, -np.inf) if radius else updated
        upper = np.nextafter(updated + radius, np.inf) if radius else updated
        # Midpoints adjacent to .5/1.5 round to the bound (ties-to-even).
        possible += np.stack((mask & ((proposed - radius <= .5) | (lower <= .5 + 2**-25)),
                              mask & ((proposed + radius >= 1.5) | (upper >= 1.5 - 2**-24))))
        gain, published = updated, next_published
        if t == length - 1:
            electrical, electrical_double = published.copy(), gain.copy()
    guard()
    attempted = kc.T @ (pair_matrix(length) @ dan)
    pair = np.where(mask, (attempted[pk, pc] if learning else np.zeros(ne)), 0.)
    epk = np.column_stack((rk[-1], ek[-1])); epd = np.column_stack((rd[-1], ed[-1]))
    tail = np.where(mask, scale / .012 * (rk[-1, pk]*ed[-1, pc] - ek[-1, pk]*rd[-1, pc]), 0.)
    grouped = np.stack([np.stack([phases[p, groups == g].sum(0) for g in range(8)]) for p in range(4)])
    result = dict(gains=published, double_gains=gain, electrical_gains=electrical,
                  electrical_double_gains=electrical_double, edge_phases=phases, group_phases=grouped,
                  publication_counts=pubs, bound_counts=bounds, endpoint_kc=epk, endpoint_dan=epd,
                  conditional_bound_counts=possible, unconstrained_pair=pair,
                  unconstrained_electrical_pair=pair-tail)
    if any(not np.isfinite(a).all() for a in result.values()):
        raise ValueError('Nonfinite independent bridge calculation')
    np.testing.assert_allclose(phases[..., 2].sum(0), pair, atol=AREA_ATOL, rtol=AREA_RTOL)
    np.testing.assert_allclose(phases[:3, :, 2].sum(0), pair-tail, atol=AREA_ATOL, rtol=AREA_RTOL)
    return result


def guard_cell(gains):
    gains = np.asarray(gains)
    if (gains.dtype != np.float32 or gains.ndim != 2 or gains.shape[0] != 8 or not gains.shape[1]
        or not np.isfinite(gains).all() or (gains < .5).any() or (gains > 1.5).any()):
        raise ValueError('Eight finite float32 eligible-edge vectors required')
    ticks = [sum(int(x) for x in row) for row in ((gains.astype(float)-1) * 2**24)]
    return dict(ticks=ticks, point_pass=9*sum(ticks)**2 <= 16*sum(t*t for t in ticks))


def compare_endpoints(reference, actual):
    errors, mismatches = {}, {}
    for name in ['double_gains', 'electrical_double_gains', 'gains', 'electrical_gains']:
        want, got = reference[name], actual[name]
        dtype = np.float64 if 'double' in name else np.float32
        if (got.dtype != dtype or got.shape != want.shape or not np.isfinite(got).all()
            or (got < .5).any() or (got > 1.5).any()):
            raise ValueError('Malformed gain endpoint ' + name)
        if dtype == np.float64:
            errors[name] = float(np.max(np.abs(got-want), initial=0))
        else:
            mismatches[name] = np.flatnonzero(got.view(np.uint32) != want.view(np.uint32)).tolist()
    return dict(status='failed_double_comparison' if max(errors.values()) > GAIN_ALLOWANCE else
                'rounding_ambiguous' if any(mismatches.values()) else 'passed',
                max_absolute_errors=errors, float32_mismatch_indices=mismatches)
