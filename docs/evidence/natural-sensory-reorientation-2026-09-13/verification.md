# Verification — natural sensory reorientation

**Passed September 13, 2026.** Scope is documentation, agent rules and source/annotation evidence. No simulator, API, frontend implementation, experiment configuration or active model pointer was changed by this task. The natural-response assay and two-source choice remain unimplemented and unverified.

| Check | Result |
| --- | --- |
| Full `make verify` | Exit 0: 4,055 Python tests, Ruff, 103 frontend tests across eight files, TypeScript/Vite build passed |
| Changed docs and complete authored wiki | 36 Markdown files checked; all local targets resolve; 23 wiki metadata headers validated |
| Source-response arithmetic | All 28 selected control/RNAi groups reproduce sample counts, mean, median and range with correct units |
| Evidence JSON | Eight JSON files parse; reading manifest accounts for all 64 original wiki Markdown files and 380,442 bytes |
| Imported research | All 59 manifest entries match original size and SHA-256 |
| Protected state | All 66 monitored files unchanged, including active pointer, source lock, configurations and imported files |
| Patch whitespace | `git diff --check` passed |

[Full repository log](make-verify.txt), [structured documentation checks](checks.json), [protected baseline](protected-before.json). Python tests emitted two dependency deprecation warnings; no failures. No production change required new regression tests; the narrow changed-surface checks cover documentation integrity and extracted numeric evidence.

The complete selected Zhao workbook groups and published axes were inspected. The extraction retains exact source cells, values, normalization and sample counts. DoOR entries remain provisional because original full methods could not be opened. Source arithmetic is not physiological validation.

No fresh browser workflow was run for this documentation-only change. The existing app continues to describe v1 and legacy reward experiments; this task adds no runtime feature or UI claim. Earlier browser acceptance remains separately dated and does not establish a natural food-choice workflow.

Another active task is writing source-protocol artifacts under the legacy repair evidence directory. Its untracked files are excluded from this commit. This verification covers the checked tracked implementation, not that task's later mutations. The new prompt was written and queued for viewing; no message was sent to redirect the other task automatically.
