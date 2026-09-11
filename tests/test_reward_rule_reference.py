"""Independent reference calculation for the candidate dopamine rule (dan_reference='none').

The reference sums signed pairwise event kernels instead of re-implementing the native trace
recurrence, so it cannot share the kernel's indexing mistakes. Cases follow the Stage B list in
output/collaboration/reward-repair: silence, KC-only, DAN-only, KC-before-DAN, DAN-before-KC,
simultaneous events, stationary tonic activity, stimulus onset/offset, residual traces, warm-up,
trial termination and reset, repeated identical trials, and the legacy offset artifact.
"""
import numpy as np
import pytest

from bet36fly.reward_brain import RewardEngine

DT = 0.2


def engine(*, n_dan=1, tau_ms=10.0, eta=0.1, bounds=(0.5, 1.5), onset_ms=0.0, window_ms=0.0, reference='none'):
    n = n_dan + 2
    return RewardEngine(
        np.array([0, 1] + [1] * (n - 1), np.int64), np.array([n - 1], np.int32), np.array([1.0], np.float32),
        np.array([0], np.int32), np.array([0], np.int32), np.arange(1, 1 + n_dan, dtype=np.int32),
        np.zeros(n_dan, np.int32), np.array([0], np.int64), np.array([0], np.int32), np.array([0], np.int32),
        n_compartments=1, tau_ms=tau_ms, learning_rate=eta, gain_bounds=bounds,
        plasticity_onset_ms=onset_ms, dan_baseline_window_ms=window_ms, dan_reference=reference,
    )


def schedule(steps, kc_steps):
    out = np.zeros((steps, 1), np.float32)
    out[list(kc_steps), 0] = 5000
    return out


def pairwise_reference(kc_steps, dan_steps, *, n_dan, onset_step, tau_ms, eta):
    """1 + eta * sum over (DAN spike, KC spike) pairs of the signed exponential kernel, mean-normalized."""
    decay = np.exp(-DT / tau_ms)
    total = 0.0
    for tk in kc_steps:
        if tk < onset_step:
            continue
        for td in dan_steps:
            if td < onset_step or td == tk:
                continue
            total += (decay ** (tk - td) if td < tk else -decay ** (td - tk)) / n_dan
    return 1.0 + eta * total


def run(steps, kc_steps, dan_steps, **kwargs):
    """dan_steps: list of (step, local_dan_index); every listed DAN pulse must actually spike."""
    eng = engine(**kwargs)
    result = eng.run(schedule(steps, kc_steps), bin_ms=DT,
                     teaching_pulses=[(step * DT, dan) for step, dan in dan_steps], record=True)
    assert result['dan_counts'].sum() == len(dan_steps), 'a scheduled DAN pulse did not spike; case is invalid'
    return eng, result


MATRIX = {
    'silence': ([], []),
    'kc_only': ([3], []),
    'dan_only': ([], [(3, 0)]),
    'kc_before_dan': ([0], [(5, 0)]),
    'dan_before_kc': ([5], [(0, 0)]),
    'simultaneous': ([4], [(4, 0)]),
    'residual_trace_after_long_silence': ([1], [(2000, 0)]),
    'mixed_order_burst': ([2, 7, 9, 30, 31], [(4, 0), (20, 0), (33, 0)]),
}


@pytest.mark.parametrize('name', sorted(MATRIX))
@pytest.mark.parametrize('n_dan', [1, 2])
def test_candidate_matches_pairwise_reference(name, n_dan):
    kc_steps, dan_steps = MATRIX[name]
    dan_steps = [(step, dan) for step, _ in dan_steps for dan in range(n_dan)]
    _, result = run(2100, kc_steps, dan_steps, n_dan=n_dan)
    expected = pairwise_reference(kc_steps, [s for s, _ in dan_steps], n_dan=n_dan, onset_step=0, tau_ms=10.0, eta=0.1)

    assert result['gains'][0] == pytest.approx(expected, abs=3e-7)
    assert result['instrumentation']['signal_bins'][:, 0, 3].max() == 0          # no reference in candidate mode


def test_warm_up_events_before_onset_carry_no_eligibility():
    _, result = run(60, [2, 49], [(53, 0)], onset_ms=9.6, window_ms=4.8)
    expected = pairwise_reference([2, 49], [53], n_dan=1, onset_step=48, tau_ms=10.0, eta=0.1)

    assert result['gains'][0] == pytest.approx(expected, abs=3e-7)
    assert result['gains'][0] == pytest.approx(1 - 0.1 * np.exp(-4 * DT / 10), abs=3e-7)


def test_stationary_independent_activity_has_zero_mean_change():
    # Random KC and DAN trains at fixed rates; the pairwise kernel predicts each realization exactly and
    # the mean over realizations is zero within sampling error (potentiation and depression balance).
    rng = np.random.default_rng(7)
    steps, changes = 2400, []
    for _ in range(120):
        kc_steps = sorted(rng.choice(steps, size=24, replace=False).tolist())
        dan_steps = sorted(rng.choice(np.arange(0, steps, 12), size=40, replace=False).tolist())
        _, result = run(steps, kc_steps, [(s, 0) for s in dan_steps], tau_ms=100.0, eta=0.001)
        expected = pairwise_reference(kc_steps, dan_steps, n_dan=1, onset_step=0, tau_ms=100.0, eta=0.001)
        assert result['gains'][0] == pytest.approx(expected, abs=5e-6)
        changes.append(result['gains'][0] - 1)
    changes = np.array(changes)

    assert abs(changes.mean()) < 3 * changes.std(ddof=1) / np.sqrt(len(changes))
    assert changes.std() > 1e-4          # the rule is not silent; only its mean vanishes


def test_traces_reset_between_trials_and_repeated_trials_add_up():
    eng, first = run(20, [0], [(5, 0)])
    dan_only = eng.run(schedule(20, []), bin_ms=DT, teaching_pulses=[(1.0, 0)])
    again = eng.run(schedule(20, [0]), bin_ms=DT, teaching_pulses=[(1.0, 0)])

    assert dan_only['gains'][0] == first['gains'][0]                          # no carried KC eligibility
    assert again['gains'][0] - first['gains'][0] == pytest.approx(first['gains'][0] - 1, abs=3e-7)


def test_disabled_plasticity_records_zero_terms_and_leaves_gains():
    eng = engine()
    result = eng.run(schedule(20, [0]), bin_ms=DT, teaching_pulses=[(1.0, 0)], plasticity=False, record=True)

    assert result['gains'][0] == 1 and not result['instrumentation']['rule_bins'][:, :, :3].any()


def stimulus_then_silence(engine_kwargs):
    # KC spikes during a 300 ms "stimulus"; a DAN fires tonically every 4.8 ms during the stimulus and
    # stops at offset, as PPL101 does on the real circuit. Plasticity starts at 100 ms; the legacy rule
    # measures its reference over the 50 ms before onset.
    kc_steps = list(range(500, 1500, 25))
    dan_steps = [(int(round(k * 24)), 0) for k in range(1, 62) if k * 24 < 1500]
    return run(2000, kc_steps, dan_steps, tau_ms=500.0, eta=0.0005, onset_ms=100.0, **engine_kwargs)


def test_legacy_reference_potentiates_after_stimulus_offset_and_candidate_does_not():
    _, legacy = stimulus_then_silence(dict(window_ms=50.0, reference='tonic-baseline'))
    _, candidate = stimulus_then_silence(dict(window_ms=50.0, reference='none'))
    post = slice(1500, 2000)

    assert legacy['compartment_tonic_hz'][0] == pytest.approx(1000 / 4.8, rel=0.05)
    assert candidate['compartment_tonic_hz'][0] == legacy['compartment_tonic_hz'][0]     # measured, not subtracted
    assert legacy['instrumentation']['rule_bins'][post, 0, 2].sum() > 0.01               # the offset artifact
    assert abs(candidate['instrumentation']['rule_bins'][post, 0, 2].sum()) < 1e-9        # nothing fires after offset
    assert candidate['instrumentation']['signal_bins'][:, 0, 3].max() == 0
    assert legacy['instrumentation']['signal_bins'][post, 0, 2].sum() < 0                 # negative legacy signal


def test_reference_mode_is_validated_and_reported():
    with pytest.raises(ValueError):
        engine(reference='moving-average')
    assert engine().dan_reference == 'none'
    assert engine(reference='tonic-baseline', window_ms=0.0).dan_reference == 'tonic-baseline'
