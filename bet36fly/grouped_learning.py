"""Shared or edge-independent v2 gain fitting; v1 learning stays unchanged."""
from __future__ import annotations

import numpy as np
import torch
from torch import nn

from .learning import SportReadout, _balanced_loss


def build_gain_groups(nodes, kc, mbon, anatomy, *, graph_ids=None):
    """Derive stable exact type pairs after aligning annotations by body ID.

    Prepared graphs order IDs increasingly. Explicit graph_ids also supports
    graph fixtures with another order. Broad source labels such as KC and KCg
    are retained verbatim; missing selected annotations are errors.
    """
    if nodes.bodyId.duplicated().any():
        raise ValueError('Duplicate annotation body IDs.')
    ids = np.sort(nodes.bodyId.to_numpy()) if graph_ids is None else np.asarray(graph_ids)
    aligned = nodes.set_index('bodyId').reindex(ids)
    kc, mbon = np.asarray(kc), np.asarray(mbon)
    anatomy = np.asarray(anatomy)
    if anatomy.shape != (len(mbon), len(kc)):
        raise ValueError('Anatomy dimensions must match KC and MBON populations.')
    labels = aligned['type']
    selected = labels.iloc[np.concatenate([kc, mbon])]
    if selected.isna().any() or selected.astype(str).str.strip().eq('').any():
        raise ValueError('Every KC and MBON needs an exact source type label.')
    kc_types = labels.iloc[kc].astype(str).to_numpy()
    mbon_types = labels.iloc[mbon].astype(str).to_numpy()
    rows, columns = np.nonzero(anatomy)
    pairs = list(zip(kc_types[columns], mbon_types[rows]))
    keys = sorted(set(pairs))
    lookup = {key: index for index, key in enumerate(keys)}
    group_ids = np.full(anatomy.shape, -1, np.int32)
    group_ids[rows, columns] = [lookup[key] for key in pairs]
    return group_ids, keys


def independent_gain_groups(anatomy):
    """One actual parameter per supported edge, in stable row-major order."""
    support = np.asarray(anatomy) != 0
    group_ids = np.full(support.shape, -1, np.int32)
    group_ids[support] = np.arange(np.count_nonzero(support), dtype=np.int32)
    return group_ids


def _windows(values):
    values = np.asarray(values, dtype=np.float32)
    if values.ndim == 2:
        values = values[:, None, :]
    if values.ndim != 3 or values.shape[1] not in (1, 4) or not np.isfinite(values).all():
        raise ValueError('Expected finite activity with one or four windows.')
    return values


def fit_surrogate_inputs(train_activity, train_kc, val_activity, val_kc):
    """Apply v1 log1p/standardization, fitted on training per window/channel.

    Supply whole-trial raw KC rates (the mean of the four raw rate windows)
    for the whole-trial model. Averaging transformed KC rates is not equivalent.
    """
    outputs = {}
    for name, training, validation in [('activity', train_activity, val_activity),
                                       ('kc', train_kc, val_kc)]:
        training, validation = _windows(training), _windows(validation)
        if (not len(training) or training.shape[1:] != validation.shape[1:]
                or np.any(training < 0) or np.any(validation < 0)):
            raise ValueError('Scaling requires nonnegative aligned rate windows and training rows.')
        training, validation = np.log1p(training), np.log1p(validation)
        mean = training.mean(0).astype(np.float32)
        std = np.maximum(training.std(0), .01).astype(np.float32)
        outputs[name + '_mean'], outputs[name + '_std'] = mean, std
        outputs[name + '_train'] = np.clip((training - mean) / std, -8, 8).astype(np.float32)
        outputs[name + '_val'] = np.clip((validation - mean) / std, -8, 8).astype(np.float32)
    if outputs['activity_train'].shape[:2] != outputs['kc_train'].shape[:2]:
        raise ValueError('Activity and KC rows/windows must align.')
    return outputs


class GroupedPlasticSurrogate(nn.Module):
    def __init__(self, anatomical_weights, group_ids, readout_dim, *, windows=1, gain_log_bound=.3):
        super().__init__()
        anatomy = torch.as_tensor(anatomical_weights, dtype=torch.float32)
        groups = torch.as_tensor(group_ids, dtype=torch.long)
        if (anatomy.ndim != 2 or anatomy.shape != groups.shape or not torch.isfinite(anatomy).all()
                or not torch.equal(groups >= 0, anatomy != 0) or windows not in (1, 4)
                or readout_dim < anatomy.shape[0] or not np.isfinite(gain_log_bound) or gain_log_bound <= 0):
            raise ValueError('Invalid gain support, readout dimension, windows or gain bound.')
        supported = groups[groups >= 0]
        count = int(supported.max()) + 1 if supported.numel() else 0
        if not torch.equal(torch.unique(supported), torch.arange(count)):
            raise ValueError('Supported gain IDs must be contiguous and start at zero.')
        self.register_buffer('anatomy', anatomy)
        self.register_buffer('group_ids', groups)
        self.register_buffer('support', anatomy != 0)
        self.register_buffer('normalizer', anatomy.abs().sum(1).clamp_min(1)[:, None])
        self.theta = nn.Parameter(torch.zeros(count))
        self.windows, self.readout_dim, self.gain_log_bound = windows, readout_dim, gain_log_bound
        self.head = SportReadout(windows * readout_dim)
        nn.init.normal_(self.head.weight, std=.02)

    def gains(self):
        expanded = torch.ones_like(self.anatomy)
        if self.theta.numel():
            expanded[self.support] = torch.exp(
                self.gain_log_bound * torch.tanh(self.theta[self.group_ids[self.support]]))
        return expanded

    def adjusted_activity(self, activity, kc_activity):
        if activity.ndim == 2:
            activity = activity[:, None, :]
        if kc_activity.ndim == 2:
            kc_activity = kc_activity[:, None, :]
        if (activity.ndim != 3 or kc_activity.ndim != 3
                or activity.shape[1:] != (self.windows, self.readout_dim)
                or kc_activity.shape != (len(activity), self.windows, self.anatomy.shape[1])):
            raise ValueError('Activity must match configured window-first dimensions.')
        delta = kc_activity @ (self.anatomy * (self.gains() - 1) / self.normalizer).T
        mbon = self.anatomy.shape[0]
        adjusted = torch.cat([activity[:, :, :mbon] + delta, activity[:, :, mbon:]], dim=2)
        return adjusted.flatten(start_dim=1)

    def forward(self, activity, kc_activity, sports):
        return self.head(self.adjusted_activity(activity, kc_activity), sports)


def fit_grouped_plasticity(anatomy, group_ids, x_train, kc_train, y_train, sport_train,
                          x_val, kc_val, y_val, sport_val, *, epochs=16, checkpoints=(4, 16),
                          seed=42, head_seed=None, minibatch_seed=None, lr=.018, gain_penalty=.003,
                          gain_log_bound=.3, gradient_clip=2., progress=None):
    """Return fixed epoch snapshots; full simulator validation selects among them.

    Inputs are already transformed using training-only statistics. Surrogate
    validation losses are diagnostic and never choose or restore a snapshot.
    """
    x_train, kc_train, x_val, kc_val = map(_windows, (x_train, kc_train, x_val, kc_val))
    checkpoints = tuple(sorted(set(int(epoch) for epoch in checkpoints)))
    if not checkpoints or checkpoints[0] < 1 or checkpoints[-1] > epochs or epochs < 1:
        raise ValueError('Checkpoints must be positive and within the training epochs.')
    if (not len(x_train) or not len(x_val) or x_train.shape[1:] != x_val.shape[1:]
            or kc_train.shape[1:] != kc_val.shape[1:]):
        raise ValueError('Training and validation require aligned nonempty arrays.')
    torch.set_num_threads(2)
    head_seed = seed if head_seed is None else head_seed
    minibatch_seed = seed if minibatch_seed is None else minibatch_seed
    torch.manual_seed(head_seed)
    model = GroupedPlasticSurrogate(anatomy, group_ids, x_train.shape[2],
                                    windows=x_train.shape[1], gain_log_bound=gain_log_bound)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    train = [torch.as_tensor(a, dtype=torch.float32 if i < 2 else torch.long)
             for i, a in enumerate((x_train, kc_train, y_train, sport_train))]
    val = [torch.as_tensor(a, dtype=torch.float32 if i < 2 else torch.long)
           for i, a in enumerate((x_val, kc_val, y_val, sport_val))]
    for dataset in (train, val):
        if (any(len(value) != len(dataset[0]) for value in dataset)
                or dataset[2].ndim != 1 or dataset[3].ndim != 1
                or torch.any((dataset[2] < 0) | (dataset[2] > 2))
                or torch.any((dataset[3] < 0) | (dataset[3] > 1))
                or torch.any((dataset[3] == 1) & (dataset[2] == 1))):
            raise ValueError('Rows, legal outcome labels and sports must align.')
    generator = np.random.default_rng(minibatch_seed)
    curve, snapshots = [], {}
    support = np.asarray(anatomy) != 0
    for epoch in range(1, epochs + 1):
        order = generator.permutation(len(y_train))
        model.train()
        for start in range(0, len(order), 256):
            index = order[start:start + 256]
            optimizer.zero_grad()
            penalty = gain_penalty * model.theta.square().mean() if model.theta.numel() else 0
            loss = _balanced_loss(model(train[0][index], train[1][index], train[3][index]),
                                  train[2][index], train[3][index]) + penalty
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), gradient_clip)
            optimizer.step()
        model.eval()
        with torch.no_grad():
            scores = {'epoch': epoch,
                      'train_loss': float(_balanced_loss(model(train[0], train[1], train[3]),
                                                         train[2], train[3])),
                      'validation_loss': float(_balanced_loss(model(val[0], val[1], val[3]),
                                                              val[2], val[3]))}
            if not all(np.isfinite(scores[key]) for key in ('train_loss', 'validation_loss')):
                raise RuntimeError('Nonfinite surrogate loss.')
            curve.append(scores)
            if epoch in checkpoints:
                gains = model.gains().detach().numpy().copy()
                snapshots[epoch] = dict(scores, gains=gains, theta=model.theta.detach().numpy().copy(),
                    weight=model.head.weight.detach().numpy().copy(),
                    bias=model.head.bias.detach().numpy().copy(),
                    changed_synapses=int(np.count_nonzero(np.abs(gains[support] - 1) > 1e-6)),
                    min_gain=float(gains[support].min()) if support.any() else 1.,
                    max_gain=float(gains[support].max()) if support.any() else 1.)
        if progress:
            progress(curve)
    return dict(checkpoints=snapshots, curve=curve, gains=model.gains().detach().numpy().copy(),
                parameter_count=model.theta.numel(),
                seeds={'head': int(head_seed), 'minibatch': int(minibatch_seed), 'stimulus': int(seed)})
