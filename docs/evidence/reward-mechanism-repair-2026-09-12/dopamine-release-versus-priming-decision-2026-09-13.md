# Activity-dependent release versus intracellular priming

September 13, 2026, checkout `dce1582618f6c386a4996695bc77ad4218dd493c`.
**Release dynamics are a distinct, falsifiable mechanism class, and a new
published quantitative implementation exists. The inspected evidence does
not fix a PPL101/PAM12 spike-to-release candidate for this 400 ms experiment.**
The new implementation is a mouse model; the available fly measurements
constrain regional evoked release and uptake without identifying a local
facilitation/depletion law. No constants or candidate are selected here.

## What was already known, and what is new

The earlier [fly release review](tonic-burst-dopamine-quantitative-source-check-2026-09-13.md)
already inspected adult regional FSCV, receptor BRET sensitivities and fly
dopamine sensors. Repeating that work would not fill the missing spike units.
The [joint-state decision](dopamine-receptor-state-decision-2026-09-13.md)
separately motivates intracellular order sensitivity; the later Handler
workbook/source reproduction establishes neither molecular rate constants
nor a quantitative γ1pedc/γ3 transfer.

The adult [Shin et al. 2020 experiment](https://pmc.ncbi.nlm.nih.gov/articles/PMC7902153/)
pools γ1/γ2 heel or γ4/γ5 tip. Its single optical pulse and pulse trains
support nonlinear stimulation-to-signal relationships, not verified
single-spike release probabilities. Uptake fits and sex effects cannot be
silently converted into named-terminal kinetics. A larval
[2015 primary report](https://pmc.ncbi.nlm.nih.gov/articles/PMC4636934/)
likewise reports larger release per initial optical pulse than the mean
over a long train. Its constant-release-per-pulse uptake fit is not itself
a facilitation/depletion equation. Fresh direct access was challenged;
only indexed Results/Table 1 were inspected. Depletion and autoregulation
remain proposed explanations there, not separately identified mechanisms.

The new lead is [Shashaank et al. 2023, PNAS Nexus 2:pgad044](https://academic.oup.com/pnasnexus/article/2/3/pgad044/7034164),
DOI 10.1093/pnasnexus/pgad044, typeset March 10, 2023. In anesthetized mouse
dorsal striatum, the model fits 30-pulse, 50 Hz bursts and repeated bursts.
Its dimensionless release factors obey

```text
A = product_j H_j
H_j' = f p_j H_j S + (1-S)(1-H_j)/tau_j.
```

Here time is seconds, f is Hz and S indicates the experimentally specified
burst interval. WT sweep-1 values are
`p=(0.0105,-0.003,-0.0011)`, `tau=(7.5,15,900) s`.
Concentration production also requires release per stimulus current,
current, uptake and geometry/measurement terms. These are fitted model
parameters, not fly receptor constants.

The linked [DARELA repository](https://github.com/DSulzerLab/DARELA) exposes
Python SUR/STUR/STDR models and requires burst start times, frequency,
pulse count and current in mA. Its README and file listing were inspected;
the computational core, supplement and commit identity were not retrieved
or independently verified. Public implementation availability is established;
executable agreement is not. No download, installation, fit or source run
belongs to this inquiry.

## What a spike-driven interpretation would have to declare

Using our teaching schedule as S would be an inadmissible experiment-label
gate. Treating S as an observed burst detector would instead require a new
detection rule. Neither choice is supplied by the release data. Continuously
evolving state driven by **every actual spike of each DAN**, including cue
activity, is a different and potentially admissible engineering construction.

For clarity, one mathematical event embedding could let each H recover
toward one between events, release a dimensionless impulse
`a_i = product_j H_ij(t_minus)` at a spike of body i, then update
`H_ij(t_plus)=exp(p_j) H_ij(t_minus)`. This illustrates a fully causal
per-cell state transition, not an adopted implementation or an exact copy
of the source's burst-switched differential equation. Choosing pre-update
release, the event jump, initial H=1 and a rested spike of unit mass are
engineering choices. The last convention removes unknown concentration
scale for a test; it does not measure release per fly spike or preserve
physical dopamine units by implication.

One would transform each body's spikes before population averaging:
`D_channel = sum_i a_i delta(t-t_i)/N_channel`, with no home-minus-away
subtraction. For nonlinear per-cell dynamics, transforming a pooled mean
does not generally equal pooling transformed cells. The existing pooled
taught records cannot supply missing individual spike histories for that
calculation. Body-local state also does not establish contact-local exposure
or justify a new synaptic routing coefficient.

Long recovery alone is **not** a 400 ms exclusion. For an uninterrupted
50 Hz interval in the printed release-factor equation, the stated WT factors
give `A(T)/A(0)=exp(50*0.0064*T)`; at 0.4 s this is `exp(0.128)`.
This is an algebraic example, not a simulation or prediction for our cells.
Conversely, the illustrative event embedding has a facilitation multiplier
`exp(p_1-Delta/tau_1)` between regularly spaced events. It lacks a finite
steady facilitation state when `Delta <= p_1*tau_1`. A finite-burst fit
therefore does not establish a bounded ongoing-release mechanism; adding a
vesicle pool or cap would introduce further unsupported choices.

Reset and tail must also be explicit. If new release states are reset to
one with the circuit, they are not steady-state tonic pools. If they evolve
before the fixed 100 ms bridge onset, that is physical state history, while
the accepted bridge still starts cold. After the last actual spike, this
example releases nothing: H recovers silently and the existing bridge tail
finishes prior impulses. A concentration/clearance model would instead need
its own continuing chemical drive and a different coupled-tail contract.
Neither option is silently authorized by calling it a release model.

## Release cannot replace the intracellular question

Release modulation could change the effective DAN waveform using the cell's
own past activity. It cannot distinguish identical complete local histories
and initial states according to whether an experimenter taught them. It also
does not, by itself, reproduce a downstream order effect under an identical
dopamine waveform. That is the distinct Handler-motivated priming question.

Keeping the old bridge after a release transform still gives zero for an
isolated exactly coincident KC/DAN pair with rested unit release. Therefore
this construction is not a two-branch coincidence-depression/ER-potentiation
model. Experimental overlapping stimulation envelopes should not be equated
with that synthetic identical-spike example.

The useful fixed falsifiers precede any outcome evaluation: identical-history
determinism; no release without actual spikes; explicit rested-pulse and
repeated-pulse responses; cell-before-pool versus pool-before-cell fixtures;
finite/bounded sustained-input behavior in the claimed domain; exact reset,
event order and whole-tail accounting; and unchanged masks, gains, onset,
qualification and acquisition/reversal controls. These are engineering
requirements. The regional fly measurements supply biological motivation,
and MaleCNS supplies cells/contacts, not these numerical laws.

The next decision is consequently narrower than another literature survey:
use the already authorized matched-record causal-prefix check to identify
what actual electrical signals teaching first changes. If root later chooses
the non-fly release hypothesis, first pin and inspect DARELA's core and choose
an explicit spike/event mapping before any replay. That would be a declared
engineering hypothesis, not a newly calibrated fly mechanism. The alternative
intracellular priming topology still needs its own input units, transition
rates and branch-to-gain conversions. No inspected source fixes those missing
quantities, and none is chosen from the rejected outcomes here.
