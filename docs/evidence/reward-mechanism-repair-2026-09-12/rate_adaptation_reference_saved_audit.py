"""Read-only independent audit of the completed, root-frozen32-row screen.

No writer import. Numerical reference is frozen DAN ODE plus KC superposition.
The output directory is new and contains only this audit's evidence.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path
import time

import numpy as np

from rate_adaptation_reference_oracle import (
    AREA_ATOL, AREA_RTOL, C, DELTA_ATOL, DELTA_RTOL, STATE_ATOL, STATE_RTOL,
)
from rate_adaptation_reference_superposition import (
    integrate_dan_events, kc_boundary_states, kc_phase_products,
)

EXPECTED_MANIFEST = "5165a92674683bf2b872753148af74e3adf038ca7a95c64735dcda8e29e5ee46"
RUNS = ("diag-rate-bridge-v1-maskgamma-de050d773763", "diag-rate-bridge-v1-maskgamma-dea14759e9ca")
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(data):
    return json.loads(data, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def npz(data):
    with np.load(io.BytesIO(data), allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def bound_read(entry):
    path = Path(entry['path'])
    if not path.is_absolute():
        path = ROOT / path
    if any(parent.is_symlink() for parent in [path, *path.parents]):
        raise ValueError(f"symlink input: {path}")
    data = path.read_bytes()
    assert len(data) == entry['bytes'] and sha(data) == entry['sha256'], str(path)
    return data


def expected_rows():
    panels = ((4362, 4366, 4370, 4374, 4378, 4383, 4387, 4391),
              (4395, 4399, 4404, 4408, 4412, 4416, 4420, 4425))
    return [dict(game=game, seed_set=noise, seed=game+42+panel*2000000+offset, run_id=RUNS[panel])
            for panel, games in enumerate(panels) for game in games
            for noise, offset in [('base', 0), ('alt', 1000000)]]


def compare(actual, expected, atol, rtol):
    assert np.isfinite(actual).all() and np.isfinite(expected).all()
    np.testing.assert_allclose(actual, expected, atol=atol, rtol=rtol)
    return float(np.max(np.abs(actual-expected), initial=0))


def publication_check(actual, reference_double, *, row, phase):
    """Exact float32 or retained, justified one-ULP midpoint ambiguity only."""
    expected = reference_double.astype(np.float32).astype(float)
    actual = np.asarray(actual, dtype=float)
    assert np.array_equal(actual.astype(np.float32).astype(float), actual)
    ambiguities = []
    for edge in np.flatnonzero(actual != expected):
        a, b = np.float32(actual[edge]), np.float32(expected[edge])
        lower, upper = min(a, b), max(a, b)
        assert np.nextafter(lower, np.float32(np.inf), dtype=np.float32) == upper
        midpoint = (float(lower)+float(upper))/2
        uncertainty = DELTA_ATOL + DELTA_RTOL*abs(reference_double[edge]-1)
        assert abs(reference_double[edge]-midpoint) <= uncertainty
        ambiguities.append(dict(row=row, phase=phase, edge=int(edge), actual=float(a),
                                reference_rounded=float(b), midpoint=midpoint,
                                reference_double=float(reference_double[edge]), uncertainty=uncertainty))
    return ambiguities


def execute(screen, output):
    started = time.monotonic()
    screen, output = Path(screen), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    manifest_data = (screen/'manifest.json').read_bytes()
    assert sha(manifest_data) == EXPECTED_MANIFEST
    manifest = strict_json(manifest_data)
    summary_data = (screen/'summary.json').read_bytes()
    summary = strict_json(summary_data)
    assert summary['status'] == 'complete' and summary['candidate_evaluations'] == 32
    assert summary['attempted_evaluations'] == 32 and summary['native_calls'] == 0
    assert summary['manifest_sha256'] == EXPECTED_MANIFEST and summary['qualification'] is False
    assert summary['elapsed_seconds'] <= 600
    rows = expected_rows()
    assert manifest['rows'] == rows and [row['row'] for row in summary['rows']] == rows
    assert {p.name for p in screen.glob('attempt_*.json')} == {f'attempt_{i:02d}.json' for i in range(32)}
    assert {p.name for p in screen.glob('completed_*.json')} == {f'completed_{i:02d}.json' for i in range(32)}
    assert {p.name for p in screen.glob('adaptation_*.npz')} == {f'adaptation_{i:02d}.npz' for i in range(32)}
    bindings = manifest['files']
    for entry in bindings.values():
        bound_read(entry)
    freeze = strict_json((HERE/'rate-adaptation-reference-superposition-freeze-2026-09-13.json').read_bytes())
    for entry in freeze['files']:
        bound_read(entry)
    maps = npz(bound_read(bindings['samples']))
    pk, pc = maps['plastic_kc_indices'], maps['plastic_compartments']
    mask, groups, dc = maps['plastic_mask'].astype(bool), maps['plastic_groups'], maps['dan_compartments']
    assert pk.shape == pc.shape == mask.shape == groups.shape == (8866,)
    assert np.array_equal(np.bincount(pc), [4184, 4682])
    assert np.array_equal(np.bincount(pc, weights=mask), [4184, 3239])
    assert np.array_equal(np.bincount(dc), [2, 22]) and np.all(groups//4 == pc)

    means = np.zeros((32, 2000, 2))
    for i, row in enumerate(rows):
        attempt = strict_json((screen/f'attempt_{i:02d}.json').read_bytes())
        assert attempt['attempt'] == i+1 and attempt['row'] == row
        complete = strict_json((screen/f'completed_{i:02d}.json').read_bytes())
        assert complete == summary['rows'][i]
        bound_read(complete['output'])
        fine = npz(bound_read(bindings[f'fine_{i:02d}']))
        trace = fine['trace']
        assert trace.shape == (2000, 4774) and trace.dtype == np.int32 and np.isin(trace, [0, 1]).all()
        dan = trace[:, maps['dan_columns']]
        for c in range(2):
            means[i, :, c] = dan[:, dc == c].sum(axis=1)/np.count_nonzero(dc == c)
    print('All frozen inputs and32 completed rows verified; starting independent DAN ODE.', flush=True)
    weighted = integrate_dan_events(means)
    np.savez_compressed(output/'independent-dan-integrals.npz', states=weighted.states,
                        intervals=weighted.weighted_intervals, tail=weighted.weighted_tail)
    records, ambiguities = [], []
    metrics_data = {mode: [] for mode in ('adaptation', 'cold', 'continuous')}
    for i, row in enumerate(rows):
        fine = npz(bound_read(bindings[f'fine_{i:02d}']))
        kc = fine['trace'][:, maps['kc_columns']]
        candidate = npz(bound_read(summary['rows'][i]['output']))
        independent = kc_phase_products(kc, weighted.weighted_intervals[i], weighted.weighted_tail[i],
                                        (500, 650, 1500, 2000))
        edge_reference = independent[:, pc, pk, :]
        edge_reference[:, ~mask] = 0
        phases = candidate['edge_phases']
        assert phases.shape == (4, 8866, 8) and np.isfinite(phases).all()
        assert np.all(phases[:, :, 0] >= 0) and np.all(phases[:, :, 1] <= 0)
        assert np.all(phases[:, :, 5:7] == 0) and np.all(phases[:, ~mask] == 0)
        observed_products = np.stack((phases[:, :, 0], -phases[:, :, 1]), axis=-1)/C
        error = compare(observed_products, edge_reference, AREA_ATOL, AREA_RTOL)
        expected_delta = C*(edge_reference[..., 0]-edge_reference[..., 1])
        delta_error = compare(phases[..., 2], expected_delta, DELTA_ATOL, DELTA_RTOL)
        compare(phases[..., 3], expected_delta, DELTA_ATOL, DELTA_RTOL)
        compare(phases[..., 2], phases[..., 0]+phases[..., 1], DELTA_ATOL, DELTA_RTOL)
        compare(phases[..., 7], phases[..., 0]-phases[..., 1], DELTA_ATOL, DELTA_RTOL)
        expected_double = 1+expected_delta.cumsum(axis=0)
        observed_published = 1+phases[..., 4].cumsum(axis=0)
        for phase in range(4):
            ambiguities += publication_check(observed_published[phase], expected_double[phase], row=i, phase=phase)
        compare(candidate['double_gains']-1, expected_double[-1]-1, DELTA_ATOL, DELTA_RTOL)
        assert np.array_equal(candidate['gains'].astype(float), observed_published[-1])
        assert np.array_equal(candidate['electrical_gains'].astype(float), observed_published[2])
        assert np.array_equal(candidate['onset_gains'], np.ones(8866, np.float32))
        assert np.array_equal(candidate['onset_double_gains'], np.ones(8866))
        assert np.array_equal(candidate['gains'][~mask], np.ones(1443, np.float32))
        state_error = max(
            compare(candidate['onset_kc'], kc_boundary_states(kc, 500), STATE_ATOL, STATE_RTOL),
            compare(candidate['endpoint_kc'], kc_boundary_states(kc, 2000), STATE_ATOL, STATE_RTOL),
            compare(candidate['onset_dan'], weighted.states[i, 500], STATE_ATOL, STATE_RTOL),
            compare(candidate['endpoint_dan'], weighted.states[i, 2000], STATE_ATOL, STATE_RTOL),
        )
        for phase in range(4):
            for field in range(8):
                group = np.bincount(groups, weights=phases[phase, :, field], minlength=8)
                compare(candidate['group_phases'][phase, :, field], group, DELTA_ATOL, DELTA_RTOL)
        area = phases[..., 7].sum(axis=0)
        compare(candidate['absolute_area'], area, DELTA_ATOL, DELTA_RTOL)
        assert np.all(area < 0.5) and candidate['excursion_excluded'].all()
        for mode in metrics_data:
            values = candidate if mode == 'adaptation' else npz(bound_read(bindings[f'{mode}_{i:02d}']))
            metrics_data[mode].append([float((values['gains'].astype(float)[pc == c]-1).sum()) for c in range(2)])
            if mode == 'continuous':
                raw_area = (values['edge_phases'][..., 0]-values['edge_phases'][..., 1]).sum(axis=0)
                assert np.all(area <= raw_area+2e-12) and np.all(raw_area < 0.5)
                compare(candidate['continuous_absolute_area'], raw_area, DELTA_ATOL, DELTA_RTOL)
        np.savez_compressed(output/f'independent-products_{i:02d}.npz', products=edge_reference,
                            deltas=expected_delta)
        records.append(dict(row=row, edge_phase_products=4*8866*2,
                            maximum_unscaled_product_error=error, maximum_gain_delta_error=delta_error,
                            maximum_state_error=state_error, max_area=float(area.max()), passed=True))
        print(f'Independent complete-edge audit {i+1}/32 passed.', flush=True)

    metrics = {}
    for run in RUNS:
        for noise in ('base', 'alt'):
            selected = [j for j, row in enumerate(rows) if row['run_id'] == run and row['seed_set'] == noise]
            assert len(selected) == 8
            for c in range(2):
                key, cell = f'{run}/{noise}/{c}', {}
                for mode, raw in metrics_data.items():
                    values = np.array([raw[j][c] for j in selected])
                    mean, sd = float(values.mean()), float(values.std(ddof=1))
                    cell[mode] = dict(values=values.tolist(), mean=mean, sd=sd, limit=0.5*sd,
                                      passed=bool(abs(mean) <= 0.5*sd))
                    assert cell[mode] == summary['metrics'][key][mode]
                metrics[key] = cell
    verdict = all(value['adaptation']['passed'] for value in metrics.values())
    assert len(metrics) == 8 and verdict == summary['necessary_stability_screen']
    for entry in bindings.values():
        bound_read(entry)
    for record in summary['rows']:
        bound_read(record['output'])
    assert (screen/'manifest.json').read_bytes() == manifest_data
    assert (screen/'summary.json').read_bytes() == summary_data
    result = dict(status='complete', source_manifest_sha256=EXPECTED_MANIFEST,
                  source_summary_sha256=sha(summary_data), verified_input_files=len(bindings),
                  rows=records, metrics=metrics, necessary_stability_screen=verdict,
                  output_rounding_midpoint_ambiguities=ambiguities, ode_evaluations=weighted.evaluations,
                  new_circuit_calls=0, writer_imported=False, parent_sources_preserved=True,
                  elapsed_seconds=time.monotonic()-started,
                  source_hashes={str(p): sha(p.read_bytes()) for p in [Path(__file__),
                                 HERE/'rate_adaptation_reference_superposition.py',
                                 HERE/'rate_adaptation_reference_oracle.py']})
    with (output/'summary.json').open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({key: result[key] for key in ('status', 'necessary_stability_screen', 'elapsed_seconds')}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--screen', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    execute(args.screen, args.output)
