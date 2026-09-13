# Independent weight-state numerical reference

September 13, 2026 UTC. Preparation only. This module and its synthetic tests
do not read captured histories, import the simulator, run native code, or
authorize a candidate evaluation. The biological and engineering distinction
in [the source decision](dopamine-weight-state-decision-2026-09-13.md) remains
unchanged.

The fixed equation is

```text
P = 0.96 E_D R_K >= 0, N = 0.96 E_K R_D >= 0
g' = 0.0005 [P (1.5-g)/0.5 - N (g-0.5)/0.5].
```

Rates retain the 100 ms filter, eligibilities the 500 ms filter, and unit
events inject 1/100 ms into rates. Gain and event masses use the existing
dimensionless normalization. No biological or outcome-fitted parameter has
been added. `N` is nonnegative; reported `negative` areas include their minus
sign and eta.

## Executable interfaces

`weight_state_reference.py` provides three scalar functions:

- `integrate_products(function, (start,end), initial_gain)` integrates a
  supplied continuous nonnegative `(P,N)` drive. It returns gain and separate
  weighted positive/negative areas. This permits analytic constant, pure,
  balanced and time-varying product tests independently of event generation.
- `event_reference(kc_times, dan_times, end_ms=..., initial_gain=1,
  kc_weights=None, dan_weights=None, full_tail=True)` reconstructs continuous
  rates and eligibilities directly from all preceding impulses. It returns
  electrical and final gain, separate electrical/tail weighted areas, and the
  final float32 conversion. Duplicate events retain their mass. Fractional
  DAN masses allow the caller to specify the existing population mean.
- `mp_event_gain(...)` accepts the same event arguments and returns a gain
  computed with a separately derived 70-digit integrating-factor quadrature.
  Only input validation is shared with the ODE path. It does not call the
  double signal construction, ODE, product or transformed-tail functions.

Times are finite nonnegative milliseconds, with every event at/before the
electrical endpoint. The caller supplies only the events admitted by its
history policy, measured from that boundary; this module does not silently
choose an onset. The current cold bridge policy can therefore supply only
events from 100 ms onward with that boundary subtracted. An event exactly at
the electrical endpoint belongs to the subsequent tail. Event boundaries are
split explicitly so a future impulse does not contaminate a left-limit RHS
evaluation. `full_tail=False` requests a finite result and is explicitly
tested; other non-boolean mode values fail.

The module is a numerical oracle, not an experiment wrapper. It does not apply
cell eligibility masks, select bodies, normalize unknown channels, implement
per-step publication counters or persist checkpoints. It carries a double
gain continuously and reports final float32 publication. A later efficient
wrapper must independently preserve the accepted masks, population mean,
0.2 ms publication cadence, whole-tail publication, learning-off behavior,
inclusive bound observations and gain-only checkpoint persistence. Equality
of published bytes near a float32 rounding midpoint needs an explicit
numerical policy; an absolute gain tolerance alone does not prove it.

## Independent methods and complete tail

The first method reconstructs an event of age a as
`R(a)=exp(-a/100)/100` and
`E(a)=1.25 exp(-a/500) [1-exp(-0.008a)]`, then sums event masses. The latter
uses `expm1` for short ages. DOP853 integrates gain and both weighted areas
without clamping, with relative tolerance 1e-13, absolute tolerance 2e-15,
and finite-interval maximum step no larger than `min(0.5 ms, interval/8)`.

For the complete tail, use `u=exp(-elapsed/500)` and integrate `z=1-u` from
zero to one. Given rate/eligibility states at the endpoint,

```text
P/u = 0.96 R_K [E_D u^5 + 125 R_D (u^5-u^9)]
N/u = 0.96 R_D [E_K u^5 + 125 R_K (u^5-u^9)].
```

The transformed products are 500 times these expressions. Their limiting
value at `u=0` is zero, so no singular division or finite tail cutoff is used.
The transformed maximum step is 0.02. No synthetic observation is used to
select a shorter tail.

The second method independently rebuilds rate and slow eligibility
coefficients at each event boundary using 70-digit exponential sums. For an
event-free interval,

```text
x = g-1, Q=P-N=q exp(-lambda t)
S=P+N=A exp(-lambda t)-2C exp(-mu t)
lambda=0.012/ms, mu=0.02/ms.
```

The coefficients follow the fixed filters; `C=0.96*125*R_K*R_D` and
`A=0.96*[R_K*E_D+R_D*E_K+250*R_K*R_D]`. Set
`z=exp(-lambda*h)` for a finite interval and `z=0` for the full tail. With

```text
H(u,z)=A (u-z)/lambda - 2C (u^(mu/lambda)-z^(mu/lambda))/mu,
x_end = x_start exp[-2 eta H(1,z)]
      + eta q/lambda integral_z^1 exp[-2 eta H(u,z)] du.
```

`mpmath.quad` evaluates this bounded integral. Thus the high-precision method
does not propagate the first method's rate states or reuse its tail coordinate.
The full tail and each finite segment use the same derived expression.

## Frozen numerical allowances and tested scope

Before any saved-history evaluation or comparison with an efficient candidate,
the absolute comparison allowances are fixed at **1e-11 for gain** and
**2e-11 for each eta-scaled weighted area**. These are numerical allowances,
not biological thresholds or a relaxation of the existing diagnostic guard.
The ODE internal tolerances are stricter. No exact interval-arithmetic or
unlimited-domain error guarantee is claimed.

The 109 synthetic cases cover constant/pure/balanced drives, five initial
gains including both bounds, substantial saturation, exact exponential
exposure, unit coincidence with separately known opposing areas, both event
orders, mirrored initial states, repeated weighted histories, finite versus
infinite endpoints, shifting the electrical/tail partition, arbitrary finite
interval splits, no-input and one-input invariance, duplicate impulse mass,
final float32 conversion and malformed event/product/interval/mode families.
Final gain comparisons include independently derived analytic expressions and
the 70-digit integrating-factor method. Constant and balanced-event formulas
also independently check each weighted area; accounting equality alone would
not validate two areas that share the same error.

The test was written before the implementation. The initial missing-module
setup error was recorded, then an unimplemented API produced the expected
test failure. A later new malformed-tail-mode test failed before the boolean
contract was implemented. The finished suite passes. This is reference
verification, not evidence that the candidate learns or that an efficient
implementation agrees; that separate implementation has not been inspected
or run by this agent.
