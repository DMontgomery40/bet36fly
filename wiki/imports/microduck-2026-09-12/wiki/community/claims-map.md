---
type: concept
updated: 2026-09-12
status: researched
---

# Comparison and claims map

> Research snapshot: 2026-09-11 America/Denver (retrieved 2026-09-12 UTC). Public source inspection; no training jobs, physical trials, or independent replay performed.

## Architecture comparison

This table compiles the linked detailed pages; it is not a ranking of overall project quality.

| Project | Anatomical core | Learned component | What reaches the environment | Evidenced scope |
|---|---|---|---|---|
| [Community Microduck RL](microduck-ecosystem.md) | Usually no anatomical core | Conventional robot actor | Joint-position targets | Task-specific simulator evidence; hardware varies and inspected community cards largely say untested |
| [Microfly default](joint-projects.md) | Fixed FlyWire graph | Previously trained separate gait | Speed/turn into ONNX actor | Browser integration, short walking and ablation checks |
| [Microfly direct](joint-projects.md) | Same fixed graph | None | Fourteen joint targets | Direct-path causality; reported fall |
| [Flyhard](flyhard.md) | MaleCNS graph | Internal edge gains/leaks | Seven foreleg targets, physical wheel, CARLA steering | One-seed learned angle interpolation and later instructed driving sequence |
| [DOOMFLY](fly-ecosystem.md) | MaleCNS graph | Small existing-edge plasticity subset | Fixed game-button mapping | Implemented learning experiment; current learning gates failed |
| [Fly64](fly-ecosystem.md) | MaleCNS graph | None | Fixed analog/jump mapping | Recreational closed-loop demo |
| [Flybywire](fly-ecosystem.md) | Frozen MaleCNS graph | Motion readout | Observer output; documented limited yaw profile | Contradictory current prose; no established autonomous-flight benchmark |

## Terms that must carry an explicit qualification

**“Uses a real fly brain.”** The sources provide measured connectivity, not a preserved biological mind or complete physiological state. State equations, synaptic efficacy, sensory encoding, and decoding must still be modeled. Use “connectome-derived computational model” and name the dataset.

**“All neurons.”** State the actual retained population and filtering rule. Flyhard's traced-only count differs from the annotated populations in Doom/Flybywire; Microfly uses a different female-brain dataset entirely. A neuron-pair edge can aggregate many synaptic contacts. Never substitute the edge count for the anatomical synapse count. [Dataset and model boundaries](fly-ecosystem.md), [Flyhard filtering](flyhard.md).

**“Learns.”** Require measured behavioral improvement attributable to changed parameters. Firing neurons, changing weights, repeated episodes, and reward delivery each establish a different intermediate fact. Also identify the location of learning: readout-only, graph-internal, or separate actor. [Doom and Flybywire examples](fly-ecosystem.md).

**“Controls the body.”** Specify command level. Speed commands to an existing gait, servo-position targets, muscle activation, and electrical motor commands are different interfaces. [Microfly's two paths](joint-projects.md) expose this distinction unusually clearly.

**“Sim-to-real ready.”** Export equivalence and simulator success are prerequisite evidence, not device timing or physical transfer. Recurrent state, clamps, command semantics, and contact assumptions can invalidate a nominally compatible shape. [Deployment examples](microduck-ecosystem.md).

## Proposed experiment that answers the user's intended question

The user's clarified objective is **real-GPU training of both the duck and the fly, while giving the fly a body**. The missing result is a validated coupling between learned duck skills and a learned fresh MaleCNS-derived core, or a direct learned anatomical motor controller, with their roles and online authority explicit. Hierarchy is a candidate architecture, not a violation of the goal. This is a research specification, not a result reported by any inspected source.

A useful minimum experiment would freeze the physical plant and compare: initialized core, trained core, matched shuffled connectivity, and a conventional actor. Log the model's actual action path and trainable parameter identities. Use held-out commands, resets, perturbations, and contact arrangements with identical evaluation rules. Check a core-disabled intervention to exclude any unintended bypass. If a critic or teacher is used only in training, demonstrate its absence from evaluation actions and disclose its role. If a learned duck policy is intentionally retained online, measure that hierarchy honestly: which core parameters learned, which commands the fly controls, which body skills learned separately, and which couplings are fixed or learned.

For fetch/drop, do not collapse locomotion, target sensing, grasp acquisition, carrying, and release into a single headline. For hazard patrol, identify which sensor actually observes the hazard and whether the actor has privileged simulator state. A graphical banana target or scripted task sequence can be useful scaffolding but changes the autonomy claim if it supplies otherwise unavailable information.

## Open questions

What is the narrow first skill, and does it need temporal neural state? Which anatomical neurons are valid interface candidates? What learned parameters remain biologically motivated versus simply engineering choices? Does anatomical topology outperform a fair control? Can learned behavior survive realistic contacts and the deployed observation/action contract? These are executable research questions; community popularity does not answer them.


---
[Community index](index.md) · [Source ledger](sources.md) · [Main wiki](../index.md)

Cross-topic: [training and deployment roles](../synthesis/training-and-deployment.md), [brain-body interface](../connectome/brain-body-interface.md), [GPU selection](../compute/gpu-selection.md).
