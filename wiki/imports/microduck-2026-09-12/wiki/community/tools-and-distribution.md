---
type: concept
updated: 2026-09-12
status: researched
---

# Community tooling and policy distribution

> Research snapshot: 2026-09-11 America/Denver (retrieved 2026-09-12 UTC). Public source inspection; no training jobs, physical trials, or independent replay performed.

## Discover, then inspect the original artifact

[Awesome Microduck](https://github.com/joeynyc/awesome-microduck) is a useful community-maintained discovery index covering policies, simulators, agent tools, hardware accessories, and benchmarks. It also maintains machine-readable policy and revocation registries. Its role here is navigation: a directory's summary can lag the linked implementation, particularly during rapid upstream development.

The registry design creates an important operational relationship: policy descriptors and revocations should be resolved at the same revision. A consumer must distinguish a listed policy from one revoked or superseded later. Directory membership is not a physical-safety or model-quality endorsement. [Registry source](https://github.com/joeynyc/awesome-microduck/blob/main/policies.json) and [revocations](https://github.com/joeynyc/awesome-microduck/blob/main/revocations.json).

## Three kinds of tool that should not be confused

| Tool layer | Source-backed example | What it contributes |
|---|---|---|
| Simulation/inference plant | [Official browser simulator source](https://huggingface.co/spaces/pollen-robotics/microduck-simulator/blob/main/README.md) | MuJoCo/WASM physics and policy execution in a browser |
| Agent transport/API | [joeynyc/microduck-mcp](https://github.com/joeynyc/microduck-mcp) | Common agent-facing tools with mock, simulator, and hardware-oriented transport options |
| High-level skill planning | [quackd](https://github.com/rokbenko/quackd) | Language-model goal decomposition and sequencing of robot skills |
| Human teleoperation | [specs-microduck](https://github.com/kgediya/specs-microduck) | Gesture-to-command mapping and simulator bridge |

The MCP server exposes control to external agents; it does not mean the low-level actor learns during the interaction. Likewise, a language model selecting a kick, roll, or walk is a planner around existing motor competence. For this project's anatomical-core question, those tools can operate an experiment or provide instructions without being counted as the trained neural controller. [MCP README](https://github.com/joeynyc/microduck-mcp), [quackd README](https://github.com/rokbenko/quackd).

The Spectacles project defines continuous velocity/jaw packets and discrete action events, with a synthetic gesture streamer for testing without the wearable. Its reported routine triggers walking, turns, kicks, rolls, and roller-mode switching. This is interface composition, not evidence of a new learned policy. [Protocol and test mode](https://github.com/kgediya/specs-microduck).

## What a reusable community release should contain

This is a proposed evidence contract, informed by the [policy examples](microduck-ecosystem.md), not a claim that every listed repository already meets it:

1. **Identity:** source revision, environment/model asset hashes, training configuration, checkpoint selection rule, and license scope.
2. **Learning:** optimizer state and explicit trainable parameter list; specify whether training touched the connectome, an adapter, a critic, a conventional actor, or several parts.
3. **Runtime semantics:** normalization, joint order, action scale, command meanings, frequency, hidden state, reset boundaries, and entry/recovery behavior.
4. **Physical assumptions:** contact model, passive versus actuated accessories, external support, grasp constraints, latency, and sensor availability.
5. **Evaluation:** multiple held-out episodes with first-failure accounting; comparison to an untrained initialization and appropriate baselines; preserve failed runs.
6. **Transfer scope:** software parity, closed-loop simulation, device timing, and physical trials recorded separately.

## Why one simulator can be a misleading comparison

A controller may reproduce in an exported ONNX path but fail in the training viewer, as [Collision Flamingo II](https://huggingface.co/Teethyfish/microduck-collision-flamingo-ii) discloses. This can arise from differences in observations, resets, action handling, or physics; the source leaves the particular cause unresolved. A fair connectome-versus-MLP experiment must keep these surfaces aligned before assigning performance differences to architecture.

## Open questions and refresh priorities

Upstream policy-channel state should be read directly from the current runtime before designing an installer; the directory still includes branch-oriented status prose. Hardware transports require actual device acceptance. Community package version changes can also alter inference/reset behavior without changing a model filename. For now, the strongest reusable assets are source, contracts, and simulator evidence, not claims of universal plug-and-play compatibility.


---
[Community index](index.md) · [Source ledger](sources.md) · [Main wiki](../index.md)
