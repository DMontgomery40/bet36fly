"""Offline independent Arrow Footer interval oracle; no network functions.

Block layout is transcribed from the preserved official File.fbs: int64 offset,
int32 metadata length, alignment padding, int64 body length (24 bytes).
"""

from dataclasses import dataclass, asdict
import hashlib
import json
from pathlib import Path
import struct


@dataclass(frozen=True)
class Region:
    kind: str
    index: int
    start: int
    metadata_bytes: int
    body_bytes: int

    @property
    def metadata_end(self):
        return self.start + self.metadata_bytes

    @property
    def end(self):
        return self.metadata_end + self.body_bytes


def intervals_from_footer(suffix, object_bytes):
    if type(object_bytes) is not int or object_bytes < len(suffix) or len(suffix) < 10:
        raise ValueError("Invalid object/suffix size")
    if suffix[-6:] != b"ARROW1":
        raise ValueError("Missing final Arrow magic")
    footer_length = int.from_bytes(suffix[-10:-6], "little", signed=True)
    if not 0 < footer_length <= len(suffix) - 10:
        raise ValueError("Incomplete footer")
    footer = suffix[-10 - footer_length : -10]
    footer_start = object_bytes - 10 - footer_length

    def unpack(fmt, pos):
        length = struct.calcsize(fmt)
        if type(pos) is not int or pos < 0 or pos + length > len(footer):
            raise ValueError("Footer reference out of bounds")
        return struct.unpack_from(fmt, footer, pos)[0]

    root = unpack("<I", 0)
    vtable = root - unpack("<i", root)
    vlen = unpack("<H", vtable)
    table_length = unpack("<H", vtable + 2)
    if (
        vlen < 4
        or vlen % 2
        or vtable + vlen > len(footer)
        or table_length < 4
        or root + table_length > len(footer)
    ):
        raise ValueError("Malformed Footer table")

    def field(index):
        if 4 + 2 * index >= vlen:
            return None
        relative = unpack("<H", vtable + 4 + 2 * index)
        if not relative:
            return None
        if relative < 4 or relative + 4 > table_length:
            raise ValueError("Field outside Footer table")
        return root + relative

    records = []
    for index, kind in [(2, "dictionary"), (3, "record_batch")]:
        pointer = field(index)
        if pointer is None:
            continue
        vector = pointer + unpack("<I", pointer)
        n = unpack("<I", vector)
        start = vector + 4
        if n > (len(footer) - start) // 24:
            raise ValueError("Block vector allocation out of range")
        for i in range(n):
            position = start + 24 * i
            offset, metadata, body = struct.unpack_from("<qi4xq", footer, position)
            region = Region(kind, i, offset, metadata, body)
            if (
                offset < 8
                or offset % 8
                or metadata < 8
                or metadata % 8
                or body < 0
                or region.end > footer_start
            ):
                raise ValueError("Block interval outside allowed file region")
            records.append(region)
    ordered = sorted(records, key=lambda r: r.start)
    for left, right in zip(ordered, ordered[1:]):
        if left.end > right.start:
            raise ValueError("Metadata/body blocks overlap")
    batches = [r for r in records if r.kind == "record_batch"]
    if any(a.start >= b.start for a, b in zip(batches, batches[1:])):
        raise ValueError("Record batch order is not strictly increasing")
    return dict(footer=footer, footer_start=footer_start, regions=records, batches=batches)


def audit_saved(root):
    directory = (
        Path(root) / "docs/evidence/reward-mechanism-repair-2026-09-12/localization-range-probe-2026-09-13"
    )
    payload = directory / "payload-02.bin"
    result = directory / "result-02.json"
    data = payload.read_bytes()
    receipt = json.loads(result.read_text())

    def sha(value):
        return hashlib.sha256(value).hexdigest()

    assert receipt["http_status"] == 206 and receipt["payload_complete"] is True
    assert len(data) == receipt["payload_bytes"] == 262144
    assert sha(data) == receipt["payload_sha256"]
    assert receipt["object_bytes"] == 6777179098
    assert receipt["headers"]["x-goog-generation"] == "1780494942562468"
    assert receipt["headers"]["etag"] == '"58efcf712f8c4d4de5f2ad51e97def76"'
    assert receipt["range_start"] == receipt["object_bytes"] - len(data)
    assert receipt["range_end"] == receipt["object_bytes"] - 1
    assert (
        receipt["headers"]["content-range"]
        == f"bytes {receipt['range_start']}-{receipt['range_end']}/{receipt['object_bytes']}"
    )
    parsed = intervals_from_footer(data, receipt["object_bytes"])
    batches = parsed["batches"]
    assert len(batches) == 4759
    assert sum(r.metadata_bytes for r in batches) == 3045760
    previous = json.loads((directory / "footer-inspection-02.json").read_text())
    assert previous["record_batches"] == [
        dict(index=r.index, offset=r.start, metadata_bytes=r.metadata_bytes, body_bytes=r.body_bytes)
        for r in batches
    ]
    rows = [
        dict(
            index=r.index,
            range_start=r.start,
            range_end=r.metadata_end - 1,
            metadata_bytes=r.metadata_bytes,
            body_start=r.metadata_end,
            body_end_exclusive=r.end,
        )
        for r in batches
    ]
    return dict(
        scope="Offline complete saved Footer metadata; no record-batch/body requests or decoding",
        network_requests=0,
        native_calls=0,
        input_payload=dict(path=str(payload), bytes=len(data), sha256=sha(data)),
        input_receipt=dict(path=str(result), sha256=sha(result.read_bytes())),
        object_identity={k: receipt[k] for k in ("url", "object_bytes")},
        generation=receipt["headers"]["x-goog-generation"],
        etag=receipt["headers"]["etag"],
        footer_bytes=len(parsed["footer"]),
        footer_start=parsed["footer_start"],
        footer_sha256=sha(parsed["footer"]),
        record_batch_count=len(batches),
        dictionary_count=sum(r.kind == "dictionary" for r in parsed["regions"]),
        aggregate_requested_metadata_bytes=sum(r.metadata_bytes for r in batches),
        metadata_lengths=sorted({r.metadata_bytes for r in batches}),
        all_metadata_ranges_exclude_all_record_and_dictionary_bodies=True,
        all_record_metadata_before_footer=True,
        previous_complete_inspection_matches=True,
        ranges=rows,
        dictionaries=[asdict(r) for r in parsed["regions"] if r.kind == "dictionary"],
    )


if __name__ == "__main__":
    print(json.dumps(audit_saved(Path.cwd()), indent=2))
