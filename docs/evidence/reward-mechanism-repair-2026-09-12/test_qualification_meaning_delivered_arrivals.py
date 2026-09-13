"""Meaning of existing qualification arithmetic, synthetic totals only.

These are not a new learning rule, a molecular simulation or a candidate run.
The exact oracle describes the frozen eight-trial predicate independently of
the production NumPy mean/SD implementation. No data archive is opened.
"""

from fractions import Fraction

import pytest

from bet36fly.reward_diagnostic import evaluate_panel


def exact_guard(values):
    values = [Fraction(x) for x in values]
    assert len(values) == 8
    return 9 * sum(values) ** 2 <= 16 * sum(x * x for x in values)


def panel(values, effect=-4):
    rows = []
    for game, total in enumerate(values):
        for seed in ["base", "alt"]:
            for condition in ["frozen", "untaught", "home", "away"]:
                applied = {
                    "frozen": [0, 0],
                    "untaught": [total, 0],
                    "home": [total + effect, 0],
                    "away": [total, effect],
                }[condition]
                rows.append(dict(game=game, seed_set=seed, condition=condition, applied=applied, clipped=0))
    return evaluate_panel(rows, expected_games=list(range(8)))


@pytest.mark.parametrize("magnitude", [2**-20, 1, 2**10])
@pytest.mark.parametrize("sign", [-1, 1])
@pytest.mark.parametrize("pattern,expected", [("constant", False), ("one", True), ("opposite", True)])
def test_guard_meaning_is_consistency_not_absolute_size(magnitude, sign, pattern, expected):
    a = sign * magnitude
    totals = [a] * 8 if pattern == "constant" else [a] + [0] * 7 if pattern == "one" else [a, -a] + [0] * 6
    assert exact_guard(totals) is expected
    result = panel(totals, effect=-4 * magnitude)
    for value in result["criteria"]["untaught_guard"]["evaluations"].values():
        assert value["passed"] is (expected if value["values"] == totals else True)


@pytest.mark.parametrize("totals,expected", [([0] * 8, True), ([10, 6, 2, -2, 0, 0, 0, 0], True), ([10, 6, 2, -1, 0, 0, 0, 0], False), ([10, 6, 2, -3, 0, 0, 0, 0], True)])
def test_exact_inclusive_equality_and_neighbors(totals, expected):
    assert exact_guard(totals) is expected
    assert panel(totals)["criteria"]["untaught_guard"]["evaluations"]["home/base"]["passed"] is expected


def test_real_matched_teaching_effect_can_pass_while_untaught_guard_fails():
    result = panel([-1] * 8, effect=-3)
    assert result["criteria"]["teaching_specific"]["passed"]
    assert result["criteria"]["cross_compartment"]["passed"]
    assert result["criteria"]["no_bound_hits"]["passed"]
    assert not result["criteria"]["untaught_guard"]["passed"]


def test_zero_gain_sums_do_not_establish_edgewise_stability():
    edges = [(Fraction(1, 16), -Fraction(1, 16))] * 8
    totals = [sum(v) for v in edges]
    assert exact_guard(totals)
    assert all(sum(abs(x) for x in row) > 0 for row in edges)


@pytest.mark.parametrize("factor", [Fraction(1, 8), Fraction(1), Fraction(7)])
def test_proportional_joint_filter_states_force_Q_zero(factor):
    rk, ek = Fraction(3, 2), Fraction(5, 4)
    rd, ed = factor * rk, factor * ek
    assert ed * rk - ek * rd == 0


def test_equal_instantaneous_rates_do_not_fix_eligibility_or_update():
    rk = rd = Fraction(1)
    states = [(Fraction(0), Fraction(1)), (Fraction(1), Fraction(0))]
    assert [ed * rk - ek * rd for ek, ed in states] == [1, -1]


def test_increasing_DAN_drive_is_not_a_global_monotonicity_guarantee():
    # Q depends separately on current drive and its historical state. This is
    # an algebraic local-state counterexample, not a physiological parameter set.
    rk, ek, ed = Fraction(1), Fraction(2), Fraction(3)
    assert ed * rk - ek * Fraction(1) > 0
    assert ed * rk - ek * Fraction(2) < 0
