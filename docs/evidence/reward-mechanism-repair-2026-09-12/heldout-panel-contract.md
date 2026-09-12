# Held-out diagnostic panel contract

**Original receipt superseded and unrun:** use the replacement identities and
[observation contract](inclusive-bound-observations.md) after independent review.
The source/seed selection below is unchanged.

Frozen September 12, 2026 UTC, before any held-out result. This tests the corrected
raw-event kernel with gamma-only away eligibility; the rate bridge remains
unimplemented. The original corrected panel's pass is separate evidence. This
held-out test must pass independently before conditioning proceeds.

The complete machine-readable [preregistration](heldout-preregistration.json)
contains all 64 expected panel rows, all 16 cumulative source/seed pairs, the
unchanged seven criteria, and exact code, frozen-input, manifest, protocol and
11 actual graph/annotation hashes. Its native source SHA256 is
`8e223c3326f0bb997750716644ac9ab929bea4980f5bb083cf4075e14a588080`.
It was created without building or running the circuit. No diagnostic output
folder exists for its prospective identity `diag-candidate-maskgamma-ee89fe032a62`.

Use calibration offsets 8 through 15 from the frozen historical pilot, with no
selection by response or outcome. All 16 original calibration IDs must be present,
unique and resolvable in the frozen source arrays even for a smaller debug run.
Base seeds are `42 + source_index + 2,000,000`; alternate seeds add 1,000,000.

| Source index | Base seed | Alternate seed |
| --- | --- | --- |
| 4395 | 2004437 | 3004437 |
| 4399 | 2004441 | 3004441 |
| 4404 | 2004446 | 3004446 |
| 4408 | 2004450 | 3004450 |
| 4412 | 2004454 | 3004454 |
| 4416 | 2004458 | 3004458 |
| 4420 | 2004462 | 3004462 |
| 4425 | 2004467 | 3004467 |

The cumulative sequence uses all 16 calibration sources in their original order,
with the same new base offset, not merely the eight held-out sources. The four
repeat checks use the first held-out source and its new base seed. Frozen,
untaught, home-taught and away-taught calls retain matching sensory seeds.

Completeness is computed from actual source/seed/condition rows plus the actual
16 cumulative rows. Missing, duplicate, unexpected or nonfinite evidence is an
error. Every cumulative gain vector must equal the running sum of its recorded
per-trial changes within absolute 1e-6, with no relative tolerance; this is an
arithmetic consistency check, not a scientific threshold. Debug panels may still
run with fewer requested rows, but all seven criteria and overall status remain
not passed. Nonnegative integer bound counts are required when present; negative,
fractional, boolean or nonfinite counts cannot cancel or evade the bound guard.

The full graph and annotation hashes must match the frozen pilot before circuit
construction and are checked again after execution, alongside code/native and
source snapshots. The selected inputs and graph hashes participate in the run
identity. Existing historical runs and preregistration receipts are not overwritten.
A changed receipt requires a newly identified preregistration before execution.

The independent native long-lag matrix uses production tau 500 ms and eta 0.0005,
unit events separated by 50, 100, 500 and 1000 ms in both orders, coincidence, and
DAN population sizes 1, 2 and 22. It verifies the analytic raw-pair effect
`-sign(lag) * eta * exp(-abs(lag)/tau)` to absolute 1e-7 and requires at least 99%
of the expected nonzero magnitude. It validates retained event semantics; it does
not establish biological timing or cue-specific acquisition.

After independent code review, the exact held-out invocation is:

```sh
.venv/bin/python scripts/reward_teaching_diagnostic.py --rule candidate --away-mask gamma --panel-kind held-out --panel-offset 8 --seed-offset 2000000 --games 8 --cumulative-games 16 --preregistration docs/evidence/reward-mechanism-repair-2026-09-12/heldout-preregistration.json --evidence docs/evidence/reward-mechanism-repair-2026-09-12
```

This command has **not** been run. Only the same selector arguments with
`--preregister-only` were executed to freeze the receipt. No browser server, live
sports refresh, conditioning run, commit or promotion is part of this harness task.

Pre-execution review caveat: the current native counters count strict overshoots,
not exact equality followed by recovery. They cannot establish the absence of
every transient bound hit. Root is assessing an instrument-only inclusive-bound
follow-up before running this held-out identity; any changed native fingerprint
requires a new original/held-out pair, preserving this preregistration unrun.
