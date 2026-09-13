"""Synthetic audit of pinned primary code, not a BET36FLY learning candidate.

The source's fixed-step choices are preserved. These tests prevent treating
them as continuous receptor kinetics or as an endogenous-DAN neutrality proof.
"""

import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


SOURCE = Path(__file__).parent / 'kc-lateral-primary-source-2026-09-13' / 'upstream' / 'codes'


def definitions(name, blob, namespace):
    raw = (SOURCE / name).read_bytes()
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == blob
    tree = ast.parse(raw, filename=name)
    # Read and execute only the inspected function definitions. The source's
    # plotting, optimization, file-writing and network entrypoints never run.
    assert all(isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)) for node in tree.body)
    functions = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)], type_ignores=[])
    exec(compile(functions, name, 'exec'), namespace)
    return SimpleNamespace(**namespace)


@pytest.fixture(scope='module')
def source():
    core = definitions('KC_population_calcium_rate_model_functions.py',
                       'dd9df93bd1d1656f934f3258bd1694d9322e5778', {'np': np})
    fit = definitions('fit_functions.py', 'a6aa50641bdcbc72b6599895d62899a0ed9267bd',
                      {'np': np, 'mdl': core})
    return core, fit


@pytest.mark.parametrize('factor', [.1, .5, .9, .99, 1.])
@pytest.mark.parametrize('dt', [.0002, 1 / 30])
@pytest.mark.parametrize('tau', [.5, 1.5])
def test_full_stored_state_recurrence_matches_independent_geometric_sum(source, factor, dt, tau):
    core, _ = source
    forcing, initial, steps = 2.3, .7, 200
    value = initial
    for _ in range(steps):
        value = core.inhibition_dynamics(value, forcing, tau, 1., dt) * factor
    ratio = factor * (1 - dt / tau)
    increment = factor * dt / tau * forcing
    expected = initial * ratio**steps + increment * (1 - ratio**steps) / (1 - ratio)
    assert value == pytest.approx(expected, rel=2e-12, abs=2e-13)


@pytest.mark.parametrize('factor', [.1, .5, .9, .99])
@pytest.mark.parametrize('tau', [.5, 1.5])
def test_fixed_source_multiplier_has_no_nonzero_continuous_equilibrium_limit(source, factor, tau):
    core, _ = source
    forcing = 2.3
    equilibria = []
    for dt in (1 / 30, .0002, .000002):
        fixed = factor * (dt / tau) * forcing / (1 - factor + factor * dt / tau)
        assert core.inhibition_dynamics(fixed, forcing, tau, 1., dt) * factor == pytest.approx(fixed)
        equilibria.append(fixed)
    assert equilibria[0] > equilibria[1] > equilibria[2] > 0
    assert equilibria[2] < .0005 * forcing


@pytest.mark.parametrize('dt', [.0002, 1 / 30])
def test_unmodulated_equilibrium_is_timestep_independent(source, dt):
    core, _ = source
    assert core.inhibition_dynamics(2.3, 2.3, 1.5, 1., dt) == pytest.approx(2.3)


@pytest.mark.parametrize('baseline', [.1, .4, 1.])
@pytest.mark.parametrize('dt', [.0002, 1 / 30])
def test_actual_wt_loop_modulates_stored_history_and_uses_previous_state(source, baseline, dt):
    core, fit = source
    tau, factor = 1.5, 2.
    inflection, slope = .5, .2
    _, _, _, inhibition = fit.simulate_WT_model(
        np.arange(3) * dt, np.zeros(3), [tau, factor, inflection, slope],
        [1., 1., 1., 0., baseline], np.zeros(2), dt, 2)
    # No forcing/adaptation changes either calcium array on the first step;
    # the second inhibition step therefore has the same calcium and sigmoid.
    modulation = core.activity_dependent_inhibition_modulation_sigmoidal(baseline, inflection, slope)
    first = modulation * dt / tau * factor * baseline
    second = modulation * ((1 - dt / tau) * first + dt / tau * factor * baseline)
    np.testing.assert_allclose(inhibition[1], [first, first], rtol=2e-14)
    np.testing.assert_allclose(inhibition[2], [second, second], rtol=2e-14)
    output_only = (1 - dt / tau) * first + modulation * dt / tau * factor * baseline
    assert not np.isclose(second, output_only, rtol=1e-8, atol=1e-14)


@pytest.mark.parametrize('inflection,slope', [(.5, .03), (1., .2), (.1, .01)])
def test_modulation_is_a_decreasing_calcium_gate_not_a_voltage_calibration(source, inflection, slope):
    core, _ = source
    calcium = inflection + slope * np.array([-10., -1., 0., 1., 10.])
    values = core.activity_dependent_inhibition_modulation_sigmoidal(calcium, inflection, slope)
    assert np.all(np.diff(values) < 0)
    assert np.all((0 < values) & (values < 1))
    assert values[2] == .5
    np.testing.assert_allclose(values + values[::-1], 1., rtol=0, atol=3e-16)


@pytest.mark.parametrize('prediction', [-3., -1., 0., 1., 3.])
@pytest.mark.parametrize('dt', [.0002, 1 / 30])
def test_cold_no_shock_cannot_generate_dopamine_from_prediction_error(source, prediction, dt):
    core, _ = source
    dopamine, weight = 0., 1.
    for _ in range(20):
        dopamine = core.DAN_dynamics(dopamine, 1., dt, shock=0., valpred=prediction)
        weight = core.KC_MBON_coincidence_based_weight_change(weight, .7, dopamine, dt)
    assert dopamine == 0.
    assert weight == 1.


@pytest.mark.parametrize('initial', [.2, 1., 3.])
def test_no_shock_retains_decay_of_previously_evoked_dopamine(source, initial):
    core, _ = source
    dt, tau = 1 / 30, .5
    dopamine = core.DAN_dynamics(initial, tau, dt, shock=0., valpred=-2.)
    assert dopamine == pytest.approx(initial * (1 - dt / tau))
    assert core.KC_MBON_coincidence_based_weight_change(1., .7, dopamine, dt) < 1.


@pytest.mark.parametrize('calcium,dopamine', [(0., 1.), (1., 0.), (.2, .4), (1., 1.), (3., 2.)])
def test_source_weight_rule_is_depression_only_and_lower_clipped(source, calcium, dopamine):
    core, _ = source
    before, eta, dt = .3, 2., .1
    actual = core.KC_MBON_coincidence_based_weight_change(before, calcium, dopamine, dt, eta)
    assert actual == pytest.approx(max(0., before - eta * calcium * dopamine * dt))
    assert 0 <= actual <= before
