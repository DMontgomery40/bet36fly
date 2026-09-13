"""Synthetic-only behavioral tests for the declared KC local-state wrapper."""

import ast
import hashlib
import importlib
import socket
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import csr_matrix

BASE = Path(__file__).parent
MODULE = BASE / "kc_local_state_evidence_ui.py"
PARAMS = dict(
    tauKCdec=1.2,
    tauinp=0.8,
    tauadapt=2.0,
    adaptscale=0.3,
    tauinh=0.7,
    inhfactor=0.9,
    infp=0.4,
    slf=0.2,
    bline=0.0,
)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Synthetic wrapper tests cannot use network")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def make(params=None, adjacency=None):
    assert MODULE.exists(), "Output-only KC local-state implementation is missing"
    cls = importlib.import_module("kc_local_state_evidence_ui").KCLocalState
    return cls(
        PARAMS if params is None else params,
        csr_matrix([[0.0, 1.0], [1.0, 0.0]]) if adjacency is None else adjacency,
    )


def snapshot(obj):
    return (
        obj.native_step,
        obj.source_frames,
        *(
            getattr(obj, name).copy()
            for name in ("calyx", "lobe", "adaptation", "inhibition", "pending_counts")
        ),
    )


def same(a, b):
    assert a[:2] == b[:2]
    for x, y in zip(a[2:], b[2:]):
        np.testing.assert_array_equal(x, y)


def upstream():
    folder = BASE / "kc-lateral-primary-source-2026-09-13/upstream/codes"
    files = [
        ("KC_population_calcium_rate_model_functions.py", "dd9df93bd1d1656f934f3258bd1694d9322e5778"),
        ("fit_functions.py", "a6aa50641bdcbc72b6599895d62899a0ed9267bd"),
    ]
    spaces = []
    for name, blob in files:
        raw = (folder / name).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == blob
        functions = [node for node in ast.parse(raw).body if isinstance(node, ast.FunctionDef)]
        space = {"np": np}
        if spaces:
            from types import SimpleNamespace

            space["mdl"] = SimpleNamespace(**spaces[0])
        exec(compile(ast.Module(body=functions, type_ignores=[]), name, "exec"), space)
        spaces.append(space)
    return spaces[1]["simulate_WT_model"]


def test_cold_first_event_is_unattenuated_and_counted_once():
    obj = make()
    np.testing.assert_array_equal(obj.consume(np.array([1, 0], np.uint8)), [1.0, 0.0])
    assert obj.native_step == 1 and obj.source_frames == 0
    np.testing.assert_array_equal(obj.pending_counts, [1, 0])
    np.testing.assert_array_equal(obj.calyx, [0, 0])


@pytest.mark.parametrize("n", [2, 3, 5])
@pytest.mark.parametrize("adapt,inh", [(0.0, 0.0), (0.3, 0.0), (0.0, 0.9), (0.3, 0.9)])
def test_complete_source_recurrence_matches_pinned_noiseless_wt(n, adapt, inh):
    params = PARAMS | {"adaptscale": adapt, "inhfactor": inh}
    weights = (np.ones((n, n)) - np.eye(n)) / (n - 1)
    obj = make(params, csr_matrix(weights))
    strengths = np.arange(n) % 3
    frames = np.array([1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0])
    # Independent physical-time grouping: frame=floor(30*t/5000).
    events = np.zeros((2000, n), np.uint8)
    for frame, on in enumerate(frames):
        first = (frame * 5000 + 29) // 30
        for j, count in enumerate(strengths * on):
            events[first : first + count, j] = 1
    observed = []
    for row in events:
        old_frame = obj.source_frames
        obj.consume(row)
        if obj.source_frames != old_frame:
            observed.append([obj.lobe, obj.calyx, obj.adaptation, obj.inhibition])
    obj.advance_boundary()
    observed.append([obj.lobe, obj.calyx, obj.adaptation, obj.inhibition])
    expected = upstream()(
        np.arange(13) / 30,
        np.r_[frames, 0],
        [params[k] for k in ("tauinh", "inhfactor", "infp", "slf")],
        [params[k] for k in ("tauKCdec", "tauinp", "tauadapt", "adaptscale", "bline")],
        strengths,
        1 / 30,
        n,
    )
    for actual, reference in zip(np.asarray(observed).transpose(1, 0, 2), expected):
        np.testing.assert_allclose(actual, reference[1:], rtol=3e-14, atol=3e-15)


@pytest.mark.parametrize("inhfactor", [0.0, 0.4, 2.0])
def test_asymmetric_neighbors_use_previous_lobe_in_recipient_row(inhfactor):
    obj = make(
        PARAMS | {"adaptscale": 0.0, "inhfactor": inhfactor},
        csr_matrix([[0.0, 0.25, 0.75], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
    )
    obj.consume_chunk(np.tile([1, 0, 0], (3, 1)))
    obj.consume_chunk(np.zeros((164, 3), np.uint8))
    obj.consume(np.zeros(3, np.uint8))  # frame1: C=L=[.125,0,0], I=0
    np.testing.assert_allclose(obj.calyx, [0.125, 0, 0], atol=1e-16)
    obj.consume_chunk(np.zeros((166, 3), np.uint8))
    obj.advance_boundary()  # source frame2 at next native time334
    expected = inhfactor * 0.125 / 0.7 / 30 / (1 + np.exp(-0.4 / 0.2))
    np.testing.assert_allclose(obj.inhibition, [0.0, 0.0, expected], rtol=2e-15, atol=1e-18)
    np.testing.assert_array_equal(obj.calyx, obj.lobe)  # previous I was zero
    obj.consume_chunk(np.zeros((166, 3), np.uint8))
    obj.advance_boundary()
    assert obj.lobe[2] == 0 and obj.calyx[2] == 0


@pytest.mark.parametrize("adjacency", [csr_matrix((2, 2)), csr_matrix([[0.0, 1.0], [1.0, 0.0]])])
def test_no_lateral_drive_leaves_original_impulses_exact(adjacency):
    obj = make(PARAMS | {"inhfactor": 0.0}, adjacency)
    events = np.zeros((2000, 2), np.uint8)
    events[::19, 0] = 1
    events[::31, 1] = 1
    np.testing.assert_array_equal(obj.consume_chunk(events), events)
    obj.advance_boundary()
    np.testing.assert_array_equal(obj.calyx, obj.lobe)


@pytest.mark.parametrize("field", ["tauKCdec", "tauinp", "tauadapt", "tauinh", "slf"])
@pytest.mark.parametrize("bad", [0.0, -1.0, np.nan, np.inf, True, "1"])
def test_invalid_times_and_slope_are_rejected(field, bad):
    with pytest.raises(ValueError):
        make(PARAMS | {field: bad})


@pytest.mark.parametrize("field", ["adaptscale", "inhfactor", "infp"])
@pytest.mark.parametrize("bad", [-1.0, np.nan, np.inf, False, "0"])
def test_invalid_nonnegative_coefficients_are_rejected(field, bad):
    with pytest.raises(ValueError):
        make(PARAMS | {field: bad})


@pytest.mark.parametrize("field", ["tauadapt", "tauinh"])
def test_positive_tau_below_source_step_is_rejected(field):
    with pytest.raises(ValueError):
        make(PARAMS | {field: np.nextafter(1 / 30, 0)})


@pytest.mark.parametrize("field,bad", [("bline", 1), ("bline", -1), ("bline", False)])
def test_candidate_baseline_contract_is_enforced(field, bad):
    with pytest.raises(ValueError):
        make(PARAMS | {field: bad})


@pytest.mark.parametrize(
    "params", [None, [], {}, PARAMS | {"unknown": 1}, {k: v for k, v in PARAMS.items() if k != "slf"}]
)
def test_complete_parameter_inventory_is_required(params):
    assert MODULE.exists()
    cls = importlib.import_module("kc_local_state_evidence_ui").KCLocalState
    with pytest.raises(ValueError):
        cls(params, csr_matrix([[0.0, 1.0], [1.0, 0.0]]))


@pytest.mark.parametrize(
    "bad",
    [
        np.eye(2),
        csr_matrix((0, 0)),
        csr_matrix(np.ones((2, 3))),
        csr_matrix([[1.0, 0.0], [0.0, 1.0]]),
        csr_matrix([[0.0, -1.0], [1.0, 0.0]]),
        csr_matrix([[0.0, np.nan], [1.0, 0.0]]),
        csr_matrix([[0.0, np.inf], [1.0, 0.0]]),
        csr_matrix([[0.0, 0.5], [1.0, 0.0]]),
        csr_matrix([[0.0, 2.0], [1.0, 0.0]]),
    ],
)
def test_adjacency_contract_rejects_wrong_support_or_normalization(bad):
    with pytest.raises(ValueError):
        make(adjacency=bad)


@pytest.mark.parametrize(
    "bad",
    [
        np.array([1]),
        np.array([[1, 0]]),
        np.array([1, -1]),
        np.array([1, 0.5]),
        np.array([1, np.nan]),
        np.array([1, np.inf]),
        np.array(["1", "0"]),
        np.array([1 + 0j, 0j]),
    ],
)
def test_invalid_event_has_no_state_or_clock_effect(bad):
    obj = make()
    obj.consume_chunk(np.zeros((167, 2), np.uint8))
    before = snapshot(obj)
    with pytest.raises(ValueError):
        obj.consume(bad)
    same(before, snapshot(obj))


def test_invalid_later_chunk_row_is_validated_before_consumption():
    obj = make()
    events = np.zeros((200, 2))
    events[-1, 0] = 0.5
    before = snapshot(obj)
    with pytest.raises(ValueError):
        obj.consume_chunk(events)
    same(before, snapshot(obj))


@pytest.mark.parametrize(
    "params",
    [
        PARAMS | {"tauKCdec": 1 / 60},
        PARAMS | {"tauKCdec": 1 / 30, "adaptscale": 1.0},
        PARAMS | {"adaptscale": 1e308, "tauadapt": 1 / 30, "tauinp": 1e-300},
    ],
)
def test_inadmissible_or_overflowing_frame_fails_before_publication(params):
    obj = make(params)
    error = None
    for _ in range(1001):
        before = snapshot(obj)
        try:
            obj.consume(np.array([1, 1], np.uint8))
        except ValueError as exc:
            error = exc
            same(before, snapshot(obj))
            break
    assert error is not None


def test_external_array_or_parameter_mutation_cannot_change_running_model():
    params = PARAMS.copy()
    weights = csr_matrix([[0.0, 1.0], [1.0, 0.0]])
    first, control = make(params, weights), make()
    params["inhfactor"] = 100
    weights.data[:] = 0
    events = np.zeros((1000, 2), np.uint8)
    events[::23] = 1
    np.testing.assert_array_equal(first.consume_chunk(events), control.consume_chunk(events))
    same(snapshot(first), snapshot(control))
    view = first.calyx
    try:
        view[:] = 123
    except ValueError:
        pass
    same(snapshot(first), snapshot(control))


@pytest.mark.parametrize("recipient", [1, 3, 8])
@pytest.mark.parametrize("neighbor", [1, 4])
def test_neighbor_attenuation_has_two_old_state_updates_of_latency(recipient, neighbor):
    params = PARAMS | {"adaptscale": 0.0}
    obj = make(params, csr_matrix([[0.0, 1.0], [0.0, 0.0]]))
    control = make(params, csr_matrix((2, 2)))
    first = np.zeros((167, 2), np.uint8)
    first[:recipient, 0] = 1
    first[:neighbor, 1] = 1
    for item in (obj, control):
        item.consume_chunk(first)
        item.advance_boundary()
    np.testing.assert_array_equal(obj.susceptibility, [1.0, 1.0])
    np.testing.assert_array_equal(obj.inhibition, [0.0, 0.0])
    for item in (obj, control):
        item.consume_chunk(np.zeros((167, 2), np.uint8))
        item.advance_boundary()
    assert obj.inhibition[0] > 0
    np.testing.assert_array_equal(obj.susceptibility, [1.0, 1.0])
    for item in (obj, control):
        item.consume_chunk(np.zeros((166, 2), np.uint8))
        item.advance_boundary()
    assert 0 <= obj.susceptibility[0] < control.susceptibility[0] == 1
    assert obj.susceptibility[1] == control.susceptibility[1] == 1
    np.testing.assert_array_equal(obj.calyx, control.calyx)


@pytest.mark.parametrize("low,high", [(1, 2), (2, 5), (5, 10)])
def test_recipient_activation_relief_under_fixed_one_way_neighbor_drive(low, high):
    models = []
    for count in (low, high):
        obj = make(PARAMS | {"adaptscale": 0.0}, csr_matrix([[0.0, 1.0], [0.0, 0.0]]))
        events = np.zeros((334, 2), np.uint8)
        events[:count, 0] = 1
        events[:4, 1] = 1
        obj.consume_chunk(events)
        obj.advance_boundary()
        models.append(obj)
    assert models[1].inhibition[0] < models[0].inhibition[0]
    assert models[1].lobe[1] == models[0].lobe[1]
    for obj in models:
        obj.consume_chunk(np.zeros((166, 2), np.uint8))
        obj.advance_boundary()
    assert models[1].susceptibility[0] > models[0].susceptibility[0]


def test_zero_recipient_ratio_and_silent_continuation_create_no_events():
    obj = make(adjacency=csr_matrix([[0.0, 1.0], [0.0, 0.0]]))
    obj.consume([0, 1])
    np.testing.assert_array_equal(obj.consume_chunk(np.zeros((999, 2), np.uint8)), 0)
    obj.advance_boundary()
    assert obj.inhibition[0] > 0 and obj.calyx[0] == obj.lobe[0] == 0
    assert obj.susceptibility[0] == 1
    fresh = make(adjacency=csr_matrix([[0.0, 1.0], [0.0, 0.0]]))
    np.testing.assert_array_equal(fresh.consume([1, 0]), [1.0, 0.0])
    assert fresh.source_frames == 0


def test_admissibility_equalities_are_allowed_without_changing_the_source():
    params = PARAMS | dict(tauKCdec=1 / 30, tauadapt=1 / 30, tauinh=1 / 30, adaptscale=0.0, inhfactor=0.0)
    obj = make(params)
    obj.consume([1, 1])
    obj.consume_chunk(np.zeros((166, 2), np.uint8))
    obj.advance_boundary()
    np.testing.assert_allclose(obj.calyx, [1 / 24, 1 / 24], rtol=1e-15)
    obj.consume_chunk(np.zeros((167, 2), np.uint8))
    obj.advance_boundary()
    np.testing.assert_array_equal(obj.calyx, 0)


@pytest.mark.parametrize(
    "field", ["tauKCdec", "tauinp", "tauadapt", "tauinh", "slf", "adaptscale", "inhfactor", "infp"]
)
def test_scalar_conversion_overflow_is_rejected_as_invalid_parameters(field):
    with pytest.raises(ValueError):
        make(PARAMS | {field: 10**1000})


def test_observing_every_step_cannot_change_state_or_weighted_events():
    observed, plain = make(), make()
    events = np.zeros((700, 2), np.uint8)
    events[::23, 0] = 1
    events[::29, 1] = 1
    rows = []
    for event in events:
        snapshot(observed)
        observed.susceptibility
        rows.append(observed.consume(event))
        snapshot(observed)
    np.testing.assert_array_equal(rows, plain.consume_chunk(events))
    same(snapshot(observed), snapshot(plain))
