"""Independent PyArrow-written fixtures for the offline Footer interval oracle."""

import struct
import numpy as np
import pyarrow as pa
import pyarrow.ipc as ipc
import pytest
from partners_metadata_independent import intervals_from_footer


def arrow_file(sizes, compression, dictionary):
    schema = pa.schema(
        [
            ("body_pre", pa.int64()),
            ("body_post", pa.int64()),
            ("x_pre", pa.int32()),
            ("conf_pre", pa.float32()),
            ("primary_post", pa.dictionary(pa.int32(), pa.string()) if dictionary else pa.string()),
        ]
    )
    sink = pa.BufferOutputStream()
    expected = []
    with ipc.new_file(sink, schema, options=ipc.IpcWriteOptions(compression=compression)) as writer:
        for n in sizes:
            labels = (
                pa.DictionaryArray.from_arrays(pa.array(np.zeros(n, np.int32)), pa.array(["TEST"]))
                if dictionary
                else pa.array(["TEST"] * n, pa.string())
            )
            batch = pa.record_batch(
                [
                    pa.array(np.arange(n), pa.int64()),
                    pa.array(np.arange(n) + 100, pa.int64()),
                    pa.array(np.arange(n), pa.int32()),
                    pa.array([None if i % 2 else 0.75 for i in range(n)], pa.float32()),
                    labels,
                ],
                schema=schema,
            )
            expected.append(batch)
            writer.write_batch(batch)
    return sink.getvalue().to_pybytes(), expected


@pytest.mark.parametrize("sizes", [[], [0], [1], [2, 3], [0, 1, 0], [65, 129, 257]])
@pytest.mark.parametrize("compression", [None, "lz4", "zstd"])
@pytest.mark.parametrize("dictionary", [False, True])
def test_all_footer_regions_match_independent_pyarrow_messages(sizes, compression, dictionary):
    data, batches = arrow_file(sizes, compression, dictionary)
    actual = intervals_from_footer(data, len(data))
    reader = ipc.open_file(pa.BufferReader(data))
    assert len(actual["batches"]) == reader.num_record_batches == len(batches)
    for i, (region, expected) in enumerate(zip(actual["batches"], batches)):
        message = ipc.read_message(pa.BufferReader(data[region.start : region.end]))
        assert message.type == "record batch"
        assert message.metadata.size + 8 == region.metadata_bytes
        assert message.body.size == region.body_bytes
        assert reader.get_batch(i).equals(expected)
    spans = sorted(actual["regions"], key=lambda r: r.start)
    assert all(a.end <= b.start for a, b in zip(spans, spans[1:]))
    assert all(r.metadata_end <= r.end <= actual["footer_start"] for r in spans)


def block_locations(data):
    length = struct.unpack_from("<i", data, len(data) - 10)[0]
    start = len(data) - 10 - length
    root = start + struct.unpack_from("<I", data, start)[0]
    vtable = root - struct.unpack_from("<i", data, root)[0]
    field = root + struct.unpack_from("<H", data, vtable + 4 + 2 * 3)[0]
    vector = field + struct.unpack_from("<I", data, field)[0]
    return vector + 4


@pytest.mark.parametrize(
    "damage",
    [
        "trailer",
        "missing_footer",
        "negative_length",
        "root_outside",
        "negative_start",
        "unaligned_start",
        "metadata_zero",
        "metadata_unaligned",
        "negative_body",
        "body_overlaps_next",
        "duplicate_region",
        "reordered_regions",
    ],
)
def test_malformed_footer_families_fail_before_any_body_use(damage):
    original, _ = arrow_file([2, 3], None, False)
    data = bytearray(original)
    first = block_locations(data)
    if damage == "trailer":
        data[-1] = 0
    elif damage == "missing_footer":
        data = data[-9:]
    elif damage == "negative_length":
        struct.pack_into("<i", data, len(data) - 10, -1)
    elif damage == "root_outside":
        length = struct.unpack_from("<i", data, len(data) - 10)[0]
        struct.pack_into("<I", data, len(data) - 10 - length, 2**31)
    elif damage == "negative_start":
        struct.pack_into("<q", data, first, -8)
    elif damage == "unaligned_start":
        struct.pack_into("<q", data, first, 9)
    elif damage == "metadata_zero":
        struct.pack_into("<i", data, first + 8, 0)
    elif damage == "metadata_unaligned":
        struct.pack_into("<i", data, first + 8, 15)
    elif damage == "negative_body":
        struct.pack_into("<q", data, first + 16, -1)
    elif damage == "body_overlaps_next":
        struct.pack_into("<q", data, first + 16, len(data))
    elif damage == "duplicate_region":
        data[first + 24 : first + 48] = data[first : first + 24]
    elif damage == "reordered_regions":
        data[first : first + 48] = data[first + 24 : first + 48] + data[first : first + 24]
    with pytest.raises(ValueError):
        intervals_from_footer(bytes(data), len(data))
