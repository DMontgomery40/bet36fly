---
type: technical-deep-dive
updated: 2026-09-12
status: source-backed
---
# Simulator surfaces and what each can prove

“Drive the simulator” can mean operating a browser demo, inspecting a training rollout, or exercising production robot software. These are useful but distinct. The user's visible-computer-use requirement concerns how the experiment is observed and operated; the simulation engine and training device still need their own identities.

## Browser playground

The [official Pollen Space](https://huggingface.co/spaces/pollen-robotics/microduck-simulator) hosts a browser application whose MuJoCo physics and ONNX policy inference execute locally in the browser. The Space's Docker hosting is not evidence of cloud GPU training. Its README describes legs and rollers, keyboard/gamepad input, and policy switching. It also documents multiplayer ghosts: other users' poses are displayed, rather than all participants necessarily sharing one authoritative contact simulation. [Application README](https://huggingface.co/spaces/pollen-robotics/microduck-simulator/blob/main/README.md?code=true).

This surface is appropriate for learning controls, seeing available body skills, and reviewing the shape of the robot. A screenshot of a standing duck establishes that a renderer loaded, not that a new controller learned to stand. A walking clip establishes movement under the selected policy; its checkpoint identity and input path are necessary to attribute the movement to a fly model.

The inspected README locates physics/policy control under `app/src/game/`, separate from the React UI and rendering rig. Missing Git LFS assets can leave text pointers where a mesh or neural model should be. A local fork therefore needs complete assets as well as source code. The loaded policy and the physics revision should be pinned together. Browser and daemon parity should be tested with shared recorded observations, not inferred from similar appearances.

## GPU training world and rollout viewer

The [training repository](trainer.md) uses MuJoCo Warp for many training environments on CUDA. Its play/export tooling imports native MuJoCo and Viser viewers. Viser is a route to a browser-visible view of a remotely computed simulation, while native viewing requires access to the GPU host's display. Viewer availability in source is not proof that a particular hosted job exposes it with working authentication and networking. [Export/viewer configuration](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/export.py).

For a future visible experiment, record which simulation instance the user is seeing and whether it runs the same checkpoint and observation path as training. Rendering can occur less often than policy updates; the simulation clock, neural clock, policy clock, and display clock must remain distinguishable. A video played faster than its simulation-time rate must be labeled. Turning a GPU allocation into a screenshot stream is an integration task, not a property implied by “cloud training.” See [compute](../compute/index.md).

## Production daemons with a simulated body

The runtime's `scripts/duck-sim` and trainer's `duck-body` provide a different seam: the real `robotd` operates against `RemoteIo` instead of the physical motor bus. Sensor measurements arrive from MuJoCo and target commands return over TCP. The same control loop, policy selection, IPC, and clients can then run against a virtual body. Optional simulated ToF and head-camera paths feed their corresponding daemons. [Runtime simulator guide](https://github.com/pollen-robotics/microduck/blob/6507d2e960417aaa4ecd38eccf59b2dcf586ecd2/docs/robot/simulation.md), [body server](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/sim/body_server.py).

There are two deployment forms. Plain processes exercise the control and client logic. Linux containers additionally exercise service identities, systemd units, restart ordering, and update behavior. Neither reproduces physical drivers, the radio, ISP, NPU, encoder electronics, or the real servo bus. More realism in deployment orchestration does not repair missing jaw-object contact physics.

Multiple duck bodies can share one MuJoCo world in this path. That is materially different from visual ghosts: physical interactions can be simulated in a shared scene. The body server owns the mapping between the daemon's fifteen-joint protocol and fourteen-joint training models. Its default scene and time step are deliberate; merely taking any MJCF file can produce a model with disabled contacts or wrong timing.

## Timing and sensor fidelity

The daemon loop follows wall time. The simulator documentation explicitly warns that a world running slower than real time changes the feedback the controller receives and can invalidate behavior. This is different from offline training, where simulation time can advance at a rate unrelated to wall time if the learning system remains internally consistent. Measure real-time factor for daemon rehearsal; measure simulated steps per second for training. [Timing guidance](https://github.com/pollen-robotics/microduck/blob/6507d2e960417aaa4ecd38eccf59b2dcf586ecd2/docs/robot/simulation.md).

The current camera implementation renders 640×360 frames, converts them to UYVY, and sends them separately from the JSON body protocol. Its code corrects a model-camera orientation mismatch. Those details matter to a learned visual front end: rotated images and stale pose timestamps are systematic sensor changes, not harmless UI choices. The ToF path likewise needs its own geometry and sampling contract. [Camera code](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/sim/camera.py).

## Evidence recorded in this project

On September 11 Denver time, Computer Use opened the official Space in visible Chrome, entered the playground, and observed a rendered duck with policy loading complete. Subsequent native-app observations returned no controls and no screenshot. Direct browser-provider selection reported Chrome unavailable. No successful driving sequence, rollers sequence, GIF, or new-policy rollout was verified. That is a tool/session observation, not a claim that Chrome or the site was broken for the user.

Related: [runtime](runtime.md), [training roles](../synthesis/training-and-deployment.md), [pickup mechanics](pickup-mechanics.md), [wiki](../index.md).
