---
type: concept
updated: 2026-09-12
status: researched
---

# Flyhard: internal connectome learning with causal body contact

> Research snapshot: 2026-09-11 America/Denver (retrieved 2026-09-12 UTC). Public source inspection; no training jobs, physical trials, or independent replay performed.

## Why this project is especially relevant

[Flyhard](https://github.com/MarkUnthank/flyhard) is the strongest inspected community example here of learning parameters **inside** a MaleCNS-derived graph while freezing engineered sensory and motor interfaces. It is a steering-skill experiment in a simulated supported fly body; it does not yet establish autonomous visual driving or Microduck locomotion.

## Source inspection: where learning resides

At inspected commit `bad2131a35518944834531f53be004e9f1b9eecb`, [motor_policy.py](https://github.com/MarkUnthank/flyhard/blob/bad2131a35518944834531f53be004e9f1b9eecb/src/flyhard/motor_policy.py) registers sensory IDs, feature assignments, input signs, output projection, neutral pose, and action scales as buffers. `WheelPolicy.core` is a `SparseConnectome`. No separate MLP motor actor appears in this policy class.

The policy constructs features from requested angle, its square, measured wheel angle, and normalized joint positions. It injects them into selected neurons and runs four graph updates. Importantly, state is reset to zero on every control decision: this pilot is a memoryless task computation despite using recurrent graph updates internally. A fixed random motor projection and tanh generate seven foreleg targets. This is an engineered interface, not a natural sensory/motor reconstruction.

[connectome.py](https://github.com/MarkUnthank/flyhard/blob/bad2131a35518944834531f53be004e9f1b9eecb/src/flyhard/connectome.py) stores immutable CSR adjacency and normalized contact counts as buffers. Edge gains and per-neuron leaks are `nn.Parameter`s. Gains remain positive and bounded; state is signed. The code explicitly declines transmitter/receptor realism. Its custom first-order sparse backward computes edge derivatives in chunks, avoiding the dense intermediate described in the development report. These are directly inspected implementation facts, not inferred from a video.

## Reported pilot result and scope

The [September 9 pilot report](https://github.com/MarkUnthank/flyhard/blob/main/docs/pilot-2026-09-09.md) retains 165,122 traced neurons and 25,563,197 neuron-pair edges. Frozen mappings use 6,365 sensory and 708 motor neurons. Training used physically executed inverse-kinematics demonstrations; evaluation runs without the teacher. One trained seed passed 100/100 held-out angle targets versus 0/100 before training after 600 optimizer updates; peak training allocation was about 3 GB and optimizer work about 186 seconds on an A6000.

The held-out angles lie inside the training range. The result is interpolation of requested stationary steering, not general driving. A supported thorax and explicit forefoot grip assist the body. Replication across training seeds and conventional/shuffled-topology comparisons remain necessary. The report's original publication/connected-CARLA status is historical and superseded by the current public repository and later report.

## What the later CARLA demonstration adds

The [connected-steering report](https://github.com/MarkUnthank/flyhard/blob/main/docs/carla-video-2026-09-09.md) takes the unchanged checkpoint into a 24-second instructed sequence. Seven joint targets move the physical leg; an assisted grip moves a passive wheel; measured wheel angle determines CARLA steering. Speed and requested turns are scripted. Disabling grip reduces the steering response by more than 99.98%, supplying intervention evidence for the body-to-wheel link.

Recorded neural decisions, body states, and CARLA frames share a checked clock. The supported cockpit does not receive vehicle acceleration forces, and no learned pedal or visual navigation participates. The reported 82.9-second capture duration includes loading/recording and is not an end-to-end driving-training estimate. This is a meaningful extension of the stationary skill without changing what was learned.

## What transfers conceptually to Microduck

A fresh experiment can borrow the discipline: fixed declared interfaces; explicitly trainable graph internals; pre/post learning comparison with identical interfaces; joint targets entering actual body physics; contact interventions; source/data/checkpoint identity; and separate presentation versus model-derived activity. The seven-joint supported steering task itself does not transfer as a walking policy.

A critical next comparison is whether anatomical topology contributes beyond parameter count, sparse connectivity, and optimizer choices. A shuffled graph and a matched conventional controller could answer that. Neither improved loss nor a successful physical wheel sequence alone answers it.

## Reproducibility and remaining unknowns

Original code is MIT, while third-party data/body/CARLA assets keep separate terms. Large graphs, checkpoints, and recordings are excluded from Git, so public source availability does not by itself guarantee immediate replay of the exact published artifact. Inspect [reproduction instructions](https://github.com/MarkUnthank/flyhard/blob/main/docs/reproduce.md) and [third-party provenance](https://github.com/MarkUnthank/flyhard/blob/main/THIRD_PARTY.md) before assuming an artifact is downloadable. No checkpoint restoration or paid GPU execution was attempted here.


---
[Community index](index.md) · [Source ledger](sources.md) · [Main wiki](../index.md)

Cross-topic: [training and deployment roles](../synthesis/training-and-deployment.md), [brain-body interface](../connectome/brain-body-interface.md), [GPU selection](../compute/gpu-selection.md).
