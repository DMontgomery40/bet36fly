---
type: concept
updated: 2026-09-12
status: researched
---

# Microduck policies, accessories, and unusual skills

> Research snapshot: 2026-09-11 America/Denver (retrieved 2026-09-12 UTC). Public source inspection; no training jobs, physical trials, or independent replay performed.

## Stable base: a family of learned controllers

The official runtime presents walking, roller locomotion, ground pickup, recovery, sitting, kicks, and a forward roll as supported behaviors. It separates the robot daemon from the neighboring MuJoCo/PPO training repository. This is the baseline against which community additions should be compared. [Official runtime README](https://github.com/pollen-robotics/microduck/blob/main/README.md).

The task registry matters more than a list of videos: ground-pick rewards mouth-tip ground contact and return to standing; ball-kick is explicitly ball-blind; roller tasks use passive wheels. A task name therefore does not imply visual object recognition or autonomous selection of the action. [Training task definitions and README](https://github.com/pollen-robotics/microduck_rl).

## Representative artifacts with useful evidence

| Artifact | What is published | Important boundary |
|---|---|---|
| [Flamingo cycle](https://huggingface.co/RemiFabre/microduck-flamingo-cycle) | One policy commands either supporting foot and returns to two-foot stance; flag and side reuse twist slots | Sim-only; stronger backward disturbances caused failures; re-lifting continues while the flag remains set |
| [Collision Flamingo II](https://huggingface.co/Teethyfish/microduck-collision-flamingo-ii) | One-foot policy trained with decomposed exterior-shell collisions | Behavior reproduced only in the safe ONNX inference path; Native/Viser play discrepancy remains unresolved |
| [Tricks](https://huggingface.co/langli11/microduck-tricks) | PPO rollout-to-roll, cone slalom, and brief single-blade lift; source branch and evaluation scripts | Sim-only; reported running handoff 200/200 and slalom 8/8 gates do not establish general hardware reliability |
| [Basketball](https://huggingface.co/HannesVonEssen/microduck-basketball) | Proprioceptive LSTM policy balancing on a free ball; checkpoint, source, evaluations, exported recurrent graph | No ball state in actor; privileged critic during training; real-board timing and physical transfer untested |
| [Beak throw](https://huggingface.co/q2p/microduck-beak-throw) | Checkpoint, overlays, liners, runtime patch, release tests | Requires anatomical action clamp and patched runtime; ordinary policy replacement is insufficient |

The tricks release distinguishes brief loaded single support from a sustained glide. Its own tested controllers/probes led the author to report an approximately one-second ceiling for that setup. Treat that as an experimental finding under the reported geometry and probes, not a universal impossibility theorem for every future controller or hardware revision. [Tricks model card](https://huggingface.co/langli11/microduck-tricks).

## Accessories change the control problem

[Stilts](https://huggingface.co/HannesVonEssen/microduck-stilts) packages eight height-specific policies from 10 cm to 2 m, with separate ONNX graphs, continuation checkpoints, manifests, and clips. The root files alias the 10 cm variant. The highest versions are explicitly simulation research; a printable geometry and a rendered successful walk do not qualify a tall physical assembly.

[Swing](https://huggingface.co/HannesVonEssen/microduck-swing) couples a policy to a two-cord seat and includes printable seat/strap artifacts. This is useful as an example of task-specific contact and attachment modeling. Its results should be read with the full validity conditions: motion amplitude alone can reward a physically invalid setup.

For [beak throw](https://huggingface.co/q2p/microduck-beak-throw), the ball is held by contact geometry rather than a weld. The reported 50/50 randomized simulation gate passed only with the supplied runtime behavior; raw output exceeded the strict target bound in every trial. This is especially relevant to fetch-and-drop research: export success, contact realism, and output authority are separate acceptance questions.

## A policy contract is more than dimensions

The [flamingo manifest](https://huggingface.co/RemiFabre/microduck-flamingo-cycle/blob/main/manifest.json) describes command semantics, entry pose, duration, and model API as well as 61 observations and 14 actions. Reusing a velocity slot for a phase or mode flag is legitimate only when every consumer agrees on the meaning.

Basketball additionally needs persistent hidden/cell states: inputs and outputs include two 256-state LSTM tensors, with defined initialization and reset boundaries. It uses `model_api: 2`; a feedforward loader is insufficient even though the observation/action vectors retain their familiar lengths. Reported Rust/Python and PyTorch/ONNX numerical parity do not measure the robot board's 20 ms budget. [Basketball deployment contract](https://huggingface.co/HannesVonEssen/microduck-basketball).

## Relevance to a fresh MaleCNS controller

These artifacts supply task environments, contact scenarios, comparator policies, and export conventions. They do not themselves supply an anatomical neural core. A rigorous adaptation can reuse the physical plant while changing the actor architecture and making its trainable graph parameters explicit. Existing policies can be comparators, training starting points, or an explicit lower layer of a learned hierarchy. The user wants real-GPU training of both duck and fly; retaining duck skills is compatible with that goal when the fly also learns and each component's authority is disclosed.

Open questions: which model/runtime revision is the target; are the jaw and body actuators controlled on separate paths; which tasks require memory; which successes persist under the actual actuator/collision model; and which community measurements have been independently replayed? No physical community policy was tested during this research pass.


---
[Community index](index.md) · [Source ledger](sources.md) · [Main wiki](../index.md)
