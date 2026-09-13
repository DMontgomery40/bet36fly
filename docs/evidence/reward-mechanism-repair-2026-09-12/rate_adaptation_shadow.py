"""Output-only fixed-spike rectified-rate adaptation calculation. No neural imports.

States/accumulators are float64; gains publish float32 once per full electrical
interval and once after the full zero-input tail. No candidate gain feeds spikes.
The CLI requires a root-frozen manifest and explicit matching SHA256.
"""

from __future__ import annotations

import functools
import argparse
import hashlib
import types
import io
import json
from pathlib import Path
import time
import zipfile
import math

import numpy as np

R, E, DELTA = 0.01, 0.002, 0.008
SCALE = 0.0005 * 0.96
DT = 0.2
FIELDS = (
    "positive_integral",
    "negative_integral",
    "attempted",
    "double_applied",
    "published_applied",
    "bound_low",
    "bound_high",
    "absolute_area",
)
PHASES = ((100.0, 130.0), (130.0, 300.0), (300.0, 400.0), (400.0, math.inf))


def _normalized_moment(n, x):
    # Integral_0^1 u^n exp(-x*u) du; convergent at all fixed active durations.
    term = 1.0
    values = []
    for j in range(64):
        values.append(term / (n + j + 1))
        term *= -x / (j + 1)
    return math.fsum(values)


@functools.lru_cache(maxsize=4096)
def _moments(h):
    """Stable F(p), F(2e), M(p), L(p)-M(p), L(2e), J²(2e), J-h."""
    p, q, x = R + E, 2 * E, DELTA * h
    fp, fq = -math.expm1(-p * h) / p, -math.expm1(-q * h) / q
    mp = h * h * _normalized_moment(1, p * h)
    lm, lq, j2 = [], [], []
    for n in range(1, 40):
        coeff = (-x) ** (n - 1) / math.factorial(n)
        if n >= 2:
            lm.append(coeff * _normalized_moment(n, p * h))
            j2.append((-x) ** (n - 2) * (2**n - 2) / math.factorial(n) * _normalized_moment(n, q * h))
        lq.append(coeff * _normalized_moment(n, q * h))
    jm = h * math.fsum((-x) ** n / math.factorial(n + 1) for n in range(1, 40))
    return fp, fq, mp, h * h * math.fsum(lm), h * h * math.fsum(lq), h**3 * math.fsum(j2), jm


def _segment(k, u, d, b, v, h, *, active):
    if math.isinf(h):
        if active:
            raise ValueError("Active interval requires finite zero crossing.")
        return (np.zeros_like(k), np.zeros_like(u), 0.0, 0.0, 0.0), k * v / (R + E), np.zeros_like(k)
    ar, ae = math.exp(-R * h), math.exp(-E * h)
    j = -math.expm1(-DELTA * h) / DELTA
    fp = -math.expm1(-(R + E) * h) / (R + E)
    if active:
        fp, fq, mp, lm, lq, j2, jm = _moments(h)
        a, h0 = R * d / DELTA, d - b
        positive = k * v * fp + k * h0 * mp + k * a * lm
        negative = u * h0 * fq + (k * h0 - u * a * DELTA) * lq - k * a * DELTA * j2
        nv = ae * (v + h0 * h + a * jm)
    else:
        positive, negative, nv = k * v * fp, np.zeros_like(k), ae * v
    # Fail closed on negative analytic states/products; never hide error by flooring.
    if (
        not np.isfinite(positive).all()
        or not np.isfinite(negative).all()
        or not math.isfinite(nv)
        or np.any(positive < 0)
        or np.any(negative < 0)
        or nv < 0
    ):
        raise ArithmeticError("Nonnegative product/state violated analytic contract.")
    state = (ar * k, ae * (u + k * j), ar * d, ae * (b + E * d * j), nv)
    if any(not np.isfinite(x).all() for x in state):
        raise ArithmeticError("Nonfinite evolved state")
    return state, positive, negative


@np.errstate(over="raise", invalid="raise", divide="raise")
def interval(k, u, d, b, v, h):
    """Exact no-event interval, splitting Dplus crossing without gain publication.

    k/u may be equal-shaped vectors; d/b/v are one channel's scalar states.
    Areas exclude the learning coefficient. Negative is the nonnegative
    magnitude of the subtractive product, not a signed-event substitute.
    """
    k, u = np.asarray(k, dtype=float), np.asarray(u, dtype=float)
    if (
        k.shape != u.shape
        or not np.isfinite(k).all()
        or not np.isfinite(u).all()
        or np.any(k < 0)
        or np.any(u < 0)
        or any(not np.isscalar(x) or not math.isfinite(x) or x < 0 for x in (d, b, v))
        or isinstance(h, bool)
        or not np.isscalar(h)
        or math.isnan(h)
        or h < 0
    ):
        raise ValueError("Expected nonnegative finite signal state and nonnegative duration.")
    state = (k, u, float(d), float(b), float(v))
    if h == 0:
        return dict(
            state=state,
            positive=np.zeros_like(k),
            negative=np.zeros_like(k),
            signed=np.zeros_like(k),
            crossing_ms=math.nan,
        )
    crossing = math.inf
    if d > b:
        c = b + E * d / DELTA
        crossing = math.log1p((d - b) / c) / DELTA
        active_h = min(h, crossing)
        state, positive, negative = _segment(*state, active_h, active=True)
        if h > active_h:
            state, p, n = _segment(*state, h - active_h, active=False)
            positive, negative = positive + p, negative + n
    else:
        state, positive, negative = _segment(*state, h, active=False)
    return dict(
        state=state, positive=positive, negative=negative, signed=positive - negative, crossing_ms=crossing
    )


def _inputs(kc, dan, pk, pc, dc, mask, groups, initial, learning):
    kc, dan = np.asarray(kc), np.asarray(dan)
    pk, pc, dc, mask, groups = (np.asarray(x) for x in (pk, pc, dc, mask, groups))
    if (
        kc.ndim != 2
        or dan.ndim != 2
        or kc.shape[0] != 2000
        or dan.shape[0] != 2000
        or min(kc.shape[1], dan.shape[1]) < 1
        or kc.dtype.kind not in "iub"
        or dan.dtype.kind not in "iub"
        or not np.isin(kc, [0, 1]).all()
        or not np.isin(dan, [0, 1]).all()
        or dc.shape != (dan.shape[1],)
        or dc.dtype.kind not in "iu"
        or np.any(dc < 0)
        or set(dc.tolist()) != set(range(int(dc.max()) + 1))
    ):
        raise ValueError("Expected binary2000-step rasters and represented contiguous DAN channels.")
    nc, ne = int(dc.max()) + 1, len(pk)
    if (
        nc > 2
        or ne < 1
        or any(x.shape != (ne,) or x.dtype.kind not in "iu" for x in (pk, pc, groups))
        or mask.shape != (ne,)
        or mask.dtype.kind not in "iub"
        or not np.isin(mask, [0, 1]).all()
        or np.any(pk < 0)
        or np.any(pk >= kc.shape[1])
        or np.any(pc < 0)
        or np.any(pc >= nc)
        or np.any(groups < 0)
        or np.any(groups >= 8)
        or np.any(groups // 4 != pc)
        or type(learning) is not bool
    ):
        raise ValueError("Invalid edge mapping, group/channel mapping, mask, or learning flag.")
    initial = np.ones(ne, np.float32) if initial is None else np.asarray(initial)
    if (
        initial.shape != (ne,)
        or initial.dtype.kind not in "fiu"
        or not np.isfinite(initial).all()
        or np.any(initial < 0.5)
        or np.any(initial > 1.5)
    ):
        raise ValueError("Initial gains must be finite within inclusive fixed bounds.")
    return kc, dan, pk, pc, dc, mask.astype(bool), groups, initial.astype(np.float32)


def publish(gains, published, delta, mask):
    """One complete interval or full-tail publication; never called at a crossing."""
    before, old = gains.copy(), published.copy()
    proposed = before + np.where(mask, delta, 0.0)
    gains = before.copy()
    gains[mask] = np.clip(proposed[mask], 0.5, 1.5)
    published = old.copy()
    published[mask] = gains[mask].astype(np.float32)
    low = mask & ((proposed <= 0.5) | (published <= 0.5))
    high = mask & ((proposed >= 1.5) | (published >= 1.5))
    return gains, published, gains - before, published.astype(float) - old.astype(float), low, high


def shadow(kc, dan, pk, pc, dcomp, mask, groups, *, initial=None, learning=True, guard=None):
    """Fixed2000-step pure shadow; dynamic states reset per call and no feedback."""
    kc, dan, pk, pc, dc, mask, groups, initial = _inputs(
        kc, dan, pk, pc, dcomp, mask, groups, initial, learning
    )
    nk, nc, ne = kc.shape[1], int(dc.max()) + 1, len(pk)
    gain, published = initial.astype(float), initial.copy()
    rk, ek, rd, bd, ed = np.zeros(nk), np.zeros(nk), np.zeros(nc), np.zeros(nc), np.zeros(nc)
    dmean = np.column_stack([dan[:, dc == c].sum(1) / np.count_nonzero(dc == c) for c in range(nc)])
    phases = np.zeros((4, ne, len(FIELDS)))
    active_mask = mask & learning
    crossing_counts = np.zeros((4, nc), np.int64)
    onset_kc = onset_dan = onset_gains = onset_double_gains = None

    def advance(h, phase):
        nonlocal rk, ek, rd, bd, ed, gain, published
        pos, neg = np.zeros(ne), np.zeros(ne)
        if math.isinf(h):
            next_k, next_u = np.zeros_like(rk), np.zeros_like(ek)
        else:
            coupling = -math.expm1(-DELTA * h) / DELTA
            next_k = rk * math.exp(-R * h)
            next_u = math.exp(-E * h) * (ek + rk * coupling)
        for c in range(nc):
            a = interval(rk, ek, rd[c], bd[c], ed[c], h)
            which = pc == c
            pos[which] = a["positive"][pk[which]]
            neg[which] = a["negative"][pk[which]]
            _, _, rd[c], bd[c], ed[c] = a["state"]
            if phase is not None and 0 < a["crossing_ms"] < h:
                crossing_counts[phase, c] += 1
        rk, ek = next_k, next_u
        if phase is None:
            return
        pos, neg = np.where(active_mask, SCALE * pos, 0.0), np.where(active_mask, SCALE * neg, 0.0)
        delta = pos - neg
        gain, published, applied, f_applied, low, high = publish(gain, published, delta, active_mask)
        phases[phase] += np.column_stack((pos, -neg, delta, applied, f_applied, low, high, pos + neg))

    for t in range(2000):
        if guard is not None and t % 50 == 0:
            guard()
        if t == 500:
            onset_kc, onset_dan = np.column_stack((rk, ek)), np.column_stack((rd, bd, ed))
            onset_gains, onset_double_gains = published.copy(), gain.copy()
        rk += kc[t] * R
        rd += dmean[t] * R
        advance(DT, None if t < 500 else 0 if t < 650 else 1 if t < 1500 else 2)
    endpoint_kc, endpoint_dan = np.column_stack((rk, ek)), np.column_stack((rd, bd, ed))
    electrical_gains, electrical_double_gains = published.copy(), gain.copy()
    advance(math.inf, 3)
    grouped = np.zeros((4, 8, len(FIELDS)))
    for phase in range(4):
        for field in range(len(FIELDS)):
            grouped[phase, :, field] = np.bincount(groups, weights=phases[phase, :, field], minlength=8)
    absolute_area = phases[..., 7].sum(0)
    # A global total-variation envelope excludes any intermediate excursion,
    # including between publication boundaries, when strictly inside bounds.
    margin = np.minimum(initial.astype(float) - 0.5, 1.5 - initial.astype(float))
    excursion_excluded = (~active_mask) | (absolute_area < margin)
    return dict(
        gains=published,
        double_gains=gain,
        edge_phases=phases,
        group_phases=grouped,
        onset_kc=onset_kc,
        onset_dan=onset_dan,
        onset_gains=onset_gains,
        onset_double_gains=onset_double_gains,
        endpoint_kc=endpoint_kc,
        endpoint_dan=endpoint_dan,
        electrical_gains=electrical_gains,
        electrical_double_gains=electrical_double_gains,
        zero_crossings=crossing_counts,
        absolute_area=absolute_area,
        excursion_excluded=excursion_excluded,
    )


# Artifact boundary is deliberately separate from the signal operator above.
# Building/validating a manifest never evaluates the candidate.

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAPTURE = HERE / "onset-history-captures/onset-history-capture-4343c21535c43f42"
DOCS = ROOT / "docs/evidence/reward-mechanism-repair-2026-09-12"
PARAMETERS = dict(
    rate_tau_ms=100.0,
    baseline_tau_ms=500.0,
    eligibility_tau_ms=500.0,
    eta=0.0005,
    normalization=0.96,
    onset_ms=100.0,
    endpoint_ms=400.0,
    dt_ms=0.2,
    bounds=[0.5, 1.5],
    history="continuous",
    signal="positive_rectified_rate_contrast",
    writes="one_per_complete_step_and_one_full_tail",
    initial="independent_unit_float32",
    feedback=False,
    native_calls=0,
    candidate_evaluations=32,
    wall_cap_seconds=600.0,
)
RUNS = ("diag-rate-bridge-v1-maskgamma-de050d773763", "diag-rate-bridge-v1-maskgamma-dea14759e9ca")
CAPTURE_HASH = "244b4dcc1aa40b8c0c7be068bf7e66f8e369921f1005dd474ca37f9460dabb1b"
RECEIPT_HASH = "9aeea0c9227bf9ad4326277c39eb47966d5ab95ba6870bb3720f0d9b278788fc"
SAMPLES_HASH = "5f2414ffe5cab3d99cc1c1f0e91071df1f48721a7709816e90360af8b41074b3"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def exact_rows():
    panels = (
        (4362, 4366, 4370, 4374, 4378, 4383, 4387, 4391),
        (4395, 4399, 4404, 4408, 4412, 4416, 4420, 4425),
    )
    return [
        dict(game=game, seed_set=noise, seed=game + 42 + panel * 2000000 + offset, run_id=RUNS[panel])
        for panel, games in enumerate(panels)
        for game in games
        for noise, offset in (("base", 0), ("alt", 1000000))
    ]


def json_bytes(data):
    value = json.loads(data, parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))

    def finite(x):
        if isinstance(x, float) and not math.isfinite(x):
            raise ValueError("Nonfinite JSON number")
        if isinstance(x, dict):
            for v in x.values():
                finite(v)
        if isinstance(x, list):
            for v in x:
                finite(v)

    finite(value)
    return value


def read_bound(entry):
    if (
        not isinstance(entry, dict)
        or set(entry) != {"path", "bytes", "sha256"}
        or type(entry["bytes"]) is not int
        or entry["bytes"] < 0
        or not isinstance(entry["sha256"], str)
        or len(entry["sha256"]) != 64
    ):
        raise ValueError("Malformed file binding")
    path = Path(entry["path"])
    if not path.is_absolute() or path.absolute() != path.resolve() or not path.is_file():
        raise ValueError("Bound path must be an existing absolute regular file without symlinks")
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    if (
        (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        or len(data) != entry["bytes"]
        or digest(data) != entry["sha256"]
    ):
        raise ValueError("Bound file changed or failed byte identity: " + str(path))
    return data


def bind(path):
    path = Path(path).absolute()
    if path != path.resolve() or not path.is_file():
        raise ValueError("Cannot bind missing/nonregular/symlinked input")
    data = path.read_bytes()
    return dict(path=str(path), bytes=len(data), sha256=digest(data))


def safe_npz(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive.infolist()
        names = [x.filename for x in members]
        if (
            len(names) > 64
            or len(names) != len(set(names))
            or any("/" in x or "\\" in x or not x.endswith(".npy") for x in names)
            or sum(x.file_size for x in members) > 128 * 1024 * 1024
        ):
            raise ValueError("Unsafe or oversized NPZ member inventory")
        declared_total = 0
        for member in members:
            with archive.open(member) as stream:
                version = np.lib.format.read_magic(stream)
                if version == (1, 0):
                    shape, fortran, dtype = np.lib.format.read_array_header_1_0(stream)
                elif version == (2, 0):
                    shape, fortran, dtype = np.lib.format.read_array_header_2_0(stream)
                else:
                    raise ValueError("Unsupported NPY format")
                if (
                    dtype.kind not in "fiub"
                    or dtype.hasobject
                    or any(type(n) is not int or n < 0 for n in shape)
                ):
                    raise ValueError("Unsafe NPY dtype or shape")
                declared = math.prod(shape) * dtype.itemsize
                declared_total += declared
                if declared_total > 128 * 1024 * 1024 or stream.tell() + declared != member.file_size:
                    raise ValueError("NPY declared allocation does not match bounded member payload")
    with np.load(io.BytesIO(data), allow_pickle=False) as z:
        result = {name: z[name] for name in z.files}
    if any(a.dtype.kind not in "fiub" or not np.isfinite(a).all() for a in result.values()):
        raise ValueError("NPZ requires finite numeric arrays without objects")
    return result


def array_identity(a):
    return dict(dtype=str(a.dtype), shape=list(a.shape), sha256=digest(np.ascontiguousarray(a).tobytes()))


def manifest_template(*, review, oracle, oracle_tests, numerical_contract):
    """Read/hash inputs only. Root changes draft to preregistered after review."""
    summary = json_bytes((CAPTURE / "summary.json").read_bytes())
    receipt = json_bytes((CAPTURE / "capture-receipt.json").read_bytes())
    paths = dict(
        capture_summary=CAPTURE / "summary.json",
        capture_receipt=CAPTURE / "capture-receipt.json",
        samples=Path(receipt["samples_path"]),
        calculator=Path(__file__),
        tests=HERE / "test_rate_adaptation_shadow.py",
        unadapted_calculator=HERE / "onset_history_capture.py",
        scientific_contract=DOCS / "rate-adaptation-shadow-preregistration.md",
        source_report=DOCS / "dopamine-signal-sources-resumed.md",
        numerical_contract=Path(numerical_contract),
        independent_review=Path(review),
        independent_oracle=Path(oracle),
        independent_oracle_tests=Path(oracle_tests),
    )
    for i, row in enumerate(summary["rows"]):
        paths[f"fine_{i:02d}"] = CAPTURE / f"fine_{i:02d}.npz"
        for history in ("cold", "continuous"):
            paths[f"{history}_{i:02d}"] = CAPTURE / row["effects"][history]["file"]
    return dict(
        schema=1,
        status="draft-not-authorized",
        scope="fixed-spike-rejection-only",
        parameters=PARAMETERS,
        rows=exact_rows(),
        files={key: bind(path) for key, path in paths.items()},
    )


def validate_manifest(manifest, *, require_review=True):
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {"schema", "status", "scope", "parameters", "rows", "files"}
        or type(manifest["schema"]) is not int
        or manifest["schema"] != 1
        or manifest["status"] != "preregistered"
        or manifest["scope"] != "fixed-spike-rejection-only"
        or json.dumps(manifest["parameters"], sort_keys=True) != json.dumps(PARAMETERS, sort_keys=True)
        or manifest["rows"] != exact_rows()
        or any(type(r[k]) is not int for r in manifest["rows"] for k in ("game", "seed"))
    ):
        raise ValueError("Only the exact root-preregistered fixed32-trial contract may execute")
    required = {
        "capture_summary",
        "capture_receipt",
        "samples",
        "calculator",
        "tests",
        "unadapted_calculator",
        "scientific_contract",
        "source_report",
        "numerical_contract",
        "independent_review",
        "independent_oracle",
        "independent_oracle_tests",
    }
    required |= {f"{kind}_{i:02d}" for i in range(32) for kind in ("fine", "cold", "continuous")}
    if not isinstance(manifest["files"], dict) or set(manifest["files"]) != required:
        raise ValueError("Manifest file inventory incomplete or extra")
    files = manifest["files"]
    if len({x["path"] for x in files.values()}) != len(files):
        raise ValueError("Manifest aliases duplicate paths")
    for key, expected in [
        ("capture_summary", CAPTURE_HASH),
        ("capture_receipt", RECEIPT_HASH),
        ("samples", SAMPLES_HASH),
        ("calculator", digest(Path(__file__).read_bytes())),
    ]:
        if files[key]["sha256"] != expected:
            raise ValueError("Fixed input/code identity differs: " + key)
    if require_review:
        review = json_bytes(read_bound(files["independent_review"]))
        if (
            review.get("status") != "passed"
            or review.get("scope") != "synthetic-numerical-and-boundary-only"
            or review.get("calculator_sha256") != files["calculator"]["sha256"]
            or review.get("tests_sha256") != files["tests"]["sha256"]
            or review.get("oracle_sha256") != files["independent_oracle"]["sha256"]
            or review.get("numerical_contract_sha256") != files["numerical_contract"]["sha256"]
        ):
            raise ValueError("Independent review missing, unsuccessful, or stale")


def validate_capture_inputs(manifest, buffers, *, guard=lambda: None):
    summary, receipt = (json_bytes(buffers[key]) for key in ("capture_summary", "capture_receipt"))
    identity = receipt["identity"]
    if (
        summary["status"] != "complete"
        or summary["calls"] != 33
        or summary["attempted_calls"] != 33
        or summary["identity"] != identity
        or identity["rows"] != exact_rows()
        or summary["run_id"] != "onset-history-capture-4343c21535c43f42"
        or [{k: row[k] for k in ("game", "seed_set", "seed", "run_id")} for row in summary["rows"]]
        != exact_rows()
        or receipt["samples_sha256"] != manifest["files"]["samples"]["sha256"]
    ):
        raise ValueError("Captured source or32-row identity differs")
    maps = safe_npz(buffers["samples"])
    if {key: array_identity(a) for key, a in maps.items()} != identity["sample_arrays"]:
        raise ValueError("Sample/anatomical mappings differ from locked capture")
    for role, size in [("kc", 4064), ("dan", 24), ("sensory", 686)]:
        cols, indices = maps[role + "_columns"], maps[role + "_indices"]
        if cols.shape != (size,) or len(np.unique(cols)) != size:
            raise ValueError("Sample columns incomplete")
        np.testing.assert_array_equal(maps["sample"][cols], indices)
    if maps["sample"].shape != (4774,) or maps["body_ids"].shape != (4774,):
        raise ValueError("Full sampled cell identity required")
    pc, mask = maps["plastic_compartments"], maps["plastic_mask"]
    if (
        pc.shape != (8866,)
        or tuple(np.bincount(pc)) != (4184, 4682)
        or tuple(np.bincount(pc, weights=mask)) != (4184, 3239)
        or np.any(maps["plastic_groups"] // 4 != pc)
    ):
        raise ValueError("Frozen full home/gamma away anatomical mask differs")
    saved = {row["name"]: row for row in summary["saved"]}
    if set(saved) != {"coarse"} | {f"fine_{i:02d}" for i in range(32)}:
        raise ValueError("Captured fine inventory incomplete")
    for i in range(32):
        guard()
        key, row = f"fine_{i:02d}", summary["rows"][i]
        meta = saved[key]
        if (
            meta["sha256"] != manifest["files"][key]["sha256"]
            or meta["bytes"] != manifest["files"][key]["bytes"]
            or meta["metadata"]["dt"] != 0.2
            or meta["metadata"]["bin_ms"] != 0.2
            or meta["metadata"]["duration_ms"] != 400.0
        ):
            raise ValueError("Fine capture file/clock binding differs")
        fine = safe_npz(buffers[key])
        if {key: array_identity(a) for key, a in fine.items()} != meta["numeric_fingerprint"]:
            raise ValueError("Fine numerical fingerprint differs")
        if fine["trace"].shape != (2000, 4774) or fine["trace"].dtype != np.int32:
            raise ValueError("Wrong actual fine raster shape/dtype")
        if not np.isin(fine["trace"], [0, 1]).all():
            raise ValueError("Lossless binary fine raster required")
        np.testing.assert_array_equal(fine["counts"][maps["sample"]], fine["trace"].sum(0))
        for history in ("cold", "continuous"):
            ck = f"{history}_{i:02d}"
            if manifest["files"][ck]["sha256"] != row["effects"][history]["sha256"]:
                raise ValueError("Comparator does not belong to this exact row")
    if digest(buffers["unadapted_calculator"]) != identity["harness_sha256"]:
        raise ValueError("Unadapted comparator implementation changed")
    return summary, maps


def _write_json(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def execute(manifest_path, manifest_sha256, out, *, clock=time.monotonic):
    """Guarded32-row invocation. No path reaches a circuit, model or production UI."""
    started = clock()

    def guard():
        if clock() - started >= 600:
            raise TimeoutError("Fixed600-second cap; partial artifacts preserved")

    manifest_binding = bind(manifest_path)
    if manifest_binding["sha256"] != manifest_sha256:
        raise ValueError("Explicit root manifest hash does not match")
    manifest_data = read_bound(manifest_binding)
    manifest = json_bytes(manifest_data)
    out = Path(out).absolute()
    output_root = HERE / "rate-adaptation-shadows"
    if (
        out.parent != output_root
        or out.name != "rate-adaptation-shadow-" + manifest_sha256[:20]
        or out != out.resolve()
        or out.exists()
    ):
        raise ValueError(
            "Use new rate-adaptation-shadows/rate-adaptation-shadow-<first20manifesthash> directory"
        )
    out.mkdir(parents=True, exist_ok=False)
    (out / "manifest.json").write_bytes(manifest_data)
    completed, attempts = [], []
    try:
        guard()
        validate_manifest(manifest)
        guard()
        buffers = {}
        for key, entry in manifest["files"].items():
            guard()
            buffers[key] = read_bound(entry)
        summary, maps = validate_capture_inputs(manifest, buffers, guard=guard)
        prior = types.ModuleType("frozen_unadapted_shadow")
        prior.__file__ = manifest["files"]["unadapted_calculator"]["path"]
        # Execute precisely verified bytes, never a second mutable file read.
        exec(compile(buffers["unadapted_calculator"], prior.__file__, "exec"), prior.__dict__)
        for i, row in enumerate(manifest["rows"]):
            guard()
            fine = safe_npz(buffers[f"fine_{i:02d}"])
            parent = fine["gains"].tobytes()
            kc, dan = fine["trace"][:, maps["kc_columns"]], fine["trace"][:, maps["dan_columns"]]
            args = (
                kc,
                dan,
                maps["plastic_kc_indices"],
                maps["plastic_compartments"],
                maps["dan_compartments"],
                maps["plastic_mask"],
                maps["plastic_groups"],
            )
            comparators = {}
            for history in ("cold", "continuous"):
                guard()
                saved = safe_npz(buffers[f"{history}_{i:02d}"])
                actual = prior.shadow(*args, history=history)
                guard()
                np.testing.assert_array_equal(actual["gains"], saved["gains"])
                np.testing.assert_allclose(
                    actual["edge_phases"], saved["edge_phases"], atol=2e-12, rtol=2e-10
                )
                np.testing.assert_array_equal(actual["onset_kc"], saved["onset_kc"])
                np.testing.assert_array_equal(actual["endpoint_kc"], saved["endpoint_kc"])
                if history == "cold":
                    np.testing.assert_array_equal(actual["gains"], fine["gains"])
                comparators[history] = saved
            attempts.append(dict(attempt=i + 1, row=row, elapsed_seconds=clock() - started))
            _write_json(out / f"attempt_{i:02d}.json", attempts[-1])
            candidate = shadow(*args, guard=guard)
            guard()
            if fine["gains"].tobytes() != parent:
                raise ValueError("Frozen actual parent checkpoint mutated")
            np.testing.assert_array_equal(candidate["onset_gains"], np.ones(8866, np.float32))
            np.testing.assert_array_equal(candidate["onset_double_gains"], np.ones(8866))
            np.testing.assert_array_equal(
                candidate["gains"][maps["plastic_mask"] == 0], np.ones(1443, np.float32)
            )
            np.testing.assert_allclose(
                candidate["onset_kc"], comparators["continuous"]["onset_kc"], atol=2e-11, rtol=2e-10
            )
            np.testing.assert_allclose(
                candidate["endpoint_kc"], comparators["continuous"]["endpoint_kc"], atol=2e-11, rtol=2e-10
            )
            raw_area = (
                comparators["continuous"]["edge_phases"][..., 0]
                - comparators["continuous"]["edge_phases"][..., 1]
            ).sum(0)
            if (
                np.any(candidate["absolute_area"] > raw_area + 2e-12)
                or not candidate["excursion_excluded"].all()
                or np.any(raw_area >= 0.5)
            ):
                raise ValueError("Per-edge domination/no-hidden-excursion proof failed")
            path = out / f"adaptation_{i:02d}.npz"
            with path.open("xb") as stream:
                np.savez_compressed(stream, **candidate, continuous_absolute_area=raw_area)
            changes = {}
            for name, data in [("adaptation", candidate), *comparators.items()]:
                changes[name] = dict(
                    published=[
                        float((data["gains"].astype(float) - 1)[maps["plastic_compartments"] == c].sum())
                        for c in range(2)
                    ],
                    attempted=[
                        float(data["edge_phases"][:, maps["plastic_compartments"] == c, 2].sum())
                        for c in range(2)
                    ],
                )
            record = dict(
                row=row,
                output=bind(path),
                changes=changes,
                bound_observations=int(candidate["edge_phases"][..., 5:7].sum()),
                parent_checkpoint_unchanged=True,
                masks_unchanged=True,
                no_hidden_excursion=True,
                domination_checked_per_edge=True,
                max_absolute_area=float(candidate["absolute_area"].max()),
            )
            completed.append(record)
            _write_json(out / f"completed_{i:02d}.json", record)
        for key, entry in manifest["files"].items():
            guard()
            if read_bound(entry) != buffers[key]:
                raise ValueError("Input changed after evaluation")
        if read_bound(manifest_binding) != manifest_data:
            raise ValueError("Manifest changed during evaluation")
        metrics = {}
        for run_id in RUNS:
            for noise in ("base", "alt"):
                rows = [
                    r for r in completed if r["row"]["run_id"] == run_id and r["row"]["seed_set"] == noise
                ]
                if len(rows) != 8:
                    raise ValueError("Missing guard-cell rows")
                for c in range(2):
                    cell = {}
                    for mode in ("adaptation", "cold", "continuous"):
                        values = np.array([r["changes"][mode]["published"][c] for r in rows])
                        mean, sd = float(values.mean()), float(values.std(ddof=1))
                        cell[mode] = dict(
                            values=values.tolist(),
                            mean=mean,
                            sd=sd,
                            limit=0.5 * sd,
                            passed=bool(abs(mean) <= 0.5 * sd),
                        )
                    metrics[f"{run_id}/{noise}/{c}"] = cell
        target = [r for r in completed if r["row"]["run_id"] == RUNS[1] and r["row"]["seed_set"] == "base"]
        contrasts = {
            mode: {
                unit: float(
                    np.mean(
                        [r["changes"]["adaptation"][unit][0] - r["changes"][mode][unit][0] for r in target]
                    )
                )
                for unit in ("published", "attempted")
            }
            for mode in ("cold", "continuous")
        }
        guard()
        report = dict(
            status="complete",
            candidate_evaluations=len(completed),
            attempted_evaluations=len(attempts),
            native_calls=0,
            manifest_sha256=manifest_sha256,
            rows=completed,
            metrics=metrics,
            second_base_home_contrasts=contrasts,
            necessary_stability_screen=bool(
                all(x["adaptation"]["passed"] for x in metrics.values())
                and all(r["bound_observations"] == 0 for r in completed)
            ),
            qualification=False,
            elapsed_seconds=clock() - started,
            note="Conditional fixed-spike rejection screen; no candidate gain affected neural activity.",
        )
        _write_json(out / "summary.pending.json", report)
        guard()
        (out / "summary.pending.json").rename(out / "summary.json")
        return report
    except BaseException as exc:
        _write_json(
            out / "failure.json",
            dict(
                status="failed-partial-preserved",
                error=repr(exc),
                attempted_evaluations=len(attempts),
                completed_evaluations=len(completed),
                native_calls=0,
                elapsed_seconds=clock() - started,
            ),
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-manifest", action="store_true")
    parser.add_argument("--review")
    parser.add_argument("--oracle")
    parser.add_argument("--oracle-tests")
    parser.add_argument("--numerical-contract")
    parser.add_argument("--manifest")
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--out")
    a = parser.parse_args()
    if a.build_manifest:
        if not all((a.review, a.oracle, a.oracle_tests, a.numerical_contract)):
            parser.error("Manifest builder needs review/oracle/oracle-tests/numerical-contract paths")
        print(
            json.dumps(
                manifest_template(
                    review=a.review,
                    oracle=a.oracle,
                    oracle_tests=a.oracle_tests,
                    numerical_contract=a.numerical_contract,
                ),
                indent=2,
                allow_nan=False,
            )
        )
    else:
        if not all((a.manifest, a.manifest_sha256, a.out)):
            parser.error("Execution needs explicit manifest/hash/new-output path")
        result = execute(a.manifest, a.manifest_sha256, a.out)
        print(
            json.dumps(
                {
                    k: result[k]
                    for k in (
                        "status",
                        "candidate_evaluations",
                        "native_calls",
                        "necessary_stability_screen",
                        "qualification",
                    )
                }
            )
        )


if __name__ == "__main__":
    main()
