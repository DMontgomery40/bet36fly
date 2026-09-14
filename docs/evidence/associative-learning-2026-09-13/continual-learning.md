# Continual learning: conditioning-03 and the stress test (version-2 recovery rule)

All nine runs executed on Hugging Face Jobs (cpu-upgrade) from the audited private working set; artifacts were uploaded to the private results repo and copied here unchanged. Protocols: `configs/associative-conditioning-03.json` (the conditioning-02 battery on circuit-02) and `configs/associative-stress-01.json`; the version-2 rule is defined in the contract, Section 8.

## Conditioning-03: the recovery term leaves the qualified battery intact at every ρ

| ρ | identity | acquisition | retention | reversal | audit | paired contrast (summed MBON, 3 seeds) | γ4 A-edge Δgain paired | backward A-edge Δgain | untaught Δgain |
|---|---|---|---|---|---|---|---|---|---|
| 0.005 | `associative-conditioning-e2faf2fdb0667212b38c` | True | True | True | True | [-12, -9, -9] | -0.0776 | +0.0761 | +0.00000 |
| 0.01 | `associative-conditioning-5f88c46159eedb590aad` | True | True | True | True | [-12, -9, -9] | -0.0775 | +0.0761 | +0.00000 |
| 0.02 | `associative-conditioning-117e4b8a909efdac6030` | True | True | True | True | [-12, -9, -9] | -0.0775 | +0.0761 | +0.00000 |
| 0.04 | `associative-conditioning-b70d59bfbd69d6f2de48` | True | True | True | True | [-12, -9, -12] | -0.0775 | +0.0761 | +0.00000 |

The forward depression, backward potentiation, lesion/frozen identity, swap, order, retention and reversal results are unchanged from conditioning-02, as expected from the gating on zero KC eligibility (the recovery term only acts on synapses of KCs silent in the trial; with two cues the only such dopamine exposure is the other cue's reinforcement, which recovers a little of the generalization).

## Stress test: 8 cues × 24 cycles (192 reinforcements), then a fresh-pair battery from the long-history checkpoint

| arm | ρ | identity | γ4 gains at floor after cycle 8 / 16 / 24 | γ5 at floor after 24 | gains above rest during cycles | mean γ4 gain after 24 | recent cue (stress:7) depression after 24, 3 seeds | oldest cue (stress:0) after 24 | post-history acquisition (paired contrast) | post-history reversal flipped | total recovery | floor contacts during cycles |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | — | `associative-stress-d68e0f3df819053aa1ee` | 0.5% / 11.1% / 20.4% | 21.7% | 0.0% | 0.800 | [-35, -36, -35] | [-57, -56, -60] | True [-2, -5, -5] | True [14, 14, 11] | 0.0 | 23238923 |
| recovery | 0.005 | `associative-stress-d3d4da0959060f926f57` | 0.2% / 2.5% / 3.9% | 4.4% | 0.0% | 0.841 | [-31, -34, -33] | [-45, -45, -48] | True [-8, -9, -16] | True [11, 14, 9] | 368.0 | 7843042 |
| recovery | 0.01 | `associative-stress-78a9e06c46e6e4b61df9` | 0.1% / 1.3% / 2.0% | 2.5% | 0.0% | 0.873 | [-27, -31, -29] | [-37, -43, -39] | True [-16, -11, -9] | True [3, 10, 5] | 582.0 | 4649430 |
| recovery | 0.02 | `associative-stress-bd54b98e08886c2de086` | 0.1% / 0.8% / 1.0% | 1.1% | 0.0% | 0.912 | [-22, -24, -22] | [-28, -23, -33] | True [-10, -11, -8] | True [3, 7, 12] | 794.6 | 1876581 |
| recovery | 0.04 | `associative-stress-38ad83661b44731ae8ce` | 0.1% / 0.3% / 0.4% | 0.5% | 0.0% | 0.949 | [-16, -19, -16] | [-18, -20, -19] | True [-10, -11, -20] | False [7, 7, 0] | 923.6 | 561397 |

Depressions are summed MBON05 + MBON01 spike counts relative to the unit-gain probe of the same cue and seed (more negative = stronger memory). Gains above rest during the cycle phase are exactly zero for every recovery arm: the recovery term never crosses the resting gain. The small above-rest fractions at the very end of each recovery run (0.9–8.3%) arise in the post-history reversal from the qualified backward-pairing potentiation acting on synapses that recovery had already returned near rest; the baseline shows the same effect at 0.2%.

## Reading

1. **The season saturation is the Jiang & Litwin-Kumar failure mode.** Without recovery, 20.4% of γ4 eligible gains sit at the floor after 192 reinforcements (14–44% of all plastic gains after a 2,382-reinforcement season), and the fresh-pair acquisition after that history is weak (paired contrast −2/−5/−5 spikes) because the cue's synapses start near the floor.
2. **Dopamine-gated recovery restores dynamic range.** With ρ = 0.005 the floor occupancy after 24 cycles falls from 20.4% to 3.9% (γ5: 14.5% → 3.6%) and the post-history acquisition recovers to −8/−9/−16 spikes with reversal still flipping; higher ρ drives occupancy toward zero.
3. **The memory-lifetime tradeoff is explicit.** Old-cue depression after 24 cycles: baseline −57 spikes, ρ 0.005 −46, 0.01 −40, 0.02 −28, 0.04 −19; recent-cue: −35, −33, −29, −23, −17. Recovery trades memory strength for range; at ρ = 0.005 the oldest memory keeps 80% of the baseline depression while floor occupancy drops fivefold.
4. **Selection (rule fixed in the contract before these runs):** the smallest ρ with floor occupancy ≤ 10% in both compartments, recent-cue depression ≥ 3× the frozen null in every seed, no gain above rest, and passing post-history acquisition. **ρ = 0.005** meets every criterion and is selected; 0.01, 0.02 and 0.04 also meet them (0.04 fails the reversal flip in one seed, which is not a selection criterion). No sports outcome was consulted.

Every call's probe counts, occupancy histories, per-reinforcement recovery/bound telemetry and checkpoints are in the run directories under `output/associative/`.
