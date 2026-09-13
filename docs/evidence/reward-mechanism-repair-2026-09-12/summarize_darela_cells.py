"""Describe saved per-DAN release arrays; never execute a model or infer causality."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def summarize(result, atlas_path, destination):
    result, atlas_path, destination = map(Path, (result, atlas_path, destination))
    if destination.exists():
        raise FileExistsError(destination)
    paths = [result / f"case_{i:02d}.npz" for i in range(32)]
    bindings = {str(p): sha(p) for p in [*paths, atlas_path, Path(__file__)]}
    atlas = {int(row["body_id"]): row for row in csv.DictReader(atlas_path.open())}
    bodies = compartments = None
    stats = []
    for path in paths:
        with np.load(path, allow_pickle=False) as z:
            row_bodies = z["map__body_ids"][z["map__dan_columns"]]
            row_compartments = z["map__dan_compartments"]
            if bodies is None:
                bodies, compartments = row_bodies.copy(), row_compartments.copy()
                assert len(bodies) == 24 and len(set(map(int, bodies))) == 24
                stats = [
                    dict(
                        events=0,
                        pre_onset_events=0,
                        admitted_events=0,
                        release_mass=0.0,
                        admitted_release_mass=0.0,
                        minimum_event_mass=None,
                        maximum_event_mass=None,
                        endpoint_min=[float("inf")] * 3,
                        endpoint_max=[float("-inf")] * 3,
                    )
                    for _ in bodies
                ]
            np.testing.assert_array_equal(row_bodies, bodies)
            np.testing.assert_array_equal(row_compartments, compartments)
            raw, mass, endpoint = z["raw_dan_events"], z["per_cell_release"], z["endpoint_state"]
            assert raw.dtype == np.int32 and raw.shape == mass.shape == (2000, 24)
            assert mass.dtype == endpoint.dtype == np.float64 and endpoint.shape == (24, 3)
            assert np.isin(raw, [0, 1]).all() and np.isfinite(mass).all() and np.isfinite(endpoint).all()
            assert np.all(mass[raw == 0] == 0) and np.all(mass[raw == 1] > 0)
            for j, cell in enumerate(stats):
                cell["events"] += int(raw[:, j].sum())
                cell["pre_onset_events"] += int(raw[:500, j].sum())
                cell["admitted_events"] += int(raw[500:, j].sum())
                cell["release_mass"] += float(mass[:, j].sum())
                cell["admitted_release_mass"] += float(mass[500:, j].sum())
                emitted = mass[raw[:, j] == 1, j]
                if emitted.size:
                    lo, hi = float(emitted.min()), float(emitted.max())
                    cell["minimum_event_mass"] = (
                        min(lo, cell["minimum_event_mass"]) if cell["minimum_event_mass"] is not None else lo
                    )
                    cell["maximum_event_mass"] = (
                        max(hi, cell["maximum_event_mass"]) if cell["maximum_event_mass"] is not None else hi
                    )
                cell["endpoint_min"] = np.minimum(cell["endpoint_min"], endpoint[j]).tolist()
                cell["endpoint_max"] = np.maximum(cell["endpoint_max"], endpoint[j]).tolist()
    records = []
    for body, comp, cell in zip(bodies, compartments, stats, strict=True):
        identity = atlas[int(body)]
        assert identity["type"] == ("PPL101" if comp == 0 else "PAM12")
        assert cell["events"] == cell["pre_onset_events"] + cell["admitted_events"]
        records.append(
            dict(
                body_id=int(body),
                graph_index=int(identity["graph_index"]),
                type=identity["type"],
                instance=identity["instance"],
                channel="home" if comp == 0 else "away",
                trials=32,
                **cell,
            )
        )
    assert bindings == {path: sha(Path(path)) for path in bindings}
    destination.mkdir()
    report = dict(
        scope="Descriptive aggregation of32 saved untaught histories. Dimensionless engineered release mass, not concentration; pooled plasticity cannot establish an individual DAN's causal contribution.",
        bindings=bindings,
        cells=records,
    )
    (destination / "cell-summary.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    flat = [{k: v for k, v in row.items() if not isinstance(v, list)} for row in records]
    with (destination / "cell-summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--atlas", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = summarize(args.result, args.atlas, args.out)
    print(json.dumps({"cells": len(result["cells"]), "output": str(args.out)}))
