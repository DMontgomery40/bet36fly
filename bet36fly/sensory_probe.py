"""Source-defined second-order gustatory probes, with explicit external readout."""

from __future__ import annotations

import json

import numpy as np
import pyarrow.feather as feather
from scipy.stats import binomtest

from .connectome import ROOT
from .sensory import SensoryEngine

SECOND_ORDER = {"Clavicle": ("ANXXX462a", [19480, 514625]), "Quasimodo": ("GNG042", [15321, 15734])}


def second_order_cells(frame):
    if frame.bodyId.dtype.kind not in "iu" or not frame.bodyId.is_unique:
        raise ValueError("Native IDs must be exact and unique.")
    result = {}
    for name, (kind, expected) in SECOND_ORDER.items():
        found = frame[frame.synonyms.fillna("").str.contains("Shiu 2022: " + name, regex=False)]
        if sorted(found.bodyId.tolist()) != expected or not found.type.eq(kind).all():
            raise ValueError(f"Native source alias mismatch: {name}.")
        result[name] = expected.copy()
    return result


def sensory_gates(rows, seeds):
    by = {k: [r for r in rows if r["condition"] == k] for k in ["null", "water", "sweet", "bitter", "mixed"]}
    if any([r["seed"] for r in v] != seeds for v in by.values()):
        return dict(complete=False, passed=False)
    checks = dict(
        null_silent=all(r["total_spikes"] == 0 for r in by["null"]),
        sweet_activates=all(min(r["output_hz"]) > 1 for r in by["sweet"]),
        bitter_not_sweet=all(max(r["output_hz"]) <= 1 for r in by["bitter"]),
        mixed_retains_sweet=all(min(r["output_hz"]) > 1 for r in by["mixed"]),
        mixed_changes_quasimodo=np.mean([r["output_hz"][2:] for r in by["mixed"]])
        < np.mean([r["output_hz"][2:] for r in by["sweet"]]),
        recovery=all(
            r["tail_spikes"] <= max(1, 0.01 * r["stimulus_spikes"]) and r["output_tail_spikes"] == 0
            for r in rows
        ),
        generator_numerical=all(r["generator_numerical_passed"] for r in rows),
    )
    checks = {k: bool(v) for k, v in checks.items()}
    return dict(complete=True, passed=all(checks.values()), checks=checks)


class SensoryProbe:
    """Full retained graph at a declared magnitude; no lesions or fitted readout."""

    def __init__(self, gain=0.11):
        source = json.loads((ROOT / "configs/sensory-assay-01.json").read_text())
        raw = feather.read_table(ROOT / "data/raw/annotations.feather").to_pandas()
        outputs = second_order_cells(raw)
        self.output_ids = sum(outputs.values(), [])
        self.input_ids = sorted(sum([source["populations"][k] for k in ["sweet", "water", "bitter"]], []))
        self.sample_ids = self.input_ids + self.output_ids + source["populations"]["MN9"]
        self.groups = {
            k: np.array([self.input_ids.index(i) for i in source["populations"][k]], np.int32)
            for k in ["sweet", "water", "bitter"]
        }
        brain = ROOT / "data/brain"
        ids, ptr, post, counts, signs = [
            np.load(brain / f"{k}.npy", mmap_mode="r") for k in ["ids", "indptr", "post", "counts", "signs"]
        ]
        weights = counts * np.repeat(signs.astype(np.float32), np.diff(ptr)) * np.float32(gain)
        self.engine = SensoryEngine(ptr, post, weights, np.searchsorted(ids, self.input_ids).astype(np.int32))
        self.sample = np.searchsorted(ids, self.sample_ids).astype(np.int32)
        self.output_local = np.arange(len(self.input_ids), len(self.input_ids) + 4)

    def schedule(self, values):
        rates = np.zeros((100, len(self.input_ids)), np.float32)
        for group, hz in values.items():
            rates[25:75, self.groups[group]] = hz
        return rates

    def run(self, rates, seed, dt=0.2):
        result = self.engine.run(rates, seed=seed, dt=dt, bin_ms=20, sample=self.sample)
        generator = []
        # Test every distinct requested rate across its cell/bin exposures.
        for hz in np.unique(rates):
            mask = rates == hz
            events = int(result["input_events"][mask].sum())
            generator.append(
                float(binomtest(events, round(20 / dt) * int(mask.sum()), float(hz) * dt / 1000).pvalue)
                if hz
                else float(events == 0)
            )
        row = dict(
            seed=seed,
            dt_ms=dt,
            output_hz=result["trace"][25:75, self.output_local].sum(axis=0).tolist(),
            MN9_hz=result["trace"][25:75, -2:].sum(axis=0).tolist(),
            tail_spikes=int(result["population"][-10:].sum()),
            output_tail_spikes=int(result["trace"][-10:, self.output_local].sum()),
            stimulus_spikes=int(result["population"][25:75].sum()),
            total_spikes=int(result["counts"].sum()),
            generator_numerical_passed=bool(
                min(generator) >= 1e-6
                and not result["population"][:25].any()
                and np.mean(result["counts"] / 2 > 100) < 0.05
            ),
            generator_p=generator,
            wall_seconds=result["wall_seconds"],
        )
        return row, result
