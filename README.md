# BET36FLY

A working paper-sports experiment driven by the **actual MaleCNS v1.0 fly connectome**: 166,700 modeled neurons, 25,582,938 directed connections and 124,177,617 synaptic contacts. The full spiking network runs on CPU. Real training modifies existing anatomical synapses and fits a readout to its recorded spikes. No language model selects the games.

Phase 1 covers Premier League soccer and MLB baseball. It fetches current fixtures, publishes model probabilities and unfilled paper picks, shows recorded neural activity, tracks the outcomes of saved pregame picks, and reports a chronological backtest. The bet365 account/API, fills, bet settlement and player props are deferred to phase 2.

## Guides

- [How the fly was trained, and how its neurons compare with LLM weights](docs/FLY_GUIDE.md).
- [Confidence, the draw audit, and proposed paper bet sizing](docs/CONFIDENCE_AND_DRAWS.md).
- [External memory, smarter training, monitoring plan and capability limits](docs/ROADMAP.md).

The draw audit checks every frozen soccer test prediction: average draw probability was 21.0%, versus 30.8% actual draws. It distinguishes that aggregate underprediction from a few overconfident individual draw picks. Roadmap and sizing sections describe proposed work, not enabled functionality.

## Open the app

```sh
make serve
```

Visit [BET36FLY on localhost](http://127.0.0.1:8765). The app serves the built frontend and API on one local port. Use **Watch brain** for a fixture to run the real checkpoint and replay its recorded 80 ms of spikes. **Training** shows actual held-out results and baseline comparisons. **Pick ledger** exports every proposed pick as CSV. **Refresh games** fetches current schedules and computes new paper picks; it also revisits the previous 14 days to capture final results.

The server loads the current model from `output/current-model.json`, verifies its hash, and warms upcoming picks. If training is still running, the interface shows that state and waits for the checkpoint. No dummy model or fake results are substituted. Close the server with Ctrl-C.

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

`make brain` downloads the official data, checks pinned SHA256 hashes, and imports all released edges among retained neuronal objects. `make train` runs the complete historical experiment. Four CPU workers are used by default; adjust with:

```sh
.venv/bin/python -m bet36fly.experiment --workers 4 --plastic-epochs 60 --readout-epochs 180
```

Training caches are keyed by actual inputs, graph weights, neural source code and simulation settings. Repeating an unchanged experiment can reuse the expensive spike simulations. Changing input data, the graph, learned gains or neural code invalidates that cache.

## What the brain does

1. Sixteen lagged pregame observations are opponent-coded into artificial stimulation of 32 real ALPN neurons.
2. All 166,700 neurons advance using leaky integrate-and-fire equations; spikes propagate through the actual signed synaptic graph.
3. A bounded supervised surrogate learns positive gains on the 61,210 existing Kenyon-cell→MBON connections. No new anatomical connections are created.
4. Those gains are installed in the full spiking graph, which is rerun for all games. The final prediction readout is trained on those resulting real spike counts. The surrogate never serves predictions.
5. For each upcoming fixture, the actual trained full brain runs again, and its readout produces home/draw/away probabilities (no draw for MLB).

The data and wiring are real. The sensory mapping, neuron equations, coarse transmitter signs, learning rule and sports readout are explicit modeling choices. This is not a validated recreation of a living fly’s cognition or a claim of betting profitability. See [the model card](docs/MODEL_CARD.md) for equations, caveats and scientific attribution. The roughly 140,000-neuron female FlyWire brain is a different release; this project uses the male CNS release shown in the supplied screenshot.

## Training and evidence

- Training: available EPL 2023/24 onward and MLB 2024 onward, before July 2025.
- Validation: July–December 2025; used for epoch/regularization selection.
- Test: January–August 2026; all held-out predictions are exported.
- Results are delayed conservatively by at least 48 hours before updating later-game features. Known resumed MLB games without reliable completion timing are excluded from labeled examples.
- Metrics: log loss, multiclass Brier score, accuracy and calibration, separately by sport.
- Controls: training-frequency prior, pregame-feature logistic regression, frozen connectome, shuffled readout labels on the trained wiring, and silenced wiring.

The first completed run (`20260910T232621Z`) used 4,447 training games, 1,351 validation games and 2,277 held-out games. Both full-network simulation passes plus training and evaluation took 11.3 minutes on CPU.

| Held-out sport | Fly accuracy | Feature baseline accuracy | Fly log loss | Feature baseline log loss |
| --- | ---: | ---: | ---: | ---: |
| Soccer (214 games) | 37.4% | 44.9% | 1.189 | 1.062 |
| Baseball (2,063 games) | 52.1% | 54.0% | 0.700 | 0.686 |

The simple feature baseline wins in both sports. This run establishes an operating, trainable connectome pipeline, not a useful predictive edge. The trained checkpoint is retained as the experiment's first result; it has not been repeatedly tuned against the test set.

Artifacts live under `output/runs/<run-id>/`: checkpoint arrays, model report, learned synaptic gains, split manifest, frozen training data/game rows and every held-out pick. `output/training-progress.json` is the current stage. The durable proposed-pick ledger is `data/picks.sqlite3`. These local data artifacts are excluded from Git, while source URLs and scientific hashes are pinned in the repository.

## Verification

```sh
make verify
```

The Python suite covers graph integrity, spike propagation, inhibition/refractory behavior, deterministic replay, anatomical plasticity, temporal leakage, reschedules, source failure state, checkpoint-array readout roundtrip, API contracts and ledger durability. Browser acceptance additionally checks actual fixture selection → full brain inference → recorded spike replay → training results → ledger/export. A successful build alone is not that acceptance.

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
