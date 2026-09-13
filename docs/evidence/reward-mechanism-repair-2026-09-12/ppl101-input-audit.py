"""Pinned retained-graph input enumeration; no simulator imports or neural calls."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import pyarrow.feather as feather

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).parent

def digest(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

s=json.loads((ROOT/'output/diagnostics/diag-rate-bridge-v1-maskgamma-dea14759e9ca/summary.json').read_text())
protocol=s['identity']['protocol'];checked={}
for path,expected in s['identity']['graph_hashes'].items():
 actual=digest(ROOT/path);assert actual==expected,path;checked[path]=actual
for name in ('reward_protocol.py','reward_encoder.py'):
 actual=digest(ROOT/'bet36fly'/name);assert actual==s['identity']['code_hashes'][name];checked['bet36fly/'+name]=actual
lock=json.loads((ROOT/'docs/connectome-source-lock.json').read_text())
assert lock==json.loads((ROOT/'data/brain/source-lock.json').read_text())
assert digest(ROOT/'data/raw/annotations.feather')==lock['annotations.feather']['sha256']
arrays={k:np.load(ROOT/f'data/brain/{k}.npy',mmap_mode='r') for k in ('ids','indptr','post','counts','signs','kc','mbon','sensory')}
ids,ptr,post,contacts,signs=[arrays[k] for k in ('ids','indptr','post','counts','signs')]
nodes=feather.read_table(ROOT/'data/brain/nodes.feather').to_pandas().set_index('bodyId').reindex(ids)
raw=feather.read_table(ROOT/'data/raw/annotations.feather',columns=['bodyId','instance','type','class','superclass']).to_pandas().set_index('bodyId').reindex(ids)
assert not nodes.index.duplicated().any() and not raw.index.duplicated().any()
target_ids=[11327,11900];targets=np.array([np.flatnonzero(ids==i).item() for i in target_ids])
assert not np.isin(targets,arrays['kc']).any() and not np.isin(targets,arrays['sensory']).any()
assert nodes.iloc[targets]['type'].tolist()==['PPL101','PPL101']
chosen=np.flatnonzero(np.isin(post,targets));pre=np.searchsorted(ptr,chosen,side='right')-1
rows=[]
sets={r:set(arrays[r].tolist()) for r in ('kc','mbon','sensory')}
for edge,i in zip(chosen,pre):
 j=int(post[edge]);row=nodes.iloc[i];nt='' if pd.isna(row.transmitter) else str(row.transmitter)
 tokens={t.strip() for t in nt.lower().split(',')};fast=({1} if 'acetylcholine' in tokens else set())|({-1} if tokens & {'gaba','glutamate','histamine'} else set())
 expected_sign=next(iter(fast)) if len(fast)==1 else 1
 assert int(signs[i])==expected_sign
 is_apl=str(row['type'])=='APL' and nt=='gaba';zero=nt=='dopamine'
 gain=float(protocol['apl_output_gain']) if is_apl else 1.
 base=np.float32(np.float32(contacts[edge])*np.float32(signs[i])*np.float32(.275*protocol['global_weight_scale']))
 modeled=np.float32(0.) if zero else np.float32(base*np.float32(gain))
 rows.append(dict(target_body_id=int(ids[j]),target_index=j,target_instance=str(raw.iloc[j]['instance']),
  pre_body_id=int(ids[i]),pre_index=int(i),pre_class=str(row['class']),pre_type=str(row['type']),pre_superclass=str(row['superclass']),pre_instance=str(raw.iloc[i]['instance']),
  transmitter=nt,modeled_fast_sign=int(signs[i]),ambiguous_fast_sign=len(fast)!=1,contacts=int(contacts[edge]),edge_index=int(edge),
  global_scale=float(protocol['global_weight_scale']),base_per_contact_scale=.275,post_gain=1.,apl_output_gain=gain,dopamine_fast_zeroed=zero,plastic_gain=1.,
  modeled_conductance_increment=float(modeled),is_kc=int(i) in sets['kc'],is_mbon=int(i) in sets['mbon'],is_sensory_port=int(i) in sets['sensory'],is_apl=is_apl))
f=pd.DataFrame(rows);assert len(f)==len(chosen) and not f[['target_body_id','pre_body_id']].duplicated().any()
def group(cols):
 return f.groupby(cols,dropna=False).agg(edges=('contacts','size'),contacts=('contacts','sum'),modeled_signed_increment_sum=('modeled_conductance_increment','sum')).reset_index().to_dict('records')
result=dict(scope='All direct incoming retained neuronal graph edges to selected PPL101 cells; not all raw edges incident to excluded fragments/glia.',source_release='MaleCNS v1.0',source_lock=lock,hashes_checked=checked,
 protocol={k:protocol[k] for k in ('global_weight_scale','kc_input_gain','sensory_input_gain','apl_output_gain','learning_rate','tau_ms','rate_tau_ms','learning_rule','away_plasticity_mask')},
 targets=[dict(body_id=int(ids[j]),index=int(j),instance=str(raw.iloc[j]['instance']),incoming_edges=int((f.target_index==j).sum()),incoming_contacts=int(f.loc[f.target_index==j,'contacts'].sum())) for j in targets],
 by_target_class=group(['target_body_id','pre_class']),by_target_transmitter=group(['target_body_id','transmitter','modeled_fast_sign','dopamine_fast_zeroed']),
 by_target_type=group(['target_body_id','pre_type']),
 roles={role:f.loc[f[role]].groupby('target_body_id').agg(edges=('contacts','size'),contacts=('contacts','sum'),signed_increment_sum=('modeled_conductance_increment','sum')).reset_index().to_dict('records') for role in ('is_kc','is_mbon','is_sensory_port','is_apl')},
 top20_per_target={str(t):f[f.target_body_id==t].sort_values(['contacts','pre_body_id'],ascending=[False,True]).head(20).to_dict('records') for t in target_ids},
 counts=dict(edges=len(f),unique_presynaptic_cells=f.pre_body_id.nunique(),contacts=int(f.contacts.sum()),ambiguous_sign_edges=int(f.ambiguous_fast_sign.sum()),dopamine_zeroed_contacts=int(f.loc[f.dopamine_fast_zeroed,'contacts'].sum())),
 caveat='Signed increment sums assume one simultaneous presynaptic event per listed edge with a nonrefractory target. They are not measured currents, activity, causal contribution or biological receptor effects.')
f.to_csv(OUT/'ppl101-direct-inputs.csv',index=False)
(OUT/'ppl101-input-audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:result[k] for k in ('targets','counts','roles','by_target_class','by_target_transmitter')},indent=2))
