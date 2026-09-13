"""Runner contracts: complete masks, immutable identities and exact guard families."""

import copy
import json

import numpy as np
import pytest

import run_weight_state_shadow as run


def maps_fixture():
    groups = np.repeat(np.array([0, 1, 2, 4, 5, 6], np.int32), [1585, 316, 2283, 3239, 1438, 5])
    bodies = np.arange(4774, dtype=np.int64) + 1000000
    bodies[4064:4066] = [11327, 11900]
    return dict(
        plastic_kc_indices=np.arange(8866, dtype=np.int32) % 4064,
        plastic_compartments=(groups // 4).astype(np.int32),
        plastic_mask=((groups < 4) | (groups == 4)).astype(np.uint8),
        plastic_groups=groups,
        sample=np.arange(4774, dtype=np.int32),
        body_ids=bodies,
        kc_indices=np.arange(4064, dtype=np.int32),
        dan_indices=np.arange(4064, 4088, dtype=np.int32),
        sensory_indices=np.arange(4088, 4774, dtype=np.int32),
        dan_compartments=np.array([0, 0] + [1] * 22, np.int32),
        kc_columns=np.arange(4064, dtype=np.int32),
        dan_columns=np.arange(4064, 4088, dtype=np.int32),
        sensory_columns=np.arange(4088, 4774, dtype=np.int32),
    )


def test_full_scientific_map_preserves_all_home_and_only_supported_away_edges():
    maps = maps_fixture()
    before = {k: v.tobytes() for k, v in maps.items()}
    selection = run.validate_maps(maps)
    assert [int(x.sum()) for x in selection] == [4184, 3239]
    assert before == {k: v.tobytes() for k, v in maps.items()}
    assert len(run.audit_edges(maps)) == 4


@pytest.mark.parametrize(
    "mutation",
    [
        "home_filter",
        "away_all",
        "mask_nonbinary",
        "wrong_group",
        "wrong_channel",
        "missing_dan",
        "wrong_ppl",
        "duplicate_columns",
        "wrong_index",
        "edge_outside",
        "negative_column",
        "missing_field",
        "float_map",
        "duplicate_body",
        "wrong_shape",
    ],
)
def test_complete_map_family_rejects_biological_routing_or_index_drift(mutation):
    maps = maps_fixture()
    if mutation == "home_filter":
        maps["plastic_mask"][0] = 0
    elif mutation == "away_all":
        maps["plastic_mask"][:] = 1
    elif mutation == "mask_nonbinary":
        maps["plastic_mask"][0] = 2
    elif mutation == "wrong_group":
        maps["plastic_groups"][0] = 1
    elif mutation == "wrong_channel":
        maps["plastic_compartments"][0] = 1
    elif mutation == "missing_dan":
        maps["dan_compartments"][0] = 1
    elif mutation == "wrong_ppl":
        maps["body_ids"][4064] = 999
    elif mutation == "duplicate_columns":
        maps["kc_columns"][1] = maps["kc_columns"][0]
    elif mutation == "wrong_index":
        maps["kc_indices"][0] = 55
    elif mutation == "edge_outside":
        maps["plastic_kc_indices"][0] = 4064
    elif mutation == "negative_column":
        maps["dan_columns"][0] = -1
    elif mutation == "missing_field":
        del maps["plastic_mask"]
    elif mutation == "float_map":
        maps["plastic_kc_indices"] = maps["plastic_kc_indices"].astype(float)
    elif mutation == "duplicate_body":
        maps["body_ids"][0] = maps["body_ids"][1]
    else:
        maps["sample"] = maps["sample"][:-1]
    with pytest.raises(ValueError):
        run.validate_maps(maps)


@pytest.mark.parametrize("broken", ["hash", "size", "missing", "symlink", "escape", "duplicate"])
def test_bound_inputs_cannot_silently_change_or_alias(tmp_path, broken):
    path = tmp_path / "source.txt"
    path.write_text("frozen bytes")
    binding = run.binding(path, tmp_path)
    bindings = [binding]
    run.verify_bindings(bindings, tmp_path)
    if broken == "hash":
        path.write_text("changedbytes")
    elif broken == "size":
        binding["bytes"] += 1
    elif broken == "missing":
        path.unlink()
    elif broken == "symlink":
        target = tmp_path / "target.txt"
        path.rename(target)
        path.symlink_to(target)
    elif broken == "escape":
        binding["path"] = "../source.txt"
    else:
        bindings.append(copy.deepcopy(binding))
    with pytest.raises((ValueError, FileNotFoundError)):
        run.verify_bindings(bindings, tmp_path)


def test_exclusive_artifacts_never_overwrite_previous_identity(tmp_path):
    path = tmp_path / "identity.json"
    run.write_json(path, {"frozen": True})
    with pytest.raises(FileExistsError):
        run.write_json(path, {"frozen": False})
    assert json.loads(path.read_text()) == {"frozen": True}


def small_rows(offset):
    rows = []
    for i in range(32):
        gains = np.array([1 + offset, 1.0], np.float32)
        rows.append(dict(**run.expected_rows()[i], gains=gains, double_gains=gains.astype(float)))
    return rows


@pytest.mark.parametrize("offset,expected", [(0.0, "all_pass"), (0.001, "all_fail"), (-0.001, "all_fail")])
def test_all_eight_panel_channel_guards_use_exact_published_totals(offset, expected):
    result = run.guard_summary(small_rows(offset), [np.array([True, False]), np.array([False, True])])
    assert len(result) == 8
    for name, cell in result.items():
        assert cell["conditional"]["classification"] == (expected if name.endswith("home") else "all_pass")
        assert cell["point_pass"] == (expected == "all_pass" or name.endswith("away"))
        assert len(cell["ticks"]) == 8


@pytest.mark.parametrize("broken", ["missing", "duplicate_label", "wrong_dtype", "outside"])
def test_incomplete_or_invalid_guard_matrix_cannot_qualify(broken):
    rows = small_rows(0)
    if broken == "missing":
        rows.pop()
    elif broken == "duplicate_label":
        rows[0]["seed_set"] = "alt"
    elif broken == "wrong_dtype":
        rows[0]["gains"] = rows[0]["gains"].astype(float)
    else:
        rows[0]["gains"][0] = 2
    with pytest.raises(ValueError):
        run.guard_summary(rows, [np.array([True, False]), np.array([False, True])])


def test_nonfinite_json_cannot_publish_success(tmp_path):
    with pytest.raises(ValueError):
        run.write_json(tmp_path / "bad.json", {"metric": float("nan")})


def test_identity_changes_with_protocol_or_source_and_preserves_row_order():
    identity = {"rows": [{"i": 1}, {"i": 2}], "bindings": [{"sha256": "a"}]}
    original = run.study_id(identity)
    assert original == run.study_id(copy.deepcopy(identity))
    identity["rows"].reverse()
    assert run.study_id(identity) != original
    identity["rows"].reverse()
    identity["bindings"][0]["sha256"] = "b"
    assert run.study_id(identity) != original


@pytest.mark.parametrize("field", ["panel", "run_id", "game", "seed_set", "seed"])
@pytest.mark.parametrize("position", [0, 15, 16, 31])
def test_any_changed_semantic_trial_identity_fails(field, position):
    rows = run.expected_rows()
    run.validate_rows(rows)
    rows[position][field] = rows[(position + 2) % 32][field]
    if rows[position] == run.expected_rows()[position]:
        rows[position][field] = "wrong"
    with pytest.raises(ValueError):
        run.validate_rows(rows)


@pytest.mark.parametrize("position", [0, 16])
def test_boolean_cannot_alias_integer_panel(position):
    rows = run.expected_rows()
    rows[position]["panel"] = bool(rows[position]["panel"])
    with pytest.raises(ValueError):
        run.validate_rows(rows)


def configure_fake_execution(tmp_path, monkeypatch):
    """Actual orchestration with labeled synthetic arrays, no simulator or historical read."""
    cap, evidence, here = [tmp_path / name for name in ("capture", "evidence", "result")]
    for path in (cap, evidence, here):
        path.mkdir()
    maps = maps_fixture()
    fine = dict(
        trace=np.zeros((2000, 4774), np.int32),
        gains=np.ones(8866, np.float32),
        counts=np.zeros(166700, np.int32),
        dan_counts=np.zeros(24, np.int32),
        pulse_times_ms=np.empty(0),
        pulse_dan_indices=np.empty(0),
    )
    capture = dict(rows=run.expected_rows(), saved=[{}])
    for i in range(32):
        path = cap / f"fine_{i:02d}.npz"
        path.write_bytes(b"synthetic fixture; arrays supplied by the test")
        capture["saved"].append(dict(file=path.name, sha256=run.sha(path)))
    (cap / "summary.json").write_text(json.dumps(capture))
    source = tmp_path / "bound.txt"
    source.write_text("bound fixture")
    identity = dict(
        rows=run.expected_rows(),
        wall_cap_seconds=1200,
        helper_evaluations=32,
        bindings=[run.binding(source, tmp_path)],
    )
    sid = run.study_id(identity)
    plan = here / "plan.json"
    plan.write_text(json.dumps(dict(identity=identity, run_id=sid)))
    for name, value in dict(ROOT=tmp_path, HERE=here, CAP=cap, EVIDENCE=evidence, PLAN=plan).items():
        monkeypatch.setattr(run, name, value)
    original_binding, original_verify = run.binding, run.verify_bindings
    monkeypatch.setattr(run, "binding", lambda path, root=None: original_binding(path, tmp_path))
    monkeypatch.setattr(run, "verify_bindings", lambda items, **kw: original_verify(items, tmp_path, **kw))

    class Archive:
        def __init__(self, values):
            self.values, self.files = values, list(values)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def __getitem__(self, key):
            return self.values[key]

    monkeypatch.setattr(run.np, "load", lambda path, **kw: Archive(maps if "samples" in str(path) else fine))
    calls = []

    def fake_shadow(*args, **kwargs):
        calls.append(len(calls))
        return dict(
            gains=np.ones(8866, np.float32),
            double_gains=np.ones(8866),
            phases=np.zeros((4, 8866, 8)),
            conditional_bound_counts=np.zeros((2, 8866), np.int64),
            publication_counts=maps["plastic_mask"].astype(np.int64) * 1501,
            rounding_ambiguous=np.zeros(8866, np.int64),
            estimated_integration_error=np.zeros((3, 8866)),
            fields=["synthetic"] * 8,
            accepted_substeps=0,
            attempted_substeps=0,
        )

    monkeypatch.setattr(run, "shadow", fake_shadow)
    return here / sid, calls, source


@pytest.mark.parametrize("fault", ["source", "helper", "row", "summary", "completion"])
def test_execution_failure_records_only_durably_completed_rows(tmp_path, monkeypatch, capsys, fault):
    output, calls, source = configure_fake_execution(tmp_path, monkeypatch)
    original_write = run.write_json
    if fault == "source":
        source.write_text("tampered")
    elif fault == "helper":

        def broken(*args, **kwargs):
            calls.append(0)
            raise ArithmeticError("synthetic helper failure")

        monkeypatch.setattr(run, "shadow", broken)
    else:
        filename = {"row": "row_00.json", "summary": "summary.json", "completion": "completion.json"}[fault]

        def failing_write(path, value):
            if path.name == filename:
                raise OSError("synthetic persistence failure")
            return original_write(path, value)

        monkeypatch.setattr(run, "write_json", failing_write)
    assert run.execute() == 1
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["screen"] == "invalid_or_incomplete"
    if fault in ("summary", "completion"):
        assert len(calls) == 32
        assert json.loads((output / "terminal-error.json").read_text())["status"] == "failed"
    else:
        summary = json.loads((output / "summary.json").read_text())
        assert summary["status"] == "failed" and summary["completed"] == 0
        assert summary["attempted"] == (0 if fault == "source" else 1)
        assert len(calls) == summary["attempted"]
    if fault == "row":
        assert len((output / "attempts.jsonl").read_text().splitlines()) == 1
        assert (output / "shadow_00.npz").is_file()


@pytest.mark.parametrize("phase", ["summary.json", "completion.json"])
def test_terminal_persistence_cannot_cross_cap_and_leave_a_valid_completion(
    tmp_path, monkeypatch, capsys, phase
):
    output, calls, _ = configure_fake_execution(tmp_path, monkeypatch)
    original_clock, original_write = run.time.monotonic, run.write_json
    shift = [0.0]
    monkeypatch.setattr(run.time, "monotonic", lambda: original_clock() + shift[0])

    def delayed_write(path, value):
        original_write(path, value)
        if path.name == phase:
            shift[0] += 1201

    monkeypatch.setattr(run, "write_json", delayed_write)
    assert run.execute() == 1 and len(calls) == 32
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["screen"] == "invalid_or_incomplete"
    assert json.loads((output / "summary.json").read_text())["status"] == "computed"
    failure = json.loads((output / "terminal-error.json").read_text())
    assert failure["status"] == "budget_stopped" and failure["elapsed_seconds"] >= 1200


def test_success_requires_completed_journal_and_hash_bound_terminal_receipt(tmp_path, monkeypatch):
    output, calls, _ = configure_fake_execution(tmp_path, monkeypatch)
    assert run.execute() == 0 and len(calls) == 32
    summary = json.loads((output / "summary.json").read_text())
    completion = json.loads((output / "completion.json").read_text())
    assert summary["status"] == "computed" and summary["completed"] == 32
    assert completion["status"] == "complete" and completion["completed"] == 32
    assert completion["summary_sha256"] == run.sha(output / "summary.json")
    assert len((output / "attempts.jsonl").read_text().splitlines()) == 64
    assert not (output / "terminal-error.json").exists()
    with pytest.raises(FileExistsError):
        run.execute()
    assert len(calls) == 32
