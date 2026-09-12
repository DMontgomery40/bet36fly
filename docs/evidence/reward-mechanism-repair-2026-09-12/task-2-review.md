# Task 2 independent review

Reviewer: mechanism_sources. September 12, 2026 UTC. Reviewed released working-tree changes from `e3850505ca76012d255d7d9b9ab718f96e24e054`, the implementation report, actual final verification receipts, and both replacement preregistrations before execution. No production edits, test reruns, browser startup or neural experiments were performed by this reviewer.

**Spec-compliance verdict: PASS.** The released diagnostic harness implements the predeclared original/held-out selection and completeness contracts, preserves the scientific thresholds, and incorporates the explicitly approved observation correction without changing neural dynamics.

**Code-quality and generalized-test verdict: PASS.** No remaining blocking findings were identified in the scoped review. This approves execution of the newly frozen original panel and, conditional on that gate, the held-out panel. It does not establish either result, acquisition, reversal or biological transfer.

## Reviewed release identity

- Native source: `01893f465b20bb3956d0537e191dc0dbe0de7c63bcc45962fc396b6da1dc485e`.
- Original: `diag-candidate-maskgamma-29c766f95f82`; receipt SHA256 `59aca2080877edf9d31a3180a3b842316adc20e8e65a712865b13ac3c7daeb7d`.
- Held-out: `diag-candidate-maskgamma-e3d8898dc68a`; receipt SHA256 `43fe4f771339d194fca11c3752aab1876ab0cbcef5e21817a1f6cfc368b60d9f`.
- Superseded unrun receipt `ee89fe032a62` remains byte-identical at SHA256 `7ad1d752629ae47d24594a3e54ecebadb2ed9eb61d0d08066d7969d07c073f5f`. Its code hashes intentionally no longer match this release.

Read both complete replacement JSON receipts, including all 64 expected matrix entries and 16 ordered cumulative entries. A separate read-only hash comparison confirmed every code hash in both replacement receipts matches the released files. All three prospective output directories were absent at that check. The earlier measured `a4e0db0de471` result remains historical evidence under its own identity.

## Contract and implementation assessment

`select_panel` validates the entire frozen calibration/source input before selecting a panel. It rejects unresolved/duplicate/malformed source IDs, nonfinite or misaligned features, invalid normalization, invalid integer selectors and unsafe seed arithmetic. Original and held-out labels require their exact canonical selectors; other selections are debug. The held-out uses offsets 8–15 with seed offset 2,000,000 and the alternate offset 1,000,000. Its cumulative sequence correctly retains all 16 calibration inputs with the fresh base offset.

The runner binds the frozen pilot input, protocol and manifest, all nine graph arrays plus two annotation files, and the relevant orchestration/native sources. It verifies graph inputs before circuit construction and checks source/input/native identity after execution. Preregistration-only returns before `make_circuit`; held-out execution requires an existing matching receipt, and mismatched receipts/output directories are not overwritten. The no-circuit preregistration test replaces `make_circuit` with a function that fails if invoked.

Completeness comes from the actual matrix's source/seed/condition identities and the actual ordered cumulative sequence. It is not inferred from requested row counts. Cumulative vectors must have exactly two finite components and reconcile with the running sum of per-trial applied changes at absolute 1e-6, relative zero. Debug panels cannot report any of the seven gates passed. Teaching ratio 3, untaught half-SD guard, cross-compartment ratio 0.05, cumulative ratio 4, replay equality, sensory invariance and zero-bound requirement remain unchanged.

## Bound-evidence defects resolved before release

The previous strict counters could miss an exact bound contact followed by recovery. The previous overall criterion also omitted cumulative observations. These were observable evidence defects, not grounds for changing the learning equation or tuning its magnitude.

The only native changes after Task 1 are comments and `<`/`>` becoming `<=`/`>=` inside recording. The counters now mean eligible edge-step observations at or beyond a bound, including equality and repeated/frozen dwelling. They are not unique edges or distinct arrivals. No pre-onset or excluded-edge observations are added. The dated observation contract explicitly preserves these limits and the legacy column names.

The released runner records counts on every cumulative row, combines panel and cumulative observations, and independently checks the actual final saved eligible gains against both inclusive bounds. Missing counts cannot stand in for zero: `check_diagnostic_complete` requires valid explicit nonnegative integer evidence in every panel and cumulative row, while `evaluate_bound_hits` independently rejects missing/negative/fractional/boolean/nonfinite evidence. The legacy descriptive helper's missing-count fallback therefore cannot certify a newly complete diagnostic gate. Final excluded edges are correctly excluded from the boundary test; nonfinite gains are still rejected.

Native tests cover both bounds, exactly representable contact, subsequent recovery, overshoot, frozen dwelling and recorded/unrecorded output equality. Evaluator tests cover panel-only, cumulative-only, final-lower/final-upper and omitted/invalid evidence on both row families. This addresses the whole observed failure family rather than only one saved endpoint.

## Nonvanishing learning and scientific limits

`test_raw_rule_preserves_independent_long_lag_pair_effect_at_production_tau` tests 27 combinations: DAN populations 1, 2 and 22; lags 50, 100, 500 and 1000 ms in both orders; and coincidence. At production eta 0.0005 and tau 500 ms, its independent analytic oracle is `-sign(lag) * eta * exp(-abs(lag)/tau)`. Besides absolute 1e-7 agreement, it requires correct sign and at least 99% of the expected nonzero magnitude, checks actual event steps and checks every DAN's count. This closes the weakness of the older near-zero, short-tau silent-tail assertion without weakening or removing that legacy behavior test.

These tests establish the implemented raw-event rule's timing and population normalization. They do not establish Jiang's continuous-rate implementation, Handler's receptor mechanisms or Hige's compartment-specific biological conditioning. The conditional rate bridge remains unimplemented. The accepted anatomy, eligibility masks, gains, encoder/readout and physiological dynamics are not retuned in this task. A held-out diagnostic pass remains a separate prerequisite to the frozen acquisition/reversal protocol.

## Verification reviewed and boundaries

Read the actual final `task2-focused.txt` and `task2-verify.txt`: 324 focused tests passed; `make verify` passed 643 pytest tests, Ruff, 66 Vitest tests and the production build. The two Python deprecation warnings were disclosed. The initial 48 red cases include tests for new APIs that did not exist yet; they must not be described as 48 separately reproduced pre-existing bugs. Additional malformed count, inconsistent cumulative sum and exact-bound tests establish concrete defects and their repairs.

No new browser check was needed for this internal CLI/evaluator change; existing frontend code is unchanged and its tests/build passed. Product evidence exposure is a later task. No review assertion substitutes a frontend build for a future visible workflow check. The Task 1 startup incident remains separately disclosed and is not silently recast as a Task 2 event.

The earlier held-out selection document retains historical commands and strict-counter caveats under its explicit superseded banner. The replacement observation contract and final report clearly govern this release. No source change or new freeze is requested for that historical prose. A later change to any hashed runtime/orchestration source requires new receipts; these verdicts apply only to the identities above.
