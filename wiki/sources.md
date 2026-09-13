---
type: source-ledger
updated: 2026-09-13
status: checked-with-access-limits
---
# Primary sources and evidence boundaries

## Calibration source addition — September 13

The [new ledger](../docs/evidence/natural-sensory-calibration-2026-09-13/source-ledger.json) adds Benton Dataset EV1 receptor/glomerulus mapping and the Tastekin Cell 2026 molecular-connectome lead. It records original-method rate checks, current Shiu code and bounded access failures. The abstract is not a retrieved subtype table; the community report is not a reproduced result.

The September 13 [natural sensory source ledger](../docs/evidence/natural-sensory-reorientation-2026-09-13/sources.json) adds measured taste/odor responses, complete selected workbook-group extraction, candidate MaleCNS sensory/output IDs and refreshed upstream checks. The [sensory page](natural-sensory-inputs.md) distinguishes measured Hz from artificial model stimulation, records the excluded workbook discrepancy and labels provisional DoOR transfer. The older source checks below remain dated records.

Checked September 12, 2026 UTC (September 11 America/Denver). The [machine-readable ledger](../docs/evidence/reassessment-2026-09-12/sources.json) records the URL, version, inspection scope and limitation for each new reference. [GitHub/release checks](../docs/evidence/reassessment-2026-09-12/upstream-checks.json) include returned revisions and content hashes. Source availability is distinct from reproduction.

| Source | Version / date | Use in this wiki | Inspection limit |
| --- | --- | --- | --- |
| [MaleCNS home](https://male-cns.janelia.org/) and [release notes](https://male-cns.janelia.org/release/) | v1.0, June 8, 2026; publication September 3 | Male CNS identity, chronology, attribution | Home and release notes disagree on October 3/5 for v0.9; preserve discrepancy. No newer release listed on the checked release page. |
| [Download schema](https://male-cns.janelia.org/download/) | v1.0 | Body IDs, annotations, aggregate contacts and separate synaptic locations | The wiki export rereads the local derived graph and annotations, not the complete raw weight table. |
| [Aso et al.](https://elifesciences.org/articles/04577) | 2014 version of record | MB compartments, MBON09 γ3β′1, MBON11 γ1pedc>α/β | Anatomical framework; do not substitute its counts for this MaleCNS specimen. |
| [Caron et al.](https://www.nature.com/articles/nature12063) | 2013 | Convergence and distributed sensory representation | Primary abstract/manuscript search text inspected; PMC full page challenged. |
| [Hige et al.](https://pubmed.ncbi.nlm.nih.gov/26637800/) | 2015; DOI 10.1016/j.neuron.2015.11.003 | Odor-specific plasticity and timing | Primary abstract and indexed author manuscript excerpts inspected; PMC direct open challenged. |
| [Handler et al.](https://pubmed.ncbi.nlm.nih.gov/31230716/) | 2019; DOI 10.1016/j.cell.2019.05.040 | DopR1/DopR2 and temporal-order sensitivity | Primary abstract and indexed publisher text inspected; direct full-page opens failed/challenged. |
| [Amin et al.](https://elifesciences.org/articles/56954) | 2020 version of record | APL local non-spiking inhibition | Primary eLife indexed abstract/introduction inspected; direct open failed. |
| [Shiu et al.](https://www.nature.com/articles/s41586-024-07763-9) / [code](https://github.com/philshiu/Drosophila_brain_model/blob/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960/model.py) | 2024; repository head `91bdd1e` | LIF foundation on female FlyWire | Paper and entire `model.py` inspected; no reference experiment reproduced. Releases endpoint returned none; one open clustering-analysis question was listed. |
| [Jiang and Litwin-Kumar](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009205) / [code](https://github.com/alitwinkumar/jiang_litwin-kumar_mb_rnn/blob/a16f86a3e9e476eff6860c3c0e0e1bbe729d7f85/runmodel.py) | 2021; head `a16f86a` | Opposing plasticity terms and optimized signal-generating circuit | Paper and entire `runmodel.py` inspected; not reproduced on MaleCNS. |
| [Bennett et al.](https://www.nature.com/articles/s41467-021-22592-4) | 2021 | Explicit feedback/error model | Primary model description inspected; its mechanisms are not automatically implemented here. |
| [Flyhard](https://github.com/MarkUnthank/flyhard) / [DOOMFLY](https://github.com/nftechie/doomfly) | Heads `bad2131` / `71ecf53` | Bounded community comparison | Entry points and heads refreshed; imported reports remain author-reported or prior code inspection. |

The peer-reviewed LIF reference used here is Shiu's female-FlyWire work. This bounded check does not establish that no other male-CNS study exists. The new wiki makes no such exhaustive absence claim.

For the imported literature and larger community map, consult the copied [connectome source ledger](imports/microduck-2026-09-12/wiki/connectome/sources.md), [community source ledger](imports/microduck-2026-09-12/wiki/community/sources.md), and [central source records](imports/microduck-2026-09-12/research/raw/2026-09-12/source-ledger.json). Their recorded retrieval states have not all been refreshed here. No full copyrighted paper has been added to the archive.

[Wiki index](index.md)

## September 13 sensory source-access update

The previously inaccessible Tastekin Cell2026 package was recovered: [published Figure2](https://ars.els-cdn.com/content/image/1-s2.0-S0092867426009438-gr2.jpg), [supplemental figures](https://ars.els-cdn.com/content/image/1-s2.0-S0092867426009438-mmc1.pdf) and [cell workbook](https://ars.els-cdn.com/content/image/1-s2.0-S0092867426009438-mmc2.xlsx), DOI10.1016/j.cell.2026.08.016. Figure2/S16/S17 and the relevant captions were inspected, along with the December13,2025 preprintv2 morphology/methods. Functional labels are proposed from morphology/genetic-driver matching. The workbook join preserves exact MaleCNS IDs and rejects source/native disagreements.

[Cameron2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2865571/), DOI10.1038/nature09011, primary Results/methods/figure captions provide the first-second water/sucrose/caffeine means and recording conditions. [Haynes2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4305081/), DOI10.7554/eLife.03868, transmitter/inhibition/receptor sections constrain the DPM sign hypothesis; its matched native diagnostic failed. [New source hashes, retrievals, reading limits and assay outcomes](../docs/evidence/sensory-backtest-goal-2026-09-13/index.md). Checked September13,2026. A source inspection is not a reproduced natural exposure.
