# Read-only browser verification acceptance

September 12, 2026 UTC. The explicit verification factory passed the full
repository gate and actual browser checks. This closes the unsafe QA startup
defect; it does not qualify the dopamine rule or demonstrate conditioning.

The [implementation report](verification-startup-implementation-report.md) and
[full verification log](verification-startup-verify.txt) record 911 Python tests,
68 frontend tests, Ruff and the rebuilt frontend passing. Tests cover fresh
process imports, runtime lifetime/concurrent initialization, missing and invalid
metadata, SQLite sidecars/WAL/symlinks/schema, blocked mutation methods and direct
APIs, and preserved normal serving behavior.

Root started `bet36fly.server:create_verification_app --factory` with bytecode
writes disabled and an automatically assigned free localhost port (50116).
The marked server passed the [historical reward browser workflow](verification-startup-browser.json):
eight downloaded artifacts matched their hashes; seven explicitly labeled
fixture states passed; tested widths from 320 through 1024 pixels had no page
overflow; no browser errors were recorded. Root inspected the captured reward
panel. The historical three-arm sports result remains historical.

A separate [visible controls check](verification-startup-controls.json) observed
the read-only notice and disabled refresh on the Observatory and Fly's desk.
All 129 Observatory neural controls and four desk neural controls were disabled.
No mutation requests or JavaScript errors occurred in that check.

The [before snapshot](verification-startup-file-baseline.json) hashes 749 files
totaling 4,350,759,224 bytes across data, ledgers and possible sidecars, model
files, historical experiments, native libraries, source/bytecode, built frontend
and the imported wiki snapshot. Both the [after-request comparison](verification-startup-files-after-requests.json)
and [after-shutdown comparison](verification-startup-files-after-shutdown.json)
found zero byte changes, added entries or removed entries. The verification
server shut down with exit code zero. Earlier servers were left alone.

The SQLite guard assumes stable files during its header/sidecar check and open;
these results do not prove safety against a separate process changing journal
mode concurrently. Source scripts, receipt hashes and server identity are
retained in the [copy manifest](verification-startup-copy-manifest.json).

The [earlier startup incident](verification-startup-incident.md), including its
81 added paper forecasts, remains disclosed and preserved. Successful later QA
does not undo those earlier side effects.
