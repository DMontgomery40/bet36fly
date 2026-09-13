"""Parse only supplied IPC metadata using inspected official Message.fbs."""

import hashlib
import json
from pathlib import Path
import struct

from localization_range_inspect import FlatFooter

HERE = Path(__file__).resolve().parent
OUT = HERE/'localization-batch-metadata-2026-09-13'
PREVIOUS = HERE/'localization-range-probe-2026-09-13'


def parse_metadata(data, schema, block):
    if len(data) < 8 or struct.unpack_from('<I', data)[0] != 0xffffffff:
        raise ValueError('Expected modern IPC continuation prefix')
    metadata_length = struct.unpack_from('<I', data, 4)[0]
    if metadata_length+8 != len(data) or len(data) != block['metadata_bytes']:
        raise ValueError('Metadata length/padding mismatch')
    flat = FlatFooter(data[8:])

    def scalar(table, number, fmt, default=0):
        field = flat.field(table, number)
        return flat.unpack(fmt, field) if field is not None else default

    def vector(table, number, stride):
        field = flat.field(table, number)
        if field is None:
            return None, 0
        pointer = field+flat.unpack('<I', field)
        count = flat.unpack('<I', pointer)
        if count*stride > len(flat.data)-pointer-4:
            raise ValueError('Vector extends beyond metadata')
        return pointer+4, count

    message = flat.root
    if scalar(message, 1, '<B') != 3:
        raise ValueError('Message header is not RecordBatch')
    field = flat.field(message, 2)
    if field is None:
        raise ValueError('Missing RecordBatch header')
    batch = field+flat.unpack('<I', field)
    body_length = scalar(message, 3, '<q')
    if body_length != block['body_bytes']:
        raise ValueError('Body length differs from locked footer')
    _, message_custom = vector(message, 4, 4)
    rows = scalar(batch, 0, '<q')
    node_pos, node_count = vector(batch, 1, 16)
    buffer_pos, buffer_count = vector(batch, 2, 16)
    _, variable_count = vector(batch, 4, 8)
    if node_count != len(schema) or buffer_count != 2*len(schema) or variable_count:
        raise ValueError('Not the frozen flat fixed-width/dictionary-index schema')
    nodes = [dict(length=flat.unpack('<q', node_pos+16*i),
                  null_count=flat.unpack('<q', node_pos+16*i+8)) for i in range(node_count)]
    if not all(x['length'] == rows and 0 <= x['null_count'] <= rows for x in nodes):
        raise ValueError('Inconsistent field-node row counts')
    buffers = [dict(index=i, offset=flat.unpack('<q', buffer_pos+16*i),
                    length=flat.unpack('<q', buffer_pos+16*i+8)) for i in range(buffer_count)]
    previous_end = 0
    for buffer in buffers:
        if not previous_end <= buffer['offset'] or not 0 <= buffer['length'] <= body_length-buffer['offset']:
            raise ValueError('Invalid buffer extent/order')
        previous_end = buffer['offset']+buffer['length']
    compression_field = flat.field(batch, 3)
    compression = None
    if compression_field is not None:
        table = compression_field+flat.unpack('<I', compression_field)
        codec, method = scalar(table, 0, '<b'), scalar(table, 1, '<b')
        if codec not in (0, 1) or method != 0:
            raise ValueError('Unsupported declared compression')
        compression = dict(codec=('LZ4_FRAME', 'ZSTD')[codec], method='BUFFER')
    body_start = block['offset']+block['metadata_bytes']
    fields = []
    for i, field in enumerate(schema):
        if not (field['type'].startswith(('int', 'uint', 'dictionary<')) or field['type'] in ('float', 'double')):
            raise ValueError('Unsupported flat storage type')
        valid, values = buffers[2*i:2*i+2]
        fields.append(dict(name=field['name'], type=field['type'], node=nodes[i],
                           validity_buffer=valid, values_buffer=values,
                           absolute_values_start=body_start+values['offset'],
                           absolute_values_end=body_start+values['offset']+values['length']-1,
                           buffer_payload_read=False))
    return dict(metadata_bytes=len(data), message_metadata_bytes=metadata_length,
                metadata_version_number=scalar(message, 0, '<h'), message_header='RecordBatch',
                body_bytes=body_length, body_start=body_start, rows=rows, compression=compression,
                custom_message_metadata_count=message_custom, nodes=nodes, buffers=buffers, fields=fields,
                all_buffer_extents_checked=True, body_payload_bytes_read=0,
                global_batch_layout_or_body_order_established=False)


def main():
    for i in (1, 2):
        request = json.loads((OUT/f'result-{i:02d}.json').read_text())
        footer = json.loads((PREVIOUS/f'footer-inspection-{i:02d}.json').read_text())
        data = (OUT/f'payload-{i:02d}.bin').read_bytes()
        assert request['status'] == 'received' and request['sources_unchanged_after_request']
        assert hashlib.sha256(data).hexdigest() == request['payload_sha256']
        result = parse_metadata(data, footer['schema'], footer['record_batches'][0])
        result['request'] = request
        with (OUT/f'metadata-inspection-{i:02d}.json').open('x') as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
            stream.write('\n')
        print(json.dumps({key: result[key] for key in ('rows', 'compression', 'body_bytes', 'custom_message_metadata_count')}, indent=2))
        for field in result['fields']:
            if field['name'] in ('body', 'body_pre', 'body_post'):
                print(json.dumps(field, indent=2))


if __name__ == '__main__':
    main()
