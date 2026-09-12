"""Read stored full-CNS bridge evidence; no simulator import or circuit execution."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def array_digest(value):
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def verify(run_id):
    path = ROOT / 'output/diagnostics' / run_id
    s = json.loads((path / 'summary.json').read_text())
    assert s['run_id'] == run_id
    assert s['panel_complete'] is True and s['source_unchanged_during_run'] is True
    assert s['identity']['protocol']['learning_rule'] == 'rate-bridge-v1'
    for name, meta in s['artifacts'].items():
        assert name in {'trials.npz', 'recording-layout.json', 'replay-evidence.json'}
        assert digest(path / name) == meta['sha256']
        assert (path / name).stat().st_size == meta['bytes']
    assert set(s['artifacts']) == {'trials.npz', 'recording-layout.json', 'replay-evidence.json'}
    layout = json.loads((path / 'recording-layout.json').read_text())
    assert layout['layout_version'] == 'rate-bridge-v1/1'
    assert layout['config']['tail'] == 'analytic_no_new_event_tail'
    rows = s['rows']
    assert len(rows) == 64
    expected = s['identity']['selection']['expected_panel']
    assert [{k:r[k] for k in ('game','seed_set','seed','condition')} for r in rows] == expected
    assert len({(r['game'],r['seed_set'],r['condition']) for r in rows}) == 64
    conditions = ('frozen', 'untaught', 'home', 'away')
    replay = json.loads((path / 'replay-evidence.json').read_text())
    assert set(replay) == set(conditions)
    assert all(v['original'] == v['repeat'] and len(v['original']) > 10 for v in replay.values())
    sums, sensory, total_bounds, max_reconciliation_error = {}, {}, 0, 0.
    with np.load(path / 'trials.npz', allow_pickle=False) as z:
        pc, mask = z['plastic_compartments'], z['plastic_mask'].astype(bool)
        groups = z['plastic_groups']
        np.testing.assert_array_equal(mask, (pc == 0) | (z['kc_classes'] == 0))
        assert np.count_nonzero(mask & (pc == 0)) == 4184
        assert np.count_nonzero(mask & (pc == 1)) == 3239
        np.testing.assert_array_equal(z['blank_gains'], 1)
        blank = z['blank_gains']
        def reduction(prefix, before, evidence):
            nonlocal total_bounds, max_reconciliation_error
            gains, rule, tail = z[prefix+'__gains'], z[prefix+'__bridge_rule'], z[prefix+'__bridge_tail']
            assert rule.shape == (2000,8,8) and tail.shape == (8,8)
            assert rule.dtype == tail.dtype == np.float64
            assert np.isfinite(rule).all() and np.isfinite(tail).all() and np.isfinite(gains).all()
            assert not rule[:500].any()
            np.testing.assert_array_equal(gains[~mask], blank[~mask])
            counts = rule[...,5:7].sum() + tail[:,5:7].sum()
            assert counts >= 0 and counts == int(counts) == evidence['clipped']
            assert rule[...,5:7].sum() == evidence['electrical_bound_observations']
            assert tail[:,5:7].sum() == evidence['tail_bound_observations']
            total_bounds += int(counts)
            for a in (rule, tail):
                np.testing.assert_allclose(a[...,0]+a[...,1], a[...,2], rtol=1e-8, atol=1e-11)
            total = rule.sum(0) + tail
            actual = gains.astype(float)-before.astype(float)
            result = np.array([actual[pc==c].sum() for c in (0,1)])
            recorded = np.array([total[np.arange(8)//4==c,4].sum() for c in (0,1)])
            error = float(np.abs(result-recorded).max())
            max_reconciliation_error = max(max_reconciliation_error,error)
            np.testing.assert_allclose(result, recorded, rtol=0, atol=1e-6)
            np.testing.assert_allclose(result, evidence['applied'], rtol=0, atol=1e-6)
            assert np.all(gains[mask] > .5) and np.all(gains[mask] < 1.5)
            return gains, result
        for r in rows:
            key = (r['game'],r['seed_set'],r['condition'])
            prefix = '__'.join(map(str,key))
            gains, result = reduction(prefix, blank, r)
            sums[key] = result
            if r['condition'] == 'frozen':
                np.testing.assert_array_equal(gains, blank)
            a = z[prefix+'__sensory_bins']
            assert array_digest(a) == r['sensory_bins_sha256']
            sensory.setdefault(key[:2],[]).append(array_digest(a))
            if r['game'] == s['panel_games'][0] and r['seed_set'] == 'base':
                checks = {'gains':gains, 'gain_delta':z[prefix+'__gain_delta'], 'trace':z[prefix+'__sampled_bins']}
                checks.update({'instrumentation/'+name:z[prefix+'__'+name] for name in
                              ('bridge_rule','bridge_tail','bridge_signals','bridge_kc_bins','bridge_kc_used')})
                for name,a in checks.items():
                    assert replay[r['condition']]['original'][name] == [str(a.dtype),list(a.shape),array_digest(a)]
        cumulative = s['cumulative_rows']
        expected_cumulative = s['identity']['selection']['expected_cumulative']
        assert [{k:r[k] for k in ('game','seed')} for r in cumulative] == expected_cumulative
        assert len(cumulative) == 16
        before = blank
        for r in cumulative:
            before, _ = reduction('cumulative_'+str(r['game']), before, r)
            np.testing.assert_allclose([np.sum((before.astype(float)-1)[pc==c]) for c in (0,1)],r['cumulative'],rtol=0,atol=1e-6)
        np.testing.assert_array_equal(before,z['cumulative_final_gains'])
        final = np.array([np.sum((before.astype(float)-1)[pc==c]) for c in (0,1)])
    criteria = dict(teaching_specific=True, untaught_guard=True, cross_compartment=True,
                    no_bound_hits=total_bounds==0, cumulative=True,
                    bit_identical_repeat=True, sensory_noise_invariance=all(len(v)==4 and len(set(v))==1 for v in sensory.values()))
    mean_effects = {0:[],1:[]}
    metrics = {}
    for seed_set in ('base','alt'):
        effects = {}
        for c,label in enumerate(('home','away')):
            u = np.array([sums[(g,seed_set,'untaught')][c] for g in s['panel_games']])
            e = np.array([sums[(g,seed_set,label)][c]-sums[(g,seed_set,'untaught')][c] for g in s['panel_games']])
            effects[label] = e.mean(); mean_effects[c].append(e.mean())
            guard = abs(u.mean()) <= .5*u.std(ddof=1)
            teaching = e.mean() < 0 and abs(e.mean()) >= 3*abs(u.mean())
            criteria['untaught_guard'] &= bool(guard)
            criteria['teaching_specific'] &= bool(teaching)
            metrics[f'{label}/{seed_set}'] = dict(mean_untaught=float(u.mean()),guard_limit=float(.5*u.std(ddof=1)),mean_teaching=float(e.mean()))
        for label,c in (('home',1),('away',0)):
            leak = np.mean([sums[(g,seed_set,label)][c]-sums[(g,seed_set,'untaught')][c] for g in s['panel_games']])
            criteria['cross_compartment'] &= bool(abs(leak) <= .05*abs(effects[label]))
    criteria['cumulative'] = bool(all(abs(final[c]) <= 4*abs(np.mean(mean_effects[c])) for c in (0,1)))
    assert criteria == {k:v['passed'] for k,v in s['criteria'].items()}
    assert all(criteria.values()) == s['all_passed']
    return dict(run_id=run_id,summary_sha256=digest(path/'summary.json'),artifacts=s['artifacts'],criteria=criteria,
                independently_recomputed=True,complete_panel_rows=64,complete_cumulative_rows=16,
                replay_scope='Persisted full-array fingerprints compared; retained original gain/trace/bridge arrays also matched to original fingerprints.',
                sensory_groups=16,bound_observations=total_bounds,max_publication_reconciliation_error=max_reconciliation_error,
                metrics=metrics,cumulative_final=final.tolist())

if __name__ == '__main__':
    result = verify(sys.argv[1])
    out = Path(sys.argv[2])
    assert not out.exists(), out
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
