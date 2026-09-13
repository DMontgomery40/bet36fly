# Independent solution of the Aso DA/NO source component

September 13, 2026; standalone preparation, no MaleCNS integration or run.

I read the corrected primary XML's full modeling Results and Methods,
including equations 1–4 and parameter-inference sections, and the root's
`aso-da-no-component-contract-2026-09-13.md`. The primary is Aso et al. 2019,
[DOI 10.7554/eLife.49257](https://elifesciences.org/articles/49257), retained
as `intracellular-primary-2026-09-13/PMC6948953.xml`. This implements its
published equations, not recovered author code. The model's variables are
phenomenological effects; they are not measured chemical concentrations.

The frozen source values are `A_D=4.3/60`, `A_N=.96/60`, `B_D=.26/60`,
`B_N=.16/60`, all s⁻¹, and expression times `tau_D=30`, `tau_N=600` seconds.
The A/B values were inferred from source behavioral data; the timescales are
source assumptions based on those data. None is fitted here. The much smaller
background-decay rates elsewhere in the paper are a distinct experiment and
are not silently substituted for these DAN-activation values. The source
softmax/readout and its fitted gain do not enter this component.

## Exact interval map

For either pair of states `(x,X)`, where `x` is latent and `X` expressed,
write a constant-input interval as

```
x' = lambda*(a-x)
X' = mu*(x-X),                 mu=1/tau.
```

Coactive KC/DAN means `(lambda,a)=(A,1)`. DAN-only means `(B,0)`.
When DAN is inactive, use `lambda=0`, `a=0`: `x` is held whether KC is
active or inactive. For initial `x0,X0` and duration `t>=0`,

```
x1 = a + (x0-a)*exp(-lambda*t)
X1 = a + (X0-a)*exp(-mu*t) + (x0-a)*F(lambda,mu,t)
F = mu*(exp(-lambda*t)-exp(-mu*t))/(mu-lambda).
```

At exact resonance `lambda=mu`, `F=mu*t*exp(-mu*t)`. This limit must not
divide by zero. Near resonance, a direct double subtraction of exponentials
can lose precision. The independent reference evaluates the formula with
70 decimal digits and rounds once at the returned float64 boundary. The
writer's implementation must solve that cancellation separately; it is not
imported by the reference. The matrix-exponential test oracle uses a separate
affine 5×5 system for `(d,n,D,N,1)`, so the tests do not merely restate the
closed-form code.

Piecewise histories compose these interval maps, preserving all four state
values. Zero elapsed time is the identity. Within one unchanged mode,
`F_map(t1+t2)=F_map(t2)∘F_map(t1)`; no mode switch or split may erase state.
Separate DA/NO branches do not obey a shared occupancy-sum constraint:
`d+n` and `D+N` need not equal one. Each individual component stays in `[0,1]`.
This follows from the latent convex relaxation and the expressed solution
as a positive weighted combination of its initial value and latent history.
Clipping is neither necessary nor authorized.

The normalized source weight is `(1-D)*(1+N)` and lies in `[0,2]`.
It is not the simulator gain with bounds `[.5,1.5]`, nor multiplied by its eta.
Both pathways can be populated simultaneously. Weight need not be monotone
during a mixed-pathway transition: DA recovery and NO recovery affect it in
opposite directions. A blanket monotonic-weight test would reject valid source
behavior; test branch states and the declared expression law instead.

## Quiet time, nulls, and hidden memory

With no DAN activity, `d,n` stay fixed. The exact quiet endpoint is

```
(d,n,D,N) -> (d,n,d+(D-d)*exp(-t/30),n+(N-n)*exp(-t/600))
```

and the infinite quiet limit is `(d,n,d,n)`, with weight `(1-d)*(1+n)`.
Quiet does not mean a source background-DAN condition and does not erase
memory. In contrast, sustained DAN-only activation with the fixed positive
B values eventually takes every state to zero and weight to one.

Two states with identical `D,N` and weight but different latent `d,n` can
produce different later weights with no new activity. Therefore storing only
current weight cannot preserve this model's history. Likewise, projecting to
the quiet limit at each segment boundary would change the finite-time source
protocol and remove its delayed expression dynamics. The quiet limit is an
explicit separate query, never an automatic hidden tail.

DA-null is a condition absent from the beginning: `d=D=0` is required on
entry and remains zero. NO-null analogously requires `n=N=0`. Disabling a
populated branch is rejected; it is not source-null preparation or acute
pharmacology. The reference returns a new array and never mutates its input.

## Independent acceptance coverage

The separate `aso_da_no_reference.py` has no producer, source executable,
native, capture or outcome imports. `test_aso_da_no_reference.py` checks all
four input modes with zero, nonzero and boundary states; exact/neighboring
resonance; interval composition; zero/1e−12/long durations; state and weight
domain; finite and infinite quiet continuation; source-null controls and
forbidden midstream erasure; distinct KC histories under a shared DAN input;
repeated acquisition and DAN-only recovery. Comparisons use fixed
`atol=rtol=1e−12`. Source-parameter API comparisons are added only against
the writer's standalone component, using synthetic histories.

These checks do not select an activity threshold for actual spikes, a NO
mapping onto PAM12, a compressed clock, an eligible-edge policy or a learning
rate. Continuous source activity and persistent four-state memory still need
an independently specified interface before any MaleCNS use. No source
protocol result, author-code reproduction, conditioning or qualified neural
learning is claimed by this preparation.
