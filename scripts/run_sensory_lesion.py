"""Nine matched source-class lesions with immutable artifacts and no plasticity."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pyarrow.feather as feather

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly.connectome import ROOT  # noqa: E402
from bet36fly.experiment import atomic_json  # noqa: E402
from bet36fly.sensory import SensoryEngine  # noqa: E402
from bet36fly.sensory_lesion import lesion_weights  # noqa: E402
from scripts.run_sensory_assay import check_locked_files  # noqa: E402


def run(path):
    raw = path.read_bytes()
    config = json.loads(raw)
    identity = 'sensory-lesion-' + hashlib.sha256(raw).hexdigest()[:20]
    output = ROOT / 'output/sensory' / identity
    if output.exists():
        raise ValueError('Refusing existing experiment identity.')
    check_locked_files(config, ROOT)
    if config['trials'] != [53, 56, 59] or config['modes'] != ['modulator', 'ALLN', 'union']:
        raise ValueError('Unsupported diagnostic schedule.')
    base = ROOT / config['baseline']
    baseline = json.loads((base / 'manifest.json').read_text())
    brain = ROOT / 'data/brain'
    ids, ptr, post, counts, signs = [np.load(brain / f'{k}.npy', mmap_mode='r')
                                   for k in ('ids', 'indptr', 'post', 'counts', 'signs')]
    nodes = feather.read_table(brain / 'nodes.feather').to_pandas()
    if not np.array_equal(ids, nodes.bodyId):
        raise ValueError('Node order differs from graph.')
    sensory = np.searchsorted(ids, baseline['input_ids']).astype(np.int32)
    sample = np.searchsorted(ids, baseline['sample_ids']).astype(np.int32)
    mn = [baseline['sample_ids'].index(i) for i in (10331, 16949)]
    weights = counts * np.repeat(signs.astype(np.float32), np.diff(ptr)) * np.float32(.22)
    output.mkdir(parents=True)
    (output / 'protocol.json').write_bytes(raw)
    manifest = dict(identity=identity, status='running', neural_calls=0, rows=[])
    atomic_json(output / 'manifest.json', manifest)
    try:
        for mode in config['modes']:
            engine = SensoryEngine(ptr, post, lesion_weights(nodes, ptr, weights, mode)[0], sensory)
            for trial in config['trials']:
                reference = np.load(base / f'trial-{trial:03d}.npz')
                seed = baseline['rows'][trial]['seed']
                manifest['neural_calls'] += 1
                atomic_json(output / 'manifest.json', manifest)
                result = engine.run(reference['requested_hz'], bin_ms=20, dt=.2, seed=seed, sample=sample)
                np.savez_compressed(output / f'{mode}-{trial:02d}.npz', **{k: v for k, v in result.items()
                                    if isinstance(v, np.ndarray)})
                row = dict(mode=mode, trial=trial, condition=baseline['rows'][trial]['condition'], seed=seed,
                    input_events_identical=bool(np.array_equal(result['input_events'], reference['input_events'])),
                    MN9_hz=result['trace'][25:75, mn].sum(axis=0).tolist(),
                    tail_spikes=int(result['population'][-10:].sum()),
                    reference_tail_spikes=int(reference['population'][-10:].sum()),
                    total_spikes=int(result['counts'].sum()), wall_seconds=result['wall_seconds'])
                row['tail_reduction_at_least_90_percent'] = row['tail_spikes'] <= .1*row['reference_tail_spikes']
                manifest['rows'].append(row)
                print(json.dumps(row), flush=True)
                atomic_json(output / 'manifest.json', manifest)
                if not row['input_events_identical']:
                    raise RuntimeError('Matched-input check failed.')
        manifest['status'] = 'completed'
        manifest['hypothesis_supported'] = all(r['tail_reduction_at_least_90_percent'] for r in manifest['rows'])
    except Exception as exc:
        manifest['status'] = 'failed_runtime'
        manifest['error'] = str(exc)
        raise
    finally:
        atomic_json(output / 'manifest.json', manifest)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    run(parser.parse_args().protocol)
