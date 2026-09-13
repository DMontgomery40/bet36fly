"""Protect source identity and edge direction in the read-only sensory audit."""
import numpy as np
import pandas as pd
import pytest

from scripts.export_sensory_crosswalk import align_annotations, direct_pairs


def tables():
    # Deliberately unsorted annotations; IDs exceed exact float64 integer range.
    ids = np.array([2**53 + 1, 2**53 + 3, 2**53 + 5], np.int64)
    nodes = pd.DataFrame({'bodyId': ids[[2, 0, 1]], 'type': ['MN9', 'ORN_VA2', None],
                          'class': [None, 'olfactory', 'gustatory'],
                          'superclass': ['cb_motor', 'cb_sensory', 'cb_sensory']})
    raw = nodes.copy()
    raw['rootSide'] = ['unknown', 'L', None]
    return ids, nodes, raw


def test_alignment_keeps_exact_ids_raw_metadata_and_unknowns():
    ids, nodes, raw = tables()
    n, r = align_annotations(ids, nodes, raw)
    assert n.index.tolist() == [2**53 + 1, 2**53 + 3, 2**53 + 5]
    assert r.iloc[0].rootSide == 'L'
    assert pd.isna(r.iloc[1].rootSide)
    assert pd.isna(n.iloc[1]['type'])
    assert r.iloc[2].rootSide == 'unknown'


@pytest.mark.parametrize('case', ['duplicate_ids', 'unsorted_ids', 'float_ids',
    'duplicate_raw', 'duplicate_nodes', 'missing_raw', 'missing_nodes', 'wrong_type', 'wrong_class'])
def test_ambiguous_or_inconsistent_identity_is_rejected(case):
    ids, nodes, raw = tables()
    if case == 'duplicate_ids':
        ids[1] = ids[0]
    if case == 'unsorted_ids':
        ids = ids[::-1]
    if case == 'float_ids':
        ids = ids.astype(float)
    if case == 'duplicate_raw':
        raw = pd.concat([raw, raw.iloc[:1]])
    if case == 'duplicate_nodes':
        nodes = pd.concat([nodes, nodes.iloc[:1]])
    if case == 'missing_raw':
        raw = raw.iloc[1:]
    if case == 'missing_nodes':
        nodes = nodes.iloc[1:]
    if case == 'wrong_type':
        raw.loc[0, 'type'] = 'other'
    if case == 'wrong_class':
        raw.loc[0, 'class'] = 'other'
    with pytest.raises(ValueError):
        align_annotations(ids, nodes, raw)


def test_direct_pairs_preserve_direction_contacts_self_edges_and_empty_targets():
    # 0->0(1), 0->2(7), 1->2(11), 2->0(13). Reversing CSR would give 13, not 7.
    ids = np.array([101, 202, 303], np.int64)
    ptr = np.array([0, 2, 3, 4], np.int64)
    post = np.array([0, 2, 2, 0], np.int32)
    counts = np.array([1, 7, 11, 13], np.uint32)
    assert direct_pairs(ids, ptr, post, counts, [0], [0, 2]) == [
        {'csr_edge_index': 0, 'pre_body_id': 101, 'post_body_id': 101, 'contacts': 1},
        {'csr_edge_index': 1, 'pre_body_id': 101, 'post_body_id': 303, 'contacts': 7}]
    assert direct_pairs(ids, ptr, post, counts, [0, 1], []) == []
    assert direct_pairs(ids, ptr, post, counts, [1], [0]) == []


def miniature_release(tmp_path):
    import hashlib
    import json
    import pyarrow as pa
    import pyarrow.feather as feather

    brain, raw, docs = [tmp_path / name for name in ('data/brain', 'data/raw', 'docs')]
    for path in (brain, raw, docs):
        path.mkdir(parents=True)
    ids = np.array([101, 202, 303, 404], np.int64)
    frame = pd.DataFrame(dict(bodyId=ids, type=['ORN_VA2', 'VA2_adPN', 'LB1a', 'MN9'],
        superclass=['cb_sensory', 'cb_intrinsic', 'cb_sensory', 'cb_motor'],
        **{'class': ['olfactory', 'ALPN', 'gustatory', None]},
        transmitter=['acetylcholine'] * 4))
    feather.write_feather(pa.Table.from_pandas(frame), brain / 'nodes.feather')
    for name in ['instance', 'rootSide', 'somaSide', 'entryNerve', 'exitNerve',
                 'receptorType', 'flywireType', 'statusLabel']:
        frame[name] = None
    frame['subclass'] = [None, None, 'labellar bristle', 'pm']
    feather.write_feather(pa.Table.from_pandas(frame), raw / 'annotations.feather')
    source = raw / 'annotations.feather'
    (docs / 'connectome-source-lock.json').write_text(json.dumps({'annotations.feather':
        dict(bytes=source.stat().st_size, sha256=hashlib.sha256(source.read_bytes()).hexdigest())}))
    arrays = dict(ids=ids, indptr=np.array([0, 1, 1, 2, 2], np.int64),
        post=np.array([1, 3], np.int32), counts=np.array([7, 2], np.uint32),
        signs=np.ones(4, np.int8))
    for name, data in arrays.items():
        np.save(brain / f'{name}.npy', data)
    (brain / 'manifest.json').write_text(json.dumps(dict(dataset='synthetic fixture',
        stats=dict(neurons=4, edges=2, contacts=9))))
    return tmp_path


def test_full_export_preserves_unknown_taste_and_uses_real_edge_support(tmp_path):
    import csv
    import io
    import json
    from scripts.export_sensory_crosswalk import build

    result = build(miniature_release(tmp_path))
    a = json.loads(result['anatomy.json'])
    assert a['neural_calls'] == 0
    assert a['labellar_receptor_annotations_present'] == 0
    assert a['direct_projection_support']['ORN_VA2']['contacts'] == 7
    rows = list(csv.DictReader(io.StringIO(result['crosswalk.csv'])))
    taste = next(row for row in rows if row['body_id'] == '303')
    assert taste['candidate_receptor'] == taste['root_side'] == ''
    assert taste['binding_status'] == 'anatomy_candidate_only_not_a_calibrated_stimulus'


@pytest.mark.parametrize('corruption', ['source', 'graph'])
def test_export_rejects_changed_source_or_inconsistent_graph(tmp_path, corruption):
    from scripts.export_sensory_crosswalk import build

    root = miniature_release(tmp_path)
    if corruption == 'source':
        with (root / 'data/raw/annotations.feather').open('ab') as stream:
            stream.write(b'changed')
    else:
        np.save(root / 'data/brain/counts.npy', np.array([8, 2], np.uint32))
    with pytest.raises(ValueError, match='mismatch'):
        build(root)


def test_cli_refuses_overwrite_and_check_detects_changed_artifact(tmp_path):
    import subprocess
    import sys
    from pathlib import Path

    root = miniature_release(tmp_path)
    output = root / 'evidence'
    cmd = [sys.executable, str(Path(__file__).resolve().parents[1] / 'scripts/export_sensory_crosswalk.py'),
           '--root', str(root), '--output', str(output)]
    assert subprocess.run(cmd, capture_output=True).returncode == 0
    original = (output / 'crosswalk.csv').read_bytes()
    assert subprocess.run(cmd, capture_output=True).returncode != 0
    assert (output / 'crosswalk.csv').read_bytes() == original
    assert subprocess.run(cmd + ['--check'], capture_output=True).returncode == 0
    (output / 'crosswalk.csv').write_bytes(b'changed evidence')
    assert subprocess.run(cmd + ['--check'], capture_output=True).returncode != 0
    assert (output / 'crosswalk.csv').read_bytes() == b'changed evidence'
