"""Bounded causal MLB feature-logistic sweep over the frozen v2 split."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from itertools import groupby
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
import warnings

from .bookmaker_comparison import _fixture_ids_hash, _paired_week_interval
from .experiment import atomic_json, utcnow
from .learning import metrics


C_GRID = (0.00001, 0.0001, 0.001, 0.01, 0.1, 1.0)
FOLD_SPECS = (
    ("2024-07", "2024-07-01", "2024-08-01"),
    ("2024-08", "2024-08-01", "2024-09-01"),
    ("2024-09", "2024-09-01", "2024-10-01"),
    ("2025-05", "2025-05-01", "2025-06-01"),
    ("2025-06", "2025-06-01", "2025-07-01"),
)
FEATURE_NAMES = (
    "home_elo", "away_elo", "elo_diff",
    "home_form", "away_form", "form_diff",
    "home_win_rate", "away_win_rate",
    "home_games_played", "away_games_played",
    "home_rest", "away_rest", "rest_diff",
    "home_margin", "away_margin",
)


def _parse(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Game times must include a timezone.")
    return parsed.astimezone(timezone.utc)


def _day_start(value):
    if isinstance(value, str) and len(value) == 10:
        parsed = datetime.strptime(value, "%Y-%m-%d")
        return parsed.replace(tzinfo=timezone.utc)
    parsed = _parse(value)
    return datetime.combine(parsed.date(), time.min, timezone.utc)


def available_before(game, evaluation_day):
    """Whether a label passed the 48-hour delay before evaluation UTC-day start."""
    return _parse(game["start_time"]) + timedelta(hours=48) <= _day_start(evaluation_day)


def predeclared_configs():
    return [
        {"id": f"w{window}-{history}-{rest}", "form_window": window, "history": history, "rest": rest}
        for window in (3, 5, 10, 20, 40)
        for history in ("pooled", "home-away")
        for rest in ("none", "capped", "recovery")
    ]


@dataclass
class _History:
    games: int = 0
    wins: int = 0
    margin: float = 0.0
    recent: deque = field(default_factory=deque)


def _new_history(window):
    return _History(recent=deque(maxlen=window))


def _rest(last_day, day, transform):
    if transform == "none" or last_day is None:
        return 0.0
    days = max((day - last_day).days, 0)
    if transform == "capped":
        return min(days, 14) / 14
    if transform == "recovery":
        return 1 - math.exp(-days / 3)
    raise ValueError(f"Unknown rest transform: {transform}")


def _mean(recent):
    return float(sum(recent) / len(recent)) if recent else 0.5


def _rate(history):
    return history.wins / history.games if history.games else 0.5


def _margin(history):
    return float(np.clip(history.margin / history.games / 5, -1, 1)) if history.games else 0.0


def _usable(game):
    return (game.get("status") == "final" and game.get("outcome") in {0, 2}
            and isinstance(game.get("home_score"), int) and isinstance(game.get("away_score"), int))


def build_feature_matrix(games, config):
    if config["history"] not in {"pooled", "home-away"}:
        raise ValueError("history must be pooled or home-away")
    if config["rest"] not in {"none", "capped", "recovery"}:
        raise ValueError("rest must be none, capped, or recovery")
    window = int(config["form_window"])
    if window not in {3, 5, 10, 20, 40}:
        raise ValueError("form_window is outside the predeclared grid")
    ordered = sorted((deepcopy(g) for g in games), key=lambda g: (_parse(g["start_time"]), g["id"]))
    histories = defaultdict(lambda: _new_history(window))
    elo = defaultdict(lambda: 1500.0)
    last_day = {}
    pending = []
    rows, labels, ids = [], [], []

    def state(team, role):
        return histories[(team, "all" if config["history"] == "pooled" else role)]

    def update(game, game_day):
        home_key, away_key = game["home_key"], game["away_key"]
        home_score, away_score = game["home_score"], game["away_score"]
        home_result, away_result = (1.0, 0.0) if home_score > away_score else (0.0, 1.0)
        expected = 1 / (1 + 10 ** ((elo[away_key] - elo[home_key]) / 400))
        delta = 16 * (home_result - expected)
        elo[home_key] += delta
        elo[away_key] -= delta
        for team, role, result, margin in (
            (home_key, "home", home_result, home_score - away_score),
            (away_key, "away", away_result, away_score - home_score),
        ):
            for key in ((team, "all"), (team, role)):
                history = histories[key]
                history.games += 1
                history.wins += int(result == 1)
                history.margin += margin
                history.recent.append(result)
            last_day[team] = game_day

    for day, grouped in groupby(ordered, key=lambda g: _parse(g["start_time"]).date()):
        cutoff = datetime.combine(day, time.min, timezone.utc)
        ready = [entry for entry in pending if entry[0] <= cutoff]
        pending = [entry for entry in pending if entry[0] > cutoff]
        for _available, prior, prior_day in ready:
            update(prior, prior_day)
        for game in grouped:
            home_key, away_key = game["home_key"], game["away_key"]
            home, away = state(home_key, "home"), state(away_key, "away")
            home_form, away_form = _mean(home.recent), _mean(away.recent)
            home_rest = _rest(last_day.get(home_key), day, config["rest"])
            away_rest = _rest(last_day.get(away_key), day, config["rest"])
            rows.append([
                elo[home_key] / 2000, elo[away_key] / 2000, (elo[home_key] - elo[away_key]) / 400,
                home_form, away_form, home_form - away_form, _rate(home), _rate(away),
                min(home.games, 50) / 50, min(away.games, 50) / 50,
                home_rest, away_rest, home_rest - away_rest, _margin(home), _margin(away),
            ])
            labels.append(int(game["outcome"]) if _usable(game) else -1)
            ids.append(game["id"])
            if _usable(game):
                pending.append((_parse(game["start_time"]) + timedelta(hours=48), game, day))
    return {"game_ids": ids, "X": np.asarray(rows, dtype=np.float64),
            "y": np.asarray(labels, dtype=np.int64), "feature_names": list(FEATURE_NAMES)}


def rolling_folds(games, training_ids, *, specs=FOLD_SPECS):
    by_id = {g["id"]: g for g in games}
    unknown = set(training_ids) - set(by_id)
    if unknown:
        raise ValueError(f"Training IDs missing from games: {len(unknown)}")
    folds = []
    for name, start, end in specs:
        start_time, end_time = _day_start(start), _day_start(end)
        partition_before = [by_id[i] for i in training_ids if _parse(by_id[i]["start_time"]) < start_time]
        fit = sorted((g for g in partition_before if available_before(g, start_time.isoformat())),
                     key=lambda g: (_parse(g["start_time"]), g["id"]))
        embargoed = sorted((g for g in partition_before if not available_before(g, start_time.isoformat())),
                           key=lambda g: (_parse(g["start_time"]), g["id"]))
        evaluation = sorted((by_id[i] for i in training_ids
                             if start_time <= _parse(by_id[i]["start_time"]) < end_time),
                            key=lambda g: (_parse(g["start_time"]), g["id"]))
        if not fit or not evaluation:
            raise ValueError(f"Fold {name} needs nonempty fit and evaluation rows.")
        folds.append({"name": name, "start": start, "end": end,
                      "fit_ids": [g["id"] for g in fit],
                      "evaluation_ids": [g["id"] for g in evaluation],
                      "embargoed_partition_ids": [g["id"] for g in embargoed]})
    return folds


def _class_counts(y):
    counts = Counter(map(int, y))
    return {str(label): counts.get(label, 0) for label in (0, 2)}


def fit_fold(train_x, train_y, evaluation_x, evaluation_y, *, C):
    if set(np.unique(train_y)) != {0, 2} or set(np.unique(evaluation_y)) - {0, 2}:
        raise ValueError("MLB folds need both fit classes and home/away-only labels.")
    mean = train_x.mean(axis=0)
    std = np.maximum(train_x.std(axis=0), 0.01)
    scaled_train = np.clip((train_x - mean) / std, -8, 8)
    scaled_evaluation = np.clip((evaluation_x - mean) / std, -8, 8)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        model = LogisticRegression(C=C, penalty="l2", solver="lbfgs", max_iter=2000, tol=1e-4)
        model.fit(scaled_train, train_y)
    probability = np.zeros((len(evaluation_y), 3))
    probability[:, model.classes_] = model.predict_proba(scaled_evaluation)
    converged = (not any(issubclass(item.category, ConvergenceWarning) for item in captured)
                 and int(model.n_iter_.max()) < model.max_iter)
    return {
        "fit_rows": len(train_y), "evaluation_rows": len(evaluation_y),
        "fit_class_counts": _class_counts(train_y), "evaluation_class_counts": _class_counts(evaluation_y),
        "scaler_mean": mean.tolist(), "scaler_std": std.tolist(),
        "probabilities": probability, "metrics": metrics(evaluation_y, probability),
        "converged": converged, "n_iter": model.n_iter_.tolist(),
        "warnings": [str(item.message) for item in captured],
    }


def training_fold_sweep(games, training_ids, *, configs=None, c_grid=C_GRID, fold_specs=FOLD_SPECS):
    configs = deepcopy(predeclared_configs() if configs is None else configs)
    folds = rolling_folds(games, training_ids, specs=fold_specs)
    candidates = []
    for config in configs:
        built = build_feature_matrix(games, config)
        index = {game_id: i for i, game_id in enumerate(built["game_ids"])}
        for strength in c_grid:
            fold_rows, oof_y, oof_p = [], [], []
            for fold in folds:
                fit_ix = np.array([index[i] for i in fold["fit_ids"]])
                evaluation_ix = np.array([index[i] for i in fold["evaluation_ids"]])
                result = fit_fold(built["X"][fit_ix], built["y"][fit_ix],
                                  built["X"][evaluation_ix], built["y"][evaluation_ix], C=strength)
                oof_y.extend(built["y"][evaluation_ix].tolist())
                oof_p.extend(result.pop("probabilities").tolist())
                fold_rows.append({**fold, **result})
            aggregate = metrics(np.asarray(oof_y), np.asarray(oof_p))
            candidates.append({"config": config, "config_id": config["id"], "C": float(strength),
                               "folds": fold_rows, "out_of_fold": aggregate,
                               "all_folds_converged": all(row["converged"] for row in fold_rows)})
    eligible = [row for row in candidates if row["all_folds_converged"]]
    if not eligible:
        raise ValueError("No sweep candidate converged in every training fold.")
    selected = min(eligible, key=lambda row: (row["out_of_fold"]["log_loss"], row["C"], row["config_id"]))
    return {"folds": folds, "candidates": candidates,
            "selected": {"config_id": selected["config_id"], "config": selected["config"],
                         "C": selected["C"], "out_of_fold": selected["out_of_fold"]}}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _fit_final(features, fit_ids, validation_ids, *, C):
    index = {game_id: i for i, game_id in enumerate(features["game_ids"])}
    fit_ix = np.array([index[i] for i in fit_ids])
    validation_ix = np.array([index[i] for i in validation_ids])
    train_x, train_y = features["X"][fit_ix], features["y"][fit_ix]
    validation_x, validation_y = features["X"][validation_ix], features["y"][validation_ix]
    mean, std = train_x.mean(0), np.maximum(train_x.std(0), 0.01)
    model = LogisticRegression(C=C, penalty="l2", solver="lbfgs", max_iter=2000, tol=1e-4)
    model.fit(np.clip((train_x - mean) / std, -8, 8), train_y)
    probability = np.zeros((len(validation_y), 3))
    probability[:, model.classes_] = model.predict_proba(np.clip((validation_x - mean) / std, -8, 8))
    return probability, validation_y, model, mean, std


def _same_game_comparison(bookmaker_directory, baseline_path, fixtures, selected_predictions, *, seed, replicates):
    bookmaker_directory = Path(bookmaker_directory).resolve()
    report_path = bookmaker_directory / "report.json"
    matched_path = bookmaker_directory / "matched-records.json"
    book_report = json.loads(report_path.read_text())
    game_ids = book_report["fixture_ids"]
    fixtures_by_id = {g["id"]: g for g in fixtures}
    if any(game_id not in fixtures_by_id for game_id in game_ids):
        raise ValueError("Bookmaker fixture intersection is outside frozen validation.")
    books = json.loads(matched_path.read_text())
    book_by_game = {r["game_id"]: r["probabilities"] for r in books if r["sportsbook"] == "Bet365"}
    baseline_rows = json.loads(Path(baseline_path).read_text())
    saved = defaultdict(dict)
    for row in baseline_rows:
        if (row["sport"] == "baseball" and row["split"] == "validation" and row["seed"] == 42
                and row["model"] in {"frequency-prior", "feature-logistic"}):
            saved[row["model"]][row["game_id"]] = row["probabilities"]
    sources = {"selected-feature-sweep": selected_predictions, **saved, "Bet365-opening": book_by_game}
    if any(any(game_id not in rows for game_id in game_ids) for rows in sources.values()):
        raise ValueError("Same-game comparator is missing a bookmaker-intersection fixture.")
    ordered_fixtures = [fixtures_by_id[game_id] for game_id in game_ids]
    outcomes = np.asarray([f["outcome"] for f in ordered_fixtures])
    shared_hash = _fixture_ids_hash(game_ids)
    scores, arrays = [], {}
    for name, rows in sources.items():
        probability = np.asarray([rows[game_id] for game_id in game_ids])
        arrays[name] = probability
        scores.append({"name": name, "fixture_ids_sha256": shared_hash, **metrics(outcomes, probability)})
    paired = []
    for right in ("feature-logistic", "frequency-prior", "Bet365-opening"):
        row = _paired_week_interval(ordered_fixtures, arrays["selected-feature-sweep"], arrays[right],
                                    seed=seed, replicates=replicates)
        row.update(left="selected-feature-sweep", right=right,
                   limitation="Single selected development model; training-fold selection and validation comparison are not independent confirmation.")
        paired.append(row)
    return {"fixture_ids": game_ids, "fixture_ids_sha256": shared_hash, "scores": scores,
            "paired_weekly": paired,
            "provenance": {str(report_path): _sha256(report_path), str(matched_path): _sha256(matched_path)}}


def run_sweep(experiment, bookmaker_evaluation, output, *, seed=20260910, replicates=2000):
    experiment, output = Path(experiment).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(f"Output directory must be new: {output}")
    games_path = experiment / "source/training-games.json"
    data_path = experiment / "source/training-data.npz"
    baseline_path = experiment / "baseline-predictions.json"
    games = json.loads(games_path.read_text())["games"]
    with np.load(data_path, allow_pickle=False) as frozen:
        train_mask, validation_mask, sports, frozen_y = (frozen[k].copy() for k in ("train", "validation", "sport", "y"))
    baseball_games = [g for g, is_baseball, selected in zip(games, sports, train_mask | validation_mask)
                      if is_baseball and selected]
    training_ids = {g["id"] for g, is_baseball, selected in zip(games, sports, train_mask)
                    if is_baseball and selected}
    validation_ids = [g["id"] for g, is_baseball, selected in zip(games, sports, validation_mask)
                      if is_baseball and selected]
    if len(training_ids) != 3687 or len(validation_ids) != 1165:
        raise ValueError("Frozen MLB split must remain 3,687 training and 1,165 validation fixtures.")
    for game, label in zip(games, frozen_y):
        if game["sport"] == "baseball" and game["id"] in training_ids | set(validation_ids) and game["outcome"] != int(label):
            raise ValueError("Frozen outcomes and training-games disagree.")

    sweep = training_fold_sweep(baseball_games, training_ids)
    selected_config, selected_c = sweep["selected"]["config"], sweep["selected"]["C"]
    built = build_feature_matrix(baseball_games, selected_config)
    final_start = "2025-07-01"
    by_id = {g["id"]: g for g in baseball_games}
    final_fit_ids = sorted((game_id for game_id in training_ids if available_before(by_id[game_id], final_start)),
                           key=lambda game_id: (_parse(by_id[game_id]["start_time"]), game_id))
    embargoed = sorted(training_ids - set(final_fit_ids), key=lambda game_id: (_parse(by_id[game_id]["start_time"]), game_id))
    probability, labels, model, mean, std = _fit_final(
        built, final_fit_ids, validation_ids, C=selected_c
    )
    selected_predictions = {game_id: row.tolist() for game_id, row in zip(validation_ids, probability)}
    validation_score = metrics(labels, probability)
    comparison = _same_game_comparison(bookmaker_evaluation, baseline_path, baseball_games,
                                       selected_predictions, seed=seed, replicates=replicates)
    prediction_rows = [{"game_id": game_id, "sport": "baseball", "split": "validation",
                        "outcome": int(label), "probabilities": row.tolist(),
                        "model": "selected-feature-sweep", "seed": 42}
                       for game_id, label, row in zip(validation_ids, labels, probability)]
    report = {
        "schema_version": 1, "created_at": utcnow(), "scope": "Frozen MLB original training/validation only",
        "design": {"configs": predeclared_configs(), "C_grid": list(C_GRID), "fold_specs": FOLD_SPECS,
                   "selection": "Minimum pooled out-of-fold log loss; lower C then config ID break ties.",
                   "timing": "Finals become available at scheduled start +48h, applied at the next UTC-day batch (48-72h).",
                   "history": "Pooled or current-role-specific form/win-rate/game-count/margin; Elo and rest remain all-game.",
                   "rest": {"none": "zero", "capped": "min(days,14)/14",
                            "recovery": "1-exp(-days/3)"},
                   "weather_and_starters": "Omitted: neither is present as point-in-time pregame data in the frozen experiment source."},
        "training_sweep": sweep,
        "final_fit": {"fit_rows": len(final_fit_ids), "fit_class_counts": _class_counts(np.asarray([by_id[i]["outcome"] for i in final_fit_ids])),
                      "embargoed_training_rows": len(embargoed), "embargoed_training_ids": embargoed,
                      "validation_rows": len(validation_ids), "validation_metrics": validation_score,
                      "converged": int(model.n_iter_.max()) < model.max_iter, "n_iter": model.n_iter_.tolist(),
                      "scaler_mean": mean.tolist(), "scaler_std": std.tolist()},
        "same_game_comparison": comparison,
        "provenance": {"experiment": str(experiment), "inputs": {str(path): _sha256(path) for path in
                       (games_path, data_path, baseline_path)}, "code_sha256": _sha256(Path(__file__)),
                       "frozen_split_ids": {"training": sorted(training_ids), "validation": validation_ids}},
        "limitations": [
            "Configuration and C were selected only on rolling folds within the original training partition.",
            "The original validation split is a final development comparison, not independent confirmation.",
            "The classifier and scaler stay frozen through validation; earlier validation outcomes only update causal history after their availability delay.",
            "The frozen source lacks completion timestamps, so scheduled time plus the conservative UTC-day delay is used.",
            "No neural simulation, online update, reinforcement learning, historical/prospective evaluation, automatic extension, or model promotion occurred.",
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output / "predictions.json", prediction_rows)
    report["output_artifacts"] = {"predictions.json": _sha256(output / "predictions.json")}
    atomic_json(output / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--bookmaker-evaluation", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--bootstrap-seed", type=int, default=20260910)
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    args = parser.parse_args(argv)
    report = run_sweep(args.experiment, args.bookmaker_evaluation, args.output,
                       seed=args.bootstrap_seed, replicates=args.bootstrap_replicates)
    print(json.dumps({"output": str(Path(args.output).resolve()), "selected": report["training_sweep"]["selected"],
                      "validation": report["final_fit"]["validation_metrics"]}))


if __name__ == "__main__":
    main()
