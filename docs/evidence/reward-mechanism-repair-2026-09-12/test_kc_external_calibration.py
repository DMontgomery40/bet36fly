"""Synthetic source-objective contracts; never run a numerical optimizer."""

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest


BASE = Path(__file__).resolve().parent
EVIDENCE = Path(__file__).resolve().parents[3] / "docs/evidence/reward-mechanism-repair-2026-09-12"
SOURCE = EVIDENCE / "kc-lateral-primary-source-2026-09-13/upstream"


def helper():
    path = BASE / "kc_external_calibration.py"
    assert path.is_file(), "Calibration helper has not been implemented"
    spec = importlib.util.spec_from_file_location("kc_external_calibration", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def upstream():
    names = {
        "KC_population_calcium_rate_model_functions": "bc36f741ab7773b5f9dc298ab9610ce915067a2cc82ea73e947174ee155b3f05",
        "fit_functions": "ca238b5d6acaa40ba7bcee650ab6697872263dd69b1ebc082b27779ae67cbc5b",
    }
    modules = []
    for name, sha in names.items():
        path = SOURCE / "codes" / (name + ".py")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == sha
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
        modules.append(module)
    return modules


def parameters(names, values):
    return {name: SimpleNamespace(value=float(v)) for name, v in zip(names, values, strict=True)}


@pytest.mark.parametrize("units", [2, 5, 17])
@pytest.mark.parametrize("dt", [1 / 30, 0.01, 0.0002])
@pytest.mark.parametrize("wt", [False, True])
@pytest.mark.parametrize("seed", [37, 93])
def test_all_states_match_actual_upstream_old_state_recurrence(upstream, units, dt, wt, seed):
    h = helper()
    rng = np.random.default_rng(seed)
    inputs = rng.uniform(0, 1, units)
    inputs[0] = 0
    stimulus = np.r_[np.zeros(4), np.ones(23), np.zeros(14)]
    kd = np.array([1.4, 0.23, 0.91, 0.61, 0.0])
    wp = np.array([0.52, 7.2, 0.42, 0.11]) if wt else None
    actual = h.simulate(stimulus, inputs, kd, wp, dt=dt, retain=True)
    kp = parameters(["tauKCdec", "tauinp", "tauadapt", "adaptscale", "bline"], kd)
    t = np.arange(len(stimulus)) * dt
    if wt:
        ip = parameters(["tauinh", "inhfactor", "infp", "slf"], wp)
        lobe, calyx, adapt, inhibition = upstream[1].simulate_WT_model(t, stimulus, ip, kp, inputs, dt, units)
    else:
        calyx, adapt = upstream[1].simulate_KD_model(t, stimulus, kp, inputs, dt, units)
        lobe, inhibition = calyx, np.zeros_like(calyx)
    for field, expected in [
        ("calyx", calyx),
        ("axon", lobe),
        ("adaptation", adapt),
        ("inhibition", inhibition),
    ]:
        np.testing.assert_allclose(actual[field], expected, rtol=2e-12, atol=2e-13)
    np.testing.assert_allclose(actual["mean"], lobe[:, inputs > 0].mean(axis=1), rtol=2e-12, atol=2e-13)
    np.testing.assert_array_equal(h.simulate(stimulus, inputs, kd, wp, dt=dt)["mean"], actual["mean"])


def test_source_population_and_rounded_time_axis(upstream):
    h = helper()
    population = h.source_population()
    assert (
        hashlib.sha256(population.astype("<f8").tobytes()).hexdigest()
        == "98b15e2996a31e8dd69a38d2d6ac163a7657f3b914abdafe77c9c5c2e5b7e5a4"
    )
    time, source_time, stimulus, fit_mask, decay_mask = h.source_schedule(499)
    t, expected = upstream[0].generate_step_stimulus(time[-1], 3.6, 8.6, time[1] - time[0])
    np.testing.assert_array_equal(source_time, t)
    np.testing.assert_array_equal(stimulus, expected)
    np.testing.assert_array_equal(fit_mask, t <= 8.6)
    np.testing.assert_array_equal(decay_mask, time >= 8.6)
    assert (np.flatnonzero(stimulus)[0], np.flatnonzero(stimulus)[-1]) == (108, 258)
    assert fit_mask.sum() == 259
    assert np.count_nonzero(population >= 0.5) == 35
    assert np.count_nonzero((population > 0) & (population < 0.5)) == 105


@pytest.mark.parametrize("wt", [False, True])
@pytest.mark.parametrize("penalty", [0.0, 3.885])
def test_objective_matches_upstream_sem_and_stage_parameter_penalty(upstream, wt, penalty):
    h = helper()
    stimulus = np.r_[0.0, 0.0, np.ones(9), np.zeros(7)]
    inputs = np.array([0.0, 0.1, 0.3, 0.7])
    kd = np.array([1.6, 0.31, 1.2, 0.9, 0.0])
    wp = np.array([0.8, 4.2, 0.3, 0.07])
    data = np.linspace(-0.2, 0.8, len(stimulus))
    se = np.linspace(0.05, 0.25, len(stimulus))
    kp = parameters(["tauKCdec", "tauinp", "tauadapt", "adaptscale", "bline"], kd)
    ip = parameters(["tauinh", "inhfactor", "infp", "slf"], wp)
    expected = upstream[1].calculate_residual(
        ip if wt else kp,
        np.arange(len(stimulus)) / 30,
        stimulus,
        data,
        se,
        inputs,
        kp if wt else None,
        1 / 30,
        len(inputs),
        wt,
        penalty,
    )
    actual = h.objective(
        wp if wt else kd[:4], stimulus, inputs, data, se, kd=kd if wt else None, penalty=penalty
    )
    assert actual == pytest.approx(expected, rel=2e-12, abs=2e-12)


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), float("inf")])
@pytest.mark.parametrize("position", [0, 1, 2])
def test_singular_kd_domains_are_rejected_without_parameter_floor(bad, position):
    h = helper()
    kd = np.array([1.2, 0.3, 0.8, 0.5])
    kd[position] = bad
    assert np.isinf(h.objective(kd, np.ones(5), np.array([0.0, 0.3]), np.zeros(5), np.ones(5)))


@pytest.mark.parametrize("where", ["se", "data", "inputs", "stimulus"])
@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_nonfinite_data_never_reaches_optimizer_objective(where, bad):
    h = helper()
    args = {"stimulus": np.ones(5), "inputs": np.array([0.0, 0.3]), "data": np.zeros(5), "se": np.ones(5)}
    args[where][0] = bad
    with pytest.raises(ValueError):
        h.objective(np.array([1.2, 0.3, 0.8, 0.5]), **args)


def test_actual_workbook_binding_and_complete_numeric_mapping():
    h = helper()
    result = h.load_inputs(EVIDENCE / "kc-lateral-primary-source-2026-09-13")
    assert result["rows"].shape == (499, 4)
    assert result["rows"][0].tolist() == [
        0.00790014285714286,
        0.00313260044147074,
        0.00530388888888889,
        0.00830130615800985,
    ]
    assert np.isfinite(result["rows"]).all()
    assert (result["rows"][:, [1, 3]] > 0).all()


@pytest.mark.parametrize("mutation", ["rows", "headers", "se_zero", "bool", "nan", "shape", "formulas"])
def test_inventory_malformed_numeric_family(mutation):
    h = helper()
    path = EVIDENCE / "kc-lateral-primary-source-2026-09-13/calcium-workbook-inventory.json"
    d = json.loads(path.read_text())
    s = d["sheets"][0]
    if mutation == "rows":
        s["rows"].pop()
    elif mutation == "headers":
        s["rows"][0][0] = "KD"
    elif mutation == "se_zero":
        s["rows"][2][1] = 0.0
    elif mutation == "bool":
        s["rows"][2][0] = True
    elif mutation == "nan":
        s["rows"][2][0] = float("nan")
    elif mutation == "shape":
        s["rows"][2].pop()
    elif mutation == "formulas":
        s["formula_cells"] = ["A3"]
    with pytest.raises(ValueError):
        h.parse_inventory(d)


@pytest.mark.parametrize("which", ["workbook", "inventory"])
def test_bound_input_replacement_rejected_before_calculation(tmp_path, which):
    h = helper()
    source = EVIDENCE / "kc-lateral-primary-source-2026-09-13"
    (tmp_path / "upstream/data").mkdir(parents=True)
    for relative in [
        "calcium-workbook-inventory.json",
        "upstream/data/gamma_mch_responses_manoim_supplement.xlsx",
    ]:
        (tmp_path / relative).write_bytes((source / relative).read_bytes())
    p = tmp_path / (
        "calcium-workbook-inventory.json"
        if which == "inventory"
        else "upstream/data/gamma_mch_responses_manoim_supplement.xlsx"
    )
    p.write_bytes(p.read_bytes() + b" ")
    with pytest.raises(ValueError):
        h.load_inputs(tmp_path)


def test_decay_initializer_selects_each_postoffset_peak_independently():
    h = helper()
    t = np.arange(8.0)
    series = np.array([100.0, 99.0, 5.0, 7.0, 6.0, 9.0, 4.0, 3.0])
    x, y, initial = h.decay_problem(t, series, t >= 2)
    np.testing.assert_array_equal(x, [0.0, 1.0, 2.0])
    np.testing.assert_array_equal(y, [9.0, 4.0, 3.0])
    np.testing.assert_array_equal(initial, [1.5, 9.0, 0.0])


def test_runtime_guard_counts_actual_evaluations_and_preserves_budget():
    h = helper()
    now = [0.0]
    guard = h.Guard(maxfun=3, seconds=120.0, clock=lambda: now[0])
    guard.start_stage("KD")
    for _ in range(3):
        guard.evaluation()
    with pytest.raises(h.BudgetExceeded):
        guard.evaluation()
    assert guard.calls == 3
    now[0] = 120.0
    with pytest.raises(h.BudgetExceeded):
        guard.check()


def test_exclusive_output_prevents_existing_run_reuse(tmp_path):
    h = helper()
    directory = tmp_path / "existing"
    directory.mkdir()
    (directory / "sentinel").write_text("retained")
    with pytest.raises(FileExistsError):
        h.run_calibration(directory)
    assert (directory / "sentinel").read_text() == "retained"


@pytest.mark.parametrize(
    "failed_stage", [None, "KD", "WT", "decay_initialization", "nan_trial", "inf_trial", "negative_inf_trial"]
)
def test_stage_order_bounds_status_and_partial_preservation_without_fitting(
    tmp_path, monkeypatch, failed_stage
):
    h = helper()
    rows = np.tile([0.3, 0.05, 0.5, 0.07], (499, 1))
    monkeypatch.setattr(h, "load_inputs", lambda *_: {"rows": rows, "bindings": []})
    calls = []

    def fake_decay(func, x, y, p0, **kwargs):
        assert kwargs["method"] == "trf"
        assert kwargs["max_nfev"] == 3000
        assert kwargs["bounds"] == (0.0, np.inf)
        assert kwargs["full_output"] is True
        calls.append("decay")
        if failed_stage == "decay_initialization":
            raise RuntimeError("synthetic decay failure")
        return np.array([2.0 if len(calls) == 1 else 4.0, p0[1], 0.0]), np.eye(3), {"nfev": 1}, "synthetic", 1

    def fake_minimize(func, initial, **kwargs):
        stage = "KD" if len(calls) == 2 else "WT"
        calls.append(stage)
        assert kwargs["method"] == "L-BFGS-B"
        assert kwargs["options"]["maxfun"] == 3000
        assert kwargs["options"]["maxiter"] == 500
        if stage == "KD":
            np.testing.assert_array_equal(initial, [3.0, 0.2, 2.0, 1.0])
            assert kwargs["bounds"] == [(0.0, None)] * 4
        else:
            np.testing.assert_array_equal(initial, [1.5, 15.0, 0.5, 0.03])
            assert kwargs["bounds"] == [(0.0, None), (0.0, None), (1e-5, None), (1e-5, None)]
        if failed_stage in ("nan_trial", "inf_trial", "negative_inf_trial"):
            initial = initial.copy()
            initial[0] = {"nan_trial": np.nan, "inf_trial": np.inf, "negative_inf_trial": -np.inf}[
                failed_stage
            ]
        value = func(initial)  # One synthetic objective calculation; no optimizer or real-data fit.
        return SimpleNamespace(
            x=np.array(initial),
            fun=value,
            success=stage != failed_stage,
            status=0 if stage != failed_stage else 1,
            message="synthetic",
            nfev=1,
            nit=0,
        )

    monkeypatch.setattr(h, "curve_fit", fake_decay)
    monkeypatch.setattr(h, "minimize", fake_minimize)
    result = h.run_calibration(tmp_path / "run")
    saved = json.loads((tmp_path / "run/status.json").read_text())
    assert saved["status"] == result["status"] == ("completed" if failed_stage is None else "failed")
    assert (
        calls
        == {
            None: ["decay", "decay", "KD", "WT"],
            "KD": ["decay", "decay", "KD"],
            "WT": ["decay", "decay", "KD", "WT"],
            "decay_initialization": ["decay"],
            "nan_trial": ["decay", "decay", "KD"],
            "inf_trial": ["decay", "decay", "KD"],
            "negative_inf_trial": ["decay", "decay", "KD"],
        }[failed_stage]
    )
    assert (tmp_path / "run/events.jsonl").is_file()
    assert all(json.loads(line) for line in (tmp_path / "run/events.jsonl").read_text().splitlines())
    assert (tmp_path / "run/calibration.npz").is_file() == (failed_stage is None)
