"""Output-only, metadata-only partners inventory. Network execution is gated."""

from collections import Counter
import argparse
import base64
from contextlib import contextmanager
import datetime
import hashlib
import http.client
import importlib.util
import json
import os
from pathlib import Path
import re
import struct
import sys
import signal
import socket
import time
from urllib.parse import urlsplit


REPO = next(p for p in Path(__file__).resolve().parents if (p / "bet36fly").is_dir())
EVIDENCE = REPO / "docs/evidence/reward-mechanism-repair-2026-09-12"
URL = "https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/syn-partners-male-cns-v1.0-minconf-0.5.feather"
GENERATION = "1780494942562468"
ETAG = '"58efcf712f8c4d4de5f2ad51e97def76"'
OBJECT_BYTES = 6777179098
SUFFIX_SHA = "7779ff2b04999bae9447db9dbae2570448bdb2c8bdbc9b11da3906f0e9789701"
TOTAL_ROWS = 311833243
NAMES = [
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
TYPES = [
    "int32",
    "int32",
    "int32",
    "int64",
    "float",
    "int32",
    "int32",
    "int32",
    "int64",
    "float",
    "dictionary<values=string, indices=int16, ordered=1>",
]
SCHEMA = [dict(name=n, type=t, nullable=True, metadata={}) for n, t in zip(NAMES, TYPES)]


def _load(name):
    path = EVIDENCE / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_footer_parser = _load("localization_range_inspect")
_metadata_parser = _load("localization_batch_metadata_inspect")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    value = json.loads(data, object_pairs_hook=pairs)
    canonical(value)
    return value


def requests_from_footer(footer, suffix):
    """Cross-check every requested block against preserved raw suffix and Arrow schema."""
    record = footer["object_record"]
    if (
        record["url"] != URL
        or record["object_bytes"] != OBJECT_BYTES
        or record["headers"]["x-goog-generation"] != GENERATION
        or record["headers"]["etag"] != ETAG
        or hashlib.sha256(suffix).hexdigest() != SUFFIX_SHA
        or record["payload_sha256"] != SUFFIX_SHA
        or len(suffix) != 262144
        or suffix[-6:] != b"ARROW1"
    ):
        raise ValueError("Preserved partners object/suffix identity differs")
    length = struct.unpack_from("<i", suffix, len(suffix) - 10)[0]
    if length != 116632 or footer["footer_start"] != OBJECT_BYTES - length - 10:
        raise ValueError("Complete footer coverage differs")
    raw = suffix[-10 - length : -10]
    if hashlib.sha256(raw).hexdigest() != footer["footer_sha256"]:
        raise ValueError("Footer hash differs")
    flat = _footer_parser.FlatFooter(raw)
    batches, dictionaries = flat.blocks(3), flat.blocks(2)
    if (
        canonical(batches) != canonical(footer["record_batches"])
        or canonical(dictionaries) != canonical(footer["dictionaries"])
        or len(batches) != 4759
        or sum(x["metadata_bytes"] for x in batches) != 3045760
        or any(x["metadata_bytes"] != 640 for x in batches)
    ):
        raise ValueError("Exported metadata intervals differ from full raw footer")
    ordered = sorted(batches + dictionaries, key=lambda b: b["offset"])
    for i, block in enumerate(ordered):
        end = block["offset"] + block["metadata_bytes"] + block["body_bytes"]
        next_start = ordered[i + 1]["offset"] if i + 1 < len(ordered) else footer["footer_start"]
        if (
            block["offset"] < 0
            or block["body_bytes"] < 0
            or not block["metadata_bytes"] > 0
            or end > next_start
        ):
            raise ValueError("Overlapping/out-of-object block extent")
    reader = _footer_parser.ipc.open_file(
        _footer_parser.SuffixFile(suffix, OBJECT_BYTES - len(suffix), OBJECT_BYTES)
    )
    actual_schema = [
        dict(name=f.name, type=str(f.type), nullable=f.nullable, metadata={}) for f in reader.schema
    ]
    if actual_schema != SCHEMA or footer["schema"] != SCHEMA or reader.num_record_batches != 4759:
        raise ValueError("Frozen flat partners schema differs")
    return batches


def validate_headers(spec, status, headers, payload_remaining):
    """Validate exact content/version/framing before any application payload read."""
    normalized = {}
    hash_lines = []
    interpreted = {
        "content-range",
        "content-length",
        "etag",
        "x-goog-generation",
        "content-encoding",
        "transfer-encoding",
    }
    for key, value in headers:
        if (
            not isinstance(key, str)
            or not re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", key)
            or not isinstance(value, str)
            or any(ord(c) < 32 and c != "\t" or ord(c) == 127 or ord(c) > 255 for c in value)
        ):
            raise ValueError("Malformed response header")
        key = key.lower()
        if key == "x-goog-hash":
            hash_lines.append(value)
        elif key in interpreted:
            if key in normalized:
                raise ValueError("Duplicate response header")
            normalized[key] = value
        # All other raw fields stay ordered/opaque in the durable response_headers.
    parse_object_hashes(hash_lines)
    if type(status) is not int or status != 206:
        raise ValueError("Exact metadata range requires206")
    if "transfer-encoding" in normalized or normalized.get("content-encoding", "identity") != "identity":
        raise ValueError("Unsupported HTTP framing or encoding")
    length = spec["metadata_bytes"]
    expected = f"bytes {spec['offset']}-{spec['offset'] + length - 1}/{spec['object_bytes']}"
    if (
        normalized.get("content-range") != expected
        or normalized.get("content-length") != str(length)
        or normalized.get("etag") != spec["etag"]
        or normalized.get("x-goog-generation") != spec["generation"]
    ):
        raise ValueError("Exact metadata range, length or version differs")
    if type(payload_remaining) is not int or not 0 < length <= payload_remaining:
        raise ValueError("Remaining payload budget insufficient")
    return length


def parse_object_hashes(lines):
    """Documented optional object checksum list; never validates a range payload."""
    result, known = [], {}
    for line in lines:
        for item in line.split(","):
            item = item.strip(" \t")
            if not item:
                continue
            algorithm, separator, encoded = item.partition("=")
            if not separator or algorithm not in {"md5", "crc32c"}:
                raise ValueError("Unsupported object hash list member")
            try:
                raw = base64.b64decode(encoded, validate=True)
            except (ValueError, TypeError) as exc:
                raise ValueError("Invalid object hash base64") from exc
            if len(raw) != (16 if algorithm == "md5" else 4) or base64.b64encode(raw).decode() != encoded:
                raise ValueError("Invalid object hash width/canonical encoding")
            if algorithm in known and known[algorithm] != encoded:
                raise ValueError("Conflicting object hash list values")
            known[algorithm] = encoded
            result.append(dict(algorithm=algorithm, value=encoded))
    if lines and not result:
        raise ValueError("Object hash list has no value")
    return result


def parse_batch(payload, schema, block):
    """Inventory declared buffer locations only; never access/decompress a body buffer."""
    if schema != SCHEMA:
        raise ValueError("Fixed partners schema required")
    value = _metadata_parser.parse_metadata(payload, schema, block)
    if value["metadata_version_number"] != 4 or value["custom_message_metadata_count"] != 0:
        raise ValueError("Uninspected Arrow version/custom metadata")
    for field, width in zip(value["fields"], [4, 4, 4, 8, 4, 4, 4, 4, 8, 4, 2]):
        for kind, needed in (
            ("validity", (value["rows"] + 7) // 8 if field["node"]["null_count"] else 0),
            ("values", value["rows"] * width),
        ):
            size = field[kind + "_buffer"]["length"]
            if value["compression"] is None:
                if size < needed:
                    raise ValueError("Undersized fixed-width/validity buffer declaration")
            elif (needed and size <= 8) or (0 < size < 8):
                raise ValueError("Compressed buffer cannot contain required8-byte prefix")
    row = dict(
        block=block.copy(),
        rows=value["rows"],
        compression=value["compression"],
        body_payload_bytes_read=0,
        metadata_sha256=hashlib.sha256(payload).hexdigest(),
    )
    for name in ("body_pre", "body_post"):
        field = next(f for f in value["fields"] if f["name"] == name)
        row[name] = dict(null_count=field["node"]["null_count"])
        for kind in ("validity", "values"):
            buf = field[kind + "_buffer"]
            row[name][kind] = dict(offset=value["body_start"] + buf["offset"], bytes=buf["length"])
    return row


def assemble_inventory(records, blocks, expected_rows=None):
    if len(records) > len(blocks):
        raise ValueError("Too many batch records")
    for i, row in enumerate(records):
        if canonical(row["block"]) != canonical(blocks[i]) or row["body_payload_bytes_read"] != 0:
            raise ValueError("Batch identity duplicate/missing/reordered or unexpected body read")
    columns = {}
    for name in ("body_pre", "body_post"):
        columns[name] = {
            kind + "_bytes": sum(row[name][kind]["bytes"] for row in records)
            for kind in ("validity", "values")
        }
        columns[name]["null_count"] = sum(row[name]["null_count"] for row in records)
    total = sum(c["validity_bytes"] + c["values_bytes"] for c in columns.values())
    rows = sum(row["rows"] for row in records)
    complete = len(records) == len(blocks)
    expected_rows = TOTAL_ROWS if expected_rows is None and len(blocks) == 4759 else expected_rows
    if complete and expected_rows is not None and (type(expected_rows) is not int or rows != expected_rows):
        raise ValueError("All-batch row total differs from declared frozen row count")
    return dict(
        complete=complete,
        inspected_batches=len(records),
        missing_batches=len(blocks) - len(records),
        inspected_rows=rows,
        full_scan_body_buffer_bytes=total if complete else None,
        inspected_body_buffer_bytes=total,
        body_columns=columns,
        compression_counts=dict(
            Counter(
                "uncompressed" if r["compression"] is None else r["compression"]["codec"] for r in records
            )
        ),
        body_payload_bytes_read=0,
        batch_records=records,
    )


def build_plan(output_directory):
    output_directory = Path(output_directory).absolute()
    base = REPO / "output/collaboration/reward-mechanism-repair"
    if (
        output_directory.parent != base
        or not re.fullmatch(r"partners-metadata-[A-Za-z0-9_-]+", output_directory.name)
        or output_directory.is_symlink()
        or base.is_symlink()
    ):
        raise ValueError("Output must be a new dedicated partners-metadata directory")
    if any(p.is_symlink() for p in [base, base.parent, base.parent.parent]):
        raise ValueError("Output ancestry cannot redirect the study")
    previous = EVIDENCE / "localization-range-probe-2026-09-13"
    footer_path = previous / "footer-inspection-02.json"
    suffix_path = previous / "payload-02.bin"
    footer = strict_json(footer_path.read_bytes())
    blocks = requests_from_footer(footer, suffix_path.read_bytes())
    paths = [
        Path(__file__),
        Path(__file__).with_name("test_partners_metadata_inventory_v2.py"),
        Path(__file__).with_name("test_partners_metadata_headers_v2.py"),
        Path(__file__).with_name("partners-metadata-v2-source-contract-2026-09-13.md"),
        Path(__file__).with_name("partners-metadata-inventory-2026-09-13") / "requests.jsonl",
        EVIDENCE / "localization_range_inspect.py",
        EVIDENCE / "localization_batch_metadata_inspect.py",
        EVIDENCE / "localization_batch_metadata_probe.py",
        footer_path,
        suffix_path,
        previous / "result-02.json",
        previous / "payload-03.bin",
        previous / "payload-04.bin",
        EVIDENCE / "localization-batch-metadata-2026-09-13/payload-03.bin",
        EVIDENCE / "localization-batch-metadata-2026-09-13/payload-02.bin",
    ]
    return dict(
        schema="partners-metadata-inventory-v2",
        status="proposed",
        object=dict(
            url=URL, object_bytes=OBJECT_BYTES, generation=GENERATION, etag=ETAG, declared_rows=TOTAL_ROWS
        ),
        schema_fields=SCHEMA,
        requests=blocks,
        output_directory=str(output_directory),
        source_bindings=[binding(p) for p in paths],
        limits=dict(
            requests=4759,
            concurrency=1,
            payload_bytes=3045760,
            header_bytes=8388608,
            response_bytes=11434368,
            header_bytes_per_request=8192,
            request_active_seconds=14,
            request_wall_seconds=15,
            total_wall_seconds=1200,
        ),
        policy=dict(
            retries=0,
            redirects=0,
            fallback_addresses=0,
            coalescing=False,
            network_scope="Each exact metadata interval once, including the earlier first-batch reference.",
            transport="Sequential fresh verified-TLS connection to one AF_INET address per request.",
            stop="First failure, source drift, cancellation or aggregate deadline; no resume/replacement requests.",
            accounting="Application HTTP status/header bytes and exact metadata payload; not TLS/TCP wire bytes.",
            header_semantics="Strict interpreted singleton fields; documented optional GCS MD5/CRC32C lists; all raw fields retained in order, ancillary fields opaque. Whole-object checksums do not validate metadata range payloads.",
            timing="The whole-study clock starts before initial validation. Recheck a 16-second reserve immediately before transport. request_wall_seconds measures DNS/TCP/TLS/HTTP/close only; processing_wall_seconds separately records source verification, parsing and payload persistence within the total cap.",
            result="Declared body-column ranges/cost only; no body values, dictionaries, coordinates or decompression.",
        ),
    )


def validate_plan(plan):
    if not isinstance(plan, dict) or plan.get("status") != "frozen":
        raise ValueError("A reviewed frozen plan is required")
    expected = build_plan(plan.get("output_directory", ""))
    expected["status"] = "frozen"
    if canonical(plan) != canonical(expected):
        raise ValueError("Plan differs from complete locked ranges, bindings or fixed execution limits")
    return plan


def binding(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 5 * 1024 * 1024:
        raise ValueError("Invalid or oversized source binding")
    data = path.read_bytes()
    return dict(path=str(path.absolute()), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def write_exclusive(path, data):
    with Path(path).open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def append(path, data):
    with Path(path).open("ab") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def atomic_json(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    write_exclusive(temp, canonical(value) + b"\n")
    os.replace(temp, path)


class BudgetStopped(RuntimeError):
    pass


class Cancelled(RuntimeError):
    pass


def _run_requests(
    plan, *, transport, clock, verify_sources, cancelled=lambda: False, plan_bytes=None, started=None
):
    """Internal prevalidated executor; injectable transport/clock support network-free fixtures."""
    started = clock() if started is None else started
    directory = Path(plan["output_directory"])
    directory.mkdir(exist_ok=False)
    limits = plan["limits"]
    plan_bytes = plan_bytes or canonical(plan)
    write_exclusive(directory / "plan.json", plan_bytes)
    journal, packed = directory / "requests.jsonl", directory / "metadata.bin"
    write_exclusive(journal, b"")
    write_exclusive(packed, b"")
    summary = dict(
        status="running",
        attempted_requests=0,
        received_requests=0,
        planned_requests=len(plan["requests"]),
        remaining_requests=len(plan["requests"]),
        payload_bytes=0,
        header_bytes=0,
        response_bytes=0,
        body_payload_bytes_read=0,
        plan_sha256=hashlib.sha256(plan_bytes).hexdigest(),
        limits=limits,
        started_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
    records = []

    def guard(*, next_request=False):
        if cancelled():
            raise Cancelled("Cancellation observed")
        elapsed = clock() - started
        if elapsed >= limits["total_wall_seconds"] or (
            next_request and elapsed > limits["total_wall_seconds"] - 16
        ):
            raise BudgetStopped("Fixed aggregate wall budget reached or insufficient request/close reserve")
        verify_sources()
        if cancelled():
            raise Cancelled("Cancellation observed during source verification")
        elapsed = clock() - started
        if elapsed >= limits["total_wall_seconds"] or (
            next_request and elapsed > limits["total_wall_seconds"] - 16
        ):
            raise BudgetStopped("Source verification reached the fixed wall boundary")

    try:
        guard()
        for block in plan["requests"]:
            guard(next_request=True)
            if summary["attempted_requests"] >= limits["requests"]:
                raise BudgetStopped("Fixed request count exhausted")
            spec = dict(
                block, **{k: plan["object"][k] for k in ("url", "object_bytes", "generation", "etag")}
            )
            request_limits = dict(
                limits,
                payload_remaining=limits["payload_bytes"] - summary["payload_bytes"],
                header_remaining=limits["header_bytes"] - summary["header_bytes"],
            )
            if (
                request_limits["payload_remaining"] < block["metadata_bytes"]
                or request_limits["header_remaining"] <= 0
            ):
                raise BudgetStopped("Aggregate byte budget exhausted")
            record = dict(
                event="intent",
                index=block["index"],
                block=block,
                status="intent",
                plan_sha256=summary["plan_sha256"],
                source_bindings_sha256=hashlib.sha256(canonical(plan["source_bindings"])).hexdigest(),
                source_hashes_checked_before=True,
                header_bytes=0,
                request_send_completed=False,
                payload_offset=summary["payload_bytes"],
            )
            append(journal, canonical(record) + b"\n")
            summary["attempted_requests"] += 1
            summary["remaining_requests"] -= 1
            payload = bytearray()
            processing_started = clock()
            record["request_wall_seconds"] = 0.0
            record["transport_started"] = False
            error = None
            try:
                guard(next_request=True)
                request_started = clock()
                record["transport_started"] = True
                try:
                    transport(spec, request_limits, record, payload)
                finally:
                    record["request_wall_seconds"] = clock() - request_started
                if record["request_wall_seconds"] > limits["request_wall_seconds"]:
                    raise BudgetStopped("Request wall cap exceeded")
                guard()
                size = validate_headers(
                    spec,
                    record["http_status"],
                    record["response_headers"],
                    request_limits["payload_remaining"],
                )
                if len(payload) != size:
                    raise ValueError("Truncated or oversized exact metadata response")
                if type(record["header_bytes"]) is not int or not 0 <= record["header_bytes"] <= min(
                    limits["header_bytes_per_request"], request_limits["header_remaining"]
                ):
                    raise ValueError("Header accounting exceeds exact request/aggregate cap")
                parsed = parse_batch(bytes(payload), plan["schema_fields"], block)
                record["status"] = "received"
            except (Exception, KeyboardInterrupt) as exc:
                error = exc
                record.update(status="failed", error_type=type(exc).__name__, error=str(exc))
            finally:
                record["event"] = "outcome"
                record["payload_bytes"] = len(payload)
                record["payload_sha256"] = hashlib.sha256(payload).hexdigest()
                record["body_payload_bytes_read"] = 0
                summary["payload_bytes"] += len(payload)
                summary["header_bytes"] += record["header_bytes"]
                summary["response_bytes"] = summary["payload_bytes"] + summary["header_bytes"]
                try:
                    append(packed, bytes(payload))
                except (Exception, KeyboardInterrupt) as exc:
                    error = exc
                    record.update(
                        status="failed",
                        error_type=type(exc).__name__,
                        error=str(exc),
                        payload_persistence_failed=True,
                    )
                try:
                    guard()
                    record["source_hashes_checked_after"] = True
                except (Exception, KeyboardInterrupt) as exc:
                    error = exc
                    record.update(status="failed", error_type=type(exc).__name__, error=str(exc))
                record["processing_wall_seconds"] = (
                    clock() - processing_started - record["request_wall_seconds"]
                )
                append(journal, canonical(record) + b"\n")
            if error is not None:
                raise error
            records.append(parsed)
            summary["received_requests"] += 1
            guard()
        guard()
        summary["status"] = "completed"
    except (Exception, KeyboardInterrupt) as exc:
        summary.update(
            status="budget_stopped"
            if isinstance(exc, BudgetStopped)
            else "cancelled"
            if isinstance(exc, (Cancelled, KeyboardInterrupt))
            else "failed",
            error_type=type(exc).__name__,
            error=str(exc),
        )
    finally:
        try:
            inventory = assemble_inventory(records, plan["requests"], plan["object"].get("declared_rows"))
        except Exception as exc:
            summary.update(status="failed", error_type=type(exc).__name__, error=str(exc))
            inventory = dict(
                complete=False,
                inspected_batches=len(records),
                missing_batches=len(plan["requests"]) - len(records),
                batch_records=records,
                full_scan_body_buffer_bytes=None,
                validation_error=str(exc),
                body_payload_bytes_read=0,
            )
        inventory["eligible_for_scan_planning"] = summary["status"] == "completed"
        if not inventory["eligible_for_scan_planning"]:
            inventory["full_scan_body_buffer_bytes"] = None
        summary["elapsed_seconds"] = clock() - started
        atomic_json(directory / "inventory.json", inventory)
        summary["files"] = {
            p.name: dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            for p in (journal, packed, directory / "inventory.json")
        }
        atomic_json(directory / "summary.json", summary)
        try:
            guard()
        except (Exception, KeyboardInterrupt) as exc:
            if summary["status"] == "completed":
                summary.update(
                    status="budget_stopped"
                    if isinstance(exc, BudgetStopped)
                    else "cancelled"
                    if isinstance(exc, (Cancelled, KeyboardInterrupt))
                    else "failed",
                    error_type=type(exc).__name__,
                    error=str(exc),
                    elapsed_seconds=clock() - started,
                )
                inventory.update(eligible_for_scan_planning=False, full_scan_body_buffer_bytes=None)
                atomic_json(directory / "inventory.json", inventory)
                p = directory / "inventory.json"
                summary["files"][p.name] = dict(
                    bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()
                )
                atomic_json(directory / "summary.json", summary)
    return summary


def fetch_one(spec, limits, record, payload):
    """One exact range GET, no retries/redirects/address fallback; called only after freeze."""
    if spec["url"] != URL or spec["generation"] != GENERATION or spec["etag"] != ETAG:
        raise ValueError("Request destination/version differs")
    target = urlsplit(URL)
    connection = None
    with deadline(limits["request_active_seconds"]):
        try:
            connection = http.client.HTTPSConnection(
                target.hostname, timeout=limits["request_active_seconds"]
            )
            connection._create_connection = ipv4_once

            class UnbufferedSocket:
                def __init__(self, sock):
                    self.sock = sock

                def makefile(self, *_args, **_kwargs):
                    return self.sock.makefile("rb", buffering=0)

            class BoundedResponse(http.client.HTTPResponse):
                def __init__(self, sock, *args, **kwargs):
                    super().__init__(UnbufferedSocket(sock), *args, **kwargs)
                    self.fp = HeaderReader(
                        self.fp, record, min(limits["header_bytes_per_request"], limits["header_remaining"])
                    )

            connection.response_class = BoundedResponse
            request_headers = {
                "Range": f"bytes={spec['offset']}-{spec['offset'] + spec['metadata_bytes'] - 1}",
                "If-Match": ETAG,
                "x-goog-if-generation-match": GENERATION,
                "Accept-Encoding": "identity",
                "Connection": "close",
                "User-Agent": "BET36FLY-partners-metadata/2.0",
            }
            record["sent_headers"] = request_headers
            connection.request("GET", target.path + "?generation=" + GENERATION, headers=request_headers)
            record["request_send_completed"] = True
            response = connection.getresponse()
            record.update(http_status=response.status, response_headers=response.getheaders())
            expected = validate_headers(
                spec, response.status, record["response_headers"], limits["payload_remaining"]
            )
            while len(payload) < expected:
                part = response.read1(expected - len(payload))
                if not part:
                    raise ValueError("Truncated exact metadata payload")
                payload.extend(part)
            # Do not probe an extra byte: the next object interval is unread body data.
        finally:
            if connection is not None:
                connection.close()


class HeaderReader:
    def __init__(self, stream, record, cap):
        self.stream, self.record, self.cap = stream, record, cap

    def readline(self, limit=-1):
        left = self.cap - self.record["header_bytes"]
        if left <= 0:
            raise ValueError("HTTP header budget exhausted")
        data = bytearray()
        maximum = min(left, 4096, limit if limit >= 0 else 4096)
        try:
            while len(data) < maximum:
                byte = self.stream.read(1)
                if not byte:
                    break
                self.record["header_bytes"] += len(byte)
                data.extend(byte)
                if byte == b"\n":
                    break
            if not data.endswith(b"\r\n"):
                raise ValueError("Incomplete/oversized/non-CRLF HTTP header")
            return bytes(data)
        finally:
            if not data.endswith(b"\r\n"):
                self.record["partial_header_line_hex"] = data.hex()

    def read1(self, size=-1):
        return self.stream.read(size)

    def __getattr__(self, name):
        return getattr(self.stream, name)


class DeadlineExceeded(RuntimeError):
    """Not OSError: it must escape socket address handling without retry."""


@contextmanager
def deadline(seconds):
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
        raise ValueError("Do not overwrite an existing alarm")
    previous = signal.getsignal(signal.SIGALRM)

    def expired(_signum, _frame):
        raise DeadlineExceeded("Absolute request I/O/close deadline")

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def ipv4_once(address, timeout, source_address=None):
    if source_address is not None:
        raise ValueError("No alternate source address")
    family, kind, proto, _, endpoint = socket.getaddrinfo(
        address[0], address[1], socket.AF_INET, socket.SOCK_STREAM
    )[0]
    sock = socket.socket(family, kind, proto)
    sock.settimeout(timeout)
    try:
        sock.connect(endpoint)
    except BaseException:
        sock.close()
        raise
    return sock


def execute(plan_path, expected_sha):
    started = time.monotonic()
    path = Path(plan_path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 5 * 1024 * 1024:
        raise ValueError("Invalid bounded plan file")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha:
        raise ValueError("Plan file hash mismatch")
    plan = validate_plan(strict_json(data))

    def verify_sources():
        if path.is_symlink() or path.read_bytes() != data:
            raise ValueError("Frozen plan changed")
        for meta in plan["source_bindings"]:
            if binding(meta["path"]) != meta:
                raise ValueError("Bound source/footer/document changed")

    verify_sources()
    # Include approval verification and initial source reads in the fixed wall budget.
    return _run_requests(
        plan,
        transport=fetch_one,
        clock=time.monotonic,
        started=started,
        verify_sources=verify_sources,
        plan_bytes=data,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--plan", required=True)
    prepare.add_argument("--output-directory", required=True)
    run = commands.add_parser("execute")
    run.add_argument("--plan", required=True)
    run.add_argument("--plan-sha256", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        write_exclusive(args.plan, canonical(build_plan(args.output_directory)) + b"\n")
        print("Proposed plan written; no networking. Root review/freeze/dispatch required.")
    else:
        result = execute(args.plan, args.plan_sha256)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["status"] == "completed" else 1)
