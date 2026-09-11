import numpy as np
import pytest

from bet36fly.brain import LIFEngine
from bet36fly.reward_brain import RewardEngine


def reward_engine(*, n_dan=1, tau_ms=10.0, learning_rate=0.1, bounds=(0.5, 1.5), weight=1.0,
                  plasticity_onset_ms=0.0, dan_baseline_window_ms=0.0, dan_reference='tonic-baseline'):
    n = n_dan + 2
    return RewardEngine(
        np.array([0, 1] + [1] * (n - 1), np.int64),
        np.array([n - 1], np.int32),
        np.array([weight], np.float32),
        np.array([0], np.int32),
        np.array([0], np.int32),
        np.arange(1, 1 + n_dan, dtype=np.int32),
        np.zeros(n_dan, np.int32),
        np.array([0], np.int64),
        np.array([0], np.int32),
        np.array([0], np.int32),
        n_compartments=1,
        tau_ms=tau_ms,
        learning_rate=learning_rate,
        gain_bounds=bounds,
        plasticity_onset_ms=plasticity_onset_ms,
        dan_baseline_window_ms=dan_baseline_window_ms,
        dan_reference=dan_reference,
    )


def exact_schedule(steps, *kc_spike_steps):
    schedule = np.zeros((steps, 1), np.float32)
    schedule[list(kc_spike_steps), 0] = 5000
    return schedule


def test_disabled_reward_engine_matches_v1_for_constant_schedule():
    ptr = np.array([0, 1, 2, 2], np.int64)
    post = np.array([1, 2], np.int32)
    weights = np.array([160, 160], np.float32)
    sensory = np.array([0], np.int32)
    sample = np.arange(3, dtype=np.int32)
    expected = LIFEngine(ptr, post, weights, sensory).run(
        np.array([200], np.float32), duration_ms=20, seed=3, sample=sample, bin_ms=4
    )
    engine = RewardEngine(
        ptr,
        post,
        weights,
        sensory,
        np.array([], np.int32),
        np.array([], np.int32),
        np.array([], np.int32),
        np.array([], np.int64),
        np.array([], np.int32),
        np.array([], np.int32),
        n_compartments=1,
    )
    actual = engine.run(
        np.full((5, 1), 200, np.float32), bin_ms=4, seed=3, plasticity=False, sample=sample
    )

    for key in ('counts', 'voltage', 'trace', 'population'):
        np.testing.assert_array_equal(actual[key], expected[key])
    np.testing.assert_array_equal(actual['trace'].sum(axis=0), actual['counts'])
    assert actual['population'].sum() == actual['counts'].sum()


def test_hand_calculated_kc_then_dan_pulse_depresses_gain():
    engine = reward_engine()
    result = engine.run(exact_schedule(6, 0), bin_ms=0.2, teaching_pulses=[(1.0, 0)])

    assert result['dan_counts'].tolist() == [1]
    assert result['gains'][0] == pytest.approx(1 - 0.1 * np.exp(-0.1), abs=2e-7)
    np.testing.assert_array_equal(result['gain_delta'], result['gains'] - 1)


def test_dan_then_kc_has_opposite_sign_and_coincident_spikes_are_neutral():
    forward = reward_engine().run(
        exact_schedule(6, 5), bin_ms=0.2, teaching_pulses=[(0.0, 0)]
    )
    backward = reward_engine().run(
        exact_schedule(6, 0), bin_ms=0.2, teaching_pulses=[(1.0, 0)]
    )
    coincident = reward_engine().run(
        exact_schedule(1, 0), bin_ms=0.2, teaching_pulses=[(0.0, 0)]
    )

    assert forward['gains'][0] > 1
    assert backward['gains'][0] < 1
    assert coincident['gains'][0] == 1


def test_missing_kc_or_missing_dan_activity_cannot_change_gain():
    dan_only = reward_engine().run(
        exact_schedule(6), bin_ms=0.2, teaching_pulses=[(1.0, 0)]
    )
    kc_only = reward_engine().run(exact_schedule(6, 0), bin_ms=0.2)

    assert dan_only['gains'][0] == 1
    assert kc_only['gains'][0] == 1


def test_dan_population_is_mean_normalized():
    one = reward_engine(n_dan=1).run(
        exact_schedule(6, 5), bin_ms=0.2, teaching_pulses=[(0.0, 0)]
    )
    two = reward_engine(n_dan=2).run(
        exact_schedule(6, 5), bin_ms=0.2, teaching_pulses=[(0.0, 0), (0.0, 1)]
    )
    half = reward_engine(n_dan=2).run(
        exact_schedule(6, 5), bin_ms=0.2, teaching_pulses=[(0.0, 0)]
    )

    assert two['gains'][0] == pytest.approx(one['gains'][0], abs=2e-7)
    assert half['gains'][0] - 1 == pytest.approx((one['gains'][0] - 1) / 2, abs=2e-7)
    np.testing.assert_array_equal(two['compartment_dan_counts'], [2])


def test_traces_reset_but_gains_persist_and_frozen_probes_are_immutable():
    engine = reward_engine()
    learned = engine.run(exact_schedule(6, 5), bin_ms=0.2, teaching_pulses=[(0.0, 0)])
    saved = learned['gains'].copy()
    no_reward = engine.run(exact_schedule(6, 0), bin_ms=0.2)
    probe = engine.run(
        exact_schedule(6, 0), bin_ms=0.2, teaching_pulses=[(1.0, 0)], plasticity=False
    )

    np.testing.assert_array_equal(no_reward['gains'], saved)
    np.testing.assert_array_equal(probe['gains'], saved)
    np.testing.assert_array_equal(engine.gains, saved)
    assert not np.shares_memory(learned['gains'], engine.gains)


def test_gain_changes_affect_sparse_propagation_during_and_after_learning():
    frozen = reward_engine(learning_rate=1, weight=800).run(
        exact_schedule(10, 0), bin_ms=0.2, teaching_pulses=[(1.0, 0)], plasticity=False
    )
    engine = reward_engine(learning_rate=1, weight=800)
    learning = engine.run(
        exact_schedule(10, 0), bin_ms=0.2, teaching_pulses=[(1.0, 0)]
    )
    later = engine.run(exact_schedule(10, 0), bin_ms=0.2, plasticity=False)

    assert learning['gains'][0] == 0.5
    assert frozen['counts'][-1] == 1
    assert learning['counts'][-1] == 0
    assert later['counts'][-1] == 0


def test_updates_are_bounded_local_and_do_not_mutate_graph_arrays():
    ptr = np.array([0, 2, 2, 2, 2], np.int64)
    post = np.array([2, 3], np.int32)
    weights = np.array([1, -2], np.float32)
    engine = RewardEngine(
        ptr, post, weights, np.array([0]), np.array([0]), np.array([1]), np.array([0]),
        np.array([0, 1]), np.array([0, 0]), np.array([0, 1]), n_compartments=2,
        tau_ms=10, learning_rate=10, gain_bounds=(0.75, 1.25), gains=np.array([1.1, 0.9]),
    )
    result = engine.run(exact_schedule(6, 5), bin_ms=0.2, teaching_pulses=[(0.0, 0)])

    np.testing.assert_array_equal(ptr, [0, 2, 2, 2, 2])
    np.testing.assert_array_equal(post, [2, 3])
    np.testing.assert_array_equal(weights, [1, -2])
    np.testing.assert_array_equal(engine.weights, [1, -2])
    np.testing.assert_allclose(result['gains'], [1.25, 0.9], atol=1e-7)


def test_scheduled_counts_and_sampled_bins_are_exact_without_all_neuron_trace():
    engine = reward_engine()
    result = engine.run(exact_schedule(4, 0, 2, 3), bin_ms=0.2, sample=np.array([0, 1]))

    np.testing.assert_array_equal(result['counts'][:2], [3, 0])
    np.testing.assert_array_equal(result['trace'][:, 0], [1, 0, 1, 1])
    np.testing.assert_array_equal(result['trace'].sum(axis=0), result['counts'][[0, 1]])
    assert result['trace'].shape == (4, 2)
    assert 'spike_bins' not in result


def test_teaching_pulses_report_actual_spikes_and_respect_dan_refractory():
    result = reward_engine().run(
        exact_schedule(10), bin_ms=0.2, teaching_pulses=[(0.0, 0), (1.0, 0)]
    )

    np.testing.assert_array_equal(result['pulse_times_ms'], [0, 1])
    np.testing.assert_array_equal(result['pulse_dan_indices'], [0, 0])
    np.testing.assert_array_equal(result['dan_counts'], [1])


@pytest.mark.parametrize(
    'mutation',
    [
        {'plastic_edge_indices': np.array([0.5])},
        {'post': np.array([2**32], np.uint64)},
        {'plastic_edge_indices': np.array([1])},
        {'plastic_kc_indices': np.array([1])},
        {'kc_indices': np.array([1])},
        {'plastic_compartments': np.array([1])},
        {'dan_compartments': np.array([1])},
        {'dan_indices': np.array([0])},
        {'gain_bounds': (0, 1)},
        {'tau_ms': 0},
        {'learning_rate': 0},
        {'learning_rate': -1},
        {'learning_rate': 1e100},
        {'gains': np.array([1.6])},
    ],
)
def test_constructor_rejects_invalid_indices_shapes_and_config(mutation):
    args = dict(
        ptr=np.array([0, 1, 1, 1]), post=np.array([2]), weights=np.array([1.0]),
        sensory=np.array([0]), kc_indices=np.array([0]), dan_indices=np.array([1]),
        dan_compartments=np.array([0]), plastic_edge_indices=np.array([0]),
        plastic_kc_indices=np.array([0]), plastic_compartments=np.array([0]),
        n_compartments=1,
    )
    args.update(mutation)
    with pytest.raises(ValueError):
        RewardEngine(**args)


@pytest.mark.parametrize(
    ('schedule', 'kwargs'),
    [
        (np.zeros(1), {}),
        (np.zeros((1, 2)), {}),
        (np.array([[np.nan]]), {}),
        (np.array([[-1.0]]), {}),
        (np.array([[5000.1]]), {}),
        (np.zeros((1, 1)), {'dt': 0.1}),
        (np.zeros((1, 1)), {'bin_ms': 0.3}),
        (np.zeros((1, 1)), {'teaching_pulses': [(0.1, 0)]}),
        (np.zeros((1, 1)), {'teaching_pulses': [(0.0, 1)]}),
        (np.zeros((1, 1)), {'sample': np.array([0.5])}),
        (np.zeros((1, 1)), {'sample': np.array([2**32], np.uint64)}),
        (np.zeros((1, 1)), {'seed': 1.5}),
        (np.zeros((1, 1)), {'seed': -1}),
        (np.zeros((1, 1)), {'plasticity': 1}),
        (np.zeros((50_001, 1)), {}),
    ],
)
def test_run_rejects_malformed_or_unsafe_schedules(schedule, kwargs):
    with pytest.raises(ValueError):
        reward_engine().run(schedule, **kwargs)


def test_external_gain_restore_is_validated_before_native_execution():
    engine = reward_engine()
    engine.gains[:] = np.nan
    with pytest.raises(ValueError):
        engine.run(exact_schedule(1), bin_ms=0.2)


@pytest.mark.parametrize(
    'replacement',
    [np.array([1.0], np.float64), np.array([0.4], np.float32), np.ones(2, np.float32)],
)
def test_replacing_gain_storage_with_an_invalid_checkpoint_is_rejected(replacement):
    engine = reward_engine()
    engine.gains = replacement
    with pytest.raises(ValueError):
        engine.run(exact_schedule(1), bin_ms=0.2)


def test_graph_inputs_are_snapshotted_read_only_while_gains_remain_writable():
    ptr = np.array([0, 1, 1, 1], np.int64)
    post = np.array([2], np.int32)
    weights = np.array([1.0], np.float32)
    engine = RewardEngine(
        ptr, post, weights, np.array([0]), np.array([0]), np.array([1]), np.array([0]),
        np.array([0]), np.array([0]), np.array([0]), n_compartments=1,
    )
    ptr[-1] = 0
    post[0] = 1
    weights[0] = 9

    np.testing.assert_array_equal(engine.ptr, [0, 1, 1, 1])
    np.testing.assert_array_equal(engine.post, [2])
    np.testing.assert_array_equal(engine.weights, [1])
    with pytest.raises(ValueError):
        engine.weights[0] = 2
    engine.gains[:] = 1.25
    np.testing.assert_array_equal(engine.gains, [1.25])


def tonic_train(periods, period_ms=4.8):
    # 4.8 ms spacing is well outside the 2.2 ms refractory period, so every pulse spikes.
    return [(period_ms * k, 0) for k in range(periods)]


def slow_engine(**kwargs):
    # Trace time constant far above the tonic period, as in the sports protocol (500 ms vs ~2.5 ms).
    return reward_engine(tau_ms=100.0, learning_rate=0.001, **kwargs)


def test_tonic_dan_firing_alone_does_not_move_gains_after_baseline_subtraction():
    # A KC burst late in the trial: the raw rule potentiates it immediately from the tonic
    # dopamine trace, and the compensating depression is cut off by the trial end.
    burst = range(2300, 2324)
    raw = slow_engine().run(exact_schedule(2400, *burst), bin_ms=0.2, teaching_pulses=tonic_train(100))
    phasic = slow_engine(plasticity_onset_ms=9.6, dan_baseline_window_ms=4.8).run(
        exact_schedule(2400, *burst), bin_ms=0.2, teaching_pulses=tonic_train(100)
    )

    assert raw['dan_counts'].tolist() == [100]
    assert phasic['dan_counts'].tolist() == [100]
    assert raw['gains'][0] - 1 > 0.3
    assert phasic['gains'][0] == pytest.approx(1, abs=0.02)
    assert phasic['compartment_tonic_hz'].tolist() == pytest.approx([1000 / 4.8])
    assert raw['compartment_tonic_hz'].tolist() == [0]


def test_phasic_dan_pulse_above_tonic_baseline_still_depresses_eligible_kc_edges():
    # Same tonic train plus one extra pulse 3.2 ms after the burst, halfway between tonic pulses.
    burst = range(2300, 2324)
    tonic = tonic_train(100)
    without = slow_engine(plasticity_onset_ms=9.6, dan_baseline_window_ms=4.8).run(
        exact_schedule(2400, *burst), bin_ms=0.2, teaching_pulses=tonic
    )
    with_pulse = slow_engine(plasticity_onset_ms=9.6, dan_baseline_window_ms=4.8).run(
        exact_schedule(2400, *burst), bin_ms=0.2, teaching_pulses=tonic + [(4.8 * 97.5, 0)]
    )

    assert without['dan_counts'].tolist() == [100]
    assert with_pulse['dan_counts'].tolist() == [101]
    assert with_pulse['gains'][0] < without['gains'][0] - 0.01


def test_kc_spikes_before_plasticity_onset_carry_no_eligibility():
    engine = reward_engine(plasticity_onset_ms=9.6, dan_baseline_window_ms=4.8)
    early = engine.run(exact_schedule(60, 2), bin_ms=0.2, teaching_pulses=[(10.6, 0)])
    late = reward_engine(plasticity_onset_ms=9.6, dan_baseline_window_ms=4.8).run(
        exact_schedule(60, 49), bin_ms=0.2, teaching_pulses=[(10.6, 0)]
    )

    assert early['gains'][0] == 1
    assert late['gains'][0] == pytest.approx(1 - 0.1 * np.exp(-4 * 0.2 / 10), abs=2e-7)


@pytest.mark.parametrize('kwargs', [
    {'plasticity_onset_ms': -1},
    {'plasticity_onset_ms': 1, 'dan_baseline_window_ms': 2},
    {'dan_baseline_window_ms': -0.2},
    {'plasticity_onset_ms': 0.3},
    {'plasticity_onset_ms': float('nan')},
])
def test_constructor_rejects_invalid_onset_and_baseline_window(kwargs):
    with pytest.raises(ValueError):
        reward_engine(**kwargs)


def test_run_rejects_plasticity_onset_at_or_after_trial_end():
    engine = reward_engine(plasticity_onset_ms=1.2, dan_baseline_window_ms=0.4)
    with pytest.raises(ValueError):
        engine.run(exact_schedule(6), bin_ms=0.2)
    assert engine.run(exact_schedule(7), bin_ms=0.2)['compartment_tonic_hz'].tolist() == [0]


# --- Stage A instrumentation: recording-only buffers must not alter dynamics ---

RECORD_KEYS = ('counts', 'voltage', 'trace', 'population', 'dan_counts', 'compartment_dan_counts',
               'compartment_tonic_hz', 'gains', 'gain_delta')


@pytest.mark.parametrize('plasticity', [True, False])
def test_recording_does_not_change_dynamics_or_gains(plasticity):
    burst = range(2300, 2324)
    kwargs = dict(bin_ms=0.2, teaching_pulses=tonic_train(100), plasticity=plasticity, sample=np.array([0, 1]))
    plain = slow_engine(plasticity_onset_ms=9.6, dan_baseline_window_ms=4.8).run(
        exact_schedule(2400, *burst), **kwargs
    )
    recorded = slow_engine(plasticity_onset_ms=9.6, dan_baseline_window_ms=4.8).run(
        exact_schedule(2400, *burst), record=True, **kwargs
    )

    for key in RECORD_KEYS:
        np.testing.assert_array_equal(recorded[key], plain[key], err_msg=key)
    assert plain['instrumentation'] is None
    rec = recorded['instrumentation']
    assert rec['signal_bins'].shape == (2400, 1, 4)
    assert rec['kc_signal_bins'].shape == (2400, 2)
    assert rec['rule_bins'].shape == (2400, 1, 7)
    assert rec['kc_trace_bins'].shape == (2400, 1)
    assert np.isfinite(rec['rule_bins']).all() and np.isfinite(rec['signal_bins']).all()
    assert rec['rule_bins'][:, 0, 2].sum() == pytest.approx(float(recorded['gain_delta'][0]), abs=1e-6)
    assert rec['kc_signal_bins'][:, 0].sum() == recorded['counts'][0]
    assert rec['signal_bins'][:, 0, 0].sum() == recorded['dan_counts'][0]
    if not plasticity:
        assert not rec['rule_bins'][:, :, :3].any()


def test_recorded_rule_terms_match_hand_calculation():
    engine = reward_engine()
    result = engine.run(exact_schedule(6, 0), bin_ms=0.2, teaching_pulses=[(1.0, 0)], record=True)
    rec = result['instrumentation']
    decay = np.exp(-5 * 0.2 / 10)

    # KC spike at step 0, DAN spike at step 5 (one bin per step).
    np.testing.assert_array_equal(rec['kc_signal_bins'][:, 0], [1, 0, 0, 0, 0, 0])
    np.testing.assert_array_equal(rec['signal_bins'][:, 0, 0], [0, 0, 0, 0, 0, 1])
    assert rec['kc_trace_bins'][0, 0] == pytest.approx(1.0)
    assert rec['kc_trace_bins'][5, 0] == pytest.approx(decay, abs=1e-6)
    assert rec['kc_signal_bins'][5, 1] == pytest.approx(decay, abs=1e-6)
    assert rec['signal_bins'][5, 0, 1] == pytest.approx(1.0)          # Dbar after the DAN spike
    assert rec['signal_bins'][5, 0, 3] == 0                           # no reference without a baseline window
    assert rec['rule_bins'][5, 0, 0] == 0                             # Dbar*K term: no KC spike at step 5
    assert rec['rule_bins'][5, 0, 1] == pytest.approx(-0.1 * decay, abs=1e-6)   # -Kbar*D term
    assert rec['rule_bins'][5, 0, 2] == pytest.approx(float(result['gain_delta'][0]), abs=1e-7)
    np.testing.assert_array_equal(rec['rule_bins'][:, 0, 3:5], 0)     # nothing clipped
    np.testing.assert_array_equal(rec['rule_bins'][:, 0, 5], [1, 0, 0, 0, 0, 0])   # KC events on edges
    assert rec['rule_bins'][:5, 0, :3].sum() == 0
    np.testing.assert_array_equal(rec['plastic_groups'], [0])


def test_recorded_groups_split_edges_and_count_clipping():
    ptr = np.array([0, 2, 2, 2, 2], np.int64)
    post = np.array([2, 3], np.int32)
    engine = RewardEngine(
        ptr, post, np.array([1, -2], np.float32), np.array([0]), np.array([0]), np.array([1]), np.array([0]),
        np.array([0, 1]), np.array([0, 0]), np.array([0, 1]), n_compartments=2,
        tau_ms=10, learning_rate=10, gain_bounds=(0.75, 1.25), gains=np.array([1.1, 0.9]),
    )
    result = engine.run(exact_schedule(6, 5), bin_ms=0.2, teaching_pulses=[(0.0, 0)], record=True,
                        plastic_groups=np.array([3, 1], np.int32))
    rec = result['instrumentation']
    attempted = 10 * np.exp(-5 * 0.2 / 10)

    assert rec['rule_bins'].shape == (6, 4, 7)
    assert rec['rule_bins'][5, 3, 0] == pytest.approx(attempted, abs=1e-5)
    assert rec['rule_bins'][5, 3, 2] == pytest.approx(1.25 - 1.1, abs=1e-6)
    assert rec['rule_bins'][5, 3, 4] == 1 and rec['rule_bins'][5, 3, 3] == 0
    assert rec['rule_bins'][5, 3, 6] == pytest.approx(1.0)   # Kbar mass at bin end includes this step's KC spike
    assert rec['rule_bins'][5, 1, 6] == pytest.approx(1.0)   # edge 1 shares the KC but sits in group 1
    assert not rec['rule_bins'][:, [0, 2], :].any()
    assert rec['rule_bins'][5, 1, 5] == 1                     # the shared KC's spike is an event on edge 1 too
    assert not rec['rule_bins'][:, 1, :5].any()               # but no rule term reaches the DAN-less compartment
    np.testing.assert_allclose(result['gains'], [1.25, 0.9], atol=1e-7)


@pytest.mark.parametrize('groups', [np.array([0, 0]), np.array([-1]), np.array([0.5]), np.array([2**40])])
def test_record_rejects_misaligned_groups(groups):
    with pytest.raises(ValueError):
        reward_engine().run(exact_schedule(1), bin_ms=0.2, record=True, plastic_groups=groups)


def test_record_accepts_an_explicit_group_count_and_rejects_a_short_one():
    wide = reward_engine().run(exact_schedule(2, 0), bin_ms=0.2, record=True,
                               plastic_groups=np.array([1], np.int32), n_groups=3)
    assert wide['instrumentation']['rule_bins'].shape == (2, 3, 7)
    assert wide['instrumentation']['rule_bins'][0, 1, 5] == 1 and not wide['instrumentation']['rule_bins'][:, [0, 2], :].any()
    with pytest.raises(ValueError):
        reward_engine().run(exact_schedule(1), bin_ms=0.2, record=True, plastic_groups=np.array([1], np.int32), n_groups=1)


# --- per-step population event recording (SCI-001 follow-up) ---

def test_recording_includes_per_step_population_events_and_eligibility():
    # KC spikes at steps 0 and 3; one of two DANs fires at step 1. Trace columns hold the values the
    # update USED at that step (after the step-start decay, before the step's own increments).
    result = reward_engine(n_dan=2).run(exact_schedule(6, 0, 3), bin_ms=0.2, teaching_pulses=[(0.2, 0)], record=True)
    rec = result['instrumentation']
    steps, rule = rec['step_signals'], rec['step_rule']
    decay = np.exp(-0.2 / 10)

    assert steps.shape == (6, 3)                                   # KC spikes, D per compartment, Dbar used
    np.testing.assert_array_equal(steps[:, 0], [1, 0, 0, 1, 0, 0])
    np.testing.assert_array_equal(steps[:, 1], [0, 0.5, 0, 0, 0, 0])  # one of two DANs fired: compartment mean
    np.testing.assert_allclose(steps[:, 2], [0, 0, 0.5 * decay, 0.5 * decay ** 2, 0.5 * decay ** 3, 0.5 * decay ** 4], rtol=1e-5)
    assert rule.shape == (6, 1, 2)                                 # per group: KC impulses on eligible edges, Kbar mass used
    np.testing.assert_array_equal(rule[:, 0, 0], [1, 0, 0, 1, 0, 0])
    mass = [0, decay, decay ** 2, decay ** 3, (decay ** 3 + 1) * decay, (decay ** 3 + 1) * decay ** 2]
    np.testing.assert_allclose(rule[:, 0, 1], mass, rtol=1e-5)
    assert result['gains'][0] == pytest.approx(1 + 0.1 * 0.5 * decay ** 2 - 0.1 * 0.5 * decay, abs=1e-6)


def test_per_step_series_reconstruct_the_applied_change_exactly():
    # Sum over the eligible edges of a group: eta * (Dbar_used(t) * impulses(t) - mass_used(t) * D(t)).
    engine = reward_engine(tau_ms=10.0, learning_rate=0.01)
    result = engine.run(exact_schedule(60, 2, 7, 9, 30, 31, 45), bin_ms=0.2,
                        teaching_pulses=[(0.8, 0), (4.0, 0), (6.6, 0), (9.2, 0)], record=True)
    rec = result['instrumentation']
    steps, rule = rec['step_signals'], rec['step_rule']
    reconstructed = 0.01 * (steps[:, 2] * rule[:, 0, 0] - rule[:, 0, 1] * steps[:, 1]).sum()

    assert result['dan_counts'][0] == 4
    assert reconstructed == pytest.approx(float(result['gain_delta'][0]), abs=1e-6)
    assert reconstructed == pytest.approx(rec['rule_bins'][:, 0, 2].sum(), abs=1e-6)
    assert reconstructed != 0


# --- Stage C: plasticity mask; excluded edges transmit normally but never update ---

def masked_engine(mask, **kwargs):
    # KC 0 -> neurons 2 and 3 through two strong edges; DAN 1 teaches compartment 0 for both edges.
    return RewardEngine(
        np.array([0, 2, 2, 2, 2], np.int64), np.array([2, 3], np.int32), np.array([800.0, 800.0], np.float32),
        np.array([0]), np.array([0]), np.array([1]), np.array([0]), np.array([0, 1]), np.array([0, 0]), np.array([0, 0]),
        n_compartments=1, tau_ms=10, learning_rate=1.0, gain_bounds=(0.5, 1.5), plastic_mask=mask, **kwargs,
    )


def test_masked_edge_keeps_transmitting_and_never_updates():
    engine = masked_engine(np.array([1, 0], np.uint8))
    learned = engine.run(exact_schedule(10, 0), bin_ms=0.2, teaching_pulses=[(1.0, 0)], record=True,
                         plastic_groups=np.array([0, 1], np.int32))
    later = engine.run(exact_schedule(10, 0), bin_ms=0.2, plasticity=False)

    np.testing.assert_allclose(learned['gains'], [0.5, 1.0], atol=1e-7)     # masked edge untouched
    assert learned['counts'][3] == 1 and learned['counts'][2] == 0          # masked edge drives its target at full strength;
    assert later['counts'][3] == 1 and later['counts'][2] == 0             # the depressed sibling (0.5 before delivery) does not
    assert not learned['instrumentation']['rule_bins'][:, 1, :5].any()    # no rule terms recorded on the masked edge
    assert learned['instrumentation']['rule_bins'][:, 1, 5].sum() == 1     # its KC event is still counted
    assert not learned['instrumentation']['step_rule'][:, 1, :].any()     # but it carries no eligible impulse or mass
    np.testing.assert_array_equal(engine.plastic_mask, [1, 0])


def test_mask_defaults_to_all_eligible_and_is_validated():
    assert masked_engine(None).plastic_mask.tolist() == [1, 1]
    for bad in (np.array([1]), np.array([1, 2]), np.array([1.0, 0.5]), np.array([[1, 0]])):
        with pytest.raises(ValueError):
            masked_engine(bad)
