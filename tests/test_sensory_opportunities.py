"""Absolute, symmetric and uncertainty-preserving opportunity encoding."""

import csv
from pathlib import Path

import numpy as np
import pytest

from bet36fly.sensory_opportunities import recruitment_order, encode_quality, compare_outputs


def source():
    return list(
        csv.DictReader(
            (
                Path(__file__).resolve().parents[1]
                / "docs/evidence/sensory-backtest-goal-2026-09-13/source-grns.csv"
            ).open()
        )
    )


def test_recruitment_is_balanced_nested_and_source_order_independent():
    rows = source()
    order = recruitment_order(rows)
    assert order == recruitment_order(rows[::-1]) and len(set(order)) == 34
    sides = {int(r["Body_ID"]): r["Root_Side"] for r in rows if r["Connectome"] == "maleCNS"}
    for n in range(35):
        assert abs(sum(sides[i] == "L" for i in order[:n]) - sum(sides[i] == "R" for i in order[:n])) <= 1
    assert encode_quality(0.85, (0.8, 0.9), order)["sweet_ids"] == order[:29]
    assert encode_quality(0.8, (0.75, 0.85), order)["sweet_ids"] == order[:27]


def test_uncertainty_prevents_an_unsupported_aversive_endpoint():
    order = recruitment_order(source())
    assert encode_quality(0.1, (0.05, 0.15), order)["condition"] == "bitter"
    assert encode_quality(0.1, (0.05, 0.65), order)["condition"] == "sweet_recruitment"
    assert encode_quality(0.2, (0.2, 0.2), order)["sweet_ids"] == order[:7]
    assert encode_quality(0.5, (0.3, 0.7), order)["quality_interval"] == [0.3, 0.7]


@pytest.mark.parametrize(
    "q,bounds",
    [(float("nan"), (0.1, 0.3)), (0.2, (0.3, 0.4)), (-0.1, (0, 1)), (0.5, (0, 1.1)), (0.5, (0.6, 0.4))],
)
def test_invalid_quality_fails(q, bounds):
    with pytest.raises(ValueError):
        encode_quality(q, bounds, list(range(34)))


def test_comparison_is_external_symmetric_and_has_no_draw_probability():
    a = np.array([2.0, 3.0, 5.0, 6.0])
    b = np.array([1.0, 2.0, 3.0, 4.0])
    assert compare_outputs(a, b) == -compare_outputs(b, a)
    assert compare_outputs(a, a) == 0
