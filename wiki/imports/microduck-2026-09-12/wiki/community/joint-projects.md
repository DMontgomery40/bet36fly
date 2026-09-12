---
type: concept
updated: 2026-09-12
status: researched
---

# Microfly: the existing fly-to-Microduck bridge

> Research snapshot: 2026-09-11 America/Denver (retrieved 2026-09-12 UTC). Public source inspection; no training jobs, physical trials, or independent replay performed.

## What is actually combined

[lvwerra/microfly](https://huggingface.co/spaces/lvwerra/microfly) is a local-browser integration of a fly-connectome model and official Microduck simulation assets. The README identifies **FlyWire FAFB v783**, not MaleCNS: 139,255 neurons and 2,698,236 aggregated directed edges inherited from a pinned FlyBrain revision. The neural weights do not learn. [Source README](https://huggingface.co/spaces/lvwerra/microfly/blob/main/README.md).

Its default control chain is:

```text
virtual scent/light/mechanosensory inputs
 → fixed connectome dynamics
 → engineered neural speed/turn decoder
 → existing trained ONNX walking policy
 → fourteen servo-position targets
 → MuJoCo body and contacts
```

This is a real physical simulation loop, but low-level gait and balance come from the pretrained robot policy. Collecting the banana neither rewards nor trains the fly model. The banana itself has no collision body; proximity handles collection. These implementation boundaries explain what the display can and cannot demonstrate. [README: model, food, and physics](https://huggingface.co/spaces/lvwerra/microfly/blob/main/README.md).

## An explicit second path isolates motor authority

The retained, hidden direct mode bypasses ONNX. It assigns descending neurons to arbitrary opposing pools, converts their rate difference into joint offsets, applies limits, and advances the same physics. That is neural authority over servo positions, not torque/current control, not learned locomotion, and not a biologically established fly-joint mapping. [Direct-mode description](https://huggingface.co/spaces/lvwerra/microfly/blob/main/README.md).

The September 11 [validation report](https://huggingface.co/spaces/lvwerra/microfly/blob/main/VALIDATION.md) reports zero ONNX calls during direct-mode checks and a fall. Default walking tests show actual short physical displacement with the body upright. Synaptic ablation leaves sensory activity while downstream output vanishes; scent reversal changes steering; clearing scent removes commands. These are valuable software/causal checks but not a learned-navigation benchmark. Tests were run by the author; this research pass did not reproduce them.

## Why the distinction matters for this project

There are several legitimate research questions:

- Can a connectome-derived signal choose useful commands for a robot whose gait already exists?
- Can a fresh MaleCNS graph learn the robot's motor competence itself?
- Can separately GPU-trained duck skills and a GPU-trained fly core be coupled into a useful embodied hierarchy, with the training and authority of each component explicit?

Microfly directly addresses the first question as an interactive fixed-weight demo. Its direct path exposes part of the second question's interface, but supplies no training result. Reusing the scene, body plant, or trained walker can accelerate a new experiment. The user explicitly wants real-GPU training of both duck and fly while giving the fly a body; a learned hierarchy is therefore a valid candidate, not disqualified by the presence of a separate gait policy. What Microfly currently lacks for that goal is a trained fly core. Direct joint control and learned hierarchical control remain distinct alternatives to evaluate.

## Useful design ideas to retain

The application keeps physics-derived poses separate from illustration, exposes disconnect and synaptic ablation, resets seeded state, and reports direct-path ONNX invocation counts. Its anatomical display uses real representative coordinates, not guaranteed somata or full neuron arbors. The fly inside the head is expressly illustrative animation. Those disclosure patterns are reusable even if the dataset and model are replaced. [README: scientific limitations and validation](https://huggingface.co/spaces/lvwerra/microfly/blob/main/README.md).

Source is distributed as `flyduck-source.zip`; the static Space tree also includes `provenance.json`, connectome data, model assets, and separate licenses. Original application code is Apache-2.0; inherited FlyBrain code is MIT; the tissue mesh is separately GPL-3.0. Original dataset terms remain distinct. [File tree](https://huggingface.co/spaces/lvwerra/microfly/tree/main), [provenance](https://huggingface.co/spaces/lvwerra/microfly/blob/main/provenance.json).

## Open questions

Can the input encoder be rebuilt for actual Microduck sensors rather than idealized scent bearing? What actuator observations belong in the anatomical core, and which belong in a separately trained duck skill? Which neural and decoder states should persist across skill switches, falls, and episode resets? Can an internally trained model learn recovery, pickup, and object contact without an existing gait actor? No answer is supplied by the current bridge. [Flyhard](flyhard.md) suggests an auditable internal-training pattern, while [community robot policies](microduck-ecosystem.md) supply comparators and physical task definitions.


---
[Community index](index.md) · [Source ledger](sources.md) · [Main wiki](../index.md)

Cross-topic: [training and deployment roles](../synthesis/training-and-deployment.md), [brain-body interface](../connectome/brain-body-interface.md), [GPU selection](../compute/gpu-selection.md).
