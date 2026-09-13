# Literal DARELA factor-kernel check, frozen before execution

This check concerns the unmodified factor kernel at DARELA commit
`125c27bc59b0c493c902c8724f58fa3d9d8b354d` (February 15, 2025).
It is a later repository revision, not an identified publication revision.
The machine contract binds all 12 pinned files, source metadata, this plan,
the driver, its synthetic tests, the published parameter transcription and
the root agent's import-only environment receipt. No authored source case
has run when this plan is frozen.

Run exactly eight cases in the declared order: manuscript WT sweep-1 and
the shipped example's tau row, each with quiet, single, repeated and
nonunit-initial-state conditions. Both rows use dimensionless
`p=(0.0105,-0.003,-0.0011)`; tau in seconds is `(7.5,15,900)` for WT1 and
`(7.5,12.5,900)` for the example. This is a factor-only comparison of those
rows; no complete concentration parameter set is implied. Frequency is
50 Hz, nominal NP is 30, and initialization current is 0.4 mA. The latter
is unused by the factor kernel.

Quiet, single and nonunit cases end at 5 seconds. Repeated cases end at
30 seconds. Single and nonunit bursts begin at 0.34 seconds; repeated
bursts begin at 0.34, 5.34, 10.34, 15.34, 20.34 and 25.34 seconds. All H
states start at one except the explicitly synthetic nonunit vector
`(1.25,0.75,0.5)`. It tests state handling, not a measured mouse state.

Only SUR construction/initialize, `_set_stimulation`, `_set_kinetics`
and `_solve_kinetics` may execute. The constructor creates a FitEngine
object, but no fit method runs. The wrapper supplies the inspected
`p1..p3/tau1..tau3` parameter dictionary and calls the unchanged kernel.
No `solve`, `solve_kinetics`, concentration, uptake, electrode, PDE,
example GUI, experimental fit or neural history evaluation is permitted.

The independent reference constructs the 20 ms grid with Decimal
arithmetic and decimal half-even rounding of both inclusive burst
arguments to 0.01 seconds. It then applies a scalar Euler recurrence,
`h_next = h*(1+p*S) + 0.02*(1-S)*(1-h)/tau`, component by component.
The fixed integral-grid cases avoid claiming agreement for arbitrary
off-grid endpoints or binary/decimal rounding ties. Source and reference
time, S, all H and derived old/new H products must be finite and agree at
every sample using the fixed combined criterion
`abs(source-reference) <= 1e-12 + 1e-12*abs(reference)`.
S must additionally match exactly; H must remain strictly positive.
There is no fit, scientific acceptance threshold or outcome-dependent
tolerance change.

Expected driving update counts are 0, 31, 186 and 31 per row. The
single burst's source S is positive at indices 17 through 47 inclusive;
state 18 is the first changed H. These eight cases require exactly 4,500
kernel updates and retain 4,508 H rows. Each case saves source/reference
time, S, H and products `A_old=prod(H[:-1])`, `A_new=prod(H[1:])`.
Both products are **derived from saved factors**, not observed
concentration or executed full-solver release. The source's use of new H
in release remains a separately inspected code fact. The quiet rested
product is one; the first active rested old product is one and the new
product is `prod(1+p)`. Complete finite source windows include their
post-burst recovery; no infinite-tail or chronic-tonic claim follows.

Use the repository `.venv/bin/python` invocation without resolving its
symlink, and the already installed isolated dependency directory.
The root's first import-only probe took 0.483363 seconds and used Python
3.12.9, NumPy 2.5.3, SciPy 1.18.1, autograd 1.9.1,
alive-progress 3.3.0, about-time 4.2.2 and graphemeu 0.10.0.
That probe performed zero construction/kernel/solve/fit calls. This
study does not install or access the network. Disable bytecode writes.

After parent review, permit one execution in a new identity directory.
An external parent kills and reaps the child at the remaining 30-second
total cap. The child has an additional 28-second limit. These limits
include persistence and final hash checks; a late overrun is recorded
as a failure even if a completion file was already written. Never resume
or repeat an identity. Preserve all produced arrays and failures.

Validate all bound files before and after. A complete result requires a
hash-bound summary, eight correctly ordered case identities and saved
array/row pairs, exact attempted/completed counts, successful comparisons,
and successful child exit/reaping. The child's `completion.json` and the
parent's `execution.json` are invalidated by any corresponding
`terminal-error.json`. Truncated, missing, stale, changed or failed
artifacts cannot establish completion. A source comparison pass establishes
only this source numerical contract. It does not validate the separate
every-spike fly embedding or repair the currently failed learning gate.
