# Independent saved Handler source/workbook comparison

September 13, 2026. This analysis was specified before this reviewer opened
the six saved case arrays. Root later communicated selected source results
while the reader was being prepared. Those values do not select windows,
normalization, parameters, tests or an acceptance threshold. No source model
is imported or rerun, no fit is performed, and no BET36FLY history is read.

The source target is the already completed six-case authored-source protocol,
with ISIs `[-6,-1.2,-0.6,0,0.5,6]`, its fixed 15 ms grid from -7 to 8 s and
driver constants 100/3, 60 and 104 samples. Root must dispatch the exact run
directory and expected identity SHA256 after reviewing this reader. The
first zero-case parent-launch failure remains separate evidence; this reader
does not retry it or reinterpret its status.

The analysis independently reads all six saved arrays, verifies their hashes,
canonical order, schemas, finite values, exact source clock and stimulus masks,
complete status, elapsed time under 30 s, summary hash, original source hashes
and helper/test/plan bindings. A terminal error invalidates the input. It then
recomputes the saved reporter summary at absolute tolerance 1e-12, relative
tolerance zero. This is a saved-array and interpretation audit, not another
independent state recurrence; the source runner owns that comparison.

Two model measurement conventions remain separate:

- **Literal driver:** mean `-dR1` on `[-7,1)` and `dR2` on
  `[ISI,ISI+4)`, using only actual saved samples. Normalize each branch across
  all six condition means and subtract normalized cAMP from normalized ER.
  The +6 s cAMP selection is a literal partial 6–8 s window, explicitly marked
  incomplete against its requested 6–10 s interval.
- **Primary windows:** actual samples in closed `[0,1]` for `-dR1` and
  `[ISI,ISI+4]` for `dR2`. No interpolation, endpoint invention, missing-data
  padding or extrapolation. +6 s cAMP is incomplete, so the six-condition
  primary-model normalized contrast and correlation are **not computed**.
  For the other five conditions report raw model and experimental branch
  means side by side, with no five-condition renormalization or unit-equivalence
  claim. The partial +6 mean and its coverage remain in the complete six-row
  report rather than being dropped.

The hash-pinned 421,421-byte workbook is independently parsed using bundled
openpyxl, without executing formulas. Primary cAMP means use the 41 closed
samples in raw `[10+ISI,14+ISI]`; ER uses the 11 in raw `[6,7]`. The 78 means
are checked against their cached row-2 values at absolute 1e-14, relative zero.
This independent per-column summation differs from the prior axis-wise
summation by at most 5.56e-17 on static data. The literal experimental ER
selection separately retains the 71 available samples from raw `[-1,7]`.

Normalize each preparation across its six conditions, then average; ER is
negated first. Record ranges and the sample-SD/sqrt(n) SEM. Preserve both the
full-precision reconstruction and the final sheet's rounded primitives;
check its cached contrast at absolute 1e-12. Do not pair preparations across
the six-preparation cAMP and seven-preparation ER experiments. The separate
MBON sheet retains all 31 measured pre/post differences and its six means.

Report descriptive Pearson correlations of the **literal** model contrast
with (a) the literal-driver experimental reporter contrast, (b) the primary
rounded-sheet reporter contrast and (c) the direct MBON condition means.
These are labeled different observables and analyses. An undefined correlation
is null. No correlation threshold qualifies success; the authors used these
conditions when selecting their model timing constants. No statistical
significance, held-out validation or receptor kinetic calibration is inferred.

Retain final internal weight, rectified recorded weight, signed increment sum
and reporter-proxy sum separately. The driver's DopR1/2 explanatory labels are
reversed relative to the Handler biological associations; array names remain
unchanged. Proxy contrast is not signed synaptic change. Gamma4 data and this
500/600 ms source protocol do not establish a transfer to the fixed 400 ms
MaleCNS home/away experiment.

Execution is one read-only analysis under a 30 s process wall cap, including
imports and persistence, in a new exclusive output directory. Write started,
analysis and hash-bound completion receipts; any exception, timeout or input
mutation writes a terminal error, which invalidates completion. Rehash all
inputs before completion; no retries or resume. Use the bundled Python path
whose NumPy and openpyxl imports were already verified, without installing
dependencies. Root may supervise the process with a separate watchdog.

Generalized synthetic tests cover closed/half-open and incomplete/empty
windows, ordering and duplicate conditions, per-preparation normalization,
zero ranges, nonfinite inputs, input mutations, invalid terminal status,
summary shape/value errors and exact workbook selections. They execute no
model. Root owns whole-repository verification and subsequent interpretation.
