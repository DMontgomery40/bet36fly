"""Independent offline artifact audit. No capture/simulator imports or circuit calls."""
from pathlib import Path
import hashlib
import json
import math
import subprocess
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).parent
RID='onset-history-capture-4343c21535c43f42'
CAP=HERE/'onset-history-captures'/RID
EVIDENCE=ROOT/'docs/evidence/reward-mechanism-repair-2026-09-12'
PRIOR=('diag-rate-bridge-v1-maskgamma-de050d773763','diag-rate-bridge-v1-maskgamma-dea14759e9ca')
SNAPSHOT='3b09865ba331b2c58c4bb8080e0d6354b4c8f612'
PHASES=((100.,130.),(130.,300.),(300.,400.),(400.,math.inf))


def digest(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def array_meta(a):return {'dtype':str(a.dtype),'shape':list(a.shape),'sha256':hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()}


def load(path):return json.loads(Path(path).read_text())


def closed_state(events,boundary,minimum_time):
 """Direct sum of exponential impulse responses; boundary event is excluded."""
 times=np.arange(len(events))*.2;keep=(times>=minimum_time)&(times<boundary);ages=boundary-times[keep]
 impulses=events[keep].astype(float)
 rate=(np.exp(-ages/100)/100)@impulses
 eligibility=((np.exp(-ages/500)-np.exp(-ages/100))/(100*(.01-.002)))@impulses
 return np.column_stack((rate,eligibility))


def independent_pair_areas(kc,dan_mean,minimum_time):
 """Sparse observed event-pair integrals, independently integrating each true product.
 Does not use the captured recurrence, its A/C coefficients or its saved oracle.
 """
 ti,kidx=np.nonzero(kc);kt=ti*.2;keep=kt>=minimum_time;kt=kt[keep];kidx=kidx[keep]
 result=np.zeros((4,kc.shape[1],dan_mean.shape[1],3))
 for c in range(dan_mean.shape[1]):
  for di in np.flatnonzero(dan_mean[:,c]):
   dt=di*.2
   if dt<minimum_time:continue
   mass=dan_mean[di,c];lag=dt-kt;latest=np.maximum(dt,kt)
   full=-.0005*mass*np.sign(lag)*(np.exp(-abs(lag)/500)-np.exp(-abs(lag)/100))
   for p,(lo,hi) in enumerate(PHASES):
    left=np.maximum(latest,lo);span=np.maximum(0,hi-left)
    active=left<hi
    main_time=np.where(active,-np.expm1(-.012*span)/.012,0)
    cross_time=np.where(active,-np.expm1(-.02*span)/.02,0)
    kd_age=left-kt;dd_age=left-dt
    common=np.exp(-.01*(kd_age+dd_age))*cross_time
    scale=.0005*.96*mass*.01**2/(.01-.002)
    positive=scale*(np.exp(-.002*dd_age-.01*kd_age)*main_time-common)
    negative=-scale*(np.exp(-.002*kd_age-.01*dd_age)*main_time-common)
    net=np.where(active,full*np.exp(-.012*(left-latest))*(-np.expm1(-.012*span)),0)
    for field,value in enumerate((positive,negative,net)):
     result[p,:,c,field]+=np.bincount(kidx,weights=value,minlength=kc.shape[1])
 return result


def main():
 s=load(CAP/'summary.json');receipt=load(EVIDENCE/'onset-capture-preregistration.json');copied=load(CAP/'capture-receipt.json');identity=receipt['identity']
 assert s['status']=='complete' and s['run_id']==RID and copied==receipt and s['identity']==identity
 assert RID=='onset-history-capture-'+hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:16]
 assert identity['contract_sha256']==digest(EVIDENCE/'onset-history-investigation-preregistration.md')
 assert s['calls']==s['attempted_calls']==identity['planned_calls']==33 and 0<s['wall_seconds']<600
 assert identity['wall_seconds_cap']==600 and identity['shadow']['feedback'] is False
 cues=((4362,4366,4370,4374,4378,4383,4387,4391),(4395,4399,4404,4408,4412,4416,4420,4425))
 expected=[dict(game=g,seed_set=ss,seed=g+42+2000000*p+off,run_id=PRIOR[p]) for p,gs in enumerate(cues) for g in gs for ss,off in [('base',0),('alt',1000000)]]
 assert identity['rows']==expected
 assert [{k:r[k] for k in ('game','seed_set','seed','run_id')} for r in s['rows']]==expected
 hashes={str(p.relative_to(ROOT)):digest(p) for p in sorted(CAP.iterdir())}
 for p in (EVIDENCE/'onset-capture-preregistration.json',Path(receipt['samples_path'])):hashes[str(p.relative_to(ROOT))]=digest(p)
 assert digest(receipt['samples_path'])==receipt['samples_sha256']
 with np.load(receipt['samples_path'],allow_pickle=False) as z:maps={k:z[k] for k in z.files}
 assert {k:array_meta(a) for k,a in maps.items()}==identity['sample_arrays']
 sample=maps['sample'];pc=maps['plastic_compartments'];pk=maps['plastic_kc_indices'];mask=maps['plastic_mask'].astype(bool);groups=maps['plastic_groups'];dc=maps['dan_compartments']
 assert sample.dtype==np.int32 and sample.shape==(4774,) and np.all(np.diff(sample)>0)
 assert np.array_equal(mask,(pc==0)|(groups%4==0)) and int(np.sum(mask&(pc==0)))==4184 and int(np.sum(mask&(pc==1)))==3239
 for role in ('kc','dan','sensory'):np.testing.assert_array_equal(sample[maps[role+'_columns']],maps[role+'_indices'])
 assert identity['role_overlaps']=={'kc/dan':[],'kc/sensory':[],'dan/sensory':[]}
 for path,sha in identity['graph_hashes'].items():assert digest(ROOT/path)==sha
 np.testing.assert_array_equal(maps['body_ids'],np.load(ROOT/'data/brain/ids.npy')[sample])
 np.testing.assert_array_equal(maps['kc_indices'],np.load(ROOT/'data/brain/kc.npy'));np.testing.assert_array_equal(maps['sensory_indices'],np.load(ROOT/'data/brain/sensory.npy'))
 source_snapshots={}
 for name,sha in identity['source_code'].items():
  path=('scripts/' if name=='reward_teaching_diagnostic.py' else 'bet36fly/')+name
  body=subprocess.check_output(['git','show',SNAPSHOT+':'+path],cwd=ROOT)
  actual=hashlib.sha256(body).hexdigest();assert actual==sha
  source_snapshots[path]={'git_commit':SNAPSHOT,'sha256':actual}
 for name,key in [('onset_history_capture.py','harness_sha256'),('test_onset_history_capture.py','tests_sha256'),('onset-reference-audit.py','independent_reference_sha256')]:assert digest(HERE/name)==identity[key]
 assert digest(identity['native_binary']['path'])==identity['native_binary']['sha256']
 pilot=Path(identity['pilot'])
 for name,key in [('source/inputs.npz','inputs_sha256'),('manifest.json','pilot_manifest_sha256'),('source/protocol.json','pilot_protocol_sha256')]:assert digest(pilot/name)==identity[key]
 attempts=load(CAP/'attempts.json');progress=load(CAP/'progress.json');shprogress=load(CAP/'shadow-progress.json')
 assert attempts['attempted_calls']==len(attempts['attempts'])==33
 expected_attempts=[(expected[0],False)]+[(r,True) for r in expected]
 starts=[]
 for n,(a,(row,fine)) in enumerate(zip(attempts['attempts'],expected_attempts),1):
  assert a['attempt']==n and a['row']==row and a['fine'] is fine and a['bin_ms']==(.2 if fine else 10.)
  assert a['schedule']['shape']==[2000 if fine else 40,686] and a['schedule']['dtype']=='float32'
  starts.append(a['started_monotonic_seconds'])
 assert np.all(np.diff(starts)>0) and starts[0]>=0 and starts[-1]<s['wall_seconds']
 for i in range(1,33,2):assert attempts['attempts'][i]['schedule']==attempts['attempts'][i+1]['schedule']
 assert progress['completed_calls']==progress['attempted_calls']==33 and progress['saved']==s['saved'] and shprogress==s['rows']
 expected_files={'summary.json','capture-receipt.json','attempts.json','progress.json','shadow-progress.json','coarse.npz'}|{f'fine_{i:02d}.npz' for i in range(32)}|{f'shadow_{i:02d}_{h}.npz' for i in range(32) for h in ('cold','continuous')}
 assert {p.name for p in CAP.iterdir()}==expected_files
 assert [a['file'] for a in s['saved']]==['coarse.npz']+[f'fine_{i:02d}.npz' for i in range(32)]
 priors={};prior_summaries={}
 for rid in PRIOR:
  path=ROOT/'output/diagnostics'/rid;meta=identity['prior'][rid]
  assert digest(path/'summary.json')==meta['summary_sha256']
  for name,a in meta['artifacts'].items():assert digest(path/name)==a['sha256'] and (path/name).stat().st_size==a['bytes']
  priors[rid]=np.load(path/'trials.npz',allow_pickle=False);prior_summaries[rid]=load(path/'summary.json')
 captured=[]
 for entry in s['saved']:
  path=CAP/entry['file'];assert not path.is_symlink() and digest(path)==entry['sha256'] and path.stat().st_size==entry['bytes']
  with np.load(path,allow_pickle=False) as z:a={k:z[k] for k in z.files}
  assert {k:array_meta(v) for k,v in a.items()}==entry['numeric_fingerprint']
  assert all(np.isfinite(v).all() for v in a.values())
  assert entry['metadata']['duration_ms']==400 and entry['metadata']['dt']==.2 and entry['metadata']['instrumentation'] is None
  assert a['counts'].shape==(166700,) and a['counts'].dtype==np.int32 and np.all(a['counts']>=0)
  np.testing.assert_array_equal(a['rates'],a['counts'].astype(np.float32)*2.5);np.testing.assert_array_equal(a['rates'],a['rates_hz'])
  np.testing.assert_array_equal(a['counts'][sample],a['trace'].sum(0));assert a['population'].sum()==a['counts'].sum()
  np.testing.assert_array_equal(a['dan_counts'],a['trace'][:,maps['dan_columns']].sum(0))
  np.testing.assert_array_equal(a['compartment_dan_counts'],[a['dan_counts'][dc==c].sum() for c in (0,1)])
  assert not a['pulse_times_ms'].size and not a['pulse_dan_indices'].size
  captured.append(a)
 coarse,fine0=captured[:2]
 for key,a in coarse.items():
  b=captured[1][key]
  if key in ('trace','population'):b=b.reshape((40,50)+b.shape[1:]).sum(1)
  np.testing.assert_array_equal(a,b,err_msg='independent coarse/fine '+key)
 maxima={'onset_state_error':0.,'endpoint_state_error':0.,'true_integral_error':0.,'net_integral_error':0.,'per_edge_publication_reconciliation_error':0.,'absolute_integral_envelope':0.}
 rows=[];bound_total=0
 for index,(row,actual) in enumerate(zip(expected,captured[1:])):
  old=priors[row['run_id']];prefix=f"{row['game']}__{row['seed_set']}__untaught";trace=actual['trace'];assert trace.shape==(2000,4774) and np.isin(trace,[0,1]).all()
  binned=trace.reshape(40,50,4774).sum(1)
  np.testing.assert_array_equal(actual['gains'],old[prefix+'__gains']);np.testing.assert_array_equal(actual['gain_delta'],old[prefix+'__gain_delta'])
  np.testing.assert_array_equal(binned[:,maps['sensory_columns']],old[prefix+'__sensory_bins']);np.testing.assert_array_equal(binned[:,maps['dan_columns']],old[prefix+'__dan_bins'])
  kc=trace[:,maps['kc_columns']];dans=trace[:,maps['dan_columns']];danmean=np.column_stack([dans[:,dc==c].sum(1)/np.count_nonzero(dc==c) for c in (0,1)])
  np.testing.assert_array_equal(kc.sum(1),old[prefix+'__step_signals'][:,0]);np.testing.assert_array_equal(danmean.astype(np.float32),old[prefix+'__step_signals'][:,1:3])
  if row['game']==prior_summaries[row['run_id']]['panel_games'][0]:
   oldsample=old['sampled'];cols=[int(np.flatnonzero(oldsample==v)[0]) for v in sample]
   np.testing.assert_array_equal(binned,old[prefix+'__sampled_bins'][:,cols])
  if index==0:
   replay=load(ROOT/'output/diagnostics'/PRIOR[0]/'replay-evidence.json')['untaught']['original']
   for key,a in coarse.items():
    if key!='trace':assert [str(a.dtype),list(a.shape),array_meta(a)['sha256']]==replay[key]
  item=dict(row,effects={})
  for history in ('cold','continuous'):
   recorded=s['rows'][index]['effects'][history];path=CAP/f'shadow_{index:02d}_{history}.npz'
   assert recorded['file']==path.name and digest(path)==recorded['sha256']
   with np.load(path,allow_pickle=False) as z:sh={k:z[k] for k in z.files}
   assert all(np.isfinite(v).all() for v in sh.values())
   ep=sh['edge_phases'];gp=sh['group_phases'];gain=sh['gains'];assert ep.shape==(4,8866,8) and gp.shape==(4,8,8) and ep.dtype==gp.dtype==np.float64 and gain.dtype==np.float32
   assert np.all(ep[...,0]>=-1e-12) and np.all(ep[...,1]<=1e-12)
   np.testing.assert_array_equal(sh['onset_gains'],1);np.testing.assert_array_equal(sh['onset_double_gains'],1)
   assert recorded['pre_onset_published_changes']==recorded['pre_onset_double_changes']==0
   assert not ep[:,~mask].any();np.testing.assert_array_equal(gain[~mask],1)
   np.testing.assert_array_equal(ep[...,4].sum(0),gain.astype(float)-1)
   np.testing.assert_allclose(ep[...,0]+ep[...,1],ep[...,2],rtol=1e-8,atol=1e-10)
   assert np.all(ep[...,5:7]>=0) and np.array_equal(ep[...,5:7],np.rint(ep[...,5:7]))
   bound=int(ep[...,5:7].sum());assert bound==recorded['bounds']==0;bound_total+=bound
   assert np.all((gain[mask]>.5)&(gain[mask]<1.5))
   reduced=np.stack([np.stack([np.bincount(groups,weights=ep[p,:,f],minlength=8) for f in range(8)],axis=1) for p in range(4)])
   np.testing.assert_array_equal(reduced,gp);np.testing.assert_array_equal(gp,np.asarray(recorded['group_phases']))
   minimum=100. if history=='cold' else 0.
   onset_kc=closed_state(kc,100.,minimum);onset_dan=closed_state(danmean,100.,minimum)
   end_kc=closed_state(kc,400.,minimum);end_dan=closed_state(danmean,400.,minimum)
   for key,expected_state in [('onset_kc',onset_kc),('onset_dan',onset_dan),('endpoint_kc',end_kc),('endpoint_dan',end_dan)]:
    error=float(np.max(abs(sh[key]-expected_state)));stat='onset_state_error' if key.startswith('onset') else 'endpoint_state_error';maxima[stat]=max(maxima[stat],error)
    np.testing.assert_allclose(sh[key],expected_state,rtol=1e-11,atol=1e-12)
   areas=independent_pair_areas(kc,danmean,minimum)[:,pk,pc,:];areas[:,~mask,:]=0
   maxima['true_integral_error']=max(maxima['true_integral_error'],float(np.max(abs(areas[...,:2]-ep[...,:2]))))
   maxima['net_integral_error']=max(maxima['net_integral_error'],float(np.max(abs(areas[...,2]-ep[...,2]))))
   np.testing.assert_allclose(areas,ep[...,:3],rtol=1e-8,atol=1e-10)
   np.testing.assert_allclose(areas[...,2],sh['independent_pair_attempted'],rtol=1e-8,atol=1e-10)
   np.testing.assert_array_equal((1+areas[...,2].sum(0)).astype(np.float32),gain)
   # Absolute true area bounds every prefix's change; if <.5 no hidden transient can hit a gain bound.
   envelope=(areas[...,0]-areas[...,1]).sum(0);maxima['absolute_integral_envelope']=max(maxima['absolute_integral_envelope'],float(envelope.max()));assert np.all(envelope<.5)
   q=ep[...,7];coeff=.0005*.96*(-math.expm1(-.012*.2)/.012)
   np.testing.assert_allclose(ep[:3,:,2],coeff*q[:3],rtol=1e-8,atol=1e-10);np.testing.assert_allclose(ep[3,:,2],(.0005*.96/.012)*q[3],rtol=1e-8,atol=1e-10)
   published=[float((gain.astype(float)-1)[pc==c].sum()) for c in (0,1)];attempted=[float(ep[:,pc==c,2].sum()) for c in (0,1)]
   np.testing.assert_array_equal(published,recorded['published']);np.testing.assert_array_equal(attempted,recorded['attempted'])
   if history=='cold':np.testing.assert_array_equal(gain,actual['gains'])
   item['effects'][history]=dict(published=published,attempted=attempted,bounds=bound,onset_kc_active=int(np.count_nonzero(onset_kc[:,0])),onset_dan_rate=onset_dan[:,0].tolist(),onset_dan_eligibility=onset_dan[:,1].tolist(),phase_published_home=gp[:,:4,4].sum(1).tolist())
  assert s['rows'][index]['actual_checkpoint_unchanged_by_shadow'] is True
  rows.append(item)
 for z in priors.values():z.close()
 metrics={}
 for rid in PRIOR:
  for ss in ('base','alt'):
   selection=[r for r in rows if r['run_id']==rid and r['seed_set']==ss];assert len(selection)==8
   for c in (0,1):
    key=f'{rid}/{ss}/{c}';metrics[key]={}
    for history in ('cold','continuous'):
     u=np.array([r['effects'][history]['published'][c] for r in selection]);metrics[key][history]={'mean':float(u.mean()),'sd':float(u.std(ddof=1)),'guard_limit':float(.5*u.std(ddof=1)),'passed':bool(abs(u.mean())<=.5*u.std(ddof=1))}
 assert metrics==s['metrics']
 selection=[r for r in rows if r['run_id']==PRIOR[1] and r['seed_set']=='base'];cold=np.array([r['effects']['cold']['published'][0] for r in selection]);warm=np.array([r['effects']['continuous']['published'][0] for r in selection])
 contrast=float(np.mean(warm-cold));attempted_contrast=float(np.mean([r['effects']['continuous']['attempted'][0]-r['effects']['cold']['attempted'][0] for r in selection]))
 directional=bool(contrast>0 and abs(warm.mean())<abs(cold.mean()));screen=bool(bound_total==0 and all(v['continuous']['passed'] for v in metrics.values()))
 assert contrast==s['mean_warm_minus_cold'] and attempted_contrast==s['attempted_warm_minus_cold'] and directional is s['directional_support'] is False and screen is s['necessary_shadow_screen'] is False
 assert s['continuous_bound_observations']==0 and s['qualification'] is False
 # Recheck immutable audited inputs after the read/compute pass.
 for path,sha in hashes.items():assert digest(ROOT/path)==sha
 result=dict(audit='PASS: recorded execution and calculations independently reconciled; scientific hypothesis falsified',run_id=RID,summary_sha256=digest(CAP/'summary.json'),preregistration_sha256=digest(EVIDENCE/'onset-capture-preregistration.json'),
             captured_source_identity=identity['source_code'],source_snapshot_validation=source_snapshots,
             protected_input_hashes=identity['graph_hashes'],pilot_hashes={k:identity[k] for k in ('inputs_sha256','pilot_manifest_sha256','pilot_protocol_sha256')},
             native_binary=identity['native_binary'],harness_sha256=identity['harness_sha256'],reference_sha256=identity['independent_reference_sha256'],tests_sha256=identity['tests_sha256'],artifact_hashes=hashes,attempted_calls=33,completed_capture_arrays=33,shadow_array_files=64,all32_canonical_parities=True,
             no_unexplained_calls_in_capture_ledger=True,scope_limit='Ledger/source structure cannot exclude unrelated calls outside this captured process; no process tracing or native rerun. Actual states/trajectories reconcile to saved cold evidence. Source snapshot is bound, not current worktree equality.',
             onset_gain_snapshots_unchanged=True,cold_actual_gains_bit_identical=True,independent_closed_pair_float_gains_bit_identical=True,all_per_edge_phases_reconciled=True,all_true_integrals_recomputed=True,zero_bounds_with_independent_absolute_area_proof=True,
             numerical_maxima=maxima,rows=rows,metrics=metrics,mean_warm_minus_cold=contrast,attempted_warm_minus_cold=attempted_contrast,directional_support=directional,necessary_shadow_screen=screen,qualification=False,recorded_wall_seconds=s['wall_seconds'])
 result['audit_script_sha256']=digest(__file__)
 out=HERE/'onset-capture-independent-audit.json';out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('artifact_hashes','rows','source_snapshot_validation','captured_source_identity')},indent=2))


if __name__=='__main__':main()
