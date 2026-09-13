# Independent v2 header compatibility review

September 13, 2026 UTC. **PASS for the frozen v2 code and proposed plan.** No
remaining actionable issue was found in this bounded compatibility review.
The reviewer made no object requests or circuit calls. The parent owns any
new execution; the reviewed proposed destination did not exist at the check.

The original client and its first failed execution remain unchanged. My
earlier independent valid-response fixtures missed the provider's separate
CRC32C and MD5 header lines. The original passing boundary review therefore
did not establish provider compatibility. Its later failure is recorded in
`partners-metadata-independent-final-receipt-2026-09-13.json` and is not
relabelled as a source or anatomical failure.

I personally read the targeted official [GCS x-goog-hash section](https://docs.cloud.google.com/storage/docs/xml-api/reference-headers#xgooghash)
and [RFC 9110 section 5.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-5.3),
with the displayed adjacent field/list syntax, through three documentation-tool
invocations covering only these two primary URLs. GCS explicitly supports
separate or comma-separated MD5/CRC32C values. RFC field handling depends on
the field's semantics and preserves order when combining a list; singleton
fields are not thereby made lists. Reasonable empty list members are tolerated.
These checks did not contact the object endpoint.

V2 retains exact singleton checks for interpreted range, length, ETag,
generation and encoding/framing fields. It validates header names and values,
handles optional checksum lists, and preserves unused ancillary fields as
ordered opaque entries. It does not merge arbitrary fields or use a
whole-object checksum as validation of a 640-byte range. Every accepted range
still has the exact pinned version and response framing before a payload read.

The independent run passed **377 tests in 0.51 seconds**: all 283 preserved
Footer/parser/transport tests were run against the actual v2 module through
a temporary process import binding, plus 94 new header cases. No v1 test file
was edited. The new cases cover separate/combined/reordered/mixed-case hash
lists and whitespace/empty members; repeated unused Cache-Control, Alt-Svc,
custom fields and Set-Cookie; identical/conflicting case-folded critical
duplicates; invalid field syntax/types; and the actual saved ordered response
headers reconstructed through `HTTPResponse`. The latter uses the previously
saved 640-byte metadata message and an unread-body sentinel, not a new response
or decoded body. Ruff passed on both new independent Python files.

The actual saved-header reconstruction succeeds and stops at exactly 640
metadata bytes. All fixed stop, partial-byte, source-drift, publication,
deadline and no-next-region tests remain passing on v2.

I rehashed the declared v2 release and all fifteen proposed-plan bindings.
All 4,759 ordered ranges, object identity, schema fields and resource limits
are exactly equal to v1, so the independent complete raw-Footer validation
continues to apply to every requested range. The new output identity is
distinct. In-memory status-only canonical validation passes without changing
the on-disk proposed plan or executing it. AST comparison shows only the
header validator, plan bindings/identity and transport user-agent changed,
plus the new checksum-list helper. All other functions/classes are unchanged.
Every source/review/run artifact bound in the prior independent receipt was
also rehashed and remains identical.

| Release file | SHA256 |
| --- | --- |
| `partners_metadata_inventory_v2.py` | `ce018ac60c768289769d272d8daacc7ce59b5226ce93804f92de1ce15aa6f255` |
| `test_partners_metadata_inventory_v2.py` | `f463488135e238fe0f287893f6bf6aeebbd67d826408d9a5ad569f2fda697a74` |
| `test_partners_metadata_headers_v2.py` | `20eb536517e4ebb9f06f5a3f3455c15cf30909789daa4836c023f6f63ddeb686` |
| `partners-metadata-v2-plan-2026-09-13.json` | `5954ee60569068916023a4393eaa97e15934909b7d082b0265747c34afbba39b` |
| `partners-metadata-v2-source-contract-2026-09-13.md` | `84ae3be7689af573e48b6b2d6c52ab7d1eb7772dc048aefad1f05db67d8a4480` |

The test log is `partners-metadata-independent-v2-tests-2026-09-13.txt`.
This establishes the reviewed software behavior. It does not guarantee
completion within the fixed request/header/time budgets, establish full body
scan cost, retrieve selected cells, infer chemical exposure, or qualify learning.
