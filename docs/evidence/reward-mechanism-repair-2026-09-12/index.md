# Dopamine mechanism repair — September 12, 2026

**Status: scientific HOLD; the rate bridge still fails the second panel's untaught-home guard.** Both the corrected raw-event rule and the subsequent rate bridge pass the original panel but fail the previously frozen second panel. The rate bridge reduces the measured drift without satisfying the unchanged guard. Numerical implementation tests pass; cue-specific acquisition, reversal and improved sports prediction remain unestablished. Conditioning has not run.

The later [KC muscarinic source/model review](handler-kc-switch-model-transfer-review-2026-09-13.md)
and [independent coupling analysis](learning-coupling-mathematical-source-review-2026-09-13.md)
identify a concrete local-state hypothesis, along with two barriers to direct
transfer: an external-shock dopamine gate and timestep-dependent inhibition.
The [current code/conditioning audit](conditioning-contract-evidence-ui-audit-2026-09-13.md)
found no new reset/sign/control defect and confirms the receptor state is
unimplemented. The [synthetic source audit](kc-lateral-source-audit-protocol-2026-09-13.md)
does not fit or evaluate a new MaleCNS mechanism. See the
[cell-specific explanation](../../../wiki/cells/kc-lateral-signaling.md).

The September 13 [individual PPL101 signal analysis](ppl101-signal-basis-result-2026-09-13.md)
reproduces all 32 canonical home gain vectors and leaves local routing
unresolved; its necessary bounds establish no passing map. The separate
[receptor-state decision](dopamine-receptor-state-decision-2026-09-13.md)
records a source-supported signaling distinction and the quantitative
assumptions still needed for a candidate. Neither changes the current rule
or qualifies conditioning.

The [complete-metadata v1 failure](partners-metadata-v1-result-2026-09-13.md)
exposed a valid repeated-header case omitted by the synthetic tests. The
[separate v2 correction](partners-metadata-v2-preparation-2026-09-13.md)
has a documented field contract and independent regression coverage. Its
[completed inventory](partners-metadata-v2-result-2026-09-13.md) covers all
4,759 batches and establishes 2,013,351,963 unread body-column buffer bytes;
no body IDs or coordinates were retrieved. Neither that metadata nor
the [new weight-state source hypothesis](dopamine-weight-state-decision-2026-09-13.md)
establishes a local dopamine exposure law or a qualified learning mechanism.

The [completed weight-state shadow](weight-state-shadow-result-2026-09-13.md)
is also rejected. All 32 histories completed once; the second/base home mean
−0.268754929304 exceeds its 0.235695145300 limit. The independent audit passes
128 fixed references and all 1,024 scalar comparisons, reproducing all eight
guard classifications with zero actual or possible bound contacts. Preparation
passed 794 distinct synthetic cases. This fixed-history failure changes no
production rule and qualifies no conditioning.

The separate [quantitative release/receptor inquiry](tonic-burst-dopamine-quantitative-source-check-2026-09-13.md)
finds measured adult-fly regional release dependence and cultured-receptor
dose responses. Those measurements do not calibrate local tonic/burst signaling
at our selected PPL101/MBON11 or PAM12/MBON09 synapses. The inquiry was declared
before the weight-state outcome and chose no new candidate parameters.

## Confirmed correction

Delayed recurrent input and instantaneous teaching pulses were being stored while their receiving neuron was refractory. That stored input could affect the neuron after release. The reward kernel now rejects those writes during refractoriness. The pinned Shiu implementation and Brian documentation support this behavior; the existing local discrete release boundary remains explicit. [Source contract and generalized regressions](../reward-refractory-contract-2026-09-12.md).

Local merge `e385050` retained the phase-1 rule instrumentation and away eligibility mask. It leaves all 4,184 home edges eligible and allows updates on 3,239 gamma away edges; 1,443 other away edges continue transmitting without plasticity. Encoder, drive gains, learning rate, eligibility time constant and diagnostic thresholds were unchanged.

## Original panel

[`diag-candidate-maskgamma-a4e0db0de471`](panel-diag-candidate-maskgamma-a4e0db0de471.json) contains the full 64-row matrix, four repeat checks and 16-trial untaught cumulative sequence. All seven criteria passed. The recorded native binary SHA256 is `3f3c02a4fde56d95fa48facac225e50efa5232b159816e5dc8ae689b70675490`.

Home untaught gain sums still averaged −0.183 and −0.188, with standard deviations 0.668 and 0.525. The guard compares each absolute mean with half its standard deviation; passing it does not mean zero spontaneous change. Matched teaching effects averaged approximately −3.18 home and −4.54 away, so passing was not achieved by suppressing all learning. Cumulative home change was −3.883. [Actual graph and annotation checks against the frozen historical inputs](corrected-event-inputs.json).

The second panel and controlled acquisition/reversal must pass separately. The [rate bridge](rate-bridge-preregistration.md) was a conditional hypothesis frozen before these measurements; its implementation and first result are described below. The [conditioning protocol](conditioning-preregistration.md) and [pre-run addendum](conditioning-prerun-addendum.md) were frozen before any conditioning measurements. The addendum makes probe timing, selectivity, controls and call arithmetic explicit; both document hashes belong in the conditioning identity.

## Complete bound reporting and held-out result

Review found that strict clipping counters could miss exact bound contact followed by recovery, and cumulative trials were omitted from the aggregate bound criterion. The [recording-only correction](inclusive-bound-observations.md) includes equality, cumulative observations and the final checkpoint. It also requires explicit counts rather than interpreting missing evidence as zero. Neural dynamics were unchanged.

The new [original panel `29c766f95f82`](panel-diag-candidate-maskgamma-29c766f95f82.json) again passed all seven criteria, with zero bound observations. [All 473 retained arrays and the full archive hash match](original-recording-parity.json) the earlier original result.

The [held-out panel `e3d8898dc68a`](panel-diag-candidate-maskgamma-e3d8898dc68a.json) is complete and source-stable. It uses the remaining eight calibration cues and the separately declared fresh noise. Six criteria passed; the untaught guard failed for home/base: mean −0.515622884, SD 0.979555768, permitted absolute mean 0.489777884. Home/alternate and both away guard cells passed. Cumulative home drift was −5.747775733, within its 13.795605525 relative limit. Zero bound contacts were recorded. The failure remains a failure even though it is close to its threshold.

No conditioning run was launched after this result. The smaller correction was insufficient for qualification; the already frozen rate bridge was then implemented and checked against independent numerical oracles before its first circuit panel. The failed raw-event result remains visible alongside the later candidate.

## Rate bridge numerical verification and first panel

The [implementation contract](rate-bridge-implementation-contract.md) fixes the 100 ms rate filter, 500 ms eligibility filter, learning rate 0.0005 and normalization 0.96. Exact interval integration uses a double-precision gain accumulator, float32 transmission/checkpoints and a separately recorded analytic no-new-event tail. That continuation changes gains after the electrical endpoint; it does not simulate additional neural activity. The [independent reference audit](bridge-reference-audit.md) checks the mathematics without importing the simulator.

The implementation passed 477 focused tests and the complete repository gate: 804 Python tests, 66 frontend tests, Ruff and the build. Independent review checked the source equations, signed timing, population normalization, masks, clipping, resets, small updates, recording and native integration. These establish numerical behavior, not biological learning.

The first [full-circuit bridge panel `1b233bc75647`](panel-diag-rate-bridge-v1-maskgamma-1b233bc75647.json) completed in 51 seconds with unchanged source and all seven criteria passing. Home untaught sums averaged −0.103840373 and −0.060988627, within respective limits 0.128355080 and 0.131732571. Matched teaching sums averaged about −1.91 home and −2.74 away; cumulative home change was −1.533297837. No electrical or tail bound contact was observed.

The runner compared complete numerical replay fingerprints during this run but did not save those comparisons' inputs. The [recording follow-up](bridge-recording-followup.json) preserves the result and extends retained fingerprints, sensory histories and artifact hashes before the final qualification pair. It changes no equations, parameters or thresholds. The first held-out bridge receipt remains unrun and superseded; the second cue/seed panel has already been used for the raw rule and must not be described as newly unseen data.

## Bridge qualification with independently checked artifacts

The final [original panel `de050d773763`](panel-diag-rate-bridge-v1-maskgamma-de050d773763.json) passes all seven criteria. [All 817 shared arrays are byte-identical](bridge-original-recording-parity.json) to the first bridge recording; the only added arrays are 64 sensory histories. Native source and binary are unchanged. The [independent artifact audit](bridge-original-independent-audit.json) recomputes the criteria from saved gains, complete matrices, electrical/tail records, sensory histories and persisted replay fingerprints.

The final [second panel `dea14759e9ca`](panel-diag-rate-bridge-v1-maskgamma-dea14759e9ca.json) completed in 46 seconds with unchanged source. Its [independent audit](bridge-heldout-independent-audit.json) reproduces the failure: home/base untaught mean −0.272640035 exceeds the absolute limit 0.240845235 (SD 0.481690471). Home/alternate passes at −0.074156590 with limit 0.101465835; both away cells remain zero. Matched teaching remains present, averaging approximately −2.04 home and −2.88 away across noise sets. Cumulative home change is −2.884238005 and passes its relative limit. All six other criteria pass; no electrical or analytic-tail bound contact is recorded.

[Independent numerical/code review](rate-bridge-independent-review.md), the [implementation report](rate-bridge-implementation-report.md), and the [artifact reanalysis script](verify_bridge_artifacts.py) preserve their respective scopes. Saved replay fingerprints permit an independent equality comparison; original gain, sampled trace and bridge arrays are additionally matched to their recorded fingerprints. The artifact audit is an offline reanalysis, not a new circuit experiment.

The bridge is therefore insufficient for qualification. The next bounded investigation attributes the residual to actual cell classes, phases and recorded signals and rechecks primary mechanism evidence. No diagnostic threshold, drive gain or home eligibility policy is changed to remove this failure. Acquisition and reversal remain gated.

The [saved-array attribution](bridge-residual-attribution.md) finds 71.54% of the failed home/base signed depression in alpha/beta KC inputs, with 94.68% applied after stimulus offset. It is distributed across cells; similar PPL101 counts do not isolate either neuron as a cause. Independent impulse-response and endpoint checks reproduce the recorded arithmetic. These findings do not justify removing home edges or treating the application time as the causal spike time.

## Onset-history hypothesis rejected

The [frozen investigation](onset-history-investigation-preregistration.md) captured
exact KC/DAN histories and compared two history operators offline. It completed
all 33 declared calls in 50.5556 seconds, with exact coarse/fine and canonical
parity. The alternative retained pre-100 ms filter history while keeping gain
writes at 100 ms and all other scientific settings fixed. Its gains never fed
back into the neurons.

The [measured result](onset-history-result.md) rejects this hypothesis:
second/base home mean worsens from −0.272640034556 to −0.481925711036. Thirty of
32 home trials worsen, and all four home panel/noise groups fail their guards.
All away groups remain zero. The [independent artifact audit](onset-capture-independent-audit.md)
checks every saved capture/shadow, exact event-pair integrals, published gains,
bound exclusion and accounting within the frozen 33-call/600-second budget.
This is a failed fixed-history calculation, not a qualified new learning rule.

The [PPL101 input audit](ppl101-input-audit.md) enumerates 7,279 retained direct
edges, 39,125 contacts and named KC/MBON/APL feedback to bodies 11327 and 11900.
KCs account for 61.52% of contacts. That fraction is anatomical; actual delayed
arrivals, refractory state and other inputs are required before interpreting
delivered activity. Source investigation of the generated dopamine signal and
its plasticity coupling continues. No next candidate is established by these
audits, and conditioning/reversal remain gated.

The subsequent [delivered KC arrival audit](delivered-arrivals-resumed-report.md)
checks all 32 fine histories and both PPL101 cells. Gamma inputs supply about
86% of accepted KC increments, distinct from alpha/beta's predominance in the
learning residual. An independent queue reproduces all 64 target/trial arrays;
31 boundary/accounting tests passed. Most non-KC input timing was not sampled,
so these results do not establish complete drive or a causal learning pathway.

The [paused conditioning draft review](conditioning-draft-review.md) also exposes
incomplete plan, frozen-gain/bound and empty-replay validation. Its numerical
counterexamples are software review evidence; the draft remains unintegrated and
must gain the full frozen-contract tests before use.

The September 13 [harness implementation contract](conditioning-implementation-contract.md)
records the production repair: exact ordered calls, all-parent
reversal entry, per-seed/mean scoring distinctions, complete numerical replay,
checkpoint isolation and independently checked artifacts. The original draft
and both scientific preregistration documents remain preserved. No conditioning
measurement has been made; the current failed mechanism pair must be refused
before constructing an engine. The [completed software acceptance](conditioning-acceptance-2026-09-13.md)
passes 4,055 Python tests, 85 frontend tests, Ruff/build and the guarded browser
workflow. The actual failed pair is refused with zero engine-factory calls;
this is no new conditioning measurement.

The completed [dopamine signal source investigation](dopamine-signal-sources-resumed.md)
records eight primary-source entries with access limits and checks all 14,551
retained outgoing pairs from the selected DANs. Both PPL101 cells contact both
MBON11 bodies, so body-side labels cannot establish local dopamine exposure.
The report describes targeted synapse-location retrieval and a fixed engineered
rate-adaptation hypothesis. At that source-reading boundary neither had been
executed; the subsequent saved-history evaluation is recorded below.
Its [122-document reading receipt](dopamine-signal-reading-receipt-resumed.json)
and [copy/input-hash verification](dopamine-signal-copy-manifest.json) preserve
the audit's actual scope.

The [bounded neuPrint access check](localization-access-report.md) subsequently
received no HTTP status or coordinates: one sandbox DNS failure and two
network-enabled timeouts. Authentication and live dataset metadata remain
undetermined; this is not evidence that the service is globally unavailable.
The subsequent [official-file range inspection](localization-range-report-2026-09-13.md)
received both complete synapse-file footers and checked all 10,214 record-batch
locations. Six requests consumed 813,653 response bytes in 58.843649 seconds;
the first request exceeded its individual 15-second cap by 0.202552 seconds,
which remains an explicit execution exception. No synapse rows were decoded
and no body-selection index was established. The [cell-specific account](../../../wiki/cells/synapse-localization.md)
distinguishes this metadata from local dopamine exposure. The [copy manifest](localization-range-copy-manifest-2026-09-13.json)
preserves the original report, complete receipts, source versions and offline
protocol tests; 11 tests passed from the copied location.
A separate [version-pinned first-batch metadata check](localization-batch-metadata-report-2026-09-13.md)
then completed three requests totaling 11,890 response bytes in 0.720422 seconds,
within every declared cap. It identifies exact unread body-column buffer
locations and 65,536 rows in each first batch. All 97 protocol/parser tests
pass from their [copied evidence](localization-batch-metadata-copy-manifest-2026-09-13.json).
It does not establish complete body selection, global transfer cost, locations
of the selected cells or local dopamine exposure.
The [IPv4 neuPrint transport check](localization-neuprint-ipv4-report-2026-09-13.md)
completed DNS, TCP and TLS, then stopped at 14.005163 seconds without a complete
HTTP response. Only the first request ran; all declared caps were met and the
conditional dataset request was skipped. Fifty copied offline client tests
passed. This does not establish an authentication or dataset condition.
The [offline next-decision synthesis](localization-next-decision-synthesis-2026-09-13.md)
narrows the useful anatomical deliverable to a complete partners-only export
of all PPL101 outputs or MBON11 inputs. Its coordinates could describe contact
geometry without a distance cutoff or exposure weights. The subsequent
[complete metadata inventory](partners-metadata-v2-result-2026-09-13.md) measures
the body predicate scan's unread buffers at 2,013,351,963 bytes. No body-value
scan, selected-row export or local plasticity candidate has been executed.
The separately completed [fixed rate-adaptation screen](rate-adaptation-shadow-result.md)
completed all 32 declared saved histories in 50.4832 seconds, with zero circuit
calls and unchanged inputs. It failed all four home guards through excessive
potentiation: second/base home mean +2.638301402, absolute limit 1.113471909.
The complete tail and both signed product areas remain in the result; no
timescale, onset, mask or threshold was retuned. The
[frozen specification](rate-adaptation-shadow-preregistration.md), independent
numerical/boundary reviews, complete arrays and copy manifest preserve this
rejected engineering hypothesis. It is not a production rule or qualification.

## Preserved evidence and execution exception

The [mechanism evidence API and Training view](task4b-acceptance.md) expose
the stored and recomputed circuit diagnostic verdicts. The offline adaptation
study remains separately documented here. Final verification passed 970 Python tests, 81
frontend tests, Ruff/build and the actual guarded browser workflow, including
stale/retry recovery and the unchanged failed bridge pair. All 782 protected
files and inventories matched after requests and shutdown. This completes the
diagnostic presentation at that earlier boundary. The subsequent
[conditioning runner and artifact reader acceptance](conditioning-acceptance-2026-09-13.md)
is complete as software; a qualified mechanism and measured conditioning/reversal
remain unfinished.

- [Historical diagnostic copies](historical-diagnostic-copies.json) retain the failed earlier results under their original identities.
- [Dated correlation erratum](lag-profile-erratum.json): the historical mean fine-lag cross-correlation peaks at 0.054121782 at +3 ms, rather than the 0.037 stated in the old prose. The weak correlation does not identify a causal anatomical path.
- [Agent reading receipts](agent-document-reading.json) record the complete initial documentation corpus; workers read later changes at review boundaries.
- [QA startup incident](task1-startup-side-effects.json): a default server startup refreshed live sports caches and inserted 81 v1 paper forecasts. The server was stopped. These shared rows are preserved because no pre-start snapshot exists. Historical reward artifacts and the active model pointer remained intact. Subsequent verification requires a read-only, refresh-disabled startup.
- [Read-only startup repair and actual browser acceptance](verification-startup-acceptance.md): 911 Python tests, 68 frontend tests, Ruff/build and browser checks passed. All 749 protected files and their inventories matched before requests, after requests and after shutdown. This fixes QA startup, independently of the failed learning qualification.

No new sports pilot, model promotion or push is part of this repair.
