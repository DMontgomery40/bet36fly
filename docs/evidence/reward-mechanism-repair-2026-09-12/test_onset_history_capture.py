"""Output-local tests: numerical history contract and bounded capture failure families."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest

P=Path(__file__).with_name('onset_history_capture.py')
spec=importlib.util.spec_from_file_location('onset_capture',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def case(events_k,events_d,steps=2000):
 k=np.zeros((steps,2),np.uint8);d=np.zeros((steps,2),np.uint8)
 for t,j in events_k:k[round(t/.2),j]=1
 for t,j in events_d:d[round(t/.2),j]=1
 return k,d


def solve(k,d,history='cold',**kwargs):
 return m.shadow(k,d,np.array([0,1,0]),np.array([0,0,1]),np.array([0,1]),np.array([1,1,0],np.uint8),np.array([0,2,4]),history=history,**kwargs)


@pytest.mark.parametrize('kt,dt',[(99.8,100),(100,100),(100,100.2),(0,20),(10,250),(150,50),(0,0)])
@pytest.mark.parametrize('history',['cold','continuous'])
def test_boundary_and_complete_tail_agree_with_independent_pair_integrals(kt,dt,history):
 k,d=case([(kt,0)],[(dt,0)]);a=solve(k,d,history)
 oracle=m.pair_integrals(k,d,np.array([0,1]),history=history)
 np.testing.assert_allclose(a['edge_phases'][:,0,2],oracle[:,0,0],rtol=1e-8,atol=1e-12)
 assert a['gains'][0]==np.float32(1+oracle[:,0,0].sum())
 assert a['gains'][2]==1
 assert a['pre_onset_published_changes']==0
 assert a['edge_phases'][...,4].sum()==float((a['gains'].astype(float)-1).sum())


def test_continuous_onset_state_is_closed_history_before_boundary_injection():
 k,d=case([(0,0),(99.8,0),(100,0),(100.2,0)],[(20,0),(100,0)])
 a=solve(k,d,'continuous');times=np.array([0,99.8]);age=100-times
 expected_r=np.sum(np.exp(-age/100)/100)
 expected_e=np.sum((np.exp(-age/500)-np.exp(-age/100))/(100*(.01-.002)))
 np.testing.assert_allclose(a['onset_kc'][0],[expected_r,expected_e],rtol=1e-12,atol=1e-14)
 assert not solve(k,d,'cold')['onset_kc'].any()
 oracle=m.pair_integrals(k,d,np.array([0,1]),history='continuous')
 np.testing.assert_allclose(a['edge_phases'][:,0,2],oracle[:,0,0],atol=1e-12,rtol=1e-8)


@pytest.mark.parametrize('events',[([],[]), ([(100,0)],[]),([] ,[(100,0)]), ([(100,0),(200,1)],[(120,0),(310,1)])])
def test_no_prehistory_cold_continuous_and_input_immutability(events):
 k,d=case(*events);bk,bd=k.copy(),d.copy();a,b=solve(k,d),solve(k,d,'continuous')
 for key in ('gains','edge_phases','onset_kc','onset_dan'):np.testing.assert_array_equal(a[key],b[key])
 np.testing.assert_array_equal(k,bk);np.testing.assert_array_equal(d,bd)


@pytest.mark.parametrize('side',[0,1])
def test_preonly_history_has_nonzero_post_boundary_tail(side):
 k,d=case([(10 if side==0 else 40,0)],[(40 if side==0 else 10,0)])
 a=solve(k,d,'continuous');assert np.sign(a['edge_phases'][:,0,2].sum())==(-1 if side==0 else 1)
 assert not solve(k,d)['edge_phases'].any()
 assert a['edge_phases'][3,0,2]!=0


@pytest.mark.parametrize('bad',['nan','fraction','negative','two','rank','length','bool_history'])
def test_invalid_rasters_fail_closed(bad):
 k,d=case([],[])
 if bad=='nan':k=k.astype(float);k[0,0]=np.nan
 elif bad=='fraction':k=k.astype(float);k[0,0]=.5
 elif bad=='negative':k=k.astype(int);k[0,0]=-1
 elif bad=='two':d[0,0]=2
 elif bad=='rank':k=k[:,0]
 elif bad=='length':d=d[:-1]
 with pytest.raises(ValueError):solve(k,d,history=True if bad=='bool_history' else 'cold')


def tiny(seed,bin_ms,sample,pulses):
 from bet36fly.reward_brain import RewardEngine
 n=4
 e=RewardEngine(np.array([0,1,1,1,1]),np.array([3]),np.array([1.],np.float32),np.array([0]),np.array([0]),np.array([1,2]),np.array([0,0]),np.array([0]),np.array([0]),np.array([0]),n_compartments=1,learning_rule='rate-bridge-v1',dan_reference='none',plasticity_onset_ms=10,dan_baseline_window_ms=0)
 coarse=np.array([[1000.],[0.],[5000.],[250.]],np.float32)
 schedule=coarse if bin_ms==10 else np.repeat(coarse,50,axis=0)
 return e.run(schedule,bin_ms=bin_ms,seed=seed,sample=np.array(sample),teaching_pulses=pulses,record=False)


@pytest.mark.parametrize('seed',[0,42,1000042])
@pytest.mark.parametrize('sample',[[0,1,2],[3,0,2,1],[2]])
@pytest.mark.parametrize('pulses',[[],[(10,0),(10.2,0),(12.2,0),(39.8,1)]])
def test_native_nonconstant_coarse_fine_parity(seed,sample,pulses):
 a=tiny(seed,10,sample,pulses);b=tiny(seed,.2,sample,pulses);m.compare_coarse_fine(a,b)


@pytest.mark.parametrize('key',['counts','voltage','gains','gain_delta','dan_counts','compartment_dan_counts','trace','population'])
def test_parity_rejects_every_mismatched_array(key):
 a=tiny(42,10,[0,1,2],[]);b=tiny(42,.2,[0,1,2],[]);b[key]=b[key].copy();b[key].flat[0]+=1
 with pytest.raises((AssertionError,ValueError)):m.compare_coarse_fine(a,b)


@pytest.mark.parametrize('failure',['coarse','fine0','parity','retained','cancel','deadline'])
def test_capture_sequence_stops_preserving_prior_outputs(failure,tmp_path):
 calls=[];saved=[];rows=list(range(32))
 def run(row,fine):
  calls.append((row,fine))
  if failure=='coarse' and not fine or failure=='fine0' and fine:raise RuntimeError('run failed')
  return {'row':row,'fine':fine}
 def parity(a,b):
  if failure=='parity':raise ValueError('parity')
 def retained(row,result,fine):
  if failure=='retained':raise ValueError('retained')
 def guard():
  if failure in ('cancel','deadline'):raise RuntimeError(failure)
 with pytest.raises((RuntimeError,ValueError)):
  m.capture_sequence(rows,run,parity,retained,lambda name,result:saved.append(name),guard)
 assert len(calls)<=2
 if failure=='parity':assert saved==['coarse','fine_00']


def test_complete_capture_has_exactly33_calls_in_frozen_order():
 calls=[];saved=[]
 def run(row,fine):calls.append((row,fine));return {}
 m.capture_sequence(list(range(32)),run,lambda a,b:None,lambda *a:None,lambda name,r:saved.append(name),lambda:None)
 assert calls==[(0,False)]+[(i,True) for i in range(32)]
 assert len(saved)==33


def test_capture_rejects_wrong_matrix_length():
 with pytest.raises(ValueError):m.capture_sequence([0],None,None,None,None,None)


def reference_module():
 p=P.with_name('onset-reference-audit.py');s=importlib.util.spec_from_file_location('independent_onset_reference',p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v


@pytest.mark.parametrize('history',['cold','continuous'])
@pytest.mark.parametrize('name',['coincident_at_boundary','pre_only_k_then_d','cross_boundary_k_first','mixed','sub_ulp_after_gate'])
def test_true_integrals_publications_and_snapshots_against_quadrature(history,name):
 ref=reference_module();ks,ds=ref.CASES[name]
 k,d=case([(t,0) for t,a in ks],[(t,0) for t,a in ds]);dc=np.zeros(2,int)
 # Mixed reference uses half-population; all other cases use unit DAN events.
 if name!='mixed':d[:,1]=d[:,0]
 a=m.shadow(k,d,np.array([0]),np.array([0]),dc,np.array([1],np.uint8),np.array([0]),history=history)
 r=ref.reference(ks,ds,warm=history=='continuous')
 np.testing.assert_allclose(a['edge_phases'][:3,0,:2].sum(0),r['true_areas'],rtol=1e-8,atol=1e-10)
 np.testing.assert_allclose(a['edge_phases'][3,0,:2],r['tail_true_areas'],rtol=1e-8,atol=1e-10)
 assert a['gains'][0]==r['final_published']
 np.testing.assert_array_equal(a['onset_gains'],1);np.testing.assert_array_equal(a['onset_double_gains'],1)
 assert a['pre_onset_published_changes']==a['pre_onset_double_changes']==0
 np.testing.assert_allclose(a['onset_kc'][0],r['onset_kc'],rtol=1e-12,atol=1e-14)
 np.testing.assert_allclose(a['onset_dan'][0],r['onset_dan'],rtol=1e-12,atol=1e-14)
 if name=='sub_ulp_after_gate':
  assert abs(a['edge_phases'][3,0,2])<np.spacing(np.float32(1))/4
  assert a['gains'][0]==np.float32(1-7.990406610006717e-7)


@pytest.mark.parametrize('population,active',[(1,1),(2,1),(2,2),(22,1),(22,2),(22,22)])
def test_partial_population_normalization(population,active):
 k=np.zeros((2000,1),np.uint8);d=np.zeros((2000,population),np.uint8);k[499]=1;d[500,:active]=1
 a=m.shadow(k,d,np.array([0]),np.array([0]),np.zeros(population,int),np.array([1]),np.array([0]),history='continuous')
 expected=-.0005*(np.exp(-.2/500)-np.exp(-.2/100))*active/population
 assert a['gains'][0]==np.float32(1+expected)
 assert a['edge_phases'][:,0,2].sum()==pytest.approx(expected,abs=1e-14)


@pytest.mark.parametrize('reverse',[False,True])
def test_clipping_both_bounds_reversal_tail_and_publication_match_independent_path(reverse):
 ref=reference_module();kt=[0,220,390];dt=[80,150,300]
 if reverse:kt,dt=dt,kt
 k,d=case([(t,0) for t in kt],[(t,0) for t in dt]);a=solve(k,d,'continuous',eta=2500.)
 r=ref.reference([(t,1) for t in kt],[(t,1) for t in dt],warm=True,scale=5000000.)
 assert a['gains'][0]==r['final_published']
 np.testing.assert_array_equal(a['edge_phases'][:3,0,5:7].sum(0),r['interval_bounds'])
 np.testing.assert_array_equal(a['edge_phases'][3,0,5:7],r['tail_bounds'])
 assert np.all(a['edge_phases'][:3,0,5:7].sum(0)>0)
 np.testing.assert_allclose(a['edge_phases'][:3,0,2:5].sum(0),[r['interval_attempted'],r['interval_double_applied'],r['interval_published']],rtol=1e-8,atol=1e-9)


@pytest.mark.parametrize('at',[3,9,31])
def test_midstream_failures_preserve_prior_attempts_and_saved_results(at):
 calls=[];saved=[]
 def run(row,fine):
  calls.append((row,fine))
  if fine and row==at:raise RuntimeError('native failure')
  return {}
 with pytest.raises(RuntimeError):m.capture_sequence(list(range(32)),run,lambda *a:None,lambda *a:None,lambda name,r:saved.append(name),lambda:None)
 assert calls[-1]==(at,True) and len(calls)==at+2 and len(saved)==at+1


@pytest.mark.parametrize('reason',['timeout','timeout_needs_kill','cancel'])
def test_supervisor_interrupts_inflight_process_and_preserves_artifacts(reason,tmp_path):
 import subprocess
 (tmp_path/'prior.npz').write_bytes(b'preserve');cancel=tmp_path/'cancel'
 if reason=='cancel':cancel.touch()
 class Proc:
  def __init__(self):self.terminated=False;self.killed=False;self.done=False
  def wait(self,timeout):
   if self.terminated and (reason!='timeout_needs_kill' or self.killed):self.done=True;return -15
   raise subprocess.TimeoutExpired('fake_native',timeout)
  def terminate(self):self.terminated=True
  def kill(self):self.killed=True
  def poll(self):return -15 if self.done else None
 proc=Proc();times=iter([0,0,601,602,603])
 with pytest.raises(RuntimeError):m.supervise(['fake'],tmp_path,cancel_file=cancel,popen=lambda c:proc,clock=lambda:next(times))
 assert proc.terminated and (reason!='timeout_needs_kill' or proc.killed)
 assert (tmp_path/'prior.npz').read_bytes()==b'preserve'
 assert (tmp_path/'supervisor-stop.json').exists()


def exact_rows():
 return [dict(game=g,seed_set=ss,seed=g+42+panel*2000000+extra,run_id=m.RUNS[panel]) for panel,values in enumerate(((4362,4366,4370,4374,4378,4383,4387,4391),(4395,4399,4404,4408,4412,4416,4420,4425))) for g in values for ss,extra in [('base',0),('alt',1000000)]]


@pytest.mark.parametrize('bad',['nonfirstseed','cue','duplicate','missing','reorder','noise','run'])
def test_exact_preregistered_selector_matrix_is_independently_locked(bad):
 rows=exact_rows();m.validate_selection(rows)
 if bad=='nonfirstseed':rows[-1]['seed']+=1
 elif bad=='cue':rows[20]['game']+=1
 elif bad=='duplicate':rows[12]=rows[11]
 elif bad=='missing':rows.pop()
 elif bad=='reorder':rows[4],rows[5]=rows[5],rows[4]
 elif bad=='noise':rows[13]['seed_set']='base'
 elif bad=='run':rows[-1]['run_id']='other'
 with pytest.raises(ValueError):m.validate_selection(rows)


def test_freeze_exclusive_immutable_mapping_and_identity(monkeypatch,tmp_path):
 maps={'sample':np.array([1,2],np.int32)};identity={'map':m.array_identity(maps['sample'])}
 monkeypatch.setattr(m,'frozen_context',lambda:(identity,maps));p=tmp_path/'receipt.json'
 a=m.freeze(p);before=p.read_bytes();sample=Path(a['samples_path']);sample_before=sample.read_bytes()
 assert m.freeze(p)['run_id']==a['run_id'];assert p.read_bytes()==before
 identity['mutated']=True
 with pytest.raises(AssertionError):m.freeze(p)
 assert p.read_bytes()==before and sample.read_bytes()==sample_before


def test_unpaired_existing_sample_file_is_preserved(monkeypatch,tmp_path):
 monkeypatch.setattr(m,'frozen_context',lambda:({'x':1},{'sample':np.array([1],np.int32)}));p=tmp_path/'receipt.json';sample=p.with_suffix('.samples.npz');sample.write_bytes(b'prior')
 with pytest.raises(FileExistsError):m.freeze(p)
 assert sample.read_bytes()==b'prior' and not p.exists()


@pytest.mark.parametrize('bad',['gains','sensory','dansteps','kcsteps','dancounts','samplecounts'])
def test_retained_artifact_parity_rejects_contract_mismatches(bad):
 trace=np.zeros((2000,3),np.int32);trace[510]=1;coarse=trace.reshape(40,50,3).sum(1);prefix='1__base__untaught'
 maps=dict(sample=np.array([0,1,2]),kc_columns=np.array([0]),dan_columns=np.array([1]),sensory_columns=np.array([2]),dan_compartments=np.array([0]))
 result=dict(gains=np.array([1.],np.float32),gain_delta=np.array([0.],np.float32),trace=trace,dan_counts=np.array([1]),counts=np.array([1,1,1]))
 steps=np.zeros((2000,3),np.float32);steps[:,0]=trace[:,0];steps[:,1]=trace[:,1]
 z={prefix+'__gains':result['gains'].copy(),prefix+'__gain_delta':result['gain_delta'].copy(),prefix+'__sensory_bins':coarse[:,2:3].copy(),prefix+'__dan_bins':coarse[:,1:2].copy(),prefix+'__step_signals':steps}
 row=dict(game=1,seed_set='base',run_id='tiny');summary=dict(panel_games=[99]);m.retained_checks(row,result,True,maps,summary,z)
 if bad=='gains':z[prefix+'__gains'][0]=.9
 elif bad=='sensory':z[prefix+'__sensory_bins'][0,0]=1
 elif bad=='dansteps':steps[1,1]=1
 elif bad=='kcsteps':steps[1,0]=1
 elif bad=='dancounts':result['dan_counts'][0]=2
 elif bad=='samplecounts':result['counts'][0]=2
 with pytest.raises(AssertionError):m.retained_checks(row,result,True,maps,summary,z)


@pytest.mark.parametrize('kind',['cancel','deadline'])
def test_midstream_guard_stops_after_preserving_completed_calls(kind):
 calls=[];saved=[]
 def run(row,fine):calls.append((row,fine));return {}
 def guard():
  if len(calls)>=5:raise RuntimeError(kind)
 with pytest.raises(RuntimeError):m.capture_sequence(list(range(32)),run,lambda *a:None,lambda *a:None,lambda name,r:saved.append(name),guard)
 assert len(calls)==len(saved)==5


def test_attempt_ledger_precedes_native_failure_and_refuses34th(tmp_path):
 import json
 attempts=[];p=tmp_path/'attempts.json';schedule=np.zeros((2,1),np.float32)
 for i in range(33):m.record_attempt(p,attempts,{'game':i},i>0,schedule,float(i))
 before=p.read_bytes();assert json.loads(before)['attempted_calls']==33
 with pytest.raises(ValueError):m.record_attempt(p,attempts,{},True,schedule,34.)
 assert p.read_bytes()==before and len(attempts)==33
 assert json.loads(before)['attempts'][-1]['row']=={'game':32}


@pytest.mark.parametrize('bad',['pk','pc','group','mask','eta','initial'])
def test_invalid_shadow_mapping_parameters_fail_closed(bad):
 k,d=case([],[]);pk=np.array([0]);pc=np.array([0]);g=np.array([0]);mask=np.array([1]);kw={}
 if bad=='pk':pk[0]=2
 elif bad=='pc':pc[0]=2
 elif bad=='group':g[0]=8
 elif bad=='mask':mask[0]=2
 elif bad=='eta':kw['eta']=True
 elif bad=='initial':kw['initial']=[np.nan]
 with pytest.raises(ValueError):m.shadow(k,d,pk,pc,np.array([0,1]),mask,g,**kw)


def test_complete_output_local_worker_on_tiny_native_graph(monkeypatch,tmp_path):
 """All33 capture calls, prior artifacts and64 shadows; seven neurons, no MaleCNS."""
 import json
 import bet36fly.reward_protocol as protocol_module
 from bet36fly.reward_brain import RewardEngine
 def build():
  return RewardEngine(np.array([0,1,3,4,4,4,4,4]),np.array([1,3,5,6]),np.array([100.,100.,1.,1.],np.float32),np.array([0]),np.array([1,2]),np.array([3,4]),np.array([0,1]),np.array([2,3]),np.array([0,1]),np.array([0,1]),n_compartments=2,learning_rule='rate-bridge-v1',dan_reference='none',plasticity_onset_ms=100,dan_baseline_window_ms=50)
 e=build();sample=np.arange(5,dtype=np.int32)
 maps=dict(sample=sample,kc_columns=np.array([1,2]),dan_columns=np.array([3,4]),sensory_columns=np.array([0]),kc_indices=np.array([1,2]),dan_indices=np.array([3,4]),sensory_indices=np.array([0]),dan_compartments=np.array([0,1]),plastic_kc_indices=np.array([0,1]),plastic_compartments=np.array([0,1]),plastic_mask=np.array([1,1],np.uint8),plastic_groups=np.array([0,4]))
 rows=exact_rows();games=sorted({r['game'] for r in rows});pilot=tmp_path/'pilot';(pilot/'source').mkdir(parents=True)
 np.savez(pilot/'source/inputs.npz',X=np.zeros((16,1)),source_indices=np.array(games),input_mean=np.zeros(1),input_std=np.ones(1))
 def encode(x):return np.array([600.],np.float32)
 schedule=np.zeros((40,1),np.float32);schedule[:30]=encode(None)
 for rid in m.RUNS:
  p=tmp_path/'output/diagnostics'/rid;p.mkdir(parents=True);selected=[r for r in rows if r['run_id']==rid]
  arrays={'sampled':sample};replay={}
  for row in selected:
   obj=build();res=obj.run(schedule,seed=row['seed'],sample=sample,record=True,plastic_groups=np.array([0,4]),n_groups=8)
   pre=f"{row['game']}__{row['seed_set']}__untaught"
   arrays.update({pre+'__'+key:res[key] for key in ('gains','gain_delta')})
   arrays[pre+'__sensory_bins']=res['trace'][:,[0]];arrays[pre+'__dan_bins']=res['trace'][:,[3,4]]
   arrays[pre+'__step_signals']=res['instrumentation']['step_signals'];arrays[pre+'__bridge_rule']=res['instrumentation']['bridge_rule'];arrays[pre+'__bridge_tail']=res['instrumentation']['bridge_tail'];arrays[pre+'__sampled_bins']=res['trace']
   if row==rows[0]:replay={'untaught':{'original':{k:[str(v.dtype),list(v.shape),m.array_identity(v)['sha256']] for k,v in res.items() if isinstance(v,np.ndarray)}}}
  np.savez(p/'trials.npz',**arrays);(p/'summary.json').write_text(json.dumps({'panel_games':[selected[0]['game']]}));(p/'replay-evidence.json').write_text(json.dumps(replay))
 identity=dict(rows=rows,pilot=str(pilot),protocol={},native_binary={'sha256':m.sha(e.lib._name)})
 frozen=dict(run_id='tiny-native-history',identity=identity)
 monkeypatch.setattr(m,'ROOT',tmp_path);monkeypatch.setattr(m,'verify_receipt',lambda p:(frozen,maps));monkeypatch.setattr(m,'frozen_context',lambda:(identity,maps))
 monkeypatch.setattr(protocol_module,'make_circuit',lambda *a,**k:(build(),{},[],np.array([0,1]),np.array([1,2]),np.array([0]),encode))
 out=tmp_path/'capture';out.mkdir();m.run_worker(tmp_path/'dummy-receipt',out)
 report=json.loads((out/'summary.json').read_text());attempts=json.loads((out/'attempts.json').read_text())
 assert report['calls']==report['attempted_calls']==attempts['attempted_calls']==33
 assert len(report['rows'])==32 and len(list(out.glob('shadow_*.npz')))==64
 assert all(r['actual_checkpoint_unchanged_by_shadow'] for r in report['rows'])
 assert report['qualification'] is False
 assert set(report['metrics'])=={f'{rid}/{ss}/{c}' for rid in m.RUNS for ss in ('base','alt') for c in range(2)}
 assert len(report['saved'])==33


def test_actual_read_only_capture_identity_and_mapping_roundtrip(monkeypatch,tmp_path):
 """Real frozen metadata only; no circuit construction or execution."""
 import json
 identity,maps=m.frozen_context()
 assert identity==json.loads(json.dumps(identity)), 'Nested identity must survive its persisted JSON representation'
 monkeypatch.setattr(m,'frozen_context',lambda:(identity,maps))
 p=tmp_path/'real-context-receipt.json';f=m.freeze(p);again,reopened=m.verify_receipt(p)
 assert again==f
 for key,a in maps.items():np.testing.assert_array_equal(a,reopened[key])
