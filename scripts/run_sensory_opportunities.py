"""Finite contact-recruitment ladder and full-reset two-opportunity controls."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly.connectome import ROOT  # noqa: E402
from bet36fly.experiment import atomic_json  # noqa: E402
from bet36fly.sensory_probe import SensoryProbe  # noqa: E402
from bet36fly.sensory_opportunities import recruitment_order, encode_quality, compare_outputs  # noqa: E402
from scripts.run_sensory_assay import check_locked_files  # noqa: E402


def run(path):
    raw = path.read_bytes()
    config = json.loads(raw)
    identity = "sensory-opportunities-" + hashlib.sha256(raw).hexdigest()[:20]
    output = ROOT / "output/sensory" / identity
    if output.exists():
        raise ValueError("Refusing an existing experiment identity.")
    check_locked_files(config, ROOT)
    if json.loads((ROOT / config["prerequisite_manifest"]).read_text())["status"] != "passed":
        raise ValueError("Second-order prerequisite is not passed.")
    if config["seeds"] != [809, 907, 1009] or config["gain"] != 0.11 or config["max_calls"] != 136:
        raise ValueError("Unsupported opportunity protocol.")
    source = list(
        csv.DictReader((ROOT / "docs/evidence/sensory-backtest-goal-2026-09-13/source-grns.csv").open())
    )
    order = recruitment_order(source)
    if order != config["recruitment_order"]:
        raise ValueError("Recruitment identity mismatch.")
    probe = SensoryProbe(0.11)
    output.mkdir(parents=True)
    (output / "protocol.json").write_bytes(raw)
    manifest = dict(
        identity=identity,
        status="running",
        neural_calls=0,
        rows=[],
        pairs=[],
        input_ids=probe.input_ids,
        sample_ids=probe.sample_ids,
        output_ids=probe.output_ids,
    )
    start = time.monotonic()

    def schedule(key):
        rates = np.zeros((100, len(probe.input_ids)), np.float32)
        if key == 35:
            rates[25:75, probe.groups["bitter"]] = 18.8
        else:
            rates[25:75, [probe.input_ids.index(i) for i in order[:key]]] = 58.9
        return rates

    def trial(key, seed, phase):
        if manifest["neural_calls"] >= 136 or time.monotonic() - start > 1800:
            raise RuntimeError("Declared opportunity budget exhausted.")
        number = manifest["neural_calls"]
        manifest["neural_calls"] += 1
        atomic_json(output / "manifest.json", manifest)
        rates = schedule(key)
        row, result = probe.run(rates, seed, 0.2)
        row.update(trial=number, recruitment_key=key, phase=phase)
        np.savez_compressed(
            output / f"trial-{number:03d}.npz",
            requested_hz=rates,
            **{k: v for k, v in result.items() if isinstance(v, np.ndarray)},
        )
        row["recovery_passed"] = (
            row["tail_spikes"] <= max(1, 0.01 * row["stimulus_spikes"]) and row["output_tail_spikes"] == 0
        )
        manifest["rows"].append(row)
        atomic_json(output / "manifest.json", manifest)
        print(json.dumps(row), flush=True)
        if not row["generator_numerical_passed"] or not row["recovery_passed"]:
            raise RuntimeError("Numerical/generator/recovery guard failed.")
        return row, result

    try:
        references = {}
        for key in range(36):
            for seed in config["seeds"]:
                row, result = trial(key, seed, "ladder")
                if seed == 809:
                    references[key] = (
                        row,
                        {k: result[k].copy() for k in ["counts", "trace", "input_events"]},
                    )
        means = np.array(
            [
                np.mean([r["output_hz"] for r in manifest["rows"] if r["recruitment_key"] == key], axis=0)
                for key in range(36)
            ]
        )
        manifest["mean_outputs"] = means.tolist()
        manifest["recruitment_spearman"] = float(
            spearmanr(np.arange(35), np.log1p(means[:35]).mean(axis=1)).statistic
        )
        for case in config["examples"]:
            encoded = [
                encode_quality(q, bounds, order) for q, bounds in zip(case["qualities"], case["intervals"])
            ]
            keys = [35 if x["condition"] == "bitter" else len(x["sweet_ids"]) for x in encoded]
            for presentation in [[0, 1], [1, 0]]:
                observed = {}
                for side in presentation:
                    row, result = trial(keys[side], 809, "pair-" + case["name"])
                    reference = references[keys[side]][1]
                    if not all(np.array_equal(result[k], reference[k]) for k in reference):
                        raise RuntimeError("Order/reset repeat differs from ladder reference.")
                    observed[side] = row["output_hz"]
                manifest["pairs"].append(
                    dict(
                        name=case["name"],
                        presentation=presentation,
                        encoded=encoded,
                        home_output_hz=observed[0],
                        away_output_hz=observed[1],
                        external_contrast=compare_outputs(observed[0], observed[1]),
                        exact_reference_match=True,
                    )
                )
        pairs = {r["name"]: r for r in manifest["pairs"]}
        checks = dict(
            ladder_order=manifest["recruitment_spearman"] >= 0.9,
            equal_equal=pairs["equal"]["external_contrast"] == 0,
            poor_poor=pairs["poor"]["external_contrast"] == 0,
            good_good=pairs["good"]["external_contrast"] > 0
            and min(np.mean(pairs["good"][s + "_output_hz"]) for s in ["home", "away"]) > 1,
            poor_below_good=np.mean(pairs["poor"]["home_output_hz"])
            < np.mean(pairs["good"]["away_output_hz"]),
            good_aversive=pairs["contrast"]["external_contrast"] > 0,
            swap_good=pairs["good"]["external_contrast"] == -pairs["good_swapped"]["external_contrast"],
            swap_contrast=pairs["contrast"]["external_contrast"]
            == -pairs["contrast_swapped"]["external_contrast"],
            uncertainty_preserved=all(
                x["condition"] == "sweet_recruitment" for x in pairs["uncertain"]["encoded"]
            ),
        )
        manifest["checks"] = {k: bool(v) for k, v in checks.items()}
        manifest["status"] = "passed" if all(checks.values()) else "failed_response"
    except Exception as exc:
        manifest.update(status="failed_runtime", error=str(exc))
        raise
    finally:
        manifest["wall_seconds"] = time.monotonic() - start
        atomic_json(output / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    run(parser.parse_args().protocol)
