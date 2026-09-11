# BET36FLY frontend contract

All endpoints are same-origin under `/api`. The production FastAPI process serves the built React app. Phase 1 is paper picks only; no account or monetary balance UI. Missing data is an explicit empty/error/loading state, never seeded values.

V1 remains the active model. The v2 registry, shadow status and anatomy-inspection payloads below are implemented; the matrix is paused at 13 completed jobs, eight user-cancelled temporal jobs and three unfinished whole-trial jobs. The completed decoder-only diagnostic and bounded stronger-L2 extension are separate CLI/artifact workflows; they do not change model pointers or resume the matrix. Their reports are linked from the guide/model card rather than being represented as a completed neural matrix run. Cancellation handling is implemented without rewriting the frozen protocol. Running-state desktop/mobile browser acceptance has passed. `/api/training` remains backward compatible for the original v1 report.

## GET /api/status

```json
{"app":"BET36FLY","mode":"paper","model_ready":true,"run_id":"20260910T...Z","runtime":"CPU","brain":{"neurons":166700,"edges":25582938,"contacts":124177617,"plastic_edges":61210},"training":{"status":"running|complete|failed|not_started","stage":"initial_full_brain","completed":20,"total":8000,"curve":[]},"refresh":{"status":"idle|running|complete|failed","message":"..."},"updated_at":"ISO UTC","sources":[{"name":"...","status":"fresh|stale|failed","fetched_at":"ISO","error":null}]}
```

## GET /api/games?sport=all|soccer|baseball

Returns `{"games":[Game],"updated_at":"ISO","sources":[...]}`. Game contains `id,sport,league,start_time,home,away,status,venue,source,source_url,source_fetched_at,home_logo?,away_logo?`. Only upcoming scheduled fixtures are listed. Optional `prediction` contains `pick` (`home|draw|away`), `pick_label` (team name or Draw), `probabilities` (`{"home":0.45,"draw":0.25,"away":0.30}`; draw exactly 0 for MLB), `confidence`, `fair_odds`, `run_id`, `created_at`, `ledger_id`. No probability before inference: show “Ready to think”. Fair odds are model-derived, not bookmaker quotes.

## GET /api/brain

Returns `dataset`, `nodes`, compatible `edges` pairs, aligned `edge_metadata`, `displayed_neurons`, `total_neurons` and `coordinate_note`.

```json
{
  "dataset": "MaleCNS v1.0",
  "nodes": [{
    "id": "body ID", "x": 0.2, "y": -0.3, "z": 0.1,
    "type": "source type or unassigned", "group": "source superclass or unknown",
    "category": "alpn|kc|mbon|other|unknown",
    "annotations": {"type": "source type", "superclass": "source superclass", "class": "source class"},
    "classification_source": "MaleCNS v1.0 released annotation, resolved by body ID"
  }],
  "edges": [[0, 1]],
  "edge_metadata": [{"contact_count": 5, "modeled_sign": 1, "plastic": false}],
  "displayed_neurons": 2500,
  "total_neurons": 166700,
  "coordinate_note": "Sampled actual soma positions; not a reconstruction of mushroom-body lobes."
}
```

The example describes field shapes, not a complete graph. Each edge is `[sourceDisplayIndex,targetDisplayIndex]`; its metadata is at the same array index. `modeled_sign` is +1 or −1. `plastic` identifies existing KC→MBON support, not whether the selected gain changed. Annotations include the persisted `transmitter` field as well as classification fields; source-dependent values may be null and must appear unavailable. The builder aligns node rows to graph body IDs before classifying them, using retained ALPN/KC/MBON membership and then available annotations for other/unknown.

Coordinates are normalized actual soma locations. The default sample has up to 2,500 cells with category coverage; displayed connections are the strongest eligible retained pairs between sampled endpoints, requiring at least five contacts and capped at 3,500 lines. Empty coordinate sets return empty node/edge/metadata arrays and an explicit note. No points, connections or activity are fabricated.

The canvas uses cyan triangles for ALPNs (`#56B4E9`), violet circles for KCs (`#B79CED`), amber diamonds for MBONs (`#E69F00`), light-gray squares for other annotated neurons (`#CBD5E1`) and muted-gray crosses for unknown categories (`#94A3B8`). Ordinary edges are slate (`#64748B`), plastic support rose (`#F18BA8`); white spike halos preserve category color. Independent layer toggles affect display only. Node inspection uses the projected canvas coordinates, refreshed on rotation/resize, and a keyboard-accessible selector. Incident-edge controls expose source/target inspection. Labeled explanation buttons provide full hover/focus and pinned content from `web/src/brainExplainers.ts`; Escape dismisses the inspector and returns focus to its original opener after nested navigation. Hover previews are pointer-transparent; the pinned inspector provides interactive source links.

## POST /api/predict/{game_id}

Runs the real checkpoint through the complete LIF graph and creates/idempotently retrieves a paper-pick ledger row. Returns `{"game":Game,"prediction":Prediction,"activity":{"rates":[one number per displayed node],"trace":[one bin per row; each row has one spike count per displayed node],"population":[one full-brain spike count per bin],"bin_ms":4,"duration_ms":80,"active_neurons":20500,"total_spikes":240000,"wall_seconds":0.2,"seed":42}}`. These are actual recorded neural spikes. Animate/replay the 80 ms trace with a Replay control and explicit simulated-time label. Do not imply a continuously thinking live brain from replayed data. Button states: Thinking… / Watch brain. Show the chosen fixture and pick beside/below the brain, never fake a confident narrative.

## GET /api/training

`{"progress":{...},"report":null|Report}`. Report has `run_id,created_at,runtime,wall_seconds,brain,splits,training_method,selected_epoch,curve:[{"epoch":1,"train_loss":1.1,"validation_loss":1.2}],plasticity_curve:[same],plasticity:{changed_synapses,actual_changed_graph_edges,min_gain,max_gain,selected_epoch},metrics:{soccer:Metrics,baseball:Metrics},controls:{train_frequency_prior:{soccer:Metrics,baseball:Metrics},pregame_feature_logistic:{...},frozen_connectome_trained_readout:{...},shuffled_readout_labels_on_trained_wiring:{...},silenced_connectome_fixed_readout:{...}},neural_evidence:{...},limitations:[string]`. Metrics: `n,accuracy,log_loss,brier,ece,calibration:[{lower,n,confidence,accuracy}]`. Display train/validation curves, held-out score comparison table, split counts and plain scientific limitations. Do not imply improvement when baselines win. No fake training start button. The real CLI command can appear in Methods, not primary product flow.

## GET /api/experiments

Returns `{"experiments":[Experiment],"active_v1":null|CurrentModelPointer,"prospective":Prospective}`. Entries are full atomic manifests, not fabricated summary rows. The active pointer is read separately from the local artifact `output/current-model.json`; the per-experiment `active_v1` is the pointer frozen at experiment creation.

The original schema-2 v2 `Experiment` includes:

- `id`, `schema_version:2`, `status`, `created_at`, `updated_at`, and `completed_at` after finalization.
- `identity`, resolved `protocol`, `protocol_sha256`, `source_hashes`, `graph_hashes`, `code_hashes`, and frozen `active_v1`.
- `jobs:[ExperimentJob]`, `artifacts:{artifact_id:Artifact}`, and nullable `selected_shadow`.
- `executions` records actual invocation IDs, start times, source hashes and training compatibility; once available: `null_controls`, `comparison`, `paired`, and `decisions`.
- `completion_scope:user-curtailed` and `execution_amendments` preserve explicit scope changes. Each cancellation amendment contains `recorded_at`, `reason`, `job_ids`, `kind:user-requested-cancellation` and `after_observing_results:true`. A finalized curtailed report uses `original_matrix_complete:false` and separates `cancelled_jobs` from `failed_jobs`. Its eventual `complete` status would mean amended scope completed, not all original jobs ran; the current paused matrix is not such a completion.

A job always identifies `id`, `variant`, `seed`, `status` (`queued|running|complete|failed|cancelled|paused`), `phase`, `gain_parameters`, `decoder_parameters` (allocated coefficients including biases), `active_parameters` (gain plus active decoder coefficients), explicit `seeds` for stimulus/minibatches/head initialization, and `completed`/`total`. Runtime updates add timestamps, actual `execution_id`, row progress, `elapsed_seconds`, `cache_hit`, `error`, `error_type`, or `interrupted` as relevant. Completed jobs contain `validation_loss`, selected plastic/decoder epochs, `wall_seconds`, decoder `curve`, `plasticity_curve`, `checkpoints`, `neural_statistics`, `gain_statistics`, `metrics`, `bundle` and `artifact_hashes`. These completion fields are absent until measured; missing values must not display as zero scores. Cancelled jobs have `phase:cancelled-by-user`, `cancellation_reason` and `cancelled_at`; counters retain the last measured work. A cancellation is distinct from an error and contributes no fabricated final score. The three remaining whole-trial jobs are `paused`, and experiment status is `paused`; they are neither completed nor automatically resumed.

Job `metrics` is keyed by `validation|historical`, then `soccer|baseball`, using the existing Metrics shape (`n,accuracy,log_loss,brier,ece,calibration`). A checkpoint comparison contains `plastic_epoch`, `selected_epoch`, `validation_loss`, and where applicable `surrogate_validation_loss` and `surrogate_full_gap`. The full-simulator validation result selects the installed pair; the surrogate curve is diagnostic.

Final `comparison` entries contain `variant`, `sport`, `split`, `seeds:[Metrics + seed]`, four-metric `mean` and `seed_spread` ranges. They cover the neural matrix, `frequency-prior`, `feature-logistic` and `selected-ensemble`. While the matrix runs, the UI builds partial comparisons from complete jobs; baseline and paired comparison tables arrive during finalization. The number of available seeds remains visible.

`paired` contains `method`, `limitation`, `replicates`, `seed` and `comparisons`. Each comparison names `left`, `right`, `sport`, `split`, `difference` (left minus right log loss), `interval:[lower,upper]`, matched-game `n`, `calendar_weeks`, `empty_weeks`, `seed_differences` and `decision`. Decisions are “better on this development comparison”, “worse on this development comparison” or “uncertain”. Three seeds are not treated as independent games; weekly blocks do not eliminate team/season dependence.

The existing Training tab renders this tracker before the archived v1 report. It polls every five seconds while any job is running and thirty seconds otherwise, preserving the last loaded data on a fetch failure. Run selection exposes measured curves/checkpoints/activity, failure text and downloads. Sport and split selectors label January–August 2026 **Historical development benchmark**. Validation alone chooses the shadow candidate.

## GET /api/reward-diagnostics

Read-only registry of the stored reward-rule diagnostic panels written by
`scripts/reward_teaching_diagnostic.py` under `output/diagnostics/<run_id>/`.
Returns `diagnostics[]` newest first (by `created_at`) and `evidence_note`
(`docs/evidence/reward-repair-phase1.md`). Each entry carries `run_id`, `rule`
(`legacy` or `candidate`), `dan_reference`, `away_plasticity_mask`,
`created_at`, `panel_complete`, `panel_note`, `all_passed`, `criteria` (name to
boolean for `teaching_specific`, `untaught_guard`, `cross_compartment`,
`no_bound_hits`, `cumulative`, `bit_identical_repeat`,
`sensory_noise_invariance`), `untaught_guard` and `teaching_specific`
per-seed-set evaluations (`mean`, `sd`, `limit`, `passed`; `mean_effect`,
`mean_untaught`, `required_magnitude`, `passed`), `has_attribution`,
`native_binary_sha256`, `source_unchanged_during_run`, `plastic_edges` and
`eligible_edges`. Directories with an unreadable or mismatched `summary.json`
are skipped. An absent or empty directory yields an empty list. A run whose
`panel_complete` is false is a debug panel and can never be a gate result.

## GET /api/reward-diagnostics/{run_id}

`summary` is the full stored `summary.json` (identity, anatomy, criteria with
every game and seed set, per-trial rows and phase terms, cumulative rows) and
`attribution` is `attribution.json` when present, otherwise `null`. Unknown,
malformed or escaping identifiers return 404. The raw `trials.npz` arrays are
never served. These panels are development diagnostics of the learning
mechanism, not sports results; a failed criterion is reported as failed.

## GET /api/experiments/{experiment_id}

The same read-only registry also serves schema-3 manifests with
`kind: dopamine-association`. These are rendered in a separate Training panel,
excluded from the v2 tracker, and have no activation route. Their `identity`
contains source/code/graph hashes and the resolved protocol. `reward` contains
anatomy, fixed readout, calibration progress, activity gate, fixed-prior metrics
and descriptive outcome. Gate fields include `kc_active_fraction`,
`max_mbon_hz`, `input_discrimination`, `teaching_responsive`,
`teaching_compartment_spikes`, `teaching_scheduled_spikes`,
`teaching_evoked_spikes`, `tonic_dan_hz`, `kc_code_overlap` and
`post_stimulus_kc_active_fraction`. The per-compartment arrays follow anatomical
compartment order, home then away. A failed gate's `message` names every failed
guard. Schema-2 protocols add `plasticity_onset_ms`, `dan_baseline_window_ms`,
`min_teaching_evoked_fraction` and `max_kc_code_overlap`; job `reward_evidence`
adds `tonic_dan_hz`. Schema-3 protocols add `encoder` (`glomerular-tuning-v1`),
`encoder_peak_hz`, `encoder_tuning_width`, `encoder_min_kc_contacts`,
`kc_input_gain`, `sensory_input_gain` and `apl_output_gain`; `reward.encoder`
names the encoder and `reward.anatomy` adds `kc_input_gain`,
`sensory_input_gain`, `apl_output_gain`, `apl_body_ids` and an `encoder` summary
(`glomeruli`, `centers_per_feature`, `center_span`, `floor_fraction`,
`ports_driven`, `ports_total`, `eligible_transmitter`, `min_kc_contacts`,
`dropped_glomeruli`, `peak_hz`, `tuning_width` and per-feature `features[]`
with `glomeruli[] {type, center, cells, kc_contacts}`). Schema-4 protocols add
`dan_reference` (`none`: the raw compartment-mean DAN spike count enters both
rule terms; `tonic-baseline`: the schema-2/3 subtraction, kept for comparison)
and `away_plasticity_mask` (`all` or `gamma`); `reward.rule` names the
implemented rule (`event-biphasic-kc-dan-raw-v3` or
`event-biphasic-kc-dan-phasic-v2`), `reward.dan_reference` and
`reward.away_plasticity_mask` echo the protocol, `reward.anatomy.dan_reference`
records the engine mode, `reward.anatomy.plasticity_mask` holds a `home` and an
`away` audit (`policy`, `eligible_edges`, `excluded_edges`, `by_class {gamma,
apbp, ab, other}`, `ambiguous_labels[]`) and each compartment adds
`eligible_edges`. `tonic_dan_hz` is measured in both modes and subtracted only
under `tonic-baseline`. Missing evidence remains unavailable.

Reward jobs use `paired|shuffled|frozen` variants and `queued|running|complete|failed|budget_stopped`
statuses. Progress counts training plus evaluation trials. Completed jobs carry
`metrics.validation.baseball`, `class_confusion` (home/away truth rows and
home/away prediction columns), `reward_curve`, `reward_evidence`, and
`evaluation_gains_unchanged`. Evidence includes changed edges, gain bounds,
activity and separate DAN compartment totals. A stopped job has no completed
metrics. Registered downloads include per-DAN time bins, gains, matched
predictions, calibration probes, frozen protocol and report; the existing
allowlist/hash checks apply. See [the reward protocol](EXPERIMENT_REWARD.md).

Returns the registry-resolved full manifest with `prospective` attached. Only identifiers matching the registry’s bounded alphanumeric/underscore/hyphen form are accepted. The manifest must remain under the experiment root and its stored ID must match the request. Unknown, invalid or escaping IDs return JSON `detail` with HTTP 404. Attached prospective status describes the currently frozen shadow candidate, which may differ from the experiment being inspected.

## GET /api/experiments/{experiment_id}/artifacts/{artifact_id}

Downloads one registered file using an opaque ID from the manifest’s `artifacts` allowlist. `Artifact` contains experiment-relative `path`, display `label`, `sha256`, `bytes`, nullable `job_id` and the ready-to-use `url`. Use that `url`; never construct a download endpoint from the stored path. Unknown IDs, unavailable files, traversal and symlinks escaping the resolved experiment directory return HTTP 404. The endpoint does not accept arbitrary filesystem paths.

## Prospective shadow payload

`Prospective.status` is `awaiting_candidate` before the local artifact `output/v2-shadow.json` exists and `active_shadow` afterward. It includes nullable `error` and `sports` keyed by soccer/baseball. Active status adds `model`, `variant`, `activated_at`, saved `forecasts` and a descriptive `note`.

Each sport reports `threshold` (100 soccer, 1,000 baseball), `eligible_completed`, cohort `status` (`pending|frozen`) and nullable `metrics`. Active payloads also supply nullable `frozen_at`, `cohort_ids`, nullable `cohort_eligible`, `cohort_invalidated` and `void`. Metrics contain `shadow` and `feature_logistic`, calculated on currently eligible members of the fixed cohort when available and otherwise on eligible completed interim forecasts. No completed forecasts means null metrics. Interim results remain descriptive.

The shadow runtime uses three full-simulator candidate bundles, averages their probability vectors and captures the frozen feature-logistic probability for the same fixture. It saves the first valid pregame forecast per model and fixture revision to a separate ledger, rechecks eligibility after inference, and records source/feature times. Changed revisions require a new forecast; cancellations are void and late forecasts never count. Cohort membership freezes once the fixed thresholds are reached. Stable first qualifying completion times determine its ordering; corrected outcomes and current eligibility remain live. Invalidated cohort members are excluded from scores, reported by `cohort_invalidated` and never replaced with later fixtures. Errors remain visible; there is no automatic active-model promotion.

## GET /api/ledger

`{"picks":[LedgerRow],"count":42}`. LedgerRow includes Prediction fields plus `id,game_id,sport,home,away,start_time,source_url,source_fetched_at,mode:"paper",status:"proposed",feature_hash,model_hash`. Table: time, sport/match, fly pick, model probability, fair odds, model run. State clear: proposed picks, unfilled; no actual wagers/P&L.

## GET /api/desk?sport=all|soccer|baseball

Returns a `forward_paper` record with `as_of`, `selection_rule`, `first_recorded_at`, `sources_updated_at`, `sources`, `refresh_interval_seconds`, `summary`, `by_sport`, `rows`, `curve`, and `excluded`. Each row contains its original `prediction`, `game_id`, `league`, `state` (`upcoming|pending|won|lost|held|void`), `reason`, `revision_count`, `can_run`, and nullable `result` (home/away scores, outcome, observation time and public source URL).

Summary counts completed/wins/losses/upcoming/pending/held/void and reports nullable hit rate, mean selected-pick probability and multiclass log loss. Curve points contain cumulative hit rate and mean selected-pick probability in kickoff order. Only the first valid pregame paper prediction matching the current fixture identity is scored. Later model/feature revisions cannot replace it. Missing, postponed or inconsistent final results are held; cancelled games are void. Rescheduled fixture revisions are excluded. Historical backtest rows are never imported. Confirmed source corrections can revise a score. All model versions are included and visible in individual record details.

The fourth tab polls this endpoint every 12 seconds, filters by sport and outcome state, and pages the actual rows. Watch calls the same real inference endpoint as the Observatory; it does not change the selected forward prediction. The illustrated fly and scripted banter are labeled as such. Only returned neural samples drive the spike replay. No invented activity, record, odds, stakes or profit is shown.

## GET /api/ledger/export

CSV download with actual ledger rows. Use `<a href="/api/ledger/export" download>`.

## POST /api/refresh

Returns `{"status":"running"}` quickly. Refreshes public game sources and computes upcoming paper picks with the current checkpoint in the background. Poll status/games/ledger/desk; disable refresh while running, surface stale/error state. Startup also warms upcoming predictions once the model is ready, requests a source refresh, and repeats every 900 seconds while the local server remains running. When a v2 shadow pointer is present, the same refresh workflow scores existing shadow records and captures new eligible shadow/feature-logistic forecasts alongside v1. Failures remain visible and the loop retries.

## GET /api/methods

Returns `{"model_card":"Markdown string","manifest":{...}}`. Link to Methods and scientific dataset from footer; can display a simple accessible details/dialog area. Errors use JSON `{"detail":"specific readable message"}`, HTTP 404/409/503 as appropriate.

## Visual design

Reference the local artifact `output/dashboard-concept.png` (1536x1024). It is a layout concept only; ALL fixture names, dates, counts, curves and probabilities in implementation must come from the API. Dynamic data is an intentional deviation from its illustrative content. Palette background #101411, lime #c5f277, white #f4f4e9, sage #9ca9a0, border #303b31. Header BET36FLY / Observatory / Training / Pick ledger / Fly’s desk / Paper mode / Refresh games. Main Observatory 63% brain + 37% fixture list. Hero copy “A small brain. A new game.” and “Real fly wiring. Real games. Paper picks.” Four open stats: Neurons, Connections, Training games, Runtime. Footer dataset / Experimental model / No real money, Methods link. Brain art uses real coordinate plot, not generated photo; the screenshot's wiring drawing is not scientific evidence. Responsive single-column mobile, accessible keyboard focus, reduced-motion support. No account toggle: Paper mode is a fixed status.
