"""Glomerular identity coding for the reward experiment's sensory interface.

Biology: an odor is represented by WHICH antennal-lobe glomeruli respond, sister
projection neurons of one glomerulus respond alike, and each Kenyon cell fires
only when several of its few glomerular inputs coincide (Caron et al. 2013;
Turner et al. 2008). This module borrows that identity code as an explicitly
engineered interface: each standardized pregame feature owns a disjoint set of
annotated cholinergic KC-projecting ALPN types, each type is tuned to a
preferred value, and a game drives the tuned types of every feature. It is not
a claim that these glomeruli naturally represent sports quantities.
"""
from __future__ import annotations

import numpy as np

ENCODER_NAME = 'glomerular-tuning-v1'
CENTER_SPAN = 1.5
FLOOR_FRACTION = 0.05


def glomerular_map(port_types, port_transmitters, port_kc_contacts, *, n_features, min_kc_contacts):
    """Assign eligible glomeruli to features and preferred values, deterministically.

    Eligible ports are cholinergic and reach Kenyon cells with at least
    ``min_kc_contacts`` summed contacts per type. Glomeruli are sorted by type
    name; with ``k = eligible // n_features`` centers per feature, the weakest
    surplus glomeruli (fewest KC contacts) are left undriven and recorded.
    """
    types = np.asarray(port_types).astype(str)
    transmitters = np.asarray(port_transmitters).astype(str)
    contacts = np.asarray(port_kc_contacts, dtype=np.float64)
    if (types.ndim != 1 or types.shape != transmitters.shape or types.shape != contacts.shape
            or not len(types) or not np.isfinite(contacts).all() or np.any(contacts < 0)
            or not isinstance(n_features, (int, np.integer)) or isinstance(n_features, bool) or n_features < 1
            or not np.isfinite(min_kc_contacts) or min_kc_contacts < 0):
        raise ValueError('Glomerular map needs aligned port annotations and a positive feature count.')
    eligible_ports = np.flatnonzero(transmitters == 'acetylcholine')
    strength = {}
    for port in eligible_ports:
        strength[types[port]] = strength.get(types[port], 0.0) + float(contacts[port])
    glomeruli = sorted(name for name, total in strength.items() if total >= min_kc_contacts and total > 0)
    per_feature = len(glomeruli) // int(n_features)
    if per_feature < 1:
        raise ValueError('Fewer eligible glomeruli than features; the identity code cannot cover every feature.')
    keep = per_feature * int(n_features)
    by_strength = sorted(glomeruli, key=lambda name: (strength[name], name))
    dropped = sorted(by_strength[:len(glomeruli) - keep])
    kept = [name for name in glomeruli if name not in set(dropped)]
    centers = np.linspace(-CENTER_SPAN, CENTER_SPAN, per_feature) if per_feature > 1 else np.zeros(1)
    port_feature = np.full(len(types), -1, np.int32)
    port_center = np.zeros(len(types), np.float32)
    assignment = {}
    for rank, name in enumerate(kept):
        assignment[name] = (rank % int(n_features), float(centers[rank // int(n_features)]))
    for port in eligible_ports:
        if types[port] in assignment:
            port_feature[port], port_center[port] = assignment[types[port]]
    features = []
    for f in range(int(n_features)):
        rows = [dict(type=name, center=assignment[name][1], cells=int(np.count_nonzero(types[eligible_ports] == name)),
                     kc_contacts=strength[name]) for name in kept if assignment[name][0] == f]
        features.append(dict(feature=f, glomeruli=sorted(rows, key=lambda r: r['center'])))
    summary = dict(encoder=ENCODER_NAME, glomeruli=len(kept), centers_per_feature=per_feature,
                   center_span=CENTER_SPAN, floor_fraction=FLOOR_FRACTION,
                   ports_driven=int(np.count_nonzero(port_feature >= 0)), ports_total=int(len(types)),
                   eligible_transmitter='acetylcholine', min_kc_contacts=float(min_kc_contacts),
                   dropped_glomeruli=dropped, features=features)
    return dict(port_feature=port_feature, port_center=port_center, summary=summary)


def glomerular_rates(features, mapping, *, peak_hz, width):
    """Gaussian-tuned Poisson rates for every sensory port; undriven ports stay at zero."""
    z = np.asarray(features, dtype=np.float64)
    port_feature = np.asarray(mapping['port_feature'], dtype=np.int32)
    port_center = np.asarray(mapping['port_center'], dtype=np.float64)
    n_features = int(mapping['summary']['features'].__len__())
    if (z.ndim != 1 or len(z) != n_features or not np.isfinite(z).all()
            or not np.isfinite(peak_hz) or peak_hz <= 0 or not np.isfinite(width) or width <= 0
            or port_feature.shape != port_center.shape or np.any(port_feature >= n_features)):
        raise ValueError('Encoder needs one finite standardized value per feature and positive tuning parameters.')
    rates = np.zeros(len(port_feature), np.float64)
    driven = port_feature >= 0
    distance = z[port_feature[driven]] - port_center[driven]
    rates[driven] = peak_hz * np.exp(-0.5 * (distance / width) ** 2)
    rates[rates < FLOOR_FRACTION * peak_hz] = 0.0
    return np.ascontiguousarray(rates, dtype=np.float32)


def scale_inputs_onto(weights, ptr, post, targets, gain):
    """Return a copy of CSR weights with every edge ending at a target neuron scaled by ``gain`` (0 silences them)."""
    weights = np.asarray(weights, dtype=np.float32)
    ptr, post, targets = np.asarray(ptr), np.asarray(post), np.asarray(targets)
    if (not np.isfinite(gain) or gain < 0 or weights.ndim != 1 or len(post) != len(weights)
            or ptr[-1] != len(post) or np.any(targets < 0) or np.any(targets >= len(ptr) - 1)):
        raise ValueError('Input scaling needs a finite nonnegative gain and a consistent graph.')
    is_target = np.zeros(len(ptr) - 1, bool)
    is_target[targets] = True
    scaled = weights.copy()
    scaled[is_target[post]] *= np.float32(gain)
    return scaled


def scale_outputs_from(weights, ptr, sources, gain):
    """Return a copy of CSR weights with every edge leaving a source neuron scaled by ``gain`` (0 silences them)."""
    weights = np.asarray(weights, dtype=np.float32)
    ptr, sources = np.asarray(ptr), np.asarray(sources)
    if (not np.isfinite(gain) or gain < 0 or weights.ndim != 1 or ptr[-1] != len(weights)
            or np.any(sources < 0) or np.any(sources >= len(ptr) - 1)):
        raise ValueError('Output scaling needs a finite nonnegative gain and a consistent graph.')
    scaled = weights.copy()
    for pre in sources:
        scaled[ptr[pre]:ptr[pre + 1]] *= np.float32(gain)
    return scaled
