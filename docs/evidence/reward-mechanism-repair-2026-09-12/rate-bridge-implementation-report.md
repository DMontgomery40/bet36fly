# Task 2B implementation — released for independent review

Final release update: the recording-only audit follow-up below governs the current code and receipts. Root subsequently executed the first original bridge panel; it passed. This worker executed no full-CNS panel. Earlier output-absence statements below describe the initial release time only.

September 12, 2026 UTC. Base local commit `1c7060b`. No commit, server startup, sports execution or full MaleCNS run by this worker. Code ownership released to root; scientific qualification remains unmeasured for the bridge. The failed raw-event held-out result remains failed.

## Delivered behavior

- Independent `learning_rule=event|rate-bridge-v1`, event default and named raw/tonic behavior preserved. make_circuit propagates rule/rate settings and anatomy metadata. No v1 source or ABI changes.
- Shared native RateBridge helper remains inside the source-hashed reward_lif.cpp. Public electrical dt is still0.2ms; the private deterministic signal-only seam tests production integration at0.1/0.2/0.4ms against independent formulas, not changed electrical scheduling.
- Appended mode and double config preserve unrounded h/tau/eta for the bridge. Actual spikes inject symmetric population-normalized causal rates; exact interval net is computed from Q directly. True separate positive/negative integrals include their cancelling common term.
- Double within-trial bounded accumulator publishes float32 for transmission each interval. Sub-ULP remainder persists within a call and is discarded only after final float32 checkpoint publication. Tail uses post-final-advance state and analytically integrates no-new-event learning signals without extending electrical time.
- Separate optional double bridge_signals, bridge_kc_bins, bridge_kc_used, bridge_rule and bridge_tail carry explicit shapes/layout. Event-specific rule arrays are absent in bridge results. Attempted, double-applied, published-applied, bounds and Q stay distinct. Inclusive bounds observe both double proposals and float publication; tail observations are separate.
- Diagnostic uses the fourth analytic_no_new_event_tail phase in all applied/attempted totals, cumulative drift and bound criteria. Group totals report clipping and final rounding discrepancies; per-trial/checkpoint arrays and layout are retained. Bridge repeat checks compare every returned numerical array, not only gains. Event attribution rejects bridge input before loading/writing arrays.
- Fixed production protocol remains h.2/tau_e500/tau_r100/eta.0005/n.96/bounds.5..1.5, home all/awaygamma. Original selectors and previously frozen held-out selectors/seeds, seven thresholds, drive gains and encoder are unchanged. Identity binds rule/layout/tail/config, both governing documents, graph/data/code hashes.

## Explicit numerical domain

Near-equal reciprocal timescales with relative gap below1e-6 are rejected; no silent replacement or parameter tuning. Validation requires finite positive derived interval/tail/coupling coefficients, conservative rate/eligibility bounds, all scaled true-area/net intermediates and conservative grouped accumulation. Extreme finite-but-unsafe inputs are rejected before native entry. Bridge bounds must be exactly float32-representable; this avoids inherited float ABI rounding putting a checkpoint outside its declared interval. The event path retains its historical bounds behavior. Production100/500 and.5/1.5 are unaffected.

## Tests and evidence

Initial new-rule tests:95 failures before the API existed (`task2b-initial-red.txt`), then239 new/existing brain tests green. This is feature red/green, not95 separate pre-existing bugs. Diagnostic dispatch/accounting tests:4 failures before implementation (`task2b-diagnostic-red.txt`), then green.

Generalized coverage includes signed lags0/±.2/±1/±5/±20/±50/±100/±500/±1000, populations1/2/22 and partial22, arbitrary histories, coincidence/empty/one-sided, onset/shift/silent extension, independent dense clipped trajectories/true terms, exact float publication and bound/tail observations, frozen dwelling, masks/mixed compartments/permutation, checkpoint clone/remainder/reset, no eligible edges, actual transmission, record parity, malformed domains/dimensions/allocation/layout/decomposition/count/checkpoint evidence. Short-lag ratios and long-lag nonvanishing floors remain the frozen numerical falsifiers.

The decisive native K0,D.2,end400 fixture requires exactly float32(1−7.99040661e−7); its analytic tail alone is below half an ULP, so resetting to rounded gains each interval cannot pass via one tail write. An independent source audit reported the same case before this regression. Its reference script/results are read evidence, not rerun by this worker.

The complete CLI matrix was executed only on a six-neuron synthetic fixture under tmp_path:64 rows+16 cumulative, repeat arrays, source/identity freeze and tail retention/accounting. That checks orchestration, not full-CNS acquisition or diagnostic success. Stress-test eta2/2000 is confined to tiny arithmetic/transmission fixtures; no candidate protocol parameter changed.

Final focused command: `.venv/bin/python -m pytest -q tests/test_reward_rate_bridge.py tests/test_reward_brain.py tests/test_reward_diagnostic.py tests/test_reward_protocol.py tests/test_reward_encoder.py` —477 passed. Full `make verify` —804pytest,66Vitest,Ruff and build passed. No browser check because no frontend source changed; exposing the new stored rule/evidence and true read-only browser startup remain Task4. Two existing Python deprecation warnings remain.

## Preregistered only, not executed

- `bridge-original-preregistration.json`: `diag-rate-bridge-v1-maskgamma-1b233bc75647`; SHA256 `7eee2f2098f9cb64a6729fc27aa02ca718624b4ed0bbfc4b3ca4c80bf63f629d`. Output directory absent at release.
- `bridge-heldout-preregistration.json`: `diag-rate-bridge-v1-maskgamma-5e557f8ada07`; SHA256 `35e5490cc846ef2baedfe48134b8e23e1b0eda2d7dab9ba85a36168559e82e04`. Output directory absent at release.

Executed commands (only the freeze option):

```sh
.venv/bin/python scripts/reward_teaching_diagnostic.py --rule rate-bridge-v1 --away-mask gamma --panel-kind original --panel-offset 0 --seed-offset 0 --games 8 --cumulative-games 16 --preregistration docs/evidence/reward-mechanism-repair-2026-09-12/bridge-original-preregistration.json --preregister-only
.venv/bin/python scripts/reward_teaching_diagnostic.py --rule rate-bridge-v1 --away-mask gamma --panel-kind held-out --panel-offset 8 --seed-offset 2000000 --games 8 --cumulative-games 16 --preregistration docs/evidence/reward-mechanism-repair-2026-09-12/bridge-heldout-preregistration.json --preregister-only
```

Root controls any full-CNS invocation after independent review. Remove only --preregister-only and optionally add --evidence with the evidence directory when authorized; all selectors remain unchanged. The second panel is previously frozen evaluation data whose raw result is known, not newly unseen data. Governing bridge parameters predate that result.

## Source identities at release

- `bet36fly/reward_lif.cpp`: `e7dbb0aa8f95873036415581e94de45c237941f05642ccc90812c1be1119be37`
- `bet36fly/reward_brain.py`: `5a6d67d38d226c6792c4f11430610772894ea3e9ae9593c2d215cfd7eaa0a6d5`
- `bet36fly/reward_protocol.py`: `e1a315f991debb677fca30f6e821a657135adccf032ad26054a00ed7688dc1bb`
- `bet36fly/reward_diagnostic.py`: `59feb14834813fa6793f0f97a8e4c208fd85494b383e9fa5875efe5b21189c99`
- `scripts/reward_teaching_diagnostic.py`: `b69f972f5c1e72ae5244fc4504b6cd7c5ff3fe79383d77ce3dc93ec3f56dff94`
- `scripts/reward_residual_attribution.py`: `3dd92270cb9a33bf11413ccc19281122eee97d7c24726ac6d2494b1fb2e27344`
- `tests/test_reward_rate_bridge.py`: `f759030dc47f6a2824540c5365ce00dbfdcd9b2ccab2794731d9713f4bf947e1`
- `tests/test_reward_diagnostic.py`: `cfbc862bfe4b786db0de76dd43817791633d982822545e7378c525a19e288488`

Native test binary `reward-lif-e7dbb0aa8f958730.dylib`: SHA256 `089af7d08e4a0eaf47b1f35a26d82f8336a0397fc4431ed8629624b2c307d91a`. Every code hash in both freezes matched current files. `git diff --check` passed; base-to-worktree diff of v1 lif.cpp/brain.py, active pointer and wiki is empty. No claim of independent live cache/ledger byte parity is made without a task-start snapshot; no server or data-mutating function was invoked by this worker.

One forward integration question sent to root before panels: the accepted Task4 validator needs stored replay/noise evidence and trial hashes. Current bridge runner retains the same summary booleans as the old runner plus stronger live repeat comparison, but a future independent revalidation benefits from retained expected/actual fingerprints, all sensory-bin arrays and trial/layout artifact digests. Any approved follow-up requires new freezes before measurement; do not silently modify current identities.

## Full verification output

```
.venv/bin/python -m pytest -q
........................................................................ [  8%]
........................................................................ [ 17%]
........................................................................ [ 26%]
........................................................................ [ 35%]
........................................................................ [ 44%]
........................................................................ [ 53%]
........................................................................ [ 62%]
........................................................................ [ 71%]
........................................................................ [ 80%]
........................................................................ [ 89%]
........................................................................ [ 98%]
............                                                             [100%]
=============================== warnings summary ===============================
.venv/lib/python3.12/site-packages/fastapi/testclient.py:1
  /Users/davidmontgomery/Documents/ChatGPT/bet36fly/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

.venv/lib/python3.12/site-packages/starlette/testclient.py:53
  /Users/davidmontgomery/Documents/ChatGPT/bet36fly/.venv/lib/python3.12/site-packages/starlette/testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
804 passed, 2 warnings in 6.16s
.venv/bin/ruff check bet36fly tests scripts
All checks passed!
cd web && npm test

> bet36fly-web@0.1.0 test
> vitest run


 RUN  v4.1.11 /Users/davidmontgomery/Documents/ChatGPT/bet36fly/web


 Test Files  7 passed (7)
      Tests  66 passed (66)
   Start at  23:53:22
   Duration  663ms (transform 689ms, setup 0ms, import 1.09s, tests 491ms, environment 0ms)

cd web && npm run build

> bet36fly-web@0.1.0 build
> tsc -b && vite build

vite v6.4.3 building for production...
transforming...
✓ 204 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.56 kB │ gzip:   0.38 kB
dist/assets/index-BI0YTwPD.css   38.34 kB │ gzip:   8.53 kB
dist/assets/index-lwZ3xUdC.js   449.31 kB │ gzip: 137.83 kB
✓ built in 679ms
```

## Final recording-only audit follow-up — September 12, 2026 UTC

Root's first original `1b233bc75647` completed source-stable with all7passed before the missing audit-retention warning arrived. Its result and original receipt are preserved. The original unrun held-out `5e557f8ada07` receipt remains byte-identical and is superseded; do not execute it. No source file was changed until root confirmed the first run finished.

Authorized follow-up changes only `scripts/reward_teaching_diagnostic.py` and its tiny CLI test. The native kernel, wrapper, protocol and evaluator are unchanged from the first bridge. The runner now saves64 per-trial sensory-bin arrays, original/repeat fingerprints for every returned numerical array in replay-evidence.json, and byte count/SHA256 for trials.npz, recording-layout.json and replay-evidence.json in summary.artifacts. The test independently reads artifacts and verifies digests, fingerprint equality and sensory equality across all64 rows. New regression:1 failed before the retained fields existed, then green. No equation, parameter, random draw, scientific criterion or existing retained array computation changed.

Focused gate rerun:477passed. Full make verify rerun:804pytest,66Vitest,Ruff/build passed. Latest complete output replaces task2b-focused.txt/task2b-verify.txt. No browser, server, sports run or full-CNS run by this worker. Ownership released again after verification and fresh freezes.

New authoritative audit receipts, preregister-only:

- `bridge-original-preregistration-audit.json` → `diag-rate-bridge-v1-maskgamma-de050d773763`, SHA256 `61136a8326bc9332c2cd9bb6ff7241a22d253b07e12872a329e60817f0dbed7e`; output absent at freeze.
- `bridge-heldout-preregistration-audit.json` → `diag-rate-bridge-v1-maskgamma-dea14759e9ca`, SHA256 `9892d0cc9fc0527b0f6ea4f8a18a376d5161ffb833a05e1653288754b6260834`; output absent at freeze.

Exact future invocation is the original/held-out command above, changing only the receipt filename to its `-audit.json` version and removing `--preregister-only` when root authorizes execution after review. Both new freezes retain the same original/prior-held-out selectors and seeds. Root will compare all shared numerical arrays between the two original recording revisions; no parity claim is made before that measurement.

Current changed-file hashes after recording follow-up:

- `scripts/reward_teaching_diagnostic.py`: `d18df419fe4c78001019d6feadff5b6c37df2de69f7e278d46d3cf02bc539598`
- `tests/test_reward_diagnostic.py`: `0b9909b78ce50ab78fb3e639f70d031c5a3b9a8da62c1eb3a26dc155b3b98328`

Full final verification output:

```
.venv/bin/python -m pytest -q
........................................................................ [  8%]
........................................................................ [ 17%]
........................................................................ [ 26%]
........................................................................ [ 35%]
........................................................................ [ 44%]
........................................................................ [ 53%]
........................................................................ [ 62%]
........................................................................ [ 71%]
........................................................................ [ 80%]
........................................................................ [ 89%]
........................................................................ [ 98%]
............                                                             [100%]
=============================== warnings summary ===============================
.venv/lib/python3.12/site-packages/fastapi/testclient.py:1
  /Users/davidmontgomery/Documents/ChatGPT/bet36fly/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

.venv/lib/python3.12/site-packages/starlette/testclient.py:53
  /Users/davidmontgomery/Documents/ChatGPT/bet36fly/.venv/lib/python3.12/site-packages/starlette/testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
804 passed, 2 warnings in 6.12s
.venv/bin/ruff check bet36fly tests scripts
All checks passed!
cd web && npm test

> bet36fly-web@0.1.0 test
> vitest run


 RUN  v4.1.11 /Users/davidmontgomery/Documents/ChatGPT/bet36fly/web


 Test Files  7 passed (7)
      Tests  66 passed (66)
   Start at  23:57:53
   Duration  681ms (transform 707ms, setup 0ms, import 1.20s, tests 518ms, environment 0ms)

cd web && npm run build

> bet36fly-web@0.1.0 build
> tsc -b && vite build

vite v6.4.3 building for production...
transforming...
✓ 204 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.56 kB │ gzip:   0.38 kB
dist/assets/index-BI0YTwPD.css   38.34 kB │ gzip:   8.53 kB
dist/assets/index-lwZ3xUdC.js   449.31 kB │ gzip: 137.83 kB
✓ built in 684ms
```
