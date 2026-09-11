# Dopamine-gated circuit learning

This implements the user's September 11 continuation: biological learning inside
the measured MaleCNS circuit, with an observable task-level experiment. The
existing v1 model and paused v2 matrix remain protected.

## What changes

A separate native engine advances the entire retained graph while accepting
time-varying sensory drive and explicit teaching pulses to annotated dopamine
neurons. Within a trial, membrane state and KC/DAN eligibility traces persist.
Across trials, membrane state and traces reset but KC-to-MBON gains persist.
Plasticity is computed from actual presynaptic KC and DAN spikes. A readout is
fixed before learning and is never fitted to the resulting responses.

The first application is a small MLB outcome-association pilot. Two annotated
circuits receive an explicitly engineered class mapping: PPL101 / MBON11 for
home and PAM11 / MBON07 for away. This is an artificial way of conveying the
task's outcome, not a claim that these cells naturally represent sports or that
reward-prediction-error feedback has already been reconstructed. The first
experiment tests outcome-gated associative learning, not autonomous wagering.

## Biology, released data, and assumptions

- MaleCNS v1.0 was released June 8, 2026; the publication/Google announcement
  followed September 3. The retained graph includes brain and ventral nerve cord.
- Raw annotations identify PPL101(y1ped), MBON11(y1pedc>a/B), PAM11(a1), and
  MBON07(a1). Only actual KC-to-selected-MBON graph edges may change.
- Type/instance labels support a targeted compartment approximation. Pairwise
  weights do not localize every contact within a neurite. Receptor dynamics and
  measured dopamine concentrations are not available in the retained data.
- The learning rule transfers the biphasic KC/DAN timing idea in Jiang and
  Litwin-Kumar (2021), not their entire optimized rate network. Exponential spike
  traces and numerical gain/dose scales are explicit engineering assumptions.
- Dopamine-only neurons are not assigned fast excitatory transmission in this
  new experiment. Their anatomical contacts remain recorded. The selected DANs
  act through the separate modeled modulation channel; other neuromodulators and
  receptor-dependent co-transmission remain unmodeled. All controls use the
  identical modified dynamics.

## Schema 3 addendum (2026-09-11, after the schema-2 gate failure)

Measured on this graph: the v1/v2 encoder produced a 98 to 99 percent shared KC
code; the antennal lobe (cholinergic local neurons under the released transmitter
labels) reverberated at the refractory ceiling after any input; the two spiking
APL proxies silenced every MBON; and the α1 output (MBON07) receives too few KC
contacts per cell to respond at any non-runaway drive. Schema 3 therefore adds a
glomerular identity encoder (`reward_encoder.py`), three recorded cell-type gains
(synapses onto ALPN ports, synapses leaving APL, synapses onto KCs) and moves the
engineered away mapping to PAM12 / MBON09 (γ3). Home stays PPL101 / MBON11. The
v1/v2 encoder and engine are untouched. See EXPERIMENT_REWARD.md for values.

## Native engine contract

Keep `lif.cpp` and its ABI unchanged. Add `reward_lif.cpp` and `reward_brain.py`.
Use the same dt=0.2 ms, delays, refractory rules, and integration as v1. Scheduled
Poisson input rates can vary by time bin; an additional schedule injects a
documented membrane pulse at selected DANs. DAN refractory timing remains active.
The pulse amplitude is an intervention parameter, not a measured light-to-spike
conversion. Report actual evoked/spontaneous spikes and pulse times.

For each KC and target compartment, decay spike traces before processing the
current step. The gain update is proportional to
`DAN_trace * KC_spike - KC_trace * mean(DAN_spikes)`, with the compartment DAN
population averaged so population size does not determine the dose. Coincident
spikes contribute no within-step ordering bias. Only listed plastic graph edges
can change; finite positive gain bounds preserve their sign and identity.
This is an event-based phenomenological implementation inspired by the upstream
rule. It does not reproduce that rate model's time discretization or slow update.

`RewardEngine.run` resets electrical/trace state and returns counts, recorded
spike bins, population counts, final gains and timing. It retains only gains for
the next call. Probe calls with plasticity disabled cannot change gains.
Graph and schedule inputs must be validated before crossing the native boundary.

## Bounded pilot and evaluation

Freeze a new protocol, source rows, feature scaling, annotation mapping, source
hashes, graph hashes, and RNG seeds in a separate `reward-v3-*` registry. Never
resume/modify `v2-24a83145c27ab220116e` or promote a new model.

Use the existing immutable sports source, selecting chronological MLB training
rows before the original validation boundary. Enforce the conservative 48-hour
plus UTC-day label delay between training and validation. Report original
validation as reused development data. Do not claim a new holdout.

Run three matched arms: true-outcome teaching, a fixed permutation of training
teaching labels, and frozen synapses. Use the same features, stimulation seeds,
initial graph, and frozen readout in all arms. No hyperparameter search.
The readout uses a fixed negative standardized response from each of the two
selected MBON populations, with training-frequency prior intercepts. Mean and
scale are calibrated on initial-graph training responses only. Its engineered
class mapping and calibration are recorded. Class probabilities must be finite
and normalized. Fixed readout logits are clipped to avoid numerical extremes.

The initial budget is at most 64 training and 32 validation games per arm,
16 shared calibration games and three shared gate probes, one seed, and 900
seconds. The budget is checked before and after each native trial and before
declaring completion; an already executing native call may finish after the
deadline but cannot produce a successful run. A short full-graph activity
check runs first. If the circuit cannot discriminate inputs, KC/DAN activity is
absent, or numerical activity violates declared guards, report a failed gate
and stop the expensive phase. Do not retune repeatedly until a favorable score
appears. Native tests also cover paired/backward/missing-reward timing, locality,
trace reset, weight bounds, probe immutability, and disabled-rule parity.

Before outcome training, three bounded single-input scale probes measured the
full graph with dopamine-only fast outputs zeroed. Original scale yielded 93.8%
KC activity and selected MBON rates above 400 Hz. Half scale yielded 74.7% KC
activity with both outputs active; quarter scale yielded 11.9% KC activity but
silent MBON07 output. Half scale is fixed for all pilot arms. These operational
guards do not establish physiological realism; the dense KC response remains a
limitation. No score-informed scale selection is permitted. The gate compares
two inputs using the same RNG seed and checks each teaching population against
an unpulsed trial with the same input and RNG seed. Per-DAN time bins are saved.

Report log loss/Brier/accuracy for all matched validation rows, fixed prior,
class-confusion, per-population activity, gain changes/bound occupancy, cumulative
progress, actual runtime, and readout-free mechanistic evidence. Comparisons are
descriptive and cannot establish bookmaker edge or biological superiority.

## Product acceptance

The existing Training workflow must show reward experiments separately from the
original v2 matrix. Show measured teaching/learning/probe progress, fixed-readout
identity, gain and KC/DAN/MBON activity evidence, per-arm results, artifacts, and
failure/empty/loading states. V1 remains visibly active. Existing API registry
and allowlisted downloads serve the new schema without model activation.

## Source checks

Checked September 11, 2026. Preserve exact source revisions/hashes in the research
note before running. Primary references:

- https://male-cns.janelia.org/download/
- https://github.com/philshiu/Drosophila_brain_model
- https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009205
- https://github.com/alitwinkumar/jiang_litwin-kumar_mb_rnn
- https://pmc.ncbi.nlm.nih.gov/articles/PMC4674068/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC9012144/

Community demos are investigated as implementation leads. Social captions alone
do not supply a training algorithm; inaccessible implementations remain unknown.
