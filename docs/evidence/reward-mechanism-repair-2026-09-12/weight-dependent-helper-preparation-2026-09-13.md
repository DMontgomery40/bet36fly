# Weight-dependent numerical helper preparation

September 13, 2026 UTC. This output-only helper implements the fixed engineered
law in the [source decision](dopamine-weight-state-decision-2026-09-13.md).
It has processed synthetic fixtures only. No saved circuit history, candidate,
native simulation, conditioning, network request or production change belongs
to this preparation. The existing failed mechanism pair remains failed.

## Fixed equation and numerical method

The helper retains eta 0.0005, normalization 0.96, the 100 ms rate filter,
500 ms eligibility filter and continuous gain bounds 0.5 and 1.5. With
`P=0.96 E_D R_K` and `N=0.96 E_K R_D`, it integrates

```text
dg/dt = 0.0005 [P (1.5-g)/0.5 - N (g-0.5)/0.5].
```

Gain changes at every integration substage. Positive and signed negative
eta-scaled weighted integrals are separate state variables. Their sum is
reported alongside the independently accumulated gain difference. Neither
instantaneous products nor the changing gain are replaced by an interval
average or a frozen checkpoint. This symmetric formula remains an engineered
hypothesis, not a calibrated fly release law, and does not remove fresh-gain
coincident-signal cancellation.

`weight_dependent_shadow.py` uses vectorized adaptive RK4 step doubling and
Richardson extrapolation, independently of the source agent's DOP853 solver.
Signal evolution between impulses is analytical. Finite electrical intervals
have a maximum numerical substep of 0.2 ms. The complete infinite no-event
tail is integrated over `z=1-exp(-t/500)` from zero to one, with continuous
polynomial transformed products and a maximum z step of 0.02. There is no
finite tail cutoff. Internal absolute error tolerance is 2e-15, with an
increment-scaled term 2e-14. These are numerical choices only.

A trial outside the continuous gain bounds is refined; it is never clipped.
Nonfinite derivatives or trial accumulations raise an error. A 20,000-attempt
limit applies to each interval, and failure to advance time also raises.
Optional guards run during each interval's work and the electrical loop;
the future runner must enforce the whole-study wall budget and preserve
partial artifacts. Adaptive error estimates are diagnostics, not a formal
interval proof or a bound on accumulated global error.

## Pure APIs and exact publication boundary

- `integrate_products(products, duration, initial_gain, max_step=.2, guard=None)`
  accepts scalar or vector initial gains and continuous nonnegative products.
- `interval(rk, ek, rd, ed, gain, duration, guard=None)` evolves the four signal
  states exactly and integrates weighted gain changes; positive infinity
  requests the complete tail.
- `shadow(kc, dan, pk, pc, dc, mask, groups, initial=None, learning=True, guard=None)`
  accepts binary 2000-row rasters, edge maps and an exact float32 checkpoint.
  It performs no file access and has no execution CLI or simulator dependency.

The wrapper admits events at steps 500 through 1999, impulse first, then
integrates each 0.2 ms interval. Thus the last event at 399.8 ms contributes
to the interval ending at 400 ms and its complete tail. Earlier rows never
enter rate or eligibility state. The four phases are 100–130, 130–300,
300–400 ms and the entire tail. There are 150, 850, 500 and one publication
respectively. DAN impulses use the mean of all declared cells in the channel;
tests include the fixed two-cell home and twenty-two-cell away populations.

An eligible gain stays double internally throughout a call. Each full
interval publishes float32 without feeding rounding back into gain or signal
state. Only the float32 checkpoint persists between calls. Excluded edges
and learning-off calls retain exact checkpoint bytes and report no learning
publications, signed effects or bound contacts. Shared KC identity across
channels does not introduce channel-order state advancement.

`phases` has shape `(4, edges, 8)` with ordered fields `positive`, `negative`,
`attempted`, `double_applied`, `published_applied`, `bound_low`, `bound_high`
and `rounding_ambiguous`. `grouped` has shape `(4,8,8)` and reconciles those
edge fields through validated compartment/group mapping. Electrical and
final double gains, electrical and final float32 gains, phase endpoints,
publication counts and integration diagnostics remain separately returned.
The standalone helper does not prove that its maps are the actual 8,866
anatomical edges; the future runner must bind every scientific selector,
mask, input hash and ordered row before invoking it.

## Conditional numerical uncertainty

The fixed comparison allowance is 1e-11 for accumulated double gain at each
publication and at the final endpoint. It is not added once per electrical
step. The allowance is zero for exact excluded/off checkpoints. Float64
lower/upper diagnostics are rounded outward with `nextafter` and intersected
with the continuous bounds; this intersection does not alter computed gains.
Per-publication ambiguity counts report when the interval spans different
float32 publications. Additional `conditional_bound_counts`, an int64 array
of shape `(2,edges)`, counts every possible inclusive low/high contact from
both continuous and float32 endpoints. The original eight phase fields
remain unchanged.

All such enclosures are conditional on the declared numerical allowance.
The independent [exact guard](weight-state-exact-guard-contract-2026-09-13.md)
should consume double centers plus the exact allowance directly, avoiding
float64 endpoint double-rounding. It owns the exact integer trial sums,
eight-row guard and conservative all-pass/all-fail/inconclusive classification.
Passing helper tests cannot turn a conditional error allowance into a
validated mathematical enclosure or qualify a learning mechanism.

## Synthetic evidence and preserved correction

The final helper suite contains 120 cases; an independently authored source
suite contributes 112 additional cases. All 232 pass in 9.10 seconds on
helper SHA256 `170ccf5c1bd533cd58f38e32d6b2f8034171db507a8ec156a33647532a2b184d`.
Ruff passes. Coverage includes analytic constant products, changing-gain
nonconstant products, independent event superposition, 70-digit full-tail
references, arbitrary signal states, finite and complete-tail intervals,
pure-branch limits, vector/scalar and permutation consistency, exact phase
boundaries, cold onset, checkpoints, two/twenty-two population normalization,
masks/off, all eight groups, input immutability, exact and allowance-only
bound contact, cancellation/work caps and malformed numerical inputs.

Own review exposed a generic extreme-input defect after the first benchmark:
finite symmetric products could overflow accumulated signed areas into NaN
while leaving gain finite. Six scalar/vector overflow cases first failed as
expected, then passed after explicit overflow/invalid and finite trial-state
rejection. Three extreme-product controls with finite integrals remain valid.
This correction changes failure handling, not the equation or tolerances.
Earlier test logs and the benchmark's prior source hash remain preserved.

The source agent's final independent review also re-ran all 432 distinct
synthetic cases: these 232, the frozen reference's 109 and exact guard's 91.
They passed in 16.16 seconds with Ruff clean. That review clears the bounded
mathematics and the rejection-only delta, preserves its initial review and
the exact earlier helper snapshot, and retains the conditional-error limit.
Runner identity, caps and persistence remain a separate review boundary.

Exactly one parent-authorized synthetic size benchmark generated 2000×4064
KC rows, 2000×24 DAN rows and 8,866 toy mapped edges, including 4,184 home,
4,682 away, 3,239 eligible away and 1,443 excluded edges. No actual graph or
capture was read. Seed 20260913 and all generated byte hashes are retained.
It completed in 2.535482542 seconds under a 120-second cap, with 1,757 accepted
and 1,760 attempted vector substeps, finite gains, 1,501 publications per
eligible edge and exact excluded checkpoint bytes. Its source was
`fe8fa0d9e782870fbcdc17b3f449b03b8414764d3fc67888866dc82f633d7be5`, before the
subsequent rejection-only hardening. No second size benchmark was run.
This is preparation timing and does not guarantee actual-history duration.

The evidence is numerical preparation only. Repository-wide verification and
any later hash-frozen 32-history study belong to root; neither a native gate
nor a saved-history evaluation was invoked by this helper task. Production
API and Training surfaces remain accurate because no production mechanism,
artifact or qualification result changed.
