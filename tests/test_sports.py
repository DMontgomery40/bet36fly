import json
import subprocess
import sys
from pathlib import Path

import pytest

from bet36fly.sports import (
    canonical_team_key,
    merge_games,
    normalize_espn_soccer,
    normalize_football_csv,
    normalize_mlb,
    refresh_games,
)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("AFC Bournemouth", "bournemouth"),
        ("Bournemouth", "bournemouth"),
        ("Manchester United", "man-united"),
        ("Man United", "man-united"),
        ("Nottingham Forest", "nottm-forest"),
        ("Nott'm Forest", "nottm-forest"),
        ("Wolverhampton Wanderers", "wolves"),
        ("Wolves", "wolves"),
        ("Brighton & Hove Albion", "brighton"),
        ("Brighton", "brighton"),
        ("Leicester City", "leicester"),
        ("Leicester", "leicester"),
        ("Ipswich Town", "ipswich"),
        ("Ipswich", "ipswich"),
        ("Sheffield United", "sheffield-utd"),
        ("Sheffield Utd", "sheffield-utd"),
        ("Luton Town", "luton"),
        ("Luton", "luton"),
        ("Leeds United", "leeds"),
        ("Leeds", "leeds"),
    ],
)
def test_canonical_team_key_joins_cross_source_soccer_aliases(name, expected):
    assert canonical_team_key(name, "soccer") == expected


def test_normalize_football_csv_uses_results_as_labels_and_keeps_odds():
    raw = (
        "Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A\n"
        "E0,11/08/2023,20:00,Burnley,Man City,0,3,A,8.0,5.5,1.33\n"
    ).encode()
    url = "https://www.football-data.co.uk/mmz4281/2324/E0.csv"

    games = normalize_football_csv(raw, url, "2026-09-10T12:00:00Z")

    assert games == [
        {
            "id": "soccer:epl:2023-08-11:burnley:man-city",
            "sport": "soccer",
            "league": "EPL",
            "start_time": "2023-08-11T19:00:00Z",
            "home": "Burnley",
            "away": "Man City",
            "home_key": "burnley",
            "away_key": "man-city",
            "status": "final",
            "home_score": 0,
            "away_score": 3,
            "outcome": 2,
            "source": "football-data.co.uk",
            "source_url": url,
            "source_fetched_at": "2026-09-10T12:00:00Z",
            "venue": "",
            "odds": [8.0, 5.5, 1.33],
        }
    ]


def test_football_csv_converts_uk_summer_and_winter_kickoffs_to_utc():
    raw = (
        "Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"
        "E0,11/08/2023,20:00,Burnley,Man City,0,3,A\n"
        "E0,01/01/2024,20:00,Liverpool,Newcastle,4,2,H\n"
    ).encode()

    games = normalize_football_csv(raw, "https://example.test/E0.csv", "2026-09-10T12:00:00Z")

    assert [game["start_time"] for game in games] == [
        "2023-08-11T19:00:00Z",
        "2024-01-01T20:00:00Z",
    ]


@pytest.mark.parametrize(
    ("provider_state", "completed", "description", "expected"),
    [
        ("pre", False, "Scheduled", "scheduled"),
        ("in", False, "In Progress", "live"),
        ("post", True, "Final", "final"),
        ("pre", False, "Postponed", "postponed"),
        ("pre", False, "Canceled", "cancelled"),
    ],
)
def test_espn_status_matrix(provider_state, completed, description, expected):
    payload = {
        "events": [
            {
                "id": "123",
                "date": "2026-09-12T14:00Z",
                "competitions": [
                    {
                        "status": {
                            "type": {
                                "state": provider_state,
                                "completed": completed,
                                "description": description,
                                "name": "STATUS_" + description.upper().replace(" ", "_"),
                            }
                        },
                        "venue": {"fullName": "Example Ground"},
                        "competitors": [
                            {
                                "homeAway": "home",
                                "score": "2",
                                "team": {"displayName": "AFC Bournemouth", "logo": "home.png"},
                            },
                            {
                                "homeAway": "away",
                                "score": "1",
                                "team": {"displayName": "Manchester United", "logo": "away.png"},
                            },
                        ],
                    }
                ],
            }
        ]
    }

    game = normalize_espn_soccer(
        payload,
        "https://site.api.espn.com/example",
        "2026-09-10T12:00:00Z",
    )[0]

    assert game["status"] == expected
    assert game["home_key"] == "bournemouth"
    assert game["away_key"] == "man-united"
    assert game["home_score"] == (2 if expected in {"live", "final"} else None)
    assert game["outcome"] == (0 if expected == "final" else None)


@pytest.mark.parametrize(
    ("abstract", "detailed", "expected"),
    [
        ("Preview", "Scheduled", "scheduled"),
        ("Live", "In Progress", "live"),
        ("Final", "Final", "final"),
        ("Preview", "Postponed", "postponed"),
        ("Preview", "Cancelled", "cancelled"),
    ],
)
def test_mlb_status_matrix_and_no_pregame_score(abstract, detailed, expected):
    payload = {
        "dates": [
            {
                "games": [
                    {
                        "gamePk": 999,
                        "gameDate": "2026-09-10T23:40:00Z",
                        "status": {"abstractGameState": abstract, "detailedState": detailed},
                        "teams": {
                            "home": {"team": {"name": "Chicago White Sox"}, "score": 4},
                            "away": {"team": {"name": "Pittsburgh Pirates"}, "score": 3},
                        },
                        "venue": {"name": "Rate Field"},
                    }
                ]
            }
        ]
    }

    game = normalize_mlb(payload, "https://statsapi.mlb.com/example", "2026-09-10T12:00:00Z")[0]

    assert game["status"] == expected
    assert game["id"] == "baseball:mlb:999"
    assert game["home_score"] == (4 if expected in {"live", "final"} else None)
    assert game["outcome"] == (0 if expected == "final" else None)
    assert game["odds"] == [None, None, None]


def test_mlb_suspended_final_without_completion_time_is_not_a_training_label():
    payload = {
        "dates": [
            {
                "games": [
                    {
                        "gamePk": 1001,
                        "gameDate": "2026-04-10T23:00:00Z",
                        "resumeDate": "2026-04-15T18:00:00Z",
                        "status": {"abstractGameState": "Final", "detailedState": "Final"},
                        "teams": {
                            "home": {"team": {"name": "Chicago Cubs"}, "score": 4},
                            "away": {"team": {"name": "St. Louis Cardinals"}, "score": 3},
                        },
                        "venue": {"name": "Wrigley Field"},
                    }
                ]
            }
        ]
    }

    game = normalize_mlb(payload, "https://statsapi.mlb.com/example", "2026-09-10T12:00:00Z")[0]

    assert game["status"] == "final"
    assert game["home_score"] is None
    assert game["away_score"] is None
    assert game["outcome"] is None


def test_mlb_duplicate_resume_entries_cannot_restore_excluded_result():
    resumed = {
        "gamePk": 1002,
        "gameDate": "2026-04-10T23:00:00Z",
        "resumeDate": "2026-04-15T18:00:00Z",
        "status": {"abstractGameState": "Final", "detailedState": "Final"},
        "teams": {
            "home": {"team": {"name": "Chicago Cubs"}, "score": 4},
            "away": {"team": {"name": "St. Louis Cardinals"}, "score": 3},
        },
        "venue": {"name": "Wrigley Field"},
    }
    repeated_without_marker = {**resumed}
    repeated_without_marker.pop("resumeDate")
    payload = {"dates": [{"games": [resumed]}, {"games": [repeated_without_marker]}]}

    games = normalize_mlb(payload, "https://statsapi.mlb.com/example", "2026-09-10T12:00:00Z")

    assert len(games) == 1
    assert games[0]["outcome"] is None


def test_merge_games_replaces_same_cross_source_fixture_without_duplication():
    old = {
        "id": "soccer:epl:2026-09-12:bournemouth:man-united",
        "sport": "soccer",
        "start_time": "2026-09-12T14:00:00Z",
        "home_key": "bournemouth",
        "away_key": "man-united",
        "status": "scheduled",
        "source_fetched_at": "2026-09-09T12:00:00Z",
    }
    fresh = {**old, "status": "final", "outcome": 0, "source_fetched_at": "2026-09-12T18:00:00Z"}

    assert merge_games([old], [fresh]) == [fresh]


def test_refresh_failure_preserves_games_and_last_successful_fetch_time(tmp_path, monkeypatch):
    data_dir = tmp_path / "sports"
    data_dir.mkdir()
    prior = {
        "games": [
            {
                "id": "historic",
                "sport": "soccer",
                "league": "EPL",
                "start_time": "2024-01-01T00:00:00Z",
                "home": "A",
                "away": "B",
                "home_key": "a",
                "away_key": "b",
                "status": "final",
                "home_score": 1,
                "away_score": 0,
                "outcome": 0,
                "source": "fixture",
                "source_url": "fixture://history",
                "source_fetched_at": "2026-09-09T10:00:00Z",
                "venue": "",
            }
        ],
        "sources": [
            {
                "id": "espn-epl-live",
                "url": "old-url",
                "status": "ok",
                "fetched_at": "2026-09-09T10:00:00Z",
                "sha256": "abc",
            }
        ],
        "updated_at": "2026-09-09T10:00:00Z",
    }
    (data_dir / "games.json").write_text(json.dumps(prior))

    def failed_live(_data_dir, previous_sources=None):
        assert previous_sources == prior["sources"]
        return {
            "games": [],
            "sources": [
                {
                    "id": "espn-epl-live",
                    "url": "new-url",
                    "status": "stale",
                    "fetched_at": "2026-09-09T10:00:00Z",
                    "attempted_at": "2026-09-10T10:00:00Z",
                    "error": "timeout",
                }
            ],
        }

    monkeypatch.setattr("bet36fly.sports._fetch_live", failed_live)
    result = refresh_games(data_dir)

    assert result["games"] == prior["games"]
    assert result["sources"][0]["status"] == "stale"
    assert result["sources"][0]["fetched_at"] == "2026-09-09T10:00:00Z"
    saved = json.loads((data_dir / "games.json").read_text())
    assert saved["games"] == prior["games"]


def test_fetch_script_runs_directly_from_repository_root():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "scripts/fetch_sports.py", "--help"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--refresh" in result.stdout


def test_live_fetch_window_includes_recent_days_for_final_result_refresh():
    from urllib.parse import parse_qs, urlparse
    from datetime import datetime, timezone, timedelta
    from bet36fly.sports import _source_specs
    today = datetime.now(timezone.utc).date()
    sources = _source_specs(historical=False, live=True)
    mlb = next(s for s in sources if s['id'] == 'mlb-live')
    query = parse_qs(urlparse(mlb['url']).query)
    assert query['startDate'] == [(today - timedelta(days=14)).isoformat()]
    soccer = next(s for s in sources if s['id'] == 'espn-epl-live')
    assert (today - timedelta(days=14)).strftime('%Y%m%d') in soccer['url']


def test_rescheduled_epl_fixture_replaces_old_date_but_keeps_other_seasons():
    def game(day, status='scheduled'):
        return {'id': day, 'sport': 'soccer', 'league': 'EPL', 'home_key': 'a', 'away_key': 'b',
                'start_time': day+'T14:00:00Z', 'status': status}
    old, other_season, new = game('2026-09-12'), game('2025-09-12', 'final'), game('2026-09-20')
    result = merge_games([old, other_season], [new])
    assert {g['id'] for g in result} == {'2025-09-12', '2026-09-20'}
