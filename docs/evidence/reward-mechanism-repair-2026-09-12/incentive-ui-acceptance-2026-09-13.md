# Dopamine reference labels and source-audit checkpoint

September 13, 2026 UTC. **The display correction and its browser workflow
pass. The learning qualification still fails.** The new source-model
reproduction supplies no acquisition or reversal result.

The Training view previously described a cue-period DAN measurement as tonic
activity and described evoked spikes without identifying the matched unpulsed
probe. It now labels a reference as cue-window only when its recorded timing
lies inside the recorded stimulus. Missing timing gets a neutral DAN reference
label; missing mode is explicitly unavailable. Historical baseline-subtracted
modes retain their distinct explanation. Evoked counts are described as the
taught-minus-unpulsed count from the teaching bin onward, using the same cue
and seed. Stored experiment messages and numeric records remain verbatim.

The API contract and frontend types document existing optional schema and
stimulus fields. No backend transport, neural rule, gain, mask or experiment
identity changed. Eighteen additional rendering cases cover the cross-product
of modes and gate outcomes plus timing-window boundaries and missing fields.
The focused RewardExperiments suite passed all 34 cases.

## Verification

Fresh [make verify output](incentive-ui-make-verify-2026-09-13.txt) records
4,055 Python tests passing in 272.17 seconds, Ruff passing, all 103 frontend
tests passing, and TypeScript/Vite building successfully. The two Python
deprecation warnings are retained in the log. No production edits followed.

The [actual browser receipt](incentive-ui-browser-2026-09-13/bet36fly-reward-browser-evidence.json)
records the rebuilt app against the marked read-only verification factory.
Port 8765 was occupied by an unrelated server, so QA used the same
`bet36fly.server:create_verification_app --factory` entry point on assigned
port 54702, with bytecode writes disabled. The normal server was not started.
The owned QA process 81668 exited cleanly after SIGINT and its session closed;
the pre-existing server was left alone.

The verifier checked the corrected labels in actual passed and failed
historical records, four diagnostic details, the failed qualification pair
`b16d9b39d7fd3057`, conditioning's `not_run_gate_failed` state, three historical
arms and eight artifact downloads with matching hashes. Twenty isolated
response-fixture scenarios cover loading, empty, errors, stale/retry recovery
and execution/validation states; they are not measured neural results.
Widths 320, 390, 540, 720 and 1024 had no horizontal page overflow, and no
JavaScript error was recorded. Root also inspected the saved
[failed-record view](incentive-ui-browser-2026-09-13/bet36fly-reward-gate-failed.png)
and [mobile view](incentive-ui-browser-2026-09-13/bet36fly-reward-mobile.png).
Those historical records retain their original populations and messages.

The [post-browser protection check](incentive-protection-after-browser-2026-09-13.json)
reconciles the 791-file baseline: 788 files are identical; the only three
baseline differences are the edited browser verifier and the rebuilt HTML
and old JavaScript asset. The new JavaScript asset is the sole inventory
addition. There are no unexpected differences. All 1,077 pre-existing
evidence files checked against HEAD match, and the active model pointer,
original data, historical experiments and copied Microduck wiki remain
unchanged. This bounded check does not undo the previously disclosed
normal-server startup incident.

## Source calculations remain separate

The [six-condition source reproduction](incentive-handler-source-result-2026-09-13.md),
[independent saved-record audit](incentive-handler-independent-saved-audit-2026-09-13.json)
and [workbook comparison](incentive-handler-saved-analysis-result-2026-09-13.md)
are complete. Their source clock, clipped versus internal quantities,
reporter windows and incomplete final primary window remain explicit.
They select no production receptor constants or new candidate. The
[copy manifest](incentive-copy-manifest-2026-09-13.json) retains original
source/data/results and browser evidence while recording exact repository
copies. The new [cell-specific explanation](../../../wiki/cells/dopamine-receptor-signaling.md)
links those limitations to the accepted PPL101/MBON11 and PAM12/MBON09 cells.

All 203 new standalone cases passed from the canonical repository evidence
directory in 2.09 seconds: 69 source-helper, 78 transfer-math, 12 launcher and
44 saved-analysis cases. The helper/test files also passed Ruff. This command
used synthetic fixtures and saved external data; it did not rerun the six
authored source conditions. [Test log](incentive-canonical-tests-2026-09-13.txt)
and [Ruff log](incentive-canonical-ruff-2026-09-13.txt).

The remaining objective is a source-grounded mechanism that passes both
complete qualification panels and the frozen acquisition/reversal controls.
No such result, model promotion, sports pilot or push occurred here.
