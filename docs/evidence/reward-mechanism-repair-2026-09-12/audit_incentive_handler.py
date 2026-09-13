# SPDX-License-Identifier: GPL-3.0-or-later
# ruff: noqa: E402
# The child wall-clock origin deliberately precedes numerical-library imports.
# Independent source audit, September 13, 2026. Not an upstream modification.
# Authored source: Evripidis Gkanias, Copyright 2021 University of Edinburgh.
# Preserve incentive-circuit-source-2026-09-13/LICENSE and all original notices.
"""Source-only reproduction; no native simulator, network, fit or experimental data.

The upstream handler/driver retain their MIT labels; repository LICENSE and
base/circuit GPLv3+ notices are preserved verbatim in the adjacent source tree.
This audit is distributed under GPLv3 or later, without any warranty.
"""

import time

_PROCESS_STARTED = time.monotonic()

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import types

import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "incentive-circuit-source-2026-09-13"
PLAN = HERE / "incentive-handler-verification-plan-evidence-ui-2026-09-13.md"
ISIS = [-6.0, -1.2, -0.6, 0.0, 0.5, 6.0]
TAUS = (100 / 3, 60.0, 104.0)
CAP = 30.0
SOURCE_HASHES = {
    "src/incentive/handler.py": "7a943ec47bfc0db20ab2679f8b5f70f1a39dd9d646dbdac33fd99b4aecf0912a",
    "src/incentive/models_base.py": "0113fedc0f15eb8c1f5c0f94a4bd566e1723a0aac34e4ab2ca8538363187f0a7",
    "src/incentive/circuit.py": "94139014ada70594545becc730fb4e9c86e0aab584d39cf993e54d8e37acbb9a",
    "examples/run_handler_2019.py": "cb4d4109083b162ee1547f385409955d65d1bedda00de4ecdc82a038cde75e53",
    "README.md": "7bfb94640ce09dde570f08a48dd44f1a7c14dd49a8dbc64745c6bf5678580062",
    "LICENSE": "3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986",
}
FIELDS = ("time", "cs", "us", "k", "d1", "d2", "m", "w", "dR1", "dR2")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_sources(source=SOURCE):
    got = {name: sha(Path(source) / name) for name in SOURCE_HASHES}
    if got != SOURCE_HASHES:
        raise ValueError("Source content differs from pinned six-file identity")
    return got


def load_source(source=SOURCE):
    verify_sources(source)
    path = Path(source) / "src/incentive/handler.py"
    module = types.ModuleType("pinned_handler_source_audit")
    module.__file__ = str(path)
    # Compile exact saved bytes, avoiding source-tree __pycache__ mutation.
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def _inputs(cs, us, taus):
    arrays = []
    for value in (cs, us):
        raw = np.asarray(value)
        if raw.ndim != 1 or raw.dtype.kind not in "fiu" or not 0 < raw.size <= 50000:
            raise ValueError("Inputs must be nonempty finite numeric vectors")
        a = raw.astype(np.float64)
        if not np.isfinite(a).all() or np.any(a < 0):
            raise ValueError("Inputs must be nonnegative and finite")
        arrays.append(a)
    if arrays[0].shape != arrays[1].shape:
        raise ValueError("CS/US lengths must agree")
    if len(taus) != 3 or any(isinstance(t, (bool, np.bool_)) for t in taus):
        raise ValueError("Three numeric filter constants required")
    tau = np.asarray(taus, dtype=np.float64)
    if tau.shape != (3,) or not np.isfinite(tau).all() or np.any(tau < 1):
        raise ValueError("Synthetic stable-domain taus must be finite and at least one sample")
    return *arrays, tau


def scalar_events(cs, us, *, taus=TAUS):
    """Independent scalar recurrence, retaining internal versus reported weights."""
    cs, us, tau = _inputs(cs, us, taus)
    alpha = 1 / tau
    k = d1 = d2 = m = 0.0
    w = 1.0
    names = ("cs", "us", "k", "d1", "d2", "m", "w", "dR1", "dR2", "w_before", "delta_w", "internal_w")
    result = {key: np.empty(len(cs), np.float64) for key in names}
    with np.errstate(over="raise", invalid="raise"):
        for i, (c, u) in enumerate(zip(cs, us)):
            before, old_m = w, m
            k = min(2.0, max(0.0, c if i == 0 else alpha[0] * c + (1 - alpha[0]) * k))
            m = min(2.0, max(0.0, k * max(w, 0.0)))
            d1 = min(2.0, max(0.0, u if i == 0 else (1 - alpha[1]) * d1 + alpha[1] * (u - old_m)))
            d2 = min(2.0, max(0.0, u if i == 0 else (1 - alpha[2]) * d2 + alpha[2] * (u - old_m)))
            delta = (d2 - d1) * (k + w - 1)
            w = w + delta
            reported = max(w, 0.0)
            up = max(d1 - d2, np.finfo(float).eps)
            down = min(d1 - d2, -np.finfo(float).eps)
            dr1 = -up * (k - 1) - (up - down) * reported
            dr2 = down * (k - 1)
            row = (c, u, k, d1, d2, m, reported, dr1, dr2, before, delta, w)
            if not np.isfinite(row).all():
                raise ValueError("Nonfinite scalar source state")
            for key, value in zip(names, row):
                result[key][i] = value
    return result


def _observed_source(module, us_on, taus):
    original = module.dopaminergic_plasticity_rule
    before, after, changes = [], [], []

    def observe(k, d1, d2, w, w_rest, passive_effect=1.0):
        delta = original(k, d1, d2, w, w_rest, passive_effect)
        before.append(float(w))
        changes.append(float(delta))
        after.append(float(w + delta))
        return delta

    module.dopaminergic_plasticity_rule = observe
    try:
        raw = module.run_case(us_on, tau_kc=taus[0], tau_short=taus[1], tau_long=taus[2])
    finally:
        module.dopaminergic_plasticity_rule = original
    result = {name: np.asarray(value, np.float64) for name, value in zip(FIELDS, raw)}
    result.update(w_before=np.asarray(before), delta_w=np.asarray(changes), internal_w=np.asarray(after))
    if any(a.shape != result["time"].shape or not np.isfinite(a).all() for a in result.values()):
        raise ValueError("Malformed or nonfinite authored source output")
    return result


def source_events(cs, us, *, taus=TAUS):
    """Test seam: exact authored functions, explicitly synthetic input generator."""
    cs, us, taus = _inputs(cs, us, taus)
    source = load_source()
    source.handler_routine = lambda us_on: ((i * 0.015, c, u) for i, (c, u) in enumerate(zip(cs, us)))
    result = _observed_source(source, None, taus)
    result.pop("time")
    return result


def reporter_summary(cases):
    if len(cases) != 6:
        raise ValueError("All six ordered reporter cases are required")
    er, ca, er_n, ca_n = [], [], [], []
    for isi, case in zip(ISIS, cases):
        t = case["time"]
        e_mask, c_mask = (t >= -7) & (t < 1), (t >= isi) & (t < isi + 4)
        er.append(float(np.mean(-case["dR1"][e_mask])))
        ca.append(float(np.mean(case["dR2"][c_mask])))
        er_n.append(int(e_mask.sum()))
        ca_n.append(int(c_mask.sum()))
    er, ca = np.asarray(er), np.asarray(ca)
    if not np.isfinite([er, ca]).all() or np.ptp(er) == 0 or np.ptp(ca) == 0:
        raise ValueError("Nonfinite or degenerate reporter normalization")
    en, cn = (er - er.min()) / np.ptp(er), (ca - ca.min()) / np.ptp(ca)
    return dict(
        ER_means=er.tolist(),
        cAMP_means=ca.tolist(),
        ER_window_samples=er_n,
        cAMP_window_samples=ca_n,
        ER_normalized=en.tolist(),
        cAMP_normalized=cn.tolist(),
        normalized_contrast=(en - cn).tolist(),
        final_internal_w=[float(c["internal_w"][-1]) for c in cases],
        final_recorded_w=[float(c["w"][-1]) for c in cases],
    )


def _compute_case(isi):
    """Only called for the six protocols after explicit root dispatch."""
    source = _observed_source(load_source(), isi, TAUS)
    independent = scalar_events(source["cs"], source["us"])
    t = np.linspace(-7.0, 8.0, 1001, endpoint=True)
    failures = []
    for key, expected in [("time", t), ("cs", (t >= 0) & (t < 0.5)), ("us", (t >= isi) & (t < isi + 0.6))]:
        if not np.array_equal(source[key], expected):
            failures.append(key + " differs from authored grid/stimulus contract")
    errors = {}
    for key, expected in independent.items():
        difference = source[key] - expected
        errors[key] = float(np.max(np.abs(difference)))
        if not np.allclose(source[key], expected, atol=1e-12, rtol=1e-12):
            failures.append(key + " fails fixed numerical comparison")
        source["independent_" + key] = expected
        source["difference_" + key] = difference
    return source, dict(
        passed=not failures,
        validation_failures=failures,
        max_absolute_errors=errors,
        cs_samples=int(source["cs"].sum()),
        us_samples=int(source["us"].sum()),
    )


def _json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w") as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)


def _npz(path, arrays):
    with path.open("xb") as f:
        np.savez_compressed(f, **arrays)
        f.flush()
        os.fsync(f.fileno())


def execute(out, *, clock=time.monotonic, started=None):
    started = clock() if started is None else started
    out = Path(out)
    out.mkdir(parents=False, exist_ok=False)
    rows, cases = [], []

    def guard():
        elapsed = clock() - started
        if not 0 <= elapsed < CAP:
            raise TimeoutError("Source calculation30second cap")
        return elapsed

    bindings = {}
    try:
        _json(out / "status.json", dict(status="started", wall_seconds=guard(), completed_cases=0))
        source_hashes = verify_sources()
        bindings = {str(p): sha(p) for p in (Path(__file__), PLAN, HERE / "test_audit_incentive_handler.py")}
        identity = dict(
            source=source_hashes,
            bindings=bindings,
            ISIS=ISIS,
            taus=TAUS,
            samples=1001,
            grid=[-7, 8],
            cap_seconds=CAP,
            scope="authored_source_only",
        )
        _json(out / "identity.json", identity)
        guard()
        for i, isi in enumerate(ISIS):
            arrays, details = _compute_case(isi)
            guard()
            file = out / f"case_{i:02d}.npz"
            _npz(file, arrays)
            rows.append(dict(index=i, isi=isi, file=file.name, sha256=sha(file), **details))
            cases.append(arrays)
            _json(
                out / "progress.json",
                dict(
                    status="running",
                    completed_cases=sum(r["passed"] for r in rows),
                    rows=rows,
                    wall_seconds=guard(),
                ),
            )
            if not details["passed"]:
                raise ValueError("Source comparison failed; observed/reference/discrepancy arrays preserved")
            guard()
        summary = reporter_summary(cases)
        verify_sources()
        if bindings != {p: sha(p) for p in bindings}:
            raise ValueError("Audit bindings changed")
        _json(out / "summary.json", summary)
        status = dict(
            status="completed",
            completed_cases=6,
            rows=rows,
            wall_seconds=guard(),
            summary_sha256=sha(out / "summary.json"),
            source_unchanged=True,
        )
        _json(out / "status.json", status)
        guard()
        return status
    except BaseException as error:
        failure = dict(
            status="failed",
            completed_cases=sum(r["passed"] for r in rows),
            rows=rows,
            error=type(error).__name__ + ": " + str(error),
            wall_seconds=clock() - started,
        )
        _json(out / "terminal-error.json", failure)
        _json(out / "status.json", failure)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    def expired(*_):
        raise TimeoutError("Source child wall cap")

    signal.signal(signal.SIGALRM, expired)
    remaining = CAP - (time.monotonic() - _PROCESS_STARTED)
    if remaining <= 0:
        raise TimeoutError("Imports exhausted source child wall cap")
    signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        status = execute(args.out, started=_PROCESS_STARTED)
        print(json.dumps(status, allow_nan=False))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == "__main__":
    main()
