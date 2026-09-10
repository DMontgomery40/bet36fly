import numpy as np
import pytest

from bet36fly.connectome import index_edges, transmitter_signs, normalize_nodes


def test_indexing_preserves_weak_and_self_edges_and_accounts_for_missing_nodes():
    ids = np.array([2, 5, 2**54 + 1], dtype=np.int64)
    pre = np.array([2, 5, 2**54 + 1, 1, 5], dtype=np.int64)
    post = np.array([2, 2**54 + 1, 5, 2, 7], dtype=np.int64)
    i, j, w, keep = index_edges(ids, pre, post, np.array([1, 3, 2, 9, 6]))
    assert i.tolist() == [0, 1, 2]
    assert j.tolist() == [0, 2, 1]
    assert w.tolist() == [1, 3, 2]
    assert keep.tolist() == [True, True, True, False, False]


@pytest.mark.parametrize('counts', [[0], [-1], [1.2], [float('nan')]])
def test_invalid_counts_fail(counts):
    with pytest.raises(ValueError):
        index_edges(np.array([1]), np.array([1]), np.array([1]), np.array(counts))


def test_floating_neuron_ids_rejected():
    with pytest.raises(ValueError):
        index_edges(np.array([1]), np.array([1.0]), np.array([1]), np.array([1]))


def test_signs_keep_uncertain_neurons_active_and_support_combinations():
    signs, uncertain = transmitter_signs(['acetylcholine', 'gaba', 'glutamate', 'histamine',
                                         'dopamine', None, 'acetylcholine,gaba'])
    assert signs.tolist() == [1, -1, -1, -1, 1, 1, 1]
    assert uncertain.tolist() == [False, False, False, False, True, True, True]


def test_neuronal_selection_does_not_include_glia_or_unresolved_objects():
    import pandas as pd
    frame = pd.DataFrame({'bodyId': [3, 1, 2, 4], 'superclass': ['cb_intrinsic', 'cb_intrinsic', None, ''],
                          'status': ['Glia', 'Traced', 'Traced', 'Traced'], 'class': ['KC'] * 4})
    nodes = normalize_nodes(frame)
    assert nodes.bodyId.tolist() == [1]
