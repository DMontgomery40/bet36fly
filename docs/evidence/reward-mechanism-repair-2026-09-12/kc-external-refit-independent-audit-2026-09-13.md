# Independent fixed-parameter audit of the external calcium re-fit

September 13, 2026 UTC. **The saved parameters reproduce the pinned source
objective and all 259 fitted KD/WT samples.** No optimizer, restart, gradient,
MaleCNS history or native engine was invoked by this audit. Numerical
consistency and reported solver convergence do not establish biological
calibration or global optimality.

The audited run is `kc-external-refit-992cef6fb05bfdb63d2b`. Parent's execution
receipt records a reaped child, exit 0, 2.324875 seconds under the hard
120-second cap, with no restart. Both main solvers report success/status 0:
KD used 210 objective calls and 29 iterations; WT used 245 and 32. Stored
stdout includes one SciPy numerical-differencing invalid-subtract warning.
The final parameters, objectives and reproduced trajectories are finite;
this audit did not identify the particular trial that produced that warning.

I independently parsed all 499 numeric rows directly from the original XLSX
XML and compared them exactly with the inventory and saved NPZ. All 14
original source/license/workbook files and their 14 repository copies match
their SHA256 and Git blob identities. The seed-666 population, all 700 input
values, both time axes, stimulus and masks match the original source. The
37 consumed-file snapshots remained byte-identical through the audit.

## Frozen parameters and fit quality

| Parameter | KD value | Parameter | WT value |
| --- | ---: | --- | ---: |
| tauKCdec (s) | 0.568940389854 | tauinh (s) | 0.936979965071 |
| tauinp (source input divisor) | 0.174652128943 | inhfactor | 16.145628741933 |
| tauadapt (s) | 2.072004315465 | infp (activity units) | 1.274134896875 |
| adaptscale | 0.730826862420 | slf (activity units) | 0.165275064846 |

Baseline remains exactly zero. No parameter was changed by this audit.
The source's two post-offset initializers and their individual peak slices
match the recorded starts, lengths and averaged KD starting decay value.

Four calls to the unchanged pinned source functions supplied independent
full 700-unit trajectories and original scalar objectives at these parameters:

| Comparison | KD | WT |
| --- | ---: | ---: |
| SE-weighted squared residual sum | 156.623930615 | 1164.114888591 |
| Stage L1 penalty | 13.777856062 | 71.958042528 |
| Total source objective | 170.401786677 | 1236.072931119 |
| RMS residual in reported SE units | 0.777641049 | 2.120059452 |
| RMS residual in normalized activity units | 0.030544344 | 0.036887153 |
| Maximum absolute saved/source mean difference | 8.88e-16 | 4.44e-16 |
| Absolute saved/source objective difference | 2.84e-14 | 2.27e-13 |

The comparison preserves all 259 samples and observes the source-defined 140
active-input units, not the whole-population mean. KD's fixed baseline adds
zero to its penalty; WT penalizes only its four inhibition parameters.
All errors are within the preparation's fixed comparison allowances.

WT is not uniformly close to the supplied SE bars. Its largest standardized
residual is +17.65335 at source time 3.67 s; KD's largest absolute residual
is −2.76279 at 1.17 s, when its modeled activity is zero. These are retained
fit-quality observations, not grounds for a restart or parameter adjustment.
No chi-square interpretation is asserted for correlated, penalized
population-mean traces.

## Numerical admissibility and scope

Every parameter satisfies its calibration domain. For the separate selected
local-calcium contract, tauadapt and tauinh both exceed 1/30 s. On the audited
external trajectories, the minimum of `A=1-dt*(1+a)/tauKCdec` is
0.876947855506 for both branches; all states are nonnegative and WT obeys
`0 <= axon <= calyx` throughout. Thus these external inputs pass the declared
ordering conditions. This does not pre-certify future spike-driven inputs:
their every-frame A/state checks remain mandatory.

The complete [numeric audit](kc-external-refit-independent-audit-2026-09-13/audit.json)
binds all consumed files and the full
[259-sample comparison arrays](kc-external-refit-independent-audit-2026-09-13/comparison.npz).
The [audit script](audit_kc_external_refit.py) executes only the two hash-checked
upstream function modules; no fitting or plotting driver is imported.
Ruff passed. Root owns repository-wide verification and subsequent candidate
authorization. This report authorizes no retuning or successful-learning claim.
