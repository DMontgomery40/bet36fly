---
type: concept
updated: 2026-09-12
status: researched
---

# Fly community: games, observers, and learning claims

> Research snapshot: 2026-09-11 America/Denver (retrieved 2026-09-12 UTC). Public source inspection; no training jobs, physical trials, or independent replay performed.

## The classification question

For every demo, ask four questions: which anatomical dataset; what signals are engineered into it; which parameters learn; and what commands can leave it? The same animated neural view can accompany a fixed controller, a learned readout, internal plasticity, or a completely separate action policy. See the [claims map](claims-map.md).

## DOOMFLY: plasticity present, survival learning unproven

The [DOOMFLY repository](https://github.com/nftechie/doomfly) reports 166,700 retained MaleCNS neurons and 25,582,938 neuron-pair connections. Actual ViZDoom frames stimulate modeled R1–R6 and R8 inputs. Fixed population-to-button assignments produce turning, motion, and firing. Damage supplies artificial reinforcement to PPL101 cells; the current experiment modifies 4,184 existing KC-to-MBON11 connections.

The current README explicitly reports failure of v6 visual, conditioning, and survival gates. Weight changes and long individual rounds are not demonstrated learning. This negative result is valuable: it distinguishes an implemented learning rule from an improvement caused by that rule. Original code is MIT; the game and third-party components retain separate terms. [Current project status](https://github.com/nftechie/doomfly).

The [older baseline README](https://github.com/nftechie/doomfly/blob/main/doom/README.md) is labeled fixed-weight historical material and points to the later live experiment. It also records a corrected refractory-event problem and treats earlier kill counts as legacy results. Do not use the old no-plasticity statement as the current architecture, or old scores as current validation.

## Fly64 / Mario: a closed loop without training

[ornata/fly](https://github.com/ornata/fly) connects a MaleCNS model to a modified Super Mario 64 build. Six small hidden views provide a synthetic retinal sphere from Mario's location; selected neural populations drive forward motion, steering, and jump requests. Background drive and noise also affect activity. The project's README says there is no reward, training, or star-collection objective, and no fly limbs/muscles. It was tested on one M2 MacBook and requires a user-provided game ROM.

This establishes an interesting sensory-to-controller engineering demo, not learned game competence. A jump request is also not proof that the game accepted it or Mario left the ground. The author labels the code an unreviewed, recreational experiment. [Fly64 methods and limitations](https://github.com/ornata/fly).

## Flybywire: a source contradiction worth preserving

The [README](https://github.com/Flybywirerh/Flybywire) describes an M-series Mac workspace displaying drone camera input alongside full MaleCNS activity, with the neural path observation-only and supervised flight in a separate process. It reports Metal/WebGPU support and approximate dynamics, not biological reconstruction.

The [brain/training document](https://github.com/Flybywirerh/Flybywire/blob/main/docs/BRAIN_AND_TRAINING.md) says the graph stays frozen while a quadratic T4/T5 readout learns image-motion direction. Early recording holdout accuracy was 0.375 versus 0.500 for a synthetic-only baseline. Later September 11 additions report 0.70 on another mixed setup and describe `brain-yaw-assist-v2`: clamped ±6 protocol-unit yaw bias through shared memory into the flight process.

**Evidence state:** default observer-only claims and a documented limited-assist profile coexist. The inspected prose cannot settle which profile is enabled on a current host or establish controlled physical efficacy. Do not report either broad autonomous flight or an unconditional absence of any neural-to-motor route. The dataset, frozen core, learned readout, and bounded downstream assistance must be distinguished.

## FlyWire-derived simulations are a separate lineage

[snedea/flybrain](https://github.com/snedea/flybrain) describes 139,255 FlyWire FAFB v783 neurons and an aggregated approximately 2.7-million-edge LIF simulation in a browser worker. It derives from an earlier worm simulator and supplies the graph used by [Microfly](joint-projects.md). Its statement that behavior emerges from propagation should be understood alongside the engineered encoders, output mappings, and numerical model; it does not establish biological fidelity or task learning.

[desktop-fly](https://github.com/DenisSergeevitch/desktop-fly) combines a spiking FlyWire model with a procedural body/gait presentation. That is a useful example of why neural anatomy and body animation must be attributed separately. It was inspected at README level only.

## What was not established

Search surfaced further Beat Saber, Minecraft, and other game claims, but this pass did not obtain an adequate inspected primary-source training/validation chain for all of them. They are not promoted into evidence of learned competence here. A future entry should name its repository, exact dataset, training locus, action mapping, controls, and measured results. [Flyhard](flyhard.md) receives its own page because its trainable-core code and physical-contact interventions are more directly relevant than another viral montage.


---
[Community index](index.md) · [Source ledger](sources.md) · [Main wiki](../index.md)
