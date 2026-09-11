import json

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import csr_matrix, load_npz, save_npz

from bet36fly.brain import FlyBrain
from bet36fly.null_graph import _rewire, graph_array_hashes, make_null_graph


def graph_fixture(path, edges, *, signs=None, kc=(0, 1), mbon=(2, 3), n=6):
    path.mkdir()
    signs = np.ones(n, np.int8) if signs is None else np.asarray(signs, np.int8)
    pre, post, count = np.asarray(edges).T
    graph = csr_matrix((count.astype(np.float32), (pre.astype(int), post.astype(int))), shape=(n, n))
    arrays = {'ids': np.arange(100, 100 + 10 * n, 10, dtype=np.int64),
              'indptr': graph.indptr.astype(np.int64), 'post': graph.indices.astype(np.int32),
              'counts': graph.data.astype(np.float32), 'signs': signs,
              'kc': np.asarray(kc, np.int32), 'mbon': np.asarray(mbon, np.int32),
              'sensory': np.array([n - 1], np.int32),
              'in_degree': np.asarray(graph.sum(0)).ravel()}
    for name, array in arrays.items():
        np.save(path / (name + '.npy'), array)
    types = ['other'] * n
    classes = ['other'] * n
    for indices, type_name, class_name in ((kc, 'KC', 'Kenyon_Cell'), (mbon, 'MBON-a', 'MBON')):
        for index in indices:
            types[index], classes[index] = type_name, class_name
    classes[n - 1] = 'ALPN'
    nodes = pd.DataFrame({'bodyId': arrays['ids'], 'type': types, 'class': classes,
                          'superclass': ['central'] * (n - 1) + ['sensory'],
                          'transmitter': ['ACh' if s > 0 else 'GABA' for s in signs]})
    # Non-graph row order must not influence role derivation or FlyBrain pooling.
    nodes.sample(frac=1, random_state=71).reset_index(drop=True).to_feather(path / 'nodes.feather')
    plastic = graph[list(kc)][:, list(mbon)].T.tocsr()
    plastic.data *= signs[list(kc)][plastic.indices]
    save_npz(path / 'plastic.npz', plastic)
    (path / 'manifest.json').write_text(json.dumps({'dataset': 'fixture', 'stats': {'edges': graph.nnz}}))
    (path / 'source-lock.json').write_text('{}')
    return path


def endpoint_map(path):
    ptr = np.load(path / 'indptr.npy')
    post, counts = np.load(path / 'post.npy'), np.load(path / 'counts.npy')
    return {(int(pre), int(target)): float(count) for pre, target, count in zip(
        np.repeat(np.arange(len(ptr) - 1), np.diff(ptr)), post, counts)}


def test_eligible_swaps_preserve_exact_degrees_weights_groups_and_self_edges(tmp_path):
    source = graph_fixture(tmp_path / 'source', [(0, 2, 2), (1, 3, 2), (4, 4, 7)])
    source_hashes = graph_array_hashes(source)
    output = tmp_path / 'null'
    report = make_null_graph(source, output, seed=42, sweeps=5)
    assert report['valid'] and report['synthetic']
    assert report['accepted_swaps'] == 5
    assert report['changed_edges'] == report['changed_plastic_edges'] == 2
    assert report['changed_edge_fraction'] == 2 / 3
    assert report['changed_plastic_edge_fraction'] == 1
    assert report['self_edges'] == 1
    assert report['gain_group_count'] == 1
    assert all(report['invariants'].values())
    assert endpoint_map(output) == {(0, 3): 2., (1, 2): 2., (4, 4): 7.}
    assert graph_array_hashes(source) == source_hashes
    assert report['graph_array_hashes'] == graph_array_hashes(output)
    assert json.loads((output / 'manifest.json').read_text())['synthetic']
    assert json.loads((output / 'invariant-report.json').read_text()) == report
    assert len(load_npz(output / 'plastic.npz').data) == 2
    brain = FlyBrain(output)
    assert brain.nodes.bodyId.to_list() == brain.ids.tolist()
    assert np.isfinite(brain.simulate(np.zeros(16))['readout']).all()
    assert make_null_graph(source, output, seed=42, sweeps=5) == report


@pytest.mark.parametrize('edges,signs,kc,mbon', [
    ([(0, 2, 2), (1, 3, 3)], None, (0, 1), (2, 3)),  # unequal contact counts
    ([(0, 2, 2), (1, 3, 2)], [1, -1, 1, 1, 1, 1], (0, 1), (2, 3)),  # mixed signs
    ([(0, 2, 2), (1, 3, 2), (0, 3, 3)], None, (0, 1), (2, 3)),  # existing edge collision
    ([(0, 1, 2), (1, 0, 2)], None, (), (2, 3)),  # new self-edges
    ([(0, 2, 2), (0, 3, 2)], None, (0, 1), (2, 3)),  # unchanged pair
])
def test_unswappable_strata_are_invalid_without_inventing_another_control(tmp_path, edges, signs, kc, mbon):
    source = graph_fixture(tmp_path / 'source', edges, signs=signs, kc=kc, mbon=mbon)
    output = tmp_path / 'null'
    report = make_null_graph(source, output, seed=3, sweeps=5)
    assert report['accepted_swaps'] == 0
    assert not report['valid'] and report['invalid_reason']
    assert report['changed_edge_fraction'] == report['changed_plastic_edge_fraction'] == 0
    assert all(report['invariants'].values())
    assert endpoint_map(output) == endpoint_map(source)
    assert report['unchanged_stratum_count'] == report['stratum_count']


def test_colliding_proposals_reject_both_pairs(monkeypatch):
    class FixedPairing:
        def shuffle(self, array):
            array[:] = array[[0, 2, 1, 3]]
    monkeypatch.setattr(np.random, 'default_rng', lambda seed: FixedPairing())
    pre = np.array([0, 0, 1, 2], np.int32)
    post = np.array([4, 5, 6, 6], np.int32)
    original = post.copy()
    # Both disjoint pairs propose 0->6, which did not exist before the sweep.
    report = _rewire(pre, post, np.full(4, 2, np.float32), np.ones(7, np.int8),
                      np.array([1, 1, 1, 0, 0, 0, 0]), np.array([0, 0, 0, 0, 1, 1, 1]),
                      seed=4, sweeps=1)
    np.testing.assert_array_equal(post, original)
    assert report['accepted_swaps'] == 0


@pytest.mark.parametrize('changed_body,label', [(110, 'KCg'), (130, 'MBON-b')])
def test_exact_source_and_destination_types_define_separate_strata(tmp_path, changed_body, label):
    source = graph_fixture(tmp_path / 'source', [(0, 2, 2), (1, 3, 2)])
    nodes = pd.read_feather(source / 'nodes.feather')
    nodes.loc[nodes.bodyId == changed_body, 'type'] = label
    nodes.to_feather(source / 'nodes.feather')
    report = make_null_graph(source, tmp_path / 'null', seed=42, sweeps=5)
    assert report['accepted_swaps'] == 0
    assert report['gain_group_count'] == 2
    assert report['invariants']['plastic_group_sizes']


def test_replay_is_deterministic_and_cached_source_changes_are_rejected(tmp_path):
    edges = [(0, 3, 2), (1, 4, 2), (2, 5, 2), (0, 4, 3), (1, 5, 3), (2, 3, 3)]
    source = graph_fixture(tmp_path / 'source', edges, kc=(0, 1, 2), mbon=(3, 4, 5), n=7)
    first = make_null_graph(source, tmp_path / 'a', seed=137, sweeps=5)
    second = make_null_graph(source, tmp_path / 'b', seed=137, sweeps=5)
    assert first['graph_array_hashes'] == second['graph_array_hashes']
    assert first['sweeps'] == second['sweeps']
    with pytest.raises(ValueError, match='does not match'):
        make_null_graph(source, tmp_path / 'a', seed=42, sweeps=5)
    changed = np.load(tmp_path / 'a' / 'counts.npy')
    changed[0] += 1
    np.save(tmp_path / 'a' / 'counts.npy', changed)
    with pytest.raises(ValueError, match='does not match'):
        make_null_graph(source, tmp_path / 'a', seed=137, sweeps=5)


def test_final_change_fraction_controls_validity_even_after_successful_swaps(tmp_path):
    source = graph_fixture(tmp_path / 'source', [(0, 2, 2), (1, 3, 2)])
    report = make_null_graph(source, tmp_path / 'null', seed=42, sweeps=2)
    assert report['accepted_swaps'] == 2
    assert not report['valid']
    assert report['changed_edges'] == report['changed_plastic_edges'] == 0


def test_graph_without_plastic_changes_cannot_support_topology_conclusion(tmp_path):
    source = graph_fixture(tmp_path / 'source', [(0, 2, 1), (4, 6, 2), (5, 7, 2)], n=9)
    report = make_null_graph(source, tmp_path / 'null', seed=42, sweeps=1)
    assert report['changed_edges'] == 2 and report['changed_plastic_edges'] == 0
    assert not report['valid']


def test_official_graph_destination_and_nonintegral_counts_are_rejected(tmp_path):
    source = graph_fixture(tmp_path / 'source', [(0, 2, 2), (1, 3, 2)])
    with pytest.raises(ValueError, match='separate'):
        make_null_graph(source, source, seed=42)
    with pytest.raises(ValueError, match='separate'):
        make_null_graph(source, source / 'null', seed=42)
    counts = np.load(source / 'counts.npy')
    counts[0] = 2.5
    np.save(source / 'counts.npy', counts)
    with pytest.raises(ValueError, match='integral'):
        make_null_graph(source, tmp_path / 'null', seed=42)
