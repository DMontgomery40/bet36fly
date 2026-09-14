"""Chronology, leakage, cache invalidation and readout fixtures for the online sports stage."""
import json

import numpy as np
import pytest

from bet36fly import associative_sports as sp
from bet36fly.associative import AssociativeEngine, array_sha256

PROTOCOL = dict(odor_code=dict(salt='s', width=2, hz=100.0), reinforcer=dict(hz=100.0), learning_rate=1e-3,
                timing=dict(bin_ms=100, probe_bins=7, cue_bins=[1, 5], reinforcement_bins=10, us_bins=[5, 9]))


def tiny_circuit():
    """Two sensory cells (one per ORN type) -> two KCs -> one MBON; a drivable DAN."""
    # neurons: 0,1 sensory (types ORN_a, ORN_b); 2,3 KCs; 4 MBON; 5 DAN
    ptr = np.array([0, 1, 2, 3, 4, 4, 4], np.int64)
    post = np.array([2, 3, 4, 4], np.int32)
    weights = np.array([40., 40., 30., 30.], np.float32)
    engine = AssociativeEngine(ptr, post, weights, sensory=[0, 1], kc_indices=[2, 3], dan_indices=[5],
                               dan_compartments=[0], plastic_edges=[2, 3], plastic_kc=[0, 1], plastic_compartments=[0, 0],
                               n_compartments=1, drive_indices=[5], learning_rate=1e-3)
    types = np.array(['ORN_a', 'ORN_b', 'KCg', 'KCg', 'MBON05', 'PAM08'])
    classes = np.array(['olfactory', 'olfactory', 'Kenyon_Cell', 'Kenyon_Cell', 'MBON', 'DAN'])
    return dict(engine=engine, types=types, classes=classes, sensory=np.array([0, 1], np.int32),
                orn_types=['ORN_a', 'ORN_b'], outputs=[np.array([4], np.int32)])


def games(n=8):
    rows = []
    for i in range(n):
        day = 1 + i // 2
        rows.append(dict(id=f'g{i}', start_time=f'2022-04-{day:02d}T{12 + i % 2}:00:00Z', season=2022,
                         home_key='t:h' if i % 2 == 0 else 't:a', away_key='t:a' if i % 2 == 0 else 't:h'))
    return rows


def test_probe_cache_key_includes_gain_hash_and_invalidates_after_learning():
    cache = sp.ProbeCache()
    a = sp.ProbeCache.key('t:h', 'aaa', 3001, 'sched')
    b = sp.ProbeCache.key('t:h', 'bbb', 3001, 'sched')
    assert a != b
    cache.put(a, dict(response=[1]))
    assert cache.get(a) == dict(response=[1]) and cache.get(b) is None
    assert cache.hits == 1 and cache.misses == 1


def test_delayed_cumulative_wins_respect_48_hour_utc_day_batches():
    rows = games(6)
    outcomes = np.array([0, 0, 0, 0, 0, 0])  # home wins every game
    wins = sp.delayed_cumulative_wins(rows, outcomes)
    # Games on day 1 become available on day 4 (start + 48h <= day start), so days 1-3 see zero wins.
    assert wins[:6].tolist() == [[0, 0]] * 6
    rows = games(8)
    wins = sp.delayed_cumulative_wins(rows, np.zeros(8, int))
    assert wins[6].tolist() == [1, 1] and wins[7].tolist() == [1, 1]


def test_within_week_permutation_keeps_weeks_and_counts():
    dates = [f'2022-04-{d:02d}T12:00:00Z' for d in range(1, 15)]
    perm = sp.within_week_permutation(dates, 7)
    weeks = sp.week_ids(dates)
    assert sorted(perm.tolist()) == list(range(14))
    assert all(weeks[i] == weeks[p] for i, p in enumerate(perm))


def test_season_learner_never_learns_at_prediction_time_and_reinforces_only_available_outcomes():
    circuit = tiny_circuit()
    rows = games(8)
    outcomes = np.zeros(8, int)  # home wins
    innate = np.zeros((8, 4))
    learner = sp.SeasonLearner(circuit, PROTOCOL, arm='plastic', games=rows, features=None, innate=innate,
                               outcomes=outcomes)
    learner.run()
    assert len(learner.rows) == 8
    # Days 1-3 use unit gains (nothing available); reinforcement starts on day 4.
    unit_sha = array_sha256(np.ones(2, np.float32))
    assert [d['reinforced'] for d in learner.days] == [0, 0, 0, 2]
    assert all(r['gains_sha256'] == unit_sha for r in learner.rows[:6])
    assert learner.rows[6]['gains_sha256'] != unit_sha
    # Probes were cached per (team, gains) and never changed gains.
    assert learner.cache.hits > 0
    frozen = sp.SeasonLearner(tiny_circuit(), PROTOCOL, arm='frozen', games=rows, features=None, innate=innate,
                              outcomes=outcomes)
    frozen.run()
    assert all(r['gains_sha256'] == unit_sha for r in frozen.rows) and frozen.reinforcements == 0
    with pytest.raises(ValueError):
        sp.SeasonLearner(tiny_circuit(), PROTOCOL, arm='shuffled', games=rows, features=None, innate=innate,
                         outcomes=outcomes)


def test_season_learner_is_deterministic_and_cancellable():
    circuit = tiny_circuit()
    rows = games(8)
    outcomes = np.array([0, 2, 0, 2, 0, 2, 0, 2])
    a = sp.SeasonLearner(circuit, PROTOCOL, arm='plastic', games=rows, features=None, innate=np.zeros((8, 4)),
                         outcomes=outcomes).run()
    b = sp.SeasonLearner(tiny_circuit(), PROTOCOL, arm='plastic', games=rows, features=None, innate=np.zeros((8, 4)),
                         outcomes=outcomes).run()
    assert json.dumps(a.rows) == json.dumps(b.rows) and a.engine.gains_sha256() == b.engine.gains_sha256()
    with pytest.raises(RuntimeError):
        sp.SeasonLearner(tiny_circuit(), PROTOCOL, arm='plastic', games=rows, features=None,
                         innate=np.zeros((8, 4)), outcomes=outcomes).run(cancelled=lambda: True)


def test_evaluate_arms_uses_one_fixed_readout_procedure_and_reports_plastic_contribution():
    rng = np.random.default_rng(1)
    n = 400
    y = rng.integers(0, 2, n)
    x = rng.normal(size=(n, 16)).astype(np.float32)
    x[:, 8:10] = 5
    signal = np.where(y == 1, 1.0, -1.0)[:, None]
    arms = dict(plastic=np.concatenate([rng.normal(size=(n, 4)), signal + rng.normal(scale=.3, size=(n, 2))], 1),
                frozen=np.concatenate([rng.normal(size=(n, 4)), rng.normal(size=(n, 2))], 1),
                shuffled=np.concatenate([rng.normal(size=(n, 4)), rng.normal(size=(n, 2))], 1))
    dates = [f'2022-{4 + i // 100:02d}-{1 + (i % 100) % 28:02d}T12:00:00Z' for i in range(n)]
    train = np.arange(n) < 200
    candidate = dict(encoder=dict(scales=[1] * 5, coef=[0] * 5, intercept=0.0), training_prior=0.5)
    result = sp.evaluate_arms(arms, x, np.zeros((n, 2)), y, dates, train, candidate, ~train)
    assert set(result['predictions']) >= {'plastic', 'frozen', 'shuffled', 'encoder_only', 'same_information', 'uniform', 'prior'}
    assert result['evaluation']['plasticity_contributes'] is True
    assert result['evaluation']['metrics']['plastic']['log_loss'] < result['evaluation']['metrics']['frozen']['log_loss']


def test_resume_from_a_day_checkpoint_reproduces_the_uninterrupted_run(tmp_path):
    rows = games(8)
    outcomes = np.array([0, 2, 0, 2, 0, 2, 0, 2])
    full = sp.SeasonLearner(tiny_circuit(), PROTOCOL, arm='plastic', games=rows, features=None,
                            innate=np.zeros((8, 4)), outcomes=outcomes, out_dir=tmp_path / 'full').run()
    partial_dir = tmp_path / 'partial'
    partial = sp.SeasonLearner(tiny_circuit(), PROTOCOL, arm='plastic', games=rows, features=None,
                               innate=np.zeros((8, 4)), outcomes=outcomes, out_dir=partial_dir).run(day_limit=2)
    assert len(partial.days) == 2
    saved = json.loads((partial_dir / 'rows.partial.json').read_text())
    state = sp.resume_state(partial_dir, 'plastic')
    assert state['day'] == saved['days'][-1]['day']
    resumed = sp.SeasonLearner(tiny_circuit(), PROTOCOL, arm='plastic', games=rows, features=None,
                               innate=np.zeros((8, 4)), outcomes=outcomes, out_dir=partial_dir)
    resumed.run(resume_after=state['day'], resume_gains=state['gains'], resume_rows=saved['rows'], resume_days=saved['days'])
    assert json.dumps(resumed.rows) == json.dumps(full.rows)
    assert resumed.engine.gains_sha256() == full.engine.gains_sha256()
    assert [d['gains_sha256'] for d in resumed.days] == [d['gains_sha256'] for d in full.days]
    with pytest.raises(ValueError):
        resumed.run(resume_after=state['day'])
