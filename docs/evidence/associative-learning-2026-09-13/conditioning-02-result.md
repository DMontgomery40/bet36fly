# Conditioning-02: passed every predeclared criterion (independently recomputed)

Identity `associative-conditioning-d1d3992e38c1dfa5fef1`, protocol `configs/associative-conditioning-02.json` (SHA-256 of protocol+circuit bytes in the identity), circuit `associative-circuit-01`, 389 native calls, 263 wall seconds. Cues `cue:E` (A) and `cue:F` (B): unit-gain KC-set Jaccard 0.134; probe seeds 3011–3013; training seed base 20,000; η = 1e-4; 12 exposures per cue; gains bounded [0.5, 1.5].

Entry gate passed: {"kc_recruited": true, "mbon05_responds": true, "ab_overlap_bounded": true, "recovery": true, "generator": true, "nonempty_partitions": true}. Unit probes (MBON05, MBON01 spikes in the 400 ms cue window; seeds × cues A,B): [[[62, 55], [73, 68]], [[61, 50], [71, 66]], [[60, 53], [73, 67]]]. Partition sizes (A-preferring / B-preferring / tied eligible edges): γ4 {'A': 304, 'B': 387, 'tied': 1148}, γ5 {'A': 262, 'B': 349, 'tied': 967}.

## Verdicts

Acquisition: all criteria passed: {"acquisition_response": true, "acquisition_gain": true, "acquisition_target_depressed": true, "frozen_and_lesion_bytes_identical": true, "backward_not_depressing": true, "backward_potentiates_gains": true, "swap_mirror": true, "order_matches_paired": true, "no_loss_of_responsiveness": true, "max_gain_change_bounded": true}. Null response scale 0.0 spikes and null gain scale 0.0 (the unpaired, untaught, frozen and lesion arms changed nothing at all: zero reward-DAN spikes in every cue-only trial, so no endogenous dopamine reached the γ4/γ5 compartments with these cues). Retention passed. Reversal passed: {"parent_preference_negative": true, "erasure_flips_preference": true, "erasure_recovers_a": true, "erasure_depresses_b": true, "frozen_retention_bytes_identical": true}. Audit: no bound contacts, no recovery failures, no generator failures, no probe changed a gain.

## Measured responses relative to unit probes (three fresh seeds; readout = MBON05 + MBON01 summed for criteria, shown separately here)

| Arm | MBON05 ΔA | MBON05 ΔB | MBON01 ΔA | MBON01 ΔB | summed contrast ΔA−ΔB | γ4 A-edge mean Δgain | γ4 B-edge mean Δgain | changed edges | max |Δgain| |
|---|---|---|---|---|---|---|---|---|---|
| paired | [-4, -4, -1] | [-1, 1, -1] | [-10, -2, -10] | [-1, 0, -3] | [-12, -7, -7] | -0.0775 | -0.0090 | 699 | 0.225 |
| unpaired | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | +0.0000 | +0.0000 | 0 | 0.000 |
| backward | [2, 5, 5] | [-1, 4, 0] | [4, 10, 7] | [-1, -1, 1] | [8, 12, 11] | +0.0762 | +0.0088 | 697 | 0.221 |
| untaught | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | +0.0000 | +0.0000 | 0 | 0.000 |
| frozen | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | +0.0000 | +0.0000 | 0 | 0.000 |
| lesion | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | +0.0000 | +0.0000 | 0 | 0.000 |
| swap | [-3, -1, 1] | [-6, -1, -4] | [-4, 4, 0] | [-9, -6, -8] | [8, 10, 13] | -0.0087 | -0.0850 | 883 | 0.201 |
| order | [-2, -4, -1] | [0, 3, -1] | [-10, -3, -8] | [-2, 0, -3] | [-10, -10, -5] | -0.0768 | -0.0091 | 688 | 0.225 |

## Reversal from the paired checkpoint (24 trials per branch; moves relative to the paired endpoint, summed readout)

| Branch | A move | B move | A−B preference vs unit | γ4 A-edge Δgain from parent | γ4 B-edge Δgain from parent | bytes identical to parent |
|---|---|---|---|---|---|---|
| contingency-swap | [-1, -5, 3] | [-16, -15, -12] | [3, 3, 8] | -0.0088 | -0.0873 | False |
| backward-erasure-plus-swap | [8, 5, 13] | [-10, -10, -8] | [6, 8, 14] | +0.0664 | -0.0781 | False |
| untaught-exposure | [0, 0, 0] | [0, 0, 0] | [-12, -7, -7] | +0.0000 | +0.0000 | True |
| frozen-retention | [0, 0, 0] | [0, 0, 0] | [-12, -7, -7] | +0.0000 | +0.0000 | True |

Contingency swap (descriptive, no extinction mechanism implemented): B depressed True, A unchanged False (A moved by [-1, -5, +3] spikes, within seed noise, with a γ4 A-edge change of −0.009 from overlap with B-active KCs).

## What this establishes and what it does not

- Established in this simulator: cue activity leaves KC eligibility; dopamine delivered afterwards depresses exactly the eligible KC→MBON05/MBON01 synapses (lesion of the dopamine→plasticity coupling with identical drive changes nothing); the depressed synapses reduce the same cue's MBON05/MBON01 response on fresh seeds; the change survives five seconds of plasticity-on silence; dopamine before the cue potentiates (backward arm); rewarding the other cue depresses the other cue (swap); presentation order does not matter; a backward-then-forward reversal recovers A, depresses B and flips the preference.
- Not established: natural sugar reward (the reinforcer is an engineered optogenetic-style drive of PAM08/PAM01, because sweet taste does not reach any dopamine neuron at this coupling), feeding, innate choice, memory decay or extinction, receptor-level mechanism, and any sports usefulness (separate stage).
- Reproducibility: every one of the 389 calls has its counts, sampled traces, drive events, compartment rule bins, traces and gains saved; `scripts/audit_associative_conditioning.py` recomputed every probe response, KC count digest, gain hash chain, partition, and all verdicts from those artifacts and agreed with the stored manifest (all_agree=True).
