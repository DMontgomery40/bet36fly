"""Root read-only complete-array accounting audit; never computes candidate signals."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def bound(entry):
    data = Path(entry["path"]).read_bytes()
    assert len(data) == entry["bytes"]
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    return data


def close(a, b):
    np.testing.assert_allclose(a, b, atol=2e-12, rtol=2e-10)


def audit(directory):
    directory = Path(directory)
    manifest_data = (directory / "manifest.json").read_bytes()
    manifest = json.loads(manifest_data)
    report = json.loads((directory / "summary.json").read_text())
    assert hashlib.sha256(manifest_data).hexdigest() == report["manifest_sha256"]
    assert report["status"] == "complete"
    assert report["candidate_evaluations"] == report["attempted_evaluations"] == 32
    assert report["native_calls"] == 0 and report["qualification"] is False
    assert len(report["rows"]) == len(manifest["rows"]) == 32
    assert len(list(directory.glob("attempt_*.json"))) == 32
    assert len(list(directory.glob("completed_*.json"))) == 32
    for entry in manifest["files"].values():
        bound(entry)
    with np.load(manifest["files"]["samples"]["path"], allow_pickle=False) as z:
        maps = {key: z[key] for key in z.files}
    pc, mask, groups = (maps[key] for key in ("plastic_compartments", "plastic_mask", "plastic_groups"))
    mask = mask.astype(bool)
    assert tuple(np.bincount(pc)) == (4184, 4682)
    assert tuple(np.bincount(pc[mask])) == (4184, 3239)
    np.testing.assert_array_equal(groups // 4, pc)
    results = []
    greatest_area = 0.0
    max_positive_excess = max_negative_excess = 0.0
    for i, (row, record) in enumerate(zip(manifest["rows"], report["rows"], strict=True)):
        assert record["row"] == row
        assert Path(record["output"]["path"]).resolve() == (directory / f"adaptation_{i:02d}.npz").resolve()
        bound(record["output"])
        attempt = json.loads((directory / f"attempt_{i:02d}.json").read_text())
        assert attempt["attempt"] == i + 1 and attempt["row"] == row
        assert json.loads((directory / f"completed_{i:02d}.json").read_text()) == record
        with np.load(record["output"]["path"], allow_pickle=False) as z:
            a = {key: z[key] for key in z.files}
        with np.load(manifest["files"][f"continuous_{i:02d}"]["path"], allow_pickle=False) as z:
            old = {key: z[key] for key in z.files}
        for value in a.values():
            assert value.dtype.kind in "fiub" and np.isfinite(value).all()
        p = a["edge_phases"]
        assert p.shape == (4, 8866, 8) and p.dtype == np.float64
        assert a["gains"].shape == (8866,) and a["gains"].dtype == np.float32
        assert a["group_phases"].shape == (4, 8, 8)
        assert np.all(p[..., 0] >= 0) and np.all(p[..., 1] <= 0)
        close(p[..., 0] + p[..., 1], p[..., 2])
        close(p[..., 0] - p[..., 1], p[..., 7])
        close(p[..., 2], p[..., 3])  # bound-free real rows
        close(p[..., 3].sum(0), a["double_gains"] - 1)
        np.testing.assert_array_equal(p[..., 4].sum(0), a["gains"].astype(float) - 1)
        np.testing.assert_array_equal(a["gains"], a["double_gains"].astype(np.float32))
        assert not p[..., 5:7].any()
        assert not p[:, ~mask].any()
        np.testing.assert_array_equal(a["gains"][~mask], np.ones(1443, np.float32))
        np.testing.assert_array_equal(a["onset_gains"], np.ones(8866, np.float32))
        np.testing.assert_array_equal(a["onset_double_gains"], np.ones(8866))
        for key in ("onset_kc", "endpoint_kc"):
            assert a[key].shape == (4064, 2) and np.all(a[key] >= 0)
            np.testing.assert_allclose(a[key], old[key], atol=2e-11, rtol=2e-10)
        for key in ("onset_dan", "endpoint_dan"):
            assert a[key].shape == (2, 3) and np.all(a[key] >= 0)
        for phase in range(4):
            for field in range(8):
                aggregate = np.bincount(groups, weights=p[phase, :, field], minlength=8)
                close(aggregate, a["group_phases"][phase, :, field])
        # Check both nonnegative products per phase and edge, not only their sum.
        positive_excess = p[..., 0] - old["edge_phases"][..., 0]
        negative_excess = -p[..., 1] + old["edge_phases"][..., 1]
        assert np.all(positive_excess <= 2e-12)
        assert np.all(negative_excess <= 2e-12)
        max_positive_excess = max(max_positive_excess, float(positive_excess.max()))
        max_negative_excess = max(max_negative_excess, float(negative_excess.max()))
        area = (p[..., 0] - p[..., 1]).sum(0)
        old_area = (old["edge_phases"][..., 0] - old["edge_phases"][..., 1]).sum(0)
        close(area, a["absolute_area"])
        close(old_area, a["continuous_absolute_area"])
        assert np.all(area <= old_area + 2e-12) and np.all(old_area < 0.5)
        assert a["excursion_excluded"].all() and np.all(area < 0.5)
        greatest_area = max(greatest_area, float(area.max()))
        published = [float((a["gains"].astype(float) - 1)[mask & (pc == c)].sum()) for c in range(2)]
        attempted = [float(p[:, mask & (pc == c), 2].sum()) for c in range(2)]
        close(published, record["changes"]["adaptation"]["published"])
        close(attempted, record["changes"]["adaptation"]["attempted"])
        assert record["bound_observations"] == 0
        results.append(dict(row=row, published=published, attempted=attempted))
    cells = {}
    for key, stored in report["metrics"].items():
        run, noise, compartment = key.rsplit("/", 2)
        values = np.array(
            [
                r["published"][int(compartment)]
                for r in results
                if r["row"]["run_id"] == run and r["row"]["seed_set"] == noise
            ]
        )
        assert values.shape == (8,)
        mean, sd = float(values.mean()), float(values.std(ddof=1))
        passed = bool(abs(mean) <= 0.5 * sd)
        expected = dict(values=values.tolist(), mean=mean, sd=sd, limit=0.5 * sd, passed=passed)
        assert stored["adaptation"] == expected
        cells[key] = expected
    assert len(cells) == 8
    assert report["necessary_stability_screen"] == all(cell["passed"] for cell in cells.values())
    for entry in manifest["files"].values():
        bound(entry)
    return dict(
        status="passed_artifact_accounting_scope",
        rows=32,
        edges_per_row=8866,
        phase_product_comparisons=32 * 4 * 8866 * 2,
        native_calls=0,
        candidate_recalculations=0,
        input_files_verified=len(manifest["files"]),
        max_absolute_area=greatest_area,
        max_positive_domination_excess=max_positive_excess,
        max_negative_domination_excess=max_negative_excess,
        cells=cells,
        necessary_stability_screen=report["necessary_stability_screen"],
        qualification=False,
        audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit(args.directory)
    with Path(args.output).open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(
        json.dumps(
            {key: result[key] for key in ("status", "rows", "necessary_stability_screen", "qualification")}
        )
    )
