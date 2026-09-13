"""Read retained pair contacts only; no simulator imports or coupling inference."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather

root = Path(__file__).resolve().parents[3]
brain = root / 'data/brain'
ids, ptr, post, counts = [np.load(brain / f'{x}.npy', mmap_mode='r')
                          for x in ('ids', 'indptr', 'post', 'counts')]
ann = feather.read_table(root / 'data/raw/annotations.feather').to_pandas().set_index('bodyId')
ann = ann.astype(object).where(pd.notna(ann), None)
atlas = pd.read_csv(root / 'wiki/cells/data/reward-edges.csv')
index = {int(body): i for i, body in enumerate(ids)}
rows = []
for channel, typ in [('home', 'PPL101'), ('away', 'PAM12')]:
    edges = atlas[(atlas.channel == channel) & (atlas.repair_gamma_eligible == 1)]
    kc_ids = set(map(int, edges.pre_body_id))
    mb_ids = set(map(int, edges.post_body_id))
    union, all_sets = set(), []
    for body in ann[ann['type'] == typ].index:
        pre = index[int(body)]
        start, end = int(ptr[pre]), int(ptr[pre + 1])
        target_ids = ids[post[start:end]]
        contacts = counts[start:end]
        kc_contact = {int(x): int(c) for x, c in zip(target_ids, contacts) if int(x) in kc_ids}
        mbon_contact = {str(int(x)): int(c) for x, c in zip(target_ids, contacts) if int(x) in mb_ids}
        union.update(kc_contact)
        all_sets.append(set(kc_contact))
        by_family = {}
        for kc, count in kc_contact.items():
            family = str(ann.loc[kc, 'type'])
            by_family[family] = by_family.get(family, 0) + count
        rows.append(dict(channel=channel, body_id=int(body), instance=ann.loc[body, 'instance'],
                         soma_side=ann.loc[body, 'somaSide'], root_side=ann.loc[body, 'rootSide'],
                         receptor_type=ann.loc[body, 'receptorType'],
                         eligible_kcs_with_direct_pair_contact=len(kc_contact),
                         direct_contacts_to_eligible_kcs=sum(kc_contact.values()),
                         direct_contacts_to_selected_mbons=mbon_contact,
                         kc_type_contact_counts=by_family))
    rows.append(dict(channel=channel, union_summary=True, eligible_kcs=len(kc_ids),
                     directly_contacted_by_any_selected_dan=len(union),
                     directly_contacted_by_all_selected_dans=len(set.intersection(*all_sets)),
                     uncontacted_by_selected_dans=len(kc_ids - union)))

# Independently align all outgoing retained pairs against the original release,
# including non-KC targets. This catches a body-index or direction mistake.
dan_ids = [r['body_id'] for r in rows if 'body_id' in r]
raw_path = root / 'data/raw/connectome-weights.feather'
raw = feather.read_table(raw_path)
raw = raw.filter(pc.is_in(raw['body_pre'], value_set=pa.array(dan_ids, type=raw['body_pre'].type)))
observed = {(int(a), int(b)): int(w) for a, b, w in zip(*[raw[x].to_pylist()
             for x in ('body_pre', 'body_post', 'weight')]) if int(b) in index}
expected = {}
for body in dan_ids:
    pre = index[body]
    for edge in range(int(ptr[pre]), int(ptr[pre + 1])):
        expected[(body, int(ids[post[edge]]))] = int(counts[edge])
assert expected == observed, 'Retained directed pairs do not match original source.'

paths = [brain / f'{x}.npy' for x in ('ids', 'indptr', 'post', 'counts')]
paths += [root / 'data/raw/annotations.feather', root / 'wiki/cells/data/reward-edges.csv']
paths.append(raw_path)
receipt = dict(scope='Pair contact audit only; no synaptic location or physiological coupling inferred.',
               original_source_pair_check=dict(passed=True, pairs=len(expected), selected_dans=len(dan_ids)),
               inputs={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
               rows=rows)
destination = Path(__file__).with_name('dan-contact-scope-resumed.json')
destination.write_text(json.dumps(receipt, indent=2, default=str) + '\n')
for row in rows:
    print(json.dumps({k: v for k, v in row.items() if k != 'kc_type_contact_counts'}, default=str))
