import pytest

from fastapi.testclient import TestClient

from bet36fly.server import create_app


def test_no_model_and_no_games_are_explicit(tmp_path):
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        response = client.get("/api/status")
        state = response.json()
        assert state["mode"] == "paper" and not state["model_ready"]
        assert "verification_mode" not in state and "stored_run_id" not in state
        assert "X-BET36FLY-Verification" not in response.headers
        assert client.get("/api/games").json()["games"] == []
        assert client.get("/api/training").json()["report"] is None
        assert client.post("/api/predict/missing").status_code == 503
        assert client.get("/api/games?sport=cricket").status_code == 422
        desk = client.get("/api/desk").json()
        assert desk["mode"] == "forward_paper"
        assert desk["summary"]["completed"] == 0 and desk["summary"]["hit_rate"] is None
        assert client.get("/api/desk?sport=cricket").status_code == 422


@pytest.mark.parametrize("prepared", ["absent", "empty", "ids_only"])
def test_brain_geometry_reports_an_unprepared_connectome_as_503(tmp_path, prepared):
    """The Circuit page documents an explicit 503 for a missing prepared connectome.

    Every partial state must reach that message rather than a 500, because the page
    shows the returned detail verbatim next to its retry control.
    """
    import numpy as np

    brain = tmp_path / "data" / "brain"
    if prepared != "absent":
        brain.mkdir(parents=True)
    if prepared == "ids_only":
        np.save(brain / "ids.npy", np.arange(10))
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        response = client.get("/api/brain")
        assert response.status_code == 503
        assert response.json()["detail"] == "Official connectome data has not been prepared yet."


def test_refresh_conflict_and_external_origin_are_rejected(tmp_path):
    app = create_app(root=tmp_path, warm_on_start=False)
    with TestClient(app) as client:
        app.state.get_runtime().refresh = lambda: False
        assert client.post("/api/refresh").status_code == 409
        assert client.post("/api/refresh", headers={"Origin": "https://unrelated.example"}).status_code == 403


def test_ledger_export_is_real_csv_and_unknown_api_is_not_html(tmp_path):
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        response = client.get("/api/ledger/export")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert response.text.startswith("id,game_id,")
        assert client.get("/api/unknown").status_code == 404
        assert client.get("/api/ledger").json() == {"picks": [], "count": 0}


def test_experiment_registry_downloads_and_prospective_panel(tmp_path):
    from bet36fly.experiments import Registry

    registry = Registry(tmp_path / "output/experiments/v2-test", {"id": "v2-test", "jobs": []})
    report = registry.directory / "report.json"
    report.write_text('{"measured": true}')
    key = registry.artifact(report)
    registry.save()
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        index = client.get("/api/experiments").json()
        assert index["experiments"][0]["id"] == "v2-test"
        assert index["prospective"]["sports"]["soccer"]["threshold"] == 100
        assert index["prospective"]["sports"]["baseball"]["threshold"] == 1000
        assert client.get("/api/experiments/v2-test").json()["jobs"] == []
        assert client.get(f"/api/experiments/v2-test/artifacts/{key}").json() == {"measured": True}
        assert client.get("/api/experiments/v2-test/artifacts/report").status_code == 404
        assert client.get("/api/experiments/missing").status_code == 404
        outside = tmp_path / "outside"
        outside.write_text("secret")
        report.unlink()
        report.symlink_to(outside)
        assert client.get(f"/api/experiments/v2-test/artifacts/{key}").status_code == 404


def _diagnostic(root, run_id, *, rule, created_at, complete=True, passed=False, attribution=True):
    import json

    directory = root / "output/diagnostics" / run_id
    directory.mkdir(parents=True)
    criteria = {
        "teaching_specific": {
            "passed": True,
            "evaluations": {
                "home/base": {
                    "mean_effect": -2.3,
                    "mean_untaught": -0.29,
                    "required_magnitude": 0.87,
                    "passed": True,
                }
            },
        },
        "untaught_guard": {
            "passed": passed,
            "evaluations": {"home/base": {"mean": -0.289, "sd": 0.32, "limit": 0.16, "passed": passed}},
        },
        "cross_compartment": {"passed": True, "evaluations": {}},
        "no_bound_hits": {"passed": True, "clipped_total": 0},
        "cumulative": {"passed": True, "per_compartment": [], "trajectory": []},
        "bit_identical_repeat": {"passed": True, "by_condition": {}},
        "sensory_noise_invariance": {"passed": True, "by_trial": {}},
    }
    summary = dict(
        run_id=run_id,
        rule=rule,
        created_at=created_at,
        panel_complete=complete,
        all_passed=complete and passed,
        panel_note="frozen v1.1 panel" if complete else "INCOMPLETE debug panel; not a gate result",
        identity={
            "protocol": {
                "dan_reference": "none" if rule == "candidate" else "tonic-baseline",
                "away_plasticity_mask": "all",
            }
        },
        native_binary={"path": "/x/reward-lif-abc.dylib", "sha256": "ab" * 32},
        source_unchanged_during_run=True,
        anatomy={
            "plastic_edges": 8866,
            "eligible_edges": 8866,
            "group_labels": ["home/gamma"],
            "group_edges": [1585],
        },
        criteria=criteria,
        rows=[{"game": 4362, "seed_set": "base", "condition": "untaught", "applied": [-0.05, 0.0]}] * 64,
    )
    (directory / "summary.json").write_text(json.dumps(summary))
    (directory / "trials.npz").write_bytes(b"not served")
    if attribution:
        (directory / "attribution.json").write_text(
            json.dumps({"run_id": run_id, "mean_applied_by_phase": {"post_offset": -0.127}})
        )
    return summary


def test_reward_diagnostics_are_listed_newest_first_and_served_read_only(tmp_path):
    _diagnostic(tmp_path, "diag-legacy-1111aaaa", rule="legacy", created_at="2026-09-11T15:30:00+00:00")
    _diagnostic(tmp_path, "diag-candidate-2222bbbb", rule="candidate", created_at="2026-09-11T15:50:00+00:00")
    _diagnostic(
        tmp_path,
        "diag-candidate-3333cccc-INCOMPLETE",
        rule="candidate",
        created_at="2026-09-11T15:55:00+00:00",
        complete=False,
        attribution=False,
    )
    early = _diagnostic(
        tmp_path, "diag-legacy-0000eeee", rule="legacy", created_at="2026-09-11T15:20:00+00:00"
    )
    import json as _json

    early_path = tmp_path / "output/diagnostics/diag-legacy-0000eeee/summary.json"
    for key in ("panel_complete", "panel_note", "all_passed"):
        early.pop(key)
    early["identity"]["protocol"] = {}  # schema-3 base protocol: no reference or mask fields
    early_path.write_text(_json.dumps(early))
    bad = tmp_path / "output/diagnostics/diag-broken"
    bad.mkdir()
    (bad / "summary.json").write_text("{not json")
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        listing = client.get("/api/reward-diagnostics").json()
        assert [d["run_id"] for d in listing["diagnostics"]] == [
            "diag-candidate-3333cccc-INCOMPLETE",
            "diag-candidate-2222bbbb",
            "diag-legacy-1111aaaa",
            "diag-legacy-0000eeee",
            "diag-broken",
        ]
        oldest = listing["diagnostics"][3]
        assert (
            oldest["panel_complete"] is None and oldest["all_passed"] is None
        )  # not recorded by that script version
        assert (
            oldest["dan_reference"] == "tonic-baseline" and oldest["away_plasticity_mask"] == "all"
        )  # implied by rule / absence
        assert listing["diagnostics"][2]["dan_reference"] == "tonic-baseline"
        entry = listing["diagnostics"][1]
        assert (
            entry["rule"] == "candidate"
            and entry["dan_reference"] == "none"
            and entry["away_plasticity_mask"] == "all"
        )
        assert (
            entry["panel_complete"] is True
            and entry["all_passed"] is False
            and entry["has_attribution"] is True
        )
        assert set(entry["criteria"].values()) == {None}
        assert entry["stored_verdict"] == "failed" and entry["evidence_status"] == "unverified"
        assert entry["validation_status"] == "stored-only"
        assert listing["diagnostics"][-1]["validation_status"] == "invalid"
        assert entry["untaught_guard"]["home/base"] == {
            "mean": -0.289,
            "sd": 0.32,
            "limit": 0.16,
            "passed": False,
        }
        assert entry["teaching_specific"]["home/base"]["mean_effect"] == -2.3
        assert entry["native_binary_sha256"] == "ab" * 32 and entry["source_unchanged_during_run"] is True
        assert "rows" not in entry
        assert (
            listing["diagnostics"][0]["panel_complete"] is False
            and listing["diagnostics"][0]["has_attribution"] is False
        )
        assert listing["evidence_note"] == "docs/evidence/reward-mechanism-repair-2026-09-12/index.md"
        full = client.get("/api/reward-diagnostics/diag-candidate-2222bbbb").json()
        assert full["validation"] == entry
        assert (
            len(full["summary"]["rows"]) == 64
            and full["attribution"]["mean_applied_by_phase"]["post_offset"] == -0.127
        )
        assert (
            client.get("/api/reward-diagnostics/diag-candidate-3333cccc-INCOMPLETE").json()["attribution"]
            is None
        )
        assert client.get("/api/reward-diagnostics/diag-missing").status_code == 404
        assert client.get("/api/reward-diagnostics/diag-broken").status_code == 404
        assert client.get("/api/reward-diagnostics/..%2Fsecret").status_code in (404, 422)
        assert client.get("/api/reward-diagnostics/diag-candidate-2222bbbb/trials.npz").status_code == 404


def test_reward_diagnostics_empty_and_absent_directories_are_explicit(tmp_path):
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        index = client.get("/api/reward-diagnostics").json()
        assert index["diagnostics"] == [] and index["qualification_pairs"] == []
        assert index["conditioning"]["status"] == "not_run"
    (tmp_path / "output/diagnostics").mkdir(parents=True)
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        assert client.get("/api/reward-diagnostics").json()["diagnostics"] == []


@pytest.mark.parametrize(
    "field,value",
    [("created_at", 123), ("bridge_contract", {}), ("mean", "overflow"), ("rate_tau_ms", "overflow")],
)
def test_reward_metadata_corruption_remains_visible_without_breaking_json(tmp_path, field, value):
    import json

    _diagnostic(tmp_path, "diag-good", rule="candidate", created_at="2026-09-12")
    summary = _diagnostic(tmp_path, "diag-malformed", rule="candidate", created_at="2026-09-12")
    if field == "mean":
        summary["criteria"]["untaught_guard"]["evaluations"]["home/base"]["mean"] = value
    elif field == "bridge_contract":
        summary["identity"][field] = value
    elif field == "rate_tau_ms":
        summary["identity"]["protocol"][field] = value
    else:
        summary[field] = value
    (tmp_path / "output/diagnostics/diag-malformed/summary.json").write_text(
        json.dumps(summary).replace('"overflow"', "1e400")
    )
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        response = client.get("/api/reward-diagnostics")
        assert response.status_code == 200
        rows = {row["run_id"]: row for row in response.json()["diagnostics"]}
        assert rows["diag-malformed"]["validation_status"] == "invalid"
        assert rows["diag-malformed"]["evidence_status"] == "unverified"
        assert rows["diag-good"]["validation_status"] == "stored-only"
        assert "diag-malformed" in _render_diagnostic_payload(response.json())


@pytest.mark.parametrize(
    "field",
    [
        "dan_reference",
        "away_plasticity_mask",
        "bridge_tail",
        "bridge_layout",
        "native_binary_sha256",
        "source_code_hashes",
    ],
)
@pytest.mark.parametrize("bad", [{"wrong": "object"}, ["unexpected"], 123, True])
def test_rendered_scalar_and_hash_objects_fail_closed_at_endpoint(tmp_path, field, bad):
    import json

    summary = _diagnostic(tmp_path, "diag-bad-field", rule="candidate", created_at="2026-09-12")
    if field == "native_binary_sha256":
        summary["native_binary"]["sha256"] = bad
    elif field == "source_code_hashes":
        summary["identity"]["code_hashes"] = {"reward_lif.cpp": bad}
    else:
        summary["identity"]["protocol"][field] = bad
    (tmp_path / "output/diagnostics/diag-bad-field/summary.json").write_text(json.dumps(summary))
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        index = client.get("/api/reward-diagnostics").json()
        row = index["diagnostics"][0]
        assert row["validation_status"] == "invalid"
        assert row["evidence_status"] == "unverified"
        assert row.get(field) is None
        rendered = _render_diagnostic_payload(index)
        assert "diag-bad-field" in rendered and "unverified" in rendered
        assert "validated passed" not in rendered


def _render_diagnostic_payload(payload):
    """Exercise the actual API-to-React boundary with the repo's existing TS toolchain."""
    import json
    from pathlib import Path
    import subprocess

    program = r"""
const esbuild = require('esbuild');
const source = `
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {readFileSync} from 'node:fs';
import {RewardEvidenceView} from './src/RewardEvidence';
const diagnostics=JSON.parse(readFileSync(0,'utf8'));
process.stdout.write(renderToStaticMarkup(React.createElement(RewardEvidenceView, {
 diagnostics, diagnosticsLoading:false, diagnosticsError:'', experiments:{experiments:[],active_v1:null,prospective:{status:'awaiting_candidate',sports:{}}},
 experimentsError:'',selectedExperimentId:'',selectedJobId:'',onSelectExperiment:()=>{},onSelectJob:()=>{}
})));
`;
const code=esbuild.buildSync({stdin:{contents:source,loader:'tsx',resolveDir:process.cwd()},bundle:true,platform:'node',format:'cjs',write:false,jsx:'automatic',external:['react','react-dom/server']}).outputFiles[0].text;
new Function('require','process',code)(require,process);
"""
    result = subprocess.run(
        ["node", "-e", program],
        cwd=Path(__file__).resolve().parents[1] / "web",
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    return result.stdout


@pytest.mark.parametrize(
    "damage",
    [
        "status",
        "reason",
        "calls",
        "stages",
        "criteria",
        "jobs",
        "artifacts",
        "record",
        "dates",
        "stored_validation",
    ],
)
def test_conditioning_registry_sanitizes_rendered_metadata_and_never_trusts_stored_pass(tmp_path, damage):
    import json

    directory = tmp_path / "output/experiments/synthetic-conditioning"
    directory.mkdir(parents=True)
    manifest = dict(
        id="synthetic-conditioning",
        kind="dopamine-conditioning",
        status="completed",
        created_at="",
        updated_at="",
        jobs=[],
        artifacts={},
        conditioning=dict(
            status_reason="synthetic only", calls=dict(actual=1632, planned=1632, cap=1640), stages=[]
        ),
    )
    bad = {"wrong": "object"}
    if damage == "status":
        manifest["status"] = bad
    if damage == "reason":
        manifest["conditioning"]["status_reason"] = bad
    if damage == "calls":
        manifest["conditioning"]["calls"] = {"actual": float("inf"), "planned": bad, "cap": True}
    if damage == "stages":
        manifest["conditioning"]["stages"] = [None, {"id": bad, "status": bad}]
    if damage == "criteria":
        manifest["conditioning"]["stages"] = [
            {
                "id": "acquisition-primary",
                "status": "completed",
                "criteria": {"arbitrary": {"passed": bad, "value": bad, "limit": float("inf")}},
            }
        ]
    if damage == "jobs":
        manifest["jobs"] = [
            None,
            {"id": "acquisition-primary", "status": bad, "completed": bad, "total": float("inf")},
        ]
    if damage == "artifacts":
        manifest["artifacts"] = {"bad": {"url": bad, "label": bad}}
    if damage == "record":
        manifest["conditioning"] = bad
    if damage == "dates":
        manifest["created_at"] = bad
        manifest["updated_at"] = 1e400
    if damage == "stored_validation":
        manifest["conditioning_validation"] = dict(
            validation_status="validated", evidence_status="passed", all_passed=True
        )
    (directory / "manifest.json").write_text(json.dumps(manifest))
    with TestClient(create_app(root=tmp_path, warm_on_start=False)) as client:
        index = client.get("/api/experiments")
        detail = client.get("/api/experiments/synthetic-conditioning")
        assert index.status_code == detail.status_code == 200
        index_run = index.json()["experiments"][0]
        detail_run = detail.json()
        assert index_run["conditioning_validation"] == detail_run["conditioning_validation"]
        assert index_run["conditioning_validation"]["validation_status"] == "stored-only"
        assert index_run["conditioning_validation"]["all_passed"] is None
        assert "wrong" not in json.dumps(index_run)
