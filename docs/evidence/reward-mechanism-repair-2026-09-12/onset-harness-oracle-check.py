"""Bounded signal-only comparison; imports output-local harness, never native/circuit."""
from pathlib import Path
import importlib.util
import hashlib
import json
import numpy as np
P=Path(__file__).parent

def load(name,file):
 s=importlib.util.spec_from_file_location(name,P/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=load('onset_harness','onset_history_capture.py');r=load('onset_ref','onset-reference-audit.py')
checks=[]
for name,(ke,de) in r.CASES.items():
 nd=22 if name=='partial_population' else 2
 k=np.zeros((2000,1),np.uint8);d=np.zeros((2000,nd),np.uint8)
 for t,mass in ke:
  assert mass==1;k[round(t/.2),0]=1
 for t,mass in de:
  count=round(mass*nd);assert np.isclose(count/nd,mass);d[round(t/.2),:count]=1
 for history,warm in [('cold',False),('continuous',True)]:
  actual=h.shadow(k,d,np.array([0]),np.array([0]),np.zeros(nd,int),np.ones(1,np.uint8),np.array([0]),history=history)
  expected=r.reference(ke,de,warm=warm)
  np.testing.assert_array_equal(actual['gains'],np.array([expected['final_published']],np.float32))
  np.testing.assert_allclose(actual['onset_kc'][0],expected['onset_kc'],rtol=1e-11,atol=1e-13)
  np.testing.assert_allclose(actual['onset_dan'][0],expected['onset_dan'],rtol=1e-11,atol=1e-13)
  np.testing.assert_allclose(actual['edge_phases'][:3,0,:3].sum(0),[*expected['true_areas'],expected['interval_attempted']],rtol=1e-8,atol=1e-10)
  np.testing.assert_allclose(actual['edge_phases'][3,0,:3],[*expected['tail_true_areas'],expected['tail_attempted']],rtol=1e-8,atol=1e-10)
  checks.append({'case':name,'history':history,'passed':True})
# Dense signal-only stress with multiple reversals; actual rasters remain binary.
k=np.zeros((2000,1),np.uint8);d=k.copy()
ke=[(t,1.) for t in [0.,20.,220.,230.,390.]];de=[(t,1.) for t in [80.,90.,150.,300.,310.]]
for t,_ in ke:k[round(t/.2),0]=1
for t,_ in de:d[round(t/.2),0]=1
a=h.shadow(k,d,np.array([0]),np.array([0]),np.array([0]),np.ones(1,np.uint8),np.array([0]),history='continuous',eta=100.)
e=r.reference(ke,de,warm=True,scale=100./r.ETA)
np.testing.assert_array_equal(a['gains'],np.array([e['final_published']],np.float32))
np.testing.assert_allclose(a['edge_phases'][:3,0,:5].sum(0),[*e['true_areas'],e['interval_attempted'],e['interval_double_applied'],e['interval_published']],rtol=1e-8,atol=1e-10)
np.testing.assert_allclose(a['edge_phases'][3,0,:5],[*e['tail_true_areas'],e['tail_attempted'],e['tail_double_applied'],e['tail_published']],rtol=1e-8,atol=1e-10)
np.testing.assert_array_equal(a['edge_phases'][:3,0,5:7].sum(0),e['interval_bounds'])
np.testing.assert_array_equal(a['edge_phases'][3,0,5:7],e['tail_bounds'])
checks.append({'case':'binary_dense_clip_reversal','history':'continuous','passed':True})
result={'scope':'signal-only harness audit; no circuit or production import','harness_sha256':hashlib.sha256((P/'onset_history_capture.py').read_bytes()).hexdigest(),'reference_sha256':hashlib.sha256((P/'onset-reference-audit.py').read_bytes()).hexdigest(),'checks':checks}
Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'passed':True,'harness_sha256':result['harness_sha256']}))
