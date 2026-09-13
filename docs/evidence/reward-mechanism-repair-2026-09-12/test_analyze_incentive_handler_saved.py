"""Independent saved-data boundaries; no model/source execution."""

import json
from pathlib import Path
import subprocess
import time

import numpy as np
import pytest

import analyze_incentive_handler_saved as a


def test_closed_window_keeps_endpoint_and_partial_window_never_pads():
    t = np.array([0., 1., 2., 3.])
    y = np.array([1., 3., 9., 27.])
    assert a.window(t, y, 0, 1, closed=True)["mean"] == 2
    assert a.window(t, y, 0, 1, closed=False)["mean"] == 1
    p = a.window(t, y, 2, 4, closed=True)
    assert (p["mean"], p["samples"], p["complete"]) == (18, 2, False)
    assert a.window(t, y, -1, 1, closed=True)["complete"] is False
    assert a.window(t, y, 4, 5, closed=True)["mean"] is None


@pytest.mark.parametrize("t,y,lo,hi", [
    ([0, 0], [1, 2], 0, 1), ([1, 0], [1, 2], 0, 1),
    ([0, np.nan], [1, 2], 0, 1), ([0, 1], [1, np.inf], 0, 1),
    ([0, 1], [1], 0, 1), ([], [], 0, 1),
    ([0, 1], [1, 2], 1, 0), ([0, 1], [1, 2], 0, np.inf),
])
def test_bad_window_inputs_fail_closed(t, y, lo, hi):
    with pytest.raises(ValueError):
        a.window(t, y, lo, hi, closed=True)


def test_normalization_is_per_preparation_not_mean_first():
    x = np.array([[0, 0], [1, 100], [2, 100]])
    r = a.normalize(x)
    np.testing.assert_array_equal(r["mean"], [0, .75, 1])
    np.testing.assert_array_equal(r["sem"], [0, .25, 0])
    assert r["mean"][1] != 101 / 102
    np.testing.assert_array_equal(a.normalize(x * [3, 7] + [9, 13])["mean"], r["mean"])


@pytest.mark.parametrize("x", [[[1], [1]], [[1], [np.nan]], [], [[1, 0], [2, 0]]])
def test_bad_or_degenerate_normalization_is_not_fabricated(x):
    with pytest.raises(ValueError):
        a.normalize(x)


def cases():
    t = np.linspace(-7, 8, 1001)
    return [{"isi": isi, "time": t, "dR1": -(i + 1) * (t + 8),
             "dR2": (i + 2) * (t + 8), "internal_w": np.full(t.shape, i + .2),
             "w": np.full(t.shape, i + .3), "delta_w": np.zeros(t.shape)}
            for i, isi in enumerate(a.ISIS)]


def test_primary_plus_six_incomplete_without_five_condition_renormalization():
    r = a.analyze_cases(cases())
    assert r["primary_model"]["normalized_contrast"] is None
    assert r["primary_model"]["correlation"] is None
    assert r["primary_model"]["complete_condition_indices"] == [0, 1, 2, 3, 4]
    last = r["rows"][-1]
    assert not last["primary_cAMP"]["complete"]
    assert last["primary_cAMP"]["requested"] == [6, 10]
    assert last["primary_cAMP"]["last_selected"] == 8
    assert len(r["literal_model"]["normalized_contrast"]) == 6
    assert last["final_internal_w"] != last["final_recorded_w"]


def test_condition_input_order_cannot_change_results():
    assert a.analyze_cases(cases()) == a.analyze_cases(list(reversed(cases())))


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unknown"])
def test_condition_identity_is_complete_unique_and_exact(mutation):
    c = cases()
    if mutation == "missing":
        c.pop()
    elif mutation == "duplicate":
        c[-1] = c[0]
    else:
        c[-1] = dict(c[-1], isi=6.01)
    with pytest.raises(ValueError):
        a.analyze_cases(c)


def saved(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    binding = tmp_path / "bound.txt"
    binding.write_text("fixed")
    identity = {"source": a.SOURCE_HASHES, "bindings": {str(binding): a.sha(binding)},
                "ISIS": a.ISIS, "taus": [100/3, 60., 104.], "samples": 1001,
                "grid": [-7, 8], "cap_seconds": 30., "scope": "authored_source_only"}
    (run / "identity.json").write_text(json.dumps(identity))
    rows = []
    for i, c in enumerate(cases()):
        data = {key: np.zeros(1001, dtype=np.float64) for key in a.ARRAY_FIELDS}
        data.update({k: v for k, v in c.items() if k != "isi"})
        data["cs"] = ((c["time"] >= 0) & (c["time"] < .5)).astype(float)
        data["us"] = ((c["time"] >= c["isi"]) & (c["time"] < c["isi"] + .6)).astype(float)
        f = run / f"case_{i:02d}.npz"
        np.savez_compressed(f, **data)
        rows.append({"index": i, "isi": c["isi"], "file": f.name,
                     "sha256": a.sha(f), "passed": True})
    summary = {"fixture": True}
    (run / "summary.json").write_text(json.dumps(summary))
    (run / "status.json").write_text(json.dumps({"status": "completed", "completed_cases": 6,
        "rows": rows, "wall_seconds": 1., "source_unchanged": True,
        "summary_sha256": a.sha(run / "summary.json")}))
    return run, a.sha(run / "identity.json"), binding


def test_saved_reader_only_reads_arrays_and_binds_every_input(tmp_path):
    run, identity, _ = saved(tmp_path)
    got, summary, hashes = a.read_saved(run, identity)
    assert [x["isi"] for x in got] == a.ISIS
    assert summary == {"fixture": True}
    assert str(run / "case_05.npz") in hashes


@pytest.mark.parametrize("mutation", ["identity", "binding", "array", "summary", "terminal",
    "missing", "failed", "cap", "nan_cap", "duplicate_row", "traversal"])
def test_saved_reader_rejects_invalid_completion_and_content(tmp_path, mutation):
    run, identity, binding = saved(tmp_path)
    status = json.loads((run / "status.json").read_text())
    if mutation == "identity":
        identity = "0" * 64
    elif mutation == "binding":
        binding.write_text("changed")
    elif mutation == "array":
        (run / "case_00.npz").write_bytes(b"bad")
    elif mutation == "summary":
        (run / "summary.json").write_text("{}")
    elif mutation == "terminal":
        (run / "terminal-error.json").write_text("{}")
    elif mutation == "missing":
        (run / "case_05.npz").unlink()
    elif mutation == "failed":
        status["rows"][0]["passed"] = False
    elif mutation == "cap":
        status["wall_seconds"] = 30
    elif mutation == "nan_cap":
        status["wall_seconds"] = float("nan")
    elif mutation == "duplicate_row":
        status["rows"][-1] = status["rows"][0]
    else:
        status["rows"][0]["file"] = "../case_00.npz"
    (run / "status.json").write_text(json.dumps(status))
    with pytest.raises((ValueError, FileNotFoundError)):
        a.read_saved(run, identity)


def test_pearson_undefined_is_null_not_nan():
    assert a.pearson([1, 1], [2, 3]) is None
    assert a.pearson([1, 2, 3], [3, 2, 1]) == -1


def test_workbook_wrong_hash_rejected_before_parsing(tmp_path):
    path = tmp_path / "data.xlsx"
    path.write_bytes(b"not a workbook")
    with pytest.raises(ValueError, match="hash"):
        a.read_workbook(path)


def expected_summary():
    # Independent literal selections on synthetic lines; no recurrence is run.
    c = cases()
    er = [float(np.mean(-r["dR1"][(r["time"] >= -7) & (r["time"] < 1)])) for r in c]
    ca = [float(np.mean(r["dR2"][(r["time"] >= r["isi"]) & (r["time"] < r["isi"] + 4)])) for r in c]
    en = ((np.array(er) - min(er)) / (max(er) - min(er))).tolist()
    cn = ((np.array(ca) - min(ca)) / (max(ca) - min(ca))).tolist()
    return {"ER_means": er, "cAMP_means": ca,
            "ER_window_samples": [534] * 6, "cAMP_window_samples": [267, 267, 267, 267, 267, 134],
            "ER_normalized": en, "cAMP_normalized": cn,
            "normalized_contrast": (np.array(en) - cn).tolist(),
            "final_internal_w": [.2, 1.2, 2.2, 3.2, 4.2, 5.2],
            "final_recorded_w": [.3, 1.3, 2.3, 3.3, 4.3, 5.3]}


def test_independent_summary_reconstruction():
    a.compare_summary(a.analyze_cases(cases()), expected_summary())


@pytest.mark.parametrize("mutation", ["shape", "value", "nan", "missing", "extra"])
def test_saved_summary_mismatch_fails(mutation):
    s = expected_summary()
    if mutation == "shape":
        s["ER_means"] = np.array(s["ER_means"])[:, None].tolist()
    elif mutation == "value":
        s["normalized_contrast"][0] += .01
    elif mutation == "nan":
        s["final_internal_w"][0] = float("nan")
    elif mutation == "missing":
        del s["final_internal_w"]
    else:
        s["unexpected"] = 1
    with pytest.raises(ValueError):
        a.compare_summary(a.analyze_cases(cases()), s)


def test_static_workbook_all_conditions_and_both_windows():
    # Bundled openpyxl exists independently of the repo environment; no install.
    runtime = "/Users/davidmontgomery/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
    code = "import json; import analyze_incentive_handler_saved as a; print(json.dumps(a.read_workbook(),allow_nan=False))"
    r = subprocess.run([runtime, "-c", code], cwd=Path(a.__file__).parent,
                       capture_output=True, text=True, timeout=15, check=True)
    x = json.loads(r.stdout)
    assert x["primary_samples"] == {"cAMP": [41] * 6, "ER": [11] * 6}
    assert [r["preparations"] for r in x["direct_MBON"]] == [5, 5, 6, 5, 5, 5]
    np.testing.assert_allclose(x["primary_rounded_sheet"]["contrast"],
        [.07566030499540898, .6047437291477007, .21246392966096872,
         -.7895777627908429, -.6622688353346606, -.08132616388141267], rtol=0, atol=1e-14)
    assert x["literal_driver_experimental"]["contrast"] != x["primary_rounded_sheet"]["contrast"]


@pytest.mark.parametrize("elapsed", [30., 31., -1.])
def test_execution_rejects_cap_and_bad_clock_before_reading(tmp_path, elapsed):
    out = tmp_path / "analysis"
    with pytest.raises(TimeoutError):
        a.execute(tmp_path / "missing", "0" * 64, out, started=0, clock=lambda: elapsed)
    assert (out / "terminal-error.json").exists()
    assert not (out / "completion.json").exists()


def test_bad_saved_summary_never_produces_successful_analysis(tmp_path):
    run, identity, _ = saved(tmp_path)
    out = tmp_path / "analysis"
    with pytest.raises(ValueError, match="summary"):
        a.execute(run, identity, out, started=time.monotonic())
    assert (out / "started.json").exists()
    assert (out / "terminal-error.json").exists()
    assert not (out / "analysis.json").exists()
    assert not (out / "completion.json").exists()
