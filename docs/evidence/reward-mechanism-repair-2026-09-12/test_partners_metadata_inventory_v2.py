"""Offline metadata protocol and accounting contracts; networking is always substituted."""

from copy import deepcopy
import json
import io
import hashlib
from pathlib import Path
import struct

import pytest

import partners_metadata_inventory_v2 as m


REPO = next(p for p in Path(__file__).resolve().parents if (p / "bet36fly").is_dir())
EVIDENCE = REPO / "docs/evidence/reward-mechanism-repair-2026-09-12"
RANGE = EVIDENCE / "localization-range-probe-2026-09-13"
BATCH = EVIDENCE / "localization-batch-metadata-2026-09-13"


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Offline tests must not open real network/DNS")

    monkeypatch.setattr(m.socket, "socket", forbidden)
    monkeypatch.setattr(m.socket, "getaddrinfo", forbidden)


@pytest.fixture
def footer():
    return json.loads((RANGE / "footer-inspection-02.json").read_text())


@pytest.fixture
def spec(footer):
    return dict(
        footer["record_batches"][0],
        object_bytes=6777179098,
        generation="1780494942562468",
        etag='"58efcf712f8c4d4de5f2ad51e97def76"',
    )


@pytest.fixture
def headers():
    return [
        ("Content-Range", "bytes 3960-4599/6777179098"),
        ("Content-Length", "640"),
        ("ETag", '"58efcf712f8c4d4de5f2ad51e97def76"'),
        ("x-goog-generation", "1780494942562468"),
        ("Content-Encoding", "identity"),
    ]


def test_all_locked_intervals_cover_metadata_only_without_gaps_or_dictionary_reads(footer):
    rows = m.requests_from_footer(footer, (RANGE / "payload-02.bin").read_bytes())
    assert len(rows) == 4759
    assert rows[0] == {"index": 0, "offset": 3960, "metadata_bytes": 640, "body_bytes": 1310264}
    assert rows[-1] == {"index": 4758, "offset": 6776807552, "metadata_bytes": 640, "body_bytes": 254256}
    assert sum(x["metadata_bytes"] for x in rows) == 3045760


@pytest.mark.parametrize(
    "field,value",
    [
        ("index", 1),
        ("index", False),
        ("offset", 3959),
        ("offset", "3960"),
        ("metadata_bytes", 641),
        ("metadata_bytes", 640.0),
        ("body_bytes", 0),
    ],
)
def test_exported_block_mutations_cannot_change_raw_footer_request_identity(footer, field, value):
    footer["record_batches"][0][field] = value
    with pytest.raises(ValueError):
        m.requests_from_footer(footer, (RANGE / "payload-02.bin").read_bytes())


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "reordered", "schema", "generation", "suffix"])
def test_full_footer_identity_is_required_not_only_total_payload(footer, mutation):
    suffix = (RANGE / "payload-02.bin").read_bytes()
    if mutation == "missing":
        footer["record_batches"].pop()
    elif mutation == "duplicate":
        footer["record_batches"][-1] = footer["record_batches"][0]
    elif mutation == "reordered":
        footer["record_batches"][:2] = footer["record_batches"][1::-1]
    elif mutation == "schema":
        footer["schema"][3]["type"] = "int32"
    elif mutation == "generation":
        footer["object_record"]["headers"]["x-goog-generation"] = "1780494942562469"
    else:
        suffix = suffix[:-1] + b"x"
    with pytest.raises(ValueError):
        m.requests_from_footer(footer, suffix)


def test_exact_pinned_response_is_accepted(spec, headers):
    assert m.validate_headers(spec, 206, headers, 640) == 640


@pytest.mark.parametrize("status", [200, 301, 302, 307, 401, 403, 404, 412, 416, 429, 500, True])
def test_nonpartial_statuses_never_authorize_payload_read(spec, headers, status):
    with pytest.raises(ValueError):
        m.validate_headers(spec, status, headers, 640)


@pytest.mark.parametrize(
    "name,value",
    [
        ("Content-Range", "bytes 3960-4600/6777179098"),
        ("Content-Range", "bytes 3961-4600/6777179098"),
        ("Content-Range", "bytes 3960-4599/6777179099"),
        ("Content-Length", "641"),
        ("Content-Length", "0639"),
        ("Content-Length", "0"),
        ("ETag", '"other"'),
        ("x-goog-generation", "1780494942562469"),
        ("Content-Encoding", "gzip"),
        ("Transfer-Encoding", "chunked"),
    ],
)
def test_framing_and_version_mismatch_families_fail_before_read(spec, headers, name, value):
    altered = [(k, v) for k, v in headers if k.lower() != name.lower()] + [(name, value)]
    with pytest.raises(ValueError):
        m.validate_headers(spec, 206, altered, 640)


@pytest.mark.parametrize(
    "name", ["content-range", "content-length", "etag", "x-goog-generation", "content-encoding"]
)
def test_duplicate_or_missing_identity_headers_are_not_collapsed(spec, headers, name):
    pair = next(x for x in headers if x[0].lower() == name)
    with pytest.raises(ValueError):
        m.validate_headers(spec, 206, headers + [(name, pair[1])], 640)
    if name != "content-encoding":
        with pytest.raises(ValueError):
            m.validate_headers(spec, 206, [x for x in headers if x != pair], 640)


@pytest.mark.parametrize("remaining", [0, 639, -1, True, 640.0])
def test_global_payload_budget_is_reserved_before_a_read(spec, headers, remaining):
    with pytest.raises(ValueError):
        m.validate_headers(spec, 206, headers, remaining)


def test_saved_first_metadata_reproduces_exact_unread_body_buffer_costs(footer):
    row = m.parse_batch(
        (BATCH / "payload-02.bin").read_bytes(), footer["schema"], footer["record_batches"][0]
    )
    assert row["rows"] == 65536
    assert row["compression"] == {"codec": "LZ4_FRAME", "method": "BUFFER"}
    assert row["body_pre"]["values"] == {"offset": 140376, "bytes": 88513}
    assert row["body_post"]["values"] == {"offset": 795168, "bytes": 285437}
    assert row["body_pre"]["validity"]["bytes"] == row["body_post"]["validity"]["bytes"] == 0
    assert row["body_payload_bytes_read"] == 0


@pytest.mark.parametrize("mutation", ["truncated", "extra", "prefix", "wrong_body", "wrong_schema"])
def test_metadata_parser_rejects_incomplete_or_mismatched_source(footer, mutation):
    data = (BATCH / "payload-02.bin").read_bytes()
    block = footer["record_batches"][0]
    if mutation == "truncated":
        data = data[:-1]
    elif mutation == "extra":
        data += b"x"
    elif mutation == "prefix":
        data = b"xxxx" + data[4:]
    elif mutation == "wrong_body":
        block["body_bytes"] += 8
    else:
        footer["schema"][3]["name"] = "wrong"
    with pytest.raises(ValueError):
        m.parse_batch(data, footer["schema"], block)


def test_partial_inventory_never_extrapolates_unread_batch_costs(footer):
    row = m.parse_batch(
        (BATCH / "payload-02.bin").read_bytes(), footer["schema"], footer["record_batches"][0]
    )
    result = m.assemble_inventory([row], footer["record_batches"])
    assert result["complete"] is False and result["missing_batches"] == 4758
    assert result["full_scan_body_buffer_bytes"] is None
    assert result["inspected_body_buffer_bytes"] == 373950
    assert result["inspected_rows"] == 65536


def test_duplicate_batch_cannot_fake_complete_inventory(footer):
    row = m.parse_batch(
        (BATCH / "payload-02.bin").read_bytes(), footer["schema"], footer["record_batches"][0]
    )
    with pytest.raises(ValueError):
        m.assemble_inventory([row, deepcopy(row)], footer["record_batches"])


def arrow_fixture(rows=7, compression="lz4", nulls=False):
    import pyarrow as pa
    import pyarrow.ipc as ipc

    names = [
        "x_pre",
        "y_pre",
        "z_pre",
        "body_pre",
        "conf_pre",
        "x_post",
        "y_post",
        "z_post",
        "body_post",
        "conf_post",
        "primary_post",
    ]
    types = [
        pa.int32(),
        pa.int32(),
        pa.int32(),
        pa.int64(),
        pa.float32(),
        pa.int32(),
        pa.int32(),
        pa.int32(),
        pa.int64(),
        pa.float32(),
    ]
    values = [None if nulls else i for i in range(rows)]
    arrays = [pa.array(values, type=t) for t in types]
    arrays += [
        pa.DictionaryArray.from_arrays(
            pa.array([None if nulls else 0] * rows, pa.int16()), pa.array(["region"]), ordered=True
        )
    ]
    batch = pa.record_batch(arrays, names=names)
    out = pa.BufferOutputStream()
    with ipc.new_file(out, batch.schema, options=ipc.IpcWriteOptions(compression=compression)) as writer:
        writer.write_batch(batch)
    data = out.getvalue().to_pybytes()
    length = struct.unpack_from("<I", data, len(data) - 10)[0]
    flat = m._footer_parser.FlatFooter(data[-10 - length : -10])
    block = flat.blocks(3)[0]
    payload = data[block["offset"] : block["offset"] + block["metadata_bytes"]]
    schema = [dict(name=f.name, type=str(f.type), nullable=f.nullable, metadata={}) for f in batch.schema]
    assert ipc.open_file(pa.BufferReader(data)).get_batch(0).equals(batch)
    return payload, schema, block


@pytest.mark.parametrize("rows", [0, 1, 7, 1024])
@pytest.mark.parametrize("compression", [None, "lz4", "zstd"])
@pytest.mark.parametrize("nulls", [False, True])
def test_independently_written_arrow_batches_include_empty_and_null_storage(rows, compression, nulls):
    data, schema, block = arrow_fixture(rows, compression, nulls)
    parsed = m.parse_batch(data, schema, block)
    assert parsed["rows"] == rows and parsed["body_pre"]["null_count"] == (rows if nulls else 0)
    assert parsed["body_payload_bytes_read"] == 0
    if compression is None:
        assert parsed["body_pre"]["values"]["bytes"] == rows * 8
        assert parsed["body_post"]["values"]["bytes"] == rows * 8


def change_buffer_size(payload, field, kind, length):
    data = bytearray(payload)
    flat = m._footer_parser.FlatFooter(data[8:])
    pointer = flat.field(flat.root, 2)
    batch = pointer + flat.unpack("<I", pointer)
    pointer = flat.field(batch, 2)
    buffers = pointer + flat.unpack("<I", pointer) + 4
    struct.pack_into("<q", data, 8 + buffers + (2 * field + kind) * 16 + 8, length)
    return bytes(data)


@pytest.mark.parametrize("field", range(11))
@pytest.mark.parametrize(
    "compression,bad_size",
    [(None, 0), (None, 1), ("lz4", 0), ("lz4", 7), ("lz4", 8), ("zstd", 1), ("zstd", 8)],
)
def test_positive_row_values_cannot_have_impossible_fixed_width_or_prefix_size(field, compression, bad_size):
    data, schema, block = arrow_fixture(7, compression)
    with pytest.raises(ValueError):
        m.parse_batch(change_buffer_size(data, field, 1, bad_size), schema, block)


@pytest.mark.parametrize(
    "compression,bad_size", [(None, 0), (None, 1), ("lz4", 0), ("lz4", 7), ("lz4", 8), ("zstd", 8)]
)
@pytest.mark.parametrize("field", [3, 8, 10])
def test_positive_null_counts_require_sized_validity_storage(field, compression, bad_size):
    data, schema, block = arrow_fixture(16, compression, True)
    with pytest.raises(ValueError):
        m.parse_batch(change_buffer_size(data, field, 0, bad_size), schema, block)


def test_plan_contains_complete_exact_requests_and_fixed_caps(tmp_path):
    plan = m.build_plan(REPO / "output/collaboration/reward-mechanism-repair/partners-metadata-unrun-test")
    assert plan["status"] == "proposed"
    assert plan["limits"] == dict(
        requests=4759,
        concurrency=1,
        payload_bytes=3045760,
        header_bytes=8388608,
        response_bytes=11434368,
        header_bytes_per_request=8192,
        request_active_seconds=14,
        request_wall_seconds=15,
        total_wall_seconds=1200,
    )
    assert len(plan["requests"]) == 4759 and plan["requests"][0]["offset"] == 3960
    plan["status"] = "frozen"
    assert m.validate_plan(plan) == plan


@pytest.mark.parametrize(
    "mutation",
    [
        "partial",
        "duplicate",
        "reorder",
        "coalesce",
        "source",
        "host",
        "generation",
        "payload",
        "concurrency",
        "retry",
        "output",
        "unfrozen",
    ],
)
def test_execution_plan_cannot_broaden_source_ranges_or_budgets(mutation):
    plan = m.build_plan(REPO / "output/collaboration/reward-mechanism-repair/partners-metadata-unrun-test")
    plan["status"] = "frozen"
    if mutation == "partial":
        plan["requests"].pop()
    elif mutation == "duplicate":
        plan["requests"][-1] = plan["requests"][0]
    elif mutation == "reorder":
        plan["requests"][:2] = plan["requests"][1::-1]
    elif mutation == "coalesce":
        plan["requests"][0]["metadata_bytes"] += 8
    elif mutation == "source":
        plan["source_bindings"][0]["sha256"] = "0" * 64
    elif mutation == "host":
        plan["object"]["url"] = "https://example.com/"
    elif mutation == "generation":
        plan["object"]["generation"] = "1"
    elif mutation in ("payload", "concurrency"):
        plan["limits"]["payload_bytes" if mutation == "payload" else "concurrency"] += 1
    elif mutation == "retry":
        plan["policy"]["retries"] = 1
    elif mutation == "output":
        plan["output_directory"] = str(REPO / "data")
    else:
        plan["status"] = "proposed"
    with pytest.raises(ValueError):
        m.validate_plan(plan)


def synthetic_run(
    tmp_path, *, change=None, clock=None, verify=None, cancelled=lambda: False, declared_rows=21
):
    payload, schema, one = arrow_fixture()
    blocks = [dict(one, index=i, offset=one["offset"] + i * 100000) for i in range(3)]
    plan = dict(
        requests=blocks,
        schema_fields=schema,
        output_directory=str(tmp_path / "synthetic-run"),
        object=dict(
            url=m.URL,
            object_bytes=m.OBJECT_BYTES,
            generation=m.GENERATION,
            etag=m.ETAG,
            declared_rows=declared_rows,
        ),
        limits=dict(
            requests=3,
            concurrency=1,
            payload_bytes=3 * len(payload),
            header_bytes=24576,
            response_bytes=24576 + 3 * len(payload),
            header_bytes_per_request=8192,
            request_active_seconds=14,
            request_wall_seconds=15,
            total_wall_seconds=1200,
        ),
        source_bindings=[],
        synthetic_only=True,
    )
    calls = []

    def transport(spec, limits, record, data):
        assert (tmp_path / "synthetic-run/requests.jsonl").read_text().count('"event":"intent"') == len(
            calls
        ) + 1
        calls.append(spec["index"])
        record.update(
            header_bytes=512,
            http_status=206,
            response_headers=[
                (
                    "Content-Range",
                    f"bytes {spec['offset']}-{spec['offset'] + len(payload) - 1}/{m.OBJECT_BYTES}",
                ),
                ("Content-Length", str(len(payload))),
                ("ETag", m.ETAG),
                ("x-goog-generation", m.GENERATION),
            ],
        )
        data.extend(payload)
        if change:
            change(spec, record, data)

    value = m._run_requests(
        plan,
        transport=transport,
        clock=clock or (lambda: 0.0),
        verify_sources=verify or (lambda: None),
        cancelled=cancelled,
    )
    return value, calls, plan


def test_complete_synthetic_run_is_durable_and_does_not_use_body_bytes(tmp_path):
    result, calls, _ = synthetic_run(tmp_path)
    assert result["status"] == "completed" and calls == [0, 1, 2]
    assert result["attempted_requests"] == result["received_requests"] == 3
    assert result["header_bytes"] == 1536 and result["body_payload_bytes_read"] == 0
    out = tmp_path / "synthetic-run"
    events = [json.loads(x) for x in (out / "requests.jsonl").read_text().splitlines()]
    assert [x["event"] for x in events] == ["intent", "outcome"] * 3
    assert [x["index"] for x in events[::2]] == [0, 1, 2]
    assert (out / "metadata.bin").stat().st_size == result["payload_bytes"]
    assert json.loads((out / "inventory.json").read_text())["missing_batches"] == 0
    with pytest.raises(FileExistsError):
        synthetic_run(tmp_path)


@pytest.mark.parametrize("position", [0, 1, 2])
@pytest.mark.parametrize("failure", ["http", "truncated", "version", "parser", "timeout", "oversize_headers"])
def test_failed_request_stops_without_retry_and_preserves_partial_outcome(tmp_path, position, failure):
    def change(spec, record, data):
        if spec["index"] != position:
            return
        if failure == "http":
            record["http_status"] = 200
        elif failure == "truncated":
            del data[-1:]
        elif failure == "version":
            record["response_headers"][-1] = ("x-goog-generation", "other")
        elif failure == "parser":
            data[0] = 0
        elif failure == "oversize_headers":
            record["header_bytes"] = 8193
        else:
            raise TimeoutError("synthetic timeout after bounded payload")

    result, calls, _ = synthetic_run(tmp_path, change=change)
    assert result["status"] == "failed" and calls == list(range(position + 1))
    assert result["attempted_requests"] == position + 1 and result["received_requests"] == position
    assert result["remaining_requests"] == 2 - position
    assert result["payload_bytes"] > 0
    events = [json.loads(x) for x in (tmp_path / "synthetic-run/requests.jsonl").read_text().splitlines()]
    assert events[-1]["status"] == "failed" and events[-1]["event"] == "outcome"
    assert (
        json.loads((tmp_path / "synthetic-run/inventory.json").read_text())["full_scan_body_buffer_bytes"]
        is None
    )


@pytest.mark.parametrize("stop", ["budget_stopped", "cancelled", "source"])
def test_stop_after_return_prevents_next_request(tmp_path, stop):
    elapsed, cancel, drift = [0.0], [False], [False]

    def change(spec, record, data):
        if stop == "budget_stopped":
            elapsed[0] = 1200
        elif stop == "cancelled":
            cancel[0] = True
        else:
            drift[0] = True

    def verify():
        if drift[0]:
            raise ValueError("synthetic bound source replacement")

    result, calls, _ = synthetic_run(
        tmp_path, change=change, clock=lambda: elapsed[0], cancelled=lambda: cancel[0], verify=verify
    )
    assert calls == [0]
    assert result["status"] == ("failed" if stop == "source" else stop)
    assert result["received_requests"] == 0


class ObservedStream(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.payload_read_sizes = []

    def read(self, size=-1):
        self.payload_read_sizes.append(size)
        return super().read(size)

    def close(self):
        # Test observation remains available after HTTPResponse correctly closes its file.
        pass


def fake_http(monkeypatch, raw):
    stream = ObservedStream(raw)

    class FakeSocket:
        def makefile(self, mode, buffering):
            assert mode == "rb" and buffering == 0
            return stream

    class Connection:
        def __init__(self, host, timeout):
            assert host == "storage.googleapis.com" and timeout == 14

        def request(self, method, path, headers):
            assert method == "GET" and path.endswith("?generation=1780494942562468")
            assert headers["Range"] == "bytes=3960-4599"
            assert headers["If-Match"] == '"58efcf712f8c4d4de5f2ad51e97def76"'
            assert headers["x-goog-if-generation-match"] == "1780494942562468"

        def getresponse(self):
            response = self.response_class(FakeSocket(), method="GET")
            response.begin()
            return response

        def close(self):
            pass

    monkeypatch.setattr(m.http.client, "HTTPSConnection", Connection)
    return stream


def http_bytes(status=206, alteration=None):
    pairs = [
        ("Content-Length", "640"),
        ("Content-Range", "bytes 3960-4599/6777179098"),
        ("ETag", '"58efcf712f8c4d4de5f2ad51e97def76"'),
        ("x-goog-generation", "1780494942562468"),
    ]
    if alteration:
        pairs = alteration(pairs)
    return (f"HTTP/1.1 {status} Example\r\n" + "".join(f"{k}: {v}\r\n" for k, v in pairs) + "\r\n").encode()


def fetch_fixture(spec):
    return (
        dict(spec, url=m.URL),
        dict(
            request_active_seconds=14,
            header_bytes_per_request=8192,
            header_remaining=8192,
            payload_remaining=640,
        ),
        dict(header_bytes=0),
        bytearray(),
    )


def test_actual_http_parser_reads_exact_range_and_no_641st_byte(monkeypatch, spec):
    header = http_bytes()
    stream = fake_http(monkeypatch, header + b"x" * 640 + b"UNREAD_BODY_SENTINEL")
    request, limits, record, payload = fetch_fixture(spec)
    m.fetch_one(request, limits, record, payload)
    assert len(payload) == 640 and stream.tell() == len(header) + 640
    assert stream.payload_read_sizes == [1] * len(header) + [640]
    assert record["header_bytes"] == len(header) and record["request_send_completed"]


@pytest.mark.parametrize("status", [200, 301, 302, 307, 401, 403, 404, 412, 416, 429, 500])
def test_real_response_status_rejection_occurs_before_payload(monkeypatch, spec, status):
    header = http_bytes(status)
    stream = fake_http(monkeypatch, header + b"DO_NOT_READ_BODY" * 100)
    request, limits, record, payload = fetch_fixture(spec)
    with pytest.raises(ValueError):
        m.fetch_one(request, limits, record, payload)
    assert not payload and stream.payload_read_sizes == [1] * len(header) and stream.tell() == len(header)


@pytest.mark.parametrize("failure", ["duplicate", "version", "range", "length", "chunked"])
def test_actual_http_identity_failure_does_not_consume_payload(monkeypatch, spec, failure):
    def change(pairs):
        if failure == "duplicate":
            return pairs + [("content-length", "640")]
        if failure == "chunked":
            return pairs + [("Transfer-Encoding", "chunked")]
        position = {"length": 0, "range": 1, "version": 3}[failure]
        pairs[position] = (pairs[position][0], "bad")
        return pairs

    header = http_bytes(alteration=change)
    stream = fake_http(monkeypatch, header + b"DO_NOT_READ_BODY" * 100)
    request, limits, record, payload = fetch_fixture(spec)
    with pytest.raises(ValueError):
        m.fetch_one(request, limits, record, payload)
    assert not payload and stream.payload_read_sizes == [1] * len(header)


@pytest.mark.parametrize("cap", [1, 16, 40, 90])
def test_header_application_bytes_stop_at_exact_remaining_budget(monkeypatch, spec, cap):
    header = http_bytes()
    stream = fake_http(monkeypatch, header + b"DO_NOT_READ_BODY" * 100)
    request, limits, record, payload = fetch_fixture(spec)
    limits["header_remaining"] = cap
    with pytest.raises(ValueError):
        m.fetch_one(request, limits, record, payload)
    assert record["header_bytes"] <= cap and stream.tell() <= cap and not payload


@pytest.mark.parametrize("boundary", ["inventory.json", "summary.json"])
@pytest.mark.parametrize("stop", ["budget", "cancel"])
def test_final_output_writes_cannot_create_completed_status_outside_budget(
    tmp_path, monkeypatch, boundary, stop
):
    elapsed, cancelled = [0.0], [False]
    write = m.atomic_json
    fired = False

    def publishing(path, value):
        nonlocal fired
        write(path, value)
        if path.name == boundary and not fired:
            fired = True
            if stop == "budget":
                elapsed[0] = 1200.0
            else:
                cancelled[0] = True

    monkeypatch.setattr(m, "atomic_json", publishing)
    result, calls, _ = synthetic_run(tmp_path, clock=lambda: elapsed[0], cancelled=lambda: cancelled[0])
    assert calls == [0, 1, 2] and result["status"] == ("budget_stopped" if stop == "budget" else "cancelled")
    inventory = json.loads((tmp_path / "synthetic-run/inventory.json").read_text())
    assert not inventory["eligible_for_scan_planning"] and inventory["full_scan_body_buffer_bytes"] is None


def test_failed_intent_persistence_never_invokes_network(tmp_path, monkeypatch):
    append = m.append

    def fail(path, data):
        if path.name == "requests.jsonl":
            raise OSError("synthetic intent fsync failure")
        append(path, data)

    monkeypatch.setattr(m, "append", fail)
    result, calls, _ = synthetic_run(tmp_path)
    assert not calls and result["attempted_requests"] == 0 and result["status"] == "failed"


def test_payload_persistence_failure_retains_measured_transfer_counts(tmp_path, monkeypatch):
    append = m.append

    def fail(path, data):
        if path.name == "metadata.bin":
            raise OSError("synthetic payload fsync failure")
        append(path, data)

    monkeypatch.setattr(m, "append", fail)
    result, calls, _ = synthetic_run(tmp_path)
    assert calls == [0] and result["status"] == "failed"
    assert result["payload_bytes"] > 0 and result["header_bytes"] == 512


def test_plan_validation_time_is_inside_total_execution_cap(tmp_path, monkeypatch):
    elapsed = [0.0]
    payload, schema, block = arrow_fixture()
    plan = dict(
        requests=[block],
        schema_fields=schema,
        output_directory=str(tmp_path / "synthetic-run"),
        object=dict(url=m.URL, object_bytes=m.OBJECT_BYTES, generation=m.GENERATION, etag=m.ETAG),
        limits=dict(
            requests=1,
            concurrency=1,
            payload_bytes=len(payload),
            header_bytes=8192,
            response_bytes=8192 + len(payload),
            header_bytes_per_request=8192,
            request_active_seconds=14,
            request_wall_seconds=15,
            total_wall_seconds=1200,
        ),
        source_bindings=[],
    )
    path = tmp_path / "plan.json"
    data = m.canonical(plan)
    path.write_bytes(data)

    def validate(value):
        elapsed[0] = 1200.0
        return value

    monkeypatch.setattr(m, "validate_plan", validate)
    monkeypatch.setattr(m.time, "monotonic", lambda: elapsed[0])
    monkeypatch.setattr(m, "fetch_one", lambda *_: pytest.fail("Cap exhausted before first GET"))
    result = m.execute(path, hashlib.sha256(data).hexdigest())
    assert result["status"] == "budget_stopped" and result["attempted_requests"] == 0


@pytest.mark.parametrize("declared_rows", [0, 20, 22, True, 21.0])
def test_final_metadata_row_reconciliation_failure_preserves_all_received_batches(tmp_path, declared_rows):
    result, calls, _ = synthetic_run(tmp_path, declared_rows=declared_rows)
    assert result["status"] == "failed" and calls == [0, 1, 2]
    assert result["received_requests"] == 3
    out = tmp_path / "synthetic-run"
    inventory = json.loads((out / "inventory.json").read_text())
    assert not inventory["eligible_for_scan_planning"] and inventory["full_scan_body_buffer_bytes"] is None
    assert len(inventory["batch_records"]) == 3 and inventory["validation_error"]
    assert json.loads((out / "summary.json").read_text())["status"] == "failed"


@pytest.mark.parametrize("check_number", [1, 2, 3])
@pytest.mark.parametrize("stop", ["budget", "cancel"])
def test_verification_crossing_stop_boundary_cannot_be_followed_by_get(tmp_path, check_number, stop):
    elapsed, cancelled, checks = [0.0], [False], [0]

    def verify():
        checks[0] += 1
        if checks[0] == check_number:
            if stop == "budget":
                elapsed[0] = 1200
            else:
                cancelled[0] = True

    result, calls, _ = synthetic_run(
        tmp_path, verify=verify, clock=lambda: elapsed[0], cancelled=lambda: cancelled[0]
    )
    assert not calls
    assert result["status"] == ("budget_stopped" if stop == "budget" else "cancelled")


def test_single_ipv4_failure_closes_socket_without_fallback(monkeypatch):
    endpoints = [(2, 1, 6, "", ("192.0.2.1", 443)), (2, 1, 6, "", ("192.0.2.2", 443))]
    monkeypatch.setattr(m.socket, "getaddrinfo", lambda *_: endpoints)
    events = []

    class Socket:
        def settimeout(self, timeout):
            events.append(("timeout", timeout))

        def connect(self, address):
            events.append(("connect", address))
            raise TimeoutError("synthetic first-address failure")

        def close(self):
            events.append(("close",))

    monkeypatch.setattr(m.socket, "socket", lambda *_: Socket())
    with pytest.raises(TimeoutError):
        m.ipv4_once(("storage.googleapis.com", 443), 14)
    assert events == [("timeout", 14), ("connect", ("192.0.2.1", 443)), ("close",)]


def test_absolute_alarm_escapes_socket_errors_and_restores_handler():
    assert not issubclass(m.DeadlineExceeded, OSError)
    previous = m.signal.getsignal(m.signal.SIGALRM)
    with pytest.raises(m.DeadlineExceeded):
        with m.deadline(14):
            m.signal.getsignal(m.signal.SIGALRM)(None, None)
    assert m.signal.getsignal(m.signal.SIGALRM) == previous
    assert m.signal.getitimer(m.signal.ITIMER_REAL) == (0.0, 0.0)


@pytest.mark.parametrize("ancestor", ["output", "collaboration", "reward-mechanism-repair"])
def test_output_ancestor_symlinks_cannot_redirect_the_study(tmp_path, monkeypatch, ancestor):
    monkeypatch.setattr(m, "REPO", tmp_path)
    base = tmp_path
    for component in ["output", "collaboration", "reward-mechanism-repair"]:
        base = base / component
        if component == ancestor:
            target = tmp_path / "outside"
            target.mkdir()
            base.symlink_to(target, target_is_directory=True)
        else:
            base.mkdir(exist_ok=True)
    with pytest.raises(ValueError):
        m.build_plan(base / "partners-metadata-example")


@pytest.mark.parametrize("count", [1, 7, 30, 90])
@pytest.mark.parametrize("failure", [TimeoutError, m.DeadlineExceeded, KeyboardInterrupt])
def test_partial_header_consumption_is_counted_when_primitive_read_raises(count, failure):
    class Partial(io.RawIOBase):
        consumed = 0

        def readinto(self, buffer):
            if self.consumed == count:
                raise failure("synthetic header interruption")
            buffer[0] = ord("x")
            self.consumed += 1
            return 1

    record = dict(header_bytes=0)
    stream = Partial()
    with pytest.raises(failure):
        m.HeaderReader(stream, record, 8192).readline()
    assert stream.consumed == record["header_bytes"] == count


@pytest.mark.parametrize("elapsed", [1184, 1185, 1199, 1200])
@pytest.mark.parametrize("stage", ["source", "intent"])
def test_request_close_reserve_is_rechecked_immediately_before_transport(
    tmp_path, monkeypatch, elapsed, stage
):
    now, checks = [0.0], [0]

    def verify():
        checks[0] += 1
        if stage == "source" and checks[0] == 3:
            now[0] = elapsed

    append = m.append

    def persist(path, data):
        append(path, data)
        if stage == "intent" and path.name == "requests.jsonl" and b'"event":"intent"' in data:
            now[0] = elapsed

    monkeypatch.setattr(m, "append", persist)
    result, calls, _ = synthetic_run(tmp_path, verify=verify, clock=lambda: now[0])
    assert calls == ([0, 1, 2] if elapsed == 1184 else [])
    assert result["status"] == ("completed" if elapsed == 1184 else "budget_stopped")


@pytest.mark.parametrize("phase", ["parse", "verification", "persistence"])
@pytest.mark.parametrize("seconds", [0, 16, 1200])
def test_transport_clock_is_separate_from_processing_and_total_cap(tmp_path, monkeypatch, phase, seconds):
    now, returned, advanced = [0.0], [False], [False]
    parse, append = m.parse_batch, m.append

    def advance():
        if returned[0] and not advanced[0]:
            now[0] += seconds
            advanced[0] = True

    def parse_slow(*args):
        result = parse(*args)
        if phase == "parse":
            advance()
        return result

    def verify():
        if phase == "verification":
            advance()

    def persist(path, data):
        append(path, data)
        if phase == "persistence" and path.name == "metadata.bin":
            advance()

    def finish(*args):
        now[0] += 1
        returned[0] = True

    monkeypatch.setattr(m, "parse_batch", parse_slow)
    monkeypatch.setattr(m, "append", persist)
    result, calls, _ = synthetic_run(tmp_path, change=finish, verify=verify, clock=lambda: now[0])
    events = [json.loads(x) for x in (tmp_path / "synthetic-run/requests.jsonl").read_text().splitlines()]
    outcomes = [x for x in events if x["event"] == "outcome"]
    assert all(x["request_wall_seconds"] == 1 for x in outcomes)
    assert outcomes[0]["processing_wall_seconds"] == seconds
    assert result["elapsed_seconds"] == len(calls) + seconds
    assert result["status"] == ("completed" if seconds < 1200 else "budget_stopped")
