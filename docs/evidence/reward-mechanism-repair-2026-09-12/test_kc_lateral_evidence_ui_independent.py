"""Tiny independent source-semantic fixtures; no fit, driver, native or data run."""

import ast
import hashlib
import math
from pathlib import Path
import socket
from types import SimpleNamespace

import numpy as np
import pytest


SOURCE = Path(__file__).parent / "kc-lateral-primary-source-2026-09-13/upstream/codes"
STEPS = (0.0002, 0.01, 1 / 30)


def load_functions(name, blob, namespace, names):
    raw = (SOURCE / name).read_bytes()
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == blob
    tree = ast.parse(raw)
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in selected} == set(names)
    exec(compile(ast.Module(body=selected, type_ignores=[]), name, "exec"), namespace)
    return SimpleNamespace(**namespace)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network is outside this source-only audit")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


@pytest.fixture(scope="module")
def source():
    core = load_functions(
        "KC_population_calcium_rate_model_functions.py",
        "dd9df93bd1d1656f934f3258bd1694d9322e5778",
        {"np": np},
        [
            "adaptation_dynamics",
            "inhibition_dynamics",
            "activity_dependent_inhibition_modulation_sigmoidal",
            "DAN_dynamics",
            "KC_MBON_coincidence_based_weight_change",
        ],
    )
    fit = load_functions(
        "fit_functions.py",
        "a6aa50641bdcbc72b6599895d62899a0ed9267bd",
        {"np": np, "mdl": core},
        ["simulate_KD_model", "simulate_WT_model"],
    )
    return core, fit


@pytest.mark.parametrize("dt", STEPS)
@pytest.mark.parametrize("permutation", [(0, 1, 2), (1, 2, 0), (2, 0, 1)])
def test_asymmetric_lateral_matrix_maps_presynaptic_column_to_recipient_row(source, dt, permutation):
    core, _ = source
    matrix = np.array([[0, 2, 0.5], [0.2, 0, 3], [5, 0.7, 0]])
    calcium = np.array([0.2, 0.7, 1.3])
    history = np.array([0.4, 0.1, 0.8])
    expected = np.array(
        [
            history[i] + dt / 1.5 * (math.fsum(matrix[i, j] * calcium[j] for j in range(3)) - history[i])
            for i in range(3)
        ]
    )
    p = np.array(permutation)
    observed = core.inhibition_dynamics(history[p], calcium[p], 1.5, matrix[np.ix_(p, p)], dt)
    np.testing.assert_allclose(observed, expected[p], rtol=2e-14, atol=2e-15)
    wrong = history + dt / 1.5 * (matrix.T @ calcium - history)
    assert not np.allclose(expected, wrong, rtol=1e-10, atol=1e-12)


def scalar_wt_reference(stimulus, inputs, noise, dt, adaptation_scale, noise_strength):
    """Independent scalar previous-state update, with explicit neighbor exclusion."""
    n = len(inputs)
    tau_c, tau_input, tau_a, tau_h, b = 0.9, 0.6, 1.7, 1.3, 0.4
    strength, inflection, slope = 1.6, 0.5, 0.15
    cal = [[b] * n]
    axon = [[b] * n]
    adaptation = [[0.0] * n]
    inhibition = [[0.0] * n]
    for t in range(len(stimulus) - 1):
        nc, nl, na, nh = [], [], [], []
        for i in range(n):
            c, ax, a, h = cal[-1][i], axon[-1][i], adaptation[-1][i], inhibition[-1][i]
            forcing = inputs[i] * stimulus[t] / tau_input
            perturbation = noise[t, i] * noise_strength * math.sqrt(2 * dt / tau_c)
            nc.append(max(0.0, c + dt * (forcing - (c - b) / tau_c - a * c / tau_c) + perturbation))
            nl.append(
                max(0.0, ax + dt * (forcing - (ax - b) / tau_c - a * ax / tau_c - h / tau_c) + perturbation)
            )
            na.append(a + dt * (adaptation_scale * c - a) / tau_a)
            neighbor = strength * math.fsum(axon[-1][j] for j in range(n) if j != i) / (n - 1)
            f = 1 / (1 + math.exp((ax - inflection) / slope))
            nh.append(f * (h + dt * (neighbor - h) / tau_h))
        cal.append(nc)
        axon.append(nl)
        adaptation.append(na)
        inhibition.append(nh)
    return tuple(np.array(v) for v in (axon, cal, adaptation, inhibition))


@pytest.mark.parametrize("dt", STEPS)
@pytest.mark.parametrize("n", [2, 3, 5])
@pytest.mark.parametrize("adaptation_scale", [0.0, 0.8])
@pytest.mark.parametrize("noise_strength", [0.0, 0.2])
def test_heterogeneous_wt_retains_separate_regions_old_states_and_normalized_neighbors(
    source,
    dt,
    n,
    adaptation_scale,
    noise_strength,
):
    _, fit = source
    stimulus = np.array([0.5, 1.0, 0.2, 0.0, 0.7, 0.0])
    inputs = np.linspace(0.0, 1.3, n)
    noise = np.arange(5 * n).reshape(5, n) % 3 - 1
    expected = scalar_wt_reference(stimulus, inputs, noise, dt, adaptation_scale, noise_strength)
    actual = fit.simulate_WT_model(
        np.arange(6) * dt,
        stimulus,
        [1.3, 1.6, 0.5, 0.15],
        [0.9, 0.6, 1.7, adaptation_scale, 0.4],
        inputs,
        dt,
        n,
        noise=noise,
        n_str=noise_strength,
    )
    for observed, reference in zip(actual, expected):
        np.testing.assert_allclose(observed, reference, rtol=2e-13, atol=2e-15)
    # Inhibition affects axon calcium after a full step of state delay, not calyx.
    np.testing.assert_array_equal(actual[0][:2], actual[1][:2])
    assert np.any(actual[0][2:] < actual[1][2:])


@pytest.mark.parametrize("dt", STEPS)
@pytest.mark.parametrize("tau", [0.5, 1.7])
@pytest.mark.parametrize("model", ["KD", "WT"])
def test_noisy_demo_prescaling_is_applied_again_by_function_not_by_learning_loop(source, dt, tau, model):
    _, fit = source
    sigma, baseline = 0.2, 0.4
    noise = np.array([[1.0, -1.0]])
    parameters = {
        k: SimpleNamespace(value=v)
        for k, v in zip(("tauKCdec", "tauinp", "tauadapt", "adaptscale", "bline"), (tau, 1, 1, 0, baseline))
    }

    def call(strength):
        if model == "KD":
            return fit.simulate_KD_model(
                [0, dt],
                [0, 0],
                parameters,
                np.zeros(2),
                dt,
                2,
                noise=noise,
                n_str=strength,
            )[0][1]
        return fit.simulate_WT_model(
            [0, dt],
            [0, 0],
            [1, 1, 0.5, 0.2],
            parameters,
            np.zeros(2),
            dt,
            2,
            noise=noise,
            n_str=strength,
        )[0][1]

    factor = math.sqrt(2 * dt / tau)
    once = baseline + noise[0] * sigma * factor
    twice = baseline + noise[0] * sigma * factor**2
    np.testing.assert_allclose(call(sigma), once, rtol=1e-14, atol=1e-16)
    np.testing.assert_allclose(call(sigma * factor), twice, rtol=1e-14, atol=1e-16)
    assert not np.allclose(once, twice, rtol=1e-10, atol=1e-12)


@pytest.mark.parametrize("dt", STEPS)
@pytest.mark.parametrize("initial", [0.0, 0.7])
@pytest.mark.parametrize("shock,prediction", [(0, -3), (0.5, -0.4), (0.5, 0.5), (0.5, 0.8)])
def test_dan_drive_clip_and_learning_old_state_lag_are_distinct_from_cold_neutrality(
    source,
    dt,
    initial,
    shock,
    prediction,
):
    core, _ = source
    tau, calcium, eta = 2.0, 0.7, 0.1
    d, w = initial, 1.0
    expected_d, expected_w = initial, 1.0
    for _ in range(6):
        # Actual learning script passes D[i], not the freshly computed D[i+1].
        w = core.KC_MBON_coincidence_based_weight_change(w, calcium, d, dt, eta)
        d = core.DAN_dynamics(d, tau, dt, shock=shock, valpred=prediction)
        expected_w = max(0.0, expected_w - eta * calcium * expected_d * dt)
        drive = shock - prediction if shock > 0 else 0.0
        expected_d = max(0.0, (1 - dt / tau) * expected_d + dt / tau * drive)
        assert d == pytest.approx(expected_d, rel=2e-13, abs=2e-15)
        assert w == pytest.approx(expected_w, rel=2e-13, abs=2e-15)
    if initial == 0 and (shock == 0 or prediction >= shock):
        assert w == 1.0 and d == 0.0
    else:
        assert w < 1.0


def test_actual_driver_time_scales_and_shock_protocol_are_read_without_execution():
    fitting = ast.parse((SOURCE / "fit_rate_model_to_data.py").read_text())
    learning = ast.parse((SOURCE / "learning_rate_screening_mbon_normalized.py").read_text())

    def assigned(tree, name):
        matches = [
            n.value
            for n in tree.body
            if isinstance(n, ast.Assign)
            and len(n.targets) == 1
            and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id == name
        ]
        assert len(matches) == 1
        return matches[0]

    assert ast.literal_eval(assigned(fitting, "sf")) == 30
    assert ast.literal_eval(assigned(learning, "dt")) == 0.01
    assert ast.literal_eval(assigned(learning, "taudan")) == 2
    assert ast.literal_eval(assigned(learning, "nshocks")) == 12
    assert ast.literal_eval(assigned(learning, "shdur")) == 1.25
    assert ast.literal_eval(assigned(learning, "shint")) == 3.75
    duration = assigned(learning, "stoff")
    assert isinstance(duration, ast.BinOp) and isinstance(duration.op, ast.Add)
    assert isinstance(duration.left, ast.Name) and duration.left.id == "ston"
    assert ast.literal_eval(duration.right) == 60
