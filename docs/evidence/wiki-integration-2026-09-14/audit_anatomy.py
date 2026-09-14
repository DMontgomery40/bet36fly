"""Read locked graph arrays and saved manifests; never construct a simulator.

Run from the repository root with .venv/bin/python and this file's path.
The output is a documentation snapshot, not an experiment or a source re-import.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow.feather as feather

ROOT = Path(__file__).resolve().parents[3]
DEST = Path(__file__).parent
brain = ROOT / 'data/brain'
ids, ptr, post, contacts = [np.load(brain / f'{k}.npy', allow_pickle=False)
                           for k in ('ids', 'indptr', 'post', 'counts')]
nodes = feather.read_table(brain / 'nodes.feather').to_pandas().set_index('bodyId').loc[ids]
assert np.array_equal(nodes.index.to_numpy(), ids)
types = nodes['type'].fillna('')
classes = nodes['class'].fillna('')
supers = nodes['superclass'].fillna('')
src = np.repeat(np.arange(len(ids)), np.diff(ptr))
populations = {name: (supers == name).to_numpy() for name in ('ol_intrinsic', 'ol_sensory', 'visual_projection', 'descending')}
populations.update({name: (classes == label).to_numpy() for name, label in
                    [('KC', 'Kenyon_Cell'), ('MBON', 'MBON'), ('DAN', 'DAN'), ('CX', 'CX'), ('ALPN', 'ALPN')]})
populations['LH'] = types.str.startswith('LH').to_numpy()
populations['KCg-d'] = (types == 'KCg-d').to_numpy()
populations['descending'] = (supers == 'descending_neuron').to_numpy()


def connection(a, b):
    selected = populations[a][src] & populations[b][post]
    return {'pairs': int(selected.sum()), 'contacts': int(contacts[selected].sum()),
            'presynaptic_cells': int(np.unique(src[selected]).size)}


result = {'checked_date_utc': '2026-09-14', 'kind': 'static_anatomy_and_saved_artifact_audit',
          'neural_calls': 0, 'neurons': len(ids), 'pairs': len(post), 'contacts': int(contacts.sum()),
          'selectors': {'superclass': ['ol_intrinsic', 'ol_sensory', 'visual_projection', 'descending_neuron'],
                        'class': ['Kenyon_Cell', 'MBON', 'DAN', 'CX', 'ALPN'],
                        'LH': 'type starts with LH (annotation proxy, not every neuron innervating LH)',
                        'KCg-d': 'type equals KCg-d'},
          'counts': {k: int(v.sum()) for k, v in populations.items()},
          'classes': {k: int(v) for k, v in classes.value_counts().items()},
          'superclasses': {k: int(v) for k, v in supers.value_counts().items()},
          'connections': {f'{a}->{b}': connection(a, b) for a, b in
                          [('visual_projection', 'KC'), ('visual_projection', 'KCg-d'),
                           ('MBON', 'CX'), ('MBON', 'DAN'), ('CX', 'DAN'), ('ALPN', 'LH'),
                           ('ALPN', 'KC'), ('MBON', 'LH'), ('LH', 'MBON'), ('CX', 'descending'),
                           ('LH', 'descending'), ('MBON', 'descending')]},
          'hashes': {f'data/brain/{k}': hashlib.sha256((brain / k).read_bytes()).hexdigest()
                     for k in ('ids.npy', 'indptr.npy', 'post.npy', 'counts.npy', 'nodes.feather')}}
incoming = {}
for name in ('LH', 'MBON'):
    selection = populations[name][src]
    incoming[name] = np.bincount(post[selection], weights=contacts[selection], minlength=len(ids))
both = (incoming['LH'] >= 20) & (incoming['MBON'] >= 20)
result['LH_MBON_convergence'] = {'threshold_contacts_from_each': 20, 'cells': int(both.sum()),
                               'DAN': int((both & populations['DAN']).sum()),
                               'CX': int((both & populations['CX']).sum())}
links = json.loads((ROOT / 'output/associative/associative-links-cd33a0b4dfd97540c887/manifest.json').read_text())
result['associative_compartments'] = links['anatomy']['compartments']
result['selected_edge_slots'] = links['anatomy']['plastic_edges']
result['eligible_edges'] = links['anatomy']['eligible_edges']
edge_selection = populations['KC'][src] & types.isin(['MBON05', 'MBON01']).to_numpy()[post]
selected_edges = np.flatnonzero(edge_selection)
eligible = types.str.startswith('KCg').to_numpy()[src[selected_edges]]
assert len(selected_edges) == result['selected_edge_slots'] and int(eligible.sum()) == result['eligible_edges']
result['season_floor_denominators'] = []
for key in ('94f9a4913dcb12a55f15', '8cc62a9ff149c9aed4e4', 'a50c18cdef85f343bf71'):
    run = ROOT / f'output/associative/associative-sports-{key}'
    checkpoint = sorted(run.glob('checkpoint-*.npz'))[-1]
    with np.load(checkpoint, allow_pickle=False) as saved:
        gains = saved['gains']
        assert len(gains) == len(eligible)
        result['season_floor_denominators'].append({'run': run.name, 'checkpoint': checkpoint.name,
                                                   'floor_count': int((gains <= .5).sum()),
                                                   'all_slots_fraction': float(np.mean(gains <= .5)),
                                                   'eligible_fraction': float(np.mean(gains[eligible] <= .5))})
for comp in result['associative_compartments']:
    assert ids[(types == comp['mbon_type']).to_numpy()].tolist() == comp['mbon_body_ids']
    assert ids[((types == comp['dan_type']) & (classes == 'DAN') & (nodes.transmitter == 'dopamine')).to_numpy()].tolist() == comp['dan_body_ids']
result['stress_cycle24'] = {}
for key in ('d68e0f3df819053aa1ee', 'd3d4da0959060f926f57'):
    manifest = json.loads((ROOT / f'output/associative/associative-stress-{key}/manifest.json').read_text())
    result['stress_cycle24'][manifest['identity']] = [x for x in manifest['occupancy'] if x['label'] == 'cycle-24']
result['sports_storage'] = []
for key in ('94f9a4913dcb12a55f15', '8cc62a9ff149c9aed4e4', 'a50c18cdef85f343bf71'):
    run = ROOT / f'output/associative/associative-sports-{key}'
    rows = json.loads((run / 'rows.json').read_text())
    if isinstance(rows, dict):
        rows = rows['rows']
    result['sports_storage'].append({'run': run.name, 'rows': len(rows),
                                    'all_have_two_counts_per_team': all(len(r['home_response']) == len(r['away_response']) == 2 for r in rows),
                                    'row_keys': sorted(set().union(*(r.keys() for r in rows))),
                                    'checkpoint_files': len(list(run.glob('checkpoint-*.npz')))})
(DEST / 'anatomy-and-storage.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ('counts', 'connections', 'LH_MBON_convergence', 'stress_cycle24', 'sports_storage')}, indent=2))
