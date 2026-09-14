---
type: assessment
updated: 2026-09-14
status: conditioning-qualified-predictive-contribution-unestablished
---
# Where BET36FLY stands

This is the current evidence summary. Detailed mechanisms belong in the linked topic pages and numerical tables in dated evidence. Older sections below retain their original scope and dates; they do not override later experiments in different circuits.

## Four questions, separate answers

| Question | Recorded answer | Evidence |
| --- | --- | --- |
| Is dopamine-dependent plasticity implemented in the circuit? | Yes, in the separate associative engine; engineered odor/reinforcer interfaces and declared interventions | [Rule, state and measured links](associative-learning.md) |
| Has controlled conditioning qualified? | Conditioning-01 failed; conditioning-02 passed; conditioning-03 passed at all four tested recovery settings | [Conditioning account](associative-learning.md#conditioning-preserve-the-failed-design-and-the-qualified-successor) |
| Does plasticity improve prediction? | No. Confirmed once on the reserved 2018 block (September 14): the frozen recovery candidate beats chance (56.98%) but is reliably worse than its frozen twin and than the encoder alone, and equal to the shuffled and no-recovery arms; 2022 development showed the same | [Prediction evidence](#prediction-evidence-and-data-use) |
| Does the product use a learned associative checkpoint for its probabilities? | No; it serves the frozen sensory confirmation. The learning page exposes separate evidence, explicit jobs and checkpoint probes | [Application contract](../docs/api-contract.md) |

## Prediction evidence and data use

The **plasticity-off sensory pipeline** passed its predefined 2023 MLB confirmation: 1,362 correct of 2,423 games, **56.21% accuracy**, 95% weekly-block bootstrap interval **54.42–58.02%**, log loss **0.680493**. This is a complete fitted historical pipeline with an engineered pregame encoder and external probability readout. Incremental benefit over encoder-only and same-information baselines remains unestablished. It is not evidence of dopamine learning, feeding, in-circuit choice, prospective performance or profit. [Frozen result](../docs/evidence/sensory-backtest-goal-2026-09-13/RESULT.md).

The **associative sports stage** uses 2022 as development: 1,137 games for the fixed readout-fitting procedure and 1,292 later games for evaluation. No-recovery and recovery circuits each tested three declared learning rates against frozen/shuffled twins and conventional baselines. At the selected recovery η = 4e-5, log loss is **0.674268**, versus frozen **0.673896** and encoder **0.668847**. Recovery-minus-frozen is **+0.000372**, interval **[−0.000806, +0.001456]**; recovery-minus-encoder is **+0.005420**, interval **[+0.000787, +0.010243]**. Lower loss is better. Thus the circuit did not establish incremental plasticity benefit and was worse than the encoder under this development comparison. Non-significant twin differences are not proof of equivalence. [Baseline](../docs/evidence/associative-learning-2026-09-13/sports-development.md), [recovery results](../docs/evidence/associative-learning-2026-09-13/sports-recovery.md).

2019–2021 trained the sensory encoder; 2022 is development; 2023 is an already used confirmation; historical v1/v2 also exposed later seasons. The 2018 associative candidate was frozen at η = 4e-5 and ρ = 0.005. Claude's session reports its single confirmation attempt launched; no completed confirmation result was present in the local evidence/output directories at this integration's cutoff. That is a session-reported launch, not a live remote-job verification or an inferred result. Do not launch it again or treat 2018 as unused. [Cutoff and provenance](../docs/evidence/wiki-integration-2026-09-14/reconciliation.md), [working handoff](../docs/ASSOCIATIVE_LEARNING_HANDOFF.md). The 2018 confirmation ran once on September 14 and failed its plasticity criterion while beating chance; the block is spent. [Result](../docs/evidence/associative-learning-2026-09-13/sports-confirmation-2018.md).

## What the new research resolved—and what it did not

The associative stage measured usable odor→KC→MBON responses with explicit ALLN/APL interventions, then demonstrated controlled synaptic learning using an engineered PAM reinforcer. It did not resolve natural sweet→dopamine transmission at the selected coupling. A conditional second-order Clavicle/Quasimodo response is established separately; MN9 feeding qualification remains failed. [Sensory evidence](natural-sensory-inputs.md), [associative links](associative-learning.md#measured-links-and-declared-interventions).

Recovery restored dynamic range during repeated associations. The retired-cue experiment exposed continued depression while other, overlapping cues were reinforced, motivating interference analysis. Neither result established a sports advantage. [Continual learning](continual-learning.md).

The [research directions](research-directions.md) integrate richer readouts, temporal reservoirs, residual reinforcement, interference reduction, visual pathways, lateral-horn integration, physiological calibration and downstream choice. They are proposals with finite questions and controls, not completed mechanisms. The [canonical direction](../docs/PROJECT_DIRECTION.md) and [current handoff](../docs/ASSOCIATIVE_LEARNING_HANDOFF.md) own execution scope. No model is promoted by this documentation.

## Preserved legacy context

SCI-001 remains HOLD for the PPL101/MBON11–PAM12/MBON09 reward diagnostic. Its failed shadows remain rejected and its gated conditioning program remains unrun. Those failures do not contradict later controlled conditioning on the separate PAM08/MBON05–PAM01/MBON01 associative engine. The historical v1 pointer remains preserved and v2 paused; neither is relabeled as a sensory or associative prediction.

## Legacy learning account — September 13 UTC

The latest [home-output physiology and DA/NO component](cells/cyclic-nucleotide-plasticity.md)
separate intracellular signaling, latent memory and expressed synaptic
change. Aso's published four-state equations now have an exact standalone
implementation with independent numerical tests; source rates and expression
times are unchanged. The [checkpoint](../docs/evidence/reward-mechanism-repair-2026-09-12/aso-da-no-component-checkpoint-2026-09-13.md)
passes 267 focused tests and the full repository gate. It is not integrated
into MaleCNS, and no source-protocol or neural experiment ran in this phase.
The current learning failure remains unresolved.

The [DARELA release-source preparation](cells/dopamine-receptor-signaling.md)
now distinguishes a published mouse burst model from one fixed finite
per-DAN engineering construction. The source is pinned and copied with its
license; its eight fixed source-kernel cases and 216 synthetic preparation
tests pass, including independent saved-state and event-transfer checks.
[Exact result and limits](../docs/evidence/reward-mechanism-repair-2026-09-12/darela-source-transfer-checkpoint-2026-09-13.md).
The subsequent [fixed 32-history screen](../docs/evidence/reward-mechanism-repair-2026-09-12/darela-shadow-result-2026-09-13.md)
is now complete and independently audited. All four home guard groups fail,
and all 32 home trials become more depressive. Every final/electrical
float32 endpoint matches the independent calculation exactly. This fixed
transfer is rejected and remains outside production; the learning
qualification is unchanged. The result includes the actual two PPL101 and
22 PAM12 cell histories and modeled release totals.

The latest [saved-record comparison](../docs/evidence/reward-mechanism-repair-2026-09-12/dan-causal-prefix-result-2026-09-13.md)
establishes a teaching input difference in all 64 matched cases at 310 ms.
The same KC history is established through that step. A missing electrical
teaching signal therefore does not explain these cases; conversion to local
dopamine exposure and plasticity remains unresolved. The first reader failed
before comparisons because its synthetic fixture repeated an incorrect
index dtype. Its failure is preserved, and the corrected source contract now
passes 223 tests and independent review of all saved results. No new neural
experiment, candidate, qualification or conditioning result follows.

The preceding [receptor/source-model check](cells/dopamine-receptor-signaling.md)
reproduces all six published Handler-model conditions and independently checks
their saved state and experimental workbook. It finds consequential differences
between receptor reporters, internal weights, plotted weights and measurement
windows. Those results do not calibrate a new mechanism for our selected cells.
The Training view also now identifies its reference as measured during the cue
when recorded timing supports that label, and explains evoked spikes against
the matched unpulsed probe. Historical records remain intact. The
[display and verification checkpoint](../docs/evidence/reward-mechanism-repair-2026-09-12/incentive-ui-acceptance-2026-09-13.md)
passed the full repository gate and actual read-only browser workflow; no new
candidate, qualification, acquisition or reversal ran.

A later [KC lateral-signaling source audit](cells/kc-lateral-signaling.md)
adds a specific missing physiological representation: muscarinic modulation
of local KC signaling. The current graph has 642,933 KC→KC pairs but no such
receptor state. Inspection of the primary model found an explicit shock gate
and clock-dependent inhibition semantics, so its reported learning cannot be
transferred directly. The source code and complete external calcium workbook
are preserved. A subsequent explicit engineering mapping used independently
fitted source-model parameters and was tested once on all 32 saved histories.
Its independent numerical audit
passes, but every home guard group fails and all 32 home trials become more
depressive. [Complete result and individual-cell table](../docs/evidence/reward-mechanism-repair-2026-09-12/kc-local-calcium-shadow-result-2026-09-13.md).
The local mapping is rejected and is not a production mechanism.

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
| Fixed gain-dependent shadow `de1ab218973eb3ecd3d3` | Second/base home mean −0.268755; absolute limit 0.235695; 128 independent references agree | Reject this specified gain-dependent hypothesis |
| Fixed KC-local calcium shadow `6734494c82c54702ead0` | Second/base home mean −0.360410; absolute limit 0.279657; all four home groups fail with exact independent float32 endpoint agreement | Reject this specified local-calcium mapping |
| Fixed per-DAN DARELA shadow `bc6993b67befdb3a6c2d` | Second/base home mean −0.443546; absolute limit 0.358810; all four home groups fail, with all 32 home trials more depressive | Reject this specified every-spike/reset release transfer |
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

The subsequent [gain-dependent calculation](../docs/evidence/reward-mechanism-repair-2026-09-12/weight-state-shadow-result-2026-09-13.md)
completed all 32 saved histories and its independent audit, with zero bound
contacts, but still failed the same second/base home guard. Its 794 synthetic
preparation tests establish numerical and artifact behavior; the actual
negative result prevents treating those passing tests as a repaired mechanism.
The new [release/receptor source check](../docs/evidence/reward-mechanism-repair-2026-09-12/tonic-burst-dopamine-quantitative-source-check-2026-09-13.md)
finds quantitative measurements, while separating adult regional release,
live-fly sensors and cultured-receptor assays from calibration of the selected
γ1pedc/γ3 synapses. No receptor parameters or new candidate were selected from
those findings.

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
