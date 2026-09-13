"""Three full-graph source-silenced controls for the frozen sensory readout."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly.connectome import ROOT  # noqa: E402
from bet36fly.experiment import atomic_json  # noqa: E402
from bet36fly.sensory_probe import SensoryProbe  # noqa: E402
from scripts.run_sensory_assay import check_locked_files  # noqa: E402


def run(path):
    raw = path.read_bytes()
    config = json.loads(raw)
    identity = "sensory-silenced-" + hashlib.sha256(raw).hexdigest()[:20]
    output = ROOT / "output/sensory" / identity
    if output.exists():
        raise ValueError("Refusing existing control identity.")
    check_locked_files(config, ROOT)
    if config["seed"] != 1103 or config["max_calls"] != 3:
        raise ValueError("Unsupported control schedule.")
    probe = SensoryProbe(0.11)
    probe.engine.weights[:] = 0
    output.mkdir(parents=True)
    (output / "protocol.json").write_bytes(raw)
    manifest = dict(identity=identity, status="running", neural_calls=0, rows=[])
    try:
        for condition, rates in [
            ("sweet", {"sweet": 58.9}),
            ("bitter", {"bitter": 18.8}),
            ("mixed", {"sweet": 58.9, "bitter": 18.8}),
        ]:
            manifest["neural_calls"] += 1
            atomic_json(output / "manifest.json", manifest)
            row, result = probe.run(probe.schedule(rates), 1103, 0.2)
            row["condition"] = condition
            np.savez_compressed(
                output / (condition + ".npz"),
                **{k: v for k, v in result.items() if isinstance(v, np.ndarray)},
            )
            row["passed"] = (
                row["generator_numerical_passed"]
                and not any(row["output_hz"])
                and not any(row["MN9_hz"])
                and row["tail_spikes"] == 0
            )
            manifest["rows"].append(row)
            print(json.dumps(row), flush=True)
        manifest["status"] = "passed" if all(r["passed"] for r in manifest["rows"]) else "failed_response"
    except Exception as exc:
        manifest.update(status="failed_runtime", error=str(exc))
        raise
    finally:
        atomic_json(output / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    run(parser.parse_args().protocol)
