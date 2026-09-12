"""Export anatomical wiki tables without constructing an engine or running a trial.

Uses the existing retained graph and the schema-3 encoder. The additional gamma
column describes the repair branch's label policy; it does not enable that policy.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np
import pyarrow.feather as feather

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def family(label):
    if label.startswith("KCa'b'"):
        return 'apbp'
    if label.startswith('KCg'):
        return 'gamma'
    if label.startswith('KCab'):
        return 'ab'
    return 'other'


def csv_bytes(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def build(root=ROOT):
    from bet36fly.reward_encoder import glomerular_map
    from bet36fly.reward_protocol import COMPARTMENTS, plastic_mapping

    brain = root / 'data/brain'
    names = ('ids', 'indptr', 'post', 'counts', 'signs', 'sensory', 'kc', 'mbon')
    arrays = {name: np.load(brain / f'{name}.npy', mmap_mode='r', allow_pickle=False) for name in names}
    ids, ptr, post, contacts = (arrays[k] for k in ('ids', 'indptr', 'post', 'counts'))
    nodes = feather.read_table(brain / 'nodes.feather').to_pandas()
    raw = feather.read_table(root / 'data/raw/annotations.feather').to_pandas()
    assert nodes.bodyId.is_unique and raw.bodyId.is_unique and len(np.unique(ids)) == len(ids)
    nodes = nodes.set_index('bodyId').reindex(ids).fillna({'type': '', 'class': '', 'transmitter': ''})
    raw = raw.set_index('bodyId').reindex(ids).fillna({'instance': '', 'somaSide': '', 'rootSide': ''})
    assert nodes.superclass.notna().all()
    assert np.array_equal(arrays['kc'], np.flatnonzero(nodes['class'].eq('Kenyon_Cell')))
    assert np.array_equal(arrays['sensory'], np.flatnonzero(nodes['class'].eq('ALPN')))
    assert np.array_equal(arrays['mbon'], np.flatnonzero(nodes['class'].eq('MBON')))
    assert nodes['type'].equals(raw['type'].fillna(''))
    kc, sensory = arrays['kc'], arrays['sensory']
    kc_types = nodes.iloc[kc]['type'].to_numpy()
    outputs = [np.flatnonzero(nodes['type'].eq(m) & nodes['class'].eq('MBON')) for _, _, m in COMPARTMENTS]
    edges, edge_kc, compartments = plastic_mapping(ptr, post, kc, outputs)
    gamma = np.array([family(str(t)) == 'gamma' for t in kc_types[edge_kc]])
    eligible = (compartments == 0) | gamma
    edge_rows = []
    for e, k, c, keep in zip(edges, edge_kc, compartments, eligible):
        edge_rows.append(dict(csr_edge_index=int(e), pre_body_id=int(ids[kc[k]]), post_body_id=int(ids[post[e]]),
                              kc_type=str(kc_types[k]), kc_family=family(str(kc_types[k])),
                              channel=COMPARTMENTS[c][0], contacts=int(contacts[e]),
                              schema3_eligible=1, repair_gamma_eligible=int(keep)))
    support = np.zeros((len(ids), 2), dtype=int)
    np.add.at(support, (kc[edge_kc], compartments), 1)
    is_kc = np.zeros(len(ids), bool)
    is_kc[kc] = True
    port_contacts = np.array([contacts[ptr[p]:ptr[p + 1]][is_kc[post[ptr[p]:ptr[p + 1]]]].sum()
                              for p in sensory], dtype=float)
    ports = nodes.iloc[sensory]
    protocol = json.loads((root / 'configs/reward-v3-pilot.json').read_text())
    mapping = glomerular_map(ports['type'].to_numpy(), ports.transmitter.to_numpy(), port_contacts,
                             n_features=16, min_kc_contacts=protocol['encoder_min_kc_contacts'])
    port_local = {int(v): k for k, v in enumerate(sensory)}
    pure_dopamine = np.flatnonzero(nodes.transmitter.eq('dopamine'))
    annotated_dan = np.flatnonzero(nodes['class'].eq('DAN'))
    apl = np.flatnonzero(nodes['type'].eq('APL'))
    selected = np.unique(np.concatenate([kc, sensory, arrays['mbon'], pure_dopamine, annotated_dan, apl]))
    cell_rows = []
    for i in selected:
        node, original = nodes.iloc[i], raw.iloc[i]
        roles = []
        if is_kc[i]:
            roles.append('KC')
        if i in port_local:
            roles.append('ALPN')
        if node['class'] in ('DAN', 'MBON'):
            roles.append(node['class'])
        if node['type'] == 'APL':
            roles.append('APL')
        for label, dan, mbon in COMPARTMENTS:
            if node['type'] == dan and node['class'] == 'DAN' and node.transmitter == 'dopamine':
                roles.append(f'{label}_teaching')
            if node['type'] == mbon and node['class'] == 'MBON':
                roles.append(f'{label}_readout')
        p = port_local.get(int(i))
        driven = p is not None and mapping['port_feature'][p] >= 0
        cell_rows.append(dict(body_id=int(ids[i]), graph_index=int(i), type=node['type'],
                              instance=original.instance, cell_class=node['class'], superclass=node.superclass,
                              soma_side=original.somaSide, root_side=original.rootSide,
                              transmitter=node.transmitter, base_model_sign=int(arrays['signs'][i]),
                              reward_fast_output_zeroed=int(node.transmitter == 'dopamine'),
                              roles=';'.join(roles), kc_family=family(node['type']) if is_kc[i] else '',
                              home_support_edges=int(support[i, 0]), away_support_edges=int(support[i, 1]),
                              encoder_feature=int(mapping['port_feature'][p]) if driven else '',
                              encoder_center=float(mapping['port_center'][p]) if driven else ''))
    type_rows = []
    for label in sorted(set(kc_types)):
        selected_type = kc_types[edge_kc] == label
        row = dict(type=label, family=family(label), cells=int(np.count_nonzero(kc_types == label)))
        for c, channel in enumerate(('home', 'away')):
            chosen = selected_type & (compartments == c)
            row[f'{channel}_edges'] = int(chosen.sum())
            row[f'{channel}_contacts'] = int(contacts[edges[chosen]].sum())
            row[f'{channel}_repair_eligible'] = int(eligible[chosen].sum())
        type_rows.append(row)
    target_types = ('PPL101', 'PAM12', 'PAM11', 'MBON11', 'MBON09', 'MBON07', 'APL')
    target_summary = {}
    for label in target_types:
        indices = np.flatnonzero(nodes['type'].eq(label))
        incoming = np.flatnonzero(np.isin(post, indices))
        incoming_pre = np.searchsorted(ptr, incoming, side='right') - 1
        kc_incoming = is_kc[incoming_pre]
        target_summary[label] = dict(body_ids=ids[indices].tolist(), instances=raw.iloc[indices].instance.tolist(),
                                     transmitters=sorted(set(nodes.iloc[indices].transmitter)),
                                     incoming_edges=len(incoming), incoming_contacts=int(contacts[incoming].sum()),
                                     kc_incoming_edges=int(kc_incoming.sum()),
                                     kc_incoming_contacts=int(contacts[incoming[kc_incoming]].sum()))
    source_paths = [brain / f'{n}.npy' for n in names] + [brain / 'nodes.feather', brain / 'manifest.json',
                    root / 'data/raw/annotations.feather', root / 'docs/connectome-source-lock.json',
                    root / 'configs/reward-v3-pilot.json', root / 'bet36fly/reward_encoder.py',
                    root / 'bet36fly/reward_protocol.py', root / 'scripts/export_fly_cell_atlas.py']
    hashes = {}
    for p in source_paths:
        with p.open('rb') as stream:
            hashes[str(p.relative_to(root))] = hashlib.file_digest(stream, 'sha256').hexdigest()
    summary = dict(schema=1, dataset='MaleCNS v1.0', license='CC-BY-4.0',
                   attribution='Berg et al.; HHMI Janelia, Cambridge, MRC LMB and Google Research',
                   scope='Anatomical table export; no neural activity measured and no plasticity enabled.',
                   neuron_count=len(ids), cell_rows=len(cell_rows), kenyon_cells=len(kc),
                   sensory_ports=len(sensory), mbon_cells=len(arrays['mbon']),
                   annotated_dan_cells=len(annotated_dan), pure_dopamine_cells=len(pure_dopamine),
                   dan_and_pure_dopamine_cells=len(np.intersect1d(annotated_dan, pure_dopamine)),
                   apl_cells=len(apl), selected_reward_support_edges=len(edges),
                   repair_gamma_eligible_edges=int(eligible.sum()),
                   encoder=mapping['summary'], kc_types=type_rows, targets=target_summary, source_sha256=hashes)
    assert len(cell_rows) == len({r['body_id'] for r in cell_rows})
    assert len(edges) == sum(r['home_edges'] + r['away_edges'] for r in type_rows)
    assert all(r['schema3_eligible'] == 1 for r in edge_rows)
    assert all(r['repair_gamma_eligible'] == 1 for r in edge_rows if r['channel'] == 'home')
    return {'neurons.csv': csv_bytes(cell_rows), 'reward-edges.csv': csv_bytes(edge_rows),
            'atlas.json': (json.dumps(summary, indent=2) + '\n').encode()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'wiki/cells/data')
    parser.add_argument('--check', action='store_true', help='Compare existing exports; do not write.')
    args = parser.parse_args()
    outputs = build()
    if args.check:
        mismatches = [name for name, data in outputs.items()
                      if not (args.output / name).is_file() or (args.output / name).read_bytes() != data]
        if mismatches:
            raise SystemExit(f'Atlas differs: {mismatches}')
    else:
        args.output.mkdir(parents=True, exist_ok=True)
        for name, data in outputs.items():
            (args.output / name).write_bytes(data)
    print(f'{"Checked" if args.check else "Exported"} {len(outputs)} anatomical tables; no simulation ran.')


if __name__ == '__main__':
    main()
