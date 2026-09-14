---
type: cell-type
updated: 2026-09-14
status: source-backed-and-code-inspected
---
# APL: two cells with unusually consequential approximations

**Two experiment policies:** legacy reward keeps APL output at 0.25. The associative links assay measured MBON05/MBON01 silence at both full and quarter APL output and selected **APL output 0** under a new protocol. This is an explicit simulator intervention, not a revised claim that biological APL should be silenced. [Measured links](../associative-learning.md#measured-links-and-declared-interventions).

**Biology.** APL is a non-spiking inhibitory neuron with spatially localized activity and inhibition. One whole-cell activity variable cannot represent all of that local computation. The primary study measures localized responses; it does not prescribe a universal 0.25 gain for a spiking simulator. [Amin et al. 2020](https://elifesciences.org/articles/56954).

**Dataset.** The retained graph contains `APL_R` (body 10540) and `APL_L` (body 10977), both labeled GABA. Together they receive 234,025 input contacts, including 210,352 from KCs. These are aggregate neuron-pair contact counts, not reconstructed electrical compartments. [Target aggregates](data/atlas.json), [identities](identities.md).

**Implementation.** APL uses the same spiking LIF update as other cells. The reward constructor scales **all outgoing APL weights** by 0.25, including its connections to MBONs, after the global scale and target-cell input scaling. That is a coarse gain intervention; graded release, spatial attenuation and local voltage propagation are not implemented. [Scaling functions](../../bet36fly/reward_encoder.py), [constructor](../../bet36fly/reward_protocol.py).

The schema-3 diagnostic found the unscaled spiking proxy overwhelming the MBON11 response: one recorded trial attributed +2,808 mV·spikes to KC input and −4,703 to APL input. These are that diagnostic's integrated model-drive quantities, not measured physiological voltages. Reducing APL output helped restore usable readout responses. [Original sweep record](../../docs/evidence/reward-v3-summary.md).

Keep the accepted 0.25 gain when reproducing the legacy diagnostic. If a future task replaces the proxy with local graded inhibition, it needs its own dynamics specification and experiment identity, compartment-level observations, and comparison against the fixed reference. A successful gain sweep has not already performed that biological validation.

[Cell atlas](index.md) · [Learning contract](../learning-rule.md)
