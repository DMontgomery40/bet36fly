"""One preregistered 2023 confirmation; no refitting or adaptive holdout retry."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
import sklearn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly.connectome import ROOT, digest  # noqa: E402
from bet36fly.experiment import atomic_json  # noqa: E402
from bet36fly.features import build_features  # noqa: E402
from bet36fly.sensory_backtest import (
    quality_keys,
    neural_features,
    readout_probability,
    encoder_probability,
    paired_evaluation,
)  # noqa: E402
from bet36fly.sensory_data import normalize_season  # noqa: E402
from scripts.run_sensory_assay import check_locked_files  # noqa: E402


def preflight(config, root=ROOT):
    if (
        config["attempt"] != 1
        or config["year"] != 2023
        or config["alpha"] != 0.025
        or config["replicates"] != 10000
    ):
        raise ValueError("Unsupported confirmation allocation; never reuse a failed holdout.")
    check_locked_files(config, root)
    if config["library_versions"] != {
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "sklearn": sklearn.__version__,
    }:
        raise ValueError("Frozen library versions differ.")
    for field, status in [
        ("development_manifest", "completed_development"),
        ("opportunities_manifest", "passed"),
        ("silenced_manifest", "passed"),
    ]:
        if json.loads((root / config[field]).read_text())["status"] != status:
            raise ValueError("A required confirmation prerequisite is incomplete.")
    candidate = json.loads((root / config["candidate"]).read_text())
    check_locked_files({"file_sha256": candidate["source_locks"]}, root)
    return candidate


def run(path):
    raw_config = path.read_bytes()
    config = json.loads(raw_config)
    identity = "sensory-confirmation-" + hashlib.sha256(raw_config).hexdigest()[:20]
    output = ROOT / "output/sensory-sports" / identity
    if output.exists():
        raise ValueError("Refusing existing confirmation identity; outcomes may already be exposed.")
    candidate = preflight(config)
    output.mkdir(parents=True)
    (output / "protocol.json").write_bytes(raw_config)
    manifest = dict(
        identity=identity,
        status="preregistered",
        attempt=1,
        year=2023,
        candidate_sha256=digest(ROOT / config["candidate"]),
        created_at=datetime.now(timezone.utc).isoformat(),
        fitted_parameters_changed=False,
        new_neural_calls=0,
        source_accessed=False,
    )
    atomic_json(output / "manifest.json", manifest)
    try:
        url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameType=R&season=2023"
        manifest.update(status="fetching_source", source_url=url, source_accessed=True)
        atomic_json(output / "manifest.json", manifest)
        with urllib.request.urlopen(url, timeout=60) as response:
            raw = response.read()
        (output / "source-2023.json").write_bytes(raw)
        manifest.update(
            status="source_retrieved",
            source_sha256=hashlib.sha256(raw).hexdigest(),
            source_fetched_at=datetime.now(timezone.utc).isoformat(),
        )
        atomic_json(output / "manifest.json", manifest)
        confirmation, exclusions = normalize_season(json.loads(raw), 2023)
        if len(confirmation) < 2000:
            raise ValueError("Insufficient eligible confirmation sample.")
        history = json.loads((ROOT / config["development_games"]).read_text())
        if any(g["season"] not in [2019, 2020, 2021, 2022] for g in history):
            raise ValueError("History contains protected/future rows.")
        all_games = history + confirmation
        if len({g["id"] for g in all_games}) != len(all_games):
            raise ValueError("Duplicate history/confirmation IDs.")
        built = build_features(all_games)
        games = built["games"]
        keep = np.array([g["season"] == 2023 for g in games])
        x = built["X"][keep]
        y = (built["y"][keep] == 0).astype(int)
        fixtures = [g for g, k in zip(games, keep) if k]
        keys = quality_keys(x, candidate["encoder"])
        z = neural_features(keys, candidate["mean_outputs"])
        predictions = dict(
            neural=readout_probability(z, candidate["readout"]),
            encoder_only=encoder_probability(x, candidate["encoder"]),
            same_information=encoder_probability(x, candidate["same_information_encoder"]),
            uniform=np.full(len(y), 0.5),
            prior=np.full(len(y), candidate["training_prior"]),
            circuit_silenced=readout_probability(np.zeros_like(z), candidate["readout"]),
        )
        if not np.array_equal(predictions["circuit_silenced"], np.full(len(y), 0.5)):
            raise ValueError("Silenced readout contract changed.")
        dates = [g["start_time"] for g in fixtures]
        evaluation = paired_evaluation(y, predictions, dates, 10000, 0.025)
        evaluation.update(
            interpretation=candidate["interpretation"],
            start=dates[0],
            end=dates[-1],
            exclusions=exclusions,
            probability_tie_rule="p_home>=0.5 selects home; accuracy of uniform/silenced is therefore always-home accuracy, not random-guess expectation.",
            independence_limit="Historical unused-year confirmation after 2022 development selection; retrospective source corrections and within-season time dependence remain limitations.",
            neural_incremental_advantage=evaluation["paired_loss"]["encoder_only"]["interval"][1] < 0,
        )
        with (output / "predictions.csv").open("w") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "game_id",
                    "start_time",
                    "home",
                    "away",
                    "home_win",
                    *predictions,
                    "home_quality",
                    "away_quality",
                    "home_lo",
                    "home_hi",
                    "away_lo",
                    "away_hi",
                    "home_contact_key",
                    "away_contact_key",
                    *[f"neural_difference_{i}" for i in range(4)],
                ]
            )
            for i, g in enumerate(fixtures):
                writer.writerow(
                    [
                        g["id"],
                        g["start_time"],
                        g["home"],
                        g["away"],
                        int(y[i]),
                        *[float(p[i]) for p in predictions.values()],
                        float(keys["home_q"][i]),
                        float(keys["away_q"][i]),
                        *keys["home_bounds"][i],
                        *keys["away_bounds"][i],
                        int(keys["home_keys"][i]),
                        int(keys["away_keys"][i]),
                        *z[i],
                    ]
                )
        atomic_json(output / "evaluation.json", evaluation)
        manifest.update(
            status="passed_confirmation" if evaluation["goal_passed"] else "failed_confirmation",
            evaluation=evaluation,
            artifact_sha256={
                p.name: digest(p) for p in output.iterdir() if p.is_file() and p.name != "manifest.json"
            },
        )
        print(json.dumps(evaluation, indent=2), flush=True)
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
