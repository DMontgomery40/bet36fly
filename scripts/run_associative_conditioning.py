"""Stage 3: controlled cue learning on the actual MaleCNS circuit (new identity per protocol bytes).

Every native call is journaled with gain hashes before/after; probes never learn; all
responses, KC counts, dopamine spikes, rule bins, drive events and checkpoints are saved.
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
from bet36fly import associative_conditioning as ac  # noqa: E402
from bet36fly.associative import (build_circuit, drive_schedule, odor_schedule, save_checkpoint,  # noqa: E402
                                  team_odor_types)
from bet36fly.connectome import ROOT  # noqa: E402
from bet36fly.associative import atomic_json  # noqa: E402


class Runner:
    def __init__(self, protocol_path, root=ROOT, rho=None):
        self.root = Path(root)
        raw = protocol_path.read_bytes()
        self.protocol = json.loads(raw)
        circuit_raw = (self.root / self.protocol['circuit']).read_bytes()
        self.circuit_protocol = json.loads(circuit_raw)
        if rho is not None:
            # Declared recovery-rate grid point (version-2 circuits only); part of the identity.
            if 'recovery' not in self.circuit_protocol:
                raise ValueError('rho applies only to a circuit with a recovery term.')
            self.circuit_protocol['recovery'] = [float(rho)] * len(self.circuit_protocol['compartments'])
            circuit_raw = json.dumps(self.circuit_protocol, indent=2).encode()
        self.rho = rho
        digest = hashlib.sha256(raw + circuit_raw).hexdigest()[:20]
        self.identity = 'associative-conditioning-' + digest
        self.out = self.root / 'output/associative' / self.identity
        if self.out.exists():
            raise ValueError('Refusing an existing conditioning identity.')
        self.out.mkdir(parents=True)
        (self.out / 'protocol.json').write_bytes(raw)
        (self.out / 'circuit.json').write_bytes(circuit_raw)
        self.circuit = build_circuit(self.root, self.circuit_protocol)
        self.engine = self.circuit['engine']
        self.timing = self.circuit_protocol['timing']
        self.spec = ac.conditioning_spec(self.protocol)
        self.plan = ac.build_plan(self.timing, self.spec)
        self.plan_summary = ac.validate_plan(self.plan, self.spec)
        self.outputs = self.circuit['outputs']
        self.sample = np.unique(np.concatenate([self.circuit['kc'], *self.outputs, self.engine.dan_indices]))
        self.kc_pos = np.searchsorted(self.sample, self.circuit['kc'])
        self.out_pos = [np.searchsorted(self.sample, o) for o in self.outputs]
        code = self.circuit_protocol['odor_code']
        self.odors = {c: team_odor_types(key, self.circuit['orn_types'], code['width'], code['salt'])
                      for c, key in self.protocol['cues'].items()}
        self.unit = np.ones(len(self.engine.plastic_edges), np.float32)
        self.checkpoints = {'unit': self.unit.copy()}
        self.manifest = dict(identity=self.identity, status='running', plan=self.plan_summary, rho=self.rho,
                             anatomy=self.circuit['anatomy'], odors=self.odors, calls=[], checkpoints={},
                             probes={}, verdicts={}, started=time.time())
        self.start = time.monotonic()

    def persist(self):
        self.manifest['wall_seconds'] = time.monotonic() - self.start
        atomic_json(self.out / 'manifest.json', self.manifest)

    def schedules(self, row):
        s = row['schedule']
        bins = s['bins']
        rates = np.zeros((bins, len(self.circuit['sensory'])), np.float32)
        if s['cue'] is not None:
            rates = odor_schedule(self.circuit, self.odors[row['cue']], bins=bins, start_bin=s['cue'][0],
                                  end_bin=s['cue'][1], hz=self.circuit_protocol['odor_code']['hz'])
        drive = None
        if s['us'] is not None:
            drive = drive_schedule(self.circuit, bins=bins, start_bin=s['us'][0], end_bin=s['us'][1],
                                   hz=self.circuit_protocol['reinforcer']['hz'])
        return rates, drive

    def call(self, position, row):
        if len(self.manifest['calls']) >= self.spec['call_cap'] or time.monotonic() - self.start > self.spec['wall_cap_seconds']:
            raise RuntimeError('Declared conditioning budget exhausted.')
        checkpoint = row['checkpoint']
        if checkpoint not in self.checkpoints:
            parent = self.checkpoints[row.get('parent', 'unit')]
            self.checkpoints[checkpoint] = parent.copy()
            self.manifest['checkpoints'][checkpoint] = dict(parent=row.get('parent', 'unit'),
                                                            start_sha256=hashlib.sha256(parent.tobytes()).hexdigest())
        self.engine.set_gains(self.checkpoints[checkpoint])
        self.engine.set_coupling([1.0, 1.0] if row['coupling'] else [0.0, 0.0])
        rates, drive = self.schedules(row)
        result = self.engine.run(rates, drive=drive, bin_ms=self.timing['bin_ms'], seed=row['seed'],
                                 plasticity=row['plasticity'], sample=self.sample)
        entry = dict(position=position, id=row['id'], stage=row['stage'], owner=row['owner'], kind=row['kind'],
                     cue=row['cue'], seed=row['seed'], plasticity=row['plasticity'], coupling=row['coupling'],
                     schedule=row['schedule'], gains_before=result['gains_sha256_before'],
                     gains_after=result['gains_sha256_after'], total_spikes=int(result['counts'].sum()),
                     kc_active=int((result['counts'][self.circuit['kc']] > 0).sum()),
                     reward_dan_spikes=int(result['counts'][self.engine.dan_indices].sum()),
                     drive_events=int(result['drive_events'].sum()), changed_edges=int((result['gain_delta'] != 0).sum()),
                     gain_delta_sum=float(result['gain_delta'].sum()),
                     bound_contacts=[float(result['comp_bins'][:, :, 4].sum()), float(result['comp_bins'][:, :, 5].sum())],
                     tail_spikes=int(result['population'][-5:].sum()),
                     stimulus_spikes=int(result['population'][row['schedule']['cue'][0]:row['schedule']['cue'][1]].sum())
                     if row['schedule']['cue'] else 0,
                     generator_p=self.generator_p(rates, result['input_events']),
                     max_abs_voltage_offset_mv=result['max_abs_voltage_offset_mv'], wall_seconds=result['wall_seconds'])
        if row['plasticity'] or row['kind'] == 'blank':
            self.checkpoints[checkpoint] = self.engine.gains.copy()
        elif result['gains_sha256_after'] != result['gains_sha256_before']:
            raise RuntimeError('A probe changed gains.')
        np.savez_compressed(self.out / f'{position:03d}-{row["id"]}.npz', counts=result['counts'], trace=result['trace'],
                            population=result['population'], drive_events=result['drive_events'],
                            comp_bins=result['comp_bins'], gains=result['gains'], traces_kc=result['traces']['kc'],
                            traces_dan=result['traces']['dan'])
        if row['kind'] == 'probe':
            lo, hi = row['schedule']['cue']
            window = result['trace'][lo:hi]
            entry['response'] = [int(window[:, p].sum()) for p in self.out_pos]
            entry['kc_counts_sha256'] = hashlib.sha256(window[:, self.kc_pos].sum(0).astype(np.int64).tobytes()).hexdigest()
            self.manifest['probes'][row['id']] = dict(owner=row['owner'], cue=row['cue'], seed=row['seed'],
                                                      response=entry['response'], gains_sha256=result['gains_sha256_after'])
            self._kc[row['id']] = window[:, self.kc_pos].sum(0).astype(np.int64)
        self.manifest['calls'].append(entry)
        if entry['bound_contacts'] != [0.0, 0.0]:
            self.manifest.setdefault('bound_contact_calls', []).append(row['id'])
        self.persist()
        return entry, result

    def generator_p(self, rates, events):
        from scipy.stats import binomtest
        steps = round(self.timing['bin_ms'] / 0.2)
        out = []
        for hz in np.unique(rates):
            if hz == 0:
                out.append(float(events[rates == 0].sum() == 0))
                continue
            mask = rates == hz
            out.append(float(binomtest(int(events[mask].sum()), steps * int(mask.sum()), float(hz) * 0.2 / 1000).pvalue))
        return out

    def endpoint(self, stage, owner):
        seeds, cues = self.spec['probe_seeds'], ac.CUES
        responses = np.zeros((len(seeds), 2, 2), np.int64)
        kc = np.zeros((len(seeds), 2, len(self.circuit['kc'])), np.int64)
        for si, seed in enumerate(seeds):
            for ci, cue in enumerate(cues):
                pid = f'{stage}-{owner}-probe-{cue}-{seed}'
                responses[si, ci] = self.manifest['probes'][pid]['response']
                kc[si, ci] = self._kc[pid]
        checkpoint = 'unit' if owner == 'unit' else owner if stage != 'reversal' else f'reversal-{owner}'
        return dict(responses=responses.tolist(), gains=self.checkpoints[checkpoint].copy(), kc=kc)

    def entry_gate(self, unit):
        gate = self.protocol['entry_gate']
        responses = np.asarray(unit['responses'])
        kc_active = (unit['kc'] > 0).sum(2)
        partition = ac.partition_edges(unit['kc'], self.engine.plastic_kc, self.engine.plastic_compartments,
                                       self.engine.plastic_mask)
        probes = [c for c in self.manifest['calls'] if c['stage'] == 'entry']
        checks = dict(kc_recruited=bool(kc_active.min() >= gate['min_kc_active']),
                      mbon05_responds=bool(responses[:, :, 0].min() >= gate['min_mbon05_spikes']),
                      ab_overlap_bounded=partition['between_jaccard_max'] <= gate['max_ab_jaccard'],
                      recovery=all(c['tail_spikes'] <= max(1, gate['max_tail_fraction'] * c['stimulus_spikes']) for c in probes),
                      generator=all(min(c['generator_p']) >= 1e-6 for c in probes),
                      nonempty_partitions=all(len(v['A']) and len(v['B']) for v in partition['edges'].values()))
        self.manifest['entry_gate'] = dict(checks=checks, passed=all(checks.values()),
                                           kc_active=kc_active.tolist(), responses=responses.tolist(),
                                           between_jaccard_max=partition['between_jaccard_max'],
                                           partition_sizes={k: {g: len(v[g]) for g in ('A', 'B', 'tied')}
                                                            for k, v in partition['edges'].items()})
        return partition, all(checks.values())

    def run(self):
        self._kc = {}
        self.persist()
        stage_done = set()
        try:
            for position, row in enumerate(self.plan):
                self.call(position, row)
                if row['stage'] == 'entry' and position == 5:
                    unit = self.endpoint('entry', 'unit')
                    self.partition, passed = self.entry_gate(unit)
                    self.unit_endpoint = unit
                    if not passed:
                        raise RuntimeError('Entry gate failed: ' + json.dumps(self.manifest['entry_gate']['checks']))
                    self.persist()
                if row['stage'] == 'endpoint' and row['id'].endswith(f'-{self.spec["probe_seeds"][-1]}') and row['cue'] == 'B':
                    arm = row['owner']
                    ep = self.endpoint('endpoint', arm)
                    self.manifest['checkpoints'][arm]['end_sha256'] = hashlib.sha256(ep['gains'].tobytes()).hexdigest()
                    save_checkpoint(self.out / f'checkpoint-{arm}.npz', self.engine, identity=self.identity,
                                    parent_sha256=self.manifest['checkpoints'][arm]['start_sha256'], note=arm) \
                        if self.engine.set_gains(ep['gains']) is None else None
                    if arm == ac.ARMS[-1] and 'acquisition' not in stage_done:
                        endpoints = {a: self.endpoint('endpoint', a) for a in ac.ARMS}
                        self.manifest['verdicts']['acquisition'] = ac.evaluate_acquisition(
                            self.unit_endpoint['responses'], endpoints, self.partition, self.unit, self.spec['effect_ratio'], self.spec)
                        stage_done.add('acquisition')
                        self.persist()
                if row['stage'] == 'retention' and row['kind'] == 'probe' and row['id'].endswith(f'-B-{self.spec["probe_seeds"][-1]}'):
                    self.manifest['verdicts']['retention'] = ac.evaluate_retention(
                        self.endpoint('endpoint', 'paired'), self.endpoint('retention', 'paired'))
                    self.persist()
            branches = {b: self.endpoint('reversal', b) for b in ac.REVERSAL_BRANCHES}
            for b in ac.REVERSAL_BRANCHES:
                self.engine.set_gains(branches[b]['gains'])
                save_checkpoint(self.out / f'checkpoint-reversal-{b}.npz', self.engine, identity=self.identity,
                                parent_sha256=self.manifest['checkpoints']['paired']['end_sha256'], note=b)
            self.manifest['verdicts']['reversal'] = ac.evaluate_reversal(
                self.unit_endpoint['responses'], self.endpoint('endpoint', 'paired'), branches, self.partition,
                self.spec['effect_ratio'], self.spec)
            self.manifest['audit'] = dict(
                bound_contact_calls=self.manifest.get('bound_contact_calls', []),
                recovery_failures=[c['id'] for c in self.manifest['calls']
                                   if c['stimulus_spikes'] and c['tail_spikes'] > max(1, 0.01 * c['stimulus_spikes'])],
                generator_failures=[c['id'] for c in self.manifest['calls'] if min(c['generator_p']) < 1e-6],
                probe_gain_changes=[c['id'] for c in self.manifest['calls'] if c['kind'] == 'probe' and c['changed_edges']],
                reward_dan_spikes_in_cue_only_trials=int(sum(c['reward_dan_spikes'] for c in self.manifest['calls']
                                                            if c['kind'] == 'train' and c['schedule']['us'] is None)))
            audit_ok = not any([self.manifest['audit']['bound_contact_calls'], self.manifest['audit']['recovery_failures'],
                                self.manifest['audit']['generator_failures'], self.manifest['audit']['probe_gain_changes']])
            v = self.manifest['verdicts']
            self.manifest['summary'] = dict(
                acquisition_passed=v['acquisition']['all_passed'], retention_passed=v['retention']['passed'],
                reversal_passed=v['reversal']['all_passed'], audit_passed=audit_ok,
                all_passed=bool(v['acquisition']['all_passed'] and v['retention']['passed']
                                and v['reversal']['all_passed'] and audit_ok))
            self.manifest['status'] = 'completed'
        except Exception as exc:
            self.manifest.update(status='failed', error=f'{type(exc).__name__}: {exc}')
            raise
        finally:
            self.manifest['finished'] = time.time()
            self.persist()
        print(json.dumps(self.manifest.get('summary'), indent=2))
        return self.manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, default=ROOT / 'configs/associative-conditioning-01.json')
    parser.add_argument('--rho', type=float, default=None)
    args = parser.parse_args()
    Runner(args.protocol, rho=args.rho).run()
