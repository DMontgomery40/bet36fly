"""Bounded direct-SciPy re-fit of the pinned external noiseless source objective.

Import is inert. Only the explicit CLI/run_calibration entry point fits data.
This is not an identical reproduction of lmfit's optimizer or a MaleCNS run.
"""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import scipy
from scipy.optimize import curve_fit, minimize
from scipy.special import expit


COMMIT = "f0ee2079dae6761cc2d07f04e96e76e2654b6e3c"
WORKBOOK_SHA = "f92ab807009e2e8160fbc8c6c100731012052843484de6c796c7faf673712a1d"
INVENTORY_SHA = "af1109cad767745802ff4fae62088e4c49e9eb05b5c9d68f013c2c7aa968f166"
DEFAULT_SOURCE = Path(__file__).resolve().parents[3] / (
    "docs/evidence/reward-mechanism-repair-2026-09-12/kc-lateral-primary-source-2026-09-13"
)
KD_NAMES = ("tauKCdec", "tauinp", "tauadapt", "adaptscale")
WT_NAMES = ("tauinh", "inhfactor", "infp", "slf")
LBFGSB_OPTIONS = {"ftol": 2.220446049250313e-9, "gtol": 1e-5, "eps": 1e-8, "maxls": 20}


def _vector(value, name):
    raw = np.asarray(value)
    if raw.dtype.kind not in "fiu" or raw.ndim != 1:
        raise ValueError(f"{name} must be a real numeric vector")
    result = raw.astype(np.float64, copy=False)
    if not np.isfinite(result).all():
        raise ValueError(f"{name} must be finite")
    return result


def _data(stimulus, inputs, data=None, se=None):
    stimulus, inputs = _vector(stimulus, "stimulus"), _vector(inputs, "inputs")
    if len(stimulus) < 2 or len(inputs) < 2 or (inputs < 0).any() or not (inputs > 0).any():
        raise ValueError("Need multiple samples/units and nonnegative, partly active inputs")
    if (stimulus < 0).any():
        raise ValueError("Stimulus must be nonnegative")
    if data is not None:
        data, se = _vector(data, "data"), _vector(se, "se")
        if data.shape != stimulus.shape or se.shape != stimulus.shape or (se <= 0).any():
            raise ValueError("Data and positive SE must match stimulus samples")
    return stimulus, inputs, data, se


def simulate(stimulus, inputs, kd, wt=None, *, dt=1 / 30, retain=False, check=None):
    """Exact source update ordering; O(N) uniform-neighbor sum, no noise.

    Retaining all states is for independent synthetic comparison. The fitter
    keeps only the mean of source-defined nonzero-input units.
    """
    stimulus, inputs, _, _ = _data(stimulus, inputs)
    kd = _vector(kd, "KD parameters")
    if kd.shape != (5,) or (kd[:3] <= 0).any() or (kd[3:] < 0).any():
        raise ValueError("Invalid KD parameter domain; no parameter floor is applied")
    if type(dt) not in (float, int) or not np.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be positive and finite")
    if wt is not None:
        wt = _vector(wt, "WT parameters")
        if wt.shape != (4,) or wt[0] <= 0 or wt[1] < 0 or (wt[2:] < 1e-5).any():
            raise ValueError("Invalid WT parameter domain")
    tau_c, tau_input, tau_adapt, adapt_scale, baseline = kd
    n, steps = len(inputs), len(stimulus)
    active = inputs > 0
    calyx = np.full(n, baseline)
    axon = calyx.copy()
    adaptation, inhibition = np.zeros(n), np.zeros(n)
    result = {"mean": np.empty(steps)}
    if retain:
        for name in ("calyx", "axon", "adaptation", "inhibition"):
            result[name] = np.empty((steps, n))

    def record(index):
        result["mean"][index] = axon[active].mean()
        if retain:
            for name, value in (
                ("calyx", calyx),
                ("axon", axon),
                ("adaptation", adaptation),
                ("inhibition", inhibition),
            ):
                result[name][index] = value

    record(0)
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        for index in range(steps - 1):
            if check is not None and index % 32 == 0:
                check()
            forcing = inputs * stimulus[index] / tau_input
            new_calyx = calyx + (forcing - (calyx - baseline) / tau_c) * dt
            new_calyx -= adaptation * calyx / tau_c * dt
            new_adaptation = adaptation + (adapt_scale * calyx - adaptation) / tau_adapt * dt
            if wt is None:
                new_axon, new_inhibition = new_calyx, inhibition
            else:
                tau_inh, factor, inflection, slope = wt
                neighbors = factor * (axon.sum() - axon) / (n - 1)
                new_inhibition = inhibition + (neighbors - inhibition) / tau_inh * dt
                new_inhibition *= expit((inflection - axon) / slope)
                new_axon = axon + (forcing - (axon - baseline) / tau_c) * dt
                new_axon -= adaptation * axon / tau_c * dt
                new_axon -= inhibition / tau_c * dt
            calyx, axon = np.maximum(new_calyx, 0), np.maximum(new_axon, 0)
            adaptation, inhibition = new_adaptation, new_inhibition
            record(index + 1)
    if not all(np.isfinite(value).all() for value in result.values()):
        raise FloatingPointError("Nonfinite source-model trajectory")
    return result


def objective(theta, stimulus, inputs, data, se, *, kd=None, penalty=3.885, check=None):
    """SE-weighted scalar sum of squares + the source stage's L1 penalty."""
    stimulus, inputs, data, se = _data(stimulus, inputs, data, se)
    if not np.isfinite(penalty) or penalty < 0:
        raise ValueError("Invalid penalty")
    try:
        theta = _vector(theta, "parameters")
        if theta.shape != (4,):
            return float("inf")
        shared = np.r_[theta, 0.0] if kd is None else kd
        mean = simulate(stimulus, inputs, shared, None if kd is None else theta, check=check)["mean"]
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            value = float(np.sum(((mean - data) / se) ** 2) + penalty * np.abs(theta).sum())
        return value if np.isfinite(value) else float("inf")
    except (ValueError, FloatingPointError):
        return float("inf")


def source_population():
    rng = np.random.default_rng(666)
    reliable = rng.choice(np.arange(700), 35, replace=False)
    unreliable = rng.choice(np.setdiff1d(np.arange(700), reliable), 105, replace=False)
    inputs = np.zeros(700)
    inputs[reliable] = rng.uniform(0.5, 1.0, len(reliable))
    inputs[unreliable] = rng.uniform(0.0, 0.5, len(unreliable))
    return inputs


def source_schedule(count):
    if type(count) is not int or count < 260:
        raise ValueError("Insufficient source samples")
    observed = np.arange(0, count / 30, 1 / 30)
    dt = observed[1] - observed[0]
    source_time = np.round(np.arange(0, observed[-1] + dt, dt), int(np.ceil(-np.log10(dt))))
    stimulus = np.zeros(source_time.shape)
    stimulus[(source_time >= 3.6) & (source_time <= 8.6)] = 1.0
    if source_time[-1] > observed[-1]:
        source_time, stimulus = source_time[:-1], stimulus[:-1]
    if len(source_time) != count or len(observed) != count:
        raise ValueError("Source time construction changed sample count")
    return observed, source_time, stimulus, source_time <= 8.6, observed >= 8.6


def parse_inventory(value):
    try:
        if value["sha256"] != WORKBOOK_SHA or value["whole_workbook_read"] is not True:
            raise ValueError("Wrong workbook binding")
        sheets = value["sheets"]
        if not isinstance(sheets, list) or len(sheets) != 1:
            raise ValueError("Expected one sheet")
        sheet = sheets[0]
        if (
            sheet["name"] != "Sheet1"
            or sheet["row_count"] != 501
            or sheet["column_count"] != 4
            or sheet["numeric_cells"] != 1996
            or sheet["formula_cells"] != []
        ):
            raise ValueError("Wrong inventory dimensions")
        rows = sheet["rows"]
        if len(rows) != 501 or rows[:2] != [["WT", None, "KD", None], ["Mean", "SE", "Mean", "SE"]]:
            raise ValueError("Wrong worksheet headers or row count")
        if any(not isinstance(row, list) or len(row) != 4 for row in rows[2:]):
            raise ValueError("Wrong numeric shape")
        if any(type(cell) not in (int, float) for row in rows[2:] for cell in row):
            raise ValueError("Non-numeric worksheet cell")
        array = np.array(rows[2:], dtype=np.float64)
        if not np.isfinite(array).all() or (array[:, [1, 3]] <= 0).any():
            raise ValueError("Nonfinite values or nonpositive standard errors")
        return array
    except (KeyError, TypeError, IndexError) as exc:
        raise ValueError("Malformed source inventory") from exc


def load_inputs(source=DEFAULT_SOURCE):
    source = Path(source)
    bindings, contents = [], {}
    for relative, size, expected in (
        ("calcium-workbook-inventory.json", 69141, INVENTORY_SHA),
        ("upstream/data/gamma_mch_responses_manoim_supplement.xlsx", 28573, WORKBOOK_SHA),
    ):
        path = source / relative
        if path.stat().st_size != size:
            raise ValueError("Bound source file size changed")
        raw = path.read_bytes()
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Bound source file hash changed")
        bindings.append({"path": str(path), "bytes": size, "sha256": expected})
        contents[relative] = raw
    inventory = json.loads(contents["calcium-workbook-inventory.json"])
    return {"rows": parse_inventory(inventory), "bindings": bindings}


def decay_problem(time_axis, data, mask):
    time_axis, data = _vector(time_axis, "time"), _vector(data, "data")
    mask = np.asarray(mask)
    if time_axis.shape != data.shape or mask.dtype != np.bool_ or mask.shape != data.shape or not mask.any():
        raise ValueError("Invalid decay selection")
    segment, selected_time = data[mask], time_axis[mask]
    peak = int(np.argmax(segment))
    x, y = selected_time[peak:] - selected_time[peak], segment[peak:]
    if len(x) < 3 or y[0] <= 0:
        raise ValueError("Insufficient positive post-offset decay")
    return x, y, np.array([1.5, y[0], 0.0])


class BudgetExceeded(RuntimeError):
    pass


class Guard:
    def __init__(self, *, maxfun=3000, seconds=120.0, clock=time.monotonic):
        if type(maxfun) is not int or not 1 <= maxfun <= 3000 or not 0 < seconds <= 120:
            raise ValueError("Invalid fixed study caps")
        self.maxfun, self.seconds, self.clock = maxfun, seconds, clock
        self.started, self.stage, self.calls = clock(), None, 0

    def check(self):
        if self.clock() - self.started >= self.seconds:
            raise BudgetExceeded("120-second whole-process internal guard reached")

    def start_stage(self, stage):
        self.check()
        self.stage, self.calls = stage, 0

    def evaluation(self):
        self.check()
        if self.calls >= self.maxfun:
            raise BudgetExceeded(f"{self.stage} objective-evaluation cap reached")
        self.calls += 1


def _persist(directory, state):
    payload = json.dumps(state, indent=2, allow_nan=False) + "\n"
    temporary = directory / "status.pending"
    with temporary.open("w") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(directory / "status.json")
    with (directory / "events.jsonl").open("a") as stream:
        stream.write(
            json.dumps(
                {
                    "status": state["status"],
                    "stage": state.get("stage"),
                    "elapsed_seconds": state["elapsed_seconds"],
                    "stage_evaluations": state.get("stage_evaluations", 0),
                },
                allow_nan=False,
            )
            + "\n"
        )
        stream.flush()
        os.fsync(stream.fileno())


def run_calibration(output, *, maxfun=3000, maxiter=500, seconds=120.0):
    """Explicit run entry; caller must additionally apply a hard process timeout."""
    if type(maxiter) is not int or not 1 <= maxiter <= 500:
        raise ValueError("maxiter exceeds frozen cap")
    guard = Guard(maxfun=maxfun, seconds=seconds)
    directory = Path(output)
    directory.mkdir(exist_ok=False)
    state = {
        "schema": "external-kc-calcium-scipy-refit-v1",
        "status": "running",
        "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_commit": COMMIT,
        "optimizer_reproduction": "direct physical-coordinate source-objective re-fit",
        "versions": {"python": sys.version, "numpy": np.__version__, "scipy": scipy.__version__},
        "settings": {
            "maxfun_per_stage": maxfun,
            "maxiter": maxiter,
            "seconds": seconds,
            "seed": 666,
            "dt_seconds": 1 / 30,
            "penalty": 3.885,
            "method": "L-BFGS-B",
            "options": LBFGSB_OPTIONS,
        },
        "stages": [],
        "stage": "input_validation",
        "elapsed_seconds": 0.0,
    }

    def persist():
        state["elapsed_seconds"] = guard.clock() - guard.started
        state["stage_evaluations"] = guard.calls
        _persist(directory, state)

    try:
        persist()
        inputs = load_inputs()
        guard.check()
        state["input_bindings"] = inputs["bindings"]
        rows = inputs["rows"]
        observed, source_time, stimulus, fit_mask, decay_mask = source_schedule(len(rows))
        population = source_population()
        state["population_sha256"] = hashlib.sha256(population.astype("<f8").tobytes()).hexdigest()
        guard.start_stage("decay_initialization")
        state["stage"] = guard.stage
        persist()
        decay_parameters = []
        for label, column in (("KD", 2), ("WT", 0)):
            x, y, initial = decay_problem(observed, rows[:, column], decay_mask)

            def exponential(times, tau, amplitude, offset):
                guard.evaluation()
                if guard.calls % 50 == 0:
                    persist()
                if tau <= 0:
                    return np.full_like(times, np.inf)
                return amplitude * np.exp(-times / tau) + offset

            fitted, covariance, info, message, flag = curve_fit(
                exponential,
                x,
                y,
                p0=initial,
                bounds=(0.0, np.inf),
                method="trf",
                max_nfev=maxfun,
                full_output=True,
            )
            guard.check()
            if flag not in (1, 2, 3, 4) or not np.isfinite(fitted).all() or fitted[0] <= 0:
                raise RuntimeError("Decay initialization did not converge to finite parameters")
            decay_parameters.append(fitted)
            state["stages"].append(
                {
                    "stage": "decay_initialization",
                    "population": label,
                    "parameters": fitted.tolist(),
                    "initial": initial.tolist(),
                    "success": True,
                    "solver_status": int(flag),
                    "message": str(message),
                    "nfev_reported": int(info.get("nfev", 0)),
                    "points": len(x),
                }
            )
            persist()
        kd_initial = np.array([np.mean([p[0] for p in decay_parameters]), 0.2, 2.0, 1.0])
        fit_stimulus = stimulus[fit_mask]
        fitted_stages = {}
        for label, initial, column, bounds in (
            ("KD", kd_initial, 2, [(0.0, None)] * 4),
            (
                "WT",
                np.array([1.5, 15.0, 0.5, 0.03]),
                0,
                [(0.0, None), (0.0, None), (1e-5, None), (1e-5, None)],
            ),
        ):
            guard.start_stage(label)
            state["stage"] = label
            state["stage_initial"] = initial.tolist()
            persist()
            fixed_kd = None if label == "KD" else np.r_[fitted_stages["KD"], 0.0]

            def loss(theta):
                guard.evaluation()
                value = objective(
                    theta,
                    fit_stimulus,
                    population,
                    rows[fit_mask, column],
                    rows[fit_mask, column + 1],
                    kd=fixed_kd,
                    check=guard.check,
                )
                parameters_finite = bool(np.isfinite(theta).all())
                state["last_evaluation"] = {
                    "parameters": np.asarray(theta).tolist() if parameters_finite else None,
                    "parameters_finite": parameters_finite,
                    "value": value if np.isfinite(value) else None,
                    "finite": bool(np.isfinite(value)),
                }
                if guard.calls % 50 == 0:
                    persist()
                return value

            result = minimize(
                loss,
                initial,
                method="L-BFGS-B",
                bounds=bounds,
                options={**LBFGSB_OPTIONS, "maxfun": maxfun, "maxiter": maxiter},
            )
            guard.check()
            finite = np.isfinite(result.x).all() and np.isfinite(result.fun)
            valid_domain = len(result.x) == 4 and all(
                result.x[i] >= lower for i, (lower, _) in enumerate(bounds)
            )
            stage = {
                "stage": label,
                "parameters": np.asarray(result.x).tolist() if finite else None,
                "objective": float(result.fun) if finite else None,
                "success": bool(result.success),
                "solver_status": int(result.status),
                "message": str(result.message),
                "nfev_reported": int(result.nfev),
                "actual_objective_calls": guard.calls,
                "iterations": int(result.nit),
                "initial": initial.tolist(),
                "bounds": bounds,
            }
            state["stages"].append(stage)
            persist()
            if not result.success or result.status != 0 or not finite or not valid_domain:
                raise RuntimeError(f"{label} optimizer did not converge within declared bounds/caps")
            fitted_stages[label] = np.array(result.x, copy=True)
        guard.check()
        kd = np.r_[fitted_stages["KD"], 0.0]
        wt = fitted_stages["WT"]
        kd_mean = simulate(fit_stimulus, population, kd, check=guard.check)["mean"]
        wt_mean = simulate(fit_stimulus, population, kd, wt, check=guard.check)["mean"]
        guard.check()
        with (directory / "calibration.npz").open("xb") as stream:
            np.savez(
                stream,
                time=observed,
                source_time=source_time,
                stimulus=stimulus,
                fit_mask=fit_mask,
                decay_mask=decay_mask,
                population=population,
                data=rows,
                kd_parameters=kd,
                wt_parameters=wt,
                kd_fit_mean=kd_mean,
                wt_fit_mean=wt_mean,
            )
        state["parameters"] = {
            "KD": dict(zip(KD_NAMES, fitted_stages["KD"].tolist(), strict=True)),
            "WT": dict(zip(WT_NAMES, wt.tolist(), strict=True)),
            "bline": 0.0,
        }
        state["stage"] = "final_source_recheck"
        load_inputs()  # Rehash both consumed inputs before declaring completion.
        guard.check()
        state["status"] = "completed"
        persist()
        guard.check()  # Final persistence time remains inside the total budget.
    except Exception as exc:
        state["status"] = "failed"
        state["error"] = {"type": type(exc).__name__, "message": str(exc)}
        persist()
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--maxfun", type=int, default=3000)
    parser.add_argument("--maxiter", type=int, default=500)
    args = parser.parse_args()
    result = run_calibration(args.output, maxfun=args.maxfun, maxiter=args.maxiter)
    print(
        json.dumps(
            {
                "status": result["status"],
                "stage": result.get("stage"),
                "elapsed_seconds": result["elapsed_seconds"],
            },
            allow_nan=False,
        )
    )
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
