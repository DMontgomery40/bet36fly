"""Independent, output-only KC local-state and complete pair-kernel auditor.

No producer calculator, optimizer, native engine or network client is imported.
The CLI requires a separately authorized completed 32-history producer run.
"""

import argparse
import ast
from functools import lru_cache
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import signal
import time
import zipfile

import numpy as np
from scipy.sparse import csr_matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EVIDENCE = ROOT / "docs/evidence/reward-mechanism-repair-2026-09-12"
CAP = HERE / "onset-history-captures/onset-history-capture-4343c21535c43f42"
MAP = EVIDENCE / "onset-capture-preregistration.samples.npz"
ANATOMY = HERE / "kc-local-anatomy-2026-09-13"
FIT = HERE / "kc-external-refit-992cef6fb05bfdb63d2b"
CORE = (
    HERE / "kc-lateral-primary-source-2026-09-13/upstream/codes/KC_population_calcium_rate_model_functions.py"
)
CORE_SHA = "bc36f741ab7773b5f9dc298ab9610ce915067a2cc82ea73e947174ee155b3f05"
CAP_SECONDS = 120


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@lru_cache(maxsize=1)
def source_functions():
    raw = CORE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CORE_SHA:
        raise ValueError("Pinned original source core changed")
    names = {
        "adaptation_dynamics",
        "inhibition_dynamics",
        "activity_dependent_inhibition_modulation_sigmoidal",
    }
    tree = ast.parse(raw, str(CORE))
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in selected} != names:
        raise ValueError("Missing original source functions")
    scope = {"np": np}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(CORE), "exec"), scope)
    return scope


def grouped_local(spikes, params, adjacency):
    """Aggregate by rational timestamps, then execute original old-state functions."""
    spikes = np.asarray(spikes)
    if spikes.ndim != 2 or spikes.dtype.kind not in "iub" or not np.isin(spikes, [0, 1]).all():
        raise ValueError("Binary, two-dimensional raw KC history required")
    keys = {"tauKCdec", "tauinp", "tauadapt", "adaptscale", "tauinh", "inhfactor", "infp", "slf", "bline"}
    if set(params) != keys or any(
        type(v) not in (int, float) or not math.isfinite(v) for v in params.values()
    ):
        raise ValueError("Complete finite source parameter vector required")
    dt = 1 / 30
    if (
        any(params[k] <= 0 for k in ("tauKCdec", "tauinp", "slf"))
        or any(params[k] < dt for k in ("tauadapt", "tauinh"))
        or any(params[k] < 0 for k in ("adaptscale", "inhfactor", "infp"))
        or params["bline"] != 0
    ):
        raise ValueError("Invalid declared source parameter domain")
    nsteps, nk = spikes.shape
    w = csr_matrix(adjacency, dtype=np.float64, copy=True)
    row_sum = np.asarray(w.sum(axis=1)).ravel()
    if (
        w.shape != (nk, nk)
        or not np.isfinite(w.data).all()
        or (w.data < 0).any()
        or w.diagonal().any()
        or not np.all((row_sum == 0) | np.isclose(row_sum, 1, rtol=0, atol=1e-12))
    ):
        raise ValueError("Recipient-row normalized nonnegative off-diagonal CSR required")
    frame = np.arange(nsteps, dtype=np.int64) * 30 // 5000
    completed = nsteps * 30 // 5000
    counts = (
        np.stack([spikes[frame == i].sum(0, dtype=np.int64) for i in range(completed)])
        if completed
        else np.zeros((0, nk), np.int64)
    )
    states = np.zeros((completed + 1, 4, nk), np.float64)
    susceptibility = np.ones((completed + 1, nk), np.float64)
    source = source_functions()
    for i, u in enumerate(counts):
        c, lobe, adapt, inhibition = states[i]
        coefficient = 1 - dt * (1 + adapt) / params["tauKCdec"]
        if not np.isfinite(coefficient).all() or (coefficient < 0).any():
            raise ValueError("Negative or invalid old-state C/L coefficient")
        a_new = source["adaptation_dynamics"](adapt, c, params["tauadapt"], params["adaptscale"], dt)
        with np.errstate(over="ignore"):
            i_new = source["inhibition_dynamics"](
                inhibition, lobe, params["tauinh"], w * params["inhfactor"], dt
            ) * source["activity_dependent_inhibition_modulation_sigmoidal"](
                lobe, params["infp"], params["slf"]
            )
        forcing = dt * u / params["tauinp"]
        c_new = np.maximum(coefficient * c + forcing, 0)
        l_new = np.maximum(coefficient * lobe + forcing - dt * inhibition / params["tauKCdec"], 0)
        states[i + 1] = np.stack((c_new, l_new, a_new, i_new))
        if not np.isfinite(states[i + 1]).all() or (states[i + 1] < 0).any() or (l_new > c_new).any():
            raise ValueError("Local source state outside admitted domain")
        np.divide(l_new, c_new, out=susceptibility[i + 1], where=c_new > 0)
    return dict(
        counts=counts, states=states, susceptibility=susceptibility, weighted=spikes * susceptibility[frame]
    )


@lru_cache(maxsize=4)
def pair_kernel(length):
    lag = (np.arange(length)[None, :] - np.arange(length)[:, None]) * 0.2
    distance = np.abs(lag)
    return -0.0005 * np.sign(lag) * (np.exp(-distance / 500) - np.exp(-distance / 100))


def pair_reference(weighted_kc, dan_means, pk, pc, mask, onset=500):
    """Full infinite-tail gain via the antisymmetric impulse pair integral."""
    kc, dan = np.asarray(weighted_kc), np.asarray(dan_means)
    pk, pc, mask = map(np.asarray, (pk, pc, mask))
    if (
        kc.ndim != 2
        or dan.shape != (len(kc), 2)
        or type(onset) is not int
        or not 0 <= onset <= len(kc)
        or not np.isfinite(kc).all()
        or not np.isfinite(dan).all()
        or (kc < 0).any()
        or (dan < 0).any()
        or pk.ndim != 1
        or pc.shape != pk.shape
        or mask.shape != pk.shape
        or pk.dtype.kind not in "iu"
        or pc.dtype.kind not in "iu"
        or (pk < 0).any()
        or (pk >= kc.shape[1]).any()
        or not np.isin(pc, [0, 1]).all()
        or not np.isin(mask, [0, 1]).all()
    ):
        raise ValueError("Invalid pair-kernel inputs or mapping")
    kc, dan = kc[onset:].astype(np.float64), dan[onset:].astype(np.float64)
    delta = kc.T @ (pair_kernel(len(kc)) @ dan)
    ages = (len(kc) - np.arange(len(kc))) * 0.2
    rate = np.exp(-ages / 100) / 100
    eligibility = 1.25 * (np.exp(-ages / 500) - np.exp(-ages / 100))
    ek = np.column_stack((kc.T @ rate, kc.T @ eligibility))
    ed = np.column_stack((dan.T @ rate, dan.T @ eligibility))
    tail = 0.0005 * 0.96 / 0.012 * (ek[:, 0, None] * ed[None, :, 1] - ek[:, 1, None] * ed[None, :, 0])
    final = 1 + np.where(mask, delta[pk, pc], 0)
    electrical = 1 + np.where(mask, (delta - tail)[pk, pc], 0)
    if not all(np.isfinite(x).all() for x in (final, electrical, ek, ed)):
        raise ValueError("Nonfinite independent pair calculation")
    return dict(
        double_gains=final,
        gains=final.astype(np.float32),
        electrical_double_gains=electrical,
        electrical_gains=electrical.astype(np.float32),
        endpoint_kc=ek,
        endpoint_dan=ed,
    )


def point_guard(ticks):
    if len(ticks) != 8 or any(type(t) is not int for t in ticks):
        raise ValueError("Eight exact Python integer trial totals required")
    return 9 * sum(ticks) ** 2 <= 16 * sum(t * t for t in ticks)


def trial_ticks(gains):
    gains = np.asarray(gains)
    if (
        gains.dtype != np.float32
        or gains.ndim != 2
        or gains.shape[0] != 8
        or not np.isfinite(gains).all()
        or (gains < 0.5).any()
        or (gains > 1.5).any()
    ):
        raise ValueError("Eight finite bounded float32 gain vectors required")
    # Every admitted F32 value is exactly an integer multiple of 2^-24.
    exact_ticks = (gains.astype(np.float64) - 1) * 2**24
    return tuple(sum(int(v) for v in row) for row in exact_ticks)


def compare_gain_endpoints(reference, producer):
    errors, mismatches = {}, {}
    for name in ("double_gains", "electrical_double_gains", "gains", "electrical_gains"):
        expected, actual = reference[name], producer[name]
        dtype = np.float64 if "double" in name else np.float32
        if actual.shape != expected.shape or actual.dtype != dtype or not np.isfinite(actual).all():
            raise ValueError(f"Invalid gain endpoint {name}")
        if dtype == np.float64:
            errors[name] = float(np.max(np.abs(actual - expected), initial=0))
        else:
            mismatches[name] = np.flatnonzero(actual.view(np.uint32) != expected.view(np.uint32)).tolist()
    status = (
        "failed_double_comparison"
        if max(errors.values()) > 1e-11
        else "rounding_ambiguous"
        if any(mismatches.values())
        else "passed"
    )
    return dict(status=status, max_absolute_errors=errors, float32_mismatch_indices=mismatches)


def read_bytes(path, limit=128 * 1024 * 1024):
    path = Path(path)
    if path != path.resolve() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError("Nonregular, symlinked or oversized input")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("Input grew beyond read ceiling")
    return raw


def read_json(path):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("Duplicate JSON key")
            value[key] = item
        return value

    def invalid(token):
        raise ValueError("Nonfinite JSON number")

    return json.loads(
        read_bytes(path, 8 * 1024 * 1024),
        object_pairs_hook=pairs,
        parse_constant=invalid,
        parse_float=lambda s: float(s) if math.isfinite(float(s)) else invalid(s),
    )


def numeric_archive(path):
    raw = read_bytes(path)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        names = [m.filename for m in members]
        if (
            len(names) > 64
            or len(set(names)) != len(names)
            or any(not re.fullmatch(r"[A-Za-z0-9_]+\.npy", n) for n in names)
            or sum(m.file_size for m in members) > 128 * 1024 * 1024
        ):
            raise ValueError("Unsafe numeric archive inventory")
        declared = 0
        for member in members:
            with archive.open(member) as stream:
                version = np.lib.format.read_magic(stream)
                readers = {
                    (1, 0): np.lib.format.read_array_header_1_0,
                    (2, 0): np.lib.format.read_array_header_2_0,
                }
                if version not in readers:
                    raise ValueError("Unsupported NPY header")
                shape, _, dtype = readers[version](stream)
                if dtype.hasobject or (
                    dtype.kind not in "fiub"
                    and not (member.filename == "format.npy" and dtype.kind == "S" and shape == ())
                ):
                    raise ValueError("Unsafe NPY type")
                size = math.prod(shape) * dtype.itemsize
                declared += size
                if declared > 128 * 1024 * 1024 or stream.tell() + size != member.file_size:
                    raise ValueError("NPY declared allocation mismatch")
    with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
        result = {k: archive[k] for k in archive.files}
    if any(not np.isfinite(a).all() for k, a in result.items() if k != "format"):
        raise ValueError("Nonfinite numeric archive")
    return result


def verify_bindings(bindings, guard=lambda: None):
    seen = set()
    for item in bindings:
        guard()
        if (
            not isinstance(item, dict)
            or set(item) != {"path", "bytes", "sha256"}
            or type(item["bytes"]) is not int
            or item["bytes"] < 0
            or not isinstance(item["path"], str)
            or not isinstance(item["sha256"], str)
            or not re.fullmatch("[0-9a-f]{64}", item["sha256"])
        ):
            raise ValueError("Malformed frozen binding")
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts or item["path"] in seen:
            raise ValueError("Escaping or duplicate frozen path")
        seen.add(item["path"])
        path = ROOT / relative
        if (
            path != path.resolve()
            or not path.is_file()
            or path.stat().st_size != item["bytes"]
            or sha(path) != item["sha256"]
        ):
            raise ValueError(f"Frozen binding changed: {relative}")
    guard()


def expected_rows():
    panels = (
        [4362, 4366, 4370, 4374, 4378, 4383, 4387, 4391],
        [4395, 4399, 4404, 4408, 4412, 4416, 4420, 4425],
    )
    runs = ("diag-rate-bridge-v1-maskgamma-de050d773763", "diag-rate-bridge-v1-maskgamma-dea14759e9ca")
    return [
        dict(panel=p, run_id=runs[p], game=g, seed_set=noise, seed=42 + g + p * 2000000 + alt * 1000000)
        for p, games in enumerate(panels)
        for g in games
        for alt, noise in enumerate(("base", "alt"))
    ]


def write_json(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def close_comparison(actual, expected, name, *, exact=False):
    if actual.shape != expected.shape or not np.isfinite(actual).all():
        raise ValueError(f"Invalid shape/finite domain: {name}")
    okay = (
        np.array_equal(actual, expected) if exact else np.allclose(actual, expected, rtol=1e-12, atol=1e-12)
    )
    if not okay:
        raise ValueError(f"Independent reconstruction mismatch: {name}")
    return float(np.max(np.abs(actual - expected), initial=0))


def audit(run, output):
    started = time.monotonic()

    def guard():
        if time.monotonic() - started >= CAP_SECONDS:
            raise TimeoutError("Single-attempt independent audit reached 120 seconds")

    run, output = Path(run).absolute(), Path(output).absolute()
    if (
        run.parent != HERE
        or not re.fullmatch(r"kc-local-shadow-[0-9a-f]{20}", run.name)
        or run != run.resolve()
    ):
        raise ValueError("Only a fixed local shadow identity is accepted")
    if output.parent != HERE or output != output.resolve() or output.exists():
        raise ValueError("Audit output must be new and directly under the evidence output directory")
    if any(
        os.environ.get(k) != "1"
        for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
    ):
        raise ValueError("Single-thread BLAS environment must be fixed before interpreter startup")
    output.mkdir()
    previous = signal.getsignal(signal.SIGALRM)

    def alarm(signum, frame):
        raise TimeoutError("Independent audit hard internal alarm")

    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, CAP_SECONDS - (time.monotonic() - started)))
    rows, saved_reference, bindings = [], {}, []
    report = dict(
        status="incomplete",
        run_id=run.name,
        wall_cap_seconds=120,
        expected_rows=32,
        completed_rows=0,
        native_calls=0,
        network_requests=0,
        optimizer_calls=0,
    )
    try:
        if (run / "terminal-error.json").exists():
            raise ValueError("Producer terminal failure overrides earlier completion")
        plan = read_json(run / "identity.json")
        identity = plan["identity"]
        if (
            plan["run_id"] != run.name
            or "kc-local-shadow-"
            + hashlib.sha256(json.dumps(identity, sort_keys=True, allow_nan=False).encode()).hexdigest()[:20]
            != run.name
        ):
            raise ValueError("Producer identity hash mismatch")
        if (
            identity["rows"] != expected_rows()
            or identity["helper_evaluations"] != 32
            or identity["source_hz"] != 30
            or identity["native_hz"] != 5000
            or identity["fit_identity"] != FIT.name
        ):
            raise ValueError("Frozen 32-row source/input schedule mismatch")
        bindings = identity["bindings"]
        required = [
            CORE,
            MAP,
            ANATOMY / "adjacency.npz",
            ANATOMY / "identities.npz",
            FIT / "result/status.json",
            CAP / "summary.json",
            Path(__file__),
            HERE / "test_audit_kc_local_shadow.py",
            HERE / "kc-local-shadow-independent-audit-contract-2026-09-13.md",
        ] + [CAP / f"fine_{i:02d}.npz" for i in range(32)]
        if not {str(p.relative_to(ROOT)) for p in required} <= {b["path"] for b in bindings}:
            raise ValueError("Identity omits consumed source or auditor bindings")
        verify_bindings(bindings, guard)
        # Snapshot every producer artifact consumed, including row metadata.
        producer_paths = [
            run / name for name in ("identity.json", "summary.json", "completion.json", "attempts.jsonl")
        ]
        producer_paths += [
            run / f"{kind}_{i:02d}.{ext}"
            for i in range(32)
            for kind, ext in (("shadow", "npz"), ("row", "json"))
        ]
        snapshots = [
            dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size, sha256=sha(p)) for p in producer_paths
        ]
        verify_bindings(snapshots, guard)
        summary, completion = read_json(run / "summary.json"), read_json(run / "completion.json")
        if (
            summary["status"] != "computed"
            or completion["status"] != "complete"
            or any(x[k] != 32 for x in (summary, completion) for k in ("attempted", "completed"))
            or completion["summary_sha256"] != sha(run / "summary.json")
            or any(x["run_id"] != run.name for x in (summary, completion))
        ):
            raise ValueError("Producer must have a complete bound 32-row result")
        journal = [
            json.loads(line) for line in read_bytes(run / "attempts.jsonl", 8 * 1024 * 1024).splitlines()
        ]
        if [(x["event"], x["index"]) for x in journal] != [
            (event, i) for i in range(32) for event in ("attempt", "complete")
        ]:
            raise ValueError("Producer attempt/completion order mismatch")
        if len(summary["saved"]) != 32:
            raise ValueError("Incomplete producer numerical inventory")
        capture = read_json(CAP / "summary.json")
        selectors = [
            dict(panel=i // 16, **{k: x[k] for k in ("run_id", "game", "seed_set", "seed")})
            for i, x in enumerate(capture["rows"])
        ]
        if capture["status"] != "complete" or selectors != expected_rows():
            raise ValueError("Captured selectors differ from frozen schedule")
        maps = numeric_archive(MAP)
        pk, pc, mask, groups = [
            maps[k] for k in ("plastic_kc_indices", "plastic_compartments", "plastic_mask", "plastic_groups")
        ]
        if (
            any(a.shape != (8866,) or a.dtype.kind not in "iu" for a in (pk, pc, mask, groups))
            or not np.array_equal(pc, groups // 4)
            or not np.array_equal(mask, ((groups < 4) | (groups == 4)).astype(mask.dtype))
            or dict(zip(*np.unique(groups, return_counts=True)))
            != {0: 1585, 1: 316, 2: 2283, 4: 3239, 5: 1438, 6: 5}
            or (pk >= 4064).any()
        ):
            raise ValueError("Original edge order, compartments or masks invalid")
        for name, size in (("kc", 4064), ("dan", 24), ("sensory", 686)):
            cols = maps[name + "_columns"]
            if cols.shape != (size,) or not np.array_equal(maps["sample"][cols], maps[name + "_indices"]):
                raise ValueError("Original recording columns inconsistent")
        columns = np.concatenate([maps[name + "_columns"] for name in ("kc", "dan", "sensory")])
        if (
            not np.array_equal(np.sort(columns), np.arange(4774))
            or not np.array_equal(
                np.sort(maps["body_ids"][maps["dan_columns"]][maps["dan_compartments"] == 0]), [11327, 11900]
            )
            or np.bincount(maps["dan_compartments"], minlength=2).tolist() != [2, 22]
        ):
            raise ValueError("KC/DAN recording identity or 2/22 pool mismatch")
        adj = numeric_archive(ANATOMY / "adjacency.npz")
        if adj["format"].item() != b"csr" or tuple(adj["shape"]) != (4064, 4064):
            raise ValueError("Expected recipient-row 4064-KC CSR")
        w = csr_matrix((adj["data"], adj["indices"], adj["indptr"]), shape=(4064, 4064))
        w.check_format(full_check=True)
        ids = numeric_archive(ANATOMY / "identities.npz")
        if not np.array_equal(ids["kc_indices"], maps["kc_indices"]) or not np.array_equal(
            ids["body_ids"], maps["body_ids"][maps["kc_columns"]]
        ):
            raise ValueError("Contact CSR identity/order mismatch")
        fit = read_json(FIT / "result/status.json")
        params = dict(**fit["parameters"]["KD"], **fit["parameters"]["WT"], bline=fit["parameters"]["bline"])
        if fit["status"] != "completed":
            raise ValueError("External fit not complete")
        for i, selector in enumerate(expected_rows()):
            guard()
            item = summary["saved"][i]
            producer_path = run / f"shadow_{i:02d}.npz"
            if (
                item
                != dict(
                    file=producer_path.name, bytes=producer_path.stat().st_size, sha256=sha(producer_path)
                )
                or journal[2 * i + 1]["artifact"] != item
            ):
                raise ValueError("Producer array inventory/ledger mismatch")
            raw_path = CAP / f"fine_{i:02d}.npz"
            if capture["saved"][i + 1]["file"] != raw_path.name or capture["saved"][i + 1]["sha256"] != sha(
                raw_path
            ):
                raise ValueError("Raw fine capture hash/order mismatch")
            raw, producer = numeric_archive(raw_path), numeric_archive(producer_path)
            detail = read_json(run / f"row_{i:02d}.json")
            if any(detail[k] != v for k, v in selector.items()) or detail["index"] != i:
                raise ValueError("Producer row metadata reordered")
            trace = raw["trace"]
            if (
                trace.shape != (2000, 4774)
                or trace.dtype.kind not in "iu"
                or not np.isin(trace, [0, 1]).all()
                or raw["pulse_times_ms"].size
                or raw["pulse_dan_indices"].size
            ):
                raise ValueError("Complete untaught binary capture required")
            for key, expected in (
                ("plastic_mask", mask),
                ("plastic_groups", groups),
                ("original_gains", raw["gains"]),
            ):
                close_comparison(producer[key], expected, key, exact=True)
            close_comparison(trace.sum(0), raw["counts"][maps["sample"]], "recorded spike counts", exact=True)
            close_comparison(
                trace[:, maps["dan_columns"]].sum(0), raw["dan_counts"], "DAN spike counts", exact=True
            )
            kc = trace[:, maps["kc_columns"]]
            local = grouped_local(kc, params, w)
            errors = {}
            for key, expected, exact in (
                ("source_frame_counts", local["counts"], True),
                ("local_frame_states", local["states"], False),
                ("local_susceptibility", local["susceptibility"], False),
                ("raw_event_totals", kc.sum(0), True),
                ("weighted_event_totals", local["weighted"].sum(0), False),
                ("weighted_post_onset_totals", local["weighted"][500:].sum(0), False),
            ):
                errors[key] = close_comparison(producer[key], expected, key, exact=exact)
            close_comparison(
                producer["publication_counts"],
                np.array([150, 850, 500, 1])[:, None] * mask,
                "phase publication counts",
                exact=True,
            )
            bounds = producer["bound_counts"]
            if (
                bounds.shape != (2, 8866)
                or bounds.dtype != np.int64
                or (bounds < 0).any()
                or not np.array_equal(producer["edge_phases"][:, :, 5:7].sum(0).T, bounds)
            ):
                raise ValueError("Invalid bound observations")
            for key in ("gains", "double_gains", "electrical_gains", "electrical_double_gains"):
                if (
                    producer[key].shape != (8866,)
                    or (producer[key] < 0.5).any()
                    or (producer[key] > 1.5).any()
                    or np.any(producer[key][mask == 0] != 1)
                ):
                    raise ValueError("Masked or bounded gain invariant violated")
            bound_contacts = int(bounds.sum())
            if detail["bound_contacts"] != bound_contacts:
                raise ValueError("Bound contact count metadata mismatch")
            row = dict(
                index=i, selector=selector, local_max_absolute_errors=errors, bound_contacts=bound_contacts
            )
            if bound_contacts:
                row.update(
                    status="screen_rejected_bound_contacts", pair_proof="not applicable to clipped history"
                )
            else:
                dan = trace[:, maps["dan_columns"]]
                means = np.column_stack([dan[:, maps["dan_compartments"] == c].mean(axis=1) for c in (0, 1)])
                reference = pair_reference(local["weighted"], means, pk, pc, mask)
                row.update(compare_gain_endpoints(reference, producer))
                for key in ("endpoint_kc", "endpoint_dan"):
                    errors[key] = close_comparison(producer[key], reference[key], key)
                saved_reference[f"gains_{i:02d}"] = reference["gains"]
                saved_reference[f"double_gains_{i:02d}"] = reference["double_gains"]
                saved_reference[f"electrical_gains_{i:02d}"] = reference["electrical_gains"]
                saved_reference[f"electrical_double_gains_{i:02d}"] = reference["electrical_double_gains"]
            row["producer_gains"] = producer["gains"]
            rows.append(row)
            write_json(output / f"row_{i:02d}.json", {k: v for k, v in row.items() if k != "producer_gains"})
            print(json.dumps(dict(audited_rows=len(rows), status=row["status"])), flush=True)
            guard()
        guards = {}
        for panel in (0, 1):
            for noise in ("base", "alt"):
                selected = [
                    r for r in rows if r["selector"]["panel"] == panel and r["selector"]["seed_set"] == noise
                ]
                for channel, c in (("home", 0), ("away", 1)):
                    key = f"{panel}/{noise}/{channel}"
                    edges = (pc == c) & mask.astype(bool)
                    ticks = trial_ticks(np.stack([r["producer_gains"][edges] for r in selected]))
                    entry = dict(producer_ticks=ticks, producer_point_pass=point_guard(ticks))
                    if (
                        list(ticks) != summary["guards"][key]["ticks"]
                        or entry["producer_point_pass"] is not summary["guards"][key]["point_pass"]
                    ):
                        raise ValueError("Saved exact guard arithmetic differs")
                    if all(f"gains_{r['index']:02d}" in saved_reference for r in selected):
                        ref_ticks = trial_ticks(
                            np.stack([saved_reference[f"gains_{r['index']:02d}"][edges] for r in selected])
                        )
                        entry.update(reference_ticks=ref_ticks, reference_point_pass=point_guard(ref_ticks))
                    guards[key] = entry
        if len(summary["guards"]) != 8 or summary["bound_contacts"] != sum(r["bound_contacts"] for r in rows):
            raise ValueError("Incomplete guard matrix or bound total")
        verify_bindings(bindings, guard)
        verify_bindings(snapshots, guard)
        if (run / "terminal-error.json").exists():
            raise ValueError("Producer acquired terminal failure during audit")
        guard()
        with (output / "comparison.npz").open("xb") as stream:
            np.savez_compressed(stream, **saved_reference)
        numerical_status = "passed" if all(r["status"] == "passed" for r in rows) else "rejected_or_ambiguous"
        report.update(
            status=numerical_status,
            guards=guards,
            completed_rows=len(rows),
            bindings=bindings,
            producer_snapshot=snapshots,
            comparison_sha256=sha(output / "comparison.npz"),
            screen="reject"
            if numerical_status != "passed" or not all(g["producer_point_pass"] for g in guards.values())
            else "offline_screen_only_not_qualification",
        )
        guard()
    except (Exception, KeyboardInterrupt) as exc:
        report.update(
            status="budget_stopped" if isinstance(exc, TimeoutError) else "failed",
            error=f"{type(exc).__name__}: {exc}",
            completed_rows=len(rows),
            screen="invalid_or_incomplete",
        )
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    report["elapsed_seconds"] = time.monotonic() - started
    write_json(output / "audit.json", report)
    if time.monotonic() - started >= CAP_SECONDS:
        write_json(
            output / "terminal-error.json",
            dict(status="budget_stopped", elapsed_seconds=time.monotonic() - started),
        )
        report["status"] = "budget_stopped"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run, args.output)
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in {"bindings", "producer_snapshot", "guards"}},
            allow_nan=False,
        )
    )
    return 0 if result["status"] in {"passed", "rejected_or_ambiguous"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
