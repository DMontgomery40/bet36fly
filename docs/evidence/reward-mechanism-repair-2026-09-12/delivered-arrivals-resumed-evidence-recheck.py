"""Independent read-only correction probes; no ASGI server or native engine import."""
import hashlib
import json
import subprocess
import sys
import tempfile
from itertools import product
from pathlib import Path

import numpy as np

from bet36fly.reward_evidence import EvidenceInvalid, _bridge_reduction, _failed_pair_members, list_reward_evidence

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_suffix('.json')
RELEASE = ROOT / 'output/collaboration/reward-mechanism-repair/task4b-release-hashes.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bridge_case(name, values, groups, *, published=True, bound_counts=False, rejected=True):
    before = np.ones(2, dtype=np.float32)
    gains = np.array(values, dtype=np.float32)
    groups = np.array(groups, dtype=np.int32)
    tail = np.zeros((8, 8), dtype=np.float64)
    if published:
        for i, group in enumerate(groups):
            tail[group, 4] += float(gains[i]) - 1
    if bound_counts:
        for i, group in enumerate(groups):
            tail[group, 5] += gains[i] <= .5
            tail[group, 6] += gains[i] >= 1.5
    count = int(tail[:, 5:7].sum())
    row = dict(applied=[float((gains.astype(np.float64)-1).sum()), 0], clipped=count,
               electrical_bound_observations=0, tail_bound_observations=count)
    archive = {'x__gains': gains, 'x__gain_delta': gains-before,
               'x__bridge_rule': np.zeros((500, 8, 8)), 'x__bridge_tail': tail}
    try:
        result = _bridge_reduction(archive, 'x', before, row, np.ones(2, dtype=bool),
                                   np.zeros(2, dtype=np.int32), groups, 500)
    except EvidenceInvalid as exc:
        assert rejected, (name, str(exc))
        return dict(case=name, rejected=True, reason=str(exc))
    assert not rejected, name
    return dict(case=name, rejected=False, bound_observations=result[4])


def main():
    assert not OUT.exists(), 'Preserve prior recheck output.'
    release = json.loads(RELEASE.read_text())
    assert all(digest(ROOT/path) == value for path, value in release.items())
    bridge = []
    for values, kind in [([.375, 1.625], 'outside'), ([.5, 1.5], 'exact'),
                         ([.5, 1], 'low-only'), ([1, 1.5], 'high-only')]:
        for groups in ([0, 0], [0, 2]):
            bridge.append(bridge_case(f'{kind}-{groups}', values, groups))
    bridge.append(bridge_case('unreported-distinct-groups', [.875, 1.125], [0, 2], published=False))
    bridge.append(bridge_case('zero-effect-control', [1, 1], [0, 2], rejected=False))
    bridge.append(bridge_case('properly-recorded-cancelling-groups', [.875, 1.125], [0, 2], rejected=False))
    bridge.append(bridge_case('recorded-exact-endpoints', [.5, 1.5], [0, 2], bound_counts=True, rejected=False))

    metadata = []
    payloads = []
    fields = ['dan_reference', 'away_plasticity_mask', 'bridge_tail', 'bridge_layout',
              'native_binary_sha256', 'source_code_hashes']
    with tempfile.TemporaryDirectory(prefix='bet36fly-evidence-independent-', dir='/private/tmp') as temporary:
        base = Path(temporary)
        for field, bad in product(fields, [{'wrong': 'object'}, ['unexpected'], 123, True]):
            case = f'{field}-{type(bad).__name__}'
            case_root = base/case
            healthy = dict(run_id='diag-good', rule='candidate', panel_complete=True, all_passed=True,
                           identity={'protocol': {'dan_reference': 'none', 'away_plasticity_mask': 'gamma'},
                                     'code_hashes': {}}, criteria={})
            malformed = json.loads(json.dumps(healthy))
            malformed['run_id'] = 'diag-malformed'
            if field == 'native_binary_sha256':
                malformed['native_binary'] = {'sha256': bad}
            elif field == 'source_code_hashes':
                malformed['identity']['code_hashes'] = {'reward_lif.cpp': bad}
            else:
                malformed['identity']['protocol'][field] = bad
            for row in (healthy, malformed):
                directory = case_root/'output/diagnostics'/row['run_id']
                directory.mkdir(parents=True)
                (directory/'summary.json').write_text(json.dumps(row))
            payload = list_reward_evidence(case_root)
            entries = {entry['run_id']: entry for entry in payload['diagnostics']}
            assert entries['diag-malformed']['validation_status'] == 'invalid', case
            assert entries['diag-malformed']['evidence_status'] == 'unverified', case
            assert entries['diag-good']['validation_status'] == 'stored-only', case
            metadata.append(dict(case=case, malformed='invalid/unverified', healthy='stored-only'))
            payloads.append(dict(case=case, diagnostics=payload))

    program = r'''
const esbuild=require('esbuild');
const code=esbuild.buildSync({entryPoints:['src/RewardEvidence.tsx'],bundle:true,platform:'node',format:'cjs',write:false,jsx:'automatic',external:['react']}).outputFiles[0].text;
const loaded={exports:{}};
new Function('require','module','exports',code)(require,loaded,loaded.exports);
const React=require('react'),{renderToStaticMarkup}=require('react-dom/server');
const payloads=JSON.parse(require('fs').readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(payloads.map(({case:name,diagnostics})=>{
 const html=renderToStaticMarkup(React.createElement(loaded.exports.RewardEvidenceView,{diagnostics,diagnosticsLoading:false,diagnosticsError:'',experiments:null,experimentsError:'',selectedExperimentId:'',selectedJobId:'',onSelectExperiment:()=>{},onSelectJob:()=>{}}));
 if(!html.includes('diag-malformed')||!html.includes('diag-good')||html.includes('validated passed'))throw Error(name);
 return {case:name,rendered:true,malformedAndHealthyVisible:true};
})));
'''
    rendered = subprocess.run(['node', '-e', program], cwd=ROOT/'web', input=json.dumps(payloads),
                              text=True, capture_output=True, check=True, timeout=30)
    blockers = []
    for original, heldout in product(['passed', 'failed'], repeat=2):
        entries = [dict(run_id='original', validation_status='validated', evidence_status=original),
                   dict(run_id='heldout', validation_status='validated', evidence_status=heldout)]
        pair = dict(original_run_id='original', heldout_run_id='heldout', validation_status='validated',
                    evidence_status='failed' if 'failed' in (original, heldout) else 'passed')
        actual = _failed_pair_members(entries, [pair])
        expected = sorted(e['run_id'] for e in entries if e['evidence_status'] == 'failed')
        assert actual == expected
        blockers.append(dict(original=original, heldout=heldout, failed_ids=actual))
    real = list_reward_evidence(ROOT)
    assert 'bet36fly.reward_brain' not in sys.modules
    assert all(digest(ROOT/path) == value for path, value in release.items())
    result = dict(release_hashes=release, bridge_probes=bridge, metadata_probes=metadata,
                  actual_component_render=json.loads(rendered.stdout), blocker_states=blockers,
                  real_panels=[{k: row.get(k) for k in ('run_id', 'learning_rule', 'panel_role',
                               'validation_status', 'evidence_status')} for row in real['diagnostics']],
                  real_pairs=real['qualification_pairs'], real_conditioning=real['conditioning'],
                  native_imported=False, release_hashes_stable=True, probe_sha256=digest(Path(__file__)))
    OUT.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'bridge_probes': len(bridge), 'malformed_field_cases': len(metadata),
                      'actual_component_renders': len(payloads), 'blocking_states': len(blockers),
                      'native_imported': False, 'release_hashes_stable': True, 'output': str(OUT)}))


if __name__ == '__main__':
    main()
