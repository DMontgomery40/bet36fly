"""Source alias identity, pure comparison and fresh assay acceptance contracts."""

import numpy as np
import pandas as pd
import pytest

from bet36fly.sensory_probe import second_order_cells, sensory_gates


def test_second_order_aliases_are_exact_not_cross_specimen_guesses():
    frame = pd.DataFrame(
        {
            "bodyId": [15321, 15734, 19480, 514625],
            "type": ["GNG042", "GNG042", "ANXXX462a", "ANXXX462a"],
            "synonyms": ["Shiu 2022: Quasimodo"] * 2 + ["Shiu 2022: Clavicle"] * 2,
        }
    )
    assert second_order_cells(frame) == {"Quasimodo": [15321, 15734], "Clavicle": [19480, 514625]}
    for col, value in [("bodyId", 123), ("type", "other"), ("synonyms", "")]:
        bad = frame.copy()
        bad.loc[0, col] = value
        with pytest.raises(ValueError):
            second_order_cells(bad)


def test_narrow_gates_keep_all_controls_and_global_recovery():
    rows = [
        dict(
            condition=k,
            seed=s,
            output_hz=[5.0, 5.0, 10.0, 10.0]
            if k == "sweet"
            else [5.0, 5.0, 8.0, 8.0]
            if k == "mixed"
            else [0.0] * 4,
            tail_spikes=0,
            output_tail_spikes=0,
            stimulus_spikes=100,
            total_spikes=0 if k == "null" else 100,
            generator_numerical_passed=True,
        )
        for k in ["null", "water", "sweet", "bitter", "mixed"]
        for s in [2, 3]
    ]
    # Output order is Clavicle pair then Quasimodo pair.
    assert sensory_gates(rows, [2, 3])["passed"]
    assert not sensory_gates(rows[:-1], [2, 3])["passed"]
    for field, value in [
        ("tail_spikes", 20),
        ("output_tail_spikes", 1),
        ("generator_numerical_passed", False),
        ("output_hz", [0.0] * 4),
    ]:
        altered = [r.copy() for r in rows]
        altered[4][field] = value
        assert not sensory_gates(altered, [2, 3])["passed"]
    assert np.array_equal(rows[4]["output_hz"], [5, 5, 10, 10])
