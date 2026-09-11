# On-circuit dopamine-association experiment

This separate experiment adds learning inside the full 166,700-neuron MaleCNS
graph. It uses 4,064 Kenyon cells, 24 selected dopamine neurons and 8,866 existing
KC-to-MBON edges. It leaves the active v1 checkpoint and paused v2 artifacts
unchanged. [Measured results and sources](evidence/reward-v3-summary.md).

Actual KC and DAN spikes update bounded synaptic gains using exponential timing
traces. Gains persist between trials; membrane state and traces reset. PPL101 /
MBON11 (γ1pedc) is assigned to home outcomes and PAM12 / MBON09 (γ3) to away
outcomes. The away mapping was PAM11 / MBON07 (α1) in schemas 1 and 2; with
labeled-line sensory drive the α1 output receives about a quarter of the KC
contacts per cell that MBON11 does and stayed near 0 Hz at every non-runaway
drive, so it could not carry a readout. These
task mappings and the event-based modulation rule are explicit approximations,
inspired by mushroom-body learning research. Receptor-dependent chemistry,
precise synaptic compartment localization and biological reward-prediction error
are not reconstructed. [Detailed design and native contract](superpowers/specs/2026-09-11-dopamine-learning-design.md).

The dopamine drive in the rule is the raw compartment-mean DAN spike count
(schema 4, `dan_reference: none`). Each trial, plasticity and its eligibility
traces start at a declared onset (100 ms); the gain of edge KC j to a MBON of
compartment c changes at each step by
`eta * (Dbar_c * K_j - Kbar_j * D_c)`, where K_j is the KC spike indicator, D_c
the compartment-mean DAN spike indicator, and the bars are exponential traces
(tau 500 ms) that exclude the current step. KC before DAN depresses, DAN before
KC potentiates, same-step events are neutral. This is the form of the inspected
upstream rule (Jiang and Litwin-Kumar 2021, `runmodel.py`, pinned in
`docs/evidence/reward-repair-phase1.md`). The 50 ms window before the onset
still measures each compartment's tonic DAN rate, which is reported but not
subtracted.

Schemas 2 and 3 subtracted that tonic rate in both terms (`dan_reference:
tonic-baseline`, still selectable for comparison). On the calibrated circuit
that reference was stimulus-driven: PPL101 fires at about 38 Hz during the
stimulus because the Kenyon cells drive it directly, and falls to about 3 Hz
after stimulus offset, so the subtracted signal turned negative after 300 ms and
potentiated every home synapse with residual eligibility on every untaught or
away-taught trial (about +2 gain-sum per trial), while home teaching pulses only
restored the reference rate and netted almost nothing. The schema-4 rule removes
that artifact by construction. The first pilot (schema 1) had fed raw DAN spikes
into the rule under a saturated circuit (PPL101 near its refractory ceiling,
56 percent of KCs firing in every bin); the drift seen there belonged to that
circuit state, not to the rule form.

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
the anatomy. The current default is `all`; the gamma restriction is a separate,
separately identified change.

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
(residual PPL101 firing against still-high KC eligibility, reproduced exactly
from the recorded eligibility mass) and half inside the stimulus, where the two
rule terms cancel to a few percent; a direct KC to PPL101 pathway in the graph
(24,068 contacts) is a candidate explanation consistent with the observed lag
asymmetry, not an established cause. This is an open finding (SCI-001) under
review; conditioning, reversal and readout centering have not been run.
Evidence: `docs/evidence/reward-repair-phase1.md`.

Open **Training → On-circuit reward learning**. Inspect each arm's progress,
scores, confusion table, gain curve, DAN response and downloads. The active v1
identity and original v2 tracker remain visible. The API reads saved manifests;
the UI has no training, activation or promotion button.

From the repository root, the reproducible entry point is:

```sh
.venv/bin/python -m bet36fly.reward_experiment --protocol configs/reward-v4-candidate.json
```

`configs/reward-v3-pilot.json` is the historical schema-3 protocol; the runner
now requires schema 4, and no schema-4 sports pilot has been run.

A matching experiment identity cannot be resumed or rerun automatically. The 900-second
budget is checked before and after native trials and before success. A native
call can finish after the deadline, but the run then stops without claiming
completion. Protocol, code snapshots, data indices, graph hashes, gains and
per-DAN spike bins are retained under the new experiment directory.
