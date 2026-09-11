"""Compare frozen MLB validation predictions with normalized historical moneylines.

This module only reads saved predictions.  It does not fit a model, search a
hyperparameter, simulate the connectome, or evaluate outside the original
validation fixtures.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import numpy as np

from .experiment import atomic_json, utcnow
from .learning import metrics


ODDS_CONTRACT = {
    "required": [
        "sportsbook", "market", "price_format", "home_key", "away_key",
        "home_price", "away_price", "quote_timing", "provider_source_row_id",
    ],
    "fixture_time": "Either UTC-aware start_time, or date with an explicit IANA timezone.",
    "optional": [
        "game_id", "game_number", "quote_time", "provider", "source_url",
        "source_fetched_at", "raw_source_sha256",
    ],
    "market": "MLB two-outcome moneyline; no draw price.",
    "matching": (
        "Canonical home/away teams plus supplied fixture identity. Date-only duplicate fixtures are rejected "
        "unless game_number uniquely identifies chronological start order. Outcomes are never match inputs."
    ),
}


_TEAM_ALIASES = {
    "ari": "arizona-diamondbacks", "az": "arizona-diamondbacks",
    "atl": "atlanta-braves", "bal": "baltimore-orioles", "bos": "boston-red-sox",
    "chc": "chicago-cubs", "chw": "chicago-white-sox", "cws": "chicago-white-sox",
    "cin": "cincinnati-reds", "cle": "cleveland-guardians", "col": "colorado-rockies",
    "det": "detroit-tigers", "hou": "houston-astros", "kc": "kansas-city-royals",
    "kcr": "kansas-city-royals", "laa": "los-angeles-angels", "ana": "los-angeles-angels",
    "lad": "los-angeles-dodgers", "mia": "miami-marlins", "mil": "milwaukee-brewers",
    "min": "minnesota-twins", "nym": "new-york-mets", "nyy": "new-york-yankees",
    "ath": "athletics", "oak": "athletics", "phi": "philadelphia-phillies",
    "pit": "pittsburgh-pirates", "sd": "san-diego-padres", "sdp": "san-diego-padres",
    "sf": "san-francisco-giants", "sfg": "san-francisco-giants",
    "sea": "seattle-mariners", "stl": "st-louis-cardinals", "tb": "tampa-bay-rays",
    "tbr": "tampa-bay-rays", "tex": "texas-rangers", "tor": "toronto-blue-jays",
    "wsh": "washington-nationals", "was": "washington-nationals",
}


def _slug(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Team keys must be nonempty strings.")
    pieces = []
    for char in value.strip().lower().replace("&", " and "):
        pieces.append(char if char.isalnum() else "-")
    return "-".join(filter(None, "".join(pieces).split("-")))


def canonical_team_key(value):
    key = _slug(value)
    return _TEAM_ALIASES.get(key, key)


def american_to_decimal(price):
    try:
        value = float(price)
    except (TypeError, ValueError) as exc:
        raise ValueError("American price must be numeric.") from exc
    if not math.isfinite(value) or value == 0 or abs(value) < 100:
        raise ValueError("American price must be finite and have absolute value at least 100.")
    return 1 + (value / 100 if value > 0 else 100 / abs(value))


def _decimal_price(price):
    try:
        value = float(price)
    except (TypeError, ValueError) as exc:
        raise ValueError("Decimal price must be numeric.") from exc
    if not math.isfinite(value) or value <= 1:
        raise ValueError("Decimal price must be finite and greater than one.")
    return value


def devig_moneyline(home_price, away_price, price_format):
    """Return proportional no-vig home/away probabilities."""
    kind = str(price_format).strip().lower()
    if kind == "american":
        home, away = american_to_decimal(home_price), american_to_decimal(away_price)
    elif kind == "decimal":
        home, away = _decimal_price(home_price), _decimal_price(away_price)
    else:
        raise ValueError("price_format must be american or decimal.")
    implied = np.array([1 / home, 1 / away], dtype=float)
    fair = implied / implied.sum()
    return float(fair[0]), float(fair[1])


def _aware_datetime(value, field="timestamp"):
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO timestamp string.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO timestamp.") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone.")
    return parsed.astimezone(timezone.utc)


def _game_id(value):
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text if text.startswith("baseball:mlb:") else f"baseball:mlb:{text}"


def normalize_odds_record(record):
    if not isinstance(record, dict):
        raise ValueError("Each odds record must be an object.")
    for field in ODDS_CONTRACT["required"]:
        if field not in record or record[field] in (None, ""):
            raise ValueError(f"Missing required odds field: {field}")
    if str(record["market"]).strip().lower() not in {"moneyline", "ml", "money-line"}:
        raise ValueError("Only MLB moneyline records are supported.")
    if "draw_price" in record and record["draw_price"] is not None:
        raise ValueError("MLB moneylines cannot contain a draw price.")
    sportsbook = str(record["sportsbook"]).strip()
    row_id = str(record["provider_source_row_id"]).strip()
    home, away = devig_moneyline(record["home_price"], record["away_price"], record["price_format"])
    normalized = {
        "sportsbook": sportsbook,
        "market": "moneyline",
        "price_format": str(record["price_format"]).strip().lower(),
        "home_key": canonical_team_key(record["home_key"]),
        "away_key": canonical_team_key(record["away_key"]),
        "home_price": record["home_price"],
        "away_price": record["away_price"],
        "probabilities": [home, 0.0, away],
        "quote_timing": str(record["quote_timing"]).strip(),
        "provider_source_row_id": row_id,
        "game_id": _game_id(record.get("game_id")),
        "raw_record": deepcopy(record),
    }
    if normalized["home_key"] == normalized["away_key"]:
        raise ValueError("Home and away teams must differ.")
    if record.get("start_time"):
        normalized["start_time"] = _aware_datetime(record["start_time"], "start_time").isoformat()
    elif record.get("date"):
        try:
            local_zone = ZoneInfo(record["timezone"])
            local_date = datetime.strptime(record["date"], "%Y-%m-%d").date()
        except (KeyError, TypeError, ValueError, ZoneInfoNotFoundError) as exc:
            raise ValueError("Date matching requires YYYY-MM-DD and an explicit valid IANA timezone.") from exc
        normalized["date"] = local_date.isoformat()
        normalized["timezone"] = str(local_zone)
    else:
        raise ValueError("Odds record needs start_time, or date and timezone.")
    if record.get("quote_time"):
        normalized["quote_time"] = _aware_datetime(record["quote_time"], "quote_time").isoformat()
    if record.get("game_number") not in (None, ""):
        try:
            normalized["game_number"] = int(record["game_number"])
        except (TypeError, ValueError) as exc:
            raise ValueError("game_number must be a positive integer.") from exc
        if normalized["game_number"] < 1:
            raise ValueError("game_number must be a positive integer.")
    for field in ("provider", "source_url", "source_fetched_at", "raw_source_sha256"):
        if field in record:
            normalized[field] = deepcopy(record[field])
    return normalized


def _fixture_date(fixture, zone):
    return _aware_datetime(fixture["start_time"], "fixture start_time").astimezone(zone).date()


def match_odds_records(records, fixtures):
    """Conservatively match normalized odds without consulting an outcome."""
    normalized_fixtures = []
    for fixture in fixtures:
        row = dict(fixture)
        row["home_key"] = canonical_team_key(fixture.get("home_key", fixture.get("home")))
        row["away_key"] = canonical_team_key(fixture.get("away_key", fixture.get("away")))
        row["_start"] = _aware_datetime(fixture["start_time"], "fixture start_time")
        normalized_fixtures.append(row)

    matched, audit, excluded = [], [], Counter()
    for raw in records:
        raw_id = raw.get("provider_source_row_id") if isinstance(raw, dict) else None
        try:
            record = normalize_odds_record(raw)
        except ValueError as exc:
            excluded["invalid_record"] += 1
            audit.append({"provider_source_row_id": raw_id, "status": "excluded",
                          "reason": "invalid_record", "detail": str(exc)})
            continue
        candidates = [f for f in normalized_fixtures
                      if f["home_key"] == record["home_key"] and f["away_key"] == record["away_key"]]
        if record.get("game_id"):
            candidates = [f for f in candidates if f["id"] == record["game_id"]]
        if record.get("start_time"):
            instant = _aware_datetime(record["start_time"])
            candidates = [f for f in candidates if f["_start"] == instant]
        elif record.get("date"):
            zone = ZoneInfo(record["timezone"])
            candidates = [f for f in candidates if _fixture_date(f, zone).isoformat() == record["date"]]
        if record.get("game_number") and len(candidates) > 1:
            explicit = [f for f in candidates if f.get("game_number") == record["game_number"]]
            if explicit:
                candidates = explicit
            else:
                ordered = sorted(candidates, key=lambda f: (f["_start"], f["id"]))
                number = record["game_number"]
                candidates = ordered[number - 1:number]
        if len(candidates) != 1:
            reason = "unmatched_fixture" if not candidates else "ambiguous_fixture"
            excluded[reason] += 1
            audit.append({"provider_source_row_id": record["provider_source_row_id"], "status": "excluded",
                          "reason": reason, "candidate_game_ids": sorted(f["id"] for f in candidates)})
            continue
        fixture = candidates[0]
        accepted = {k: deepcopy(v) for k, v in record.items()}
        accepted["game_id"] = fixture["id"]
        accepted["fixture_start_time"] = fixture["_start"].isoformat()
        matched.append(accepted)
        audit.append({"provider_source_row_id": record["provider_source_row_id"], "status": "matched",
                      "game_id": fixture["id"], "matched_by": "game_id" if record.get("game_id") else
                      "start_time" if record.get("start_time") else
                      "date_and_game_number" if record.get("game_number") else "unique_team_date"})
    return {"matched": matched, "audit": {"records": audit, "excluded_counts": dict(sorted(excluded.items())),
                                           "input_records": len(records), "matched_records": len(matched)}}


def _fixture_ids_hash(game_ids):
    encoded = json.dumps(game_ids, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _select_book_quotes(matched, fixtures_by_id):
    grouped = defaultdict(list)
    for row in matched:
        grouped[(row["sportsbook"], row["game_id"])].append(row)
    selected, excluded = [], []
    for (sportsbook, game_id), rows in sorted(grouped.items()):
        if len(rows) == 1:
            selected.append(rows[0])
            continue
        timed = [r for r in rows if r.get("quote_time")]
        kickoff = _aware_datetime(fixtures_by_id[game_id]["start_time"])
        pregame = [r for r in timed if _aware_datetime(r["quote_time"]) <= kickoff]
        if pregame:
            latest = max(_aware_datetime(r["quote_time"]) for r in pregame)
            winners = [r for r in pregame if _aware_datetime(r["quote_time"]) == latest]
            if len(winners) == 1:
                selected.append(winners[0])
                excluded.extend(r for r in rows if r is not winners[0])
                continue
        excluded.extend(rows)
    return selected, excluded


def _paired_week_interval(fixtures, left, right, *, seed, replicates):
    entries = []
    for fixture, a, b in zip(fixtures, left, right):
        label = int(fixture["outcome"])
        delta = -math.log(max(float(a[label]), 1e-12)) + math.log(max(float(b[label]), 1e-12))
        day = _aware_datetime(fixture["start_time"]).date()
        entries.append((day - timedelta(days=day.weekday()), delta))
    first, last = min(x[0] for x in entries), max(x[0] for x in entries)
    weeks = (last - first).days // 7 + 1
    totals, counts = np.zeros(weeks), np.zeros(weeks)
    for week, delta in entries:
        index = (week - first).days // 7
        totals[index] += delta
        counts[index] += 1
    rng = np.random.default_rng(seed)
    indices = rng.integers(weeks, size=(replicates, weeks))
    denominators = counts[indices].sum(axis=1)
    samples = totals[indices].sum(axis=1)[denominators > 0] / denominators[denominators > 0]
    low, high = np.percentile(samples, [2.5, 97.5]).tolist()
    return {
        "difference": float(np.mean([x[1] for x in entries])), "interval": [low, high],
        "n": len(entries), "calendar_weeks": weeks, "empty_weeks": int((counts == 0).sum()),
    }


def evaluate_matched(fixtures, predictions, matched, *, replicates=2000, seed=20260910):
    if not predictions:
        raise ValueError("At least one saved prediction model is required.")
    fixtures_by_id = {f["id"]: f for f in fixtures}
    selected, duplicate_quotes = _select_book_quotes(matched, fixtures_by_id)
    by_book = defaultdict(dict)
    for row in selected:
        by_book[row["sportsbook"]][row["game_id"]] = row["probabilities"]
    if not by_book:
        raise ValueError("No conservatively matched sportsbook records remain.")
    overlap = set(predictions) & set(by_book)
    if overlap:
        raise ValueError(f"Model and sportsbook names overlap: {sorted(overlap)}")
    sources = [set(rows) for rows in predictions.values()] + [set(rows) for rows in by_book.values()]
    common = set(fixtures_by_id).intersection(*sources)
    game_ids = sorted(common, key=lambda game_id: (_aware_datetime(fixtures_by_id[game_id]["start_time"]), game_id))
    if not game_ids:
        raise ValueError("No fixtures are shared by every model and sportsbook.")
    selected_fixtures = [fixtures_by_id[game_id] for game_id in game_ids]
    outcomes = np.array([int(row["outcome"]) for row in selected_fixtures])
    if np.any((outcomes != 0) & (outcomes != 2)):
        raise ValueError("MLB outcomes must be home or away; draws are invalid.")
    shared_hash = _fixture_ids_hash(game_ids)
    scores = []
    all_probabilities = {}
    for kind, sources_by_name in (("model", predictions), ("sportsbook", by_book)):
        for name in sorted(sources_by_name):
            probability = np.asarray([sources_by_name[name][game_id] for game_id in game_ids], dtype=float)
            score = metrics(outcomes, probability)
            scores.append({"name": name, "kind": kind, "fixture_ids_sha256": shared_hash, **score})
            all_probabilities[name] = probability
    paired = []
    limitation = ("Single frozen seed-42 development scores on the original validation split; weekly blocks approximate "
                  "but do not eliminate team and time dependence. The intervals are neither profit estimates nor "
                  "independent confirmation.")
    for model in sorted(predictions):
        for book in sorted(by_book):
            row = _paired_week_interval(selected_fixtures, all_probabilities[model], all_probabilities[book],
                                        seed=seed, replicates=replicates)
            row.update(model=model, sportsbook=book, comparison="model minus sportsbook log loss",
                       decision="better on this development comparison" if row["interval"][1] < 0 else
                       "worse on this development comparison" if row["interval"][0] > 0 else "uncertain",
                       limitation=limitation)
            paired.append(row)
    book_union = set().union(*(set(rows) for rows in by_book.values()))
    coverage = {
        "validation_fixtures": len(fixtures_by_id),
        "matched_unique_fixtures": len(book_union),
        "global_intersection": len(game_ids),
        "excluded_not_shared_by_all_books": len(book_union - common),
        "duplicate_or_ambiguous_quotes_excluded": len(duplicate_quotes),
        "by_model": {name: len(rows) for name, rows in sorted(predictions.items())},
        "by_sportsbook": {name: len(rows) for name, rows in sorted(by_book.items())},
    }
    return {"fixture_ids": game_ids, "fixture_ids_sha256": shared_hash, "coverage": coverage,
            "scores": scores, "paired_weekly": paired,
            "quote_selection_exclusions": [r["provider_source_row_id"] for r in duplicate_quotes]}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_odds(path):
    path = Path(path).resolve()
    raw = json.loads(path.read_text())
    if isinstance(raw, list):
        records, source = raw, None
    elif isinstance(raw, dict) and isinstance(raw.get("records"), list):
        records, source = raw["records"], deepcopy(raw.get("source"))
    else:
        raise ValueError("Odds JSON must be a list or an object with a records list.")
    return {"records": deepcopy(records), "source": source,
            "provenance": {"path": str(path), "sha256": _sha256(path), "records": len(records)}}


def _load_saved_predictions(experiment, diagnostic):
    experiment, diagnostic = Path(experiment).resolve(), Path(diagnostic).resolve()
    games_path = experiment / "source/training-games.json"
    features_path = experiment / "source/training-data.npz"
    baseline_path = experiment / "baseline-predictions.json"
    diagnostic_predictions_path = diagnostic / "predictions.json"
    diagnostic_report_path = diagnostic / "report.json"
    games = json.loads(games_path.read_text())["games"]
    baselines = json.loads(baseline_path.read_text())
    report = json.loads(diagnostic_report_path.read_text())
    diagnostic_rows = json.loads(diagnostic_predictions_path.read_text())

    baseline_rows = [r for r in baselines if r["sport"] == "baseball" and r["split"] == "validation"
                     and r["seed"] == 42 and r["model"] in {"frequency-prior", "feature-logistic"}]
    by_baseline = defaultdict(list)
    for row in baseline_rows:
        by_baseline[row["model"]].append(row)
    if set(by_baseline) != {"frequency-prior", "feature-logistic"}:
        raise ValueError("Both saved seed-42 MLB validation baselines are required.")
    expected = {r["game_id"] for r in by_baseline["feature-logistic"]}
    if len(expected) != 1165 or any({r["game_id"] for r in rows} != expected for rows in by_baseline.values()):
        raise ValueError("Saved baselines must contain the same 1,165 MLB validation fixtures.")
    fixtures_by_id = {g["id"]: g for g in games if g["id"] in expected}
    if set(fixtures_by_id) != expected:
        raise ValueError("Frozen training-games source does not align with saved validation predictions.")

    predictions = {}
    outcome_by_game = {}
    for name, rows in by_baseline.items():
        predictions[name] = {r["game_id"]: r["probabilities"] for r in rows}
        for row in rows:
            prior = outcome_by_game.setdefault(row["game_id"], row["outcome"])
            if prior != row["outcome"] or fixtures_by_id[row["game_id"]]["outcome"] != row["outcome"]:
                raise ValueError("Saved outcomes disagree across frozen artifacts.")
    for representation in ("whole", "temporal"):
        best = report["best_validation"]["baseball"][representation]
        if float(best["C"]) != 0.0001:
            raise ValueError("Frozen stronger-L2 MLB selected C must remain 0.0001.")
        prefix = f"{representation}-baseball-C"
        candidates = [r for r in diagnostic_rows if r["sport"] == "baseball" and r["split"] == "validation"
                      and r["model"].startswith(prefix)
                      and math.isclose(float(r["model"][len(prefix):]), float(best["C"]), rel_tol=0, abs_tol=1e-15)]
        if len(candidates) != 1165 or {r["game_id"] for r in candidates} != expected:
            raise ValueError(f"Selected saved {representation} predictions do not cover frozen validation fixtures.")
        for row in candidates:
            if row["outcome"] != outcome_by_game[row["game_id"]]:
                raise ValueError("Selected decoder outcomes disagree with saved baselines.")
        predictions[f"fly-{representation}-C0.0001"] = {r["game_id"]: r["probabilities"] for r in candidates}
    provenance = {
        "experiment": str(experiment), "diagnostic": str(diagnostic),
        "artifacts": {str(path): _sha256(path) for path in (
            games_path, features_path, baseline_path, diagnostic_predictions_path, diagnostic_report_path
        )},
        "method": "Read saved seed-42 validation predictions only; no fit, simulation, or C search.",
    }
    return list(fixtures_by_id.values()), predictions, provenance


def run_comparison(experiment, diagnostic, odds, output, *, replicates=2000, seed=20260910):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(f"Output directory must be new: {output}")
    fixtures, predictions, saved_provenance = _load_saved_predictions(experiment, diagnostic)
    odds_input = load_odds(odds)
    matching = match_odds_records(odds_input["records"], fixtures)
    evaluation = evaluate_matched(fixtures, predictions, matching["matched"], replicates=replicates, seed=seed)
    report = {
        "schema_version": 1, "created_at": utcnow(),
        "scope": "MLB original validation only (1,165 games); frozen seed-42 development comparison.",
        "odds_contract": ODDS_CONTRACT,
        "provenance": {"saved_inputs": saved_provenance, "odds_input": odds_input["provenance"],
                       "odds_source": odds_input["source"], "code_sha256": _sha256(Path(__file__))},
        **evaluation,
        "matching": {k: v for k, v in matching["audit"].items() if k != "records"},
        "limitations": [
            "Scores use one frozen biological seed and C selected on this validation split; they are development evidence.",
            "Book prices are proportionally de-vigged historical quotes, not verified executable prices.",
            "No profit, staking, new fit, neural simulation, additional C search, historical-development, or prospective evaluation is included.",
            "Weekly intervals approximate but do not eliminate dependence and are not independent confirmation.",
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output / "match-audit.json", matching["audit"])
    atomic_json(output / "matched-records.json", matching["matched"])
    report["output_artifacts"] = {
        "match-audit.json": _sha256(output / "match-audit.json"),
        "matched-records.json": _sha256(output / "matched-records.json"),
    }
    atomic_json(output / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--diagnostic", required=True)
    parser.add_argument("--odds", required=True)
    parser.add_argument("--output", required=True, help="New output directory; existing paths are rejected.")
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260910)
    args = parser.parse_args(argv)
    if args.bootstrap_replicates < 1:
        parser.error("--bootstrap-replicates must be positive")
    report = run_comparison(args.experiment, args.diagnostic, args.odds, args.output,
                            replicates=args.bootstrap_replicates, seed=args.bootstrap_seed)
    print(json.dumps({"output": str(Path(args.output).resolve()), "matched": report["coverage"]["global_intersection"],
                      "sportsbooks": sorted(report["coverage"]["by_sportsbook"])}))


if __name__ == "__main__":
    main()
