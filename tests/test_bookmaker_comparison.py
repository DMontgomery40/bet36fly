import copy
import hashlib
import json
import math

import pytest

from bet36fly import bookmaker_comparison as comparison


@pytest.mark.parametrize(
    ("price", "expected"),
    [(150, 2.5), (-200, 1.5), ("+120", 2.2), ("-125", 1.8)],
)
def test_american_prices_convert_to_decimal_without_rounding(price, expected):
    assert comparison.american_to_decimal(price) == pytest.approx(expected)


@pytest.mark.parametrize("price", [0, 99, -99, float("inf"), "evens"])
def test_invalid_american_prices_are_rejected(price):
    with pytest.raises(ValueError, match="American"):
        comparison.american_to_decimal(price)


def test_moneyline_is_proportionally_devigged_for_both_formats():
    # Raw implied probabilities are .6 and 1 / 2.3; proportional normalization gives these literals.
    assert comparison.devig_moneyline(-150, 130, "american") == pytest.approx((0.5798319328, 0.4201680672))
    assert comparison.devig_moneyline(2.0, 4.0, "decimal") == pytest.approx((2 / 3, 1 / 3))


def _fixture(game_id, start_time, *, game_number=None, outcome=0):
    row = {
        "id": game_id,
        "sport": "baseball",
        "start_time": start_time,
        "home": "New York Yankees",
        "away": "Boston Red Sox",
        "home_key": "new-york-yankees",
        "away_key": "boston-red-sox",
        "outcome": outcome,
    }
    if game_number is not None:
        row["game_number"] = game_number
    return row


def _odds(row_id, **overrides):
    row = {
        "sportsbook": "Example Book",
        "market": "moneyline",
        "price_format": "american",
        "home_key": "NYY",
        "away_key": "BOS",
        "date": "2025-07-04",
        "timezone": "America/New_York",
        "home_price": -120,
        "away_price": 110,
        "quote_timing": "closing",
        "provider": "public-example",
        "provider_source_row_id": row_id,
        "source_url": "https://example.test/archive",
        "source_fetched_at": "2026-09-11T00:00:00Z",
        "raw_source_sha256": "a" * 64,
    }
    row.update(overrides)
    return row


def test_date_only_doubleheader_is_rejected_without_using_outcomes_and_exact_start_resolves_it():
    fixtures = [
        _fixture("baseball:mlb:1", "2025-07-04T17:05:00Z", game_number=1, outcome=0),
        _fixture("baseball:mlb:2", "2025-07-04T23:05:00Z", game_number=2, outcome=2),
    ]
    records = [
        _odds("ambiguous"),
        _odds("timed", start_time="2025-07-04T23:05:00Z"),
        _odds("numbered", game_number=1),
    ]
    original = copy.deepcopy(records)

    result = comparison.match_odds_records(records, fixtures)

    assert records == original
    assert [(row["provider_source_row_id"], row["game_id"]) for row in result["matched"]] == [
        ("timed", "baseball:mlb:2"),
        ("numbered", "baseball:mlb:1"),
    ]
    assert result["audit"]["excluded_counts"] == {"ambiguous_fixture": 1}
    rejected = result["audit"]["records"][0]
    assert rejected["provider_source_row_id"] == "ambiguous"
    assert rejected["candidate_game_ids"] == ["baseball:mlb:1", "baseball:mlb:2"]
    assert "outcome" not in rejected


def test_date_matching_requires_an_explicit_valid_timezone():
    fixture = _fixture("baseball:mlb:1", "2025-07-04T17:05:00Z")
    for timezone in (None, "Not/A_Zone"):
        record = _odds("bad-zone", timezone=timezone)
        if timezone is None:
            record.pop("timezone")
        result = comparison.match_odds_records([record], [fixture])
        assert result["matched"] == []
        assert result["audit"]["excluded_counts"] == {"invalid_record": 1}


def test_every_model_and_book_is_scored_on_one_global_fixture_intersection():
    fixtures = [
        _fixture("g1", "2025-07-04T17:05:00Z", outcome=0),
        _fixture("g2", "2025-07-11T17:05:00Z", outcome=2),
    ]
    predictions = {
        "fly-whole": {
            "g1": [0.8, 0.0, 0.2],
            "g2": [0.1, 0.0, 0.9],
        },
        "feature-logistic": {
            "g1": [0.6, 0.0, 0.4],
            "g2": [0.9, 0.0, 0.1],
        },
    }
    matched = [
        {"game_id": "g1", "sportsbook": "Book A", "probabilities": [0.7, 0.0, 0.3]},
        {"game_id": "g2", "sportsbook": "Book A", "probabilities": [0.4, 0.0, 0.6]},
        {"game_id": "g1", "sportsbook": "Book B", "probabilities": [0.75, 0.0, 0.25]},
    ]

    result = comparison.evaluate_matched(fixtures, predictions, matched, replicates=40, seed=7)

    assert result["fixture_ids"] == ["g1"]
    assert result["coverage"]["global_intersection"] == 1
    assert result["coverage"]["excluded_not_shared_by_all_books"] == 1
    assert {row["n"] for row in result["scores"]} == {1}
    assert {row["fixture_ids_sha256"] for row in result["scores"]} == {
        hashlib.sha256(b'["g1"]').hexdigest()
    }
    scores = {row["name"]: row for row in result["scores"]}
    assert scores["fly-whole"]["log_loss"] == pytest.approx(-math.log(0.8))
    assert scores["Book A"]["log_loss"] == pytest.approx(-math.log(0.7))
    assert scores["fly-whole"]["brier"] == pytest.approx(0.08)
    assert scores["fly-whole"]["accuracy"] == 1.0
    assert scores["fly-whole"]["ece"] == pytest.approx(0.2)
    assert len(result["paired_weekly"]) == 4
    assert all(row["n"] == 1 for row in result["paired_weekly"])
    assert all(row["limitation"].startswith("Single frozen seed-42") for row in result["paired_weekly"])


def test_load_odds_preserves_raw_rows_and_file_provenance(tmp_path):
    raw = {
        "schema_version": 1,
        "source": {"provider": "archive", "license": "public"},
        "records": [_odds("source-17", unused_provider_field={"line": 17})],
    }
    path = tmp_path / "odds.json"
    encoded = json.dumps(raw, separators=(",", ":"))
    path.write_text(encoded)

    loaded = comparison.load_odds(path)

    assert loaded["records"] == raw["records"]
    assert loaded["source"] == raw["source"]
    assert loaded["provenance"]["sha256"] == hashlib.sha256(encoded.encode()).hexdigest()
    assert loaded["provenance"]["path"] == str(path.resolve())
