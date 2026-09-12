---
type: verification
updated: 2026-09-12
status: checked-with-limitations
---
# Verification record

This records checks actually performed for the initial research batch, not a certification of a controller or physical robot.

## Research coverage and structure

The compiled wiki contains 34 Markdown pages covering the four requested research areas and their integration. A local structural check verified required metadata, existing relative-link targets, and reachability of every page from the index. The central ledger contains 80 source records with unique IDs and 80 distinct source URLs. Fifteen selected licensed upstream snapshots matched every SHA-256 digest in their manifest. The check excludes original upstream Markdown from compiled-wiki link validation: the archive preserves selected files exactly, not a complete offline copy of each repository.

All topic pages are linked from the [index](index.md). Source-only pointers remain distinguishable from offline snapshots. Working URLs and correct hashes do not establish factual truth; the evidence review below is a separate check. This pass did not exhaustively re-fetch every external link after writing.

## Independent evidence review

Three researchers covered compute, connectome, and community work; the main agent inspected pinned trainer/runtime code and reconciled their output. Cross-review independently checked Flyhard's trainable graph parameters and frozen interfaces, Flybywire's version-dependent authority, the runtime's recurrence contract, and the training/evaluation synthesis. A final Microfly check used the locally retrieved public README after network retrieval failed. That check corrected a misleading open question: persistent neural dynamics already exist there; the relevant design question is persistence across skill switches, falls, and resets.

The review also corrected a configured ground-pick objective being phrased as though it proved execution, and clarified that conditional stage probabilities multiply by the chain rule without assuming independent failures. The wiki preserves unresolved source contradictions instead of selecting the more impressive claim. See [open questions](synthesis/open-questions.md).

## Local code checks

The earlier graph-builder path repair is covered by subprocess regression cases launched from multiple working directories. Fresh checks after the research integration:

- `.venv/bin/pytest -q`: **11 passed**.
- `.venv/bin/ruff check scripts/build_brain.py tests/test_build_brain.py`: **passed**.
- `.venv/bin/ruff check flybrain scripts tests`: **14 existing findings** in untouched `flybrain/brain.py`, `flybrain/connectome.py`, `flybrain/reward_brain.py`, `flybrain/reward_encoder.py`, and `tests/test_connectome.py`. The full source lint is not clean; those unrelated files were preserved.

No project build command is defined in `pyproject.toml`. Archived upstream Python files are research inputs, not this project's maintained executable source. The graph build was executed before the research pivot and produced a fresh anatomical graph; this does not establish neural learning or GPU execution.

## What is still unverified

No paid GPU job was launched during this research pass. No new trained fly/body checkpoint, measured full-stack GPU capacity, simulator pickup success, physical retention/deposit result, or deployed neural-control latency is claimed. Community results remain author reports unless explicitly marked as locally observed. The [evaluation protocol](synthesis/hazard-evaluation.md) is proposed and unexecuted; the [training/deployment map](synthesis/training-and-deployment.md) preserves training both systems without prematurely selecting an architecture.

[Start page](index.md) · [Research log](log.md) · [Source archive](../research/raw/index.md).
