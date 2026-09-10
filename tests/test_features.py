from copy import deepcopy

import numpy as np

from bet36fly.features import FEATURE_NAMES, build_features


def game(game_id, when, home, away, status="final", home_score=1, away_score=0, sport="soccer"):
    if status != "final":
        home_score = away_score = None
    outcome = None
    if status == "final":
        outcome = 0 if home_score > away_score else 2 if home_score < away_score else 1
    return {
        "id": game_id,
        "sport": sport,
        "league": "EPL" if sport == "soccer" else "MLB",
        "start_time": when,
        "home": home,
        "away": away,
        "home_key": home.lower(),
        "away_key": away.lower(),
        "status": status,
        "home_score": home_score,
        "away_score": away_score,
        "outcome": outcome,
        "source": "fixture",
        "source_url": "fixture://games",
        "source_fetched_at": "2026-09-10T00:00:00Z",
        "venue": "",
    }


def test_build_features_contract_is_sorted_typed_and_finite():
    games = [
        game("later", "2024-01-02T12:00:00Z", "A", "C", status="scheduled"),
        game("earlier", "2024-01-01T12:00:00Z", "A", "B", home_score=2, away_score=0),
    ]

    result = build_features(games)

    assert [g["id"] for g in result["games"]] == ["earlier", "later"]
    assert result["X"].shape == (2, 16)
    assert result["X"].dtype == np.float32
    assert np.isfinite(result["X"]).all()
    assert result["y"].dtype == np.int64
    assert result["y"].tolist() == [0, -1]
    assert result["feature_names"] == FEATURE_NAMES
    assert len(set(FEATURE_NAMES)) == 16
    assert all("odd" not in name for name in FEATURE_NAMES)


def test_current_game_result_never_changes_its_own_features():
    original = game("target", "2024-01-01T12:00:00Z", "A", "B", home_score=9, away_score=0)
    reversed_result = deepcopy(original)
    reversed_result.update(home_score=0, away_score=9, outcome=2)

    first = build_features([original])
    second = build_features([reversed_result])

    np.testing.assert_array_equal(first["X"], second["X"])
    assert first["y"].tolist() == [0]
    assert second["y"].tolist() == [2]


def test_same_utc_day_results_do_not_leak_into_later_games_or_doubleheaders():
    first_final = game("first", "2024-06-01T12:00:00Z", "A", "B", home_score=10, away_score=0)
    later_same_day = game("same-day", "2024-06-01T22:00:00Z", "A", "C", status="scheduled")
    cold_start = game("cold", "2024-06-01T22:00:00Z", "A", "C", status="scheduled")
    next_day = game("next-day", "2024-06-02T12:00:00Z", "A", "D", status="scheduled")
    after_safety_delay = game("safe", "2024-06-04T12:00:00Z", "A", "E", status="scheduled")

    with_result = build_features([first_final, later_same_day, next_day, after_safety_delay])
    without_result = build_features([cold_start])

    np.testing.assert_array_equal(with_result["X"][1], without_result["X"][0])
    np.testing.assert_array_equal(with_result["X"][2], without_result["X"][0])
    assert not np.array_equal(with_result["X"][3], without_result["X"][0])


def test_late_prior_day_result_waits_48_hours_before_entering_state():
    late_final = game("late", "2024-06-01T23:00:00Z", "A", "B", home_score=6, away_score=0)
    after_midnight = game("midnight", "2024-06-02T00:30:00Z", "A", "C", status="scheduled")
    nearly_48_hours = game("nearly", "2024-06-03T22:30:00Z", "A", "D", status="scheduled")
    safely_available = game("available", "2024-06-04T12:00:00Z", "A", "E", status="scheduled")
    cold = build_features([after_midnight])

    result = build_features([late_final, after_midnight, nearly_48_hours, safely_available])

    np.testing.assert_array_equal(result["X"][1], cold["X"][0])
    np.testing.assert_array_equal(result["X"][2], cold["X"][0])
    assert not np.array_equal(result["X"][3], cold["X"][0])


def test_nonfinal_and_cancelled_games_never_update_team_state():
    baseline = game("target", "2024-07-02T12:00:00Z", "A", "B", status="scheduled")
    for ignored_status in ("scheduled", "live", "postponed", "cancelled"):
        ignored = game("ignored", "2024-07-01T12:00:00Z", "A", "B", status=ignored_status)
        result = build_features([ignored, baseline])
        cold = build_features([baseline])
        np.testing.assert_array_equal(result["X"][1], cold["X"][0])


def test_team_state_carries_across_calendar_year_and_function_restarts_are_deterministic():
    prior_season = game("season-one", "2024-05-20T12:00:00Z", "A", "B", home_score=2, away_score=0)
    new_season = game("season-two", "2024-08-17T12:00:00Z", "A", "C", status="scheduled")

    first = build_features([new_season, prior_season])
    restarted = build_features([prior_season, new_season])

    np.testing.assert_array_equal(first["X"], restarted["X"])
    assert first["X"][1, FEATURE_NAMES.index("home_games_played")] > 0
    assert first["X"][1, FEATURE_NAMES.index("home_elo")] > 0


def test_soccer_draw_and_baseball_two_class_labels_are_supported():
    games = [
        game("draw", "2024-01-01T12:00:00Z", "A", "B", home_score=1, away_score=1),
        game(
            "away-win",
            "2024-01-02T12:00:00Z",
            "C",
            "D",
            home_score=2,
            away_score=4,
            sport="baseball",
        ),
    ]

    result = build_features(games)

    assert result["y"].tolist() == [1, 2]
    assert result["X"][0, FEATURE_NAMES.index("is_baseball")] == 0
    assert result["X"][1, FEATURE_NAMES.index("is_baseball")] == 1
