# Connectome v2 experiment

V2 compares biological and randomized wiring, frozen and learned KC→MBON gains, and whole-trial versus temporal readouts. It uses the independent LIF simulator and MaleCNS graph described in the [model card](MODEL_CARD.md). Gain fitting is supervised surrogate learning; dopamine-dependent plasticity is not implemented.

## Frozen protocol

[The machine-readable protocol](../configs/experiment-v2.json) identifies source run `20260910T232621Z`, seeds 42/137/2026, four workers, 80 ms trials and four 20 ms windows. It specifies 16 plasticity epochs, checkpoints at 4 and 16, 180 readout epochs, gain bounds, optimizer settings and 2,000 weekly bootstrap replicates.

The eight variants are biological frozen, independent-gain and shared-gain models with either whole-trial or temporal readouts, plus randomized frozen-temporal and shared-temporal controls. Independent plasticity has 61,210 anatomical edges; shared plasticity has 295 supported KC/MBON type-pair groups. Randomization preserves declared graph invariants. Whole-trial and temporal variants stimulate the same network; their recorded-spike representation differs.

The frozen source has 4,447 training rows, 1,351 validation rows and 2,277 historical development rows. Validation originally selected checkpoints, baseline regularization and architectures. The January–August 2026 historical period has already influenced design and is not an independent test. Prospective cohorts require newly recorded eligible pregame forecasts.

## Retained execution

The local experiment `v2-24a83145c27ab220116e` is paused: 13 jobs completed, eight were cancelled and three are unfinished. No biological architecture has all three planned seeds, no final shadow candidate was activated, and the original v1 checkpoint remains active. Partial measurements do not establish a replicated topology advantage.

Subsequent decoder and feature diagnostics were separate, finite studies. The [tracked development summary](evidence/v2-development-summary.md) preserves their aggregate results, limitations and hashes. The original caches, predictions, ledgers, raw odds, browser evidence and full reports remain local under ignored `data/` and `output/` directories. They are not distributed with a clone of this repository.

## Execution requirements

The checked-in configuration describes a particular retained study. Running it requires that exact source run's aligned `training-data.npz` and `training-games.json` artifacts; source code alone does not recreate the archived dataset or results. The runner validates source, graph, protocol and code identities and stores a registry and resumable row caches under `output/experiments/`.

Completed diagnostic artifacts and session notes are archived separately from the active model and experiment caches. Evidence paths and report hashes retain their original identities; diagnostic commands require restoring the relevant archived study inputs to their expected locations or supplying the corresponding explicit paths. An absent archived input must not trigger a new simulation.

`make experiment-v2` starts a new experiment only when its required local source exists and the frozen experiment does not already exist. It does not request resume. Explicit `--resume` can continue unfinished work and must not be used for the currently paused study. For a different study, create a separate protocol with its own source identity; do not edit the retained protocol or overwrite its artifacts. Whole-brain matrix execution can take hours on CPU.

The Training interface reads local registry state and provides run details and allowlisted artifact downloads. A clean checkout shows an empty registry until an experiment exists. Readout diagnostics are command-line research artifacts, not additional completed neural-matrix jobs. The [API contract](api-contract.md) documents that distinction. Current serving remains local and paper-only.

## Research status

The measured decoder and feature studies did not establish a bookmaker edge or a benefit from biological topology. Those negative and uncertain results are retained because they constrain interpretation of this implementation. Biological reward learning and richer sports inputs are separate future experiments; their absence here does not establish that those approaches cannot work.
