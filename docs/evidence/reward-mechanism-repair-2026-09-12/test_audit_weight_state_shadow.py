"""Synthetic artifact mutation tests; never opens preserved circuit histories."""

import copy
import hashlib
import json

import numpy as np
import pytest

import audit_weight_state_shadow as audit


def blank_arrays():
    n = 5
    a = {
        k: np.ones(n, dtype=d)
        for k, d in (
            ("gains", "float32"),
            ("double_gains", "float64"),
            ("electrical_gains", "float32"),
            ("electrical_double_gains", "float64"),
            ("gain_lower", "float64"),
            ("gain_upper", "float64"),
            ("original_gains", "float32"),
        )
    }
    a.update(
        phase_end_double_gains=np.ones((4, n)),
        phases=np.zeros((4, n, 8)),
        grouped=np.zeros((4, 8, 8)),
        publication_counts=np.array([1501] * 4 + [0]),
        conditional_bound_counts=np.zeros((2, n), np.int64),
        estimated_integration_error=np.zeros((3, n)),
        rounding_ambiguous=np.zeros(n, np.int64),
    )
    a["gain_lower"][:4] = np.nextafter(1 - 1e-11, -np.inf)
    a["gain_upper"][:4] = np.nextafter(1 + 1e-11, np.inf)
    return a


MASK = np.array([1, 1, 1, 1, 0], bool)
GROUPS = np.array([0, 1, 2, 4, 5])


def test_zero_fixture():
    assert audit.check_arrays(blank_arrays(), MASK, GROUPS)["publications"] == 6004


@pytest.mark.parametrize(
    "field,index,value",
    [
        ("gains", 4, 1.1),
        ("double_gains", 0, np.nan),
        ("double_gains", 0, 1.6),
        ("publication_counts", 0, 1500),
        ("publication_counts", 4, 1),
        ("phases", (0, 0, 0), -1),
        ("phases", (0, 0, 1), 1),
        ("phases", (0, 0, 2), 1e-5),
        ("phases", (0, 0, 3), 1e-5),
        ("phases", (0, 0, 4), 2**-24),
        ("phases", (0, 0, 5), 0.5),
        ("phases", (0, 0, 6), 151),
        ("phases", (3, 0, 7), 2),
        ("phases", (1, 4, 0), 1),
        ("phase_end_double_gains", (2, 0), 1.1),
        ("electrical_gains", 0, 1.1),
        ("gain_lower", 0, 1),
        ("gain_upper", 0, 1),
        ("conditional_bound_counts", (0, 0), 1502),
        ("conditional_bound_counts", (0, 4), 1),
        ("rounding_ambiguous", 0, 1),
        ("estimated_integration_error", (0, 0), -1),
        ("grouped", (0, 0, 0), 1),
    ],
)
def test_corrupt_array_families(field, index, value):
    a = blank_arrays()
    a[field][index] = value
    with pytest.raises((ValueError, AssertionError)):
        audit.check_arrays(a, MASK, GROUPS)


@pytest.mark.parametrize("field", list(blank_arrays()))
def test_array_missing_and_wrong_shape(field):
    a = blank_arrays()
    del a[field]
    with pytest.raises(ValueError):
        audit.check_arrays(a, MASK, GROUPS)
    a = blank_arrays()
    a[field] = a[field][:-1]
    with pytest.raises(ValueError):
        audit.check_arrays(a, MASK, GROUPS)


@pytest.mark.parametrize("field", ["gains", "double_gains", "publication_counts", "phases"])
def test_storage_type_is_contract(field):
    a = blank_arrays()
    a[field] = a[field].astype(np.float16)
    with pytest.raises(ValueError):
        audit.check_arrays(a, MASK, GROUPS)


def test_endpoint_counter_cannot_claim_zero():
    a = blank_arrays()
    # A complete, internally reconciled tail transition to the inclusive bound.
    a["gains"][0] = a["double_gains"][0] = 0.5
    a["phase_end_double_gains"][3, 0] = 0.5
    a["gain_lower"][0] = 0.5
    a["gain_upper"][0] = np.nextafter(0.5 + 1e-11, np.inf)
    a["phases"][3, 0, 1:5] = -0.5
    a["phases"][3, 0, 5] = 1
    a["conditional_bound_counts"][0, 0] = 1
    a["grouped"][3, 0] = a["phases"][3, 0]
    audit.check_arrays(a, MASK, GROUPS)
    a["conditional_bound_counts"][0, 0] = 0
    with pytest.raises(ValueError):
        audit.check_arrays(a, MASK, GROUPS)


def terminal_fixture(tmp_path):
    identity = dict(analysis="synthetic-only")
    plan = dict(identity=identity, run_id=audit.study_id(identity))
    audit.write_json(tmp_path / "identity.json", plan)
    saved, journal = [], []
    for i in range(32):
        p = tmp_path / f"shadow_{i:02d}.npz"
        p.write_bytes(b"synthetic placeholder, arrays not opened")
        item = audit.binding(p, tmp_path)
        saved.append(item)
        audit.write_json(tmp_path / f"row_{i:02d}.json", dict(index=i))
        journal.extend(
            [
                dict(event="attempt", index=i, source=f"fine_{i:02d}.npz", elapsed=i * 2),
                dict(event="complete", index=i, artifact=item, elapsed=i * 2 + 1),
            ]
        )
    (tmp_path / "attempts.jsonl").write_text("".join(json.dumps(r) + "\n" for r in journal))
    audit.write_json(
        tmp_path / "summary.json",
        dict(
            run_id=plan["run_id"],
            status="computed",
            error=None,
            attempted=32,
            completed=32,
            saved=saved,
            elapsed_seconds=65,
            circuit_calls=0,
            native_calls=0,
            network_requests=0,
        ),
    )
    audit.write_json(
        tmp_path / "completion.json",
        dict(
            run_id=plan["run_id"],
            status="complete",
            attempted=32,
            completed=32,
            elapsed_through_summary_seconds=66,
            summary_sha256=audit.sha(tmp_path / "summary.json"),
        ),
    )
    return plan


def test_terminal_valid(tmp_path):
    plan = terminal_fixture(tmp_path)
    assert audit.check_terminal(tmp_path, plan, tmp_path)["status"] == "computed"


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_completion",
        "error_marker",
        "stale_summary",
        "wrong_status",
        "at_cap",
        "nan_clock",
        "count",
        "journal_drop",
        "journal_swap",
        "journal_backwards",
        "journal_source",
        "extra_row",
        "missing_pair",
        "changed_npz",
        "identity",
    ],
)
def test_terminal_failure_families(tmp_path, mutation):
    plan = terminal_fixture(tmp_path)
    completion = tmp_path / "completion.json"
    if mutation == "missing_completion":
        completion.unlink()
    elif mutation == "error_marker":
        (tmp_path / "terminal-error.json").write_text("{}")
    elif mutation == "stale_summary":
        with (tmp_path / "summary.json").open("a") as stream:
            stream.write(" ")
    elif mutation in ("wrong_status", "at_cap", "nan_clock", "count"):
        value = json.loads(completion.read_text())
        key, v = {
            "wrong_status": ("status", "computed"),
            "at_cap": ("elapsed_through_summary_seconds", 1200),
            "nan_clock": ("elapsed_through_summary_seconds", float("nan")),
            "count": ("completed", 31),
        }[mutation]
        value[key] = v
        completion.write_text(json.dumps(value))
    elif mutation.startswith("journal"):
        p = tmp_path / "attempts.jsonl"
        rows = [json.loads(line) for line in p.read_text().splitlines()]
        if mutation == "journal_drop":
            rows.pop()
        if mutation == "journal_swap":
            rows[0], rows[1] = rows[1], rows[0]
        if mutation == "journal_backwards":
            rows[3]["elapsed"] = 0
        if mutation == "journal_source":
            rows[0]["source"] = "fine_01.npz"
        p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    elif mutation == "extra_row":
        (tmp_path / "row_32.json").write_text("{}")
    elif mutation == "missing_pair":
        (tmp_path / "row_31.json").unlink()
    elif mutation == "changed_npz":
        (tmp_path / "shadow_31.npz").write_bytes(b"different")
    else:
        plan = copy.deepcopy(plan)
        plan["identity"]["analysis"] = "changed"
    with pytest.raises((ValueError, FileNotFoundError)):
        audit.check_terminal(tmp_path, plan, tmp_path)


@pytest.mark.parametrize("path", ["../x", "/tmp/x", "a/../../x", "a/./b"])
def test_binding_rejects_noncanonical_paths(tmp_path, path):
    with pytest.raises(ValueError):
        audit.verify_bindings([dict(path=path, bytes=0, sha256="0" * 64)], tmp_path)


def test_binding_symlink_duplicate_and_byte_hash(tmp_path):
    p = tmp_path / "x"
    p.write_bytes(b"one")
    b = audit.binding(p, tmp_path)
    audit.verify_bindings([b], tmp_path)
    with pytest.raises(ValueError):
        audit.verify_bindings([b, b], tmp_path)
    p.write_bytes(b"two")
    with pytest.raises(ValueError):
        audit.verify_bindings([b], tmp_path)
    p.unlink()
    p.symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError):
        audit.verify_bindings([b], tmp_path)


def test_selection_and_cold_event_population_mass():
    groups = np.array([4, 0, 1, 2, 4, 0, 1, 2, 0])
    assert audit.select_edges(groups) == [5, 6, 7, 4]
    maps = dict(
        plastic_kc_indices=np.array([0]),
        plastic_compartments=np.array([0]),
        kc_columns=np.array([0]),
        dan_columns=np.array([1, 2, 3]),
        dan_compartments=np.array([0, 0, 1]),
    )
    trace = np.zeros((2000, 4), np.int32)
    trace[499, :] = 1
    trace[500, [0, 1, 2, 3]] = 1
    trace[1999, [0, 1]] = 1
    k, d, w = audit.edge_events(trace, maps, 0)
    np.testing.assert_array_equal(k, [0, 299.8])
    np.testing.assert_array_equal(d, [0, 0, 299.8])
    np.testing.assert_array_equal(w, [0.5, 0.5, 0.5])


def test_reference_comparison_absolute_boundary():
    a = blank_arrays()
    ref = dict(
        gain=1.0,
        electrical_gain=1.0,
        positive=0.0,
        negative=0.0,
        electrical_positive=0.0,
        electrical_negative=0.0,
        tail_positive=0.0,
        tail_negative=0.0,
    )
    assert audit.compare_reference(a, 0, ref)["passed"]
    ref["positive"] = 2e-11
    assert audit.compare_reference(a, 0, ref)["passed"]
    ref["positive"] = np.nextafter(2e-11, np.inf)
    assert not audit.compare_reference(a, 0, ref)["passed"]


def test_guard_matrix_exact_point_and_conditional():
    rows = []
    for p in range(2):
        for game in range(8):
            for noise in ("base", "alt"):
                rows.append(
                    dict(panel=p, seed_set=noise, gains=np.ones(2, np.float32), double_gains=np.ones(2))
                )
    guards = audit.recompute_guards(rows, [np.array([True, False]), np.array([False, True])])
    assert len(guards) == 8
    assert all(v["point_pass"] and v["conditional"]["classification"] == "all_pass" for v in guards.values())
    assert audit.screen_verdict(guards, 0) == "permits_circuit_consideration"
    assert audit.screen_verdict(guards, 1) == "reject"
    rows.pop()
    with pytest.raises(ValueError):
        audit.recompute_guards(rows, [np.array([True, False]), np.array([False, True])])


def test_no_helper_or_runner_dependency():
    source = audit.__file__
    text = open(source).read()
    assert "from weight_dependent_shadow" not in text
    assert "from run_weight_state_shadow" not in text
    assert hashlib.sha256(text.encode()).hexdigest()


@pytest.mark.parametrize("row", range(32))
@pytest.mark.parametrize("field", ["game", "panel", "seed", "seed_set", "run_id"])
def test_fixed_row_identity_matrix(row, field):
    rows = audit.expected_rows()
    audit.check_rows(rows)
    rows[row][field] = str(rows[row][field]) + "changed"
    with pytest.raises(ValueError):
        audit.check_rows(rows)


def synthetic_maps():
    groups = np.repeat([0, 1, 2, 4, 5, 6], [1585, 316, 2283, 3239, 1438, 5])
    m = dict(
        plastic_groups=groups,
        plastic_kc_indices=np.arange(8866) % 4064,
        plastic_compartments=groups // 4,
        plastic_mask=((groups < 4) | (groups == 4)).astype(int),
        sample=np.arange(4774),
        body_ids=np.arange(4774) + 100000,
        kc_columns=np.arange(4064),
        dan_columns=np.arange(4064, 4088),
        sensory_columns=np.arange(4088, 4774),
        kc_indices=np.arange(4064),
        dan_indices=np.arange(4064, 4088),
        sensory_indices=np.arange(4088, 4774),
        dan_compartments=np.array([0] * 2 + [1] * 22),
    )
    m["body_ids"][4064:4066] = [11327, 11900]
    return m


def test_complete_map_fixture():
    m = synthetic_maps()
    selectors = audit.check_maps(m)
    assert [s.sum() for s in selectors] == [4184, 3239]


@pytest.mark.parametrize(
    "field,index,value",
    [
        ("plastic_groups", 0, 1),
        ("plastic_compartments", 0, 1),
        ("plastic_mask", 0, 0),
        ("plastic_mask", 8000, 1),
        ("plastic_kc_indices", 0, 4064),
        ("sample", 0, 1),
        ("sample", 0, 166700),
        ("body_ids", 0, 100001),
        ("body_ids", 4064, 99999),
        ("kc_columns", 0, 1),
        ("dan_columns", 0, 0),
        ("kc_indices", 0, 1),
        ("dan_compartments", 0, 1),
        ("sensory_indices", 0, 0),
    ],
)
def test_anatomical_contract_mutations(field, index, value):
    m = synthetic_maps()
    m[field][index] = value
    with pytest.raises(ValueError):
        audit.check_maps(m)


@pytest.mark.parametrize("train", ["coincident", "kc_first", "dan_first", "last_event"])
def test_nonzero_event_path_against_separate_helper(train):
    # Synthetic-only helper dependency belongs in tests, never in the audit/oracle.
    from weight_dependent_shadow import shadow

    trace = np.zeros((2000, 3), np.int32)
    kt, dt = {
        "coincident": ([500, 900], [500, 900]),
        "kc_first": ([500, 800], [600, 900]),
        "dan_first": ([600, 900], [500, 800]),
        "last_event": ([1999], [1800]),
    }[train]
    trace[kt, 0] = 1
    trace[dt, 1] = 1
    m = dict(
        plastic_kc_indices=np.array([0]),
        plastic_compartments=np.array([0]),
        kc_columns=np.array([0]),
        dan_columns=np.array([1, 2]),
        dan_compartments=np.array([0, 0]),
    )
    value = shadow(
        trace[:, :1],
        trace[:, 1:],
        m["plastic_kc_indices"],
        m["plastic_compartments"],
        m["dan_compartments"],
        np.array([True]),
        np.array([0]),
    )
    a = {k: v for k, v in value.items() if isinstance(v, np.ndarray)}
    a["original_gains"] = np.ones(1, np.float32)
    audit.check_arrays(a, np.array([True]), np.array([0]))
    k, d, w = audit.edge_events(trace, m, 0)
    ref = audit.event_reference(k, d, end_ms=300, dan_weights=w)
    assert audit.compare_reference(a, 0, ref)["passed"]


def test_area_cancellation_cannot_hide_total_error():
    a = blank_arrays()
    # Each phase falls inside the 4e-11 sum comparison, but the complete
    # electrical+tail discrepancy exceeds that same fixed total allowance.
    a["phases"][:, 0, 0] = 3e-11
    a["phases"][:, 0, 2] = 3e-11
    a["grouped"][:, 0] = a["phases"][:, 0]
    with pytest.raises(ValueError):
        audit.check_arrays(a, MASK, GROUPS)


def test_readonly_import_and_exclusive_output_creation(tmp_path):
    directory = tmp_path / "existing"
    directory.mkdir()
    (directory / "preserved").write_bytes(b"unchanged")
    with pytest.raises(FileExistsError):
        audit.execute(tmp_path / "missing", tmp_path / "absent", directory)
    assert (directory / "preserved").read_bytes() == b"unchanged"


def test_failure_record_without_any_reference_execution(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Reference invoked on invalid inputs")

    monkeypatch.setattr(audit, "event_reference", forbidden)
    output = tmp_path / "audit"
    assert audit.execute(tmp_path / "missing-plan", tmp_path / "missing-result", output) == 1
    summary = json.loads((output / "summary.json").read_text())
    assert summary["attempted"] == summary["completed"] == 0
    assert summary["status"] == "invalid_or_incomplete"
    completion = json.loads((output / "completion.json").read_text())
    assert completion["status"] == "failed"
    assert completion["summary_sha256"] == audit.sha(output / "summary.json")


@pytest.mark.parametrize("failure", ["write", "flush"])
def test_completed_reference_requires_durable_journal(tmp_path, failure):
    class BrokenJournal:
        def write(self, value):
            if failure == "write":
                raise OSError("synthetic journal write failure")

        def flush(self):
            if failure == "flush":
                raise OSError("synthetic journal flush failure")

    references = []
    ref = dict(index=0, edge=17, passed=True)
    with pytest.raises(OSError):
        audit.persist_reference(tmp_path, BrokenJournal(), ref, 1.0, references)
    assert references == []
    assert (tmp_path / "reference_00_17.json").is_file()


@pytest.mark.parametrize("computed", ["reject", "permits_circuit_consideration", "inconclusive"])
def test_numerical_failure_invalidates_interpretation(computed):
    value = audit.audit_verdict([dict(passed=True), dict(passed=False)], computed)
    assert value["status"] == "numerical_failure"
    assert value["screen"] == "invalid_numerical_comparison"
    assert value["computed_shadow_screen"] == computed
    assert audit.audit_verdict([dict(passed=True)], computed)["screen"] == computed
