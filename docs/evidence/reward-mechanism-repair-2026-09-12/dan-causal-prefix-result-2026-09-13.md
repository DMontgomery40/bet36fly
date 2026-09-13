# Teaching supplies a recorded DAN contrast; the learning rule is still unqualified

The completed offline audit `dan-causal-prefix-b3bbc7ad5a3c1040de18` finds a
DAN input difference in **all 64 matched comparisons** at the first teaching
pulse, step 1550 = 310 ms. The common-code proof and observed checks establish
the same KC spike history through that step. Missing teaching input is
therefore not the explanation for these current-code contrasts. This is
neither a new plasticity mechanism nor a passed learning experiment.

## Complete result

The audit covers both original diagnostic panels, eight cues per panel,
base/alternate noise and both home/away teaching conditions. Each comparison
uses its matched active-plasticity untaught history. All 113 bound input
files (917,311,069 bytes) were checked before and after execution. The parent
exited 0 after 4.067663 seconds. The child completion receipt records
3.963974 seconds after final input checks and summary persistence, within
the 120-second cap. All 64 row artifacts and completion/status/summary hashes pass root's
acceptance checks. [Frozen plan](dan-causal-prefix-b3bbc7ad5a3c1040de18-plan.json)
and [complete saved summary](dan-causal-prefix-b3bbc7ad5a3c1040de18-execution/result/summary.json).

| Recorded observation | Home teaching: 32 contrasts | Away teaching: 32 contrasts |
| --- | --- | --- |
| First pooled DAN difference | Step 1550 / 310 ms | Step 1550 / 310 ms |
| Untaught pooled counts at that step | [0, 0] | [0, 0] |
| Taught pooled counts at that step | [2, 0] | [0, 22] |
| First recorded rule difference | Step 1550 | Step 1550 |
| Total target-pool excess events | 8 in 31 contrasts; 7 in one | 88 in every contrast |
| Difference in the other pool | None at any step | None at any step |

Sixty-three difference vectors contain only the four requested pulse steps:
1550, 1650, 1750 and 1850. Home contrast 058 (second panel, cue 4420,
alternate noise) also has a one-event deficit at step 1556 / 311.2 ms,
giving a net excess of seven. This is event accounting, not an inferred
release or receptor mechanism. All vectors are preserved in the 64 NPZs,
with [descriptive inspection by cue](dan-causal-prefix-saved-output-inspection-2026-09-13.json).

The first-step target pool is saturated: both PPL101 cells, or all 22 PAM12
cells, fired, while none of those cells fired in the matched untaught step.
That individual-event inference follows from the verified binary event
contract and exact population counts. It does not reconstruct the complete
taught per-cell history. The home cells are bodies 11327 and 11900; the
away identities are preserved in the [cell atlas](../../../wiki/cells/identities.md).

Each artifact also retains all 4,064 KC body IDs and event counts through the
inclusive common prefix. Across the 32 histories, 490–1,446 KCs fired within
that prefix, with 1,299–5,548 total KC events. No individual KC exceeded 17
events. Total KC counts and grouped KC bridge inputs happen to remain equal
for the entire recorded trial. That aggregate observation does **not** extend
the established per-cell KC equality beyond step 1550. No hidden individual
DAN count difference occurs in the 31 whole bins before the pulse.

## The failed reader is preserved

The first identity, `dan-causal-prefix-cb7eb73ca0c41bd37e4b`, failed before
any contrast because the new reader expected int32 main sample indices;
the actual producer saves int64 indices. Its complete synthetic fixture
repeated the same wrong assumption, and the first reviews missed it. The
original code, tests, plan and failed result remain unchanged. The separate
[v2 correction](dan-causal-prefix-v2-reader-correction-2026-09-13.md) follows
the inspected producer and both real index arrays, with 33 additional
dtype/order/membership/range tests. All 223 helper/v2-driver tests pass.

## Consequence for the repair

The data provide an available input distinction at teaching, together with
substantial prior KC activity. They do not specify how PPL101 or PAM12 spikes
become local dopamine exposure or intracellular plasticity. The separate
[release-versus-priming source decision](dopamine-release-versus-priming-decision-2026-09-13.md)
does not calibrate a new law for these cells. A candidate still needs an
explicit source-grounded state/update contract and independent numerical
tests before both unchanged qualification panels and acquisition/reversal.

The old criterion-3 explanation also needs a precise correction. Identical
DAN input alone cannot prove that a difference in learning terms is a
wiring or index leak: those terms also depend on KC history and gain
feedback. The [independent causal contract](causal-prefix-identifiability-contract-delivered-arrivals-2026-09-13.md)
states the required joint conditions. The frozen historical specification
and its numeric gate are preserved; this corrects the interpretation only.

The production pair `b16d9b39d7fd3057` still fails the second panel's
untaught-home guard. Conditioning remains `not_run_gate_failed`. No neuronal
run, learning-rule replay, fit, parameter tuning, model promotion or push
occurred in this audit. Accepted gains, interfaces, all 4,184 eligible home
edges and the 3,239 gamma-only eligible away edges are unchanged; the 1,443
other away edges continue transmitting. Backend/frontend behavior is
unchanged and its existing display remains accurate. Fresh `make verify`
passed 4,055 Python tests, 103 frontend tests, Ruff and the build before the
audit; no new browser verification is claimed for this output/docs-only work.
