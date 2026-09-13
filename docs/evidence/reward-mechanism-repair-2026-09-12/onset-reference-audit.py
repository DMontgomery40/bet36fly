"""Independent fixed-history oracle: closed event pairs and direct impulse quadrature.
No production imports, native calls, circuit replay or parameter search.
"""
from pathlib import Path
import json
import math
import numpy as np
from scipy.integrate import quad

ALPHA, BETA, ETA, NORM, DT = 1/500., 1/100., .0005, .96, .2

def state(events, time, before=False):
    values = [(time-t, mass) for t,mass in events if t < time or (not before and t == time)]
    rate = math.fsum(m*BETA*math.exp(-BETA*u) for u,m in values)
    eligibility = math.fsum(m*BETA/(BETA-ALPHA)*(math.exp(-ALPHA*u)-math.exp(-BETA*u)) for u,m in values)
    return rate, eligibility

def pair_integral(kc, dan, lo, hi=math.inf, scale=1.):
    terms=[]
    for tk,mk in kc:
        for td,md in dan:
            first=max(tk,td,lo)
            if first >= hi or tk == td:
                continue
            lag=abs(td-tk)
            value=-math.copysign(1.,td-tk)*ETA*scale*mk*md*(math.exp(-ALPHA*lag)-math.exp(-BETA*lag))
            value*=math.exp(-(ALPHA+BETA)*(first-max(tk,td)))
            if math.isfinite(hi):
                value*=-math.expm1(-(ALPHA+BETA)*(hi-first))
            terms.append(value)
    return math.fsum(terms)

def true_areas(kc,dan,lo,hi=math.inf,scale=1.):
    def pos(t):
        rk,_=state(kc,t); _,ed=state(dan,t)
        return ETA*NORM*scale*ed*rk
    def neg(t):
        _,ek=state(kc,t); rd,_=state(dan,t)
        return -ETA*NORM*scale*ek*rd
    cuts=sorted({lo,*[t for t,_ in kc+dan if lo<t<hi],hi})
    return [math.fsum(quad(f,a,b,epsabs=1e-13,epsrel=1e-11,limit=300)[0] for a,b in zip(cuts,cuts[1:])) for f in (pos,neg)]

def reference(kc,dan,*,warm,onset=100.,end=400.,scale=1.):
    k=[(float(t),float(m)) for t,m in kc if warm or t>=onset]
    d=[(float(t),float(m)) for t,m in dan if warm or t>=onset]
    gain=1.; pub=np.float32(1.); applied=[]; published=[]; attempted=[]; bound=[]
    start=int(round(onset/DT)); stop=int(round(end/DT))
    for i in range(start,stop):
        v=pair_integral(k,d,i*DT,(i+1)*DT,scale)
        before=gain; fbefore=pub; proposal=gain+v
        gain=min(1.5,max(.5,proposal)); pub=np.float32(gain)
        attempted.append(v); applied.append(gain-before); published.append(float(pub)-float(fbefore))
        bound.append([int(proposal<=.5 or pub<=.5),int(proposal>=1.5 or pub>=1.5)])
    tail=pair_integral(k,d,end,scale=scale)
    before=gain; fbefore=pub; proposal=gain+tail
    gain=min(1.5,max(.5,proposal)); pub=np.float32(gain)
    areas=true_areas(k,d,onset,end,scale); tail_areas=true_areas(k,d,end,scale=scale)
    for v,target in ((sum(areas),math.fsum(attempted)),(sum(tail_areas),tail)):
        assert math.isclose(v,target,rel_tol=1e-8,abs_tol=1e-10),(v,target)
    return dict(onset_kc=list(state(k,onset,before=True)),onset_dan=list(state(d,onset,before=True)),
                interval_attempted=math.fsum(attempted),interval_double_applied=math.fsum(applied),
                interval_published=math.fsum(published),true_areas=areas,tail_true_areas=tail_areas,
                tail_attempted=tail,tail_double_applied=gain-before,tail_published=float(pub)-float(fbefore),
                interval_bounds=np.sum(bound,axis=0).tolist(),tail_bounds=[int(proposal<=.5 or pub<=.5),int(proposal>=1.5 or pub>=1.5)],
                final_double=gain,final_published=float(pub),
                pair_post_onset_total=pair_integral(k,d,onset,scale=scale),
                published_reconciliation=math.fsum(published)+float(pub)-float(fbefore)-(float(pub)-1.))

CASES={
 'empty':([],[]),
 'coincident_at_boundary':([(100.,1.)],[(100.,1.)]),
 'pre_only_k_then_d':([(20.,1.)],[(80.,1.)]),
 'pre_only_d_then_k':([(80.,1.)],[(20.,1.)]),
 'cross_boundary_k_first':([(99.8,1.)],[(100.,1.)]),
 'cross_boundary_d_first':([(100.,1.)],[(99.8,1.)]),
 'boundary_then_next':([(100.,1.)],[(100.2,1.)]),
 'mixed':([(0.,1.),(99.8,1.),(100.,1.),(100.2,1.),(270.,1.)],[(30.,.5),(100.,.5),(150.,.5),(310.,.5)]),
 'partial_population':([(10.,1.),(100.,1.)],[(80.,1/22),(100.2,2/22),(300.,1/22)]),
 'one_sided':([(10.,1.),(100.,1.)],[]),
 'no_prehistory':([(100.,1.),(120.,1.)],[(105.,1.),(310.,1.)]),
 'sub_ulp_after_gate':([(100.,1.)],[(100.2,1.)]),
}

def main():
    results={}
    for name,(k,d) in CASES.items():
        results[name]={m:reference(k,d,warm=m=='warm') for m in ('cold','warm')}
        for v in results[name].values():
            assert v['published_reconciliation']==0
            assert math.isclose(v['pair_post_onset_total'],v['interval_attempted']+v['tail_attempted'],rel_tol=1e-12,abs_tol=1e-14)
    for name in ('empty','coincident_at_boundary','no_prehistory','boundary_then_next'):
        assert results[name]['cold']==results[name]['warm']
    assert results['one_sided']['cold']['final_published']==results['one_sided']['warm']['final_published']==1.
    assert results['pre_only_k_then_d']['cold']['final_published']==1.
    assert results['pre_only_k_then_d']['warm']['pair_post_onset_total']<0
    assert results['pre_only_d_then_k']['warm']['pair_post_onset_total']>0
    assert results['cross_boundary_k_first']['cold']['final_published']==1.
    assert results['cross_boundary_k_first']['warm']['onset_dan']==[0.,0.]
    assert results['cross_boundary_k_first']['warm']['onset_kc'][0]>0
    # Deliberate mutant: double the event exactly at the write boundary.
    original=results['cross_boundary_k_first']['warm']['pair_post_onset_total']
    duplicate=pair_integral([(99.8,1.)],[(100.,2.)],100.)
    assert math.isclose(duplicate,2*original,rel_tol=1e-12)
    results['duplicate_boundary_mutant']={'correct':original,'mutant':duplicate,'detected':duplicate!=original}
    # Stress clipping only, same time constants: opposite orders force sign reversals.
    k=[(0.,50.),(220.,50.),(390.,50.)]; d=[(80.,50.),(150.,50.),(300.,50.)]
    results['clipped_mixed']=reference(k,d,warm=True,scale=2000.)
    assert sum(results['clipped_mixed']['interval_bounds'])>0
    output={'assumptions':{'dt':DT,'tau_e':500.,'tau_r':100.,'eta':ETA,'normalization':NORM,'onset':100.,'end':400.,'independent_method':'closed pair integrals; direct impulse-response quadrature; gain clamp per declared .2ms interval and tail'},'cases':results}
    path=Path(__file__).with_suffix('.json'); path.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'cases':len(results),'all_assertions_passed':True,'output':str(path)}))

if __name__=='__main__':main()
