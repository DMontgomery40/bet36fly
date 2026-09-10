# BET36FLY phase 1

The user delegates implementation decisions and asks for a working fruit-fly neural network, real training, fetched games, and a modest visual artifact. Their follow-up explicitly defers the bet365 demo account/API until phase 2. Phase 1 publishes paper picks only. No account credentials are required.

## Scientific implementation

Use the official MaleCNS v1.0 annotated neuronal graph, not a generic network with a fly theme. Import every released connection between retained annotated neurons, preserving weak and self connections. Record source URLs, SHA256 hashes, contact counts, exclusion accounting, neuron IDs, and transmitter-sign assumptions. Run all retained neurons and edges on CPU using a native sparse leaky integrate-and-fire simulator using Shiu et al. equations and parameter values. A connectome specifies wiring, not measured dynamics or cognition; describe the resulting model accordingly.

Encode pregame numerical observations through an explicit artificial sensory interface. Learn positive multiplicative gains on existing Kenyon-cell to mushroom-body-output-neuron connections and an artificial output readout. Learned edges keep their anatomical support and transmitter signs. Use cached initial spike activity for a bounded differentiable plasticity surrogate, then apply the learned gains to the actual anatomical synapses and rerun the full spiking network. Fit and validate the final readout on the resulting real spike counts. All shipped predictions come from this final full-network simulation, never from the surrogate. Do not claim calibrated visual perception, sentience, natural fly betting ability, or validated biological learning.

Use chronological train/validation/test partitions; estimate any scaling from training data alone. Report log loss, Brier score and accuracy by sport, training curves, calibration, naïve and feature-only baselines, and a no-connectome ablation. Include source dates and explicit evaluation limitations. All inference and dashboard neural activity must come from the checkpoint and graph, never illustrative data.

## Data and product

Choose Premier League soccer (home/draw/away) and MLB baseball (home/away), active in September 2026. Fetch public schedules, keep raw timestamped source responses, normalize postponed/cancelled/finished games, and compute features only from information available before kickoff. Historical football odds, when available, are optional evaluation data, never pretend current bookmaker quotes exist. For current events, output probabilities and picks with fair model odds; no invented offered odds or profit.

Build a React/Vite spectator dashboard backed by FastAPI: Observatory, Training, Pick ledger. Show real upcoming fixtures, per-match neural processing/activity, honest source freshness, trained model status, metrics/learning curves, and downloadable timestamped paper picks. Dark near-black, sage, chartreuse scientific visualization. The neuron plot uses real annotated coordinates where present and clearly labels its visual subset.

## Acceptance

Run a real historical training experiment and save the checkpoint, report, and future picks. Prove that existing anatomical synapses change, that predictions depend on the connectome, that outcome leakage is absent, and that save/load is stable. Run automated Python tests, lint, frontend build, and real browser clicks through refresh, sport filters, game inference, training results and ledger export. Leave a local running app, restart commands, source/model documentation and phase 2 adapter contract.
