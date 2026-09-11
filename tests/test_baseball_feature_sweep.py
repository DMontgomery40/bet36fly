from copy import deepcopy
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from bet36fly import baseball_feature_sweep as sweep


def _game(index, start, home, away, home_score, away_score, *, split="train"):
    return {
        "id": f"baseball:mlb:{index}",
        "sport": "baseball",
        "league": "MLB",
        "start_time": start,
        "home_key": home,
        "away_key": away,
        "home": home,
        "away": away,
        "status": "final",
        "home_score": home_score,
        "away_score": away_score,
        "outcome": 0 if home_score > away_score else 2,
        "split": split,
    }


def test_predeclared_sweep_is_exactly_five_by_two_by_three():
    configs = sweep.predeclared_configs()

    assert len(configs) == 30
    assert len({row["id"] for row in configs}) == 30
    assert {row["form_window"] for row in configs} == {3, 5, 10, 20, 40}
    assert {row["history"] for row in configs} == {"pooled", "home-away"}
    assert {row["rest"] for row in configs} == {"none", "capped", "recovery"}


def test_result_enters_features_only_after_48_hours_and_next_utc_day_boundary():
    games = [
        _game(1, "2024-07-01T12:00:00Z", "a", "b", 5, 1),
        # 49 hours later, but the July 3 UTC-day batch begins before the 48-hour availability instant.
        _game(2, "2024-07-03T13:00:00Z", "a", "c", 2, 1),
        _game(3, "2024-07-04T13:00:00Z", "a", "d", 2, 1),
    ]
    changed = deepcopy(games)
    changed[0]["home_score"], changed[0]["away_score"], changed[0]["outcome"] = 0, 5, 2
    config = {"id": "w3-pooled-capped", "form_window": 3, "history": "pooled", "rest": "capped"}

    original = sweep.build_feature_matrix(games, config)
    mutated = sweep.build_feature_matrix(changed, config)
    form_index = original["feature_names"].index("home_form")

    assert original["game_ids"] == mutated["game_ids"]
    assert original["X"][1, form_index] == mutated["X"][1, form_index] == 0.5
    assert original["X"][2, form_index] == 1.0
    assert mutated["X"][2, form_index] == 0.0


def test_home_away_history_changes_role_statistics_but_rest_uses_all_games():
    games = [
        _game(1, "2024-06-01T12:00:00Z", "a", "b", 8, 1),
        _game(2, "2024-06-05T12:00:00Z", "c", "a", 9, 1),
        _game(3, "2024-06-10T12:00:00Z", "a", "d", 3, 2),
    ]
    pooled = sweep.build_feature_matrix(
        games, {"id": "pooled", "form_window": 5, "history": "pooled", "rest": "capped"}
    )
    roles = sweep.build_feature_matrix(
        games, {"id": "roles", "form_window": 5, "history": "home-away", "rest": "capped"}
    )
    form = pooled["feature_names"].index("home_form")
    rest = pooled["feature_names"].index("home_rest")

    assert pooled["X"][2, form] == pytest.approx(0.5)
    assert roles["X"][2, form] == pytest.approx(1.0)
    assert roles["X"][2, rest] == pooled["X"][2, rest]


def test_fold_and_final_fit_embargo_labels_unavailable_at_evaluation_day_start():
    games = [
        _game(1, "2024-06-28T00:00:00Z", "a", "b", 2, 1),
        _game(2, "2024-06-29T00:01:00Z", "c", "d", 2, 1),
        _game(3, "2024-07-01T12:00:00Z", "a", "c", 2, 1),
        _game(4, "2024-07-02T12:00:00Z", "b", "d", 2, 1),
    ]
    folds = sweep.rolling_folds(
        games,
        {game["id"] for game in games},
        specs=[("july", "2024-07-01", "2024-08-01")],
    )

    assert folds[0]["fit_ids"] == ["baseball:mlb:1"]
    assert folds[0]["evaluation_ids"] == ["baseball:mlb:3", "baseball:mlb:4"]
    assert folds[0]["embargoed_partition_ids"] == ["baseball:mlb:2"]
    assert sweep.available_before(games[0], "2024-07-01")
    assert not sweep.available_before(games[1], "2024-07-01")


def _synthetic_selection_games():
    games = []
    day = datetime(2024, 1, 1, 12, tzinfo=timezone.utc)
    teams = ["a", "b", "c", "d"]
    for index in range(32):
        home, away = teams[index % 4], teams[(index + 1) % 4]
        games.append(_game(index, (day + timedelta(days=index)).isoformat(), home, away,
                           4 if index % 2 == 0 else 1, 1 if index % 2 == 0 else 4))
    games += [
        _game(100, "2024-02-10T12:00:00Z", "a", "c", 4, 1, split="validation"),
        _game(101, "2024-02-11T12:00:00Z", "b", "d", 1, 4, split="validation"),
    ]
    return games


def test_changing_original_validation_labels_cannot_change_training_fold_selection():
    games = _synthetic_selection_games()
    changed = deepcopy(games)
    for game in changed:
        if game["split"] == "validation":
            game["outcome"] = 2 if game["outcome"] == 0 else 0
            game["home_score"], game["away_score"] = game["away_score"], game["home_score"]
    train_ids = {game["id"] for game in games if game["split"] == "train"}
    specs = [("fold-1", "2024-01-15", "2024-01-23"), ("fold-2", "2024-01-23", "2024-02-02")]
    configs = [
        {"id": "small-pooled", "form_window": 3, "history": "pooled", "rest": "none"},
        {"id": "large-roles", "form_window": 10, "history": "home-away", "rest": "recovery"},
    ]

    first = sweep.training_fold_sweep(games, train_ids, configs=configs, c_grid=[0.01, 0.1], fold_specs=specs)
    second = sweep.training_fold_sweep(changed, train_ids, configs=configs, c_grid=[0.01, 0.1], fold_specs=specs)

    assert first == second
    assert first["selected"]["config_id"] in {"small-pooled", "large-roles"}
    assert first["selected"]["C"] in {0.01, 0.1}
    assert len(first["candidates"]) == 4


def test_fold_scaler_ignores_evaluation_distribution():
    train_x = np.array([[0.0, 2.0], [2.0, 4.0], [1.0, 3.0], [3.0, 5.0]])
    train_y = np.array([0, 2, 0, 2])
    evaluation_x = np.array([[1000.0, -1000.0], [2000.0, -2000.0]])
    evaluation_y = np.array([0, 2])

    result = sweep.fit_fold(train_x, train_y, evaluation_x, evaluation_y, C=0.1)

    assert result["scaler_mean"] == [1.5, 3.5]
    assert result["fit_rows"] == 4
    assert result["evaluation_rows"] == 2
    assert np.isfinite(result["probabilities"]).all()
