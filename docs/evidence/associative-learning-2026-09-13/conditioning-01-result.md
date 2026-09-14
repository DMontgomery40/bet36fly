# Conditioning-01: failed under its predeclared criteria (preserved)

Identity `associative-conditioning-42845736c62d3ac9841e`, protocol `configs/associative-conditioning-01.json`, circuit `associative-circuit-01`, 389 native calls, 255 wall seconds, cues `cue:A`/`cue:B` (unit-gain KC-set Jaccard 0.389), probe seeds 3001–3003, η = 1e-4, 12 exposures per cue.

Entry gate passed: {"kc_recruited": true, "mbon05_responds": true, "ab_overlap_bounded": true, "recovery": true, "generator": true, "nonempty_partitions": true}. Unit probes (MBON05, MBON01 spikes in the 400 ms cue window; seeds × cues): [[[90, 85], [80, 74]], [[90, 84], [84, 75]], [[90, 86], [86, 74]]].

## Verdict under the predeclared criteria

Acquisition criteria: {"acquisition_response": false, "acquisition_gain": false, "acquisition_target_depressed": true, "frozen_and_lesion_bytes_identical": true, "backward_not_depressing": true, "swap_mirror": false, "order_matches_paired": false, "no_loss_of_responsiveness": true, "max_gain_change_bounded": true}. Null response scale 1.000 spikes, null gain scale 0.0503 (dominated by the backward arm), untaught total |Δgain| 0.4075. Retention passed (gains byte-identical after five plasticity-on blank trials; probes identical). Reversal failed at its entry gate (`parent_preference_negative` false: MBON05 contrast [−4, 0, −2]). Audit passed: no bound contacts, no recovery failures, no generator failures, no probe changed a gain; reward-DAN spikes in cue-only training trials 1,875 (≈14 per trial, 1.3% of one reinforcer trial).

## Measured responses relative to unit probes (three fresh seeds)

| Arm | MBON05 ΔA | MBON05 ΔB | MBON01 ΔA | MBON01 ΔB | A-edge mean Δgain (γ4) | B-edge mean Δgain (γ4) | changed edges | max |Δgain| |
|---|---|---|---|---|---|---|---|---|
| paired | [-4, -7, -8] | [0, -7, -6] | [-9, -8, -11] | [-2, -5, -3] | -0.0886 | -0.0349 | 1401 | 0.218 |
| unpaired | [1, 0, 0] | [0, 0, -1] | [-2, 1, -3] | [0, 0, 0] | -0.0003 | -0.0001 | 1388 | 0.001 |
| backward | [5, 5, 5] | [9, 3, 0] | [6, 5, 2] | [5, 2, 6] | +0.0824 | +0.0320 | 1377 | 0.208 |
| untaught | [1, 0, 0] | [0, 0, -1] | [-2, 1, -3] | [0, 0, 0] | -0.0003 | -0.0001 | 1388 | 0.001 |
| frozen | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | +0.0000 | +0.0000 | 0 | 0.000 |
| lesion | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | +0.0000 | +0.0000 | 0 | 0.000 |
| swap | [-2, -4, -5] | [-2, -7, -8] | [-4, -4, -6] | [-7, -8, -9] | -0.0303 | -0.0989 | 1553 | 0.229 |
| order | [-4, -5, -4] | [-1, -2, -6] | [-10, -10, -11] | [-5, -6, -4] | -0.0876 | -0.0346 | 1381 | 0.215 |

Reversal branches from the paired checkpoint (MBON01 ΔA / ΔB relative to unit): contingency-swap: [-18, -14, -16] / [-14, -14, -15], A-edge Δgain -0.0305, B-edge -0.0988; backward-erasure-plus-swap: [-6, -5, -7] / [-9, -8, -12], A-edge Δgain +0.0537, B-edge -0.0655; untaught-exposure: [-10, -8, -9] / [-4, -5, -5], A-edge Δgain -0.0004, B-edge -0.0002; frozen-retention: [-9, -8, -11] / [-2, -5, -3], A-edge Δgain +0.0000, B-edge +0.0000.

## Diagnosis

1. The mechanism acts as declared at the synapse level: paired A-edge depression −0.089 (mean) against untaught −0.0003, lesion 0 and frozen 0; backward pairing potentiates (+0.082); swap depresses B-edges (−0.099) more than A-edges (−0.030); order matches paired (−0.088).
2. The response readout declared as primary (MBON05 alone) moves by only 2–8 spikes of ~90 while fresh-seed noise is ±2–3 spikes; MBON01, measured afterwards to be twice as sensitive per unit gain, shows the effect clearly (paired ΔA −9/−8/−11 versus unpaired −2/+1/−3, backward +6/+5/+2). Choosing the readout after the fact is not allowed for this identity, so the run stays failed.
3. Treating the backward arm as a null was a design error: its predicted, opposite-sign potentiation set the gain null scale (0.050) to the size of the paired effect (0.054) and masked it.
4. cue:A and cue:B share 39% of their active KCs; B was depressed by roughly a third of A's effect whenever A was reinforced (generalization), which shrinks the selective contrast.
5. Endogenous PAM01/PAM08 activity under cue-only exposure is small (≈14 spikes per 1 s trial) and produced negligible untaught drift (max |Δgain| 0.0012).

Conditioning-02 (`configs/associative-conditioning-02.json`) predeclares the corrections before running: summed learned-MBON readout justified by the independent sensitivity measurement, the backward arm as a directional control, a low-overlap cue pair chosen on unit gains, fresh probe and training seeds. Nothing in the circuit, rule, η, bounds, timing or exposure count changes.
