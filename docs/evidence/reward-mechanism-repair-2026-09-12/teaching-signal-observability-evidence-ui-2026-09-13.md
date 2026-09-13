# Current teaching signal and retained observability

Read-only audit at `f08e88e8dc969ad8f0217eeb73e9c06c50afea79`, September 13, 2026. No new implementation inconsistency found against the frozen refractory and rate-bridge contracts. No circuit, candidate, fit, test or network execution. The 176 current narrative files match the personal full-reading chain; current relevant code and archive headers were inspected directly.

**Teaching changes electrical inputs to identified DANs. Learning receives the resulting actual spikes, with no teaching label. Existing artifacts support complete matched comparisons of pooled DAN waveforms, but do not directly retain every taught cell's fine spike history.**

## What distinguishes teaching

Both final panels use a 400 ms trial, sensory cue on `[0,300)` ms, and pulses at **310, 330, 350 and 370 ms**. Each pulse time addresses every selected DAN in the taught channel: two PPL101 cells for home or 22 PAM12 cells for away. These are respectively eight or 88 scheduled cell-pulse requests. They are not guaranteed spike counts. All four conditions use matched cue schedules/seeds and unit initial gains; frozen has no pulses and effective eta zero, untaught has no pulses and active learning, home/away have active learning and their respective pulses. [Diagnostic scheduling and resets](../../../scripts/reward_teaching_diagnostic.py#L195) are at lines 195–214 and 264–305.

At the native 0.2 ms clock, delayed synaptic arrivals are delivered before integration; a due teaching request then adds **68.75 simulator voltage units**, after integration and before the strict `v > 7` threshold. The API supplies time and DAN index, not a physical dopamine dose. Both recurrent arrivals and teaching pulses are discarded during refractory. A spike at step `s` releases at `s+11`; exact release accepts input. Duplicate requests can add voltage but produce at most one binary spike per cell/step. Refractory rejection and sufficiently negative voltage mean an accepted schedule is not proof of an evoked spike. See `reward_lif.cpp:181–215,300–310`, `reward_brain.py:396–419`, and the [frozen refractory contract](../../../docs/evidence/reward-refractory-contract-2026-09-12.md).

The actual learning input is `D_c(t) = count(actual DAN spikes in channel c)/N_c`, with double division. One synchronous spike from every cell has mass one in either channel; one isolated PPL101 spike has mass 1/2 and one PAM12 spike 1/22. Body identity, hemisphere, contact-specific release, concentration and receptor occupancy are absent from this aggregation. Pure-dopamine fast outgoing weights are zeroed; teaching can affect later circuit activity through changed KC→MBON gains, not a separate fast DAN current. See `reward_protocol.py:170–174,200–236` and `reward_lif.cpp:254–261`.

All actual KC and DAN events from **100 ms inclusive** enter their respective 100 ms rate filters and 500 ms eligibility filters. Earlier events are excluded and those states remain cold. Both products use the same causal inputs: `E_D R_K − E_K R_D`. The mask permits all 4,184 home edges and 3,239 gamma away edges; the 1,443 excluded away edges retain transmission. There is no postsynaptic-voltage or teaching-label gate. Each call resets electrical, refractory and filter states; only declared float32 gains can carry across cumulative trials. The separate analytic tail assumes no further events rather than simulating a silent brain. See `reward_lif.cpp:11–67,134–162,241–261,342` and the [bridge contract](../../../docs/evidence/reward-mechanism-repair-2026-09-12/rate-bridge-implementation-contract.md).

“Untaught endogenous” here means circuit-generated activity under the engineered sensory drive and recurrent aftermath. There is no independent spontaneous-DAN drive. The reported baseline window **50–100 ms occurs during the cue**, so `tonic_hz` is not a resting tonic measurement. Current `dan_reference='none'` correctly leaves this diagnostic value unsubtracted. Active home/away/untaught runs have identical dynamics before the first intervention by construction; later feedback and refractory interactions preclude attributing every extra or missing spike directly to a pulse request.

## What is already retained

I inspected all NPY headers in both final `trials.npz` archives (`de050d773763`, `dea14759e9ca`), and all 32 `fine_*.npz` capture headers. This establishes storage/schema coverage, not a new waveform analysis or complete payload-integrity audit.

| Signal | Retained coverage | Interpretation |
|---|---|---|
| `step_signals[:,1:3]`, float32 `(2000,5)` container | All 128 main rows: 32 each frozen/untaught/home/away | Actual pooled DAN events at 0.2 ms, including pre-onset. Integer pool counts can be recovered by checked enumeration of `float32(k/N)`, then divided in double. Last two columns are unused event-trace fields in bridge mode. |
| `bridge_signals`, float64 `(2000,2,2)` | All main rows plus 32 cumulative rows | Exact recorded post-injection DAN rate/prior eligibility for the current bridge; zeros before onset. |
| `dan_bins`, int32 `(40,24)` | All main rows | Individual DAN identity and 10 ms counts; within-bin timing and pulse acceptance are not recorded. |
| `bridge_kc_used` `(2000,8,2)` and `bridge_kc_bins` `(40,4064,2)` | All main/cumulative rows | Eligible-edge-weighted group moments and individual KC filter endpoints; not a recorded fine KC raster. |
| `sampled_bins` `(40,4780)` | First game of each panel, both seeds, all conditions: 16 rows | Individual MBON/DAN/KC/sensory counts at 10 ms. |
| Fine `trace`, int32 `(2000,4774)` | Exactly 32 untaught histories in capture `4343c21535c43f42` | All 4,064 KCs, 24 DANs and 686 sensory cells, with stored column maps. Empty pulse arrays in all 32. |

Retention is explicit at `reward_teaching_diagnostic.py:278–321,360–368`; capture selection, binary parity checks and no-pulse execution are at `onset_history_capture.py:125–169,202–224,271–278`. Replay fingerprints are hashes, not additional spike arrays. No retained acceptance flags, full voltage/conductance/refractory waveforms or release/receptor measurements were found in these current evidence paths.

## Useful next-decision boundary

A channel-pooled chemical model could use the **actual nonnegative DAN event series** from every matched condition without seeing condition labels. Descriptive comparisons can examine pulse-aligned timing, amplitude, persistence and overlap using existing arrays. Individual-DAN release dynamics or nonlinear coupling to each taught KC's exact history require finer retained inputs or an independently validated reconstruction; the current summaries cannot simply be substituted as rasters. Reusing untaught KC histories after teaching is also unjustified once gain feedback can diverge.

The minimal label-free ingredients available in the kernel are actual DAN spikes, actual KC spikes and the fixed cell/edge/mask mapping. Release, clearance, receptor states and their gain coupling remain explicit new modeling choices. The [bounded quantitative source review](../../../docs/evidence/reward-mechanism-repair-2026-09-12/tonic-burst-dopamine-quantitative-source-check-2026-09-13.md) documents relevant fly release and receptor-pathway measurements, but no calibrated PPL101/PAM12 spike-to-local-exposure mapping for this trial. That gap neither licenses treating ongoing activity as biologically inactive nor shows that a local chemical mechanism cannot work.

Existing inspected tests cover refractory boundary matrices and per-DAN rejection (`test_reward_brain.py:190–246`), population sizes 1/2/22 with partial activity, signed pair histories, onset exclusion, complete tails and record/reset parity (`test_reward_rate_bridge.py:46–112`). They were read, not rerun. No gate, parameter, rule or production surface changed.
