# Dopamine mechanism repair — September 12, 2026

**Status: corrected raw-event rule fails held-out qualification; conditioning is on hold.** The refractory handling repair passed the original seven diagnostic criteria, but its independent held-out panel failed the untaught-home guard. Cue-specific acquisition, reversal and improved sports prediction remain unestablished. The preregistered rate-bridge hypothesis is the next candidate, without changing diagnostic thresholds.

## Confirmed correction

Delayed recurrent input and instantaneous teaching pulses were being stored while their receiving neuron was refractory. That stored input could affect the neuron after release. The reward kernel now rejects those writes during refractoriness. The pinned Shiu implementation and Brian documentation support this behavior; the existing local discrete release boundary remains explicit. [Source contract and generalized regressions](../reward-refractory-contract-2026-09-12.md).

Local merge `e385050` retained the phase-1 rule instrumentation and away eligibility mask. It leaves all 4,184 home edges eligible and allows updates on 3,239 gamma away edges; 1,443 other away edges continue transmitting without plasticity. Encoder, drive gains, learning rate, eligibility time constant and diagnostic thresholds were unchanged.

## Original panel

[`diag-candidate-maskgamma-a4e0db0de471`](panel-diag-candidate-maskgamma-a4e0db0de471.json) contains the full 64-row matrix, four repeat checks and 16-trial untaught cumulative sequence. All seven criteria passed. The recorded native binary SHA256 is `3f3c02a4fde56d95fa48facac225e50efa5232b159816e5dc8ae689b70675490`.

Home untaught gain sums still averaged −0.183 and −0.188, with standard deviations 0.668 and 0.525. The guard compares each absolute mean with half its standard deviation; passing it does not mean zero spontaneous change. Matched teaching effects averaged approximately −3.18 home and −4.54 away, so passing was not achieved by suppressing all learning. Cumulative home change was −3.883. [Actual graph and annotation checks against the frozen historical inputs](corrected-event-inputs.json).

The held-out panel and controlled acquisition/reversal must pass separately. The [rate bridge](rate-bridge-preregistration.md) remains an unimplemented conditional hypothesis. The [conditioning protocol](conditioning-preregistration.md) and [pre-run addendum](conditioning-prerun-addendum.md) were frozen before any conditioning measurements. The addendum makes probe timing, selectivity, controls and call arithmetic explicit; both document hashes belong in the conditioning identity.

## Complete bound reporting and held-out result

Review found that strict clipping counters could miss exact bound contact followed by recovery, and cumulative trials were omitted from the aggregate bound criterion. The [recording-only correction](inclusive-bound-observations.md) includes equality, cumulative observations and the final checkpoint. It also requires explicit counts rather than interpreting missing evidence as zero. Neural dynamics were unchanged.

The new [original panel `29c766f95f82`](panel-diag-candidate-maskgamma-29c766f95f82.json) again passed all seven criteria, with zero bound observations. [All 473 retained arrays and the full archive hash match](original-recording-parity.json) the earlier original result.

The [held-out panel `e3d8898dc68a`](panel-diag-candidate-maskgamma-e3d8898dc68a.json) is complete and source-stable. It uses the remaining eight calibration cues and the separately declared fresh noise. Six criteria passed; the untaught guard failed for home/base: mean −0.515622884, SD 0.979555768, permitted absolute mean 0.489777884. Home/alternate and both away guard cells passed. Cumulative home drift was −5.747775733, within its 13.795605525 relative limit. Zero bound contacts were recorded. The failure remains a failure even though it is close to its threshold.

No conditioning run was launched after this result. The smaller correction is insufficient for qualification; the already frozen rate bridge will be implemented and checked against independent numerical oracles before new circuit panels. The failed raw-event result must remain visible alongside any later candidate.

## Preserved evidence and execution exception

- [Historical diagnostic copies](historical-diagnostic-copies.json) retain the failed earlier results under their original identities.
- [Dated correlation erratum](lag-profile-erratum.json): the historical mean fine-lag cross-correlation peaks at 0.054121782 at +3 ms, rather than the 0.037 stated in the old prose. The weak correlation does not identify a causal anatomical path.
- [Agent reading receipts](agent-document-reading.json) record the complete initial documentation corpus; workers read later changes at review boundaries.
- [QA startup incident](task1-startup-side-effects.json): a default server startup refreshed live sports caches and inserted 81 v1 paper forecasts. The server was stopped. These shared rows are preserved because no pre-start snapshot exists. Historical reward artifacts and the active model pointer remained intact. Subsequent verification requires a read-only, refresh-disabled startup.

No new sports pilot, model promotion or push is part of this repair.
