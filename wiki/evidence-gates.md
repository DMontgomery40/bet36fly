---
type: experimental-reasoning
updated: 2026-09-13
status: qualification-failed-conditioning-unrun
---
# Evidence required for a learning claim

The active scientific hold is **SCI-001: untaught-home change exceeds the predeclared
operational guard**. Corrected raw panel `e3d8898dc68a` fails at home/base mean
−0.515622884 against absolute limit 0.489777884. Bridge panel `dea14759e9ca` fails
at −0.272640035 against 0.240845235. The onset-history shadow was also rejected.
[Current results and complete identities](../docs/evidence/reward-mechanism-repair-2026-09-12/index.md).
The following sequence describes evidence still needed; conditioning and reversal
have not run.

## Keep four levels separate

| Level | What would establish it | Current evidence |
| --- | --- | --- |
| Anatomical identity | Locked source files, source-aligned cell IDs, actual directed contacts | Imported graph and freshly exported atlas |
| Numerical implementation | Rule oracle, trace-order tests, bounds, masking, disabled-learning parity, exact replay | Integrated refractory/mask/bridge tests and independent artifact audits; scientific qualification still fails |
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

## Frozen conditioning contract and separate sports handoff

The [conditioning preregistration](../docs/evidence/reward-mechanism-repair-2026-09-12/conditioning-preregistration.md)
and [pre-run addendum](../docs/evidence/reward-mechanism-repair-2026-09-12/conditioning-prerun-addendum.md)
specify acquisition of A/B, an independent C/D pair, and reversal from acquired
A/B checkpoints. They fix 1,632 planned calls, a 1,640-call cap and 1,200-second
cap. Both unchanged qualification panels must pass before entry. Reversal requires
old response and preferred-edge gain recovery, new-target depression, fixed fresh
noise probes and lineage checks. A preference flip alone can be dual-channel
remapping without erasure and is not strict reversal.

The historical [sports handoff](../docs/evidence/reassessment-2026-09-12/repair-handoff.md)
specifies a descriptive development comparison with paired, shuffled, untaught
and frozen arms. It is distinct from the conditioning/reversal program above.
The active repair requires a qualified mechanism before a new sports default or
pilot. No schema-5 pilot has run; historical scores do not satisfy these gates.

[Wiki index](index.md) · [Reassessment](reassessment.md)
