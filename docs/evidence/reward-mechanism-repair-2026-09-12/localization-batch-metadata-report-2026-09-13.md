# First-batch metadata: exact body-buffer locations, no body selection yet

September 13, 2026, 05:27 UTC. The two separately authorized, version-pinned
metadata ranges succeeded. **Each first batch contains 65,536 rows and
declares LZ4 frame compression at buffer level.** Their exact body-ID buffer
locations and lengths are now known. Those buffers were not requested or
decoded; this result supplies neither selected-body rows nor a global scan
cost or sorting guarantee.

## Separate frozen request identity

The [new plan](localization-batch-metadata-plan-2026-09-13.json) was frozen
before requests, SHA256
`e05a9ecfcddc8f8ddd022b0992f5cfcbdcf21e5ad85723c0e2ac465169e3edf5`.
The new client passed **55 offline protocol tests** and Ruff beforehand.
The previous range report, client versions and evidence remain unchanged.
The earlier first-request timing overrun remains recorded there; it is not
erased by this new probe.

Exactly **three HTTP requests** consumed **9,300 payload bytes** and **2,590
header bytes**, totaling **11,890 response bytes** in **0.720422 seconds**.
All three per-request 15-second limits, the 45-second total and 65,536-byte
combined-response cap passed. There were no retries, redirects, credentials,
body-column payloads, dictionaries, row samples or further network requests.
The [complete result](localization-batch-metadata-2026-09-13/summary.json)
retains those values and the unread buffer inventory.

| Request | Range or resource | Status | Payload bytes | Seconds |
| --- | --- | ---: | ---: | ---: |
| Syn-points first-batch metadata | `61496–63575` | 206 | 2,080 | 0.161893 |
| Syn-partners first-batch metadata | `3960–4599` | 206 | 640 | 0.170251 |
| Official Apache Arrow `Message.fbs` | Complete schema source | 200 | 6,580 | 0.388279 |

Both object requests used the previously observed generation as a query
parameter and `x-goog-if-generation-match`, together with `If-Match` for the
exact ETag. Exact 206 status, interior Content-Range, Content-Length, ETag,
generation and HTTP identity encoding were checked before payload reads.
All source dependencies were rehashed before and after every request.
Each persisted attempt includes the then-current executing source SHA256:
`b4bde33bc78a738b4bd84a38be4123075000d177d0505eb471c5fe43f1465227`.
This new identity has contemporaneous source hashes, unlike the earlier
probe's reconstructed per-request source versions.

## What the metadata actually supplies

The pinned objects are the official
[syn-points](https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/syn-points-male-cns-v1.0-minconf-0.5.feather)
generation `1780494991007477`, ETag
`c69d08758de07582035cc8843574493a`, and
[syn-partners](https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/syn-partners-male-cns-v1.0-minconf-0.5.feather)
generation `1780494942562468`, ETag
`58efcf712f8c4d4de5f2ad51e97def76`.

The IPC metadata includes its eight-byte continuation/length prefix.
The points message has 2,072 bytes after that prefix; the partners message
has 632. Both identify RecordBatch messages whose body lengths exactly match
the earlier footer: 1,919,392 bytes for points and 1,310,264 for partners.
The points batch has 41 field nodes and 82 buffer entries; partners has 11
nodes and 22 buffers. Every field-node row count and every buffer extent/order
was checked. Both messages have empty custom metadata.

The following absolute ranges are **unread locations**, not downloaded data:

| Object / field | Values-buffer range | Stored buffer bytes | Null count | Validity bytes |
| --- | --- | ---: | ---: | ---: |
| Points `body` | `1044248–1320355` | 276,108 | 0 | 0 |
| Partners `body_pre` | `140376–228888` | 88,513 | 0 | 0 |
| Partners `body_post` | `795168–1080604` | 285,437 | 0 | 0 |

Together, these three first-batch value buffers occupy 650,058 stored bytes;
the two partners buffers occupy 373,950. These exact lengths establish the
size of those particular buffer reads only. They are not global compression
ratios, complete body-predicate results or evidence of sorted body IDs.

The inspected primary [Arrow Message schema](https://raw.githubusercontent.com/apache/arrow/main/format/Message.fbs)
defines buffer-level compression: each nonempty buffer carries an eight-byte
uncompressed-length prefix, followed by its encoded data. A prefix of −1
can mark an uncompressed buffer. Metadata declaring `LZ4_FRAME/BUFFER` is
therefore not by itself a successful decode. A future authorized buffer
reader would need to validate that prefix, the frame and the expected decoded
length; one first-batch int64 body column represents 524,288 uncompressed
value bytes. No such prefix or frame was read here.

`Message.fbs` was read in full, with its mutable-main version preserved by
payload SHA256 `ec4274d76bfeb959b4a1961fa7ddb07dd06aa4a4a4960832c9fecec61f3bce53`
and response ETag in the request record. The prior complete File/Schema
specifications remain bound inputs. No additional source lookup was made.

## What this does not establish about complete retrieval

The common fixed-width schema identifies the body columns' buffer slots.
Actual offsets, lengths, row counts and compression metadata for the other
5,454 points batches and 4,758 partners batches have not been inspected.
Their compression costs must not be extrapolated from these first batches.
The difference between first-batch pre/post buffer sizes also does not prove
body ordering.

The earlier complete footer inventory still gives 10,214 batch-metadata
regions totaling 14,392,160 bytes. Without a verified body index or ordering
contract, a complete predicate scan cannot discard the unread batches merely
because a desired body is absent from a sample. Such a scan would need the
relevant body columns across all batches, then coordinate/region data for
the matched rows, or a separately verified server-side selection mechanism.
Exact compressed bytes for that global operation remain unknown.

No body-buffer scan or full-object download is proposed as an automatic next
action. The previously documented body-filtered neuPrint route remains a
potential alternative whose live access must be established separately.
This report authorizes no more requests.

## Independent local verification and biological scope

The metadata parser passed **42 additional synthetic tests** using independently
written and read PyArrow IPC fixtures: empty/single/multiple-row batches,
non-null/fully-null/mixed fields, int64/float/dictionary storage, uncompressed,
LZ4 and Zstandard messages, malformed lengths, footer mismatch, schema mismatch
and dictionary-message rejection. These tests ran after retrieval and validate
the parser, not the requested biological data. The installed PyArrow version
was 21.0.0. Ruff passed for both client and parser surfaces.

No PPL101, KC or MBON11 location was decoded. Eventual geometry could provide
an anatomical locality check, subject to full selected-body accounting and
coordinate/region conventions. It would not on its own calibrate dopamine
release, diffusion or receptor exposure. No coupling coefficient, distance
cutoff, soma-side assignment, eligibility change or alternative learning rule
follows from these metadata. Conditioning remains separately gated.
