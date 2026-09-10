"""Chronological, pregame-only sports features.

Feature state advances in UTC-day batches. A final earlier in clock time does not
prove it was known before another game that day, so no same-day result can affect
another game's row.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from itertools import groupby

import numpy as np


FEATURE_NAMES = [
    "home_elo",
    "away_elo",
    "elo_diff",
    "home_form",
    "away_form",
    "form_diff",
    "home_win_rate",
    "away_win_rate",
    "home_games_played",
    "away_games_played",
    "home_rest_days",
    "away_rest_days",
    "rest_diff",
    "home_avg_margin",
    "away_avg_margin",
    "is_baseball",
]


@dataclass
class _TeamState:
    elo: float = 1500.0
    games: int = 0
    wins: int = 0
    margin_sum: float = 0.0
    recent: deque[float] = field(default_factory=lambda: deque(maxlen=5))
    last_day: object | None = None


def _parse_start(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _mean(values: deque[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.5


def _win_rate(state: _TeamState) -> float:
    return state.wins / state.games if state.games else 0.5


def _games_scale(state: _TeamState) -> float:
    return min(state.games, 50) / 50.0


def _rest_scale(state: _TeamState, day) -> float:
    if state.last_day is None:
        return 0.0
    return min(max((day - state.last_day).days, 0), 14) / 14.0


def _margin_scale(state: _TeamState, sport: str) -> float:
    if not state.games:
        return 0.0
    typical_margin = 5.0 if sport == "baseball" else 3.0
    return float(np.clip((state.margin_sum / state.games) / typical_margin, -1.0, 1.0))


def _state_key(game: dict, side: str) -> tuple[str, str, str]:
    return game["sport"], game["league"], game[f"{side}_key"]


def _row(game: dict, states: defaultdict, day) -> list[float]:
    home = states[_state_key(game, "home")]
    away = states[_state_key(game, "away")]
    home_form = _mean(home.recent)
    away_form = _mean(away.recent)
    home_rest = _rest_scale(home, day)
    away_rest = _rest_scale(away, day)
    return [
        home.elo / 2000.0,
        away.elo / 2000.0,
        (home.elo - away.elo) / 400.0,
        home_form,
        away_form,
        home_form - away_form,
        _win_rate(home),
        _win_rate(away),
        _games_scale(home),
        _games_scale(away),
        home_rest,
        away_rest,
        home_rest - away_rest,
        _margin_scale(home, game["sport"]),
        _margin_scale(away, game["sport"]),
        float(game["sport"] == "baseball"),
    ]


def _is_usable_final(game: dict) -> bool:
    return (
        game.get("status") == "final"
        and game.get("outcome") in {0, 1, 2}
        and isinstance(game.get("home_score"), int)
        and isinstance(game.get("away_score"), int)
    )


def _update(game: dict, states: defaultdict, day) -> None:
    home = states[_state_key(game, "home")]
    away = states[_state_key(game, "away")]
    home_score = game["home_score"]
    away_score = game["away_score"]
    if home_score > away_score:
        home_result, away_result = 1.0, 0.0
    elif home_score < away_score:
        home_result, away_result = 0.0, 1.0
    else:
        home_result = away_result = 0.5

    expected_home = 1.0 / (1.0 + 10.0 ** ((away.elo - home.elo) / 400.0))
    k = 16.0 if game["sport"] == "baseball" else 24.0
    delta = k * (home_result - expected_home)
    home.elo += delta
    away.elo -= delta

    for state, result, margin in (
        (home, home_result, home_score - away_score),
        (away, away_result, away_score - home_score),
    ):
        state.games += 1
        state.wins += int(result == 1.0)
        state.margin_sum += margin
        state.recent.append(result)
        state.last_day = day


def build_features(games: list[dict]) -> dict:
    """Build deterministic 16-channel feature rows in chronological order.

    Unknown teams use neutral priors. Unfinished, cancelled and postponed games
    receive a feature row and label ``-1`` but never update team state.
    """

    sorted_games = sorted(games, key=lambda game: (_parse_start(game["start_time"]), game["id"]))
    states: defaultdict[tuple[str, str, str], _TeamState] = defaultdict(_TeamState)
    rows: list[list[float]] = []
    labels: list[int] = []
    pending: list[tuple[dict, object, datetime]] = []

    for day, day_games_iter in groupby(sorted_games, key=lambda game: _parse_start(game["start_time"]).date()):
        day_start = datetime.combine(day, time.min, timezone.utc)
        ready, pending = (
            [entry for entry in pending if entry[2] <= day_start],
            [entry for entry in pending if entry[2] > day_start],
        )
        for prior_game, prior_day, _available_at in ready:
            _update(prior_game, states, prior_day)
        day_games = list(day_games_iter)
        for game in day_games:
            rows.append(_row(game, states, day))
            labels.append(int(game["outcome"]) if _is_usable_final(game) else -1)
        for game in day_games:
            if _is_usable_final(game):
                pending.append((game, day, _parse_start(game["start_time"]) + timedelta(hours=48)))

    matrix = np.asarray(rows, dtype=np.float32)
    if not rows:
        matrix = np.empty((0, len(FEATURE_NAMES)), dtype=np.float32)
    return {
        "games": sorted_games,
        "X": matrix,
        "y": np.asarray(labels, dtype=np.int64),
        "feature_names": FEATURE_NAMES.copy(),
    }
