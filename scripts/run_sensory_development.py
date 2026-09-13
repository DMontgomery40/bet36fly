"""Finite 2019–2022 development batch; refuses access to confirmation years."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly.connectome import ROOT, digest  # noqa: E402
from bet36fly.experiment import atomic_json  # noqa: E402
from bet36fly.features import build_features  # noqa: E402
from bet36fly.sensory_backtest import (
    C_VALUES,
    fit_encoder,
    encoder_probability,
    quality_keys,
    neural_features,
    fit_readout,
    readout_probability,
    metrics,
    paired_evaluation,
)  # noqa: E402
from scripts.run_sensory_assay import check_locked_files  # noqa: E402


def run(path):
    raw = path.read_bytes()
    config = json.loads(raw)
    identity = "sensory-development-" + hashlib.sha256(raw).hexdigest()[:20]
    output = ROOT / "output/sensory-sports" / identity
    if output.exists():
        raise ValueError("Refusing an existing development identity.")
    check_locked_files(config, ROOT)
    prerequisite = json.loads((ROOT / config["prerequisite_manifest"]).read_text())
    if prerequisite["status"] != "passed":
        raise ValueError("Opportunity prerequisite has not passed.")
    games = json.loads((ROOT / config["games"]).read_text())
    if any(g["season"] not in [2019, 2020, 2021, 2022] for g in games) or len(
        {g["id"] for g in games}
    ) != len(games):
        raise ValueError("Invalid development source identity or protected-year access.")
    built = build_features(games)
    games = built["games"]
    x = built["X"]
    y = (built["y"] == 0).astype(int)
    train = np.array([g["season"] <= 2021 for g in games])
    dev = np.array([g["season"] == 2022 for g in games])
    if int(train.sum()) != 5742 or int(dev.sum()) != 2429 or not np.isin(built["y"], [0, 2]).all():
        raise ValueError("Frozen eligible development split changed.")
    dates = [g["start_time"] for g in games]
    cache = np.asarray(prerequisite["mean_outputs"], float)
    output.mkdir(parents=True)
    (output / "protocol.json").write_bytes(raw)
    manifest = dict(
        identity=identity,
        status="running",
        encoder_fits=0,
        readout_fits=0,
        candidates=[],
        confirmation_accessed=False,
    )
    atomic_json(output / "manifest.json", manifest)
    candidates = []
    encoders = []
    try:
        for ec in C_VALUES:
            encoder = fit_encoder(x[train], y[train], np.asarray(dates)[train], ec, 100)
            manifest["encoder_fits"] += 101
            keys = quality_keys(x, encoder)
            z = neural_features(keys, cache)
            ep = encoder_probability(x, encoder)
            encoders.append(
                dict(C=ec, encoder=encoder, probabilities=ep, development=metrics(y[dev], ep[dev]))
            )
            for dc in C_VALUES:
                readout = fit_readout(z[train], y[train], dc)
                manifest["readout_fits"] += 1
                p = readout_probability(z, readout)
                cid = f"encoder-{ec}-readout-{dc}"
                candidate = dict(
                    id=cid,
                    encoder_C=ec,
                    readout_C=dc,
                    training=metrics(y[train], p[train]),
                    development=metrics(y[dev], p[dev]),
                )
                manifest["candidates"].append(candidate)
                candidates.append(
                    dict(**candidate, encoder=encoder, readout=readout, probabilities=p, keys=keys)
                )
                atomic_json(output / "manifest.json", manifest)
                print(json.dumps(candidate), flush=True)
                with (output / (cid + "-development.csv")).open("w") as f:
                    writer = csv.writer(f)
                    writer.writerow(["game_id", "start_time", "home_win", "neural_p_home", "encoder_p_home"])
                    writer.writerows(
                        (g["id"], g["start_time"], int(label), float(a), float(b))
                        for g, label, a, b, keep in zip(games, y, p, ep, dev)
                        if keep
                    )
        selected = min(
            candidates, key=lambda c: (c["development"]["log_loss"], c["encoder_C"], c["readout_C"])
        )
        baseline = min(encoders, key=lambda e: (e["development"]["log_loss"], e["C"]))
        prior = float(y[train].mean())
        ep = encoder_probability(x, selected["encoder"])
        predictions = dict(
            neural=selected["probabilities"][dev],
            encoder_only=ep[dev],
            same_information=baseline["probabilities"][dev],
            uniform=np.full(dev.sum(), 0.5),
            prior=np.full(dev.sum(), prior),
            circuit_silenced=np.full(dev.sum(), 0.5),
        )
        evaluation = paired_evaluation(y[dev], predictions, np.asarray(dates)[dev])
        evaluation["interpretation"] = (
            "Development-selected results; goal_passed here is descriptive only, never confirmation."
        )
        atomic_json(output / "development-evaluation.json", evaluation)
        frozen = dict(
            schema=1,
            development_identity=identity,
            selected_id=selected["id"],
            encoder=selected["encoder"],
            readout=selected["readout"],
            same_information_encoder=baseline["encoder"],
            training_prior=prior,
            mean_outputs=cache.tolist(),
            neural_response_source=config["prerequisite_manifest"],
            source_locks=config["file_sha256"],
            interpretation="Frozen native second-order response cache with engineered absolute-quality encoder and fitted external readout. No neural plasticity, feeding qualification or innate choice.",
        )
        atomic_json(output / "candidate.json", frozen)
        keys = selected["keys"]
        with (output / "selected-development-predictions.csv").open("w") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "game_id",
                    "start_time",
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
                ]
            )
            pos = 0
            for i, g in enumerate(games):
                if not dev[i]:
                    continue
                writer.writerow(
                    [
                        g["id"],
                        g["start_time"],
                        int(y[i]),
                        *[float(p[pos]) for p in predictions.values()],
                        float(keys["home_q"][i]),
                        float(keys["away_q"][i]),
                        *keys["home_bounds"][i],
                        *keys["away_bounds"][i],
                        int(keys["home_keys"][i]),
                        int(keys["away_keys"][i]),
                    ]
                )
                pos += 1
        manifest.update(
            status="completed_development",
            selected=selected["id"],
            same_information_C=baseline["C"],
            candidate_sha256=digest(output / "candidate.json"),
            development_evaluation=evaluation,
            artifact_sha256={
                p.name: digest(p) for p in output.iterdir() if p.is_file() and p.name != "manifest.json"
            },
        )
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
