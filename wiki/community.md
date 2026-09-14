---
type: synthesis
updated: 2026-09-14
status: source-inspected-not-reproduced
---
# What the copied fly research contributes

The copied wiki supplies useful comparisons, especially the separation of anatomy, internal learning, engineered interfaces and downstream control. Its research is preserved with its original caveats. This page identifies relevance to BET36FLY; none of those external experiments was reproduced here.

| Project / research | What the imported record describes | Relevance here |
| --- | --- | --- |
| [Flyhard](imports/microduck-2026-09-12/wiki/community/flyhard.md) | Trainable graph internals with fixed interfaces; supported steering skill and author-reported interventions | Internal connectome learning is an inspectable engineering direction. It does not validate this dopamine rule or prove a topology advantage. |
| [DOOMFLY](imports/microduck-2026-09-12/wiki/community/fly-ecosystem.md) | Implemented plasticity and candid failed learning gates | Changing weights and live neural activity can coexist with failed task learning; controls must remain visible. |
| [Microfly](imports/microduck-2026-09-12/wiki/community/joint-projects.md) | Fixed female FlyWire core coupled to a trained robot gait; separate untrained direct mode | Attribute the competence to its actual owner. A downstream learned component can dominate behavior. |
| [Fly64 and Flybywire](imports/microduck-2026-09-12/wiki/community/fly-ecosystem.md) | Closed-loop fixed control, observer/assist modes and learned readout distinctions | A live brain display is insufficient to identify the training locus or neural control authority. |
| [FlyGM, Eon and embodiment literature](imports/microduck-2026-09-12/wiki/connectome/embodiment-research.md) | Different datasets, learned policies and engineered body support; availability discrepancies retained | Compare like with like before drawing conclusions from a demo. |
| [FlyOCR](https://github.com/jerryjliu/fly_ocr/tree/48cf341e99c17dc911fb09fdc8419d98b4d0ea86) (jerryjliu, September 12, 2026) | Fixed MaleCNS v1.0 LIF model (DOOMFLY kernel lineage, same three source files as our lock) reads printed glyphs through an R1-R6 → L1/L2/L3 column map; a 266,628-parameter decoder on 1,024 optic-lobe cells scores 87.6% on a 68-class glyph benchmark and loses to a raw-pixel linear classifier on digits (99% vs 89%) | The nearest precedent for the optic-lobe-as-encoder direction. Its released column annotations supply the eye map our visual page requires; its controls and its loss to the same-information baseline are the outcome to expect. [Inspection record](../docs/evidence/community-sources-2026-09-14/flyocr.md) |
| [Training/deployment roles](imports/microduck-2026-09-12/wiki/synthesis/training-and-deployment.md) | Distinguishes core, interface and body training | BET36FLY similarly distinguishes KC→MBON learning from the sports encoder and fixed decoder. |

This pass refreshed the primary GitHub entry points and heads for [Flyhard](https://github.com/MarkUnthank/flyhard/tree/bad2131a35518944834531f53be004e9f1b9eecb) and [DOOMFLY](https://github.com/nftechie/doomfly/tree/71ecf53d78eaffaf1a57ed7b0ccf5d458abc9f33). The copied Flyhard code analysis is a prior source inspection, not code replay in this task. The broader imported ecosystem and compute pages were not all fetched again. [Dated checks](../docs/evidence/reassessment-2026-09-12/upstream-checks.json).

The useful transfer is experimental discipline: identify trainable variables, freeze or explicitly version interfaces, compare before/after and against controls, and retain interventions showing which circuit contributes. A hobby project is neither an authority that our simulator must succeed nor evidence that biological learning cannot work.

BET36FLY needs more cellular detail than the robot overview: exact KC subtypes, MBON multi-territory anatomy, DAN selection, APL's model mismatch, transmitter assumptions and trace semantics. Those are now the [cell atlas](cells/index.md) and [learning contract](learning-rule.md).

## FlyOCR — inspected September 14, 2026

Jerry Liu's FlyOCR ("I trained a fly brain to read a PDF", X post, September 13) is a **community report**; the repository at commit `48cf341` is an **inspected implementation**; nothing was **reproduced** here. Read from the code and report: the same MaleCNS v1.0 flat-connectome files as `docs/connectome-source-lock.json` (identical SHA-256; 166,700 neurons, 25,582,938 edges), a current-based LIF at 0.275 × contact count with DOOMFLY constants (τm 20 ms, τs 5 ms, threshold −45 mV, 3,718 unknown-sign cells defaulted positive), glyph pixels delivered to the 3,335 `R1-R6` cells through their strongest L1/L2/L3 anchor's released `assignedOlHex1/2` column, one 100 ms presentation per glyph with a full reset, and a small trained decoder on four spike-count bins from 1,024 `ol_intrinsic`/`visual_projection` cells. There is no plasticity, dopamine or in-circuit decision. The authors' own controls show the activity is informative (label mismatch → 2.3%, near chance) and that degree-preserving rewiring with retrained heads retains 54–65% of a pilot's 82%, while a raw-pixel linear classifier on the same digits reaches 99% against the circuit's 89%.

Relevance: it is the first inspected use of the released optic-lobe column annotations as an eye map, which the [visual pathway page](cells/visual-and-downstream.md) names as a prerequisite; and it is a direct precedent for [research direction E](research-directions.md) that already carries the honest verdict, a fixed anatomy plus fitted readout does not beat a conventional model on identical input. The 0.275 weight scale is the same legacy engineering constant BET36FLY's v1 used and the associative engine replaced with 0.11 mV/contact and measured interventions. [Full inspection record](../docs/evidence/community-sources-2026-09-14/flyocr.md).

[Wiki index](index.md)
