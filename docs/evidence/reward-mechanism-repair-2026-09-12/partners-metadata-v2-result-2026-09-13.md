# Complete partners metadata inventory

September 13, 2026 UTC. The single frozen v2 execution completed all **4,759
record-batch metadata requests**, with no failures, retries or additional
object requests. It retrieved exactly 3,045,760 metadata payload bytes in
815.861276 seconds, within the 1,200-second cap. **No body IDs, compressed
body buffers, coordinates or dictionaries were retrieved or decoded.**

The complete declared cost of the two body-ID columns is now known:

| Column | Value-buffer bytes | Validity-buffer bytes | Declared nulls |
| --- | ---: | ---: | ---: |
| `body_pre` | 363,074,510 | 0 | 0 |
| `body_post` | 1,650,277,453 | 0 | 0 |
| Total | **2,013,351,963** | **0** | **0** |

This is about 2.01 GB of currently unread buffer data before future HTTP
overhead. It includes the declared compressed buffer lengths, including their
compression prefixes; gaps and alignment padding outside those buffers are
excluded. It does not include coordinates, confidence columns, dictionaries
or a selected-row export. Every batch declares LZ4_FRAME compression, and
all 9,518 body-column value-buffer ranges are retained in the inventory.
No first-batch compression extrapolation is used.

All metadata messages together declare 311,833,243 rows, exactly matching the
frozen Footer's pandas RangeIndex. This is internal metadata consistency,
not validation of decoded row contents, body-ID sorting, a body-selection
index, anatomical completeness or a local dopamine exposure law. A later
body predicate scan would require its own finite plan and authorization;
none was performed or dispatched by this result.

## Execution and retained evidence

The object is the official MaleCNS v1.0 min-confidence-0.5 partners Feather,
6,777,179,098 bytes, generation `1780494942562468`, ETag
`"58efcf712f8c4d4de5f2ad51e97def76"`. The frozen v2 plan SHA256 is
`3d77faa491248c15913e8a9b5b96f29e9420c63597d3d12a34d0f56e587913c4`;
client SHA256 is `ce018ac60c768289769d272d8daacc7ce59b5226ce93804f92de1ce15aa6f255`.
Root explicitly dispatched this identity after the source contract and
independent review passed. The sole process, exec session `61220`, exited 0.

| Recorded resource | Used | Cap |
| --- | ---: | ---: |
| Requests, all successful | 4,759 | 4,759 |
| Metadata payload bytes | 3,045,760 | 3,045,760 |
| HTTP status/header bytes | 4,027,890 | 8,388,608 |
| Application response bytes | 7,073,650 | 11,434,368 |
| Maximum transport time, including close | 0.606863 s | 15 s |
| Whole-study recorded elapsed time | 815.861276 s | 1,200 s |

Concurrency was one. The active per-request alarm remained 14 seconds.
Transport time averaged 0.163808 seconds; the largest recorded surrounding
processing interval was 0.009726 seconds. Header counts include status lines
and line terminators, but are not TLS/TCP wire-byte counts. No body/native/
circuit call occurred. Metadata ranges exclude every adjacent record body;
the reader never probes beyond the exact requested payload.

The five files in `partners-metadata-v2-inventory-2026-09-13` total 16,791,998
bytes: frozen `plan.json`, `requests.jsonl`, `metadata.bin`, `inventory.json`
and `summary.json`. The packed metadata SHA256 is
`987eea35d6c6c5784c2b6538130ea9df8d4b65fbef238e04eed28e36476ca93f`.
The inventory is complete, with zero missing batches and a populated full
body-column cost. All source bindings remain at their frozen values.

The writer's [saved-result audit](partners-metadata-v2-execution-integrity-2026-09-13.json)
checks every one of 9,518 journal rows, every payload slice/hash, all 4,759
range/version/framing records, fifteen source bindings, per-request and total
accounting, complete row/cost aggregates, and file identity before/after the
audit. Re-parsing uses the already reviewed frozen parser; this is a writer
integrity recomputation, not an independent body decoder. The first message
also matches the previously saved metadata reference exactly. No network
access occurs in this audit.

Before execution, 782 distinct offline cases passed: 405 writer tests and
377 independent tests. The overlapping 499-case combined log is not another
499 unique tests. These include independent Footer/Arrow fixtures, transport
and deadline families, actual recorded-header reconstruction, and broad
singleton/list/opaque-field regressions. Root separately ran the repository
gate and copied-location tests before local checkpoint `62aa5dd`.

The [v1 failure](partners-metadata-v1-result-2026-09-13.md) remains preserved:
its client rejected documented repeated hash fields after one GET and 842
header bytes, before reading a payload. It was not retried or edited. Across
the two separately frozen object studies there were 4,760 GETs, 3,045,760
payload bytes and 4,028,732 header bytes. V2 corrected the field-handling
family under its separate identity; it does not erase that earlier test gap.

The production API, Training view, scientific rule, channels, masks, gain
parameters and qualification thresholds are unchanged. Complete metadata
retrieval establishes storage cost. It does not qualify conditioning, reverse
the failed second-panel learning result, select anatomical exposure weights,
or demonstrate learning.
