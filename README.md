# BET36FLY

## Latest sensory checkpoint

[Natural sensory calibration](docs/evidence/natural-sensory-calibration-2026-09-13/index.md) now records exact candidate cells, source measurements and native projections. The rate/cell contract remains unresolved, so no new sensory simulation ran. [Next bounded decision](docs/NATURAL_SENSORY_HANDOFF.md).

**Current research direction, September 13:** represent matchup information as two food opportunities using calibrated fruit-odor or sweet/aversive taste patterns, establish the circuit's natural sensory response, then measure its contribution to matchup selection. Both teams can be attractive. Read the [canonical direction](docs/PROJECT_DIRECTION.md), [continuation prompt](docs/NATURAL_SENSORY_HANDOFF.md) and [measured sensory-rate evidence](wiki/natural-sensory-inputs.md). This is the next research task, not an implemented sensory encoder or a new active model.

Read the [fly cell and circuit wiki](wiki/index.md) for the [reassessment](wiki/reassessment.md), exact neuron identities, learning-rule limits, and copied Microduck research. The legacy refractory correction, gamma away eligibility mask and rate bridge are integrated; qualification and subsequent fixed shadows failed. [Repair evidence](docs/evidence/reward-mechanism-repair-2026-09-12/index.md) retains SCI-001 HOLD. The new plasticity-off sensory assay does not depend on that learning repair. Conditioning and reversal remain unrun.

A working paper-sports experiment driven by the **actual MaleCNS v1.0 fly connectome**: 166,700 modeled neurons, 25,582,938 directed connections and 124,177,617 synaptic contacts. The full spiking network runs on CPU. Real training modifies existing anatomical synapses and fits a readout to its recorded spikes. No language model selects the games.

Phase 1 covers Premier League soccer and MLB baseball. It fetches current fixtures, publishes model probabilities and unfilled paper picks, shows recorded neural activity, tracks the outcomes of saved pregame picks, and reports a chronological backtest. The bet365 account/API, fills, bet settlement and player props are deferred to phase 2.

The accepted **v1 checkpoint remains active**. The [v2 comparison](docs/EXPERIMENT_V2.md) is paused by user instruction: 13 runs are complete, eight temporal jobs were cancelled after partial results, and three whole-trial jobs remain unfinished. The [tracked development summary](docs/evidence/v2-development-summary.md#decoder-diagnostics) records the bounded stronger-L2 diagnostic: all 16 fits converged after reproducing the four C=0.01 references. Within the authorized grid, selected temporal readouts now slightly beat selected whole-trial readouts in both sports, while the feature baseline retains lower validation log loss. These are validation-selected development results, not independent confirmation; the grid will not expand automatically. No neural simulation, gain training, matrix resume or model-pointer change occurred; the [model card](docs/MODEL_CARD.md) explains the limits.

The completed bookmaker diagnostic is summarized in [MLB bookmaker comparison](docs/evidence/v2-development-summary.md#mlb-bookmaker-comparison). It compares 1,159 of 1,165 frozen MLB validation fixtures with SBR-provided Bet365 opening moneylines: de-vigged book log loss is 0.680574, versus 0.682797 feature-logistic, 0.687661 temporal, 0.688220 whole-trial and 0.690029 frequency-prior on the same games. SBR supplies an opening label but no actual quote timestamp, all paired intervals cross zero, and the result demonstrates no edge, equivalence or profit. The separate [MLB feature sweep](docs/evidence/v2-development-summary.md#feature-sweep) is also complete. Training-only chronological selection chose 10-game pooled form, capped rest and C=0.001. Its same-game validation loss of 0.684327 did not improve the saved feature baseline or beat Bet365. All 900 fold fits converged. This feature experiment did not run the fly or implement reinforcement learning.

## Guides

- [How the fly was trained, and how its neurons compare with LLM weights](docs/FLY_GUIDE.md).
- [Confidence, the draw audit, and proposed paper bet sizing](docs/CONFIDENCE_AND_DRAWS.md).
- [External memory, smarter training, monitoring plan and capability limits](docs/ROADMAP.md).

The draw audit checks every frozen soccer test prediction: average draw probability was 21.0%, versus 30.8% actual draws. It distinguishes that aggregate underprediction from a few overconfident individual draw picks. Roadmap and sizing sections describe proposed work, not enabled functionality.

## Open the app

```sh
make serve
```

Visit [BET36FLY on localhost](http://127.0.0.1:8765). The app serves the built frontend and API on one local port. Use **Watch brain** for a fixture to run the real checkpoint and replay its recorded 80 ms of spikes. **Training** shows mechanism diagnostics and their qualification evidence, distinguishing stored verdicts from independently recomputed results. It also retains the historical reward/v2 registries, selectable run details, sport/split comparisons and prospective status, followed by the archived v1 reference. **Pick ledger** exports every proposed pick as CSV. **Refresh games** fetches current schedules and computes new paper picks; it also revisits the previous 14 days to capture final results.

The server loads the current model from `output/current-model.json`, verifies its hash, and warms upcoming picks. If training is still running, the interface shows that state and waits for the checkpoint. No dummy model or fake results are substituted. In the Observatory, the anatomy legend filters the display; explanation buttons and the searchable neuron selector open detailed inspectors. These controls never change the prediction. Close the server with Ctrl-C.

For QA, rebuild the frontend and start `make serve-verify`. This explicit
read-only server disables model warming and sports refresh. The guarded
`scripts/verify_reward_browser.cjs` check requires that verification server;
ordinary `make serve` is the user app and can refresh live paper-pick data.

## Reproduce from source

Requires Python 3.12, `uv`, Node.js/npm and a C++17 compiler (Xcode Command Line Tools on macOS; a normal C++ compiler on Linux). Allow about 1.5 GB for raw scientific data and additional room for neural caches. No API keys or paid hardware are required.

```sh
make setup
make brain
make fetch
make train
cd web && npm run build
cd ..
make serve
```

`make brain` downloads the official data, checks pinned SHA256 hashes, and imports all released edges among retained neuronal objects. `make train` runs the original v1 historical experiment and is unchanged by v2. Four CPU workers are used by default; adjust with:

```sh
.venv/bin/python -m bet36fly.experiment --workers 4 --plastic-epochs 60 --readout-epochs 180
```

Training caches are keyed by actual inputs, graph weights, neural source code and simulation settings. Repeating an unchanged experiment can reuse the expensive spike simulations. Changing input data, the graph, learned gains or neural code invalidates that cache.

## Experiment commands and current pause

The original v2 command is retained for reproducibility. **Do not run or resume it under the current scope:** the user paused the remaining matrix in favor of a decoder-only diagnostic. The source run must already exist locally for this command:

```sh
make experiment-v2
```

This invokes `.venv/bin/python -m bet36fly.experiment_v2 --protocol configs/experiment-v2.json`. It freezes the protocol and existing v1 data, uses four CPU workers for one graph job at a time, and requires the exact local source run. Explicit `--resume` can continue unfinished work for a separately authorized study; it remains prohibited for the currently paused study. The original frozen protocol declares eight neural variants across seeds 42, 137 and 2026. A separate user-requested execution amendment cancelled eight unfinished temporal jobs. A subsequent instruction paused the three remaining biological whole-trial jobs as well. Current accounting is 13 completed, eight cancelled and three unfinished; neither a 16-run amended completion nor the original 24-run matrix has been delivered. The original frozen protocol and cancellation provenance remain intact. Source/protocol/graph identity determines the experiment directory under `output/experiments/`. A registry lock prevents simultaneous runners.

Keep `make serve` running to inspect retained results and the paused state in Training. Queued and cancelled jobs have no fabricated final scores; cancelled work is distinguished from a failed implementation. The implemented completion workflow can freeze a separate v2 shadow ensemble and feature-logistic baseline, but the current diagnostic does not activate or change one. Shadow capture through the ordinary 15-minute refresh requires a frozen candidate pointer. V1 and `data/picks.sqlite3` remain separate. The first prospective cohorts require 100 completed eligible soccer fixtures and 1,000 baseball fixtures; that future evidence is pending, not a reason to keep training.

The completed bounded stronger-L2 diagnostic can be reproduced into a new, separate directory without neural simulation:

```sh
.venv/bin/python -m bet36fly.decoder_stronger_l2 \
  --experiment output/experiments/v2-24a83145c27ab220116e \
  --output output/diagnostics/decoder-seed42-stronger-l2-recheck
```

It verifies the frozen biological seed-42 cache and first reproduces all four C=0.01 scores within 0.000001 before fitting only C=0.00001, 0.0001 and 0.001. It reuses training/validation rows, refuses an existing output directory and never supplies a missing-cache simulation fallback. Aggregate results are in the [tracked decoder summary](docs/evidence/v2-development-summary.md#decoder-diagnostics); full reports are local artifacts under `output/diagnostics/` and are not distributed with the repository.

## What the active v1 brain does

1. Sixteen lagged pregame observations are opponent-coded into artificial stimulation of 32 real ALPN neurons.
2. All 166,700 neurons advance using leaky integrate-and-fire equations; spikes propagate through the actual signed synaptic graph.
3. A bounded supervised surrogate learns positive gains on the 61,210 existing Kenyon-cell→MBON connections. No new anatomical connections are created.
4. Those gains are installed in the full spiking graph, which is rerun for all games. The final prediction readout is trained on those resulting real spike counts. The surrogate never serves predictions.
5. For each upcoming fixture, the actual trained full brain runs again, and its readout produces home/draw/away probabilities (no draw for MLB).

The data and wiring are real. The sensory mapping, neuron equations, coarse transmitter signs, learning rule and sports readout are explicit modeling choices. This is not a validated recreation of a living fly’s cognition or a claim of betting profitability. See [the model card](docs/MODEL_CARD.md) for equations, caveats and scientific attribution. The roughly 140,000-neuron female FlyWire brain is a different release; this project uses the male CNS release shown in the supplied screenshot.

## Historical v1 evidence

- Training: available EPL 2023/24 onward and MLB 2024 onward, before July 2025.
- Validation: July–December 2025; used for epoch/regularization selection.
- Historical development benchmark: January–August 2026. This was the original v1 test period; its observed results have since influenced v2 design, so it is no longer untouched evidence.
- Results are delayed conservatively by at least 48 hours before updating later-game features. Known resumed MLB games without reliable completion timing are excluded from labeled examples.
- Metrics: log loss, multiclass Brier score, accuracy and calibration, separately by sport.
- Controls: training-frequency prior, pregame-feature logistic regression, frozen connectome, shuffled readout labels on the trained wiring, and silenced wiring.

The first completed run (`20260910T232621Z`) used 4,447 training games, 1,351 validation games and 2,277 held-out games. Both full-network simulation passes plus training and evaluation took 11.3 minutes on CPU.

| Held-out sport | Fly accuracy | Feature baseline accuracy | Fly log loss | Feature baseline log loss |
| --- | ---: | ---: | ---: | ---: |
| Soccer (214 games) | 37.4% | 44.9% | 1.189 | 1.062 |
| Baseball (2,063 games) | 52.1% | 54.0% | 0.700 | 0.686 |

The simple feature baseline wins in both sports. This run establishes an operating, trainable connectome pipeline, not a useful predictive edge. The trained checkpoint is retained as the experiment's first result. V2 selection is confined to validation, and its prospective evaluation uses newly saved pregame forecasts.

Artifacts live under `output/runs/<run-id>/`: checkpoint arrays, model report, learned synaptic gains, split manifest, frozen training data/game rows and every held-out pick. `output/training-progress.json` is the current stage. The durable proposed-pick ledger is `data/picks.sqlite3`. These local data artifacts are excluded from Git, while source URLs and scientific hashes are pinned in the repository.

Completed diagnostic reports, source snapshots and session notes may be retained in an external local archive. Paths in the development evidence identify their original locations; restore only the required study artifacts before running a retained-study diagnostic. Active model assets, run registries and neural caches remain in place.

## Verification

```sh
make verify
```

The Python suite covers graph integrity, spike propagation, inhibition/refractory behavior, deterministic replay, anatomical plasticity, temporal leakage, reschedules, source failure state, checkpoint-array readout roundtrip, API contracts and ledger durability. The repair adds independent numerical oracles, masks, electrical/tail bound observations and persisted-evidence validation. Browser acceptance additionally checks the actual affected workflow; a successful build alone is not that acceptance. See the [dated repair checks](docs/evidence/reward-mechanism-repair-2026-09-12/index.md#preserved-evidence-and-execution-exception) for current evidence and limitations. The historical stronger-L2 gate passed 240 Python tests, 49 frontend tests, Ruff and the production build while preserving 453 files; those counts describe that earlier diagnostic. [Verification and scope](docs/MODEL_CARD.md#verification-and-acceptance) distinguish the completed decoder diagnostic from the paused matrix.

## Fly’s desk

The fourth tab at [Fly’s desk](http://127.0.0.1:8765/#desk) shows real upcoming picks, their original probabilities, result history, and cumulative accuracy against mean pick confidence. It scores the first valid pregame prediction for each current fixture across model versions. Reruns cannot replace that prediction; cancelled or unresolved games do not count as successes or misses. This is prospective forecast scoring, separate from the historical backtest and any future bet settlement.

Public schedules and final scores refresh every 15 minutes while `make serve` is running. The browser polls the record every 12 seconds. Refresh games requests an immediate source check. Watch runs the actual full connectome and replays its measured spikes. The fly artwork and jokes are explicitly illustrative; the probabilities, spike counts, timestamps and score history come from saved model runs and public results.

## Data, research and phase 2

- [MaleCNS official download and license](https://male-cns.janelia.org/download/): Berg et al., HHMI Janelia, Cambridge, MRC LMB and Google Research; CC-BY 4.0.
- [Shiu et al., Nature 2024](https://www.nature.com/articles/s41586-024-07763-9): simulation equations and parameter basis.
- [Published reference simulator](https://github.com/philshiu/Drosophila_brain_model) and [DOOMFLY](https://github.com/nftechie/doomfly): reference implementations and scientific limitations consulted.
- [Sports sources and feature timing](docs/sports-data.md).
- [Local API contract](docs/api-contract.md).

Phase 2 should consume the immutable paper-pick records via a separate demo-account adapter. Its inputs must include provider fixture/market IDs, fresh offered odds and explicit demo-account identity. Fair model odds in this app are not executable quotes. No private credentials were read or copied for phase 1.
