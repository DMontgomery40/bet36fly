# PPL101 individual-signal basis: fixed-history feasibility bounds

This is a new offline analysis, not a new learning rule or a circuit experiment.
It uses all 32 already captured fine untaught histories and the original cold
bridge boundary. No gain, channel, mask, onset, time constant or guard changes.
No coefficient is chosen from outcomes, and no alternative gain affects neurons.
The testable question is whether separating the two actual PPL101 histories
offers any mathematical freedom under fixed nonnegative normalized local
coupling, before interpreting unread synapse coordinates as a solution.

For each KC event at k and DAN event at d, the full infinite-tail signed change
under the existing 100/500 ms bridge equals
`eta * sign(d-k) * (exp(-abs(d-k)/100) - exp(-abs(d-k)/500))`, eta=0.0005.
This follows by integrating the two true continuous products, including both
100 ms rate filters and 500 ms eligibility states; the bridge normalization
0.96 cancels the integral factor 500²/(500²-100²). Retain positive and negative
areas separately. Events before the existing 100 ms onset are excluded.
Coincident events have zero net change but nonzero equal opposing products.

Derive one unnormalized basis per actual PPL101 body (11327 and 11900), per KC
and per trial. Their mean must reproduce the recorded cold home positive,
negative and net areas to the existing 1e-10 absolute numerical tolerance;
final float32 home gain bytes must match all 32 original captures exactly.
Check every source/capture/sample-map hash before and after analysis. Any
discrepancy fails the analysis before biological interpretation. Synthetic
tests use independent improper quadrature of the continuous products,
explicit event-pair reductions, permutations, malformed inputs and convex
envelope containment. Source code/tests/inputs are frozen before saved-basis
evaluation. No new neuronal or native call is permitted.

Map basis effects onto all 4,184 home edges. All remain eligible. The selected
away mask and transmissions are unchanged and are not evaluated as a candidate.
The sum of each edge's positive and absolute-negative areas bounds every prefix
change. Require every individual basis to satisfy
`absolute_area + 2*1e-10 + gamma_1501*1.5 + 2^-24 < 0.5`, where
`gamma_N = N*2^-53/(1-N*2^-53)`. The 1,501 double gain additions cover
1,500 active steps plus the tail; the float32 half-ULP also reserves distance
from inclusive published bound contact. This is conditional on the declared
per-product integration allowance. Canonical endpoint agreement alone is not
a formal arbitrary-prefix numerical proof. If this condition fails, do not
claim linear convex bounds cover clipped publication.

For each of the four eight-trial home groups, permit arbitrary convex weights
over the two DAN bases independently for every edge AND trial to obtain a
deliberately loose response interval: sum of edgewise minima to sum of maxima.
Any anatomically fixed constant coupling is a subset of this larger set.
Use float64 internal arithmetic. Expand each trial endpoint by
`4184 * (2^-24 + 1e-10 + gamma_1501*1.5) + rho` for final float32
publication, accumulation and numerical comparison error. Here
`rho = 1e-10 * max(1, max_trial sum_edge max_DAN abs(basis))` is a
declared reduction/statistics allowance. Derive the minimum possible
absolute mean from its interval and an upper bound on sample SD by evaluating
all 256 interval-box vertices; SD is a convex norm, so its maximum is at a
vertex. Further lower the minimum absolute mean by rho (floor zero), and
raise the SD maximum by rho. If that mean lower bound exceeds half that
SD upper bound, every
fixed normalized coupling is excluded on these same frozen trajectories.
This remains conditional numerical padding, not formal interval arithmetic.
Equality and numerical ambiguity are inconclusive. Otherwise the bound is
inconclusive: it does not establish a feasible
shared weight map, meaningful anatomy or a passing candidate.

Report both individual endpoint totals, their pooled canonical total,
per-trial differences, complete arrays and four necessary-exclusion bounds.
Do not optimize weights, delete KCs, suppress background, infer release from
contact counts, select a distance cutoff, alter criteria, claim source-cell
causality or qualify acquisition/reversal. A failure of this restricted
fixed-history class cannot rule out recurrent effects, receptor-dependent
state or general biological learning.

Fixed execution cap: one exclusive analysis identity, all 32 histories, no
adaptive repeats, 120 seconds for the analysis after its inputs are prepared.
Network requests, candidate/native/circuit calls and production edits: zero.
