# Fixed weight-state shadow: preregistered rejection screen

September 13, 2026 UTC. Freeze this protocol, code, tests, reviews and original
inputs before evaluating any saved history under the new law. This is one
output-only experiment on all 32 already recorded untaught fine histories.
It makes zero network, native or neuronal calls and feeds no alternative gain
back into spikes. The second panel has already informed development; it is
not held-out evidence.

The [source decision](dopamine-weight-state-decision-2026-09-13.md) separates
the documented plasticity evidence from this new engineering assumption:

```text
P = 0.96 E_D R_K >= 0, N = 0.96 E_K R_D >= 0
g' = 0.0005 [P (1.5-g)/0.5 - N (g-0.5)/0.5].
```

Keep the existing 100 ms rate filters, 500 ms eligibility filters, actual
2-cell home and 22-cell away DAN population means, cold 100 ms history onset,
learning rate, channels and biological masks. Every trial starts from gain
one. All 4,184 home edges are eligible; exactly 3,239 gamma away edges are
eligible and 1,443 other away edges remain unchanged. No pooling or mask is
selected from these outcomes. The formula changes gain dependence throughout
each interval; it is not the old additive rule multiplied after integration.
It retains fresh-gain coincidence cancellation and is not a calibrated
receptor, release-probability or local dopamine concentration model.

## Complete timing and numerical contract

The original raster has 2,000 rows of 0.2 ms. Admit rows 500 through 1,999.
At row t, first inject that row's KC and averaged DAN events into their rate
states, then integrate from `0.2*t` to `0.2*(t+1)` ms. The final event is at
399.8 ms and its electrical interval ends at 400 ms. Continue all filtered
signals over the complete zero-input tail to infinity with the same changing
gain equation; this tail is an integral, not additional neuronal activity.

Use the independently tested adaptive RK4 step-doubling helper. Its analytic
rate/eligibility evolution, changing gain at every substage and transformed
complete tail must preserve separate eta-scaled weighted positive and signed
negative integrals. Keep double gain inside a trial and publish float32 after
each complete electrical step and once after the entire tail: exactly 1,501
publications per eligible edge. Do not feed publication rounding back into the
double gain. No routine clamp may hide an overshoot or nonfinite arithmetic.

Save every edge's four phase arrays: 100–130, 130–300, 300–400 ms and the entire
tail. Fields are weighted positive, signed weighted negative, attempted net,
double applied, published applied, inclusive lower/upper bound observations
and ambiguous publications. Also preserve phase endpoints, electrical/final
double and float32 gains, diagnostic error estimates, outward numerical
enclosures, per-edge publication counts and possible bound counts under the
declared allowance. Ineligible edge gains/accounting remain exact.

The previously frozen numerical comparison allowances remain **1e-11 for
gain and 2e-11 for each weighted area**, with zero relative tolerance. These
are conditional numerical allowances, not a formal global interval proof.
Estimated RK errors do not establish that proof. An independent direct-event
DOP853 reference and separate 70-digit integrating-factor reference already
cover synthetic timing, weighting, bounds and full-tail cases. No tolerance
is enlarged after inspecting this experiment.

## Unchanged screen and explicit ambiguity

For each of the two panels, two noise families and two channels, use all eight
trials and sum the eligible edges' final published gain changes. The criterion
is exactly `abs(mean) <= 0.5 * sample_SD`. Represent each float32 gain in common
integer ticks of 2^-24; with trial totals T, S=sum(T), Q=sum(T^2), the exact
eight-trial point comparison is **9 S^2 <= 16 Q**. Equality passes. The earlier
incorrect draft formula was rejected before freeze or outcome evaluation and
is documented in the [exact guard contract](weight-state-exact-guard-contract-2026-09-13.md).

For the conditional classification, use each computed double gain plus/minus
the unchanged 1e-11 allowance. Construct exact rational endpoints and round
directly to the float32 lattice with ties to even. Do not substitute an
intermediate rounded double or aggregate approximate SD for this decision.
The existing exact classifier encloses all possible eight-trial totals in a
box, computes the exact mean range, minimum variance and all 256 variance
vertices, then reports all-pass, all-fail or inconclusive. Its larger box is
conservative; all conclusions remain conditional on the gain allowance.

Reject this fixed-history hypothesis if any guard is all-fail or any possible
inclusive publication bound contact is observed. If all eight cells are
all-pass and possible bounds are zero, the result only permits considering a
new full-circuit candidate. Otherwise report inconclusive. A point pass with
ambiguous conditional classification is not sufficient. Rounding ambiguity
that does not affect this conservative guard classification is retained in
the artifacts and is not silently called exact numerical publication proof.

Complete all 32 predetermined histories even if an early guard appears poor;
stop only on a technical failure, source-integrity mismatch or the fixed wall
cap. Do not choose alternative histories, KCs, weights, thresholds, taus,
initial conditions or onset from the results. Failure rejects this specified
law on these captured trajectories; it does not refute biological learning or
recurrent effects. A favorable result is not acquisition, reversal or circuit
qualification. All seven original and second circuit criteria must pass under
a new identity before the separately frozen conditioning protocol can run.

## Independent audit, frozen before outcomes

Recompute all source/copy hashes, all 32 artifacts, all 8 guard cells, complete
edge eligibility and gain/accounting/publication/bound invariants. Select one
edge from each eligible anatomical group 0, 1, 2, 4 at the median index in that
group's original edge order, independent of activity or outcomes. Freeze those
four indices in the plan. For each selected edge in every history (128 scalar
comparisons total), reconstruct cold KC events and every contributing DAN event
with the exact existing population mass, then compare the independent direct-
event reference. Check electrical and final gains plus positive and negative
electrical, tail and total areas against the fixed allowances. The scalar
reference is not a second candidate evaluation or a neuronal run. No adaptive
edge replacement is allowed if an edge is silent or a discrepancy appears.

Any failed numerical comparison invalidates scientific interpretation until
its cause is resolved under a separate identity; do not relabel it as evidence
that the biological hypothesis failed. Complete array accounting and these
128 reference checks do not claim an independent ODE reconstruction of every
edge. Saved phase counters permit complete domain, sum, mask and endpoint
checks; every intermediate gain is not retained, so this audit cannot
independently reconstruct every transient bound or rounding counter. The
separately tested wrapper supplies those observations. Synthetic high-precision
tests and the conditional error boundary remain explicit.

## Bounded execution and preservation

Freeze one new SHA-derived identity with all 32 source archives, their capture
summary/receipt, original map/preregistration, current native source, connectome
lock, decision, numerical contracts, code, tests and completed prerun review.
Require exclusive creation of the output directory and files. Check bound
sources before and after; append and flush an attempt before each helper call.
Keep every completed row and any incomplete/failure journal. No resume, retry
or overwrite of this identity is allowed.

`summary.json` uses status `computed` for finished calculations and does not
by itself establish completion. A separate `completion.json` must have status
`complete`, the exact summary hash, the matching identity, 32 attempted and
completed rows, and elapsed time through summary persistence below the cap.
All 64 ordered attempt/complete journal entries and all 32 array/detail pairs
must exist. Any `terminal-error.json` invalidates completion. Keep the active
alarm through summary and completion persistence and check the clock after
both writes; a late terminal write produces a budget-failure marker. A failed
row-detail or completion write cannot increase the durably completed count.

The shadow has a **1,200-second cap**, including source checks and final
validation, with a ten-second reserve for terminal records. Exactly 32 helper
calls are permitted. The independent saved-output audit is a separate bounded
operation with 128 prescribed scalar references and its own 1,200-second cap.
The one earlier native-sized synthetic timing benchmark was preparation only;
it is neither this experiment nor a promised execution time. No additional
timing trial is needed. Original captures, scientific artifacts, model pointer,
Microduck source and dated copies remain untouched. Production/API/UI behavior
remains the current failed qualification state throughout this offline study.
