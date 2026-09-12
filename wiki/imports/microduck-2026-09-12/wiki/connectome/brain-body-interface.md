---
type: research-note
updated: 2026-09-12
status: researched
---

# Contract: MaleCNS controls Microduck as its body

[Connectome index](index.md) · [Source graph](malecns-release.md) · [Embodiment precedents](embodiment-research.md) · [Sources](sources.md)

**Status: proposed architecture and evaluation contract.** This page states project deductions and future acceptance criteria, not experiments already performed. It preserves the user's objective: a fresh fly nervous system learns to operate Microduck, using real NVIDIA GPUs for training, with explicit control authority when the systems are coupled at execution time. Both duck body skills and the fly network may require GPU training; staged, joint, and hierarchical designs remain research choices.

## The causal path

At a control step, Microduck supplies observation `o[t]`. A declared sensory adapter injects signals into chosen anatomical populations. Recurrent state evolves on the retained MaleCNS graph. A declared readout converts output-population state into bounded actuator commands. The body evolves, producing `o[t+1]` and a learning signal.

```text
Microduck observations -> sensory adapter -> MaleCNS recurrent state
    -> output population -> actuator adapter -> Microduck dynamics
    -> next observations and learning feedback
```

The graph must have meaningful causal authority in the coupled deployment path. A trained duck locomotion controller can provide body skills while the fly governs higher-level actions. Alternatively the fly can supply lower-level outputs directly. Saving neural activity beside an independent controller does not establish either. A fly used solely as an offline teacher is distinct from runtime embodiment. Demonstrations initializing the graph, separate body-skill training, and joint fine-tuning are all legitimate research choices to compare; [FlyGM](embodiment-research.md) informs one direction of teacher transfer.

## Anatomical ports need a real specification

The existing [importer](../../flybrain/connectome.py) calls the 686 `ALPN` cells its `sensory_ports`. That is a specific annotated class selected by equality, not a comprehensive collection of MaleCNS sensory neurons. The count cannot validate a multimodal robot interface. Likewise, 97 mushroom-body outputs are not a complete map of the VNC motor population.

The next implementation needs a versioned port table with source neuron IDs, source labels, robot channel, encoder/readout rule, normalization, units, and justification. “Input” must distinguish direct sensory neurons, projection neurons, and abstract learned injection sites. “Output” must distinguish descending neurons, VNC interneurons, and motor neurons. These distinctions survive even if an engineered mapping is ultimately chosen.

| Robot channel family | Required definition before a training claim |
|---|---|
| Camera observations | Actual camera geometry, frame timing, preprocessing, and receiving populations; an image cannot simply be labeled smell. |
| Joint/body feedback | Position, velocity, orientation, contact and available sensor semantics, including units and delays. |
| Task cues | What the robot can observe versus privileged simulator state; whether cues are labels, detections, or raw observations. |
| Actuator commands | Real action dimensions, limits, rates, and control mode; which neural states determine each output. |
| Reward/modulation | The implemented learning signal and affected parameters; do not equate an arbitrary scalar reward with measured dopamine physiology. |

This page does not assert which sensors or joints Microduck has. Those belong to the verified robot specification. A neural mapping should follow that specification, not invent hardware to match fly anatomy.

## Keep the VNC computationally relevant

MaleCNS's [continuous anatomical coverage](malecns-release.md) creates an opportunity to model communication through the brain and VNC. Merely loading every node into memory does not show that the VNC matters. Choose input and output populations so relevant source-to-actuator paths traverse the intended network; check reachability, latency, normalization, and the effect of perturbing those pathways.

A bounded actuator adapter can translate a neural output into a motor target, and a learned body controller can translate fly commands into coordinated motion. Record which functions each owns and test how much performance it achieves with constant neural input. If a separate policy recognizes goals, plans routes, and completes tasks without fly decisions, report its authority rather than attributing its performance to the fly.

## Dynamics and learning are separate commitments

The source provides structure; the executing model supplies an update law. Document its state per neuron, integration interval, recurrent steps per robot step, leak/gain rules, numerical precision, sign handling, and parameter initialization. The local [manifest](../../data/brain/manifest.json) already acknowledges unvalidated dynamics. Preserve that disclosure alongside later performance results.

Choose a plasticity scope explicitly. The present importer stores a 61,210-edge Kenyon-cell-to-MBON submatrix, but that choice alone neither proves learning nor establishes whole-body control. If training changes only a readout, say so. If it changes neuron gains, adapters, or existing synapse strengths, say so. If it introduces connections absent from the source, describe the architectural departure rather than quietly continuing to call the operator exact.

Source fidelity and trainability can be measured independently: source ID retention, edge support retention, parameter changes, and behavioral adaptation. This allows an honest claim such as “all retained anatomical edges are present; gains and body adapters were learned” without claiming that every parameter is a biological measurement.

## Future acceptance evidence

These tests are proposed research controls, not checks performed during wiki authoring:

| Evidence | What it resolves |
|---|---|
| Raw hashes, retained IDs, source/excluded counts, graph orientation check | The intended released nervous system was loaded correctly. |
| Sensor-to-neuron-to-action trace with timestamps | The brain actually participates in the closed loop. |
| Constant/clamped neural state and disconnected readout controls | Behavior is not generated independently by the adapter. |
| Targeted brain/VNC perturbations, recovery after removing the perturbation | Neural contributions are causal and reproducible. |
| Degree-preserving rewiring and matched-budget learned baselines | Whether anatomy helps, beyond model size and optimizer budget. |
| New seeds, held-out layouts and changed body conditions | Task learning generalizes beyond a single successful clip. |
| GPU identity, CUDA device placement, utilization and peak-memory receipts | Training actually executed on the claimed NVIDIA hardware. |
| Checkpoint reload reproducing behavior | The result is a saved controller, not an unrecoverable live state. |

Ablations and baselines must be reported fairly: perturbation severity and capacity can themselves change performance. Loss of function after catastrophic deletion proves dependence, but not uniquely biological computation. Stronger conclusions require matched controls.

## What success would mean

The first meaningful result is a reproducible controller whose task performance improves through interaction with Microduck's dynamics, whose action path still runs through the MaleCNS-derived network, and whose contribution survives causal scrutiny. Physical hardware validation is a further evidence tier beyond simulator control. Native fly physiology, broad animal intelligence, and identity preservation are separate hypotheses, not prerequisites for honestly completing this robot experiment.

## Training versus deployment ownership

| Phase | Learner or actor | Evidence to record |
|---|---|---|
| Duck body-skill training | A body controller learns Microduck dynamics on real NVIDIA GPUs. | Observations, actions, reward, device receipts, checkpoints, skills acquired. |
| Fly-controller training | The MaleCNS-derived network learns its control role on real NVIDIA GPUs. | Inputs, outputs, trainable parameters, curriculum, feedback and checkpoints. |
| Coupling or joint refinement | One or both controllers adapt through a declared interface. | Frozen versus trainable components, command semantics, end-to-end feedback. |
| Deployment | Fly and body controllers execute their assigned roles. | Who chooses goals, who stabilizes motion, inference device and latency, causal ablations. |

A hierarchical result can be successful embodiment if the fly has meaningful control and receives consequential feedback. End-to-end direct torque control is an alternative hypothesis, not an assumed requirement. Training compute location also need not equal deployment compute location.
