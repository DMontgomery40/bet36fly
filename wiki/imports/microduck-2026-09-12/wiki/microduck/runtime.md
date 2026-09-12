---
type: technical-deep-dive
updated: 2026-09-12
status: source-backed
---
# Runtime, recurrent state, and deployment contracts

## The deployment system is not the training system

The physical robot runs Rust daemons on a Rockchip RK3566. `robotd` owns control and the motor bus; camera, ToF, Bluetooth, configuration, and updates have separate services. Clients communicate through the shared IPC contract. Training happens in a different repository and produces models the runtime loads. [Runtime overview](https://github.com/pollen-robotics/microduck/blob/6507d2e960417aaa4ecd38eccf59b2dcf586ecd2/README.md).

For the fly-body project, deployment must answer four separate questions: where the fly model executes, where the body skill executes, who combines their outputs, and which component has final actuator authority. “Trained on NVIDIA” answers none of those by itself. A GPU-trained model may execute onboard, on a nearby computer, or remotely, subject to measured latency and runtime support. These are alternatives to evaluate, not promises that the current hardware can run the full CNS in real time.

## Standard policy tensors

The standard feed-forward policy consumes one 61-dimensional observation and returns fourteen actions. Its normalizer must be part of the exported model. The runtime checks advertised observation and action widths and robot compatibility in the policy manifest. Additional camera features or a jaw command cannot simply be appended without changing the contract. [Manifest schema](https://github.com/pollen-robotics/microduck/blob/6507d2e960417aaa4ecd38eccf59b2dcf586ecd2/docs/policy-manifest.md).

Command semantics also matter. A constant command, cyclic phase, and posture flag have different meanings despite occupying the same vector slots. Ground pick and roller crouch use phase information; generic constant-command skills use different invocation logic. A model file with the right tensor shapes can still be behaviorally incompatible if its command encoding is wrong.

## Recurrence already exists, with limits

The inspected runtime supports explicit-state LSTM exports in addition to feed-forward policies. It does not accept every recurrent network automatically. The supported inputs are `obs`, `h_in`, and `c_in`; outputs are `actions`, `h_out`, and `c_out`. Hidden/cell tensors use `[layers, 1, hidden]` with float32 values, static positive state dimensions, and a limit of 1,048,576 elements per state. GRU and arbitrary extra state signatures are not implemented in the documented contract. LSTM models advertise `model_api: 2`. [Recurrent policy contract](https://github.com/pollen-robotics/microduck/blob/6507d2e960417aaa4ecd38eccf59b2dcf586ecd2/docs/recurrent-policies.md).

This corrects an easy but consequential mistake: “the runtime cannot carry neural memory” is false; “it can directly load a full sparse spiking CNS” is also unsupported. An LSTM signature is not interchangeable with membrane voltage, synaptic current, refractory state, delayed spikes, and plasticity traces. A connectome controller needs either a compatible explicit export or a purpose-built runtime integration whose state ownership is tested.

## State lifetime is part of behavior

The documented LSTM implementation keeps state across successful steps and ordinary command changes, but resets it on activation, network switches, explicit disable, controller resets, and specified recovery/skill transitions. It discards warm-up state and clears state after inference failure. Active-file hash changes also affect state retention. The documented file digest excludes external ONNX weight files, so that digest alone does not identify a model using external weights. These are substantive behavior rules. A learner trained with persistent memory across an event that clears memory on hardware is trained for a different process. [Memory lifetime](https://github.com/pollen-robotics/microduck/blob/6507d2e960417aaa4ecd38eccf59b2dcf586ecd2/docs/recurrent-policies.md).

A future fly controller needs its own explicit policy for episode reset, pause, sensor dropout, fall, skill switch, checkpoint reload, and recovery. If neural memory persists while the body is teleported to a reset pose, the experiment must intentionally account for that discontinuity. Learned weights and fast neural state should be treated separately: clearing a membrane state need not erase training.

## Timing on the physical board

The nominal loop is 50 Hz, leaving 20 ms per full control cycle. The runtime provides an offline policy-rehearsal example that measures latency distributions and deadline overruns on a fixed observation sequence. Its documentation explicitly requires measurements on the Radxa board to establish onboard inference timing; development-machine measurements do not do that. Even board inference timing excludes sensor reads, motor writes, and scheduling. [Rehearsal procedure](https://github.com/pollen-robotics/microduck/blob/6507d2e960417aaa4ecd38eccf59b2dcf586ecd2/docs/recurrent-policies.md).

A remote fly model adds transport delay, jitter, disconnections, and clock alignment. A hierarchical design may allow slower high-level updates while a local motor controller keeps its own faster loop. A direct-motor design has a tighter coupling between neural inference and actuator deadlines. This is a testable trade-off rather than a reason to conflate the two. See [training and deployment roles](../synthesis/training-and-deployment.md).

## What deployment evidence would include

The minimum useful record is the deployed model identity, training and evaluation lineage, input transformation, accepted recurrent contract, action scaling, command semantics, state resets, host placement, and measured end-to-end timing. Rehearsal should compare a recorded observation sequence across the reference model and production inference, including reset transitions. Then a [daemon-backed simulated body](simulators.md) checks dynamic consequences. Neither substitutes for physical-object trials once the robot exists.

Related: [trainer](trainer.md), [pickup mechanics](pickup-mechanics.md), [hazard evaluation](../synthesis/hazard-evaluation.md), [sources](sources.md), [wiki](../index.md).
