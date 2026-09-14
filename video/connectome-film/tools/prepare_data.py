"""Create a deterministic display sample of actual soma positions. No simulation."""
from pathlib import Path
import json, hashlib
import numpy as np
import pyarrow.feather as feather
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[1]
p=REPO/'data/brain/nodes.feather'
df=feather.read_table(p).to_pandas()
mask=df.somaLocation.map(lambda x:x is not None and len(x)==3)
s=df[mask].sample(n=min(5500,int(mask.sum())),random_state=36).sort_values('bodyId')
xyz=np.vstack(s.somaLocation).astype(float)
# Actual X and Z form the frontal projection; Y supplies depth.
xyz=xyz[:,[0,2,1]];center=(np.percentile(xyz,1,axis=0)+np.percentile(xyz,99,axis=0))/2
xyz=(xyz-center);scale=np.max(np.percentile(xyz,99,axis=0)-np.percentile(xyz,1,axis=0));xyz/=scale
classes=s['class'].fillna(''); supers=s.superclass.fillna('')
groups=np.zeros(len(s),int);groups[supers.str.startswith('ol_')]=1;groups[classes=='KC']=2;groups[classes=='MBON']=3;groups[classes=='DAN']=4;groups[supers=='descending_neuron']=5
np.savez_compressed(ROOT/'assets/anatomy.npz',xyz=xyz.astype(np.float32),groups=groups.astype(np.int8),ids=s.bodyId.to_numpy())
(ROOT/'sources/anatomy.json').write_text(json.dumps({'source':'data/brain/nodes.feather','source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'display_sample':len(s),'sampling_seed':36,'projection':'X,Z with Y depth; rotation is camera motion only','activity':'none'},indent=2)+'\n')
print('Exported',len(s),'actual soma coordinates')
