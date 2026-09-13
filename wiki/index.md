---
type: index
updated: 2026-09-13
status: active
---
# BET36FLY: cells, circuits, and learning

Start with the [reassessment](reassessment.md). The current problem is demonstrating specific, controlled learning in the implemented mushroom-body circuit. A usable activity range and changing gains have been demonstrated; useful associative learning has not. This wiki connects individual MaleCNS cells to the code, measured failures, and evidence needed next.

The repair is integrated, but both corrected raw-event and rate-bridge rules fail
the second panel's untaught-home guard. A later fixed-history investigation made
that failure worse; acquisition and reversal have not run. The
[current evidence index](../docs/evidence/reward-mechanism-repair-2026-09-12/index.md)
preserves those results. Dates use UTC; the
[initial workspace record](../docs/evidence/reassessment-2026-09-12/index.md)
remains a dated snapshot.

## Cell reference

| Question | Read |
| --- | --- |
| Which exact cells and synapses are involved? | [Cell atlas](cells/index.md), [individual identities and subtype counts](cells/identities.md) |
| How do sports features reach the circuit? | [ALPN inputs and the glomerular proxy](cells/alpn.md) |
| Which Kenyon cells can learn, and why is the away mask different? | [KC families and synaptic support](cells/kenyon-cells.md) |
| Why did inhibition silence the readout? | [The two APL cells](cells/apl.md) |
| What do PPL101 and PAM12 actually do here? | [Dopamine neurons and teaching channels](cells/dopamine.md) |
| Is MBON09 exclusively γ3? | [MBON identities, compartments, and readout](cells/mbons.md) |
| What about other transmitters, receptors, and glia? | [Cell biology represented and omitted](cells/neurochemistry.md) |

## Mechanism and experiment

- [Current state and what went wrong](reassessment.md)
- [Circuit and learning-rule contract](learning-rule.md)
- [Conditioning, controls, and evidence gates](evidence-gates.md)
- [Community results and what transfers to this experiment](community.md)
- [Primary sources and retrieval limits](sources.md)
- [Maintenance conventions](SCHEMA.md), [change log](log.md), [verification](verification.md)

## Copied Microduck research

All 38 source wiki files, including every fly-specific passage in mixed-topic pages, are preserved byte-for-byte in the [Microduck snapshot](imports/microduck-2026-09-12/README.md). The copy also retains its source records, licensed upstream excerpts, and two local references so its compiled-wiki links resolve. Microduck's originals remain in place. Robot-only context is retained for completeness; it does not define BET36FLY's architecture or authorize training.

Useful entry points: [MaleCNS](imports/microduck-2026-09-12/wiki/connectome/index.md), [embodiment research](imports/microduck-2026-09-12/wiki/connectome/embodiment-research.md), [fly community](imports/microduck-2026-09-12/wiki/community/fly-ecosystem.md), [Flyhard](imports/microduck-2026-09-12/wiki/community/flyhard.md), [Microfly](imports/microduck-2026-09-12/wiki/community/joint-projects.md), [training roles](imports/microduck-2026-09-12/wiki/synthesis/training-and-deployment.md), and [GPU considerations](imports/microduck-2026-09-12/wiki/compute/gpu-selection.md).

Existing project documents remain connected: [model card](../docs/MODEL_CARD.md), [plain-language fly guide](../docs/FLY_GUIDE.md), [reward protocol](../docs/EXPERIMENT_REWARD.md), and [historical measurements](../docs/evidence/reward-v3-summary.md).
