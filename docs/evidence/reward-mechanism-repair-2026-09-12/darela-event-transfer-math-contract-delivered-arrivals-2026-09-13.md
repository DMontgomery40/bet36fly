# Independent DARELA event-transfer mathematics

September 13, 2026; preparation at clean `64a4b1d8797ebf0e76049e3a9995fb11d2e38795`.
All 197 narrative docs/wiki match this agent's complete personal reading
chain. This is an independently derived synthetic contract, not a release
candidate, fit, source reproduction or evaluation of MaleCNS histories.
The specified WT sweep-1 Euler-derived jump is mathematically admissible
for the fixed 400 ms reset domain without a new state cap; implementation
verification and unchanged scientific qualification remain required.
The minimal executable core has now been personally read without importing
or executing it. The version-specific comparison concerns
[`125c27bc59b0c493c902c8724f58fa3d9d8b354d`](https://github.com/DSulzerLab/DARELA/commit/125c27bc59b0c493c902c8724f58fa3d9d8b354d),
dated February 15, 2025, acquired by root on September 13, 2026. This is
later than the paper, not a claim of publication-revision identity.

The source review reports WT sweep-1
`p=(0.0105,-0.003,-0.0011)` and `tau=(7.5,15,900)` seconds.
Those values are externally specified inputs to this algebra, not values
selected from the 32 histories or 64 contrasts. The independent primary-paper
reviewer confirmed that table row; the shipped example differs as recorded
below. The paper's
mouse dorsal-striatum fit does not supply a calibrated fly release law.

## Three different objects

The printed continuous source law is

```text
dH_j/dt = f p_j H_j S + (1-S)(1-H_j)/tau_j
A = product_j H_j.
```

Here `t,tau` are in seconds, `f` is in reciprocal seconds, `p,H,A` are
dimensionless, and `S` is the experiment's burst switch. For a constant
active burst, recovery is absent: `H_j(t)=H_j(0)exp(f p_j t)` and
`A(t)=A(0)exp(f P t)`, where `P=sum(p)=0.0064`. For a quiet interval of
duration `Delta`, `H_j -> 1+(H_j-1)exp(-Delta/tau_j)`. These exact
subsolutions must not be confused with the implementation's discretization.

The independent paper reviewer reports that supplementary SUR integration
uses forward Euler with `dt=1/f`. Thus an active SUR step has multiplier
`1+p_j`, not `exp(p_j)`. More generally its Euler factor is
`1+f*p_j*dt`. Its inactive Euler recovery factor is `1-dt/tau_j`.
Those statements are confirmed by the pinned `_solve_kinetics` and SUR
`initialize` implementation. Choosing exact subsolutions instead is a numerical/model
change, not automatically an identical source reproduction.

The proposed **exponential event embedding** is a third object:

```text
at each actual spike of cell i:
    release mass a_i = product_j H_ij(t_minus)
    H_ij(t_plus) = q_j H_ij(t_minus), q_j=exp(p_j)
between spikes:
    H_ij(t+Delta) = 1+(H_ij(t)-1)exp(-Delta/tau_j).
```

It recovers between every pair of spikes, including spikes within an
experimental burst. The continuous source suppresses that recovery while
`S=1`. It also turns a continuously specified release-factor evolution into
pre-jump impulse masses. Consequently it is not an exact event rewrite of
either the printed burst law or the SUR Euler source.

A **source-Euler-factor event embedding**, if separately considered, uses
`q_j=1+p_j` with the same between-spike exponential recovery. It remains an
engineered embedding because its recovery schedule and impulse readout differ
from the source. The two factors must not be silently exchanged. Root's
subsequent finite-domain question specifically selects this Euler-derived
factor for the mathematical transfer decision below; the exponential factor
remains a comparison, not an alternative to optimize against outcomes.

If a source production term is proportional to `f*A` throughout a burst,
integrating that term is another distinction from assigning pre-jump masses.
For a recovery-free segment of `N` pulse periods, the exact continuous
production integral is `A0*(exp(N*P)-1)/P` (limit `N*A0` at `P=0`), whereas
pre-jump exponential events sum to
`A0*(exp(N*P)-1)/(exp(P)-1)` (also limit `N*A0` at `P=0`).
This comparison concerns the printed continuous
law; the pinned source instead uses its new Euler-updated factor in release.

## What the pinned implementation actually does

The complete `base.py`, `ode.py`, `pde.py`, `models.py` and SUR example were
read, along with README, citation and package metadata. Root's download
manifest pins each file by Git blob and SHA256. No solver or example was run.

* `ODEModel.initialize` sets `dt=1/f`. `_solve_kinetics` returns
  `H+dt*(f*p*H*S+(1-S)*(1-H)/tau)`. From rested `H=1`, an active SUR
  step gives `H_new=1+p`. `solve` computes `A=prod(H_new)` before release.
  Thus the first source step is not a pre-jump unit mass.
* The chemical increment uses `release=L*DAp*I*f*S*A_new`, then subtracts
  old-state uptake `Vm*DAs_old/(DAs_old+Km)` and multiplies by `dt`.
  Electrode and adsorption updates use previous chemical states. Current,
  loss, uptake, sensor terms and concentration units are absent from a
  dimensionless rested-event mass normalization.
* `_set_stimulation` adds rounded inclusive Heaviside windows; both endpoints
  count. A grid-aligned 30-pulse, 50 Hz burst with output extending through
  its final update activates 31 source update steps. Two-decimal rounding
  can move boundaries. Overlapping windows can produce `S>1`, outside the
  binary-S domain of the preceding positivity proof. Test that source
  behavior explicitly; do not silently repair it or infer a burst detector.
* `nt=int(end/dt)+1` followed by `linspace(0,end,nt)` can give displayed
  grid spacing different from `dt` when `end/dt` is nonintegral; updates
  still multiply by `dt`. Source timing tests need both cases. An event
  construction must use the existing electrical timestamps and must not
  inherit the two-decimal stimulation rounding.
* Current `solve` accepts optional initial H, otherwise H starts at one.
  Chemical and electrode states still restart at zero; final H is not
  returned. This is not complete chemical continuation. Separate
  `solve_kinetics` and fitting paths still allocate three H factors while
  the main solver uses the configured count. The selected hypothesis has
  three factors and does not require a broader source API claim.
* PDE models use `dt=1/480` seconds for their one-micrometre grid and
  diffusion coefficient 240. Their active factor is `1+f*p*dt`; release
  also uses new H. They zero negative chemical concentrations. That clamp
  is not a cap on H and is not part of the proposed event-only transform.
* The shipped SUR example has `tau2=12.5 s` and `DAp=0.43`. The specified
  manuscript WT sweep-1 row has `tau2=15 s`; the primary-paper reviewer
  reports `DAp=0.420`. The shipped bundle must not substitute for that row
  or become an alternative selected for the fly outcome.

The requested event jump `q=1+p` directly matches one active SUR H update.
Proposed pre-H release equals `prod(H_post)/prod(q)` exactly in real
arithmetic, giving rested mass one. That fixed normalization, recovery
between every actual spike, removal of experiment burst metadata and an
impulse readout remain explicit engineering changes, not an exact source
reproduction.

## Exact event recurrence and finite versus ongoing domains

Let `h_n` be one factor immediately before spike `n`, starting with rested
`h_0=1`; let the same cell's interspike gap be `Delta>0`. Set
`r=exp(-Delta/tau)`, `a=q*r` and `b=1-r`. Then

```text
h_(n+1) = a*h_n+b
h_n = a^n*h_0 + b*(1-a^n)/(1-a),  a != 1
h_n = h_0+n*b,                    a == 1.
```

This supplies expected values without the future candidate's integration
helper. The steady pre-spike factor is `(1-r)/(1-q*r)` only when `q*r<1`.
For `q>1`, equality gives linear divergence because `b>0`; `q*r>1` gives
exponential divergence from the positive rested state. With `p<0` and either
positive proposed jump factor, `0<q<1`: the factor remains positive and
bounded by one from rest, and its periodic equilibrium is strictly positive
for any fixed positive gap. Therefore, if the facilitating factor diverges
at a fixed gap, the product release also diverges; the depressing factors do
not cancel it by tending to zero under this event/recovery recurrence.

For the exponential factor the facilitation boundary is exactly

```text
Delta > p_1*tau_1 = 0.07875 seconds
f_periodic < 1/0.07875 Hz  (approximately 12.6984 Hz).
```

For the Euler-derived jump factor it is instead
`Delta > tau_1*log(1+p_1)`, provided `1+p_1>0`.
Regular synthetic 50 Hz input is on the divergent side of both conditions.
This algebra does not evaluate the published source or any recorded neuron.

Indefinite divergence is **not** a proof of failure over a finite trial.
For `N` finite spikes from rest, exponential jumps and exact recovery imply
`1 <= H_1 <= exp(N*p_1)` and
`exp(N*p_j) <= H_j <= 1` for each depressing factor. Thus one conservative
finite-count product enclosure is
`exp(N*(p_2+p_3)) <= A <= exp(N*p_1)`. A caller's actual count/time domain
must be declared before using this enclosure. The analogous expressions use
powers of `1+p_j` for the other jump choice. They are not empirical bounds
on chemical release, and do not justify clamping a state.

The current simulator's selected DAN refractory rule permits gaps as short
as 11 electrical steps = 2.2 ms, much shorter than either tonic stability
boundary. A hypothetical 400 ms trial on 2000 steps can contain at most
182 such events for one cell. This is a structural upper bound derived from
the existing clock/refractory contract, not an observed event count. A model
explicitly restricted to a finite, reset trial must advertise that domain;
it cannot claim bounded steady tonic release. Increasing the refractory
period or dropping rapid actual spikes to obtain a stable release state
would change the accepted input contract.

## Decision for the specified 400 ms reset construction

**Mathematically transferable as an explicitly engineered finite-domain
hypothesis, subject to its independent synthetic implementation gate.**
There is no positivity, finite-horizon divergence or tail inconsistency
requiring rejection of the fixed WT sweep-1 `q=1+p` construction. This is
a finite-domain judgment, not approval of measured fly kinetics or learning.

Use the deliberately looser binary limit of one event in each 0.2 ms step:
at most 2000 events per cell in the 400 ms trial. This does not rely on
the stronger refractory bound or on any recorded history. Exact recovery
is a convex combination of the previous state and one. Induction gives,
both at events and during quiet intervals,

```text
1             <= H_1 <= 1.0105^2000
0.997^2000    <= H_2 <= 1
0.9989^2000   <= H_3 <= 1
(0.997*0.9989)^2000 <= A <= 1.0105^2000.
```

These are strictly positive finite numbers, with conservative normal-range
enclosure `2^-14 < A < 2^32`. For example, `log(1+x)<=x` bounds the upper
exponent by 21, and `log(1-x)>=-x/(1-x)` bounds the lower exponent above -9.
Individual factors also stay far from float64 underflow/overflow. Pooled
impulse mass summed over all 2000 steps is less than `2^43` per channel.
No invented resource cap, discarded spike or altered parameter is required.
Numerical error still needs independent validation; representability alone
is not an accuracy test or a guarantee of zero downstream gain-bound hits.

Resetting H to one when each electrical trial resets is coherent with this
domain. It is not long-term steady release or a source chemical checkpoint.
Pre-H mass one at rest (equivalently post-H divided by fixed `prod(q)`)
preserves the chosen rested impulse scale without changing eta. Every actual
cell event advances the declared release state; requested teaching labels do
not decide which events count. Quiet recovery emits no impulses, so the
existing bridge's complete no-new-event tail is coherent after the last
admitted release. The fixed learning onset and off/mask/checkpoint rules
remain separately enforced.

The synthetic gate must cover the full claimed binary domain, including
2000 maximally packed events as a conservative numerical stress fixture,
rested and irregular legal streams, and the analytic enclosures above.
It must not introduce a tonic-rate threshold as an input filter. Long-run
tonic behavior remains outside this reset construction's supported claim.

## Rest, event order, reset and tail

For rested factors, the first pre-jump release is exactly one. For two
spikes separated by `Delta`, the second release is exactly

```text
a_2 = product_j [1+(q_j-1)exp(-Delta/tau_j)].
```

It tends to one as `Delta` tends to infinity, and to `product(q)` as
`Delta` tends to zero. The latter is a mathematical limit, not permission
for duplicate same-cell events within one binary electrical step. Pre-jump
and post-jump release differ already on the first spike. Tests must label
and reject accidental swaps rather than treating them as harmless rounding.

Positive finite `q`, positive finite `tau` and positive initial factors
give positive real states and masses for every finite legal sequence.
This is not a float64 overflow guarantee. A numerical implementation must
report nonfinite state/mass or loss of its declared error envelope; clipping,
renormalization or saturation introduces additional dynamics. Euler jump
factors additionally require `1+p>0`; their arbitrary-parameter positivity
cannot be inferred from the exponential version.

No event means no release impulse. Silent recovery of `H` toward one is not
continuing dopamine input under the proposed impulse readout. After the last
event, `H` can recover exactly while the existing bridge completes the tail
of already admitted impulses. A concentration/clearance source instead
continues chemical dynamics and requires its own complete-tail contract.
These two meanings of tail are not interchangeable.

For a finite raster with T rows, row t occurs at exactly `t/5000` seconds.
`state_before[t]` should mean the recovered state immediately before that
row's event; `state_after[t]` should mean immediately after its kick, not
after the following electrical interval. They agree on silent rows. The
endpoint at `T/5000` includes the last quiet 0.2 ms after row `T-1`.
An empty raster has no releases and endpoint H=1. These definitions provide
explicit endpoint and zero-length tests without moving the event clock.

State initialization, carryover and the fixed 100 ms learning onset are
separate. Resetting `H` to one is a rested engineered reset, not a measured
tonic equilibrium. In root's specified every-actual-spike construction,
pre-onset events also advance H from the trial start. The existing bridge
still starts cold at its unchanged 100 ms onset; earlier release is not
silently backfilled into its filter state. No future test may shift that
onset or choose a reset convention after viewing qualification outcomes.
Off/frozen learning, excluded masks, float32 gain checkpointing and the
existing gain bounds remain their original independent contracts.

## Per-cell state before pooling

The causal input is each cell's actual nonnegative binary event, never the
taught-minus-untaught difference vector. In particular the saved negative
net offset is not a negative release impulse. Apply the nonlinear transform
to each cell's complete history, then pool with the fixed channel divisor
2 or 22. Do not feed experiment condition, requested pulse labels, trial
outcome, or an unregistered burst detector into the transform.

An exact noncommutation fixture uses two cells. In case A, cell 1 fires at
0 and `Delta`, while cell 2 is silent. In case B, cell 1 fires at 0 and
cell 2 fires at `Delta`. Both have identical pooled binary counts at every
time. Their second pooled release is respectively `a_2/2` and `1/2`.
Use the exact two-pulse expression above at a declared gap with `a_2!=1`.
The test requires no fitted threshold. It exposes why pooled taught records
cannot generally drive this mechanism. The first saturated event in the
saved audit identifies all participating DANs at that step, but does not
supply every later individual event assignment.

Cell permutations must carry their states and parameters with them; the
pooled output must remain invariant. Simultaneous events in different cells
must commute. Different channels must not share state or subtract their
signals. Matching complete local histories and initial states must produce
identical releases irrespective of irrelevant teaching metadata.

## Required synthetic comparisons before a transfer decision

| Family | Independently specified expectation |
| --- | --- |
| Quiet/rested and long rest | No impulse without an event; exact exponential recovery; first rested mass one. |
| Two events | Exact product expression above, both jump conventions separately, short/long gaps and tau in seconds. |
| Repeated events | Affine closed form for arbitrary fixed gaps and finite counts; include `a<1`, `a=1`, `a>1` and depressing factors. |
| Irregular gaps | Compose the exact affine maps in event order; a separate direct piecewise ODE/jump oracle must agree. |
| Source versus event embedding | During source `S=1`, no recovery; source Euler factor `1+f*p*dt`; event exact recovery persists between spikes. Agreement must be claimed only for the specific limiting/equivalent cases proved. |
| Source clock and state carry | Actual source step-size, event boundary, initial state, reset and previous kinetic-state handling must be pinned and checked. |
| Positivity/domain | Positive legal states remain positive; exponential and Euler jump domains differ. Explicitly test overflow/nonfinite rejection and finite-window bounds without silent caps. |
| Per-cell/pooling | Same pooled event stream with different cell assignments gives the analytic distinct releases; permutation and simultaneous-cell order controls pass. |
| Event identity | Reject negative/fractional/multiple same-cell binary events, invalid times/order, unknown cells or wrong channel routing; irrelevant teaching metadata cannot change release. |
| Onset/reset/off/mask | Declared release initialization/history is distinct from unchanged bridge write onset; retained checkpoints and excluded/off gain bytes obey the existing policy. |
| Complete tail | No new event release in silence; exact recovery endpoint; bridge tail for all admitted impulses, with any source concentration tail tested separately. |
| Coincident pair | With an otherwise isolated rested exactly coincident KC/DAN pair, the old antisymmetric bridge remains zero over the complete tail. Do not advertise the release transform as a Handler intracellular order detector. |

## Transfer or reject

A source reproduction can pass only against the pinned core's actual
discretization, switching and state continuity. A separately declared
engineered transfer can be considered only after its input units, jump
choice, readout phase, initialization, clock, domain and tail are fixed and
its independent synthetic comparisons pass. Neither pass calibrates fly
chemistry or demonstrates learning.

Reject an alleged exact-source mapping that silently changes `1+p` to
`exp(p)`, inserts recovery during an active source burst, substitutes impulse
sampling for a continuous production integral, or reuses experiment burst
metadata as a teaching gate. Reject an ongoing bounded-release claim for
the proposed affine event law on an input domain that includes its divergent
periodic streams. Do not rescue it with fitted caps, altered refractory
rules, discarded endogenous spikes or post-outcome parameter selection.

A clearly stated finite reset-domain hypothesis is not rejected merely by
its indefinite asymptote, but still requires honest source scope, finite
numerical verification and all unchanged learning/conditioning gates.
The existing learning failure remains unresolved regardless of these
preparation tests. No proposed mechanism is adopted by this report.
