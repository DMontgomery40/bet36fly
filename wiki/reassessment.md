---
type: assessment
updated: 2026-09-13
status: learning-unvalidated
---
# Where BET36FLY stands, and what went wrong

**The present bottleneck is the learning mechanism and its causal validation.** We have real anatomical connectivity, an executing spiking circuit, and measured synaptic gain changes. We do not yet have a controlled demonstration that this configuration acquires and reverses a cue-specific association, or improves sports prediction. The biological approach is not refuted by a failure of these engineered dynamics.

## Current account — September 13 UTC

The retained repair was merged in `e385050`; it is now in this checkout.
Refractory input banking was fixed, the away gamma mask is implemented, and
`rate-bridge-v1` has independent numerical tests. None of those software results
establishes acquisition or reversal. Both the corrected raw-event rule and the
rate bridge pass the original diagnostic panel but fail the second panel's
untaught-home guard. [Complete repair evidence](../docs/evidence/reward-mechanism-repair-2026-09-12/index.md).

| Current measured boundary | Result | Consequence |
| --- | --- | --- |
| Corrected raw, second panel `e3d8898dc68a` | Home/base mean −0.515623; absolute limit 0.489778 | Qualification fails |
| Rate bridge, second panel `dea14759e9ca` | Home/base mean −0.272640; absolute limit 0.240845 | Qualification fails despite a smaller drift |
| Fixed-history shadow `4343c21535c43f42` | Retaining pre-100 ms history worsens home/base to −0.481926; 30/32 home trials worsen | Reject the onset-history-only hypothesis |
| Fixed rate-adaptation shadow `5165a92674683bf2b872` | Second/base home mean +2.638301; absolute limit 1.113472; all four home groups fail | Reject this fixed adaptation hypothesis |
| Conditioning and reversal | Not run; entry gate remains unmet | No learned-association or reversal claim |

The shadow used the actual recorded spikes and never transmitted its alternative
gains. It does not measure what a recurrent circuit with those gains would do.
The [PPL101 input audit](cells/ppl101-inputs.md) identifies the two cells and their
direct feedback paths; the 61.52% KC contact fraction does not establish a current
fraction or causal explanation. The later
[rate-adaptation result](../docs/evidence/reward-mechanism-repair-2026-09-12/rate-adaptation-shadow-result.md)
also uses only saved spikes: it changes depression to excessive potentiation,
with the complete mathematical tail retained. Signal generation and plasticity
coupling remain under investigation, with accepted gains, channels and
thresholds unchanged.

An earlier QA startup refreshed live sports caches and inserted 81 local v1 paper
forecasts. These were preserved because no complete prior snapshot exists. The
subsequent [read-only QA repair](../docs/evidence/reward-mechanism-repair-2026-09-12/verification-startup-acceptance.md)
passed browser and file-integrity checks; it does not undo that incident. The
evidence API/UI extension is now complete and
[verified in the browser](../docs/evidence/reward-mechanism-repair-2026-09-12/task4b-acceptance.md).
The [continuation handoff](../docs/REWARD_REPAIR_HANDOFF.md) records the remaining
scientific work; a correct evidence display does not close its learning gate.

The [conditioning harness is now verified](../docs/evidence/reward-mechanism-repair-2026-09-12/conditioning-acceptance-2026-09-13.md)
with an independent artifact reader and generalized schedule, numerical,
checkpoint and execution-state tests. It refuses the actual failed pair before
constructing an engine. This repairs the experiment machinery; it supplies no
new acquisition or reversal result. The [synapse-location account](cells/synapse-localization.md)
also identifies a complete home contact selection, while keeping unread
coordinates and uncalibrated dopamine exposure explicit.

## Initial wiki assessment — September 12 UTC

The following account preserves the initial inspection before integration. It
inspected the checkout, repair worktree, saved manifests, annotations and primary
sources; existing neural measurements were read, not rerun during that wiki task.
Its statements about separate branches refer to that date, not the current code.
[Workspace identities and preserved reports](../docs/evidence/reassessment-2026-09-12/index.md).

## Two code states must remain visible

| State at inspection | What it contains | What it establishes |
| --- | --- | --- |
| Working branch `feat/bet36fly-dopamine-learning`, pre-wiki commit `daaf080` | Schema 3; signed tonic-baseline subtraction; all 8,866 selected KC→MBON edges eligible | This is the code in this checkout. Its latest saved sports pilot is the historical all-away result. |
| Separate `feat/reward-repair-phase1` worktree, commit `81037f1` | Schema 4 raw-D option, recording instrumentation, gamma-only away mask, diagnostic API | The repairs exist, but have not been integrated into this branch. SCI-001 still fails. |
| Saved later [handoff](../docs/evidence/reassessment-2026-09-12/repair-handoff.md) | Exactly one schema-5 four-arm descriptive MLB comparison specified | A deliverable specification, not a completed run. It does not close SCI-001 or authorize promotion. |

The main checkout was clean before this wiki task. The repair worktree had an untracked `.venv` entry; its tracked code was clean. The three reward manifests in the main registry are schema-1 complete, schema-2 failed at the activity gate, and schema-3 complete. No schema-4/5 sports result was found in the inspected locations. V1 remains the active historical model and v2 remains paused. [State snapshot](../docs/evidence/reassessment-2026-09-12/workspace-state.json).

## The failure sequence

| Stage | Measured failure or result | Conclusion supported |
| --- | --- | --- |
| Early reward pilot, `84fc629bc8045cbff7e0` | Very dense/persistent KC activity, KC-set overlap 0.98–0.99, tonic DAN activity, weak evoked home teaching. Paired loss 2.504442; frozen 0.755230. | The inputs and teaching channel were not adequate for an honest conditioning comparison. Both trained arms predicted away throughout validation. |
| Schema 2, `40d7263f0d2cc1974cf0` | Added phasic proxy and stricter gate; gate failed before any arm trained. | A correctly stopped run, not a trained model with a new score. |
| Schema 3, `209f7c49983f5873f650` | Calibrated drive and identity encoder: KC active fraction 0.160, overlap 0.298, responsive teaching populations. Paired loss about 0.974; frozen about 0.684. | Activity guard passed, but paired and shuffled arms both predicted all-away. Shared gain change dominated the teaching-specific difference. |
| Legacy-rule diagnostic | During post-offset silence, DAN activity fell below the earlier reference; `-Kbar*(D-reference)` became positive. | Signed baseline subtraction introduced a positive update even with no new DAN event. It cannot be described as simply making tonic dopamine neutral. |
| Raw-D repair candidate | Teaching-specific effects and locality checks passed; untaught home mean gain-sum change was −0.289/−0.240 in the two seed panels. | The predeclared untaught-home guard still failed. Removing the legacy artifact did not establish a valid learning mechanism. |
| Gamma-only away mask | 3,239 away edges eligible; 1,443 away edges excluded from updates; all 4,184 home edges retained. | The mask's software behavior was verified in the repair worktree. It does not address home drift. |

Historical sports and calibration numbers come from the [reward evidence](../docs/evidence/reward-v3-summary.md); diagnostic values and thresholds come from the [preserved repair report](../docs/evidence/reassessment-2026-09-12/repair-phase1.md). These values refer to different experiment identities and must not be combined into a fictional repaired pilot.

## What we got wrong in the work process

1. **We advanced to sports scoring before establishing conditioning.** Changing anatomical gains and passing activity checks were treated as encouraging progress, while the indispensable paired-versus-untaught and cue-specific controls remained incomplete. Shuffled outcomes alone cannot isolate exposure-driven changes.
2. **We imported a learning-rule shape without the rest of the source model.** The source model optimized recurrent circuitry that generates learning signals; our circuit uses fixed anatomy, event spikes, externally scheduled pulses and different units. Formula resemblance is not a reproduced biological mechanism. [Rule contract](learning-rule.md).
3. **The proposed next step moved too quickly to readout centering.** Centering can remove a class bias while leaving nonspecific plasticity intact. It belongs after acquisition and reversal with controls, as the accepted repository rules now state. The old recommendation is retained as historical context, not current priority.
4. **Cell names were shortened past a useful distinction.** MBON09 is annotated `y3B'1` (γ3β′1), not a γ3-only output. It receives substantial α′/β′ KC input. The away teaching territory and all inputs to that MBON are not identical. [Exact identities and support](cells/mbons.md).
5. **Our records outpaced integration.** Main docs describe schema 3; a separate worktree has the repairs; ignored handoffs describe schema 5. Reporting any one of these as the whole current system obscures what can actually execute. This wiki preserves their identities without silently merging them.

## What remains uncertain

The repair report's fine-resolution replay reconstructs the actual updates and shows sensitivity to KC/DAN ordering at the 5–20 ms scale. It does **not** establish a single anatomical causal source of the residual. PPL101's 24,068 KC input contacts out of 39,125 total inputs make feedback a plausible investigation target; contact counts alone do not prove a delay mechanism. The early coarse-bin correlation explanation is weaker than the later per-step evidence. [Dopamine page](cells/dopamine.md).

The current gains are not the accepted tuning target. Preserve sensory input gain 0, APL output gain 0.25, KC input gain 1.25, and global scale 0.5. Next mechanistic evidence should resolve the rule and trace contract, retain the supported away mask, then demonstrate acquisition, timing controls and reversal with fresh-noise probes. The separately specified four-arm descriptive backtest remains distinct from that scientific gate. [Evidence sequence](evidence-gates.md).

The initial wiki task copied, documented, audited and exported anatomy. It did not
launch the pending backtest, retune the circuit, merge the repair branch, resume
v1/v2 work, or change a model pointer. The later repair work is described above.

[Wiki index](index.md) · [Primary sources](sources.md)
