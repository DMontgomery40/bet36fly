# MaleCNS selected-synapse localization access check

Checked September 13, 2026, 04:20–04:23 UTC. **Public/unauthenticated access is unresolved from this host. No synapse coordinates were retrieved.** None of the three endpoint attempts received an HTTP status. The failures therefore establish neither an authentication requirement nor global service unavailability.

## Actual access results

All requests were read-only GETs to the official `neuprint.janelia.org` service. No authorization header, cookies, account login, redirect following or application credential was used. No token/profile endpoint, credential store, installation, custom query or circuit was accessed.

| Attempt | Endpoint | Limit | Observed result |
|---|---|---|---|
| 1, default sandbox | `/api/dbmeta/datasets` | 15 s; 64 KiB | DNS `gaierror`, `[Errno 8] nodename nor servname provided, or not known`; 0.013 s; no HTTP response. |
| 2, single network-enabled attempt after sandbox DNS failure | `/api/dbmeta/datasets` | 15 s; 64 KiB | `TimeoutError: The read operation timed out`; 15.290 s; no HTTP status or body returned to the client. |
| 3, network-enabled curl with user config disabled | `/api/serverinfo` | 5 s connect, 12 s total; 4 KiB | curl exit 28, operation timed out; 12.021 s; zero response bytes, no HTTP status. |

The exact records are [default dataset attempt](localization-access-datasets.json), [network-enabled dataset attempt](localization-access-datasets-network.json), and [public-status attempt](localization-access-serverinfo.json). Their timestamps, limits, elapsed time and error text are preserved. There were three service attempts, two fresh official documentation/source pages, no automatic retry loop and no further service probes. The second dataset attempt was an explicit one-time retry across the sandbox boundary. Reading cached sections of the already-open source page did not add another endpoint attempt.

The earlier web-tool failure to open a dbmeta URL remains distinct from these direct transport results. Neither kind of failure is an HTTP 401/403. No dataset inventory, `IsPublic` flag, MaleCNS version metadata, confidence/ROI metadata or selected-body response was obtained.

## Documentation and feasible route

The freshly read [official neuprint-python Client documentation, version 0.6.3](https://connectome-neuprint.github.io/neuprint-python/docs/client.html) documents dataset discovery, a server-public-status check and custom Cypher queries. Its [tagged client implementation](https://github.com/connectome-neuprint/neuprint-python/blob/0.6.3/neuprint/client.py) maps these to `/api/dbmeta/datasets`, `/api/serverinfo`, and `/api/custom/custom`. The custom-query request includes both the dataset name and Cypher text. The client documents explicit token or `NEUPRINT_APPLICATION_CREDENTIALS` configuration; this audit supplied neither. That interface supports authenticated access but does not prove that authentication was the cause of the observed transport failures.

The previously completed, fully read [source investigation](dopamine-signal-sources-resumed.md) records the official MaleCNS `male-cns:v1.0` dataset choice and body-filtered synapse/query APIs. It also records confidence, postsynaptic ROI-filtering and overlapping-ROI caveats. Those documented query capabilities were not executed in this assignment. No claim of live schema or data delivery follows from them.

The next available step is to establish service reachability and dataset metadata through an already authorized connection. If the service then requires authentication, use an existing authorized neuPrint session/token privately; this report neither located nor created one. After metadata confirms the intended dataset, a separately bounded retrieval can inspect selected PPL101 bodies 11327/11900 and KC→MBON11 bodies 10704/11402. Freeze exact query text, dataset metadata, row/byte limits, confidence criteria and ROI conventions before geometry analysis. Retrieve a deliberately limited sample first and label it incomplete. Full selected-pair/site accounting must subsequently reconcile with the locked retained graph before deriving local exposure weights; soma/instance side and whole-body pair counts do not supply those weights.

The official bulk synapse files remain a documented alternative in the source investigation, but their combined 19.5 GB payload was not downloaded. Cheap body-selective remote Feather access was not established. No automatic bulk fallback or coupling coefficient was invented.

## Reading and verification

This agent had already read the complete original narrative corpus and all later additions recorded in `delivered-arrivals-resumed-reading-receipt.json` and `delivered-arrivals-resumed-evidence-review-final.md`. For this assignment it additionally read the complete current AGENTS and 04:13 handoff, Task4B acceptance and implementation report, current evidence index, evidence/UI reading receipt, and wiki verification. The source investigation was already read in full and remained hash-identical. The corrected current wiki verification paragraph was also read after root removed its obsolete pending-acceptance wording. Current narrative hashes and access-result hashes are recorded in `localization-access-receipt.json`.

Only output evidence files were created. All response records were parsed and checked for absent HTTP status, bounded request count and zero coordinate retrieval. No production code changed; no simulator, server, repository test suite or browser was run for this access-only task. The parallel rate-adaptation work and scientific qualification status are unchanged by these access failures.
