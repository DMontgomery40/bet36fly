"""Declared source-class transmission lesions for recurrent-activity diagnosis."""
import numpy as np


def lesion_weights(nodes, ptr, weights, mode):
    if (mode not in ('modulator', 'ALLN', 'union') or len(ptr) != len(nodes)+1
            or ptr[0] != 0 or ptr[-1] != len(weights) or np.any(np.diff(ptr) < 0)
            or not np.isfinite(weights).all()):
        raise ValueError('Invalid class lesion or graph.')
    modulators = {'dopamine', 'serotonin', 'octopamine'}
    pure = np.array([bool(tokens := {x.strip().lower() for x in str(value).split(',')})
                     and tokens <= modulators for value in nodes.transmitter])
    al = nodes['class'].eq('ALLN').to_numpy()
    mask = pure if mode == 'modulator' else al if mode == 'ALLN' else pure | al
    result = np.array(weights, np.float32, copy=True)
    for i in np.flatnonzero(mask):
        result[ptr[i]:ptr[i+1]] = 0
    return result, mask
