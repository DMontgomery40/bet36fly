"""Frozen >=3 comparisons: exact integer/rational boundary and neighbors.

Expected truth follows literal signed integer sums and Fraction arithmetic,
never the production comparison helpers. All fixtures are manufactured.
"""

from fractions import Fraction

import numpy as np
import pytest

from bet36fly import conditioning as c


def endpoint(counts, gains, population, family="AB", reversal=False):
    counts = np.array(counts, np.int64)
    pop = np.array(population, np.int32)
    return dict(
        response_counts=counts,
        response_populations=pop,
        responses=counts / (pop * 0.3),
        gains=np.array(gains, np.float32),
        bound_hits=0,
        probe_contract=dict(
            family=family,
            duration_ms=800 if reversal else 400,
            cue_window=[300, 600] if reversal else [0, 300],
            seeds=list(range(5_000_042, 5_000_046)) if reversal else list(range(2_000_042, 2_000_046)),
        ),
    )


def acquisition(family, populations, count_delta, sizes=(3, 7)):
    # Unequal fixed preferred sets in both anatomical channels.
    a, b = sizes
    pk = np.tile(np.r_[np.zeros(a, int), np.ones(b, int)], 2)
    pc = np.repeat([0, 1], a + b)
    partitions = c.partition_kcs(
        np.array([[[2, 0], [0, 2]]] * 4, np.int32), pk, pc, np.ones(2 * (a + b), np.uint8)
    )
    counts = np.arange(16, dtype=np.int64).reshape(4, 2, 2) + 100
    gains = np.ones(len(pk), np.float32)
    unit = endpoint(counts, gains, populations, family)
    panels = {}
    for panel in ("0", "1000000"):
        panels[panel] = {}
        for arm in ("paired", "shuffled", "timing-unpaired", "untaught", "frozen"):
            out = counts.copy()
            gain = gains.copy()
            factor = 3 if arm == "paired" else 1 if arm == "shuffled" else 0
            for channel in (0, 1):
                target = channel
                other = 1 - channel
                target_edges = np.flatnonzero((pc == channel) & (pk == target))
                other_edges = np.flatnonzero((pc == channel) & (pk == other))
                out[:, target, channel] -= factor * count_delta
                gain[target_edges[0]] -= np.float32(factor / 16)
                gain[other_edges[0]] -= np.float32(factor / 128)
            panels[panel][arm] = endpoint(out, gain, populations, family)
    return unit, panels, partitions


def _exact_contrast(gains, unit, target, other):
    def mean_delta(indices):
        return sum((Fraction(float(gains[i])) - Fraction(float(unit[i])) for i in indices), Fraction()) / len(
            indices
        )

    return mean_delta(target) - mean_delta(other)


@pytest.mark.parametrize("family", ["AB", "CD"])
@pytest.mark.parametrize("populations", [(2, 4), (4, 2)])
@pytest.mark.parametrize("count_delta", [1, 7, 29])
@pytest.mark.parametrize("panel", ["0", "1000000"])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("neighbor", [-1, 0, 1])
def test_count_threefold_equality_and_single_count_neighbors(
    family, populations, count_delta, panel, channel, seed, neighbor
):
    unit, panels, partition = acquisition(family, populations, count_delta)
    paired = panels[panel]["paired"]
    paired["response_counts"][seed, channel, channel] += neighbor
    paired["responses"] = paired["response_counts"] / (paired["response_populations"] * 0.3)
    # Four-seed contrast sum is -12*d + neighbor; strongest null is -4*d.
    expected = abs(-12 * count_delta + neighbor) >= 3 * abs(-4 * count_delta)
    assert expected is (neighbor <= 0)
    result = c.evaluate_acquisition(unit, panels, partition)
    assert result["all_passed"] is expected, result


@pytest.mark.parametrize("sizes", [(3, 7), (7, 3)])
@pytest.mark.parametrize("panel", ["0", "1000000"])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("neighbor", [-1, 0, 1])
def test_unequal_gain_set_exact_equality_and_single_float32_neighbors(sizes, panel, channel, neighbor):
    unit, panels, partition = acquisition("AB", (2, 4), 7, sizes)
    groups = partition["channels"][("home", "away")[channel]]
    target = groups["first" if channel == 0 else "second"]
    other = groups["second" if channel == 0 else "first"]
    paired = panels[panel]["paired"]
    null = panels[panel]["shuffled"]
    assert _exact_contrast(paired["gains"], unit["gains"], target, other) == 3 * _exact_contrast(
        null["gains"], unit["gains"], target, other
    )
    if neighbor:
        i = target[0]
        paired["gains"][i] = np.nextafter(paired["gains"][i], np.float32(0 if neighbor < 0 else 1))
    actual = _exact_contrast(paired["gains"], unit["gains"], target, other)
    expected = abs(actual) >= 3 * abs(_exact_contrast(null["gains"], unit["gains"], target, other))
    assert expected is (neighbor <= 0)
    result = c.evaluate_acquisition(unit, panels, partition)
    assert result["all_passed"] is expected, result


def reversal(populations, scale):
    from conditioning_independent_contract import clone_fixture

    f = clone_fixture()
    p = f["partitions"]
    f["partitions"] = c.partition_kcs(p["counts"], p["pk"], p["pc"], p["mask"])
    for old in [
        f["unit"],
        *f["parents"].values(),
        *[x for panel in f["finals"].values() for x in panel.values()],
    ]:
        counts = (old["responses"] * scale).astype(np.int64)
        start = old.get("start_sha256")
        old.update(endpoint(counts, old["gains"], populations, reversal=True))
        if start is not None:
            old["start_sha256"] = start
    return f


@pytest.mark.parametrize("populations", [(2, 4), (4, 2)])
@pytest.mark.parametrize("scale", [1, 7, 29])
@pytest.mark.parametrize("panel", ["3000000", "4000000"])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("neighbor", [-1, 0, 1])
def test_old_recovery_per_seed_exact_integer_ratio_neighbors(
    populations, scale, panel, channel, seed, neighbor
):
    f = reversal(populations, scale)
    strict = f["finals"][panel]["backward-erasure-plus-swap"]
    strict["response_counts"][seed, channel, channel] += neighbor
    strict["responses"] = strict["response_counts"] / (strict["response_populations"] * 0.3)
    # Strict recovery was +3*scale against untaught +scale. Neighbor -1 alone fails.
    expected = (3 * scale + neighbor) >= 3 * scale
    result = c.evaluate_reversal(f["unit"], f["parents"], f["finals"], f["partitions"], f["starts"])
    assert result["all_passed"] is expected, result


@pytest.mark.parametrize("populations", [(2, 4), (4, 2)])
@pytest.mark.parametrize("scale", [1, 7, 29])
@pytest.mark.parametrize("panel", ["3000000", "4000000"])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("neighbor", [-1, 0, 1])
def test_new_association_four_seed_exact_integer_ratio_neighbors(
    populations, scale, panel, channel, seed, neighbor
):
    f = reversal(populations, scale)
    for p, branches in f["finals"].items():
        for ch in (0, 1):
            for arm, multiple in [("backward-erasure-plus-swap", 3), ("untaught-exposure", 1)]:
                branches[arm]["response_counts"][:, 1 - ch, ch] = (
                    f["parents"][p]["response_counts"][:, 1 - ch, ch] - multiple * scale
                )
                branches[arm]["responses"] = branches[arm]["response_counts"] / (
                    branches[arm]["response_populations"] * 0.3
                )
    strict = f["finals"][panel]["backward-erasure-plus-swap"]
    strict["response_counts"][seed, 1 - channel, channel] += neighbor
    strict["responses"] = strict["response_counts"] / (strict["response_populations"] * 0.3)
    # New-minus-old sum: -24*scale+neighbor versus untaught -8*scale.
    expected = abs(-24 * scale + neighbor) >= 3 * abs(-8 * scale)
    result = c.evaluate_reversal(f["unit"], f["parents"], f["finals"], f["partitions"], f["starts"])
    assert result["all_passed"] is expected, result


@pytest.mark.parametrize("sizes", [(3, 7), (7, 3)])
@pytest.mark.parametrize("panel", ["3000000", "4000000"])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("selected", ["old", "new"])
@pytest.mark.parametrize("neighbor", [-1, 0, 1])
def test_reversal_unequal_gain_sets_exact_rational_boundary(sizes, panel, channel, selected, neighbor):
    import hashlib

    f = reversal((2, 4), 7)
    _, _, partition = acquisition("AB", (2, 4), 7, sizes)
    f["partitions"] = partition
    n = len(partition["plastic_mask"])
    f["unit"]["gains"] = np.ones(n, np.float32)
    for p, branches in f["finals"].items():
        parent = np.ones(n, np.float32)
        for ch in (0, 1):
            groups = partition["channels"][("home", "away")[ch]]
            old = groups["first" if ch == 0 else "second"]
            parent[old] = 0.75
        f["parents"][p]["gains"] = parent
        identity = hashlib.sha256(parent.tobytes()).hexdigest()
        for arm, value in branches.items():
            gains = parent.copy()
            for ch in (0, 1):
                groups = partition["channels"][("home", "away")[ch]]
                old = groups["first" if ch == 0 else "second"]
                new = groups["second" if ch == 0 else "first"]
                if arm in ("backward-erasure-plus-swap", "untaught-exposure"):
                    factor = 3 if arm == "backward-erasure-plus-swap" else 1
                    gains[old[0]] += np.float32(factor / 16)
                    gains[new[0]] -= np.float32(factor / 16)
                elif arm == "ordinary-contingency-swap":
                    gains[new] -= 0.25
                elif arm == "continued-acquisition":
                    gains[old] -= 0.125
            value["gains"] = gains
            value["start_sha256"] = identity
            f["starts"][p][arm] = identity
    groups = partition["channels"][("home", "away")[channel]]
    old = groups["first" if channel == 0 else "second"]
    new = groups["second" if channel == 0 else "first"]
    gains = f["finals"][panel]["backward-erasure-plus-swap"]["gains"]
    if neighbor:
        edge = old[0] if selected == "old" else new[0]
        gains[edge] = np.nextafter(gains[edge], np.float32(0 if neighbor < 0 else 2))
    # Old recovery loses strict 3x when old gain decreases; new association
    # loses strict 3x when new gain increases. Both statements use one ULP.
    expected = neighbor >= 0 if selected == "old" else neighbor <= 0
    result = c.evaluate_reversal(f["unit"], f["parents"], f["finals"], f["partitions"], f["starts"])
    assert result["all_passed"] is expected, result
