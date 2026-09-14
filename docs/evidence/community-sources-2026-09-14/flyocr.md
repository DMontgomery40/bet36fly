# FlyOCR (jerryjliu/fly_ocr): inspection record

**Checked 2026-09-14 UTC.** Repository https://github.com/jerryjliu/fly_ocr, shallow clone of `main` at commit `48cf341e99c17dc911fb09fdc8419d98b4d0ea86` (author date 2026-09-12 20:37 -0700). Announcement: Jerry Liu on X, "Introducing FlyOCR — I trained a fly brain to read a PDF" (screenshot supplied by David on September 14; the post text is a community report, the repository is the inspected implementation). Nothing was executed here: no download, no `flyocr prepare`, no recognition run. Status: **community report + inspected implementation, not reproduced.**

## What it is

A fixed MaleCNS v1.0 spiking model receives one printed glyph at a time through an engineered photoreceptor adapter; a small trained decoder (4,096 → 64 → 68 MLP, 266,628 parameters) reads four 25 ms spike-count bins from 1,024 selected optic-lobe / visual-projection cells and names the character. Segmentation, normalization, word gaps and table geometry are conventional preprocessing outside the circuit. Architecture, graph import, retinal projection and the native LIF kernel are adapted from DOOMFLY commit `71ecf53d` (MIT), the same DOOMFLY head this wiki already pins.

## Same dataset files as BET36FLY

`configs/malecns-v1.json` pins the same three flat-connectome files as `docs/connectome-source-lock.json`, byte-for-byte:

| File | SHA-256 (both projects) |
| --- | --- |
| body-annotations-male-cns-v1.0-minconf-0.5.feather | 2177e246…f99a9a3b2 |
| body-neurotransmitters-male-cns-v1.0.feather | 95c92892…8da8879621 |
| connectome-weights-male-cns-v1.0-minconf-0.5.feather | e35da783…c1a56afc1 |

Retained graph: 166,700 nodes, 25,582,938 edges in both projects. FlyOCR's `graph-manifest.json` reports 124,177,617 contacts; our zero-call audit (`docs/evidence/wiki-integration-2026-09-14/anatomy-and-storage.json`) sums 124,177,616 from `data/brain/counts.npy`. The one-contact difference is unexplained and worth a bounded check of `scripts/prepare_connectome.py` (self-edges or a clipped count); it does not affect any result recorded here.

## Implementation facts read from the code (not from the post)

- **Dynamics** (`src/flyocr/brain/kernel.cpp`, report §4): current-based LIF on a 0.1 ms grid, membrane τ 20 ms, synaptic τ 5 ms, rest/reset −52 mV, threshold −45 mV, 1.8 ms delay, 2.2 ms refractory, incoming events ignored during refractory; every edge retained (lazy exact subthreshold solver). Weight = contact count × inferred transmitter sign × **0.275**. Acetylcholine positive; GABA, glutamate, histamine negative; unknown or ambiguous sign defaults **positive for 3,718 cells**. These are DOOMFLY-lineage constants, not Shiu et al. 2024's (our associative engine uses 0.11 mV/contact with Shiu constants and measured ALLN/APL/DA interventions).
- **Input** (`src/flyocr/data/connectome.py`): `type == "R1-R6"` cells (3,335 retinal inputs) are assigned to their strongest connected L1/L2/L3 anchor that carries the released `assignedOlHex1`/`assignedOlHex2` column annotation; hex coordinates are flattened to a plane per eye and the two eyes overlaid. 825 distinct sites; the "calibrated" adapter moves them onto a 33 × 25 grid by minimum squared displacement (RMS displacement 0.2022 normalized units). Brightness is inverted, low-pass filtered, saturating gain applied; tonic drive to L1/L2/L3/L5 (7,114 cells). Report §5 quotes receptor gain 20, half-saturation 0.2, tonic 20; `model.py` defaults are 30 / 0.02 / 12, so the artifact model cards, not the defaults, carry the identities used.
- **Readout**: feature candidates are `superclass ∈ {ol_intrinsic, visual_projection}` minus retina and lamina (91,490 cells); 1,024 are selected from training responses; square-root counts; standardization from training only. Gradients never enter the graph; there is no plasticity, dopamine, or learning inside the circuit.
- **Protocol**: 50 ms blank warm-up to a canonical state, full reset between glyphs (no cross-character memory), 100 ms presentation per glyph, about 0.29 s per glyph on an M2 Pro.

## Results as recorded by the authors (MODEL_CARD.md, docs/research-report.md)

| Measurement | Value | Scope |
| --- | --- | --- |
| 68-class glyph benchmark | 87.6% (1,429/1,632) | Synthetic glyphs, disjoint font families; benchmark had been inspected during iteration, not blind |
| Letters subset | 85.0% (1,061/1,248) | Same |
| Fresh two-family challenge | 84.9% on 544 glyphs | Uses macOS Georgia/Verdana, not bundled |
| PDF text (Microsoft 2025 annual report crops) | 5.7% character error over 176 characters; 1/8 lines exactly right | Manually chosen crops |
| Numeric tables | 21/21, 44/45 exact cells | Separate numeric checkpoint; 3° tilt breaks the grid |
| Label-mismatch control | 2.3% (chance 1.5%) | Signals carry information |
| Edge-removal control (digit pilot, 200 examples) | 82% intact → 10% removed | Pilot only |
| Degree-preserving target randomization, retrained heads (digit pilot) | 65.0%, 63.5%, 54.5% vs 82% intact | Activity scale changes with rewiring; authors say this does not establish a biological advantage |
| Conventional comparators (original 500-digit test) | raw-pixel linear 99%, small CNN 100%, circuit 89% | The circuit loses to the same-information baseline |

The X post's "~86% over the balance sheet heading" and "1.7k+ sampled glyphs … 87%" correspond to the 85.0% letter subset / 87.6% benchmark; the post rounds and does not mention the conventional-baseline comparison or the 1/8 exact-line figure.

## What transfers to BET36FLY, and what does not

- **Transfers:** the released `assignedOlHex1/2` column annotations give a real body-to-column eye map for R1-R6 → L1/L2/L3, which is exactly the "verified body-to-column/eye map" that [wiki/cells/visual-and-downstream.md](../../../wiki/cells/visual-and-downstream.md) lists as a prerequisite for any retinotopic stimulation (roadmap items 11A/11B). The control set (label mismatch, edge lesion, degree-preserving rewiring with retrained readouts, conventional model on identical pixels) is the same shape as our v2 null-graph and same-information comparators, and it reached the same verdict shape: the anatomy produces informative activity, and a conventional model on the same input still wins.
- **Does not transfer:** the 0.275 weight scale, positive-default unknown signs, tonic lamina drive and uniform cell constants are DOOMFLY engineering choices, not physiology; our own legacy v1 used the same 0.275 figure, and the associative engine deliberately does not. No dopamine, plasticity or in-circuit choice is involved. A fly reading a PDF is a decoder on frozen optic-lobe activity; the animated fly is presentation.
- **For roadmap item 11A/2 (optic lobe as encoder):** FlyOCR is the closest existing precedent and its own numbers predict the outcome we should expect: structured 2-D input becomes separable optic-lobe activity, and a fitted readout on it loses to a conventional classifier on the same pixels. Any BET36FLY visual-encoder arm must therefore declare the nonlinear same-information comparator up front, as the memo already requires.
