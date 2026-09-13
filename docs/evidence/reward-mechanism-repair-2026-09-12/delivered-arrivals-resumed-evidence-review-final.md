# Independent evidence reader/UI correction review

September 13, 2026 UTC. **PASS: no remaining actionable findings in the three corrected families.** Reviewed final reader SHA256 `bb36ad4ee0dfd73bb7e01e9c67bb2ca833015828fe91b20b22a85516c1adab0e` and component `1b9400fa0a818b736ca6bf17ef7f7178a2eba0c29a39a63f0998ae8a7cec2f71`. All files in `task4b-release-hashes.json` matched before and after the independent probes.

The initial findings remain preserved in `delivered-arrivals-resumed-evidence-review.md`. This correction review was limited to those findings and their covering tests; it did not initiate another broad audit.

- **Per-trial publication and endpoint checks:** the reader now reconciles each recorded KC class/channel group, checks group/compartment alignment, rejects out-of-range eligible endpoints, and requires observations for inclusive endpoint bounds. Independent probes covered overshoot, exact lower/upper endpoints, same-group cancellation, distinct-group cancellation, valid zero effect, valid recorded cancellation and correctly recorded endpoint bounds. All 12 passed. Recorded bounds remain evidence against qualification, even when the record itself is internally valid.
- **Malformed presentation metadata:** the reader rejects invalid scalar/hash shapes before they reach the UI. All 24 combinations of six fields with object, array, number and boolean values produced an invalid/unverified row while preserving a healthy stored-only sibling. Every resulting payload rendered through the actual `RewardEvidenceView` and React server renderer without crashing or claiming a validated pass. This was pure reader/component execution; no web server or ASGI application was started.
- **Blocking run IDs:** all four original/second pass/fail combinations identify exactly the failed validated members, including neither and both. The production regression selection also passed: **8 passed, 23 deselected**.

The independent executable probe and full results are `delivered-arrivals-resumed-evidence-recheck.py` and `.json`. Ruff passed on that output-only script. It confirms no `bet36fly.reward_brain` import, stable release hashes, and the real preserved evidence classifications: final original bridge validated passed, final second bridge validated failed on the untaught guard, raw panels stored-only/unverified, conditioning not run because the second bridge failed. The counterexamples concerned validator robustness; they do not alter the scientific results or demonstrate learning.

The writer's stored standard-gate log was read: **970 pytest, 81 Vitest, Ruff and build passed**. The parent separately reported an actual marked read-only browser pass and byte preservation; browser acceptance remains the parent's evidence, not an independently reproduced result by this reviewer. No production/test edits, native call, circuit experiment, model-pointer change, server launch or commit was performed by this reviewer. Conditioning qualification remains outside the implemented harness and is not treated as complete.

## Final document-reading receipt

The complete prior document reading is recorded in `delivered-arrivals-resumed-reading-receipt.json`: all 28 original corpus chunks, 31 additional chunks and nine final-refresh chunks were actually read, with truncated portions reread. The current AGENTS hash still matches that receipt. Afterward, the complete changed API/UI contract and root's final changes to FLY_GUIDE, dopamine cells, PPL101 inputs and the evidence index were read against their already-read contents. The newly copied `dopamine-signal-sources-resumed.md` was read in full. Its engineered adaptation hypothesis remains unimplemented and unqualified; it was not used to claim a repaired biological learning mechanism.

Final read boundary hashes:

| Document | SHA256 |
|---|---|
| AGENTS.md | `1867e109eeb497a9e86a5069d6846ff02408317bfebb0d01315713aab1a765a1` |
| docs/FLY_GUIDE.md | `27d87d0211f1c238c2877360fb8c8ca6b1c7c6da8b74044d78296ac2897ce882` |
| docs/api-contract.md | `74a9b6cf92e41dd225389a5841ef362caf7fb50e22e51db0a1bd0ef67cb6028c` |
| wiki/cells/ppl101-inputs.md | `9a20418c05666133fd240d2929793493e586395a7f687b8e4780d692faeafd51` |
| wiki/cells/dopamine.md | `7fb6f25c5dfa0a622fe03d9446378aab6495c7c501352bff9b2136d3358648a1` |
| docs/evidence/reward-mechanism-repair-2026-09-12/index.md | `0e7ca01f3219e934e31e4a453639111a9a626b7a14c1c727c1b6d1362af7069e` |
| docs/evidence/reward-mechanism-repair-2026-09-12/dopamine-signal-sources-resumed.md | `3eb2b28f996b1972444e50676ffcf29aa907a24ef39082f7c6a8883a62bb67b5` |
