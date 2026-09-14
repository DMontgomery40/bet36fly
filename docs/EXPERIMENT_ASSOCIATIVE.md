# Associative learning on the MaleCNS circuit: causal learning contract

**Stage authorized September 13, 2026 (evening) by David: implement and demonstrate dopamine-dependent synaptic learning in the actual MaleCNS circuit, then test whether it improves sports prediction.** This is a new experiment family with its own engine, identities and gates. It does not reopen the legacy PPL101/PAM12 reward diagnostic, whose SCI-001 HOLD and rejected candidates remain as recorded. The frozen 2023 sensory confirmation remains the only qualified sports result until the stages below pass.

This document predeclares the contract before each stage runs. Measured outcomes are recorded in the dated evidence folder [`docs/evidence/associative-learning-2026-09-13/`](evidence/associative-learning-2026-09-13/index.md), never edited into the criteria after the fact.

## 1. Three things kept separate

| Claim class | Content used here |
| --- | --- |
| Biology in real flies | Odor → Kenyon cells (KCs). Sugar reward → PAM dopamine neurons of the γ4, γ5, β′2 and α1 compartments. Dopamine after KC activity depresses that KC's synapse onto the compartment's MBON (DopR1/cAMP), dopamine before KC activity potentiates (DopR2), on a seconds timescale, presynaptically and independent of MBON spiking (Hige 2015; Cohn 2015; Handler 2019). Appetitive memory is expressed as reduced odor drive of the avoidance-promoting glutamatergic MBONs γ4>γ1γ2 (MBON05) and γ5β′2a (MBON01) (Aso 2014 eLife 04580; Yamagata 2015). Sweet-taste short-term reinforcement is carried by PAM neurons to β′2 and γ4, nutrient long-term reward to γ5b (Huetteroth 2015): γ4/PAM08 is the closest match to a taste reward, γ5/PAM01 is a sugar-reward compartment of the nutrient/long-term kind. Primary-source records with DOIs and the 2026-09-14 check are in the evidence index. |
| Information in the released dataset | 2,635 ORN cells of 53 `ORN_*` types; 4,064 KCs (1,557 γ); PAM08 (γ4) 50 cells; PAM01 (γ5) 44 cells; KC→MBON05 1,999 edges (1,839 from γ KCs, 35,977 γ contacts); KC→MBON01 2,109 edges (1,578 γ, 34,697 γ contacts); 34 proposed sweet LB3b/c cells with excitatory two-hop paths to PAM01 (834 contacts), PAM11, PAM02, PAM12, PAM04 and PAM08, but zero direct contacts onto any DAN, KC or MBON. Dataset type names are Aso-style compartment labels; synapse positions inside a compartment are not used. |
| Mechanisms implemented in this simulator | `bet36fly/associative_lif.cpp` + `bet36fly/associative.py`: Shiu-style LIF on the full retained graph at 0.11 mV/contact with three declared interventions (Section 3); multiplicative gains on the listed KC→MBON edges; a per-step opposing-term rule driven by compartment-mean dopamine spikes and exponential eligibility traces; an engineered Poisson reinforcer drive of the reward DANs. Everything else (odor code, team mapping, outcome-to-reward translation, readouts) is engineered interface. |

## 2. Measured links before any learning (plasticity off, identity `associative-links-01`)

Recorded from the exploratory probes that fixed this contract; the frozen re-measurement is the first entry of the evidence index.

1. **Sweet taste → dopamine: absent.** 34 sweet cells at 58.9 Hz for 500 ms produced 1,304 spikes, none in any DAN, KC or MBON. The two-hop excitatory anatomy exists but does not transmit at 0.11 mV/contact; the earlier calibration record shows that raising the coupling to 0.165–0.22 makes taste input trigger persistent population activity instead. The natural reinforcer pathway is therefore **unresolved**. The reinforcer used below is an optogenetic-style drive of the same sugar-reward DAN types, declared engineered.
2. **Odor → KCs needs the antennal-lobe local-neuron intervention.** Four ORN types at 118 Hz with intact local-neuron output drove 18,400–24,000 spikes per 100 ms in the antennal lobe that never recovered after offset, with 17.8% of KCs active. With local-neuron output zeroed the lobe recovered within 100 ms.
3. **γ4/γ5 MBONs need the APL intervention.** The spiking APL proxy silenced MBON01 and MBON05 completely (21,582 and 31,192 contact-weighted inhibitory events in one odor trial); at 0.25 they stayed silent; at 0 MBON05 fired 80 spikes with 5% KCs active.
4. **Odor alone drives the reward DANs only weakly.** With the interventions of Section 3, the four-type probe odor produced zero PAM01/PAM08 spikes; the frozen re-measurement of the 16-type code produced 58 PAM01/PAM08 spikes summed over 34 cue keys (about 1.7 per cue trial, against 1,075 evoked by one reinforcer trial). Endogenous dopamine under cue-only exposure is therefore small but not zero for every cue; the untaught, unpaired and lesion arms measure its effect and the 3× criterion is applied to it, not to an assumed zero.
5. **Odor code calibration (30 MLB team keys plus the four conditioning keys, seed 17, frozen run `associative-links-cd33a0b4dfd97540c887`).** 16 of 53 ORN types per key at 118 Hz: KC active 98–988 cells (median 388, 9.5%), MBON05 12–97 spikes per 400 ms (no silent cue), pairwise KC-set Jaccard mean 0.140, max 0.443, recovery tail 0. Narrower codes (4–12 types) left most cues without a MBON05 response.

## 3. The circuit (`configs/associative-circuit-01.json`)

Full retained graph, 0.275 mV base replaced by the qualified sensory coupling 0.11 mV/contact, ACh +, GABA/glutamate/histamine −, ambiguous +. Three declared interventions with the measured justification above: antennal-lobe local-neuron (`ALLN`, 420 cells) outgoing weights ×0; APL (2 cells) outgoing ×0; pure-dopamine (392 cells) fast outgoing ×0. No KC input gain, no ALPN input gain, no global 0.5 scale: the legacy reward gains are not inherited.

Compartments and eligible synapses:

| Compartment | Dopamine population (D_c) | MBON readout | Eligible edges |
| --- | --- | --- | --- |
| γ4 | PAM08, 50 cells | MBON05, 2 cells, glutamate | 1,839 γ-KC → MBON05 edges of 1,999 (159 α′β′ and 1 αβ edge transmit but never update) |
| γ5 | PAM01, 44 cells | MBON01, 2 cells, glutamate | 1,578 γ-KC → MBON01 edges of 2,109 (531 α′β′ edges transmit but never update) |

Plastic gains are multiplicative on existing excitatory edges, bounded to [0.5, 1.5], initial 1.0, float32. The connectome is never edited.

## 4. Rule, units, state and lifetimes

Per 0.2 ms step, after spike detection:

```text
D_c      = (spikes of compartment-c DAN cells this step) / (cell count) × coupling_c      [spikes per cell per step]
K_j      = 1 if KC j spiked this step else 0
Δgain_k  = η × (D̄_c × K_j − K̄_j × D_c)          for each eligible edge k = (KC j → compartment c)
gain_k   = clip(gain_k + Δgain_k, 0.5, 1.5)
K̄_j     += K_j;   D̄_c += D_c                     (traces decay by exp(−0.2/τ) at each step start, τ = 1,000 ms)
```

η = 1 × 10⁻⁴ for conditioning (Section 5) and 2 × 10⁻⁵ for the sports stage (Section 6, declared before that stage because each cue receives up to ~90 reinforcements instead of 12). KC before dopamine depresses; dopamine before KC potentiates; an isolated coincident pair is neutral. The rule is the inspected Jiang & Litwin-Kumar opposing form in event units. It is not a receptor kinetics model; τ = 1 s is a model timescale consistent with the seconds-scale pairing windows reported in flies, not a measured value.

State lifetimes: membrane voltage, synaptic conductance, event queue and refractory clocks reset at every call. Traces reset at every call unless explicitly supplied; they are always returned. Gains persist on the engine; checkpoints store gains + SHA-256 + parent SHA-256 + circuit binding; restore refuses another circuit's checkpoint. A plasticity-off call is verified byte-identical afterwards. Electrical reset never touches gains.

Reinforcer: Poisson drive of every PAM08 and PAM01 cell at 30 Hz (requested), 400 ms, 68.75 mV events, ordinary refractory kept; requested events and evoked spikes are counted separately. Drive cells consume randomness only in bins where their rate is non-zero, so a schedule without drive reproduces the sensory engine's event stream exactly (tested).

Cue: a set of 16 ORN types chosen by SHA-256 ranking of `BET36FLY-team-odor-01:<key>:<type>`, every cell of those types at 118 Hz (Zhao 2022 anchor, uniform transfer is an assumption). Identical rule for every key.

Timing (20 ms bins): probe trial 700 ms, cue 100–500 ms, recovery check 600–700 ms; reinforcement trial 1,000 ms, cue 100–500 ms, reinforcer 500–900 ms (forward pairing: KC eligibility high, KCs silent), recovery check 900–1,000 ms; backward control: reinforcer 100–500 ms, cue 500–900 ms.

## 5. Stage 3 protocol: controlled cue learning (`configs/associative-conditioning-01.json`)

Cues A and B are keys `cue:A` and `cue:B` through the same odor code. Entry gate on unit gains (three seeds 3001–3003): every cue ≥ 81 active KCs (2%), MBON05 ≥ 8 spikes per 400 ms in every seed, A/B KC-set Jaccard ≤ 0.5, recovery tail ≤ 1% of stimulus spikes, generator binomial p ≥ 1e-6, finite states. If the gate fails the stage stops and reports the failing link.

Arms, each from unit gains, 12 exposures per cue in the order A B B A … (24 trials), training seeds 10,000 + exposure index identical across arms:

| Arm | A trials | B trials | Plasticity |
| --- | --- | --- | --- |
| paired | cue then reinforcer (forward) | cue alone | on |
| unpaired | cue alone; 12 reinforcer-alone trials interleaved (matched reinforcer exposure) | cue alone | on |
| backward | reinforcer then cue | cue alone | on |
| untaught | cue alone | cue alone | on |
| frozen | forward pairing | cue alone | off |
| lesion | forward pairing with dopamine→plasticity coupling zero in both compartments (drive delivered, spikes unchanged) | cue alone | on |
| swap | cue alone | cue then reinforcer | on |
| order | as paired, presented B A A B … | | on |

Endpoint probes: three fresh seeds × {A, B}, plasticity off, MBON05 and MBON01 spike counts in the cue window and the sampled KC counts. Readout is frozen across arms: raw cue-window spike counts, no fitted calibration.

Retention: from the paired checkpoint, five 1,000 ms blank trials with plasticity on, then the endpoint probes again; gains must be byte-identical and probes identical.

Reversal from the paired checkpoint, 24 trials each: (i) contingency swap (B forward-paired, A alone); (ii) backward erasure plus swap (A backward-paired, B forward-paired); (iii) untaught exposure (A and B alone); (iv) frozen retention (the swap schedule with plasticity off). Endpoint probes as above; (iii) and (iv) supply the null scales.

Acceptance (all fixed before the run; effect ratio 3):

- **Acquisition:** for the paired arm, mean over seeds of (ΔMBON05_A − ΔMBON05_B) relative to unit probes is negative in every seed, and its magnitude ≥ 3 × the largest |contrast| among unpaired, backward, untaught, frozen and lesion; the mean gain change on A-preferring eligible γ4 edges is ≤ −3 × the largest |null change|; frozen and lesion gains are byte-identical to unit gains.
- **Causal dependence:** lesion (coupling zero) produces no change while receiving the identical drive; backward pairing produces no depression of A (its contrast is ≥ 0 or smaller than one third of paired).
- **Cue identity and order:** swap depresses B not A (mirror criterion); order matches paired within 3 × null.
- **Retention:** as above.
- **Reversal:** branch (ii) flips the sign of the A−B preference with A recovery and B depression each ≥ 3 × the untaught change; branch (i) is reported descriptively (no extinction mechanism is implemented, so A is expected to stay depressed).
- **Audit:** zero bound contacts; untaught total |Δgain| reported (expected 0); max |Δgain| < 0.4; every endpoint probe keeps MBON05 > 0 (no loss of responsiveness); recovery tail ≤ 1% in every trial.

Budget: 389 planned native calls, cap 420, ≤ 1,800 wall seconds. Every call's counts, sampled traces, drive events, compartment rule bins, gain checkpoints (SHA-256 before/after) and probe responses are saved under `output/associative/<identity>/`.


### 5a. Conditioning-01 outcome and the predeclared conditioning-02 amendments

Conditioning-01 (`associative-conditioning-42845736c62d3ac9841e`) **failed under the criteria above** and is preserved as failed: the synapse-level effects were as predicted (paired A-edge depression −0.089 against untaught −0.0003, lesion 0, frozen 0, backward +0.082, swap mirror), but the MBON05-only response moved by 2–8 spikes against ±3 fresh-seed noise, the backward arm's predicted potentiation defined the "null" gain scale, and cue:A/cue:B shared 39% of their active KCs. [Full result and diagnosis](evidence/associative-learning-2026-09-13/conditioning-01-result.md).

Conditioning-02 (`configs/associative-conditioning-02.json`) declares, before its run and without touching the circuit, rule, η, bounds, timing or exposure counts: (i) the primary response readout is the summed cue-window count of both learned MBONs (MBON05 + MBON01), justified by the plasticity-off sensitivity measurement (all eligible gains at 0.5 reduce MBON01 by 55% and MBON05 by 29%); gain criteria stay per compartment on the γ4 eligible edges; (ii) the null set for the 3× criterion is unpaired, untaught, frozen and lesion, and the backward arm is a directional control whose predicted sign is potentiation (a criterion, not a null); (iii) cues are cue:E and cue:F, the lowest-overlap pair (Jaccard 0.128) among twelve candidate keys with at least 400 active KCs and 60 MBON05 spikes on unit gains; (iv) fresh probe seeds 3011–3013 and training seed base 20,000. Reversal, retention, audit and budget are unchanged.

**Conditioning-02 outcome** (`associative-conditioning-d1d3992e38c1dfa5fef1`, 389 calls): every predeclared criterion passed and an independent recomputation from the saved artifacts agreed. Paired summed-MBON contrast −12/−7/−7 spikes against a null scale of exactly 0 (no cue-only trial evoked a reward-DAN spike), γ4 A-edge depression −0.078 (B-edge −0.009), backward potentiation +0.076, lesion and frozen byte-identical, swap mirror, order match, retention exact, reversal by backward erasure plus swap recovered A (+8/+5/+13), depressed B (−10/−10/−8) and flipped the preference. [Result](evidence/associative-learning-2026-09-13/conditioning-02-result.md).

## 6. Stage 4 protocol: does plasticity contribute to prediction (`configs/associative-sports-01.json`, frozen before the development run)

Translation (engineered, identical for both teams): each team key `mlb:<id>` is a 16-type odor; the pregame quality → sweet-contact path of the confirmed sensory pipeline is unchanged and its frozen cache is reused only after a direct test that sweet probes are invariant to the plastic gains (sweet input evokes no KC spike). The outcome → reinforcer translation is: after a game's result becomes available (UTC-day batches, 48-hour delay, the same rule as the features), the winner's odor is presented with the forward reinforcer once (η = 2 × 10⁻⁵). The loser receives nothing (cue-only exposures are measured null in Stage 3). Prediction probes present each team's odor alone with plasticity off and never consume outcomes.

Arms with identical encoder, initial gains, seeds and data: plastic; matched frozen (same probes, plasticity off); reinforcement-shuffled (outcomes permuted within ISO week, matched reinforcer count); encoder-only; same-information conventional (logistic on encoder features plus each team's delayed cumulative wins, the information the circuit receives); uniform and training prior.

Readout, fixed procedure for every arm: L2 logistic regression without intercept (C = 0.01) on the four frozen innate response differences plus the two learned differences log1p(MBON count home) − log1p(MBON count away) for MBON05 and MBON01, fitted on the development block only.

Data audit and blocks: 2019–2021 trained the encoder; 2022 selected the sensory candidate; 2023 was the exposed confirmation; 2024–2026 were training/validation/test data of the historical v1/v2 models. Development block: 2022 (readout fit on games starting before July 1, evaluation on the rest, descriptive). Candidate budget: two learning rates (2 × 10⁻⁵ primary, 1 × 10⁻⁵ alternative) selected by development log loss. Reserved confirmation block: the 2018 MLB regular season, never accessed by any pipeline in this repository; it is fetched only after the candidate is frozen and committed. Primary metric: log loss; uncertainty: 10,000 paired complete-ISO-week bootstrap resamples, seed 20260913, one-sided α = 0.025. Acceptance: (a) better than chance as in the sensory protocol; (b) plasticity contributes if the plastic − frozen paired log-loss interval lies below zero and the reinforcement-shuffled arm does not. A repeat of the 2023-style chance-beating result without (b) is reported as "no incremental plastic contribution".

Compute: ≤ 3 × (games + 1) native calls per plastic arm per season, ≤ 4 wall hours per arm.

## 7. Backend and application

Training jobs run through `bet36fly/associative_jobs.py`: explicit state (`queued|running|completed|failed|cancelled|budget_stopped`), progress, cancellation, deterministic resume from the last completed checkpoint, per-checkpoint provenance, and a single job lock; inference reads a named immutable checkpoint and never updates weights. `/api/associative/*` exposes mechanism links, conditioning verdicts, sports evaluations and checkpoint readiness exactly as recorded; missing or failed evidence stays missing or failed. See [the application contract](api-contract.md).

## 8. Continual learning: dopamine-gated recovery (version-2 rule, September 14)

**Trigger.** In the 2022 season arms the plastic circuit hits the lower gain bound on its most active synapses after roughly 30 UTC days at η = 2 × 10⁻⁵ (per-day bound-contact counts are in each arm manifest). This is the bounded-weight failure described by Jiang & Litwin-Kumar 2021 (PLOS Comput Biol 17(8):e1009205, "Continual learning of associations"): long sequences of associations drive KC→MBON weights toward their minimum. The running 2022 arms are finished and scored unchanged as the **no-recovery baseline**; nothing in them is reinterpreted.

**Source rule.** JLK Eq. 5: `dw_ij/dt = r̄_i^DAN r_j^KC − r̄_j^KC r_i^DAN + β r̄_i^DAN`, β ≥ 0 per compartment, motivated by dopamine activation in the absence of KC activity potentiating KC→MBON synapses (their reference 33; Berry et al. 2012 Neuron and Berry, Phan & Davis 2018 Cell Reports show dopamine-neuron activity after learning restores the depressed MBON-γ2α′1 response and causes forgetting; Shuai et al. 2015 PNAS identify PAM-β′1 and MBON-γ4>γ1γ2 pathways for time-dependent decay; Handler et al. 2019 show dopamine-before-odor potentiation). Their Fig. 7 shows β keeps many weights potentiated after thousands of CS/US presentations.

**Implemented (circuit-02, `configs/associative-circuit-02.json`).** Per step, for each eligible edge whose KC has exactly zero eligibility trace in the current trial and whose gain is below rest: `gain += η·ρ_c·D̄_c·(rest − gain)`, capped at rest = 1.0. Deviations from JLK, each deliberate: (i) gated on zero KC eligibility so the qualified forward depression and backward potentiation on active edges are bit-identical to version 1 (tested); JLK apply β to every synapse; (ii) bounded toward rest, not toward the maximum weight, so already-normal synapses are never pushed past rest; (iii) event units and per-step traces as in version 1, β_c = η·ρ_c; (iv) no elapsed-time term at all: recovery occurs only while the compartment's dopamine trace is nonzero, i.e. during reinforcement of other cues, so no calendar-day-to-fly-time mapping exists. Rac1, DAMB, calcium, NO, consolidation and generic decay are deliberately not added.

**Predeclared tests before any sports use.** (a) Conditioning-03 (`configs/associative-conditioning-03.json`): the conditioning-02 battery re-run on circuit-02 for every ρ in the grid; must pass acquisition, retention, reversal, causal, timing, identity, order and audit criteria unchanged, plus no gain above rest. (b) Stress test (`configs/associative-stress-01.json`): eight cues reinforced in a fixed cycle for 24 cycles (192 reinforcements), probes of all cues every 4 cycles, then a fresh-pair acquisition/reversal battery from the long-history checkpoint; arms A = circuit-01 (no recovery) and B = circuit-02 at ρ ∈ {0.005, 0.01, 0.02, 0.04}. Measured: fraction of eligible edges at the lower/upper bound over time per compartment, gain deciles, recent-cue memory, oldest-cue memory, post-history acquisition and reversal. Selection rule, fixed now: the smallest ρ with lower-bound occupancy ≤ 10% after 24 cycles in both compartments, recent-cue depression ≥ 3× the frozen null in every seed, no gain above rest, and passing post-history acquisition; the old-cue forgetting is reported as the lifetime tradeoff and never used for selection. Sports outcomes are never consulted. (c) Only then: a new 2022 sports arm on circuit-02 with the selected ρ (new identities; the circuit-01 arms are kept), evaluated with the same fixed readout procedure against its own frozen/shuffled twins and against the no-recovery baseline.

**Outcome (September 14):** conditioning-03 passed at every ρ; the stress test reduced γ4 floor occupancy after 192 reinforcements from 20.4% (no recovery) to 3.9% at ρ = 0.005 with no gain above rest and post-history acquisition/reversal intact; by the fixed rule **ρ = 0.005** is selected (`configs/associative-circuit-02.json` now carries it). [Tables](evidence/associative-learning-2026-09-13/continual-learning.md). The 2022 recovery arms (`configs/associative-sports-02.json`) run next with the same three declared learning rates and the same readout procedure; the 2018 block stays held for the final candidate.
