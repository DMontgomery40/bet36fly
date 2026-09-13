"""Finite, reset, dimensionless actual-event hypothesis; not a DARELA solver.

WT sweep-1 factors from PNAS Nexus 2(3):pgad044, Table 1. The source-Euler
kick q=1+p, pre-kick unit-rested impulse and exact recovery between actual
events are explicitly an engineering construction, not calibrated fly
kinetics or an indefinitely bounded tonic mechanism. No burst/teaching gate,
source current/concentration, state cap, simulator, or history loader exists
here. Upstream DARELA files are preserved separately and not imported.
"""

from numbers import Real

import numpy as np

WT1_P = (0.0105, -0.003, -0.0011)
WT1_TAU_S = (7.5, 15.0, 900.0)


def _fixed_vector(value, expected, name):
    if not isinstance(value, (tuple, list, np.ndarray)):
        raise ValueError(f"{name} must contain the fixed WT1 triple")
    array = np.asarray(value)
    if (
        array.shape != (3,)
        or array.dtype.kind not in "fi"
        or any(not isinstance(x, Real) or isinstance(x, (bool, np.bool_)) for x in value)
    ):
        raise ValueError(f"{name} must be three real numerical values")
    array = array.astype(np.float64)
    if not np.isfinite(array).all() or not np.array_equal(array, expected):
        raise ValueError(f"{name} differs from the frozen WT1 parameters")
    return array


def release_events(spikes, compartments, *, p=WT1_P, tau_s=WT1_TAU_S):
    """Transform ordered per-body events, then pool by fixed populations 2/22.

    Inputs are strictly int32 ndarray spikes(T,24), binary, 0<=T<=2000;
    compartments(24) contains exactly two 0s and twenty-two 1s. Columns retain
    caller's body ordering. Each call resets all H to one at trial time zero.
    p/tau keywords only validate the exact fixed row; retuning is rejected.

    state_before[t] is H at t/5000 seconds after quiet recovery; state_after[t]
    is immediately after the event kick, equal to before on silent rows.
    endpoint_state is H at T/5000 seconds, including the final silent interval.
    All five outputs are independent float64 arrays. H evolves for all actual
    events, including those before the separate bridge's 100ms write onset.
    Silent H recovery emits no release; an external bridge owns its own tail.
    """
    factors = _fixed_vector(p, (0.0105, -0.003, -0.0011), "p")
    tau = _fixed_vector(tau_s, (7.5, 15.0, 900.0), "tau_s")
    if (
        not isinstance(spikes, np.ndarray)
        or spikes.dtype != np.dtype(np.int32)
        or spikes.ndim != 2
        or spikes.shape[1] != 24
        or not 0 <= spikes.shape[0] <= 2000
    ):
        raise ValueError("spikes must be int32(T,24), with 0<=T<=2000")
    if np.any((spikes != 0) & (spikes != 1)):
        raise ValueError("each body's actual event must be binary")
    if (
        not isinstance(compartments, np.ndarray)
        or compartments.dtype != np.dtype(np.int32)
        or compartments.shape != (24,)
        or np.count_nonzero(compartments == 0) != 2
        or np.count_nonzero(compartments == 1) != 22
    ):
        raise ValueError("compartments must be int32(24) with fixed populations 2/22")

    steps = len(spikes)
    before = np.empty((steps, 24, 3), dtype=np.float64)
    after = np.empty_like(before)
    release = np.zeros((steps, 24), dtype=np.float64)
    # Reference each body's recovery directly to its last actual event. Silent
    # rows never advance this anchor or accumulate per-step recovery rounding.
    post_event = np.ones((24, 3), dtype=np.float64)
    event_step = np.zeros(24, dtype=np.int64)
    q = 1 + factors
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            for t in range(steps):
                elapsed = ((t - event_step) / 5000)[:, None]
                current = 1 + (post_event - 1) * np.exp(-elapsed / tau)
                before[t] = current
                active = spikes[t] == 1
                release[t, active] = np.prod(current[active], axis=1)
                current[active] *= q
                after[t] = current
                post_event[active] = current[active]
                event_step[active] = t
            elapsed = ((steps - event_step) / 5000)[:, None]
            endpoint = 1 + (post_event - 1) * np.exp(-elapsed / tau)
            pooled = np.column_stack(
                [
                    release[:, compartments == 0].sum(axis=1) / 2,
                    release[:, compartments == 1].sum(axis=1) / 22,
                ]
            )
    except FloatingPointError as exc:
        raise ValueError("nonfinite release arithmetic") from exc
    result = {
        "per_cell_release": release,
        "pooled_release": pooled,
        "state_before": before,
        "state_after": after,
        "endpoint_state": endpoint,
    }
    if (
        any(not np.isfinite(a).all() for a in result.values())
        or any(np.any(a <= 0) for a in (before, after, endpoint))
        or np.any(release < 0)
        or np.any(release[spikes == 1] <= 0)
    ):
        raise ValueError("release/state positivity or finite-domain failure")
    return result
