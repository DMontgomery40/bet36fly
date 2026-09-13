# Handler timing mechanism and the newly identified KC voltage switch

September 13, 2026 UTC; checkpoint `ab0f80f`. This is a bounded source and
transfer review, not a candidate design or evaluation. It continues the
[receptor-state decision](dopamine-receptor-state-decision-2026-09-13.md) and
[quantitative release check](tonic-burst-dopamine-quantitative-source-check-2026-09-13.md).
The failed fixed-history outcomes remain rejected with their original guards.

**Handler does not supply an inspected, publicly executable intracellular
kinetic model. A newer primary paper supplies a concrete additional mechanism
and a public model repository: KC muscarinic signaling whose effect depends
on KC activation. Its numerical model still requires an explicit transfer
contract; it is not a calibrated replacement for the present rule.**

## What Handler actually provides

[Handler et al., Cell 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC9012144/),
DOI 10.1016/j.cell.2019.05.040, separates dopamine release from downstream
order sensitivity. Its indexed primary text describes comparable release
under opposite pairing orders and proposes IP3-receptor agonist-order
sensitivity as a candidate explanation. The cited channel studies support
that reasoning; the inspected text does not give a KC-local set of rate
equations and fitted rates. The [publisher's availability statement](https://www.sciencedirect.com/science/article/pii/S0092867419306117)
says customized scripts/data are available upon request, rather than linking
a public intracellular simulator. No author was contacted.

Consequently the earlier three-state equations remain our engineering
representation, with their input maps, branch conversion and relaxation rates
unfilled. The same-release/different-order experiment is a useful causal
constraint, not a numerical calibration. The fresh publisher open returned
403; this check used indexed primary text and retained earlier documented
reading, not an asserted new full-page read.

## New primary physiological constraint

[Manoim Wolkovitz, Tunc et al., Current Biology 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC12948350/),
DOI 10.1016/j.cub.2026.01.014, reports mAChR-B/Gi/o inhibition of KC cAMP
that weakens with activation. R71G10-driven γ-KC experiments used 5 mM applied
DA and a 2-s puff including 0.5 mM ACh, with/without odor. These are applied
solutions, not measured synaptic concentrations. Xenopus oocyte dose-response
EC50 shifted from 516 nM at −80 mV to 1,470 nM at +40 mV. The stated fit is

```text
Y = Bottom + X (Top − Bottom) / (EC50 + X)
```

`Y` is normalized response; `X` and `EC50` are ACh concentrations in matching
units. This is a static assay fit, not a time-evolution equation. Adult flies
were 7–10 days old; γ-KC rescue and cAMP experiments support a local mechanism,
not a body-specific γ1pedc/γ3 calibration. The model has 700 two-compartment
KCs, activity-dependent lateral inhibition, and MBON–DAN feedback. The local
source separates the 5-s calcium-fitting stimulus from 60-s learning with
12 shocks; the earlier indexed synopsis must not conflate those protocols.
Main-text polarity labels differ between prose and Figure 2 caption. Below,
the inspected code's trained/untrained labels avoid assigning that ambiguity
to our fixed home/away channels.

## Pinned model and access limits

The authors' [public repository](https://github.com/nawrotlab/KC_KC_lateral_interactions)
was initially observed on `master`, with nine commits and GPL-3.0 licensing.
The README identifies an ordered workflow:

1. `fit_rate_model_to_data.py` fits model parameters to calcium imaging from
   the separately cited 2022 study.
2. `rate_model_get_summed_KC_activity_different_model_variants.py` prepares
   normalization used to tune MBON output.
3. `learning_rate_screening_mbon_normalized.py` precedes valence plotting.

Parent subsequently pinned commit
`f0ee2079dae6761cc2d07f04e96e76e2654b6e3c` and downloaded a bounded source
selection. I then personally read the complete core, `fit_functions.py` and
`fit_rate_model_to_data.py` from that verified local copy, plus learning-script
lines 1–100 and 208–262. No upstream code was imported or executed by this
review. Parent's separate download exceeded its requested 120-s cap
(225.688 s); its original receipt and explicit budget-failure review are
preserved. My own four-search/six-open cap was exhausted without extra requests.

The paper explicitly identifies **Methods S1: Mathematical network model**,
`mmc2.pdf`, approximately 383.9 KB. Both attempted supplementary URLs returned
tool errors and supplied no PDF bytes; the direct primary PMC page returned a
challenge and the publisher returned 403. The attempted supplementary URLs
were conventional candidate addresses, not verified working download links.
The supplement was not read. The following equations are verified from the
pinned code instead; they are discrete calcium-model updates, not an inferred
receptor-binding ODE or measured local intracellular concentration model.

## Exact inspected source equations and units

For the noiseless WT fitting path, let `C` denote calyx calcium, `L` axonal
calcium, `a` adaptation, `I` inhibition and `u` scaled odor input. All right-hand
sides use the previous sample. `clip+` means the source's nonnegative clip:

```text
a' = a + dt (adaptscale C − a) / tauadapt
C' = clip+[C + dt (u/tauinp − (C−b)/tauKCdec − a C/tauKCdec)]
f(L) = 1 / [1 + exp((L−infp)/slf)]
I' = f(L) [I + dt (W L − I)/tauinh]
L' = clip+[L + dt (u/tauinp − (L−b)/tauKCdec − a L/tauKCdec − I/tauKCdec)]
```

The fit uses uniform row-normalized lateral `W`, no self-inhibition; `C,L`
start at `b`, while `a,I` start at zero. It does not use connectome weights.
Time is seconds and plotted calcium is arbitrary normalized activity, not
millivolts or molarity. Thus `infp,slf` are activity-scale parameters. The
listed time constants are fitted model quantities, not direct receptor
binding measurements. [Pinned fitting functions](https://github.com/nawrotlab/KC_KC_lateral_interactions/blob/f0ee2079dae6761cc2d07f04e96e76e2654b6e3c/codes/fit_functions.py)

Multiplication of the **entire stored inhibition state** matters. For a
constant recipient factor `f` and constant neighboring drive `B=W L`, the
recurrence has the algebraic fixed point

```text
r = dt/tauinh
I* = f r B / (1 − f + f r)
```

For `0≤f<1`, fixed `tauinh,B` and decreasing `dt`, this tends to zero.
Replacing it with `dI/dt=(f B−I)/tauinh`, or merely inserting our 0.2-ms step,
would therefore change the mechanism. This is a transfer constraint, not a
claim that the authors' fitted discrete model is invalid. Parent and the
independent mathematical reviewer own synthetic recurrence checks; none were
rerun here.

The source fitter reads the separately supplied 2022 γ-KC calcium spreadsheet,
uses 30 Hz, 5-s odor duration, and sequentially fits knockdown dynamics then
WT inhibition. Its objective is standard-error-weighted squared residuals
plus an L1 parameter penalty `3.885 Σ|parameter|`; baseline is fixed at zero.
The overexpression inhibitory factor is fitted to a simulated
voltage-independent trace, not another measured kinetic constant. Numerical
optimizer starting values are not released biological calibrations. [Pinned
fitter](https://github.com/nawrotlab/KC_KC_lateral_interactions/blob/f0ee2079dae6761cc2d07f04e96e76e2654b6e3c/codes/fit_rate_model_to_data.py)

The separate learning path implements

```text
prediction = untrained_MBON − trained_MBON
D' = clip+[D + dt (1[shock>0] (shock−prediction) − D)/tauDAN]
w' = clip+[w − learning_rate L D dt]
```

`D` is a normalized DAN-driven cAMP state, not a measured spike train or DA
concentration. Learning uses previous-sample `L,D`; after shock ends, an
existing `D` decays and can still cause depression. From zero `D`, no shock
means no generated `D`, independently of ongoing KC activity. There is no
positive weight-change branch. [Pinned core](https://github.com/nawrotlab/KC_KC_lateral_interactions/blob/f0ee2079dae6761cc2d07f04e96e76e2654b6e3c/codes/KC_population_calcium_rate_model_functions.py)

Its learning script separately sets `dt=0.01 s`, `tauDAN=2 s`, 60-s odor,
12 shocks of 1.25 s with 3.75-s gaps, zero initial `D`, and unit initial
weights. The script explicitly identifies the remaining learning parameters
as not fitted to data and screens learning rates. These must not silently
replace our accepted timing, η, gains or controls. [Pinned learning script](https://github.com/nawrotlab/KC_KC_lateral_interactions/blob/f0ee2079dae6761cc2d07f04e96e76e2654b6e3c/codes/learning_rate_screening_mbon_normalized.py)

## Transfer constraints that can be fixed independently of our outcomes

The source's external-shock gate cannot be imported to make an untaught
condition quiet. Our fixed rule must still confront recorded endogenous DAN
activity. Substituting zero generated dopamine for that activity would change
the experiment and bypass its central control, regardless of source-model
performance.

Several structural decisions follow without fitting the 32 histories. A
muscarinic contribution must be distinguished from fast cholinergic
transmission. It must depend on an explicit local KC state and lateral input,
with its inhibitory influence weaker for stronger recipient activation.
The source's model route changes KC axonal activity; reducing it to a scalar
multiplier on the current signed gain update would be a new approximation.
Preserve these distinctions as falsifiable hypotheses, rather than treating
all receptor effects as interchangeable dopamine filters.

Current code inspection found `RateBridge` driven only by KC spikes and a
population-mean DAN event stream. Its per-edge products contain no KC voltage,
axon calcium, cAMP or muscarinic state. The electrical kernel has one `v` and
one fast input state per neuron; it does not instantiate separate KC calyx
and axon calcium compartments. Fast retained KC contacts still transmit.
These observations identify a concrete missing representation, not the cause
of the failed untaught control.

A faithful source-model reproduction could use its original external calcium
data and fitting procedure without fitting BET36FLY outcomes. That would be a
separate reproduction, not permission to retune our encoder, drive gains,
readout or learning rate. Its numerical parameters would remain in the source
model's units. A later transfer needs all of the following declared before
any candidate run:

- The variable affected: electrical KC activity, axonal transmitter output,
  plasticity susceptibility, or multiple explicitly separated variables.
- The mapping from our reset-to-zero voltage state and event trains to the
  source's local activation/calcium variables. A whole-neuron spike raster
  does not contain a measured local axonal voltage or calcium history.
- The representation of lateral cholinergic input and its relation to the
  retained fast synapses; no silent sign flip or deletion of anatomical edges.
- Source-fit quantities versus new engineering choices, with units, state
  lifetimes, initial conditions, simultaneous-event semantics and complete
  post-input continuation. The source learning-rate search cannot silently
  replace eta 0.0005, and its timing cannot silently rescale 400 ms into the
  source's 5-s calcium stimulus or 60-s learning stimulus.
- The additional assumptions needed for all eligible home KC classes and the
  supported away γ edges. The γ-KC experiments do not justify deleting other
  home classes or changing either teaching channel.

## Consequences for controls and the next concrete step

The paper's learned CS− generalization is not the present fresh-checkpoint
untaught condition. Its feedback topology and lateral state could change
responses under ongoing endogenous DAN activity, but the direction and size
of that change are unestablished here. A favorable source-model reproduction
would not imply that our untaught guard passes. Likewise an activity-dependent
LTD mechanism does not by itself supply the separate order-dependent recovery
branch needed to explain Handler's bidirectional results or demonstrate our
frozen reversal criterion.

Before transfer, synthetic tests should independently constrain lateral-input
removal, a fixed receptor state, and activation-dependent release from
inhibition while keeping external stimulation identical. They must distinguish
changes in KC dynamics from changes in plasticity with a fixed KC history,
retain no-learning and no-DAN controls, and disclose any effects on recurrent
activity. These are design constraints, not invented expected outcomes for
the saved 32 trials. Untaught, timing-unpaired, matched teaching, masks,
checkpoint isolation and both full qualification panels remain mandatory.

The concrete next step is a bounded reproduction contract for the pinned
public model's external-data fits and discrete semantics, followed by a declared
mapping to our variables if that inspection supports one. It is more specific
than another unspecified receptor search. No intracellular parameter choice,
new stimulation, candidate implementation/evaluation, native call or shared
production/wiki edit was made by this review.
