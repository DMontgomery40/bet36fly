---
type: anatomical-pathways
updated: 2026-09-14
status: anatomy-checked-functional-assays-proposed
---
# Visual input, lateral horn and downstream choice pathways

Claude's recent research identified several routes beyond the current taste and team-odor interfaces. This page owns their anatomical inventory and biological precedents. [Research directions](../research-directions.md) owns the proposed experiments and comparators. None of these proposed functional assays was launched by this wiki integration.

## Three different visual questions

**Biology.** Vogt et al. found shared dopaminergic requirements and partly overlapping mushroom-body populations for visual and olfactory associative memory. Li et al.'s hemibrain analysis identifies visual inputs to the mushroom body and output paths toward descending neurons and the central complex. These are biological/hemibrain precedents; the MaleCNS counts below are independently selected from this repository's locked specimen. [Vogt 2014](https://elifesciences.org/articles/02395), [Li 2020](https://elifesciences.org/articles/62576).

Lappalainen et al. modeled 64 optic-lobe cell types, optimized unknown neuron/synapse parameters for motion detection, and compared predicted responses with recordings from 26 studies. This supports testing anatomically constrained computation with fitted dynamics. It is not evidence that an uncalibrated MaleCNS LIF model will interpret a baseball image or beat its encoder. [Primary paper](https://www.nature.com/articles/s41586-024-07939-3).

| Question | Proposed pathway | Required distinction |
| --- | --- | --- |
| Fixed visual encoding | Photoreceptors → optic lobe → LC/LPLC/MeVP or other measured visual outputs | Compare against a nonlinear model with the same rendered information |
| Visual associative memory | Visual projection neurons → accessory calyx / γ-d KCs → compartment-specific MB output | Establish input/output transmission and then conditioning against a frozen twin |
| Bilateral choice | Two alternatives → value/heading integration → lateralized downstream response | Demonstrate a reproducible swap-reversing response before calling it neural choice |

Rendering an existing probability as brightness changes its presentation, not its information. Any scene must declare quantities, spatial arrangement, contrast, timing and uncertainty. Retinotopic stimulation also needs a verified body-to-column/eye map; the current compact node table alone does not supply that mapping.

**An inspected eye map exists.** [FlyOCR](../community.md#flyocr--inspected-september-14-2026) (commit 48cf341, read September 14) builds its retinotopic input from the released `assignedOlHex1`/`assignedOlHex2` column annotations on L1/L2/L3 cells, assigning each of the 3,335 `R1-R6` cells to its strongest connected annotated lamina anchor (825 distinct sites, then a 33 × 25 grid by minimum displacement). That is a reproducible body-to-column map from the same annotation file our lock pins; it is an inferred projection, not optical calibration, and it feeds a DOOMFLY-constant LIF rather than this simulator's dynamics. Any BET36FLY retinotopic stimulus should start from those annotation fields and re-derive the map under our own coupling, not import FlyOCR's stimulus constants.

## What this MaleCNS graph contains

These are **retained neuron counts and aggregate synaptic contacts**, recomputed from all local graph arrays without a simulator. `LH` means a type-name prefix, not all cells with processes in the lateral horn. Class, superclass and type selectors are recorded in the [reproducible static audit](../../docs/evidence/wiki-integration-2026-09-14/anatomy-and-storage.json).

| Population or path | Count | Interpretation |
| --- | ---: | --- |
| `superclass=ol_intrinsic` | 89,403 cells | Optic-lobe intrinsic population |
| `superclass=ol_sensory` | 6,098 cells | Includes 6,091 `class=visual` cells; the superclass is not identical to an exact photoreceptor subtype selection |
| `superclass=visual_projection` | 9,201 cells | Visual projection population |
| `type=KCg-d` | 206 cells | Candidate γ-d visual-memory targets |
| Visual projection → any KC | 252 presynaptic cells; 1,616 pairs; 11,094 contacts | Anatomical visual input support |
| Visual projection → KCg-d | 200 presynaptic cells; 1,088 pairs; 8,041 contacts | Subset of the preceding path, not 8,041 cells |
| `class=CX` | 2,950 cells | Central-complex annotation |
| MBON → CX | 8,543 contacts | All CX targets; this aggregate is not a fan-shaped-body-only count |
| MBON → DAN / CX → DAN | 11,309 / 3,852 contacts | Anatomical feedback support, not demonstrated prediction error |
| `type` starts with `LH` | 2,028 cells | A reproducible lateral-horn type proxy |
| ALPN → LH / ALPN → KC | 443,271 / 390,928 contacts | Parallel anatomical routes |
| MBON → LH / LH → MBON | 36,712 / 21,199 contacts | Bidirectional aggregate support |
| Targets receiving ≥20 contacts from each of MBON and LH | 1,766 cells; includes 86 DAN and 59 CX cells | Candidate convergence, not verified joint information transmission |
| `superclass=descending_neuron` | 1,314 cells | Exact descending-neuron selection |
| CX → descending / LH → descending / MBON → descending | 7,187 / 22,810 / 4,347 contacts | Potential output paths; not an implemented choice readout |

The original memo also inventories L1, Mi, Tm, Dm, T4/T5, photoreceptor families, LC/LPLC/LLPC/MeVP, ER/EPG/PEN/PFL and fan-shaped-body type families. These prefix-based inventories are retained in the [research memo](../../docs/ASSOCIATIVE_NEXT_APPROACHES.md#what-the-imported-graph-contains-beyond-the-mushroom-body); the main table uses explicit, independently checked selectors. Do not treat counts from overlapping type families as mutually exclusive subdivisions.

The existing [KC subtype table](identities.md) records 6,038 KCg-d→MBON09 contacts. That is a legacy γ3β′1 output, not the γ4/γ5 learning target. It cannot stand in for verified KCg-d→MBON05/MBON01 eligibility; a visual-conditioning protocol must inspect those specific edges.

## Lateral horn and mushroom body integration

Li's study supports investigating convergence between innate and learned pathways. A candidate BET36FLY design would preserve a calibrated innate input, learn a contextual correction in the mushroom body and read anatomically supported convergence cells. The contact totals above justify a links assay; they do not establish that the current odor codes already produce separable innate and learned components there. “Innate” must refer to a calibrated response, not a sports value assigned because a cell is named LH.

## Central complex and descending output

Westeinde et al. studied transformation of heading signals into steering commands through PFL3, with a different role for PFL2. Hulse et al. supply a central-complex connectivity framework. These navigation findings motivate a comparison assay; assigning teams to headings remains an engineered hypothesis. [Westeinde 2024](https://www.nature.com/articles/s41586-024-07039-2), [Hulse 2021](https://elifesciences.org/articles/66039).

The first question is whether simultaneous alternatives evoke stable lateralized responses that reverse with identity/side swaps and survive appropriate controls. A sensory-to-motor claim requires a measured downstream chain, not Python subtraction of two independently reset probes. None of this follows solely from retaining these neurons in a whole-graph integrator. Physiological calibration of inhibition and response dynamics should precede functional claims for the new routes.

## Other sensory channels

The retained class inventory includes 2,558 `mechanosensory_tactile`, 1,454 `mechanosensory_proprioceptive`, 1,733 `mechanosensory`, 66 `hygrosensory` and 25 `thermosensory` cells. Encoding rest, travel or score histories through these channels would be an engineered input assignment requiring its own calibration and same-information comparator. Those annotations do not provide a natural baseball code.

[Cell atlas](index.md) · [Sensory rate evidence](../natural-sensory-inputs.md)
