# MaleCNS range access works; body-selective retrieval remains unproved

Checked September 13, 2026, 05:09–05:13 UTC. The two official v1.0 synapse
objects returned genuine HTTP 206 suffix responses. Both complete Arrow
footers were retrieved and parsed locally. **This establishes bounded file
access and exact batch locations, but not a cheap body lookup or defensible
local dopamine exposure weights.** No synapse rows or dictionary values were
decoded, and no circuit, graph, production source or checkpoint was changed.

The [frozen request plan](localization-range-plan-2026-09-13.json) preceded all
network access. The [complete machine summary](localization-range-probe-2026-09-13/summary.json)
and six attempt/result pairs preserve the actual limits and outcomes.

## Exact access and budget

There were **six HTTP requests**, **807,635 payload bytes**, **6,018 header
bytes**, and **58.843649 seconds** of accumulated request duration. The total
813,653 response bytes is below 1 MiB, and total duration is below 90 seconds.
There were no redirects, automatic HTTP retries, credentials, account actions,
neuPrint requests, installations or bulk fallback.

**One per-request timing cap was exceeded:** the first request took
15.202552 seconds against a 15-second limit. Preserve that exception; this
was not a strictly within-budget first request. The original signal handler
raised `TimeoutError`, which is an `OSError` subclass that socket address
fallback can catch. Consequently attributing the overrun only to teardown
would be unsupported. Requests 2–4 used a 14-second active timer and finished
below 15 seconds; requests 5–6 used a non-OSError deadline exception and one
DNS-resolved IPv4 address, with no address fallback. They finished in 0.533
and 0.309 seconds. No additional request followed the sixth.

The script was revised during the probe. Its three executed versions are
preserved under the result directory, with request-to-version mapping in the
summary. Earlier versions were reconstructed from the exact recorded edits;
per-request records originally hashed the plan, not the executed source.
These reconstructed hashes are not contemporaneous source-hash evidence.

| Request | Primary resource | Status | Payload bytes | Seconds |
| --- | --- | ---: | ---: | ---: |
| 1 | Official syn-points suffix | 206 | 262,144 | 15.202552 |
| 2 | Official syn-partners suffix | 206 | 262,144 | 14.287058 |
| 3 | Apache Arrow `File.fbs` | 200 | 1,512 | 14.275400 |
| 4 | Apache Arrow `Schema.fbs` | 200 | 21,803 | 14.237373 |
| 5 | Google Cloud object-download reference | 200 | 194,496 | 0.532627 |
| 6 | Apache Arrow Feather documentation prefix | 200 | 65,536 | 0.308640 |

Both file requests required 206, a valid suffix Content-Range and a matching
bounded Content-Length before payload reads. The offline protocol suite now
passes **11 tests**, with network and timers replaced: full-body/redirect/error
responses, malformed and oversized ranges, length disagreement, truncation,
partial evidence, exact bounded reads, deadline/address fallback and identity
reuse. Ruff passes. Exact interior-range and version-pinning validation remain
required before a subsequent retrieval; the suffix validator is not a generic
interior-range client.

## Observed object identity and complete footer coverage

The exact official destinations, already documented by the MaleCNS release,
are [syn-points](https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/syn-points-male-cns-v1.0-minconf-0.5.feather)
and [syn-partners](https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/syn-partners-male-cns-v1.0-minconf-0.5.feather).
The actual response sizes total **19,838,668,196 bytes**; the older website's
rounded display sizes are not the exact object lengths.

| Metadata | Syn-points | Syn-partners |
| --- | ---: | ---: |
| Object bytes | 13,061,489,098 | 6,777,179,098 |
| Generation | 1780494991007477 | 1780494942562468 |
| ETag | `c69d08758de07582035cc8843574493a` | `58efcf712f8c4d4de5f2ad51e97def76` |
| Last modified UTC | June 3, 2026 13:56:31 | June 3, 2026 13:55:42 |
| Complete footer bytes | 140,760 | 116,632 |
| Record batches | 5,455 | 4,759 |
| Dictionary blocks | 18 | 1 |
| Schema fields | 41 | 11 |
| Total batch metadata bytes | 11,346,400 | 3,045,760 |

Both trailers contain `ARROW1`. A local suffix-only reader permits access
only to bytes actually retrieved; it rejects any requested hole. Installed
PyArrow successfully reads the schema and batch count from those bytes.
A separate small Flatbuffer parser, following the inspected official schema,
checks every one of the **10,214 record-batch blocks**, all 19 dictionary
blocks, their metadata/body extents and non-overlapping placement before the
footer. The full block inventories and reader byte requests are retained in
`footer-inspection-01.json` and `footer-inspection-02.json`.

The points schema includes int64 `body`, int32 xyz, `kind`, confidence, region
fields and uint64 `point_id`. The partners schema includes both body IDs,
both xyz triples, both confidences and categorical `primary_post`. Region and
kind dictionary values were not read. The footers carry no file-level custom
metadata and no field-level custom metadata. The only schema metadata key is
`pandas`; its recorded creator is PyArrow 19.0.1. The points dataframe index is
`point_id`; the partners metadata declares a RangeIndex of 311,833,243 rows.
Neither is a body-selection index. The declared row count has not been checked
against decoded batches.

## Primary format documentation and its limits

The current official [Arrow File schema](https://raw.githubusercontent.com/apache/arrow/main/format/File.fbs)
and [Arrow Schema definitions](https://raw.githubusercontent.com/apache/arrow/main/format/Schema.fbs)
were read in full. Their mutable `main` versions are bound by the response
ETags and saved payload SHA256s. The footer's batch block specifies offset,
metadata length and body length. It does not supply body-ID min/max statistics.
The inspected custom metadata contains no body sort or partition contract.
This does not rule out useful information elsewhere in an unread batch or a
separate index; it means none was established by this bounded inspection.

The complete [Google Cloud object-download reference](https://docs.cloud.google.com/storage/docs/xml-api/get-object-download)
was read. It documents byte ranges, ETag and generation preconditions, and
circumstances where a range may be ignored. It also distinguishes whole-object
checksums from validation of a downloaded range. The preserved suffix hashes
identify our received bytes; they do not verify the full object against its
published checksum. Later multipart work must pin generation/ETag and validate
every returned range, not merely trust an `Accept-Ranges` header.

The [Feather documentation](https://arrow.apache.org/docs/python/feather.html)
response advertised 174,385 bytes, but its frozen 65,536-byte cap stopped in
navigation content. Its page title identified Apache Arrow v25.0.1. No claim
about complete Feather methods or body filtering is derived from that partial
page. No extra request was made to complete it.

## Smallest next data step and the unresolved scan cost

A separately authorized metadata-only probe can request the first record-batch
metadata of each version-pinned object:

| Object | Exact next Range | Expected bytes |
| --- | --- | ---: |
| Points | `bytes=61496-63575` | 2,080 |
| Partners | `bytes=3960-4599` | 640 |

Use the observed generation and ETag as explicit preconditions, require exact
206/Content-Range/length agreement and fail before any payload if they differ.
New offline tests must cover these interior ranges and version mismatch first.
The two ranges total 2,720 bytes. They can establish the message layout,
compression and body-column buffers for those batches. They cannot prove the
other batches' layout, a global sort order or a complete selected-body result.
These requests have **not** been made.

Without an independently verified index or ordering contract, a complete
body-predicate scan cannot exclude any of the 5,455 points batches or 4,759
partners batches. All relevant body columns would need inspection, potentially
via projected compressed-buffer reads rather than full-batch downloads.
The complete batch metadata totals 14,392,160 bytes. Individually reading it
would involve 10,214 disjoint indexed metadata regions; coalescing could reduce
request count by retrieving intervening data. This is a layout fact, not an
approved download plan.

For scale only, the partners' declared RangeIndex implies 2,494,665,944
uncompressed bytes for one int64 body column, or 4,989,331,888 bytes for both.
Those figures exclude validity, compression and framing, and are **not** an
estimate of compressed network transfer. Selecting the union of outgoing
PPL101 partners and incoming MBON11 partners would require both body predicates
unless another verified selection mechanism were supplied. The compressed
body-column byte totals, actual batch row counts and a smaller proven selection
cost remain unknown. A small first-batch sample cannot establish them globally.

## Anatomical and biological boundary

The intended bodies remain PPL101 11327/11900 and MBON11 10704/11402, with the
existing selected KC map. Eventual selected-coordinate retrieval could locate
DAN synapses and KC→MBON11 sites and reconcile them with the locked retained
graph and region conventions. It would still need complete selected-body
coverage, dictionary decoding and confidence/coordinate checks. Proximity or
shared region membership would be anatomical evidence, not a calibrated
spike-to-dopamine release or receptor-exposure law.

No soma-only hemispheric assignment, coupling coefficient, distance cutoff,
contact deletion or home eligibility change follows from these footers.
The rejected rate-adaptation equation remains rejected. No local exposure was
computed, and conditioning/reversal remain separate gated work.
