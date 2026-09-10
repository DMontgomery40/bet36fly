"""Public EPL and MLB schedule/result ingestion with raw provenance archives."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data" / "sports"

_SOCCER_ALIASES = {
    "afc-bournemouth": "bournemouth",
    "bournemouth": "bournemouth",
    "brighton-hove-albion": "brighton",
    "brighton-and-hove-albion": "brighton",
    "brighton": "brighton",
    "ipswich-town": "ipswich",
    "ipswich": "ipswich",
    "leeds-united": "leeds",
    "leeds": "leeds",
    "leicester-city": "leicester",
    "leicester": "leicester",
    "luton-town": "luton",
    "luton": "luton",
    "manchester-city": "man-city",
    "man-city": "man-city",
    "manchester-united": "man-united",
    "man-united": "man-united",
    "newcastle-united": "newcastle",
    "newcastle": "newcastle",
    "nottingham-forest": "nottm-forest",
    "nott-m-forest": "nottm-forest",
    "nottm-forest": "nottm-forest",
    "sheffield-united": "sheffield-utd",
    "sheffield-utd": "sheffield-utd",
    "tottenham-hotspur": "tottenham",
    "tottenham": "tottenham",
    "west-ham-united": "west-ham",
    "west-ham": "west-ham",
    "wolverhampton-wanderers": "wolves",
    "wolves": "wolves",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_team_key(name: str, sport: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    normalized = normalized.replace("&", " and ").replace("'", " ")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return _SOCCER_ALIASES.get(slug, slug) if sport == "soccer" else slug


def _iso_utc(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _score(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _outcome(home_score: int | None, away_score: int | None) -> int | None:
    if home_score is None or away_score is None:
        return None
    return 0 if home_score > away_score else 2 if home_score < away_score else 1


def normalize_football_csv(raw: bytes, source_url: str, fetched_at: str) -> list[dict]:
    games = []
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig", errors="replace")))
    for row in reader:
        if not row.get("Date") or not row.get("HomeTeam") or not row.get("AwayTeam"):
            continue
        try:
            day = datetime.strptime(row["Date"].strip(), "%d/%m/%Y").date()
        except ValueError:
            continue
        time_text = (row.get("Time") or "15:00").strip() or "15:00"
        try:
            start = datetime.combine(
                day, datetime.strptime(time_text, "%H:%M").time(), ZoneInfo("Europe/London")
            ).astimezone(timezone.utc)
        except ValueError:
            start = datetime.combine(
                day, datetime.strptime("15:00", "%H:%M").time(), ZoneInfo("Europe/London")
            ).astimezone(timezone.utc)
        home = row["HomeTeam"].strip()
        away = row["AwayTeam"].strip()
        home_key = canonical_team_key(home, "soccer")
        away_key = canonical_team_key(away, "soccer")
        result = (row.get("FTR") or "").strip().upper()
        home_score = _score(row.get("FTHG")) if result in {"H", "D", "A"} else None
        away_score = _score(row.get("FTAG")) if result in {"H", "D", "A"} else None
        odds = []
        for key in ("B365H", "B365D", "B365A"):
            try:
                odds.append(float(row[key]))
            except (KeyError, TypeError, ValueError):
                odds.append(None)
        game = {
            "id": f"soccer:epl:{day.isoformat()}:{home_key}:{away_key}",
            "sport": "soccer",
            "league": "EPL",
            "start_time": start.isoformat().replace("+00:00", "Z"),
            "home": home,
            "away": away,
            "home_key": home_key,
            "away_key": away_key,
            "status": "final" if result in {"H", "D", "A"} else "scheduled",
            "home_score": home_score,
            "away_score": away_score,
            "outcome": {"H": 0, "D": 1, "A": 2}.get(result),
            "source": "football-data.co.uk",
            "source_url": source_url,
            "source_fetched_at": fetched_at,
            "venue": "",
            "odds": odds,
        }
        games.append(game)
    return games


def _espn_status(status_type: dict) -> str:
    text = " ".join(
        str(status_type.get(key, "")) for key in ("name", "description", "detail", "shortDetail")
    ).lower()
    if "postpon" in text:
        return "postponed"
    if "cancel" in text:
        return "cancelled"
    if status_type.get("completed") or status_type.get("state") == "post":
        return "final"
    if status_type.get("state") == "in":
        return "live"
    return "scheduled"


def normalize_espn_soccer(payload: dict, source_url: str, fetched_at: str) -> list[dict]:
    games = []
    for event in payload.get("events", []):
        competitions = event.get("competitions") or []
        if not competitions:
            continue
        competition = competitions[0]
        sides = {item.get("homeAway"): item for item in competition.get("competitors", [])}
        if "home" not in sides or "away" not in sides:
            continue
        home_item, away_item = sides["home"], sides["away"]
        home_team, away_team = home_item.get("team", {}), away_item.get("team", {})
        home = home_team.get("displayName") or home_team.get("name")
        away = away_team.get("displayName") or away_team.get("name")
        if not home or not away:
            continue
        start_time = _iso_utc(competition.get("date") or event["date"])
        day = start_time[:10]
        home_key = canonical_team_key(home, "soccer")
        away_key = canonical_team_key(away, "soccer")
        status = _espn_status(competition.get("status", {}).get("type", {}))
        home_score = _score(home_item.get("score")) if status in {"live", "final"} else None
        away_score = _score(away_item.get("score")) if status in {"live", "final"} else None
        game = {
            "id": f"soccer:epl:{day}:{home_key}:{away_key}",
            "sport": "soccer",
            "league": "EPL",
            "start_time": start_time,
            "home": home,
            "away": away,
            "home_key": home_key,
            "away_key": away_key,
            "status": status,
            "home_score": home_score,
            "away_score": away_score,
            "outcome": _outcome(home_score, away_score) if status == "final" else None,
            "source": "ESPN",
            "source_url": source_url,
            "source_fetched_at": fetched_at,
            "venue": competition.get("venue", {}).get("fullName", ""),
        }
        if home_team.get("logo"):
            game["home_logo"] = home_team["logo"]
        if away_team.get("logo"):
            game["away_logo"] = away_team["logo"]
        games.append(game)
    return games


def _mlb_status(status: dict) -> str:
    text = f"{status.get('abstractGameState', '')} {status.get('detailedState', '')}".lower()
    if "postpon" in text:
        return "postponed"
    if "cancel" in text:
        return "cancelled"
    if status.get("abstractGameState") == "Final" or "final" in text or "completed" in text:
        return "final"
    if status.get("abstractGameState") == "Live" or "progress" in text or "warmup" in text:
        return "live"
    return "scheduled"


def normalize_mlb(payload: dict, source_url: str, fetched_at: str) -> list[dict]:
    raw_games = [item for day in payload.get("dates", []) for item in day.get("games", [])]
    resumed_ids = {item.get("gamePk") for item in raw_games if item.get("resumeDate")}
    games_by_id = {}
    for day in payload.get("dates", []):
        for item in day.get("games", []):
            teams = item.get("teams", {})
            if "home" not in teams or "away" not in teams:
                continue
            home_item, away_item = teams["home"], teams["away"]
            home = home_item.get("team", {}).get("name")
            away = away_item.get("team", {}).get("name")
            if not home or not away or not item.get("gameDate"):
                continue
            status = _mlb_status(item.get("status", {}))
            # This endpoint exposes the original start and resume time, but not a
            # trustworthy completion time. Exclude resumed finals from lagged state.
            resumed_without_completion = status == "final" and item.get("gamePk") in resumed_ids
            score_available = status in {"live", "final"} and not resumed_without_completion
            home_score = _score(home_item.get("score")) if score_available else None
            away_score = _score(away_item.get("score")) if score_available else None
            game = {
                    "id": f"baseball:mlb:{item['gamePk']}",
                    "sport": "baseball",
                    "league": "MLB",
                    "start_time": _iso_utc(item["gameDate"]),
                    "home": home,
                    "away": away,
                    "home_key": canonical_team_key(home, "baseball"),
                    "away_key": canonical_team_key(away, "baseball"),
                    "status": status,
                    "home_score": home_score,
                    "away_score": away_score,
                    "outcome": _outcome(home_score, away_score) if status == "final" else None,
                    "source": "MLB Stats API",
                    "source_url": source_url,
                    "source_fetched_at": fetched_at,
                    "venue": item.get("venue", {}).get("name", ""),
                    "odds": [None, None, None],
                }
            games_by_id[game["id"]] = game
    return list(games_by_id.values())


def merge_games(existing: list[dict], incoming: list[dict]) -> list[dict]:
    def epl_identity(game):
        if game.get('sport') != 'soccer' or game.get('league') != 'EPL':
            return None
        start = datetime.fromisoformat(game['start_time'].replace('Z', '+00:00'))
        season = start.year if start.month >= 7 else start.year - 1
        return season, game['home_key'], game['away_key']

    by_id = {game["id"]: game for game in existing}
    # Each ordered EPL pairing occurs once per season. A new kickoff date must
    # replace its older occurrence rather than leaving a second phantom fixture.
    epl_ids = {epl_identity(game): game['id'] for game in existing if epl_identity(game) is not None}
    for game in incoming:
        identity = epl_identity(game)
        if identity is not None:
            old_id = epl_ids.get(identity)
            if old_id and old_id != game['id']:
                by_id.pop(old_id, None)
            epl_ids[identity] = game['id']
        by_id[game['id']] = game
    return sorted(by_id.values(), key=lambda game: (game.get("start_time", ""), game["id"]))


def _source_specs(historical: bool, live: bool) -> list[dict]:
    today = datetime.now(timezone.utc).date()
    specs = []
    if historical:
        for season in ("2324", "2425", "2526", "2627"):
            specs.append(
                {
                    "id": f"football-data-epl-{season}",
                    "url": f"https://www.football-data.co.uk/mmz4281/{season}/E0.csv",
                    "parser": normalize_football_csv,
                    "suffix": ".csv",
                }
            )
        for year in range(2024, today.year + 1):
            end = min(date(year, 10, 1), today - timedelta(days=1))
            if end < date(year, 3, 1):
                continue
            url = (
                "https://statsapi.mlb.com/api/v1/schedule?sportId=1"
                f"&startDate={year}-03-01&endDate={end.isoformat()}&gameType=R"
            )
            specs.append(
                {"id": f"mlb-history-{year}", "url": url, "parser": normalize_mlb, "suffix": ".json"}
            )
    if live:
        lookback = today - timedelta(days=14)
        soccer_end = today + timedelta(days=8)
        soccer_url = (
            "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
            f"?dates={lookback.strftime('%Y%m%d')}-{soccer_end.strftime('%Y%m%d')}&limit=100"
        )
        mlb_end = today + timedelta(days=7)
        mlb_url = (
            "https://statsapi.mlb.com/api/v1/schedule?sportId=1"
            f"&startDate={lookback.isoformat()}&endDate={mlb_end.isoformat()}"
        )
        specs.extend(
            [
                {"id": "espn-epl-live", "url": soccer_url, "parser": normalize_espn_soccer, "suffix": ".json"},
                {"id": "mlb-live", "url": mlb_url, "parser": normalize_mlb, "suffix": ".json"},
            ]
        )
    return specs


def _failure_source(spec: dict, attempted_at: str, error: Exception, previous: dict | None) -> dict:
    source = {
        "id": spec["id"],
        "url": spec["url"],
        "url_sha256": hashlib.sha256(spec["url"].encode()).hexdigest(),
        "status": "stale" if previous and previous.get("fetched_at") else "failed",
        "attempted_at": attempted_at,
        "error": f"{type(error).__name__}: {error}",
    }
    if previous and previous.get("fetched_at"):
        for key in ("fetched_at", "sha256", "archive_path"):
            if key in previous:
                source[key] = previous[key]
    return source


def _fetch_one(spec: dict, data_dir: Path, previous: dict | None) -> tuple[list[dict], dict]:
    attempted_at = utc_now_iso()
    error = RuntimeError("request was not attempted")
    raw = b""
    for attempt in range(3):
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(spec["url"], headers={"User-Agent": "bet36fly/0.1 public-data"})
                response.raise_for_status()
                raw = response.content
            fetched_at = utc_now_iso()
            if spec["suffix"] == ".json":
                payload = json.loads(raw)
                games = spec["parser"](payload, spec["url"], fetched_at)
            else:
                games = spec["parser"](raw, spec["url"], fetched_at)
            raw_dir = data_dir / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            stamp = fetched_at.replace("-", "").replace(":", "")
            url_hash = hashlib.sha256(spec["url"].encode()).hexdigest()
            archive = raw_dir / f"{stamp}-{spec['id']}-{url_hash[:12]}{spec['suffix']}"
            archive.write_bytes(raw)
            source = {
                "id": spec["id"],
                "url": spec["url"],
                "url_sha256": url_hash,
                "status": "ok",
                "fetched_at": fetched_at,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "archive_path": str(archive.relative_to(data_dir)),
                "game_count": len(games),
            }
            return games, source
        except Exception as exc:  # network and malformed upstream data share source failure reporting
            error = exc
            if attempt < 2:
                time.sleep(0.25 * (2**attempt))
    return [], _failure_source(spec, attempted_at, error, previous)


def _fetch_specs(specs: list[dict], data_dir: Path, previous_sources=None) -> dict:
    previous_by_id = {source["id"]: source for source in (previous_sources or [])}
    results = {}
    with ThreadPoolExecutor(max_workers=min(4, max(1, len(specs)))) as pool:
        futures = {
            pool.submit(_fetch_one, spec, data_dir, previous_by_id.get(spec["id"])): spec for spec in specs
        }
        for future in as_completed(futures):
            spec = futures[future]
            try:
                results[spec["id"]] = future.result()
            except Exception as exc:
                results[spec["id"]] = (
                    [],
                    _failure_source(spec, utc_now_iso(), exc, previous_by_id.get(spec["id"])),
                )
    games = []
    sources = []
    for spec in specs:
        source_games, source = results[spec["id"]]
        games = merge_games(games, source_games)
        sources.append(source)
    return {"games": games, "sources": sources}


def _fetch_live(data_dir: Path, previous_sources=None) -> dict:
    return _fetch_specs(_source_specs(historical=False, live=True), data_dir, previous_sources)


def _write_outputs(data_dir: Path, games: list[dict], sources: list[dict]) -> dict:
    from .features import build_features

    data_dir.mkdir(parents=True, exist_ok=True)
    updated_at = utc_now_iso()
    dataset = build_features(games)
    document = {"games": dataset["games"], "sources": sources, "updated_at": updated_at}
    target = data_dir / "games.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(document, indent=2) + "\n")
    os.replace(temporary, target)
    np.savez_compressed(
        data_dir / "dataset.npz",
        X=dataset["X"],
        y=dataset["y"],
        feature_names=np.asarray(dataset["feature_names"]),
    )
    (data_dir / "dataset-games.json").write_text(
        json.dumps(
            {
                "games": dataset["games"],
                "feature_names": dataset["feature_names"],
                "updated_at": updated_at,
            },
            indent=2,
        )
        + "\n"
    )
    return document


def fetch_all(data_dir: Path = DEFAULT_DATA_DIR, historical: bool = True) -> dict:
    """Fetch public sources, archive raw responses and build the feature dataset."""

    data_dir = Path(data_dir)
    fetched = _fetch_specs(_source_specs(historical=historical, live=True), data_dir)
    return _write_outputs(data_dir, fetched["games"], fetched["sources"])


def refresh_games(data_dir: Path = DEFAULT_DATA_DIR) -> dict:
    """Refresh current schedules while retaining history and prior success timestamps."""

    data_dir = Path(data_dir)
    path = data_dir / "games.json"
    prior = json.loads(path.read_text()) if path.exists() else {"games": [], "sources": []}
    live = _fetch_live(data_dir, previous_sources=prior.get("sources", []))
    games = merge_games(prior.get("games", []), live["games"])
    live_ids = {source["id"] for source in live["sources"]}
    sources = [source for source in prior.get("sources", []) if source.get("id") not in live_ids]
    sources.extend(live["sources"])
    return _write_outputs(data_dir, games, sources)
