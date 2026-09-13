# Metadata inventory v1: client rejected valid repeated hash fields

September 13, 2026 UTC. The frozen metadata-only inventory stopped on its
first response. The server returned HTTP 206 with the exact requested range,
length, generation and ETag. Our client incorrectly rejected its separate
CRC32C and MD5 `x-goog-hash` fields as duplicate headers. This was a client
compatibility bug, not a failed source, an unavailable object or an anatomical
result.

The [original plan](partners-metadata-frozen-plan-2026-09-13.json) allowed
4,759 exact metadata requests. Its execution made one request, consumed
842 application HTTP header bytes and zero payload bytes, and skipped all
4,758 later requests. Recorded transport time was 0.181904 seconds and
study elapsed time 0.206358 seconds. Zero batches were parsed; the full
body-column transfer cost remains unknown. No synapse body data or coordinates
were read. The frozen client was not changed or retried.

The [raw response and durable journal](partners-metadata-inventory-2026-09-13/requests.jsonl),
[summary](partners-metadata-inventory-2026-09-13/summary.json),
[source/result integrity receipt](partners-metadata-execution-integrity-2026-09-13.json)
and [copy manifest](partners-metadata-v1-copy-manifest-2026-09-13.json)
preserve the attempt. All 12 frozen source bindings and the five result files
matched their recorded hashes.

The preparation had passed 565 synthetic tests, including 283 independent
cases. Those tests covered metadata structure, ranges, budgets and failure
persistence but omitted this valid provider response. The
[independent review receipt](partners-metadata-independent-final-receipt-2026-09-13.json)
records that gap separately from its earlier passing review. A green synthetic
suite did not establish HTTP compatibility.

The provider explicitly permits separate or comma-separated MD5/CRC32C hash
fields. These are whole-object checksums and cannot validate an individual
640-byte metadata range. [Google Cloud Storage XML API headers](https://docs.cloud.google.com/storage/docs/xml-api/reference-headers#xgooghash),
checked September 13, 2026. HTTP field handling depends on each field's
semantics; cardinality alone is insufficient. [RFC 9110, sections 5.2–5.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-5.2),
June 2022, checked September 13, 2026.

A separate v2 preparation corrects the family: exact singleton checks for
interpreted framing/range/version fields, documented hash-list handling,
and preservation of unused ancillary fields without inventing their semantics.
It must pass the recorded-response regression and broader field-category
tests before a new frozen execution. The v1 failure remains part of the record.
