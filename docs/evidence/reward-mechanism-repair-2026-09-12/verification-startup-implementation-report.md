# Task 4A — Safe verification startup

Date: 2026-09-12

## Outcome

Task 4A is implemented and verified for its stated stable-file scope. Importing `bet36fly.server` no longer constructs a `Runtime`. The normal application constructs its runtime lazily at lifespan or first request and retains its existing warm-start behavior. The explicit `create_verification_app` factory constructs a read-only runtime with warm startup disabled.

The scientific decision remains **HOLD**. This work does not qualify the rate bridge, authorize conditioning, alter an experiment identity, or run a sports experiment.

## Verification behavior

- Verification mode exposes only stored metadata and stored evidence through GET/HEAD/OPTIONS requests.
- Verification responses carry `X-BET36FLY-Verification: read-only`.
- All other HTTP methods return 405 before route handling or request-body processing.
- Model construction, native execution, prediction, source following, pick refresh, ledger mutation, and shadow-ledger mutation fail closed in verification mode.
- Missing read-only databases are treated as empty without creating files.
- SQLite inputs must be regular, non-symlink, stable rollback-journal databases. WAL mode and journal/WAL/SHM sidecars are rejected before SQLite is opened.
- Malformed current-model pointers, training reports, and brain manifests produce an explicit 503 evidence-unavailable response instead of a model fallback or fabricated absence.
- The web UI labels verification mode, displays stored evidence, and disables refresh and prediction controls.
- The browser verifier requires the exact verification marker in both the response header and status payload before creating output directories or launching Chromium.
- `make serve-verify` documents the explicit factory entrypoint.

The SQLite guard proves behavior for a stable file inventory. It cannot guarantee a no-write view if an external process changes journal mode or sidecars concurrently after the guard checks. The actual QA run therefore still requires before, after, and post-shutdown file inventories and hashes.

## Regression coverage

The added and widened tests cover:

- fresh-process import and lifespan behavior;
- repeated lifespans and simultaneous first requests, including exactly one runtime construction;
- absence of neural-model and source-follower startup in verification mode;
- stored status, training, diagnostics, artifacts, frontend, picks, and shadow reads;
- the complete mutating-method/path/origin rejection matrix;
- missing databases without SQLite connection or path creation;
- valid rollback-journal databases with URI-significant path characters;
- corrupt headers, wrong schemas, symlinks, valid WAL headers, and real valid databases accompanied by journal/WAL/SHM sidecars;
- every direct read-only mutation guard;
- malformed JSON and wrong-shaped pointer/report/manifest metadata;
- normal-mode startup, follower, and status compatibility;
- UI verification notice and disabled controls;
- browser preflight refusal before filesystem or browser side effects.

## Final gate

`make verify` passed:

- pytest: 911 passed, 2 dependency deprecation warnings;
- Ruff: all checks passed;
- Vitest: 68 passed across 7 files;
- Vite production build: passed.

The complete log is `output/collaboration/reward-mechanism-repair/task4a-verify.txt`.

## Files in Task 4A

- `AGENTS.md`
- `Makefile`
- `bet36fly/server.py`
- `bet36fly/runtime.py`
- `bet36fly/ledger.py`
- `bet36fly/shadow.py`
- `docs/api-contract.md`
- `scripts/verify_reward_browser.cjs`
- `scripts/verification_server_guard.cjs`
- `tests/test_api.py`
- `tests/test_verification_server.py`
- `tests/test_browser_verification_guard.py`
- `web/src/App.tsx`
- `web/src/App.test.tsx`
- `web/src/style.css`
- `web/src/types.ts`
- `output/collaboration/reward-mechanism-repair/conditioning-reading.md`
- `output/collaboration/reward-mechanism-repair/task4a-verify.txt`
- `.superpowers/sdd/2026-09-12-reward-mechanism-repair/task-4a-report.md`

Other modified or untracked evidence files shown by Git belong to concurrent root/source work and are outside this ownership report.

## Pending operator proof

No server or browser was started during this implementation. Root will run the explicit verification factory on port 8766, leaving the pre-existing warm-disabled process on port 8765 untouched, and will use `output/collaboration/reward-mechanism-repair/verify_qa_files.py` to capture before, after, and post-shutdown file inventories and hashes. Production edits are frozen until that proof completes.
