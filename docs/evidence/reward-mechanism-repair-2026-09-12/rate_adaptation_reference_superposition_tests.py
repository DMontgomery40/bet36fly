"""Synthetic pre-execution validation of the all-KC independent oracle."""

import numpy as np
import pytest

from rate_adaptation_reference_oracle import (
    AREA_ATOL, AREA_RTOL, R, STATE_ATOL, STATE_RTOL, finite_ode, tail_quadrature,
)
from rate_adaptation_reference_superposition import (
    integrate_dan_events, kc_boundary_states, kc_phase_products,
)


def scalar_event_reference(kc, dan, boundaries):
    state = np.zeros(5)
    areas = np.zeros((len(boundaries), 2))
    saved_states = [state.copy()]
    for i in range(len(kc)):
        state[0] += R * kc[i]
        state[2] += R * dan[i]
        step = finite_ode(state, 0.2)
        state = step.state
        saved_states.append(state.copy())
        for phase, (start, end) in enumerate(zip(boundaries, boundaries[1:])):
            if start <= i < end:
                areas[phase] += [step.positive_area, step.negative_area]
    tail = tail_quadrature(state)
    areas[-1] = [tail.positive_area, tail.negative_area]
    return areas, np.asarray(saved_states)


@pytest.mark.parametrize("seed", [0, 1, 2])
@pytest.mark.parametrize("onset", [0, 2, 8])
def test_every_kc_phase_matches_full_scalar_event_ode(seed, onset):
    rng = np.random.default_rng(seed)
    kc = rng.integers(0, 2, size=(20, 4), dtype=np.int32)
    dan = rng.integers(0, 3, size=(20, 2)) / 2
    boundaries = (onset, 10, 20)
    weighted = integrate_dan_events(dan[None])
    actual = kc_phase_products(kc, weighted.weighted_intervals[0], weighted.weighted_tail[0], boundaries)
    for c in range(2):
        for j in range(4):
            expected, states = scalar_event_reference(kc[:, j], dan[:, c], boundaries)
            np.testing.assert_allclose(actual[:, c, j], expected, atol=AREA_ATOL, rtol=AREA_RTOL)
            np.testing.assert_allclose(weighted.states[0, :, c], states[:, [2, 3, 4]],
                                       atol=STATE_ATOL, rtol=STATE_RTOL)
            for boundary in boundaries:
                expected_kc = states[boundary, :2]
                np.testing.assert_allclose(kc_boundary_states(kc, boundary)[j], expected_kc,
                                           atol=STATE_ATOL, rtol=STATE_RTOL)


def test_batch_channel_scaling_zero_channels_and_onset_history():
    kc = np.zeros((20, 2), dtype=np.int32)
    kc[[0, 1, 9, 10, 19], 0] = 1
    kc[[2, 6, 19], 1] = 1
    dan = np.zeros((3, 20, 2))
    dan[0, [0, 8, 19], 0] = 1
    dan[1] = dan[0] * 0.5
    # Third trial and second channel are entirely silent DAN, not missing input.
    weighted = integrate_dan_events(dan)
    all_areas = np.stack([
        kc_phase_products(kc, weighted.weighted_intervals[i], weighted.weighted_tail[i], (5, 10, 20))
        for i in range(3)
    ])
    np.testing.assert_allclose(all_areas[1], all_areas[0] * 0.5, atol=AREA_ATOL, rtol=AREA_RTOL)
    assert not np.any(all_areas[:, :, 1])
    assert not np.any(all_areas[2])
    assert np.any(all_areas[0, :, 0] > 0)


@pytest.mark.parametrize("events", [np.zeros((0, 3, 2)), np.zeros((3, 2)),
                                    np.full((1, 3, 2), np.nan), np.full((1, 3, 2), -0.1),
                                    np.full((1, 3, 2), 1.1)])
def test_bad_dan_inputs_fail_closed(events):
    with pytest.raises(ValueError):
        integrate_dan_events(events)


@pytest.mark.parametrize("boundaries", [(0, 1, 1), (2, 1, 3), (0, 2), (0.0, 1, 3), (-1, 1, 3)])
def test_bad_phase_boundaries_fail_closed(boundaries):
    with pytest.raises(ValueError):
        kc_phase_products(np.zeros((3, 2)), np.zeros((3, 1, 3)), np.zeros((1, 3)), boundaries)
