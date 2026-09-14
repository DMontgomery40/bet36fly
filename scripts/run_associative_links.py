"""Plasticity-off link measurement for the associative contract (identity associative-links-01).

Records, on the actual MaleCNS graph: sweet taste -> dopamine transmission at 0.11 mV/contact,
antennal-lobe runaway with and without local-neuron output, APL silencing of the gamma4/gamma5
MBONs, reward-DAN silence under odor alone, and the odor-code calibration over the 30 MLB team
keys. No plasticity, no sports labels, no fitted parameters.
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
from bet36fly.associative import AssociativeEngine, build_circuit, odor_schedule, team_odor_types  # noqa: E402
from bet36fly.connectome import ROOT  # noqa: E402
from bet36fly.associative import atomic_json  # noqa: E402


def variant_engine(circuit, root, *, alln_out, apl_out, da_out, alpn_in=1.0, inputs):
    """Same graph and coupling as the circuit with alternative interventions (link diagnostics only)."""
    path = Path(root) / 'data/brain'
    ptr, post, contacts, signs = [np.load(path / f'{k}.npy', allow_pickle=False)
                                  for k in ('indptr', 'post', 'counts', 'signs')]
    src = np.repeat(np.arange(len(ptr) - 1), np.diff(ptr))
    types, classes = circuit['types'], circuit['classes']
    transmitter = circuit['transmitter']
    w = (contacts * np.repeat(signs.astype(np.float32), np.diff(ptr)) * np.float32(0.11)).astype(np.float32)
    w[np.isin(src, np.flatnonzero(classes == 'ALLN'))] *= np.float32(alln_out)
    w[np.isin(src, np.flatnonzero((types == 'APL') & (transmitter == 'gaba')))] *= np.float32(apl_out)
    w[np.isin(src, np.flatnonzero(transmitter == 'dopamine'))] *= np.float32(da_out)
    if alpn_in != 1.0:
        w[np.isin(post, np.flatnonzero(classes == 'ALPN'))] *= np.float32(alpn_in)
    return AssociativeEngine(ptr, post, w, inputs, circuit['kc'], circuit['engine'].dan_indices,
                             circuit['engine'].dan_compartments, [], [], [], n_compartments=2)


def summarize(circuit, result, cue_bins):
    counts = result['counts']
    types, classes = circuit['types'], circuit['classes']
    kc = circuit['kc']
    by = lambda idx: {t: int(counts[idx][types[idx] == t].sum()) for t in sorted(set(types[idx]))}  # noqa: E731
    dan = np.flatnonzero(classes == 'DAN')
    mbon = np.flatnonzero(classes == 'MBON')
    population = result['population']
    return dict(total_spikes=int(counts.sum()), kc_active=int((counts[kc] > 0).sum()),
                kc_active_fraction=float((counts[kc] > 0).mean()), kc_spikes=int(counts[kc].sum()),
                alpn_spikes=int(counts[classes == 'ALPN'].sum()), alln_spikes=int(counts[classes == 'ALLN'].sum()),
                dan_spikes_by_type={k: v for k, v in by(dan).items() if v},
                mbon_spikes_by_type={k: v for k, v in by(mbon).items() if v},
                population_per_100ms=[int(population[i:i + 5].sum()) for i in range(0, len(population), 5)],
                tail_spikes=int(population[-5:].sum()), stimulus_spikes=int(population[cue_bins[0]:cue_bins[1]].sum()),
                wall_seconds=result['wall_seconds'], max_abs_voltage_offset_mv=result['max_abs_voltage_offset_mv'])


def main(protocol_path):
    raw = protocol_path.read_bytes()
    protocol = json.loads(raw)
    identity = 'associative-links-' + hashlib.sha256(raw).hexdigest()[:20]
    out = ROOT / 'output/associative' / identity
    if out.exists():
        raise ValueError('Refusing an existing links identity.')
    out.mkdir(parents=True)
    (out / 'protocol.json').write_bytes(raw)
    circuit = build_circuit(ROOT, protocol)
    import pyarrow.feather as feather
    nodes = feather.read_table(ROOT / 'data/brain/nodes.feather').to_pandas().set_index('bodyId').reindex(circuit['ids'])
    circuit['transmitter'] = nodes['transmitter'].fillna('').to_numpy()
    engine = circuit['engine']
    manifest = dict(identity=identity, status='running', plasticity=False, anatomy=circuit['anatomy'], links={},
                    calls=0, started=time.time())
    atomic_json(out / 'manifest.json', manifest)
    sensory = circuit['sensory']
    bins, cue = 35, (5, 25)
    probe_types = ['ORN_DM2', 'ORN_DM1', 'ORN_VA2', 'ORN_DL3']

    def call(name, eng, rates, seed=17):
        result = eng.run(rates, bin_ms=20, seed=seed)
        manifest['calls'] += 1
        row = summarize(circuit, result, cue)
        np.savez_compressed(out / f'{name}.npz', counts=result['counts'], population=result['population'],
                            input_events=result['input_events'])
        return row

    # Link 1: sweet and bitter taste at the source-anchored rates, natural interventions of the circuit.
    natural = variant_engine(circuit, ROOT, alln_out=1.0, apl_out=1.0, da_out=1.0, inputs=sensory)
    for name, key, hz in (('sweet', 'sweet', 58.9), ('bitter', 'bitter', 18.8)):
        rates = np.zeros((bins, len(sensory)), np.float32)
        rates[cue[0]:cue[1], np.searchsorted(sensory, circuit['taste'][key])] = hz
        manifest['links'][f'taste_{name}_no_interventions'] = call(f'taste-{name}', natural, rates)
    # Link 2: odor with local-neuron output intact versus zeroed.
    for label, kw in (('odor_no_interventions', dict(alln_out=1.0, apl_out=1.0, da_out=1.0)),
                      ('odor_alln_zero', dict(alln_out=0.0, apl_out=1.0, da_out=1.0)),
                      ('odor_alln_zero_apl_quarter', dict(alln_out=0.0, apl_out=0.25, da_out=1.0)),
                      ('odor_alln_zero_apl_zero', dict(alln_out=0.0, apl_out=0.0, da_out=1.0)),
                      ('odor_circuit_interventions', dict(alln_out=0.0, apl_out=0.0, da_out=0.0))):
        eng = variant_engine(circuit, ROOT, inputs=sensory, **kw)
        rates = odor_schedule(circuit, probe_types, bins=bins, start_bin=cue[0], end_bin=cue[1], hz=118.)
        manifest['links'][label] = dict(kw, probe_types=probe_types, **call(label, eng, rates))
        atomic_json(out / 'manifest.json', manifest)
    # Link 3: reinforcer drive alone on the circuit (pure-dopamine fast output zero).
    from bet36fly.associative import drive_schedule
    drive = drive_schedule(circuit, bins=bins, start_bin=cue[0], end_bin=cue[1], hz=30.)
    result = engine.run(np.zeros((bins, len(sensory)), np.float32), drive=drive, bin_ms=20, seed=17)
    manifest['calls'] += 1
    manifest['links']['reinforcer_alone'] = dict(summarize(circuit, result, cue),
                                                  drive_events=int(result['drive_events'].sum()),
                                                  dan_spikes=int(result['counts'][engine.dan_indices].sum()))
    # Link 4: odor code calibration over the 30 team keys and the four conditioning cues.
    games = json.loads((ROOT / protocol['odor_code']['calibration_games']).read_text())
    keys = sorted({g['home_key'] for g in games} | {g['away_key'] for g in games}) + [f'cue:{c}' for c in 'ABCD']
    outputs = circuit['outputs']
    rows = []
    active = {}
    for key in keys:
        odor = team_odor_types(key, circuit['orn_types'], protocol['odor_code']['width'], protocol['odor_code']['salt'])
        rates = odor_schedule(circuit, odor, bins=bins, start_bin=cue[0], end_bin=cue[1], hz=protocol['odor_code']['hz'])
        result = engine.run(rates, bin_ms=20, seed=17)
        manifest['calls'] += 1
        counts = result['counts']
        active[key] = set(np.flatnonzero(counts[circuit['kc']] > 0).tolist())
        rows.append(dict(key=key, odor_types=odor, kc_active=len(active[key]), kc_spikes=int(counts[circuit['kc']].sum()),
                         mbon05=int(counts[outputs[0]].sum()), mbon01=int(counts[outputs[1]].sum()),
                         reward_dan_spikes=int(counts[engine.dan_indices].sum()), tail_spikes=int(result['population'][-5:].sum()),
                         stimulus_spikes=int(result['population'][cue[0]:cue[1]].sum()), total_spikes=int(counts.sum()),
                         wall_seconds=result['wall_seconds']))
    jaccard = [len(active[a] & active[b]) / max(1, len(active[a] | active[b]))
               for i, a in enumerate(keys) for b in keys[i + 1:]]
    kc = [r['kc_active'] for r in rows]
    m5 = [r['mbon05'] for r in rows]
    manifest['links']['odor_code'] = dict(width=protocol['odor_code']['width'], hz=protocol['odor_code']['hz'], keys=len(keys),
                                          kc_active_min_median_max=[min(kc), float(np.median(kc)), max(kc)],
                                          mbon05_min_median_max=[min(m5), float(np.median(m5)), max(m5)],
                                          mbon05_silent_keys=[r['key'] for r in rows if r['mbon05'] == 0],
                                          reward_dan_spikes_total=int(sum(r['reward_dan_spikes'] for r in rows)),
                                          jaccard_mean=float(np.mean(jaccard)), jaccard_max=float(max(jaccard)),
                                          tail_max=max(r['tail_spikes'] for r in rows), rows=rows)
    checks = dict(
        sweet_reaches_dopamine=bool(manifest['links']['taste_sweet_no_interventions']['dan_spikes_by_type']),
        odor_runaway_without_alln_intervention=manifest['links']['odor_no_interventions']['tail_spikes'] > 0,
        odor_recovers_with_alln_zero=manifest['links']['odor_alln_zero']['tail_spikes'] == 0,
        mbon05_silent_with_apl=manifest['links']['odor_alln_zero']['mbon_spikes_by_type'].get('MBON05', 0) == 0,
        mbon05_responds_with_apl_zero=manifest['links']['odor_alln_zero_apl_zero']['mbon_spikes_by_type'].get('MBON05', 0) > 0,
        reward_dans_silent_under_odor=manifest['links']['odor_code']['reward_dan_spikes_total'] == 0,
        reinforcer_drives_reward_dans=manifest['links']['reinforcer_alone']['dan_spikes'] > 0,
        every_cue_recruits_kcs=min(kc) >= protocol['odor_code']['min_kc_active'],
        every_cue_drives_mbon05=min(m5) >= protocol['odor_code']['min_mbon05_spikes'],
        cue_overlap_bounded=max(jaccard) <= protocol['odor_code']['max_jaccard'],
        cues_recover=manifest['links']['odor_code']['tail_max'] <= 1,
    )
    manifest['checks'] = checks
    manifest['status'] = 'completed'
    manifest['wall_seconds'] = time.time() - manifest.pop('started')
    atomic_json(out / 'manifest.json', manifest)
    print(json.dumps(checks, indent=2))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, default=ROOT / 'configs/associative-circuit-01.json')
    main(parser.parse_args().protocol)
