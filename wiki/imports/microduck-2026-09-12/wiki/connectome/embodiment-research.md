---
type: research-note
updated: 2026-09-12
status: researched
---

# What whole-brain embodiment research actually demonstrates

[Connectome index](index.md) · [MaleCNS provenance](malecns-release.md) · [Interface contract](brain-body-interface.md) · [Sources](sources.md)

The useful comparison is the complete causal chain: observations, neural update, motor readout, body dynamics, and learning. A realistic animal image does not identify which part of that chain generated the behavior.

## FlyGM: the closest graph-policy reference, with a different training path

Jin et al.'s February 20, 2026 preprint represents the FlyWire-derived connectome as a directed recurrent operator. Trainable neuron descriptors, shared neural updates, an observation encoder, and an action decoder make the static wiring executable. The methods first imitate trajectories from a pretrained MLP flybody expert, then use PPO for refinement. Reported tasks include gait initiation, walking, turning, and flight, with graph-rewiring and MLP comparisons. These are learned-controller results, not native behavior recovered without training. [FlyGM methods, §§3–4](https://arxiv.org/html/2602.17997v1)

The paper's sign convention labels glutamate and histamine excitatory; the local importer gives them negative signs. That discrepancy must be reviewed explicitly rather than inheriting a convention through a citation. The preprint is a methodological reference, not a validated MaleCNS controller or Microduck checkpoint. No hardware throughput claim is adopted here from this paper. [FlyGM methods](https://arxiv.org/html/2602.17997v1)

### Reproducibility check

The current author site says **Code (Coming soon)** despite the paper's statement that code is available. It describes 139,246 nodes, with 19,262 afferent, 118,496 intrinsic, and 1,488 efferent nodes. It also calls the graph unweighted, whereas the paper specifies a signed synapse-count operator. Neither discrepancy is silently reconciled here. [Author project page](https://lnsgroup.cc/research/FlyGM/)

**Microduck inference:** retain the idea of making the graph itself the recurrent policy. Expert demonstrations initializing that same graph controller would be a possible curriculum choice; this differs from a fly teacher training a separate duck policy that replaces the graph. Both duck body-skill training and fly-controller training are in scope; staged versus joint training and the interface remain research decisions. The reported fly tasks do not establish transfer to a bipedal duck robot, hazard patrol, object acquisition, or drop behavior.

## Eon: a closed loop with explicit engineered motor support

Eon's March 10 technical account combines a simplified whole-brain LIF model with NeuroMechFly. Selected descending activities influence lower-level imitation-trained controllers; mappings are partly hand chosen. It does not execute the full downstream motor hierarchy. The account says visual activity did not substantially drive the demonstrated behavior, and learning, internal state, and biological dynamics validation remained limited. This is meaningful integration evidence with clearly bounded fidelity. [Eon technical account](https://eon.systems/updates/embodied-brain-emulation)

The September 11 perspective is a new public update, not evidence that the March implementation acquired full motor-neuron control. It again describes descending readouts controlling body-level controllers and advocates held-out neural recordings and intervention tests. Its claims about other projects are leads, not primary verification of their implementations. [Eon September update](https://eon.systems/updates/more-flies-are-getting-uploaded)

**Microduck inference:** learned body skills and fly-level control can form a legitimate embodied hierarchy. A brain selecting a fixed “fetch” routine demonstrates a narrower role than learning its sensorimotor consequences. Report which decisions belong to the fly, which belong to the body controller, and whether the fly adapts through feedback. Hierarchical control is not inherently excluded; attribution needs causal tests.

## NeuroMechFly v2: body and sensorimotor research infrastructure

Wang-Chen et al.'s 2024 Nature Methods paper adds vision, olfaction, ascending feedback, terrain interaction, and adhesion to a fly neuromechanical platform. Demonstrations include engineered controllers, reinforcement-learned multimodal navigation, and a connectome-constrained visual subsystem. That does not make every controller in the platform a whole-brain connectome model. [Original paper](https://www.nature.com/articles/s41592-024-02497-y)

**Microduck inference:** reuse its experimental decomposition—sense, act, integrate body dynamics, return feedback—and its separation of body from controller. Do not place a fly body simulator between the brain and the actual target body merely to reproduce a familiar video. A Microduck simulator and eventual hardware have to own the dynamics and observations in the training loop.

## Flybody: anatomically detailed mechanics and learned locomotion

TuragaLab's project supplies a MuJoCo fly body, walking/flight environments, and optional learning dependencies. The core body installation does not itself supply policy rollout or training. The repository exposes a Ray-distributed RL path and separates physics from optional ML components. Its illustrative walking action has 59 dimensions. [Official repository README](https://github.com/TuragaLab/flybody/blob/main/README.md)

**Microduck inference:** a simulator asset, an RL algorithm, and a neural policy are separate artifacts. A functioning asset is not proof of brain control. Flybody's action space is not Microduck's actuator contract, and installing it cannot resolve that contract.

## What the literature licenses us to conclude

| Claim | Assessment for this project |
|---|---|
| Anatomical wiring can constrain useful executable models. | Supported by these research approaches. |
| A connectome graph can be placed inside a learned embodied policy. | FlyGM reports this; reproduction is incomplete here. |
| MaleCNS natively knows Microduck's mechanics or tasks. | No evidence in the reviewed sources. |
| A brain can causally control a body while its interface is engineered. | Coherent and testable; disclose where engineering occurs. |
| Successful robot behavior proves a particular biological fly was uploaded. | Not established by robot task success. |
| These sources demonstrate our NVIDIA training run. | No: device execution needs local or remote run receipts. |

The next research step is therefore a [testable brain–body contract](brain-body-interface.md), not a claim of completed emulation.
