# GCS hash-list compatibility contract

Personally checked September 13, 2026 UTC, before v2 implementation and any
v2 object request. The frozen v1 client, tests, plan and first failed execution
remain unchanged. The observed response returned two `x-goog-hash` field lines,
one CRC32C and one MD5; v1 incorrectly rejected every repeated field name.

The official [Cloud Storage XML API header reference](https://docs.cloud.google.com/storage/docs/xml-api/reference-headers#xgooghash)
documents base64 MD5 and CRC32C object checksums. It explicitly permits both
separate same-name field lines and their comma-separated equivalent. These are
object metadata; they do not verify an isolated 640-byte range payload.

[RFC 9110 §§5.1–5.6.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-5.3)
defines case-insensitive field names, ordered list-field combination, singleton
versus list values, optional space/tab and bounded handling of empty list
members. Repeated lines are permissible when the field definition supports
such a list. This does not make every singleton safely combinable.

The scoped v2 policy preserves the entire raw ordered response-header array.
For `x-goog-hash` only, it parses repeated/comma-separated MD5 and CRC32C
members, preserving their order. Whitespace and bounded empty members are
handled within the existing header-byte cap. Supplied values must decode to
their checksum width; contradictory repeated values for one algorithm fail.
Identical redundant values are harmless. Missing hash headers remain allowed;
the checksum is informational and is never compared with the range SHA.

Content-Range, Content-Length, ETag and x-goog-generation retain exact singleton
cardinality and frozen values. Unsupported transfer/content encoding remains
a pre-payload failure. All field names and values must have valid HTTP syntax.
Other fields are preserved as ordered opaque entries, including repetitions;
the client does not merge or interpret them as authority. Request intervals,
object generation, payload/header/request/time caps,
no-retry policy, parser, source checks and durable outcomes stay unchanged.
V2 has separate code, tests, plan and output identity and requires a new dispatch.
