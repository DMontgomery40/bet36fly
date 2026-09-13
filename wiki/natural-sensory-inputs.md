---
type: sensory-calibration
updated: 2026-09-13
status: second-order-response-qualified-feeding-unqualified
---
# Fruit, sugar water and aversive inputs

## Calibration checkpoint — September 13

The earlier [zero-call calibration checkpoint](../docs/evidence/natural-sensory-calibration-2026-09-13/index.md) remains frozen. [New primary-source retrieval and native trials](../docs/evidence/sensory-backtest-goal-2026-09-13/index.md) bind 34 proposed sweet LB3b/c, 17 water LB3a and 38 bitter LB1a–d cells, with exact MN9 IDs 10331/16949. Published functional assignments are morphology-based proposals. Cameron 2010 supplies first-second raw bristle means: 100 mM sucrose 58.9 ±3.3, water 12.0 ±0.9, 10 mM caffeine 18.8 ±3.0 Hz (SEM, all solutions 1 mM KCl). Uniform class transfer, constant waveform and zero background are explicit model assumptions. The first16-call feeding assay and coupling sweep failed. A subsequent narrower Clavicle/Quasimodo sensory assay passed fresh-seed, timing and recovery guards at0.11 mV/contact; its independent-contact comparison is external. Water ingestion, calibrated chemical mixtures, innate choice and prospective sports usefulness remain unverified. The separate conditional historical backtest passed.

The [current direction](../docs/PROJECT_DIRECTION.md) is to establish a natural sensory-response assay before returning to sports learning. There is no single “Hz into the fly brain” for fruit or sugar water. A defensible input is a stimulus-specific pattern over identified sensory neurons, with a dose, baseline, onset, duration and uncertainty. This page records actual measurements and separates them from simulator settings.

## Measured taste and odor responses

**Zhao et al. 2022**, Figure 7, Mex-Gal4 controls: workbook values and figure axes checked. Taste counts are **spikes/3 sec** (divided by three); odor values are already rates. [Methods](https://www.nature.com/articles/s41467-022-35527-4), [workbook cells and calculations](../docs/evidence/natural-sensory-reorientation-2026-09-13/measured-response-extraction.json).

| Stimulus | Recorded population | Dose | Median response, spikes/s | Observed range | Recordings |
| --- | --- | --- | --- | --- | --- |
| L-glucose | Long labellar sensilla, sweet response | 50 mM | 12.5 | 7.3–18.0 | 8 |
| L-glucose | Same | 100 mM | 25.3 | 13.3–35.7 | 11 |
| L-glucose | Same | 500 mM | 44.7 | 33.0–52.7 | 5 |
| L-canavanine | Intermediate labellar sensilla, bitter response | 20 mM | 12.3 | 8.3–14.0 | 7 |
| 2,3-butanedione | ab1B / Or92a olfactory neurons | 10⁻³ dilution, v/v | 118 | 111–153 | 5 |

Taste values are diluent-subtracted averages, not onset rates; L-glucose differs from sucrose and nutritive D-glucose. Odor values are changes from baseline for a 0.5-second stimulus. Recordings sample sensilla from three flies. Ranges are not confidence intervals. RNAi groups remain separate; Figure 7f is excluded for a figure/workbook diet-label discrepancy. These averages do not recover a waveform.

For **sucrose specifically**, Charlu et al. 2013 measured 100 mM sucrose responses in 3–10-day-old male flies, counting the first 0–500 ms and doubling to obtain spikes/s. Their inclusion criteria were **at least 50 spikes/s for L-type sensilla**, or **30 spikes/s for I/S-type**. These are sample-selection thresholds, not typical firing rates. The study also examines temporal responses in 50-ms bins and sugar/acid mixtures. Its shorter window must not be compared as if equivalent to Zhao's three-second average. [Primary methods and Figure 4](https://pmc.ncbi.nlm.nih.gov/articles/PMC3710667/).

These sources establish useful numerical anchors. They do not yet specify a validated native MaleCNS drive schedule. Resolve the chosen tastant, sensory identities and baseline/window semantics before choosing parameters; do not average unlike assays into a universal “sugar Hz.” Water also needs its own source and cell mapping—the taste electrolyte suppresses water-neuron responses.

## Fruit odor is a population pattern

DoOR preserves source-specific electrophysiology as well as a merged normalized response matrix. Only the former can provide candidate firing-rate evidence. In its pinned `Hallem.2006.EN` columns, Or22a responses to ethyl acetate, ethyl butyrate and methyl hexanoate are respectively **57, 197 and 260**; corresponding Or85a responses are **79, 139 and −2**. Metadata describes baseline subtraction and a 10⁻² stimulus dilution. These are empty-neuron assay responses, provisionally interpreted as changes in spikes/s; the original Cell methods could not be opened in this task. They are **reference leads, not approved drive values**. Negative response means suppression relative to baseline, not a negative event rate. [Pinned source data](https://github.com/ropensci/DoOR.data/tree/db323a496577c4b4a72b5c2fcd1859e07521ffb5/data), [original study](https://pubmed.ncbi.nlm.nih.gov/16615896/), [extraction and limits](../docs/evidence/natural-sensory-reorientation-2026-09-13/odor-reference-extraction.json).

The same compound can activate channels differently; an entire fruit mixture cannot be identified with its strongest receptor or with total spikes. Verify current receptor coexpression and nomenclature before binding a DoOR receptor to a MaleCNS type. [Benton et al. 2025 reference map](https://link.springer.com/article/10.1038/s44319-025-00476-8).

A candidate aversive odor route is **geosmin → Or56a/DA2**. Stensmyr et al. demonstrate a specialized microbial-warning pathway and avoidance. This is a more defensible starting contrast than assuming any weaker fruit odor is unpleasant; no geosmin dose/rate has been calibrated here. Mixture and behavioral context still matter. [Primary study](https://doi.org/10.1016/j.cell.2012.09.046).

## What exists in this MaleCNS import

All 166,700 local node rows were examined. This inventory is annotation evidence, not a functional test. [Full counts and candidate body IDs](../docs/evidence/natural-sensory-reorientation-2026-09-13/annotation-audit.json), [source lock](../docs/connectome-source-lock.json).

| Exact annotation | Local count | Meaning and remaining work |
| --- | --- | --- |
| `class=olfactory` | 2,639 | Contains candidate sensory populations; not a chosen stimulus set |
| `class=gustatory` | 1,428 | Labels alone do not resolve sweet/water/bitter receptor identity |
| `ORN_DM1` / `ORN_DM2` | 74 / 54 | Candidate odor crosswalk anchors; verify receptor-to-type and source compatibility |
| `ORN_DM5` / `ORN_DA2` / `ORN_VA2` | 35 / 48 / 83 | Additional anchors, not proof of natural valence or measured response |
| `type=MN9` | 2 | Body IDs **10331**, **16949**, annotated cholinergic motor cells; verify paths and function before selecting output |

Do not stimulate all gustatory cells as sugar. Do not copy female FlyWire sensory IDs into MaleCNS. Anatomy must connect the chosen sensory population to a justified downstream observation; simply finding a type name is insufficient.

## What the reference simulator establishes

Shiu et al. 2024 use female FlyWire connectivity to model taste-to-feeding responses, including sugar/water/bitter input and MN9-related feeding initiation. Their **10–200 Hz** sugar sweep is a computational stimulation range. It is not an electrophysiological measurement of natural sugar. The paper cautions against interpreting absolute predicted firing rates as accurate physiological values. This motivates a bounded replication of qualitative sensory/feeding relationships in our specimen, not a claim that MaleCNS already reproduces them. [Primary paper](https://www.nature.com/articles/s41586-024-07763-9).

The inspected reference `model.py`, revision `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960`, defaults to 150 Hz Poisson input with a 250× synaptic scaling factor and removes the refractory delay for externally driven cells. Those are interface settings. [Pinned code](https://github.com/philshiu/Drosophila_brain_model/blob/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960/model.py).

## What BET36FLY currently does

The legacy reward encoder assigns sports features to 64 ALPN annotation-type groups and drives 275 ports with Gaussian preferred values and a 150 Hz peak. It does not contain a stimulus/receptor response map. Incoming ALPN connections are scaled to zero in that diagnostic. The native input loop uses a per-step event probability `rate_hz * dt_ms / 1000`; each event adds 68.75 mV to a designated input cell. With the usual 0.2-ms step this is a discrete Bernoulli drive. Requested generator rates must therefore be checked against achieved spikes and time-bin resolution. [Encoder](../bet36fly/reward_encoder.py), [constructor](../bet36fly/reward_protocol.py), [native loop](../bet36fly/reward_lif.cpp), [existing ALPN explanation](cells/alpn.md).

The fixed legacy home/away MBON readout is an engineered sports interface. It has not been validated as a natural approach/avoid or feeding readout. A source-supported sensory assay may use different input/output cells and must explicitly review connectivity, interventions and resets.

PAM-γ3 provides a particularly useful warning against equating stimulation with sweetness: Yamagata et al. find that sugar ingestion suppresses its ongoing activity, and selective manipulation distinguishes appetitive memory from innate sucrose preference. This does not validate a particular PAM12 rate or transfer function in our specimen. [Primary study](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1002586).

The [handoff](../docs/NATURAL_SENSORY_HANDOFF.md) records the current finite assay stage. The isolated sensory engine does not change the legacy ALPN encoder or active model. Second-order response and external independent-opportunity controls passed; feeding and in-circuit choice remain unqualified. The frozen pipeline passed the predefined historical 2023 backtest; incremental neural value remains unproven. [Result](../docs/evidence/sensory-backtest-goal-2026-09-13/RESULT.md).
