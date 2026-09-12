---
type: experimental-reasoning
updated: 2026-09-12
status: proposed-mechanism-validation
---
# Evidence required for a learning claim

The active scientific hold is **SCI-001: untaught-home change exceeds the predeclared operational guard**. It remains open in the [repair report](../docs/evidence/reassessment-2026-09-12/repair-phase1.md). The following sequence describes evidence still needed, not experiments run by this wiki task.

## Keep four levels separate

| Level | What would establish it | Current evidence |
| --- | --- | --- |
| Anatomical identity | Locked source files, source-aligned cell IDs, actual directed contacts | Imported graph and freshly exported atlas |
| Numerical implementation | Rule oracle, trace-order tests, bounds, masking, disabled-learning parity, exact replay | Existing main tests and separate repair tests/diagnostics; verify each on its own branch |
| Cue-specific learning | Acquisition versus matched controls, independent probe noise, selective effects and reversal | Not yet established |
| Sports usefulness | Matched, out-of-sample comparison against controls and same-information baselines | Historical pilots failed; no repaired sports result verified here |

## Controls answer different questions

| Condition | Sensory exposure | Teaching | Plasticity | Question |
| --- | --- | --- | --- | --- |
| Paired | Matched | Correct association | On | Does pairing add a specific effect? |
| Shuffled labels | Matched | Permuted association labels | On | Does label correspondence matter? |
| Timing-unpaired | Matched and explicitly scheduled | Teaching temporally separated from the cue | On | Does temporal association matter? |
| Untaught | Matched | None | On | What changes from exposure and endogenous modulation alone? |
| Frozen | Matched | None for the specified sports control | Off | What changes without gain updates? |

Shuffled labels are not a timing-unpaired experiment. A frozen comparison does not isolate spontaneous learning drift. The exact timing-unpaired schedule and reset boundaries must be specified before its result is interpreted; it must not accidentally erase eligibility in only one condition. Biological experiments motivate specificity and timing dependence, but protocols can produce different backward-pairing outcomes. [Hige et al.](https://pubmed.ncbi.nlm.nih.gov/26637800/), [Handler et al.](https://pubmed.ncbi.nlm.nih.gov/31230716/).

## Mechanism sequence

1. Declare units, onset, trace decay/update order, clipping and trial reset; reconstruct the rule's changes from recorded KC/DAN events.
2. Account for untaught change and preserve the predefined pass/fail threshold. Inspect each channel and KC family, not only pooled means.
3. Apply the verified gamma-only away policy while preserving transmission and all home support. This policy cannot repair a home-channel failure.
4. Measure cue-specific acquisition against untaught, timing-unpaired and frozen controls. Separate repeated-noise reproducibility from fresh-noise generalization; shared random seeds are useful for comparisons but cannot establish robustness alone.
5. Start reversal from the **acquired gains**, change the association, and compare with continued-acquisition and matched exposure controls. Resetting gains to one would test reacquisition, not reversal of a stored association.
6. Only after those gates, assess whether the fixed readout needs centering, with a new identity and preserved uncentered results. Larger sports pilots and odds scoring remain deferred.

No new thresholds are invented here. Existing guard definitions and failures are preserved; a future mechanistic protocol must declare any additional criteria before observing the result.

## The separate schema-5 handoff

The saved [handoff](../docs/evidence/reassessment-2026-09-12/repair-handoff.md) specifies one descriptive development comparison with paired, shuffled, untaught and frozen arms, raw D, gamma-only away updates, unchanged data/gains/encoder/readout and identical initial gains. It is not the timing-unpaired/reversal program above. Its scores would be descriptive even if improved; SCI-001 remains unchanged. No schema-5 pilot was executed by this task.

[Wiki index](index.md) · [Reassessment](reassessment.md)
