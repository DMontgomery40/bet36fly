# SPDX-License-Identifier: GPL-3.0-or-later
"""Independent synthetic checks; never execute the six published protocols."""

import importlib
import json
from pathlib import Path

import numpy as np
import pytest


def audit():
    assert Path(__file__).with_name("audit_incentive_handler.py").is_file(), "Audit helper is not implemented"
    return importlib.import_module("audit_incentive_handler")


@pytest.mark.parametrize("tau", [1.0, 2.0, 8.0, 60.0, 104.0])
@pytest.mark.parametrize("kind", ["impulse", "step", "rectangle"])
def test_unclipped_filters_follow_analytic_impulse_step_and_dc_gain(tau, kind):
    a = audit()
    n = 4000
    us = np.zeros(n)
    us[1 : (2 if kind == "impulse" else 31 if kind == "rectangle" else n)] = 1
    r = a.scalar_events(np.zeros(n), us, taus=(4.0, tau, tau))
    gamma = 1 - 1 / tau
    t = np.arange(n - 1)
    if kind == "impulse":
        expected = (1 / tau) * gamma**t
    else:
        expected = 1 - gamma ** (t + 1)
        if kind == "rectangle":
            expected[30:] = (1 - gamma**30) * gamma ** np.arange(1, n - 30)
    np.testing.assert_allclose(r["d1"][1:], expected, atol=2e-14, rtol=2e-13)
    np.testing.assert_array_equal(r["d1"], r["d2"])
    np.testing.assert_array_equal(r["internal_w"], 1)
    if kind != "step":
        assert r["d1"].sum() == pytest.approx(us.sum(), abs=2e-12)


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("taus", [(2.0, 3.0, 7.0), (100 / 3, 60.0, 104.0), (1.0, 1.0, 2.0)])
def test_every_authored_state_matches_independent_scalar_for_synthetic_history(seed, taus):
    a = audit()
    rng = np.random.default_rng(seed)
    cs, us = rng.integers(0, 5, (2, 83)).astype(float)
    expected = a.scalar_events(cs, us, taus=taus)
    actual = a.source_events(cs, us, taus=taus)
    for key in expected:
        np.testing.assert_allclose(actual[key], expected[key], atol=1e-12, rtol=1e-12, err_msg=key)


def test_source_first_sample_old_mbon_and_unclipped_internal_weight_are_distinct():
    a = audit()
    r = a.scalar_events([1, 0, 0], [0, 1, 0], taus=(2, 2, 4))
    # At n1 current MBON=.5, but prior MBON=1 makes DAN drive zero.
    np.testing.assert_array_equal(r["k"], [1, 0.5, 0.25])
    np.testing.assert_array_equal(r["d1"], [0, 0, 0])
    np.testing.assert_array_equal(r["d2"], [0, 0, 0])
    r = a.scalar_events([2, 2, 0, 0], [0, 5, 0, 0], taus=(1, 1, 104))
    assert r["internal_w"][1] < 0
    assert r["w"][1] == 0
    assert r["internal_w"][2] < 0
    assert r["m"][2] == 0
    s = a.source_events([2, 2, 0, 0], [0, 5, 0, 0], taus=(1, 1, 104))
    np.testing.assert_allclose(s["internal_w"], r["internal_w"], atol=1e-12)


@pytest.mark.parametrize("w0", [-1.0, 0.2, 1.0, 1.8, 3.0])
@pytest.mark.parametrize("delta", [-0.25, 0.0, 0.2])
def test_dan_only_rule_has_exact_affine_iteration_and_zero_factor_invariants(w0, delta):
    a = audit()
    source = a.load_source()
    w = w0
    for _ in range(12):
        w += source.dopaminergic_plasticity_rule(0.0, max(-delta, 0), max(delta, 0), w, 1.0)
    assert w == pytest.approx(1 + (w0 - 1) * (1 + delta) ** 12, abs=1e-12)


def test_biphasic_filter_full_tail_is_zero_but_euler_passive_product_is_not():
    a = audit()
    n = 5000
    us = np.zeros(n + 1)
    us[1] = 1
    r = a.scalar_events(np.zeros(n + 1), us)
    delta = r["d2"][1:] - r["d1"][1:]
    assert delta[0] < 0 and delta[-1] > 0
    gs, gl = 59 / 60, 103 / 104
    # Finite sum plus closed-form remaining impulse masses is exactly zero analytically.
    tail = gl**n - gs**n
    assert delta.sum() + tail == pytest.approx(0, abs=2e-14)
    assert abs(delta[:50].sum()) > 0.05
    continuous_complete_multiplier = np.exp(0.0)
    euler_log = np.log1p(delta).sum()
    # Remaining logarithm magnitude <= remaining absolute filter mass/(1-max residual).
    tail_bound = (gl**n + gs**n) / (1 - max(gl**n / 104, gs**n / 60))
    assert abs(euler_log) > 1000 * tail_bound
    assert np.exp(euler_log) < continuous_complete_multiplier - 1e-4
    assert 1 + (0.2 - 1) * np.exp(euler_log) > 0.2


def test_source_grid_and_float_endpoint_membership_are_not_resampled():
    a = audit()
    source = a.load_source()
    samples = np.array(list(source.handler_routine(us_on=0.123, us_duration=0.6)))
    expected_time = np.linspace(-7, 8, 1001)
    np.testing.assert_array_equal(samples[:, 0], expected_time)
    assert len(samples) == 1001 and samples[0, 0] == -7 and samples[-1, 0] == 8
    np.testing.assert_allclose(np.diff(samples[:, 0]), 0.015, atol=2e-15, rtol=0)
    np.testing.assert_array_equal(samples[:, 1], (expected_time >= 0) & (expected_time < 0.5))
    # Existing source arithmetic includes the 1.1 endpoint represented just below1.1.
    assert expected_time[540] < 0.5 + 0.6
    assert 15 * 540 - 7000 == 1100


def test_reporter_proxy_uses_post_rectified_weight_and_signed_delta_is_separate():
    a = audit()
    r = a.scalar_events([0, 1, 1, 0, 0], [0, 0, 1, 0, 0], taus=(2, 2, 4))
    eps = np.finfo(float).eps
    signed = r["d2"] - r["d1"]
    up, down = np.maximum(-signed, eps), np.minimum(-signed, -eps)
    expected = (up - down) * (r["k"] + r["w"] - 1)
    np.testing.assert_allclose(-r["dR1"] - r["dR2"], expected, atol=1e-15)
    assert not np.allclose(expected, r["delta_w"])
    np.testing.assert_allclose(r["delta_w"], signed * (r["k"] + r["w_before"] - 1), atol=1e-15)


@pytest.mark.parametrize("bad", [[], [np.nan], [np.inf], [-1.0], [[1.0]], [True]])
def test_scalar_input_domain_rejects_malformed_history(bad):
    with pytest.raises(ValueError):
        audit().scalar_events(bad, [0])


@pytest.mark.parametrize(
    "taus", [(0, 2, 3), (0.5, 2, 3), (np.nan, 2, 3), (2, np.inf, 3), (True, 2, 3), (2, 3)]
)
def test_scalar_tau_domain_rejects_invalid_or_unstable_parameters(taus):
    with pytest.raises(ValueError):
        audit().scalar_events([0, 1], [0, 1], taus=taus)


def test_reporter_window_contrast_is_not_final_weight_or_window_interchange():
    a = audit()
    t = np.linspace(-7, 8, 1001)
    cases = []
    for i, isi in enumerate(a.ISIS):
        cases.append(
            {
                "time": t,
                "dR1": -(i + 1) * (t + 8),
                "dR2": (6 - i) * (t + 9),
                "w": np.ones(1001) * 3,
                "internal_w": np.ones(1001) * 3,
            }
        )
    got = a.reporter_summary(cases)
    er = np.array([(i + 1) * np.mean((t + 8)[(t >= -7) & (t < 1)]) for i in range(6)])
    ca = np.array([(6 - i) * np.mean((t + 9)[(t >= isi) & (t < isi + 4)]) for i, isi in enumerate(a.ISIS)])
    expected = (er - er.min()) / np.ptp(er) - (ca - ca.min()) / np.ptp(ca)
    np.testing.assert_allclose(got["normalized_contrast"], expected, atol=1e-14)
    assert not np.allclose(got["normalized_contrast"], 3)
    assert got["cAMP_window_samples"][-1] < got["cAMP_window_samples"][0]


def test_source_bindings_fail_before_import_on_mutation(tmp_path):
    a = audit()
    import shutil

    shutil.copytree(a.SOURCE, tmp_path / "source")
    (tmp_path / "source" / "src/incentive/handler.py").write_text('raise RuntimeError("executed")')
    with pytest.raises(ValueError, match="Source"):
        a.load_source(tmp_path / "source")


@pytest.mark.parametrize("field", ["k", "internal_w"])
def test_failed_numerical_comparison_retains_observed_reference_and_error_arrays(
    tmp_path, monkeypatch, field
):
    a = audit()
    # Non-published synthetic interval; never call authored run_case here.
    t = np.linspace(-7, 8, 1001)
    cs, us = ((t >= 0) & (t < 0.5)).astype(float), ((t >= 0.123) & (t < 0.723)).astype(float)
    fake = dict(time=t, **a.scalar_events(cs, us))
    fake[field][5] += 0.25
    monkeypatch.setattr(a, "_observed_source", lambda *args: fake.copy())
    compute = a._compute_case
    monkeypatch.setattr(a, "_compute_case", lambda isi: compute(0.123))
    out = tmp_path / "mismatch"
    with pytest.raises(ValueError, match="comparison"):
        a.execute(out)
    status = json.loads((out / "status.json").read_text())
    assert status["status"] == "failed" and status["completed_cases"] == 0
    assert len(status["rows"]) == 1 and status["rows"][0]["passed"] is False
    path = out / status["rows"][0]["file"]
    assert a.sha(path) == status["rows"][0]["sha256"]
    with np.load(path, allow_pickle=False) as z:
        assert z["difference_" + field][5] == 0.25
        assert z[field][5] - z["independent_" + field][5] == 0.25
    assert not (out / "case_01.npz").exists()


@pytest.mark.parametrize("failure", ["case", "case_write", "completion_write", "late_clock"])
def test_execution_failure_preserves_terminal_error_and_never_reports_complete(
    tmp_path, monkeypatch, failure
):
    a = audit()
    monkeypatch.setattr(
        a, "_compute_case", lambda isi: (_ for _ in ()).throw(RuntimeError("synthetic case failure"))
    )
    clock = [0.0]
    if failure != "case":
        t = np.linspace(-7, 8, 1001)

        def fake(isi):
            i = a.ISIS.index(isi)
            return {
                "time": t,
                "dR1": np.ones(1001) * -(i + 1),
                "dR2": np.ones(1001) * (6 - i),
                "w": np.ones(1001),
                "internal_w": np.ones(1001),
            }, {"synthetic": True, "passed": True}

        monkeypatch.setattr(a, "_compute_case", fake)
        original = a._json

        def writer(path, value):
            if (
                failure == "completion_write"
                and path.name == "status.json"
                and value["status"] == "completed"
            ):
                raise OSError("synthetic final persistence failure")
            original(path, value)
            if failure == "late_clock" and path.name == "status.json" and value["status"] == "completed":
                clock[0] = 30.0

        monkeypatch.setattr(a, "_json", writer)
        if failure == "case_write":
            monkeypatch.setattr(
                a, "_npz", lambda *args: (_ for _ in ()).throw(OSError("synthetic array persistence failure"))
            )
    out = tmp_path / "run"
    with pytest.raises((RuntimeError, OSError, TimeoutError)):
        a.execute(out, clock=lambda: clock[0])
    status = json.loads((out / "status.json").read_text())
    assert status["status"] == "failed"
    assert (out / "terminal-error.json").is_file()
    with pytest.raises(FileExistsError):
        a.execute(out)
