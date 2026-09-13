"""Pure fixed-contract replay of KC impulses and finite DAN release masses.

This copies the frozen antisymmetric weighted-event bridge. Only the DAN
input envelope is widened to [0,2**32] for the finite reset release hypothesis;
KC remains in [0,1]. This is not a new cellular model. No native library, graph loader, RNG or captured history is
accessed. Counts include proposed or float32-published equality at a bound,
including eta-zero mode, exactly as the native bridge does.
"""

import math

import numpy as np

DT, R, E, SCALE = 0.2, 0.01, 0.002, 0.00048
ONSET = 500
FIELDS = (
    "positive",
    "negative",
    "attempted",
    "applied_double",
    "applied_published",
    "low_count",
    "high_count",
    "absolute_area",
)


def _inputs(kc, dan, pk, pc, mask, groups, initial, learning):
    kc, dan = np.asarray(kc), np.asarray(dan)
    if (
        any(x.ndim != 2 or x.dtype.kind not in "fiub" for x in (kc, dan))
        or kc.shape[0] != dan.shape[0]
        or kc.shape[0] <= ONSET
        or kc.shape[1] < 1
        or dan.shape[1] not in (1, 2)
        or any(not np.isfinite(x).all() or np.any(x < 0) for x in (kc, dan))
        or np.any(kc > 1)
        or np.any(dan > 2**32)
    ):
        raise ValueError("Expected matching finite impulses: KC [0,1], DAN [0,2**32], with steps > 500.")
    pk, pc, mask, groups = map(np.asarray, (pk, pc, mask, groups))
    if pk.ndim != 1 or not pk.size:
        raise ValueError("Expected at least one mapped plastic edge.")
    ne = pk.size
    if (
        any(x.shape != (ne,) or x.dtype.kind not in "iu" for x in (pk, pc, groups))
        or mask.shape != (ne,)
        or mask.dtype.kind not in "iub"
        or not np.isin(mask, [0, 1]).all()
        or np.any(pk < 0)
        or np.any(pk >= kc.shape[1])
        or np.any(pc < 0)
        or np.any(pc >= dan.shape[1])
        or np.any(groups < 0)
        or np.any(groups >= 8)
        or np.any(groups // 4 != pc)
        or type(learning) is not bool
    ):
        raise ValueError("Invalid KC/channel/group mapping, mask, or learning flag.")
    initial = np.ones(ne, np.float32) if initial is None else np.asarray(initial)
    if (
        initial.shape != (ne,)
        or initial.dtype != np.dtype("float32")
        or not np.isfinite(initial).all()
        or np.any(initial < 0.5)
        or np.any(initial > 1.5)
    ):
        raise ValueError("Initial checkpoint must be float32, finite and within [0.5,1.5].")
    return kc.astype(float), dan.astype(float), pk, pc, mask.astype(bool), groups, initial.copy()


def replay(kc, dan_means, pk, pc, mask, groups, *, initial=None, learning=True):
    """Cold onset500; publish once per full .2ms interval and once for full tail.

    Inputs are event masses, not rates: KC [0,1], DAN [0,2**32].
    The conservative DAN bound belongs to the finite 2000-slot release domain;
    this replay may append silence for independent complete-tail checks.
    DAN columns are already
    population means. ``pk`` and ``pc`` map each edge to KC/channel; groups0..7
    obey group//4 == channel. Repeated KC/channel mappings are valid. Excluded
    edges retain their checkpoint and have no publications; learning=False
    uses eta zero but retains native masked publication/bound observations.

    Four phases are [100,130), [130,300), [300,end) ms and the complete tail.
    Signed negative areas are <=0. Double gains contain the stepwise clipped
    accumulator; float32 publication never feeds back into that accumulator.
    Endpoint signals are the finite electrical endpoint, before the tail.
    """
    kc, dan, pk, pc, mask, groups, initial = _inputs(kc, dan_means, pk, pc, mask, groups, initial, learning)
    nk, nc, ne = kc.shape[1], dan.shape[1], pk.size
    gain, published = initial.astype(float), initial.copy()
    rk, ek, rd, ed = np.zeros(nk), np.zeros(nk), np.zeros(nc), np.zeros(nc)
    edge_phases = np.zeros((4, ne, len(FIELDS)))
    publication_counts = np.zeros((4, ne), np.int64)
    bound_counts = np.zeros((2, ne), np.int64)
    scale = SCALE if learning else 0.0
    ar, ae = math.exp(-R * DT), math.exp(-E * DT)
    area = -math.expm1(-(R + E) * DT) / (R + E)
    common = (-math.expm1(-2 * R * DT) / (2 * R) - area) / (E - R)
    coupling = ae * math.expm1((E - R) * DT) / (E - R)

    def update(a, c, phase):
        nonlocal gain, published
        kr, ke, dr, de = rk[pk], ek[pk], rd[pc], ed[pc]
        shared = c * kr * dr
        positive = np.where(mask, scale * (a * de * kr + shared), 0.0)
        negative = np.where(mask, -scale * (a * ke * dr + shared), 0.0)
        # Integrate Q directly: P-N would cancel two common product areas.
        delta = np.where(mask, scale * a * (de * kr - ke * dr), 0.0)
        proposed = gain + delta
        next_gain = np.where(mask, np.clip(proposed, 0.5, 1.5), gain)
        next_published = np.where(mask, next_gain.astype(np.float32), published)
        low = mask & ((proposed <= 0.5) | (next_published <= 0.5))
        high = mask & ((proposed >= 1.5) | (next_published >= 1.5))
        edge_phases[phase] += np.column_stack(
            (
                positive,
                negative,
                delta,
                next_gain - gain,
                next_published.astype(float) - published.astype(float),
                low,
                high,
                positive - negative,
            )
        )
        publication_counts[phase] += mask
        bound_counts[0] += low
        bound_counts[1] += high
        gain, published = next_gain, next_published

    with np.errstate(over="raise", invalid="raise", divide="raise"):
        for step in range(ONSET, len(kc)):
            rk += kc[step] * R
            rd += dan[step] * R
            update(area, common, 0 if step < 650 else 1 if step < 1500 else 2)
            ek = ae * ek + coupling * rk
            ed = ae * ed + coupling * rd
            rk *= ar
            rd *= ar
        endpoint_kc, endpoint_dan = np.column_stack((rk, ek)), np.column_stack((rd, ed))
        electrical_gains, electrical_double_gains = published.copy(), gain.copy()
        update(1 / (R + E), 1 / (2 * R * (R + E)), 3)
    group_phases = np.zeros((4, 8, len(FIELDS)))
    for phase in range(4):
        for field in range(len(FIELDS)):
            group_phases[phase, :, field] = np.bincount(
                groups, weights=edge_phases[phase, :, field], minlength=8
            )
    result = dict(
        gains=published,
        double_gains=gain,
        electrical_gains=electrical_gains,
        electrical_double_gains=electrical_double_gains,
        edge_phases=edge_phases,
        group_phases=group_phases,
        publication_counts=publication_counts,
        bound_counts=bound_counts,
        endpoint_kc=endpoint_kc,
        endpoint_dan=endpoint_dan,
    )
    if any(not np.isfinite(value).all() for value in result.values()):
        raise FloatingPointError("Nonfinite weighted bridge result.")
    return result
