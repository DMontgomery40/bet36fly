# Separate DA/NO memory states: verified numerical component

September 13, 2026. Starting checkpoint `bcefc77`; inspect Git for the local
commit containing this checkpoint. The full learning repair remains active.

The new [cell-specific account](../../../wiki/cells/cyclic-nucleotide-plasticity.md)
adds direct physiology at the home output type, MBON-γ1pedc. Yamada, Davidson
and Hige (2024) distinguish cAMP elevation from the KC-dependent downstream
process that produces presynaptic depression. Their minute-long induction
protocol does not supply a calibrated conversion from this simulator's
individual spikes to intracellular drive. The earlier attempts to transform
the input of the old antisymmetric rule did not implement that distinction.

The [source-selection review](intracellular-source-selection-dopamine-sources-2026-09-13.md)
identifies Aso et al. (2019), equations 1–3, as a complete, bounded first
component: latent DA/NO effects `d,n`, delayed expressed effects `D,N`, and
weight `(1-D)(1+N)`. The source concerns PPL1-γ1pedc. These are phenomenological
effect states, not measured chemical concentrations or receptor occupancies.
No equivalent PAM12 nitric-oxide assignment follows. The paper and its
transcript-analysis correction are copied with retrieval receipts; the
separate Doi/Purkinje model sources were retrieved but not executed or selected.

## What the implementation establishes

The [fixed contract](aso-da-no-component-contract-2026-09-13.md) and
[standalone helper](aso_da_no.py) retain the published rates and 30/600-second
expression times, with exact coupled evolution for each constant-input
interval. Source-null controls start with empty branches. Quiet time permits
expression to catch up with latent memory; it does not erase that memory.
Two states with equal current weight can therefore diverge later. This is
our equation reimplementation; no source-author code was identified or run.

Independent testing covered all input modes, the unit-cube boundaries,
nonzero initial states, split-interval composition, source-null branches,
acquisition and DAN-only recovery at the equation level, tiny and long
durations, and equal/near-equal rates. The frozen 70-digit closed form was
also checked against an independently arranged high-precision matrix
exponential. These synthetic checks are not a reproduction of source
behavioral data or a circuit experiment.

Two preparation failures and their corrections are retained:

- A double-precision SciPy matrix oracle disagreed near equal rates by up to
  `6.41e-8`. The helper agreed with independent high-precision calculations.
  The entire near-resonance oracle family was corrected without changing
  model parameters or tolerances. [Diagnosis](aso-da-no-near-resonance-oracle-diagnosis-2026-09-13.json).
- A valid near-one state could be rejected because rounded positive
  coefficients summed above one. Independent review found six failing rate
  pairs. A complementary evaluation near the upper boundary fixes this
  without clipping; broader corner/rate tests cover the family. The
  [initial component](aso-da-no-preparation-v1/preserved.json),
  [failing regression](aso-da-no-unit-cube-red-2026-09-13.txt), and
  [independent final review](aso-da-no-comparison-review-delivered-arrivals-2026-09-13.json)
  preserve that history.

## Verification and continuation

The final canonical suite passes **267 tests**: 197 writer cases, 32 frozen
reference cases, nine independent comparison cases, and 29 tests of the
existing qualification guard's interpretation. Explicit Ruff checks of all
six new Python files pass. [Canonical test output](aso-da-no-canonical-final-tests-2026-09-13.txt).
Fresh [make verify](aso-da-no-make-verify-2026-09-13.log) passes 4,055 Python
tests, 103 frontend tests, Ruff and the build, with two existing warnings.
The [protected-file check](aso-da-no-protected-2026-09-13.json) finds no byte
changes in the 760 baseline files, including the active model pointer and
historical evidence. It checks that baseline, not a new complete inventory.

Production/API/UI behavior remains unchanged; the failed qualification and
`not_run_gate_failed` display remain accurate. No new browser run is claimed.
All 4,184 home edges remain eligible; away still updates only 3,239 supported
gamma edges while 1,443 other edges transmit unchanged. The Microduck source
wiki and original research artifacts were retained.

The next bounded work is a source-protocol calculation with the paper's
actual activity durations, observation times and pathway-null controls.
Prespecify those conditions before execution, then compare the saved states
independently. No such calculation has run in this phase. A subsequent
MaleCNS candidate requires an explicit actual-spike input map, complete-state
persistence, compartment scope and finite observation semantics. Do not
compress the source's minutes into the existing 400 ms electrical trial or
borrow the old gain normalization, bounds or quiet tail without a new model
contract. The [integration review](intracellular-integration-boundary-evidence-ui-2026-09-13.md)
identifies the affected native/checkpoint surfaces.

The [guard review](qualification-meaning-delivered-arrivals-2026-09-13.md)
also distinguishes the frozen engineering criterion from a biological
neutrality theorem. Its threshold is unchanged. Both full native
qualification panels, then controlled acquisition and reversal, are still
required to complete the goal. Passing this component does not qualify the
learning mechanism. Keep rejected experiments closed; do not push or promote.
