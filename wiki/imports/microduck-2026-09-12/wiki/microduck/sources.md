---
type: source-ledger
updated: 2026-09-12
status: inspected
---
# Microduck sources and exact revisions

This section is based on public upstream source trees inspected during the research pass. The trainer was cloned at `53b8971b61baf5b7f3c16d135dd7cac37623de4b`; the runtime at `6507d2e960417aaa4ecd38eccf59b2dcf586ecd2`. These are historical research revisions, not a promise that a current default branch still points there. Selected Apache-2.0 files and notices are preserved in the [source archive](../../research/raw/index.md); [sources.json](sources.json) records their individual URLs and hashes.

## Trainer sources

| Source | What it establishes | Limits |
|---|---|---|
| [README](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/README.md) | Task families, CUDA workflow, policy export, source map | Documentation is not local training proof |
| [pyproject.toml](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/pyproject.toml) | Locked direct dependency choices, entrypoints, platform sources | Does not establish installed local/remote environment |
| [Velocity config](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/tasks/microduck_velocity_env_cfg.py) | Standard actor/critic, observations, rewards, DR | A body-skill baseline, not a fly actor |
| [GroundPick](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/tasks/microduck_ground_pick_env_cfg.py) | Near-floor mouth trajectory, phase, payload-force approximation | No complete physical retention/container task |
| [BallKick](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/tasks/microduck_ball_kick_env_cfg.py) | Object example, ball-blind actor, privileged critic | Large-ball kicking is not small-object grasping |
| [Export](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/export.py) | Normalized ONNX export and viewer options | Does not prove arbitrary neural-state export support |
| [Body server](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/sim/body_server.py) | Production-daemon body seam, protocol, joint mapping | Drivers and physical jaw are separate concerns |
| [Camera](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/sim/camera.py) | Rendered image size/format/orientation handling | Simulated imagery is not a real-camera dataset |

## Runtime sources

| Source | What it establishes | Limits |
|---|---|---|
| [README](https://github.com/pollen-robotics/microduck/blob/6507d2e960417aaa4ecd38eccf59b2dcf586ecd2/README.md) | Board/software architecture and daemon roles | Product summary is not a measured performance guarantee |
| [Simulation guide](https://github.com/pollen-robotics/microduck/blob/6507d2e960417aaa4ecd38eccf59b2dcf586ecd2/docs/robot/simulation.md) | Visible body, daemon/container forms, timing and limits | Commands were read, not executed in this research |
| [Recurrent policies](https://github.com/pollen-robotics/microduck/blob/6507d2e960417aaa4ecd38eccf59b2dcf586ecd2/docs/recurrent-policies.md) | Accepted explicit LSTM tensors, resets, board rehearsal | Not generic SNN/GRU compatibility |
| [Manifest](https://github.com/pollen-robotics/microduck/blob/6507d2e960417aaa4ecd38eccf59b2dcf586ecd2/docs/policy-manifest.md) | Widths, model API, command encodings, skill installation semantics | Correct metadata alone does not demonstrate motion |

## Web surface

The [product page](https://pollen-robotics.com/microduck/) identifies hardware and accessories. The [Space README](https://huggingface.co/spaces/pollen-robotics/microduck-simulator/blob/main/README.md?code=true) describes browser inference, controls, and development assets. Those pages are mutable; refresh current UI behavior before driving or publishing a changed demo. Their narratives may compress distinct task or hardware details, so implementation claims should prefer the exact relevant source file.

## Local evidence

This research also inspected [the importer](../../flybrain/connectome.py) and built local MaleCNS artifacts. [Connectome provenance](../connectome/malecns-release.md) explains the counts. No large raw connectome file is duplicated into the wiki; the local manifest and source hashes identify it. The build-script path regression was fixed and tested; that is data-preparation evidence, not learning evidence.

[Microduck index](index.md) · [Training roles](../synthesis/training-and-deployment.md) · [Wiki](../index.md).
