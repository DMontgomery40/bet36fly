"""Anatomical orientation/normalization contracts for the slow local branch."""

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from kc_local_anatomy import lateral_contacts


def graph():
    matrix = csr_matrix((np.array([2, 6, 5, 9, 99, 31]),
                         ([1, 4, 3, 1, 2, 4], [3, 3, 1, 1, 3, 5])), shape=(6, 6))
    return matrix.indptr, matrix.indices, matrix.data, np.array([4, 1, 3])


def test_uses_incoming_contacts_with_noncontiguous_neuron_order_and_excludes_self():
    arrays = graph()
    before = [x.copy() for x in arrays]
    adjacency, audit = lateral_contacts(*arrays)
    np.testing.assert_array_equal(adjacency.toarray(), [[0, 0, 0], [0, 0, 1], [.75, .25, 0]])
    assert audit['directed_pairs'] == 3
    assert audit['contacts'] == 13
    assert audit['excluded_self_pairs'] == 1
    assert audit['excluded_self_contacts'] == 9
    assert audit['empty_recipient_rows'] == 1
    for observed, expected in zip(arrays, before):
        np.testing.assert_array_equal(observed, expected)


@pytest.mark.parametrize('order', [[0, 1, 2], [2, 0, 1], [1, 2, 0]])
def test_joint_kc_relabeling_preserves_connectivity(order):
    ptr, post, count, kc = graph()
    original, _ = lateral_contacts(ptr, post, count, kc)
    observed, _ = lateral_contacts(ptr, post, count, kc[order])
    np.testing.assert_array_equal(observed.toarray(), original.toarray()[np.ix_(order, order)])


@pytest.mark.parametrize('factor', [1, 2, 17])
def test_uniform_contact_scaling_preserves_normalized_branch(factor):
    ptr, post, count, kc = graph()
    original, audit = lateral_contacts(ptr, post, count, kc)
    scaled, scaled_audit = lateral_contacts(ptr, post, count*factor, kc)
    np.testing.assert_array_equal(scaled.toarray(), original.toarray())
    assert scaled_audit['contacts'] == audit['contacts']*factor


@pytest.mark.parametrize('which,value', [
    (0, [0, 1, 0]), (0, [1, 2, 3]), (1, [-1, 0, 0, 0, 0, 0]),
    (1, [6, 0, 0, 0, 0, 0]), (2, [1, -1, 1, 1, 1, 1]),
    (2, [1, float('nan'), 1, 1, 1, 1]), (3, [4, 1, 1]), (3, [4, 1, 6]),
])
def test_rejects_malformed_anatomical_correspondence(which, value):
    arrays = list(graph())
    arrays[which] = np.asarray(value)
    with pytest.raises(ValueError):
        lateral_contacts(*arrays)


def test_disconnected_kcs_are_zero_rows_without_invented_neighbors():
    adjacency, audit = lateral_contacts([0, 0, 0], [], [], [1, 0])
    np.testing.assert_array_equal(adjacency.toarray(), np.zeros((2, 2)))
    assert audit['empty_recipient_rows'] == 2
    assert audit['directed_pairs'] == audit['contacts'] == 0


@pytest.mark.parametrize('dtype', [np.float32, np.float64])
def test_integral_float_contact_storage_matches_integer_contact_values(dtype):
    ptr, post, count, kc = graph()
    expected, expected_audit = lateral_contacts(ptr, post, count, kc)
    actual, actual_audit = lateral_contacts(ptr, post, count.astype(dtype), kc)
    np.testing.assert_array_equal(actual.toarray(), expected.toarray())
    assert actual_audit == expected_audit


@pytest.mark.parametrize('invalid', [.5, -1., float('inf'), float('nan'), float(2**63)])
def test_float_storage_does_not_admit_fractional_nonfinite_or_overflowed_contacts(invalid):
    ptr, post, count, kc = graph()
    count = count.astype(float)
    count[0] = invalid
    with pytest.raises(ValueError):
        lateral_contacts(ptr, post, count, kc)
