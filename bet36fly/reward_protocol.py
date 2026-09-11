"""Frozen inputs and explicitly engineered interfaces for circuit reward learning."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path

import numpy as np

# Engineered task-to-compartment mapping. 'away' moved from PAM11/MBON07 (alpha1) to
# PAM12/MBON09 (gamma3) on 2026-09-11: with labeled-line ALPN drive the alpha1 output
# receives a quarter of the KC contacts per cell that MBON11 does and stays near 0 Hz at
# every non-runaway drive, whereas MBON09 responds at rates comparable to MBON11.
COMPARTMENTS = (('home', 'PPL101', 'MBON11'), ('away', 'PAM12', 'MBON09'))


def file_hash(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def select_rows(arrays, games, *, train_n, validation_n, calibration_n):
    """Freeze a chronological MLB slice with conservative label availability."""
    x, y, sport, train, validation = [np.asarray(arrays[k]) for k in
                                     ('X', 'y', 'sport', 'train', 'validation')]
    n = len(games)
    if (any(not isinstance(v, int) or isinstance(v, bool) or v < 1 for v in
            (train_n, validation_n, calibration_n)) or calibration_n > train_n
            or x.ndim != 2 or not x.shape[1] or len(x) != n or not np.isfinite(x).all()
            or any(a.shape != (n,) for a in (y, sport, train, validation))
            or train.dtype != bool or validation.dtype != bool
            or np.any(train & validation) or not np.isin(y, [0, 1, 2]).all()
            or not np.isin(sport, [0, 1]).all() or np.any((sport == 1) & (y == 1))):
        raise ValueError('Invalid frozen sports arrays or requested sample sizes.')
    dates = [datetime.fromisoformat(g['start_time'].replace('Z', '+00:00')) for g in games]
    if (len({g['id'] for g in games}) != n or any(d.tzinfo is None for d in dates)
            or any(a > b for a, b in zip(dates, dates[1:]))
            or any(g['outcome'] != int(label) for g, label in zip(games, y))
            or any(g['sport'] != ('baseball' if s == 1 else 'soccer')
                   for g, s in zip(games, sport))):
        raise ValueError('Frozen game identities, outcomes, sports or chronology do not match arrays.')
    vi = np.flatnonzero(validation & (sport == 1))[:validation_n]
    if len(vi) != validation_n:
        raise ValueError('Insufficient frozen MLB validation rows.')
    boundary = dates[int(vi[0])].astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    candidates = np.flatnonzero(train & (sport == 1))
    available = np.array([i for i in candidates if dates[int(i)] + timedelta(hours=48) <= boundary], int)
    ti = available[-train_n:]
    if len(ti) != train_n:
        raise ValueError('Insufficient MLB training labels available before validation.')
    if dates[int(ti[-1])] >= dates[int(vi[0])]:
        raise ValueError('Training must precede validation.')
    ci = ti[np.linspace(0, len(ti) - 1, calibration_n, dtype=int)]
    return dict(train_indices=ti, validation_indices=vi, calibration_indices=ci,
                input_mean=x[ti].mean(0), input_std=x[ti].std(0).clip(.01),
                embargoed=len(candidates) - len(available), boundary=boundary.isoformat())


def fit_fixed_readout(responses, labels):
    """Calibrate scale/prior only; no response-to-outcome coefficient is fitted."""
    r, labels = np.asarray(responses, float), np.asarray(labels)
    if (r.ndim != 2 or r.shape[1] != 2 or len(r) < 1 or not np.isfinite(r).all()
            or np.any(r < 0) or labels.ndim != 1 or not len(labels)
            or not np.isin(labels, [0, 2]).all()):
        raise ValueError('Readout calibration needs finite nonnegative two-population rates and MLB labels.')
    z = np.log1p(r)
    prior = (np.array([(labels == 0).sum(), (labels == 2).sum()]) + 1) / (len(labels) + 2)
    return dict(method='negative-standardized-log1p-MBON-rate-plus-smoothed-training-prior',
                mean=z.mean(0).tolist(), scale=z.std(0).clip(.05).tolist(), prior=prior.tolist())


def decode(responses, fixed):
    r = np.asarray(responses, float)
    mean, scale, prior = [np.asarray(fixed[k], float) for k in ('mean', 'scale', 'prior')]
    if (r.shape != (2,) or not np.isfinite(r).all() or np.any(r < 0)
            or any(a.shape != (2,) or not np.isfinite(a).all() for a in (mean, scale, prior))
            or np.any(scale <= 0) or np.any(prior <= 0) or not np.isclose(prior.sum(), 1)):
        raise ValueError('Invalid activity or frozen readout calibration.')
    logits = np.log(prior) - np.clip((np.log1p(r) - mean) / scale, -4, 4)
    probs = np.exp(logits - logits.max())
    probs /= probs.sum()
    return np.array([probs[0], 0., probs[1]])


def plastic_mapping(ptr, post, kc, outputs):
    """Map selected existing CSR edges to KC index and declared output population."""
    n = len(ptr) - 1
    lookup = np.full(n, -1, dtype=np.int32)
    if len(np.unique(kc)) != len(kc):
        raise ValueError('Duplicate KC identity.')
    for c, indices in enumerate(outputs):
        if (not len(indices) or np.any(indices < 0) or np.any(indices >= n)
                or np.any(lookup[indices] != -1) or len(np.unique(indices)) != len(indices)):
            raise ValueError('Output populations must be nonempty, distinct graph neurons.')
        lookup[indices] = c
    edges, cells, groups = [], [], []
    for k, pre in enumerate(kc):
        lo, hi = ptr[pre:pre + 2]
        chosen = np.flatnonzero(lookup[post[lo:hi]] >= 0)
        edges.extend((lo + chosen).tolist())
        cells.extend([k] * len(chosen))
        groups.extend(lookup[post[lo + chosen]].tolist())
    if not edges or set(groups) != set(range(len(outputs))):
        raise ValueError('Every declared compartment needs existing KC-to-MBON edges.')
    return np.asarray(edges, np.int64), np.asarray(cells, np.int32), np.asarray(groups, np.int32)


def make_circuit(root, protocol, *, n_features=16):
    """Construct a separate full graph with an explicit modulation-only proxy and identity encoder."""
    import pyarrow.feather as feather
    from .reward_brain import RewardEngine
    from .reward_encoder import glomerular_map, glomerular_rates, scale_inputs_onto, scale_outputs_from

    root = Path(root)
    path = root / 'data/brain'
    names = ('ids', 'indptr', 'post', 'counts', 'signs', 'sensory', 'kc', 'mbon')
    arrays = {name: np.load(path / f'{name}.npy', allow_pickle=False) for name in names}
    ids, ptr, post, contacts, signs = [arrays[k] for k in ('ids', 'indptr', 'post', 'counts', 'signs')]
    nodes = feather.read_table(path / 'nodes.feather').to_pandas()
    raw_path = root / 'data/raw/annotations.feather'
    raw = feather.read_table(raw_path, columns=['bodyId', 'type', 'instance', 'class']).to_pandas()
    if nodes.bodyId.duplicated().any() or raw.bodyId.duplicated().any():
        raise ValueError('Duplicate anatomical annotation identities.')
    nodes = nodes.set_index('bodyId').reindex(ids)
    raw = raw.set_index('bodyId').reindex(ids)
    if nodes.superclass.isna().any():
        raise ValueError('Graph IDs missing retained annotation rows.')
    weights = np.asarray(contacts * np.repeat(signs.astype(np.float32), np.diff(ptr)) *
                         np.float32(.275 * protocol['global_weight_scale']), dtype=np.float32)
    dopamine_only = np.flatnonzero(nodes.transmitter.eq('dopamine').to_numpy())
    for pre in dopamine_only:
        weights[ptr[pre]:ptr[pre + 1]] = 0
    # Cell-type input gain onto Kenyon cells: an engineered stand-in for the high
    # coincidence threshold of real KCs, applied to every synapse ending at a KC.
    weights = scale_inputs_onto(weights, ptr, post, arrays['kc'], protocol['kc_input_gain'])
    # The ALPN ports are driven by the scheduled input. Their recurrent antennal-lobe
    # inputs are scaled separately; at 0 they are labeled lines, which stops the
    # all-excitatory lobe (as signed here) from re-exciting itself indefinitely.
    weights = scale_inputs_onto(weights, ptr, post, arrays['sensory'], protocol['sensory_input_gain'])
    # APL is a non-spiking, graded GABAergic feedback neuron in real flies; a spiking
    # LIF proxy at full contact strength delivers tens of mV per spike onto MBONs.
    apl = np.flatnonzero(nodes['type'].eq('APL').to_numpy() & nodes.transmitter.eq('gaba').to_numpy())
    if len(apl) != 2:
        raise ValueError('Expected exactly two annotated GABAergic APL neurons.')
    weights = scale_outputs_from(weights, ptr, apl, protocol['apl_output_gain'])
    is_kc = np.zeros(len(ids), bool)
    is_kc[arrays['kc']] = True
    port_kc_contacts = np.array([contacts[ptr[i]:ptr[i + 1]][is_kc[post[ptr[i]:ptr[i + 1]]]].sum()
                                 for i in arrays['sensory']], np.float64)
    ports = nodes.iloc[arrays['sensory']]
    mapping = glomerular_map(ports['type'].fillna('').to_numpy(), ports.transmitter.fillna('').to_numpy(),
                             port_kc_contacts, n_features=int(n_features),
                             min_kc_contacts=protocol['encoder_min_kc_contacts'])

    def encode(features):
        return glomerular_rates(features, mapping, peak_hz=protocol['encoder_peak_hz'],
                                width=protocol['encoder_tuning_width'])
    outputs, dans, dcomp, annotations = [], [], [], []
    for c, (label, d_type, m_type) in enumerate(COMPARTMENTS):
        d = np.flatnonzero(nodes['type'].eq(d_type) & nodes['class'].eq('DAN') &
                           nodes.transmitter.eq('dopamine'))
        m = np.flatnonzero(nodes['type'].eq(m_type) & nodes['class'].eq('MBON'))
        if not len(d) or not len(m) or not np.isin(m, arrays['mbon']).all():
            raise ValueError(f'Missing confirmed target population {d_type}/{m_type}.')
        for indices, kind in ((d, d_type), (m, m_type)):
            if raw.iloc[indices]['instance'].isna().any() or not raw.iloc[indices]['type'].eq(kind).all():
                raise ValueError('Raw instance labels do not match the retained target annotations.')
        outputs.append(m)
        dans.extend(d.tolist())
        dcomp.extend([c] * len(d))
        annotations.append(dict(label=label, dan_type=d_type, mbon_type=m_type, dans=len(d), mbons=len(m),
                                dan_body_ids=ids[d].tolist(), mbon_body_ids=ids[m].tolist(),
                                dan_instances=raw.iloc[d]['instance'].tolist(),
                                mbon_instances=raw.iloc[m]['instance'].tolist()))
    edges, kcs, compartments = plastic_mapping(ptr, post, arrays['kc'], outputs)
    if not np.all(weights[edges] > 0):
        raise ValueError('The selected KC-to-MBON plastic support must be excitatory.')
    for c, annotation in enumerate(annotations):
        annotation['plastic_edges'] = int((compartments == c).sum())
    engine = RewardEngine(ptr, post, weights, arrays['sensory'], arrays['kc'], np.asarray(dans),
                          np.asarray(dcomp), edges, kcs, compartments, n_compartments=2,
                          tau_ms=protocol['tau_ms'], learning_rate=protocol['learning_rate'],
                          gain_bounds=tuple(protocol['gain_bounds']),
                          plasticity_onset_ms=protocol['plasticity_onset_ms'],
                          dan_baseline_window_ms=protocol['dan_baseline_window_ms'],
                          dan_reference=protocol.get('dan_reference', 'tonic-baseline'))
    anatomy = dict(neurons=len(ids), kc=len(arrays['kc']), dans=len(dans), plastic_edges=len(edges),
                   dan_reference=engine.dan_reference,
                   compartments=annotations, dopamine_only_fast_outputs_zeroed=len(dopamine_only),
                   kc_input_gain=protocol['kc_input_gain'], sensory_input_gain=protocol['sensory_input_gain'],
                   apl_output_gain=protocol['apl_output_gain'], apl_body_ids=ids[apl].tolist(),
                   encoder=dict(mapping['summary'], peak_hz=protocol['encoder_peak_hz'],
                                tuning_width=protocol['encoder_tuning_width']),
                   mapping='type-instance-compartment-proxy; pairwise contacts lack exact synaptic location',
                   graph_hashes={name: file_hash(path / f'{name}.npy') for name in names},
                   annotations_sha256=file_hash(raw_path))
    return engine, anatomy, outputs, np.asarray(dcomp, np.int32), arrays['kc'], arrays['sensory'], encode
