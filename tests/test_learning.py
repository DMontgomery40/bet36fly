import numpy as np
import torch

from bet36fly.learning import PlasticSurrogate, masked_logits, fit_readout, probabilities, metrics


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
