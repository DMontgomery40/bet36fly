"""Leakage, symmetry, uncertainty and chance-acceptance contracts."""

import numpy as np
import pytest

from bet36fly.sensory_backtest import team_vectors, quality_keys, neural_features, paired_evaluation


def encoder():
    return dict(
        coef=[1.0, 0, 0, 0, 0],
        intercept=0.2,
        scales=[1.0] * 5,
        center=0.0,
        spread=1.0,
        bootstrap_coef=[[1.0, 0, 0, 0, 0]] * 3,
        bootstrap_intercept=[0.2] * 3,
    )


def matrix():
    x = np.zeros((2, 16))
    x[:, 0] = [0.8, 0.7]
    x[:, 1] = [0.7, 0.8]
    x[:, 3:5] = 0.5
    x[:, 6:8] = 0.5
    x[:, 8:10] = 1
    return x


def test_independent_qualities_include_venue_without_pair_normalization():
    x = matrix()
    h, a = team_vectors(x)
    assert np.allclose(h[:, 0], [0.05, -0.05]) and np.allclose(a[:, 0], [-0.05, 0.05])
    first = quality_keys(x, encoder())
    changed = x.copy()
    changed[:, 1] = 0.99
    second = quality_keys(changed, encoder())
    assert np.array_equal(first["home_q"], second["home_q"])
    assert not np.array_equal(first["away_q"], second["away_q"])


def test_cold_start_preserves_full_uncertainty_and_no_bitter_endpoint():
    x = matrix()
    x[:, 8:10] = 0
    e = encoder()
    e["coef"] = [100.0, 0, 0, 0, 0]
    e["bootstrap_coef"] = [e["coef"]] * 3
    result = quality_keys(x, e)
    assert np.array_equal(result["home_bounds"], np.tile([0.0, 1.0], (2, 1)))
    assert np.array_equal(result["away_bounds"], np.tile([0.0, 1.0], (2, 1)))
    assert not (result["home_keys"] == 35).any()


def test_neural_features_only_use_neural_cache_and_reverse_exactly():
    cache = np.arange(144, dtype=float).reshape(36, 4)
    keys = dict(home_keys=np.array([4, 10]), away_keys=np.array([10, 4]))
    z = neural_features(keys, cache)
    assert np.array_equal(z[0], -z[1])
    assert not neural_features(keys, np.zeros((36, 4))).any()


def test_acceptance_requires_accuracy_and_both_loss_comparisons():
    y = np.tile([0, 1], 50)
    dates = [f"2022-04-{1 + i % 28:02d}T12:00:00Z" for i in range(100)]
    good = np.where(y, 0.7, 0.3)
    result = paired_evaluation(
        y,
        {"neural": good, "uniform": np.full(100, 0.5), "prior": np.full(100, 0.5), "encoder_only": good},
        dates,
        replicates=100,
    )
    assert result["goal_passed"]
    assert result["paired_loss"]["encoder_only"]["mean"] == 0
    result = paired_evaluation(
        y,
        {"neural": np.full(100, 0.5), "uniform": np.full(100, 0.5), "prior": np.full(100, 0.5)},
        dates,
        replicates=100,
    )
    assert not result["goal_passed"]


@pytest.mark.parametrize("p", [np.array([np.nan, 0.5]), np.array([1.1, 0.5]), np.array([0.5])])
def test_invalid_prediction_sets_fail(p):
    with pytest.raises(ValueError):
        paired_evaluation(
            np.array([0, 1]),
            {"neural": p, "uniform": p, "prior": p},
            ["2022-01-01", "2022-01-08"],
            replicates=10,
        )


def test_fitted_encoder_and_readout_roundtrip_preserve_predictions():
    import json
    from bet36fly.sensory_backtest import fit_encoder, encoder_probability, fit_readout, readout_probability

    rng = np.random.default_rng(17)
    x = np.zeros((80, 16))
    x[:, 0:2] = 0.75 + rng.normal(0, 0.05, (80, 2))
    x[:, 3:5] = rng.uniform(0.2, 0.8, (80, 2))
    x[:, 6:8] = rng.uniform(0.2, 0.8, (80, 2))
    x[:, 8:10] = 1
    y = (x[:, 0] > x[:, 1]).astype(int)
    dates = [f"2020-{1 + i // 28:02d}-{1 + i % 28:02d}T00:00:00Z" for i in range(80)]
    e = fit_encoder(x, y, dates, 0.1, bootstraps=3)
    restored = json.loads(json.dumps(e))
    assert np.array_equal(encoder_probability(x, e), encoder_probability(x, restored))
    cache = np.tile(np.arange(36, dtype=float)[:, None], (1, 4))
    cache[35] = 0
    z = neural_features(quality_keys(x, e), cache)
    readout = fit_readout(z, y, 0.1)
    p = readout_probability(z, readout)
    assert np.allclose(readout_probability(-z, readout), 1 - p)
    assert np.array_equal(readout_probability(np.zeros_like(z), readout), np.full(80, 0.5))


def test_confirmation_preflight_rejects_changed_allocation_before_source_access(tmp_path):
    from scripts.run_sensory_confirmation import preflight

    for key, value in [("year", 2022), ("attempt", 2), ("alpha", 0.05), ("replicates", 100)]:
        config = dict(attempt=1, year=2023, alpha=0.025, replicates=10000)
        config[key] = value
        with pytest.raises(ValueError):
            preflight(config, root=tmp_path)


def test_future_outcome_does_not_enter_its_own_or_prior_features():
    from copy import deepcopy
    from bet36fly.features import build_features

    games = [
        dict(
            id=str(i),
            sport="baseball",
            league="MLB",
            season=2022,
            start_time=f"2022-04-{1 + i * 3:02d}T12:00:00Z",
            home_key="h",
            away_key="a",
            status="final",
            outcome=0,
            home_score=4,
            away_score=2,
        )
        for i in range(4)
    ]
    a = build_features(games)["X"]
    modified = deepcopy(games)
    modified[2].update(home_score=0, away_score=9, outcome=2)
    b = build_features(modified)["X"]
    assert np.array_equal(a[:3], b[:3])
    assert not np.array_equal(a[3], b[3])
