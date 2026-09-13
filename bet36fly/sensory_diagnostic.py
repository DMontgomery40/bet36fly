"""Explicit DPM fast-sign hypothesis; never changes the imported annotations."""
import numpy as np


def dpm_weights(nodes, ptr, weights, mode):
    if (mode not in ('zero', 'inhibitory') or not nodes.bodyId.is_unique
            or nodes.bodyId.dtype.kind not in 'iu'
            or sorted(nodes.loc[nodes.type == 'DPM', 'bodyId'].tolist()) != [11734, 12569]
            or len(ptr) != len(nodes) + 1 or ptr[0] != 0 or ptr[-1] != len(weights)
            or np.any(np.diff(ptr) < 0) or not np.isfinite(weights).all()):
        raise ValueError('DPM intervention identity or graph mismatch.')
    result = np.array(weights, dtype=np.float32, copy=True)
    for i in np.flatnonzero(nodes.type.to_numpy() == 'DPM'):
        result[ptr[i]:ptr[i+1]] = 0 if mode == 'zero' else -np.abs(weights[ptr[i]:ptr[i+1]])
    return result
