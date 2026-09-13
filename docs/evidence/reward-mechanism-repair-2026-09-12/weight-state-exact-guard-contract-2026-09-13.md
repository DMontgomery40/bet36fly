# Exact published-gain guard and numerical ambiguity

September 13, 2026 UTC. Output-only synthetic preparation. No real trial,
candidate, circuit or network request was evaluated. This arithmetic preserves
the existing eight-trial criterion `abs(mean) <= 0.5 * sample_SD`.

## Independent derivation and corrected draft formula

Let `T_i` be each trial's exact summed eligible-edge gain change in a common
integer unit, `S=sum(T_i)`, `Q=sum(T_i^2)`, and `n=8`. Then

```text
mean = S/n
sample_variance = (Q-S^2/n)/(n-1)
4 mean^2 <= sample_variance
iff [4(n-1)+n] S^2 <= n^2 Q
iff (5n-4) S^2 <= n^2 Q.
```

For eight trials this is `36 S^2 <= 64 Q`, equivalently **`9 S^2 <= 16 Q`**.
The suggested draft expression `[4(n-1)+1] S^2 <= n Q` was incorrect and was
rejected before any plan freeze or data evaluation. The simple vector
`(1,0,0,0,0,0,0,0)` passes the actual mean/sample-SD guard but fails that draft
expression. This is an algebra correction, not a change to the scientific
criterion. `T=(5,3,1,-1,0,0,0,0)` is an exact nonzero equality example and
passes; increasing its final zero to one fails.

## Exact float32 accounting and rounding

Every finite float32 gain in `[0.5,1.5]` is an integer multiple of `2^-24`.
Below one, adjacent values differ by one such tick; above one, by two ticks.
`f32_trial_totals(gains, initial=1)` requires eight rows of nonempty selected
eligible edges, exact float32 values, and a scalar initial checkpoint that
is itself exactly float32 representable. It converts each delta to integer
ticks and sums using Python integers. Array reduction overflow and rounded
mean/variance calculations therefore cannot change `point_guard(totals)`.
The caller owns eligibility selection and the identity of the eight trials;
this module does not choose them or permit fewer rows.

`allowance_totals(double_gains, allowance, initial=1)` constructs a lower and
upper possible published total for each trial. The allowance may be a scalar
or an array broadcastable to the gain array. Inactive or learning-off edges
can use exact checkpoint centers with zero allowance. Each stored center and
allowance is converted to an exact rational number before subtraction or
addition; integer allowances also remain exact. The resulting interval is
intersected with the continuous law's `[0.5,1.5]` bounds. A disjoint interval
is invalid, not a reason to clamp the calculated center or infer a verdict.

`round_f32_ticks(Fraction)` performs nearest, ties-to-even quantization on
the correct float32 lattice directly. Monotonic rounding means the rounded
closed endpoints bound all possible float32 results. An intermediate
`float(Fraction)` is deliberately avoided: it can collapse an endpoint just
above or below an exact float32 midpoint onto that midpoint and double-round
to the wrong value. Similarly, ordinary double `center +/- allowance` can
lose a small allowance entirely. The tests include midpoint perturbations
of `2^-100` to detect both families.

This module consumes the declared center/allowance directly. A helper's
precomputed float64 lower/upper arrays are useful diagnostics, but they need
outward rounding if claimed as enclosures. They are not substituted for the
exact construction here. All conclusions remain **conditional on the
declared numerical allowance actually enclosing the continuous solution**;
exact downstream arithmetic is not a proof of an ODE error bound.

## Conservative universal classification

For each trial let the possible total interval be `[L_i,U_i]`. The classifier
deliberately includes the entire continuous box, which can be larger than the
actually attainable float32 total set. It selects no scientific routing or
plasticity parameters.

The mean interval is exactly `[sum(L_i)/8, sum(U_i)/8]`. Its endpoints give
the maximum possible squared absolute mean. The minimum is zero if that
interval crosses zero, otherwise the smaller squared endpoint.

The maximum sample variance is attained at a box vertex because variance is
a convex quadratic. All 256 vertices are evaluated using Fraction arithmetic.
The minimum is the squared distance between the box and the line of constant
vectors, divided by seven:

```text
min_variance = min_c sum_i distance(c,[L_i,U_i])^2 / 7.
```

Between consecutive endpoints, the active distances give a quadratic in c.
Its stationary point is the mean of the applicable interval endpoints; all
in-segment stationary points and endpoints are considered exactly. Clipping
c to each trial interval supplies the mathematical minimizing witness. That
witness is a certificate for the numerical bound, not a selected biological
weight map. The implementation checks `c=mean(witness)` exactly. Independent
tests additionally verify every bound/interior KKT condition and compare the
variance with an independently computed pairwise-difference expression.

The three possible results are:

- **all_pass:** `4 * maximum_mean_squared <= minimum_variance`.
- **all_fail:** `4 * minimum_mean_squared > maximum_variance`.
- **inconclusive:** neither sufficient inequality is established.

Equality is a pass only when the all-pass condition proves it. Equality in
the all-fail comparison cannot establish failure. Singleton boxes reduce to
the exact point criterion, including zero mean/zero variance. Wider boxes
may remain inconclusive even if all attainable discrete values happen to
share a verdict; no favorable result is inferred from that limitation.

`classify_box` returns exact Fractions, including the mean interval and
variance bounds. Persist them as numerator/denominator pairs or exact
strings. Converted floats can be shown as diagnostics, but must not replace
the exact comparison in the verdict.

## Verification and scope

The 91 synthetic tests pass, including all 6,561 eight-trial vectors over
`{-1,0,1}`, exact equality and one-tick neighbors with arbitrary-size integers,
every integer point in sixteen small boxes, twenty-four rational minimum-
variance certificates, every box vertex, float32 midpoint/binade cases,
large cancelling sums over 4,184 synthetic edges, bound intersection and
malformed shape/type/value/interval families. An odd integer allowance above
double's exact integer range exposed and corrected an additional conversion
bug before freeze. Both files pass Ruff.

The test-first failure and subsequent correction remain in the reading/freeze
receipt. These tests establish numerical accounting behavior only. They do
not qualify a candidate, prove learning, replace the remaining diagnostic
criteria, or authorize an actual saved-history run.
