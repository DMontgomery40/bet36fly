"""Independent event enumeration and closed exponential accounting oracles."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location("arrival_analysis", Path(__file__).with_name("delivered-arrivals-resumed.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def queue_oracle(emissions, spikes, steps):
    """Time-ordered toy queue, independently avoiding latest-spike search."""
    queue = {}
    for event_id, step in enumerate(emissions):
        queue.setdefault(step + 9, []).append(event_id)
    ready = 0
    states = ["pending"] * len(emissions)
    coincident = []
    for time in range(steps):
        for event_id in queue.get(time, []):
            states[event_id] = "accepted" if time >= ready else "rejected"
            if time in spikes and time >= ready:
                coincident.append(event_id)
        if time in spikes:
            assert time >= ready
            ready = time + 11
    return states, coincident


@pytest.mark.parametrize("target_spikes", [[], [0], [9], [10], [11], [0, 11, 23], [9, 20, 33]])
def test_complete_delay_release_same_step_and_end_matrix(target_spikes):
    emissions = np.arange(40, dtype=np.int64)
    result = MODULE.classify(emissions, np.array(target_spikes, dtype=np.int64), 40)
    states, same = queue_oracle(emissions, target_spikes, 40)
    for key in ("accepted", "rejected", "pending"):
        assert result[key].tolist() == [state == key for state in states]
    assert np.flatnonzero(result["same_step"]).tolist() == same
    assert sum(result[key].sum() for key in ("accepted", "rejected", "pending")) == 40
    assert result["due"].tolist() == list(range(9, 49))


def test_exact_release_and_same_step_use_previous_spike():
    # Source at 0 arrives 9: accepted, then target resets. 19 rejects; 20 accepts
    # even though a new target spike is recorded at exactly 20.
    result = MODULE.classify(np.array([0, 10, 11, 12]), np.array([9, 20]), 40)
    assert result["accepted"].tolist() == [True, False, True, False]
    assert result["same_step"].tolist() == [True, False, True, False]
    assert result["ready"].tolist() == [0, 20, 20, 31]


def test_exact_400ms_is_pending_never_counted_as_delivered():
    result = MODULE.classify(np.array([1990, 1991, 1999]), np.array([], dtype=int), 2000)
    assert result["due"].tolist() == [1999, 2000, 2008]
    assert result["accepted"].tolist() == [True, False, False]
    assert result["pending"].tolist() == [False, True, True]


@pytest.mark.parametrize("spikes", [[0, 10], [10, 9], [11, 11]])
def test_impossible_refractory_raster_rejected(spikes):
    with pytest.raises(ValueError, match="refractory"):
        MODULE.classify(np.array([0]), np.array(spikes), 40)


@pytest.mark.parametrize("emissions", [np.array([-.1]), np.array([-1]), np.array([40]), np.array([True])])
def test_invalid_emission_times_are_not_rounded(emissions):
    with pytest.raises(ValueError):
        MODULE.classify(emissions, np.array([], dtype=int), 40)


@pytest.mark.parametrize("spikes", [[], [9], [20], [9, 20, 36]])
def test_conductance_decay_and_spike_reset_match_closed_individual_impulses(spikes):
    increments = np.zeros((40, 4))
    for step, family, weight in [(9, 0, .1375), (12, 1, .55), (20, 0, .4125), (36, 2, 1.1), (39, 3, .2)]:
        # For this linear primitive, accepted increments are supplied directly.
        increments[step, family] += weight
    ledger = MODULE.conductance_ledger(increments, np.array(spikes, dtype=int))
    reset = np.zeros_like(increments)
    before = np.zeros_like(increments)
    endpoint = np.zeros(4)
    for due, family in zip(*np.nonzero(increments)):
        weight = increments[due, family]
        next_spike = next((spike for spike in spikes if spike >= due), None)
        last = next_spike if next_spike is not None else 39
        for time in range(due, last + 1):
            before[time, family] += weight * np.exp(-.2 * (time - due) / 5.)
        if next_spike is not None:
            reset[next_spike, family] += weight * np.exp(-.2 * (next_spike - due + 1) / 5.)
        else:
            endpoint[family] += weight * np.exp(-.2 * (40 - due) / 5.)
    np.testing.assert_allclose(ledger["pre_integration"], before, rtol=0, atol=2e-15)
    np.testing.assert_allclose(ledger["spike_resets"], reset, rtol=0, atol=2e-15)
    np.testing.assert_allclose(ledger["endpoint"], endpoint, rtol=0, atol=2e-15)
    np.testing.assert_allclose(increments.sum(0), ledger["decay_losses"].sum(0) + reset.sum(0) + endpoint, rtol=0, atol=4e-15)


def test_rejected_inputs_never_enter_conductance_or_bank_for_release():
    events = np.zeros((40, 2), dtype=int)
    events[[0, 1, 10, 11], 0] = 1
    events[1, 1] = 1
    result, series = MODULE.summarize_target(events, np.array([0, 1]),
                                            np.array([.1375, 1.375]), np.array([1, 10]),
                                            np.array([0, 2]), np.array([9, 20]))
    assert result["totals"]["accepted"]["edge_events"] == 2
    assert result["totals"]["rejected"]["edge_events"] == 3
    assert result["totals"]["accepted"]["contact_events"] == 2
    assert result["totals"]["rejected"]["contact_events"] == 12
    assert series["accepted_increment"][10].sum() == 0
    assert series["pre_integration"][19].sum() == 0
    assert series["pre_integration"][20, 0] == .1375
    assert series["pre_integration"][:, 2].sum() == 0


def test_phase_boundaries_follow_delayed_arrival_and_keep_all_families():
    events = np.zeros((2000, 4), dtype=int)
    # Arrivals just before/at all three internal boundaries, last processed,
    # exact endpoint and after endpoint. Deliberately differ emission phases.
    due_times = [499, 500, 649, 650, 1499, 1500, 1999, 2000, 2008]
    for index, due in enumerate(due_times):
        events[due - 9, index % 4] = 1
    result, _ = MODULE.summarize_target(events, np.arange(4), np.ones(4), np.ones(4, dtype=int),
                                       np.arange(4), np.array([], dtype=int))
    counts = {name: sum(phase["due"]["edge_events"] for phase in result["phases"] if phase["phase"] == name)
              for name, _, _ in MODULE.PHASES}
    assert list(counts.values()) == [1, 2, 2, 2]
    assert [event["due_step"] for event in result["pending_events"]] == [2000, 2008]
    assert result["totals"]["emitted"]["edge_events"] == 9


def test_targets_are_independent_and_duplicate_graph_edges_fail():
    events = np.zeros((40, 1), dtype=int)
    events[0, 0] = 1
    args = (events, np.array([0]), np.array([.1375]), np.array([1]), np.array([0]))
    first, _ = MODULE.summarize_target(*args, np.array([0]))
    second, _ = MODULE.summarize_target(*args, np.array([], dtype=int))
    assert first["totals"]["rejected"]["edge_events"] == 1
    assert second["totals"]["accepted"]["edge_events"] == 1
    with pytest.raises(ValueError, match="Duplicate"):
        MODULE.summarize_target(events, np.array([0, 0]), np.ones(2), np.ones(2, dtype=int),
                                np.zeros(2, dtype=int), np.array([], dtype=int))


@pytest.mark.parametrize("contacts,valid", [(np.array([3], dtype=np.float32), True),
                                            (np.array([3], dtype=np.int64), True),
                                            (np.array([3.5]), False), (np.array([np.nan]), False),
                                            (np.array([np.inf]), False), (np.array([0.]), False)])
def test_contact_counts_use_integral_value_not_storage_dtype(contacts, valid):
    events = np.zeros((40, 1), dtype=int)
    events[0, 0] = 1
    args = (events, np.array([0]), np.array([.4125]), contacts,
            np.array([0]), np.array([], dtype=int))
    if valid:
        result, _ = MODULE.summarize_target(*args)
        assert result["totals"]["accepted"]["contact_events"] == 3
    else:
        with pytest.raises(ValueError, match="contact"):
            MODULE.summarize_target(*args)


def test_all_32_explicit_selectors_are_ordered_and_unique():
    rows = MODULE.expected_rows()
    assert len(rows) == len({tuple(row.values()) for row in rows}) == 32
    assert [(row["game"], row["seed"]) for row in rows[::2]] == [
        (4362, 4404), (4366, 4408), (4370, 4412), (4374, 4416),
        (4378, 4420), (4383, 4425), (4387, 4429), (4391, 4433),
        (4395, 2004437), (4399, 2004441), (4404, 2004446), (4408, 2004450),
        (4412, 2004454), (4416, 2004458), (4420, 2004462), (4425, 2004467)]
    assert all(alternate["seed"] - base["seed"] == 1_000_000
               for base, alternate in zip(rows[::2], rows[1::2]))


def test_existing_analysis_refused_before_input_reads(tmp_path, monkeypatch):
    prefix = tmp_path / "kept"
    prefix.with_suffix(".npz").write_bytes(b"existing")
    monkeypatch.setattr(MODULE, "read_inputs", lambda: pytest.fail("read_inputs reached"))
    with pytest.raises(FileExistsError):
        MODULE.run(prefix)
    assert prefix.with_suffix(".npz").read_bytes() == b"existing"
