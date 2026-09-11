# V2 development evidence — September 11, 2026

This summary preserves aggregate results from local, frozen experiments. [The accompanying JSON](v2-development-summary.json) contains every decoder setting, all 180 feature configuration/C aggregates, solver accounting, matched-bookmaker comparisons and SHA256 hashes of the original reports. It contains no credentials, machine-specific absolute paths, raw bookmaker payloads or per-game predictions. Full data and reports remain local and are not distributed with the repository; this summary alone is not an independently reproducible dataset.

## Experiment state

The retained experiment is `v2-24a83145c27ab220116e`: 13 completed runs, eight cancelled runs and three paused unfinished runs. The original 24-run design is incomplete and no architecture has all three seeds. V1 remains active; no v2 shadow candidate was activated. See [the protocol and execution requirements](../EXPERIMENT_V2.md).

The frozen training/validation counts are 760/186 soccer games and 3,687/1,165 baseball games. The later historical development period was not used in these diagnostics. Existing validation results had already influenced development, so none of the scores below constitutes independent confirmation.

## Decoder diagnostics

Both representations use the same saved biological frozen seed-42 activity from four 20 ms windows. Whole uses `log1p(mean(raw rates))`, with 124 channels; temporal uses window-first `log1p(raw rates)`, with 496. Scaling is fitted on training rows only, with the original floor and clipping unchanged. The first grid was C = 0.01, 0.1, 1.0. The bounded extension used C = 0.00001, 0.0001, 0.001, 0.01, after reproducing all four C=0.01 references within 0.000001. All 16 extension fits converged without captured warnings.

| Predictor | Soccer validation log loss | Baseball validation log loss |
|---|---:|---:|
| Saved feature logistic | 0.962021 | 0.682923 |
| Selected frozen whole readout | 1.011525 | 0.688307 |
| Selected frozen temporal readout | 1.002819 | 0.687752 |
| Saved training-frequency prior | 1.056507 | 0.690260 |

Both soccer readouts selected C=0.001 and both baseball readouts selected C=0.0001 on validation. Stronger regularization removed the earlier temporal disadvantage in this bounded comparison. It did not establish the cause of earlier failures, a topology advantage or an improved biological learning mechanism. No neural activity was resimulated and no model was promoted.

## MLB bookmaker comparison

Exact ordered-team and scheduled-UTC matching yielded 1,161 potential Bet365 opening quotes among the 1,165 validation fixtures. Two invalid 0/0 American moneylines were excluded. All predictors below use the same 1,159 games. Outcomes were not used to resolve fixture identity.

| Predictor | Log loss | Brier score |
|---|---:|---:|
| Bet365 opening, proportionally de-vigged | 0.680574 | 0.487886 |
| Saved feature logistic | 0.682797 | 0.489874 |
| Frozen temporal readout | 0.687661 | 0.494555 |
| Frozen whole readout | 0.688220 | 0.495087 |
| Saved frequency prior | 0.690029 | 0.496884 |

Lower scores are better. Bet365 had the lowest log loss and Brier point estimates. All four model-minus-book weekly bootstrap intervals include zero; this establishes neither superiority nor equivalence.

The source is [Sportsbook Review's archived MLB odds](https://www.sportsbookreview.com/betting-odds/mlb-baseball/?date=2025-07-01), using its Bet365 `openingLine` fields. SBR supplies no actual opening-quote timestamp, so the model's information set cannot be aligned to that time. Its `currentLine` was not treated as closing. These scores do not establish executable prices, a contemporaneous betting edge or profit. Paid Odds-API.io access was not used for this comparison.

## Feature sweep

Thirty configurations crossed form windows 3/5/10/20/40, pooled versus home/away-specific histories, and absent/capped/nonlinear rest. Each was tested at six C values across five chronological folds entirely inside the original training partition. All 900 fold fits converged. Configuration selection never used the original validation outcomes.

Training-fold selection chose 10-game pooled form, capped rest and C=0.001. The final fit withheld 21 original training labels under the conservative 48-hour plus UTC-day availability rule, leaving 3,666 fit rows. Its log loss was 0.684507 on all 1,165 validation games and 0.684327 on the matched 1,159-game bookmaker intersection. It did not improve the saved feature baseline or beat Bet365 in point estimate. All paired weekly intervals include zero.

The changed training embargo and selection method mean this is not an isolated test of changing five-game form to ten-game form. The classifier and scaler stayed frozen through validation; earlier validation outcomes updated feature history only after the declared delay. Weather and probable starters were absent from this frozen source and were not added. This was a conventional feature-model study, not a fly simulation or reinforcement-learning experiment.

## Verification scope

The combined implementation passed 260 Python tests, Ruff, 49 frontend tests and a production build. Earlier desktop/mobile journeys verified the local anatomy/registry workflows; their full screenshots and browser JSON remain local, so they are not presented here as independently reproduced evidence. No browser inference, full-brain simulation, gain fitting, matrix resume or model activation was performed for the decoder, bookmaker or feature diagnostics. Software checks do not establish predictive superiority.
