# Fixed rate-adaptation numerical reference contract

2026-09-13 UTC. This is a numerical specification for the explicitly engineered hypothesis in the committed dopamine source report. It adds no physiology claim. Only synthetic numerical cases are authorized in this reference task; no saved-trial outcome, new circuit call, or parameter tuning.

## Fixed equations, state and publication

Let r=1/100, e=b=1/500, δ=r−e=0.008, p=r+e=0.012 and q=2e=0.004, all inverse milliseconds. Write k=R_K, u=E_K, d=R_D, B=adaptive DAN baseline, v=E_Dplus. Rates have spikes/ms and eligibilities spike units. Between events:

```
k' = −r k                 u' = k − e u
d' = −r d                 B' = e(d−B)
H = max(d−B,0)            v' = H − e v
P = v k                  N = u H
g' = c(P−N),              c = 0.0005 × 0.96
```

P and N are nonnegative product magnitudes. A signed negative-product record is −N. Both products use the same rectified signal and its causal eligibility. A KC event adds r to k. Actual simultaneous DAN events add r times their count divided by the unchanged selected channel population size to d. u, B and v do not jump. Aggregate same-time events before integration; do not sequentially apply learning at their shared timestamp.

Initialize all five states at electrical time zero. Evolve them throughout 0–400 ms; suppress gain writes before 100 ms. Process events at 0,0.2,…,399.8 ms, integrating each subsequent complete 0.2 ms interval. No event at 400 ms belongs to that capture. At 400 ms continue with zero new events through infinity. Only gains persist to another call; all five dynamic states and double remainders reset after final float32 checkpoint publication. Eligibility masks and gain bounds stay fixed.

Root explicitly confirmed the existing publication policy: **one double-accumulator clamp and float32 publication per complete electrical 0.2 ms interval, then one for the entire infinite tail**. Rectifier crossings split only mathematical integration. They are not extra gain updates. This is not continuously projected/clamped ODE gain evolution. Before/after double gain, attempted delta, applied double delta and float32 publication delta must remain distinct. Include exact-bound contact in existing publication-bound counts. Masked edges and learning-off gains remain byte-identical.

## Exact no-event interval and unique crossing

States below are immediately after any event at the interval start. For x≥0, define X=exp(−rx), Y=exp(−ex), Jδ(x)=−expm1(−δx)/δ. Then:

```
k(x) = k X
d(x) = d X
B(x) = Y [B + e d Jδ(x)]
u(x) = Y [u + k Jδ(x)]
A = r d / δ
C = B + e d / δ
d(x)−B(x) = A X − C Y
```

For valid nonnegative d and B, if d≤B the rectifier is inactive for the whole no-event interval. If d>B there is exactly one positive→zero crossing:

```
x* = log1p((d−B)/C) / δ
0 < x* ≤ log(r/e)/δ = log(5)/0.008
```

For d>B, C>0 automatically. Both zero is inactive without dividing. Exact d=B is inactive; no sign epsilon may erase a small positive signal. A finite segment has active length a=min(h,x*), then an inactive remainder. In exact arithmetic x* is at most approximately 201.18 ms. Crossing exactly at an endpoint belongs to the active integral ending there and adds no separate impulse or gain write.

On an active subsegment:

```
v(x) = Y [v + A Jδ(x) − C x]
```

On an inactive subsegment v(x)=vY. Evaluate nonnegative states stably. In particular v(x)=Y[v+(d−B)x+A(Jδ(x)−x)] avoids cancellation between A and C when d≈B, with Jδ(x)−x evaluated by a series beginning at order x². Do not silently floor negative states to hide an implementation error. At a computed crossing preserve the integrated v and all other states; H alone becomes zero.

## Exact positive/negative product areas

For an active duration a, define moments

```
F(λ,a)  = ∫0^a exp(−λx) dx = −expm1(−λa)/λ
M_n(λ,a)= ∫0^a x^n exp(−λx) dx
L(λ,δ,a)= ∫0^a exp(−λx) Jδ(x) dx
         = [F(λ,a)−F(λ+δ,a)]/δ
```

With Fp=F(p,a), Fq=F(q,a), Mp=M_1(p,a):

```
area_P = k v Fp + k A L(p,δ,a) − k C Mp
area_N = u A Fp − u C Fq
         + k A L(p,δ,a) − k C L(q,δ,a)
```

The signed area is area_P−area_N; multiply by c only afterward. An independent simplification is

```
Q(x)=P(x)−N(x)
    =(k v−A u−C k/δ−k C x) exp(−px)
      +(C u+C k/δ) exp(−qx).
```

This provides an algebraic check, not the sole numerical oracle. Inactive duration a has area_P=kvF(p,a), area_N=0, while all states still evolve.

For tiny a or d≈B, avoid differences of nearly equal F or L values. Put H0=d−B and J2(λ,δ,a)=∫0^a exp(−λx)Jδ(x)² dx. Stable equivalent areas are:

```
area_P = k v Fp + k H0 Mp + k A [L(p,δ,a)−Mp]
area_N = u H0 Fq + (k H0−u A δ)L(q,δ,a)
         − k A δ J2(q,δ,a)
```

The following convergent moment series give the relevant divided-difference limits without cancellation:

```
L(λ,δ,a) = Σ[n≥1] (−δ)^(n−1) M_n(λ,a)/n!
L−M_1    = the same series starting at n=2
J2       = Σ[n≥2] (−δ)^(n−2)(2^n−2) M_n(λ,a)/n!
M_n      = a^(n+1) Σ[j≥0] (−λa)^j/[j!(n+j+1)]
```

At δ→0, Jδ→a, L→M_1 and J2→M_2; at λ→0, M_n→a^(n+1)/(n+1), so F→a and M_1→a²/2. These are numerical divided-difference limits, not authorization to change the fixed taus. The equality b=e is intentional: the term −Cx exp(−ex) in v is the repeated-exponent solution and must not be evaluated by dividing by b−e. Tests must include this exact repeated-exponent case. Use bounded-error series or equivalent stable special functions, not arbitrary physiological cutoffs. The active interval is bounded, so exponential arguments needed in these active moment formulas are bounded independently of the full tail length.

## Complete infinite tail

If d≤B at the electrical endpoint, H remains zero forever and:

```
tail_P = k v / p
tail_N = 0.
```

If d>B, evaluate active areas through x*, evolve all five states to that crossing, then add k(x*)v(x*)/p to tail_P. tail_N has no further contribution. Integrate first, clamp/publish once for the total tail. Adding an arbitrary long zero-event window, dropping the remaining eligibility product, or reusing the old unrectified bridge tail changes the equation.

An independent Laplace-moment derivation uses M̂λ=∫0^∞ exp(−λs)H(s) ds. Swapping the nonnegative causal integrals gives

```
tail_P = k v/p + k M̂r/p
tail_N = u M̂e + k(M̂e−M̂r)/δ.
```

The reference oracle evaluates these moments with 70-digit numerical quadrature of H and a numerical sign-root bracket, not the finite-interval moment recurrence. A separate high-accuracy DOP853 solution of the five-state ODE and P/N accumulator equations checks finite segments. It detects the rectifier through max(d−B,0), without the analytic crossing formula. Numerical gain clipping is applied only after complete scheduled intervals/tail, never inside the ODE solver.

## No hidden-bound-excursion proof

For identical nonnegative spike histories and zero initialization, 0≤H≤R_D pointwise. The eligibility kernel is nonnegative, so 0≤E_Dplus≤E_Draw. Therefore Pplus≤Praw and Nplus≤Nraw pointwise, while the KC states are identical. For each eligible edge and any time after onset,

```
|unbounded g(t)−g(initial)|
  ≤ c ∫[onset,∞] (Pplus+Nplus)
  ≤ c ∫[onset,∞] (Praw+Nraw).
```

If the last, already-recorded same-history raw total is strictly below the distance from initial gain to each bound, no hidden continuous excursion can hit a bound. This is a conservative mathematical bound, not a fitted guard. It must be verified for every eligible edge using the correct history comparator and entire tail; an aggregate signed sum is insufficient. An unavailable/failed proof is not interpreted as no excursion. Existing inclusive publication observations remain separately reported. Synthetic clipping tests exercise the specified discrete publication policy even when this sufficient proof fails.

## Frozen tolerances and generalized cases

These values are fixed before any saved-history candidate result and before running the synthetic reference suite:

- State comparisons (rates, baseline, eligibility): `atol=2e-11`, `rtol=2e-10`.
- Unscaled positive/negative/signed integrated areas: `atol=2e-10`, `rtol=2e-10`.
- Gain delta comparisons: `atol=2e-12`, `rtol=2e-10` applied to the delta, not to the approximately unit gain.
- DOP853 oracle requests `rtol=2e-13`, `atol=2e-15`, with maximum step no larger than 0.5 ms and h/8 for finite segments. Its raw result must be finite and successful; no warning or failed solve counts as a pass.
- Tail quadrature uses 70 decimal digits. Synthetic repeated/near-crossing references additionally use 70-digit moment calculations where needed.
- Masked/learning-off gains and deterministic replay must match bytes. Float32 oracle publication should be exact unless the independent error interval actually straddles a rounding midpoint; only then permit at most one ULP and retain the midpoint/uncertainty evidence. This is not a blanket one-ULP allowance.

Cases must include zero states; DAN-only and KC-only; coincident and ordered pulses; exact/near-positive crossing and endpoint crossings; tiny/ordinary/long intervals; b=e repeated exponent; constant input from zero, upward/downward baseline steps and finite pulse offset; pre-onset events with suppressed writes but retained history; simultaneous population-normalized spikes; unequal channel sizes; masks and learning-off; end-at-399.8 versus forbidden 400 ms events; reset/checkpoint isolation; complete tails; lower/upper/equality/bounce clipping and subinterval cancellation; positive/negative area accounting; and the dominance/no-excursion inequality.

The new nonlinear rule need not preserve the old bridge's antisymmetry or zero net effect for isolated coincident KC/DAN impulses. Those are old-mode contracts, not assumptions to force onto this equation. Derive the candidate's coincident result from the independent oracle and retain it even if unfavorable. No synthetic or saved-history outcome is evidence of biological calibration or circuit qualification.

Appending zero-event electrical intervals before the remaining tail preserves unbounded integrated areas. It preserves bound-free final gains up to the fixed arithmetic tolerances. With clipping, changing a former single tail into multiple publication intervals may legitimately change the bounded result; no invariance test may silently replace the approved publication schedule or assert continuous projection equivalence.
