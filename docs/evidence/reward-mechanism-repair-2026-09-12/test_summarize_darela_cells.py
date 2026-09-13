"""Synthetic artifact aggregation, in the recorded per-DAN array contract."""

import csv

import numpy as np
import pytest

from summarize_darela_cells import summarize


def fixture_files(tmp_path, corruption=None):
    result = tmp_path / "result"
    result.mkdir()
    atlas = tmp_path / "atlas.csv"
    with atlas.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["body_id", "graph_index", "type", "instance"])
        writer.writeheader()
        writer.writerows(
            dict(body_id=100 + j, graph_index=j, type="PPL101" if j < 2 else "PAM12", instance=str(j))
            for j in range(24)
        )
    for i in range(32):
        events = np.zeros((2000, 24), np.int32)
        mass = np.zeros((2000, 24), np.float64)
        events[499, 0] = events[500, 0] = 1
        mass[499, 0], mass[500, 0] = 1.0, 1.0 + i / 100
        bodies = np.arange(100, 124, dtype=np.int64)
        if i == 31:
            if corruption == "cell_order":
                bodies[[0, 1]] = bodies[[1, 0]]
            elif corruption == "silent_mass":
                mass[10, 3] = 1.0
            elif corruption == "nonfinite":
                mass[500, 0] = np.nan
            elif corruption == "missing_trial":
                continue
        np.savez_compressed(
            result / f"case_{i:02d}.npz",
            map__body_ids=bodies,
            map__dan_columns=np.arange(24, dtype=np.int32),
            map__dan_compartments=np.array([0, 0] + [1] * 22, np.int32),
            raw_dan_events=events,
            per_cell_release=mass,
            endpoint_state=np.ones((24, 3), np.float64),
        )
    return result, atlas


def test_full32_per_cell_counts_units_and_quiet_cells(tmp_path):
    result, atlas = fixture_files(tmp_path)
    report = summarize(result, atlas, tmp_path / "summary")
    first, quiet = report["cells"][0], report["cells"][2]
    assert first["events"] == 64 and first["pre_onset_events"] == first["admitted_events"] == 32
    assert first["admitted_release_mass"] == pytest.approx(32 + sum(range(32)) / 100)
    assert first["release_mass"] == pytest.approx(64 + sum(range(32)) / 100)
    assert (first["minimum_event_mass"], first["maximum_event_mass"]) == (1.0, 1.31)
    assert (
        quiet["events"] == 0 and quiet["minimum_event_mass"] is None and quiet["maximum_event_mass"] is None
    )
    assert len(report["cells"]) == 24 and all(x["trials"] == 32 for x in report["cells"])
    assert len(list(csv.DictReader((tmp_path / "summary/cell-summary.csv").open()))) == 24
    with pytest.raises(FileExistsError):
        summarize(result, atlas, tmp_path / "summary")


@pytest.mark.parametrize("corruption", ["cell_order", "silent_mass", "nonfinite", "missing_trial"])
def test_incomplete_or_inconsistent_saved_evidence_never_publishes(tmp_path, corruption):
    result, atlas = fixture_files(tmp_path, corruption)
    with pytest.raises((AssertionError, FileNotFoundError)):
        summarize(result, atlas, tmp_path / "summary")
    assert not (tmp_path / "summary").exists()
