# BET36FLY

A research application for a frozen, plasticity-off **MaleCNS sensory pipeline** and its completed **2023 MLB historical confirmation**.

The complete fitted pipeline achieved **56.21% accuracy on 2,423 games**, with a 95% weekly-block bootstrap interval of **54.42–58.02%** and log loss **0.680493**. It passed its predeclared better-than-chance criterion. Added neural benefit over the fitted encoder and same-information baseline remains unestablished; their paired uncertainty intervals include zero. [Result, predictions and limitations](docs/evidence/sensory-backtest-goal-2026-09-13/RESULT.md).

The circuit uses real anatomical connectivity with modeled neural dynamics. Pregame encoding and the probability readout are engineered and fitted externally. The result does not establish neural learning, in-circuit choice, feeding behavior, prospective performance or betting profit. Both teams can receive attractive inputs.

**Associative learning stage (September 13 evening):** dopamine-dependent KC→MBON plasticity now runs on the actual circuit with controlled acquisition, retention and reversal ([contract](docs/EXPERIMENT_ASSOCIATIVE.md), [evidence](docs/evidence/associative-learning-2026-09-13/index.md), [handoff](docs/ASSOCIATIVE_LEARNING_HANDOFF.md)). The product's predictions remain the frozen sensory confirmation; the `/#learning` page reports the learning stage separately.

## Open the research application

```sh
cd web && npm run build
cd ..
make serve
```

Open [BET36FLY locally](http://127.0.0.1:8765/#overview).

- **Overview:** full confirmation, uncertainty, comparator performance and claim boundaries.
- **Backtest explorer:** every eligible game, team/date filters, probabilities, outcomes and matchup details.
- **Pipeline & methods:** chronological splits, independent qualities, sensory probes, output measurements, provenance and exact frozen downloads.

Each matchup shows its persisted quality scores and uncertainty, reconstructed recruited body IDs and requested rates, and recorded Clavicle/ANXXX462a and Quasimodo/GNG042 responses. A lookup reuses previously simulated probes; it never starts a neural run. Achieved per-cell input rates are explicitly unavailable in this adapter. The old brain animation, model selectors, training dashboards and live-pick workflows are no longer mounted. Old bookmarks resolve to the overview.

The default server does not warm the old model or follow sports sources. It leaves `output/current-model.json` unchanged. Historical code, checkpoints, ledgers, research and failed results remain on disk; none are relabeled as sensory evidence. The retired backend endpoints remain separate compatibility APIs. [Current API contract](docs/api-contract.md).

## Installation and verification

Requires Python 3.12, `uv` and Node.js/npm. Install dependencies with `make setup`. The current application reads the frozen files named in `configs/sensory-application-lock.json`; missing, incomplete, symlinked or corrupt evidence produces an explicit unavailable state. Opening the application requires no source retrieval, fit, confirmation rerun or large neural-data load.

```sh
make verify
make serve-verify
# In another terminal, with the existing Playwright package available:
node scripts/verify_sensory_browser.cjs /tmp/bet36fly-sensory-browser
```

`make verify` runs pytest, Ruff, vitest and the production build. Rebuild before browser checks. If 8765 is occupied, use `make serve-verify QA_PORT=8766` and set `BET36FLY_BASE_URL=http://127.0.0.1:8766` for the browser command. The guard checks the exact read-only server marker before Chromium starts. The acceptance suite covers real results, filtering, details, downloads, loading/empty/error recovery, old URLs and desktop/mobile layouts. The old reward/desk browser commands now launch this current suite.

## Research and preservation

The backtest stopping condition is fulfilled. Do not tune on 2023, repeat it as an unused holdout, resume paused experiments or promote a model. New scientific work needs a distinct objective and experiment identity. Local changes are committed on the working branch; pushing and deployment remain David's decision.

- [Current direction](docs/PROJECT_DIRECTION.md) and [handoff](docs/NATURAL_SENSORY_HANDOFF.md).
- [Model card and retained historical results](docs/MODEL_CARD.md).
- [Authored cell/circuit wiki](wiki/index.md), [reassessment](wiki/reassessment.md) and [sensory-rate evidence](wiki/natural-sensory-inputs.md).
- [Locked MaleCNS source](docs/connectome-source-lock.json). Attribution: Berg et al.; HHMI Janelia, Cambridge, MRC LMB and Google Research, CC BY 4.0.
- [Shiu reference simulator](https://github.com/philshiu/Drosophila_brain_model), on female FlyWire; its stimulation settings are not measurements of natural sugar input.

The retained v1/v2 and dopamine protocols describe distinct historical experiments. SCI-001 remains HOLD for the legacy learning claim, and its rejected results remain rejected. Their old UI and source-following descriptions are historical, not the current application contract.
