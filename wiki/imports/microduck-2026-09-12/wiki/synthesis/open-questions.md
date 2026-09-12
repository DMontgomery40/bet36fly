---
type: research-backlog
updated: 2026-09-12
status: active
---
# Open questions and evidence needed next

These are concrete research gaps, not questions being handed back to the user to solve. The current task is a source-backed wiki; subsequent experiments should resolve them in a bounded order.

| Question | Why it changes the implementation | Evidence to obtain |
|---|---|---|
| Which hierarchical, direct, or hybrid control interface best trains both systems? | Determines actions, feedback, training objectives, and deployment authority | Matched small GPU experiments with body-only/fly-frozen controls; [role map](training-and-deployment.md) |
| Which MaleCNS sensory/motor populations map to duck observations and actions? | Existing 686 ALPN selection is insufficient as a complete sensorimotor specification | Annotation audit, graph connectivity, explicit engineered mapping; [interface](../connectome/brain-body-interface.md) |
| Which neural dynamics and trainable parameters provide useful learning? | LIF, graded models, and message-passing networks differ in physiology, gradients, and runtime cost | Reproducible learning curves, numerical tests, graph-causality controls; [research precedents](../connectome/embodiment-research.md) |
| Can the selected jaw model retain each object class? | No optimizer can repair missing jaw contact or unreachable geometry | Exact MJCF contact audit, physical settle/lift tests, then hardware dimensions; [pickup](../microduck/pickup-mechanics.md) |
| What container envelope is feasible? | A bottle rim may require poses the beak cannot achieve | Reachability/contact measurement against selected aperture/rim geometry |
| What perception is needed, and where does it run? | Actor observation width and deployment sensor limits constrain detector use | Real label taxonomy, synthetic/real split, precision/recall/localization by class and pose |
| What GPU and batch size fit the full learning stack? | Body-policy defaults do not size a full recurrent graph | Peak VRAM, steps/second, utilization and learning progress on allocated hardware; [GPU selection](../compute/gpu-selection.md) |
| Which authenticated browser path launches and shows the actual run? | Docs support modern HF/Brev web workflows, but local UI access failed | Fresh Computer Use connection and account-specific form inspection, visible viewer paired to run |
| Where can the trained fly execute at physical deployment? | Full graph latency may require a different placement from training | Board and remote end-to-end timings, disconnect behavior; [runtime](../microduck/runtime.md) |
| Does a reported community capability survive source/revision reconciliation? | README, appendices, and clips sometimes describe different versions | Pin revisions, reproduce the exact condition, preserve contradictory reports; [community](../community/index.md) |

## Resolved corrections

- NVIDIA's acquisition agreement is real and recent; the inspected SEC filing forecasts closing in the first half of 2027. Do not collapse agreement, closing, and account integration. [Ownership](../compute/ownership.md).
- Current HF documentation includes browser device authorization and Jobs web creation. Missing local cached credentials did not prove that token pasting was necessary. [HF workflows](../compute/hugging-face.md).
- MaleCNS v1.0 availability and the September paper/Google publicity are different dates. [Release chronology](../connectome/malecns-release.md).
- The successful microfly walking path and its untrained direct mode have different control architectures; neither currently demonstrates training both systems for this project. [Community](../community/index.md).
- Microduck has both a daemon-backed simulator and explicit-state LSTM runtime support. Those do not automatically support an arbitrary sparse CNS actor. [Simulators](../microduck/simulators.md), [runtime](../microduck/runtime.md).

## Source contradictions to keep visible

The compute section records conflicting billing granularity language and mutable device tables. The connectome section records weighted/unweighted descriptions and code-availability claims for FlyGM, as well as release-date discrepancies. Community pages preserve differences between default observer-only operation and limited-assist documentation where found. These are reasons to verify specific claims at a pinned revision, not to discard an otherwise useful source wholesale.

[Wiki](../index.md) · [Overview](../overview.md) · [Evaluation](hazard-evaluation.md).
