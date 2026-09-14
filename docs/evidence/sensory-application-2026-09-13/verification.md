# Application verification — September 13, 2026

The mounted product is the sensory research application. The frozen confirmation and its scientific claim are unchanged. No push, deployment, fit, confirmation rerun or model-pointer update occurred.

## Software

`make verify` completed with exit 0: **4,161 Python tests, 109 frontend tests, Ruff and the TypeScript/Vite production build passed**. Python emitted the two existing Starlette/httpx and AnyIO deprecation warnings. The application bundle contains no legacy endpoint strings or old view imports. Tests cover every confirmation row via pagination, the first matchup's exact artifact values, all download hashes, filters, empty/invalid queries, missing/corrupt/symlinked artifacts, stale cached bytes, semantic CSV corruption, and runtime isolation in normal/verification modes.

The first full run failed because old compatibility tests assumed eager runtime construction during startup. Those tests now explicitly initialize the compatibility runtime while retaining their mutation/origin/read-only assertions. New tests forbid any such construction during sensory requests in either server mode. No guard was weakened. A mobile overflow regression was fixed by containing the table's absolutely positioned accessibility label; the table remains scrollable and keyboard focusable. The team select now has an explicit accessible label.

Full log: `/tmp/bet36fly-ui-make-verify-final.log`. Focused logs: `/tmp/bet36fly-sensory-focused.log` and `/tmp/bet36fly-sensory-closeout-tests.log`. The standard build completed again before the final browser check.

## Rendered acceptance

Guarded server: `make serve-verify QA_PORT=8766`, URL `http://127.0.0.1:8766`. The previously occupied 8765 process was left alone. Browser plugin was unavailable; used the existing bundled Playwright Chromium. Preflight verified both the exact read-only response header and verification status before browser launch.

The flow under test was overview → full game explorer → team/date filters → matchup-specific qualities/requests/output measurements → methods/provenance/downloads, plus legacy URLs and unavailable-state recovery.

All 11 acceptance groups passed:

- Correct page identity, meaningful overview, confirmation numbers, all six comparisons and no framework overlay.
- Pagination and filters against actual backend records; filtered summaries distinguished from the full confirmation.
- Exact first-matchup quality, probability, recruited IDs, four outputs and six seed/opportunity records.
- Empty subsets, invalid date ranges and clear-filter recovery.
- Methods, provenance and all nine browser-initiated downloads, each byte-verified against its SHA-256.
- Old hashes and path bookmarks resolve to the current overview.
- No legacy endpoint requests, polling or mutating product requests.
- Keyboard skip navigation preserves the active page and focuses content.
- Overview, explorer, matchup and methods at widths 320, 390, 720 and 1024, plus desktop 1440×1050; no page overflow. The results table scrolls internally on narrow screens.
- Loading, unavailable and invalid-summary states with successful retry.
- Game-fetch failure, unknown matchup and recovery to real results.

There were **zero page errors and zero unexpected console warnings/errors**. The deliberately injected 503 and requested unknown-game 404 produced expected browser resource messages. Failure/loading fixtures are labeled synthetic test coverage; displayed successful evidence comes from the actual API.

Browser record and screenshots: `/tmp/bet36fly-sensory-browser/evidence.json` and adjacent PNGs. Desktop overview/matchup and mobile overview/matchup were visually inspected. No anatomical brain visualization is retained; charts represent only recorded output rates. Achieved per-cell input rates remain explicitly unavailable in this adapter. Browser engines other than Chromium were not tested.

## Preservation and concurrent work

All 43 pre-existing protected files matched their initial hashes: frozen sensory evidence/configs, the active model pointer and `PUBLIC_POST_HANDOFF.md`. [Preservation check](preservation.json). The new presentation lock is an authored file, not an edited scientific artifact. Unrelated associative-model files appeared from another writer during this task and were excluded from the local commit and completion claim.
