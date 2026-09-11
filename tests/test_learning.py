import numpy as np
import torch

from bet36fly.learning import PlasticSurrogate, masked_logits, fit_readout, probabilities, metrics
from bet36fly.grouped_learning import (
    GroupedPlasticSurrogate, build_gain_groups, fit_grouped_plasticity,
    fit_surrogate_inputs, independent_gain_groups,
)


def test_mask_prevents_baseball_draws_without_changing_soccer():
    x = torch.zeros((3, 3))
    z = masked_logits(x, torch.tensor([0, 1, 1]))
    p = torch.softmax(z, dim=1).numpy()
    assert p[0, 1] > 0
    assert np.all(p[1:, 1] == 0)
    np.testing.assert_allclose(p.sum(1), 1)


def test_plastic_learning_preserves_sign_and_anatomical_support():
    torch.manual_seed(3)
    w = np.array([[2, 0, 4], [0, -3, 2]], np.float32)
    model = PlasticSurrogate(w, 4)
    before = model.gains().detach().numpy().copy()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.05)
    x, kc = torch.randn(24, 4), torch.randn(24, 3)
    sport = torch.zeros(24, dtype=torch.long)
    loss = torch.nn.functional.cross_entropy(model(x, kc, sport), (kc[:, 0] > 0).long())
    loss.backward()
    optimizer.step()
    after = model.gains().detach().numpy()
    assert np.any(before[w != 0] != after[w != 0])
    assert np.all(after[w == 0] == 1)
    assert np.all(after > 0)
    np.testing.assert_array_equal(np.sign(w * after), np.sign(w))


def test_real_readout_training_learns_and_prediction_roundtrip(tmp_path):
    rng = np.random.default_rng(2)
    x = rng.normal(size=(180, 6)).astype(np.float32)
    y = np.where(x[:, 0] > 0, 0, 2)
    sport = np.ones(180, dtype=np.int64)
    result = fit_readout(x[:120], y[:120], sport[:120], x[120:], y[120:], sport[120:], epochs=90)
    p = probabilities(x[120:], sport[120:], result['weight'], result['bias'])
    assert (p.argmax(1) == y[120:]).mean() > 0.85
    assert np.all(p[:, 1] == 0)
    np.savez(tmp_path / 'head.npz', weight=result['weight'], bias=result['bias'])
    ck = np.load(tmp_path / 'head.npz')
    np.testing.assert_array_equal(p, probabilities(x[120:], sport[120:], ck['weight'], ck['bias']))
    assert len(result['curve']) == 90


def test_metrics_count_all_samples_and_keep_probabilities_honest():
    p = np.array([[.5, .3, .2], [.4, 0, .6]])
    m = metrics(np.array([0, 2]), p)
    assert m['n'] == 2 and m['accuracy'] == 1
    assert m['log_loss'] > 0 and m['brier'] > 0


def test_gain_groups_reindex_by_graph_body_id_and_keep_broad_source_labels():
    import pandas as pd
    nodes = pd.DataFrame({'bodyId': [40, 10, 50, 20, 30],
                          'type': ['MBON-b', 'KC', 'MBON-a', 'KCg', 'KC']})
    anatomy = np.array([[1, 0, -2], [3, 4, 5]], np.float32)
    expected, keys = build_gain_groups(nodes, [0, 1, 2], [3, 4], anatomy)
    assert keys == [('KC', 'MBON-a'), ('KC', 'MBON-b'), ('KCg', 'MBON-a')]
    assert expected[0, 1] == -1
    assert expected[0, 0] == expected[0, 2]
    for seed in (1, 5, 42):
        actual, actual_keys = build_gain_groups(nodes.sample(frac=1, random_state=seed),
                                                [0, 1, 2], [3, 4], anatomy)
        np.testing.assert_array_equal(actual, expected)
        assert actual_keys == keys
    custom, custom_keys = build_gain_groups(nodes, [1, 3, 4], [0, 2], anatomy,
                                            graph_ids=[40, 10, 50, 20, 30])
    np.testing.assert_array_equal(custom, expected)
    assert custom_keys == keys


def test_grouped_and_independent_gains_have_only_actual_bounded_parameters():
    anatomy = np.array([[2, 0, 4], [0, -3, 2]], np.float32)
    shared = np.array([[0, -1, 0], [-1, 1, 1]])
    for groups, count in ((shared, 2), (independent_gain_groups(anatomy), 4)):
        model = GroupedPlasticSurrogate(anatomy, groups, 4)
        assert model.theta.shape == (count,)
        assert sum(p.numel() for name, p in model.named_parameters() if not name.startswith('head.')) == count
        with torch.no_grad():
            model.theta.copy_(torch.linspace(-1e6, 1e6, count))
        gains = model.gains().detach().numpy()
        assert np.isfinite(gains).all()
        assert gains.min() >= np.exp(-.3) - 1e-7 and gains.max() <= np.exp(.3) + 1e-7
        assert np.all(gains[anatomy == 0] == 1)
        np.testing.assert_array_equal(np.sign(anatomy * gains), np.sign(anatomy))
        for group in range(count):
            assert len(np.unique(gains[groups == group])) == 1


def test_temporal_surrogate_inserts_window_specific_delta_and_flattens_window_first():
    anatomy = np.array([[2, 0], [-1, 3]], np.float32)
    groups = np.array([[0, -1], [1, 0]])
    for windows in (1, 4):
        model = GroupedPlasticSurrogate(anatomy, groups, 3, windows=windows)
        with torch.no_grad():
            model.theta.copy_(torch.tensor([.4, -.2]))
        activity = torch.arange(2 * windows * 3, dtype=torch.float32).reshape(2, windows, 3)
        kc = torch.arange(2 * windows * 2, dtype=torch.float32).reshape(2, windows, 2) / 4
        expected = activity.clone()
        for window in range(windows):
            expected[:, window, :2] += kc[:, window] @ (
                model.anatomy * (model.gains() - 1) / model.normalizer).T
        torch.testing.assert_close(model.adjusted_activity(activity, kc), expected.flatten(1))
        torch.testing.assert_close(model.adjusted_activity(activity, kc).reshape(2, windows, 3)[:, :, 2],
                                   activity[:, :, 2])
        loss = model(activity, kc, torch.tensor([0, 1])).sum()
        loss.backward()
        assert model.theta.grad is not None and torch.any(model.theta.grad != 0)


def test_surrogate_scaling_is_training_only_per_window_and_whole_kc_precedes_log():
    raw = np.arange(8 * 4 * 3, dtype=np.float32).reshape(8, 4, 3)
    kc = raw[:, :, :2] ** 2
    first = fit_surrogate_inputs(raw[:6], kc[:6], raw[6:], kc[6:])
    extreme = fit_surrogate_inputs(raw[:6], kc[:6], raw[6:] * 1000, kc[6:] * 1000)
    for key in ('activity_train', 'kc_train', 'activity_mean', 'activity_std', 'kc_mean', 'kc_std'):
        np.testing.assert_array_equal(first[key], extreme[key])
    np.testing.assert_allclose(first['kc_mean'], np.log1p(kc[:6]).mean(0))
    whole = fit_surrogate_inputs(raw[:6].mean(1), kc[:6].mean(1), raw[6:].mean(1), kc[6:].mean(1))
    np.testing.assert_allclose(whole['kc_mean'][0], np.log1p(kc[:6].mean(1)).mean(0))
    assert not np.allclose(whole['kc_mean'][0], first['kc_mean'].mean(0))


def test_surrogate_fixed_checkpoints_are_reproducible_and_never_validation_selected():
    rng = np.random.default_rng(21)
    anatomy = np.array([[2, 0, 4], [0, -3, 2]], np.float32)
    groups = np.array([[0, -1, 0], [-1, 1, 1]])
    for windows in (1, 4):
        x = rng.normal(size=(40, windows, 4)).astype(np.float32)
        kc = rng.normal(size=(40, windows, 3)).astype(np.float32)
        y, sports = np.where(kc[:, 0, 0] > 0, 0, 2), np.arange(40) % 2
        args = (anatomy, groups, x[:30], kc[:30], y[:30], sports[:30], x[30:], kc[30:])
        result = fit_grouped_plasticity(*args, y[30:], sports[30:], seed=9)
        changed_validation = fit_grouped_plasticity(*args, 2 - y[30:], sports[30:], seed=9)
        assert list(result['checkpoints']) == [4, 16]
        assert len(result['curve']) == 16 and result['parameter_count'] == 2
        assert result['checkpoints'][4]['changed_synapses'] > 0
        for epoch in (4, 16):
            np.testing.assert_array_equal(result['checkpoints'][epoch]['gains'],
                                          changed_validation['checkpoints'][epoch]['gains'])
            assert np.isfinite(result['checkpoints'][epoch]['validation_loss'])
        np.testing.assert_array_equal(result['gains'], result['checkpoints'][16]['gains'])
        assert not np.array_equal(result['checkpoints'][4]['gains'], result['gains'])


def test_decoder_parameter_accounting_matches_masked_sport_heads():
    from bet36fly.learning import SportReadout
    for dimension, allocated, active in [(124, 750, 625), (496, 2982, 2485)]:
        model = SportReadout(dimension)
        assert sum(p.numel() for p in model.parameters()) == allocated
        assert allocated - (dimension + 1) == active
