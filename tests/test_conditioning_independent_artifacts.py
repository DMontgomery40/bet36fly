"""Independent bounded-container tests. No engine, external path, or large allocation."""

import io
import json
import warnings
import zipfile

import numpy as np
import pytest

from bet36fly.conditioning_artifacts import decode_result, encode_result, safe_npz


def npy_header(*, shape=(2,), descr="<f8", payload=b"\0" * 16):
    stream = io.BytesIO()
    np.lib.format.write_array_header_1_0(stream, {"shape": shape, "fortran_order": False, "descr": descr})
    return stream.getvalue() + payload


def archive(members):
    stream = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for name, data in members:
                z.writestr(name, data)
    return stream.getvalue()


@pytest.mark.parametrize(
    "shape,descr,payload",
    [
        ((100_000_000,), "<f8", b""),
        ((2,), "<f8", b"\0" * 8),
        ((2,), "<f8", b"\0" * 24),
        ((2,), "|O", b"\0" * 16),
        ((2,), "<c16", b"\0" * 32),
    ],
)
def test_declared_allocation_and_dtype_rejected_before_numpy_load(monkeypatch, shape, descr, payload):
    data = archive([("a.npy", npy_header(shape=shape, descr=descr, payload=payload))])

    def must_not_load(*args, **kwargs):
        raise AssertionError("Unsafe header reached allocating NumPy load")

    monkeypatch.setattr(np, "load", must_not_load)
    with pytest.raises(ValueError):
        safe_npz(data)


@pytest.mark.parametrize("damage", ["duplicate", "traversal", "absolute", "too-many", "nonfinite"])
def test_complete_archive_member_inventory(damage):
    good = npy_header()
    members = [("a.npy", good)]
    if damage == "duplicate":
        members.append(("a.npy", good))
    elif damage == "traversal":
        members = [("../a.npy", good)]
    elif damage == "absolute":
        members = [("/a.npy", good)]
    elif damage == "too-many":
        members = [(f"a{i}.npy", good) for i in range(65)]
    else:
        members = [("a.npy", npy_header(payload=np.array([np.nan, 0.0]).tobytes()))]
    with pytest.raises(ValueError):
        safe_npz(archive(members))


def test_nested_real_numeric_container_roundtrip_preserves_dtype_shape_and_bytes():
    value = {
        "counts": np.array([1, 2], np.int32),
        "instrumentation": {"tail": np.zeros((2, 8), np.float64)},
        "duration_ms": 400.0,
    }
    data, metadata = encode_result(value)
    decoded = decode_result(data, metadata)
    for first, second in (
        (value["counts"], decoded["counts"]),
        (value["instrumentation"]["tail"], decoded["instrumentation"]["tail"]),
    ):
        assert (
            first.dtype == second.dtype
            and first.shape == second.shape
            and first.tobytes() == second.tobytes()
        )


@pytest.mark.parametrize(
    "metadata",
    [
        '{"x":{"array":"a"},"x":{"array":"a"}}',
        '{"x":{"array":"a"},"x":null}',
        '{"x":{"array":"a"},"duration_ms":800,"duration_ms":400}',
    ],
)
def test_duplicate_json_keys_are_not_canonical_native_metadata(metadata):
    with pytest.raises(ValueError):
        decode_result(archive([("a.npy", npy_header())]), metadata)


@pytest.mark.parametrize(
    "metadata",
    [
        {"x": {"array": "missing"}},
        {"x": {"array": "a"}, "y": {"array": "a"}},
        {"x": {"array": "a"}, "bad": float("nan")},
        {"x": {"array": "a"}, "bad": float("inf")},
    ],
)
def test_array_references_and_nonfinite_metadata_are_complete(metadata):
    with pytest.raises(ValueError):
        decode_result(archive([("a.npy", npy_header())]), json.dumps(metadata))
