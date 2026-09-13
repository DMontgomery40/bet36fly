"""Independent fixed-parameter source audit; never optimizes or imports a driver."""

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import xml.etree.ElementTree as ET
import zipfile

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "output/collaboration/reward-mechanism-repair"
EVIDENCE = ROOT / "docs/evidence/reward-mechanism-repair-2026-09-12"
RUN = BASE / "kc-external-refit-992cef6fb05bfdb63d2b"
SOURCE = EVIDENCE / "kc-lateral-primary-source-2026-09-13"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def binding(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def read_workbook(path):
    """Independent XML parse of this hash-verified four-column source workbook."""
    with zipfile.ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(node.itertext()) for node in root.findall("s:si", NS)]
        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows = [[None] * 4 for _ in range(501)]
        for row in root.findall("s:sheetData/s:row", NS):
            index = int(row.attrib["r"]) - 1
            assert 0 <= index < 501
            for cell in row.findall("s:c", NS):
                reference = cell.attrib["r"]
                assert reference[0] in "ABCD" and reference[1:].isdigit()
                assert cell.find("s:f", NS) is None, "Unexpected workbook formula"
                value_node = cell.find("s:v", NS)
                if value_node is None:
                    value = None
                elif cell.get("t") == "s":
                    value = shared[int(value_node.text)]
                else:
                    value = float(value_node.text)
                rows[index][ord(reference[0]) - ord("A")] = value
    assert rows[:2] == [["WT", None, "KD", None], ["Mean", "SE", "Mean", "SE"]]
    result = np.array(rows[2:], dtype=np.float64)
    assert result.shape == (499, 4) and np.isfinite(result).all()
    assert (result[:, [1, 3]] > 0).all()
    return result


def module_from_verified_bytes(path, name, expected_sha):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected_sha
    module = ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def audit(output):
    directory = Path(output)
    directory.mkdir(exist_ok=False)
    plan = json.loads((RUN / "plan.json").read_text())
    execution = json.loads((RUN / "execution.json").read_text())
    status = json.loads((RUN / "result/status.json").read_text())
    files = {
        RUN / name
        for name in (
            "plan.json",
            "execution.json",
            "result/status.json",
            "result/calibration.npz",
            "result/events.jsonl",
        )
    }
    for record in plan["identity"]["bindings"]:
        path = ROOT / record["path"]
        actual = binding(path)
        assert actual["bytes"] == record["bytes"] and actual["sha256"] == record["sha256"]
        files.add(path)
    downloads = json.loads((SOURCE / "download-receipt.json").read_text())
    for record in downloads["files"]:
        for source in (SOURCE, BASE / "kc-lateral-primary-source-2026-09-13"):
            path = source / "upstream" / record["path"]
            raw = path.read_bytes()
            assert len(raw) == record["bytes"] and hashlib.sha256(raw).hexdigest() == record["sha256"]
            blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            assert blob == record["git_blob_sha"]
            files.add(path)
    before = [binding(path) for path in sorted(files)]
    assert status["status"] == execution["status"] == "completed"
    assert execution["exit_code"] == 0 and execution["no_restart"] is True
    assert execution["elapsed_seconds"] < 120 and status["elapsed_seconds"] < 120
    assert execution["run_id"] == plan["run_id"] == "kc-external-refit-992cef6fb05bfdb63d2b"
    stages = status["stages"]
    assert [stage["stage"] for stage in stages] == [
        "decay_initialization",
        "decay_initialization",
        "KD",
        "WT",
    ]
    for stage in stages:
        assert stage["success"] is True
    for stage in stages[2:]:
        assert stage["solver_status"] == 0
        assert stage["actual_objective_calls"] <= 3000 and stage["iterations"] <= 500
    inventory = json.loads((SOURCE / "calcium-workbook-inventory.json").read_text())
    workbook = SOURCE / "upstream/data/gamma_mch_responses_manoim_supplement.xlsx"
    rows = read_workbook(workbook)
    np.testing.assert_array_equal(rows, np.array(inventory["sheets"][0]["rows"][2:]))
    with np.load(RUN / "result/calibration.npz", allow_pickle=False) as archive:
        expected_names = {
            "time",
            "source_time",
            "stimulus",
            "fit_mask",
            "decay_mask",
            "population",
            "data",
            "kd_parameters",
            "wt_parameters",
            "kd_fit_mean",
            "wt_fit_mean",
        }
        assert set(archive.files) == expected_names
        arrays = {name: archive[name] for name in archive.files}
    np.testing.assert_array_equal(arrays["data"], rows)
    rng = np.random.default_rng(666)
    reliable = rng.choice(np.arange(700), 35, replace=False)
    unreliable = rng.choice(np.setdiff1d(np.arange(700), reliable), 105, replace=False)
    inputs = np.zeros(700)
    inputs[reliable] = rng.uniform(0.5, 1.0, 35)
    inputs[unreliable] = rng.uniform(0.0, 0.5, 105)
    np.testing.assert_array_equal(arrays["population"], inputs)
    assert hashlib.sha256(inputs.astype("<f8").tobytes()).hexdigest() == status["population_sha256"]
    core = module_from_verified_bytes(
        SOURCE / "upstream/codes/KC_population_calcium_rate_model_functions.py",
        "KC_population_calcium_rate_model_functions",
        "bc36f741ab7773b5f9dc298ab9610ce915067a2cc82ea73e947174ee155b3f05",
    )
    fit = module_from_verified_bytes(
        SOURCE / "upstream/codes/fit_functions.py",
        "fit_functions",
        "ca238b5d6acaa40ba7bcee650ab6697872263dd69b1ebc082b27779ae67cbc5b",
    )
    observed = np.arange(0, len(rows) / 30, 1 / 30)
    dt = observed[1] - observed[0]
    time_axis, stimulus = core.generate_step_stimulus(observed[-1], 3.6, 8.6, dt)
    mask, decay_mask = time_axis <= 8.6, observed >= 8.6
    assert mask.sum() == 259
    for name, expected in (
        ("time", observed),
        ("source_time", time_axis),
        ("stimulus", stimulus),
        ("fit_mask", mask),
        ("decay_mask", decay_mask),
    ):
        np.testing.assert_array_equal(arrays[name], expected)
    kd, wt = arrays["kd_parameters"], arrays["wt_parameters"]
    assert kd.shape == (5,) and wt.shape == (4,) and kd[4] == 0
    assert np.isfinite(kd).all() and np.isfinite(wt).all()
    assert (kd[:3] > 0).all() and kd[3] >= 0 and wt[0] > 0 and wt[1] >= 0 and (wt[2:] >= 1e-5).all()
    np.testing.assert_array_equal(kd[:4], stages[2]["parameters"])
    np.testing.assert_array_equal(wt, stages[3]["parameters"])
    for label, vector, names in (
        ("KD", kd[:4], ("tauKCdec", "tauinp", "tauadapt", "adaptscale")),
        ("WT", wt, ("tauinh", "inhfactor", "infp", "slf")),
    ):
        np.testing.assert_array_equal(vector, [status["parameters"][label][name] for name in names])
    assert status["parameters"]["bline"] == 0
    for stage, column in zip(stages[:2], (2, 0), strict=True):
        data_segment, time_segment = rows[decay_mask, column], observed[decay_mask]
        peak = int(data_segment.argmax())
        assert stage["points"] == len(time_segment[peak:])
        np.testing.assert_array_equal(stage["initial"], [1.5, data_segment[peak], 0.0])
        assert stage["solver_status"] in (1, 2, 3, 4)
        assert np.isfinite(stage["parameters"]).all() and np.min(stage["parameters"]) >= 0
    np.testing.assert_array_equal(
        stages[2]["initial"], [np.mean([s["parameters"][0] for s in stages[:2]]), 0.2, 2.0, 1.0]
    )
    np.testing.assert_array_equal(stages[3]["initial"], [1.5, 15.0, 0.5, 0.03])
    kp = {
        name: SimpleNamespace(value=float(value))
        for name, value in zip(("tauKCdec", "tauinp", "tauadapt", "adaptscale", "bline"), kd, strict=True)
    }
    ip = {
        name: SimpleNamespace(value=float(value))
        for name, value in zip(("tauinh", "inhfactor", "infp", "slf"), wt, strict=True)
    }
    kd_calcium, kd_adaptation = fit.simulate_KD_model(time_axis[mask], stimulus[mask], kp, inputs, dt, 700)
    wt_axon, wt_calyx, wt_adaptation, wt_inhibition = fit.simulate_WT_model(
        time_axis[mask], stimulus[mask], ip, kp, inputs, dt, 700
    )
    comparisons = {}
    numeric = {}
    for label, calcium, column, parameters, stage in (
        ("KD", kd_calcium, 2, kp, stages[2]),
        ("WT", wt_axon, 0, ip, stages[3]),
    ):
        mean = calcium[:, inputs > 0].mean(axis=1)
        saved_mean = arrays[label.lower() + "_fit_mean"]
        np.testing.assert_allclose(saved_mean, mean, rtol=2e-12, atol=2e-13)
        residual = mean - rows[mask, column]
        weighted = residual / rows[mask, column + 1]
        squared_error = float(weighted @ weighted)
        penalty = float(3.885 * sum(abs(p.value) for p in parameters.values()))
        source_objective = fit.calculate_residual(
            parameters,
            time_axis[mask],
            stimulus[mask],
            rows[mask, column],
            rows[mask, column + 1],
            inputs,
            kp if label == "WT" else None,
            dt,
            700,
            label == "WT",
            3.885,
        )
        np.testing.assert_allclose(source_objective, squared_error + penalty, rtol=2e-12, atol=2e-12)
        np.testing.assert_allclose(stage["objective"], source_objective, rtol=2e-12, atol=2e-12)
        comparisons[label] = {
            "points": len(mean),
            "units": 700,
            "observed_units": int((inputs > 0).sum()),
            "weighted_squared_error": squared_error,
            "L1_penalty": penalty,
            "total_source_objective": float(source_objective),
            "reported_objective": stage["objective"],
            "objective_absolute_error": abs(float(source_objective) - stage["objective"]),
            "mean_max_absolute_error": float(np.max(np.abs(saved_mean - mean))),
            "weighted_residual_RMS": float(np.sqrt(np.mean(weighted**2))),
            "activity_residual_RMSE": float(np.sqrt(np.mean(residual**2))),
            "max_absolute_weighted_residual": float(np.max(np.abs(weighted))),
        }
        for suffix, values in (
            ("source_mean", mean),
            ("saved_mean", saved_mean),
            ("residual", residual),
            ("weighted_residual", weighted),
        ):
            numeric[label.lower() + "_" + suffix] = values
    admissibility = {
        "finite_nonnegative_parameters": True,
        "positive_time_divisors_and_sigmoid_slope": True,
        "tau_adapt_at_least_source_step": bool(kd[2] >= dt),
        "tau_inh_at_least_source_step": bool(wt[0] >= dt),
        "min_external_KD_A": float(np.min(1 - dt * (1 + kd_adaptation) / kd[0])),
        "min_external_WT_A": float(np.min(1 - dt * (1 + wt_adaptation) / kd[0])),
        "external_WT_L_le_C": bool((wt_axon <= wt_calyx).all()),
        "external_states_nonnegative": bool(
            all(
                (x >= 0).all()
                for x in [kd_calcium, kd_adaptation, wt_axon, wt_calyx, wt_adaptation, wt_inhibition]
            )
        ),
        "scope": "Static fitted-parameter conditions and this external259-sample input only; every future candidate update still requires its own A>=0 and state checks.",
    }
    assert admissibility["tau_adapt_at_least_source_step"] and admissibility["tau_inh_at_least_source_step"]
    assert admissibility["min_external_KD_A"] >= 0 and admissibility["min_external_WT_A"] >= 0
    assert admissibility["external_WT_L_le_C"] and admissibility["external_states_nonnegative"]
    after = [binding(Path(record["path"])) for record in before]
    assert before == after, "Source/run inputs changed during independent audit"
    report = {
        "status": "passed_fixed_parameter_source_reproduction",
        "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "run_id": plan["run_id"],
        "comparisons": comparisons,
        "admissibility": admissibility,
        "input_snapshot": before,
        "all_snapshot_bytes_unchanged": True,
        "source_original_and_copy_files_verified_each": 14,
        "independent_workbook_XML_rows_compared": 499,
        "source_forward_calls": 4,
        "optimizer_calls": 0,
        "gradient_calls": 0,
        "candidate_or_native_calls": 0,
        "solver_report": execution,
        "interpretation": "Reported solver termination and exact source-objective reproduction; neither global optimality nor measured biological calibration is established.",
    }
    with (directory / "comparison.npz").open("xb") as stream:
        np.savez(stream, fit_time=time_axis[mask], **numeric)
    report["numeric_comparison"] = binding(directory / "comparison.npz")
    report["audit_source"] = binding(Path(__file__))
    with (directory / "audit.json").open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {"status": report["status"], "comparisons": comparisons, "admissibility": admissibility}, indent=2
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    audit(parser.parse_args().output)
