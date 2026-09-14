# Sports development, no-homeostasis baseline (2022, circuit-01)

Protocol `configs/associative-sports-01.json`: 2022 MLB regular season (2,429 eligible games), identical frozen encoder and innate response cache for every arm, team odors (16-type code), winner cue + reinforcer applied only after the 48-hour/UTC-day availability rule, prediction probes with plasticity off (cached per exact gain hash). Readouts (L2 logistic, C = 0.01, no intercept, fixed procedure for every arm) fitted on the games before July 1, 2022 and evaluated on the rest. Three declared learning rates; the arms were finished and scored exactly as frozen after the saturation was noticed. Uncertainty: 10,000 paired complete-ISO-week bootstrap resamples, seed 20260913.

Training games 1137, evaluation games 1292.

| η | plastic accuracy / log loss | frozen | shuffled | encoder only | same information | plastic − frozen (95%) | plastic − encoder (95%) | plasticity contributes | better than chance |
|---|---|---|---|---|---|---|---|---|---|
| 2e-05 | 59.21% / 0.67538 | 0.67385 | 0.67528 | 0.66885 | 0.67553 | +0.00153 [-0.00128, +0.00417] | +0.00654 [+0.00109, +0.01220] | False | True |
| 4e-05 | 59.06% / 0.67490 | 0.67385 | 0.67524 | 0.66885 | 0.67553 | +0.00105 [-0.00080, +0.00288] | +0.00605 [+0.00129, +0.01126] | False | True |
| 1e-05 | 58.59% / 0.67556 | 0.67385 | 0.67496 | 0.66885 | 0.67553 | +0.00171 [-0.00083, +0.00391] | +0.00671 [+0.00125, +0.01229] | False | True |

**Reading.** Every plastic arm beats uniform chance and the training prior (accuracy interval lower bounds 56.5–56.8%), but none beats its matched frozen twin (the plastic − frozen intervals all include zero and the point estimates are worse), and every plastic pipeline is **worse than the encoder alone** by about 0.006–0.007 log loss with intervals entirely above zero. The reinforcement-shuffled twins score the same as the true-outcome arms. On this development block, dopamine plasticity without homeostasis adds no predictive information; the learned features carry team-identity noise that the readout cannot separate from the innate quality signal.

## Season-long saturation (matches the Jiang & Litwin-Kumar bounded-weight failure)

| arm / η | first UTC day with a lower-bound contact | fraction of the 4,108 plastic edges at the 0.5 floor at season end | gain deciles at season end (min, 10%, 25%, 50%, 75%, 90%, max) |
|---|---|---|---|
| plastic|4e-05 | 2022-04-22 | 0.439 | [0.5, 0.5, 0.5, 0.681, 1.0, 1.0, 1.0] |
| plastic|2e-05 | 2022-05-03 | 0.319 | [0.5, 0.5, 0.5, 0.842, 1.0, 1.0, 1.0] |
| shuffled|1e-05 | 2022-05-25 | 0.139 | [0.5, 0.5, 0.67, 0.924, 1.0, 1.0, 1.0] |
| plastic|1e-05 | 2022-05-27 | 0.144 | [0.5, 0.5, 0.666, 0.922, 1.0, 1.0, 1.0] |
| shuffled|2e-05 | 2022-05-03 | 0.318 | [0.5, 0.5, 0.5, 0.844, 1.0, 1.0, 1.0] |
| shuffled|4e-05 | 2022-04-22 | 0.441 | [0.5, 0.5, 0.5, 0.683, 1.0, 1.0, 1.0] |

The floor occupancy grows monotonically with η and with the number of reinforcements (per-day checkpoints are the trajectory in [`sports-development-baseline.json`](sports-development-baseline.json)). With no upward force except the rare backward-timing potentiation, every synapse of a KC that is active for any reinforced team's odor ratchets down until it hits the bound; by September the median eligible gain is 0.68–0.92 and a quarter to a half of all plastic edges sit exactly at 0.5. This is the failure mode JLK describe for long association sequences with bounded weights, quantitatively: 191 reinforcements per team-odor family over the season versus the 12 pairings of the conditioning battery. The remedy they propose and test (Eq. 5, non-specific dopamine-gated potentiation) is the version-2 rule declared in the contract, Section 8.

Evaluation identities: η=2e-05: `associative-sports-evaluation-598315dd5d972e2c351d`, η=4e-05: `associative-sports-evaluation-519a45872fdd88cf567b`, η=1e-05: `associative-sports-evaluation-7dca9f2ee7292c49a8bc`. No 2018 access; the reserved block stays untouched for the final candidate.
