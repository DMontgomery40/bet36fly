# Independent review of the selected KC local-calcium contract

September 13, 2026 UTC, checkout `b86405d`. This reviews root's selected
`kc-local-calcium-candidate-contract-2026-09-13.md`, not an alternate model.
No network, fit, parameter choice, saved-history evaluation or circuit run
was made. The external parameter vector and a successful bounded fit remain
separate prerequisites; this review does not claim that vector exists yet.

**The selected mapping is a concrete, mathematically coherent engineering
hypothesis under the admissibility conditions below.** Weighting actual KC
events before both matched filters preserves the existing exact bridge and
tail. Its additional information is the preceding local KC/neighbor state.
It can therefore change cell-specific and time-specific learning, but it has
no mathematical guarantee of neutral untaught gain. The pan-KC receptor
extension, per-frame spike scale, contact normalization and calcium-ratio
coupling are explicit transfer assumptions, not uniquely measured biology.

## Exact selected recurrence and a bounded ratio

Use seconds and the source step d0=1/30. The state immediately after frame n
is calyx activity C, axonal activity L, adaptation a and inhibition I. All
start at zero. For N_i actual spikes in the next completed source frame,
u_i=N_i. Thus one spike/frame supplies unit source input; equivalently
q=1/30 source-input seconds/spike multiplies that frame's mean rate. There is
no division by the alternating number of electrical samples.

Let W have postsynaptic recipients as rows, presynaptic KCs as columns, with
each nonempty incoming contact row normalized to one. g is the externally
fitted inhibition strength. The full source old-state equations are

```text
B_i = g * sum_j W_ij L_j
f_i = 1 / (1 + exp((L_i-inflection)/slope))
A_i = 1 - d0*(1+a_i)/tau_C
F_i = d0*u_i/tau_input
C_i_next = max(A_i*C_i + F_i, 0)
L_i_next = max(A_i*L_i + F_i - d0*I_i/tau_C, 0)
a_i_next = (1-d0/tau_adapt)*a_i + d0*kappa*C_i/tau_adapt
I_i_next = f_i * ((1-d0/tau_inh)*I_i + d0*B_i/tau_inh).
```

All right-hand sides use the old state; L_next does not use I_next and a_next
does not use C_next. Here kappa is the externally fitted adaptation strength.
No source noise, shock-only DAN function, depressive-only weight function or
learning-rate search is part of this mapping. Source time constants retain
seconds; bridge constants retain their existing millisecond conversion.

Assume finite nonnegative coefficients/states/input, positive tau_C,
tau_input and sigmoid slope, tau_adapt>=d0 and tau_inh>=d0, and **A_i>=0 at
each update**. If initially 0<=L<=C, then B>=0, 0<=f<=1 and the last two
updates keep a and I nonnegative. Also

```text
A_i*L_i + F_i - d0*I_i/tau_C <= A_i*C_i + F_i.
```

The nonnegative clip is monotone, so 0<=L_next<=C_next. Induction therefore
proves the held ratio s=L/C lies in [0,1] whenever C>0. At C=L=0 the selected
s=1 is well-defined as an engineering uninhibited reference. C=0,L>0 is an
invalid state, not another case for that fallback.

The A condition matters. For example, A=-1, C=2, L=1, F=3 and I=0 give
C_next=1 and L_next=2, although the old state obeyed 0<=L<=C. With F=1.5,
the same example gives C_next=0,L_next=0.5. A source Euler step can reverse
the ordering; silently clamping L/C would conceal that transfer failure.

Fail on any nonfinite intermediate/output, negative state, A<0, L>C, or
C=0,L>0 before accepting a candidate result. Do not change fitted parameters
or clip the ratio to make a failed trial admissible. The logistic should be
evaluated in a numerically stable form; exponential overflow must not become
an unrecorded exceptional path. Numerical tests must distinguish deliberate
source calcium clipping from an invented susceptibility clamp.

## Event phase, initialization and tail

The physical local states evolve from electrical time zero, including before
100 ms. The bridge filters remain cold until their unchanged 100-ms onset.
This adds a physiological-state hypothesis; it does not insert pre-onset
events into the bridge eligibility or revive the rejected onset-history rule.

Use source boundaries k/30 for integer **k>=1**, electrical event times
j/5000, and exact rational/integer comparisons. A convenient shared clock is
1/15000 second: electrical events occur at ticks 3j and source boundaries at
500k. Before an electrical event, advance all due source boundaries using
only events strictly earlier than each boundary. Read the resulting held
ratio for the current spike, then count that original spike in its new or
current source frame. Thus source updates precede electrical samples 167,
334,500,667,834,1000,...; exact100-ms coincident boundaries also precede
the current event. At zero there is initialization, not an empty frame.

Close the last completed frame at the declared electrical endpoint even if
there is no electrical event there. A 400-ms trial consequently completes
12 source frames. That last update cannot retrospectively change any event
weight. Retain integer counts, source-frame indices, source states and the
held ratio across implementation chunks; chunk boundaries are not resets.

The first event from a zero C,L state has susceptibility one, even if a
neighbor-driven I is present. A later frame can reveal suppression. Moreover,
s may approach zero while C remains positive and then jump to the declared
one at an exact zero state. This phase/discontinuity behavior is an explicit
consequence of the proposed ratio convention, not a physiological claim.
Test it directly, including a spike just before/at/after a source boundary.
Do not replace the exact zero case with an outcome-selected epsilon.

For actual event times t_m, supply
`S_local = sum_m s(t_m)*delta(t-t_m)` to the existing KC rate filter, with
the eligibility driven by that same rate. DAN inputs and both bridge time
constants are unchanged. A held calcium ratio changing between spikes makes
no bridge impulse. Once actual events stop, the existing full analytic
no-event bridge tail is exact; no calcium cutoff is needed to end learning.

If a continuous physical-time interpretation after the endpoint is needed,
continue the same source recurrence with N=0. Under admissibility, put
z=1-d0/tau_C, alpha=1-d0/tau_adapt, beta=1-d0/tau_inh. With M=max_i C_i at
the start of this continuation, C_i(n)<=M*z^n. Adaptation is bounded by the
convolution of that bound with alpha^n, and inhibition by its convolution
with beta^n times g (since L<=C and each W row sums to at most one). All
states tend to zero for finite admitted time constants. This is a mathematical
continuation, not additional spikes or a carried next-trial state. If actual
tail values are computed, the same domain checks apply; no finite cutoff
should be labeled the exact physical tail. Because the state has no further
influence on learning after the last event, root may retain the terminal
state plus this closure instead of numerically iterating to an arbitrary
tolerance. The next trial starts with new zero local states; only gains carry
where the accepted protocol specifies them.

## Contact scope, the home channel and what can be falsified

The retained graph stores outgoing rows (pre->post); constructing the local
W requires the opposite recipient-row orientation. Use raw contact counts,
exclude the one self-pair only from this newly declared lateral branch,
normalize incoming rows, and keep empty rows zero. The electrical self-pair
and every other fast contact remain intact. No APL/KC electrical gain or
transmitter sign enters W. This is contact-supported coupling; released
counts do not measure receptor abundance, local calcium or conductance.

Root's selected extension applies the same local-state mechanism to all 4,064
KCs. This can affect home's all-class event histories without removing any of
its 4,184 eligible edges. Applying a receptor only to gamma KCs would leave
other classes directly unmodulated, although later recurrent feedback could
still reach them; there is no theorem that either scope fixes or cannot fix
the home guard. The pan-KC option makes the proposed reach explicit, but the
gamma physiology does not establish its validity in alpha/beta,
alpha-prime/beta-prime or unresolved types. Keep an explicit unresolved/other
bucket alongside named subtype summaries. Away's 3,239 supported eligible
edges and 1,443 nonplastic transmitting edges retain their existing flags.

This candidate affects **plasticity susceptibility** through weighted KC
events. It does not assert that fast axonal release or MBON firing equals
the source L variable. Fast sensory transmission and no-learning trajectories
must remain unchanged; in live learning, subsequent recurrent activity can
change through updated gains. The source's direct L-dependent depressive
learning is motivation for the local signal, not the equation being copied.

Several pre-outcome tests distinguish this mechanism from scalar retuning:

- With g=0 or W=0 and zero initial I, calyx and lobe updates are identical,
  so s=1 for every event. This must reproduce the original bridge exactly
  even though C and a still evolve. Adaptation alone is therefore canceled
  by the ratio in this ablation; it is not the rejected dopamine-adaptation
  shadow.
- For fixed local old states and recipient modulation, increasing neighbor
  B increases I_next; its influence on L appears at the subsequent update.
  For fixed B and I, increasing recipient L decreases f and thus I_next.
  These are controlled local identities. They are not a proof that the
  fully recurrent network's ratio is globally monotone with every input.
- Correct source-function agreement on matched external inputs, asymmetric
  W/permutation tests, empty/self-row cases, and multi-step old-state tests
  must distinguish this mapping from a matrix transpose or simultaneous
  update error. Recorders and chunk sizes must not change trajectories.
- No DAN events imply no learning; no-learning mode and excluded masks leave
  gains unchanged. Identical weighted histories still obey current isolated
  coincidence cancellation and the full timing kernel. An external teaching
  label must never select s or switch plasticity.
- Since 0<=s<=1, local KC rate and eligibility are pointwise dominated by
  their raw-event counterparts. For fixed histories, each separate positive
  and negative bridge product area is correspondingly no greater than its
  raw-KC reference. This provides a useful independent accounting invariant;
  it does not determine their signed difference or prove the untaught guard.

Any inadmissible row invalidates the complete fixed 32-history screen; it
cannot be dropped. All eight unchanged cells, masks, publication semantics,
hash bindings and original trials remain required. A favorable offline screen
still requires both independent live qualification panels and the accepted
acquisition/reversal controls. No proposed identity is yet qualified here.

## Review boundary

The concrete changes requested of root before freeze are: specify k>=1 and
endpoint frame closure; explicitly reject invalid/nonfinite states and ratio
cases; scope local monotonicity tests correctly; retain unresolved subtypes.
The core selected mapping has no further mathematical contradiction found
in this review. Its parameter vector must independently pass the external-fit
and numerical admissibility gates, without using BET36FLY outcomes to choose
a replacement if those gates fail.

All current narrative docs/wiki were reconciled against the preserved personal
reading chain. The new 08:51 handoff section, full final source result/reviews,
current local-KC page and root's complete proposed contract were personally
read. Current graph orientation, reward constructor and bridge event/tail
code were rechecked, as were the complete upstream core definitions. This
report is output-only; no production/shared-narrative edits or implementation
claim belongs to it.
