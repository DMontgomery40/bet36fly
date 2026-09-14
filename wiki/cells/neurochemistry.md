---
type: model-boundary
updated: 2026-09-14
status: implementation-audited
---
# Transmitters, receptors, glia, and unmodeled cell biology

The table below describes the **legacy reward kernel**. The separate associative engine also lacks receptor kinetics, local dopamine concentration, glia and consolidation; it adds [dopamine-gated recovery toward resting gain](../continual-learning.md) on inactive eligible synapses. That tested engineering recovery is not a molecular homeostasis model. Its traces use 1,000 ms rather than the legacy 500 ms, and APL outgoing weights are zero rather than quarter-scaled. [Current state contract](../associative-learning.md).

This is an inventory of what the code represents, not a claim that excluded biology is irrelevant or unavailable to future models. The official release provides neuron annotations and aggregate transmitter predictions, plus separate synaptic-location and transmitter resources. An anatomical label does not supply the numerical dynamics of this simulator. [MaleCNS download schema](https://male-cns.janelia.org/download/).

| Component | Implemented here | Boundary |
| --- | --- | --- |
| Fast transmitter sign | ACh positive; GABA, glutamate and histamine negative; uncertain cases positive | One presynaptic sign per cell, independent of postsynaptic receptor |
| Dopamine | Reward engine suppresses pure-dopamine fast output and uses selected DAN spikes in an update rule | No dopamine concentration field, release/clearance kinetics or receptor binding |
| Other modulators / mixed labels | Retained topology and importer sign policy | No separate octopamine, serotonin or cotransmitter learning system in the inspected reward code |
| APL | Two uniform spiking cells with scaled outgoing weights | Local graded inhibition absent |
| KCs / MBONs | Uniform LIF states, source-specific topology and selected gains | Subtype-specific intrinsic physiology and dendritic compartments absent |
| Receptors and intracellular signaling | No implemented receptor state in the native reward kernel | Label fields are not a DopR1/DopR2 biochemical simulation |
| Glia | Excluded by neuronal retention policy | No glial homeostasis, metabolic support or glial signaling model |
| Memory | Gains persist between trials; electrical state and traces reset | No demonstrated consolidation, structural remodeling or long-term homeostatic mechanism |

Implementation sources: [graph importer](../../bet36fly/connectome.py), [reward constructor](../../bet36fly/reward_protocol.py), [native engine](../../bet36fly/reward_lif.cpp). The manifest's 3,718 uncertain-sign neurons refer to the base graph. The reward engine's subsequent dopamine-zeroing policy is another operation, not a correction of those source labels.

Handler et al. measured receptor-dependent differences in timing-sensitive depression and potentiation. That supports taking temporal order seriously; it does not validate our 500 ms event traces as those receptor pathways. [Handler et al. 2019](https://pubmed.ncbi.nlm.nih.gov/31230716/). Bennett et al. explicitly modeled feedback-generated reinforcement prediction errors; the presence of MBON→DAN anatomical edges here does not establish that their functional computation emerges automatically. [Bennett et al. 2021](https://www.nature.com/articles/s41467-021-22592-4).

The whole retained graph includes other brain and VNC populations, but retaining and updating them is not evidence that every population contributes causally to the sports readout. A future cell-specific ablation needs its own defined scope and experiment identity.

[Cell atlas](index.md) · [Learning contract](../learning-rule.md)
