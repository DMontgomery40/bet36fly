---
type: index
updated: 2026-09-12
status: researched
---

# Community ecosystem: what can actually be reused

> Research snapshot: 2026-09-11 America/Denver (retrieved 2026-09-12 UTC). Public source inspection; no training jobs, physical trials, or independent replay performed.

The useful ecosystem consists of several different things: trained robot policies, tools that invoke those policies, simulations using measured fly wiring, and experiments that train parameters inside that wiring. Keeping these categories separate makes the community useful for a fresh MaleCNS controller.

## Reading paths

- [Microduck policies and accessories](microduck-ecosystem.md): learned skills, unusual contact tasks, manifests, and deployment limits.
- [Community tools and distribution](tools-and-distribution.md): simulators, agent interfaces, model registries, and reproducibility contracts.
- [Fly community experiments](fly-ecosystem.md): Doom, Mario, drone observation, and the distinction between neural activity and learned competence.
- [Microfly and the joint architecture](joint-projects.md): the existing fly-to-Microduck bridge and exactly where the robot's competence resides.
- [Flyhard: trainable core and physical contact](flyhard.md): the closest inspected example of learning inside a MaleCNS graph while maintaining a causal body interface.
- [Comparison and claims map](claims-map.md): evidence categories and the missing experiment for this project.
- [Sources and refresh priorities](sources.md): primary-source ledger and unresolved contradictions.

## Three consequential findings

**Microfly is an integration reference, not a ready-made MaleCNS learner.** Its source describes a fixed FlyWire-derived graph feeding commands to an existing Microduck gait. Its direct motor experiment bypasses that gait but falls in the published test. [Architecture](joint-projects.md).

**Flyhard provides a more relevant training pattern.** The inspected implementation registers the sensory projection and output decoder as buffers while graph gains and leaks are trainable parameters. That is a concrete way to distinguish learning inside the connectome from fitting only a readout. [Code and evidence](flyhard.md).

**Community demonstrations are heterogeneous and rapidly revised.** Doom's live plasticity experiment reports failed learning gates; Mario explicitly has no learning; Flybywire has conflicting observer-only and limited-yaw-assist documentation. These are separate states, not interchangeable examples of autonomous fly intelligence. [Details](fly-ecosystem.md).

## Scope and maintenance

This is a compiled research wiki: each page resolves a question, links related concepts, records source boundaries, and preserves open questions. It is not an exhaustive popularity ranking. Model cards are authors' experimental reports, not independent certification. Recheck exact revisions and the complete runtime contract before adopting an artifact; neither a compelling clip nor an ONNX suffix establishes transfer to a physical robot.

The current unresolved question is how real-GPU training of both the duck skills and a fresh MaleCNS model can produce a coupled embodied controller under the real observation, actuator, and contact constraints. None of the inspected community sources establishes that complete result. The [claims map](claims-map.md) explains the experiments needed to discriminate it from simpler alternatives.


---
[Community index](index.md) · [Source ledger](sources.md) · [Main wiki](../index.md)
