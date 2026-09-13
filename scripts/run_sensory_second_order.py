"""Fresh-seed second-order sensory response; feeding remains unqualified."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly.connectome import ROOT  # noqa: E402
from bet36fly.experiment import atomic_json  # noqa: E402
from bet36fly.sensory_probe import SensoryProbe, sensory_gates  # noqa: E402
from scripts.run_sensory_assay import check_locked_files  # noqa: E402


def run(path):
    raw = path.read_bytes()
    config = json.loads(raw)
    identity = "sensory-second-order-" + hashlib.sha256(raw).hexdigest()[:20]
    output = ROOT / "output/sensory" / identity
    if output.exists():
        raise ValueError("Refusing an existing experiment identity.")
    check_locked_files(config, ROOT)
    if config["seeds"] != [503, 601, 701] or config["gain"] != 0.11 or config["dt_ms"] != [0.2, 0.1]:
        raise ValueError("Unsupported second-order assay schedule.")
    source = json.loads((ROOT / "configs/sensory-assay-01.json").read_text())
    probe = SensoryProbe(config["gain"])
    output.mkdir(parents=True)
    (output / "protocol.json").write_bytes(raw)
    manifest = dict(
        identity=identity,
        status="running",
        neural_calls=0,
        rows=[],
        assays=[],
        input_ids=probe.input_ids,
        sample_ids=probe.sample_ids,
        output_ids=probe.output_ids,
    )
    atomic_json(output / "manifest.json", manifest)
    started = time.monotonic()
    try:
        for dt in config["dt_ms"]:
            first = None
            rows = []
            trials = [(c, s) for c in source["conditions"] for s in config["seeds"]]
            trials.append((source["conditions"][2], config["seeds"][0]))
            for condition, seed in trials:
                if time.monotonic() - started > 1800 or manifest["neural_calls"] >= 32:
                    raise RuntimeError("Declared assay budget exhausted.")
                number = manifest["neural_calls"]
                manifest["neural_calls"] += 1
                atomic_json(output / "manifest.json", manifest)
                rates = probe.schedule(condition["rates_hz"])
                row, result = probe.run(rates, seed, dt)
                row.update(condition=condition["name"], trial=number, repeat=len(rows) == 15)
                np.savez_compressed(
                    output / f"trial-{number:02d}.npz",
                    requested_hz=rates,
                    **{k: v for k, v in result.items() if isinstance(v, np.ndarray)},
                )
                if condition["name"] == "sweet" and seed == config["seeds"][0]:
                    current = [result[k].copy() for k in ["counts", "trace", "input_events"]]
                    if first is None:
                        first = current
                    else:
                        row["exact_repeat_passed"] = all(np.array_equal(a, b) for a, b in zip(first, current))
                rows.append(row)
                manifest["rows"].append(row)
                print(json.dumps(row), flush=True)
                atomic_json(output / "manifest.json", manifest)
                if not row["generator_numerical_passed"] or row.get("exact_repeat_passed") is False:
                    raise RuntimeError("Generator, numerical or exact repeat failure.")
            manifest["assays"].append(dict(dt_ms=dt, **sensory_gates(rows[:15], config["seeds"])))
        sweet = [
            np.mean(
                [
                    r["output_hz"]
                    for r in manifest["rows"]
                    if r["dt_ms"] == dt and r["condition"] == "sweet" and not r["repeat"]
                ],
                axis=0,
            )
            for dt in config["dt_ms"]
        ]
        manifest["half_dt_relative_change"] = (np.abs(sweet[1] - sweet[0]) / np.maximum(sweet[0], 1)).tolist()
        manifest["half_dt_passed"] = max(manifest["half_dt_relative_change"]) <= 0.2
        manifest["status"] = (
            "passed"
            if all(a["passed"] for a in manifest["assays"]) and manifest["half_dt_passed"]
            else "failed_response"
        )
    except Exception as exc:
        manifest["status"] = "failed_runtime"
        manifest["error"] = str(exc)
        raise
    finally:
        manifest["wall_seconds"] = time.monotonic() - started
        atomic_json(output / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    run(parser.parse_args().protocol)
