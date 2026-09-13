# Pinned KC lateral-interaction model: source-semantic audit

September 13, 2026 UTC. This is a bounded synthetic audit before any paper fit,
MaleCNS candidate, recorded-history evaluation or changed physiology. Root read
the complete core functions, fitting functions and calibration driver; an
independent agent checked the recurrence algebra without running the code.

The primary article is Manoim Wolkovitz, Tunc et al., Current Biology 2026,
DOI [10.1016/j.cub.2026.01.014](https://doi.org/10.1016/j.cub.2026.01.014).
Its linked public implementation is pinned to
`nawrotlab/KC_KC_lateral_interactions@f0ee2079dae6761cc2d07f04e96e76e2654b6e3c`.
All fourteen selected source/license/calibration files match the public Git
blob identities. Original files remain intact under `kc-lateral-primary-source-2026-09-13`.
No fitting or plotting driver is imported or run. The test executes only the
personally inspected definitions in the two hash-checked function modules.

For fixed neighboring calcium drive `L`, modulation `f`, step `dt` and `tau`,
the actual source recurrence is

```
h_next = f * ((1 - dt/tau) * h + (dt/tau) * L)
h_equilibrium = f * (dt/tau) * L / (1 - f + f*dt/tau)
```

The second expression follows independently from the fixed-point equation.
For fixed `0 < f < 1`, its limit as `dt` approaches zero is zero. The `f=1`
case instead has equilibrium `L`. These are discrete-source semantics; they
do not prove that the published fixed-step model is invalid. Importing its
fitted multiplier unchanged as a timestep-independent continuous receptor
law would be a transfer error. The source fits at `dt=1/30 s`; our electrical
kernel advances at `0.0002 s`.

The test matrix covers both steps, several decay times and modulation values,
the exact finite geometric sum, stationary states, the actual two-step WT
loop, sigmoid direction, and the separate no-shock behavior. The core DAN
function gates new drive with `shock > 0`; cold no-shock dopamine therefore
stays zero even for a nonzero modeled prediction error. Previously evoked
dopamine can decay after shock and still depress weights. These two cases
must not be conflated. The source plasticity function is purely depressive.

No test invokes the full CNS, sports data, native engine, old 32 histories,
network, fitting driver or a generated biological candidate. Synthetic
values are mathematical probes, not fitted physiology. Passing this audit
does not establish learning, justify the shock gate, remove home eligibility,
or authorize a replacement of accepted drive gains or teaching interfaces.

The source download finished all files but exceeded its requested 120-second
bound (recorded 225.688 seconds); its original completion receipt and a
separate budget review preserve that exception. The process is terminal.
There are no retries or outstanding downloads. That acquisition exception
is distinct from the prospective synthetic audit.
