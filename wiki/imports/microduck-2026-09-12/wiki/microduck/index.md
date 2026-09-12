---
type: index
updated: 2026-09-12
status: source-backed
---
# Microduck: body, trainer, simulator, runtime

Microduck's software is several cooperating systems. The GPU trainer learns control policies; the browser playground executes policies in WebAssembly physics; the production runtime runs the physical robot; a daemon-backed simulator replaces the body while keeping production software. Treating all four as “the simulator” hides the interfaces that matter for giving a fly controller a duck body.

| Page | Question |
|---|---|
| [GPU trainer and motor skills](trainer.md) | What learns, what is observed, how do rewards and actuator physics work? |
| [Simulator surfaces](simulators.md) | Which visible simulator tests which part of the system? |
| [Runtime and recurrent contracts](runtime.md) | What runs on the robot and what neural state signatures are accepted? |
| [Pickup mechanics and missing task physics](pickup-mechanics.md) | What does GroundPick accomplish and what would real retrieval add? |
| [Sources and revisions](sources.md) | Which exact primary files support this section? |

Start with [training versus deployment](../synthesis/training-and-deployment.md) before choosing a controller architecture. Compare existing [community integrations](../community/index.md) against those roles. Use [compute](../compute/index.md) for remote GPU launch and monitoring, and [connectome](../connectome/index.md) for anatomical and neural modeling constraints.

This section describes inspected upstream code and documentation. It does not claim that GPU training, a daemon rehearsal, or physical pickup was performed in this checkout.

[Return to the wiki](../index.md).
