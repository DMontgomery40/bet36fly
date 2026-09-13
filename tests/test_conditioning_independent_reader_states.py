"""Reader disposition/budget families on one shared complete synthetic matrix.

Qualification and input preparation are substituted explicitly; the separate
real diagnostic-pair gate suite covers those boundaries without substitution.
No native library is imported or executed by these tests.
"""

from pathlib import Path

import pytest

from bet36fly import conditioning_runner as runner, conditioning_evidence as evidence
from bet36fly.conditioning_artifacts import canonical, strict_json, binding
from test_conditioning_runner import FakeEngine, inputs


@pytest.fixture(scope="module")
def complete_fake_artifacts(tmp_path_factory):
    root = tmp_path_factory.mktemp("independent-reader-state")
    prepared = inputs()
    source = root / "synthetic-source.py"
    source.write_text("# immutable synthetic source fixture\n")
    gate = dict(
        bindings=[binding(source)], pair=dict(pair_id="synthetic-only"), scientific_identity=dict(protocol={})
    )
    engine = FakeEngine(prepared)
    manifest = runner._execute(root, gate, prepared, lambda: engine)
    assert manifest["status"] == "completed", manifest
    assert len(engine.calls) == 1632
    directory = Path(root) / "output/experiments" / manifest["id"]
    return root, manifest["id"], directory, gate, prepared


@pytest.mark.parametrize(
    "status", ["completed", "budget_stopped", "cancelled", "failed", "gate_failed", "running", "unknown"]
)
@pytest.mark.parametrize("wall", [0.0, 1199.999, 1200.0, 1201.0])
def test_only_completed_matrix_inside_cap_can_be_validated_pass(
    complete_fake_artifacts, monkeypatch, status, wall
):
    root, experiment, directory, gate, prepared = complete_fake_artifacts
    monkeypatch.setattr(evidence, "qualify", lambda *_: gate)
    monkeypatch.setattr(evidence, "prepare_inputs", lambda *_: prepared)
    ledger = directory / "ledger.json"
    original = ledger.read_bytes()
    value = strict_json(original)
    value.update(status=status, wall_seconds=wall)
    try:
        ledger.write_bytes(canonical(value))
        result = evidence.validate_conditioning(root, experiment)
        expected = status == "completed" and wall < 1200
        assert (result["evidence_status"] == "passed") is expected, result
        assert (result["all_passed"] is True) is expected, result
        if expected:
            assert result["validated_calls"] == 1632 and result["validation_status"] == "validated"
        if status == "unknown":
            assert result["validation_status"] == "invalid"
    finally:
        ledger.write_bytes(original)


@pytest.mark.parametrize(
    "target",
    [
        "0000-before.npz",
        "0000-compact.npz",
        "0000-compact.json",
        "0008-result.npz",
        "0008-result.json",
        "source",
    ],
)
def test_consumed_artifacts_and_source_cannot_change_after_read(complete_fake_artifacts, monkeypatch, target):
    root, experiment, directory, gate, prepared = complete_fake_artifacts
    monkeypatch.setattr(evidence, "qualify", lambda *_: gate)
    monkeypatch.setattr(evidence, "prepare_inputs", lambda *_: prepared)
    path = Path(gate["bindings"][0]["path"]) if target == "source" else directory / target
    saved = path.read_bytes()
    replaced = False
    original = evidence.read_artifact

    def replace_after_last_read(folder, meta):
        nonlocal replaced
        data = original(folder, meta)
        if meta["path"].startswith("1631-") and not replaced:
            replaced = True
            changed = bytes([saved[0] ^ 1]) + saved[1:]
            path.write_bytes(changed)
        return data

    monkeypatch.setattr(evidence, "read_artifact", replace_after_last_read)
    try:
        result = evidence.validate_conditioning(root, experiment)
        assert replaced and result["validation_status"] == "invalid" and result["all_passed"] is not True, (
            result
        )
    finally:
        path.write_bytes(saved)
