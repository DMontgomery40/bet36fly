---
type: cell-family
updated: 2026-09-12
status: source-backed-and-code-inspected
---
# ALPNs: the engineered entrance to the circuit

**Biology.** Antennal-lobe projection neurons carry processed sensory signals toward regions including the mushroom body. Convergence from different glomerular channels onto KCs supplies a combinatorial representation. Sports quantities have no natural ALPN assignment. [Caron et al. 2013](https://www.nature.com/articles/nature12063).

**Dataset.** The importer selects 686 cells by the exact `ALPN` class. Their released type and transmitter labels, and the sum of retained contacts reaching KCs, determine encoder eligibility. The complete population remains in the graph, even when a cell is not externally driven. [Cell IDs](data/neurons.csv), [encoder map](data/atlas.json).

**Implementation.** `glomerular_map` groups cholinergic ALPNs by their supplied type label and requires at least 100 summed KC contacts per type. It keeps 64 groups for 16 features, with four preferred standardized values per feature (−1.5, −0.5, 0.5, 1.5). The weakest surplus eligible type, `M_adPNm5`, is undriven. These assignments cover 275 ports. Rates follow a Gaussian of width 0.5 and peak 150 Hz, with values below 7.5 Hz set to zero. A particular game drives only the tuned subset. [Exact code](../../bet36fly/reward_encoder.py).

“Glomerulus” in the encoder is therefore an **annotation-type grouping proxy**. The exporter does not reconstruct glomerular geometry, infer an odorant receptor, or prove that all 64 supplied type groups are separate anatomical glomeruli. Record the actual type and member IDs when interpreting a channel.

## What labeled-line drive changes

The schema-3 constructor sets the gain on all edges **ending at** ALPNs to zero. Their outgoing anatomical edges remain. Scheduled inputs can then drive projection neurons without the previous antennal-lobe recurrence re-exciting them. This bypasses part of the natural sensory computation; it is an explicit interface intervention. The main kernel also exempts designated sensory cells from its normal refractory delay. [Constructor](../../bet36fly/reward_protocol.py), [native event loop](../../bet36fly/reward_lif.cpp).

The old 32-port rate interface drove nearly the same KC population for every game. Changing which ALPN groups receive input improved measured separation, but it did not fix the learning rule. The frozen protocol remains the current reference; another encoder redesign would confound the mechanism investigation. [Reassessment](../reassessment.md).

## Evidence to keep with any future change

Retain feature→type→body-ID assignments, the actual stimulus schedule, sensory spike counts, ALPN→KC contact totals, and repeated-seed versus fresh-noise KC responses. Confirm that rates and source IDs agree with the declared protocol before attributing a KC change to plasticity. The generated atlas provides assignments and contacts, not new activity traces.

[Cell atlas](index.md) · [Kenyon cells](kenyon-cells.md)
