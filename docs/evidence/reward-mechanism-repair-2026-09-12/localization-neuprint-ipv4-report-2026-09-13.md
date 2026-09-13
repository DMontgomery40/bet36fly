# Bounded neuPrint IPv4 transport result — September 13, 2026 UTC

One unauthenticated GET reached the selected IPv4 endpoint, completed verified
TLS and sent its request, but produced no complete HTTP status line before the
deadline. The conditional dataset-list request was skipped. Dataset identity,
public-access configuration, authentication requirements and selected-cell
synapse locations remain undetermined. This result does not establish that
neuPrint is globally unavailable or explain the earlier transport failures.

## Frozen scope and execution identity

The approved [plan](localization-neuprint-ipv4-plan-2026-09-13.json) was frozen
at 2026-09-13T05:43:10.548074+00:00, before networking, with SHA256
`efe9a69ba50cf8e26050e2ef07965bb173a612378176e771a976d4dc36a32914`.
It permitted at most two exact GETs, 65,536 response bytes including HTTP
headers, 15 wall seconds per request and 30 total request wall seconds.
Each request had a 14-second active deadline to reserve time for closing the
connection. Redirects, retries, address fallback and further requests were
forbidden. Request two required a complete HTTP 200 response containing valid
JSON from request one, with all identity and execution checks passing.

The contemporaneously bound client was
[`localization_neuprint_ipv4_probe.py`](localization_neuprint_ipv4_probe.py),
SHA256 `5ff0de604faa7d6e146d48b78ae8ef873263eb66629c08a9379b5a4f573d0ab0`.
Its seven bound source/input files were rehashed before and after the attempt
and remained unchanged. The earlier proposal and access failures remain
unchanged historical records.

The client selected one AF_INET address, used ordinary certificate-verified
HTTPS and recorded DNS, TCP, TLS, request-send and response-header stages.
It used no credentials, cookies, browser state, environment proxies, account
changes, custom queries or synapse/body data requests. Its deadline exception
does not inherit from `OSError`, avoiding the earlier probe's possibility of
catching a deadline inside socket address fallback. That client improvement
does not prove that IPv6 caused any previous neuPrint failure.

Before the freeze, 50 offline tests passed in 0.17 seconds and Ruff passed.
The tests cover status/auth/redirect stops, malformed or duplicate-key JSON,
exact JSON field names/types, size/framing/truncation families, conditional
second requests, identity reuse and a failed first IPv4 address without
fallback. They use fake connections and make no network requests. They
establish software contracts, not server access or biology.

## Actual request and measured stages

The sole requested primary endpoint was
[`https://neuprint.janelia.org/api/serverinfo`](https://neuprint.janelia.org/api/serverinfo).
It began at **2026-09-13T05:43:29.446806+00:00** and selected
**206.241.0.110:443** from one resolved IPv4 result. One connection was attempted.
The separate planned
[`/api/dbmeta/datasets`](https://neuprint.janelia.org/api/dbmeta/datasets)
endpoint was not requested.

| Stage | Seconds since attempt start |
| --- | ---: |
| DNS start / end | 0.010388000 / 0.027359208 |
| TCP start / end | 0.027386500 / 0.073336917 |
| TLS start / end | 0.073340875 / 0.164595583 |
| Request sent | 0.164655542 |
| Complete HTTP status line | Not observed |
| Complete HTTP headers | Not observed |
| Active I/O ended | 14.005004458 |
| Request elapsed, including connection close | 14.005163167 |

The recorded failure is `DeadlineExceeded: Absolute active deadline`.
The 15-second request wall cap and 30-second total wall cap were met. The
14-second active timer showed approximately five milliseconds of scheduling
overhead; it is not reported as an exact 14.000000-second return.

The client recorded **zero consumed HTTP header bytes and zero payload bytes**,
and saved no payload. These counters are application-level observations, not
TCP/TLS wire-byte measurements. The deadline interrupted a buffered status-line
read; this record cannot exclude an incomplete fragment inside that buffer.
No complete HTTP status, headers or JSON object was available. Accordingly
there is no observed `publicaccess`, `IsPublic` or other access field whose
case, value or type could be reported. Absence of a response is not a false
value and does not identify an authentication failure.

The preserved [attempt](localization-neuprint-ipv4-2026-09-13/attempt-01.json),
[result](localization-neuprint-ipv4-2026-09-13/result-01.json) and
[summary](localization-neuprint-ipv4-2026-09-13/summary.json) establish one
request, zero complete JSON responses and no second attempt. The unused
request slot is closed by the failed prerequisite; it does not authorize a
later retry. No further network request was made for this result.

## Source and scientific limits

This is a transport observation from one endpoint at one time. It advances
the earlier inconclusive access evidence by locating this attempt after
successful DNS/TCP/TLS, while waiting for an HTTP response. It does not supply
a neuPrint server version, a live MaleCNS dataset identity, a documented
unauthenticated query path or selected-body coordinates.

The separate [official-file metadata result](localization-batch-metadata-report-2026-09-13.md)
remains the demonstrated data route: generation-pinned ranges provide complete
footers and the two inspected first-batch metadata messages. Actual body-ID
values and coordinates remain unread. Without an independently verified body
index or ordering contract, complete body selection cannot discard any batch
merely because an inspected example lacks a selected body. The previously
identified all-batch metadata and unread body-buffer requirements remain
unchanged; this transport failure supplies no shortcut or global transfer
estimate.

The minimum evidence for a local PPL101/KC/MBON11 analysis remains a complete,
version-bound selected-cell synapse export, with its coverage and aggregate
pairs reconciled to the locked graph. This experiment neither acquires that
export nor authorizes bulk downloads, repeated transport checks or account
access. Anatomical location would still require a separate source-backed
local-release/plasticity hypothesis; no exposure coefficient, distance cutoff,
hemisphere assignment or change to the rejected adaptation rule follows here.

There were zero circuit calls and zero production edits. Root owns the
repository verification and evidence-copy/commit gate; the offline client
tests above are the changed-surface verification for this output-only study.
