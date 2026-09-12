# Conditioning pre-run scientific review and precise addendum

September 12, 2026 UTC; mechanism_sources. Read-only source/artifact review; no conditioning result, simulation, kernel change or runner change was produced. Root may copy this as a dated, hashed addendum before implementation. This clarifies the original conditioning preregistration; it does not revise a threshold after observing conditioning data. Coordination with conditioning_integration and root resolved the definitions below.

## Corrected-event result: what passed

`diag-candidate-maskgamma-a4e0db0de471` records all seven frozen diagnostic criteria passing. I inspected its identity, complete criteria, all 64 rows' core numerical fields, the 16 cumulative rows and mask audit, and checked row uniqueness and the reported statistics against the stored rows. The original input hash and accepted protocol match the historical gamma panel: eta 0.0005, eligibility 500 ms, global gain 0.5, ALPN input 0, APL output 0.25, KC input 1.25, home-all and away-gamma. The source/native identity identifies the corrected refractory kernel; the rate bridge remains unimplemented.

| Quantity | Historical gamma panel | Corrected gamma panel |
| --- | --- | --- |
| Home untaught mean, base / alt | −0.2892 / −0.2402 | −0.1832 / −0.1881 |
| Home untaught SD, base / alt | 0.3219 / 0.3812 | 0.6676 / 0.5250 |
| Absolute mean / SD, base / alt | 0.899 / 0.630; fail 0.5 guard | 0.274 / 0.358; pass 0.5 guard |
| Negative untaught home rows | 13 / 16 | 13 / 16 |
| Cumulative untaught home gain sum | −3.6127, limit 9.1351 | −3.8829, limit 12.7340 |

Corrected teaching effects are approximately −3.18 home and −4.54 away per trial in eligible gain-sum units; every per-cue matched teaching effect has the expected negative sign. Away untaught is exactly zero, recorded cross-compartment teaching effects are zero, and no clipping is reported. This is not learning made numerically negligible. The original mean-within-half-SD criterion passes through a smaller negative mean and greater across-cue variation, not through elimination of untaught home plasticity. The cumulative absolute drift did not decrease; its unchanged relative criterion still passes because the matched teaching effect is stronger.

The result establishes that the source-backed input-delivery correction is sufficient to pass this particular original full-CNS diagnostic panel without a rate bridge or gain/criterion retuning. In an untaught trial no external teaching pulse is requested; the recurrent-delivery correction is therefore the relevant changed input path for untaught histories. The two refractory corrections together remain the identified intervention for the complete taught/untaught panel. This does not demonstrate zero systematic drift, generalization to the held-out cues/noise, cue-specific retained MBON responses, acquisition, reversal, sports prediction, or biological validity. Passing this panel is not permission to skip the remaining entry gates. Old failed artifacts remain failed historical results.

## Schedule and exact call arithmetic

An acquisition block is four cue exposures `A B B A`; six blocks give 24 exposures, indexed `i=0..23`, with 12 per cue. Each exposure comprises one cue trial followed by one blank companion, both 400 ms, with independent reset membrane/trace state and persisting gains. The cue occupies `[0,300)` ms; the remaining interval is silent sensory input. Cue seed is `42 + panel_offset + 2*i`; blank seed is one larger. Panel offsets are 0 and 1,000,000. Apply the identical index convention to C/D. Do not accidentally use the six-block index as the 24-exposure seed index.

The paired, shuffled, timing-unpaired, untaught and frozen state table remains unchanged. Four teaching times are 310/330/350/370 ms, each applied to every declared DAN of the selected population. Shuffled `home,home,away,away` against each ABBA block gives A and B one pairing with each population per block, hence six of each pairing per cue. Timing-unpaired teaching is confined to the blank companion; all arms execute the same two electrical calls per exposure. Freeze the shuffled table itself, not only its name.

Reversal has one 800 ms electrical call per exposure, 24 per branch, with no extra blank companion. It uses the same six ABBA blocks. Use seed `42 + reversal_panel_offset + i`, offsets 3,000,000 and 4,000,000. Sensory cue is `[300,600)` ms, with zero drive elsewhere. Onset remains 100 ms. The early train is 110/130/150/170 ms; first late train is 610/630/650/670 ms; second late train is 690/710/730/750 ms. Continued acquisition and ordinary swap use both late trains on their respective one population. Backward-erasure-plus-swap uses the early train on the old population and the first late train on the new population; it never uses the second late train. Untaught/frozen have no teaching. All events lie inside the trial and all teaching lies after plasticity onset.

“Eight reversal pulses” means eight population stimulation times, not eight individual neuron impulses. With 2 home DANs and 22 away DANs, continued acquisition requests 16 individual impulses on A and 176 on B, whereas backward-erasure-plus-swap requests 96 on either cue. Across a complete 24-exposure panel, each taught branch requests the same 192 home plus 2,112 away impulses, total 2,304. Thus channel exposure is matched over the balanced panel, not per cue. Record requested times/DAN indices and observed spikes separately. Existing `record=True` per-step compartment mean spikes, multiplied by population size, supply observed population spike counts at each requested pulse step; retain per-DAN total counts too. Label these observed spikes, not proven pulse-evoked spikes or accepted causal impulses: a coincident endogenous spike cannot be attributed to a pulse without a counterfactual. No new native instrumentation is required. Acquisition paired/shuffled/timing-unpaired each request 96 home plus 1,056 away impulses per panel, total 1,152; their placement differs as declared.

Acquisition unit-gain pre-probes are shared across arms AND training panels within a cue family because gains, schedule and probe seeds are identical. This is one shared pretraining measurement, not two independent pretraining panels. Each family has:

- training: 2 panels × 5 arms × 24 exposures × 2 trials = 480 calls;
- unit pre-probes: 2 cues × 4 seeds = 8;
- interim probes: 2 checkpoints × 2 cues × 5 arms × 2 panels = 40;
- endpoint probes: 4 seeds × 2 cues × 5 arms × 2 panels = 80.

That is 608 per family, 1,216 for both. Reversal has 240 training, 40 interim and 80 endpoint calls, PLUS 8 shared unit-gain baseline calls and 16 acquired-parent calls under the reversal schedule. Reversal therefore totals 384, and the non-replay program totals 1,600, not 1,576.

Add exactly 32 explicitly selected replay calls:

1. Replay the first paired-arm acquisition cue trial and its blank companion for each family/panel: 2 trials × 2 families × 2 panels = 8. Start from the saved pre-cue gains and use the two original seeds.
2. Replay the first reversal trial in each branch/panel from its saved parent gains and original seed: 5 × 2 = 10.
3. Duplicate both frozen cue probes at the first fresh probe seed for four paired acquisition endpoints, two backward-erasure-plus-swap final checkpoints and the one shared reversal unit baseline: 7 checkpoints × 2 cues = 14.

Replay clones must reproduce every numerical output and gain array byte-for-byte; wall time is excluded. Discard replay state. These establish selected-trial and selected-probe determinism, not a complete training-trajectory replay. Schedule replay next to its corresponding original call where possible. Planned full program is **1,632 calls**, hard ceiling **1,640 calls and 1,200 wall seconds**, frozen before any conditioning output. The eight spare calls do not authorize an additional adaptive experiment. Preserve gate-failed and budget-stopped stages explicitly; only executed, complete required matrices can pass.

## Probe identity and KC partition

Acquisition probes use 400 ms duration, `[0,300)` cue, no teaching and no plasticity. Pre/end fresh seeds are 2,000,042 through 2,000,045, common across checkpoints and arms. For interim curves use the fixed nontraining seed 2,001,042 at both checkpoints; this is descriptive and separate from the four fresh-seed endpoint gate.

Every reversal response comparison uses **800 ms duration with cue `[300,600)`**, no teaching, no plasticity, and fresh seeds 5,000,042 through 5,000,045. Remeasure unit gains, both acquired parents and all final branches this way. Use fixed seed 5,001,042 for reversal interim curves. Never compare the 400 ms acquisition response directly with an 800 ms reversal response: identical numerical seeds do not align sensory randomness after a 300 ms silent interval, because the engine continues drawing sensory random values. Store schedule and seed identities with each response.

Define `R_c(g,q,s)` as total cue-window spikes in MBON population c, divided by its cell count and the 0.3-second cue duration. It is a within-population mean in Hz. Do not subtract home and away raw Hz, standardize a new decoder, or recenter predictions for these gates.

For each family, freeze KC preference from the four shared unit-gain acquisition probes: each KC's unweighted mean cue-window count for first cue minus second cue. Positive, negative and exactly zero define first-preferred, second-preferred and tied sets. Map this fixed KC classification onto existing eligible edges, separately for home-all and away-gamma. Never repartition at an acquired or reversed checkpoint. Both preferred sets must be nonempty in each channel; tied/shared edges remain reported but do not enter preferred-versus-other contrasts. Contact-count weighting is not part of the gate.

For code specificity, define each active KC set using at least one spike in the cue window. Within-cue stability is mean Jaccard over the six unordered fresh-seed pairs, separately for each cue. Between-cue overlap is mean Jaccard over all 16 cross-cue seed pairs. Both within means must exceed the between mean, and the between mean must be at most 0.5. Empty union has Jaccard 1, consistent with the existing guard, and empty preferred sets fail separately. This shared pre-probe gate is evaluated once per family. Preserve all pairwise values so a mean is not mistaken for a per-pair guarantee.

## Gain and acquisition definitions

For fixed eligible edge set S, `G_S(g)=mean(g_e for e in S)` is an arithmetic mean per eligible edge. Save edge counts, sums and distributions as secondary evidence, but do not compare sums of differently sized preferred sets in the conditioning selectivity gate. This differs deliberately from the frozen diagnostic panel, whose criteria remain gain SUMS; do not modify those criteria or reuse their units here.

For channel c and its taught target cue q versus other cue o, acquisition response selectivity is

`C_R = [R_c(g,q,s)-R_c(1,q,s)] - [R_c(g,o,s)-R_c(1,o,s)]`.

Gain selectivity is

`C_G = [G_target(g)-1] - [G_other(g)-1]`.

Both must be negative in each training panel. Every fresh response seed must have strictly negative selectivity. Apply the original 3× control magnitude test separately to response selectivity and gain selectivity: paired magnitude must be at least three times the largest absolute corresponding shuffled, timing-unpaired, untaught or frozen/error value. Use the four-seed mean response contrast for this panel-level comparison; keep every seed's sign requirement. Exact equality at 3× satisfies “at least”; zero effect never passes the separate strict-sign and nonzero-error tests.

A negative difference alone is insufficient: require the taught target response itself to decrease from its same-seed unit baseline and the target-preferred mean gain itself to decrease from one. Their magnitudes must exceed the corresponding numerical/frozen replay error. Otherwise a result driven only by potentiation of the other cue would be mislabeled depression. Retain both absolute components, not just the contrast. All existing non-finite, byte-change, bound-hit, matrix and family/seed separation failures remain failures.

Compute error on the same statistic being gated from duplicated numerical outputs or matched frozen/unit probes; do not invent a data-dependent epsilon. Exact replay is an independent bytewise requirement, so an error-producing replay is a software failure rather than an opportunity to enlarge tolerance. Any exact bound equality or excursion in an updated gain is a bound hit even if an instrumentation counter counts only strict clipping.

## Strict reversal and comparator definitions

Before reversal training, the acquired parent must still express the original mapping in the matched 800 ms fresh probes. For every fresh seed, old target MBON responses must be below matched unit baselines and both original within-channel selectivity contrasts must be negative. The old target-preferred mean gains must be below one. Otherwise report `parent_mapping_gate_failed` and do not execute a valid-reversal claim from that parent. Never alter the parent to manufacture a suitable starting memory.

For old target set/cue (home/A and away/B), define response recovery movement `M_R=R_final-R_parent`, and gain recovery `M_G=G_old(final)-G_old(parent)`. Require positive movements, smaller absolute distance to the matched unit response/mean gain one than the parent, and the original 3× magnitude separation from untaught-exposure and frozen-retention/replay error. Apply response recovery and distance tests at every fresh seed in both panels; gain tests apply to each panel's single saved vector. These are recovery of the fixed preferred-edge MEAN and MBON population response. Report individual gain distributions; do not claim every synapse returned to its former state or that the entire circuit's memory was erased.

New associations are evaluated against the acquired parent, not unit gains: target is B for home and A for away. Form the analogous new-target-minus-other-cue response and gain CHANGE contrasts from parent to final. Require negative new-target selectivity and actual new-target MBON depression from its same-seed parent response, plus actual new-target-preferred mean gain depression from its parent value. The absolute requirements prevent old-response recovery alone from masquerading as newly acquired suppression.

For these new-association selectivity contrasts, retain the 3× threshold using untaught-exposure and frozen-retention/error as the reversal null comparators. The five-branch reversal design has no shuffled or timing-unpaired branch; do not silently claim those acquisition controls were repeated. Continued acquisition is an opposite-direction positive control, required to retain the old mapping. Its intentionally large opposite-sign learning magnitude is NOT a null-noise threshold. Ordinary contingency swap is a positive new-learning comparator, not a null and not something the strict branch must exceed threefold.

Define response preference flip separately, relative to the matched UNIT baseline under the reversal schedule:

`P_home(g,s) = [R_home(g,A,s)-R_home(g,B,s)] - [R_home(1,A,s)-R_home(1,B,s)]`

`P_away(g,s) = [R_away(g,B,s)-R_away(g,A,s)] - [R_away(1,B,s)-R_away(1,A,s)]`.

Both acquired-parent values must be negative, both strict-final values positive, and both continued-acquisition values negative at each fresh seed. This is a within-channel baseline-corrected response test, not a fitted home/away decoder. Frozen retains its acquired gains byte-for-byte. Every branch starts from the exact acquired hash. Resetting gains, new-channel depression without old recovery, old recovery without new-target depression, gain-only effects and response-only effects fail strict reversal. Ordinary swap with a preference flip but no old recovery is reported as dual-channel remapping without erasure.

## Sources, interpretation and entry-test status

The reviewed biological anchors support testing these distinctions, not the chosen numerical protocol. [Hige et al. 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4674068/) supports cue-specific KC–MBON depression and compartment-dependent timing, with a backward condition that did not produce a universal opposite-sign effect. [Handler et al. 2019](https://pubmed.ncbi.nlm.nih.gov/31230716/) supports temporally ordered opposing plasticity pathways and behavioral reversal in studied fly compartments. [Jiang and Litwin-Kumar 2021](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009205) implements rate-based plasticity within a separately optimized recurrent model. These primary sources were inspected during the preceding source investigation; the full Handler article remained unavailable, so its use is limited to inspected abstract/primary indexed figure material.

The present raw-event male-CNS model lacks reconstructed receptor chemistry and a learned biological prediction-error circuit. Explicit early-old/late-new stimulation is an engineered reversal intervention. Because reversal does not include shuffled/time-unpaired branches, and population exposure differs per cue despite aggregate matching, it cannot isolate a biological backward-timing mechanism. Even a strict pass establishes aggregate old-response/old-gain recovery and new cue association under these schedules, not universal physiological erasure or sports competence.

Existing entry-test names checked in the code:

- `test_instantaneous_teaching_has_no_refractory_bank`, `test_refractory_teaching_rejection_is_per_dan`, `test_recurrent_delivery_obeys_target_refractory_boundary`, `test_recurrent_delivery_preserves_sensory_zero_refractory`;
- `test_candidate_matches_pairwise_reference`, `test_warm_up_events_before_onset_carry_no_eligibility`, `test_traces_reset_between_trials_and_repeated_trials_add_up`, `test_disabled_plasticity_records_zero_terms_and_leaves_gains`;
- `test_legacy_reference_potentiates_after_stimulus_offset_and_candidate_does_not`, preserving the named baseline and raw silent-offset contracts;
- `test_masked_edge_keeps_transmitting_and_never_updates`, `test_per_step_impulses_weight_unequal_edge_multiplicity_and_masks`, `test_gamma_policy_restricts_away_to_gamma_kcs_and_never_filters_home`;
- `test_recording_does_not_change_dynamics_or_gains`, `test_per_step_series_reconstruct_the_applied_change_exactly`.

At the time of this review, the existing `residual_trace_after_long_silence` matrix case has approximately 400 ms separation but tau 10 ms, so its expected change is effectively zero; it does NOT prove nonvanishing behavior at production tau 500 ms. Root reports Task 2 is adding independent native tests at production eta/tau for 50/100/500/1,000 ms in both orders, coincidence and population normalization. Inspect and name those actual tests in the Task 2 review before treating that entry gate as satisfied. The independently expected isolated-pair magnitude is `eta*exp(-abs(lag)/500)`; at 500 ms it is about 0.00018394, readily nonzero in float gains. No test or new experiment was run by this reviewer.

The original panel pass is established as stored evidence. Held-out mechanism qualification, the new long-lag regression receipt and complete schedule/evaluator/ancestry tests remain entry requirements. This addendum resolves definitions before any conditioning measurement; it does not assert those unperformed stages passed.
