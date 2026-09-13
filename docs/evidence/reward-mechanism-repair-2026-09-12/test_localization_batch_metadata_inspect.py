"""Metadata parser checked against independently written/read Arrow fixtures."""

import struct

import pyarrow as pa
import pyarrow.ipc as ipc
import pytest

from localization_batch_metadata_inspect import parse_metadata
from localization_range_inspect import FlatFooter


def fixture(rows, compression, pattern):
    values = [i if pattern == 'none' or pattern == 'alternate' and i % 2 else None for i in range(rows)]
    batch = pa.record_batch([pa.array(values, type=pa.int64()),
                             pa.array(values, type=pa.float32()),
                             pa.array(['gamma' if x is not None else None for x in values],
                                      type=pa.string()).dictionary_encode()],
                            names=['body', 'conf', 'region'])
    output = pa.BufferOutputStream()
    with ipc.new_file(output, batch.schema, options=ipc.IpcWriteOptions(compression=compression)) as writer:
        writer.write_batch(batch)
    data = output.getvalue().to_pybytes()
    footer_length = struct.unpack_from('<I', data, len(data)-10)[0]
    footer = FlatFooter(data[-10-footer_length:-10])
    block = footer.blocks(3)[0]
    metadata = data[block['offset']:block['offset']+block['metadata_bytes']]
    schema = [dict(name=x.name, type=str(x.type)) for x in batch.schema]
    return data, metadata, schema, block, batch, footer


@pytest.mark.parametrize('rows', [0, 1, 7, 1024])
@pytest.mark.parametrize('compression', [None, 'lz4', 'zstd'])
@pytest.mark.parametrize('pattern', ['none', 'all', 'alternate'])
def test_metadata_nodes_and_buffers_match_arrow_roundtrip(rows, compression, pattern):
    data, metadata, schema, block, expected, _ = fixture(rows, compression, pattern)
    decoded = ipc.open_file(pa.BufferReader(data)).get_batch(0)
    assert decoded.equals(expected)
    result = parse_metadata(metadata, schema, block)
    assert result['rows'] == decoded.num_rows == rows
    assert result['body_bytes'] == block['body_bytes']
    assert result['body_payload_bytes_read'] == 0
    assert len(result['fields']) == decoded.num_columns
    for i, field in enumerate(result['fields']):
        assert field['node']['null_count'] == decoded.column(i).null_count
        if rows:
            assert field['values_buffer']['length'] > 0
    expected_codec = {None: None, 'lz4': 'LZ4_FRAME', 'zstd': 'ZSTD'}[compression]
    assert (result['compression']['codec'] if result['compression'] else None) == expected_codec


@pytest.mark.parametrize('change', ['short', 'truncated', 'extra', 'wrong_footer_body', 'wrong_schema', 'dictionary_message'])
def test_metadata_integrity_families_reject(change):
    data, metadata, schema, block, _, footer = fixture(7, 'lz4', 'none')
    if change == 'short':
        metadata = metadata[:7]
    elif change == 'truncated':
        metadata = metadata[:-1]
    elif change == 'extra':
        metadata += b'\0'
    elif change == 'wrong_footer_body':
        block = dict(block, body_bytes=block['body_bytes']+1)
    elif change == 'wrong_schema':
        schema = schema[:-1]
    else:
        block = footer.blocks(2)[0]
        metadata = data[block['offset']:block['offset']+block['metadata_bytes']]
    with pytest.raises(ValueError):
        parse_metadata(metadata, schema, block)
