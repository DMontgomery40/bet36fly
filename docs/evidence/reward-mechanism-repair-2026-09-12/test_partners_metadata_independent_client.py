"""Independent PyArrow fixtures applied to the proposed metadata parser API."""

import struct
import pyarrow as pa
import pyarrow.ipc as ipc
import pytest
from partners_metadata_independent import intervals_from_footer
import partners_metadata_inventory as candidate


FIELDS = [
    ("x_pre", pa.int32()),
    ("y_pre", pa.int32()),
    ("z_pre", pa.int32()),
    ("body_pre", pa.int64()),
    ("conf_pre", pa.float32()),
    ("x_post", pa.int32()),
    ("y_post", pa.int32()),
    ("z_post", pa.int32()),
    ("body_post", pa.int64()),
    ("conf_post", pa.float32()),
]


def fixture(rows, codec, nulls):
    arrays = []
    for _, kind in FIELDS:
        arrays.append(
            pa.array(
                [None if nulls == "all" or (nulls == "mixed" and i % 3 == 0) else i for i in range(rows)],
                kind,
            )
        )
    indices = pa.array(
        [None if nulls == "all" or (nulls == "mixed" and i % 3 == 0) else i % 2 for i in range(rows)],
        pa.int16(),
    )
    arrays.append(
        pa.DictionaryArray.from_arrays(indices, pa.array(["SYNTHETIC-A", "SYNTHETIC-B"]), ordered=True)
    )
    batch = pa.record_batch(arrays, names=[x[0] for x in FIELDS] + ["primary_post"])
    out = pa.BufferOutputStream()
    with ipc.new_file(out, batch.schema, options=ipc.IpcWriteOptions(compression=codec)) as writer:
        writer.write_batch(batch)
    raw = out.getvalue().to_pybytes()
    region = intervals_from_footer(raw, len(raw))["batches"][0]
    block = dict(
        index=0, offset=region.start, metadata_bytes=region.metadata_bytes, body_bytes=region.body_bytes
    )
    schema = [dict(name=f.name, type=str(f.type), nullable=f.nullable, metadata={}) for f in batch.schema]
    assert ipc.open_file(pa.BufferReader(raw)).get_batch(0).equals(batch)
    return raw[region.start : region.metadata_end], schema, block, batch


def pointer(data, table, index):
    vtable = table - struct.unpack_from("<i", data, table)[0]
    offset = struct.unpack_from("<H", data, vtable + 4 + 2 * index)[0]
    assert offset
    return table + offset


def mutate_buffer_length(payload, field, kind, length):
    data = bytearray(payload)
    root = 8 + struct.unpack_from("<I", data, 8)[0]
    header = pointer(data, root, 2)
    batch = header + struct.unpack_from("<I", data, header)[0]
    vector = pointer(data, batch, 2)
    start = vector + struct.unpack_from("<I", data, vector)[0] + 4
    assert struct.unpack_from("<I", data, start - 4)[0] == 22
    struct.pack_into("<q", data, start + (2 * field + kind) * 16 + 8, length)
    return bytes(data)


@pytest.mark.parametrize("rows", [0, 1, 11, 16])
@pytest.mark.parametrize("codec", [None, "lz4", "zstd"])
@pytest.mark.parametrize("nulls", ["none", "mixed", "all"])
def test_independently_generated_primitive_dictionary_metadata_is_accepted(rows, codec, nulls):
    payload, schema, block, batch = fixture(rows, codec, nulls)
    actual = candidate.parse_batch(payload, schema, block)
    assert actual["rows"] == rows
    for name in ("body_pre", "body_post"):
        assert actual[name]["null_count"] == batch.column(batch.schema.get_field_index(name)).null_count
        if codec is None:
            assert actual[name]["values"]["bytes"] == 8 * rows
    assert actual["body_payload_bytes_read"] == 0


@pytest.mark.parametrize("codec", ["lz4", "zstd"])
@pytest.mark.parametrize("field", range(11))
@pytest.mark.parametrize("kind", [0, 1])
@pytest.mark.parametrize("size", [0, 7, 8])
def test_positive_compressed_buffers_need_prefix_and_nonempty_encoded_values(codec, field, kind, size):
    payload, schema, block, _ = fixture(16, codec, "all")
    with pytest.raises(ValueError):
        candidate.parse_batch(mutate_buffer_length(payload, field, kind, size), schema, block)
