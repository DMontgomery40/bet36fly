"""Independent spike-pair and continuous-integral oracles for the named bridge."""
import numpy as np
import pytest

from bet36fly import reward_brain


ETA, TE, TR = .0005, 500., 100.
LAGS = [0, .2, 1, 5, 20, 50, 100, 500, 1000]


def engine(n_dan=1, weight=1., **kwargs):
    n = n_dan + 2
    return reward_brain.RewardEngine(
        np.array([0, 1] + [1] * (n - 1)), np.array([n - 1]), np.array([weight], np.float32),
        np.array([0]), np.array([0]), np.arange(1, 1 + n_dan), np.zeros(n_dan, int),
        np.array([0]), np.array([0]), np.array([0]), n_compartments=1,
        tau_ms=TE, learning_rate=kwargs.pop('learning_rate', ETA), dan_reference='none', learning_rule='rate-bridge-v1',
        rate_tau_ms=TR, **kwargs)


def pair_sum(kc_times, dan_times, amplitudes=None):
    amplitudes = np.ones(len(dan_times)) if amplitudes is None else amplitudes
    return sum(-ETA * a * np.sign(d - k) * (np.exp(-abs(d-k)/TE) - np.exp(-abs(d-k)/TR))
               for k in kc_times for d, a in zip(dan_times, amplitudes))


def run_events(kc_times, dan_times, *, n_dan=1, active=None, end=None, onset=0, record=True):
    active = n_dan if active is None else active
    end = max([0, *kc_times, *dan_times]) + .2 if end is None else end
    rates = np.zeros((round(end/.2), 1), np.float32)
    rates[np.rint(np.asarray(kc_times)/.2).astype(int), 0] = 5000
    obj = engine(n_dan, plasticity_onset_ms=onset)
    result = obj.run(rates, bin_ms=.2, teaching_pulses=[(d, i) for d in dan_times for i in range(active)],
                     sample=np.arange(n_dan + 1), record=record)
    return obj, result


def totals(result):
    rec = result['instrumentation']
    return rec['bridge_rule'].sum(axis=(0, 1)) + rec['bridge_tail'].sum(axis=0)


@pytest.mark.parametrize('n_dan,active', [(1, 1), (2, 2), (22, 22), (22, 1)])
@pytest.mark.parametrize('lag', sorted({x*s for x in LAGS for s in (-1, 1)}))
def test_native_bridge_signed_pairs_have_analytic_magnitude_and_population_mean(lag, n_dan, active):
    k, d = max(0, -lag), max(0, lag)
    _, result = run_events([k], [d], n_dan=n_dan, active=active)
    expected = pair_sum([k], [d], [active/n_dan])
    observed = totals(result)
    assert observed[2] == pytest.approx(expected, abs=1e-11)
    assert observed[3] == pytest.approx(expected, abs=1e-11)
    assert result['gains'][0] == pytest.approx(np.float32(1 + expected), abs=np.spacing(np.float32(1)), rel=0)
    assert observed[4] == float(result['gains'][0]) - 1
    assert result['trace'][:, 0].nonzero()[0].tolist() == [round(k/.2)]
    assert result['dan_counts'].tolist() == [1]*active + [0]*(n_dan-active)
    if abs(lag) in (50, 500):
        floor = .25 if abs(lag) == 50 else .95
        assert abs(float(result['gains'][0])-1) >= floor*ETA*np.exp(-abs(lag)/TE)*active/n_dan


@pytest.mark.parametrize('kc,dan', [([], []), ([0, 20], []), ([], [5, 25]),
                                  ([0, 5, 15], [0, 10, 30]), ([2, 4, 80], [20, 40, 60])])
@pytest.mark.parametrize('end', [100, 600, 1200])
def test_native_arbitrary_histories_and_silent_extension_include_complete_tail(kc, dan, end):
    _, result = run_events(kc, dan, end=end)
    t = totals(result)
    assert t[2] == pytest.approx(pair_sum(kc, dan), abs=1e-11)
    assert t[0] + t[1] == pytest.approx(t[2], abs=1e-11)
    rec = result['instrumentation']
    a = -np.expm1(-(.01+.002)*.2)/(.01+.002)
    np.testing.assert_allclose(rec['bridge_rule'][..., 2], ETA*.96*a*rec['bridge_rule'][..., 7], atol=1e-14)
    np.testing.assert_allclose(rec['bridge_tail'][..., 2], ETA*.96/(.01+.002)*rec['bridge_tail'][..., 7], atol=1e-14)
    assert abs(t[4]-t[3]) <= np.spacing(result['gains'][0]) + 1e-11


@pytest.mark.parametrize('offset', [0, 50, 100])
def test_bridge_onset_excludes_earlier_history_and_shift_is_invariant(offset):
    _, result = run_events([offset, offset+10, offset+20], [offset+5, offset+30],
                           onset=offset+10, end=offset+50)
    assert totals(result)[2] == pytest.approx(pair_sum([10, 20], [30]), abs=1e-11)
    rec = result['instrumentation']
    assert not rec['bridge_signals'][:round((offset+10)/.2)].any()


def test_bridge_accumulates_sub_ulp_intervals_and_never_leaks_tail_into_electrical_bins():
    _, result = run_events([0], [5], end=6)
    rec = result['instrumentation']
    assert abs(rec['bridge_rule'][..., 2]).max() < np.spacing(np.float32(1)) / 2
    assert abs(totals(result)[4]) > 10*np.spacing(np.float32(1))
    assert abs(rec['bridge_tail'][..., 2].sum()) > abs(rec['bridge_rule'][..., 2].sum())
    assert result['duration_ms'] == 6 and result['trace'].shape[0] == 30


@pytest.mark.parametrize('record', [False, True])
def test_bridge_frozen_checkpoint_reset_and_record_parity(record):
    obj, first = run_events([0, 10], [20], end=40)
    checkpoint = first['gains'].copy()
    rates = np.zeros((200, 1), np.float32)
    rates[0, 0] = 5000
    result = obj.run(rates, bin_ms=.2, teaching_pulses=[(20, 0)], plasticity=False, record=record)
    np.testing.assert_array_equal(obj.gains, checkpoint)
    np.testing.assert_array_equal(result['gains'], checkpoint)
    if record:
        np.testing.assert_array_equal(totals(result)[:5], 0)
    empty = obj.run(np.zeros((200, 1)), bin_ms=.2, record=record)
    np.testing.assert_array_equal(empty['gains'], checkpoint)
    _, plain = run_events([0, 10], [20], end=40, record=False)
    for key in ('gains', 'voltage', 'trace', 'counts', 'dan_counts', 'population'):
        np.testing.assert_array_equal(first[key], plain[key])


@pytest.mark.parametrize('config', [dict(rate_tau_ms=0), dict(rate_tau_ms=500), dict(rate_tau_ms=np.nan),
                                  dict(rate_tau_ms=np.inf), dict(learning_rule='bad'),
                                  dict(learning_rule='rate-bridge-v1', dan_reference='tonic-baseline')])
def test_bridge_rejects_invalid_configuration_before_native(config, monkeypatch):
    monkeypatch.setattr(reward_brain, '_native_library', lambda: pytest.fail('invalid configuration reached native'))
    values = dict(learning_rule='rate-bridge-v1', rate_tau_ms=100, dan_reference='none') | config
    with pytest.raises(ValueError):
        reward_brain.RewardEngine(np.array([0, 1, 1, 1]), np.array([2]), np.array([1.]),
            np.array([0]), np.array([0]), np.array([1]), np.array([0]), np.array([0]),
            np.array([0]), np.array([0]), n_compartments=1, **values)


def replay(kc, dan, *, dt=.2, end=100, **kwargs):
    k = np.zeros((round(end/dt), 1))
    d = np.zeros_like(k)
    k[np.rint(np.asarray(kc)/dt).astype(int), 0] = 1
    d[np.rint(np.asarray(dan)/dt).astype(int), 0] = 1
    return reward_brain._bridge_signal_replay(k, d, dt=dt, **kwargs)


@pytest.mark.parametrize('dt', [.1, .2, .4])
@pytest.mark.parametrize('kc,dan', [([0], [20]), ([20], [0]), ([0, 10, 40], [0, 20, 80])])
def test_shared_native_integrator_grids_match_independent_pair_sum(dt, kc, dan):
    result = replay(kc, dan, dt=dt)
    total = result['bridge_rule'].sum((0, 1))+result['bridge_tail'].sum(0)
    assert total[2] == pytest.approx(pair_sum(kc, dan), abs=1e-11)
    assert total[3] == pytest.approx(total[2], abs=1e-11)


def continuous_terms(times, events):
    # Closed impulse responses, evaluated directly at arbitrary continuous times.
    ages = times[:, None] - np.asarray(events)[None, :]
    present = ages >= 0
    ages = np.maximum(ages, 0)
    rate = (np.exp(-ages/TR)/TR*present).sum(1)
    eligibility = ((np.exp(-ages/TE)-np.exp(-ages/TR))/(1-TR/TE)*present).sum(1)
    return rate, eligibility


def dense_clipped_oracle(kc, dan, *, initial, eta, low=.5, high=1.5, h=.01, end=100):
    # Independent midpoint quadrature of CLOSED impulse responses; no native recurrence.
    times = np.arange(h/2, end, h)
    rk, ek = continuous_terms(times, kc)
    rd, ed = continuous_terms(times, dan)
    positive, negative = eta*.96*ed*rk, -eta*.96*ek*rd
    gain = initial
    for delta in h*(positive+negative):
        gain = min(high, max(low, gain+delta))
    # Independent quadrature of the tail over transformed finite u in [0,1],
    # using Q(end+s)=Q(end)*exp(-b*s); integration is exact at constant sign.
    rk, ek = continuous_terms(np.array([end]), kc)
    rd, ed = continuous_terms(np.array([end]), dan)
    gain = min(high, max(low, gain+float((eta*.96*(ed*rk-ek*rd)/(.01+.002))[0])))
    return gain, positive.sum()*h, negative.sum()*h


@pytest.mark.parametrize('kc,dan', [([0, 1, 2, 90], [20, 30, 40]), ([20, 30, 40], [0, 1, 2, 90])])
@pytest.mark.parametrize('initial', [.5, 1., 1.5])
def test_clipped_recovery_and_separate_true_integrals_match_dense_continuous_oracle(kc, dan, initial):
    result = replay(kc, dan, gains=[initial], learning_rate=2.)
    expected, positive, negative = dense_clipped_oracle(kc, dan, initial=initial, eta=2.)
    assert result['gains'][0] == pytest.approx(expected, abs=3e-7, rel=0)
    finite = result['bridge_rule'].sum((0, 1))
    assert finite[0] == pytest.approx(positive, abs=2e-8)
    assert finite[1] == pytest.approx(negative, abs=2e-8)
    total = finite+result['bridge_tail'].sum(0)
    assert total[4] == float(result['gains'][0])-initial
    assert total[5:7].sum() > 0


@pytest.mark.parametrize('upper', [False, True])
def test_tail_published_only_boundary_is_observed_even_when_double_remains_inside(upper):
    bound = np.float32(1.5 if upper else .5)
    initial = np.nextafter(bound, np.float32(1))
    gap = abs(float(bound)-float(initial))
    expected_unit = abs(pair_sum([0], [5]))
    amplitude = .75*gap/expected_unit
    k = np.zeros((26, 1))
    d = k.copy()
    k[25 if upper else 0] = 1
    d[0 if upper else 25] = amplitude
    result = reward_brain._bridge_signal_replay(k, d, gains=[initial])
    tail = result['bridge_tail'][0]
    total = result['bridge_rule'].sum((0, 1))+tail
    assert abs(total[3]) < gap
    assert result['gains'][0] == bound
    assert tail[6 if upper else 5] == 1
    assert result['bridge_rule'][..., 5:7].sum() == 0


@pytest.mark.parametrize('gain', [.5, 1.5])
def test_frozen_dwelling_finite_and_tail_counts_are_separate(gain):
    result = replay([0], [5], end=10, gains=[gain], learning_rate=0)
    col = 5 if gain == .5 else 6
    assert result['bridge_rule'][..., col].sum() == 50
    assert result['bridge_tail'][0, col] == 1
    assert not result['bridge_rule'][..., :5].any()
    assert not result['bridge_tail'][..., :5].any()


@pytest.mark.parametrize('mask', [[1, 1, 1, 1], [0, 1, 0, 1], [0, 0, 0, 0]])
@pytest.mark.parametrize('permutation', [[0, 1, 2, 3], [3, 1, 0, 2]])
def test_multiple_compartments_edge_multiplicity_masks_and_permutation(mask, permutation):
    k = np.zeros((500, 2))
    d = k.copy()
    k[[0, 50], 0] = 1
    k[[100, 200], 1] = 1
    d[150, 0] = 1
    d[20, 1] = .5
    pk, pc = np.array([0, 0, 1, 1]), np.array([0, 1, 0, 1])
    p = np.asarray(permutation)
    result = reward_brain._bridge_signal_replay(k, d, plastic_kc=pk[p], plastic_compartments=pc[p],
        plastic_groups=[0, 0, 0, 0], plastic_mask=np.array(mask)[p], gains=np.ones(4))
    expected = np.array([pair_sum([0, 10], [30]), pair_sum([0, 10], [4], [.5]),
                         pair_sum([20, 40], [30]), pair_sum([20, 40], [4], [.5])])*mask
    np.testing.assert_allclose(result['gains'], (1+expected[p]).astype(np.float32), atol=1e-7)
    assert (result['bridge_rule'][..., 2].sum()+result['bridge_tail'][..., 2].sum()) == pytest.approx(expected.sum(), abs=1e-11)
    np.testing.assert_array_equal(result['gains'][np.array(mask)[p] == 0], 1)


@pytest.mark.parametrize('tau', [np.nextafter(500., 0), 499.999999, 1e-320, 1e-300])
def test_unsupported_numerical_domains_fail_before_native(tau, monkeypatch):
    monkeypatch.setattr(reward_brain, '_native_library', lambda: pytest.fail('bad numerical config reached native'))
    with pytest.raises(ValueError, match='numerical domain'):
        reward_brain._bridge_signal_replay(np.zeros((1, 1)), np.zeros((1, 1)), rate_tau_ms=tau)


@pytest.mark.parametrize('tau', [1., 100., 499.999])
def test_supported_numeric_domain_has_finite_recording(tau):
    result = replay([0], [5], rate_tau_ms=tau)
    assert all(np.isfinite(a).all() for a in result.values())


@pytest.mark.parametrize('lag', [-20, -5, 5, 20])
def test_short_lag_sensitivity_is_below_raw_ratio_without_erasing_long_lag(lag):
    _, short = run_events([max(0, -lag)], [max(0, lag)])
    _, long = run_events([0], [500])
    assert abs(totals(short)[2]/totals(long)[2]) < np.exp((500-abs(lag))/500)


def test_bridge_allocation_budget_covers_every_new_buffer(monkeypatch):
    obj = engine()
    monkeypatch.setattr(reward_brain, '_MAX_TRACE_VALUES', 200)
    with pytest.raises(ValueError, match='bridge instrumentation'):
        obj.run(np.zeros((20, 1)), bin_ms=.2, record=True)
    with pytest.raises(ValueError, match='bridge replay'):
        replay([0], [5], end=10)


def test_long_electrical_sub_ulp_accumulation_cannot_be_rescued_by_one_tail_write():
    _, result = run_events([0], [.2], end=400)
    expected = np.float32(1+pair_sum([0], [.2]))
    assert result['gains'][0] == expected
    assert expected != 1
    rec = result['instrumentation']
    assert abs(rec['bridge_tail'][0, 2]) < np.spacing(np.float32(1))/2
    assert np.count_nonzero(rec['bridge_rule'][..., 2]) > 1900
    assert abs(rec['bridge_rule'][..., 4].sum()) > 5*np.spacing(np.float32(1))


@pytest.mark.parametrize('config', [dict(learning_rate=1e308),
    dict(rate_tau_ms=1e-150, learning_rate=1e308), dict(gain_bounds=(1e-300, 1.5)),
    dict(onset_steps=-1), dict(onset_steps=True), dict(plastic_groups=(-1,)),
    dict(plastic_kc=(2,)), dict(plastic_compartments=(-1,))])
def test_replay_invalid_domain_dimensions_and_publication_bounds_fail_before_native(config, monkeypatch):
    monkeypatch.setattr(reward_brain, '_native_library', lambda: pytest.fail('invalid replay reached native'))
    with pytest.raises(ValueError):
        replay([0], [5], **config)


@pytest.mark.parametrize('bounds', [(.9, 1.1), (.5000000001, 1.5)])
def test_bridge_rejects_bounds_whose_float_publication_changes_the_declared_interval(bounds):
    with pytest.raises(ValueError, match='representable'):
        engine(gain_bounds=bounds)
    with pytest.raises(ValueError, match='representable'):
        replay([0], [5], gain_bounds=bounds)


def test_bridge_checkpoint_roundtrip_discards_hidden_remainder_and_restarts_signals(tmp_path):
    obj, first = run_events([0], [.2], end=400)
    path = tmp_path / 'checkpoint.npz'
    np.savez(path, gains=first['gains'])
    with np.load(path) as stored:
        clone = engine(gains=stored['gains'])
    rates = np.zeros((2000, 1), np.float32)
    rates[0] = 5000
    results = [item.run(rates, bin_ms=.2, teaching_pulses=[(.2, 0)], record=True) for item in (obj, clone)]
    for name in ('gains', 'counts', 'voltage', 'gain_delta'):
        np.testing.assert_array_equal(results[0][name], results[1][name])
    expected = np.float32(float(first['gains'][0])+pair_sum([0], [.2]))
    assert results[0]['gains'][0] == expected


@pytest.mark.parametrize('mask', [0, 1])
def test_bridge_published_gains_drive_transmission_and_masked_edge_keeps_transmitting(mask):
    obj = engine(weight=80, learning_rate=2000, plastic_mask=[mask])
    rates = np.zeros((100, 1), np.float32)
    rates[0] = 5000
    first = obj.run(rates, bin_ms=.2, teaching_pulses=[(.2, 0)], record=True)
    later = obj.run(rates, bin_ms=.2, plasticity=False)
    assert first['gains'][0] == (.5 if mask else 1)
    assert later['counts'][-1] == (0 if mask else 1)
    if not mask:
        assert not first['instrumentation']['bridge_rule'].any()
        assert not first['instrumentation']['bridge_tail'].any()


def test_bridge_empty_eligible_support_preserves_empty_checkpoint():
    empty = np.array([], int)
    result = reward_brain._bridge_signal_replay(np.ones((4, 1)), np.ones((4, 1)), gains=[],
        plastic_kc=empty, plastic_compartments=empty, plastic_groups=empty, plastic_mask=empty)
    assert result['gains'].size == 0
    assert not result['bridge_rule'].any() and not result['bridge_tail'].any()
