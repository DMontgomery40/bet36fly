"""Synthetic-only, independent ODE and input-contract tests. Never run a neural engine."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import solve_ivp

HERE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("rate_adaptation_shadow", HERE / "rate_adaptation_shadow.py")
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)


def ode_interval(state, duration):
    """Independent adaptive ODE; no production moment/crossing formula is reused."""
    k, u, d, b, v = state

    def rhs(_, z):
        rk, ek, rd, baseline, ed, positive, negative = z
        dp = max(rd - baseline, 0.0)
        return [
            -0.01 * rk,
            rk - 0.002 * ek,
            -0.01 * rd,
            0.002 * (rd - baseline),
            dp - 0.002 * ed,
            ed * rk,
            ek * dp,
        ]

    end = 20000.0 if np.isinf(duration) else duration
    result = solve_ivp(
        rhs, [0.0, end], [k, u, d, b, v, 0.0, 0.0], method="DOP853", rtol=2e-13, atol=2e-14, max_step=2.0
    )
    assert result.success
    return result.y[:, -1]


@pytest.mark.parametrize(
    "state",
    [
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (0.01, 0.0, 0.01, 0.0, 0.0),
        (0.02, 0.3, 0.01, 0.02, 0.4),
        (0.02, 0.3, 0.01, 0.01, 0.4),
        (0.02, 0.3, 0.010000001, 0.01, 0.4),
        (0.02, 0.3, 0.012, 0.01, 0.4),
        (0.3, 3.0, 0.2, 0.001, 0.2),
        (0.01, 0.0, 0.0, 0.0, 0.3),
    ],
)
@pytest.mark.parametrize("duration", [0.000001, 0.2, 20.0, 400.0, np.inf])
def test_interval_states_and_true_product_areas_against_independent_ode(state, duration):
    expected = ode_interval(state, duration)
    actual = m.interval(*state, duration)
    np.testing.assert_allclose(actual["state"], expected[:5], atol=2e-11, rtol=2e-10)
    np.testing.assert_allclose([actual["positive"], actual["negative"]], expected[5:], atol=2e-10, rtol=2e-10)
    assert actual["positive"] >= 0 and actual["negative"] >= 0
    assert np.isclose(actual["signed"], actual["positive"] - actual["negative"], atol=2e-12)


def raster(kc_events=(), dan_events=(), *, n_kc=1, n_dan=1):
    k = np.zeros((2000, n_kc), np.uint8)
    d = np.zeros((2000, n_dan), np.uint8)
    for time, col in kc_events:
        k[round(time / 0.2), col] = 1
    for time, col in dan_events:
        d[round(time / 0.2), col] = 1
    return k, d


def run(k, d, **kwargs):
    return m.shadow(
        k,
        d,
        np.array([0]),
        np.array([0]),
        np.zeros(d.shape[1], int),
        np.ones(1, np.uint8),
        np.array([0]),
        **kwargs,
    )


@pytest.mark.parametrize("events", [([], []), ([(120.0, 0)], []), ([], [(120.0, 0)])])
def test_silence_or_single_partner_cannot_write_gain(events):
    a = run(*raster(*events))
    np.testing.assert_array_equal(a["gains"], np.ones(1, np.float32))
    assert not a["edge_phases"].any()


def test_pre_onset_history_retained_without_pre_onset_writes_and_tail_is_present():
    a = run(*raster([(20.0, 0)], [(80.0, 0)]))
    assert a["onset_kc"].sum() > 0 and a["onset_dan"].sum() > 0
    np.testing.assert_array_equal(a["onset_gains"], np.ones(1, np.float32))
    np.testing.assert_array_equal(a["onset_double_gains"], np.ones(1))
    assert a["edge_phases"][3, 0, :2].sum() > 0
    np.testing.assert_allclose(
        a["edge_phases"][:, 0, 2].sum(), a["double_gains"][0] - 1, atol=2e-12, rtol=2e-10
    )


@pytest.mark.parametrize("order", [False, True])
def test_event_order_full_tail_matches_independent_ode_history(order):
    kt, dt = (120.0, 160.0) if order else (160.0, 120.0)
    a = run(*raster([(kt, 0)], [(dt, 0)]))
    state = np.zeros(5)
    positive = negative = 0.0
    last = 0.0
    for time in sorted({kt, dt}):
        segment = ode_interval(state, time - last)
        state = segment[:5]
        positive += segment[5]
        negative += segment[6]
        state[0] += 0.01 if time == kt else 0.0
        state[2] += 0.01 if time == dt else 0.0
        last = time
    tail = ode_interval(state, np.inf)
    expected = 0.0005 * 0.96 * (positive + tail[5] - negative - tail[6])
    np.testing.assert_allclose(a["edge_phases"][..., 2].sum(), expected, atol=2e-12, rtol=2e-10)
    assert a["gains"][0] == np.float32(1 + expected)


def test_unequal_dan_population_uses_per_cell_mean_and_channels_are_isolated():
    k, d = raster([(120.0, 0)], [(160.0, 0), (160.0, 1)], n_dan=24)
    d[:, 2:] = d[:, :1]
    a = m.shadow(
        k,
        d,
        np.array([0, 0]),
        np.array([0, 1]),
        np.array([0, 0] + [1] * 22),
        np.ones(2, np.uint8),
        np.array([0, 4]),
    )
    np.testing.assert_array_equal(a["gains"][:1], a["gains"][1:])
    np.testing.assert_array_equal(a["edge_phases"][:, :1], a["edge_phases"][:, 1:])
    d[:, 2:] = 0
    b = m.shadow(
        k,
        d,
        np.array([0, 0]),
        np.array([0, 1]),
        np.array([0, 0] + [1] * 22),
        np.ones(2, np.uint8),
        np.array([0, 4]),
    )
    assert b["gains"][1] == 1 and b["gains"][0] != 1


def test_mask_learning_off_reset_replay_and_inputs_are_immutable():
    k, d = raster([(20.0, 0), (180.0, 0)], [(80.0, 0), (120.0, 0)])
    before = (k.tobytes(), d.tobytes())
    initial = np.array([1.13, 0.83], np.float32)
    args = (
        k,
        d,
        np.array([0, 0]),
        np.array([0, 0]),
        np.array([0]),
        np.array([1, 0], np.uint8),
        np.array([0, 2]),
    )
    a, b = (m.shadow(*args, initial=initial) for _ in range(2))
    for key in a:
        np.testing.assert_array_equal(a[key], b[key])
    assert a["gains"][1].tobytes() == initial[1].tobytes()
    off = m.shadow(*args, initial=initial, learning=False)
    np.testing.assert_array_equal(off["gains"], initial)
    np.testing.assert_array_equal(a["endpoint_kc"], off["endpoint_kc"])
    np.testing.assert_array_equal(a["endpoint_dan"], off["endpoint_dan"])
    assert not off["edge_phases"].any()
    assert before == (k.tobytes(), d.tobytes())
    reset = m.shadow(*args, initial=a["gains"])
    np.testing.assert_array_equal(a["onset_kc"], reset["onset_kc"])
    np.testing.assert_array_equal(a["onset_dan"], reset["onset_dan"])


@pytest.mark.parametrize("which", ["shape", "negative", "two", "float", "nan", "empty"])
def test_invalid_raster_family_fails_before_computation(which):
    k, d = raster()
    if which == "shape":
        k = k[:-1]
    if which == "negative":
        k = k.astype(int)
        k[0, 0] = -1
    if which == "two":
        d[0, 0] = 2
    if which == "float":
        k = k.astype(float)
    if which == "nan":
        k = k.astype(float)
        k[0, 0] = np.nan
    if which == "empty":
        d = d[:, :0]
    with pytest.raises(ValueError):
        run(k, d)


@pytest.mark.parametrize("mutation", ["pk", "pc", "groups", "mask", "initial", "learning"])
def test_mapping_and_policy_contract_rejects_invalid_families(mutation):
    k, d = raster()
    args = [k, d, np.array([0]), np.array([0]), np.array([0]), np.array([1], np.uint8), np.array([0])]
    kwargs = {}
    if mutation == "pk":
        args[2] = np.array([1])
    if mutation == "pc":
        args[3] = np.array([-1])
    if mutation == "groups":
        args[6] = np.array([4])
    if mutation == "mask":
        args[5] = np.array([2])
    if mutation == "initial":
        kwargs["initial"] = [1.50001]
    if mutation == "learning":
        kwargs["learning"] = "yes"
    with pytest.raises(ValueError):
        m.shadow(*args, **kwargs)


@pytest.mark.parametrize(
    "state", [(0.2, 4.0, 0.2, 0.01, 3.0), (0.2, 4.0, 0.001, 0.01, 3.0), (0.01, 0.0, 0.01, 0.0, 0.0)]
)
@pytest.mark.parametrize("silence", [0.000001, 0.2, 100.0, 400.0, 1000.0])
def test_appended_silence_plus_complete_tail_preserves_unbounded_areas(state, silence):
    whole = m.interval(*state, np.inf)
    head = m.interval(*state, silence)
    tail = m.interval(*head["state"], np.inf)
    for field in ("positive", "negative", "signed"):
        np.testing.assert_allclose(head[field] + tail[field], whole[field], atol=2e-10, rtol=2e-10)
    gain = 1 + m.SCALE * whole["signed"]
    if 0.5 < gain < 1.5:
        assert np.float32(gain) == np.float32(1 + m.SCALE * (head["signed"] + tail["signed"]))


@pytest.mark.parametrize(
    "initial,delta,expected,counts",
    [
        (1.0, -0.6, 0.5, (1, 0)),
        (1.0, 0.6, 1.5, (0, 1)),
        (1.0, -0.5, 0.5, (1, 0)),
        (1.0, 0.5, 1.5, (0, 1)),
        (1.0, -0.5 + 1e-9, 0.5, (1, 0)),
        (1.0, 0.5 - 1e-9, 1.5, (0, 1)),
        (1.0, 0.01, 1.01, (0, 0)),
    ],
)
def test_inclusive_lower_upper_rounding_only_and_regular_publications(initial, delta, expected, counts):
    g, f, applied, pub, low, high = m.publish(
        np.array([initial]), np.array([initial], np.float32), np.array([delta]), np.ones(1, bool)
    )
    assert f[0] == np.float32(expected)
    assert (int(low[0]), int(high[0])) == counts
    assert applied[0] == g[0] - initial
    assert pub[0] == float(f[0]) - initial


def test_sub_ulp_accumulates_and_contact_recovery_keeps_prior_observations():
    g, f = np.ones(1), np.ones(1, np.float32)
    low = high = 0
    for delta in [1e-9] * 100:
        g, f, _, _, lo, hi = m.publish(g, f, np.array([delta]), np.ones(1, bool))
        low += int(lo.sum())
        high += int(hi.sum())
    assert f[0] > 1 and low == high == 0
    for delta in [-1.0, 0.2, 1.0, -0.2]:
        g, f, _, _, lo, hi = m.publish(g, f, np.array([delta]), np.ones(1, bool))
        low += int(lo.sum())
        high += int(hi.sum())
    assert low == high == 1 and f[0] == np.float32(1.3)


def test_subinterval_opposite_deltas_are_summed_before_one_publication():
    # Clamping at an internal mathematical split would incorrectly yield0.9.
    a = m.publish(np.ones(1), np.ones(1, np.float32), np.array([0.8 - 0.6]), np.ones(1, bool))
    assert a[1][0] == np.float32(1.2) and not a[4].any() and not a[5].any()
    first = m.publish(np.ones(1), np.ones(1, np.float32), np.array([0.8]), np.ones(1, bool))
    wrong = m.publish(first[0], first[1], np.array([-0.6]), np.ones(1, bool))
    assert wrong[1][0] != a[1][0]


def test_exact_onset_endpoint_coincidence_and_permuted_groups():
    k, d = raster([(99.8, 0), (100.0, 1), (399.8, 0)], [(99.8, 0), (100.0, 0), (399.8, 0)], n_kc=2)
    args = (
        k,
        d,
        np.array([0, 1, 0]),
        np.zeros(3, int),
        np.array([0]),
        np.array([1, 1, 0], np.uint8),
        np.array([0, 2, 0]),
    )
    a = m.shadow(*args)
    permutation = np.array([2, 0, 1])
    p_args = args[:2] + tuple(x[permutation] if i != 2 else x for i, x in enumerate(args[2:]))
    b = m.shadow(*p_args)
    np.testing.assert_array_equal(a["gains"][permutation], b["gains"])
    np.testing.assert_array_equal(a["group_phases"], b["group_phases"])
    assert a["onset_kc"][0].sum() > 0 and a["onset_kc"][1].sum() == 0
    assert a["endpoint_kc"][0].sum() > 0
    with pytest.raises(ValueError):
        run(np.vstack((k, np.zeros((1, 2), np.uint8))), np.vstack((d, np.zeros((1, 1), np.uint8))))


@pytest.mark.parametrize("value", [-1.0, np.nan, np.inf])
@pytest.mark.parametrize("field", range(5))
def test_invalid_state_family_fails_closed(value, field):
    state = [0.01, 0.3, 0.02, 0.001, 0.2]
    state[field] = value
    with pytest.raises(ValueError):
        m.interval(*state, 0.2)


def test_finite_pulse_offset_preserves_positive_eligibility_after_rectifier_turns_off():
    state = np.zeros(5)
    for t in range(1500):
        state[0] += 0.01 if t % 50 == 0 else 0.0
        state[2] += 0.01 if t < 100 and t % 10 == 0 else 0.0
        state = np.array(m.interval(*state, 0.2)["state"])
    assert state[2] < state[3] and state[4] > 0
    tail = m.interval(*state, np.inf)
    assert tail["positive"] > 0 and tail["negative"] == 0
    assert tail["signed"] > 0


def test_all_eight_class_channel_group_labels_and_swapped_family_rejection():
    k, d = raster([(120.0, 0)], [(160.0, 0), (180.0, 1)], n_dan=2)
    for groups in (np.arange(8), np.array([0, 1, 2, 4, 5, 6]), np.array([3, 7])):
        pc = groups // 4
        args = (
            k,
            d,
            np.zeros(len(groups), int),
            pc,
            np.array([0, 1]),
            np.ones(len(groups), np.uint8),
            groups,
        )
        a = m.shadow(*args)
        np.testing.assert_allclose(a["group_phases"].sum(1), a["edge_phases"].sum(1), atol=1e-15)
        with pytest.raises(ValueError):
            m.shadow(*args[:3], 1 - pc, *args[4:])


def test_shared_kc_states_do_not_depend_on_channel_order_or_rectifier_splitting():
    k, d = raster([(20.0, 0), (180.0, 0)], [(60.0, 0), (120.0, 1)], n_dan=2)
    common = (np.array([0, 0]), np.array([0, 1]), np.array([0, 1]), np.ones(2, np.uint8), np.array([0, 4]))
    a, b = (m.shadow(k, x, *common) for x in (d, d[:, ::-1]))
    np.testing.assert_array_equal(a["onset_kc"], b["onset_kc"])
    np.testing.assert_array_equal(a["endpoint_kc"], b["endpoint_kc"])


@pytest.mark.parametrize(
    "state",
    [(1e308, 1e308, 1e308, 0.0, 1e308), (1e308, 1e308, 0.1, 0.0, 1e308), (0.1, 1e308, 1e308, 0.0, 0.1)],
)
def test_finite_inputs_that_overflow_analytic_products_fail_closed(state):
    with pytest.raises((ArithmeticError, ValueError)):
        m.interval(*state, 0.2)


def test_ordinary_large_finite_states_remain_supported():
    actual = m.interval(100.0, 10000.0, 200.0, 10.0, 20000.0, 0.2)
    expected = ode_interval((100.0, 10000.0, 200.0, 10.0, 20000.0), 0.2)
    np.testing.assert_allclose(actual["state"], expected[:5], atol=2e-11, rtol=2e-10)
    np.testing.assert_allclose([actual["positive"], actual["negative"]], expected[5:], atol=2e-10, rtol=2e-10)


@pytest.mark.parametrize("change", ["content", "size", "digest", "symlink", "ancestor_symlink", "missing"])
def test_bound_file_identity_and_symlink_family(tmp_path, change):
    path = tmp_path / "input.dat"
    path.write_bytes(b"locked bytes")
    binding = m.bind(path)
    assert m.read_bound(binding) == b"locked bytes"
    if change == "content":
        path.write_bytes(b"changed data")
    if change == "size":
        binding["bytes"] += 1
    if change == "digest":
        binding["sha256"] = "0" * 64
    if change == "symlink":
        target = tmp_path / "target"
        path.rename(target)
        path.symlink_to(target)
    if change == "ancestor_symlink":
        link = tmp_path / "alias"
        link.symlink_to(tmp_path, target_is_directory=True)
        binding["path"] = str(link / "input.dat")
    if change == "missing":
        path.unlink()
    with pytest.raises((ValueError, OSError)):
        m.read_bound(binding)


@pytest.mark.parametrize(
    "values",
    [np.array([np.nan]), np.array([np.inf]), np.array([{"payload": "object"}], object), np.array(["text"])],
)
def test_npz_rejects_nonfinite_object_and_non_numeric_family(values):
    import io

    data = io.BytesIO()
    np.savez(data, x=values)
    with pytest.raises(ValueError):
        m.safe_npz(data.getvalue())


@pytest.mark.parametrize(
    "name", ["../escape.npy", "/absolute.npy", "nested/x.npy", "windows\\x.npy", "x.txt"]
)
def test_npz_rejects_unsafe_member_inventory(name):
    import io
    import zipfile

    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        z.writestr(name, b"numeric payload irrelevant")
    with pytest.raises(ValueError):
        m.safe_npz(data.getvalue())


@pytest.mark.parametrize("text", ["NaN", "Infinity", "-Infinity", "1e400", '{"deep":[1e400]}'])
def test_json_rejects_literal_and_overflow_nonfinite_family(text):
    with pytest.raises(ValueError):
        m.json_bytes(text.encode())


def synthetic_manifest(tmp_path, monkeypatch):
    """Boundary fixture only: minimal stand-ins deliberately bypass capture science.

    Full signal mathematics is tested above and independently. This fixture
    tests the real runner's ordering, files, status, partial records and guards.
    """
    import json
    import io

    monkeypatch.setattr(m, "HERE", tmp_path)
    paths = {}
    base = {
        "capture_summary",
        "capture_receipt",
        "samples",
        "calculator",
        "tests",
        "unadapted_calculator",
        "scientific_contract",
        "source_report",
        "numerical_contract",
        "independent_review",
        "independent_oracle",
        "independent_oracle_tests",
    }
    keys = base | {f"{kind}_{i:02d}" for i in range(32) for kind in ("fine", "cold", "continuous")}
    phases = np.zeros((4, 8866, 8))
    prior = dict(
        gains=np.ones(8866, np.float32),
        edge_phases=phases,
        onset_kc=np.zeros((1, 2)),
        endpoint_kc=np.zeros((1, 2)),
    )
    fine = dict(gains=np.ones(8866, np.float32), trace=np.zeros((2000, 1), np.int32))
    maps = dict(
        kc_columns=np.array([0]),
        dan_columns=np.array([0]),
        plastic_kc_indices=np.zeros(8866, int),
        plastic_compartments=np.array([0] * 4184 + [1] * 4682),
        dan_compartments=np.array([0]),
        plastic_mask=np.array([1] * 7423 + [0] * 1443, np.uint8),
        plastic_groups=np.zeros(8866, int),
    )
    for key in keys:
        path = tmp_path / (key + ".dat")
        if key.startswith(("fine_", "cold_", "continuous_")):
            data = io.BytesIO()
            np.savez_compressed(data, **(fine if key.startswith("fine_") else prior))
            path.write_bytes(data.getvalue())
        elif key == "calculator":
            path.write_bytes(Path(m.__file__).read_bytes())
        elif key == "unadapted_calculator":
            path.write_text(
                "import numpy as np\ndef shadow(*args, **kwargs):\n"
                " return dict(gains=np.ones(8866,np.float32),edge_phases=np.zeros((4,8866,8)),"
                "onset_kc=np.zeros((1,2)),endpoint_kc=np.zeros((1,2)))\n"
            )
        else:
            path.write_text("{}")
        paths[key] = path
    for key, constant in [
        ("capture_summary", "CAPTURE_HASH"),
        ("capture_receipt", "RECEIPT_HASH"),
        ("samples", "SAMPLES_HASH"),
    ]:
        monkeypatch.setattr(m, constant, m.bind(paths[key])["sha256"])
    review = dict(
        status="passed",
        scope="synthetic-numerical-and-boundary-only",
        calculator_sha256=m.bind(paths["calculator"])["sha256"],
        tests_sha256=m.bind(paths["tests"])["sha256"],
        oracle_sha256=m.bind(paths["independent_oracle"])["sha256"],
        numerical_contract_sha256=m.bind(paths["numerical_contract"])["sha256"],
    )
    paths["independent_review"].write_text(json.dumps(review))
    manifest = dict(
        schema=1,
        status="preregistered",
        scope="fixed-spike-rejection-only",
        parameters=m.PARAMETERS.copy(),
        rows=m.exact_rows(),
        files={key: m.bind(path) for key, path in paths.items()},
    )
    monkeypatch.setattr(m, "validate_capture_inputs", lambda *args, **kwargs: ({}, maps))

    def fake_shadow(*args, guard=None):
        if guard:
            guard()
        return dict(
            **prior,
            onset_gains=np.ones(8866, np.float32),
            onset_double_gains=np.ones(8866),
            absolute_area=np.zeros(8866),
            excursion_excluded=np.ones(8866, bool),
        )

    monkeypatch.setattr(m, "shadow", fake_shadow)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    checksum = m.bind(path)["sha256"]
    out = tmp_path / "rate-adaptation-shadows" / ("rate-adaptation-shadow-" + checksum[:20])
    return manifest, path, checksum, out, fake_shadow


def test_complete_runner_32_rows_ledger_identity_and_parent_file_preservation(tmp_path, monkeypatch):
    manifest, path, checksum, out, _ = synthetic_manifest(tmp_path, monkeypatch)
    before = {k: m.read_bound(v) for k, v in manifest["files"].items()}
    result = m.execute(path, checksum, out)
    assert result["candidate_evaluations"] == result["attempted_evaluations"] == 32
    assert result["native_calls"] == 0 and result["qualification"] is False
    assert len(result["metrics"]) == 8
    assert [r["row"] for r in result["rows"]] == m.exact_rows()
    assert len(list(out.glob("attempt_*.json"))) == len(list(out.glob("completed_*.json"))) == 32
    assert before == {k: m.read_bound(v) for k, v in manifest["files"].items()}
    with pytest.raises(ValueError):
        m.execute(path, checksum, out)
    with pytest.raises(ValueError):
        m.execute(path, checksum, out.parent / "different-name")


@pytest.mark.parametrize(
    "mutation", ["missing", "duplicate", "order", "seed", "role", "eta", "status", "review"]
)
def test_manifest_selection_configuration_and_review_family_rejects(tmp_path, monkeypatch, mutation):
    manifest, _, _, _, _ = synthetic_manifest(tmp_path, monkeypatch)
    if mutation == "missing":
        manifest["rows"].pop()
    if mutation == "duplicate":
        manifest["rows"][-1] = manifest["rows"][0]
    if mutation == "order":
        manifest["rows"].reverse()
    if mutation == "seed":
        manifest["rows"][0]["seed"] += 1
    if mutation == "role":
        manifest["rows"][0]["seed_set"] = "chosen"
    if mutation == "eta":
        manifest["parameters"]["eta"] *= 2
    if mutation == "status":
        manifest["status"] = "draft-not-authorized"
    if mutation == "review":
        p = Path(manifest["files"]["independent_review"]["path"])
        p.write_text('{"status":"failed"}')
        manifest["files"]["independent_review"] = m.bind(p)
    with pytest.raises(ValueError):
        m.validate_manifest(manifest)


@pytest.mark.parametrize("when", ["candidate_failure", "budget_in_candidate", "input_replacement"])
def test_runner_preserves_partial_attempts_and_fails_changed_inputs(tmp_path, monkeypatch, when):
    manifest, path, checksum, out, original = synthetic_manifest(tmp_path, monkeypatch)
    ticks = [0.0]
    calls = [0]

    def compute(*args, guard=None):
        calls[0] += 1
        if calls[0] == 3:
            if when == "candidate_failure":
                raise RuntimeError("synthetic failure")
            if when == "budget_in_candidate":
                ticks[0] = 601.0
                guard()
            if when == "input_replacement":
                Path(manifest["files"]["fine_00"]["path"]).write_bytes(b"changed")
        return original(*args, guard=guard)

    monkeypatch.setattr(m, "shadow", compute)
    with pytest.raises((ValueError, RuntimeError, TimeoutError)):
        m.execute(path, checksum, out, clock=lambda: ticks[0])
    import json

    failure = json.loads((out / "failure.json").read_text())
    assert failure["status"] == "failed-partial-preserved" and not (out / "summary.json").exists()
    assert failure["attempted_evaluations"] == (32 if when == "input_replacement" else 3)
    assert failure["completed_evaluations"] == (32 if when == "input_replacement" else 2)


@pytest.mark.parametrize(
    "shape,payload", [((100000000,), b""), ((2**62, 2**62), b""), ((1,), b""), ((1,), b"\0" * 16)]
)
def test_npz_declared_allocation_and_payload_mismatch_rejected_before_numpy_allocation(
    shape, payload, monkeypatch
):
    import io
    import zipfile

    header = io.BytesIO()
    np.lib.format.write_array_header_1_0(header, dict(descr="<f8", fortran_order=False, shape=shape))
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        z.writestr("x.npy", header.getvalue() + payload)

    def forbidden(*args, **kwargs):
        raise AssertionError("np.load must not receive invalid allocation")

    monkeypatch.setattr(np, "load", forbidden)
    with pytest.raises(ValueError):
        m.safe_npz(data.getvalue())


def test_npz_valid_numeric_dtypes_shapes_and_fortran_arrays():
    import io

    arrays = dict(
        scalar=np.array(3.0),
        empty=np.zeros((0, 5)),
        binary=np.array([True, False]),
        signed=np.array([-1, 2], np.int64),
        fortran=np.asfortranarray(np.eye(4)),
    )
    data = io.BytesIO()
    np.savez(data, **arrays)
    actual = m.safe_npz(data.getvalue())
    for key in arrays:
        np.testing.assert_array_equal(actual[key], arrays[key])
