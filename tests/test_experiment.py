import numpy as np
import pytest

from bet36fly.experiment import chronological_split, fit_scale, scale, cache_identity


def test_chronological_partition_boundary_matrix():
    dates = ['2025-06-30T23:00:00+00:00', '2025-07-01T00:00:00+00:00',
             '2025-12-31T23:00:00+00:00', '2026-01-01T00:00:00+00:00',
             '2026-08-31T23:00:00+00:00', '2026-09-01T00:00:00+00:00']
    games = [{'start_time': d} for d in dates]
    train, val, test = chronological_split(games)
    assert np.flatnonzero(train).tolist() == [0]
    assert np.flatnonzero(val).tolist() == [1, 2]
    assert np.flatnonzero(test).tolist() == [3, 4]
    assert not (train & val | train & test | val & test).any()


def test_scaler_is_train_only_and_constant_features_are_finite():
    train = np.array([[1, 3], [3, 3]], np.float32)
    mean, std = fit_scale(train)
    np.testing.assert_allclose(mean, [2, 3])
    assert np.isfinite(scale(np.array([[10000, 3]], np.float32), mean, std)).all()
    np.testing.assert_allclose(scale(train, mean, std).mean(0), 0, atol=1e-7)


def test_cache_identity_covers_input_and_weight_and_neural_code_changes():
    x = np.zeros((2, 16), np.float32)
    first = cache_identity(x, 'graph-a', 'gain-a', 'code-a')
    assert first != cache_identity(x + 1, 'graph-a', 'gain-a', 'code-a')
    assert first != cache_identity(x, 'graph-b', 'gain-a', 'code-a')
    assert first != cache_identity(x, 'graph-a', 'gain-b', 'code-a')
    assert first != cache_identity(x, 'graph-a', 'gain-a', 'code-b')


def test_split_requires_aware_timestamps():
    with pytest.raises(ValueError):
        chronological_split([{'start_time': '2025-01-01T12:00:00'}])
