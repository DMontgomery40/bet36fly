"""Independent checker tests use toy sequences, never the28 source trajectories."""

from copy import deepcopy
from dataclasses import astuple
import importlib
from pathlib import Path
import io
import json
import zipfile

import numpy as np
import pytest

import aso_da_no as component


@pytest.fixture
def api():
    return importlib.import_module("audit_aso_source_protocol")


def toy_fixture(pathway=None, initial=(0.2, 0.4, 0.6, 0.3)):
    """Manually specified short toy clock; producer component supplies fixtures."""
    pathway = pathway or dict(id="both", da_enabled=True, no_enabled=True)
    initial = list(initial)
    if not pathway["da_enabled"]:
        initial[0] = initial[2] = 0.0
    if not pathway["no_enabled"]:
        initial[1] = initial[3] = 0.0
    protocol = dict(
        id="synthetic_toy",
        duration_s=41.25,
        odor_a_intervals_s=[[0.5, 1.25]],
        odor_b_intervals_s=[[2.0, 2.5]],
        dan_intervals_s=[[0.5, 1.25], [3.0, 3.5]],
        test_windows_s=[[1.25, 41.25]],
    )
    times = np.array([0, 0.5, 1.25, 2, 2.5, 3, 3.5, 41.25], dtype=np.float64)
    inputs = np.zeros((7, 4, 2), dtype=np.bool_)
    inputs[1, [0, 2], 0] = True
    inputs[3, [1, 2], 0] = True
    inputs[[1, 5], :, 1] = True
    states = np.empty((8, 4, 4), dtype=np.float64)
    states[0] = initial
    kwargs = {k: pathway[k] for k in ("da_enabled", "no_enabled")}
    for j, duration in enumerate(np.diff(times)):
        for c in range(4):
            states[j + 1, c] = astuple(
                component.advance(
                    component.SourceState(*states[j, c]),
                    duration,
                    kc_active=bool(inputs[j, c, 0]),
                    dan_active=bool(inputs[j, c, 1]),
                    **kwargs,
                )
            )
    observation_times = np.array([[1.25, 11.25, 41.25]], dtype=np.float64)
    indices = np.array([[2, 6, 6]], dtype=np.int64)
    observations = np.empty((1, 3, 4, 4), dtype=np.float64)
    for j, (time, index) in enumerate(zip(observation_times[0], indices[0], strict=True)):
        for c in range(4):
            observations[0, j, c] = astuple(
                component.advance(
                    component.SourceState(*states[index, c]),
                    time - times[index],
                    kc_active=bool(inputs[index, c, 0]),
                    dan_active=bool(inputs[index, c, 1]),
                    **kwargs,
                )
            )

    def weight(s):
        return (1 - s[..., 2]) * (1 + s[..., 3])

    arrays = dict(
        segment_times_s=times,
        segment_inputs=inputs,
        segment_states=states,
        segment_weights=weight(states),
        observation_times_s=observation_times,
        observation_states=observations,
        observation_weights=weight(observations),
        observation_segment_indices=indices,
    )
    return protocol, pathway, tuple(initial), arrays


@pytest.mark.parametrize("da,no", [(True, True), (True, False), (False, True), (False, False)])
def test_complete_toy_case_all_pathways(api, da, no):
    protocol, pathway, initial, arrays = toy_fixture(dict(id="toy", da_enabled=da, no_enabled=no))
    report, references = api.compare_case(protocol, pathway, arrays, initial_state=initial)
    assert report["passed"]
    assert report["checked_values"] == sum(a.size for a in arrays.values())
    assert set(references) == set(arrays)


@pytest.mark.parametrize(
    "mutation",
    [
        "interior_latent",
        "interior_expressed",
        "state_columns",
        "observation_time",
        "observation_reset",
        "observation_segment",
        "kc_class",
        "dan_input",
        "segment_time",
        "linear_weight",
        "quiet_latent_erased",
    ],
)
def test_same_shaped_contradictions_fail(api, mutation):
    protocol, pathway, initial, arrays = toy_fixture()
    if mutation == "interior_latent":
        arrays["segment_states"][3, 0, 0] += 0.01
    elif mutation == "interior_expressed":
        arrays["segment_states"][3, 0, 2] += 0.01
    elif mutation == "state_columns":
        arrays["segment_states"] = arrays["segment_states"][..., [2, 3, 0, 1]]
    elif mutation == "observation_time":
        arrays["observation_times_s"][0, 1] += 0.1
    elif mutation == "observation_reset":
        arrays["observation_states"][0, 1] = 0
    elif mutation == "observation_segment":
        arrays["observation_segment_indices"][0, 0] = 1
    elif mutation == "kc_class":
        arrays["segment_inputs"][1, 1, 0] = True
    elif mutation == "dan_input":
        arrays["segment_inputs"][0, :, 1] = True
    elif mutation == "segment_time":
        arrays["segment_times_s"][2] += 0.1
    elif mutation == "linear_weight":
        arrays["segment_weights"] = 1 - arrays["segment_states"][..., 2] + arrays["segment_states"][..., 3]
    elif mutation == "quiet_latent_erased":
        arrays["segment_states"][-1, :, :2] = 0
    report, _ = api.compare_case(protocol, pathway, arrays, initial_state=initial)
    assert not report["passed"]


@pytest.mark.parametrize(
    "mutation", ["nan", "infinity", "negative", "over_one", "float32", "missing", "extra", "shape"]
)
def test_array_contract_family_rejected(api, mutation):
    protocol, pathway, initial, arrays = toy_fixture()
    if mutation == "nan":
        arrays["segment_states"][0, 0, 0] = np.nan
    elif mutation == "infinity":
        arrays["segment_states"][0, 0, 0] = np.inf
    elif mutation == "negative":
        arrays["segment_states"][0, 0, 0] = -1e-15
    elif mutation == "over_one":
        arrays["segment_states"][0, 0, 0] = 1 + 1e-15
    elif mutation == "float32":
        arrays["segment_states"] = arrays["segment_states"].astype(np.float32)
    elif mutation == "missing":
        del arrays["observation_weights"]
    elif mutation == "extra":
        arrays["unrequested"] = np.zeros(1)
    elif mutation == "shape":
        arrays["observation_states"] = arrays["observation_states"][:, :, :3]
    with pytest.raises(ValueError):
        api.compare_case(protocol, pathway, arrays, initial_state=initial)


def test_null_exactness_not_hidden_by_numerical_tolerance(api):
    protocol, pathway, initial, arrays = toy_fixture(dict(id="no_only", da_enabled=False, no_enabled=True))
    arrays["observation_states"][0, 1, 0, 0] = 1e-15
    report, _ = api.compare_case(protocol, pathway, arrays, initial_state=initial)
    assert not report["passed"]


def test_frozen_real_schedule_structure_without_computing_trajectories(api):
    plan = api.load_plan(Path(__file__).with_name("aso-source-protocol-plan-2026-09-13.json"))
    cases = api.case_specs(plan)
    assert len(cases) == 28
    assert [(x["protocol"]["id"], x["pathway"]["id"]) for x in cases[:4]] == [
        ("fig6_naive", name) for name in ("both", "da_only", "no_only", "neither")
    ]
    for case in cases:
        times, flags, observations, indices = api.schedule(case["protocol"])
        assert flags.shape == (len(times) - 1, 4, 2)
        np.testing.assert_array_equal(flags[:, 3, 0], False)
        assert indices.shape == observations.shape
    reversal = cases[16]["protocol"]
    _, _, observations, _ = api.schedule(reversal)
    np.testing.assert_array_equal(
        observations, [[300, 330, 360], [900, 930, 960], [1260, 1290, 1320], [1860, 1890, 1920]]
    )


def test_independent_reference_is_not_producer_state_driven(api):
    protocol, pathway, initial, arrays = toy_fixture()
    _, references = api.compare_case(protocol, pathway, arrays, initial_state=initial)
    changed = deepcopy(arrays)
    changed["segment_states"][2:, 0, 0] *= 0.5
    _, second_references = api.compare_case(protocol, pathway, changed, initial_state=initial)
    for name in references:
        np.testing.assert_array_equal(references[name], second_references[name])


@pytest.mark.parametrize("da,no", [(True, False), (False, True)])
def test_reversal_latent_falls_while_delayed_expression_can_still_rise(api, da, no):
    protocol, pathway, initial, arrays = toy_fixture(
        dict(id="toy", da_enabled=da, no_enabled=no), initial=(0.8, 0.6, 0.1, 0.1)
    )
    report, expected = api.compare_case(protocol, pathway, arrays, initial_state=initial)
    assert report["passed"]
    latent, expressed = (0, 2) if da else (1, 3)
    before, after = expected["segment_states"][[5, 6], 0]
    assert after[latent] < before[latent]
    assert after[expressed] > before[expressed]


@pytest.mark.parametrize("mutation", [None, "duplicate", "allocation_header", "short_payload", "wrong_dtype"])
def test_saved_npz_exact_header_and_payload_before_allocation(api, tmp_path, monkeypatch, mutation):
    protocol, _, _, arrays = toy_fixture()
    path = tmp_path / "toy.npz"
    np.savez_compressed(path, **arrays)
    if mutation is None:
        loaded = api.read_case_npz(path, protocol)
        for name in arrays:
            np.testing.assert_array_equal(loaded[name], arrays[name])
        return
    with zipfile.ZipFile(path) as archive:
        members = [(name, archive.read(name)) for name in archive.namelist()]
    key = "segment_times_s.npy"
    changed = []
    for name, payload in members:
        if name == key:
            if mutation == "short_payload":
                payload = payload[:-1]
            elif mutation == "allocation_header":
                buffer = io.BytesIO()
                np.lib.format.write_array_header_1_0(
                    buffer, dict(descr="<f8", fortran_order=False, shape=(10**12,))
                )
                payload = buffer.getvalue()
            elif mutation == "wrong_dtype":
                buffer = io.BytesIO()
                np.save(buffer, arrays["segment_times_s"].astype(np.float32))
                payload = buffer.getvalue()
        changed.append((name, payload))
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in changed:
            archive.writestr(name, payload)
        if mutation == "duplicate":
            with pytest.warns(UserWarning, match="Duplicate"):
                archive.writestr(key, changed[0][1])

    def forbidden(*args, **kwargs):
        raise AssertionError("np.load was reached before header/payload rejection")

    monkeypatch.setattr(api.np, "load", forbidden)
    with pytest.raises(ValueError):
        api.read_case_npz(path, protocol)


def saved_toy(api, tmp_path):
    plan = api.load_plan(Path(__file__).with_name("aso-source-protocol-plan-2026-09-13.json"))
    protocol, _, _, _ = toy_fixture()
    plan["protocols"] = [protocol]
    plan["expected_case_count"] = 4
    raw = json.dumps(plan, sort_keys=True).encode()
    identity = dict(
        plan_path="synthetic_only",
        plan_sha256=api._bytes_identity(raw)["sha256"],
        helper_path="synthetic_only",
        helper_sha256=api.HELPER_SHA256,
        producer_path="synthetic_only",
        producer_sha256="1" * 64,
    )
    directory = tmp_path / "toy_producer"
    directory.mkdir()
    (directory / "plan.json").write_bytes(raw)
    rows = []
    for i, pathway in enumerate(plan["pathways"]):
        _, _, _, arrays = toy_fixture(pathway, initial=(0, 0, 0, 0))
        name = f"{i:02d}_{protocol['id']}_{pathway['id']}.npz"
        np.savez_compressed(directory / name, **arrays)
        rows.append(
            dict(
                index=i,
                protocol_id=protocol["id"],
                pathway_id=pathway["id"],
                file=name,
                **api.file_identity(directory / name),
            )
        )
    status = dict(
        schema=1,
        kind="aso2019_source_equation_protocol",
        status="completed",
        started_at="2026-09-13T12:00:00+00:00",
        elapsed_seconds=0.01,
        identity=identity,
        expected_case_count=4,
        completed_case_count=4,
        cases=rows,
        failed_case=None,
        error=None,
        kc_classes=plan["kc_classes"],
        state_columns=plan["state_columns"],
        observation_labels=plan["test_observations"],
        unit="seconds",
        parameters=plan["parameters"],
    )
    (directory / "status.json").write_text(json.dumps(status))
    return plan, raw, identity, directory, status


def test_complete_toy_artifact_audit_persists_all_references_once(api, tmp_path):
    plan, raw, identity, source, _ = saved_toy(api, tmp_path)
    output = tmp_path / "audit"
    report = api.audit_saved(plan, source, output, expected_identity=identity, plan_bytes=raw)
    assert report["status"] == "completed" and report["numerical_status"] == "passed"
    assert report["completed_case_count"] == 4
    assert report == json.loads((output / "audit.json").read_text())
    for row in report["rows"]:
        assert api.file_identity(output / row["reference_file"]) == row["reference_binding"]
    saved = {p.name: p.read_bytes() for p in output.iterdir()}
    with pytest.raises(FileExistsError):
        api.audit_saved(plan, source, output, expected_identity=identity, plan_bytes=raw)
    assert saved == {p.name: p.read_bytes() for p in output.iterdir()}


@pytest.mark.parametrize("mutation", ["failed", "float_count", "wrong_order", "path", "cap", "identity"])
def test_terminal_status_and_case_binding_family_fails_before_calculation(
    api, tmp_path, monkeypatch, mutation
):
    plan, raw, identity, source, status = saved_toy(api, tmp_path)
    if mutation == "failed":
        status["status"] = "failed"
    elif mutation == "float_count":
        status["completed_case_count"] = 4.0
    elif mutation == "wrong_order":
        status["cases"].reverse()
    elif mutation == "path":
        status["cases"][0]["file"] = "../elsewhere.npz"
    elif mutation == "cap":
        status["elapsed_seconds"] = 30.0
    elif mutation == "identity":
        status["identity"] = dict(identity, helper_sha256="0" * 64)
    (source / "status.json").write_text(json.dumps(status))

    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid producer reached reference dynamics")

    monkeypatch.setattr(api, "reference_case", forbidden)
    report = api.audit_saved(plan, source, tmp_path / "audit", expected_identity=identity, plan_bytes=raw)
    assert report["status"] == "failed" and report["completed_case_count"] == 0
    assert "Invalid producer reached" not in report["error"]


def test_final_persistence_timeout_cannot_leave_completed_audit(api, tmp_path, monkeypatch):
    plan, raw, identity, source, _ = saved_toy(api, tmp_path)
    now = [0.0]
    original = api._write_json

    def write(path, value):
        original(path, value)
        if value.get("status") == "completed":
            now[0] = 60.0

    monkeypatch.setattr(api, "_write_json", write)
    output = tmp_path / "audit"
    report = api.audit_saved(
        plan, source, output, expected_identity=identity, plan_bytes=raw, clock=lambda: now[0]
    )
    assert report["status"] == "failed" and report["numerical_status"] == "failed"
    assert json.loads((output / "audit.json").read_text())["status"] == "failed"
    assert len(list(output.glob("reference_*.npz"))) == 4


def test_late_consumed_artifact_change_rejects_completion(api, tmp_path, monkeypatch):
    plan, raw, identity, source, status = saved_toy(api, tmp_path)
    original = api.compare_case
    first = [True]

    def compare(*args, **kwargs):
        result = original(*args, **kwargs)
        if first[0]:
            first[0] = False
            with (source / status["cases"][0]["file"]).open("ab") as stream:
                stream.write(b"changed")
        return result

    monkeypatch.setattr(api, "compare_case", compare)
    report = api.audit_saved(plan, source, tmp_path / "audit", expected_identity=identity, plan_bytes=raw)
    assert report["status"] == "failed"
    assert "changed during the audit" in report["error"]


def test_failed_later_case_retains_earlier_independent_reference(api, tmp_path):
    plan, raw, identity, source, status = saved_toy(api, tmp_path)
    row = status["cases"][1]
    path = source / row["file"]
    with np.load(path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    arrays["segment_states"][1, 0, 0] = np.nan
    np.savez_compressed(path, **arrays)
    row.update(api.file_identity(path))
    (source / "status.json").write_text(json.dumps(status))
    output = tmp_path / "audit"
    report = api.audit_saved(plan, source, output, expected_identity=identity, plan_bytes=raw)
    assert report["status"] == "failed" and report["completed_case_count"] == 1
    assert (output / "reference_00.npz").exists()
    assert not (output / "reference_01.npz").exists()
    assert report == json.loads((output / "audit.json").read_text())
