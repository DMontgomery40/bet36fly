---
type: synthesis
updated: 2026-09-12
status: research-complete-experiments-pending
---
# What the research changes

The project is to train both duck body control and a fresh MaleCNS fly controller on real GPUs, then embody the fly through Microduck. The two training problems interact, but they are not interchangeable. A trained gait can serve the fly's commands; a direct graph actor can instead learn actuator control; a hybrid can combine them. The research establishes useful precedents and constraints without pretending that this project's architecture has already won an experiment. See the [training and deployment role map](synthesis/training-and-deployment.md).

## Compute and organizations

NVIDIA announced a definitive agreement to acquire Hugging Face. The inspected SEC filing describes an expected first-half-2027 closing subject to conditions. This is a real recent development, but does not establish merged credentials, billing, or credits. Current Hugging Face documentation supports browser device authorization and web Jobs creation; absence of a cached local token was not sufficient reason to demand token entry. The [compute section](compute/index.md) separates transaction status, account workflows, hardware requirements, and a bounded run contract. Its [ownership page](compute/ownership.md) links the announcement and filing; its [HF page](compute/hugging-face.md) links current authentication and Jobs documentation.

## The duck has several distinct software surfaces

Microduck's [trainer](microduck/trainer.md) uses GPU-accelerated MuJoCo/Warp through mjlab. The [browser simulator](microduck/simulators.md), GPU training viewer, and daemon-backed body simulator answer different questions. Visible walking is evidence of a running policy, not evidence of the selected fly checkpoint learning. The [production runtime](microduck/runtime.md) already supports a specific explicit-state LSTM contract, which is useful but does not make an arbitrary sparse neural graph deployable unchanged. These findings are grounded in pinned upstream code and licensed snapshots linked from [Microduck sources](microduck/sources.md).

## The connectome and its controller are different artifacts

[MaleCNS](connectome/malecns-release.md) supplies anatomical structure and annotations. Dynamics, engineered sensory inputs, motor decoding, learning rules, and embodiment remain modeling choices. Release availability must be distinguished from September paper and publicity dates. The [embodiment review](connectome/embodiment-research.md) compares Google/academic work and embodied demonstrations, including which systems learn graph parameters and which use engineered body support. The [brain-body interface](connectome/brain-body-interface.md) explains why this repository's ALPN selection is not yet a complete mapping for a robot's camera, inertial sensing, contacts, and actions.

## Community demonstrations are useful when control authority is explicit

The [community map](community/index.md) covers duck and fly projects separately and together. Microfly's functioning locomotion path combines fly-derived commands with a learned conventional body policy; its untrained direct-joint path is a different condition. Flyhard reports trainable internal graph parameters in a bounded driving experiment. Flybywire has version-dependent observer and limited-assist descriptions. These are concrete precedents, not proof that this project has learned pickup. Read the [claims comparison](community/claims-map.md), [joint projects](community/joint-projects.md), and [Flyhard deep dive](community/flyhard.md) for source-specific boundaries.

## Object retrieval requires its own evidence

A ground-pick reward objective and a synthetic payload do not demonstrate retaining a loose hazardous object or depositing it through a narrow opening. The [mechanics review](microduck/pickup-mechanics.md) identifies the contact, jaw, and geometry questions. The proposed [evaluation protocol](synthesis/hazard-evaluation.md) records actual scene outcomes separately from rewards, with held-out objects, container geometry, stage failures, and uncertainty. This protocol has not been executed.

## What exists here now

This pass produced a current research wiki, source records, pinned upstream excerpts, and a [verification record](verification.md). Before the research pivot, the local graph builder's path bug was repaired and the fresh anatomical graph was built; those actions are not GPU training. No paid GPU training was launched in this research pass. Architecture selection, measured GPU capacity, trained checkpoints, end-to-end pickup results, and physical deployment remain experimental work listed in [open questions](synthesis/open-questions.md).

[Start page](index.md) · [Maintenance schema](SCHEMA.md) · [Research log](log.md)
