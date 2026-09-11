from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from bet36fly.reward_protocol import decode, fit_fixed_readout, select_rows, plastic_mapping


def source_rows():
    dates = [datetime(2025, 6, 20, 12, tzinfo=timezone.utc) + timedelta(days=i) for i in range(12)]
    games = [
        {"id": str(i), "start_time": d.isoformat(), "outcome": i % 2 * 2, "sport": "baseball"}
        for i, d in enumerate(dates)
    ]
    return {
        "X": np.arange(36, dtype=np.float32).reshape(12, 3),
        "y": np.arange(12) % 2 * 2,
        "sport": np.ones(12, int),
        "train": np.arange(12) < 9,
        "validation": np.arange(12) >= 9,
    }, games


def test_chronological_selection_embargoes_unavailable_labels_and_fits_scaling_on_train():
    arrays, games = source_rows()
    selected = select_rows(arrays, games, train_n=4, validation_n=3, calibration_n=2)
    # Validation begins June 29. June 27 12:00 +48h is after its UTC day start.
    assert selected["train_indices"].tolist() == [3, 4, 5, 6]
    assert selected["validation_indices"].tolist() == [9, 10, 11]
    assert selected["calibration_indices"].tolist() == [3, 6]
    assert selected["embargoed"] == 2
    np.testing.assert_allclose(selected["input_mean"], [13.5, 14.5, 15.5])
    arrays["X"][9:] = 1e6
    again = select_rows(arrays, games, train_n=4, validation_n=3, calibration_n=2)
    np.testing.assert_array_equal(selected["input_mean"], again["input_mean"])
    np.testing.assert_array_equal(selected["input_std"], again["input_std"])


@pytest.mark.parametrize("damage", ["duplicate", "labels", "overlap", "nonfinite", "short", "order"])
def test_source_integrity_family_rejected(damage):
    arrays, games = source_rows()
    if damage == "duplicate":
        games[1]["id"] = games[0]["id"]
    if damage == "labels":
        games[0]["outcome"] = 2
    if damage == "overlap":
        arrays["train"][10] = True
    if damage == "nonfinite":
        arrays["X"][0, 0] = np.nan
    if damage == "short":
        games.pop()
    if damage == "order":
        games[0]["start_time"] = games[-1]["start_time"]
    with pytest.raises(ValueError):
        select_rows(arrays, games, train_n=4, validation_n=3, calibration_n=2)


def test_fixed_negative_response_readout_has_no_fitted_coefficients_and_respects_prior():
    fixed = fit_fixed_readout(np.array([[10.0, 20.0], [10.0, 20.0]]), np.array([0, 0, 0, 2]))
    p = decode(np.array([10.0, 20.0]), fixed)
    np.testing.assert_allclose(p, [2 / 3, 0, 1 / 3])
    assert decode(np.array([0.0, 20.0]), fixed)[0] > p[0]
    assert decode(np.array([10.0, 0.0]), fixed)[2] > p[2]
    before = {key: np.array(value).copy() for key, value in fixed.items() if key != "method"}
    for rates in [[0, 0], [1e6, 0], [0, 1e6], [1e6, 1e6]]:
        q = decode(np.array(rates), fixed)
        assert np.isfinite(q).all() and q.sum() == pytest.approx(1) and q[1] == 0
    for key, value in before.items():
        np.testing.assert_array_equal(fixed[key], value)


@pytest.mark.parametrize("rates", [[-1, 0], [float("nan"), 0], [float("inf"), 0], [1, 2, 3]])
def test_readout_rejects_invalid_activity(rates):
    fixed = fit_fixed_readout(np.array([[10.0, 20.0], [20.0, 10.0]]), np.array([0, 2]))
    with pytest.raises(ValueError):
        decode(np.array(rates), fixed)


def test_plastic_mapping_uses_only_existing_kc_to_declared_mbon_edges():
    # 0/1 are KCs, 2/3 target MBONs; 4 is an unselected output.
    ptr = np.array([0, 3, 5, 5, 5, 5])
    post = np.array([2, 3, 4, 2, 4])
    edges, kcs, compartments = plastic_mapping(ptr, post, np.array([0, 1]), [np.array([2]), np.array([3])])
    np.testing.assert_array_equal(edges, [0, 1, 3])
    np.testing.assert_array_equal(kcs, [0, 0, 1])
    np.testing.assert_array_equal(compartments, [0, 1, 0])
    with pytest.raises(ValueError):
        plastic_mapping(ptr, post, np.array([0, 1]), [np.array([2]), np.array([2])])
