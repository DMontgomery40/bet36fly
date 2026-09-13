# Aso DA/NO source component: fixed implementation contract

September 13, 2026. Starting checkpoint bcefc77. This is a standalone
reimplementation of published equations, outside the MaleCNS simulator.
It is the next bounded implementation in the active learning repair, not a
selected replacement for the production learning rule.

## Source and scope

Aso et al., eLife 2019, DOI [10.7554/eLife.49257](https://elifesciences.org/articles/49257),
Methods equations 1–3, describes latent effects d,n and delayed expressed
effects D,N. Its multiplicative weight is (1-D)(1+N). The fitted induction
rates are 4.3 and 0.96 per minute; reversal rates are 0.26 and 0.16 per minute;
expression times are 30 and 600 seconds. These are phenomenological memory
states, not dopamine/NO concentrations or identified receptor occupancies.
The model concerns PPL1-γ1pedc. NO is not required for the paper's backward
valence inversion. γ3 staining did not establish PAM-γ3 NO synthesis. The
2020 correction updates transcript processing, not these equations.

Retrieved corrected XML and correction are in intracellular-primary-2026-09-13,
with source URLs, UTC retrieval dates and SHA256 receipts. No published
executable model code has been identified in this inspection. This component
must be described as our equation reimplementation, never an author-code run.

## Frozen source parameters and inputs

Use seconds throughout: A_D=4.3/60, A_N=0.96/60, B_D=0.26/60,
B_N=0.16/60, tau_D=30, tau_N=600. No fitting, parameter search or time
compression. Inputs are piecewise-constant Boolean KC and DAN activity levels
representing the source experiment. They are not single somatic spike events,
local concentrations, sports labels, or commanded teaching-pulse metadata.

For each branch latent x and expressed X:

- KC and DAN active: x' = A(1-x).
- DAN active and KC inactive: x' = -B x.
- DAN inactive: x' = 0, whether the KC is active or inactive.
- At all times X' = (x-X)/tau.

Use the exact coupled interval solution, including coincident decay-rate
limits. No Euler stepping, intermediate clipping, or reset on a mode switch.
An input state is immutable; each call returns a new four-state value.
Initial states and every output must be finite and within [0,1]. Duration is
finite and nonnegative; tau positive and A/B nonnegative. Reject Boolean
values masquerading as numeric states, durations or parameters. Activity and
branch-enable flags accept only actual bool values. Alternate parameter values
are for mathematical tests only and are not a new candidate selection.

## Branch controls and persistence

DA-disabled means that pathway is absent from the beginning: d=D=0 is
required on entry and remains zero. NO-disabled analogously requires n=N=0.
Reject attempts to disable an already populated branch. This models source
null conditions, not acute inhibition, state erasure or a new output mask.
Both-disabled with zero state remains zero. Weight is always (1-D)(1+N),
without the production eta, gain bounds, normalization, or softmax readout.

For a complete quiet continuation, d and n remain fixed, while D tends to d
and N tends to n. Therefore the limiting state is (d,n,d,n), with weight
(1-d)(1+n). Quiet time does not erase memory. Expose this limit separately
from a finite elapsed-time advance; do not call it an electrical simulation.

## Acceptance before any source-protocol experiment

Tests must independently check zero duration, all four input modes, nonzero
initial states, split-time composition, near/equal decay rates, tiny/long
intervals, state and weight ranges, distinct KC histories sharing one DAN
input, branch-null controls, repeated acquisition, DAN-only recovery and
reversal. Compare both state pairs to an independent high-precision or matrix
exponential reference; it must not import the implementation's solver.
Preserve the initial failing tests and final output. Do not construct another
generic launcher or artifact-validation framework for this pure component.

A source-protocol calculation can use the paper's explicit activity durations
after the component passes. It cannot establish MaleCNS learning. Translating
actual spikes into these activity levels, anatomical application beyond the
source compartment, state persistence across simulator calls, and interaction
with the fixed qualification protocol remain separate decisions. Neither a
new circuit run nor a modification to timing, masks, gains, model pointer,
API or frontend is authorized by this component specification.
