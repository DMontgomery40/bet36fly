"""Independent recomputation of a conditioning run's verdict from its saved per-call artifacts.

Reads only the run directory: protocol/circuit JSON, per-call NPZ traces and gains, and the
checkpoints. Recomputes probe responses, gain changes, partitions and every verdict with the
pure evaluators, then compares against the stored manifest. Never runs the engine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly import associative_conditioning as ac  # noqa: E402
from bet36fly.associative import load_checkpoint  # noqa: E402


def audit(run_dir):
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / 'manifest.json').read_text())
    protocol = json.loads((run_dir / 'protocol.json').read_text())
    circuit = json.loads((run_dir / 'circuit.json').read_text())
    spec = ac.conditioning_spec(protocol)
    plan = ac.build_plan(circuit['timing'], spec)
    ac.validate_plan(plan, spec)
    files = sorted(run_dir.glob('[0-9][0-9][0-9]-*.npz'))
    if len(files) != len(plan):
        raise ValueError(f'{len(files)} artifacts for {len(plan)} planned calls.')
    anatomy = manifest['anatomy']
    n_edges = anatomy['plastic_edges']
    # Rebuild anatomy only (no simulation) to recover the exact sample layout the runner used.
    from bet36fly.associative import build_circuit
    circuit_obj = build_circuit(Path(__file__).resolve().parents[1], circuit)
    engine = circuit_obj['engine']
    sample = np.unique(np.concatenate([circuit_obj['kc'], *circuit_obj['outputs'], engine.dan_indices]))
    kc_pos = np.searchsorted(sample, circuit_obj['kc'])
    out_pos = [np.searchsorted(sample, o) for o in circuit_obj['outputs']]
    dan_pos = np.searchsorted(sample, engine.dan_indices)
    responses = {}
    kc_counts = {}
    gains_after = {}
    cue = circuit['timing']['cue_bins']
    checks = dict(probe_gain_unchanged=True, gains_hash_chain=True, bound_contacts=0, recovery_failures=[],
                  response_mismatches=[], probes_with_reward_dan_spikes=[])
    previous = {}
    for position, (row, path) in enumerate(zip(plan, files)):
        assert path.name.startswith(f'{position:03d}-{row["id"]}'), path.name
        with np.load(path) as data:
            gains = data['gains'].copy()
            trace = data['trace']
            population = data['population']
            comp = data['comp_bins']
        sha = hashlib.sha256(gains.tobytes()).hexdigest()
        entry = manifest['calls'][position]
        if entry['gains_after'] != sha:
            checks['gains_hash_chain'] = False
        checkpoint = row['checkpoint']
        if row['kind'] == 'probe':
            start = previous.get(checkpoint)
            if start is not None and start != sha:
                checks['probe_gain_unchanged'] = False
        previous[checkpoint] = sha
        checks['bound_contacts'] += float(comp[:, :, 4:6].sum())
        if row['schedule']['cue'] is not None:
            lo, hi = row['schedule']['cue']
            stimulus = int(population[lo:hi].sum())
            if population[-5:].sum() > max(1, 0.01 * stimulus):
                checks['recovery_failures'].append(row['id'])
        if row['kind'] == 'probe':
            window = trace[cue[0]:cue[1]]
            recomputed = [int(window[:, p].sum()) for p in out_pos]
            if recomputed != entry['response']:
                checks['response_mismatches'].append(row['id'])
            responses[row['id']] = recomputed
            counts = window[:, kc_pos].sum(0).astype(np.int64)
            if hashlib.sha256(counts.tobytes()).hexdigest() != entry['kc_counts_sha256']:
                raise ValueError(f'KC count digest mismatch for {row["id"]}.')
            kc_counts[row['id']] = counts
            if int(trace[:, dan_pos].sum()):
                checks['probes_with_reward_dan_spikes'].append(row['id'])
        gains_after[row['id']] = gains
    seeds = spec['probe_seeds']

    def endpoint(stage, owner, checkpoint_name):
        r = np.zeros((3, 2, 2), np.int64)
        k = None
        for si, seed in enumerate(seeds):
            for ci, c in enumerate(ac.CUES):
                pid = f'{stage}-{owner}-probe-{c}-{seed}'
                r[si, ci] = responses[pid]
                if k is None:
                    k = np.zeros((3, 2, len(kc_counts[pid])), np.int64)
                k[si, ci] = kc_counts[pid]
        last = [row for row in plan if row['checkpoint'] == checkpoint_name and row['kind'] != 'probe']
        gains = gains_after[last[-1]['id']] if last else np.ones(n_edges, np.float32)
        return dict(responses=r.tolist(), gains=gains, kc=k)

    unit = endpoint('entry', 'unit', 'unit')
    meta = load_checkpoint(run_dir / 'checkpoint-paired.npz')[1]
    if meta['edges'] != n_edges:
        raise ValueError('Checkpoint edge count differs from anatomy.')
    stored_partition_sizes = manifest['entry_gate']['partition_sizes']
    partition = ac.partition_edges(unit['kc'], engine.plastic_kc, engine.plastic_compartments, engine.plastic_mask)
    sizes = {k: {g: len(v[g]) for g in ('A', 'B', 'tied')} for k, v in partition['edges'].items()}
    if sizes != stored_partition_sizes:
        raise ValueError('Recomputed partition sizes differ from the stored entry gate.')
    endpoints = {arm: endpoint('endpoint', arm, arm) for arm in ac.ARMS}
    for arm in ac.ARMS:
        saved, _ = load_checkpoint(run_dir / f'checkpoint-{arm}.npz')
        if saved.tobytes() != endpoints[arm]['gains'].tobytes():
            raise ValueError(f'Saved checkpoint for {arm} differs from the last training call artifact.')
    acquisition = ac.evaluate_acquisition(unit['responses'], endpoints, partition, np.ones(n_edges, np.float32),
                                          spec['effect_ratio'], spec)
    retention = ac.evaluate_retention(endpoints['paired'], endpoint('retention', 'paired', 'paired'))
    branches = {b: endpoint('reversal', b, f'reversal-{b}') for b in ac.REVERSAL_BRANCHES}
    reversal = ac.evaluate_reversal(unit['responses'], endpoints['paired'], branches, partition, spec['effect_ratio'], spec)
    stored = manifest['verdicts']
    agreement = dict(
        acquisition_criteria=acquisition['criteria'] == stored['acquisition']['criteria'],
        acquisition_all_passed=acquisition['all_passed'] == stored['acquisition']['all_passed'],
        retention=retention == stored['retention'],
        reversal_criteria=reversal['criteria'] == stored['reversal']['criteria'],
        reversal_all_passed=reversal['all_passed'] == stored['reversal']['all_passed'],
        arms_numeric=all(abs(acquisition['arms'][a]['a_edge_mean_gain_change'] - stored['acquisition']['arms'][a]['a_edge_mean_gain_change']) < 1e-12
                         and acquisition['arms'][a]['contrast'] == stored['acquisition']['arms'][a]['contrast'] for a in ac.ARMS),
    )
    result = dict(run=run_dir.name, calls=len(files), checks=checks, agreement=agreement,
                  independent=dict(acquisition=acquisition['criteria'], acquisition_all_passed=acquisition['all_passed'],
                                   retention=retention, reversal=reversal['criteria'], reversal_all_passed=reversal['all_passed'],
                                   paired_contrast=acquisition['arms']['paired']['contrast'],
                                   null_response_scale=acquisition['null_response_scale'],
                                   null_gain_scale=acquisition['null_gain_scale']),
                  all_agree=all(agreement.values()) and checks['probe_gain_unchanged'] and checks['gains_hash_chain']
                  and checks['bound_contacts'] == 0 and not checks['recovery_failures']
                  and not checks['response_mismatches'])
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--out', type=Path, default=None)
    result = audit(parser.parse_args().run)
    print(json.dumps(result, indent=2))
    out = parser.parse_args().out
    if out:
        out.write_text(json.dumps(result, indent=2) + '\n')
