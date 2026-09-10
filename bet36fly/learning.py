"""Learning on actual spiking outputs and anatomically supported synapses.

The plasticity warm-up uses an explicit rate surrogate, not biological dopamine
or exact BPTT. Learned gains are later applied to the full LIF graph, which is
rerun before the final readout is fitted. The surrogate is never served.
"""
from __future__ import annotations

import copy

import numpy as np
import torch
from torch import nn


def masked_logits(logits, sports):
    output = logits.clone()
    output[sports == 1, 1] = -1e9
    return output


class SportReadout(nn.Module):
    def __init__(self, dimension):
        super().__init__()
        self.weight = nn.Parameter(torch.zeros(2, 3, dimension))
        self.bias = nn.Parameter(torch.zeros(2, 3))

    def forward(self, x, sports):
        output = torch.einsum('bcd,bd->bc', self.weight[sports], x) + self.bias[sports]
        return masked_logits(output, sports)


class PlasticSurrogate(nn.Module):
    def __init__(self, anatomical_weights, readout_dim):
        super().__init__()
        w = torch.as_tensor(anatomical_weights, dtype=torch.float32)
        self.register_buffer('anatomy', w)
        self.register_buffer('support', w != 0)
        self.register_buffer('normalizer', w.abs().sum(1).clamp_min(1)[:, None])
        self.log_gain = nn.Parameter(torch.zeros_like(w))
        self.head = SportReadout(readout_dim)
        # Nonzero deterministic head init lets the first gradient reach synapses.
        nn.init.normal_(self.head.weight, std=0.02)

    def gains(self):
        return torch.where(self.support, torch.exp(0.3 * torch.tanh(self.log_gain)), 1.0)

    def forward(self, activity, kc_activity, sports):
        delta = kc_activity @ (self.anatomy * (self.gains() - 1) / self.normalizer).T
        adjusted = torch.cat([activity[:, :delta.shape[1]] + delta, activity[:, delta.shape[1]:]], dim=1)
        return self.head(adjusted, sports)


def _balanced_loss(logits, y, sport):
    # Sports receive equal weight despite the much larger MLB schedule.
    pieces = [nn.functional.cross_entropy(logits[sport == s], y[sport == s])
              for s in (0, 1) if torch.any(sport == s)]
    return torch.stack(pieces).mean()


def fit_readout(x_train, y_train, sport_train, x_val, y_val, sport_val,
                *, epochs=150, seed=42, progress=None):
    torch.set_num_threads(2)
    torch.manual_seed(seed)
    model = SportReadout(x_train.shape[1])
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.025, weight_decay=0.03)
    train = [torch.as_tensor(a) for a in (x_train.astype(np.float32), y_train, sport_train)]
    val = [torch.as_tensor(a) for a in (x_val.astype(np.float32), y_val, sport_val)]
    best, best_loss, curve, selected_epoch = None, float('inf'), [], 0
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        loss = _balanced_loss(model(train[0], train[2]), train[1], train[2])
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 2)
        optimizer.step()
        model.eval()
        with torch.no_grad():
            train_loss = float(_balanced_loss(model(train[0], train[2]), train[1], train[2]))
            val_loss = float(_balanced_loss(model(val[0], val[2]), val[1], val[2]))
        curve.append({'epoch': epoch + 1, 'train_loss': train_loss, 'validation_loss': val_loss})
        if val_loss < best_loss:
            best, best_loss, selected_epoch = copy.deepcopy(model.state_dict()), val_loss, epoch + 1
        if progress and (epoch % 10 == 0 or epoch + 1 == epochs):
            progress(curve)
    model.load_state_dict(best)
    return dict(weight=model.weight.detach().numpy(), bias=model.bias.detach().numpy(),
                curve=curve, selected_epoch=selected_epoch, validation_loss=best_loss)


def fit_plasticity(anatomy, x_train, kc_train, y_train, sport_train, x_val, kc_val, y_val, sport_val,
                   *, epochs=80, seed=42, progress=None):
    torch.set_num_threads(2)
    torch.manual_seed(seed)
    model = PlasticSurrogate(anatomy, x_train.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.018)
    train = [torch.as_tensor(a) for a in (x_train, kc_train, y_train, sport_train)]
    val = [torch.as_tensor(a) for a in (x_val, kc_val, y_val, sport_val)]
    best, best_loss, curve, selected_epoch = None, float('inf'), [], 0
    generator = np.random.default_rng(seed)
    for epoch in range(epochs):
        # Each batch contains both sports when both exist, preventing majority domination.
        order = generator.permutation(len(y_train))
        for start in range(0, len(order), 256):
            ix = order[start:start + 256]
            optimizer.zero_grad()
            logits = model(train[0][ix], train[1][ix], train[3][ix])
            penalty = 0.003 * model.log_gain[model.support].square().mean()
            loss = _balanced_loss(logits, train[2][ix], train[3][ix]) + penalty
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 2)
            optimizer.step()
        with torch.no_grad():
            train_loss = float(_balanced_loss(model(train[0], train[1], train[3]), train[2], train[3]))
            val_loss = float(_balanced_loss(model(val[0], val[1], val[3]), val[2], val[3]))
        curve.append({'epoch': epoch + 1, 'train_loss': train_loss, 'validation_loss': val_loss})
        if val_loss < best_loss:
            best, best_loss, selected_epoch = copy.deepcopy(model.state_dict()), val_loss, epoch + 1
        if progress and (epoch % 5 == 0 or epoch + 1 == epochs):
            progress(curve)
    model.load_state_dict(best)
    gains = model.gains().detach().numpy()
    support = anatomy != 0
    return dict(gains=gains, curve=curve, selected_epoch=selected_epoch,
                changed_synapses=int(np.count_nonzero(np.abs(gains[support] - 1) > 1e-6)),
                min_gain=float(gains[support].min()), max_gain=float(gains[support].max()))


def probabilities(activity, sports, weight, bias):
    logits = np.einsum('bcd,bd->bc', weight[sports], activity) + bias[sports]
    logits[sports == 1, 1] = -1e9
    logits -= logits.max(axis=1, keepdims=True)
    p = np.exp(logits)
    return p / p.sum(axis=1, keepdims=True)


def metrics(y, p):
    y, p = np.asarray(y), np.asarray(p)
    if (len(y) == 0 or p.shape != (len(y), 3) or not np.isfinite(p).all()
            or np.any(p < 0) or not np.allclose(p.sum(1), 1, atol=1e-5)):
        raise ValueError('Metrics need finite normalized three-outcome probabilities and nonempty labels.')
    onehot = np.eye(3)[y]
    confidence = p.max(1)
    correct = p.argmax(1) == y
    bins, ece = [], 0.0
    for lo in np.arange(0, 1, .1):
        ix = (confidence >= lo) & (confidence < lo + .1 + (1e-9 if lo > .89 else 0))
        if ix.any():
            acc, conf = float(correct[ix].mean()), float(confidence[ix].mean())
            ece += float(ix.mean()) * abs(acc - conf)
            bins.append({'lower': round(float(lo), 1), 'n': int(ix.sum()), 'confidence': conf, 'accuracy': acc})
    return {'n': len(y), 'accuracy': float(correct.mean()),
            'log_loss': float(-np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1)).mean()),
            'brier': float(np.square(p - onehot).sum(1).mean()), 'ece': ece, 'calibration': bins}
