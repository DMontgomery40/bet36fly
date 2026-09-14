"""Associative engine: rule timing, state lifetimes, masks, coupling, checkpoints, equivalence."""
import json

import numpy as np
import pytest

from bet36fly.associative import (AssociativeEngine, array_sha256, load_checkpoint, restore_checkpoint,
                                  save_checkpoint, team_odor_types)
from bet36fly.sensory import SensoryEngine


def chain(**kw):
    """0 (sensory) -> 1 (KC) -> 2 (MBON, plastic edge 1); 3 is a DAN reachable by the reinforcer drive."""
    ptr = np.array([0, 1, 2, 2, 2], np.int64)
    post = np.array([1, 2], np.int32)
    weights = np.array([40., 20.], np.float32)
    defaults = dict(sensory=[0], kc_indices=[1], dan_indices=[3], dan_compartments=[0], plastic_edges=[1],
                    plastic_kc=[0], plastic_compartments=[0], n_compartments=1, drive_indices=[3],
                    tau_kc_ms=1000., tau_dan_ms=1000., learning_rate=1e-3, gain_bounds=(0.5, 1.5))
    defaults.update(kw)
    return AssociativeEngine(ptr, post, weights, **defaults)


def schedule(bins, cue=(), us=()):
    rates = np.zeros((bins, 1), np.float32)
    drive = np.zeros((bins, 1), np.float32)
    for lo, hi in cue:
        rates[lo:hi, 0] = 200.
    for lo, hi in us:
        drive[lo:hi, 0] = 200.
    return rates, drive


def test_kc_before_dopamine_depresses_and_dopamine_before_kc_potentiates():
    forward = chain()
    rates, drive = schedule(20, cue=[(0, 5)], us=[(6, 12)])
    result = forward.run(rates, drive=drive, bin_ms=100., seed=3, plasticity=True)
    assert result['counts'][1] > 0 and result['counts'][3] > 0
    assert forward.gains[0] < 1.0
    assert result['comp_bins'][:, 0, 2].sum() < 0 and result['comp_bins'][:, 0, 1].sum() == 0
    backward = chain()
    rates, drive = schedule(20, cue=[(6, 11)], us=[(0, 5)])
    backward.run(rates, drive=drive, bin_ms=100., seed=3, plasticity=True)
    assert backward.gains[0] > 1.0


def test_cue_alone_and_reinforcer_alone_leave_gains_unchanged():
    engine = chain()
    rates, drive = schedule(10, cue=[(0, 5)])
    engine.run(rates, drive=drive, bin_ms=100., seed=5, plasticity=True)
    assert engine.gains[0] == 1.0
    rates, drive = schedule(10, us=[(0, 5)])
    engine.run(rates, drive=drive, bin_ms=100., seed=5, plasticity=True)
    assert engine.gains[0] == 1.0


def test_plasticity_off_and_zero_coupling_are_byte_identical_and_masked_edges_never_update():
    rates, drive = schedule(20, cue=[(0, 5)], us=[(6, 12)])
    frozen = chain()
    before = frozen.gains.tobytes()
    result = frozen.run(rates, drive=drive, bin_ms=100., seed=3, plasticity=False)
    assert frozen.gains.tobytes() == before and result['gain_delta'].tolist() == [0.0]
    assert result['comp_bins'][:, 0, 0].sum() > 0  # dopamine spikes were recorded even without learning
    lesion = chain(coupling=[0.0])
    lesion.run(rates, drive=drive, bin_ms=100., seed=3, plasticity=True)
    assert lesion.gains.tobytes() == before
    masked = chain(plastic_mask=[0])
    masked.run(rates, drive=drive, bin_ms=100., seed=3, plasticity=True)
    assert masked.gains.tobytes() == before


def test_learned_gain_changes_subsequent_transmission_and_persists_across_electrical_resets():
    engine = chain()
    rates, drive = schedule(20, cue=[(0, 5)], us=[(6, 12)])
    probe, _ = schedule(10, cue=[(0, 10)])
    baseline = engine.run(probe, bin_ms=100., seed=11)['counts'][2]
    for _ in range(6):
        engine.run(rates, drive=drive, bin_ms=100., seed=3, plasticity=True)
    assert engine.gains[0] < 0.75
    after = engine.run(probe, bin_ms=100., seed=11)['counts'][2]
    assert after < baseline
    # Blank trials reset electrical state and traces but do not erase the learned gain.
    blank, _ = schedule(10)
    for _ in range(3):
        blank_result = engine.run(blank, bin_ms=100., seed=1, plasticity=True)
        assert blank_result['counts'].sum() == 0
    assert engine.run(probe, bin_ms=100., seed=11)['counts'][2] == after


def test_bounds_are_respected_and_contacts_are_counted():
    engine = chain(learning_rate=0.5)
    rates, drive = schedule(20, cue=[(0, 5)], us=[(6, 12)])
    result = engine.run(rates, drive=drive, bin_ms=100., seed=3, plasticity=True)
    assert engine.gains[0] == np.float32(0.5)
    assert result['comp_bins'][:, 0, 4].sum() > 0


def test_traces_reset_per_call_unless_supplied_and_are_returned():
    engine = chain()
    rates, drive = schedule(5, cue=[(0, 5)])
    first = engine.run(rates, drive=drive, bin_ms=100., seed=3, plasticity=True)
    assert first['traces']['kc'][0] > 0
    second = engine.run(np.zeros((5, 1), np.float32), bin_ms=100., seed=3, plasticity=True)
    assert second['traces']['kc'][0] == 0
    third = engine.run(np.zeros((5, 1), np.float32), bin_ms=100., seed=3, plasticity=True,
                       traces=first['traces'])
    assert 0 < third['traces']['kc'][0] < first['traces']['kc'][0]
    with pytest.raises(ValueError):
        engine.run(rates, bin_ms=100., traces=dict(kc=[-1.0], dan=[0.0]))


def test_determinism_and_reinforcer_drive_respects_refractory():
    a = chain()
    b = chain()
    rates, drive = schedule(10, cue=[(0, 5)], us=[(0, 10)])
    ra = a.run(rates, drive=drive, bin_ms=100., seed=9, plasticity=True)
    rb = b.run(rates, drive=drive, bin_ms=100., seed=9, plasticity=True)
    assert np.array_equal(ra['counts'], rb['counts']) and a.gains.tobytes() == b.gains.tobytes()
    assert ra['drive_events'].sum() >= ra['counts'][3]  # refractory-blocked events do not spike
    assert ra['counts'][3] <= 1000 / 2.2 + 1


def test_checkpoint_round_trip_provenance_and_circuit_binding(tmp_path):
    engine = chain()
    rates, drive = schedule(20, cue=[(0, 5)], us=[(6, 12)])
    engine.run(rates, drive=drive, bin_ms=100., seed=3, plasticity=True)
    meta = save_checkpoint(tmp_path / 'ck.npz', engine, identity='assoc-test', parent_sha256='0' * 64, note='x')
    gains, loaded = load_checkpoint(tmp_path / 'ck.npz')
    assert loaded == meta and array_sha256(gains) == meta['gains_sha256'] == engine.gains_sha256()
    fresh = chain()
    restore_checkpoint(fresh, tmp_path / 'ck.npz', identity='assoc-test')
    assert fresh.gains.tobytes() == engine.gains.tobytes()
    with pytest.raises(ValueError):
        restore_checkpoint(fresh, tmp_path / 'ck.npz', identity='other')
    other = chain(plastic_mask=[0])
    with pytest.raises(ValueError):
        restore_checkpoint(other, tmp_path / 'ck.npz')
    with np.load(tmp_path / 'ck.npz') as data:
        arrays = {k: data[k] for k in data.files}
    arrays['gains'] = arrays['gains'] * 0 + 1.2
    np.savez_compressed(tmp_path / 'bad.npz', **arrays)
    with pytest.raises(ValueError):
        load_checkpoint(tmp_path / 'bad.npz')


def test_matches_sensory_engine_exactly_without_reinforcer_drive():
    rng = np.random.default_rng(4)
    n = 60
    ptr = np.zeros(n + 1, np.int64)
    post, weights = [], []
    for i in range(n):
        targets = rng.choice(n, size=6, replace=False)
        post.extend(targets.tolist())
        weights.extend((rng.uniform(-15, 30, size=6)).tolist())
        ptr[i + 1] = len(post)
    post, weights = np.array(post, np.int32), np.array(weights, np.float32)
    sensory = np.array([0, 1, 2], np.int32)
    rates = rng.uniform(0, 150, size=(12, 3)).astype(np.float32)
    reference = SensoryEngine(ptr, post, weights, sensory).run(rates, bin_ms=25., seed=77, sample=[5, 6])
    engine = AssociativeEngine(ptr, post, weights, sensory, kc_indices=[10], dan_indices=[11],
                               dan_compartments=[0], plastic_edges=[], plastic_kc=[], plastic_compartments=[],
                               n_compartments=1, drive_indices=[11])
    result = engine.run(rates, bin_ms=25., seed=77, sample=[5, 6])
    for key in ('counts', 'trace', 'input_events', 'population'):
        assert np.array_equal(result[key], reference[key]), key


def test_engine_validation_rejects_invalid_configuration():
    with pytest.raises(ValueError):
        chain(plastic_kc=[1])  # edge 1 originates at neuron 1 (KC index 0), not KC index 1
    with pytest.raises(ValueError):
        chain(coupling=[-1.0])
    with pytest.raises(ValueError):
        chain(gains=[2.0])
    engine = chain()
    with pytest.raises(ValueError):
        engine.run(np.zeros((5, 2), np.float32), bin_ms=100.)
    with pytest.raises(ValueError):
        engine.run(np.zeros((5, 1), np.float32), drive=np.zeros((4, 1)), bin_ms=100.)
    with pytest.raises(ValueError):
        engine.set_gains([3.0])
    assert engine.gains[0] == 1.0


def test_team_odor_code_is_deterministic_distinct_and_symmetric():
    types = [f'ORN_{i}' for i in range(53)]
    a = team_odor_types('mlb:147', types, 16)
    assert a == team_odor_types('mlb:147', types, 16) and len(set(a)) == 16 and a == sorted(a)
    assert a != team_odor_types('mlb:121', types, 16)
    assert json.dumps(a) == json.dumps(team_odor_types('mlb:147', list(reversed(types)), 16))
    with pytest.raises(ValueError):
        team_odor_types('', types, 16)
    with pytest.raises(ValueError):
        team_odor_types('mlb:1', types, 60)


def two_kc(**kw):
    """0,1 sensory -> 2,3 KCs -> 4 MBON (edges 2,3 plastic); 5 is the drivable DAN."""
    ptr = np.array([0, 1, 2, 3, 4, 4, 4], np.int64)
    post = np.array([2, 3, 4, 4], np.int32)
    weights = np.array([40., 40., 30., 30.], np.float32)
    defaults = dict(sensory=[0, 1], kc_indices=[2, 3], dan_indices=[5], dan_compartments=[0], plastic_edges=[2, 3],
                    plastic_kc=[0, 1], plastic_compartments=[0, 0], n_compartments=1, drive_indices=[5],
                    tau_kc_ms=1000., tau_dan_ms=1000., learning_rate=1e-3, gain_bounds=(0.5, 1.5))
    defaults.update(kw)
    return AssociativeEngine(ptr, post, weights, **defaults)


def test_dopamine_gated_recovery_moves_only_inactive_depressed_synapses_toward_rest_and_never_past_it():
    def pair(engine, cue_cell):
        rates = np.zeros((20, 2), np.float32)
        rates[0:5, cue_cell] = 200.
        drive = np.zeros((20, 1), np.float32)
        drive[6:12, 0] = 200.
        return engine.run(rates, drive=drive, bin_ms=100., seed=3, plasticity=True)

    plain = two_kc()
    recovering = two_kc(recovery=[0.05])
    for _ in range(4):
        pair(plain, 0)
        pair(recovering, 0)
    # Forward pairing of KC 0 is bit-identical with and without the recovery term (KC 0 is eligible).
    assert plain.gains[0] == recovering.gains[0] < 1.0
    assert plain.gains[1] == recovering.gains[1] == 1.0  # KC 1 was silent and already at rest: no change
    depressed = float(recovering.gains[0])
    # Now reward KC 1: KC 0 is silent, so dopamine without KC 0 activity recovers its depressed edge.
    result = pair(recovering, 1)
    assert depressed < recovering.gains[0] < 1.0
    assert result['comp_bins'][:, 0, 7].sum() > 0
    control = pair(plain, 1)
    assert plain.gains[0] == depressed and control['comp_bins'][:, 0, 7].sum() == 0
    # Many unrelated rewards converge to rest exactly, never above it.
    for _ in range(300):
        pair(recovering, 1)
    assert np.float32(0.999) <= recovering.gains[0] <= np.float32(1.0)  # asymptotic approach, never past rest
    # An edge above rest (potentiated) is not pulled down by the recovery term.
    above = two_kc(recovery=[0.05], gains=[1.2, 1.0])
    pair(above, 1)
    assert above.gains[0] == np.float32(1.2)
    with pytest.raises(ValueError):
        two_kc(recovery=[-1.0])
    with pytest.raises(ValueError):
        two_kc(rest_gain=2.0)
