"""Loss-accounted import of the official MaleCNS v1.0 neuronal connectome.

Data: Berg et al. / HHMI Janelia / Google Research, CC-BY 4.0.
Wiring and synapse counts are measured data; transmitter signs are a model.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = 'https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/'
SOURCES = {
    'annotations.feather': BASE_URL + 'body-annotations-male-cns-v1.0-minconf-0.5.feather',
    'neurotransmitters.feather': BASE_URL + 'body-neurotransmitters-male-cns-v1.0.feather',
    'connectome-weights.feather': BASE_URL + 'connectome-weights-male-cns-v1.0-minconf-0.5.feather',
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        while b := f.read(8 * 1024 * 1024):
            h.update(b)
    return h.hexdigest()


def index_edges(ids, pre, post, counts):
    ids, pre, post, counts = map(np.asarray, (ids, pre, post, counts))
    if any(x.dtype.kind not in 'iu' for x in (ids, pre, post)):
        raise ValueError('Neuron IDs must remain exact integers.')
    if not len(ids) or np.any(ids[1:] <= ids[:-1]) or np.any(ids < 0):
        raise ValueError('Neuron IDs must be nonnegative, sorted and unique.')
    if not len(pre) == len(post) == len(counts):
        raise ValueError('Edge column lengths differ.')
    if (not np.all(np.isfinite(counts)) or np.any(counts < 1)
            or np.any(counts != np.floor(counts)) or np.any(counts > 2**32 - 1)):
        raise ValueError('Synapse counts must be positive uint32-compatible integers.')
    i, j = np.searchsorted(ids, pre), np.searchsorted(ids, post)
    keep = (i < len(ids)) & (j < len(ids))
    keep &= ids[np.minimum(i, len(ids) - 1)] == pre
    keep &= ids[np.minimum(j, len(ids) - 1)] == post
    return i[keep].astype(np.int32), j[keep].astype(np.int32), counts[keep].astype(np.uint32), keep


def transmitter_signs(values):
    """Fast sign proxy: ACh +, GABA/glutamate/histamine -, ambiguous +.

    Unknown and modulator-only neurons retain their edges. These signs do not
    model receptor-dependent effects; ambiguous counts are disclosed.
    """
    signs, uncertain = [], []
    for value in values:
        tokens = {t.strip() for t in str(value).lower().split(',')}
        fast = ({1} if 'acetylcholine' in tokens else set())
        fast |= {-1} if tokens & {'gaba', 'glutamate', 'histamine'} else set()
        uncertain.append(len(fast) != 1)
        signs.append(next(iter(fast)) if len(fast) == 1 else 1)
    return np.array(signs, np.int8), np.array(uncertain, bool)


def normalize_nodes(frame):
    keep = frame.superclass.notna() & frame.superclass.ne('') & frame.status.ne('Glia')
    nodes = frame.loc[keep].sort_values('bodyId').reset_index(drop=True)
    if nodes.bodyId.duplicated().any():
        raise ValueError('Duplicate annotated neuron IDs.')
    return nodes


def prepare(raw: Path = ROOT / 'data/raw', out: Path = ROOT / 'data/brain') -> dict:
    import pyarrow as pa
    import pyarrow.feather as feather
    import pyarrow.ipc as ipc
    from scipy.sparse import csr_matrix, save_npz

    out.mkdir(parents=True, exist_ok=True)
    hashes = {name: {'url': url, 'bytes': (raw / name).stat().st_size, 'sha256': digest(raw / name)}
              for name, url in SOURCES.items()}
    lock = out / 'source-lock.json'
    if lock.exists() and json.loads(lock.read_text()) != hashes:
        raise ValueError('Raw source changed; preserve the old dataset and prepare a new version directory.')
    frame = feather.read_table(raw / 'annotations.feather').to_pandas()
    nodes = normalize_nodes(frame)
    ids = nodes.bodyId.to_numpy(np.int64)
    nts = feather.read_table(raw / 'neurotransmitters.feather', columns=['body', 'consensus_nt']).to_pandas()
    nodes['transmitter'] = nodes.bodyId.map(nts.set_index('body').consensus_nt)
    signs, uncertain = transmitter_signs(nodes.transmitter)
    reader = ipc.open_file(pa.memory_map(str(raw / 'connectome-weights.feather'), 'r'))
    pres, posts, weights = [], [], []
    stats = dict(source_edges=0, source_contacts=0, excluded_edges=0, excluded_contacts=0,
                 weak_edges=0, self_edges=0)
    for number in range(reader.num_record_batches):
        b = reader.get_batch(number)
        pre, post, w = [b.column(b.schema.get_field_index(c)).to_numpy() for c in
                        ('body_pre', 'body_post', 'weight')]
        i, j, count, keep = index_edges(ids, pre, post, w)
        pres.append(i)
        posts.append(j)
        weights.append(count)
        stats['source_edges'] += len(pre)
        stats['source_contacts'] += int(w.sum(dtype=np.uint64))
        stats['excluded_edges'] += int((~keep).sum())
        stats['excluded_contacts'] += int(w[~keep].sum(dtype=np.uint64))
        stats['weak_edges'] += int((count == 1).sum())
        stats['self_edges'] += int((i == j).sum())
    pre, post, count = np.concatenate(pres), np.concatenate(posts), np.concatenate(weights)
    del pres, posts, weights
    # Outgoing CSR, ordered pre -> post. No strength threshold or edge deletion.
    counts = csr_matrix((count.astype(np.float32), (pre, post)), shape=(len(ids), len(ids)))
    if counts.nnz != len(pre):
        raise ValueError('Source has repeated directed pairs; investigate before claiming exact edge preservation.')
    np.save(out / 'indptr.npy', counts.indptr.astype(np.int64))
    np.save(out / 'post.npy', counts.indices.astype(np.int32))
    np.save(out / 'counts.npy', counts.data.astype(np.float32))
    np.save(out / 'signs.npy', signs)
    np.save(out / 'ids.npy', ids)
    kc = np.flatnonzero(nodes['class'].eq('Kenyon_Cell')).astype(np.int32)
    mbon = np.flatnonzero(nodes['class'].eq('MBON')).astype(np.int32)
    sensory = np.flatnonzero(nodes['class'].eq('ALPN')).astype(np.int32)
    for name, arr in [('kc', kc), ('mbon', mbon), ('sensory', sensory)]:
        np.save(out / (name + '.npy'), arr)
    plastic = counts[kc][:, mbon].T.tocsr()
    # Transmitter signs remain presynaptic; count magnitude is never negative.
    plastic.data *= signs[kc][plastic.indices]
    save_npz(out / 'plastic.npz', plastic)
    nodes[['bodyId', 'class', 'type', 'superclass', 'somaLocation', 'transmitter']].to_feather(out / 'nodes.feather')
    np.save(out / 'in_degree.npy', np.asarray(counts.sum(axis=0)).ravel())
    stats.update(neurons=len(ids), edges=int(counts.nnz), contacts=int(count.sum(dtype=np.uint64)),
                 kenyon_cells=len(kc), mushroom_body_outputs=len(mbon), sensory_ports=len(sensory),
                 plastic_edges=int(plastic.nnz), uncertain_transmitter_neurons=int(uncertain.sum()))
    assert stats['edges'] + stats['excluded_edges'] == stats['source_edges']
    assert stats['contacts'] + stats['excluded_contacts'] == stats['source_contacts']
    report = {
        'dataset': 'MaleCNS v1.0', 'release': '2026-06-08', 'publication': '2026-09-03',
        'source': 'https://male-cns.janelia.org/download/', 'license': 'CC-BY-4.0',
        'attribution': 'Berg et al.; HHMI Janelia, Cambridge, MRC LMB and Google Research',
        'node_policy': 'All non-glial objects with an assigned neuronal superclass.',
        'edge_policy': 'Every released edge among retained neurons; no extra threshold; self edges retained.',
        'excluded_policy': 'Edges incident to unresolved fragments/non-retained objects; counted, not hidden.',
        'sign_assumption': 'ACh excitatory; GABA/glutamate/histamine inhibitory; ambiguous +1.',
        'biological_dynamics_validated': False, 'stats': stats, 'source_hashes': hashes,
    }
    lock.write_text(json.dumps(hashes, indent=2) + '\n')
    (out / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    print(json.dumps(prepare(), indent=2))
