"""Read-only identities, saved-state relations and reporter audit; never runs source cases."""

from pathlib import Path
import hashlib
import json
import datetime
import numpy as np

B = Path(__file__).absolute().parent
ROOT = B.parents[2]
RUN = B / "incentive-handler-source-9c5800e30fdae747b49a"
PLAN = B / "incentive-handler-execution-plan-v2-2026-09-13.json"
OUT = B / "incentive-handler-independent-saved-audit-2026-09-13.json"
ISIS = [-6.0, -1.2, -0.6, 0.0, 0.5, 6.0]
FIELDS = ("cs", "us", "k", "d1", "d2", "m", "w", "dR1", "dR2", "w_before", "delta_w", "internal_w")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text())


def entry(p):
    return dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size, sha256=sha(p))


def check_close(actual, expected):
    np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=1e-12)
    return float(np.max(np.abs(actual - expected)))


def main():
    plan = read(PLAN)
    assert len(plan["files"]) == 35
    assert plan["identity"] == RUN.name and plan["launch_attempt_number"] == 2
    assert plan["previous_attempt_source_cases"] == 0
    assert plan["parent_wall_cap_seconds"] == 30 and plan["restarts_allowed"] == 0
    assert len({r["path"] for r in plan["files"]}) == 35
    for r in plan["files"]:
        p = ROOT / r["path"]
        assert p.stat().st_size == r["bytes"] and sha(p) == r["sha256"], r["path"]
    protected = {str(ROOT / r["path"]): r["sha256"] for r in plan["files"]}
    for p in [PLAN, *RUN.iterdir(), *(B / (RUN.name + "-execution")).iterdir()]:
        assert p.is_file() and not p.is_symlink()
        protected[str(p)] = sha(p)
    execution = read(B / (RUN.name + "-execution") / "execution.json")
    assert execution["plan_sha256"] == sha(PLAN)
    assert execution["identity"] == RUN.name and execution["completed_cases"] == 6
    assert execution["returncode"] == 0 and execution["child_reaped"] is True
    assert execution["wall_seconds"] < 30 and execution["bindings_unchanged"] is True
    assert Path(execution["command"][0]) == ROOT / ".venv/bin/python"
    failed = B / "incentive-handler-source-b7ce8a8ec24dab37ebe0-execution"
    first = read(failed / "execution.json")
    assert first["returncode"] == 1 and first["child_status"] is None
    assert "ModuleNotFoundError: No module named 'numpy'" in (failed / "stderr.txt").read_text()
    assert not (B / "incentive-handler-source-b7ce8a8ec24dab37ebe0").exists()
    status, identity, summary = [read(RUN / (n + ".json")) for n in ("status", "identity", "summary")]
    assert status["status"] == "completed" and status["completed_cases"] == 6
    assert status["wall_seconds"] < 30 and status["source_unchanged"] is True
    assert sha(RUN / "summary.json") == status["summary_sha256"]
    assert identity["ISIS"] == ISIS and identity["taus"] == [100 / 3, 60.0, 104.0]
    assert identity["samples"] == 1001 and identity["grid"] == [-7, 8]
    assert identity["scope"] == "authored_source_only" and identity["cap_seconds"] == 30
    for name, h in identity["source"].items():
        assert sha(B / "incentive-circuit-source-2026-09-13" / name) == h
    for name, h in identity["bindings"].items():
        assert sha(Path(name)) == h
    progress = read(RUN / "progress.json")
    assert progress["rows"] == status["rows"] and progress["completed_cases"] == 6
    cases, rows, means_er, means_ca, counts_er, counts_ca = [], [], [], [], [], []
    allkeys = {"time", *FIELDS, *("independent_" + k for k in FIELDS), *("difference_" + k for k in FIELDS)}
    assert len(status["rows"]) == 6
    for i, (isi, row) in enumerate(zip(ISIS, status["rows"])):
        assert row["index"] == i and row["isi"] == isi and row["file"] == f"case_{i:02d}.npz"
        assert row["passed"] is True and row["validation_failures"] == []
        path = RUN / row["file"]
        assert sha(path) == row["sha256"]
        with np.load(path, allow_pickle=False) as z:
            assert set(z.files) == allkeys and len(z.files) == 37
            d = {k: z[k] for k in z.files}
        assert all(a.shape == (1001,) and a.dtype == np.float64 and np.isfinite(a).all() for a in d.values())
        t = np.linspace(-7.0, 8.0, 1001)
        np.testing.assert_array_equal(d["time"], t)
        np.testing.assert_array_equal(d["cs"], (t >= 0) & (t < 0.5))
        np.testing.assert_array_equal(d["us"], (t >= isi) & (t < isi + 0.6))
        assert int(d["cs"].sum()) == row["cs_samples"]
        assert int(d["us"].sum()) == row["us_samples"]
        discrepancies = {}
        ratios = []
        for key in FIELDS:
            expected = d["independent_" + key]
            difference = d[key] - expected
            np.testing.assert_array_equal(difference, d["difference_" + key])
            discrepancies[key] = check_close(d[key], expected)
            assert discrepancies[key] == row["max_absolute_errors"][key]
            ratios.append(float(np.max(np.abs(difference) / (1e-12 + 1e-12 * np.abs(expected)))))
        residuals = {}
        np.testing.assert_array_equal(d["w_before"][1:], d["internal_w"][:-1])
        assert d["w_before"][0] == 1
        np.testing.assert_array_equal(d["internal_w"], d["w_before"] + d["delta_w"])
        np.testing.assert_array_equal(d["w"], np.maximum(d["internal_w"], 0))
        residuals["delta"] = check_close(d["delta_w"], (d["d2"] - d["d1"]) * (d["k"] + d["w_before"] - 1))
        residuals["mbon"] = check_close(d["m"], np.clip(d["k"] * np.maximum(d["w_before"], 0), 0, 2))
        for key, tau in [("k", 100 / 3), ("d1", 60.0), ("d2", 104.0)]:
            gamma = 1 - 1 / tau
            initial = d["cs"][0] if key == "k" else d["us"][0]
            drive = d["cs"][1:] if key == "k" else d["us"][1:] - d["m"][:-1]
            expected = np.r_[initial, np.clip((1 - gamma) * drive + gamma * d[key][:-1], 0, 2)]
            residuals[key] = check_close(d[key], expected)
            assert (d[key] >= 0).all() and (d[key] <= 2).all()
        assert (d["m"] >= 0).all() and (d["m"] <= 2).all()
        up = np.maximum(d["d1"] - d["d2"], np.finfo(float).eps)
        down = np.minimum(d["d1"] - d["d2"], -np.finfo(float).eps)
        residuals["dR1"] = check_close(d["dR1"], -up * (d["k"] - 1) - (up - down) * d["w"])
        residuals["dR2"] = check_close(d["dR2"], down * (d["k"] - 1))
        emask, cmask = (t >= -7) & (t < 1), (t >= isi) & (t < isi + 4)
        means_er.append(float(np.mean(-d["dR1"][emask])))
        means_ca.append(float(np.mean(d["dR2"][cmask])))
        counts_er.append(int(emask.sum()))
        counts_ca.append(int(cmask.sum()))
        rows.append(
            dict(
                index=i,
                isi=isi,
                fields=37,
                samples=1001,
                max_source_scalar_difference=max(discrepancies.values()),
                max_used_tolerance_fraction=max(ratios),
                max_saved_state_relation_residual=max(residuals.values()),
                final_internal_w=float(d["internal_w"][-1]),
                final_recorded_w=float(d["w"][-1]),
                internal_min=float(d["internal_w"].min()),
                internal_max=float(d["internal_w"].max()),
                negative_internal_samples=int((d["internal_w"] < 0).sum()),
                signal_ranges={k: [float(d[k].min()), float(d[k].max())] for k in ("k", "d1", "d2", "m")},
                endpoint_signals={k: float(d[k][-1]) for k in ("k", "d1", "d2", "m")},
                cs_samples=int(d["cs"].sum()),
                us_samples=int(d["us"].sum()),
            )
        )
        cases.append(d)
    er, ca = np.array(means_er), np.array(means_ca)
    en, cn = (er - er.min()) / np.ptp(er), (ca - ca.min()) / np.ptp(ca)
    expected_summary = dict(
        ER_means=means_er,
        cAMP_means=means_ca,
        ER_window_samples=counts_er,
        cAMP_window_samples=counts_ca,
        ER_normalized=en.tolist(),
        cAMP_normalized=cn.tolist(),
        normalized_contrast=(en - cn).tolist(),
        final_internal_w=[r["final_internal_w"] for r in rows],
        final_recorded_w=[r["final_recorded_w"] for r in rows],
    )
    assert expected_summary == summary
    for p, h in protected.items():
        assert sha(Path(p)) == h, p
    prior = read(B / "incentive-dpr-equations-timing-reading-receipt-2026-09-13.json")
    old = {x["path"]: x["sha256"] for x in prior["current_narrative_inventory"]}
    narratives = sorted(
        set(
            [
                ROOT / "AGENTS.md",
                ROOT / "README.md",
                *(ROOT / "docs").rglob("*.md"),
                *(ROOT / "wiki").rglob("*.md"),
            ]
        )
    )
    inventory = [entry(p) for p in narratives]
    deltas = [r for r in inventory if old.get(r["path"]) != r["sha256"]]
    result = dict(
        status="passed_saved_artifact_consistency_audit",
        agent="/root/delivered_arrivals",
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_result_id=RUN.name,
        actual_source_case_reruns=0,
        native_calls=0,
        fits=0,
        network_calls=0,
        scope="Complete saved 6-case/37-field/1001-sample validation, using local algebra on recorded states and direct source/scalar/discrepancy comparisons. No source induction recomputed.",
        coverage=dict(
            cases=6,
            arrays=222,
            scalar_values=222222,
            source_scalar_comparisons=72072,
            input_bindings=35,
            snapshot_files=len(protected),
        ),
        launcher=dict(
            first_launch_failed_before_cases=True,
            first_failure_preserved=True,
            second_launch_attempt=2,
            actual_source_induction_count=6,
            parent_wall_seconds=execution["wall_seconds"],
            child_wall_seconds=status["wall_seconds"],
            parent_cap_seconds=30,
            reviewer_launcher_tests="12 passed in 0.80 s",
        ),
        rows=rows,
        recomputed_summary=expected_summary,
        all_bindings_unchanged=True,
        limitations=[
            "These are finite t=8 s released-source states, not complete-tail results or BET36FLY brain measurements.",
            "Relative and absolute comparison tolerances remain the declared 1e-12 each; maximum absolute error alone is not the pass rule.",
            "This checks saved local recurrence identities and complete recorded independent results, not a second authored source induction.",
            "Raw source internal W is unbounded; rectified recording at zero must not be interpreted as a clipped internal checkpoint.",
            "Literal reporter windows and six-condition normalization are not the primary workbook reporter protocol or actual weight changes.",
        ],
        reading=dict(
            prior_full_receipt=entry(B / "incentive-dpr-equations-timing-reading-receipt-2026-09-13.json"),
            prior_preexecution_review=entry(
                B / "incentive-handler-independent-preexecution-review-2026-09-13.json"
            ),
            current_narrative_count=len(inventory),
            current_narrative_inventory=inventory,
            new_or_changed_narratives=deltas,
            all_deltas_personally_read=True,
            new_output_narratives_personally_read=[entry(B / "incentive-launcher-correction-2026-09-13.md")],
            new_code_and_test_full_reads=[
                entry(B / "source_audit_launch.py"),
                entry(B / "test_source_audit_launch.py"),
            ],
        ),
        bindings=[entry(PLAN), entry(Path(__file__)), *[entry(Path(p)) for p in protected]],
    )
    with OUT.open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(
        json.dumps(
            dict(
                receipt=entry(OUT),
                coverage=result["coverage"],
                rows=[
                    {
                        k: r[k]
                        for k in (
                            "isi",
                            "final_internal_w",
                            "final_recorded_w",
                            "negative_internal_samples",
                            "max_source_scalar_difference",
                            "max_saved_state_relation_residual",
                        )
                    }
                    for r in rows
                ],
                narrative_deltas=deltas,
            )
        )
    )


if __name__ == "__main__":
    main()
