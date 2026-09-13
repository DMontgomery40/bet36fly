# Calibration checkpoint verification — September 13, 2026

Checkpoint `sensory-calibration-355e1f3d476830f4` is an unresolved cell/rate contract, with **zero new sensory assay neural calls**. Tests below exercise evidence tooling and existing software; they do not demonstrate a natural response.

| Check | Fresh result |
|---|---|
| `.venv/bin/python -m pytest tests/test_sensory_crosswalk.py -q` | 15 passed; exact integers, reordering, ambiguous/missing IDs, annotation mismatch, directed/weak/self contacts, source/graph corruption and non-overwriting evidence CLI |
| Exporter `--output docs/evidence/natural-sensory-calibration-2026-09-13 --check` | All three output files reproduced byte-for-byte after rechecking all three locked raw hashes and complete retained graph accounting |
| Independent evidence arithmetic | All 523 pairs checked against reverse CSR index lookup and target membership; all 10 source measurement groups recomputed; nine identity-bound artifact hashes matched |
| `make verify` | 4,070 pytest tests passed in 284.40 s; Ruff passed; 103 Vitest tests across 8 files passed; TypeScript/Vite production build passed |
| Guarded browser acceptance | Existing `scripts/verify_reward_browser.cjs` passed against marked read-only verification app on port 8766 after rebuild; no page errors |
| Preservation | All 124 snapshotted files unchanged, including imported research, source lock, graph arrays, production neural code, configs and recorded pointers/manifests; active v1 checkpoint bytes additionally matched pointer hash |
| Documentation | 179 local Markdown file targets checked; zero broken targets; `git diff --check` passed |

The browser used the `make serve-verify` factory command with only the port changed to 8766 because an existing normal server occupied 8765. The normal server was left running; the verification app does not warm models or refresh sports. Acceptance checked stored completed results against the API, validated versus stored-only failures, paused v2, active v1, downloads, responsive widths and 20 isolated loading/empty/error/running/recovery/conditioning fixture scenarios. Synthetic fixture verdicts are not neural evidence. The [captured existing mechanism panel](existing-mechanism-desktop.png) was visually inspected: it retains the failed rate-bridge qualification and the distinct stored-only statuses. No natural assay was exposed in the frontend, and production/API/frontend behavior is unchanged.

[Full standard gate output](make-verify.txt), [focused output](focused-tests.txt), [browser evidence](browser-evidence.json), [integrity checks](integrity-check.json). Pytest emitted two existing Starlette/TestClient deprecation warnings; no test failed. The initial exporter test was red before implementation; final results above are fresh.

Active v1 remains `20260910T232621Z`, checkpoint SHA-256 `3b6e7312cc4be07a354df4ff377bd6a05fb3af67effe6b86c67bedfa25bcf76e`; v2 remains paused. The pre-existing untracked `PUBLIC_POST_HANDOFF.md` was untouched. This checkpoint does not claim a complete snapshot of every output file; the protected manifest states its exact scope. The temporary verification server shut down cleanly after acceptance. Nothing was pushed or deployed.

Unverified scientific contracts: exact sweet/water/bitter subtype binding, absolute baseline and transient/adaptation schedule, native specimen transfer, supported aversive/mixed input schedules and behavioral output interpretation. The two-source comparison is a prepared external design, not an implemented neural choice. Follow the targeted next decision in [the checkpoint](index.md).
