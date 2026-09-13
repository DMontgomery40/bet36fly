# Incentive-circuit DPR: equations, executable timing and transfer limits

September 13, 2026. Independent source inspection only. No upstream model,
external fitting, saved-history candidate or native circuit was executed.

The executable source contains a real two-timescale distinction absent from
the accessible printed equations. It also contains a weight-dependent term
that operates without KC activity. Neither fact establishes that a continuous
positive-spike transplant would retain DAN-only recovery over its full tail.

## Paper equation boundary

The accessible [Gkanias et al. 2022 article](https://pmc.ncbi.nlm.nih.gov/articles/PMC8975552/)
prints equations 35–36 with the same decay coefficient
`lambda = 2 - 1/tau_short - 1/tau_long`. Their input coefficients differ.
For one depressing channel, write `a = -d^T W_minus >= 0`, with positive
modulation absent:

```text
D_down' = a/tau_short - lambda D_down
D_up'   = a/tau_long  - lambda D_up.
```

From zero initial states, linearity gives
`D_up = (tau_short/tau_long) D_down` for every input history. Consequently
their difference cannot become biphasic after a nonnegative pulse. Equation
37's instantaneous signed factor is a coarse reduction, not the finite-time
solution of these ODEs.

Figure 16 uses 60/104 from a comparison with Handler data, claims 100 Hz, and
does not establish exact receptor kinetics. The coarse behavioral treatment
uses 1/infinity. The public author response acknowledges earlier equation
corrections. The current HTML/code discrepancy is demonstrable; its exact
typesetting origin is unresolved because the PMC PDF returned a browser
challenge and the publisher PDF returned HTTP 403. No bypass was attempted.

## Actual released figure computation

I read the complete
[handler](https://github.com/InsectRobotics/IncentiveCircuit/blob/1610c80072fe8bb59bd397e7a61f716393a509b9/src/incentive/handler.py),
[figure driver](https://github.com/InsectRobotics/IncentiveCircuit/blob/1610c80072fe8bb59bd397e7a61f716393a509b9/examples/run_handler_2019.py),
[base model](https://github.com/InsectRobotics/IncentiveCircuit/blob/1610c80072fe8bb59bd397e7a61f716393a509b9/src/incentive/models_base.py)
and [circuit](https://github.com/InsectRobotics/IncentiveCircuit/blob/1610c80072fe8bb59bd397e7a61f716393a509b9/src/incentive/circuit.py),
plus README. Root pinned this public revision to
`1610c80072fe8bb59bd397e7a61f716393a509b9` (December 2, 2023).
I independently checked the saved publication-revision copies: handler and
figure driver are byte-identical at the article's archived revision
`98a8f85745a1426e8e5b787ceedd3f680a2b66c6` (March 28, 2022). That comparison
does not establish equality of the other two files across revisions.

For later samples, the actual handler recurrence is:

```text
K_n  = clip((1-1/tau_K) K_(n-1) + CS_n/tau_K, 0, 2)
m_n  = clip(K_n max(W_n,0), 0, 2)
a_n  = US_n - m_(n-1)
D1_n = clip((1-1/tau_short) D1_(n-1) + a_n/tau_short, 0, 2)
D2_n = clip((1-1/tau_long)  D2_(n-1) + a_n/tau_long,  0, 2)
delta_n = D2_n - D1_n
W_(n+1) = W_n + delta_n (K_n + W_n - 1).
```

At the first sample the source initializes K from CS and both D components
from US. The source's `passive_effect=1` makes its `maximum` algebraically
the identity. It does not project updated internal W back to nonnegative
values: the saved weight is `max(W_(n+1),0)`, and the MBON separately uses
rectified internal W. There is no upper weight bound in this handler.

The driver overrides the function's 58/100 defaults with 60/104. It leaves
`tau_K=100/3` and the 1001-point `linspace(-7,8)` unchanged. Thus the actual
sample interval is 0.015 seconds, or 66.6667 Hz. The constants count updates;
they are not 60 and 104 seconds or milliseconds. Their actual discrete
e-folding times are `-0.015/log(59/60)=0.892479 s` and
`-0.015/log(103/104)=1.552488 s`. These are source-derived model times,
not measured fly receptor constants. Half-open stimulus tests use the
floating grid directly; replacing it with ideal rational membership can
change a boundary sample.

The different poles permit a sign change. For an isolated unclipped impulse
of amplitude A delivered after initialization, after its first update:

```text
D1_n = (A/60)  (59/60)^n
D2_n = (A/104) (103/104)^n.
```

Their crossing is at 76.9812 updates, approximately 1.15472 seconds on the
released grid. This analytic example excludes feedback and clipping; it is
not a simulation or a prediction of a particular Handler trace.

## Two additional distinctions that must survive reproduction

The handler's reporter calculation is not its signed weight update. Define
`q=D1-D2`, `U=max(q,eps)`, `V=min(q,-eps)`. Its posthoc arrays obey:

```text
-dR1-dR2 = (U-V) (K+w_saved-1).
```

Here `U-V` is approximately `abs(delta)`, and `w_saved` is the rectified
post-update value. Actual weight change instead uses signed delta and the
pre-update internal weight. They cannot be used as interchangeable numerical
oracles. The figure driver further applies different display scales to the
experimental signals and separately normalizes each reporter across ISIs.
The biological labeling and data-window audit is owned by the independent
source reviewer; retain upstream array names without treating them as direct
receptor measurements.

The main base model is another regime. It uses instantaneous
`D=max(v,0) @ signed_modulation_matrix`,
`eta=1/max(nb_timesteps-1,1)`, and
`W_new=clip(W+eta*D*(K+W-W_rest),0,50)`. It normally performs four internal
relaxation repeats. It has no explicit US-only check in the weight updater.
The circuit supplies engineered feedback and signed modulation matrices,
including inhibitory susceptible-MBON to DAN feedback. Its gamma4 peer is
not this repository's selected PAM12/gamma3 away channel. These matrices,
units and 0–50 bounds are not our accepted electrical graph or 0.5–1.5 gains.

## Independent full-tail recovery check

Let a proposed continuous transplant use cold, unclipped unit-DC filters
`tau_s D_s'=u-D_s`, `tau_l D_l'=u-D_l`, a finite nonnegative actual DAN drive,
and complete continuation until both states vanish. Integrating gives
`integral D_s = integral D_l = integral u`, hence `integral delta=0` for
`delta=D_l-D_s`. Write `y=W-W_rest`. If K is identically zero, continuous DPR
would give:

```text
y' = eta delta(t) y
y(infinity) = y(0) exp(eta integral delta) = y(0).
```

Therefore this particular transplant has **no net DAN-only recovery after
the full tail**. A finite-window recovery segment cannot establish it.
Nonzero initial filter state, feedback-driven negative input, separate
clipping, unequal DC gains or truncation can break this identity; each would
be an additional assumption. For truly silent K in the handler, m is zero,
so its inhibitory-feedback exception disappears.

The source's discrete update instead gives
`y_N/y_0 = product(1+eta*delta_n)`. Even when the complete discrete sum of
delta is zero, this product is below one for a nonzero signal with positive
factors: `log(1+x)<x`. Its leading residual is
`-eta^2 sum(delta_n^2)/2` in log space. That contraction depends on the update
scheme and does not survive as an intrinsic continuous recovery mechanism.
The coarse signed-D base rule has no equal-DC cancellation requirement and
can recover inactive weights toward rest.

I also independently reviewed root's `dpr_filter_transfer_math.py` and all
78 tests, then ran that synthetic suite: 78 passed in 0.26 seconds. These
formulas are an analytic audit, not a replacement source implementation.
For unit-area KC and DAN impulse filters with positive time constants k, s,
l, the first derivative of resting-weight continuous DPR at eta=0 is:

```text
H(lag) = exp(-lag/k) [1/(l+k)-1/(s+k)]                 for lag >= 0
H(lag) = exp(lag/l)/(l+k)-exp(lag/s)/(s+k)             for lag < 0.
```

Direct integration gives a backward sign boundary
`log((l+k)/(s+k))/(1/s-1/l)`. With recurrence poles embedded using
`T=-dt/log(1-1/tau_samples)`, I independently obtained 0.545423 seconds for
the paper's stated 10 ms grid and 0.818134 seconds for the actual 15 ms grid.
Both exceed 400 ms; thus every pair wholly inside a 400 ms input window has
nonpositive linear-response contribution under these assumptions. This is
only the zero-feedback, unclipped, cold-state, full-tail derivative at
eta=0. It is not the finite-eta DPR result, the source's closed-loop response,
or a prediction of any recorded BET36FLY history.

## Constraint for the next decision

The signed dopamine factor and `W-W_rest` term are a concrete, source-defined
coupling, structurally different from multiplying separate positive and
negative bridge areas by remaining gain headroom. But copying only the
two filters onto positive recorded spikes can remove the very DAN-only
effect motivating the transfer. Nor should the handler's `US-m_previous`
be subtracted again from already recurrent DAN recordings without declaring
an additional feedback mechanism.

A 400 ms, 5000 Hz trial is shorter than the source's 500 ms CS and 600 ms US,
and spans neither of its full filter decays. Reproduction should first retain
the exact source clock, feedback, internal weights and reporter definitions.
Any later simulator mapping must separately fix input units, integration,
full-tail semantics and untouched-edge behavior without using the rejected
32 histories to choose them. Preserve accepted stimulation, electrical gains,
masks and qualification controls. No such candidate is selected by this audit.
