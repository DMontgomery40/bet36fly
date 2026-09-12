# Controlled acquisition and reversal preregistration

Frozen before any new conditioning result, September 12, 2026 UTC. This protocol is a proposed engineered test, not measured fly behavior. Source-grounded constraints and the selected learning-rule contract are in [the rate-bridge preregistration](rate-bridge-preregistration.md); the confirmed timing defect is in [the refractory contract](../reward-refractory-contract-2026-09-12.md). The underlying cell gains and encoder remain fixed. No sports pilot or probability/readout fitting is part of this test.


Use a new experiment kind and version, for example `dopamine-conditioning` schema 1. Do not reuse the sports schema-5 identity. The manifest must name the exact rule/kernel identity that has already passed the mechanism gates; corrected raw-event and `rate-bridge-v1` results may never share an identity.

### Entry gate

No full-CNS acquisition begins unless all of the following are true:

1. The refractory-delivery fix passes its independent unit/oracle tests under a new identity while all historical raw/tonic assertions remain unchanged under their named modes.
2. The exact original 8 cues × 2 seed sets × frozen/untaught/home/away panel passes every frozen v1.1 criterion, including SCI-001, without retuning.
3. The remaining calibration cues with a predeclared fresh-noise seed set pass the held-out mechanism panel from the rate-bridge preregistration.
4. The selected rule has a non-vanishing long-lag functional effect, no unexplained tail, and the gamma-only away mask audit is exact.

If any item fails, preserve the result and stop. Do not run acquisition descriptively under the same identity.

### Outcome-blind cue lock

Use fixed standardized feature vectors at the existing encoder centers. This avoids selecting a historical game by its downstream response or taught outcome and makes the conditioning identity independent of sports labels:

- primary A: all 16 features = −1.5;
- primary B: all 16 features = +1.5;
- challenge C: features alternate −1.5, +1.5 starting with −1.5;
- challenge D: the exact sign inverse of C.

The primary pair maximally separates low/high glomerular identities. The sign-alternating challenge uses the same values and equal numbers of low/high feature assignments, so a primary result is not accepted as a general cue result by itself. Encode these vectors with the unchanged saved 64-glomerulus/275-port map, width 0.5, 150 Hz peak and 5% floor. Save the vectors, encoded-rate hashes and total scheduled rates before any neural result. No sports outcome enters selection or scoring.

### Acquisition schedule

Run two independently initialized training seed panels with offsets 0 and 1,000,000. In each panel, every arm starts from byte-identical unit gains and uses six repetitions of cue order `A B B A` (24 cue exposures, 12 per cue). For cycle `i`, use cue-trial seed `42 + panel_offset + 2*i` and blank-trial seed one larger. Every arm executes the same two 400 ms electrical trials per cycle, so reset boundaries and exposure counts match. Run the primary A/B family first; run the C/D challenge only if A/B passes every acquisition criterion:

1. Cue trial: the selected cue is present for 0–300 ms.
2. Blank companion trial: no sensory drive.

Teaching remains four pulses at 310, 330, 350 and 370 ms; all other accepted timing, gains and mapping stay fixed. Arms:

| Arm | Cue trial | Blank companion | Plasticity |
| --- | --- | --- | --- |
| paired | A→home, B→away | no pulses | on in both |
| shuffled | repeated block labels `home, home, away, away` against cue order `A,B,B,A`, giving each cue 6 home and 6 away pairings | no pulses | on in both |
| timing-unpaired | no pulses | true A→home/B→away pulses | on in both |
| untaught | no pulses | no pulses | on in both |
| frozen | no pulses | no pulses | off in both |

The timing-unpaired arm uses the same resets as every other arm; its pulse trial contains no cue eligibility. Shuffled remains a separate label-correspondence control. Untaught measures endogenous/exposure plasticity. Frozen must have neither teaching nor plasticity.

Before training, after blocks 2 and 4, and at the endpoint, clone each checkpoint and probe both cues with teaching off and plasticity off. Use one fixed nontraining seed for each interim curve point. Training-noise replay proves determinism; pre/end independent generalization uses four fresh common-randomness seeds `2,000,042 + k`, `k=0..3`, never used in training. The blank-gain pre-probe is shared across arms; every arm receives its own endpoint probe. Assert probe gains are byte-identical before/after.

The whole conditioning program has a hard ceiling of 1,600 full-engine calls and 1,200 wall seconds. The complete planned matrix is 1,576 calls: 1,216 for both acquisition cue families including probes, and 360 for primary-pair reversal including probes. An over-budget stage is `budget_stopped`, never partial success. If primary acquisition fails, stop before C/D and reversal. If C/D fails, stop before reversal. These stop rules are predeclared and the unrun stages remain explicitly `not_run_gate_failed`.

### Acquisition measurements

The primary measurement is raw mean firing of the selected MBON population during the cue window, not a centered probability or refitted decoder. Also retain KC spike counts and the full eligible gain vector.

From the pretraining fresh probes, partition eligible edges by the sign of the presynaptic KC's mean spike-count contrast A−B: A-preferred (>0), B-preferred (<0), and tied/shared (=0). Report counts, between-cue KC Jaccard, same-cue fresh-noise stability and whether both preferred sets are nonempty.

For home, define response selectivity `C_home = ΔMBON11(A) − ΔMBON11(B)`; for away, `C_away = ΔMBON09(B) − ΔMBON09(A)`. Negative is the expected cue-selective depression. Define analogous target-preferred-minus-other-preferred gain contrasts within home-all and away-gamma eligible edges.

Apply the identical definitions to C→home and D→away in the challenge family. A/B and C/D are separate required results; do not pool them into an average that can hide a failed family.

Acquisition fails if any of these predeclared conditions fails:

1. Identity, row, arm, seed, schedule or checkpoint matrix is incomplete; any result is non-finite; any gain clips/hits a bound; or a frozen/probe gain byte changes.
2. Between-cue active-KC Jaccard exceeds the existing 0.5 guard in either seed panel, either cue-preferred eligible set is empty, or same-cue fresh-noise stability is no better than between-cue similarity.
3. In either training seed panel, paired `C_home` or `C_away` is not negative, or the corresponding paired gain-selectivity contrast is not negative.
4. For either channel/seed panel, the magnitude of paired selectivity is less than three times the maximum magnitude in shuffled, timing-unpaired, untaught and frozen-repeat error. This reuses the existing frozen 3× teaching-specific standard rather than fitting a new threshold to the result.
5. Any of the four fresh-noise probe contrasts has the wrong sign for either channel, or the mean effect is not finite and above both numerical replay error and frozen response error.
6. A common decrease in both cues explains the result: target-versus-other-cue MBON and target-preferred-versus-other-preferred gain differences must both pass. Gain movement alone or decoder probability movement cannot pass acquisition.

### Reversal from acquired gains

For each successful paired acquisition panel, save and hash the acquired gains. Clone that exact array, not unit gains, into five reversal branches. Every branch must record `parent_checkpoint_sha256`; reject a branch whose initial gains do not byte-match the acquired parent.

Use six ABBA blocks again (12 presentations per cue). Version the reversal electrical trial at 800 ms for every branch: onset remains 100 ms; a pre-cue pulse train can occur at 110/130/150/170 ms; the 300 ms cue occurs at 300–600 ms; post-cue trains occur at 610/630/650/670 and, where needed, 690/710/730/750 ms. Use new common seeds with panel offsets 3,000,000 and 4,000,000. Branches:

| Branch | A schedule | B schedule | What it tests |
| --- | --- | --- | --- |
| continued-acquisition | home twice after cue | away twice after cue | old association retention/deepening with eight DAN pulses |
| ordinary-contingency-swap | away twice after cue | home twice after cue | whether adding the new channel changes preference; it is not erasure by itself |
| backward-erasure-plus-swap | home before + away after | away before + home after | old-channel recovery plus new association with matched eight DAN pulses |
| untaught-exposure | no pulses | no pulses | drift from continued exposure, plasticity on |
| frozen-retention | no pulses | no pulses | response/noise retention, plasticity off |

All branches use the same cue window, duration, order, seeds and reset contract. The three taught branches have matched pulse counts; untaught/frozen intentionally have none. Probe the parent, blocks 2 and 4 with one nontraining curve seed, and the endpoint with four fresh common seeds starting at 5,000,042, teaching/plasticity off.

Strict reversal passes only if, in both training panels and every fresh-noise probe set:

1. The old depressed response actually recovers: MBON11(A) and MBON09(B) move toward their pre-acquisition baselines, and their absolute baseline errors become smaller than at the acquired parent.
2. The old stored gains actually recover: A-preferred home gains and B-preferred away-gamma gains move toward unit gain and become closer to unit than at the parent. Response recovery without old-weight recovery and old-weight recovery without response recovery both fail strict reversal.
3. Each recovery movement has the correct sign and is at least 3× the corresponding untaught-exposure movement and frozen replay error.
4. New cue associations also pass the acquisition response and gain-selectivity criteria for A→away and B→home.
5. The response preference flips from the acquired mapping to the changed mapping; continued-acquisition retains the original direction; frozen retains the acquired gains byte-for-byte; no branch clips.

If ordinary-contingency-swap flips the response while old responses/gains remain depressed, report **dual-channel preference remapping without erasure**. Do not call it reversal. Only the backward-erasure-plus-swap branch can satisfy the strict erasure criterion above. Resetting gains to one, depressing only a new channel, or showing an analytic gain effect without an actual MBON response change fails.

