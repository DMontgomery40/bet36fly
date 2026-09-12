---
type: proposed-evaluation
updated: 2026-09-12
status: proposed-not-executed
---
# Evaluating small-object retrieval without fooling ourselves

The task is to find small target objects, retain them, carry them, and deposit them into a narrow-opening container. The user is not relying on this robot as a child-safety system. The engineering objective nevertheless warrants honest failure accounting, because a visually appealing demonstration can hide missed objects, dropped objects, or unsuccessful deposits.

This page proposes an experimental design. It does not report successful trials, establish a safety certification, or prescribe a medical response. Its mechanical motivation comes from the gap between the current [GroundPick primitive](../microduck/pickup-mechanics.md) and the requested complete retrieval sequence.

## Define success independently of training reward

A completed episode requires all of the following: the intended object was localized, physically retained, transported, released through the opening, and remained inside for a declared observation interval. Record the interval rather than invent a universal value. If the object is merely near the container, supported on the rim, stuck to the beak, or no longer visible, containment is not established.

Training can use intermediate rewards for learning, but evaluation should read independent state and video evidence. An environment's own success flag must be cross-checked against object position/contact and visible behavior. A physically disappearing object must not be treated as collected. The [microfly demo](../community/index.md) is relevant precisely because its virtual fruit collection is a software event, not proof of grasp-and-carry mechanics.

## Stage outcomes and failure taxonomy

| Stage | Positive evidence | Failure to count |
|---|---|---|
| Search/detection | Target appears in the sensor stream and is correctly identified/localized | Miss, false positive, wrong object, excessive localization error |
| Approach | Body reaches a feasible pickup pose with target still tracked | Collision, fall, target pushed away, lost track |
| Retention | Object is supported by beak contact and follows it after lift | Empty closure, slip, object damage, simulator attachment artifact |
| Carry | Object remains retained throughout the declared path | Drop, expulsion, collision, custody uncertain |
| Rim alignment | Feasible release pose over the opening | Rim collision, unreachable geometry, unstable lean |
| Release | Object separates from beak as commanded | Sticking, premature drop, release outside opening |
| Containment | Object remains physically inside after settling | Bounce-out, rim balance, false completion report |

Track where the object ends up after failure. A miss that leaves an object in place differs from pushing it into an obscured location. Recovery behavior should be evaluated, not removed from the dataset because it makes the clip less clean.

## Object and environment matrix

The user's target set includes grapes, button/coin batteries, coins, beads, marbles, and magnets. Evaluation should preserve class identity, individual specimen identity, size, shape, material/contact assumptions, surface, pose, visibility, and container geometry. A rigid sphere is an initial development object, not a substitute for the full matrix. [Mechanical differences](../microduck/pickup-mechanics.md).

Test clean backgrounds and clutter; multiple instances; distractors; reflective and low-contrast appearance; partial occlusion; object orientations; friction changes; slope; body initialization; battery-dependent actuation where modeled; camera exposure and viewpoint shifts. Separate physically plausible variations from impossible simulation states. The initial training scene should be simple enough to debug, but held-out scenes should be locked before tuning on their results.

Use object instances and scene layouts held out from training. A new image of the same rendered object under nearly identical lighting is a weak independence claim. Synthetic-to-real transfer needs real sensor samples once hardware is available. Any borrowed detector's label set must be inspected; a model named “duck detector” is not thereby a detector for coins or batteries.

## Statistical reporting

Report trial counts and denominators per class and scenario. Include overall end-to-end success, each stage's conditional success, time to completion, false-completion rate, drops, falls, and failures that move an object to an unintended location. Conditional stage rates help diagnose failure, but the end-to-end rate remains the task result. Sequential conditional stage rates can be multiplied by the probability chain rule when their denominators follow the same episode cohort. Multiplying marginal stage rates requires independence or another justified model.

Attach uncertainty intervals and distinguish independent trials from many correlated frames in one episode. Zero failures in a small sample is not an estimated failure rate of exactly zero. For scale, under independent identically distributed Bernoulli trials, zero failures in 100 trials gives a one-sided 95% upper bound of about 2.95% on failure probability, from `1 - 0.05**(1/100)`. This is an illustrative calculation, not a project acceptance threshold. Choose thresholds before evaluating and state what consequence each one controls.

## Control attribution and timing

Log both the fly's output and the duck controller's response in the same episode. Preserve neural state summaries, selected skill/command, actuator targets, measured joint motion, object/contact state, observations, reset events, and simulation timestamps. Video and plotted spikes should share a run identifier. A synchronized replay is stronger than independently generated neural and motion animations.

On a remote controller path, test delay and dropout explicitly. Onboard inference needs board measurements. On either path, reward improvement must not rely on a simulator running with mismatched body/control clocks. See [simulators](../microduck/simulators.md) and [runtime](../microduck/runtime.md).

## Progression and stopping evidence

Proposed progression: validate contact geometry; establish body primitives; establish that the fly learns a causal control role; integrate retention and transport; add narrow-rim release; evaluate the held-out matrix; rehearse production runtime; then perform physical trials when available. Training both systems can be staged or joint; this sequence describes evidence dependencies, not an obligatory neural architecture.

Do not spend a large run to compensate for an impossible jaw opening or missing object contact. Stop an experiment when NaNs, invalid geometry, reward artifacts, persistent state corruption, or lost checkpoints make the measurement uninterpretable. Preserve failure artifacts and resume from a documented correction. Each run should have an explicit compute cap and saved outputs as described in the [run contract](../compute/run-contract.md).

Related: [training roles](training-and-deployment.md), [open questions](open-questions.md), [wiki](../index.md).
