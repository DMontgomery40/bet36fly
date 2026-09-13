# On-circuit dopamine-association experiment

**Legacy protocol; research priority changed September 13, 2026.** Preserve this experiment's controls, identities and SCI-001 HOLD. The [current direction](PROJECT_DIRECTION.md) and [new handoff](NATURAL_SENSORY_HANDOFF.md) begin with natural sensory calibration and a plasticity-off response assay. That separate assay does not require this learning gate to pass. Nothing in this update qualifies the legacy mechanism or authorizes its historical unrun candidates.

**Status checked September 13, 2026 UTC:** the working checkout includes the
retained raw-D and gamma-mask options, corrected refractory input handling and
the numerically verified `rate-bridge-v1`. Both corrected raw and bridge rules
pass the original diagnostic panel but fail the second panel's untaught-home
guard (SCI-001). Retaining pre-onset history in a fixed-spike shadow made the
failure worse and was rejected. Conditioning and reversal have not run.
Read the [current reassessment](../wiki/reassessment.md), [cell atlas](../wiki/cells/index.md)
and [current repair evidence](evidence/reward-mechanism-repair-2026-09-12/index.md).
The later four-arm handoff is a specification, not a completed repaired pilot.
`configs/reward-v4-candidate.json` is a historical, unrun candidate with the old
three-arm/all-away-input protocol; it is not approved for execution.
The reward kernel now rejects instantaneous input during target refractory;
[the exact timing contract and regression scope](evidence/reward-refractory-contract-2026-09-12.md)
distinguish this correction from the unchanged historical v1 behavior.

This separate experiment adds learning inside the full 166,700-neuron MaleCNS
graph. It uses 4,064 Kenyon cells, 24 selected dopamine neurons and 8,866 existing
KC-to-MBON edges. It leaves the active v1 checkpoint and paused v2 artifacts
unchanged. [Measured results and sources](evidence/reward-v3-summary.md).

Actual KC and DAN spikes update bounded synaptic gains using exponential timing
traces. Gains persist between trials; membrane state and traces reset. PPL101 /
MBON11 (γ1pedc>α/β) is assigned to home outcomes and PAM12 (γ3) / MBON09 (γ3β′1) to away
outcomes. The away mapping was PAM11 / MBON07 (α1) in schemas 1 and 2; with
labeled-line sensory drive the α1 output receives about a quarter of the KC
contacts per cell that MBON11 does and stayed near 0 Hz at every non-runaway
drive, so it could not carry a readout. These
task mappings and the event-based modulation rule are explicit approximations,
inspired by mushroom-body learning research. Receptor-dependent chemistry,
precise synaptic compartment localization and biological reward-prediction error
are not reconstructed. [Detailed design and native contract](superpowers/specs/2026-09-11-dopamine-learning-design.md).

The integrated phase-1 candidate adds raw compartment-mean DAN spikes
(`dan_reference: none`) and immutable anatomical eligibility masks. Its per-step
rule is `eta * (Dbar_c * K_j - Kbar_j * D_c)`, with exponential traces excluding
the current step. KC before DAN depresses, DAN before KC potentiates, and isolated
same-step pairs are neutral. This is an event-based approximation to the inspected
Jiang and Litwin-Kumar rate rule, not an established spike-to-rate equivalence.
The tonic rate remains reported but is not subtracted. Removing that subtraction
removes its signed-reference contribution; residual untaught-home depression
still fails SCI-001. [Preserved phase-1 evidence](evidence/reward-repair-phase1.md).

The separately versioned bridge uses actual events to drive 100 ms rate filters
and 500 ms eligibility filters, with normalization 0.96 and learning rate 0.0005.
Exact continuous integration retains a double gain accumulator within each trial
and publishes float32 gains for transmission. An explicitly recorded analytic
no-new-event tail updates gains after the 400 ms electrical endpoint; it does not
simulate further neural activity. The second panel `dea14759e9ca` fails at
home/base mean −0.272640035 against absolute limit 0.240845235, with no bound
contacts. Numerical correctness and a smaller drift do not close the gate.
[Exact rule/state/tail contract](../wiki/learning-rule.md),
[independently checked measurements](evidence/reward-mechanism-repair-2026-09-12/index.md).

Schemas 2 and 3 use a signed phasic dopamine proxy (`dan_reference: tonic-baseline`),
still selectable for historical comparison. Each trial, plasticity and
its eligibility traces start at a declared onset (100 ms). The 50 ms window that
ends at the onset measures each compartment's tonic DAN rate, and that rate is
subtracted from the DAN population signal in both rule terms. This signed proxy
was intended to suppress tonic drift, but the later diagnostic found positive
gain updates after stimulus offset when activity fell below the earlier reference.
It cannot be described as making untaught activity neutral. The original motivation
was adaptive dopamine baselines discussed in fly research and models, not a
reconstruction of their circuitry. [Exact rule and limitations](../wiki/learning-rule.md).
The first pilot (schema 1) fed raw DAN spikes into the rule; with PPL101 firing
near its refractory ceiling and PAM11 at tens of hertz without any teaching, the
gains drifted identically in the paired and shuffled arms, and the fixed readout
turned that shared drift into all-away predictions.

Schema 3 replaces the sensory interface and calibrates the drive. The v1/v2
encoder drove the same 32 ALPN ports for every game and only varied their rates,
so the active KC set was 98 to 99 percent identical between games. The new
glomerular identity code treats each annotated cholinergic ALPN type that
reaches Kenyon cells with at least 100 contacts as a glomerulus (64 of 82
qualify and divide evenly; the weakest surplus type stays undriven). Each of the
16 standardized features owns four glomeruli with preferred values at −1.5,
−0.5, 0.5 and 1.5; a glomerulus fires all of its sister projection neurons at a
Gaussian-tuned rate (width 0.5, peak 150 Hz) of its feature's value and is
silent below 5 percent of peak. Which of the 275 driven ports fire therefore
depends on the game, borrowing the fly's odor identity code as an explicitly
engineered interface. This is not a claim that these glomeruli represent sports
quantities. [Encoder module](../bet36fly/reward_encoder.py).

Three cell-type gains, all recorded in the protocol and anatomy, correct
giant-neuron artifacts of a uniform LIF on this graph. Synapses onto the 686
ALPN ports are scaled by 0 (labeled lines): as signed here, the antennal lobe's
local neurons are mostly cholinergic (the dataset's own ground truth for lLN1
types), so once kicked the lobe re-excited its projection neurons at the
refractory ceiling indefinitely and drove 95 percent of all spikes. Synapses
leaving the two GABAergic APL neurons are scaled by 0.25: real APL inhibition is
graded and non-spiking, while this spiking proxy delivered about 60 mV per spike
pair onto the MBON11 cells and silenced every readout. Synapses onto Kenyon
cells are scaled by 1.25 to restore coincidence-driven KC firing. With these
settings 16 percent of KCs fire at about 10 Hz during the stimulus, 0.5 percent
still fire after offset, both readout MBONs respond at 40 to 50 Hz on every
calibration game, PAM12 is silent at baseline, PPL101 fires tonically at about
40 Hz (subtracted by the phasic rule) and the calibration KC-set overlap is
0.31. About 600 antennal-lobe local neurons keep reverberating after offset;
they do not reach the KC, DAN or MBON populations. Calibration sweeps are
recorded in the evidence note.

Before any arm trains, the activity gate has to pass. Besides the numerical
guards on KC activity and MBON rate, it now requires that each teaching
population evoke at least half of its scheduled forced spikes above the same-seed
unpulsed probe (a population already at its refractory ceiling cannot carry
teaching), and that the active KC set differ between calibration games (mean
pairwise Jaccard overlap of at most 0.5). It also records the tonic DAN rate of
each compartment and the fraction of KCs still firing after stimulus offset. A
failed gate stops the run before any arm and reports each failed guard.

The fixed protocol uses 64 chronological MLB training games, 32 reused validation
games and 16 training-only calibration games plus three activity probes. The
48-hour/UTC-day availability rule excludes late training labels. Each trial
lasts 400 ms, with 300 ms sensory input and outcome-teaching pulses at 310, 330,
350 and 370 ms. No teaching or gain update occurs in evaluation.

All three arms share initial gains, input seeds, half-strength fast transmission,
the three cell-type gains and zero direct fast outputs from 392 pure dopamine
neurons. Only the selected DANs modulate the plastic edges. These altered
dynamics belong to this engine; KC activity is still denser than the 5 percent
reported in real flies, even when numerical guards pass.

The readout is fixed before training: negative standardized log MBON response
plus a smoothed training-frequency prior. Calibration fits means/scales, with no
response-to-label coefficient optimization. True-outcome teaching is compared
with shuffled teaching, frozen gains, and the prior. The data and single seed
make this a development experiment; it cannot establish a bookmaker edge.

Plasticity eligibility (schema 4, `away_plasticity_mask`) is a per-edge mask
built from the released KC type labels. Under `gamma` the PAM12 / MBON09
channel updates only edges from gamma Kenyon cells (the documented compartment
approximation for gamma3); excluded alpha-prime/beta-prime and alpha/beta edges
keep transmitting at their current gain and never update. Home is never
filtered, because MBON11 receives substantial alpha/beta and
alpha-prime/beta-prime input. The audit of edge counts by class is recorded in
the anatomy. The historical sports runner default is `all`; the gamma restriction
is implemented and used in the current mechanism diagnostics as a separately
identified change, verified on the diagnostic panel (excluded edges
never update, transmission identical, gamma updates identical to the unmasked
run; numbers in the evidence note).

**Mechanism status (2026-09-11, phase 1 of the reward repair).** On the frozen
diagnostic panel (8 calibration games, two seed sets, frozen / untaught /
home-taught / away-taught from blank gains; criteria predeclared before the
candidate ran) the schema-4 rule passed six of seven criteria: teaching-specific
effects of about -2.3 (home) and -3.6 (away) gain-sum per taught trial against
untaught changes of -0.29 (home) and exactly 0 (away); no cross-compartment
leak; no bound hits; bounded cumulative untaught change; bit-identical repeats;
identical sensory noise across conditions. The untaught operational guard
failed on home: the small untaught change is consistently negative (14 of 16
trials). Its recorded terms place half of it in the 10 ms after stimulus offset
(residual PPL101 firing against still-high KC eligibility, reproduced from the
recorded per-step eligibility mass and DAN events) and half in the later part of
the stimulus, where the two rule terms cancel to a few percent; a direct KC to PPL101 pathway in the graph
(24,068 contacts) is a candidate explanation consistent with the observed lag
asymmetry, not an established cause. This is an open finding (SCI-001) under
review; conditioning, reversal and readout centering have not been run.
Evidence: `docs/evidence/reward-repair-phase1.md`.

That paragraph is the preserved phase-1 result. Later corrected-raw and bridge
panels and the failed history shadow are separate identities, summarized at the
top of this document. The frozen [conditioning protocol](evidence/reward-mechanism-repair-2026-09-12/conditioning-preregistration.md)
and [addendum](evidence/reward-mechanism-repair-2026-09-12/conditioning-prerun-addendum.md)
require matched acquisition controls and reversal from acquired checkpoints,
including old-weight recovery. Their entry gate has not passed, so the 1,632-call
protocol has not run.

Open **Training → On-circuit reward learning**. Inspect each arm's progress,
scores, confusion table, gain curve, DAN response and downloads. The active v1
identity and original v2 tracker remain visible. The API reads saved manifests;
the UI has no training, activation or promotion button.

The historical candidate configuration is retained for provenance only. Do not
execute `configs/reward-v4-candidate.json`: its three-arm protocol and all-input
away default predate the accepted gamma restriction and later four-arm handoff.

`configs/reward-v3-pilot.json` is the historical schema-3 protocol; the runner
now requires schema 4, and no schema-4 sports pilot has been run.

A matching experiment identity cannot be resumed or rerun automatically. The 900-second
budget is checked before and after native trials and before success. A native
call can finish after the deadline, but the run then stops without claiming
completion. Protocol, code snapshots, data indices, graph hashes, gains and
per-DAN spike bins are retained under the new experiment directory.
