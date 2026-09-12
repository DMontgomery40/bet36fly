---
type: source-ledger
updated: 2026-09-12
status: researched
---

# Connectome primary-source ledger

[Connectome index](index.md) · [Release analysis](malecns-release.md) · [Embodiment analysis](embodiment-research.md) · [Interface contract](brain-body-interface.md)

Retrieved September 12, 2026 UTC / September 11 America/Denver. This ledger records source access, not independent reproduction. Sources are paraphrased in the wiki; full articles and videos are not mirrored. Machine-readable records: [sources.json](sources.json).

| ID | Primary source | Date/version | Used for |
|---|---|---|---|
| MC-HOME | [MaleCNS project](https://male-cns.janelia.org/) | Live project chronology | Publication date, collaboration, license pointer. |
| MC-RELEASE | [Release notes](https://male-cns.janelia.org/release/) | v1.0 June 8, 2026 | Dataset version date and documented changes. |
| MC-DATA | [Download documentation](https://male-cns.janelia.org/download/) | v1.0 | Raw table semantics and access. |
| MC-OVERVIEW | [Janelia overview](https://www.janelia.org/project-team/flyem/male-cns-connectome) | Current project description | Anatomical coverage and intact neck. |
| MC-GOOGLE | [Google announcement](https://www.research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/) | September 3, 2026 | Rounded public counts and publication context. |
| MC-PAPER | [Berg et al., Cell](https://doi.org/10.1016/j.cell.2026.08.015) | September 3, 2026 | Canonical publication pointer; full text failed to open in this pass. |
| FW-PAPER | [Dorkenwald et al., Nature](https://www.nature.com/articles/s41586-024-07558-y) | October 2, 2024 | Female brain counts and source boundary. |
| FGM-PAPER | [Jin et al., arXiv](https://arxiv.org/html/2602.17997v1) | v1, February 20, 2026 | Architecture, signs, imitation initialization and PPO. |
| FGM-SITE | [FlyGM author site](https://lnsgroup.cc/research/FlyGM/) | Live September 12 UTC | Code availability and method discrepancy. |
| EON-TECH | [Eon technical account](https://eon.systems/updates/embodied-brain-emulation) | March 10, 2026 | Actual integration and stated limitations. |
| EON-UPDATE | [Eon perspective](https://eon.systems/updates/more-flies-are-getting-uploaded) | September 11, 2026 | Latest author account; not a new peer-reviewed result. |
| NMF-PAPER | [NeuroMechFly v2](https://www.nature.com/articles/s41592-024-02497-y) | 2024 | Sensorimotor and controller framework. |
| FB-CODE | [Flybody official README](https://github.com/TuragaLab/flybody/blob/main/README.md) | Live main | Body assets, optional ML and distributed training interfaces. |
| CC-BY | [Creative Commons deed](https://creativecommons.org/licenses/by/4.0/) | 4.0 | Dataset license terms summary. |
| LOCAL-MANIFEST | [Local manifest](../../data/brain/manifest.json) | Existing local build | Counts, retention policy, source hashes and explicit assumptions. |
| LOCAL-IMPORTER | [Local importer](../../flybrain/connectome.py) | Read during research pass | Actual retention, ALPN selection, sign rules and CSR orientation. |

## Discrepancies to preserve

1. MaleCNS home gives October 3, 2025 for v0.9; release notes give October 5. No need to resolve this to identify the June 2026 v1.0 source.
2. FlyGM paper says source code is available; author site says coming soon. Treat implementation reproducibility as unresolved.
3. FlyGM site says unweighted; paper defines signed synaptic weights. Pin a real code revision before adopting either as executable truth.
4. FlyGM's glutamate/histamine signs differ from the local importer. A paper's convention is not a biological adjudication.
5. The Cell publisher link failed to fetch. Publication identity and chronology were verified through the official project and Google; this pass does not claim full-text examination of the Cell methods.

## Evidence still needed

No external study was reproduced here. No NVIDIA job, simulator learning run, robot rollout, or biological intervention was executed by this research task. The local manifest was read and its aggregate arithmetic checked, but this pass did not independently reread every source row or recompute all hashes. These limits should stay attached when citing this wiki in an implementation plan.
