"""Frozen source eligibility and leakage boundary for sensory sports research."""

from copy import deepcopy

import pytest

from bet36fly.sensory_data import normalize_season


def game(pk=1):
    return dict(
        gamePk=pk,
        gameType="R",
        gameDate="2022-04-01T20:00:00Z",
        status=dict(abstractGameState="Final", detailedState="Final"),
        teams=dict(
            home=dict(team=dict(id=10, name="H"), score=4, isWinner=True),
            away=dict(team=dict(id=20, name="A"), score=2, isWinner=False),
        ),
    )


def payload(*games):
    return dict(dates=[dict(games=list(games))])


def test_eligible_result_and_exact_team_identity():
    rows, excluded = normalize_season(payload(game()), 2022)
    assert len(rows) == 1 and rows[0]["outcome"] == 0 and rows[0]["home_key"] == "mlb:10"
    assert not excluded


@pytest.mark.parametrize(
    "key,value", [("gamePk", 1.5), ("gameDate", "2023-01-01T00:00:00Z"), ("gameDate", "2022-04-01T20:00:00")]
)
def test_malformed_eligible_source_fails(key, value):
    g = game()
    g[key] = value
    with pytest.raises(ValueError):
        normalize_season(payload(g), 2022)


def test_resumed_id_is_excluded_across_occurrences_before_duplicate_check():
    g = game()
    r = deepcopy(g)
    r["resumeDate"] = "2022-05-01T20:00:00Z"
    rows, excluded = normalize_season(payload(g, r, game(2)), 2022)
    assert [r["id"] for r in rows] == ["baseball:mlb:2"]
    assert excluded["resumed_or_suspended"] == 2


def test_duplicate_or_score_conflict_fails_closed():
    with pytest.raises(ValueError):
        normalize_season(payload(game(), game()), 2022)
    for score in [True, 4.5, -1]:
        g = game()
        g["teams"]["home"]["score"] = score
        with pytest.raises(ValueError):
            normalize_season(payload(g), 2022)
    g = game()
    g["teams"]["away"]["isWinner"] = True
    with pytest.raises(ValueError):
        normalize_season(payload(g), 2022)


def test_nonfinal_nonregular_and_ties_are_counted():
    a = game()
    a["gameType"] = "S"
    b = game(2)
    b["status"]["abstractGameState"] = "Preview"
    c = game(3)
    c["teams"]["away"]["score"] = 4
    rows, excluded = normalize_season(payload(a, b, c), 2022)
    assert not rows and sum(excluded.values()) == 3
    with pytest.raises(ValueError):
        normalize_season({}, 2022)


@pytest.mark.parametrize("status", ["Postponed", "Cancelled", "Canceled", "Postponed: Rain"])
def test_terminal_unplayed_status_overrides_final_abstract_state(status):
    g = game()
    g["status"]["detailedState"] = status
    del g["teams"]["home"]["score"]
    rows, excluded = normalize_season(payload(g), 2022)
    assert not rows and excluded == {"unplayed": 1}
