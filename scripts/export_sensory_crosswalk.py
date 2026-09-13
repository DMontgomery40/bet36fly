"""Read-only MaleCNS sensory candidates. No engine, rate binding, or valence inference.

Derived data: Berg et al., HHMI Janelia/Cambridge/MRC LMB/Google, CC BY 4.0.
Receptor/glomerulus crosswalk: Benton et al. 2025, Dataset EV1 rows 14/15/19/20/23.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pyarrow.feather as feather

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = {
    'ORN_DM1': ('Or42b', 'ab1A', 14),
    'ORN_VA2': ('Or92a', 'ab1B', 15),
    'ORN_DM5': ('Or85a/(Or33b)', 'ab2B', 19),
    'ORN_DM2': ('Or22a/(Or22b)', 'ab3A', 20),
    'ORN_DA2': ('Or56a/(Or33a)', 'ab4B', 23),
}
PN_TYPES = {'ORN_VA2': 'VA2_adPN', 'ORN_DA2': 'DA2_lPN'}


def align_annotations(ids, nodes, raw):
    """Refuse lossy IDs, duplicate/missing rows and mismatched retained annotations."""
    ids = np.asarray(ids)
    if (ids.ndim != 1 or ids.dtype.kind not in 'iu' or not len(ids)
            or np.any(ids[1:] <= ids[:-1])):
        raise ValueError('Retained IDs must be exact, sorted, unique integers.')
    for frame in (nodes, raw):
        if (frame.bodyId.dtype.kind not in 'iu' or not frame.bodyId.is_unique
                or not np.isin(ids, frame.bodyId.to_numpy()).all()):
            raise ValueError('Annotations must have exact unique IDs covering the retained graph.')
    n, r = [frame.set_index('bodyId').reindex(ids) for frame in (nodes, raw)]
    for column in ('type', 'class', 'superclass'):
        if not np.array_equal(n[column].fillna('').astype(str).to_numpy(),
                              r[column].fillna('').astype(str).to_numpy()):
            raise ValueError(f'Retained/raw {column} mismatch.')
    return n, r


def direct_pairs(ids, ptr, post, counts, sources, targets):
    """Enumerate existing directed pairs, including weak and self contacts."""
    target_set = set(int(i) for i in targets)
    rows = []
    for pre in sources:
        for edge in range(int(ptr[pre]), int(ptr[pre + 1])):
            if int(post[edge]) in target_set:
                rows.append(dict(csr_edge_index=edge, pre_body_id=int(ids[pre]),
                                 post_body_id=int(ids[post[edge]]), contacts=int(counts[edge])))
    return rows


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def csv_text(rows, fields):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def build(root=ROOT):
    brain = root / 'data/brain'
    names = ('ids', 'indptr', 'post', 'counts', 'signs')
    arrays = {name: np.load(brain / f'{name}.npy', mmap_mode='r', allow_pickle=False) for name in names}
    ids, ptr, post, counts = [arrays[k] for k in names[:4]]
    lock = json.loads((root / 'docs/connectome-source-lock.json').read_text())
    # Check original release bytes as well as derived array identities.
    for name, record in lock.items():
        path = root / 'data/raw' / name
        if path.stat().st_size != record['bytes'] or digest(path) != record['sha256']:
            raise ValueError(f'Locked source mismatch: {name}')
    n, raw = align_annotations(ids, feather.read_table(brain / 'nodes.feather').to_pandas(),
                               feather.read_table(root / 'data/raw/annotations.feather').to_pandas())
    manifest = json.loads((brain / 'manifest.json').read_text())
    if (len(ptr) != len(ids) + 1 or ptr[0] != 0 or ptr[-1] != len(post)
            or len(post) != len(counts) or np.any(np.diff(ptr) < 0)
            or np.any(post < 0) or np.any(post >= len(ids)) or np.any(counts < 1)
            or len(ids) != manifest['stats']['neurons']
            or len(post) != manifest['stats']['edges']
            or int(counts.sum(dtype=np.uint64)) != manifest['stats']['contacts']):
        raise ValueError('Derived graph accounting mismatch.')
    gustatory = n['class'].eq('gustatory')
    labellar = gustatory & (raw.subclass.eq('labellar bristle') | raw['type'].str.startswith('LB', na=False))
    selected = labellar | n['type'].isin(CANDIDATES) | n['type'].isin([*PN_TYPES.values(), 'MN9'])
    fields = ['body_id', 'graph_index', 'type', 'class', 'superclass', 'instance', 'root_side',
              'soma_side', 'entry_nerve', 'exit_nerve', 'subclass', 'receptor_type_annotation',
              'flywire_type_annotation', 'status_label', 'transmitter', 'candidate_receptor',
              'candidate_sensillum_neuron', 'benton_ev1_row', 'binding_status']
    rows = []
    for i in np.flatnonzero(selected):
        a, b = n.iloc[i], raw.iloc[i]
        def value(column):
            item = b[column]
            return '' if item is None or (isinstance(item, float) and np.isnan(item)) else str(item)
        receptor, sensillum, source_row = CANDIDATES.get(a['type'], ('', '', ''))
        rows.append(dict(zip(fields, [int(ids[i]), int(i), value('type'), value('class'),
            value('superclass'), value('instance'), value('rootSide'), value('somaSide'),
            value('entryNerve'), value('exitNerve'), value('subclass'), value('receptorType'),
            value('flywireType'), value('statusLabel'), str(a.transmitter), receptor, sensillum,
            source_row, 'anatomy_candidate_only_not_a_calibrated_stimulus'])))
    populations = {}
    for name in CANDIDATES:
        mask = n['type'].eq(name)
        populations[name] = dict(body_ids=ids[mask].tolist(), cells=int(mask.sum()),
            root_side_counts=raw.loc[mask, 'rootSide'].fillna('missing').value_counts().sort_index().to_dict())
    pairs, pathways = [], {}
    for orn, pn in PN_TYPES.items():
        sources = np.flatnonzero(n['type'].eq(orn))
        targets = np.flatnonzero(n['type'].eq(pn) & n['class'].eq('ALPN'))
        found = direct_pairs(ids, ptr, post, counts, sources, targets)
        pairs.extend(dict(route=f'{orn}->{pn}', **row) for row in found)
        pathways[orn] = dict(candidate_output_type=pn, output_body_ids=ids[targets].tolist(),
            directed_pairs=len(found), contacts=sum(row['contacts'] for row in found),
            input_cells_with_direct_contact=len({row['pre_body_id'] for row in found}),
            interpretation='anatomical transmission support, not observed activity or valence')
    g = raw.loc[gustatory]
    groups = []
    for key, group in g.groupby(['type', 'subclass', 'receptorType'], dropna=False, observed=True):
        groups.append(dict(type='' if key[0] != key[0] else key[0],
            subclass='' if key[1] != key[1] else key[1],
            receptor_type='' if key[2] != key[2] else key[2], cells=len(group)))
    report = dict(schema_version=1, stage='anatomical_crosswalk_rate_contract_unresolved',
        neural_calls=0, dataset=manifest['dataset'], source_lock=lock,
        graph=dict(neurons=len(ids), directed_pairs=len(post), contacts=int(counts.sum(dtype=np.uint64))),
        hashes={str(path.relative_to(root)): digest(path) for path in
            [*[brain / f'{name}.npy' for name in names], brain / 'nodes.feather',
             root / 'docs/connectome-source-lock.json']},
        crosswalk_rows=len(rows), gustatory_cells=int(gustatory.sum()), labellar_candidates=int(labellar.sum()),
        labellar_receptor_annotations_present=int(raw.loc[labellar, 'receptorType'].notna().sum()),
        gustatory_groups=groups, odor_candidates=populations, direct_projection_support=pathways,
        feeding_output_candidates=ids[n['type'].eq('MN9')].tolist(),
        limitation='No gustatory functional subtype assigned; no physiological rate schedule or valence readout approved.')
    return {'crosswalk.csv': csv_text(rows, fields),
            'projection-edges.csv': csv_text(pairs, ['route', 'csr_edge_index', 'pre_body_id', 'post_body_id', 'contacts']),
            'anatomy.json': json.dumps(report, indent=2, sort_keys=True) + '\n'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    artifacts = build(args.root)
    if args.check:
        for name, content in artifacts.items():
            if (args.output / name).read_bytes() != content.encode():
                raise SystemExit(f'Artifact differs: {name}')
        print('Sensory crosswalk reproduced exactly; zero neural calls.')
        return
    if any((args.output / name).exists() for name in artifacts):
        raise SystemExit('Refusing to overwrite existing evidence; use --check or a new output directory.')
    args.output.mkdir(parents=True, exist_ok=True)
    for name, content in artifacts.items():
        (args.output / name).write_text(content)
    print('Exported candidate anatomy only; no calibrated stimulus and zero neural calls.')


if __name__ == '__main__':
    main()
