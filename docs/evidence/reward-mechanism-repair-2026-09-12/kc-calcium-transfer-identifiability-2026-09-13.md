# What the external calcium fit can identify before KC transfer

September 13, 2026 UTC. Independent offline assessment by `dopamine_sources`.
No fit, residual analysis, parameter selection, downloaded-code execution,
saved-history evaluation or circuit run was performed.

**The 499-row workbook can support a reproduction of the published fixed-clock
population model. By itself it cannot determine a spike-to-axon-calcium map for
the retained KCs.** A local-state module remains mathematically possible as an
explicit engineering hypothesis. The next action should separate reproducing
the external fit from specifying that additional input/observation map; a
successful fit cannot silently supply the latter.

This conclusion uses the complete personally read pinned fitter and fitting
functions, not a proposed interpretation of missing supplementary equations.
The original source is
[nawrotlab/KC_KC_lateral_interactions](https://github.com/nawrotlab/KC_KC_lateral_interactions/tree/f0ee2079dae6761cc2d07f04e96e76e2654b6e3c),
commit `f0ee2079dae6761cc2d07f04e96e76e2654b6e3c`, accompanying DOI
10.1016/j.cub.2026.01.014. The workbook is the repository's separately cited
2022 gamma-KC dataset. Source files and workbook remain unchanged. No new
primary lookup was made for this assessment.

## What the fitter actually conditions on

The workbook has two header rows, followed by 499 rows of WT mean/SE and KD
mean/SE. The source uses **knockdown**, not a demonstrated complete knockout.
There is no timestamp, per-cell spike train, cell identity or sample-size
column in this four-column workbook. Parent's whole-workbook inventory binds
1,996 finite numeric cells and no formulas; I inspected its schema and parsed
all row values for that structural check, without using residuals or fitting.

The driver supplies the time axis at 30 Hz, odor onset 3.6 s and duration 5 s.
It states that the data are already normalized to zero baseline; it fixes
model baseline at zero and fits without noise. These files do not give an
absolute calcium concentration or a calibrated fluorescence-to-spike map.

The model has 700 units. With seed 666 the driver imposes 35 reliable
responders with input amplitudes drawn uniformly from 0.5 to 1, 105 unreliable
responders drawn from 0 to 0.5, and 560 zero-input units. The residual compares
the mean of the **140 nonzero-input units**, not all 700. Those categories and
input amplitudes are model assumptions, not inferred cell-by-cell from the
499 rows. WT inhibition uses the full all-to-all, zero-diagonal,
row-normalized matrix, multiplied by a fitted strength.

The post-offset data first initialize a decay fit. The main KD and WT
objectives use times through stimulus offset; the full 499 rows are not all
used as equally weighted residual points in those objectives. KD dynamics
are fitted first, then held for WT inhibition. Each objective adds the
source's `3.885 * sum(abs(parameters))` penalty to squared SE-scaled residuals.
A later residual-derived noise amplitude and simulated overexpression target
are additional steps. None was run here. The penalty can choose among fits;
it does not create missing input or molecular measurements.

## Exact input and observation ambiguities

Let the noiseless source calcium equation, before nonnegative clipping, be

```text
C_next = C + dt [u/tau_input - (C-b)/tau_C - a*C/tau_C - I/tau_C].
```

The calyx branch omits I. In this source, `tau_input` appears only as an input
divisor. There is **no separately evolving input-filter state**. With no
adaptation or inhibition and a constant input, the relaxation pole is set by
`tau_C`; `tau_input` changes the forcing amplitude. Calling its fitted value
an independently measured spike-to-calcium low-pass constant would add a
mechanism absent from the inspected code.

Suppose a transfer proposes `u(t)=q*r(t)` for spike rate r in spikes/s. Then
q has source-input-unit seconds/spike, and only `q/tau_input` enters the
calcium update. For any positive c, the substitutions

```text
q_new = c*q,   tau_input_new = c*tau_input
```

leave every trajectory unchanged for the same rate input. The source fixes
odor-step amplitude instead of measuring q. Its fitted `tau_input` therefore
does not determine q for actual spike rates. Holding that fitted value in a
transfer removes one free model parameter by convention; it does not turn
the unmeasured q into an identified biological quantity. Mapping impulses,
counts per bin, a filtered rate or membrane voltage into u are also distinct
input models, not interchangeable units.

A second ambiguity concerns physical calcium versus normalized activity.
For any s>0, rescale calyx/lobe calcium, inhibition, baseline, input, sigmoid
inflection and sigmoid slope by s; divide adaptation strength by s. The
adaptation state itself is unchanged. Every source update then produces s
times the original calcium/inhibition trajectory, with the same sigmoid and
adaptation trajectory. If the observation is `y=alpha*C+offset`, dividing
alpha by s leaves y unchanged. Nonnegative clipping respects this positive
scaling. Thus without an independent observation calibration the physical
calcium scale is unidentifiable. The source convention effectively sets an
activity scale; fitted inflection/slope are in that convention, not molarity
or millivolts. This equivalence is about a general physical interpretation;
it does not claim the source's fixed numerical input convention leaves all
its fitted coordinates free.

Jointly permuting source cells, their inputs and states preserves its mean
observation and uniform lateral coupling exactly. No fit of those means can
assign a response type to a particular MaleCNS body. Nor does a population
mean close the nonlinear local equation: in general
`mean(f(L)*I) != f(mean(L))*mean(I)`. Different distributions and correlations
can share a mean calcium trace while producing different local inhibition.
The supplied SE column is not a measurement of those hidden joint histories.

These are explicit structural ambiguities. They do not prove that every
parameter in the fixed published population model is unidentifiable, and this
assessment did not attempt a rank or confidence analysis of that fit.

## A faithful clock versus a continuous embedding

At fixed recipient factor f and neighbor drive B, let the source's declared
step be d0=1/30 s and write

```text
I_next = A*I + b*B,
A = f*(1-d0/tau_inh),   b = f*d0/tau_inh.
```

For 0<A<1, one exact constant-input scalar continuous embedding is

```text
lambda = -log(A)/d0,
mu = lambda*b/(1-A),
dI/dt = -lambda*I + mu*B.
```

Its d0 endpoint equals the discrete update and its stationary state is
`b*B/(1-A)`. This is a mathematical embedding, not a measured receptor law.
It depends explicitly on the original clock. A=0 has no finite-rate
exponential realization of this form; A<0 cannot be the endpoint multiplier
of a real scalar first-order decay. The source fit does not enforce these
embedding conditions explicitly, so they would have to be checked before
using such a representation.

The equivalence assumes f and B are frozen across the original interval.
Recomputing them continuously as calcium evolves changes the coupled model.
Likewise the other source states use previous-sample values and Euler updates;
embedding the inhibition branch alone does not make the full multistate
system equivalent. Thirty-Hz observations do not uniquely specify an
intersample trajectory. Many embeddings can share those sampled endpoints.

An exact source-clock wrapper can instead retain all original update maps and
sample-and-hold semantics. Its scheduling against the 0.2-ms electrical grid
must be explicit: one source step is 166 2/3 electrical steps, so rounding
every step to a fixed integer would change the clock. How electrical events
are accumulated into the source input, and how its local state is read between
updates, remains a new engineering contract. Reproduction of the source alone
does not decide either choice.

## Minimum additional quantities and pre-outcome falsifiers

The next useful transfer specification can be short, but must fill these
particular quantities rather than claim that a fit supplied them:

| Quantity | What would identify or declare it | Independent falsifier |
| --- | --- | --- |
| Input map and scale q | External paired KC spike/rate and local calcium observations, with stimulus timing and observation normalization; or an explicitly declared engineering reference-input equivalence | Matched isolated pulses, sustained drive and repeated bursts must predict held-out local responses under one map, without refitting amplitude per stimulus |
| Local observation and output placement | Name calyx versus axon activity and whether the output changes release, cAMP or plasticity susceptibility; specify the normalized observation operator | A map that reproduces population fluorescence but predicts the wrong local effect under receptor perturbation is insufficient |
| Lateral drive and recipient distribution | An independently specified relation between neighboring activity, contacts and local modulation; source all-to-all W can be retained only as an identified source-model assumption | Neighbor-drive removal and recipient activation must separate lateral suppression from direct-drive/adaptation effects; matching only their mean is insufficient |
| Clock and continuation | Exact source-clock update or explicitly derived continuous model, including input aggregation, initial states and post-input continuation | Constant-drive equilibrium, source-step endpoint comparison where claimed, event/clock phase tests and complete decay must agree with that chosen contract |
| Scope across the eligible cells | State which quantities are shared engineering assumptions beyond the gamma experiments and which have cell-specific evidence | Existing masks, off-channel behavior, no-learning controls and both complete qualification panels remain unchanged; no home cells are deleted to match experimental scope |

To establish a *measured* per-spike map, the minimum new biological anchor is
joint input/output information: a known spike/rate drive and the corresponding
local calcium observation in stated units, with temporal excitation adequate
to distinguish impulse, sustained and adaptive responses. To establish the
neighbor-coupling branch independently also requires varying neighbor drive
or receptor state while holding recipient input controlled. This need not
begin as a complete calibration for every body, but extrapolation to the
remaining eligible classes must be labeled. Neither the population workbook
nor released contact counts supply these quantities alone.

For an *engineering hypothesis*, root can specify a dimensionless local-state
mapping and its external reference-input equivalence before seeing BET36FLY
outcomes. That is mathematically defensible if its new scale, clock and
coupling assumptions are explicit and its independent falsifiers are fixed.
It should not be described as a uniquely source-calibrated spike-to-calcium
transfer. This note chooses no such scale or parameter and does not authorize
a candidate. It narrows the immediate decision to that explicit mapping
contract, separate from any bounded source-fit reproduction; it does not
require another open-ended source search.
