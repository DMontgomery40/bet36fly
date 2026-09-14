# 2018 confirmation of the frozen recovery candidate: better than chance, no contribution from plasticity

Identity `associative-confirmation-662fc9e1bd5d450aba64`, protocol `configs/associative-confirmation-01.json` (attempt 1 of 1), candidate `configs/associative-candidate-01.json` (SHA-256 34b8177d4539d31d…, η = 4e-5, circuit-02 with ρ = 0.005, readouts fitted on 2022 only). Source: `https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameType=R&season=2018`, fetched 2026-09-14T04:02:12.384720+00:00 (SHA-256 1e4f07f54161e93b…), 2429 eligible regular-season games from 2018-03-29 to 2018-10-01; excluded {'unplayed': 54, 'resumed_or_suspended': 4}. The whole run executed as one Hugging Face job after the candidate was committed (de5cd7c); no parameter was changed and nothing was refitted. Every arm ran the full season chronologically under the 48-hour/UTC-day rule: recovery plastic (6,500 calls, 2,388 reinforcements), frozen twin (30 calls), reinforcement-shuffled twin (6,500 calls), and the no-recovery circuit-01 plastic baseline at the same η (6,500 calls).

## Result (10,000 paired complete-ISO-week resamples, seed 20260913, α = 0.025)

| Arm | Accuracy / log loss | plastic − arm (negative favours plastic) |
|---|---|---|
| recovery plastic (candidate) | 56.98% / 0.678718 | — |
| frozen twin | 56.57% / 0.678014 | +0.000704 [+0.000096, +0.001368] |
| reinforcement-shuffled twin | 56.77% / 0.678966 | -0.000248 [-0.000622, +0.000125] |
| no-recovery plastic baseline (circuit-01, η 4e-5) | 56.61% / 0.679097 | -0.000380 [-0.000939, +0.000182] |
| encoder only | 57.18% / 0.674228 | +0.004490 [+0.001288, +0.007607] |
| same-information conventional | 56.61% / 0.677262 | +0.001456 [-0.004359, +0.007247] |
| training prior | 52.74% / 0.691824 | -0.013106 [-0.019325, -0.006826] |
| uniform chance | 52.74% / 0.693147 | -0.014429 [-0.021275, -0.007575] |

Accuracy interval of the candidate: 54.70–59.10%. Shuffled − frozen: +0.000952 [+0.000084, +0.001848]. Baseline − frozen: +0.001084 [+0.000131, +0.002059].

## Verdict

- **Better than chance:** yes. The candidate beats uniform chance and the training prior with both intervals entirely below zero, and its accuracy interval excludes 50%.
- **Plasticity contributes:** **no.** The recovery circuit is reliably *worse* than its matched frozen twin (interval entirely above zero), indistinguishable from the reinforcement-shuffled twin and from the no-recovery baseline, and reliably worse than the encoder alone. The shuffled and baseline arms are likewise worse than frozen. Dopamine-gated learning of team value, with or without homeostatic recovery, adds noise rather than information to this readout.
- **Recovery mechanism:** it did what it was built for (season-end floor occupancy 0.9% versus 44% in the baseline arm at the same η, no gain above rest) without helping prediction.
- The 2018 block is now spent; `configs/associative-confirmation-01.json` may never be rerun. The frozen 2023 sensory confirmation remains the product's only qualified sports result.

Independent recomputation: every stored accuracy and log loss was recomputed from `predictions.csv` (2,429 unique rows) and all four artifact hashes in the manifest matched (see the session log in the evidence index).
