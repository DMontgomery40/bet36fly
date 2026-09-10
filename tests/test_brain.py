import numpy as np

from bet36fly.brain import LIFEngine, encode_rates, stimulus_rates


def tiny_engine(weight=160):
    return LIFEngine(np.array([0, 1, 2, 2], np.int64), np.array([1, 2], np.int32),
                     np.array([weight, weight], np.float32), np.array([0], np.int32))


def test_spikes_propagate_across_real_edges_and_ablation_stops_them():
    e = tiny_engine()
    live = e.run(np.array([500], np.float32), duration_ms=100, seed=5)
    cut = tiny_engine(0).run(np.array([500], np.float32), duration_ms=100, seed=5)
    assert live['counts'][0] > 0
    assert live['counts'][1] > 0
    assert live['counts'][2] > 0
    assert cut['counts'][1:].sum() == 0


def test_inhibition_does_not_create_excitatory_spikes():
    result = tiny_engine(-160).run(np.array([500], np.float32), duration_ms=100, seed=5)
    assert result['counts'][0] > 0
    assert result['counts'][1:].sum() == 0


def test_seed_reproducibility_and_spike_trace_accounting():
    e = tiny_engine()
    a = e.run(np.array([200], np.float32), duration_ms=100, seed=3, sample=np.arange(3, dtype=np.int32))
    b = e.run(np.array([200], np.float32), duration_ms=100, seed=3, sample=np.arange(3, dtype=np.int32))
    np.testing.assert_array_equal(a['counts'], b['counts'])
    np.testing.assert_array_equal(a['trace'], b['trace'])
    np.testing.assert_array_equal(a['trace'].sum(axis=0), a['counts'])
    assert a['population'].sum() == a['counts'].sum()


def test_no_drive_means_quiescence_and_refractory_caps_output():
    e = tiny_engine()
    assert e.run(np.zeros(1, np.float32), duration_ms=100, seed=3)['counts'].sum() == 0
    result = e.run(np.array([1000], np.float32), duration_ms=100, seed=3)
    assert result['counts'][1] <= 100 / 2.2 + 1


def test_encoder_is_bounded_opponent_coded_and_feature_sensitive():
    a = encode_rates(np.zeros(4), 32)
    b = encode_rates(np.array([2, 0, 0, 0]), 32)
    assert a.shape == b.shape == (32,)
    assert np.isfinite(b).all() and b.min() >= 0 and b.max() <= 300
    assert b[0] > a[0] and b[4] < a[4]


def test_engine_validation_rejects_bad_graphs_and_parameters():
    import pytest
    with pytest.raises(ValueError):
        LIFEngine(np.array([0, 2]), np.array([1]), np.array([1.0]), np.array([0]))
    with pytest.raises(ValueError):
        tiny_engine().run(np.array([float('nan')]), duration_ms=100)


def test_large_sensory_catalog_uses_one_port_per_opponent_channel():
    for n_features in [2, 8, 16]:
        a = stimulus_rates(np.zeros(n_features), 686)
        b = stimulus_rates(np.ones(n_features), 686)
        assert np.count_nonzero(a) == 2 * n_features
        assert np.count_nonzero(a != b) == 2 * n_features
        assert np.all(a[a > 0] == 150)
