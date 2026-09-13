"""Saved-array-only residual attribution. No production imports, native calls or fitted parameters."""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
import pyarrow.feather as feather

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent
RUNS = {
 'bridge_original': 'diag-rate-bridge-v1-maskgamma-de050d773763',
 'bridge_second': 'diag-rate-bridge-v1-maskgamma-dea14759e9ca',
 'raw_original': 'diag-candidate-maskgamma-29c766f95f82',
 'raw_second': 'diag-candidate-maskgamma-e3d8898dc68a',
}
FAMILIES = ('gamma','apbp','ab','other')
PHASES = {'early_100_130':(500,650),'late_130_300':(650,1500),'post_300_400':(1500,2000)}

def sha(path):
 with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def main():
 ids=np.load(ROOT/'data/brain/ids.npy'); kc=np.load(ROOT/'data/brain/kc.npy')
 nodes=feather.read_table(ROOT/'data/brain/nodes.feather',columns=['bodyId','type']).to_pandas()
 types=nodes.set_index('bodyId').reindex(ids)['type'].fillna('').to_numpy()
 report={'scope':'Descriptive saved-array attribution; no circuit execution, surrogates, parameter changes or causal pathway inference. Gain sums are edge units, not anatomical contact-weighted.', 'runs':{},'comparison':{}}
 per_kc=[]; per_family=[]
 for label,runid in RUNS.items():
  p=ROOT/'output/diagnostics'/runid; s=json.loads((p/'summary.json').read_text()); bridge=label.startswith('bridge')
  for path in ('data/brain/ids.npy','data/brain/kc.npy','data/brain/nodes.feather'):
   assert sha(ROOT/path)==s['identity']['graph_hashes'][path]
  checks={'q_max_error':0.,'tail_max_error':0.,'net_max_error':0.,'endpoint_mass_max_error':0.,'dan_signal_max_error':0.,'pre_onset_learning_zero':True}
  d={'run_id':runid,'summary_sha256':sha(p/'summary.json'),'trials_sha256':sha(p/'trials.npz'),'measured_code_hashes':s['identity']['code_hashes'],'all_passed':s['all_passed'],'rows':[],'seed_sets':{}}
  if bridge: assert d['trials_sha256']==s['artifacts']['trials.npz']['sha256']
  with np.load(p/'trials.npz',allow_pickle=False) as z:
   pc,pk,groups=z['plastic_compartments'],z['plastic_kc_indices'],z['plastic_groups']; hm=pc==0
   home_kcs=np.unique(pk[hm]); multiplicity=np.bincount(pk[hm],minlength=len(kc)); hgroup=np.full(len(kc),-1)
   for g in range(4): hgroup[pk[groups==g]]=g
   d['home_edges']=int(hm.sum()); d['home_unique_kcs']=len(home_kcs);d['home_edge_multiplicity']=dict(zip(*[v.tolist() for v in np.unique(multiplicity[home_kcs],return_counts=True)]))
   d['home_family_edges']={f:int((groups==g).sum()) for g,f in enumerate(FAMILIES)}
   allnets={}; alltails={}
   for row in s['rows']:
    if row['condition']!='untaught': continue
    prefix=f"{row['game']}__{row['seed_set']}__untaught"; net=z[prefix+'__gain_delta'].astype(float)
    bykc=np.bincount(pk[hm],weights=net[hm],minlength=len(kc)); assert np.isfinite(net).all()
    np.testing.assert_array_equal(net[hm],bykc[pk[hm]]/multiplicity[pk[hm]])
    allnets[(row['game'],row['seed_set'])]=bykc
    a={'game':row['game'],'seed_set':row['seed_set'],'seed':row['seed'],'total':float(net[hm].sum()),'sensory_hash':row['sensory_bins_sha256'],'families':{},'phase_total':{},'dan_spikes':{},'kc_spikes':row['kc_spikes']}
    step=z[prefix+'__step_signals']; dan=z[prefix+'__dan_bins']; dc=z['dan_compartments']; sampled=z['sampled']; output_count=len(sampled)-len(dc)-len(kc)-len(np.load(ROOT/'data/brain/sensory.npy'))
    for n in np.flatnonzero(dc==0):
     globalidx=sampled[output_count+n]
     a['dan_spikes'][str(ids[globalidx])]={phase:int(dan[start:end,n].sum()) for phase,(start,end) in {'pre':(0,10),'stimulus':(10,30),'post':(30,40)}.items()}
    if bridge:
     rule=z[prefix+'__bridge_rule'];tail=z[prefix+'__bridge_tail'];sig=z[prefix+'__bridge_signals'];used=z[prefix+'__bridge_kc_used'];end=z[prefix+'__bridge_kc_bins'][-1]
     h=.2;r=.01;e=.002;eta=.0005;norm=.96;ar=np.exp(-r*h);ae=np.exp(-e*h);coupling=(ae-ar)/(r-e)
     q=sig[:,0,1,None]*used[:,:4,0]-sig[:,0,0,None]*used[:,:4,1]
     checks['q_max_error']=max(checks['q_max_error'],float(np.max(abs(q-rule[:,:4,7]))))
     checks['pre_onset_learning_zero'] &= not bool(rule[:500].any() or sig[:500].any() or z[prefix+'__bridge_kc_bins'][:10].any())
     # Independently closed impulse convolution of actual compartment-mean DAN spike sequence.
     event=step[:,1].copy();event[:500]=0;lag=np.arange(len(event))*h
     rd=np.convolve(event,r*np.exp(-r*lag))[:len(event)]
     ed=np.convolve(event,r*(np.exp(-e*lag)-np.exp(-r*lag))/(r-e))[:len(event)]
     checks['dan_signal_max_error']=max(checks['dan_signal_max_error'],float(np.max(abs(rd-sig[:,0,0]))),float(np.max(abs(ed-sig[:,0,1]))))
     rend=rd[-1]*ar;eend=ed[-1]*ae+rd[-1]*coupling
     ktail=eta*norm/(r+e)*(eend*end[:,0]-rend*end[:,1]);alltails[(row['game'],row['seed_set'])]=ktail*multiplicity
     for g in range(4):
      mask=groups==g
      predicted=ktail[pk[mask]].sum()
      checks['tail_max_error']=max(checks['tail_max_error'],abs(float(predicted-tail[g,2])))
      checks['endpoint_mass_max_error']=max(checks['endpoint_mass_max_error'],abs(float(end[pk[mask],0].sum()-used[-1,g,0]*ar)),abs(float(end[pk[mask],1].sum()-(used[-1,g,1]*ae+used[-1,g,0]*coupling))))
     total=rule.sum(0)+tail
     checks['net_max_error']=max(checks['net_max_error'],abs(float(total[:4,4].sum()-a['total'])))
     for phase,(start,stop) in PHASES.items():a['phase_total'][phase]=float(rule[start:stop,:4,4].sum())
     a['phase_total']['tail']=float(tail[:4,4].sum())
     a['silent_320_400_published']=float(rule[1600:,:4,4].sum()); assert not step[1600:,:3].any()
     a['home_dan_spikes_after_onset']=float(step[500:,1].sum()*2)
     a['home_dan_spikes_before_onset']=float(step[:500,1].sum()*2)
     a['electrical_positive']=float(rule[:,:4,0].sum());a['electrical_negative']=float(rule[:,:4,1].sum());a['tail_positive']=float(tail[:4,0].sum());a['tail_negative']=float(tail[:4,1].sum())
     a['last_home_dan_spike_ms']=float(np.flatnonzero(step[:,1])[-1]*h) if step[:,1].any() else None
     a['last_any_kc_spike_ms']=float(np.flatnonzero(step[:,0])[-1]*h) if step[:,0].any() else None
     for g,f in enumerate(FAMILIES):
      phases={name:float(rule[start:stop,g,4].sum()) for name,(start,stop) in PHASES.items()};phases['tail']=float(tail[g,4])
      a['families'][f]={'net':float(net[groups==g].sum()),'phases':phases,'attempted':float(total[g,2]),'positive':float(total[g,0]),'negative':float(total[g,1])}
    else:
     rb=z[prefix+'__rule_bins'];assert rb.shape==(40,8,7)
     for name,(start,stop) in PHASES.items(): a['phase_total'][name]=float(rb[start//50:stop//50,:4,2].sum())
     a['phase_total']['tail']=0.
     for g,f in enumerate(FAMILIES): a['families'][f]={'net':float(net[groups==g].sum()),'phases':{name:float(rb[start//50:stop//50,g,2].sum()) for name,(start,stop) in PHASES.items()}}
    for j in home_kcs:
     rec={'run':label,'game':row['game'],'seed_set':row['seed_set'],'kc_body_id':int(ids[kc[j]]),'type':str(types[kc[j]]),'family':FAMILIES[hgroup[j]],'eligible_home_edges':int(multiplicity[j]),'published_net_sum':float(bykc[j]),'mean_edge_net':float(bykc[j]/multiplicity[j])}
     if bridge: rec['analytic_tail_attempted_sum']=float(ktail[j]*multiplicity[j]);rec['finite_net_minus_exact_tail']=rec['published_net_sum']-rec['analytic_tail_attempted_sum']
     per_kc.append(rec)
    ranked=home_kcs[np.argsort(bykc[home_kcs])];neg=-np.minimum(bykc,0);a['negative_mass']=float(neg.sum());a['positive_mass']=float(np.maximum(bykc,0).sum());a['negative_kcs']=int((bykc[home_kcs]<0).sum());a['positive_kcs']=int((bykc[home_kcs]>0).sum());a['zero_kcs']=int((bykc[home_kcs]==0).sum())
    a['top10_negative_mass_share']=float(neg[ranked[:10]].sum()/neg.sum()) if neg.sum() else 0
    a['top10_negative_kcs']=[{'body_id':int(ids[kc[j]]),'type':str(types[kc[j]]),'net':float(bykc[j]),'edges':int(multiplicity[j])} for j in ranked[:10]]
    d['rows'].append(a)
   for ss in ('base','alt'):
    rows=[a for a in d['rows'] if a['seed_set']==ss];u=np.array([a['total'] for a in rows]);mean_kc=np.mean([allnets[(a['game'],ss)] for a in rows],axis=0);neg=-np.minimum(mean_kc,0);ranked=home_kcs[np.argsort(mean_kc[home_kcs])]
    stat={'mean':float(u.mean()),'sd':float(u.std(ddof=1)),'guard_limit':float(.5*u.std(ddof=1)),'passes_guard':bool(abs(u.mean())<=.5*u.std(ddof=1)),'family_mean':{f:float(np.mean([a['families'][f]['net'] for a in rows])) for f in FAMILIES},'phase_mean':{name:float(np.mean([a['phase_total'][name] for a in rows])) for name in (*PHASES,'tail')},'negative_trial_count':int((u<0).sum()),'mean_net_negative_kcs':int((mean_kc[home_kcs]<0).sum()),'mean_net_positive_kcs':int((mean_kc[home_kcs]>0).sum()),'mean_net_zero_kcs':int((mean_kc[home_kcs]==0).sum()),'top10_negative_mass_share':float(neg[ranked[:10]].sum()/neg.sum()),'top100_negative_mass_share':float(neg[ranked[:100]].sum()/neg.sum()),'top10_kcs':[{'body_id':int(ids[kc[j]]),'type':str(types[kc[j]]),'mean_net':float(mean_kc[j]),'edges':int(multiplicity[j])} for j in ranked[:10]]}
    for f in FAMILIES:
     for name in (*PHASES,'tail'):
      per_family.append({'run':label,'seed_set':ss,'family':f,'phase':name,'mean_published_change':float(np.mean([a['families'][f]['phases'].get(name,0) for a in rows]))})
    d['seed_sets'][ss]=stat
   if bridge:
    assert checks['q_max_error']<1e-9 and checks['tail_max_error']<1e-10 and checks['net_max_error']<1e-10 and checks['dan_signal_max_error']<1e-10 and checks['endpoint_mass_max_error']<1e-9 and checks['pre_onset_learning_zero']
    d['checks']=checks
  report['runs'][label]=d
 for panel in ('original','second'):
  b=report['runs']['bridge_'+panel];raw=report['runs']['raw_'+panel]
  pairs=[]
  for br,rr in zip(b['rows'],raw['rows']):
   assert (br['game'],br['seed_set'],br['seed'])==(rr['game'],rr['seed_set'],rr['seed'])
   assert br['sensory_hash']==rr['sensory_hash']
   pairs.append({'game':br['game'],'seed_set':br['seed_set'],'raw':rr['total'],'bridge':br['total'],'ratio':br['total']/rr['total'] if rr['total'] else None,'same_sensory':True,'same_dan_phase_counts':br['dan_spikes']==rr['dan_spikes'],'same_aggregate_kc_phase_counts':br['kc_spikes']==rr['kc_spikes']})
  with np.load(ROOT/'output/diagnostics'/b['run_id']/'trials.npz') as bz, np.load(ROOT/'output/diagnostics'/raw['run_id']/'trials.npz') as rz:
   for pair in pairs:
    prefix=f"{pair['game']}__{pair['seed_set']}__untaught"
    bs,rs=bz[prefix+'__step_signals'],rz[prefix+'__step_signals']
    pair['same_home_dan_mean_per_step']=bool(np.array_equal(bs[:,1],rs[:,1]))
    pair['same_aggregate_kc_count_per_step']=bool(np.array_equal(bs[:,0],rs[:,0]))
  report['comparison'][panel]=pairs
 (OUT/'bridge-residual-attribution.json').write_text(json.dumps(report,indent=2)+'\n')
 for filename,rows in [('bridge-residual-per-kc.csv',per_kc),('bridge-residual-family-phase.csv',per_family)]:
  fields=list(dict.fromkeys(k for row in rows for k in row))
  with (OUT/filename).open('w') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 print(json.dumps({label:{'home_unique_kcs':d['home_unique_kcs'],'checks':d.get('checks'), 'seed_sets':{ss:{k:v for k,v in stat.items() if k!='top10_kcs'} for ss,stat in d['seed_sets'].items()}} for label,d in report['runs'].items()},indent=2))

if __name__=='__main__':main()
