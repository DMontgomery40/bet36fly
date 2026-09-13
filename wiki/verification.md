---
type: verification
updated: 2026-09-13
status: dated-verification-records
---
# Verification of this wiki integration

## Sensory calibration checkpoint — September 13

The [calibration verification record](../docs/evidence/natural-sensory-calibration-2026-09-13/verification.md) records exporter regression coverage, complete graph/hash checks, standard repository verification and guarded browser acceptance. These verify evidence tooling and the existing product; no natural sensory response has been measured.

## Natural sensory direction update — September 13

The [reorientation verification record](../docs/evidence/natural-sensory-reorientation-2026-09-13/verification.md) covers the current documentation/rules change, measured-response arithmetic, local links, protected files and repository gate. Earlier software/browser checks below retain their dates and scope. The new natural sensory assay has not run; documentation verification does not establish physiology or choice behavior.

The September 13 [mechanism evidence UI acceptance](../docs/evidence/reward-mechanism-repair-2026-09-12/task4b-acceptance.md)
passed 970 Python tests, 81 frontend tests, Ruff/build and the actual guarded
browser workflow. It includes the failed bridge guard, stored-only raw evidence,
stale/retry recovery and mobile widths. All 782 protected files and inventories
were unchanged after requests and shutdown. These checks verify the evidence
display; the learning mechanism still has not qualified.

The later [fixed rate-adaptation screen](../docs/evidence/reward-mechanism-repair-2026-09-12/rate-adaptation-shadow-result.md)
completed 32 saved histories with zero circuit calls and failed all four home
guards. Before that screen, 373 synthetic cases passed. A separate complete-edge
reference method passed 20 tests before its later independent artifact audit. Root checked
all phase/edge product accounting and preserved the full failed result. The
[protected-file recheck](../docs/evidence/reward-mechanism-repair-2026-09-12/rate-adaptation-protected-verification.json)
still matches all 782 files, inventories, five historical pointer/manifest hashes
and 59 imported copies. No production API or browser behavior changed during
this offline investigation; the UI proof above remains separate.

## Current documentation refresh — September 13 UTC

The original 59-file imported snapshot still matches every saved hash and byte
count. All source files still exist, but 16 have changed in the separately active
Microduck checkout and five new orchestration wiki files now exist there. This
refresh did not modify that checkout or replace the dated copy. The initial copy
was not cut; a source that later evolves is distinct from a corrupted snapshot.
[Current copy/source comparison](../docs/evidence/reward-mechanism-repair-2026-09-12/wiki-refresh-verification.json).

The atlas check initially identified one stale field: the recorded source hash
of `reward_protocol.py`, changed by the integrated repair. Regeneration updated
that metadata only. Both cell/edge CSVs and all anatomical aggregates are
byte-identical; `export_fly_cell_atlas.py --check` now passes. Current authored
page links and the active pointer/four historical manifests were also checked.

These checks cover documentation and anatomy. They preceded the separately
completed evidence API/UI software and browser gate linked above. The earlier
[read-only startup acceptance](../docs/evidence/reward-mechanism-repair-2026-09-12/verification-startup-acceptance.md)
remains its own dated product check. The learning qualification remains failed
and conditioning/reversal remain unrun.

## Initial copy acceptance — September 12 UTC

The verified change is a copied research wiki, BET36FLY-specific cell/mechanism documentation, deterministic anatomical tables, and correction of an overstated Training-panel explanation. No new scientific experiment or trained checkpoint is claimed.

## Copy and atlas

- All **38** original wiki files are present. All **59** copied files (wiki, source archive and local references) match their original SHA-256 and byte count. Microduck originals remain untouched. [Manifest](imports/microduck-2026-09-12/COPY_MANIFEST.json).
- The atlas contains **5,243 unique cells** and **8,866 selected directed pairs**, with all body IDs aligned to source annotations. Gamma-policy eligibility totals **7,423** (4,184 home and 3,239 away). It describes the repair policy without enabling it.
- `.venv/bin/python scripts/export_fly_cell_atlas.py --check` reproduces all three exported files byte-for-byte. The exporter reads anatomy only; it does not construct an engine or simulate activity.
- The final structural check covers authored-page metadata, existing local link targets, index reachability, copied-source coverage, source hashes, source-ledger IDs and atlas accounting. [Machine-readable verification](../docs/evidence/reassessment-2026-09-12/copy-verification.json).
- The protected active-model pointer and four experiment manifests retain all five recorded hashes. The repair worktree remains at its recorded commit with no tracked edits.

Original upstream Markdown excerpts are excluded from compiled-wiki link checking: they are selected immutable files, not full mirrors of their repositories. The copied compiled wiki itself is checked. Small atlas and source-snapshot directories have explicit Git ignore exceptions; bulk project data stays ignored.

## Software checks

| Command | Result |
| --- | --- |
| `cd web && npm test -- --run src/RewardExperiments.test.tsx` | 15 passed |
| `.venv/bin/python scripts/export_fly_cell_atlas.py --check` | Exact match |
| `.venv/bin/ruff check scripts/export_fly_cell_atlas.py` | Passed |
| `make verify` | 379 Python tests, Ruff, 65 frontend tests, TypeScript/Vite production build passed |

Pytest emitted two dependency deprecation warnings (Starlette/httpx and AnyIO's portal alias), with no failures. The build completed before browser verification. No API contract, protocol, native engine or model artifact changed.

## Visible Training workflow

Flow: `http://127.0.0.1:8765/#training` → select a recorded reward experiment and arm → inspect the corrected baseline explanation, gate status, curves and downloads. The existing server was identified as this checkout, started with `warm_on_start=False`; no background training or inference refresh was started for the check.

The dedicated Browser plugin/skill was not available. Used the repository's existing Playwright script with Playwright from the bundled workspace runtime; installed no new dependencies.

```sh
NODE_PATH=/Users/davidmontgomery/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules \
  node scripts/verify_reward_browser.cjs /tmp/bet36fly-wiki-qa-20260912
```

| Check | Observed result |
| --- | --- |
| Page identity / meaningful content | BET36FLY Connectome observatory at the expected Training route |
| Corrected explanation | States that signed subtraction can change gains without teaching; old neutrality claim absent |
| Interaction | Paired, shuffled and frozen details selected; separate failed-gate experiment opened |
| Recorded results | Schema-3 completed pilot and schema-2 failed gate remained distinguishable |
| Downloads | Eight registered artifacts matched their SHA-256 |
| State handling | Loading, empty, error, running, failed and budget-stopped fixtures passed; fixtures are not experiment results |
| Responsive layout | Desktop 1,440 px; widths 320, 390, 540, 720 and 1,024 px without horizontal page overflow |
| Console / overlay | No page errors; focused follow-up found no console warnings/errors or Vite overlay |
| Visual inspection | Corrected explanation screenshot inspected at mobile width |

Browser execution records are preserved as [reward browser evidence](../docs/evidence/reassessment-2026-09-12/browser-evidence.json) and [focused explanation evidence](../docs/evidence/reassessment-2026-09-12/explanation-evidence.json). Screenshots remain in `/tmp/bet36fly-wiki-qa-20260912/`; they are local QA artifacts, not a committed scientific result.

## Limits

The scientific hold SCI-001 remains. No new acquisition, reversal, schema-5 backtest, biology validation or external community reproduction ran. Existing full-circuit diagnostics were inspected rather than replayed. The raw weight table was not re-imported, and not every external link in the copied wiki was refreshed. Browser acceptance covers the existing reward workflow and the changed explanation, not an interactive wiki application or every product route.

[Wiki index](index.md) · [Reassessment](reassessment.md)

## September13 sensory goal preconfirmation gate

The [new verification record](../docs/evidence/sensory-backtest-goal-2026-09-13/verification.md) records4,132 Python tests,103 frontend tests, Ruff/build and guarded browser acceptance. This is software/retained-UI evidence, separate from the narrower passed sensory and external-probe assays and the still-pending sports confirmation.

The later [confirmation integrity check](../docs/evidence/sensory-backtest-goal-2026-09-13/confirmation-integrity.json) reproduced all predictions and confidence bounds. The backtest goal passed; the protected model/legacy files remain unchanged.
