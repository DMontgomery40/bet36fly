# Published Handler-model reproduction and its limits

September 13, 2026 UTC. **All six authored source conditions reproduce under
the frozen numerical comparison. This is not a new BET36FLY learning rule or
a successful MaleCNS qualification.** The published model's plotted reporter
contrast and displayed nonnegative weight conceal distinct internal quantities.

The source is [Gkanias et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC8975552/),
with public code at `InsectRobotics/IncentiveCircuit` commit
`1610c80072fe8bb59bd397e7a61f716393a509b9`. The relevant helper and figure driver
are byte-identical at the paper's archived revision `98a8f85745a1426e8e5b787ceedd3f680a2b66c6`.
The six original source/license files, both archived copies and the complete
421,421-byte linked experimental workbook are retained with download receipts.
Mixed original license notices remain unchanged.

## The one completed source calculation

The [frozen v2 plan](incentive-handler-execution-plan-v2-2026-09-13.json) binds
35 files / 1,187,284 bytes. Identity
`incentive-handler-source-9c5800e30fdae747b49a` completed all six conditions in
0.375147 seconds under a 30-second external cap, exited zero and was reaped.
There were no source-case restarts, fits, native calls or saved BET36FLY
history evaluations. All input bindings remain unchanged.

The earlier launch `b7ce8a8ec24dab37ebe0` failed before any model case because
root resolved the virtual-environment Python symlink to the base interpreter,
which lacked NumPy. Its receipt/stderr remain preserved. The
[launcher correction](incentive-launcher-correction-2026-09-13.md) passed
12 actual subprocess/path regressions before the new identity. The model,
parameters and scientific comparisons were unchanged.

The authored grid has 1,001 samples from −7 to 8 seconds: 15 ms steps, not
the paper's stated 100 Hz. The source uses rectangular CS and US inputs of
0.5 and 0.6 seconds; it does not reconstruct the primary experiment's puff
and five-pulse induction waveforms. KC/short/long constants are `100/3,60,104`
samples. The helper retains first-sample semantics, previous-MBON feedback,
individual signal clipping, unbounded internal W and rectified recorded w.
No timestep multiplier or new gain bound was added.

| DAN minus KC onset, seconds | Final internal W | Final displayed w | Literal normalized reporter contrast |
| --- | ---: | ---: | ---: |
| −6 | 1.005381 | 1.005381 | 0.000000 |
| −1.2 | 1.664034 | 1.664034 | 0.161321 |
| −0.6 | 0.567270 | 0.567270 | −0.038343 |
| 0 | −32.485987 | 0 | −0.639624 |
| +0.5 | −9.799187 | 0 | −0.611870 |
| +6 | 0.999998 | 0.999998 | −0.173417 |

These columns are different observables. In particular, the last column is
a separately normalized, windowed reporter proxy; it is not the actual signed
weight change. The source keeps negative internal W while using rectified W
for MBON drive and plotted weights. The coincidence and +0.5 cases have 401
and 294 negative internal samples respectively. These are properties of the
inspected source calculation, not negative weights in our production circuit.

## Independent numerical and data checks

Before execution, 69 source-helper regressions and 78 independent analytic
transfer tests passed. Review caught and fixed a failure path that would have
discarded a mismatching case before saving its discrepancy arrays. The expanded
family now preserves failed observations/references/errors and a failed status.

The [saved-record audit](incentive-handler-independent-saved-audit-2026-09-13.json)
checks all 222 arrays / 222,222 finite double values, all 35 frozen inputs,
every saved local recurrence and all 72,072 source/scalar values. Summary
statistics reconcile exactly. The largest absolute source/scalar difference
is 1.62e-12 at a large-magnitude weight, within the frozen combined
`atol=1e-12, rtol=1e-12` comparison. The audit did not rerun source inductions.

Separately, the [workbook inventory](incentive-handler-workbook-independent-inventory-2026-09-13.json)
reads all four sheets / 35,418 cells and independently recalculates all 205
formulas. All 78 primary reporter means agree exactly with their timecourses.
The source's active ER averaging window differs from those primary means.
The model's +6 s cAMP window is also only partly recorded: its intended
four seconds extend to 10 s, while the source stops at 8 s. There are 134
retained model samples there, versus 267 in each other literal cAMP window.
No padded full-window observation or six-condition primary-window validation
is asserted. The separate [predeclared data-comparison specification](incentive-handler-source-protocol-specification-2026-09-13.md)
keeps those analyses distinct.

## Consequence for the repair

The [source/equation audit](incentive-dpr-equations-timing-audit-2026-09-13.md)
and [continuous-transfer analysis](incentive-dpr-continuous-transfer-boundary-2026-09-13.md)
identify why a direct transplant is not justified. Positive-spike equal-DC
filters lose DAN-only recovery over a full continuous tail, and their
source-pole linear-response order boundary exceeds our entire 400 ms trial.
The source also changes filtered dopamine through KC/MBON feedback, so equal
external US pulses do not isolate matched local dopamine exposure.

These checks establish a reproducible phenomenological source, not calibrated
DopR1/DopR2 states for PPL101/MBON11 or PAM12/MBON09. No new production rule,
kinetic constant, input scale or mask was selected. The existing failed
qualification pair, accepted electrical gains and model pointer remain in
place; acquisition/reversal and the full repair goal remain incomplete.
