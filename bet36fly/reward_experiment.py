"""Bounded outcome-gated learning in the full measured MaleCNS graph."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

import numpy as np

from .connectome import ROOT
from .experiment import atomic_json, utcnow
from .experiments import Registry, writer_lock
from .learning import metrics
from .reward_brain import DAN_REFERENCE_MODES
from .reward_encoder import ENCODER_NAME
from .reward_protocol import MASK_POLICIES, decode, file_hash, fit_fixed_readout, make_circuit, select_rows

SOURCE_ID = 'v2-24a83145c27ab220116e'


def default_protocol():
    return dict(schema_version=4, seed=42, train_n=64, validation_n=32, calibration_n=16,
                duration_ms=400., stimulus_ms=300., teaching_ms=310., bin_ms=10.,
                plasticity_onset_ms=100., dan_baseline_window_ms=50.,
                dan_reference='none', away_plasticity_mask='all',
                teaching_pulse_count=4, teaching_interval_ms=20.,
                encoder=ENCODER_NAME, encoder_peak_hz=150., encoder_tuning_width=.5,
                encoder_min_kc_contacts=100., kc_input_gain=1.25, sensory_input_gain=0., apl_output_gain=.25,
                global_weight_scale=.5, tau_ms=500., learning_rate=.0005, gain_bounds=[.5, 1.5],
                wall_seconds=900., min_kc_active_fraction=.001, max_kc_active_fraction=.85,
                max_mbon_hz=400., min_teaching_evoked_fraction=.5, max_kc_code_overlap=.5,
                arms=['paired', 'shuffled', 'frozen'])


def validate_protocol(protocol):
    expected = default_protocol()
    if set(protocol) != set(expected):
        raise ValueError('Protocol fields must match the versioned reward schema.')
    if protocol['arms'] != expected['arms'] or protocol['schema_version'] != 4:
        raise ValueError('The bounded pilot requires schema 4 with paired, shuffled and frozen arms.')
    if protocol['encoder'] != ENCODER_NAME:
        raise ValueError('Schema 4 fixes the glomerular identity encoder.')
    if protocol['dan_reference'] not in DAN_REFERENCE_MODES:
        raise ValueError(f'dan_reference must be one of {sorted(DAN_REFERENCE_MODES)}.')
    if protocol['away_plasticity_mask'] not in MASK_POLICIES:
        raise ValueError(f'away_plasticity_mask must be one of {MASK_POLICIES}.')
    integer_fields = ('seed', 'train_n', 'validation_n', 'calibration_n', 'teaching_pulse_count')
    for key in integer_fields:
        value = protocol[key]
        if not isinstance(value, int) or isinstance(value, bool) or value < (0 if key == 'seed' else 1):
            raise ValueError(f'Invalid {key}.')
    nonnegative_fields = ('plasticity_onset_ms', 'dan_baseline_window_ms', 'encoder_min_kc_contacts', 'sensory_input_gain', 'apl_output_gain')
    for key in set(expected) - set(integer_fields) - {'arms', 'gain_bounds', 'schema_version', 'encoder',
                                                       'dan_reference', 'away_plasticity_mask'}:
        value = protocol[key]
        floor = 0 if key in nonnegative_fields else None
        if (not isinstance(value, (int, float)) or isinstance(value, bool) or not np.isfinite(value)
                or (value < 0 if floor == 0 else value <= 0)):
            raise ValueError(f'Invalid finite {"nonnegative" if floor == 0 else "positive"} {key}.')
    bounds = np.asarray(protocol['gain_bounds'], float)
    if (bounds.shape != (2,) or not np.isfinite(bounds).all() or not 0 < bounds[0] <= 1 <= bounds[1]
            or not 2 <= protocol['calibration_n'] <= protocol['train_n'] or protocol['train_n'] > 64
            or protocol['validation_n'] > 32 or protocol['calibration_n'] > 16
            or protocol['duration_ms'] > 10000 or protocol['wall_seconds'] > 1800
            or protocol['seed'] >= 2**32 or protocol['teaching_pulse_count'] > 10
            or not 0 < protocol['min_kc_active_fraction'] < protocol['max_kc_active_fraction'] <= 1
            or not 0 < protocol['min_teaching_evoked_fraction'] <= 1
            or not 0 < protocol['max_kc_code_overlap'] <= 1
            or protocol['encoder_peak_hz'] > 1000 or protocol['kc_input_gain'] > 10
            or protocol['sensory_input_gain'] > 10 or protocol['apl_output_gain'] > 10):
        raise ValueError('Protocol exceeds the bounded pilot or invalid gain/activity/teaching bounds.')
    if not protocol['dan_baseline_window_ms'] <= protocol['plasticity_onset_ms'] < protocol['teaching_ms']:
        raise ValueError('The tonic baseline window must end at a plasticity onset that precedes teaching.')
    for key in ('duration_ms', 'stimulus_ms', 'teaching_ms', 'bin_ms', 'teaching_interval_ms',
                'plasticity_onset_ms', 'dan_baseline_window_ms'):
        if not np.isclose(protocol[key] / .2, round(protocol[key] / .2), rtol=0, atol=1e-7):
            raise ValueError('Protocol timing must align to the fixed 0.2 ms step.')
    for key in ('duration_ms', 'stimulus_ms'):
        if not np.isclose(protocol[key] / protocol['bin_ms'], round(protocol[key] / protocol['bin_ms'])):
            raise ValueError('Trial and stimulus duration must align to recording bins.')
    last_pulse = protocol['teaching_ms'] + (protocol['teaching_pulse_count'] - 1) * protocol['teaching_interval_ms']
    if not 0 < protocol['stimulus_ms'] <= protocol['teaching_ms'] <= last_pulse < protocol['duration_ms']:
        raise ValueError('Teaching must follow the stimulus and fit inside the trial.')
    return protocol


class BudgetStop(RuntimeError):
    pass


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def run_experiment(root=ROOT, protocol=None, *, circuit_factory=make_circuit):
    root, protocol = Path(root), validate_protocol(default_protocol() if protocol is None else protocol)
    started = time.monotonic()
    source = root / f'output/experiments/{SOURCE_ID}/source'
    data_file, games_file = source / 'training-data.npz', source / 'training-games.json'
    arrays = dict(np.load(data_file, allow_pickle=False))
    games = json.loads(games_file.read_text())['games']
    rows = select_rows(arrays, games, **{k: protocol[k] for k in ('train_n', 'validation_n', 'calibration_n')})
    module_dir = Path(__file__).parent
    code_paths = [module_dir / name for name in ('reward_lif.cpp', 'reward_brain.py', 'reward_encoder.py',
                  'reward_protocol.py', 'reward_experiment.py', 'learning.py')]
    identity = dict(protocol=protocol, source_hashes={'data': file_hash(data_file), 'games': file_hash(games_file)},
                    code_hashes={p.name: file_hash(p) for p in code_paths})
    # Graph identity is frozen by the adapter before any simulated trial. These
    # source hashes also ensure a changed prepared graph gets a new run identity.
    graph_files = sorted((root / 'data/brain').glob('*.npy'))
    identity['graph_hashes'] = {p.name: file_hash(p) for p in graph_files}
    node_annotation = root / 'data/brain/nodes.feather'
    if node_annotation.exists():
        identity['node_annotations_sha256'] = file_hash(node_annotation)
    raw_annotation = root / 'data/raw/annotations.feather'
    if raw_annotation.exists():
        identity['raw_annotations_sha256'] = file_hash(raw_annotation)
    identifier = 'reward-v3-' + _digest(identity)[:20]
    directory = root / 'output/experiments' / identifier
    protected = [p for p in (root / 'output/current-model.json', source.parent / 'manifest.json',
                             data_file, games_file) if p.exists()]
    before = {str(p.relative_to(root)): file_hash(p) for p in protected}
    rule_name = 'event-biphasic-kc-dan-raw-v3' if protocol['dan_reference'] == 'none' else 'event-biphasic-kc-dan-phasic-v2'
    rule_note = ('Dopamine drive is the raw compartment-mean DAN spike count in both rule terms (upstream form); '
                 'each compartment\'s tonic rate before the plasticity onset is measured and reported, not subtracted.'
                 if protocol['dan_reference'] == 'none' else
                 'Dopamine drive is phasic: each compartment\'s tonic rate, measured before the declared plasticity '
                 'onset, is subtracted in both rule terms (legacy schema-2/3 rule, kept for comparison).')
    mask_note = ('Away-side plasticity is restricted to gamma-KC inputs of MBON09; excluded edges keep transmitting. '
                 if protocol['away_plasticity_mask'] == 'gamma' else 'Every listed KC-to-MBON edge is plastic. ')
    initial = dict(id=identifier, schema_version=4, kind='dopamine-association', status='running',
                   created_at=utcnow(), identity=identity, protocol=protocol, artifacts={}, selected_shadow=None,
                   jobs=[dict(id=arm, variant=arm, seed=protocol['seed'], status='queued', phase='queued',
                              gain_parameters=0, decoder_parameters=0, active_parameters=0,
                              completed=0, total=protocol['train_n'] + protocol['validation_n'])
                         for arm in protocol['arms']],
                   reward=dict(scope='reused-development-pilot', rule=rule_name,
                               dan_reference=protocol['dan_reference'],
                               away_plasticity_mask=protocol['away_plasticity_mask'],
                               encoder=protocol['encoder'],
                               note='Artificial sports-to-glomerulus and outcome-to-DAN mappings; fixed readout. '
                                    'Each feature drives its own tuned set of annotated ALPN glomeruli, so which '
                                    'ports fire depends on the game. ' + rule_note + ' ' + mask_note +
                                    'This tests on-circuit associative learning, not biological RPE or betting edge.',
                               train_n=protocol['train_n'], validation_n=protocol['validation_n'],
                               calibration_n=protocol['calibration_n'], embargoed_training_labels=rows['embargoed']))

    def budget():
        if time.monotonic() - started >= protocol['wall_seconds']:
            raise BudgetStop('Declared wall-clock budget reached; unfinished jobs are not results.')

    with writer_lock(root / 'output/experiments'):
        if directory.exists():
            raise FileExistsError(f'Experiment already exists: {identifier}; automatic reruns are forbidden.')
        registry = Registry(directory, initial)
        try:
            freeze = directory / 'source'
            freeze.mkdir()
            for path in code_paths:
                shutil.copyfile(path, freeze / path.name)
            selected = np.concatenate([rows['train_indices'], rows['validation_indices']])
            np.savez(freeze / 'inputs.npz', X=arrays['X'][selected], y=arrays['y'][selected],
                     source_indices=selected, input_mean=rows['input_mean'], input_std=rows['input_std'],
                     calibration_indices=rows['calibration_indices'])
            atomic_json(freeze / 'games.json', {'games': [games[int(i)] for i in selected]})
            atomic_json(freeze / 'protocol.json', protocol)
            budget()
            engine, anatomy, outputs, dan_compartments, kc, sensory, encode = circuit_factory(root, protocol, n_features=int(arrays['X'].shape[1]))
            registry.manifest['reward']['anatomy'] = anatomy
            atomic_json(freeze / 'anatomy.json', anatomy)
            output_count = sum(map(len, outputs))
            dan_count = len(engine.dan_indices)
            dan_slice = slice(output_count, output_count + dan_count)
            kc_slice = slice(output_count + dan_count, output_count + dan_count + len(kc))
            sampled = np.concatenate([*outputs, engine.dan_indices, kc])
            n_bins = round(protocol['duration_ms'] / protocol['bin_ms'])
            stimulus_bins = round(protocol['stimulus_ms'] / protocol['bin_ms'])
            output_slices = [slice(0, len(outputs[0])), slice(len(outputs[0]), output_count)]
            blank_gains = engine.gains.copy()
            compartment_sizes = [int(np.count_nonzero(dan_compartments == c)) for c in (0, 1)]

            def jaccard(a, b):
                union = a | b
                return len(a & b) / len(union) if union else 1.0

            def trial(i, *, teach=None, learn=False, seed_override=None):
                budget()
                features = np.clip((arrays['X'][i] - rows['input_mean']) / rows['input_std'], -8, 8)
                schedule = np.zeros((n_bins, len(sensory)), np.float32)
                schedule[:stimulus_bins] = encode(features)
                pulses = []
                if teach is not None:
                    compartment = 0 if teach == 0 else 1
                    pulses = [(protocol['teaching_ms'] + pulse * protocol['teaching_interval_ms'], int(dan))
                              for pulse in range(protocol['teaching_pulse_count'])
                              for dan in np.flatnonzero(dan_compartments == compartment)]
                trial_seed = protocol['seed'] + int(i) if seed_override is None else seed_override
                out = engine.run(schedule, bin_ms=protocol['bin_ms'], seed=trial_seed,
                                 teaching_pulses=pulses, plasticity=learn, sample=sampled)
                budget()
                # Read activity before the teaching signal; probe calls have no teaching at all.
                activity = out['trace'][:stimulus_bins].sum(0) * (1000 / protocol['stimulus_ms'])
                response = np.array([activity[s].mean() for s in output_slices])
                return out, response

            calibration, activity, kc_sets, persistence, tonic_rates = [], [], [], [], []
            registry.manifest['reward']['activity_gate'] = {'status': 'running', 'message': 'Measuring initial circuit responses.'}
            registry.save()
            for count, i in enumerate(rows['calibration_indices'], 1):
                out, response = trial(int(i))
                if count == 1:
                    first_calibration = out
                calibration.append(response)
                activity.append((np.count_nonzero(out['counts'][kc]) / len(kc), float(response.max())))
                kc_bins = out['trace'][:, kc_slice]
                kc_sets.append(set(np.flatnonzero(kc_bins[:stimulus_bins].sum(0)).tolist()))
                persistence.append(float(np.count_nonzero(kc_bins[stimulus_bins:].sum(0)) / len(kc)))
                tonic_rates.append(out['compartment_tonic_hz'])
                registry.manifest['reward']['calibration_completed'] = count
                registry.save()
            fixed = fit_fixed_readout(np.asarray(calibration), arrays['y'][rows['train_indices']])
            registry.manifest['reward']['fixed_readout'] = fixed
            registry.manifest['reward']['fixed_readout_sha256'] = _digest(fixed)
            atomic_json(freeze / 'readout.json', fixed)
            fraction = float(np.mean([a[0] for a in activity]))
            maximum = float(max(a[1] for a in activity))
            first_index = int(rows['calibration_indices'][0])
            common_seed = protocol['seed'] + first_index
            _, alternate_response = trial(int(rows['calibration_indices'][-1]), seed_override=common_seed)
            discrimination = not np.array_equal(alternate_response, calibration[0])
            baseline_dan = first_calibration['trace'][:, dan_slice]
            teaching_responsive, teaching_spikes, teaching_traces, pulse_times, pulse_dans = [], [], [], [], []
            teaching_scheduled, teaching_evoked = [], []
            teaching_bin = int(protocol['teaching_ms'] // protocol['bin_ms'])
            for label, compartment in ((0, 0), (2, 1)):
                taught, _ = trial(first_index, teach=label, seed_override=common_seed)
                trace = taught['trace'][:, dan_slice]
                target = dan_compartments == compartment
                scheduled = protocol['teaching_pulse_count'] * compartment_sizes[compartment]
                evoked = int(trace[teaching_bin:, target].sum() - baseline_dan[teaching_bin:, target].sum())
                # The pulses are meant to force one spike per DAN each; a population already
                # at its refractory ceiling cannot carry them, and then teaching is absent.
                teaching_responsive.append(bool(evoked > 0 and evoked >= protocol['min_teaching_evoked_fraction'] * scheduled))
                teaching_scheduled.append(int(scheduled))
                teaching_evoked.append(evoked)
                teaching_spikes.append(int(trace[teaching_bin:, target].sum()))
                teaching_traces.append(trace)
                pulse_times.append(taught['pulse_times_ms'])
                pulse_dans.append(taught['pulse_dan_indices'])
            gate_path = freeze / 'activity-gate.npz'
            np.savez(gate_path, baseline_dan_bins=baseline_dan, teaching_dan_bins=teaching_traces,
                     dan_compartments=dan_compartments, common_seed=common_seed,
                     pulse_times_ms=np.concatenate(pulse_times), pulse_dan_indices=np.concatenate(pulse_dans),
                     calibration_responses=calibration, alternate_response=alternate_response)
            registry.artifact(gate_path, label='Activity and teaching response checks')
            overlap = float(np.mean([jaccard(a, b) for k, a in enumerate(kc_sets) for b in kc_sets[k + 1:]])
                            if len(kc_sets) > 1 else 1.0)
            tonic_hz = np.mean(tonic_rates, axis=0).tolist()
            post_fraction = float(np.mean(persistence))
            failures = []
            if not protocol['min_kc_active_fraction'] <= fraction <= protocol['max_kc_active_fraction']:
                failures.append('KC active fraction is outside the declared range')
            if maximum > protocol['max_mbon_hz']:
                failures.append('an output population exceeds the MBON rate guard')
            if not np.all(np.max(calibration, axis=0) > 0):
                failures.append('an output population never fired during calibration')
            if not discrimination:
                failures.append('different inputs gave identical output under a common seed')
            if not all(teaching_responsive):
                failures.append('a teaching population evoked fewer spikes above its tonic rate than the declared margin')
            if overlap > protocol['max_kc_code_overlap']:
                failures.append('the active KC set is not game-specific (calibration overlap exceeds the guard)')
            passed = not failures
            gate = dict(status='passed' if passed else 'failed', kc_active_fraction=fraction,
                        max_mbon_hz=maximum, input_discrimination=discrimination,
                        teaching_responsive=teaching_responsive, teaching_compartment_spikes=teaching_spikes,
                        teaching_scheduled_spikes=teaching_scheduled, teaching_evoked_spikes=teaching_evoked,
                        tonic_dan_hz=tonic_hz, kc_code_overlap=overlap,
                        post_stimulus_kc_active_fraction=post_fraction,
                        message='Inputs alter output with a common random seed; both teaching populations evoke spikes '
                                'above their tonic rate; the KC code differs between games; activity is inside numerical guards.'
                        if passed else 'No outcome-trained comparison ran: ' + '; '.join(failures) + '.')
            registry.manifest['reward']['activity_gate'] = gate
            registry.artifact(freeze / 'readout.json', label='Frozen task readout')
            registry.save()
            if not passed:
                raise RuntimeError(gate['message'])
            labels = arrays['y'][rows['train_indices']]
            shuffled = np.random.default_rng(protocol['seed']).permutation(labels)
            if np.array_equal(shuffled, labels) and len(np.unique(labels)) > 1:
                shuffled = np.roll(labels, 1)
            atomic_json(freeze / 'teaching.json', dict(original=labels.tolist(), shuffled=shuffled.tolist(),
                                                      timing='Outcome delivered after encoded stimulus in replay training.'))
            for job in registry.manifest['jobs']:
                arm, job_start = job['variant'], time.monotonic()
                engine.gains[:] = blank_gains
                registry.update(job, status='running', phase='outcome-teaching', completed=0,
                                gain_parameters=len(blank_gains), active_parameters=0 if arm == 'frozen' else len(blank_gains),
                                fixed_readout_sha256=_digest(fixed), reward_curve=[])
                neural_stats, dan_counts, dan_bins, teaching_labels, arm_tonic = [], [], [], [], []
                for number, i in enumerate(rows['train_indices']):
                    teaching = int(shuffled[number] if arm == 'shuffled' else labels[number])
                    out, response = trial(int(i), teach=teaching, learn=arm != 'frozen')
                    dan_counts.append(out['dan_counts'])
                    dan_bins.append(out['trace'][:, dan_slice])
                    teaching_labels.append(teaching)
                    arm_tonic.append(out['compartment_tonic_hz'])
                    neural_stats.append((np.count_nonzero(out['counts'][kc]) / len(kc), int(out['dan_counts'].sum()), float(response.mean())))
                    job['reward_curve'].append(dict(trial=number + 1, gain_mean=float(engine.gains.mean()),
                                                     dan_spikes=int(out['dan_counts'].sum()),
                                                     dan_compartment_spikes=out['compartment_dan_counts'].tolist(),
                                                     home_response=float(response[0]), away_response=float(response[1])))
                    registry.update(job, completed=number + 1, elapsed_seconds=time.monotonic() - job_start)
                trained_gains = engine.gains.copy()
                predictions = []
                registry.update(job, phase='frozen-evaluation')
                for number, i in enumerate(rows['validation_indices']):
                    out, response = trial(int(i))
                    predictions.append(decode(response, fixed))
                    registry.update(job, completed=protocol['train_n'] + number + 1,
                                    elapsed_seconds=time.monotonic() - job_start)
                if not np.array_equal(engine.gains, trained_gains):
                    raise RuntimeError('An evaluation probe changed synaptic gains.')
                scores = metrics(arrays['y'][rows['validation_indices']], np.asarray(predictions))
                evidence = dict(changed_edges=int(np.count_nonzero(trained_gains != blank_gains)),
                                gain_min=float(trained_gains.min()), gain_max=float(trained_gains.max()),
                                gain_mean=float(trained_gains.mean()),
                                lower_bound_fraction=float(np.mean(trained_gains <= protocol['gain_bounds'][0] + 1e-6)),
                                upper_bound_fraction=float(np.mean(trained_gains >= protocol['gain_bounds'][1] - 1e-6)),
                                kc_active_fraction=float(np.mean([s[0] for s in neural_stats])),
                                dan_spikes=sum(s[1] for s in neural_stats),
                                dan_compartment_spikes=[int(np.asarray(dan_counts)[:, dan_compartments == c].sum()) for c in (0, 1)],
                                tonic_dan_hz=np.mean(arm_tonic, axis=0).tolist(),
                                mbon_mean_hz=float(np.mean([s[2] for s in neural_stats])))
                truth = arrays['y'][rows['validation_indices']]
                predicted = np.argmax(predictions, axis=1)
                confusion = [[int(np.count_nonzero((truth == t) & (predicted == p))) for p in (0, 2)] for t in (0, 2)]
                artifact = directory / f'{arm}-results.npz'
                np.savez(artifact, gains=trained_gains, predictions=predictions,
                         training_dan_counts=dan_counts, training_dan_bins=dan_bins,
                         training_teaching_labels=teaching_labels, training_source_indices=rows['train_indices'],
                         dan_compartments=dan_compartments,
                         source_indices=rows['validation_indices'], labels=arrays['y'][rows['validation_indices']])
                registry.artifact(artifact, label=f'{arm.title()} gains and matched predictions', job=job['id'])
                registry.update(job, status='complete', phase='complete', wall_seconds=time.monotonic() - job_start,
                                metrics={'validation': {'baseball': scores}}, validation_loss=scores['log_loss'],
                                reward_evidence=evidence, class_confusion=confusion, evaluation_gains_unchanged=True)
            jobs = {j['variant']: j for j in registry.manifest['jobs']}
            prior_p = np.tile([fixed['prior'][0], 0, fixed['prior'][1]], (len(rows['validation_indices']), 1))
            prior_scores = metrics(arrays['y'][rows['validation_indices']], prior_p)
            registry.manifest['reward']['prior_metrics'] = prior_scores
            registry.manifest['reward']['outcome'] = dict(status='descriptive',
                message='Completed fixed-readout development comparison; one seed and 32 or fewer reused validation games cannot establish predictive superiority.',
                paired_minus_frozen_log_loss=jobs['paired']['validation_loss'] - jobs['frozen']['validation_loss'],
                paired_minus_shuffled_log_loss=jobs['paired']['validation_loss'] - jobs['shuffled']['validation_loss'])
            budget()
            registry.manifest['status'] = 'complete'
        except Exception as exc:
            status = 'budget_stopped' if isinstance(exc, BudgetStop) else 'failed'
            registry.manifest.update(status=status, error=str(exc))
            registry.manifest['reward']['outcome'] = dict(status=status, message=str(exc))
            for job in registry.manifest['jobs']:
                if job['status'] != 'complete':
                    job.update(status=status, phase=status, error=str(exc))
        finally:
            after = {str(p.relative_to(root)): file_hash(p) for p in protected}
            registry.manifest['protected_inputs_unchanged'] = before == after
            if before != after:
                registry.manifest.update(status='failed', error='Protected prior experiment/model inputs changed during execution.')
            registry.manifest['wall_seconds'] = time.monotonic() - started
            for name in ('protocol.json', 'anatomy.json', 'readout.json'):
                path = directory / 'source' / name
                if path.exists():
                    registry.artifact(path, label=name.removesuffix('.json').replace('_', ' ').title())
            registry.save()
            report = directory / 'report.json'
            atomic_json(report, registry.manifest)
            registry.artifact(report, label='Complete measured reward experiment report')
            registry.save()
        return registry.manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    result = run_experiment(args.root, json.loads(args.protocol.read_text()))
    print(json.dumps({'id': result['id'], 'status': result['status'], 'wall_seconds': result['wall_seconds'],
                      'outcome': result['reward'].get('outcome')}, indent=2))
    if result['status'] != 'complete':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
