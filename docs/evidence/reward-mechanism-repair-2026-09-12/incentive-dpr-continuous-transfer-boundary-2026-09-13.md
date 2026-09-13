# What a positive-spike transfer of the published DPR would change

September 13, 2026 UTC. This is an analytic source-transfer check, not a new
BET36FLY candidate or an analysis of saved circuit outcomes. The source is
[Gkanias et al. 2022, eLife 11:e75611](https://pmc.ncbi.nlm.nih.gov/articles/PMC8975552/).
The relevant released Handler helper and figure driver are byte-identical at
the paper's archived commit `98a8f85745a1426e8e5b787ceedd3f680a2b66c6` and the
inspected current commit `1610c80072fe8bb59bd397e7a61f716393a509b9`.
[Preserved comparison](incentive-circuit-source-2026-09-13/publication-revision-receipt.json).

The source's coarse DPR permits dopamine-driven recovery when a KC is inactive.
That property does not automatically survive replacing its signed modulatory
factor with two normalized filters of actual nonnegative DAN spikes and
integrating a complete continuous tail. The source also does not fix the
spike-to-rate units of such a replacement.

## Recovery over the entire continuation

Consider the proposed mathematical transfer, without selecting it:

```text
tau_s * dD_s/dt = u - D_s
tau_l * dD_l/dt = u - D_l
delta = D_l - D_s
y = w - w_rest
dy/dt = eta * delta * (K + y)
```

Here both filters have unit DC gain, start at zero and receive the same finite
input. With a complete no-new-input continuation, both return to zero and
their total integrals equal the total input. Consequently `integral(delta)=0`.
For a KC inactive throughout (`K=0`), the exact solution is
`y_final = y_initial * exp(eta * integral(delta)) = y_initial`.
A finite window can show recovery that later reverses. This result does not
assume a particular dopamine pulse amplitude, spacing or number.

The source's discrete update instead multiplies an inactive KC's offset by
`1 + eta*delta_n` each sample. If all factors are positive and the summed
delta is zero, `log(1+x) < x` yields a strict contraction for a nonzero sequence.
This residual can depend on the Euler clock even though the exact continuous
solution returns to its original offset. It is not an independently established
molecular recovery process.

The source's signed `US - previous MBON` feedback and independent clipping of
the two filters can violate equal-area assumptions when a KC is active. Its
coarse circuit uses a separately signed DAN-to-plasticity matrix. Neither is
the same as this positive-spike transfer. For a KC inactive throughout the
Handler helper, its MBON is zero, so that feedback exception disappears.

## The small-learning-rate pair response has a different clock

For unit-area impulses, let `a` be DAN time minus KC time, and let K have a
unit-area exponential filter with time constant `tau_k`. Starting at resting
weight, the derivative of final continuous DPR weight with respect to eta at
eta=0 is `H(a)=integral(K*(D_l-D_s))`. Its exact values are:

```text
a >= 0: H(a) = exp(-a/tau_k) * [1/(tau_l+tau_k) - 1/(tau_s+tau_k)]
a <  0: H(a) = exp(a/tau_l)/(tau_l+tau_k) - exp(a/tau_s)/(tau_s+tau_k)
```

For `tau_l > tau_s`, coincidence and DAN-after-KC responses are negative.
The backward zero occurs at DAN lead duration
`x = log((tau_l+tau_k)/(tau_s+tau_k)) / (1/tau_s - 1/tau_l)`.

Matching the source recurrence's poles uses
`physical_tau = -step_seconds/log(1-1/tau_samples)`; this preserves decay,
not the full nonlinear source model or its forcing amplitudes. The figure
driver supplies sample constants `100/3, 60, 104` for KC, short and long:

| Clock interpretation | Matched KC / short / long poles, seconds | Backward zero, seconds |
| --- | --- | --- |
| Paper's stated 100 Hz | 0.328308 / 0.594986 / 1.034992 | 0.545423 |
| Released 1,001 samples across 15 s | 0.492462 / 0.892479 / 1.552488 | 0.818134 |

Both zeros exceed the entire 400 ms BET36FLY trial. For this explicit
linear-response transfer, every possible pair within that window has negative
area; a positive sum of such pairs is therefore nonpositive. This is not a
prediction of the source's finite-eta, clipped feedback model, or of a new
MaleCNS experiment. It does show why copying the source constants and expecting
its long-delay order response inside our existing short trial is unjustified.
Changing the time unit silently would change the hypothesis.

## Verification and decision

[Analytic helper](dpr_filter_transfer_math.py) and
[78 independent tests](test_dpr_filter_transfer_math.py) cover exact pole
matching across clocks, positive/negative/equal filter families, both order
directions, coincidence, improper-quadrature agreement, finite versus complete
tail cancellation and invalid inputs. All passed; Ruff passed. No recorded
BET36FLY history, source induction condition, fit or native circuit was run by
this helper. The separate source-protocol reproduction has its own plan.

The mathematical check rules out claiming that a direct positive-spike,
continuous two-filter copy preserves the source's DAN-only recovery or timing.
It does not reject a fully specified intracellular model. Its signal units,
coincidence mechanism, feedback, kinetic constants and full-tail semantics must
be specified independently before any new candidate is evaluated. No parameter,
mask, accepted electrical gain, threshold or production rule changes here.
