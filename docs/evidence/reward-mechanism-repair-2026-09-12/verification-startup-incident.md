# Browser verification startup incident

On September 12, 2026, the first browser verification attempt started the normal
`bet36fly.server:app` server. Its startup follower refreshed public sports data
and created 81 local v1 paper forecasts between 04:54:40 and 04:54:54 UTC. This
was unintended work during mechanism verification. The server was stopped and
the incident was disclosed to David during the task.

The retained [incident receipt](task1-startup-side-effects.json)
records the affected cache files, forecast IDs and creation timestamps. The
active model pointer remained byte-identical with SHA-256
`975badb63a16ca1b24291a741b6818f1d83776b51adb18b18c6f0902b3a18b21`.
The historical reward and v2 manifests also retained their recorded hashes.
Those checks do not establish that the live sports state was untouched.

There was no complete pre-start cache or ledger snapshot. The new rows and
refreshed files were preserved; deleting shared rows or reconstructing an
assumed previous cache would not constitute a verified rollback. The repair
experiments continue to use their frozen historical inputs, never these
refreshed sports files.

The corrective implementation introduces an explicit read-only verification
factory, lazy runtime initialization, read-only ledger access and a browser
preflight that refuses a normal server. Its acceptance requires both tests of
the no-write contract and file/inventory comparisons around actual browser
startup, requests and shutdown. The subsequent results are recorded separately
in the [acceptance report](verification-startup-acceptance.md).
