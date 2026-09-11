import json

import numpy as np
import pytest

from bet36fly.reward_experiment import run_experiment, default_protocol, validate_protocol
from bet36fly.reward_brain import RewardEngine
from bet36fly.experiments import read_experiment
from test_reward_protocol import source_rows


def install_source(root):
    path = root / 'output/experiments/v2-24a83145c27ab220116e/source'
    path.mkdir(parents=True)
    arrays, games = source_rows()
    np.savez(path / 'training-data.npz', **arrays)
    (path / 'training-games.json').write_text(json.dumps({'games': games}))
    (path.parent / 'manifest.json').write_text('{"id":"v2-24a83145c27ab220116e","status":"paused","jobs":[]}')
    (root / 'output/current-model.json').write_text('{"run_id":"protected-v1"}')
    return path


def circuit(root, protocol, **_):
    # Sensory 0/1 -> KC 2/3 -> MBON 6/7. DAN 4/5 carry no fast output.
    engine = RewardEngine([0, 1, 2, 3, 4, 4, 4, 4, 4], [2, 3, 6, 7], [160.] * 4,
                          [0, 1], [2, 3], [4, 5], [0, 1], [2, 3], [0, 1], [0, 1],
                          n_compartments=2, tau_ms=protocol['tau_ms'],
                          learning_rate=protocol['learning_rate'], gain_bounds=protocol['gain_bounds'],
                          plasticity_onset_ms=protocol['plasticity_onset_ms'],
                          dan_baseline_window_ms=protocol['dan_baseline_window_ms'])
    def encode(features):
        # Both fake ports stay driven for every game so the shared-code guard can be exercised.
        return (150 + 20 * np.tanh(np.array([features[0], -features[0]]) / 2)).astype(np.float32)
    return engine, {'neurons': 8, 'kc': 2, 'dans': 2, 'plastic_edges': 2, 'compartments': []}, \
        [np.array([6]), np.array([7])], np.array([0, 1]), np.array([2, 3]), np.array([0, 1]), encode


def small_protocol():
    return dict(default_protocol(), train_n=4, validation_n=3, calibration_n=2,
                duration_ms=50., stimulus_ms=30., teaching_ms=30., bin_ms=10.,
                plasticity_onset_ms=10., dan_baseline_window_ms=10.,
                teaching_pulse_count=1, wall_seconds=20., max_mbon_hz=1000., max_kc_active_fraction=1.,
                max_kc_code_overlap=1.)


def test_real_native_runner_freezes_controls_and_preserves_prior_experiment(tmp_path):
    source = install_source(tmp_path)
    protected = [(source.parent / 'manifest.json'), tmp_path / 'output/current-model.json']
    before = [p.read_bytes() for p in protected]
    result = run_experiment(tmp_path, small_protocol(), circuit_factory=circuit)
    assert result['status'] == 'complete'
    assert result['kind'] == 'dopamine-association'
    assert {j['variant'] for j in result['jobs']} == {'paired', 'shuffled', 'frozen'}
    frozen = next(j for j in result['jobs'] if j['variant'] == 'frozen')
    assert frozen['reward_evidence']['changed_edges'] == 0
    for job in result['jobs']:
        assert job['status'] == 'complete'
        assert job['metrics']['validation']['baseball']['n'] == 3
        assert len(job['reward_curve']) == 4
        assert job['fixed_readout_sha256'] == result['reward']['fixed_readout_sha256']
        assert job['evaluation_gains_unchanged'] is True
        assert np.asarray(job['class_confusion']).sum() == 3
        evidence = job['reward_evidence']
        assert sum(evidence['dan_compartment_spikes']) == evidence['dan_spikes']
        artifact = np.load(tmp_path / 'output/experiments' / result['id'] / f"{job['variant']}-results.npz")
        assert artifact['training_dan_bins'].shape == (4, 5, 2)
        np.testing.assert_array_equal(artifact['training_dan_bins'].sum(axis=1), artifact['training_dan_counts'])
    gate = result['reward']['activity_gate']
    assert gate['status'] == 'passed'
    assert gate['teaching_scheduled_spikes'] == [1, 1] and gate['teaching_evoked_spikes'] == [1, 1]
    assert gate['tonic_dan_hz'] == [0, 0] and gate['kc_code_overlap'] == 1.0
    assert 0 <= gate['post_stimulus_kc_active_fraction'] <= 1
    assert result['reward']['rule'] == 'event-biphasic-kc-dan-phasic-v2'
    assert result['reward']['encoder'] == 'glomerular-tuning-v1'
    assert 'reward_encoder.py' in result['identity']['code_hashes']
    assert (tmp_path / 'output/experiments' / result['id'] / 'source/reward_encoder.py').exists()
    assert [p.read_bytes() for p in protected] == before
    stored = read_experiment(tmp_path / 'output/experiments', result['id'])
    assert stored['reward']['outcome']['status'] == 'descriptive'
    assert result['artifacts']
    with pytest.raises(FileExistsError):
        run_experiment(tmp_path, small_protocol(), circuit_factory=circuit)


def test_budget_stop_is_saved_and_not_reported_as_completed(tmp_path):
    install_source(tmp_path)
    result = run_experiment(tmp_path, dict(small_protocol(), wall_seconds=1e-9), circuit_factory=circuit)
    assert result['status'] == 'budget_stopped'
    assert all(j['status'] != 'complete' for j in result['jobs'])
    assert result['reward']['outcome']['status'] == 'budget_stopped'


def test_native_call_finishing_after_budget_never_reports_success(tmp_path, monkeypatch):
    import bet36fly.reward_experiment as module
    install_source(tmp_path)
    clock, calls = [0.], [0]
    monkeypatch.setattr(module.time, 'monotonic', lambda: clock[0])

    def slow_factory(root, protocol, **kw):
        values = circuit(root, protocol, **kw)
        original = values[0].run

        def slow(*args, **kwargs):
            out = original(*args, **kwargs)
            calls[0] += 1
            # Two calibration, one common-seed comparison, two teaching probes,
            # then three arms with four training and three evaluation trials.
            if calls[0] == 26:
                clock[0] = 21
            return out
        values[0].run = slow
        return values

    result = run_experiment(tmp_path, small_protocol(), circuit_factory=slow_factory)
    assert result['status'] == 'budget_stopped'
    assert calls[0] == 26
    assert result['jobs'][-1]['status'] == 'budget_stopped'
    assert 'metrics' not in result['jobs'][-1]


def test_each_teaching_compartment_must_respond_even_when_other_one_fires(tmp_path):
    install_source(tmp_path)

    def silent_factory(root, protocol, **kw):
        values = circuit(root, protocol, **kw)
        original = values[0].run

        def suppress_second(*args, **kwargs):
            kwargs['teaching_pulses'] = [p for p in kwargs.get('teaching_pulses', []) if p[1] != 1]
            return original(*args, **kwargs)
        values[0].run = suppress_second
        return values

    result = run_experiment(tmp_path, small_protocol(), circuit_factory=silent_factory)
    assert result['status'] == 'failed'
    assert result['reward']['activity_gate']['teaching_responsive'] == [True, False]
    assert all(not j.get('metrics') for j in result['jobs'])


def test_input_discrimination_uses_common_randomness_not_seed_variation(tmp_path):
    source = install_source(tmp_path)
    arrays, games = source_rows()
    arrays['X'][:] = 1
    np.savez(source / 'training-data.npz', **arrays)
    result = run_experiment(tmp_path, small_protocol(), circuit_factory=circuit)
    assert result['status'] == 'failed'
    assert result['reward']['activity_gate']['input_discrimination'] is False


@pytest.mark.parametrize('field,value', [('train_n', 0), ('tau_ms', -1), ('teaching_ms', 10000),
                                         ('duration_ms', float('nan')), ('wall_seconds', 0),
                                         ('global_weight_scale', 0), ('gain_bounds', [1.5, .5]),
                                         ('bin_ms', .3), ('learning_rate', float('inf')),
                                         ('plasticity_onset_ms', 310.), ('plasticity_onset_ms', 100.3),
                                         ('dan_baseline_window_ms', 150.), ('dan_baseline_window_ms', -1.),
                                         ('min_teaching_evoked_fraction', 0), ('min_teaching_evoked_fraction', 1.5),
                                         ('max_kc_code_overlap', 0), ('max_kc_code_overlap', 1.5),
                                         ('schema_version', 1), ('schema_version', 2),
                                         ('encoder', 'opponent-channels'), ('encoder_peak_hz', 0),
                                         ('encoder_peak_hz', 5000.), ('encoder_tuning_width', 0),
                                         ('encoder_min_kc_contacts', -1.), ('kc_input_gain', 0),
                                         ('kc_input_gain', float('nan')), ('kc_input_gain', 20.),
                                         ('sensory_input_gain', -1.), ('sensory_input_gain', 20.),
                                         ('apl_output_gain', -1.), ('apl_output_gain', 20.)])
def test_invalid_protocol_rejected_before_native_work(field, value):
    with pytest.raises(ValueError):
        validate_protocol(dict(default_protocol(), **{field: value}))


def test_default_protocol_declares_phasic_baseline_and_code_specificity_guards():
    protocol = validate_protocol(default_protocol())
    assert protocol['schema_version'] == 3
    assert protocol['encoder'] == 'glomerular-tuning-v1'
    assert protocol['encoder_peak_hz'] > 0 and protocol['encoder_tuning_width'] > 0
    assert protocol['encoder_min_kc_contacts'] >= 0 and protocol['kc_input_gain'] > 0
    assert protocol['sensory_input_gain'] == 0 and 0 <= protocol['apl_output_gain'] <= 1
    assert 0 < protocol['dan_baseline_window_ms'] <= protocol['plasticity_onset_ms'] < protocol['teaching_ms']
    assert 0 < protocol['min_teaching_evoked_fraction'] <= 1
    assert 0 < protocol['max_kc_code_overlap'] < 1
    assert validate_protocol(dict(default_protocol(), plasticity_onset_ms=0., dan_baseline_window_ms=0.))


def test_saturated_teaching_population_fails_the_evoked_margin_and_reports_tonic_rate(tmp_path):
    install_source(tmp_path)

    def saturated_factory(root, protocol, **kw):
        values = circuit(root, protocol, **kw)
        original = values[0].run

        def tonic_second_dan(*args, **kwargs):
            # Compartment 1 fires at its refractory ceiling all trial (a kick every 2.2 ms),
            # so the 30 ms teaching pulse only merges into the next scheduled spike.
            tonic = [(round(2.2 * k, 1), 1) for k in range(23)]
            kwargs['teaching_pulses'] = list(kwargs.get('teaching_pulses', [])) + tonic
            return original(*args, **kwargs)
        values[0].run = tonic_second_dan
        return values

    result = run_experiment(tmp_path, small_protocol(), circuit_factory=saturated_factory)
    gate = result['reward']['activity_gate']
    assert result['status'] == 'failed'
    assert gate['teaching_responsive'] == [True, False]
    assert gate['teaching_scheduled_spikes'] == [1, 1]
    assert gate['teaching_evoked_spikes'][0] == 1
    assert gate['teaching_evoked_spikes'][1] <= 0
    assert gate['tonic_dan_hz'][0] == 0
    assert gate['tonic_dan_hz'][1] == pytest.approx(1000 / 2.2, rel=.2)
    assert all(not j.get('metrics') for j in result['jobs'])


def test_shared_kc_code_across_games_fails_the_specificity_guard(tmp_path):
    install_source(tmp_path)
    result = run_experiment(tmp_path, dict(small_protocol(), max_kc_code_overlap=.5), circuit_factory=circuit)
    gate = result['reward']['activity_gate']
    assert result['status'] == 'failed'
    assert gate['kc_code_overlap'] == 1.0
    assert gate['teaching_responsive'] == [True, True]
    assert 'game-specific' in gate['message']
    assert all(not j.get('metrics') for j in result['jobs'])
