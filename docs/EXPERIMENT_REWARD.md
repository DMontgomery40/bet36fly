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

The dopamine drive in the rule is phasic (schema 2). Each trial, plasticity and
its eligibility traces start at a declared onset (100 ms). The 50 ms window that
ends at the onset measures each compartment's tonic DAN rate, and that rate is
subtracted from the DAN population signal in both rule terms. Tonic firing then
carries no teaching, and only deviations from it, such as the outcome pulses,
move gains. This stands in for the adaptive dopamine baseline reported in real
flies (Rajagopalan et al. 2023; Bennett et al. 2021), not for its circuitry.
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

Open **Training → On-circuit reward learning**. Inspect each arm's progress,
scores, confusion table, gain curve, DAN response and downloads. The active v1
identity and original v2 tracker remain visible. The API reads saved manifests;
the UI has no training, activation or promotion button.

From the repository root, the reproducible entry point is:

```sh
.venv/bin/python -m bet36fly.reward_experiment --protocol configs/reward-v3-pilot.json
```

A matching experiment identity cannot be resumed or rerun automatically. The 900-second
budget is checked before and after native trials and before success. A native
call can finish after the deadline, but the run then stops without claiming
completion. Protocol, code snapshots, data indices, graph hashes, gains and
per-DAN spike bins are retained under the new experiment directory.
