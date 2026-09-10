# BET36FLY frontend contract

All endpoints are same-origin under `/api`. The production FastAPI process serves the built React app. Phase 1 is paper picks only; no account or monetary balance UI. Missing data is an explicit empty/error/loading state, never seeded values.

## GET /api/status

```json
{"app":"BET36FLY","mode":"paper","model_ready":true,"run_id":"20260910T...Z","runtime":"CPU","brain":{"neurons":166700,"edges":25582938,"contacts":124177617,"plastic_edges":61210},"training":{"status":"running|complete|failed|not_started","stage":"initial_full_brain","completed":20,"total":8000,"curve":[]},"refresh":{"status":"idle|running|complete|failed","message":"..."},"updated_at":"ISO UTC","sources":[{"name":"...","status":"fresh|stale|failed","fetched_at":"ISO","error":null}]}
```

## GET /api/games?sport=all|soccer|baseball

Returns `{"games":[Game],"updated_at":"ISO","sources":[...]}`. Game contains `id,sport,league,start_time,home,away,status,venue,source,source_url,source_fetched_at,home_logo?,away_logo?`. Only upcoming scheduled fixtures are listed. Optional `prediction` contains `pick` (`home|draw|away`), `pick_label` (team name or Draw), `probabilities` (`{"home":0.45,"draw":0.25,"away":0.30}`; draw exactly 0 for MLB), `confidence`, `fair_odds`, `run_id`, `created_at`, `ledger_id`. No probability before inference: show “Ready to think”. Fair odds are model-derived, not bookmaker quotes.

## GET /api/brain

`{"dataset":"MaleCNS v1.0","nodes":[{"id":"123","x":0.2,"y":-0.3,"z":0.1,"type":"KC...","group":"cb_intrinsic"}],"edges":[[sourceDisplayIndex,targetDisplayIndex]],"displayed_neurons":2500,"total_neurons":166700,"coordinate_note":"..."}`. Coordinates normalized from actual annotated soma positions. All connections displayed come from real retained graph. Render a scientific point-cloud/graph canvas from these values, not an image or fabricated points. Full computation includes all neurons; visual sampling is labeled.

## POST /api/predict/{game_id}

Runs the real checkpoint through the complete LIF graph and creates/idempotently retrieves a paper-pick ledger row. Returns `{"game":Game,"prediction":Prediction,"activity":{"rates":[one number per displayed node],"trace":[one bin per row; each row has one spike count per displayed node],"population":[one full-brain spike count per bin],"bin_ms":4,"duration_ms":80,"active_neurons":20500,"total_spikes":240000,"wall_seconds":0.2,"seed":42}}`. These are actual recorded neural spikes. Animate/replay the 80 ms trace with a Replay control and explicit simulated-time label. Do not imply a continuously thinking live brain from replayed data. Button states: Thinking… / Watch brain. Show the chosen fixture and pick beside/below the brain, never fake a confident narrative.

## GET /api/training

`{"progress":{...},"report":null|Report}`. Report has `run_id,created_at,runtime,wall_seconds,brain,splits,training_method,selected_epoch,curve:[{"epoch":1,"train_loss":1.1,"validation_loss":1.2}],plasticity_curve:[same],plasticity:{changed_synapses,actual_changed_graph_edges,min_gain,max_gain,selected_epoch},metrics:{soccer:Metrics,baseball:Metrics},controls:{train_frequency_prior:{soccer:Metrics,baseball:Metrics},pregame_feature_logistic:{...},frozen_connectome_trained_readout:{...},shuffled_readout_labels_on_trained_wiring:{...},silenced_connectome_fixed_readout:{...}},neural_evidence:{...},limitations:[string]`. Metrics: `n,accuracy,log_loss,brier,ece,calibration:[{lower,n,confidence,accuracy}]`. Display train/validation curves, held-out score comparison table, split counts and plain scientific limitations. Do not imply improvement when baselines win. No fake training start button. The real CLI command can appear in Methods, not primary product flow.

## GET /api/ledger

`{"picks":[LedgerRow],"count":42}`. LedgerRow includes Prediction fields plus `id,game_id,sport,home,away,start_time,source_url,source_fetched_at,mode:"paper",status:"proposed",feature_hash,model_hash`. Table: time, sport/match, fly pick, model probability, fair odds, model run. State clear: proposed picks, unfilled; no actual wagers/P&L.

## GET /api/ledger/export

CSV download with actual ledger rows. Use `<a href="/api/ledger/export" download>`.

## POST /api/refresh

Returns `{"status":"running"}` quickly. Refreshes public game sources and computes upcoming paper picks with the current checkpoint in the background. Poll status/games/ledger; disable refresh while running, surface stale/error state. Startup also warms upcoming predictions once the model is ready.

## GET /api/methods

Returns `{"model_card":"Markdown string","manifest":{...}}`. Link to Methods and scientific dataset from footer; can display a simple accessible details/dialog area. Errors use JSON `{"detail":"specific readable message"}`, HTTP 404/409/503 as appropriate.

## Visual design

Reference `output/dashboard-concept.png` (1536x1024). It is a layout concept only; ALL fixture names, dates, counts, curves and probabilities in implementation must come from the API. Dynamic data is an intentional deviation from its illustrative content. Palette background #101411, lime #c5f277, white #f4f4e9, sage #9ca9a0, border #303b31. Header BET36FLY / Observatory / Training / Pick ledger / Paper mode / Refresh games. Main Observatory 63% brain + 37% fixture list. Hero copy “A small brain. A new game.” and “Real fly wiring. Real games. Paper picks.” Four open stats: Neurons, Connections, Training games, Runtime. Footer dataset / Experimental model / No real money, Methods link. Brain art uses real coordinate plot, not generated photo; the screenshot's wiring drawing is not scientific evidence. Responsive single-column mobile, accessible keyboard focus, reduced-motion support. No account toggle: Paper mode is a fixed status.
