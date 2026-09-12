---
type: technical-deep-dive
updated: 2026-09-12
status: mixed-evidence-and-proposal
---
# Pickup mechanics: crouching, grasping, carrying, containment

## The key distinction

GroundPick implements a reaching-task objective, not a complete autonomous hazard-fetch task. At the inspected revision, it is configured to lower the mouth tip close to the floor without contact and return the body to standing. A phase signal separates descent from return. It also samples a modeled mouth payload force during return. That load approximates carrying weight; it does not instantiate and retain a grape, coin, or battery between physical beak surfaces. Source inspection establishes that objective and implementation; successful movement still requires checkpoint and rollout evidence. [GroundPick configuration](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/tasks/microduck_ground_pick_env_cfg.py).

This matters because optimizing reaching with a synthetic load can succeed while grasp contact fails completely. A detector can identify a target accurately while depth and beak alignment remain wrong. A release command can execute while the object remains stuck in the mouth. The proposed [evaluation plan](../synthesis/hazard-evaluation.md) tracks those outcomes separately.

## Fifteen physical motors, fourteen standard actions

The robot advertises fifteen motors, while the normal learned actor controls fourteen joints. The runtime handles the mouth separately. The simulated body protocol explicitly includes `mouth` at position nine but adapts to fourteen-joint training models that lack it. Thus a mouth angle visible in the renderer or protocol does not prove the jaw exists as an actuated collision mechanism in the training model. [Product specifications](https://pollen-robotics.com/microduck/), [body protocol and mapping](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/sim/body_server.py).

For the requested task, inspect the exact chosen MJCF for a jaw joint, actuator, opposing contact geoms, travel limits, and compliance. Inspect the production mouth command path separately. A fifteen-action actor is one possible integration; retaining a separate mouth controller is another. Either requires training and deployment to agree about timing, observation, and control authority. It should not be chosen solely to preserve a familiar tensor width.

## Why a small sphere is only an initial test object

A 15–25 mm sphere is convenient for development, but it cannot stand in for every target class. A coin or button battery is a thin cylinder with edge-on poses; a bead may roll or have a hole; a grape deforms and can be damaged; magnets can interact in ways a rigid-body friction model does not represent. These are geometry/material distinctions for experimental design, not medical advice. The first physical model should state which effects it includes and excludes.

BallKick supplies a useful source example for introducing a separate dynamic object, but its roughly 70 mm ball, ball-blind actor, and kicking objective are poor proxies for precise retention. Its configuration also documents a spawn-penetration failure where contact resolution could provide apparent progress for free. Small-object fetching needs equivalent checks for accidental initial attachment, interpenetration, and teleportation. [BallKick scene and task](https://github.com/pollen-robotics/microduck_rl/blob/53b8971b61baf5b7f3c16d135dd7cac37623de4b/src/mjlab_microduck/tasks/microduck_ball_kick_env_cfg.py).

## Container physics

A narrow container adds more than a target point. The mouth must reach a feasible pose above an opening; the object must clear the rim; the beak must release; the object must remain inside after bouncing or rolling. A simple distance reward to a box center can reward impossible or unsuccessful configurations. Model the opening and rim as physical geometry, distinguish container interior from its exterior, and test release from multiple offsets and heights before training the full task.

The user's “box/bottle with a narrow top” leaves a mechanical envelope to determine: aperture dimensions, rim height, internal depth, access angle, and whether the beak fits without collision. Those can be measured in the exact robot model and then checked physically. Do not invent those values from a rendered image or assume that one container proves performance on another.

## Proposed task decomposition

The useful decomposition is perception/localization, approach, beak placement, retention, carry, rim alignment, release, and containment confirmation. These may be learned jointly or in stages. Decomposition is an evaluation strategy, not a requirement to hard-code behavior phases into the deployed brain. A fly controller and trained body skills can cooperate across these functions, or a more integrated controller may learn them together; the architecture needs explicit attribution experiments.

At every transition, record the physical state that establishes success. Retention means the object moves with the beak under contact, not that a flag was set. Carry means retention survives motion. Deposit means sustained physical containment after release. A lost-object event resets the task's belief about custody even if the last perception result was high confidence.

## Current evidence boundary

The source review establishes available motor primitives and missing contact-task components. This project has not trained a hazard detector, a jaw-contact controller, a carry policy, or narrow-rim deposit behavior. Community demonstrations such as beak-ball tricks are additional evidence to inspect in the [community section](../community/index.md); success with their object geometry does not yet establish the user's entire target set.

Related: [hazard evaluation](../synthesis/hazard-evaluation.md), [training roles](../synthesis/training-and-deployment.md), [simulators](simulators.md), [wiki](../index.md).
