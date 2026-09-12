# Independent mechanism and source investigation

Date checked: September 12, 2026 UTC. Scope: read-only scientific investigation after reading all 28 corpus chunks (81 complete documents); see `mechanism-sources-reading.md`. No neural experiment, offline candidate replay, production modification, gain tuning, sports pilot or child agent was performed. The following candidate is specified **before observing its replay results**.

## Finding and recommendation

The schema-3 signed-reference artifact is established. The raw-D candidate repairs that artifact but retains a separate mismatch: it turns a seconds-scale rate-learning idea into an odd, discontinuous-at-zero event-pair kernel with nearly maximal updates for arbitrarily short nonzero KC/DAN lags. This can interpret ordinary sensory-driven DAN timing as reinforcement. Existing recordings make that hypothesis plausible, not proven. The most defensible signal-model candidate is a normalized spike-to-rate bridge with an independently derived oracle and the unchanged SCI-001 thresholds. Root subsequently reported independently reproduced refractory-delivery defects. Correct and evaluate those verified native defects first, under a separate identity, before deciding whether this signal-model candidate is necessary. It must also demonstrate acquisition and reversal; making all updates tiny is not a repair.

This recommendation retains the anatomical graph, cell gains, encoder, accepted home/away assignment, fixed readout, 100 ms onset, 400 ms electrical trial and existing teaching schedule for the legacy diagnostic panel. Home remains all 4,184 supported edges. Away updates use its 3,239 gamma edges while all 4,682 away edges still transmit. It adds a learning-signal timescale; it does not retune circuit drive.

## Actual source and workspace state

Main HEAD read here: `26c3e9f6ae2ce58ca5131150375ef373047c50c3`. Main native kernel SHA-256 `ae78961d9bd14c909f7379aec3b0cb20b964729f57a69ec21ecb0c1ec16ab154`. Separate phase-1 HEAD: `81037f15118c1d9857e78aa579292e9a46327c09`; native SHA-256 `9b9dfb95deb74e37acbd3b569dce2b4b7aa28e1dec8b57579b19a86bc9d379e4`. Both kernels were inspected. The latter supports raw/legacy reference, mask and recording, but still computes instantaneous event/trace products and immediately clips float gains. Neither implements a spike-rate bridge, dopamine concentration or receptors.

Inspected historical evidence: candidate spec v1 and v1.1, phase-1 report, `attribution-diag-candidate-b57b80fdcdfc.json`, review 0019, and `codex-scratch/onset-history-and-mask-validation.json`, all under `output/collaboration/reward-repair/`. The report is not a rerun of these measurements.

### Primary-source ledger and limits

- [Jiang and Litwin-Kumar, 2021, PLOS Computational Biology, DOI 10.1371/journal.pcbi.1009205](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009205): reopened Results, Methods and pertinent supplemental descriptions. The authors justify continuous rates by a seconds-scale timing curve. Their rate-network time constant is 1 s; simulation step 0.5 s; CS/US duration 2 s. The network generating DAN signals, biases and readout is optimized. Thus taking only its plasticity expression does not inherit its conditioning, extinction or reversal results. It also reports direct KC→DAN connections without a qualitative loss of performance, so those anatomical contacts alone do not establish a pathological pathway here. Paper parameters are modeling choices, not measured MaleCNS receptor constants.
- [Jiang pinned `runmodel.py`](https://raw.githubusercontent.com/alitwinkumar/jiang_litwin-kumar_mb_rnn/a16f86a3e9e476eff6860c3c0e0e1bbe729d7f85/runmodel.py) and [pinned `definemodel.py`](https://raw.githubusercontent.com/alitwinkumar/jiang_litwin-kumar_mb_rnn/a16f86a3e9e476eff6860c3c0e0e1bbe729d7f85/definemodel.py), commit `a16f86a3e9e476eff6860c3c0e0e1bbe729d7f85`: both full files reopened. Code uses nonnegative DAN rates, update-before-trace order, eligibility 5 s, weight tracking 5 s and initialized maximal KC weights. Its `wfast` is recomputed from current `w`, then `w` tracks that value. Unclipped this introduces two factors of dt. Copying that literal discretization to a 0.2 ms step can suppress learning by timestep choice; it is not an appropriate unnoticed unit conversion.
- [Hige et al., 2015, Neuron, DOI 10.1016/j.neuron.2015.11.003](https://pmc.ncbi.nlm.nih.gov/articles/PMC4674068/): reopened full available article and targeted Figures 1–6/Methods. PPL1-γ1pedc pairing strongly depresses cue-evoked MBON response; postsynaptic spikes are unnecessary. Its backward condition (odor 0.5 s after the last light pulse) showed no effect. The same short pairing was ineffective in another compartment. Cue overlap permits some generalization, and untaught controls separate exposure effects. Therefore a universal backward-potentiation or identical-compartment biology assertion would be wrong.
- [Handler et al., 2019, Cell, DOI 10.1016/j.cell.2019.05.040](https://pubmed.ncbi.nlm.nih.gov/31230716/): abstract and primary indexed figure captions reopened. DopR1/DopR2-dependent depression/potentiation support order-sensitive association and reversal; reported γ4 timing conditions include −1.2, 0 and +0.5 s. Direct [PMC full-page](https://pmc.ncbi.nlm.nih.gov/articles/PMC9012144/) retrieval challenged/failed. This pass does not claim full Handler methods inspection. The source motivates a bidirectional phenomenology, but does not calibrate PAM12/MBON09 or PPL101/MBON11 kinetics.
- [Shiu pinned `model.py`](https://raw.githubusercontent.com/philshiu/Drosophila_brain_model/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960/model.py), `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960`: full file reopened; fixed LIF transmission foundation, no KC/DAN learning implementation there. Its sensory refractory exemption agrees with our engine. Its female FlyWire sensorimotor provenance does not validate male-CNS learning.
- [MaleCNS home](https://male-cns.janelia.org/) and [downloads](https://male-cns.janelia.org/download/): current indexed primary pages inspected, listing v1.0 June 8 and paper September 3, 2026. Download resources distinguish aggregate connectivity from synapse locations and transmitter resources. Release-page direct open failed. GitHub latest-commit/releases/open-issues API checks for Shiu/Jiang were attempted with bounded requests but shell DNS failed; pinned raw files succeeded through web. No newer-head or absence-of-new-issues assertion is made.

## What the recorded evidence establishes

The raw candidate's home update is reconstructed from actual events to about 1e-5 gain-sum. Most of the residual is later during the stimulus and within the first 10 ms after offset. There are no recorded untaught events after 305 ms. Advancing DAN events 20 ms nearly cancels the mean, reversing their order reverses its sign, while 5 ms jitter largely preserves it. These are sensitivities; they do not prove a specific upstream synapse causes the effect.

Warm-history replay is actively adverse evidence for an onset-only repair: adding pre-onset history changes mean attempted U from −0.2647 to −0.6416 (base −0.6735, alternate −0.6097). An onset-history correction may be scientifically interesting but is not a supported fix. Extending a raw-event trial after all events have ceased cannot produce additional raw-rule updates, even while traces remain; tail truncation is not the measured raw residual's cause.

The frozen SCI-001 criterion is scale invariant: multiplying all unclipped updates by any positive constant leaves `abs(mean)/SD` unchanged. Lowering eta, introducing a uniform slow factor or changing gain-sum to mean-edge units cannot honestly pass it. Float rounding that erases all learning could falsely yield 0 ≤ 0, so oracle and functional effect tests must explicitly reject numerical extinction.

One small discrepancy requires correction when integrating evidence: the fine-resolution JSON's lag-profile mean reaches **0.0541218 at +3 ms**. Phase-1 prose says the maximum is 0.037. This does not alter the causal limitation; use the saved numeric series.

## Predeclared candidate: normalized 100 ms rate bridge

### Scientific status and parameter choice

Call the rule `rate-bridge-v1`, preserving selectable historical rules. The bridge is an engineered model inspired by rate-based plasticity. It is not a receptor simulation, exact Jiang replication, or biological proof.

Retain existing eligibility τe = 500 ms. Choose rate smoothing τr = 100 ms once, before replay, from the source's 1:5 neuronal-rate/eligibility timescale ratio under a **declared 10:1 compression** (source 1 s/5 s → 100/500 ms). Existing 300 ms stimuli are not exactly compressed versions of the source's 2 s stimuli; explicitly retain that mismatch. Choosing 20 ms because it matches a favorable residual shift would be weaker justification. Neither paper prescribes a unique spike-to-rate filter, so this candidate remains falsifiable. Do not claim its 100 ms is measured dopamine clearance.

Do not add a separate slow weight state in this first discriminating candidate. That would add another state-lifetime assumption without testing the main event-versus-rate hypothesis. Source slow tracking is a known omission; if later introduced, it needs a continuous-time contract and independent identity.

### State, units and equations

For each KC j keep rate R_Kj and eligibility E_Kj. For each teaching compartment c keep population-mean rate R_Dc and eligibility E_Dc. Rates have spikes per **millisecond**; eligibility has spike units. Current raw observations are K_j ∈ {0,1} and D_c = number of actual DAN spikes / population size. Scheduled pulses are not substituted for actual events. D is nonnegative; the measured tonic baseline is diagnostic only.

At t < 100 ms all bridge rates and eligibility remain zero. At the onset start them at zero, preserving the historical exclusion of pre-onset events. This choice is explicit rather than described as biological necessity. Record pre-onset spikes, but do not silently warm either side. At each active step of h = 0.2 ms:

1. Add `K_j/τr` and `D_c/τr` to their respective rates at the step's left boundary. These are unit-area impulses into causal filters. Existing eligibility does not include the new events yet.
2. For each eligible edge form `Q = E_Dc*R_Kj − E_Kj*R_Dc` using the rates after event injection and prior eligibility.
3. Let `b = 1/τr + 1/τe`, `A = (1 − exp(−b*h))/b`, and `n = 1 − (τr/τe)^2 = 0.96`. Apply `delta = eta * n * A * Q`, with eta still **0.0005**, and existing positive bounds [0.5,1.5]. Record attempted and actually applied change separately.
4. Advance each eligibility exactly: `E_next = exp(−h/τe)*E + R*(exp(−h/τr) − exp(−h/τe))/(1/τe − 1/τr)`. Then `R_next = exp(−h/τr)*R`. Use the same pre-advance rates in each eligibility update. Double precision for learning states/accumulation is recommended; prove numerical error before downcasting gains for transmission.

Derivation (this investigator's mathematical proposal): between impulses, R decays on τr and E obeys `dE/dt = R − E/τe`. Consequently `dQ/dt = −b*Q`; A integrates the gain update exactly over the step. Both sides are treated symmetrically. Exactly coincident isolated KC and DAN impulses therefore generate no mutual directional update. Each new event can still interact with previous history, as it should. No extra dt factor is allowed.

### Tail and reset semantics

The bridge contains continuing rates after the last spike, unlike the raw-event rule. Truncating it at 400 ms would manufacture a new endpoint effect. At the end of the unchanged 400 ms electrical trial, analytically complete the bridge under an explicit **no-new-spike continuation**: `tail_delta = eta*n*Q_end/b`, clipped to the same bounds. With no new events Q has fixed sign while decaying, so this is equivalent to completing the monotone tail. Record this tail separately; it cannot be hidden in a measured 390–400 ms bin.

This continuation integrates only the declared learning signals derived from recorded spikes. It does not assert that the CNS was observed silent forever or run more neural time. Actual residual neural firing after 400 ms is outside this finite trial contract. All bridge states are then discarded. Gains, including tail changes, persist to the next electrical trial. Disabled plasticity must bypass every gain mutation, including the tail. Loading a checkpoint starts electrical and bridge states zero; it must preserve gains. If a later continuous protocol is desired, it needs a new state-persistence contract.

### Normalization and analytic oracle

For isolated unit KC/DAN events separated by positive lag ℓ, complete-tail gain change is:

`Δg(ℓ) = −eta*(exp(−ℓ/500) − exp(−ℓ/100))` for KC before DAN; sign reverses for DAN before KC; at exact coincidence it is zero.

This follows from convolving the raw odd exponential timing kernel with the autocorrelation of the identical causal rate filters. The n=0.96 factor cancels the coefficient τe²/(τe²−τr²), preserving the raw kernel's long-lag amplitude. It is derived from the filters, not fitted to measured U. At 500 ms the bridge retains about 98.2% of the raw isolated-event effect. At 50 ms it retains about 33.0%, while a 5 ms lag retains about 3.9%. Thus it discounts short ordering without making well-separated associations disappear.

Finite event histories have a pairwise superposition oracle when unclipped. Test the formula with independent pair summation, not another copy of the recurrence. Under bounds test against dense high-precision integration, because clipping invalidates simple pair summation. Tail location must be part of the recorded experiment identity.

## Falsifiable test and measurement contract

### Numerical tests before circuit replay

- Retain **all old raw/tonic assertions under their named historical modes**, including raw exponential timing magnitudes, onset exclusion, the signed-baseline offset artifact, mask transmission, learning-off parity, source identity and non-overwrite. Do not alter their expected values to fit the new rule.
- New-rule table: signed lags 0, ±0.2, ±1, ±5, ±20, ±50, ±100, ±500, ±1000 ms; same event count and complete tail. Compare to the analytic oracle with declared tolerance derived from numeric precision. Coincidence zero; antisymmetry; large-lag decay; 500 ms effect ≥95% of the raw effect and 50 ms effect ≥25% prevent suppression masquerading as a fix. These numeric floors follow the fixed analytic candidate rather than data tuning.
- Time-grid convergence at 0.1, 0.2 and 0.4 ms for exactly representable event times. Shift all events and the onset together while keeping their relationship fixed; gain change should not depend on absolute placement. Appending silent electrical bins before analytic drain must produce the same final gain when the event sequence is unchanged.
- Matrix of multiple events, simultaneous events, KC-only/DAN-only/empty, zero learning rate, no eligible edges, one versus replicated identical DAN populations, permuted plastic-edge ordering, both KC families and compartments. Check integrated effects and rates against an independent reference; verify all noneligible gain bytes untouched.
- Instrumentation on/off, disabled-plasticity native parity, checkpoint roundtrip and trial/reset transitions. Frozen probes may record hypothetical rule terms but must retain gain bytes exactly. Check float accumulation error and ensure nonzero analytically expected learning survives storage.

### Original operational panel

Run once with a new identity on the exact frozen 8 cues × 2 seed sets × F/U/H/A panel, then the original 16 U sequence, unchanged source rows/seeds/drive/teaching. Preserve v1.1 criteria verbatim: each channel/seed teaching effect negative and at least 3× mean U magnitude; each U mean ≤0.5 SD; cross-channel limits; cumulative limit; no clipping; deterministic repeat and same sensory randomness. Add rates, eligibility, step Q, in-trial/tail attempted/applied change and final gain vectors. Report normalized mean/SD and attempted changes so rounding cannot fake neutrality.

**Falsification:** any unchanged SCI-001 component failure, vanishing functional learning, oracle failure, drift transferred into an unreported tail, or unchanged/greater 5–20 ms sensitivity relative to the long-lag teaching effect rejects this candidate as a repair. Preserve the failed result; do not tune τr, eta, onset or the guard afterward under the same identity.

Use remaining calibration cues and a separately declared fresh-noise seed set as an additional held-out mechanism panel. The old panel is already development evidence; passing it alone is not independent confirmation. Do not replace a failed original seed set with the new one.

### Acquisition and reversal

Freeze cue identities without looking at taught outcomes; report same-cue fresh-noise stability, between-cue overlap, unique/shared eligible support and actual MBON responses. Minimum arms: paired, untaught plastic, genuinely timing-unpaired plastic, and frozen. A label shuffle does not test timing. Keep electrical duration/exposure, event counts and resets matched across timing arms. If separated timing needs a longer electrical interval, use that same new interval in all its arms and version it; never insert an unmatched reset that clears only unpaired traces.

Measure cue-specific gain changes and raw MBON response changes with plasticity-off fresh-noise probes from the same pre/post checkpoints. Prespecify a difference-of-differences between trained and control cues, plus paired-minus-untaught/unpaired contrasts. Require consistent direction in each tested channel and fresh-noise panel, with finite effect above numerical and frozen-noise error. Do not use probability centering, an optimized decoder or a common population decrease as acquisition evidence.

Reversal must clone the **acquired checkpoint** into continued-acquisition, changed-contingency, untaught-exposure and frozen-retention branches. Record checkpoint ancestry. Distinguish two questions: (1) can backward timing in the same engineered channel undo its stored depression and restore the cue response; (2) does an ordinary contingency swap reverse two cue associations without an explicit backward erasure schedule? The rate bridge predicts the first. It does **not** supply a prediction-error/omission circuit that guarantees the second. Do not call continued depression of a new channel, or resetting gains to one, erasure of the old association. Report both old/new cue preferences and recovery/retention of their original eligible synapses. A two-cue sign reversal without old-weight recovery is a different, weaker result and should be named accurately.

## Competing hypotheses and bounded decisions

1. **Event-timescale mismatch:** strongest actionable candidate above. Predicts reduced sensitivity to tiny lags while retaining 50–500 ms pairing and cue-specific effects. Can fail if coarse sensory/DAN coactivation remains systematically directional.
2. **Uncalibrated endogenous DAN generator:** anatomy may produce real sensory-evoked modulation inconsistent with the engineering task. Rate filtering cannot guarantee neutrality for a truly delayed rate envelope. If this remains, inspect causal inputs/functional DAN feedback rather than declaring the biology invalid. No contact deletion, extra inhibition or training-pulse-only mask is authorized by this report.
3. **Boundary/history model:** existing onset-warming evidence worsens raw drift; reject warming alone. The new rate bridge requires its own explicit tail; refusing to account for it would create a different boundary error.
4. **Global gain drift/readout sensitivity:** a real downstream amplifier of nonspecific changes, but centering cannot establish the missing association. Keep it deferred.
5. **Compartmental physiology mismatch:** Hige and Handler do not give one universal plasticity law. A successful symmetric bridge establishes a working engineered mechanism only. A future receptor/compartment model needs measured parameters and separate validation; changing the accepted anatomical channels now would confound this repair.

The recommended sequence is: correct independently reproduced refractory delivery defects; evaluate the corrected raw-event mechanism separately; then decide whether to implement this already prespecified rate-bridge candidate with oracle tests, original guard replay and controlled conditioning/reversal. Do not combine those changes into one causal comparison. A failed candidate remains a failed candidate. No claim of biological invalidity, sports success, promotion or completed repair follows from this source report.

## Later coordination update

Read the complete new plan `docs/superpowers/plans/2026-09-12-reward-mechanism-repair.md` after this report was drafted. Root reports native tests newly demonstrate banking of pulses and incoming conductance during refractory intervals. My own inspection confirms the kernel currently adds to v/g before checking readiness; Shiu specifies both states as unless-refractory. I have not yet reproduced the new tests independently, so the reproduction belongs to the kernel investigator. The verified simulator defect precedes the proposed model change: fix, identify and measure it separately before adopting rate filtering. This report's bridge remains a preregistered competing hypothesis, not a measured fix.
