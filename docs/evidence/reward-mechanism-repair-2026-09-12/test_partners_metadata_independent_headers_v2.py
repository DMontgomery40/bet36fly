"""Independent RFC/GCS header compatibility cases; all HTTP input is synthetic or saved."""

import copy
import io
import json
from pathlib import Path

import pytest

import partners_metadata_inventory_v2 as candidate


HERE = Path(__file__).resolve().parent
OUTCOME = json.loads(
    (HERE / "partners-metadata-inventory-2026-09-13/requests.jsonl").read_text().splitlines()[-1]
)
SPEC = dict(
    OUTCOME["block"],
    url="https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/syn-partners-male-cns-v1.0-minconf-0.5.feather",
    object_bytes=6777179098,
    generation="1780494942562468",
    etag='"58efcf712f8c4d4de5f2ad51e97def76"',
)
HASHES = ["crc32c=jTlNIA==", "md5=WO/PcS+MTU3l8q1R6X3vdg=="]
CRITICAL = [
    "content-range",
    "content-length",
    "etag",
    "x-goog-generation",
    "content-encoding",
    "transfer-encoding",
]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def prohibited(*_args, **_kwargs):
        pytest.fail("Independent v2 review prohibits object/network requests")

    monkeypatch.setattr(candidate.socket, "socket", prohibited)
    monkeypatch.setattr(candidate.socket, "getaddrinfo", prohibited)


def saved_headers():
    assert OUTCOME["http_status"] == 206 and OUTCOME["payload_bytes"] == 0
    return copy.deepcopy(OUTCOME["response_headers"])


@pytest.mark.parametrize(
    "style", ["separate", "combined", "combined_ows", "split_combined", "empty_elements"]
)
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("name", ["x-goog-hash", "X-Goog-Hash", "X-GOOG-HASH"])
def test_documented_hash_list_representations_accept_without_mutating_raw_pairs(style, reverse, name):
    values = HASHES[::-1] if reverse else HASHES
    headers = [h for h in saved_headers() if h[0].lower() != "x-goog-hash"]
    extras = {
        "separate": [(name, v) for v in values],
        "combined": [(name, ",".join(values))],
        "combined_ows": [(name, " ,\t".join(values))],
        "split_combined": [(name, values[0] + ","), (name.lower(), values[1])],
        "empty_elements": [(name, ", " + values[0] + ", , " + values[1] + ",")],
    }[style]
    headers.extend(extras)
    original = copy.deepcopy(headers)
    assert candidate.validate_headers(SPEC, 206, headers, 640) == 640
    assert headers == original


@pytest.mark.parametrize(
    "name,values",
    [
        ("Cache-Control", ["public", "max-age=3600"]),
        ("Alt-Svc", ['h3=":443"; ma=2592000', 'h3-29=":443"; ma=2592000']),
        ("X-Unused-Metadata", ["first,opaque", "second opaque"]),
        ("Set-Cookie", ["synthetic=a; Path=/", "synthetic=b; Path=/"]),
    ],
)
@pytest.mark.parametrize("case", ["lower", "upper", "mixed"])
def test_opaque_uninterpreted_repeated_fields_do_not_change_range_identity(name, values, case):
    headers = saved_headers()
    key = name.lower() if case == "lower" else name.upper() if case == "upper" else name
    headers.extend([(key, values[0]), (name.lower(), values[1])])
    original = copy.deepcopy(headers)
    assert candidate.validate_headers(SPEC, 206, headers, 640) == 640
    assert headers == original


@pytest.mark.parametrize("key", CRITICAL)
@pytest.mark.parametrize("case", ["lower", "upper", "title"])
@pytest.mark.parametrize("value_kind", ["identical", "conflicting"])
def test_critical_duplicates_still_fail_with_valid_ancillary_lists(key, case, value_kind):
    headers = saved_headers()
    existing = next((v for k, v in headers if k.lower() == key), None)
    if existing is None:
        existing = "identity"
        headers.append((key, existing))
    spelling = key.lower() if case == "lower" else key.upper() if case == "upper" else key.title()
    headers.append((spelling, existing if value_kind == "identical" else "different"))
    with pytest.raises(ValueError):
        candidate.validate_headers(SPEC, 206, headers, 640)


@pytest.mark.parametrize(
    "key", ["", "Bad Name", "Bad:Name", "Bad\tName", "Bad\rName", "Bad\nName", "Bad\0Name", "Bäd"]
)
def test_invalid_field_name_never_becomes_an_ignored_ancillary_field(key):
    with pytest.raises(ValueError):
        candidate.validate_headers(SPEC, 206, saved_headers() + [(key, "value")], 640)


@pytest.mark.parametrize("value", ["a\rb", "a\nb", "a\0b", True, 3, {}, []])
def test_malformed_ancillary_values_remain_invalid(value):
    with pytest.raises(ValueError):
        candidate.validate_headers(SPEC, 206, saved_headers() + [("X-Unused", value)], 640)


def test_saved_failed_response_passes_actual_http_parser_without_reading_next_region(monkeypatch):
    headers = saved_headers()
    metadata = (candidate.EVIDENCE / "localization-batch-metadata-2026-09-13/payload-02.bin").read_bytes()
    assert len(metadata) == 640
    header = (
        b"HTTP/1.1 206 Partial Content\r\n"
        + b"".join(f"{k}: {v}\r\n".encode("latin1") for k, v in headers)
        + b"\r\n"
    )

    class Stream(io.BytesIO):
        def close(self):
            pass

    stream = Stream(header + metadata + b"UNREAD_BODY_SENTINEL")

    class Socket:
        def makefile(self, mode, buffering):
            assert mode == "rb" and buffering == 0
            return stream

    class Connection:
        def __init__(self, host, timeout):
            assert host == "storage.googleapis.com" and timeout == 14

        def request(self, method, path, headers):
            assert method == "GET" and headers["Range"] == "bytes=3960-4599"

        def getresponse(self):
            response = self.response_class(Socket(), method="GET")
            response.begin()
            return response

        def close(self):
            pass

    monkeypatch.setattr(candidate.http.client, "HTTPSConnection", Connection)
    limits = dict(
        request_active_seconds=14, header_bytes_per_request=8192, header_remaining=8192, payload_remaining=640
    )
    record, payload = {"header_bytes": 0}, bytearray()
    candidate.fetch_one(SPEC, limits, record, payload)
    assert bytes(payload) == metadata and stream.tell() == len(header) + 640
    assert record["header_bytes"] == len(header)
    assert record["response_headers"] == [tuple(h) for h in headers]
