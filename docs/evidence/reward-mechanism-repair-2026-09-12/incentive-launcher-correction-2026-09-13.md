# Source-audit launcher correction

The first parent attempt, `incentive-handler-source-b7ce8a8ec24dab37ebe0`,
failed in 0.044392 seconds on September 13, 2026. Its child could not import
NumPy and exited before creating a source-result directory or evaluating any
of the six cases. The full failed receipt and stderr are preserved in the
adjacent `-execution` directory; all 26 bound input files are unchanged.

Root mistakenly resolved `.venv/bin/python` to the shared base interpreter.
That bypassed Python's virtual-environment discovery and its installed
packages. The repair retains the absolute **invocation path**, including its
symlink, and probes the child prefix/imports before dispatch. It changes no
source model, data, parameters, tolerances or scientific comparison.

The [launcher helper](source_audit_launch.py) has
[12 regression tests](test_source_audit_launch.py), including actual subprocess
imports through three repository aliases, spaces and literal shell characters,
relative paths and invalid environment configurations. All passed; Ruff passed.
This fixes the invocation-path family rather than special-casing one binary.

The next source calculation requires a new identity binding this correction,
the helper/tests and the failed parent receipt. It is a second launch attempt,
with zero source cases executed by the first. Do not overwrite the failed
identity or describe its startup as a scientific negative result. No source
fit, constant adjustment, saved-history evaluation or native call is involved.
