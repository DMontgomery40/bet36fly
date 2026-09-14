"""Continual-learning stress test: circuit-01 (no recovery) versus circuit-02 (dopamine-gated recovery).

For one arm (baseline or a recovery rho): eight cues reinforced in a fixed cycle, probes of every cue
every few cycles, then a fresh-pair acquisition + backward-erasure reversal battery from the
long-history checkpoint. No sports data. Identity per (protocol bytes, arm, rho).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly.associative import build_circuit, drive_schedule, odor_schedule, save_checkpoint, team_odor_types  # noqa: E402
from bet36fly.connectome import ROOT  # noqa: E402
from bet36fly.associative import atomic_json  # noqa: E402


def reinforcement_plan(keys, cycles, retired_cue=None, retire_after_cycles=None):
    """Ordered (cycle, cue) reinforcements; a retired cue is never reinforced from its retirement cycle on."""
    if (retired_cue is None) != (retire_after_cycles is None):
        raise ValueError('retired_cue and retire_after_cycles must be given together.')
    if retired_cue is not None and (retired_cue not in keys or not 0 < retire_after_cycles <= cycles):
        raise ValueError('The retired cue must be one of the cues and retire inside the run.')
    return [(cycle, key) for cycle in range(cycles) for key in keys
            if not (retired_cue is not None and key == retired_cue and cycle >= retire_after_cycles)]


def last_in_cycle(keys, retired_cue, retire_after_cycles, cycle):
    active = [k for k in keys if not (retired_cue is not None and k == retired_cue and cycle >= retire_after_cycles)]
    return active[-1]


def run(protocol_path, arm, rho, root=ROOT):
    raw = protocol_path.read_bytes()
    protocol = json.loads(raw)
    circuit_path = protocol['baseline_circuit'] if arm == 'baseline' else protocol['recovery_circuit']
    circuit_protocol = json.loads((root / circuit_path).read_text())
    if arm == 'baseline':
        rho = None
    else:
        if rho not in protocol['rho_grid']:
            raise ValueError('rho outside the declared grid.')
        circuit_protocol['recovery'] = [rho] * len(circuit_protocol['compartments'])
    identity = 'associative-stress-' + hashlib.sha256(raw + f'|{arm}|{rho!r}'.encode()).hexdigest()[:20]
    out = root / 'output/associative' / identity
    if out.exists():
        raise ValueError('Refusing an existing stress identity.')
    out.mkdir(parents=True)
    (out / 'protocol.json').write_bytes(raw)
    (out / 'circuit.json').write_text(json.dumps(circuit_protocol, indent=2) + '\n')
    circuit = build_circuit(root, circuit_protocol)
    engine = circuit['engine']
    timing = circuit_protocol['timing']
    code = circuit_protocol['odor_code']
    keys = protocol['cues']
    odors = {k: team_odor_types(k, circuit['orn_types'], code['width'], code['salt']) for k in keys}
    pair = {c: team_odor_types(k, circuit['orn_types'], code['width'], code['salt'])
            for c, k in protocol['post_history']['cues'].items()}
    outputs = circuit['outputs']
    sample = np.unique(np.concatenate([circuit['kc'], *outputs]))
    kc_pos = np.searchsorted(sample, circuit['kc'])
    out_pos = [np.searchsorted(sample, o) for o in outputs]
    mask = engine.plastic_mask.astype(bool)
    comps = engine.plastic_compartments
    lo, hi = timing['cue_bins']
    manifest = dict(identity=identity, arm=arm, rho=rho, status='running', calls=0, anatomy=circuit['anatomy'],
                    odors=odors, probes=[], occupancy=[], reinforcements=[], started=time.time())
    start = time.monotonic()

    def guard():
        if manifest['calls'] >= protocol['call_cap'] or time.monotonic() - start > protocol['wall_cap_seconds']:
            raise RuntimeError('Declared stress budget exhausted.')

    def occupancy(label):
        g = engine.gains
        rows = {}
        for c in sorted(set(comps.tolist())):
            e = mask & (comps == c)
            rows[str(c)] = dict(lower=float(np.mean(g[e] <= engine.gain_bounds[0])), upper=float(np.mean(g[e] >= engine.gain_bounds[1])),
                                above_rest=float(np.mean(g[e] > engine.rest_gain)), mean=float(g[e].mean()),
                                deciles=np.quantile(g[e], np.linspace(0, 1, 11)).tolist())
        manifest['occupancy'].append(dict(label=label, calls=manifest['calls'], gains_sha256=engine.gains_sha256(), **rows))

    def probe(key, odor, seed, label):
        guard()
        rates = odor_schedule(circuit, odor, bins=timing['probe_bins'], start_bin=lo, end_bin=hi, hz=code['hz'])
        r = engine.run(rates, bin_ms=timing['bin_ms'], seed=seed, sample=sample)
        manifest['calls'] += 1
        w = r['trace'][lo:hi]
        row = dict(label=label, key=key, seed=seed, response=[int(w[:, p].sum()) for p in out_pos],
                   kc_active=int((w[:, kc_pos].sum(0) > 0).sum()), gains_sha256=r['gains_sha256_after'],
                   tail=int(r['population'][-5:].sum()))
        manifest['probes'].append(row)
        np.savez_compressed(out / f'probe-{len(manifest["probes"]):04d}.npz', kc_counts=w[:, kc_pos].sum(0).astype(np.int64),
                            response=np.array(row['response']))
        return row

    def reinforce(odor, seed, key, backward=False):
        guard()
        bins = timing['reinforcement_bins']
        cue_b = timing['backward_cue_bins'] if backward else timing['cue_bins']
        us_b = timing['backward_us_bins'] if backward else timing['us_bins']
        rates = odor_schedule(circuit, odor, bins=bins, start_bin=cue_b[0], end_bin=cue_b[1], hz=code['hz'])
        drive = drive_schedule(circuit, bins=bins, start_bin=us_b[0], end_bin=us_b[1], hz=circuit_protocol['reinforcer']['hz'])
        r = engine.run(rates, drive=drive, bin_ms=timing['bin_ms'], seed=seed, plasticity=True)
        manifest['calls'] += 1
        manifest['reinforcements'].append(dict(key=key, seed=seed, changed=int((r['gain_delta'] != 0).sum()),
                                               applied=float(r['comp_bins'][:, :, 3].sum()), recovery=float(r['comp_bins'][:, :, 7].sum()),
                                               bound=float(r['comp_bins'][:, :, 4:6].sum()), gains_sha256=r['gains_sha256_after']))
        return r

    def probe_all(label):
        for key in keys:
            for seed in protocol['probe_seeds']:
                probe(key, odors[key], seed, label)
        occupancy(label)
        atomic_json(out / 'manifest.json', manifest)

    try:
        probe_all('unit')
        base = protocol['training_seed_base']
        n = 0
        for cycle, key in reinforcement_plan(keys, protocol['cycles'], protocol.get('retired_cue'),
                                             protocol.get('retire_after_cycles')):
            reinforce(odors[key], base + n, key)
            n += 1
            if key == last_in_cycle(keys, protocol.get('retired_cue'), protocol.get('retire_after_cycles'), cycle) \
                    and (cycle + 1) % protocol['probe_every_cycles'] == 0:
                probe_all(f'cycle-{cycle + 1}')
        save_checkpoint(out / 'checkpoint-history.npz', engine, identity=identity, note='after the long history')
        history = engine.gains.copy()
        # Post-history battery on the fresh pair: unit probes at the history checkpoint, then paired/untaught/frozen.
        ph = protocol['post_history']
        seeds = protocol['probe_seeds']
        for c in ('A', 'B'):
            for seed in seeds:
                probe(c, pair[c], seed, 'post-unit')
        order = ('A', 'B', 'B', 'A')
        endpoints = {}
        for arm_name in ph['arms']:
            engine.set_gains(history.copy())
            for exposure in range(ph['exposures_per_cue'] * 2):
                cue = order[exposure % 4]
                seed = base + 10000 + exposure
                if cue == 'A' and arm_name != 'untaught':
                    if arm_name == 'frozen':
                        rates = odor_schedule(circuit, pair['A'], bins=timing['reinforcement_bins'], start_bin=lo, end_bin=hi, hz=code['hz'])
                        drive = drive_schedule(circuit, bins=timing['reinforcement_bins'], start_bin=timing['us_bins'][0],
                                               end_bin=timing['us_bins'][1], hz=circuit_protocol['reinforcer']['hz'])
                        guard()
                        engine.run(rates, drive=drive, bin_ms=timing['bin_ms'], seed=seed, plasticity=False)
                        manifest['calls'] += 1
                    else:
                        reinforce(pair['A'], seed, 'post:A')
                else:
                    guard()
                    rates = odor_schedule(circuit, pair[cue], bins=timing['reinforcement_bins'], start_bin=lo, end_bin=hi, hz=code['hz'])
                    engine.run(rates, bin_ms=timing['bin_ms'], seed=seed, plasticity=arm_name != 'frozen')
                    manifest['calls'] += 1
            resp = np.zeros((3, 2, 2), np.int64)
            for si, seed in enumerate(seeds):
                for ci, c in enumerate('AB'):
                    resp[si, ci] = probe(c, pair[c], seed, f'post-{arm_name}')['response']
            endpoints[arm_name] = dict(responses=resp.tolist(), gains=engine.gains.copy())
            save_checkpoint(out / f'checkpoint-post-{arm_name}.npz', engine, identity=identity, note=arm_name)
        # Reversal from the post-history paired checkpoint: backward erasure plus swap.
        engine.set_gains(endpoints['paired']['gains'].copy())
        for exposure in range(ph['exposures_per_cue'] * 2):
            cue = order[exposure % 4]
            seed = base + 20000 + exposure
            reinforce(pair[cue], seed, 'post-reversal:' + cue, backward=(cue == 'A'))
        rev = np.zeros((3, 2, 2), np.int64)
        for si, seed in enumerate(seeds):
            for ci, c in enumerate('AB'):
                rev[si, ci] = probe(c, pair[c], seed, 'post-reversal')['response']
        save_checkpoint(out / 'checkpoint-post-reversal.npz', engine, identity=identity, note='reversal')
        occupancy('final')
        # Summaries.
        unit = {(p['key'], p['seed']): p['response'] for p in manifest['probes'] if p['label'] == 'unit'}
        post_unit = np.array([[sum(p['response']) for p in manifest['probes'] if p['label'] == 'post-unit' and p['key'] == c and p['seed'] == s]
                              for s in seeds for c in 'AB']).reshape(3, 2)

        def summed(label, key):
            return [sum(p['response']) for p in manifest['probes'] if p['label'] == label and p['key'] == key]

        memory = {}
        for label in sorted({p['label'] for p in manifest['probes'] if p['label'].startswith('cycle-')},
                            key=lambda x: int(x.split('-')[1])):
            memory[label] = {k: [a - sum(unit[(k, s)]) for a, s in zip(summed(label, k), seeds)] for k in keys}
        post_delta = {a: (np.array(endpoints[a]['responses']).sum(2) - post_unit).tolist() for a in endpoints}
        rev_delta = (rev.sum(2) - post_unit).tolist()
        paired_contrast = np.array(post_delta['paired'])[:, 0] - np.array(post_delta['paired'])[:, 1]
        untaught_contrast = np.array(post_delta['untaught'])[:, 0] - np.array(post_delta['untaught'])[:, 1]
        rev_pref = np.array(rev_delta)[:, 0] - np.array(rev_delta)[:, 1]
        final = manifest['occupancy'][-1]
        manifest['summary'] = dict(
            recent_key=keys[-1], oldest_key=keys[0], memory_by_cycle=memory,
            post_history=dict(delta=post_delta, paired_contrast=paired_contrast.tolist(), untaught_contrast=untaught_contrast.tolist(),
                              reversal_delta=rev_delta, reversal_preference=rev_pref.tolist(),
                              acquisition_passed=bool(np.all(paired_contrast < 0) and abs(paired_contrast.mean()) >= 3 * max(abs(untaught_contrast.mean()), 1e-9)),
                              reversal_flipped=bool(np.all(paired_contrast < 0) and np.all(rev_pref > 0))),
            lower_bound_occupancy={c: final[c]['lower'] for c in ('0', '1')},
            upper_bound_occupancy={c: final[c]['upper'] for c in ('0', '1')},
            above_rest={c: final[c]['above_rest'] for c in ('0', '1')},
            total_recovery=float(sum(r['recovery'] for r in manifest['reinforcements'])),
            total_bound_contacts=float(sum(r['bound'] for r in manifest['reinforcements'])))
        manifest['status'] = 'completed'
    except Exception as exc:
        manifest.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        manifest['wall_seconds'] = time.monotonic() - start
        atomic_json(out / 'manifest.json', manifest)
    print(json.dumps({k: v for k, v in manifest['summary'].items() if k != 'memory_by_cycle'}, indent=1))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, default=ROOT / 'configs/associative-stress-01.json')
    parser.add_argument('--arm', choices=['baseline', 'recovery'], required=True)
    parser.add_argument('--rho', type=float, default=None)
    args = parser.parse_args()
    run(args.protocol, args.arm, args.rho)
