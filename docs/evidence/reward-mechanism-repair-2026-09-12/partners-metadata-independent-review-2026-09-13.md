# Independent partners metadata review

September 13, 2026 UTC. Reviewer: `/root/delivered_arrivals`. **PASS for the
bounded proposed metadata client and complete request list.** No unresolved
actionable finding remains at the release hashes below. This review is not an
execution instruction or a claim that all batch metadata have been retrieved.
The parent owns plan freeze and any separately authorized dispatch.

The work was offline and output-only: zero network requests, zero neuronal or
native circuit calls, and no production, connectome, gain or earlier evidence
edits. PyArrow generated and decoded synthetic fixtures; it did not decode
actual body values or dictionaries. Preserved prior suffix bytes were read.

## Complete saved-footer result

An independent parser transcribed the official `File.fbs` Block layout using
Python `struct`, without importing the writer's parser or the earlier Footer
helper. It parsed every dictionary and record-batch Block from the complete
saved raw Footer, checked bounds and ordering, and compared all exported records.
The result is 4,759 ordered record-batch metadata intervals, each 640 bytes,
totaling **3,045,760 requested metadata bytes**. Every interval excludes every
record-batch and dictionary body and precedes the Footer. This is complete
interval validation, not a first-batch extrapolation.

The object is the official MaleCNS v1.0 min-confidence-0.5 partners Feather,
6,777,179,098 bytes, generation `1780494942562468`, ETag
`"58efcf712f8c4d4de5f2ad51e97def76"`. The preserved 262,144-byte suffix has SHA256
`7779ff2b04999bae9447db9dbae2570448bdb2c8bdbc9b11da3906f0e9789701`.
Its 116,632-byte Footer starts at 6,777,062,456 and has SHA256
`9d790d9e9e5ffa32574f1f2a2a79594a000200496b996ab031e345977846a5a5`.

The first requested inclusive range is 3,960–4,599 and its unread body starts
at 4,600. The last requested range is 6,776,807,552–6,776,808,191 and its unread
body starts at 6,776,808,192. The sole dictionary block starts at 2,392 and
contains 192 metadata bytes plus 1,376 body bytes; no proposed request includes
that block. All 4,759 intervals are retained in
`partners-metadata-independent-all-ranges.json`.

A separate PyArrow 21.0.0 reader against a Footer-only file object independently
confirmed 4,759 batches, the exact eleven-field schema, and the declared
311,833,243-row pandas RangeIndex. Its only reads were the ten-byte file trailer
and the 116,632-byte Footer. The row declaration is an independent reconciliation
target for the later complete metadata inventory, not a body-data observation.

## Reviewed release and fixed execution boundary

| File | SHA256 |
| --- | --- |
| `partners_metadata_inventory.py` | `1f4394d5bc4621125709eb8c3a972ba0f25cc242424d0ed683c71d93657931ed` |
| `test_partners_metadata_inventory.py` | `7923d3cb120f3f2d509a4966bcd334dd1ae1ba8c7944fece6f92fa0549f3415b` |
| `partners-metadata-plan-2026-09-13.json` | `26309100ef7c6efd3bed12ce25409e353d369b50640d9f9703cad9e2587a7fea` |

Every proposed plan interval was compared with the independent raw-Footer
oracle, and every one of its twelve bound source files was rehashed. Changing
only a temporary in-memory copy's status to `frozen` passed the actual canonical
plan validator. The on-disk plan remains `proposed`; its dedicated output run
directory did not exist at review. No executor was called with actual transport.

The plan allows at most 4,759 requests at concurrency one, 3,045,760 metadata
payload bytes, 8,388,608 application header bytes, and 11,434,368 combined
application response bytes. Each request has an 8,192-byte header ceiling, a
14-second active I/O/close deadline and 15-second transport wall ceiling. The
1,200-second study clock includes initial validation and subsequent processing.
A sixteen-second reserve is checked immediately before starting transport.
No retry, redirect, address fallback, coalescing, resume or replacement request
is provided. Transport uses a fresh verified-TLS connection and one IPv4 address.
The first earlier metadata interval is explicitly requested again under this
new plan; the previous artifact remains preserved.

HTTP status, exact Content-Range/Length, generation, ETag and framing are checked
before payload reads. No 641st-byte probe follows a 640-byte metadata interval.
Status/header bytes are counted at primitive reads, including partial lines that
end in timeout, deadline or cancellation; this accounts for application bytes,
not TLS/TCP wire traffic. Durable intent and outcome records identify each
attempt, while `transport_started` and `request_send_completed` preserve the
distinction between a reserved attempt and known transport/send progress.

On first failure, already returned metadata bytes and receipts are retained;
incomplete or invalid inventories do not publish a full-scan body cost.
Final complete row reconciliation must match 311,833,243. Completion is
reclassified if final persistence crosses the deadline/cancellation/source
boundary. A storage failure can still prevent a file from being written; the
tests verify explicit failure and retained measured counts, not impossible
guarantees against unavailable storage or abrupt process loss.

## Independent tests and corrected families

The frozen release passed **283 independently authored tests in 4.31 seconds**:
48 Footer tests, 168 record-batch parser tests and 67 transport/runner tests.
Ruff passed on the four independent Python files. The preserved final log is
`partners-metadata-independent-final-tests-2026-09-13.txt`. The writer's separate
release log records 565 combined passing cases: its 282 plus these 283.

Coverage includes independent PyArrow files with empty and multiple batches,
nullable primitive and ordered dictionary fields, uncompressed/LZ4/ZSTD storage;
Footer offsets, vector/table bounds, ordering, duplicate and overlapping blocks;
all eleven fields' compressed validity/value boundary families; exact and
fragmented HTTP payload reads, interim status headers, inclusive header budgets;
failure at every position in a three-request synthetic sequence; partial payload
preservation, source drift, cancellation, total caps, preparation time, immediate
reserve checks and durable final row/error reconciliation.

Review found and the writer corrected these concrete families before freeze:

- A compressed buffer containing only its eight-byte length prefix was accepted
  despite positive required values. The independent matrix exposed 44 such
  false accepts across both codecs and all fields; valid empty controls remain.
- Source hashing could cross a stop boundary, or consume the reserved close
  time after an earlier check, and still allow a GET. Boundary tests now cover
  1,184-second equality, 1,185/1,199-second insufficient reserve, 1,200 seconds,
  and cancellation after verification or intent persistence.
- A partial header line lost consumed application-byte counts when `readline`
  raised. Primitive-read accounting now preserves counts across timeout,
  absolute deadline and keyboard interruption.
- The checked request wall time was overwritten after parsing, permitting a
  received record to report a value over its own cap. Transport and processing
  clocks are now distinct and both remain under the study clock.
- Root's independently identified preparation-clock reset and unguarded final
  assembly were also rechecked: preparation remains in elapsed time and invalid
  all-batch row totals retain complete received bytes plus a failure summary.

The complete requested metadata count is known; complete body-column scan cost
is still unknown until those messages are successfully retrieved and validated.
No timing prediction, complete-request success guarantee, coordinate result,
local dopamine exposure, chemical transfer law, learning improvement or
conditioning qualification follows from this review.
