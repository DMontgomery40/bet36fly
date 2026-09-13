"""Frozen native coupling calibration; no changes to historical assay identities."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pyarrow.feather as feather
from scipy.stats import binomtest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly.connectome import ROOT  # noqa: E402
from bet36fly.experiment import atomic_json  # noqa: E402
from bet36fly.sensory import SensoryEngine  # noqa: E402
from scripts.run_sensory_assay import check_locked_files  # noqa: E402


def gates(rows, seeds):
    by = {k: [r for r in rows if r['condition'] == k] for k in ['null', 'water', 'sweet', 'bitter', 'mixed']}
    if any([r['seed'] for r in v] != seeds for v in by.values()):
        return {'complete': False, 'passed': False}
    checks = dict(null_silent=all(r['total_spikes'] == 0 for r in by['null']),
        sweet_activates=all(r['MN9_hz_mean'] > 1 for r in by['sweet']),
        bitter_not_appetitive=all(r['MN9_hz_mean'] <= 1 for r in by['bitter']),
        mixed_suppresses=all(a['MN9_hz_mean'] < b['MN9_hz_mean'] for a, b in zip(by['mixed'], by['sweet'])),
        offset_recovery=all(r['tail_spikes'] <= max(1, .01*r['stimulus_spikes']) and r['MN9_tail_spikes'] == 0 for r in rows),
        generator_numerical=all(r['generator_numerical_passed'] for r in rows))
    return dict(complete=True, passed=all(checks.values()), checks=checks)


def run(path):
    raw = path.read_bytes()
    config = json.loads(raw)
    identity = 'sensory-calibration-' + hashlib.sha256(raw).hexdigest()[:20]
    output = ROOT / 'output/sensory' / identity
    if output.exists():
        raise ValueError('Refusing an existing experiment identity.')
    check_locked_files(config, ROOT)
    if (config['dt_ms'] not in [.1, .2] or config['plasticity'] is not False
            or len(config['gains']) * len(config['conditions']) * len(config['seeds']) != config['max_calls']
            or config['max_calls'] > 100 or config['conditions'] != ['null', 'water', 'sweet', 'bitter', 'mixed']):
        raise ValueError('Invalid finite calibration schedule.')
    source = json.loads((ROOT / 'configs/sensory-assay-01.json').read_text())
    brain = ROOT / 'data/brain'
    ids, ptr, post, counts, signs = [np.load(brain / f'{k}.npy', mmap_mode='r')
                                   for k in ('ids', 'indptr', 'post', 'counts', 'signs')]
    nodes = feather.read_table(brain / 'nodes.feather').to_pandas()
    if not np.array_equal(ids, nodes.bodyId):
        raise ValueError('Native node order mismatch.')
    input_ids = sorted(sum([source['populations'][k] for k in ['sweet', 'water', 'bitter']], []))
    sample_ids = sorted(input_ids + source['populations']['MN9'])
    sensory = np.searchsorted(ids, input_ids).astype(np.int32)
    sample = np.searchsorted(ids, sample_ids).astype(np.int32)
    mn = [sample_ids.index(i) for i in source['populations']['MN9']]
    groups = {k: [input_ids.index(i) for i in source['populations'][k]] for k in ['sweet', 'water', 'bitter']}
    weights = counts * np.repeat(signs.astype(np.float32), np.diff(ptr))
    output.mkdir(parents=True)
    (output / 'protocol.json').write_bytes(raw)
    manifest = dict(identity=identity, status='running', neural_calls=0, rows=[], candidates=[],
                    input_ids=input_ids, sample_ids=sample_ids)
    atomic_json(output / 'manifest.json', manifest)
    start = time.monotonic()
    try:
        for gain in config['gains']:
            engine = SensoryEngine(ptr, post, weights * np.float32(gain), sensory)
            rows = []
            for condition in source['conditions']:
                rates = np.zeros((100, len(sensory)), np.float32)
                for group, hz in condition['rates_hz'].items():
                    rates[25:75, groups[group]] = hz
                for seed in config['seeds']:
                    if time.monotonic()-start > config['wall_cap_seconds']:
                        raise RuntimeError('Declared wall cap exceeded.')
                    number = manifest['neural_calls']
                    manifest['neural_calls'] += 1
                    atomic_json(output / 'manifest.json', manifest)
                    result = engine.run(rates, dt=config['dt_ms'], bin_ms=20, seed=seed, sample=sample)
                    np.savez_compressed(output / f'trial-{number:03d}.npz', requested_hz=rates,
                        **{k: v for k, v in result.items() if isinstance(v, np.ndarray)})
                    generator = []
                    for group, indices in groups.items():
                        hz = condition['rates_hz'].get(group, 0.)
                        events = int(result['input_events'][25:75, indices].sum())
                        p = hz*config['dt_ms']/1000
                        generator.append(float(binomtest(events, round(1000/config['dt_ms'])*len(indices), p).pvalue) if p else float(events == 0))
                    row = dict(trial=number, gain=gain, condition=condition['name'], seed=seed,
                        MN9_hz=result['trace'][25:75, mn].sum(axis=0).tolist(),
                        MN9_hz_mean=float(result['trace'][25:75, mn].sum(axis=0).mean()),
                        MN9_tail_spikes=int(result['trace'][-10:, mn].sum()),
                        tail_spikes=int(result['population'][-10:].sum()),
                        stimulus_spikes=int(result['population'][25:75].sum()),
                        total_spikes=int(result['counts'].sum()),
                        generator_numerical_passed=bool(min(generator) >= 1e-6 and not result['population'][:25].any()
                                                       and np.mean(result['counts']/2 > 100) < .05),
                        generator_p=generator, wall_seconds=result['wall_seconds'])
                    rows.append(row)
                    manifest['rows'].append(row)
                    atomic_json(output / 'manifest.json', manifest)
                    print(json.dumps(row), flush=True)
                    if not row['generator_numerical_passed']:
                        raise RuntimeError('Generator or numerical guard failed.')
            outcome = gates(rows, config['seeds'])
            manifest['candidates'].append(dict(gain=gain, **outcome))
            atomic_json(output / 'manifest.json', manifest)
        passing = [r['gain'] for r in manifest['candidates'] if r['passed']]
        manifest['selected_gain'] = min(passing) if passing else None
        manifest['status'] = 'passed' if passing else 'failed_response'
    except Exception as exc:
        manifest['status'] = 'failed_runtime'
        manifest['error'] = str(exc)
        raise
    finally:
        manifest['wall_seconds'] = time.monotonic()-start
        atomic_json(output / 'manifest.json', manifest)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    run(parser.parse_args().protocol)
