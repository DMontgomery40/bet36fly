# BET36FLY passed the predefined backtest goal

The frozen sensory pipeline achieved **56.21% accuracy: 1,362 correct out of 2,423 eligible 2023 MLB regular-season games**. The 95% paired-week bootstrap interval was **54.42–58.02%**, above 50% chance. Log loss beat both uniform chance and the training-frequency prior with the predeclared confidence bounds. The goal is complete for this conditional historical backtest; further tuning stopped.

## Confirmation results

| Pipeline / baseline | Accuracy | Log loss | Brier |
|---|---:|---:|---:|
| Complete sensory pipeline |56.21%|0.680493|0.243765|
| Encoder only |55.84%|0.681353|0.244165|
| Independently selected same-information baseline |56.29%|0.681467|0.244228|
| Training-frequency prior |52.13%|0.692725|0.249788|
| Uniform probability / silenced circuit |52.13%*|0.693147|0.250000|

*At probability 0.5 the fixed tie rule picks home, producing always-home accuracy. Random binary guessing has expected accuracy 50%; chance log loss is ln 2. All methods use the same 2,423 games.

Positive values below mean lower loss for the complete sensory pipeline. Intervals use 10,000 resamples of complete ISO weeks, 27 observed blocks, seed 20260913. The original one-sided alpha 0.025 acceptance requires a lower accuracy bound above 0.5 and positive lower improvement bounds against both chance and the training prior.

| Comparator | Log-loss improvement |95% interval |
|---|---:|---:|
| Uniform chance |0.012654|0.006125 to 0.019307|
| Training prior |0.012232|0.006311 to 0.018245|
| Encoder only |0.000860|−0.000510 to 0.002273|
| Same information |0.000974|−0.000636 to 0.002582|

**An incremental neural advantage is not established:** the encoder and same-information intervals include zero. The complete circuit pipeline beats chance; the evidence does not show that the neural transformation adds reliable predictive value beyond its engineered encoder. This is not demonstrated neural learning, innate team choice, feeding behavior or betting profit.

## What was tested

The locked MaleCNS graph received source-informed taste input at exact proposed sweet/bitter cell IDs. A stable, narrower second-order Clavicle/Quasimodo assay passed fresh-seed, timing and recovery checks after the broader MN9 feeding assay failed. The feeding failure remains rejected. Thirty-five nested bilateral sweet-contact patterns and one bitter pattern formed an exact native response cache, with common seeds and full resets. Every contacted cell used the same first-second source-rate anchor. Contact extent and homogeneous rate transfer are engineered assumptions, not measured food-dose laws.

A training-fitted pregame encoder assigns each team an independent quality relative to a fixed training reference, with the same rule on both sides and explicit parameter uncertainty. It does not force the weaker of two good teams to be bitter. Only the four downstream neural response differences enter the fitted external probability readout. Cached responses reuse identical native schedules exactly; they are not a trained surrogate. Silenced native controls retained input spikes but produced zero downstream output. No neural plasticity was used.

Parameters were fit on 5,742 eligible 2019–2021 games. Nine pipeline candidates were evaluated on 2,429 games from 2022; minimum development log loss selected encoder C=1.0 and readout C=0.01. The final pipeline and confirmation protocol were committed locally as `22b3fb2` **before any 2023 source retrieval**. No parameters changed and no additional neural calls ran during confirmation. Prediction state used only earlier results delayed by 48 hours, in UTC-day batches. Resumed/suspended and unplayed games were excluded under the frozen rule.

Confirmation identity: `sensory-confirmation-4887cb8c17f6281d8166`. Dates: March 30–October 1, 2023. Source: public MLB Stats API. Raw data, exact source URL/retrieval time and hashes are preserved in the output manifest. Retrospective schedule corrections, unknown exact historical publication times, within-season dependence and the choice of weekly bootstrap blocks limit interpretation. This is an unused-year historical confirmation, not a prospective forecast trial.

## Evidence and verification

- [Every eligible confirmation prediction](confirmation-predictions.csv), [complete evaluation](confirmation-evaluation.json), [frozen candidate](frozen-candidate.json), [source/run manifest](confirmation-manifest.json).
- [Independent integrity check](confirmation-integrity.json): CSV metrics, every frozen readout prediction and all 10,000 fixture-resampled confidence bounds reproduced. All artifact/source/code/parameter hashes match.
- [Predeclared confirmation](../../../configs/sensory-confirmation-01.json), [development batch](development-batch-01.md), [all earlier results and source limits](index.md).
- [Verification](verification.md): 4,132 Python tests, 103 frontend tests, Ruff/build and guarded browser acceptance passed. All 124 protected files remained unchanged. The temporary QA server was stopped; v1 remains active and v2 paused. No push, deployment or model promotion.
