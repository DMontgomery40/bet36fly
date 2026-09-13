"""Run one immutable, finite, plasticity-off taste assay; never activate a model."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pyarrow.feather as feather
from scipy.stats import binomtest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly.connectome import ROOT, digest  # noqa: E402
from bet36fly.experiment import atomic_json  # noqa: E402
from bet36fly.sensory import SensoryEngine, reconcile_cells  # noqa: E402


def response_gates(rows):
    by = {name: [r['MN9_stimulus_hz_mean'] for r in rows if r['condition'] == name]
          for name in ('null', 'water', 'sweet', 'bitter', 'mixed')}
    if any(len(v) != 3 for v in by.values()):
        return dict(complete=False, passed=False)
    means = {k: float(np.mean(v)) for k, v in by.items()}
    gates = dict(null_silent=all(x == 0 for x in by['null']),
                 sweet_activates=all(x > 1 for x in by['sweet']),
                 water_activates=all(x > 1 for x in by['water']),
                 bitter_not_appetitive=means['bitter'] <= means['water'],
                 mixed_suppresses_sweet=all(a < b for a, b in zip(by['mixed'], by['sweet'])))
    return dict(complete=True, passed=all(gates.values()), gates=gates, means=means)


def check_locked_files(config, root):
    for name, expected in config['file_sha256'].items():
        if digest(root / name) != expected:
            raise ValueError(f'Identity-bound file differs: {name}')


def run(config_path, *, root=ROOT):
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    identity = 'sensory-' + hashlib.sha256(config_bytes).hexdigest()[:20]
    output = root / 'output/sensory' / identity
    if output.exists():
        raise ValueError('Refusing to rerun or overwrite an existing sensory identity.')
    check_locked_files(config, root)
    if (config['schema'] != 1 or config['plasticity'] is not False
            or config['seeds'] != [17, 43, 101] or config['max_calls'] != 16
            or config['dt_ms'] != .2 or config['bin_ms'] != 20
            or config['onset_ms'] != 500 or config['stimulus_ms'] != 1000
            or config['recovery_ms'] != 500 or config['synapse_mv'] != .275
            or [c['name'] for c in config['conditions']] != ['null', 'water', 'sweet', 'bitter', 'mixed']):
        raise ValueError('Unsupported assay protocol; declare a separate runner for a changed design.')
    brain = root / 'data/brain'
    nodes = feather.read_table(brain / 'nodes.feather').to_pandas()
    tables = [list(csv.DictReader((root / config[key]).open())) for key in ('grn_table', 'mn_table')]
    cells = reconcile_cells(*tables, nodes)
    if cells['populations'] != config['populations']:
        raise ValueError('Cell population differs from frozen protocol.')
    ids, ptr, post, counts, signs = [np.load(brain / f'{k}.npy', mmap_mode='r', allow_pickle=False)
                                   for k in ('ids', 'indptr', 'post', 'counts', 'signs')]
    input_ids = sorted(sum((cells['populations'][k] for k in ('sweet', 'water', 'bitter')), []))
    sensory = np.searchsorted(ids, input_ids).astype(np.int32)
    sample_ids = sorted(input_ids + cells['populations']['MN9'])
    sample = np.searchsorted(ids, sample_ids).astype(np.int32)
    mn_local = [sample_ids.index(i) for i in cells['populations']['MN9']]
    groups = {k: np.array([input_ids.index(i) for i in cells['populations'][k]], np.int32)
              for k in ('sweet', 'water', 'bitter')}
    weights = counts * np.repeat(signs.astype(np.float32), np.diff(ptr)) * np.float32(config['synapse_mv'])
    engine = SensoryEngine(ptr, post, weights, sensory)
    output.mkdir(parents=True)
    (output / 'protocol.json').write_bytes(config_bytes)
    manifest = dict(identity=identity, status='running', neural_calls=0, completed_calls=0,
                    config_sha256=hashlib.sha256(config_bytes).hexdigest(), rows=[],
                    input_ids=input_ids, sample_ids=sample_ids,
                    interpretation=config['interpretation'])
    atomic_json(output / 'manifest.json', manifest)
    start = time.monotonic()
    first_sweet = None
    lo, hi = 25, 75
    try:
        trials = [(c, seed) for c in config['conditions'] for seed in config['seeds']]
        trials.append((config['conditions'][2], config['seeds'][0]))
        for number, (condition, seed) in enumerate(trials):
            if manifest['neural_calls'] >= config['max_calls'] or time.monotonic()-start >= config['wall_cap_seconds']:
                manifest['status'] = 'budget_stopped'
                break
            rates = np.zeros((100, len(sensory)), np.float32)
            for group, hz in condition['rates_hz'].items():
                rates[lo:hi, groups[group]] = hz
            manifest['neural_calls'] += 1
            atomic_json(output / 'manifest.json', manifest)
            result = engine.run(rates, bin_ms=20, dt=.2, seed=seed, sample=sample)
            np.savez_compressed(output / f'trial-{number:02d}.npz', requested_hz=rates,
                                counts=result['counts'], voltage=result['voltage'], trace=result['trace'],
                                input_events=result['input_events'], population=result['population'])
            generator = {}
            for group, indices in groups.items():
                hz = condition['rates_hz'].get(group, 0.)
                events = int(result['input_events'][lo:hi, indices].sum())
                p = hz*.2/1000
                generator[group] = dict(requested_hz=hz, delivered_events=events,
                    two_sided_binomial_p=float(binomtest(events, 5000*len(indices), p).pvalue) if p else float(events == 0))
            delivered = result['input_events'][lo:hi].sum(axis=0)
            achieved = result['trace'][lo:hi].sum(axis=0)
            mn_rates = result['trace'][lo:hi, mn_local].sum(axis=0).astype(float)
            row = dict(condition=condition['name'], seed=seed, repeat=number == 15,
                MN9_stimulus_hz=mn_rates.tolist(), MN9_stimulus_hz_mean=float(mn_rates.mean()),
                input_delivered_hz=delivered.tolist(), sampled_achieved_hz=achieved.tolist(), generator=generator,
                wall_seconds=result['wall_seconds'], total_spikes=int(result['counts'].sum()),
                active_neurons=int(np.count_nonzero(result['counts'])),
                max_abs_voltage_offset_mv=result['max_abs_voltage_offset_mv'],
                max_abs_synaptic_state_mv=result['max_abs_synaptic_state_mv'],
                high_rate_neuron_fraction=float(np.mean(result['counts']/2 > 100)),
                prestimulus_spikes=int(result['population'][:lo].sum()))
            numerical_ok = (row['prestimulus_spikes'] == 0 and row['high_rate_neuron_fraction'] < .05
                            and all(v['two_sided_binomial_p'] >= 1e-6 for v in generator.values()))
            row['numerical_generator_passed'] = numerical_ok
            if condition['name'] == 'sweet' and seed == 17:
                exact = (result['counts'].copy(), result['trace'].copy(), result['input_events'].copy())
                if first_sweet is None:
                    first_sweet = exact
                else:
                    row['exact_repeat_passed'] = all(np.array_equal(a, b) for a, b in zip(first_sweet, exact))
                    numerical_ok &= row['exact_repeat_passed']
            manifest['rows'].append(row)
            manifest['completed_calls'] += 1
            print(json.dumps({k: row[k] for k in ['condition', 'seed', 'MN9_stimulus_hz', 'wall_seconds',
                                                 'active_neurons', 'numerical_generator_passed']}), flush=True)
            if not numerical_ok:
                manifest['status'] = 'failed_numerical_or_generator'
                break
            atomic_json(output / 'manifest.json', manifest)
        if manifest['status'] == 'running':
            manifest['response'] = response_gates([r for r in manifest['rows'] if not r['repeat']])
            manifest['status'] = 'passed' if manifest['response']['passed'] else 'failed_response'
    except Exception as exc:
        manifest['status'] = 'failed_runtime'
        manifest['error'] = str(exc)
        raise
    finally:
        manifest['wall_seconds'] = time.monotonic()-start
        atomic_json(output / 'manifest.json', manifest)
    print(json.dumps(dict(identity=identity, status=manifest['status'], response=manifest.get('response'))))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    args = parser.parse_args()
    run(args.protocol)
