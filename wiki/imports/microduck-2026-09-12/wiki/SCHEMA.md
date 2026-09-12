---
type: schema
updated: 2026-09-12
status: active
---
# How this wiki is maintained

This is a research knowledge base for Microduck embodiment, connectome models, GPU training, and object retrieval. It uses [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): maintain a durable synthesis between original sources and questions; organize navigation in an index and changes in a chronological log; revisit related pages when evidence changes. The pattern does not prescribe this folder layout or mandate a particular Markdown application.

## Layers

- [Source records](../research/raw/index.md): dated retrieval records and selected licensed upstream snapshots. Keep completed snapshots unchanged; add a new dated snapshot for a revision. A URL-only record is a pointer, not an archived document. Author reports are not local reproductions.
- [Compiled wiki](index.md): explanatory topic, entity, comparison, and source-synthesis pages. Prefer an integrated account over a pile of summaries. Change conclusions when new evidence warrants it.
- This schema: project-specific conventions for interpreting and maintaining the research. It does not grant permission to train, spend, publish, or alter external accounts.

## User intent and terminology

The user wants NVIDIA GPUs used to train **both duck body skills/control and the fly controller**, while giving a fresh MaleCNS model a Microduck body. Training architecture and deployed control authority must be explicit. Do not silently replace that intent with either a frozen fly demo or a prohibition on training conventional motor skills. See [training and deployment roles](synthesis/training-and-deployment.md).

“Fresh” means project-specific initialization and checkpoints with no imported sports-trained gains. It does not mean discarding anatomy, forbidding published methods, or forbidding movement demonstrations. Hardware arrival timing is user planning context, not a verified shipping commitment.

## Page format

Use ordinary Markdown with relative links that work in GitHub, an editor, and Obsidian. Each substantive page should identify its question, answer, evidence, implications, limits, and related pages. YAML metadata includes `type`, `updated`, and `status`; optional fields include `sources`, `tags`, and `confidence`. Use headings where they aid research navigation. Page length follows substance, not a minimum word quota.

Claims need citations near the text they support. Source records retain original URLs and, where available, source publication dates, repository revisions, retrieval dates, and license. Cite a specific file or method rather than an organization homepage for an implementation claim. Do not copy whole copyrighted articles or papers into the wiki. Preserve third-party license notices on permitted code/document snapshots.

## Evidence vocabulary

| Label | Meaning |
|---|---|
| Source-backed | Directly supported by inspected primary documentation, code, data, or paper |
| Author-reported | The project reports a result; this project has not reproduced it |
| Locally observed | Executed or observed here, with the exact scope and artifact specified |
| Synthesis | Our inference across evidence; not a source's demonstrated result |
| Proposed | A design or experiment to be evaluated |
| Unresolved | Conflicting or insufficient evidence |

Never promote one tier to another by linking to it. A rendered brain is not proof it controls motion. A changing weight is not proof of learning a useful behavior. A reward improvement is not proof of successful object containment. A GPU model name in a command is not proof of execution on that GPU.

## Ingest, query, and lint

On ingest: record the source, identify affected pages, update both supporting and contradicting claims, add cross-links, revise the [index](index.md), and append the [log](log.md). For batch research, reconcile all topic sections before calling the batch complete. A source may alter several pages.

On a query: consult the index, read the relevant pages, refresh drift-prone facts, and answer with evidence. File a reusable comparison or conclusion into the wiki when it belongs in the current authorized research scope. Do not turn private account state or tokens into research content.

On lint: check broken relative links, index coverage, unreachable/orphan pages, absent sources, stale operational facts, incompatible dates, contradictory architectures, overclaimed community demos, and missing cross-topic connections. Append what was actually checked and what remains unresolved. Structural lint cannot prove factual truth; use independent primary-source spot checks as well.

## Scope and change control

The research pass does not launch training. Any later experiment needs its controller identities, parameter updates, checkpoint lineage, observation/action contract, actual GPU allocation, maximum runtime, and acceptance evidence recorded. Preserve existing repository work; wiki maintenance is not authorization to rewrite the neural engine.

Related: [index](index.md), [overview](overview.md), [open questions](synthesis/open-questions.md).
