"""Frozen, output-local history capture and offline shadow. Never a production rule."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
import subprocess
import sys
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).parent
CONTRACT=ROOT/'docs/evidence/reward-mechanism-repair-2026-09-12/onset-history-investigation-preregistration.md'
CONTRACT_SHA='ca01c345c6c28ba2879b7cf05a6d1b2b802392f0067862e701a69da5778a5ad5'
RUNS=('diag-rate-bridge-v1-maskgamma-de050d773763','diag-rate-bridge-v1-maskgamma-dea14759e9ca')
PHASES=((100.,130.),(130.,300.),(300.,400.),(400.,math.inf))
FIELDS=('positive_integral','negative_integral','attempted','double_applied','published_applied','bound_low','bound_high','q_used')


def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def array_identity(a):
 return dict(dtype=str(a.dtype),shape=list(a.shape),sha256=hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest())


def atomic_json(path,value):
 path=Path(path);tmp=path.with_suffix(path.suffix+'.partial');tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def validate_events(kc,dan,dcomp,history):
 kc,dan=np.asarray(kc),np.asarray(dan);dc=np.asarray(dcomp)
 if (history not in ('cold','continuous') or kc.ndim!=2 or dan.ndim!=2 or kc.shape[0]!=2000 or dan.shape[0]!=2000
     or min(kc.shape[1],dan.shape[1])<1 or kc.dtype.kind not in 'iub' or dan.dtype.kind not in 'iub'
     or not np.isin(kc,[0,1]).all() or not np.isin(dan,[0,1]).all() or dc.shape!=(dan.shape[1],)
     or dc.dtype.kind not in 'iu' or np.any(dc<0) or set(dc.tolist())!=set(range(int(dc.max())+1))):
  raise ValueError('Expected lossless binary2000-step KC/DAN rasters, contiguous represented compartments, and explicit history.')
 return kc,dan,dc


def shadow(kc,dan,pk,pc,dcomp,mask,groups,*,history='cold',eta=.0005,initial=None):
 """Double signal/gain operator; no neuron state or callback to the native engine."""
 kc,dan,dc=validate_events(kc,dan,dcomp,history);pk=np.asarray(pk);pc=np.asarray(pc);groups=np.asarray(groups);mask=np.asarray(mask)
 nc=int(dc.max())+1;nk=kc.shape[1];ne=len(pk)
 if (any(a.shape!=(ne,) or a.dtype.kind not in 'iu' for a in (pk,pc,groups)) or mask.shape!=(ne,) or not np.isin(mask,[0,1]).all()
     or np.any(pk<0) or np.any(pk>=nk) or np.any(pc<0) or np.any(pc>=nc) or np.any(groups<0) or np.any(groups>=8)
     or mask.dtype.kind not in 'iub' or isinstance(eta,(bool,np.bool_)) or not math.isfinite(eta) or eta<0):raise ValueError('Invalid shadow edge mapping or eta.')
 mask=mask.astype(bool);gain=np.ones(ne,float) if initial is None else np.asarray(initial,dtype=np.float32).astype(float)
 if gain.shape!=(ne,) or not np.isfinite(gain).all() or np.any(gain<.5) or np.any(gain>1.5):raise ValueError('Invalid initial gains.')
 initial_gain=gain.copy();published=gain.astype(np.float32);initial_publication=published.copy();rk=np.zeros(nk);ek=np.zeros(nk);rd=np.zeros(nc);ed=np.zeros(nc)
 phase=np.zeros((4,ne,8));h=.2;r=.01;e=.002;ar=math.exp(-r*h);ae=math.exp(-e*h);b=r+e
 A=-math.expm1(-b*h)/b;C=(-math.expm1(-2*r*h)/(2*r)-A)/(e-r);coupling=ae*math.expm1((e-r)*h)/(e-r)
 dmean=np.column_stack([dan[:,dc==c].sum(1)/np.count_nonzero(dc==c) for c in range(nc)])
 onset_kc=onset_dan=onset_gains=onset_double_gains=None
 def update(p,a,c):
  nonlocal gain,published
  q=ed[pc]*rk[pk]-ek[pk]*rd[pc];common=c*rd[pc]*rk[pk]
  delta=eta*.96*a*q;delta[~mask]=0
  before=gain;fp=published.astype(float);proposed=before+delta;gain=np.clip(proposed,.5,1.5);published=gain.astype(np.float32)
  values=np.column_stack((eta*.96*(a*ed[pc]*rk[pk]+common),-eta*.96*(a*ek[pk]*rd[pc]+common),delta,gain-before,published.astype(float)-fp,((proposed<=.5)|(published<=.5)).astype(float),((proposed>=1.5)|(published>=1.5)).astype(float),q))
  values[~mask]=0;phase[p]+=values
 for t in range(2000):
  if t==500:
   onset_kc=np.column_stack((rk,ek));onset_dan=np.column_stack((rd,ed));onset_gains=published.copy();onset_double_gains=gain.copy()
  if history=='cold' and t<500:continue
  rk+=kc[t]*r;rd+=dmean[t]*r
  if t>=500:update(0 if t<650 else 1 if t<1500 else 2,A,C)
  ek=ae*ek+coupling*rk;rk*=ar;ed=ae*ed+coupling*rd;rd*=ar
 endpoint_kc=np.column_stack((rk,ek));endpoint_dan=np.column_stack((rd,ed));update(3,1/b,1/(2*r*b))
 grouped=np.zeros((4,8,8))
 for p in range(4):
  for f in range(8):grouped[p,:,f]=np.bincount(groups,weights=phase[p,:,f],minlength=8)
 return dict(gains=published,edge_phases=phase,group_phases=grouped,onset_kc=onset_kc,onset_dan=onset_dan,endpoint_kc=endpoint_kc,endpoint_dan=endpoint_dan,onset_gains=onset_gains,onset_double_gains=onset_double_gains,
             pre_onset_published_changes=float(np.abs(onset_gains.astype(float)-initial_publication.astype(float)).sum()),
             pre_onset_double_changes=float(np.abs(onset_double_gains-initial_gain).sum()))


def pair_integrals(kc,dan,dcomp,*,history='cold',eta=.0005):
 """Independent closed pair contribution to each interval; no R/E recurrence."""
 kc,dan,dc=validate_events(kc,dan,dcomp,history);nc=int(dc.max())+1
 times=np.arange(2000)*.2;include=np.ones(2000,bool) if history=='continuous' else times>=100
 ke=kc.astype(float).copy();ke[~include]=0;out=np.zeros((4,kc.shape[1],nc))
 for c in range(nc):
  dm=dan[:,dc==c].sum(1)/np.count_nonzero(dc==c);dt=times[(dm>0)&include];amp=dm[(dm>0)&include]
  lag=dt[None,:]-times[:,None];last=np.maximum(dt[None,:],times[:,None]);magnitude=-eta*np.sign(lag)*(np.exp(-abs(lag)/500)-np.exp(-abs(lag)/100))*amp
  for p,(lo,hi) in enumerate(PHASES):
   lo_tail=np.exp(-.012*np.maximum(0,lo-last));hi_tail=np.zeros_like(last) if math.isinf(hi) else np.exp(-.012*np.maximum(0,hi-last))
   potential=(magnitude*(lo_tail-hi_tail)).sum(1)
   out[p,:,c]=ke.T@potential
 return out


def compare_coarse_fine(coarse,fine):
 for key,value in coarse.items():
  if not isinstance(value,np.ndarray):continue
  other=fine[key]
  if key in ('trace','population'):
   assert other.shape[0]==value.shape[0]*50
   other=other.reshape((len(value),50)+other.shape[1:]).sum(1,dtype=np.int64)
  np.testing.assert_array_equal(value,other,err_msg=f'coarse/fine {key}')
 for key in ('duration_ms','dt'):assert coarse[key]==fine[key]


def capture_sequence(rows,run,parity,retained,save,guard):
 if len(rows)!=32:raise ValueError('Exactly32 frozen fine calls required.')
 guard();coarse=run(rows[0],False);save('coarse',coarse);guard();retained(rows[0],coarse,False)
 for i,row in enumerate(rows):
  guard();fine=run(row,True);save(f'fine_{i:02d}',fine);guard()
  if i==0:parity(coarse,fine)
  retained(row,fine,True)
 return 33


def validate_selection(rows):
 cues=((4362,4366,4370,4374,4378,4383,4387,4391),(4395,4399,4404,4408,4412,4416,4420,4425))
 expected=[dict(game=g,seed_set=ss,seed=g+42+panel*2000000+extra,run_id=RUNS[panel])
           for panel,values in enumerate(cues) for g in values for ss,extra in [('base',0),('alt',1000000)]]
 if (rows!=expected or any(type(r.get(k)) is not int for r in rows for k in ('game','seed'))):raise ValueError('Exact frozen32-row cue/noise/seed/order differs.')


def frozen_context():
 """Read/hash source-locked maps and prior evidence; never build a circuit."""
 assert sha(CONTRACT)==CONTRACT_SHA,'Frozen scientific contract changed'
 summaries=[json.loads((ROOT/'output/diagnostics'/rid/'summary.json').read_text()) for rid in RUNS]
 original=summaries[0];protocol=original['identity']['protocol']
 fixed={'learning_rule':'rate-bridge-v1','dan_reference':'none','plasticity_onset_ms':100.,'duration_ms':400.,'stimulus_ms':300.,'bin_ms':10.,'tau_ms':500.,'rate_tau_ms':100.,'learning_rate':.0005,'bridge_normalization':.96,'gain_bounds':[.5,1.5],'away_plasticity_mask':'gamma','global_weight_scale':.5,'kc_input_gain':1.25,'apl_output_gain':.25,'sensory_input_gain':0.}
 for key,value in fixed.items():assert protocol[key]==value,key
 rows=[];prior={}
 for rid,s in zip(RUNS,summaries):
  assert s['run_id']==rid and s['source_unchanged_during_run'] and s['panel_complete']
  for key in ('protocol','code_hashes','graph_hashes','inputs_sha256','pilot_manifest_sha256','pilot_protocol_sha256'):
   assert s['identity'][key]==original['identity'][key]
  p=ROOT/'output/diagnostics'/rid
  prior[rid]={'summary_sha256':sha(p/'summary.json'),'artifacts':s['artifacts']}
  for name,meta in s['artifacts'].items():assert sha(p/name)==meta['sha256'] and (p/name).stat().st_size==meta['bytes']
  selected=[{k:r[k] for k in ('game','seed_set','seed')} for r in s['rows'] if r['condition']=='untaught']
  expected=[{k:r[k] for k in ('game','seed_set','seed')} for r in s['identity']['selection']['expected_panel'] if r['condition']=='untaught']
  assert selected==expected and len(selected)==16 and len({(r['game'],r['seed_set']) for r in selected})==16
  rows.extend([dict(r,run_id=rid) for r in selected])
 validate_selection(rows)
 code=original['identity']['code_hashes']
 for name,digest in code.items():assert sha(ROOT/('scripts' if name=='reward_teaching_diagnostic.py' else 'bet36fly')/name)==digest
 for path,digest in original['identity']['graph_hashes'].items():assert sha(ROOT/path)==digest
 native=original['native_binary'];assert sha(native['path'])==native['sha256']
 pilot=ROOT/'output/experiments'/original['identity']['pilot']
 for name,key in [('source/inputs.npz','inputs_sha256'),('manifest.json','pilot_manifest_sha256'),('source/protocol.json','pilot_protocol_sha256')]:assert sha(pilot/name)==original['identity'][key]
 kc=np.load(ROOT/'data/brain/kc.npy').astype(np.int32);sensory=np.load(ROOT/'data/brain/sensory.npy').astype(np.int32);ids=np.load(ROOT/'data/brain/ids.npy')
 with np.load(ROOT/'output/diagnostics'/RUNS[0]/'trials.npz') as z:
  dc=z['dan_compartments'];sampled=z['sampled'];no=len(sampled)-len(kc)-len(sensory)-len(dc)
  assert no>0;dan=sampled[no:no+len(dc)].astype(np.int32)
  np.testing.assert_array_equal(sampled[no+len(dc):no+len(dc)+len(kc)],kc);np.testing.assert_array_equal(sampled[-len(sensory):],sensory)
  maps={name:z[name].copy() for name in ('plastic_kc_indices','plastic_compartments','plastic_mask','plastic_groups')}
 sample=np.unique(np.concatenate((kc,dan,sensory))).astype(np.int32)
 maps.update(sample=sample,body_ids=ids[sample],kc_indices=kc,dan_indices=dan,sensory_indices=sensory,dan_compartments=dc)
 for role,indices in [('kc',kc),('dan',dan),('sensory',sensory)]:
  assert len(np.unique(indices))==len(indices)
  maps[role+'_columns']=np.searchsorted(sample,indices).astype(np.int32)
  np.testing.assert_array_equal(sample[maps[role+'_columns']],indices)
 overlap={a+'/'+b:np.intersect1d(maps[a+'_indices'],maps[b+'_indices']).astype(int).tolist() for a,b in [('kc','dan'),('kc','sensory'),('dan','sensory')]}
 identity=dict(contract_sha256=CONTRACT_SHA,source_code=code,graph_hashes=original['identity']['graph_hashes'],native_binary=native,
               protocol=protocol,pilot=str(pilot),inputs_sha256=original['identity']['inputs_sha256'],pilot_manifest_sha256=original['identity']['pilot_manifest_sha256'],
               pilot_protocol_sha256=original['identity']['pilot_protocol_sha256'],prior=prior,rows=rows,planned_calls=33,wall_seconds_cap=600,
               sample_arrays={k:array_identity(v) for k,v in maps.items()},role_overlaps=overlap,
               capture=dict(bin_ms=.2,electrical_dt=.2,coarse_bin_ms=10.,schedule_repeat=50,record=False,plasticity=True,pulses=[],unit_initial_gains=True,
                            raster_unit='actual binary spike events per .2ms interval; columns by stored global index'),
               shadow=dict(histories=['cold','continuous'],feedback=False,eta=.0005,tau_e_ms=500.,tau_r_ms=100.,normalization=.96,onset_ms=100.,endpoint_ms=400.,bounds=[.5,1.5],tail='analytic_no_new_event',fields=list(FIELDS)),
               runtime=dict(python=sys.version,numpy=np.__version__,platform=platform.platform()),
               independent_reference_sha256=sha(HERE/'onset-reference-audit.py'),
               harness_sha256=sha(__file__),tests_sha256=sha(HERE/'test_onset_history_capture.py'))
 return identity,maps


def freeze(receipt):
 identity,maps=frozen_context();run_id='onset-history-capture-'+hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:16]
 receipt=Path(receipt);sample_file=receipt.with_suffix('.samples.npz')
 if receipt.exists():
  existing=json.loads(receipt.read_text());assert existing['identity']==identity and existing['run_id']==run_id
  assert sha(sample_file)==existing['samples_sha256'];return existing
 if sample_file.exists():raise FileExistsError('Unpaired existing mapping file; preserve it and choose another receipt path.')
 receipt.parent.mkdir(parents=True,exist_ok=True)
 with sample_file.open('xb') as f:np.savez(f,**maps)
 document=dict(status='preregistered-not-captured',run_id=run_id,identity=identity,samples_path=str(sample_file.resolve()),samples_sha256=sha(sample_file),created_at=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
 with receipt.open('x') as f:json.dump(document,f,indent=2,allow_nan=False);f.write('\n')
 return document


def verify_receipt(receipt):
 frozen=json.loads(Path(receipt).read_text());identity,maps=frozen_context()
 assert frozen['status']=='preregistered-not-captured' and frozen['identity']==identity
 expected='onset-history-capture-'+hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:16]
 assert frozen['run_id']==expected and sha(frozen['samples_path'])==frozen['samples_sha256']
 with np.load(frozen['samples_path']) as z:
  assert set(z.files)==set(maps)
  for k,a in maps.items():np.testing.assert_array_equal(z[k],a)
 return frozen,maps


def retained_checks(row,result,fine,maps,summary,z):
 prefix=f"{row['game']}__{row['seed_set']}__untaught"
 np.testing.assert_array_equal(result['gains'],z[prefix+'__gains'])
 np.testing.assert_array_equal(result['gain_delta'],z[prefix+'__gain_delta'])
 trace=result['trace'];coarse=trace.reshape(40,50,trace.shape[1]).sum(1,dtype=np.int64) if fine else trace
 np.testing.assert_array_equal(coarse[:,maps['sensory_columns']],z[prefix+'__sensory_bins'])
 np.testing.assert_array_equal(coarse[:,maps['dan_columns']],z[prefix+'__dan_bins'])
 np.testing.assert_array_equal(result['dan_counts'],coarse[:,maps['dan_columns']].sum(0))
 if fine:
  np.testing.assert_array_equal(result['counts'][maps['sample']],trace.sum(0))
  assert trace.shape==(2000,len(maps['sample'])) and np.isin(trace,[0,1]).all()
  events=trace[:,maps['dan_columns']];dc=maps['dan_compartments'];actual=z[prefix+'__step_signals']
  for c in range(int(dc.max())+1):np.testing.assert_array_equal((events[:,dc==c].sum(1)/np.count_nonzero(dc==c)).astype(np.float32),actual[:,1+c])
  np.testing.assert_array_equal(trace[:,maps['kc_columns']].sum(1),actual[:,0])
 if row['game']==summary['panel_games'][0]:
  oldsample=z['sampled'];lookup={int(v):i for i,v in enumerate(oldsample)}
  np.testing.assert_array_equal(coarse,z[prefix+'__sampled_bins'][:,[lookup[int(v)] for v in maps['sample']]])
 if row['run_id']==RUNS[0] and row['game']==4362 and row['seed_set']=='base':
  replay=json.loads((ROOT/'output/diagnostics'/RUNS[0]/'replay-evidence.json').read_text())['untaught']['original']
  for key,a in result.items():
   if not isinstance(a,np.ndarray) or key=='trace':continue
   if key=='population' and fine:a=a.reshape(40,50).sum(1).astype(np.int32)
   expected=replay[key];assert expected==[str(a.dtype),list(a.shape),array_identity(a)['sha256']],key


def compare_cold_shadow(result,shadow_result,oracle,maps,z,prefix):
 np.testing.assert_array_equal(shadow_result['gains'],result['gains'])
 assert not shadow_result['edge_phases'][...,5:7].any(),'Cold canonical bound observation'
 pk,pc,mask=maps['plastic_kc_indices'],maps['plastic_compartments'],maps['plastic_mask'].astype(bool)
 expected=oracle[:,pk,pc];expected[:,~mask]=0
 np.testing.assert_allclose(shadow_result['edge_phases'][...,2],expected,rtol=1e-8,atol=1e-10)
 np.testing.assert_array_equal((1+expected.sum(0)).astype(np.float32),result['gains'])
 native=z[prefix+'__bridge_rule'];tail=z[prefix+'__bridge_tail']
 phases=np.stack([native[500:650].sum(0),native[650:1500].sum(0),native[1500:].sum(0),tail])
 # Same gain publications may occur at slightly different final rounding ties in
 # an independent algorithm; required final publications remain bit-identical.
 np.testing.assert_allclose(shadow_result['group_phases'][...,:4],phases[...,:4],rtol=1e-8,atol=1e-10)
 np.testing.assert_array_equal(shadow_result['group_phases'][...,5:7],phases[...,5:7])


def record_attempt(path,attempts,row,fine,schedule,elapsed):
 if len(attempts)>=33:raise ValueError('Capture attempt cap exceeded')
 attempts.append(dict(attempt=len(attempts)+1,row=row,fine=fine,bin_ms=.2 if fine else 10.,schedule=array_identity(schedule),started_monotonic_seconds=elapsed))
 atomic_json(path,dict(attempted_calls=len(attempts),attempts=attempts))


def run_worker(receipt,out,cancel_file=None):
 started=time.monotonic();frozen,maps=verify_receipt(receipt);identity=frozen['identity'];rows=identity['rows']
 out=Path(out);assert out.is_dir()
 def guard():
  if cancel_file and Path(cancel_file).exists():raise RuntimeError('Cancelled; partial capture preserved.')
  if time.monotonic()-started>=600:raise TimeoutError('600second cap; partial capture preserved.')
 sys.path.insert(0,str(ROOT))
 from bet36fly.reward_protocol import make_circuit
 pilot=Path(identity['pilot'])
 with np.load(pilot/'source/inputs.npz') as z:inputs={k:z[k] for k in z.files}
 engine,anatomy,outputs,dc,kc,sensory,encode=make_circuit(ROOT,identity['protocol'],n_features=inputs['X'].shape[1])
 for attr,key in [('kc_indices','kc_indices'),('dan_indices','dan_indices'),('sensory','sensory_indices'),('dan_compartments','dan_compartments'),('plastic_kc_indices','plastic_kc_indices'),('plastic_compartments','plastic_compartments'),('plastic_mask','plastic_mask')]:np.testing.assert_array_equal(getattr(engine,attr),maps[key])
 assert sha(engine.lib._name)==identity['native_binary']['sha256'];assert engine.learning_rule=='rate-bridge-v1' and engine.dan_reference=='none'
 summaries={rid:json.loads((ROOT/'output/diagnostics'/rid/'summary.json').read_text()) for rid in RUNS}
 archives={rid:np.load(ROOT/'output/diagnostics'/rid/'trials.npz',allow_pickle=False) for rid in RUNS}
 saved=[];analyses=[];attempts=[]
 def save(name,result):
  path=out/(name+'.npz');assert not path.exists()
  arrays={k:v for k,v in result.items() if isinstance(v,np.ndarray)}
  with path.open('xb') as f:np.savez_compressed(f,**arrays)
  metadata={k:v for k,v in result.items() if not isinstance(v,np.ndarray)}
  entry=dict(name=name,file=path.name,sha256=sha(path),bytes=path.stat().st_size,numeric_fingerprint={k:array_identity(v) for k,v in arrays.items()},metadata=metadata)
  saved.append(entry);atomic_json(out/'progress.json',dict(status='partial',completed_calls=len(saved),attempted_calls=len(attempts),saved=saved,wall_seconds=time.monotonic()-started))
 def run(row,fine):
  idx=np.flatnonzero(inputs['source_indices']==row['game']);assert len(idx)==1
  x=np.clip((inputs['X'][idx[0]]-inputs['input_mean'])/inputs['input_std'],-8,8)
  schedule=np.zeros((40,len(sensory)),np.float32);schedule[:30]=encode(x)
  if fine:schedule=np.repeat(schedule,50,axis=0)
  engine.gains[:]=1
  record_attempt(out/'attempts.json',attempts,row,fine,schedule,time.monotonic()-started)
  return engine.run(schedule,bin_ms=.2 if fine else 10.,seed=row['seed'],sample=maps['sample'],record=False,plasticity=True,teaching_pulses=())
 def retained(row,result,fine):
  z=archives[row['run_id']];retained_checks(row,result,fine,maps,summaries[row['run_id']],z)
  if not fine:return
  guard();events=result['trace'];ke=events[:,maps['kc_columns']];de=events[:,maps['dan_columns']]
  before={k:array_identity(v) for k,v in result.items() if isinstance(v,np.ndarray)}
  prefix=f"{row['game']}__{row['seed_set']}__untaught";trial_index=rows.index(row);effects={}
  for history in ('cold','continuous'):
   a=shadow(ke,de,maps['plastic_kc_indices'],maps['plastic_compartments'],maps['dan_compartments'],maps['plastic_mask'],maps['plastic_groups'],history=history)
   assert a['pre_onset_published_changes']==0 and a['pre_onset_double_changes']==0,'Pre-onset gain write'
   oracle=pair_integrals(ke,de,maps['dan_compartments'],history=history)
   if history=='cold':compare_cold_shadow(result,a,oracle,maps,z,prefix)
   expected=oracle[:,maps['plastic_kc_indices'],maps['plastic_compartments']];expected[:,maps['plastic_mask']==0]=0
   np.testing.assert_allclose(a['edge_phases'][...,2],expected,rtol=1e-8,atol=1e-10)
   arrays={k:v for k,v in a.items() if isinstance(v,np.ndarray)};arrays['independent_pair_attempted']=expected
   path=out/f'shadow_{trial_index:02d}_{history}.npz'
   with path.open('xb') as f:np.savez_compressed(f,**arrays)
   effects[history]=dict(file=path.name,sha256=sha(path),pre_onset_published_changes=a['pre_onset_published_changes'],pre_onset_double_changes=a['pre_onset_double_changes'],
    published=[float((a['gains'].astype(float)-1)[maps['plastic_compartments']==c].sum()) for c in range(2)],
    attempted=[float(a['edge_phases'][:,maps['plastic_compartments']==c,2].sum()) for c in range(2)],
    bounds=int(a['edge_phases'][...,5:7].sum()),group_phases=a['group_phases'].tolist())
  assert before=={k:array_identity(v) for k,v in result.items() if isinstance(v,np.ndarray)}
  np.testing.assert_array_equal(engine.gains,result['gains'])
  analyses.append(dict(row,effects=effects,actual_checkpoint_unchanged_by_shadow=True));atomic_json(out/'shadow-progress.json',analyses)
  guard()
 try:
  calls=capture_sequence(rows,run,compare_coarse_fine,retained,save,guard)
  current,_=frozen_context();assert current==identity,'Source or protected input changed during capture'
  metrics={}
  for rid in RUNS:
   for ss in ('base','alt'):
    selected=[r for r in analyses if r['run_id']==rid and r['seed_set']==ss];assert len(selected)==8
    for c in range(2):
     metrics[f'{rid}/{ss}/{c}']={}
     for history in ('cold','continuous'):
      values=np.array([r['effects'][history]['published'][c] for r in selected]);metrics[f'{rid}/{ss}/{c}'][history]=dict(mean=float(values.mean()),sd=float(values.std(ddof=1)),guard_limit=float(.5*values.std(ddof=1)),passed=bool(abs(values.mean())<=.5*values.std(ddof=1)))
  target=[r for r in analyses if r['run_id']==RUNS[1] and r['seed_set']=='base'];cu=np.array([r['effects']['cold']['published'][0] for r in target]);wu=np.array([r['effects']['continuous']['published'][0] for r in target])
  total_bounds=sum(r['effects']['continuous']['bounds'] for r in analyses)
  report=dict(status='complete',run_id=frozen['run_id'],calls=calls,attempted_calls=len(attempts),identity=identity,saved=saved,rows=analyses,metrics=metrics,
              directional_support=bool((wu-cu).mean()>0 and abs(wu.mean())<abs(cu.mean())),
              mean_warm_minus_cold=float((wu-cu).mean()),attempted_warm_minus_cold=float(np.mean([r['effects']['continuous']['attempted'][0]-r['effects']['cold']['attempted'][0] for r in target])),
              continuous_bound_observations=total_bounds,necessary_shadow_screen=bool(total_bounds==0 and all(v['continuous']['passed'] for v in metrics.values())),
              qualification=False,note='Fixed-history shadow only; altered gains never drive neurons. A shadow pass is not circuit qualification.',wall_seconds=time.monotonic()-started)
  atomic_json(out/'summary.json',report)
 except BaseException as exc:
  atomic_json(out/'failure.json',dict(status='failed-partial-preserved',error=repr(exc),completed_calls=len(saved),attempted_calls=len(attempts),wall_seconds=time.monotonic()-started));raise
 finally:
  for z in archives.values():z.close()


def supervise(command,out,*,cancel_file=None,timeout=600.,popen=subprocess.Popen,clock=time.monotonic):
 """External process deadline interrupts an in-flight native call, not just Python boundaries."""
 started=clock();proc=popen(command)
 try:
  while True:
   remaining=timeout-(clock()-started)
   if remaining<=0 or cancel_file and Path(cancel_file).exists():
    reason='deadline' if remaining<=0 else 'cancelled'
    proc.terminate()
    try:proc.wait(timeout=1.)
    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=1.)
    atomic_json(Path(out)/'supervisor-stop.json',dict(status='partial-preserved',reason=reason,wall_seconds=clock()-started))
    raise RuntimeError(reason)
   try:
    code=proc.wait(timeout=min(.2,remaining))
    if code:raise RuntimeError(f'Capture worker exited{code}; partial artifacts preserved')
    return
   except subprocess.TimeoutExpired:pass
 finally:
  if proc.poll() is None:proc.kill();proc.wait(timeout=1.)


def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--freeze-only',action='store_true');p.add_argument('--out',type=Path,default=HERE/'onset-history-captures');p.add_argument('--cancel-file',type=Path);p.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
 a=p.parse_args(argv)
 if a.freeze_only:
  assert not a.worker;f=freeze(a.receipt);print(json.dumps(dict(run_id=f['run_id'],status=f['status'],receipt=str(a.receipt),samples=f['samples_path'])));return
 if a.worker:run_worker(a.receipt,a.out,a.cancel_file);return
 frozen,_=verify_receipt(a.receipt);out=a.out/frozen['run_id'];out.mkdir(parents=True,exist_ok=False)
 atomic_json(out/'capture-receipt.json',frozen)
 cmd=[sys.executable,str(Path(__file__).resolve()),'--receipt',str(a.receipt.resolve()),'--out',str(out.resolve()),'--worker']
 if a.cancel_file:cmd+=['--cancel-file',str(a.cancel_file.resolve())]
 supervise(cmd,out,cancel_file=a.cancel_file)
 print(json.dumps(dict(status='complete',summary=str(out/'summary.json'))))


if __name__=='__main__':main()
