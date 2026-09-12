---
type: technical-deep-dive
updated: 2026-09-12
status: source-backed
---
# GPU trainer and motor skills

## What the trainer actually trains

`pollen-robotics/microduck_rl` contains task environments and the standard reinforcement-learning path for learning the duck's motor skills. The inspected revision uses mjlab 1.3.0, MuJoCo Warp, and rsl_rl PPO. Its walking configuration instantiates an actor and critic with hidden widths 512, 256, 128. This is a conventional neural motor policy; a connectome model does not appear automatically when the stock training command is run. [Pinned trainer configuration](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/tasks/microduck_velocity_env_cfg.py), [dependencies](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/pyproject.toml).

That stock actor remains useful when the project trains **both** body skills and fly control. It can learn stable locomotion or crouching that a learned fly controller commands, provide motion demonstrations for another policy, or serve as a comparison against a connectome actor. Those are different experimental roles. A hierarchy with a trained fly above a trained motor policy is not the same experiment as direct connectome-to-joint control, but both can place the fly model in a body-feedback loop. The [role map](../synthesis/training-and-deployment.md) records the distinction rather than selecting one by rhetoric.

## Observation and action contract

The standard actor sees 61 values: 48 proprioceptive/history values plus 13 command values. The former comprise gyro, projected gravity, 14 joint-position offsets, 14 joint velocities, and the previous 14 actions. The command block contains twist (3), head pose (4), and body pose (6). Unused command slots remain in place so policies can be switched without changing buffer shape. Actions are 14 raw values converted into position targets for the trained servo set. The robot has a separate mouth actuator, discussed in [pickup mechanics](pickup-mechanics.md). [Upstream invariants](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/AGENTS.md).

The stock 61-vector is not a camera image or a hazard detector output. Adding pixels, object pose, contact, or a learned sensory front end requires an explicit new interface or an upstream controller that transforms those observations into existing commands. A privileged critic may observe variables the actor cannot. For example, BallKick's critic can inspect the ball while the actor is intentionally ball-blind. Therefore good kick rewards cannot establish visual target acquisition. [BallKick implementation](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/tasks/microduck_ball_kick_env_cfg.py).

## Physics and transfer fidelity

The important reusable work is more than PPO. The trainer models XL330 actuators using BAM, including voltage control and load-dependent friction. Domain randomization covers physical and sensor uncertainty; variants model passive roller wheels and joint backlash. Passive joints interleave with actuated joints in some models, so consumers must resolve servo joints by name rather than assume a contiguous index list. Observation bias and reward measurements must refer to the same sensed quantity. Randomization must restore nominal values on reset rather than accumulate indefinitely. These are upstream engineering invariants, not evidence that our future task already transfers. [Actuator and reset guidance](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/AGENTS.md).

Copying only a robot mesh and an optimizer would discard this transfer machinery. A custom hazard environment should inherit the appropriate existing task configuration and change the physical scene, observations, controls, and reward terms deliberately. The walking model omits contacts needed when the head or hull touches the floor. Ground-contact and roller variants exist for those other regimes. Select the model according to the experiment's real contact pattern, not whichever loads fastest.

## Task families and reward interpretation

Walking optimizes velocity tracking; stand-up targets recovery; sit/stand handles commanded posture; GroundPick lowers the mouth and returns upright; BallKick moves a large ball; rollers introduce different contacts and passive mechanics. Their reward definitions and policy invocation semantics differ. In particular, phase-encoded crouching is not a generic constant-command one-shot. [Task registry and source map](https://github.com/pollen-robotics/microduck_rl/tree/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/tasks).

Upstream guidance identifies recurrent reward mistakes: sign-reversed penalties, rewarding a stable fallen pose, payout for reaching a state repeatedly, and regularization that prevents discovery of the requested movement. For hazard fetching, the consequence is concrete: rewarding proximity to a battery can teach the duck to approach it without ever retaining or containing it. [Proposed task outcomes](../synthesis/hazard-evaluation.md) must be measured independently of aggregate training reward.

## GPU execution and export

CUDA is required for the training path. The upstream minimal smoke example uses 64 environments and five iterations before longer training. Those defaults belong to its motor policy; a full neural graph per environment changes memory and throughput enough that 4,096 environments cannot be assumed feasible. A graph with 166,700 nodes and 32 float32 channels would use about 20.3 MiB for **one** state per environment, before gradients, graph storage, optimizer state, and physics. That arithmetic alone would exceed 81 GiB at 4,096 environments. This is a sizing illustration, not a measured implementation requirement.

Export must include the trained observation normalizer. A checkpoint that behaves correctly under a Python runner can behave incorrectly on the robot if the normalizer is omitted from ONNX. The standard exporter handles that; the [runtime page](runtime.md) covers its accepted tensor signatures. [Exporter](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/export.py).

## What remains to establish here

No GPU training has run in this project. Before choosing a trainer extension, identify the actor at each layer, trainable parameters, body feedback, reset semantics, and checkpoints. Then measure actual CUDA execution, task correctness, and visible rollouts. The [compute section](../compute/index.md) addresses available services; provisioning a service does not validate the learning method.

Related: [simulators](simulators.md), [runtime](runtime.md), [source archive](sources.md), [wiki](../index.md).
