"""Strict season ingestion for the separate sensory backtest; no live ledger writes."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone


def exact_int(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an exact integer >= {minimum}.")
    return value


def normalize_season(payload, year):
    items = [g for d in payload.get("dates", []) for g in d.get("games", [])]
    if not items:
        raise ValueError("Season source contains no games.")
    resumed = {
        g.get("gamePk")
        for g in items
        if any("resume" in k.lower() and v for k, v in g.items())
        or "suspend" in str(g.get("status", {}).get("detailedState", "")).lower()
    }
    rows = []
    excluded = Counter()
    seen = set()
    for g in items:
        if g.get("gamePk") in resumed:
            excluded["resumed_or_suspended"] += 1
            continue
        if g.get("gameType") != "R":
            excluded["nonregular"] += 1
            continue
        detail = str(g.get("status", {}).get("detailedState", "")).lower()
        if "postpon" in detail or "cancel" in detail:
            excluded["unplayed"] += 1
            continue
        if g.get("status", {}).get("abstractGameState") != "Final":
            excluded["nonfinal"] += 1
            continue
        pk = exact_int(g.get("gamePk"), "gamePk", 1)
        start = datetime.fromisoformat(str(g["gameDate"]).replace("Z", "+00:00"))
        if start.tzinfo is None or start.astimezone(timezone.utc).year != year:
            raise ValueError("Game time is naive or outside requested season.")
        home, away = g["teams"]["home"], g["teams"]["away"]
        hs = exact_int(home.get("score"), "home score")
        aws = exact_int(away.get("score"), "away score")
        if hs == aws:
            excluded["tie"] += 1
            continue
        hi = exact_int(home["team"]["id"], "home team ID", 1)
        ai = exact_int(away["team"]["id"], "away team ID", 1)
        if hi == ai or pk in seen:
            raise ValueError("Duplicate eligible game or identical teams.")
        if home.get("isWinner") is not (hs > aws) or away.get("isWinner") is not (aws > hs):
            raise ValueError("Winner flag and final score disagree.")
        seen.add(pk)
        rows.append(
            dict(
                id=f"baseball:mlb:{pk}",
                sport="baseball",
                league="MLB",
                season=year,
                start_time=start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                home=home["team"]["name"],
                away=away["team"]["name"],
                home_key=f"mlb:{hi}",
                away_key=f"mlb:{ai}",
                home_score=hs,
                away_score=aws,
                outcome=0 if hs > aws else 2,
                status="final",
            )
        )
    return sorted(rows, key=lambda g: (g["start_time"], g["id"])), dict(excluded)
