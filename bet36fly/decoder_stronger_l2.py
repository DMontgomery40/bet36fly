"""One fixed C-grid extension of the saved seed-42 decoder diagnostic."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import shutil

import numpy as np

from . import decoder_diagnostic as decoder
from .connectome import digest
from .experiment import atomic_json, utcnow

GRID = (0.00001, 0.0001, 0.001, 0.01)
EXPECTED = {('soccer', 'whole'): 1.023964, ('soccer', 'temporal'): 1.128515,
            ('baseball', 'whole'): 0.696803, ('baseball', 'temporal'): 0.721956}
TOLERANCE = 0.000001


@contextmanager
def fixed_grid(grid):
    """Reuse the original fitting code verbatim; restore its process-local default."""
    original = decoder.C_GRID
    decoder.C_GRID = tuple(grid)
    try:
        yield
    finally:
        decoder.C_GRID = original


def reproduction_gate(report):
    fits = {(r['sport'], r['representation']): r for r in report['fits']}
    if len(report['fits']) != 4 or set(fits) != set(EXPECTED):
        raise ValueError('Reproduction must contain exactly four C=0.01 fits.')
    checks = []
    for key, expected in EXPECTED.items():
        row = fits[key]
        actual = row['validation']['log_loss']
        error = abs(actual - expected)
        passed = bool(row['C'] == .01 and row['converged'] and np.isfinite(actual) and error <= TOLERANCE)
        checks.append(dict(sport=key[0], representation=key[1], expected=expected,
                           actual=actual, absolute_error=error, passed=passed))
    return dict(C=.01, tolerance=TOLERANCE, passed=all(c['passed'] for c in checks), checks=checks)


def run_extension(experiment, output):
    experiment, output = Path(experiment).resolve(), Path(output).resolve()
    if output.is_relative_to(experiment):
        raise ValueError('Output must be separate from the preserved experiment.')
    # Refuse even an empty existing directory, before any fits or source reads.
    output.mkdir(parents=True, exist_ok=False)
    status_path = output / 'status.json'
    atomic_json(status_path, dict(status='reproducing', created_at=utcnow(), C_grid=GRID))
    shutil.copy2(Path(__file__), output / 'decoder_stronger_l2.py')
    shutil.copy2(Path(decoder.__file__), output / 'decoder_diagnostic.py')
    try:
        with fixed_grid((.01,)):
            reference = decoder.run_diagnostic(experiment, output / 'reproduction')
        gate = reproduction_gate(reference)
        atomic_json(output / 'reproduction-gate.json', gate)
        if not gate['passed']:
            raise ValueError('C=0.01 reproduction failed; stronger settings were not run. See reproduction-gate.json.')
        atomic_json(status_path, dict(status='fitting-fixed-extension', reproduction_passed=True, C_grid=GRID))
        with fixed_grid(GRID[:-1]):
            extension = decoder.run_diagnostic(experiment, output / 'stronger-settings')
        for field in ('provenance', 'comparison_hashes', 'preprocessing', 'saved_validation_comparisons',
                      'code_sha256', 'numpy_version', 'sklearn_version'):
            if extension[field] != reference[field]:
                raise ValueError(f'Reproduction and extension setup differ: {field}')
        if ({k: v for k, v in extension['settings'].items() if k != 'C_grid'} !=
                {k: v for k, v in reference['settings'].items() if k != 'C_grid'}):
            raise ValueError('Decoder settings changed beyond C.')
        fits = sorted(reference['fits'] + extension['fits'], key=lambda r: (r['sport'], r['representation'], r['C']))
        best, conclusions = {}, []
        for sport in ('soccer', 'baseball'):
            best[sport] = {}
            for representation in ('whole', 'temporal'):
                choices = [r for r in fits if r['sport'] == sport and r['representation'] == representation and r['converged']]
                best[sport][representation] = min(choices, key=lambda r: (r['validation']['log_loss'], r['C']))
            whole, temporal = best[sport]['whole'], best[sport]['temporal']
            original = {r['representation']: r['validation']['log_loss'] for r in reference['fits'] if r['sport'] == sport}
            baseline = next(r['log_loss'] for r in reference['saved_validation_comparisons']
                            if r['sport'] == sport and r['model'] == 'feature-logistic')
            prior = next(r['log_loss'] for r in reference['saved_validation_comparisons']
                         if r['sport'] == sport and r['model'] == 'frequency-prior')
            conclusions.append(dict(sport=sport, original_temporal_minus_whole=original['temporal'] - original['whole'],
                selected_temporal_minus_whole=temporal['validation']['log_loss'] - whole['validation']['log_loss'],
                feature_logistic_validation_loss=baseline, frequency_prior_validation_loss=prior,
                neural_minus_feature_baseline={rep: row['validation']['log_loss'] - baseline for rep, row in best[sport].items()}))
        predictions, parameters = [], {}
        for directory in ('reproduction', 'stronger-settings'):
            predictions.extend(json.loads((output / directory / 'predictions.json').read_text()))
            with np.load(output / directory / 'decoders.npz', allow_pickle=False) as saved:
                for key in saved.files:
                    if key in parameters and not np.array_equal(parameters[key], saved[key]):
                        raise ValueError(f'Decoder scaling changed: {key}')
                    parameters[key] = saved[key].copy()
        np.savez(output / 'decoders.npz', **parameters)
        atomic_json(output / 'predictions.json', predictions)
        report = dict(reference, diagnostic='Frozen biological seed-42 stronger-L2 extension', created_at=utcnow(),
            extension_code_sha256=digest(Path(__file__)), reproduction=gate,
            settings=dict(reference['settings'], C_grid=list(GRID)), fits=fits, best_validation=best,
            matched_C_differences=sorted(reference['matched_C_differences'] + extension['matched_C_differences'],
                                         key=lambda r: (r['sport'], r['C'])), conclusions=conclusions,
            all_solvers_converged=all(r['converged'] for r in fits),
            limitations=['Single bounded development diagnostic; validation-selected scores are not independent confirmation.',
                'Only the fixed C grid changed; no feature selection, dimensionality reduction, or other decoder changes.',
                'Saved prior and feature-logistic comparisons were not refitted. No further grid extension is automatic.',
                'No simulations, gain training, matrix resume, extra seeds, historical/prospective evaluation or model promotion.'])
        report['artifact_hashes'] = {name: digest(output / name) for name in
            ('decoders.npz', 'predictions.json', 'decoder_diagnostic.py', 'decoder_stronger_l2.py', 'reproduction-gate.json')}
        atomic_json(output / 'report.json', report)
        atomic_json(status_path, dict(status='complete', completed_at=utcnow(), C_grid=GRID, fits=len(fits),
                                      reproduction_passed=True, automatic_extension=False))
        return report
    except Exception as exc:
        atomic_json(status_path, dict(status='stopped', stopped_at=utcnow(), error=str(exc), automatic_extension=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = run_extension(args.experiment, args.output)
    print(json.dumps(dict(output=args.output, reproduction=result['reproduction'], conclusions=result['conclusions'])), flush=True)
