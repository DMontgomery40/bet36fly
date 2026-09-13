"""Documented GCS list representation and singleton boundaries; no networking."""

import base64
from copy import deepcopy
import io
import json
from pathlib import Path

import pytest

import partners_metadata_inventory as old
import partners_metadata_inventory_v2 as m


BASE = Path(__file__).parent
RAW = [
    json.loads(x)
    for x in (BASE / "partners-metadata-inventory-2026-09-13/requests.jsonl").read_text().splitlines()
][1]
SPEC = dict(RAW["block"], url=m.URL, object_bytes=m.OBJECT_BYTES, generation=m.GENERATION, etag=m.ETAG)
CRC = "crc32c=jTlNIA=="
MD5 = "md5=WO/PcS+MTU3l8q1R6X3vdg=="


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("No real network/DNS in header regressions")

    monkeypatch.setattr(m.socket, "socket", forbidden)
    monkeypatch.setattr(m.socket, "getaddrinfo", forbidden)


def with_hashes(values, name="x-goog-hash"):
    return [x[:] for x in RAW["response_headers"] if x[0].lower() != "x-goog-hash"] + [
        [name, value] for value in values
    ]


def test_actual_recorded_http206_reproduces_old_failure_and_new_compatibility():
    headers = deepcopy(RAW["response_headers"])
    with pytest.raises(ValueError, match="Duplicate response header"):
        old.validate_headers(SPEC, 206, headers, 640)
    assert m.validate_headers(SPEC, 206, headers, 640) == 640
    assert headers == RAW["response_headers"]


@pytest.mark.parametrize(
    "values",
    [
        [],
        [CRC],
        [MD5],
        [CRC, MD5],
        [MD5, CRC],
        [CRC + "," + MD5],
        [MD5 + ", " + CRC],
        [CRC, CRC, MD5],
        [" , " + CRC + ", , \t" + MD5 + ", "],
        ["", CRC, "", MD5],
    ],
)
@pytest.mark.parametrize("name", ["x-goog-hash", "X-Goog-Hash", "X-GOOG-HASH"])
def test_documented_hash_list_representations_preserve_raw_order(values, name):
    headers = with_hashes(values, name)
    before = deepcopy(headers)
    assert m.validate_headers(SPEC, 206, headers, 640) == 640
    assert headers == before
    expected = [item.strip().split("=", 1) for line in values for item in line.split(",") if item.strip()]
    assert m.parse_object_hashes(values) == [
        dict(algorithm=algorithm, value=value) for algorithm, value in expected
    ]


@pytest.mark.parametrize(
    "key",
    ["Content-Range", "Content-Length", "ETag", "x-goog-generation", "Content-Encoding", "Transfer-Encoding"],
)
@pytest.mark.parametrize("mutation", ["repeat", "conflict", "combine", "case"])
def test_list_permission_never_weakens_singleton_or_encoding_contract(key, mutation):
    headers = with_hashes([CRC, MD5])
    if key == "Content-Encoding":
        headers.append([key, "identity"])
    if key == "Transfer-Encoding":
        headers.append([key, "chunked"])
    index = next(i for i, x in enumerate(headers) if x[0].lower() == key.lower())
    value = headers[index][1]
    if mutation == "combine":
        headers[index][1] = value + ", " + value
    else:
        headers.append(
            [key.upper() if mutation == "case" else key, "wrong" if mutation == "conflict" else value]
        )
    with pytest.raises(ValueError):
        m.validate_headers(SPEC, 206, headers, 640)


@pytest.mark.parametrize(
    "values",
    [
        [""],
        [", ,"],
        ["sha256=AAAA"],
        ["md5=bad!"],
        ["crc32c="],
        ["md5=" + base64.b64encode(b"x" * 15).decode()],
        ["crc32c=" + base64.b64encode(b"x" * 5).decode()],
        [CRC, "crc32c=" + base64.b64encode(b"x" * 4).decode()],
        [MD5, "md5=" + base64.b64encode(b"x" * 16).decode()],
        ["md5"],
        [CRC + "\r\nContent-Length: 0"],
        [CRC + "\x00"],
        [CRC + ",sha256=AAAA"],
    ],
)
def test_malformed_or_conflicting_hash_lists_fail_before_payload(values):
    with pytest.raises(ValueError):
        m.validate_headers(SPEC, 206, with_hashes(values), 640)


@pytest.mark.parametrize(
    "field", ["Date", "Server", "Content-Type", "x-unknown", "Cache-Control", "Alt-Svc", "Set-Cookie"]
)
def test_unused_ancillary_fields_stay_opaque_ordered_and_repeatable(field):
    headers = with_hashes([CRC, MD5]) + [[field, "a"], [field.upper(), "b"]]
    before = deepcopy(headers)
    assert m.validate_headers(SPEC, 206, headers, 640) == 640
    assert headers == before


@pytest.mark.parametrize("key", ["", "bad name", " bad", "bad:", "bad\r", "bad\n", "é", "bad\x00", 123, None])
def test_every_header_name_obeys_http_token_syntax(key):
    with pytest.raises(ValueError):
        m.validate_headers(SPEC, 206, with_hashes([CRC, MD5]) + [[key, "x"]], 640)


@pytest.mark.parametrize(
    "value", ["a\x00b", "a\x01b", "a\x0bb", "a\x1fb", "a\x7fb", "a\rb", "a\nb", "☃", None, 123]
)
@pytest.mark.parametrize("key", ["x-goog-hash", "Content-Length", "x-opaque"])
def test_interpreted_and_opaque_fields_reject_invalid_value_octets(key, value):
    headers = [x for x in with_hashes([CRC, MD5]) if x[0].lower() != key.lower()] + [[key, value]]
    with pytest.raises(ValueError):
        m.validate_headers(SPEC, 206, headers, 640)


@pytest.mark.parametrize("value", ["", "\t", "a\tb", "é", "\xff", "ASCII !~"])
def test_opaque_field_valid_whitespace_and_octets_are_preserved(value):
    headers = with_hashes([CRC, MD5]) + [["x-opaque", value], ["x-opaque", value]]
    assert m.validate_headers(SPEC, 206, headers, 640) == 640


def test_actual_http_parser_preserves_repeated_hashes_and_exact_payload_boundary(monkeypatch):
    payload = (m.EVIDENCE / "localization-batch-metadata-2026-09-13/payload-02.bin").read_bytes()
    prefix = (
        b"HTTP/1.1 206 Partial Content\r\n"
        + b"".join((k + ": " + v + "\r\n").encode() for k, v in RAW["response_headers"])
        + b"\r\n"
    )

    class ObservedStream(io.BytesIO):
        def close(self):
            if not self.closed:
                self.final_position = self.tell()
            super().close()

    stream = ObservedStream(prefix + payload + b"UNREAD-BODY")

    class Sock:
        def makefile(self, *_args, **_kwargs):
            return stream

    class Connection:
        response_class = None

        def __init__(self, *_args, **_kwargs):
            pass

        def request(self, *_args, **_kwargs):
            pass

        def getresponse(self):
            response = self.response_class(Sock())
            response.begin()
            return response

        def close(self):
            pass

    monkeypatch.setattr(m.http.client, "HTTPSConnection", Connection)
    record, data = {"header_bytes": 0}, bytearray()
    limits = dict(
        request_active_seconds=14, header_bytes_per_request=8192, header_remaining=8192, payload_remaining=640
    )
    m.fetch_one(SPEC, limits, record, data)
    assert bytes(data) == payload
    assert record["header_bytes"] == len(prefix)
    assert stream.final_position == len(prefix) + 640
    assert [list(x) for x in record["response_headers"]] == RAW["response_headers"]


def test_v2_preserves_all_v1_bound_input_bytes():
    for spec in json.loads((BASE / "partners-metadata-frozen-plan-2026-09-13.json").read_text())[
        "source_bindings"
    ]:
        assert m.binding(spec["path"]) == spec
