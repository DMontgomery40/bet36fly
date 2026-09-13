# Metadata inventory v2: header compatibility repair

V2 is a separate output-only client, test suite, proposed plan and destination.
The [v1 result](partners-metadata-v1-result-2026-09-13.md) and every frozen v1
byte remain preserved. No v2 object request has run at this preparation boundary.

The [personally read source contract](partners-metadata-v2-source-contract-2026-09-13.md)
grounds the correction in the official GCS field definition and RFC 9110.
V2 accepts repeated or comma-separated MD5/CRC32C object hash entries, retains
their order, and rejects invalid encodings or contradictory algorithm values.
These object hashes do not validate a 640-byte metadata range. It preserves
all ancillary header fields, including repetitions, as opaque ordered data.
This fixes the general duplicate-field family without interpreting unused
fields as authority. Field names/values require valid HTTP syntax; interpreted
range, length, ETag, generation and framing/encoding fields remain strict.

The exact object identity, all 4,759 ordered ranges, total 3,045,760 metadata
payload bytes, 8,388,608 aggregate header bytes, concurrency one, 14-second
active request deadline, 15-second transport cap, 16-second start reserve and
1,200-second whole-study cap are identical to v1. There are no retries,
redirects, fallback addresses, coalesced requests, body-buffer reads or
decompression. The complete-row consistency check and partial/failure
dispositions are unchanged.

The proposed plan is `partners-metadata-v2-plan-2026-09-13.json`; its new
destination is `partners-metadata-v2-inventory-2026-09-13`. Fifteen source
bindings include the v2 client and tests, the source contract and the exact
recorded v1 header array. The v1 scientific input/source identities are
preserved. Root must freeze this proposed plan by changing only its status
and then explicitly dispatch the new identity.

Writer validation has 282 copied baseline tests plus 123 header-family tests.
An additional 94 independently written header cases pass. The real recorded
header array reproduces v1's failure and passes v2; a reconstructed HTTPResponse
reads exactly the saved 640-byte metadata fixture and stops before an unread
body sentinel. Tests also cover mixed case/order/list grouping, redundant and
conflicting checksums, singleton duplicates, ancillary repetitions, malformed
field syntax, and preservation of all v1 bindings. The 499-case combined run
and Ruff checks pass. Final independent footer/parser/transport review of v2
is recorded separately before any dispatch.

After root freezes and approves the exact v2 plan:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python output/collaboration/reward-mechanism-repair/partners_metadata_inventory_v2.py execute --plan <root-frozen-v2-plan-path> --plan-sha256 <root-frozen-v2-plan-sha256>
```

This header repair has no production or frontend impact. It neither changes
the accepted learning mechanism nor qualifies conditioning or reversal.
