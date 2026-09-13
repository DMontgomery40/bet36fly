# DARELA source and finite event-transfer checkpoint

September 13, 2026, following local `64a4b1d`. **The repair remains incomplete.**
This phase pins and checks a release-source lead and its explicitly engineered
finite event construction. No DARELA saved-history screen, native circuit
integration, qualification, acquisition or reversal has run.

## Exact scientific boundary

The [primary-source review](darela-primary-source-contract-dopamine-sources-2026-09-13.md)
and [parameter transcription](darela-published-parameter-transcription-dopamine-sources-2026-09-13.json)
distinguish the paper's mouse FSCV measurements, the pinned 2025 source
revision, and the finite event construction. The released SUR core uses
Euler `1+p` factors, rounded inclusive burst endpoints and a new-H release
factor. The shipped example is a separate parameter fixture. Neither that
code nor a successful numerical comparison supplies measured PPL101/PAM12
release kinetics.

The chosen manuscript WT sweep-1 factors are fixed at
`p=(0.0105,-0.003,-0.0011)` and `tau=(7.5,15,900)` seconds. Each actual DAN
spike emits the product of that cell's pre-event factors, then multiplies
them by `1+p`. Recovery between events is exact and each 400 ms trial starts
at H=1. All events, including those before 100 ms, advance H. The existing
bridge still begins cold at 100 ms; it receives per-cell masses averaged
over the fixed populations of two PPL101 or 22 PAM12. Its complete tail,
gains, masks, numerical publication and learning constants are unchanged.

These are engineering assumptions, not an exact rewrite of the source's
burst envelope. The [independent mathematics](darela-event-transfer-math-contract-delivered-arrivals-2026-09-13.md)
proves positivity and finite bounds over all 2,000 binary slots without a cap.
It also identifies indefinite tonic divergence outside this reset domain.
The construction does not model clearance or intracellular KC receptors.

## Numerical checks and retained failures

The event helper has 88 writer cases and 36 independent cases. The latter
use a separate 60-digit transformed-state calculation and geometric/finite
sum identities to check every state, event mass, pooled signal and endpoint.
The fixed comparison is `atol=rtol=1e-12`. Tests include maximal binary input,
irregular events, cell permutations, different cell histories with identical
pooled counts, pre-onset activity, reset and silence.

The separate release bridge adds 53 cases. It widens only the DAN input
envelope to finite `[0,2^32]`, retains KC inputs in `[0,1]`, and preserves the
entire prior calculation body and constants. Tests compare every old-domain
output byte, independent impulse integrals and complete tails, frozen and
excluded gains, inclusive bounds, and malformed inputs. Original helpers
and red/green logs remain intact; this is not a production change.

The literal eight-case source-kernel check completed once under identity
`darela-source-kernel-42b38e1924b4af6c82cf`. Its
[frozen plan](darela-source-kernel-preregistration-2026-09-13.md) preceded
execution. The child exited zero and was reaped, with 0.617201 seconds through
parent checks under the 30-second cap. All eight cases and 4,500 updates
completed; all 132 bound files remained unchanged. The largest source versus
scalar-reference error is 1.11e-14. These calls exercise only initialization,
stimulation and H kinetics, not the concentration solver, fitting or release
measurement. Old/new H products are derived quantities.
[Execution and reading receipt](darela-source-kernel-execution-reading-receipt-2026-09-13.json).

Root's separate [saved-array audit](darela-saved-kernel-root-review-2026-09-13.json)
checks all 80 arrays and 63,080 scalar values against piecewise geometric
solutions, with maximum absolute error 3.29e-14 under the same fixed combined
tolerance. It checks every input binding and terminal/row/archive identity
without rerunning the source. Exact masks confirm 31 inclusive driving
updates in each single burst. There are no failure markers or timeouts.

All 216 distinct synthetic cases pass from repository copies: 177 release,
independent-reference and bridge cases, plus 39 source-harness cases. The
latter include malformed/truncated/stale result artifacts, deadline expiry,
and external kill/reap controls. The
[177-case canonical run](darela-canonical-release-tests-receipt-2026-09-13.json)
and source preparation logs retain their respective scopes. The earlier
[import-only environment probe](darela-source-2026-09-13/import-only-environment-2026-09-13.json)
remains distinct from the subsequent source execution. Four isolated
dependency packages are under the original output source directory; the
repository environment and lockfile were not changed.

Fresh [repository verification](darela-make-verify-receipt-2026-09-13.json)
passed 4,055 Python tests, 103 frontend tests, Ruff and the Vite build, with
two existing Python warnings. Production/API/UI behavior is unchanged and
still accurately reports the failed qualification; no new browser run is
claimed for this source-only phase.

## Preservation and next execution

The [source-copy manifest](darela-source-preparation-copy-manifest-2026-09-13.json)
and [numerical-copy manifest](darela-numerical-preparation-copy-manifest-2026-09-13.json)
bind repository copies while retaining all originals and the upstream MIT
license. All 59 imported Microduck files still match the import manifest,
and all 59 originals remain present. Sixteen originals have different current
bytes; the preserved September 12 snapshot was not overwritten or mistaken
for a current upstream mirror. [Read-only preservation check](darela-microduck-preservation-2026-09-13.json).

The [post-verification protection check](darela-protected-after-verify-2026-09-13.json)
finds all 760 protected files unchanged and no inventory additions/removals,
including the active model pointer, data, historical runs and production code.

The numerical preparation gates pass. Next, preregister one 32-untaught-history screen under
the unchanged guards and a fresh identity. Preserve complete per-DAN release
and state evidence, exact selected body mappings, masked gain bytes and the
existing float32 publication policy. A pass is a necessary conditional
screen only; it does not establish the taught per-cell histories or recurrent
feedback of the changed mechanism. A failure rejects this fixed construction
without tuning the external row, onset, eta, bounds or thresholds.

The production pair `b16d9b39d7fd3057` still fails second-panel untaught-home,
and conditioning remains `not_run_gate_failed`. The full goal requires both
native qualification panels and controlled acquisition/reversal. The
[continuation handoff](../../REWARD_REPAIR_HANDOFF.md) owns the latest execution
state and next bounded step. Nothing has been pushed or promoted.
