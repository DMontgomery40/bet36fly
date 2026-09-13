"""Synthetic local-state -> weighted-bridge composition; no fit or native calls."""

import math

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from kc_local_state_evidence_ui import KCLocalState
from kc_weighted_bridge_replay import replay

# Synthetic, admissible values already used in the standalone writer suite.
# They are mathematical probes, not candidate fitted parameters.
PARAMS = dict(
    tauKCdec=1.2,
    tauinp=0.8,
    tauadapt=2.0,
    adaptscale=0.3,
    tauinh=0.7,
    inhfactor=0.9,
    infp=0.4,
    slf=0.2,
    bline=0.0,
)
STATE = ("calyx", "lobe", "adaptation", "inhibition", "pending_counts", "susceptibility")


def fixture(n):
    matrix = np.zeros((n, n))
    matrix[0, 1], matrix[0, -1], matrix[1, 0] = 0.25, 0.75, 1
    for post in range(2, n - 1):
        matrix[post, post + 1] = 1
    events = np.zeros((2000, n), np.uint8)
    boundaries = (0, 166, 167, 333, 334, 499, 500, 666, 667, 999, 1000, 1499, 1500, 1666, 1667, 1999)
    for kc in range(n):
        for base in boundaries:
            if base + kc < len(events):
                events[base + kc, kc] = 1
    dan = np.zeros((len(events), 2))
    dan[[500, 600, 834, 1300, 1700], 0] = 0.5
    dan[[550, 667, 1000, 1510, 1999], 1] = 1 / 22
    pk, pc = np.repeat(np.arange(n), 2), np.tile([0, 1], n)
    groups = 4 * pc + pk % 4
    return csr_matrix(matrix), events, dan, pk, pc, groups


def run(weighted, dan, pk, pc, groups, *, learning=True, mask=None):
    return replay(
        weighted,
        dan,
        pk,
        pc,
        np.ones(len(pk), bool) if mask is None else mask,
        groups,
        initial=np.linspace(0.8, 1.2, len(pk), dtype=np.float32),
        learning=learning,
    )


def assert_identical(left, right):
    assert set(left) == set(right)
    for key in left:
        np.testing.assert_array_equal(left[key], right[key], err_msg=key)


@pytest.mark.parametrize("n", [3, 5])
def test_no_lateral_composition_exactly_reproduces_all_raw_bridge_outputs(n):
    _, events, dan, pk, pc, groups = fixture(n)
    model = KCLocalState(PARAMS, csr_matrix((n, n)))
    weighted = model.consume_chunk(events)
    model.advance_boundary()
    assert model.source_frames == 12 and model.native_step == 2000
    np.testing.assert_array_equal(weighted, events)
    np.testing.assert_array_equal(model.calyx, model.lobe)
    assert_identical(run(weighted, dan, pk, pc, groups), run(events, dan, pk, pc, groups))


@pytest.mark.parametrize("mode", ["no_dan", "no_learning"])
def test_active_local_suppression_cannot_bypass_no_dan_or_no_learning(mode):
    matrix, events, dan, pk, pc, groups = fixture(3)
    model = KCLocalState(PARAMS, matrix)
    weighted = model.consume_chunk(events)
    assert np.any((weighted > 0) & (weighted < events))
    result = run(weighted, dan * (mode != "no_dan"), pk, pc, groups, learning=mode != "no_learning")
    checkpoint = np.linspace(0.8, 1.2, len(pk), dtype=np.float32)
    np.testing.assert_array_equal(result["gains"], checkpoint)
    np.testing.assert_array_equal(result["double_gains"], checkpoint.astype(float))
    assert not result["edge_phases"].any()
    assert np.all(result["publication_counts"].sum(0) == 1501)
    assert result["endpoint_kc"].sum() > 0


def test_excluded_edges_stay_exact_while_other_composed_edges_update():
    matrix, events, dan, pk, pc, groups = fixture(5)
    weighted = KCLocalState(PARAMS, matrix).consume_chunk(events)
    mask = np.arange(len(pk)) % 3 != 0
    result = run(weighted, dan, pk, pc, groups, mask=mask)
    checkpoint = np.linspace(0.8, 1.2, len(pk), dtype=np.float32)
    np.testing.assert_array_equal(result["gains"][~mask], checkpoint[~mask])
    assert not result["edge_phases"][:, ~mask].any()
    assert not result["publication_counts"][:, ~mask].any()
    assert not result["bound_counts"][:, ~mask].any()
    assert np.any(result["gains"][mask] != checkpoint[mask])


@pytest.mark.parametrize("n", [3, 5])
def test_each_positive_and_negative_product_area_is_dominated_by_raw_events(n):
    matrix, events, dan, pk, pc, groups = fixture(n)
    weighted = KCLocalState(PARAMS, matrix).consume_chunk(events)
    assert np.all(weighted >= 0) and np.all(weighted <= events)
    assert np.any((weighted > 0) & (weighted < events))
    local, raw = run(weighted, dan, pk, pc, groups), run(events, dan, pk, pc, groups)
    for field, sign in [(0, 1), (1, -1)]:
        area, reference = sign * local["edge_phases"][..., field], sign * raw["edge_phases"][..., field]
        assert np.all(area >= 0)
        assert np.all(area <= reference + 1e-13)
        assert np.any(area < reference - 1e-13)
    # No monotonicity assertion is made about P-N, total gains or the guard.


@pytest.mark.parametrize("n", [3, 5])
def test_chunk_boundaries_and_recorders_cannot_change_composed_publication(n):
    matrix, events, dan, pk, pc, groups = fixture(n)
    whole, observed = KCLocalState(PARAMS, matrix), KCLocalState(PARAMS, matrix)
    expected = whole.consume_chunk(events)
    parts, snapshots = [], []
    start = 0
    for stop in [1, 166, 167, 334, 500, 501, 667, 1000, 1500, 2000]:
        snapshots.append({name: getattr(observed, name) for name in STATE})
        parts.append(observed.consume_chunk(events[start:stop]))
        assert observed.consume_chunk(events[:0]).shape == (0, n)
        snapshots.append({name: getattr(observed, name) for name in STATE})
        start = stop
    whole.advance_boundary()
    observed.advance_boundary()
    actual = np.concatenate(parts)
    np.testing.assert_array_equal(actual, expected)
    for name in STATE:
        np.testing.assert_array_equal(getattr(observed, name), getattr(whole, name))
    assert whole.source_frames == observed.source_frames == 12
    assert whole.native_step == observed.native_step == 2000
    assert snapshots  # Recorder actually sampled local state across frames.
    assert_identical(run(actual, dan, pk, pc, groups), run(expected, dan, pk, pc, groups))


def test_boundary_weighted_pair_uses_cold_bridge_and_both_matched_filters():
    matrix, _, _, pk, pc, groups = fixture(3)
    events, dan = np.zeros((600, 3), np.uint8), np.zeros((600, 2))
    events[[0, 167, 334], :] = 1  # Physical local state exists before bridge onset.
    events[500, 0] = 1
    dan[550, 0], dan[500, 1] = 0.5, 0.25
    model = KCLocalState(PARAMS, matrix)
    weighted = model.consume_chunk(events)
    assert 0 < weighted[500, 0] < 1
    result = run(weighted, dan, pk, pc, groups)
    # Only the t=100ms KC event is admitted to the bridge. Its home partner
    # follows10ms later; its away partner is coincident and must cancel.
    kernel = -0.0005 * (math.exp(-10 / 500) - math.exp(-10 / 100))
    expected = np.zeros(len(pk))
    expected[0] = weighted[500, 0] * 0.5 * kernel
    np.testing.assert_allclose(result["edge_phases"][..., 2].sum(0), expected, rtol=0, atol=1e-13)
    assert not result["endpoint_kc"][1:].any()
