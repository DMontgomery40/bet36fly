"""Small independent synthetic tests; no saved history is opened."""

from fractions import Fraction
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest
from scipy.sparse import csr_matrix


def oracle():
    path = Path(__file__).with_name("audit_kc_local_shadow.py")
    assert path.is_file(), "Independent shadow auditor is not implemented"
    spec = importlib.util.spec_from_file_location("audit_kc_local_shadow", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PARAMS = dict(
    tauKCdec=1.0,
    tauinp=1.0,
    tauadapt=1.0,
    adaptscale=0.0,
    tauinh=1.0,
    inhfactor=1.0,
    infp=0.0,
    slf=1.0,
    bline=0.0,
)


def test_rational_counting_endpoint_and_no_lateral_fraction_recurrence():
    h = oracle()
    spikes = np.zeros((2000, 2), np.uint8)
    spikes[[0, 166, 167, 333, 334, 499, 500, 1999], 0] = 1
    result = h.grouped_local(spikes, PARAMS, csr_matrix((2, 2)))
    expected_counts = np.zeros((12, 2), np.int64)
    expected_counts[[0, 1, 2], 0] = 2
    expected_counts[[3, 11], 0] = 1
    np.testing.assert_array_equal(result["counts"], expected_counts)
    calcium = [Fraction(0)]
    for n in expected_counts[:, 0]:
        calcium.append(calcium[-1] * Fraction(29, 30) + Fraction(int(n), 30))
    for state in (0, 1):
        np.testing.assert_allclose(result["states"][:, state, 0], [float(x) for x in calcium], atol=1e-15)
    assert not result["states"][:, 2:].any()
    np.testing.assert_array_equal(result["susceptibility"], np.ones((13, 2)))
    np.testing.assert_array_equal(result["weighted"], spikes)


def test_asymmetric_lateral_orientation_old_state_latency_and_boundary_weight():
    h = oracle()
    spikes = np.zeros((667, 2), np.uint8)
    spikes[0] = 1
    spikes[500, 1] = 1
    adjacency = csr_matrix(([1.0], ([1], [0])), shape=(2, 2))
    result = h.grouped_local(spikes, PARAMS, adjacency)
    first = 1 / 30
    second = 29 / 900
    third = 841 / 27000
    inhibition_second = (first / 30) / (1 + np.exp(first))
    np.testing.assert_allclose(result["states"][1, :2], first)
    np.testing.assert_allclose(result["states"][2, :2], second)
    assert result["states"][2, 3, 0] == 0
    assert result["states"][2, 3, 1] == pytest.approx(inhibition_second, abs=1e-15)
    assert result["states"][3, 1, 1] == pytest.approx(third - inhibition_second / 30, abs=1e-15)
    assert result["weighted"][500, 1] == pytest.approx((third - inhibition_second / 30) / third)
    assert result["weighted"][0, 1] == 1


@pytest.mark.parametrize(
    "broken", ["negative_A", "short_adaptation", "short_inhibition", "negative_weight", "self_weight"]
)
def test_invalid_local_domains_fail_before_claiming_reconstruction(broken):
    h = oracle()
    params = PARAMS.copy()
    matrix = csr_matrix((2, 2))
    if broken == "negative_A":
        params["tauKCdec"] = 0.01
    elif broken == "short_adaptation":
        params["tauadapt"] = 0.01
    elif broken == "short_inhibition":
        params["tauinh"] = 0.01
    elif broken == "negative_weight":
        matrix = csr_matrix(([-1.0], ([0], [1])), shape=(2, 2))
    else:
        matrix = csr_matrix(([1.0], ([0], [0])), shape=(2, 2))
    with pytest.raises(ValueError):
        h.grouped_local(np.zeros((200, 2), np.uint8), params, matrix)


@pytest.mark.parametrize("lag", [-3, -1, 0, 1, 3])
@pytest.mark.parametrize("mass", [0.25, 1.0])
def test_complete_pair_sign_mass_and_masks(lag, mass):
    h = oracle()
    kc, dan = np.zeros((9, 1)), np.zeros((9, 2))
    kc[4, 0] = mass
    dan[4 + lag, 0] = 0.5
    result = h.pair_reference(kc, dan, np.array([0, 0]), np.array([0, 0]), np.array([1, 0]), onset=0)
    delta = (
        -0.0005 * np.sign(lag) * (np.exp(-abs(lag) * 0.2 / 500) - np.exp(-abs(lag) * 0.2 / 100)) * mass * 0.5
    )
    assert result["double_gains"][0] == pytest.approx(1 + delta, abs=1e-15)
    assert result["double_gains"][1] == result["gains"][1] == 1
    np.testing.assert_array_equal(result["gains"], result["double_gains"].astype(np.float32))


def test_pair_cold_onset_and_endpoint_residual_are_independent_impulse_sums():
    h = oracle()
    kc, dan = np.zeros((600, 1)), np.zeros((600, 2))
    kc[[499, 500], 0] = [100, 0.75]
    dan[[499, 503], 1] = [100, 0.25]
    result = h.pair_reference(kc, dan, np.array([0]), np.array([1]), np.array([1]))
    duration = 120.0
    xk, xd = duration - 100.0, duration - 100.6
    rk = 0.75 * np.exp(-xk / 100) / 100
    ek = 0.75 * (np.exp(-xk / 500) - np.exp(-xk / 100)) * 1.25
    rd = 0.25 * np.exp(-xd / 100) / 100
    ed = 0.25 * (np.exp(-xd / 500) - np.exp(-xd / 100)) * 1.25
    np.testing.assert_allclose(result["endpoint_kc"], [[rk, ek]], rtol=0, atol=1e-15)
    np.testing.assert_allclose(result["endpoint_dan"][1], [rd, ed], rtol=0, atol=1e-15)
    tail = 0.0005 * 0.96 * (ed * rk - ek * rd) / 0.012
    assert result["electrical_double_gains"][0] == pytest.approx(result["double_gains"][0] - tail, abs=1e-15)


@pytest.mark.parametrize("change,expected", [(0, True), (1, False), (-1, True)])
def test_exact_integer_guard_equality_and_neighbors(change, expected):
    h = oracle()
    ticks = [5, 3, 1, -1 + change, 0, 0, 0, 0]
    assert h.point_guard(ticks) is expected


def test_exact_f32_totals_do_not_use_rounded_decimal_gain_sums():
    h = oracle()
    ticks = [5, 3, 1, -1, 0, 0, 0, 0]
    gains = np.ones((8, 2), np.float32)
    for i, total in enumerate(ticks):
        if total > 0:
            gains[i] = [1 + (total + 1) / 2**24, 1 - 1 / 2**24]
        elif total < 0:
            gains[i, 1] = 1 + total / 2**24
    assert h.trial_ticks(gains) == tuple(ticks)


@pytest.mark.parametrize("which", ["gains", "electrical_gains"])
def test_f32_rounding_mismatch_is_explicit_ambiguity(which):
    h = oracle()
    fields = {
        "double_gains": np.array([1.0]),
        "gains": np.array([1.0], np.float32),
        "electrical_double_gains": np.array([1.0]),
        "electrical_gains": np.array([1.0], np.float32),
    }
    changed = {k: v.copy() for k, v in fields.items()}
    changed[which][0] = np.nextafter(np.float32(1), np.float32(2))
    result = h.compare_gain_endpoints(fields, changed)
    assert result["status"] == "rounding_ambiguous"
    assert result["float32_mismatch_indices"][which] == [0]


def test_wrong_double_endpoint_exceeds_fixed_allowance():
    h = oracle()
    fields = {
        "double_gains": np.array([1.0]),
        "gains": np.array([1.0], np.float32),
        "electrical_double_gains": np.array([1.0]),
        "electrical_gains": np.array([1.0], np.float32),
    }
    changed = {k: v.copy() for k, v in fields.items()}
    changed["double_gains"] += 2e-11
    assert h.compare_gain_endpoints(fields, changed)["status"] == "failed_double_comparison"


@pytest.mark.parametrize("active", ["neither", "kc_only", "dan_only"])
def test_valid_unpaired_controls_have_zero_pair_change(active):
    h = oracle()
    kc, dan = np.zeros((600, 2)), np.zeros((600, 2))
    if active == "kc_only":
        kc[500:510] = 0.5
    if active == "dan_only":
        dan[500:510] = 0.25
    result = h.pair_reference(kc, dan, np.array([0, 1]), np.array([0, 1]), np.array([1, 1]))
    for key in ("gains", "double_gains", "electrical_gains", "electrical_double_gains"):
        np.testing.assert_array_equal(result[key], [1, 1])


@pytest.mark.parametrize("kind", ["object", "nonfinite"])
def test_archive_invalid_array_domain_rejected(tmp_path, kind):
    h = oracle()
    path = tmp_path / "bad.npz"
    value = np.array([{}], object) if kind == "object" else np.array([np.inf])
    np.savez(path, value=value)
    with pytest.raises(ValueError):
        h.numeric_archive(path)


@pytest.mark.parametrize("kind", ["duplicate", "overflow"])
def test_json_duplicate_and_overflow_families_rejected(tmp_path, kind):
    h = oracle()
    path = tmp_path / "bad.json"
    path.write_text('{"a":1,"a":2}' if kind == "duplicate" else '{"nested":[1e400]}')
    with pytest.raises(ValueError):
        h.read_json(path)


def test_binding_positive_then_mutation_and_escape(tmp_path, monkeypatch):
    h = oracle()
    monkeypatch.setattr(h, "ROOT", tmp_path)
    path = tmp_path / "input.txt"
    path.write_text("frozen")
    binding = dict(path="input.txt", bytes=6, sha256=h.sha(path))
    h.verify_bindings([binding])
    with pytest.raises(ValueError):
        h.verify_bindings([dict(binding, path="../input.txt")])
    path.write_text("mutate")
    with pytest.raises(ValueError):
        h.verify_bindings([binding])


def test_missing_completed_run_preserves_failure_without_calculation(tmp_path, monkeypatch):
    h = oracle()
    monkeypatch.setattr(h, "HERE", tmp_path)
    run = tmp_path / ("kc-local-shadow-" + "0" * 20)
    run.mkdir()
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        monkeypatch.setenv(key, "1")
    monkeypatch.setattr(
        h, "grouped_local", lambda *args: pytest.fail("No calculation allowed at failed entry")
    )
    result = h.audit(run, tmp_path / "audit-output")
    assert result["status"] == "failed"
    assert result["completed_rows"] == 0
    assert result["expected_rows"] == 32
    assert result["wall_cap_seconds"] == 120
    assert (tmp_path / "audit-output/audit.json").is_file()
    with pytest.raises(ValueError):
        h.audit(run, tmp_path / "audit-output")
