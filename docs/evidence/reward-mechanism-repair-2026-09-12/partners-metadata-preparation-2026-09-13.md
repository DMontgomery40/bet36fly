# Complete partners metadata inventory: reviewed preparation

September 13, 2026 UTC. This output-only preparation has made **zero network
requests and zero native/circuit calls**. The exact JSON plan remains proposed;
root must freeze it and explicitly dispatch its execution after independent
review. The destination output directory has not been created.

The objective is to read the metadata messages for all 4,759 record batches
and determine the declared compressed storage cost of the `body_pre` and
`body_post` columns. This does not retrieve a body value, synapse coordinate,
dictionary, or compressed frame. It does not establish a synapse-local dopamine
exposure map, a new mechanism, or conditioning qualification. Production API
and Training behavior remain unchanged and accurate.

## Exact source and request plan

The saved complete partners Footer is bound through its preserved 262,144-byte
suffix (SHA256 `7779ff2b04999bae9447db9dbae2570448bdb2c8bdbc9b11da3906f0e9789701`)
and inspected JSON. The client independently reparses the actual Footer block
structs and compares all of them with the export. It checks the Arrow trailer,
footer SHA, full block/body/dictionary separation, fixed eleven-field schema,
and all 4,759 ordered record-batch entries. The independent reviewer derives
the same ranges directly from the raw Footer without using the writer helper.

The sole object is the official v1.0
`syn-partners-male-cns-v1.0-minconf-0.5.feather`, with object length
6,777,179,098 bytes, GCS generation `1780494942562468`, and exact HTTP ETag
`"58efcf712f8c4d4de5f2ad51e97def76"`. Every planned interval is exactly 640
bytes. The first is 3960–4599; the last is 6776807552–6776808191. The
dictionary and every adjacent compressed record-batch body are outside all
requests. The earlier first-batch reference is requested again within the
4,759-attempt plan, so this identity has a complete ordered metadata collection.
There is no coalescing across unread body data.

The complete plan lives in `partners-metadata-plan-2026-09-13.json`. It binds
the client, writer tests, three preserved client/parser sources, inspected
footer/export, generation receipt, official Arrow File/Schema/Message format
sources, and saved first metadata message. The validator reconstructs the
entire approved plan; editing its ranges, host, source hashes, output path,
budget, retries, or concurrency cannot turn it into another valid plan.

## Fixed budget and transport behavior

| Resource | Maximum |
| --- | ---: |
| Ordered request intents / possible GET attempts | 4,759 |
| Simultaneous requests | 1 |
| Metadata payload bytes | 3,045,760 |
| HTTP status/header bytes per request | 8,192 |
| Aggregate HTTP status/header bytes | 8,388,608 |
| Aggregate application response bytes | 11,434,368 |
| Active DNS/TCP/TLS/HTTP/close alarm per request | 14 seconds |
| Measured transport wall time per request | 15 seconds |
| Minimum remaining whole-study reserve at request start | 16 seconds |
| Whole-study wall cap, including initial verification and output | 1,200 seconds |
| Retries, redirects, alternate-address attempts, resumes | 0 |

These response bytes are application bytes, not a claim about TLS/TCP/IP
wire traffic. Fresh verified-TLS connections use only the first resolved
IPv4 address; no alternate address or protocol is tried after a failure.
The URL query and request headers pin the generation; `If-Match` pins the
ETag. The client requires status 206, exact Content-Range and Content-Length,
matching generation and ETag, and no transfer/content encoding. All headers
are validated before an application payload read. Header counting includes
the status line, CRLF terminators, and returned partial bytes on a timeout.
An unbuffered response stream prevents application-layer body prefetch while
reading headers. The body reader requests exactly the remaining metadata
bytes; it never probes a 641st byte.

The whole-study clock starts before initial plan/source validation. Before
each transport, after durable intent persistence and source verification,
the client rechecks both cancellation and the 16-second remaining reserve.
The `request_wall_seconds` field measures only transport, including close.
The separate `processing_wall_seconds` covers source checks, parsing and
payload persistence around that request; all of these consume the whole-study
cap. The client checks again after final output persistence. The cap is an
execution stop with preserved overrun/failure evidence, not a hard real-time
guarantee for operating-system file writes or a promise of complete retrieval.
Sequential latency or the aggregate header budget may leave the result partial.

## Metadata interpretation and durable outcomes

The strict parser accepts only the inspected Arrow message version, no custom
message metadata, the exact record-batch body extent, matching field nodes and
buffers, and inspected compression forms. It checks all fixed-width values
and validity buffer declarations. A required compressed buffer must contain
more than its eight-byte length prefix; zero rows and null-free omitted
validity buffers retain their separate valid cases. This validates metadata
consistency only: unread compressed frames, body IDs and row contents remain
unverified.

Each intent is fsynced before transport and includes the plan/source identity.
An intent does not prove that an HTTP request was sent: the outcome separately
records `transport_started` and `request_send_completed`. Once an intent is
durable it consumes a slot even if a later guard prevents transport. An abrupt
interruption can leave an unresolved intent, which remains an incomplete
attempt rather than permission to replace it.

The exclusive run directory will contain a frozen `plan.json`, ordered
`requests.jsonl` intents/outcomes, packed `metadata.bin`, `inventory.json`,
and `summary.json`. Each outcome retains measured header/payload bytes,
metadata SHA, source-check state, status, error and timing. Payload accounting
advances even if its disk persistence fails. The first failure stops the
sequence and leaves the prefix and failure disposition available. Disk errors
can limit what can be saved; they do not establish successful receipt.

The inventory retains every parsed batch's row count, codec, two body-column
null counts and absolute validity/value buffer ranges. A complete collection
must sum to the frozen pandas RangeIndex declaration of 311,833,243 rows;
this is an internal metadata check, not decoded-row validation. A row-total
mismatch produces a durable failed summary and preserves the parsed records.
Missing, reordered, duplicated or failed collections cannot provide a complete
scan cost. `eligible_for_scan_planning` requires successful full completion,
and `full_scan_body_buffer_bytes` remains null otherwise. No uniform batch-size
or first-batch compression extrapolation is used.

## Offline validation and execution handoff

The frozen writer release passed 565 offline cases: 282 writer cases and 283
independently authored cases (48 Footer, 168 parser, 67 transport). The tests
include real saved Footer identities; independently constructed PyArrow files;
all-codec and all-field buffer-size matrices; header, generation and framing
failures; full request-plan mutations; partial reads and closes; source drift;
durable failure outcomes; cancellation and cap transitions during verification,
intent, transport, parsing and persistence; and complete versus partial cost
reporting. The independent transport suite prohibits socket/DNS access.
The preserved test output is `partners-metadata-offline-tests-2026-09-13.txt`.
The client and writer tests also pass Ruff. No production tests, native tests,
browser, server or new neural studies were run for this output-only change.

After independent review, root can copy the exact proposed plan to a new
frozen plan file with only `status` changed to `frozen`, bind its resulting
SHA256 in the approval receipt, and dispatch:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python output/collaboration/reward-mechanism-repair/partners_metadata_inventory.py execute --plan <root-frozen-plan-path> --plan-sha256 <root-frozen-plan-sha256>
```

The frozen plan validator rejects any other difference. The dedicated planned
destination is
`output/collaboration/reward-mechanism-repair/partners-metadata-inventory-2026-09-13`.
It must not already exist. Root owns the explicit network dispatch and later
decision about whether any separately bounded body-column retrieval is useful.
