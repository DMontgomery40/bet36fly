"""Retrieve only 2019–2022 public MLB development data; confirmation is inaccessible."""

import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly.connectome import ROOT  # noqa: E402
from bet36fly.sensory_data import normalize_season  # noqa: E402


def main():
    dest = ROOT / "data/sensory-sports/development-2019-2022-v2"
    if dest.exists():
        raise ValueError("Refusing to overwrite an existing source retrieval.")
    dest.mkdir(parents=True)
    manifest = dict(status="running", sources=[], rows=0, confirmation_accessed=False)
    games = []
    try:
        for year in [2019, 2020, 2021, 2022]:
            url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameType=R&season={year}"
            with urllib.request.urlopen(url, timeout=60) as response:
                raw = response.read()
            (dest / f"{year}.json").write_bytes(raw)
            now = datetime.now(timezone.utc).isoformat()
            rows, excluded = normalize_season(json.loads(raw), year)
            source = dict(
                year=year,
                url=url,
                fetched_at=now,
                sha256=hashlib.sha256(raw).hexdigest(),
                bytes=len(raw),
                eligible=len(rows),
                exclusions=excluded,
            )
            for row in rows:
                row.update(source_url=url, source_fetched_at=now, source_sha256=source["sha256"])
            games.extend(rows)
            manifest["sources"].append(source)
            print(json.dumps(source), flush=True)
        manifest["rows"] = len(games)
        (dest / "games.json").write_text(json.dumps(games, indent=2) + "\n")
        manifest["games_sha256"] = hashlib.sha256((dest / "games.json").read_bytes()).hexdigest()
        manifest["status"] = "completed"
    except Exception as exc:
        manifest.update(status="failed", error=str(exc))
        raise
    finally:
        (dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
