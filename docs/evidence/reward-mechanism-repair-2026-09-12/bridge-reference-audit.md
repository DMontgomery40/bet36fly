# Independent numerical audit of the frozen rate bridge

September 12, 2026 UTC, before bridge circuit measurements. This is a reference-only arithmetic audit. It imports no production module, native kernel, neural circuit or diagnostic runner. The script and results are [bridge-reference-audit.py](bridge-reference-audit.py) and [bridge-reference-audit.json](bridge-reference-audit.json). Script SHA256 recorded in the result: `ec734469c2f6b3814e514a16903097b1198d8c3c65b70d6b9d71e904a357d2e4`.

Ran `.venv/bin/python output/collaboration/reward-mechanism-repair/bridge-reference-audit.py`: **28 checks passed** in the fixed production arithmetic and explicitly identified clipping stress fixture. No candidate circuit result exists in this audit. Failures in generic numeric-domain probes are retained and described below, rather than hidden in the passing fixed-configuration total.

Read the updated evidence index, complete recording-parity receipt and implementation-freeze receipt. The frozen implementation-contract copy is byte-identical to the full document authored/read earlier, hash `c35484a6a6f1a1405d79ec7673810887edd5744373e7519f0d35358f0588a71e`. The parent preregistration hash remains `ab7c640f3bfbc74845ff2759421b8b2de91d6411b9a6685acd3a62d1147508e3`. Neither frozen document was edited.

## Independent methods and assumptions

The reference reconstructs R and E directly from all past impulses at each requested time. For an impulse of amplitude a and age s, R=a*exp(−s/tau_r)/tau_r and E=a*exp(−s/tau_e)*(1−exp(−(1/tau_r−1/tau_e)*s))/(tau_r*(1/tau_r−1/tau_e)). `expm1` evaluates the exponential difference. This is a closed event-history convolution, not another copy of the native step recurrence.

SciPy quadrature independently integrates the positive E_D*R_K and negative −E_K*R_D products. Integration intervals are explicitly divided at all impulse times. Infinite upper limits test the complete no-new-event continuation. A separate all-KC/DAN-pair sum uses the closed timing kernel −sign(lag)*eta*(exp(−abs(lag)/500)−exp(−abs(lag)/100)); amplitudes multiply. Clipping fixtures integrate the closed-history derivative between every event, then compare event-only and dense subdivisions. The sole clipping fixture uses eta=1 and bounds [.9,1.1] to exercise sign changes and bounds; these are arithmetic stress inputs, not candidate parameter choices or a circuit protocol.

All biological/model attribution remains that of the existing source report. This audit checks the mathematics of the engineered impulse-filter model. It makes no new receptor, dopamine-clearance or biological conditioning claim.

## Results

- True separate interval/tail areas agree with independent quadrature; largest checked area discrepancy is approximately 1.08e−19. The shared cross term must be included in each separate area even though it cancels from the net. For a coincident unit pair integrated forever, the positive and negative contributions are +0.0002 and −0.0002, while net learning is exactly zero. Omitting the common terms would report those real contributions as absent.
- Finite mixed histories, partial DAN population amplitudes and isolated pairs at signed lags .2,1,5,20,50,100,500,1000 ms agree with the independent all-pairs kernel. Largest checked history discrepancy is approximately 3.96e−18; quadrature error estimates are separately retained.
- The clipping fixture encounters low, high, low and high bound segments as the derivative reverses after successive events. Dense 2 ms subdivision and event-only integration end at the same 1.1 bound. This supports monotone event-free segment integration with explicit clipping; it does not justify using unclipped pair superposition after clipping.
- The 0.2 ms unit-pair effect should be −7.990406610006717e−7. Double accumulation gives −7.990406603042288e−7 and final float32 publication gives −7.748603820800781e−7, exactly the expected rounded checkpoint. Reinitializing from float32 after every interval gives **zero**. Of 1,999 nonzero intervals, 1,986 have zero immediate float publication; their double residuals must accumulate. The analytic tail contributes −6.59170364172932e−9 and remains separately visible.

The stable net should be computed directly as eta*n*A*Q. The positive and negative recorded areas are verification/decomposition fields; subtracting two large recorded terms must not become the gain decision when the direct Q expression is available. Final float rounding differs from integrated double change and must not be mistaken for an altered learning equation.

## Numeric-domain failures and minimal validation

The frozen production values h=.2, tau_e=500, tau_r=100, eta=.0005, n=.96 are well behaved. Literal double C coefficient subtraction at those values differs from a 90-digit mpmath reference by approximately 1.45e−13 relative. The following finite scalar inputs demonstrate why a general engine cannot validate only positivity and finiteness:

| Probe, tau_e=500 | Observed arithmetic problem |
| --- | --- |
| tau_r=499.999999 | Literal shared-area coefficient has approximately 8.09e−5 relative error from cancellation. |
| tau_r=nextafter(500,0)=499.99999999999994 | tau_r<tau_e is true, but rounded reciprocal difference is zero; literal formula divides by zero. |
| tau_r=1e−300 | Reciprocal is finite, but C underflows to zero; its true value is approximately 5e−601, while rate products can overflow before cancellation. |
| tau_r=1e−320 | Reciprocal is infinite despite a finite positive timescale; subsequent coefficient/product arithmetic is unsupported. |

For this fixed candidate, explicit rejection of unsupported near-equal/extreme inputs is preferable to quietly replacing timescales. Require finite positive derived reciprocals, normalization, interval/tail integrals and eligibility-coupling coefficients; reject numerically indistinguishable reciprocal gaps and zero-invalid coefficients. A documented relative reciprocal-gap floor, such as the kernel worker's proposed 1e−6, is a supported-domain validation restriction, not a selected physiology parameter. Test values on both sides of the chosen supported boundary. Production 100/500 must remain unchanged.

Also guard true-area products, not merely their factors. With at most one event per cell/compartment-mean per step, a conservative post-injection rate bound is Rmax=(1/tau_r)/[−expm1(−h/tau_r)]. Eligibility can be conservatively bounded by min(tau_e,maximum_trial_duration)*Rmax. Ensure the resulting rate-rate and rate-eligibility products and their configured scaled areas remain finite. Alternatively impose a clearly documented supported numeric range that guarantees those conditions. Ineligible or zero-eta paths must not evaluate `0*infinity` and emit NaN.

If broad near-equal support is later desired, implement and independently test the divided-difference limit. As r→e, eligibility coupling becomes h*exp(−e*h), and C becomes the integral from 0 to h of s*exp(−2*r*s), equal to [1−(1+2*r*h)*exp(−2*r*h)]/(4*r²), evaluated with a small-argument series/stable function. This limit is not required to alter the fixed candidate, and blindly evaluating that final subtraction would introduce another cancellation problem. A permissive validator without stable math is unacceptable.

## Exact short-lag falsifier, clarified before measurements

Use the numerical isolated-pair kernel test only for the preregistered short-ordering discount. For both signs of lag l=5 and 20 ms, require:

`abs(bridge_delta(l))/abs(bridge_delta(500)) < abs(raw_delta(l))/abs(raw_delta(500)) = exp((500−abs(l))/500)`.

The fixed analytic ratios are approximately 0.1074936275 versus raw 2.6912344723 at 5 ms, and 0.3933601881 versus raw 2.6116964734 at 20 ms. Retain the already declared floors: the 50 ms effect must be at least 25% of raw and the 500 ms effect at least 95% of raw. Their analytic fractions are approximately .329679954 and .981684361. Native tests must satisfy the oracle and these comparisons; reporting the formula alone does not verify implementation.

No additional observational train-shift metric is intended. There will be no post-result choice of a shift, event deletion, wrapping, onset adjustment or secondary numerical threshold. The unchanged original and previously frozen diagnostic panels separately determine whether the bridge repairs measured untaught drift. Passing the isolated-pair ratio is not an operational drift result or causal neural rerun.

## Review boundary

This audit gives the independent reviewer an executable reference and identifies concrete invalid numeric domains before candidate measurement. It has not inspected the final new kernel or certified its tests. The kernel worker is implementing/testing separately. Production gains, accepted channels/masks, neural timestep, normalization and all scientific gate thresholds remain fixed; conditioning stays held pending the operational gates.
