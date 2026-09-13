"""Independent no-network stream and durable-boundary probes for the metadata client."""

import hashlib
import io
import json

import pytest

import partners_metadata_inventory as candidate
from test_partners_metadata_independent_client import fixture


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("Independent metadata review forbids real network access")

    monkeypatch.setattr(candidate.socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(candidate.socket, "socket", forbidden)


def plan_and_payload(tmp_path, count=3):
    payload, schema, block, _ = fixture(11, "lz4", "mixed")
    blocks = [dict(block, index=i, offset=block["offset"] + i * 100000) for i in range(count)]
    plan = dict(
        requests=blocks,
        schema_fields=schema,
        output_directory=str(tmp_path / "SYNTHETIC_ONLY"),
        object=dict(
            url=candidate.URL,
            object_bytes=candidate.OBJECT_BYTES,
            generation=candidate.GENERATION,
            etag=candidate.ETAG,
        ),
        limits=dict(
            requests=count,
            concurrency=1,
            payload_bytes=count * len(payload),
            header_bytes=8192 * count,
            response_bytes=(8192 + len(payload)) * count,
            header_bytes_per_request=8192,
            request_active_seconds=14,
            request_wall_seconds=15,
            total_wall_seconds=1200,
        ),
        source_bindings=[],
        synthetic_only=True,
    )
    return plan, payload


def exact_headers(spec, size):
    return [
        ("Content-Range", f"bytes {spec['offset']}-{spec['offset'] + size - 1}/{spec['object_bytes']}"),
        ("Content-Length", str(size)),
        ("ETag", spec["etag"]),
        ("x-goog-generation", spec["generation"]),
    ]


class Wire(io.BytesIO):
    def __init__(self, raw, chunk):
        super().__init__(raw)
        self.chunk = chunk
        self.body_calls = []
        self.read_positions = []

    def read(self, size=-1):
        self.body_calls.append(size)
        self.read_positions.append(self.tell())
        assert size >= 0
        return super().read(min(size, self.chunk))

    def close(self):
        pass  # Preserve the synthetic stream position for independent inspection.


def injected_connection(monkeypatch, wire, observations):
    class Socket:
        def makefile(self, mode, buffering):
            assert mode == "rb" and buffering == 0
            return wire

    class Connection:
        def __init__(self, host, timeout):
            observations.append(("open", host, timeout))

        def request(self, method, path, headers):
            observations.append(("request", method, path, headers))

        def getresponse(self):
            result = self.response_class(Socket(), method="GET")
            result.begin()
            return result

        def close(self):
            observations.append(("close",))

    monkeypatch.setattr(candidate.http.client, "HTTPSConnection", Connection)


@pytest.mark.parametrize("chunk", [1, 7, 639, 640, 4096])
@pytest.mark.parametrize("prefix", [b"", b"HTTP/1.1 100 Continue\r\nX-Test: synthetic\r\n\r\n"])
def test_exact_payload_stream_never_reads_next_region(tmp_path, monkeypatch, chunk, prefix):
    plan, payload = plan_and_payload(tmp_path, 1)
    spec = dict(plan["requests"][0], **plan["object"])
    header = (
        b"HTTP/1.1 206 Partial Content\r\n"
        + b"".join(f"{k}: {v}\r\n".encode() for k, v in exact_headers(spec, len(payload)))
        + b"\r\n"
    )
    wire = Wire(prefix + header + payload + b"UNREAD_BODY_SENTINEL", chunk)
    observations = []
    injected_connection(monkeypatch, wire, observations)
    limits = dict(plan["limits"], payload_remaining=len(payload), header_remaining=8192)
    record, received = {"header_bytes": 0}, bytearray()
    candidate.fetch_one(spec, limits, record, received)
    assert bytes(received) == payload
    assert wire.tell() == len(prefix) + len(header) + len(payload)
    assert record["header_bytes"] == len(prefix) + len(header)
    assert [x[0] for x in observations] == ["open", "request", "close"]
    assert all(0 < size <= len(payload) for size in wire.body_calls)


@pytest.mark.parametrize("difference", [-1, 0, 1])
def test_header_budget_is_exact_inclusive_and_payload_is_separate(tmp_path, monkeypatch, difference):
    plan, payload = plan_and_payload(tmp_path, 1)
    spec = dict(plan["requests"][0], **plan["object"])
    header = (
        b"HTTP/1.1 206 Partial Content\r\n"
        + b"".join(f"{k}: {v}\r\n".encode() for k, v in exact_headers(spec, len(payload)))
        + b"\r\n"
    )
    wire = Wire(header + payload + b"UNREAD", 71)
    injected_connection(monkeypatch, wire, [])
    cap = len(header) + difference
    limits = dict(plan["limits"], payload_remaining=len(payload), header_remaining=cap)
    record, received = {"header_bytes": 0}, bytearray()
    if difference < 0:
        with pytest.raises(ValueError):
            candidate.fetch_one(spec, limits, record, received)
        assert not received and wire.tell() <= cap
        assert all(position < len(header) for position in wire.read_positions)
    else:
        candidate.fetch_one(spec, limits, record, received)
        assert bytes(received) == payload and record["header_bytes"] == len(header)


@pytest.mark.parametrize("position", [0, 1, 2])
@pytest.mark.parametrize("failure", ["partial", "cancel", "source", "deadline"])
def test_first_failure_preserves_all_received_bytes_and_no_later_attempt(tmp_path, position, failure):
    plan, payload = plan_and_payload(tmp_path)
    elapsed, cancelled, changed = [0.0], [False], [False]
    seen = []

    def transport(spec, limits, record, received):
        seen.append(spec["index"])
        record.update(header_bytes=311, http_status=206, response_headers=exact_headers(spec, len(payload)))
        if spec["index"] == position and failure == "partial":
            received.extend(payload[:97])
            raise TimeoutError("Synthetic interrupted exact metadata interval")
        received.extend(payload)
        if spec["index"] == position:
            cancelled[0] = failure == "cancel"
            changed[0] = failure == "source"
            elapsed[0] = 1200.0 if failure == "deadline" else 0.0

    def verify():
        if changed[0]:
            raise ValueError("Synthetic immutable source drift")

    result = candidate._run_requests(
        plan,
        transport=transport,
        clock=lambda: elapsed[0],
        verify_sources=verify,
        cancelled=lambda: cancelled[0],
    )
    assert seen == list(range(position + 1))
    assert result["received_requests"] == position
    assert result["attempted_requests"] == position + 1
    assert result["status"] == {"cancel": "cancelled", "deadline": "budget_stopped"}.get(failure, "failed")
    directory = tmp_path / "SYNTHETIC_ONLY"
    expected = payload * position + (payload[:97] if failure == "partial" else payload)
    assert (directory / "metadata.bin").read_bytes() == expected
    assert result["payload_bytes"] == len(expected)
    assert result["header_bytes"] == 311 * (position + 1)
    assert result["response_bytes"] == result["payload_bytes"] + result["header_bytes"]
    assert result["files"]["metadata.bin"]["sha256"] == hashlib.sha256(expected).hexdigest()
    events = [json.loads(x) for x in (directory / "requests.jsonl").read_text().splitlines()]
    assert [x["event"] for x in events] == ["intent", "outcome"] * (position + 1)
    assert events[-1]["status"] == "failed"
    inventory = json.loads((directory / "inventory.json").read_text())
    assert not inventory["eligible_for_scan_planning"]
    assert inventory["full_scan_body_buffer_bytes"] is None


@pytest.mark.parametrize("position", [0, 1, 2])
@pytest.mark.parametrize("remaining", [0, 310, 311])
def test_aggregate_headers_reserve_each_request_without_retry(tmp_path, position, remaining):
    plan, payload = plan_and_payload(tmp_path)
    plan["limits"]["header_bytes"] = position * 311 + remaining
    seen = []

    def transport(spec, limits, record, received):
        seen.append(spec["index"])
        record.update(
            header_bytes=min(311, limits["header_remaining"]),
            http_status=206,
            response_headers=exact_headers(spec, len(payload)),
        )
        if limits["header_remaining"] < 311:
            raise ValueError("Synthetic header parser cap before payload")
        received.extend(payload)

    result = candidate._run_requests(
        plan, transport=transport, clock=lambda: 0.0, verify_sources=lambda: None
    )
    successes = min(3, position + int(remaining == 311))
    attempts = min(3, successes + int(remaining == 310))
    assert seen == list(range(attempts))
    assert result["header_bytes"] <= plan["limits"]["header_bytes"]
    assert result["received_requests"] == successes
    assert result["payload_bytes"] == successes * len(payload)
    assert result["status"] == (
        "completed" if successes == 3 else "failed" if remaining == 310 else "budget_stopped"
    )


@pytest.mark.parametrize("stop", ["deadline", "cancel"])
def test_pre_request_source_verification_cannot_cross_stop_and_then_start_transport(tmp_path, stop):
    plan, _ = plan_and_payload(tmp_path)
    elapsed, cancelled, verifications, invoked = [0.0], [False], [0], []

    def verify():
        verifications[0] += 1
        if verifications[0] == 3:  # Initial, loop reservation, then immediately before transport.
            elapsed[0] = 1200.0 if stop == "deadline" else 0.0
            cancelled[0] = stop == "cancel"

    result = candidate._run_requests(
        plan,
        transport=lambda *_: invoked.append(True),
        clock=lambda: elapsed[0],
        verify_sources=verify,
        cancelled=lambda: cancelled[0],
    )
    assert not invoked, "Source hashing crossed the stop boundary before transport began"
    assert result["status"] == ("budget_stopped" if stop == "deadline" else "cancelled")


@pytest.mark.parametrize("consumed", [1, 7, 31])
@pytest.mark.parametrize("error", [TimeoutError, candidate.DeadlineExceeded, KeyboardInterrupt])
def test_interrupted_header_line_keeps_every_returned_socket_byte_in_accounting(consumed, error):
    class Interrupted(io.RawIOBase):
        def __init__(self):
            self.consumed = 0

        def readable(self):
            return True

        def readinto(self, buffer):
            if self.consumed == consumed:
                raise error("Synthetic partial header interruption")
            buffer[0] = ord("H")
            self.consumed += 1
            return 1

    stream, record = Interrupted(), {"header_bytes": 0}
    reader = candidate.HeaderReader(stream, record, 8192)
    with pytest.raises(error):
        reader.readline()
    assert stream.consumed == consumed
    assert record["header_bytes"] == consumed


@pytest.mark.parametrize("elapsed_after", [1184.0, 1185.0, 1199.0, 1200.0])
@pytest.mark.parametrize("phase", ["verification", "intent_persistence"])
def test_request_reserve_is_checked_after_all_pre_transport_work(tmp_path, monkeypatch, phase, elapsed_after):
    plan, _ = plan_and_payload(tmp_path)
    elapsed, verifications, invoked = [0.0], [0], []
    append = candidate.append

    def persist(path, data):
        append(path, data)
        if phase == "intent_persistence" and b'"event":"intent"' in data:
            elapsed[0] = elapsed_after

    def verify():
        verifications[0] += 1
        if phase == "verification" and verifications[0] == 3:
            elapsed[0] = elapsed_after

    def transport(*_args):
        invoked.append(True)
        raise TimeoutError("Synthetic stop after observing eligibility to start")

    monkeypatch.setattr(candidate, "append", persist)
    result = candidate._run_requests(
        plan, transport=transport, clock=lambda: elapsed[0], verify_sources=verify
    )
    assert bool(invoked) == (elapsed_after == 1184.0)
    assert result["status"] == ("failed" if elapsed_after == 1184.0 else "budget_stopped")


def completing_transport(payload):
    def transport(spec, limits, record, received):
        record.update(header_bytes=311, http_status=206, response_headers=exact_headers(spec, len(payload)))
        received.extend(payload)

    return transport


@pytest.mark.parametrize("preparation_seconds", [1.0, 600.0, 1200.0])
def test_execution_uses_the_initial_clock_origin(tmp_path, monkeypatch, preparation_seconds):
    plan, payload = plan_and_payload(tmp_path, 1)
    data = candidate.canonical(plan)
    path = tmp_path / "synthetic-plan.json"
    path.write_bytes(data)
    elapsed, invoked = [0.0], []

    def validate(value):
        elapsed[0] = preparation_seconds
        return value  # This tests only execution timing, never a scientific qualification claim.

    complete = completing_transport(payload)

    def transport(*args):
        invoked.append(True)
        complete(*args)

    monkeypatch.setattr(candidate, "validate_plan", validate)
    monkeypatch.setattr(candidate, "fetch_one", transport)
    monkeypatch.setattr(candidate.time, "monotonic", lambda: elapsed[0])
    result = candidate.execute(path, hashlib.sha256(data).hexdigest())
    assert result["elapsed_seconds"] == preparation_seconds
    assert len(invoked) == int(preparation_seconds < 1200.0)
    assert result["status"] == ("completed" if preparation_seconds < 1200 else "budget_stopped")


@pytest.mark.parametrize("declared_rows", [32, 33, 34])
def test_all_batch_row_crosscheck_failure_still_has_durable_terminal_summary(tmp_path, declared_rows):
    plan, payload = plan_and_payload(tmp_path)
    plan["object"]["declared_rows"] = declared_rows
    result = candidate._run_requests(
        plan, transport=completing_transport(payload), clock=lambda: 0.0, verify_sources=lambda: None
    )
    directory = tmp_path / "SYNTHETIC_ONLY"
    durable = json.loads((directory / "summary.json").read_text())
    inventory = json.loads((directory / "inventory.json").read_text())
    assert result == durable
    assert durable["received_requests"] == 3
    assert (directory / "metadata.bin").read_bytes() == payload * 3
    assert durable["status"] == ("completed" if declared_rows == 33 else "failed")
    assert inventory["eligible_for_scan_planning"] == (declared_rows == 33)
    if declared_rows != 33:
        assert inventory["full_scan_body_buffer_bytes"] is None


@pytest.mark.parametrize("boundary", ["inventory.json", "summary.json"])
@pytest.mark.parametrize("stop", ["deadline", "cancel", "source"])
def test_last_persist_cannot_leave_success_after_stop_or_input_drift(tmp_path, monkeypatch, boundary, stop):
    plan, payload = plan_and_payload(tmp_path)
    elapsed, cancelled, drift, fired = [0.0], [False], [False], [False]
    publish = candidate.atomic_json

    def persist(path, value):
        publish(path, value)
        if path.name == boundary and not fired[0]:
            fired[0] = True
            elapsed[0] = 1200.0 if stop == "deadline" else 0.0
            cancelled[0] = stop == "cancel"
            drift[0] = stop == "source"

    def verify():
        if drift[0]:
            raise ValueError("Synthetic source replacement while writing final result")

    monkeypatch.setattr(candidate, "atomic_json", persist)
    result = candidate._run_requests(
        plan,
        transport=completing_transport(payload),
        clock=lambda: elapsed[0],
        verify_sources=verify,
        cancelled=lambda: cancelled[0],
    )
    directory = tmp_path / "SYNTHETIC_ONLY"
    assert result["status"] == {"deadline": "budget_stopped", "cancel": "cancelled", "source": "failed"}[stop]
    assert json.loads((directory / "summary.json").read_text()) == result
    inventory = json.loads((directory / "inventory.json").read_text())
    assert not inventory["eligible_for_scan_planning"]
    assert inventory["full_scan_body_buffer_bytes"] is None
    assert (
        result["files"]["inventory.json"]["sha256"]
        == hashlib.sha256((directory / "inventory.json").read_bytes()).hexdigest()
    )


@pytest.mark.parametrize("phase", ["parse", "after_transport_verification"])
def test_received_outcome_cannot_report_an_accepted_request_wall_cap_violation(tmp_path, monkeypatch, phase):
    plan, payload = plan_and_payload(tmp_path, 1)
    elapsed, returned, advanced = [0.0], [False], [False]
    parse, complete = candidate.parse_batch, completing_transport(payload)

    def transport(*args):
        complete(*args)
        returned[0] = True

    def parse_slow(*args):
        result = parse(*args)
        if phase == "parse":
            elapsed[0] = 16.0
        return result

    def verify():
        if phase == "after_transport_verification" and returned[0] and not advanced[0]:
            advanced[0] = True
            elapsed[0] = 16.0

    monkeypatch.setattr(candidate, "parse_batch", parse_slow)
    result = candidate._run_requests(
        plan, transport=transport, clock=lambda: elapsed[0], verify_sources=verify
    )
    events = [json.loads(x) for x in (tmp_path / "SYNTHETIC_ONLY/requests.jsonl").read_text().splitlines()]
    assert events[-1]["status"] != "received" or events[-1]["request_wall_seconds"] <= 15.0
    assert result["status"] != "completed" or events[-1]["request_wall_seconds"] <= 15.0
