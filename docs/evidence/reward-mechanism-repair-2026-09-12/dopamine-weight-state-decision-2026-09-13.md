# Weight-dependent opposing plasticity: bounded source decision

Checked September 13, 2026 UTC. Output-only review of existing primary-source
coverage, three bounded web-tool actions, and the current implementation. No
candidate was implemented or evaluated, no saved histories were inspected for
this decision, and no circuit or synapse-data request occurred.

The proposed symmetric weight dependence is a concrete, fully specified
engineering hypothesis worth a separately frozen test. The inspected fly
evidence supports modulation of KC output and intracellular plasticity state;
it does **not** establish this distance-to-bound formula, a linear dependence
on initial synaptic strength, or these numerical limits as release-probability
bounds. Its specific new effect is activity-dependent contraction of altered
gains. It does not implement the receptor coincidence branch identified in the
preceding [source decision](dopamine-receptor-state-decision-2026-09-13.md).

## Source support and its limits

The earlier [full source ledger](dopamine-signal-sources-resumed.md) and joint
state decision were personally reread. Coverage and access limits carry
forward; the fresh actions below did not replace a full methods inspection.

- [Hige et al., 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4674068/),
  Neuron 88, DOI 10.1016/j.neuron.2015.11.003: prior inspected γ1pedc recordings
  establish dopamine-dependent depression of KC-driven MBON input, with MBON
  spiking dispensable. The reported backward procedure had no significant
  effect, and induction differed between compartments. These results constrain
  the home family but do not determine a gain-dependent update function.
  Postsynaptic spikes being dispensable is not by itself a direct measurement
  of presynaptic release probability. This review found no inspected initial-
  strength series calibrating either proposed branch. A fresh direct PMC open
  returned a browser challenge; a targeted paired-pulse search returned no
  results. Neither failed access establishes the absence of such evidence
  elsewhere in the paper or literature.
- [Handler et al., 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC9012144/),
  Cell 178, DOI 10.1016/j.cell.2019.05.040: prior indexed Results/Figures 5–7
  and selected Methods distinguish receptor/second-messenger pathways and
  opposite plasticity orders in γ4, with additional γ-compartment support.
  Fresh indexed primary text again connects synchronous conditioning to
  maximal cAMP and depression, and a different timing to ER calcium and
  potentiation. Comparable release-side signals across induction orders
  support a downstream distinction. They do not show symmetric distance-to-
  bound dependence. Reporter normalization is not a physiological conversion
  to this model's gain. Full methods access is not newly claimed.
- [Cohn, Morantte and Ruta, 2015](https://stacks.cdc.gov/view/cdc/38872/cdc_38872_DS1.pdf),
  Cell 163, DOI 10.1016/j.cell.2015.11.019: prior main text/main methods and
  fresh [indexed primary Results](https://pmc.ncbi.nlm.nih.gov/articles/PMC4732734/)
  support local KC-axon calcium domains and state-dependent modulation of
  transmission. Prior measured γ4 paired depression and separated potentiation
  establish that KC output is modifiable in both directions. This does not
  distinguish the proposed weight dependence from changes in upstream calcium,
  receptor state, additive plasticity or other release mechanisms. Presynaptic
  calcium is not a calibrated release-probability or initial-strength axis.
  γ4 findings cannot supply a γ1pedc/γ3 equation by analogy.

There is thus support for a **cellular state affecting transmission**, but no
direct quantitative support in the inspected material for a plasticity rate
proportional to remaining headroom, equal opposing slopes, a midpoint fixed at
gain 1, or common parameters across these two teaching channels. Existing
synapse counts do not fill those gaps. The question “does changing initial
strength while holding the relevant local signals fixed change the subsequent
plasticity rate in this way?” remains unmeasured here.

## Exact engineering law and parameter provenance

Retain the existing causal rate and eligibility filters, actual pooled DAN
events, cold history at the 100 ms learning onset, learning rate, masks and
full zero-input continuation. Define **nonnegative** instantaneous products

```text
P(t) = 0.96 E_D(t) R_K(t)
N(t) = 0.96 E_K(t) R_D(t)
dg/dt = eta [P(t) (1.5 − g)/0.5 − N(t) (g − 0.5)/0.5]
eta = 0.0005
```

`N` here is a magnitude; it is not the negative-valued accounting column in
existing saved artifacts. `g` and its bounds are dimensionless; rates have
spikes/ms and eligibility has spike units under the existing event
normalization. Consequently `P,N` have the same event-product/ms units as the
current bridge drive, and eta has the same inherited conversion. The 0.96
normalization, 100/500 ms filters and eta retain their current engineering
provenance. The **new linear branch factors** come exclusively from the
existing 0.5/1.5 gain limits and the choice to match both branch coefficients
at initial gain 1. They are an additional engineering assumption even though
no free numerical parameter was added. Away from gain 1 the effective branch
coefficients change between zero and two.

Gain is a multiplier on an edge's retained anatomical weight. Two edges at
gain 1 can have different underlying weights and contact counts. Dependence
on this normalized gain is therefore not automatically dependence on their
absolute initial synaptic strength, number of release sites or release
probability. The proposed rule selects the normalized multiplier as its
state variable by engineering convention.

Writing `p = g − 0.5` gives

```text
dp/dt = 2 eta [P (1 − p) − N p],  0 <= p <= 1.
```

This can be represented as a coarse two-state efficacy occupancy, with rates
`2 eta P` and `2 eta N`. That is a mathematical representation, not evidence
that anatomical synapses have those two molecular states or that `p` is their
measured release probability. In particular the simulator still transmits at
gain 0.5 when this proposed occupancy is zero.

The current `RateBridge::update` in `bet36fly/reward_lif.cpp` adds the
integrated opposing drive independently of the prior gain, then clamps the
double accumulator and publishes float32. The proposed rule changes that
gain dependence throughout each interval. It cannot be implemented merely by
renaming the old clamp or multiplying the old net area after integration.

## Consequences derived before any candidate outcome

Let `x = g − 1`, `Q = P − N`, `S = P + N`. Then

```text
dx/dt = eta Q − 2 eta S x.
```

The initial instantaneous update at gain 1 is exactly the old bridge update.
At lower gains balanced activity increases gain; at higher gains it decreases
gain. This gives an input-dependent recovery/forgetting mechanism, with no
decay during complete silence after all filters have relaxed. Two solutions
under the same fixed input contract by
`difference(T) = difference(0) exp(−2 eta integral_0^T S dt)`.

For constant nonzero products, the stable equilibrium is
`g* = 0.5 + P/(P+N)`. A pure potentiating drive approaches 1.5 as
`g(T) = 1.5 − (1.5−g(0)) exp(−2 eta integral P dt)`; a pure depressing
drive approaches 0.5 analogously. These are mathematical limiting cases,
not claims that real dopamine or KC stimulation isolates those branches.
At the lower bound the derivative is nonnegative, and at the upper bound it
is nonpositive, so the continuous equation preserves the interval without
routine clipping. This does not automatically prove a discrete implementation
or its published float32 values stay strictly away from bounds.

If histories are identical or proportional so that `P=N` at all times,
starting from gain 1 still produces **exactly zero** plasticity. Starting from
a different gain instead restores it toward 1. The formula therefore does not
resolve the bridge's fresh-gain coincidence cancellation. This algebraic
case must not be equated with experimentally overlapping stimulation envelopes
or used to negate the observed depression during synchronous conditioning.

For an isolated KC/DAN pair from a fresh gain, the existing opposing drive has
a fixed sign after the later event. A positive integrating factor preserves
that polarity and attenuates the net magnitude relative to the additive
bridge. Exchanging the two event times reverses the response about gain 1;
the isolated-pair curve remains antisymmetric. Exactly simultaneous unit
events have equal nonzero product areas but zero net change at gain 1.
Consequently the known γ1pedc backward-protocol limitation and the missing
distinct coincidence branch remain unresolved source constraints.

For mixed event histories, signed contributions can cancel in different
ways and later activity damps earlier deviations. There is no theorem that
the guard mean/SD ratio improves, that potentiation remains sufficient for
reversal, or that a taught signal is protected from subsequent balanced
activity. Repeated background can erase useful acquired gains. With inherited
signals and eta, this effect may also be too small to matter. No candidate
results or basis-analysis outcomes were used to choose the law or its values.

## Numerical contract needed before an authorized evaluation

The equation is linear in gain for fixed event histories. Its exact solution
over any interval ending at T is

```text
x(T) = x(0) exp(−2 eta integral_0^T S)
     + eta integral_0^T Q(s) exp(−2 eta integral_s^T S(u) du) ds.
```

The same expression with `T=infinity` defines the entire no-new-event tail;
the filtered signals make these integrals finite. The old single additive
tail update does not evaluate this law. An independent integrating-factor
quadrature/ODE oracle must agree with any implementation, including time
varying products inside each 0.2 ms interval. Freezing the gain multiplier
over an interval is a different numerical approximation whose error cannot
be assumed away. Preserve one float32 publication per full electrical step
and one after the entire tail, a double continuous gain state within the call,
and the existing gain-only checkpoint persistence/reset policy.

Before real evaluation, freeze independent tests for constant/pure/balanced
products, distinct initial gains, silence, isolated and simultaneous pairs,
event exchange, repeated mixed histories, interval partition invariance,
full-tail convergence and bound invariance. Retain positive and negative
**weighted** integrals separately so attempted and applied accounting remain
meaningful. Test excluded-edge and learning-off byte invariance, both channel
population sizes, exact inherited masks and publication/bound counts. A
numerical clamp hiding overshoot is not evidence for the continuous law.

All 4,184 home edges and 3,239 gamma-eligible away edges remain eligible;
the other 1,443 away edges keep transmitting. Gains driving the electrical
network, encoder, teaching schedules, onset, times and qualification guards
remain fixed. An offline result could reject this law under fixed recorded
histories. A favorable shadow would still need a new full-circuit diagnostic
identity and every unchanged criterion before conditioning/reversal. No
candidate is qualified by this decision.

## Access and decision boundary

The fresh web budget used three web-tool invocations: one targeted search
with no results, one batch of three targeted primary-source searches, and
one challenged direct Hige open. Thus four search queries and one page open
were issued across those three invocations; their distinct counts are
recorded rather than conflated. The batch returned unrelated papers that
were not adopted as evidence. No full new methods retrieval, account access,
synapse download, candidate or native run occurred.

This review supports testing the **explicit engineering hypothesis of
activity-driven, strength-dependent plasticity**, provided its missing source
calibration remains visible and the numerical contract is frozen first. It
does not support presenting symmetric soft bounds as the measured cellular
mechanism, selecting parameters from the inconclusive routing analysis, or
claiming that this replaces local dopamine or receptor dynamics.
