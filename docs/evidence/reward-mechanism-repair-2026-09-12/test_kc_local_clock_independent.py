"""Independent rational-clock and closed-form checks for the local KC map.

No fit, connectome history, native engine, or network is used by this suite.
The reference groups spike timestamps as rational seconds rather than using
the implementation's scheduler or source-update helper.
"""

from fractions import Fraction

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from kc_local_state_evidence_ui import KCLocalState


PARAMS = dict(tauKCdec=0.9, tauinp=0.6, tauadapt=1.7, adaptscale=0.0,
              tauinh=1.3, inhfactor=1.6, infp=0.5, slf=0.15, bline=0.0)
STATE = ('calyx', 'lobe', 'adaptation', 'inhibition', 'pending_counts')


def impulses(length, cells=3):
    result = np.zeros((length, cells), np.uint8)
    for j in range(cells):
        for t in (0, 166, 167, 333, 334, 499, 500, 666, 667, 999, 1000, 4999, 5000):
            index = t + j
            if index < length:
                result[index, j] = 1
    return result


def rational_frame_counts(events, completed):
    """Count half-open frames directly, including exact endpoint exclusion."""
    counts = np.zeros((completed, events.shape[1]), np.int64)
    pending = np.zeros(events.shape[1], np.int64)
    times = [Fraction(t, 5000) for t in range(len(events))]
    for frame in range(completed):
        left, right = Fraction(frame, 30), Fraction(frame+1, 30)
        selected = [i for i, time in enumerate(times) if left <= time < right]
        if selected:
            counts[frame] = events[selected].sum(0)
    selected = [i for i, time in enumerate(times) if time >= Fraction(completed, 30)]
    if selected:
        pending = events[selected].sum(0)
    return counts, pending


@pytest.mark.parametrize('length', [1, 166, 167, 168, 334, 335, 500, 501, 1000, 1001, 5000, 5001])
@pytest.mark.parametrize('finish_boundary', [False, True])
def test_exact_frame_partition_and_closed_form_calcium(length, finish_boundary):
    events = impulses(length)
    model = KCLocalState(PARAMS, csr_matrix((3, 3)))
    observed = model.consume_chunk(events)
    if finish_boundary:
        model.advance_boundary()
    stamp = Fraction(length if finish_boundary else length-1, 5000)
    completed = int(stamp / Fraction(1, 30))
    counts, pending = rational_frame_counts(events, completed)
    rho = 1 - (1/30)/PARAMS['tauKCdec']
    expected = np.zeros(3)
    if completed:
        powers = np.arange(completed-1, -1, -1)
        expected = ((rho**powers)[:, None] * counts).sum(0) / (30*PARAMS['tauinp'])
    np.testing.assert_allclose(model.calyx, expected, rtol=2e-14, atol=2e-16)
    np.testing.assert_array_equal(model.lobe, model.calyx)
    np.testing.assert_array_equal(model.pending_counts, pending)
    np.testing.assert_array_equal(observed, events)
    assert model.native_step == length
    assert model.source_frames == completed


@pytest.mark.parametrize('breaks', [[1, 166, 167, 500, 1000], [167, 334, 500, 667], [1, 2, 3, 4, 5]])
def test_chunk_boundaries_cannot_change_local_state_or_weighted_events(breaks):
    events = impulses(1700)
    matrix = csr_matrix([[0, 0.25, 0.75], [1, 0, 0], [0.4, 0.6, 0]])
    params = dict(PARAMS, adaptscale=0.7)
    whole, chunked = [KCLocalState(params, matrix) for _ in range(2)]
    reference = whole.consume_chunk(events)
    pieces = []
    start = 0
    for stop in [*breaks, len(events)]:
        pieces.append(chunked.consume_chunk(events[start:stop]))
        chunked.consume_chunk(events[:0])
        start = stop
    np.testing.assert_array_equal(np.concatenate(pieces), reference)
    assert whole.native_step == chunked.native_step
    assert whole.source_frames == chunked.source_frames
    for name in STATE:
        np.testing.assert_array_equal(getattr(whole, name), getattr(chunked, name))
    assert np.any((reference > 0) & (reference < events))


def test_explicit_boundary_flush_is_idempotent_and_does_not_invent_a_spike():
    model = KCLocalState(PARAMS, csr_matrix((3, 3)))
    events = impulses(500)
    model.consume_chunk(events)
    assert model.source_frames == 2
    model.advance_boundary()
    assert model.source_frames == 3
    snapshot = {name: getattr(model, name).copy() for name in STATE}
    for _ in range(3):
        model.advance_boundary()
        assert model.consume_chunk(events[:0]).shape == (0, 3)
    assert model.native_step == 500
    assert model.source_frames == 3
    for name in STATE:
        np.testing.assert_array_equal(getattr(model, name), snapshot[name])
    model.consume(np.ones(3, np.uint8))
    np.testing.assert_array_equal(model.pending_counts, [1, 1, 1])


def test_joint_cell_permutation_changes_neither_timing_nor_recipient_effect():
    matrix = np.array([[0, 0.25, 0.75], [1, 0, 0], [0.4, 0.6, 0]])
    order = np.array([2, 0, 1])
    events = impulses(2000)
    original = KCLocalState(PARAMS, csr_matrix(matrix))
    permuted = KCLocalState(PARAMS, csr_matrix(matrix[np.ix_(order, order)]))
    expected = original.consume_chunk(events)[:, order]
    actual = permuted.consume_chunk(events[:, order])
    np.testing.assert_allclose(actual, expected, rtol=2e-14, atol=2e-16)
    for name in STATE:
        np.testing.assert_allclose(getattr(permuted, name), getattr(original, name)[order],
                                   rtol=2e-14, atol=2e-16)


@pytest.mark.parametrize('bad', [[-1, 0, 0], [2, 0, 0], [float('nan'), 0, 0], [1, 0], [[1, 0, 0]]])
def test_invalid_event_does_not_advance_clock_or_partially_publish_state(bad):
    model = KCLocalState(PARAMS, csr_matrix((3, 3)))
    model.consume_chunk(impulses(167))
    snapshot = {name: getattr(model, name).copy() for name in STATE}
    with pytest.raises((ValueError, TypeError)):
        model.consume(np.asarray(bad))
    assert model.native_step == 167
    assert model.source_frames == 0
    for name in STATE:
        np.testing.assert_array_equal(getattr(model, name), snapshot[name])
