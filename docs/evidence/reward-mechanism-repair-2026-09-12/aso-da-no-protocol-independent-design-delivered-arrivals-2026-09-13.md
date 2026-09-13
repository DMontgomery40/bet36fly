# Independent checks before the Aso source-protocol calculation

September 13, 2026; repository checkpoint `7698c152825643f6b2dccd30d1903738a30d6c74`.
This is a mathematical design, not a source-protocol execution, fit, new
candidate or MaleCNS experiment. The frozen independent helper
`aso_da_no_reference.py` and its source parameters remain unchanged.

## Source personally inspected

I reread the complete modeling Results and Methods in the copied corrected
article, including equations 1–4, Figure 8 and its two supplement captions,
plus Figure 6/7 captions and the olfactory-learning Methods. Source:
[Aso et al. 2019, eLife 49257](https://elifesciences.org/articles/49257),
DOI `10.7554/eLife.49257`; copied `intracellular-primary-2026-09-13/PMC6948953.xml`.
The existing retrieval receipt records the exact download identity. This
pass made no network request. I then personally viewed the official v3 PDF
renders of Figure 6, Figure 7, Figure 8 and Figure 8 supplement 1 (printed
pages 27, 29, 31 and 32). The corresponding PDF and retrieval receipts are
in `aso-source-protocol-primary-2026-09-13`. A separate PDF text-coordinate
inspection resolves the duplicated axis label described below; its exact
evidence is `aso-figure7-axis-audit-delivered-arrivals-2026-09-13.json`.

The model describes dimensionless latent effects `d,n` and expressed
effects `D,N`, not receptor occupancy or chemical concentrations. Parameters
are the already frozen `A_D=4.3/60`, `A_N=.96/60`, `B_D=.26/60`,
`B_N=.16/60` per second, `tau_D=30`, `tau_N=600` seconds. The source fitted
these induction/reversal rates to external behavioral data. No new fitting,
time compression, old production eta or gain bounds belongs here.

## Invariants of any frozen sequence

For either branch, write latent state `x`, expressed state `X`, induction
rate `A`, activated-DAN recovery rate `B`, and `mu=1/tau`. Both states remain
in `[0,1]`. Segments change derivatives, never state instantaneously.
Independent DA and NO branches share the declared activity inputs, but do
not exchange state.

- During coactivity, `x1=1-(1-x0) exp(-A T)`; with DAN alone,
  `x1=x0 exp(-B T)`; without DAN, `x1=x0`. These are exact endpoint
  identities, including nonzero initial states.
- Splitting a constant-input segment or inserting an observation leaves
  subsequent states unchanged within the frozen numerical tolerance.
  Reordering distinct input modes generally changes the result. An
  observation must not secretly reset state or advance the main trajectory
  twice.
- After any number of coactivity intervals separated only by genuine quiet,
  `x=1-(1-x_initial) exp(-A sum(T_coactive))`. Latent induction depends on
  total paired duration in this restricted case; expressed state depends
  on the placement and duration of the gaps. This is not an assertion of
  invariance when DAN-only intervals intervene.
- For rested acquisition, latent state and expressed state increase, with
  `0 <= X <= x <= 1`. DA-only weight `1-D` consequently decreases, and
  NO-only weight `1+N` increases. The combined weight is their product.
  There is no general monotonic-weight invariant when both branches operate.
- Given identical input sequences and matching initial branch states,
  `D_both=D_DA-only`, `N_both=N_NO-only`, and
  `w_both=w_DA-only*w_NO-only`. The absent branch must start and remain
  exactly zero. Null-from-start is not an acute inhibition or erasure
  intervention on an already populated branch.
- KC-only segments have the same state dynamics as fully quiet segments
  under this contract. That includes observation periods with odors but no
  DAN activity. Their elapsed duration still changes expressed state.

All four states, rather than weight alone, must therefore be retained at
every segment boundary and observation. The prior independent test already
demonstrates equal current weights with different latent states and
different later quiet weights.

## Quiet time and reversal require different assertions

For a finite quiet delay `q`,

`x(q)=x0`,

`X(q)=x0+(X0-x0) exp(-q/tau)`.

Thus expressed state lies between its initial value and its latent target,
approaching that target monotonically. Complete quiet gives `(d,n,d,n)`,
not zero. Its weight is `(1-d)(1+n)`. A delayed observation cannot be
replaced by this infinite limit. Background-DAN memory decay is a different
source regime, with different fitted rates, and is not genuine quiet.

DAN-only reversal makes latent states decrease immediately. It need not
make expressed states decrease immediately. At entry,

`X'(0)=mu*(x0-X0)`.

When `0 <= X0 < x0` and `B>0`, expressed state first rises, then declines.
For `mu != B`, its unique turning time is

`t_star = log(1 + (mu-B)*(x0-X0)/(B*x0)) / (mu-B)`.

At equal rates the continuous limit is

`t_star = (x0-X0)/(B*x0)`.

These formulas apply only to the stated nonzero-latent conditions. If
`X0>=x0`, expression decreases from entry; a fully zero branch remains zero.
No immediate weight-recovery requirement should reject a valid delayed
trajectory. In the combined model,

`w' = -(1+N)*(d-D)/tau_D + (1-D)*(n-N)/tau_N`,

so either branch can dominate the instantaneous weight change.

Sustained DAN-only activation eventually sends all four states to zero and
weight to one. A **finite** activated interval followed by genuine quiet
instead tends to its remaining latent states, which generally are nonzero.
Calling the latter complete erasure would be incorrect.

For representative A-selective and B-selective KCs, a reversal interval
with odor B and the same DAN input makes the A-selective latent state decay
while the B-selective latent state acquires. An overlapping KC is coactive
under either odor and does not obey the A-only recovery equation. The
source's random ten-percent odor populations and softmax readout must not
be inferred from just two representative trajectories. A state contrast
is not automatically a reproduced performance index.

## Ambiguities to freeze before execution

1. Figure 7A visibly contains **three** acquisition and **three** subsequent
   reversal bouts. Figure 8 supplement 1 plots four test indices, although
   its caption calls the first two and second two “pairings.” The visible
   Figure 7 bout count should take precedence over that loose caption.
   Acquisition A occupies minutes `[1,2]`, `[7,8]`, `[11,12]`; control B
   occupies `[3,4]`, `[9,10]`, `[13,14]`; tests occupy `[5,6]`, `[15,16]`.
   Thus an intermediate test separates the first and second acquisition
   bouts; the whole schedule is not uniform four-minute repetition.
2. The official Figure 7 bottom axis has **seventeen** tick labels:
   `16,17,18,19,20,20,21,22,23,24,25,26,27,28,29,30,31`.
   Two successive ticks are printed `20`. This explains why the final
   label reads 31 despite the top and bottom blocks having the same width.
   A declared continuous sixteen-minute second block must explicitly
   correct the second `20` and all following labels by adding one. Under
   that interpretation, reversal B/DAN bouts are `[17,18]`, `[23,24]`,
   `[27,28]`; control A is `[19,20]`, `[25,26]`, `[29,30]`; tests are
   `[21,22]`, `[31,32]`. The DAN-only comparator uses those same DAN bouts
   without odor. Preserve the printed error and the interpretation; do not
   claim an exact author-code clock was recovered.
3. Test windows are drawn, but the model figures do not specify whether
   their plotted value is a start, end or window-average readout. Record
   start, last-30-second start, and end states/weights for each test as
   explicit samples, as root subsequently froze. None is automatically the
   authors' PI or a window-average result.
   Likewise, red LED strokes represent experimental stimulation; use a
   declared continuous Boolean model-DAN envelope over each depicted bout,
   not individual LED strokes or somatic spike counts. The source methods
   also refer to
   Figure 7F, although the copied Figure 7 caption lists panels A–E.
   Figure 8C's caption refers to data from Figure 7 while parameter fitting
   uses Figure 6B. These citation inconsistencies do not define a readout.
4. The source initializes `D=N=0` at the beginning of each “trial,” without
   unambiguously defining a trial as a whole assay versus a training block
   in that sentence. The component contract supplies a rested four-state
   initialization for each independent case. It must not reset between
   training, gap, reversal and observation segments of that case.
5. Figure 8E's 24-hour decay uses separately fitted background-DAN rates
   (`.0027` and `.0016` per minute; its text repeats the DA subscript).
   The current component has activated-DAN rates `.26` and `.16` per
   minute and a true-quiet mode. A quiet-delay demonstration is valid,
   but is not a Figure 8E memory-decay reproduction. No background rate
   or duty cycle is selected here.
6. The source specifies random ten-percent KC odor membership and fitted
   softmax constants. A representative-synapse protocol can omit them only
   with a corresponding limit on claims: state and normalized weight,
   not behavioral PI or exact Figure 8 curves. No new population seed,
   gain or readout is needed for the present component check.

Root and the independent source reader were notified of these ambiguities
before any numerical source-protocol result. The mathematical checks do
not require choosing a favorable observation time or changing parameters.

## Minimal saved-result checker

After root freezes the source matrix, a separate output-only checker will
read that exact declared sequence, its selected observation times and the
producer arrays. It will import only the frozen independent 70-digit
reference for its dynamics, never the producer's transition function or
saved states as its initial conditions for later computation.

Root subsequently froze seven protocols times four pathways, 28 cases,
each retaining A-only, B-only, shared and neither KC classes. The protocols
are naive/10-second/single-minute/three-minute Figure 6 acquisition, and
the three Figure 7 followups after their common acquisition. Figure 6 test
window is minutes 14–15; Figure 7 windows are 5–6, 15–16, 21–22 and 31–32
under the declared duplicated-label correction. Tenfold training and the
24-hour background-decay regime are excluded. Exact machine contract and
array schema will follow before implementation or execution.

The thin per-case schema needs segment-end times, all four states for all
four KC classes, the explicit inputs, and all requested observation times,
states and weights. States and times are float64, inputs Boolean; state
order is `d,n,D,N`. A requested quiet-limit array is separately labeled,
never inserted into the finite trajectory. Metadata identifies initial
state, source-null flags and exact schedule provenance. The independently
constructed seven schedules and four pathway assignments, rather than
producer-generated flags or whatever rows happen to be present, define
required coverage.

The checker independently composes every segment from the declared initial
state. Each observation is computed from the independent state at the start
of its containing segment. Boundary observations use the continuous state;
query insertion/order must not change later endpoints. Compare all four
states and normalized weights with the existing `atol=rtol=1e-12` policy,
without incrementing an allowance per segment or widening it after results.
Require exact schedule identity, array shape/type, finite values, state
bounds, null zeros and complete case coverage. No float32 publication,
current gain guard, Monte Carlo fitting or generic launcher is needed.

Small synthetic tests should cover the following families before dispatch:

- Complete valid multi-segment fixture and every Boolean input mode.
- Missing/duplicate/reordered case or schedule rows and wrong units.
- Wrong state-column order, latent/expressed swaps and nonlinear weight
  calculation, even when the current weight alone looks plausible.
- Mutated interior boundary versus final-only agreement.
- Wrong observation time, segment attribution, observation-induced reset
  or double advancement; valid boundary and repeated-query controls.
- Nonzero latent quiet continuation and separately requested infinite limit.
- Null-from-start exact zeros versus an invalid midstream erasure.
- DAN-only delayed-expression turn, compared to the independent solution
  rather than an incorrect immediate-recovery assertion.
- Pathway factorization and A-only/B-only distinctions if the frozen matrix
  includes those paired cases; no unrequested population model.

These are proposed checker tests, not executed protocols. The case count
is now fixed at 28; exact machine contract and producer schema are pending.
Tests will exercise numerical reconstruction only on explicitly synthetic
short toy sequences. They will inspect the real protocol schedule as data,
without calculating its trajectories before root dispatch. Numerical
component verification is already complete and will not be rerun merely
to expand this design. The existing failed native qualification, unchanged
guards, accepted stimulation and gains, masks, and full learning goal are
untouched.
