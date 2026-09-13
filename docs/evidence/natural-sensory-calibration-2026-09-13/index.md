# Natural sensory calibration checkpoint — September 13, 2026

**Outcome: exact anatomical candidates exported; the physiological drive contract remains unresolved. Zero new sensory neural calls.** No natural response, feeding, acquired association, two-source neural choice or sports improvement is claimed. This is the bounded unresolved-contract endpoint authorized in the handoff.

## What is resolved

The read-only [exporter](../../../scripts/export_sensory_crosswalk.py) checked all three original source-lock hashes and the complete retained graph accounting: 166,700 neurons, 25,582,938 directed pairs and 124,177,617 contacts. It exports 475 candidate rows, preserving integer body IDs, unknown sides, tracing labels and cross-specimen annotation strings. [Exact cells](crosswalk.csv), [anatomy and hashes](anatomy.json), [523 directed projection pairs](projection-edges.csv).

| Candidate | Exact population in this specimen | Evidence and limit |
|---|---:|---|
| Or92a / ab1B / ORN_VA2 | 83 | Benton Dataset EV1 row 15 plus native type; all 83 contact VA2_adPN 10390 and/or 10561: 149 pairs, 13,092 contacts |
| Or56a / ab4B / ORN_DA2 | 48 | EV1 row 23 plus native type; all 48 contact DA2_lPN: 374 pairs, 4,671 contacts |
| Additional odor candidates | DM1 74; DM2 54; DM5 35 | Receptor/glomerulus correspondence; no rate binding or valence assigned |
| Labellar candidates | 167 of 1,428 gustatory-class cells | All 167 lack `receptorType`; sweet/water/bitter membership remains unresolved |
| Feeding output candidates | MN9 10331, 16949 | Native labels with incomplete tracing; no demonstrated feeding response |

DA2_lPN IDs are 18416, 18776, 19339, 20105, 20311, 20995, 21876, 23958, 26423 and 34301. Projection contacts establish an anatomical path, not activity or approach/avoidance. Bilateral ORN projections do not supply independent home/away channels. Taste `flywireType` values are often many-to-one; copying female IDs or assigning modalities from LB names is unsupported.

## What prevents a run

[Calibration](calibration.json) retains original measurement vectors for four taste groups and all six control odor doses. Rates below are response measurements, **not requested simulator rates**:

| Stimulus and recorded class | Dose | Median response; observed range | Window and correction |
|---|---|---|---|
| L-glucose, long labellar sensilla | 50 / 100 / 500 mM | 12.50 / 25.33 / 44.67 Hz; ranges 7.33–18 / 13.33–35.67 / 33–52.67 | Counts divided by 3 s; 30 mM TCC diluent response subtracted; n=8/11/5 |
| L-canavanine, intermediate sensilla | 20 mM | 12.33 Hz; 8.33–14 | Same 3 s correction; n=7 |
| 2,3-butanedione, ab1B | 10⁻³ v/v | 118 ΔHz; 111–153 | 0.5 s stimulus; prestimulus frequency subtracted; n=5 |

The Zhao methods were reread. Taste recordings used 8–10-day adults and TCC to suppress the water neuron. Odor delivery used dichloromethane, 10 µl on 1 cm² filter paper, a pipette 2 cm from the antenna and a 10 s recording beginning 2 s before the 0.5 s stimulus. These window averages do not recover absolute baseline or transient/adaptation dynamics. Replicate ranges are not confidence intervals or specimen-transfer guarantees. Water physiology and a compatible geosmin schedule were not established here; mixtures are not assumed additive.

A newly identified primary source, **Tastekin et al., Cell 2026**, reports molecular mapping of male gustatory neurons and feeding pathways. Its accessible primary abstract supports pursuing the mapping; full text and subtype supplements could not be retrieved in the bounded check. This is an access/extraction gap, not evidence that no mapping has been published. [Source ledger](source-ledger.json) records the DOI, versions, access outcomes and the inspected Shiu implementation. Shiu's female-FlyWire model sweeps are not natural sugar measurements. The community Flycoin README is an unreproduced lead, not subtype ground truth.

## Decision and continuation

The preferred route remains a sweet/water/bitter feeding assay. The narrower ORN fallback has stronger anatomical identity, but currently only supports a proposed sensory-processing readout; it lacks a complete neutral/appetitive/aversive/mixed physiological contract. [Assay decision](assay-decision.md) freezes the current zero-call boundary and declares the finite conditional design. [Two-source and sports contract](sports-contract.md) separates external comparison from neural choice and prevents pairwise endpoint normalization.

The next bounded decision is to extract Tastekin's molecular subtype/body-ID table and its source dataset/version, then determine whether exact input identities and matching absolute physiology can be bound. Stop after that targeted source package and its directly relevant recording source; return the remaining explicit gaps if unresolved. Do not repeat the molecular repair pipeline or launch a sports pilot.

Production neural code, API and frontend behavior are unchanged. The exporter is an offline evidence tool; no UI claims a new assay. Historical v1 remains active, v2 paused, and legacy learning failures remain failures. [Reading coverage](reading-coverage.json), [checkpoint identity](checkpoint.json), [verification](verification.md).
