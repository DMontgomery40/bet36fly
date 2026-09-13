# Signals available for DAN release or joint KC state

Read-only audit at `dce1582`, September 13, 2026. All 189 current narrative
docs/wiki match the personally read chain; no new narrative delta. No native,
model, fit, test or network execution. Metadata and small identity maps were
read; no new waveform comparison was performed. **No inconsistency with the
current frozen electrical/bridge contract was found.** The missing release
and intracellular mechanisms are modeling gaps, not demonstrated code bugs.

## Exact available signals

| Signal | Native availability and phase | Existing retention / limitation |
| --- | --- | --- |
| Selected DAN events | `spiked[dan_indices[d]]`, binary at every 0.2 ms, after integration and teaching requests, before reset (`reward_lif.cpp:193–217`). All 24 identities survive here. | All 32 untaught fine rasters preserve individual events. Main taught records retain individual 10 ms counts and 0.2 ms population means. |
| KC events | `spiked[kc_indices[k]]`, same phase, all 4,064 cells (`reward_lif.cpp:255`). | All 32 untaught fine rasters; main records have total step counts, individual bridge filter endpoints every 10 ms, and individual coarse counts for only the first game of each panel. |
| Membrane state | `v[i]` after recurrent integration, then external voltage impulses, before threshold. Spike detection uses strict `v > 7`; `v` is reset after learning (`reward_lif.cpp:193–217,301–310`). | Only final `voltage = v - 52`, float32 for all 166,700 neurons. No prethreshold voltage trajectory. A future voltage-dependent model must name the exact sampling phase; a point-neuron voltage is not local terminal calcium. |
| Refractory availability | `t >= ready[i]`; selected DANs release 11 steps after each actual spike. Arrivals and teaching requests inside refractory are discarded (`reward_lif.cpp:181–207,310`). | Exact availability can be reconstructed for sampled non-sensory cells from complete fine events, cold `ready=0`, and the fixed 11-step rule. It cannot be reconstructed exactly from their 10 ms counts. |
| Synaptic input accumulator | `g[target] += weights[edge] * gain` for accepted delayed arrivals; integration then decays `g`, and spikes reset it (`reward_lif.cpp:181–197,309`). | No `g` trajectory or endpoint is exported. This signed simulator accumulator is not a measured conductance, concentration, or receptor state. The recorded KC subset can reconstruct accepted KC→PPL101 increments, not total input from unrecorded neurons. |
| Receiving anatomy | Presynaptic CSR `ptr`, postsynaptic `post`, signed fast `weights`; selected plastic edge index identifies its actual MBON target. Raw contact counts remain separately in `data/brain/counts.npy` (`reward_protocol.py:158–174,217–236`). | Body-pair connectivity and masks are retained, but no receptor expression, release probability, terminal geometry or per-contact chemical exposure. Zero fast DAN weights do not delete anatomical pairs. |
| MBON output | Actual MBON spikes and state are in the same graph loop; their recurrent outputs retain their signed fast pathways. The bridge does not consume MBON events directly. | Fine untaught sample excludes MBONs; all-neuron totals/final voltage remain. Main summary reports cue-window MBON means; full coarse MBON events exist only in the first game's sampled records. No full-panel MBON event raster. |

The bridge receives only binary KC impulses and the **mean of actual DAN
events per channel**, double division by 2 or 22 (`reward_lif.cpp:254–261`).
It receives no pulse flag, condition label, voltage, refractory state, input
accumulator, body-pair routing or MBON signal. The pulse schedule is an
electrical intervention, not a release measurement. All electrical and filter
states reset per call; only explicitly supplied gains persist. Its current
no-new-event analytic tail is not a nonlinear chemical continuation.

The inspected Handler evidence places order effects downstream of comparable
release-side signals; the proposed priming/inhibition topology is in the KC,
not an identified presynaptic DAN release cycle. Adult fly frequency-dependent
release and receptor sensitivity measurements exist, but do not specify a
PPL101/PAM12 spike-to-exposure map. Neither fact licenses rejecting ongoing
events or deciding release from a teaching label. See the previously read
`dopamine-receptor-state-decision-2026-09-13.md`,
`receptor-order-quantitative-transfer-decision-2026-09-13.md` and
`tonic-burst-dopamine-quantitative-source-check-2026-09-13.md` in canonical
repair evidence. Their γ4/γ5, heel, assay and kinetic-transfer limits remain.

## Exact existing-record joins for the next bounded audit

Fine directory:
`output/collaboration/reward-mechanism-repair/onset-history-captures/onset-history-capture-4343c21535c43f42/`.
`capture-receipt.json.identity.rows[i]` joins `fine_{i:02d}.npz` to the exact
`run_id`, `game`, `seed_set`, `seed`. The receipt is the original preregistration;
terminal `summary.json` says complete with 33 calls (one coarse plus 32 fine).
The earlier progress file's `partial` wording is not the terminal disposition.

| Fine indices | Diagnostic directory under `output/diagnostics/` | Ordered games; each base then alt |
| --- | --- | --- |
| 00–15 | `diag-rate-bridge-v1-maskgamma-de050d773763` | 4362, 4366, 4370, 4374, 4378, 4383, 4387, 4391 |
| 16–31 | `diag-rate-bridge-v1-maskgamma-dea14759e9ca` | 4395, 4399, 4404, 4408, 4412, 4416, 4420, 4425 |

Seed is `game + 42 + panel_index*2000000 + (1000000 if alt else 0)`.
Validate the actual row identity, rather than joining on game alone.
The main `trials.npz` prefix is `{game}__{seed_set}__{condition}__`, with
conditions `frozen`, `untaught`, `home`, `away`. Each panel has 64 main rows.
Use active untaught versus home/away for the causal comparison; frozen has
a different learning switch before teaching.

The small map is
`docs/evidence/reward-mechanism-repair-2026-09-12/onset-capture-preregistration.samples.npz`,
SHA256 `5f2414ffe5cab3d99cc1c1f0e91071df1f48721a7709816e90360af8b41074b3`.
This audit checked its hash and all column/index identities. `trace` is
int32 `(2000,4774)` in every fine file. `kc_columns` selects 4,064 columns,
`dan_columns` 24, and `sensory_columns` 686; the three sets do not overlap.
`dan_compartments` assigns the first two DANs to home and the other 22 to away.
PPL101 body 11327 is global index 1235 / fine column 52; body 11900 is index
1774 / column 74. All 32 fine files have empty pulse arrays.

Main retained keys are:

- `__step_signals`: float32 `(2000,5)`, total KC events in column 0,
  DAN means in columns 1 and 2, documented unused zeros in columns 3 and 4.
  The integer population count divided by 2 or 22 and cast to float32 is the
  exact expected recording. These means do not identify which DAN fired.
- `__dan_bins`: int32 `(40,24)` for every main row, individual 10 ms counts.
- `__bridge_signals`: float64 `(2000,2,2)`, rate after impulse / eligibility
  before evolution; `__bridge_kc_bins`: float64 `(40,4064,2)`, individual KC
  rate / eligibility after the completed bin. Both also exist for cumulative
  rows under their separate keys. They are not per-cell DAN release states.
- `__sampled_bins`: int32 `(40,4780)`, only first game × two noises × four
  conditions (eight per panel). `sampled` contains six MBONs, 24 DANs, 4,064
  KCs, 686 sensory cells; join its global indices to the fine map. Do not
  mistake this subset for complete full-panel fine recording.

All 32 fine ZIP/NPY header inventories and both complete main ZIP inventories
were inspected. No fine event payload was newly evaluated. Existing capture
code checks binary events, exact coarse aggregation, per-DAN counts, pooled
step parity and gain parity (`onset_history_capture.py:202–224`). Existing
hash fingerprints remain fingerprints, not missing time-series measurements.

## Causal-prefix claim that the current code supports

Matched active untaught/home/away runs use the same encoded schedule, seed,
unit initial gains and electrical reset. Their only input difference is
teaching requests at steps 1550, 1650, 1750, 1850 (310, 330, 350, 370 ms):
`reward_teaching_diagnostic.py:193–214,264–274`. Before the first request,
all states/events agree by the common deterministic execution.

Let T be the first step where **either** recorded pooled DAN signal differs
between the matched active conditions. Inductively, equal earlier pooled
signals and KC events give equal bridge states and gains. The selected DANs
have zero fast outgoing weights (`reward_protocol.py:170–174`), so individual
DAN differences hidden by an equal mean cannot affect other neurons through
fast transmission. KC spikes at T are detected before the gain update at T.
Consequently all KC events agree **through T inclusive** under the inspected
current code; a gain-mediated electrical difference can begin only later,
subject to actual delayed arrivals. This proof does not depend on assuming
that a requested teaching pulse elicited a spike.

This is a conditional code-based causal proof, not a direct taught per-KC
raster measurement. Check every retained pooled, total-KC, individual-bin and
filter-endpoint consistency that is available. A same pooled DAN mean after
the first pulse does **not** prove identical per-cell DAN histories. Later
intra-10 ms assignments/timing remain unknown, and a new per-cell release or
voltage-dependent law could invalidate this pooling-based proof. No such law
is implemented or approved here.

## Smallest justified seam and testing impact

For a future explicitly specified event-only release state, the native seam
is after actual spike detection and before pooling/reset: consume
`spiked[dan_indices[d]]` separately for each DAN, then apply the declared
coupling to KCs/eligible edges. A joint intracellular state can consume the
same events and actual KC events. Its clock, initial conditions, write onset,
pooling/contact map and complete tail must be defined first. Current anatomy
does not identify those chemical coefficients. If the model genuinely uses
subthreshold voltage or total input, the current fine archive is insufficient;
do not silently substitute its KC-only reconstructed arrivals for total drive.

No instrumentation is justified merely to collect more quantities now.
The existing `.2 ms` sampled-trace pathway already captures event-only inputs
when given the proven repeated schedule. The next selected task is the
existing-record prefix audit, with no new capture. Any later recording/model
extension would need a new identity/layout and independent validator before
API/Training could present scientific pass; unchanged historical records must
retain their present rule labels and fail-closed status.

Relevant existing tests were read, not rerun: actual versus requested spikes,
per-DAN refractory boundaries and record parity in `test_reward_brain.py:179–290`,
population normalization / onset / full-tail / reset checks in
`test_reward_rate_bridge.py:44–110`. A later justified change should expand
these families: same pooled counts with different per-cell assignments;
permutation with the matching identity/routing permutation; same observed
spikes with different irrelevant teaching metadata; simultaneous KC/DAN
ordering; exact onset/reset/tail behavior; masks/frozen gain bytes; and
record-off/on electrical/RNG parity. Voltage/input models additionally need
an independent phase-specific state oracle. Those are future obligations,
not tests or a candidate executed in this audit.
