"""Independent analytic/oracle fixtures; only generated synthetic events.

Breaks caught: exponential instead of source-Euler jump, post/pre phase swap,
seconds/milliseconds, onset gating, recovery clock drift, state sharing,
pool-before-cell transformation, omitted endpoint interval and silent caps.
"""

import math

import mpmath as mp
import numpy as np
import pytest

from darela_release import release_events
from darela_release_reference import reference_events, scalar_reference

PARAMS = (("0.0105", "7.5"), ("-0.003", "15"), ("-0.0011", "900"))
ATOL = RTOL = 1e-12


def fixture(steps):
    return np.zeros((steps, 24), np.int32), np.array([0] * 2 + [1] * 22, np.int32)


def compare(actual, expected):
    assert set(actual) == set(expected)
    for key in expected:
        assert actual[key].dtype == expected[key].dtype == np.dtype("float64")
        assert actual[key].shape == expected[key].shape
        assert np.isfinite(actual[key]).all()
        np.testing.assert_allclose(actual[key], expected[key], atol=ATOL, rtol=RTOL, err_msg=key)


@pytest.mark.parametrize("steps", [0, 1, 499, 500, 501, 2000])
def test_scalar_quiet_domain_has_no_fabricated_release(steps):
    x = scalar_reference(steps, [])
    assert x["before"].shape == x["after"].shape == (steps, 3)
    assert x["release"].shape == (steps,)
    assert x["endpoint"].shape == (3,)
    for key in ["before", "after", "endpoint"]:
        np.testing.assert_array_equal(x[key], 1)
    np.testing.assert_array_equal(x["release"], 0)


@pytest.mark.parametrize("event", [0, 499, 500, 1999])
def test_scalar_one_event_closed_form_every_state_and_endpoint(event):
    x = scalar_reference(2000, [event])
    pre = np.ones((2000, 3))
    post = np.ones_like(pre)
    for j, (p, tau) in enumerate(PARAMS):
        p, tau = float(p), float(tau)
        for t in range(event + 1, 2000):
            pre[t, j] = 1 + p * math.exp(-(t - event) / 5000 / tau)
        post[:, j] = pre[:, j]
        post[event, j] = 1 + p
    np.testing.assert_allclose(x["before"], pre, atol=2e-15, rtol=2e-15)
    np.testing.assert_allclose(x["after"], post, atol=2e-15, rtol=2e-15)
    endpoint = [1 + float(p) * math.exp(-(2000 - event) / 5000 / float(tau)) for p, tau in PARAMS]
    np.testing.assert_allclose(x["endpoint"], endpoint, atol=2e-15, rtol=2e-15)
    assert x["release"][event] == 1 and np.count_nonzero(x["release"]) == 1
    # Direct binary32 conversion is checked only here; helper publishes no F32 gain.
    np.testing.assert_array_equal(x["after"].astype(np.float32), post.astype(np.float32))


@pytest.mark.parametrize("gap", [1, 11, 100, 400, 1999])
def test_scalar_periodic_oracle_matches_geometric_closed_form(gap):
    events = list(range(0, 2000, gap))
    x = scalar_reference(2000, events)
    with mp.workdps(70):
        for j, (p, tau) in enumerate(PARAMS):
            q = 1 + mp.mpf(p)
            r = mp.exp(-mp.mpf(gap) / 5000 / mp.mpf(tau))
            a, b = q * r, 1 - r
            exact = [float(a**n + b * (1 - a**n) / (1 - a)) for n in range(len(events))]
            np.testing.assert_allclose(x["before"][events, j], exact, atol=2e-14, rtol=2e-14)


def test_irregular_oracle_matches_direct_finite_event_sum():
    events = [0, 3, 9, 11, 17]
    x = scalar_reference(21, events)
    with mp.workdps(70):
        for t in range(22):
            for j, (p, tau) in enumerate(PARAMS):
                q, tau = 1 + mp.mpf(p), mp.mpf(tau)
                prior = [s for s in events if s < t]
                z = (q - 1) * sum(
                    q ** (len(prior) - 1 - k) * mp.exp(mp.mpf(s) / 5000 / tau) for k, s in enumerate(prior)
                )
                want = float(1 + mp.exp(-mp.mpf(t) / 5000 / tau) * z)
                got = x["endpoint"][j] if t == 21 else x["before"][t, j]
                assert got == pytest.approx(want, abs=2e-15, rel=2e-15)


@pytest.mark.parametrize(
    "kind", ["empty", "quiet", "single", "last", "onset", "dense", "staggered", "random4", "random19"]
)
def test_every_helper_output_matches_independent_scalar_reference(kind):
    steps = 0 if kind == "empty" else 2000 if kind in ["dense", "last", "onset", "staggered"] else 151
    spikes, compartments = fixture(steps)
    if kind == "single":
        spikes[0, [0, 1, 2, 23]] = 1
    elif kind == "last":
        spikes[1999, :] = 1
    elif kind == "onset":
        spikes[[0, 499, 500, 501, 1999], :] = 1
    elif kind == "dense":
        spikes[:] = 1
    elif kind == "staggered":
        for c in range(24):
            gap = [1, 2, 7, 11, 17, 50, 99, 389][c % 8]
            spikes[c % gap :: gap, c] = 1
    elif kind.startswith("random"):
        spikes[:] = np.random.default_rng(int(kind[6:])).random(spikes.shape) < 0.17
    original = spikes.copy()
    actual = release_events(spikes, compartments)
    expected = reference_events(spikes, compartments)
    compare(actual, expected)
    np.testing.assert_array_equal(actual["per_cell_release"][spikes == 0], 0)
    np.testing.assert_array_equal(actual["state_before"][spikes == 0], actual["state_after"][spikes == 0])
    np.testing.assert_array_equal(spikes, original)
    if kind == "dense":
        assert (actual["state_before"] > 0).all()
        assert (actual["per_cell_release"] > 2**-14).all()
        assert (actual["per_cell_release"] < 2**32).all()
        assert actual["pooled_release"].sum(axis=0).max() < 2**43
        assert actual["per_cell_release"][-1, 0] > 1000


@pytest.mark.parametrize("seed", [2, 13, 97])
def test_oracle_catches_body_channel_or_shared_state_permutation_error(seed):
    spikes, compartments = fixture(101)
    rng = np.random.default_rng(seed)
    spikes[:] = rng.random(spikes.shape) < 0.12
    perm = rng.permutation(24)
    expected = reference_events(spikes[:, perm], compartments[perm])
    actual = release_events(spikes[:, perm], compartments[perm])
    compare(actual, expected)
    base = reference_events(spikes, compartments)
    np.testing.assert_allclose(expected["pooled_release"], base["pooled_release"], atol=ATOL, rtol=RTOL)
    np.testing.assert_array_equal(expected["state_before"], base["state_before"][:, perm])


def test_cell_before_pool_distinction_has_independent_two_event_value():
    same, compartments = fixture(12)
    different = same.copy()
    same[[0, 11], 0] = 1
    different[0, 0] = different[11, 1] = 1
    np.testing.assert_array_equal(same.sum(1), different.sum(1))
    a, b = reference_events(same, compartments), reference_events(different, compartments)
    want = math.prod(1 + float(p) * math.exp(-11 / 5000 / float(tau)) for p, tau in PARAMS) / 2
    assert a["pooled_release"][11, 0] == pytest.approx(want, abs=2e-15)
    assert b["pooled_release"][11, 0] == 0.5 and want > 0.5
    compare(release_events(same, compartments), a)
    compare(release_events(different, compartments), b)


def test_reset_pre_onset_history_and_complete_endpoint_are_distinct():
    spikes, compartments = fixture(501)
    spikes[[0, 500], 0] = 1
    full = reference_events(spikes, compartments)
    only = spikes.copy()
    only[0] = 0
    rested = reference_events(only, compartments)
    assert full["per_cell_release"][500, 0] > rested["per_cell_release"][500, 0] == 1
    compare(release_events(spikes, compartments), full)
    compare(release_events(only, compartments), rested)
    assert 1 < full["endpoint_state"][0, 0] < full["state_after"][-1, 0, 0]
    compare(release_events(spikes, compartments), full)


@pytest.mark.parametrize("events", [[-1], [3], [1, 1], [2, 1], [True], [1.0]])
def test_scalar_oracle_refuses_ambiguous_event_identity(events):
    with pytest.raises(ValueError):
        scalar_reference(3, events)
