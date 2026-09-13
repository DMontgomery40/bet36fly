"""Prepare or execute the frozen offline PPL101 basis accounting."""

from pathlib import Path
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
import numpy as np

from ppl101_signal_basis import (
    signal_basis,
    relaxed_guard_envelope,
    prefix_linear_applicability,
    AREA_ATOL,
    PREFIX_MARGIN,
)

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent
EVIDENCE = ROOT / "docs/evidence/reward-mechanism-repair-2026-09-12"
CAP = HERE / "onset-history-captures/onset-history-capture-4343c21535c43f42"
PLAN = HERE / "ppl101-signal-basis-frozen-2026-09-13.json"


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, data):
    with Path(path).open("x") as f:
        json.dump(data, f, indent=2, allow_nan=False)
        f.write("\n")


def prepare():
    capture = read(CAP / "summary.json")
    assert capture["status"] == "complete" and len(capture["rows"]) == 32
    paths = [
        HERE / name
        for name in (
            "ppl101_signal_basis.py",
            "test_ppl101_signal_basis.py",
            "run_ppl101_signal_basis.py",
            "ppl101-signal-basis-preregistration-2026-09-13.md",
        )
    ] + [CAP / name for name in ("summary.json", "capture-receipt.json")]
    paths += [
        EVIDENCE / name
        for name in (
            "onset-capture-preregistration.json",
            "onset-capture-preregistration.samples.npz",
        )
    ] + [ROOT / "bet36fly/reward_lif.cpp"]
    paths += [
        CAP / f"{kind}_{i:02d}{suffix}.npz"
        for i in range(32)
        for kind, suffix in (("fine", ""), ("shadow", "_cold"))
    ]
    bindings = [dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size, sha256=sha(p)) for p in paths]
    identity = dict(
        analysis="ppl101-signal-basis-v1",
        bindings=bindings,
        rows=[{k: r[k] for k in ("run_id", "game", "seed_set", "seed")} for r in capture["rows"]],
        circuit_calls=0,
        wall_cap_seconds=120,
    )
    sid = (
        "ppl101-signal-basis-"
        + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:20]
    )
    write(PLAN, dict(identity=identity, run_id=sid, prepared_at=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(dict(run_id=sid, input_files=len(bindings), bytes=sum(x["bytes"] for x in bindings))))


def execute():
    plan = read(PLAN)
    identity = plan["identity"]
    sid = plan["run_id"]
    assert (
        sid
        == "ppl101-signal-basis-"
        + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:20]
    )

    def verify():
        for item in identity["bindings"]:
            p = ROOT / item["path"]
            assert not p.is_symlink() and p.stat().st_size == item["bytes"] and sha(p) == item["sha256"], p

    verify()
    output = HERE / sid
    output.mkdir(exist_ok=False)
    write(output / "identity.json", plan)
    start = time.monotonic()
    capture = read(CAP / "summary.json")
    with np.load(EVIDENCE / "onset-capture-preregistration.samples.npz", allow_pickle=False) as z:
        maps = {k: z[k] for k in z.files}
    home = maps["plastic_compartments"] == 0
    assert home.sum() == 4184 and np.all(maps["plastic_mask"][home] == 1)
    home_pk = maps["plastic_kc_indices"][home]
    home_dan = maps["dan_columns"][maps["dan_compartments"] == 0]
    bodies = maps["body_ids"][home_dan]
    assert set(bodies) == {11327, 11900} and len(home_dan) == 2
    bases = []
    rows = []
    max_error = 0.0
    max_area = 0.0
    for i, row in enumerate(identity["rows"]):
        if time.monotonic() - start >= 120:
            raise RuntimeError("Fixed analysis wall cap reached")
        saved = capture["saved"][i + 1]
        assert saved["file"] == f"fine_{i:02d}.npz" and saved["sha256"] == sha(CAP / saved["file"])
        with np.load(CAP / saved["file"], allow_pickle=False) as z:
            trace = z["trace"]
            original_gain = z["gains"][home]
            assert trace.shape == (2000, 4774) and np.isin(trace, (0, 1)).all()
            np.testing.assert_array_equal(
                trace[:, home_dan].sum(0), z["dan_counts"][maps["dan_compartments"] == 0]
            )
        with np.load(CAP / f"shadow_{i:02d}_cold.npz", allow_pickle=False) as z:
            expected = z["edge_phases"][:, home, :3].sum(0)
            np.testing.assert_array_equal(z["gains"][home], original_gain)
        basis = signal_basis(trace[:, maps["kc_columns"]], trace[:, home_dan])[home_pk]
        pooled = basis.mean(axis=1)
        error = float(np.max(abs(pooled - expected)))
        max_error = max(max_error, error)
        np.testing.assert_allclose(pooled, expected, atol=AREA_ATOL, rtol=0)
        if error > AREA_ATOL:
            raise ValueError("Canonical areas exceed the frozen absolute allowance")
        np.testing.assert_array_equal((1 + pooled[:, 2]).astype(np.float32), original_gain)
        area = float(np.max(basis[:, :, 0] - basis[:, :, 1]))
        max_area = max(max_area, area)
        with (output / f"basis_{i:02d}.npz").open("xb") as f:
            np.savez_compressed(
                f, home_edge_indices=np.flatnonzero(home), home_pk=home_pk, dan_body_ids=bodies, areas=basis
            )
        bases.append(basis[:, :, 2])
        rows.append(
            dict(
                **row,
                individual_attempted=basis[:, :, 2].sum(0).tolist(),
                pooled_attempted=float(pooled[:, 2].sum()),
                published=float((original_gain.astype(float) - 1).sum()),
                maximum_true_absolute_area=area,
                maximum_canonical_area_error=error,
                home_dan_counts=trace[:, home_dan].sum(0).tolist(),
                post_onset_home_dan_counts=trace[500:, home_dan].sum(0).tolist(),
                full_history_dan_disagreements=int(
                    np.count_nonzero(trace[:, home_dan[0]] != trace[:, home_dan[1]])
                ),
                all_home_gain_bytes_match=True,
            )
        )
        write(output / f"row_{i:02d}.json", rows[-1])
    applicable = prefix_linear_applicability(max_area)
    envelopes = {}
    for panel in range(2):
        for noise in ("base", "alt"):
            ids = [i for i, r in enumerate(rows) if i // 16 == panel and r["seed_set"] == noise]
            assert len(ids) == 8
            envelopes[f"{panel}/{noise}"] = (
                relaxed_guard_envelope(np.stack([bases[i] for i in ids])) if applicable else None
            )
    verify()
    elapsed = time.monotonic() - start
    if elapsed >= 120:
        raise RuntimeError("Fixed analysis wall cap reached during final validation")
    result = dict(
        run_id=sid,
        status="complete",
        rows=rows,
        envelopes=envelopes,
        unclipped_linear_bounds_applicable=applicable,
        prefix_numerical_margin=PREFIX_MARGIN,
        prefix_error_scope="Conditional on the declared per-product integration allowance; no formal arbitrary-prefix numerical proof.",
        maximum_true_absolute_area=max_area,
        maximum_canonical_area_error=max_error,
        all_32_published_home_gain_vectors_match=True,
        wall_seconds=elapsed,
        circuit_calls=0,
        network_requests=0,
        scope="Fixed-history basis and necessary bounds only; no weight selection, anatomy map or candidate qualification.",
    )
    write(output / "summary.json", result)
    print(json.dumps({k: v for k, v in result.items() if k not in ("rows", "envelopes")}))
    print(json.dumps(envelopes, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    prepare() if args.prepare else execute()
