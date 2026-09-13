"""Local-only full-footer inspection; no network and no record-batch reads."""

import hashlib
import io
import json
from pathlib import Path
import struct

import pyarrow
import pyarrow.ipc as ipc

HERE = Path(__file__).resolve().parent
OUT = HERE / 'localization-range-probe-2026-09-13'


class SuffixFile(io.RawIOBase):
    def __init__(self, data, start, size):
        self.data, self.start, self.size, self.pos = data, start, size, 0
        self.reads = []

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos+offset if whence == 1 else self.size+offset
        if not 0 <= self.pos <= self.size:
            raise ValueError('seek outside source object')
        return self.pos

    def read(self, length=-1):
        if length < 0:
            length = self.size-self.pos
        if self.pos < self.start or self.pos+length > self.size:
            raise ValueError('reader requested bytes not retrieved')
        self.reads.append(dict(offset=self.pos, length=length))
        result = self.data[self.pos-self.start:self.pos-self.start+length]
        self.pos += length
        return result


class FlatFooter:
    def __init__(self, data):
        self.data = data
        self.root = self.unpack('<I', 0)

    def unpack(self, fmt, pos):
        if not 0 <= pos <= len(self.data)-struct.calcsize(fmt):
            raise ValueError('Flatbuffer offset out of range')
        return struct.unpack_from(fmt, self.data, pos)[0]

    def field(self, table, number):
        vtable = table-self.unpack('<i', table)
        length = self.unpack('<H', vtable)
        if 4+2*number >= length:
            return None
        relative = self.unpack('<H', vtable+4+2*number)
        return table+relative if relative else None

    def vector(self, number):
        field = self.field(self.root, number)
        if field is None:
            return None, 0
        vector = field+self.unpack('<I', field)
        return vector+4, self.unpack('<I', vector)

    def blocks(self, number):
        pos, length = self.vector(number)
        if length == 0:
            return []
        if length*24 > len(self.data)-pos:
            raise ValueError('oversized block vector')
        return [dict(index=i, offset=self.unpack('<q', pos+24*i),
                     metadata_bytes=self.unpack('<i', pos+24*i+8),
                     body_bytes=self.unpack('<q', pos+24*i+16)) for i in range(length)]


def inspect(index):
    record = json.loads((OUT/f'result-{index:02d}.json').read_text())
    data = (OUT/f'payload-{index:02d}.bin').read_bytes()
    assert record['status'] == 'received' and record['http_status'] == 206
    assert hashlib.sha256(data).hexdigest() == record['payload_sha256']
    assert data[-6:] == b'ARROW1'
    length = struct.unpack_from('<i', data, len(data)-10)[0]
    assert 0 < length <= len(data)-10
    footer = data[-10-length:-10]
    flat = FlatFooter(footer)
    dictionaries, batches = flat.blocks(2), flat.blocks(3)
    custom_pos, custom_count = flat.vector(4)
    assert custom_count == 0, 'Nonempty file custom metadata requires complete additional parsing'
    footer_start = record['object_bytes']-10-length
    ordered = sorted(dictionaries+batches, key=lambda block: block['offset'])
    for i, block in enumerate(ordered):
        assert block['offset'] >= 0 and block['metadata_bytes'] > 0 and block['body_bytes'] >= 0
        end = block['offset']+block['metadata_bytes']+block['body_bytes']
        assert end <= (ordered[i+1]['offset'] if i+1 < len(ordered) else footer_start)
    suffix = SuffixFile(data, record['range_start'], record['object_bytes'])
    reader = ipc.open_file(suffix)
    assert reader.num_record_batches == len(batches)
    schema = reader.schema
    metadata = {k.decode(): v.decode() for k, v in (schema.metadata or {}).items()}
    pandas_metadata = json.loads(metadata['pandas'])
    fields = [dict(name=field.name, type=str(field.type), nullable=field.nullable,
                   metadata={k.decode(): v.decode() for k, v in (field.metadata or {}).items()})
              for field in schema]
    assert all(not field['metadata'] for field in fields)
    version = flat.field(flat.root, 0)
    result = dict(object_record=record, footer_bytes=length, footer_start=footer_start,
                  footer_sha256=hashlib.sha256(footer).hexdigest(),
                  arrow_metadata_version_number=flat.unpack('<h', version) if version else 0,
                  pyarrow_reader_version=pyarrow.__version__, schema=fields,
                  schema_metadata=metadata, pandas_metadata=pandas_metadata,
                  file_custom_metadata_count=custom_count, dictionaries=dictionaries,
                  record_batches=batches, record_batches_verified=len(batches),
                  dictionary_blocks_verified=len(dictionaries), reader_byte_requests=suffix.reads,
                  record_batches_read=0, dictionary_values_read=0,
                  body_index_or_body_sort_contract_in_inspected_metadata=False,
                  minimum_next_batch_metadata_range=f"bytes={batches[0]['offset']}-{batches[0]['offset']+batches[0]['metadata_bytes']-1}")
    with (OUT/f'footer-inspection-{index:02d}.json').open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(index=index, object_bytes=record['object_bytes'], footer_bytes=length,
                          batches=len(batches), dictionaries=len(dictionaries), fields=len(fields),
                          batch_metadata_bytes=sum(x['metadata_bytes'] for x in batches),
                          first_batch=batches[0], last_batch=batches[-1],
                          pandas_creator=pandas_metadata.get('creator'),
                          pandas_index=pandas_metadata.get('index_columns'),
                          schema_metadata_keys=list(metadata)), indent=2))


if __name__ == '__main__':
    inspect(1)
    inspect(2)
