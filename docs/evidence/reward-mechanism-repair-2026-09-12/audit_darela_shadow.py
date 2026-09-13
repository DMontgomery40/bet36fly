"""Independent saved-shadow audit. No producer bridge or rejected model imports.

Only separately authorized CLI execution may read actual saved histories.
Pure functions use supplied arrays, direct impulse superposition and the
previously reviewed complete pair kernel, with fixed numerical comparisons.
"""

import argparse
import signal
import sys
import time
import run_dan_causal_prefix_v2 as reader

from fractions import Fraction
from functools import lru_cache
import math
import hashlib
import io
import json
import os
from pathlib import Path
import re
import zipfile

from darela_release_reference import reference_events
from weight_state_guard_reference import round_f32_ticks

import numpy as np
from scipy.sparse import csr_matrix

GAIN_ALLOWANCE = 1e-11
AREA_ATOL, AREA_RTOL = 2e-11, 1e-12


@lru_cache(maxsize=4)
def impulse_matrices(length):
    """Direct post-event states including one final quiet boundary."""
    age = (np.arange(length + 1)[:, None] - np.arange(length)[None, :]) * 0.2
    admitted = age >= 0
    age = np.maximum(age, 0)
    rate = np.where(admitted, np.exp(-age / 100) / 100, 0.0)
    eligibility = np.where(admitted, 1.25 * np.exp(-age / 500) * -np.expm1(-0.008 * age), 0.0)
    return rate, eligibility


@lru_cache(maxsize=4)
def pair_matrix(length):
    """Pure formula from the frozen independent KC shadow pair audit."""
    lag = (np.arange(length)[None, :] - np.arange(length)[:, None]) * 0.2
    return -0.0005 * np.sign(lag) * (np.exp(-abs(lag) / 500) - np.exp(-abs(lag) / 100))


def _bridge_inputs(kc, dan, pk, pc, mask, groups, initial, learning):
    kc, dan = np.asarray(kc), np.asarray(dan)
    if (
        kc.ndim != 2
        or dan.ndim != 2
        or len(kc) != len(dan)
        or not 500 < len(kc) <= 2000
        or kc.shape[1] < 1
        or dan.shape[1] != 2
        or kc.dtype.kind not in "fiub"
        or dan.dtype.kind not in "fiub"
        or not np.isfinite(kc).all()
        or not np.isfinite(dan).all()
        or (kc < 0).any()
        or (kc > 1).any()
        or (dan < 0).any()
        or (dan > 2**32).any()
    ):
        raise ValueError("Invalid finite independent bridge inputs")
    pk, pc, mask, groups = map(np.asarray, (pk, pc, mask, groups))
    if (
        pk.ndim != 1
        or not pk.size
        or any(a.shape != pk.shape for a in [pc, mask, groups])
        or any(a.dtype.kind not in "iu" for a in [pk, pc, groups])
        or mask.dtype.kind not in "iub"
        or (pk < 0).any()
        or (pk >= kc.shape[1]).any()
        or not np.isin(pc, [0, 1]).all()
        or not np.isin(mask, [0, 1]).all()
        or not np.isin(groups, range(8)).all()
        or not np.array_equal(groups // 4, pc)
        or type(learning) is not bool
    ):
        raise ValueError("Invalid exact edge/channel/mask mapping")
    initial = np.ones(pk.size, np.float32) if initial is None else np.asarray(initial)
    if (
        initial.shape != pk.shape
        or initial.dtype != np.float32
        or not np.isfinite(initial).all()
        or (initial < 0.5).any()
        or (initial > 1.5).any()
    ):
        raise ValueError("Invalid float32 checkpoint")
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
    scale = 0.00048 if learning else 0.0
    a = -math.expm1(-0.012 * 0.2) / 0.012
    b = (a - (-math.expm1(-0.02 * 0.2) / 0.02)) / 0.008
    electrical = electrical_double = None
    for t in range(length + 1):
        if t % 50 == 0:
            guard()
        phase = 3 if t == length else 0 if t < 150 else 1 if t < 1000 else 2
        aa, bb = (1 / 0.012, 1 / (0.02 * 0.012)) if t == length else (a, b)
        r, k, d, h = rk[t, pk], ek[t, pk], rd[t, pc], ed[t, pc]
        common = bb * r * d
        pos = np.where(mask, scale * (aa * r * h + common), 0.0)
        neg = np.where(mask, -scale * (aa * k * d + common), 0.0)
        delta = np.where(mask, scale * aa * (r * h - k * d), 0.0)
        proposed = gain + delta
        updated = np.where(mask, np.minimum(1.5, np.maximum(0.5, proposed)), gain)
        next_published = np.where(mask, updated.astype(np.float32), published)
        low = mask & ((proposed <= 0.5) | (next_published <= 0.5))
        high = mask & ((proposed >= 1.5) | (next_published >= 1.5))
        phases[phase] += np.stack(
            (
                pos,
                neg,
                delta,
                updated - gain,
                next_published.astype(float) - published.astype(float),
                low,
                high,
                pos - neg,
            ),
            axis=1,
        )
        pubs[phase] += mask
        bounds += np.stack((low, high))
        radius = GAIN_ALLOWANCE if learning else 0.0
        lower = np.nextafter(updated - radius, -np.inf) if radius else updated
        upper = np.nextafter(updated + radius, np.inf) if radius else updated
        # Midpoints adjacent to .5/1.5 round to the bound (ties-to-even).
        possible += np.stack(
            (
                mask & ((proposed - radius <= 0.5) | (lower <= 0.5 + 2**-25)),
                mask & ((proposed + radius >= 1.5) | (upper >= 1.5 - 2**-24)),
            )
        )
        gain, published = updated, next_published
        if t == length - 1:
            electrical, electrical_double = published.copy(), gain.copy()
    guard()
    attempted = kc.T @ (pair_matrix(length) @ dan)
    pair = np.where(mask, (attempted[pk, pc] if learning else np.zeros(ne)), 0.0)
    epk = np.column_stack((rk[-1], ek[-1]))
    epd = np.column_stack((rd[-1], ed[-1]))
    tail = np.where(mask, scale / 0.012 * (rk[-1, pk] * ed[-1, pc] - ek[-1, pk] * rd[-1, pc]), 0.0)
    grouped = np.stack([np.stack([phases[p, groups == g].sum(0) for g in range(8)]) for p in range(4)])
    result = dict(
        gains=published,
        double_gains=gain,
        electrical_gains=electrical,
        electrical_double_gains=electrical_double,
        edge_phases=phases,
        group_phases=grouped,
        publication_counts=pubs,
        bound_counts=bounds,
        endpoint_kc=epk,
        endpoint_dan=epd,
        conditional_bound_counts=possible,
        unconstrained_pair=pair,
        unconstrained_electrical_pair=pair - tail,
    )
    if any(not np.isfinite(a).all() for a in result.values()):
        raise ValueError("Nonfinite independent bridge calculation")
    np.testing.assert_allclose(phases[..., 2].sum(0), pair, atol=AREA_ATOL, rtol=AREA_RTOL)
    np.testing.assert_allclose(phases[:3, :, 2].sum(0), pair - tail, atol=AREA_ATOL, rtol=AREA_RTOL)
    return result


def guard_cell(gains):
    gains = np.asarray(gains)
    if (
        gains.dtype != np.float32
        or gains.ndim != 2
        or gains.shape[0] != 8
        or not gains.shape[1]
        or not np.isfinite(gains).all()
        or (gains < 0.5).any()
        or (gains > 1.5).any()
    ):
        raise ValueError("Eight finite float32 eligible-edge vectors required")
    ticks = [sum(int(x) for x in row) for row in ((gains.astype(float) - 1) * 2**24)]
    return dict(ticks=ticks, point_pass=9 * sum(ticks) ** 2 <= 16 * sum(t * t for t in ticks))


def compare_endpoints(reference, actual):
    errors, mismatches, intervals = {}, {}, {}
    for name in ["double_gains", "electrical_double_gains", "gains", "electrical_gains"]:
        want, got = reference[name], actual[name]
        dtype = np.float64 if "double" in name else np.float32
        if (
            got.dtype != dtype
            or got.shape != want.shape
            or not np.isfinite(got).all()
            or (got < 0.5).any()
            or (got > 1.5).any()
        ):
            raise ValueError("Malformed gain endpoint " + name)
        if dtype == np.float64:
            errors[name] = float(np.max(np.abs(got - want), initial=0))
        else:
            mismatches[name] = np.flatnonzero(got.view(np.uint32) != want.view(np.uint32)).tolist()
    publication_bad = any(
        not np.array_equal(actual[p + "gains"], actual[p + "double_gains"].astype(np.float32))
        for p in ["", "electrical_"]
    )
    outside = False
    for name, indices in mismatches.items():
        centers = reference[name.replace("gains", "double_gains")]
        intervals[name] = []
        for i in indices:
            center, radius = Fraction(float(centers[i])), Fraction(GAIN_ALLOWANCE)
            low = round_f32_ticks(max(Fraction(1, 2), center - radius))
            high = round_f32_ticks(min(Fraction(3, 2), center + radius))
            observed = int(float(actual[name][i]) * 2**24)
            outside |= not low <= observed <= high
            intervals[name].append(dict(edge=i, lower_ticks=low, upper_ticks=high, observed_ticks=observed))
    return dict(
        status="failed_publication"
        if publication_bad or outside
        else "failed_double_comparison"
        if max(errors.values()) > GAIN_ALLOWANCE
        else "rounding_ambiguous"
        if any(mismatches.values())
        else "passed",
        max_absolute_errors=errors,
        float32_mismatch_indices=mismatches,
        conditional_mismatch_publication_intervals=intervals,
    )


def fingerprint(a):
    return dict(
        dtype=str(a.dtype),
        shape=list(a.shape),
        sha256=hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest(),
    )


def exact(actual, expected, name):
    if (
        not isinstance(actual, np.ndarray)
        or actual.shape != expected.shape
        or actual.dtype != expected.dtype
        or not np.array_equal(actual, expected)
    ):
        raise ValueError("Exact identity/accounting mismatch: " + name)


def audit_case(trace, maps, saved, *, original, original_delta, original_electrical=None, guard=lambda: None):
    if (
        trace.dtype != np.int32
        or trace.ndim != 2
        or trace.shape[1] != len(maps["sample"])
        or not 500 < len(trace) <= 2000
        or not np.isin(trace, [0, 1]).all()
    ):
        raise ValueError("Original binary raster shape/type")
    kc = np.ascontiguousarray(trace[:, maps["kc_columns"]])
    dan = np.ascontiguousarray(trace[:, maps["dan_columns"]])
    ne = len(maps["plastic_mask"])
    mask = maps["plastic_mask"].astype(bool)
    originals = dict(
        initial_gains=np.ones(ne, np.float32),
        original_gains=original,
        original_gain_delta=original_delta,
        raw_dan_events=dan,
        raw_kc_event_totals=kc.sum(0, dtype=np.int64),
        raw_dan_event_totals=dan.sum(0, dtype=np.int64),
        raw_compartment_event_counts=np.column_stack(
            [dan[:, maps["dan_compartments"] == c].sum(1, dtype=np.int64) for c in [0, 1]]
        ),
    )
    originals.update({"map__" + k: a for k, a in maps.items()})
    if original_electrical is not None:
        originals["original_electrical_gains"] = original_electrical
    for k, expected in originals.items():
        if k not in saved:
            raise ValueError("Missing saved identity field " + k)
        exact(saved[k], expected, k)
    exact(original_delta, original - np.float32(1), "original delta")
    for value in [original] + ([] if original_electrical is None else [original_electrical]):
        if (
            value.dtype != np.float32
            or value.shape != (ne,)
            or not np.isfinite(value).all()
            or (value < 0.5).any()
            or (value > 1.5).any()
            or not np.array_equal(value[~mask], np.ones(np.count_nonzero(~mask), np.float32))
        ):
            raise ValueError("Original comparator bounds/masked checkpoint")
    guard()
    release = reference_events(dan, maps["dan_compartments"])
    guard()
    bridge = bridge_reference(
        kc,
        release["pooled_release"],
        *[maps[k] for k in ["plastic_kc_indices", "plastic_compartments", "plastic_mask", "plastic_groups"]],
        guard=guard,
    )
    reference = {**release, **bridge}
    required = (
        set(originals)
        | set(release)
        | (set(bridge) - {"conditional_bound_counts", "unconstrained_pair", "unconstrained_electrical_pair"})
    )
    if set(saved) != required:
        raise ValueError("Complete saved numerical schema")
    errors, failed = {}, []
    for k in required - set(originals):
        a, wanted = saved[k], reference[k]
        if a.dtype != wanted.dtype or a.shape != wanted.shape or not np.isfinite(a).all():
            raise ValueError("Saved numeric shape/type/finite field " + k)
        if k in ["publication_counts", "bound_counts"]:
            exact(a, wanted, k)
        elif k in ["gains", "double_gains", "electrical_gains", "electrical_double_gains"]:
            if not np.array_equal(a[~mask], np.ones(np.count_nonzero(~mask), dtype=a.dtype)):
                raise ValueError("Masked gain checkpoint changed")
        else:
            atol, rtol = (
                (1e-12, 1e-12)
                if k in release or k in ["endpoint_kc", "endpoint_dan"]
                else (AREA_ATOL, AREA_RTOL)
            )
            errors[k] = float(np.max(np.abs(a - wanted), initial=0))
            if not np.allclose(a, wanted, atol=atol, rtol=rtol):
                failed.append(k)
    if np.any(saved["per_cell_release"][dan == 0] != 0):
        failed.append("silent_release")
    if any(np.any(saved[k] <= 0) for k in ["state_before", "state_after", "endpoint_state"]):
        failed.append("nonpositive_release_state")
    endpoints = compare_endpoints(bridge, saved)
    contacts = int(bridge["bound_counts"].sum())
    possible = int(bridge["conditional_bound_counts"].sum())
    status = "failed_numerical_comparison" if failed else endpoints["status"]
    if status == "passed" and not contacts and possible:
        status = "bound_ambiguous"
    report = dict(
        status=status,
        max_absolute_errors=errors,
        failed_fields=failed,
        endpoints=endpoints,
        bound_contacts=contacts,
        conditional_possible_bound_contacts=possible,
        release_values_checked=sum(a.size for a in release.values()),
        bridge_values_checked=sum(a.size for a in bridge.values()),
        pair_gain_proof="unclipped only"
        if contacts == 0
        else "not applicable; independent interval clipping used",
    )
    return report, reference


def checked_bytes(path, item, limit=128 * 1024 * 1024):
    p = Path(path)
    if (
        type(item) is not dict
        or set(item) != {"path", "bytes", "sha256"}
        or type(item["bytes"]) is not int
        or not 0 <= item["bytes"] <= limit
        or type(item["path"]) is not str
        or str(p) != item["path"]
        or not p.is_absolute()
        or p != p.resolve()
        or not p.is_file()
        or type(item["sha256"]) is not str
        or not re.fullmatch("[0-9a-f]{64}", item["sha256"])
        or p.stat().st_size != item["bytes"]
    ):
        raise ValueError("Malformed, changed, unsafe or oversized binding")
    with p.open("rb") as f:
        raw = f.read(limit + 1)
    if len(raw) != item["bytes"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
        raise ValueError("Bound bytes differ")
    return raw


def load_bound_npz(path, item):
    raw = checked_bytes(path, item)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        members = z.infolist()
        names = [a.filename for a in members]
        if (
            not 0 < len(names) <= 64
            or len(set(names)) != len(names)
            or any(not re.fullmatch(r"[A-Za-z0-9_]+\.npy", n) for n in names)
            or sum(a.file_size for a in members) > 128 * 1024 * 1024
        ):
            raise ValueError("Unsafe NPZ inventory")
        for member in members:
            if member.flag_bits & 1:
                raise ValueError("Encrypted NPZ member")
            with z.open(member) as stream:
                v = np.lib.format.read_magic(stream)
                if v not in [(1, 0), (2, 0)]:
                    raise ValueError("Unsupported NPY version")
                reader = (
                    np.lib.format.read_array_header_1_0
                    if v == (1, 0)
                    else np.lib.format.read_array_header_2_0
                )
                shape, _, dtype = reader(stream)
                size = math.prod(shape) * dtype.itemsize
                if (
                    dtype.hasobject
                    or dtype.fields
                    or dtype.kind not in "fiub"
                    or len(shape) > 4
                    or size > 128 * 1024 * 1024
                    or stream.tell() + size != member.file_size
                ):
                    raise ValueError("Unsafe or inconsistent NPY allocation")
    with np.load(io.BytesIO(raw), allow_pickle=False) as z:
        result = {k: z[k] for k in z.files}
    if any(not np.isfinite(a).all() for a in result.values()):
        raise ValueError("Nonfinite numeric artifact")
    return result


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "bet36fly/reward_lif.cpp").is_file())
SCIENTIFIC_CONTRACT = dict(
    steps=2000,
    dt_ms=0.2,
    onset_step=500,
    populations=[2, 22],
    p=[0.0105, -0.003, -0.0011],
    tau_s=[7.5, 15.0, 900.0],
    reset="unit H at t0; pre-H release then q kick",
    initial_gains="unit float32",
    rate_tau_ms=100.0,
    eligibility_tau_ms=500.0,
    eta=0.0005,
    normalization=0.96,
    bounds=[0.5, 1.5],
    tail="single full analytic bridge tail",
    expected_histories=32,
    expected_guard_cells=8,
    wall_seconds_cap=1200,
    native_calls=0,
    network_calls=0,
)


WORK_SECONDS, TOTAL_SECONDS = 580, 600


def write_json(path, value):
    path = Path(path)
    raw = json.dumps(value, indent=2, allow_nan=False).encode() + b"\n"
    temporary = path.with_name(path.name + ".partial")
    with temporary.open("xb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)


def binding(path, guard=lambda: None):
    p = Path(path).absolute()
    return dict(path=str(p), bytes=p.stat().st_size, sha256=reader.sha(p, guard))


class VerifiedArchive(reader.NumericArchive):
    """Read each validated member into a stable buffer before NumPy allocation."""

    def array(self, name):
        self.guard()
        key = name + ".npy"
        if key not in self.names:
            raise ValueError("Missing source numeric member " + name)
        info = self.names[key]
        if info.file_size > 128 * 1024 * 1024:
            raise ValueError("Selected member exceeds audit byte ceiling")
        with self.z.open(info) as f:
            raw = f.read(info.file_size + 1)
        if len(raw) != info.file_size:
            raise ValueError("Truncated/growing numeric member")
        value = np.load(io.BytesIO(raw), allow_pickle=False)
        self.guard()
        return value


class Store(reader.BoundInputs):
    def json(self, path):
        p = self.path(path)
        return reader.strict_json(checked_bytes(p, self.items[str(p)], 32 * 1024 * 1024))

    def archive(self, path):
        p = self.path(path)
        self.guard()
        if reader.sha(p, self.guard) != self.items[str(p)]["sha256"]:
            raise ValueError("Changed source archive")
        return VerifiedArchive(p, self.guard)

    def npy(self, path):
        p = self.path(path)
        raw = checked_bytes(p, self.items[str(p)])
        stream = io.BytesIO(raw)
        version = np.lib.format.read_magic(stream)
        if version not in [(1, 0), (2, 0)]:
            raise ValueError("Unsupported numeric source header")
        header = (
            np.lib.format.read_array_header_1_0 if version == (1, 0) else np.lib.format.read_array_header_2_0
        )
        shape, _, dtype = header(stream)
        if (
            dtype.hasobject
            or dtype.fields
            or dtype.kind not in "fiub"
            or stream.tell() + math.prod(shape) * dtype.itemsize != len(raw)
        ):
            raise ValueError("Unsafe numeric source allocation")
        return np.load(io.BytesIO(raw), allow_pickle=False)


def source_rows(plan, store, guard):
    m, summaries, outputs, saved = reader._identity_context(plan, store)
    if [int(np.sum((m["plastic_compartments"] == c) & (m["plastic_mask"] == 1))) for c in [0, 1]] != [
        4184,
        3239,
    ] or np.count_nonzero(m["plastic_mask"] == 0) != 1443:
        raise ValueError("Frozen eligible map counts")

    def rows():
        archive = None
        active = None
        try:
            for i, meta in enumerate(plan["expected_rows"]):
                guard()
                rid = meta["run_id"]
                if active != rid:
                    if archive:
                        archive.__exit__()
                    archive = store.archive(Path(plan["run_dirs"][rid]) / "trials.npz")
                    active = rid
                    for k in [
                        "plastic_kc_indices",
                        "plastic_compartments",
                        "plastic_groups",
                        "plastic_mask",
                        "dan_compartments",
                    ]:
                        exact(archive.array(k), m[k], "original main " + k)
                    exact(archive.array("blank_gains"), np.ones(8866, np.float32), "original unit checkpoint")
                    reader.validate_main_sampled(archive.array("sampled"), outputs, m, reader.ACTUAL_SHAPE)
                name = f"fine_{i:02d}.npz"
                path = Path(plan["capture_dir"]) / name
                fine = load_bound_npz(path, store.items[str(path)])
                if not reader.same_json(
                    {k: fingerprint(a) for k, a in fine.items()}, saved[name]["numeric_fingerprint"]
                ):
                    raise ValueError("Complete original fine fingerprint")
                reader.validate_fine(fine, m, reader.ACTUAL_SHAPE)
                prefix = f"{meta['game']}__{meta['seed_set']}__untaught__"
                for k in ["gains", "gain_delta"]:
                    exact(fine[k], archive.array(prefix + k), "fine/main " + k)
                exact(fine["gain_delta"], fine["gains"] - np.float32(1), "fine unit delta")
                electrical = (
                    archive.array(prefix + "electrical_gains")
                    if prefix + "electrical_gains.npy" in archive.names
                    else None
                )
                yield i, meta, fine["trace"], fine["gains"], fine["gain_delta"], electrical
        finally:
            if archive:
                archive.__exit__()

    return m, rows()


def guards_for_rows(rows, maps, key):
    result = {}
    for rid in reader.RUNS:
        for noise in ["base", "alt"]:
            selected = [
                r for r in rows if r["metadata"]["run_id"] == rid and r["metadata"]["seed_set"] == noise
            ]
            if len(selected) != 8:
                raise ValueError("Eight ordered trials per guard required")
            for c, name in enumerate(["home", "away"]):
                edges = (maps["plastic_mask"] == 1) & (maps["plastic_compartments"] == c)
                exact_guard = guard_cell(np.stack([r[key][edges] for r in selected]))
                values = np.asarray(exact_guard["ticks"], np.float64) / 2**24
                sd = float(np.std(values, ddof=1))
                result[f"{rid}/{noise}/{name}"] = dict(
                    ticks=exact_guard["ticks"],
                    edge_count=int(edges.sum()),
                    games=[r["metadata"]["game"] for r in selected],
                    mean=float(values.mean()),
                    sample_sd=sd,
                    limit=0.5 * sd,
                    passed=exact_guard["point_pass"],
                )
    return result


def same_guards(actual, expected):
    if type(actual) is not dict or set(actual) != set(expected):
        raise ValueError("Complete guard matrix")
    for key, want in expected.items():
        got = actual[key]
        if type(got) is not dict or set(got) != set(want):
            raise ValueError("Guard field inventory")
        for k in ["ticks", "edge_count", "games", "passed"]:
            if not reader.same_json(got[k], want[k]):
                raise ValueError("Exact guard identity/arithmetic " + key + "/" + k)
        for k in ["mean", "sample_sd", "limit"]:
            if type(got[k]) not in [float, int] or not math.isclose(
                got[k], want[k], abs_tol=1e-15, rel_tol=1e-12
            ):
                raise ValueError("Guard description must use trial sums: " + key + "/" + k)


def validate_plan(plan):
    if (
        type(plan) is not dict
        or type(plan.get("schema")) is not int
        or plan["schema"] != 1
        or plan.get("analysis") != "darela-reset-release-shadow-v1"
        or not reader.same_json(plan.get("contract"), SCIENTIFIC_CONTRACT)
        or not reader.same_json(plan.get("expected_rows"), reader.expected_rows())
        or type(plan.get("wall_seconds_cap")) is not int
        or plan["wall_seconds_cap"] != 1200
        or plan.get("root") != str(ROOT)
        or tuple(plan.get("run_dirs", {})) != reader.RUNS
    ):
        raise ValueError("Frozen scientific/ordered-selector plan")
    identity = (
        "darela-shadow-"
        + hashlib.sha256(
            json.dumps(
                {k: v for k, v in plan.items() if k != "run_id"},
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode()
        ).hexdigest()[:20]
    )
    if plan.get("run_id") != identity:
        raise ValueError("New complete plan identity")
    for key in [
        "output_root",
        "capture_dir",
        "samples_path",
        "context_plan",
        "preregistration",
        "audit_contract",
    ]:
        if (
            type(plan.get(key)) is not str
            or not Path(plan[key]).is_absolute()
            or ".." in Path(plan[key]).parts
        ):
            raise ValueError("Exact plan path " + key)
    Store(plan.get("inputs"))


def check_runtime(plan, store):
    modules = [
        Path(__file__).resolve(),
        Path(reader.__file__).resolve(),
        Path(reader.prefix.__file__).resolve(),
        Path(sys.modules[reference_events.__module__].__file__).resolve(),
        Path(sys.modules[round_f32_ticks.__module__].__file__).resolve(),
    ]
    required = modules + [
        Path(__file__).with_name(n)
        for n in [
            "test_audit_darela_shadow.py",
            "launch_audit_darela_shadow.py",
            "darela-shadow-independent-audit-contract-2026-09-13.md",
        ]
    ]
    for path in required + [Path(plan[k]) for k in ["context_plan", "preregistration", "audit_contract"]]:
        store.path(path)
    context = store.json(plan["context_plan"])
    reader.validate_plan(context)
    if len(context["inputs"]) != 113:
        raise ValueError("Complete frozen historical context")
    for item in context["inputs"]:
        if store.items.get(item["path"]) != item:
            raise ValueError("Omitted/changed historical input")
    for key in ["root", "capture_dir", "samples_path", "run_dirs", "source_snapshot", "expected_rows"]:
        if not reader.same_json(plan[key], context[key]):
            raise ValueError("Historical context " + key)


def validate_terminals(plan, plan_raw, producer, artifacts):
    def read(name):
        return artifacts.json(producer / name)

    identity, status, summary, completion = [
        read(n) for n in ["identity.json", "status.json", "summary.json", "completion.json"]
    ]
    parent = artifacts.json(producer.parent / "parent-result.json")
    if (producer / "terminal-error.json").exists() or (producer.parent / "terminal-error.json").exists():
        raise ValueError("Producer terminal failure overrides completion")
    if (
        not reader.same_json(identity["plan"], plan)
        or identity["plan_sha256"] != hashlib.sha256(plan_raw).hexdigest()
        or any(x["run_id"] != plan["run_id"] for x in [identity, summary, completion, parent])
        or status["status"] != "completed"
        or completion["status"] != "complete"
        or summary["status"] != "computed"
        or parent["status"] != "completed"
        or type(parent["exit_code"]) is not int
        or parent["exit_code"] != 0
        or parent["child_reaped"] is not True
        or parent["timed_out"] is not False
        or parent["plan_sha256"] != hashlib.sha256(plan_raw).hexdigest()
    ):
        raise ValueError("Successful bound producer terminal conjunction")
    for value in [status["wall_seconds"], completion["elapsed_through_summary"], parent["wall_seconds"]]:
        if type(value) not in [float, int] or not 0 <= value < 1200:
            raise ValueError("Producer deadline")
    if type(parent["wall_seconds_cap"]) is not int or parent["wall_seconds_cap"] != 1200:
        raise ValueError("Producer parent cap")
    for obj, keys in [
        (status, ["completed", "attempted"]),
        (summary, ["completed"]),
        (completion, ["completed"]),
    ]:
        if any(type(obj[k]) is not int or obj[k] != 32 for k in keys):
            raise ValueError("Exactly32 completed producer cases")
    if any(not reader.same_json(status[k], dict(release=32, bridge=32)) for k in ["invocations", "returned"]):
        raise ValueError("Producer helper accounting")
    if not reader.same_json(parent["child_completion"], artifacts.items[str(producer / "completion.json")]):
        raise ValueError("Parent completion binding")
    wanted = {
        str(producer / n): artifacts.items[str(producer / n)]
        for n in ["identity.json", "status.json", "summary.json", "attempts.jsonl"]
    }
    if {x["path"]: x for x in completion["bindings"]} != wanted or len(completion["bindings"]) != 4:
        raise ValueError("Completion inventory")
    journal = [
        reader.strict_json(line)
        for line in checked_bytes(
            producer / "attempts.jsonl", artifacts.items[str(producer / "attempts.jsonl")], 8 * 1024 * 1024
        ).splitlines()
    ]
    if len(journal) != 160:
        raise ValueError("Complete per-helper journal")
    for i in range(32):
        block = journal[i * 5 : i * 5 + 5]
        expected = [
            dict(event=e, index=i, helper=h) for h in ["release", "bridge"] for e in ["intent", "returned"]
        ]
        if not reader.same_json(block[:4], expected) or not reader.same_json(
            block[4],
            dict(event="complete", index=i, detail=artifacts.items[str(producer / f"case_{i:02d}.json")]),
        ):
            raise ValueError("Per-helper journal order or row binding")
    if (
        summary["screen"] != "pending_independent_audit"
        or type(summary["native_calls"]) is not int
        or summary["native_calls"] != 0
        or type(summary["network_calls"]) is not int
        or summary["network_calls"] != 0
    ):
        raise ValueError("Producer scope")
    return summary


def audit(
    plan_path,
    producer_result,
    output,
    *,
    _source_loader=source_rows,
    _check_runtime=True,
    clock=time.monotonic,
):
    started = clock()
    output = Path(output).absolute()
    output.mkdir(parents=False, exist_ok=False)
    report = dict(
        status="running",
        attempted=0,
        completed=0,
        wall_seconds_cap=TOTAL_SECONDS,
        screen="invalid_or_unresolved",
        native_calls=0,
        source_solver_calls=0,
    )
    rows = []
    old_alarm = None

    def guard(final=False):
        if clock() - started >= (TOTAL_SECONDS if final else WORK_SECONDS):
            raise TimeoutError("Independent audit deadline/final reserve")

    def persist():
        report["wall_seconds"] = clock() - started
        write_json(output / "status.json", report)

    try:
        if _check_runtime and any(
            os.environ.get(k) != "1"
            for k in ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]
        ):
            raise ValueError("Single-thread audit environment")
        if clock is time.monotonic:
            old_alarm = signal.getsignal(signal.SIGALRM)
            signal.signal(
                signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("Hard600s audit deadline"))
            )
            signal.setitimer(signal.ITIMER_REAL, TOTAL_SECONDS)
        pp = Path(plan_path).absolute()
        plan_binding = binding(pp)
        plan_raw = checked_bytes(pp, plan_binding, 4 * 1024 * 1024)
        plan = reader.strict_json(plan_raw)
        validate_plan(plan)
        report["run_id"] = plan["run_id"]
        persist()
        guard()
        producer = Path(producer_result).absolute()
        if (
            producer != Path(plan["output_root"]) / plan["run_id"] / "result"
            or producer != producer.resolve()
        ):
            raise ValueError("Exact producer result directory")
        store = Store(plan["inputs"], guard)
        store.verify()
        if _check_runtime:
            check_runtime(plan, store)
        wanted = [
            producer / n
            for n in ["identity.json", "status.json", "summary.json", "completion.json", "attempts.jsonl"]
        ] + [producer.parent / "parent-result.json"]
        wanted += [producer / f"case_{i:02d}.{ext}" for i in range(32) for ext in ["json", "npz"]]
        if set(producer.glob("case_*.json")) != {producer / f"case_{i:02d}.json" for i in range(32)} or set(
            producer.glob("case_*.npz")
        ) != {producer / f"case_{i:02d}.npz" for i in range(32)}:
            raise ValueError("Complete32 producer artifact inventory")
        snapshots = [binding(p, guard) for p in wanted]
        artifacts = Store(snapshots, guard)
        artifacts.verify()
        summary = validate_terminals(plan, plan_raw, producer, artifacts)
        maps, iterator = _source_loader(plan, store, guard)
        for index, meta, trace, original, delta, electrical in iterator:
            guard()
            if (
                type(index) is not int
                or index != report["completed"]
                or not index < 32
                or not reader.same_json(meta, plan["expected_rows"][index])
            ):
                raise ValueError("Audit source row identity/order")
            report["attempted"] += 1
            persist()
            guard()
            detail = artifacts.json(producer / f"case_{index:02d}.json")
            archive = producer / f"case_{index:02d}.npz"
            if (
                type(detail["index"]) is not int
                or detail["index"] != index
                or not reader.same_json(detail["metadata"], meta)
                or not reader.same_json(detail["artifact"], artifacts.items[str(archive)])
            ):
                raise ValueError("Producer row identity/archive binding")
            saved = load_bound_npz(archive, detail["artifact"])
            if not reader.same_json({k: fingerprint(a) for k, a in saved.items()}, detail["arrays"]):
                raise ValueError("Full producer numerical fingerprint")
            if detail["original_electrical_available"] is not (electrical is not None):
                raise ValueError("Original electrical evidence availability")
            row, reference = audit_case(
                trace,
                maps,
                saved,
                original=original,
                original_delta=delta,
                original_electrical=electrical,
                guard=guard,
            )
            if (
                type(detail["gain_bound_observations"]) is not int
                or detail["gain_bound_observations"] != row["bound_contacts"]
            ):
                raise ValueError("Bound contacts/metadata")
            row.update(index=index, metadata=meta)
            with (output / f"reference_{index:02d}.npz").open("xb") as f:
                np.savez_compressed(f, **reference)
                f.flush()
                os.fsync(f.fileno())
            row["reference_artifact"] = binding(output / f"reference_{index:02d}.npz", guard)
            write_json(output / f"row_{index:02d}.json", row)
            rows.append(dict(**row, gains=saved["gains"].copy(), original_gains=original.copy()))
            report["completed"] += 1
            persist()
            guard()
        if report["completed"] != 32 or report["attempted"] != 32:
            raise ValueError("Independent audit requires all32 rows")
        candidate = guards_for_rows(rows, maps, "gains")
        original = guards_for_rows(rows, maps, "original_gains")
        same_guards(summary["candidate_guards"], candidate)
        same_guards(summary["original_guards"], original)
        contacts = sum(r["bound_contacts"] for r in rows)
        provisional = (
            "passed_necessary_untaught_screen"
            if contacts == 0 and all(r["passed"] for r in candidate.values())
            else "rejected_fixed_hypothesis"
        )
        if (
            type(summary["gain_bound_observations"]) is not int
            or summary["gain_bound_observations"] != contacts
            or summary["provisional_screen"] != provisional
        ):
            raise ValueError("Producer screen accounting")
        store.verify()
        artifacts.verify()
        if checked_bytes(pp, plan_binding, 4 * 1024 * 1024) != plan_raw:
            raise ValueError("Plan changed")
        validate_terminals(plan, plan_raw, producer, artifacts)
        guard(final=True)
        numerical = "passed" if all(r["status"] == "passed" for r in rows) else "unresolved"
        report.update(
            status="completed",
            numerical_status=numerical,
            screen=provisional if numerical == "passed" else "invalid_or_unresolved",
            candidate_guards=candidate,
            original_guards=original,
            gain_bound_observations=contacts,
            rows=[{k: v for k, v in r.items() if k not in ["gains", "original_gains"]} for r in rows],
            producer_snapshots=snapshots,
            plan_binding=plan_binding,
        )
        persist()
        guard(final=True)
        write_json(output / "audit.json", report)
        guard(final=True)
        completed_paths = [output / n for n in ["audit.json", "status.json"]] + [
            output / f"{prefix}_{i:02d}.{ext}"
            for i in range(32)
            for prefix, ext in [("row", "json"), ("reference", "npz")]
        ]
        completion = dict(
            status="complete",
            run_id=plan["run_id"],
            completed=32,
            audit=binding(output / "audit.json", lambda: guard(True)),
            bindings=[binding(p, lambda: guard(True)) for p in completed_paths],
            elapsed_seconds=clock() - started,
        )
        write_json(output / "completion.json", completion)
        guard(final=True)
        return report
    except BaseException as exc:
        report.update(
            status="budget_stopped" if isinstance(exc, TimeoutError) else "failed",
            error=f"{type(exc).__name__}: {exc}",
            wall_seconds=clock() - started,
            screen="invalid_or_unresolved",
        )
        error = {
            k: v
            for k, v in report.items()
            if k not in ["rows", "producer_snapshots", "candidate_guards", "original_guards"]
        }
        if (output / "completion.json").is_file():
            error["invalidated_completion_sha256"] = reader.sha(output / "completion.json")
        write_json(output / "terminal-error.json", error)
        try:
            persist()
        except OSError:
            pass
        return report
    finally:
        if old_alarm is not None:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_alarm)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--producer-result", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    r = audit(args.plan, args.producer_result, args.output)
    print(
        json.dumps(
            {
                k: v
                for k, v in r.items()
                if k not in ["rows", "producer_snapshots", "candidate_guards", "original_guards"]
            },
            allow_nan=False,
        ),
        flush=True,
    )
    return 0 if r["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
