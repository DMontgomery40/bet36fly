#!/usr/bin/env python3
"""Fetch or refresh the public BET36FLY phase-one sports dataset."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bet36fly.sports import DEFAULT_DATA_DIR, fetch_all, refresh_games  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--refresh", action="store_true", help="refresh live schedules and preserve history")
    parser.add_argument("--no-history", action="store_true", help="fetch current schedule windows only")
    args = parser.parse_args()

    result = (
        refresh_games(args.data_dir)
        if args.refresh
        else fetch_all(args.data_dir, historical=not args.no_history)
    )
    status_counts = Counter(game["status"] for game in result["games"])
    sport_counts = Counter(game["sport"] for game in result["games"])
    summary = {
        "data_dir": str(args.data_dir),
        "updated_at": result["updated_at"],
        "games": len(result["games"]),
        "by_sport": dict(sorted(sport_counts.items())),
        "by_status": dict(sorted(status_counts.items())),
        "sources": [
            {key: source.get(key) for key in ("id", "status", "fetched_at", "attempted_at", "game_count")}
            for source in result["sources"]
        ],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
