# External noiseless KC calcium calibration: prepared source-objective re-fit

September 13, 2026 UTC, checkpoint `b86405d`. The helper is prepared and
synthetically tested; **this preparation performed no numerical fit**. Parent
owns one separately frozen execution with a hard 120-second process watchdog.
No MaleCNS data, saved spike history or conditioning outcome enters calibration.

Use [kc_external_calibration.py](kc_external_calibration.py), with
[81 tests](test_kc_external_calibration.py). This is a direct physical-coordinate
SciPy L-BFGS-B **re-fit of the source objective**, not an identical lmfit
optimizer reproduction. Upstream pins lmfit 1.3.2, SciPy 1.6.2 and NumPy 1.24.4;
the available environment has Python 3.12.9, SciPy 1.18.1 and NumPy 2.5.3,
with lmfit absent. No package was installed or fetched.

## Fixed data and model contract

The pinned upstream commit is `f0ee2079dae6761cc2d07f04e96e76e2654b6e3c`.
Its complete tree contains no fitted parameter NPZ or numerical fit report.
The README states that fitting generates the parameters required by later
scripts. Source defaults are optimizer starting values, not published fitted
estimates. The compiled bytecode files in the tree are not parameter artifacts.

The helper reads the complete existing workbook inventory: two header rows,
then 499 rows of WT mean, WT SE, KD mean, KD SE. Both SE columns must be
strictly positive; all 1,996 cells must be finite numbers. The original XLSX
SHA256 is `f92ab807009e2e8160fbc8c6c100731012052843484de6c796c7faf673712a1d`;
the inventory SHA256 is
`af1109cad767745802ff4fae62088e4c49e9eb05b5c9d68f013c2c7aa968f166`.
Both files are size/hash checked before use and again before completion.
No XLSX parser or new dependency is needed for execution.

Retain the source's seed 666 RNG call order and 700-unit population: 35
reliable inputs uniform on [0.5,1), 105 other active inputs on [0,0.5), and
560 zero inputs. The residual observes the mean of the 140 active-input
units. The exact little-endian float64 input-vector SHA256 is
`98b15e2996a31e8dd69a38d2d6ac163a7657f3b914abdafe77c9c5c2e5b7e5a4`.

The observed time axis is `arange(0,499/30,1/30)`. Reproduce the source's
separate two-decimal rounded stimulus axis, inclusive 3.6–8.6 s odor step,
and endpoint removal. The main fit uses `source_time <= 8.6`, exactly 259
rows. The decay initialization instead uses `observed_time >= 8.6`.
These two axes and masks are retained in the output.

The noiseless old-state recurrence and source nonnegative calcium clipping
are preserved. WT lateral input is the uniform, zero-diagonal source matrix:
`factor * (sum(axon) - axon)/(N-1)`. This O(N) evaluation is independently
tested against the actual dense-matrix source functions. The sigmoid
multiplies the entire newly computed inhibitory state; old inhibition is
used in the calcium update. No clock change, noise, OE fit, MBON tuning,
learning driver or gain rule is included.

## Three sequential optimization stages

1. **Post-offset initialization.** For KD, then WT, select the post-offset
   segment. Locate that segment's own maximum; fit from its maximum onward,
   resetting time to zero at that maximum. Fit `a exp(-t/tau) + c` with
   initial `(tau,a,c)=(1.5,first_selected_value,0)` and nonnegative bounds.
   This stage is unweighted, as in the source. Use SciPy `curve_fit`, TRF,
   and preserve its convergence flag. Set the KD starting decay parameter
   to the mean of the two fitted tau values. The two fits share one 3,000
   actual function-call budget.
2. **KD.** Optimize `(tauKCdec,tauinp,tauadapt,adaptscale)`, starting at
   `(mean_decay_tau,0.2,2,1)`, with bounds `[0,infinity)` for each. Baseline
   remains fixed at zero. The objective is
   `sum(((active_mean - KD_mean)/KD_SE)^2) + 3.885*sum(abs(KD_parameters))`
   over the 259 fit rows. The source also includes fixed baseline in its
   penalty; it contributes exactly zero here.
3. **WT.** Freeze the first converged KD vector. Optimize
   `(tauinh,inhfactor,infp,slf)`, starting at `(1.5,15,0.5,0.03)`, with lower
   bounds `(0,0,1e-5,1e-5)` and no upper bounds. Use the same SE-scaled
   objective against WT, penalizing only these four WT parameters. The
   frozen KD parameters are not penalized again.

For KD and WT, the helper passes `method='L-BFGS-B'`, direct physical bounds,
`maxfun=3000`, `maxiter=500`, `ftol=2.220446049250313e-9`, `gtol=1e-5`,
`eps=1e-8`, `maxls=20`; other behavior follows the pinned local SciPy version.
Zero divisors or nonfinite parameter/trajectory evaluations return an invalid
infinite objective. They are not replaced by a hidden positive parameter
floor. Input schema errors remain errors. No alternative starts, restarts,
parameter selection among fits, or post-outcome tolerance changes are planned.

This preserves the source forward equations, objective, population, stages
and starting values within the tested floating-point allowance. Direct
physical-coordinate bounds, current libraries and explicit budgets can
produce a different optimizer path or optimum from lmfit. Matching the
original optimizer would require a separate pinned-lmfit reproduction.

## Execution boundary and independent acceptance

Parent freezes helper/test/workbook/inventory hashes and settings before
dispatch. The CLI is:

```text
.venv/bin/python output/collaboration/reward-mechanism-repair/kc_external_calibration.py \
  --output <new-exclusive-directory> --maxfun 3000 --maxiter 500
```

Set the parent's BLAS thread limits before interpreter startup and apply the
external subprocess timeout of 120 seconds. The internal timer covers input
preparation through final persistence. Actual objective/model-function calls,
including numerical derivative probes, are counted; solver-reported `nfev`
alone is insufficient. Status and stage progress are atomically persisted,
with a flushed event journal. A limit, failed solver or invalid result stops
the sequence and preserves partial evidence. A killed process's last running
status must be labeled interrupted by the parent, never interpreted as success.

After one run, the independent acceptance checks should:

- Verify every frozen identity, exact 700-unit input vector and both time
  masks; verify no source or workbook bytes changed.
- Preserve the two decay-fit flags and KD/WT status, objective-call counts,
  iterations and wall time. Require converged finite KD and WT results
  within the declared bounds and process cap. An incomplete fit supplies
  no accepted parameter vector and triggers no automatic restart.
- At the returned vectors, recompute all 259 KD and WT mean samples and
  both scalar objectives using the unchanged upstream functions. Compare
  with the helper using `rtol=2e-12, atol=2e-13` for state/mean trajectories
  and `rtol=2e-12, atol=2e-12` for scalar objectives, as preregistered in the
  synthetic suite. Do not refit to remove a discrepancy.
- Verify SE division occurs before squaring, the active-unit mean excludes
  zero-input units, WT uses the returned KD vector, and the penalty includes
  only that stage's parameters. Preserve the fit residuals and parameters
  without a claim that optimizer convergence establishes biological validity.

Final preparation tests passed **81 cases in 0.55 s**; Ruff passed. These
include actual source-function equivalence, schedule/population identities,
objective/penalty checks, input corruption/domain matrices and synthetic
stage success/failure. Workflow tests replace optimizers and use synthetic
rows; none invokes an optimizer on the real workbook. A concrete NaN/±Inf
progress-serialization failure was first reproduced, then fixed with the
three-case regression family. All 14 upstream files remain hash-exact.

Primary SciPy documentation was independently checked by parent on September
13: [L-BFGS-B](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html)
and [curve_fit](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html).
This agent inspected the local signatures/documentation and source files;
it made no network request. Parent owns repository-wide verification.
