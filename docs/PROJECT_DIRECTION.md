# Current direction: let the fly perform a food-choice task

**Decision: David's September 13, 2026 reorientation. Status: research and specification; not implemented or biologically validated.** This is the canonical project objective. The [handoff](NATURAL_SENSORY_HANDOFF.md) defines the next bounded task; the [reassessment](../wiki/reassessment.md) records evidence. Dated experiment protocols remain authoritative for their own results, not for choosing the project's next objective.

## The intended experiment

Represent the information available before a sports matchup as two distinguishable food opportunities. Better-supported prospects should evoke more appetitive fruit-odor or sweet-taste input patterns; sufficiently poor prospects can evoke a source-supported aversive pattern. Let the MaleCNS circuit transform those sensory inputs and measure its response. Establish ordinary sensory/feeding responses first, then ask whether this transformation contributes anything to matchup selection.

Both teams can look like good food. A close matchup between two strong teams must not become sweet versus bitter just because one team ranks second. Preserve absolute quality, relative advantage and uncertainty separately. Also allow two poor options, equal options, mixed cues and weak evidence. Use the same mapping for home and away. Large, reliable differences should be representable as appetitive versus aversive; exact biochemical profiles must come from calibration, not from the phrase “perfect fruit.”

The sensory mapping is engineered. The fly is not expected to understand football, baseball or team names. A simulated feeding signal is not a living fly eating or evidence of subjective taste. We are testing how much useful, anatomically constrained computation survives this translation.

## What changes now

The immediate question changes from “which dopamine equation passes our old guard?” to “can this circuit distinguish and appropriately respond to a calibrated appetitive versus aversive sensory exposure?” A frozen-plasticity sensory assay does **not** depend on repairing associative learning first. Innate response, learned association and sports prediction are separate claims.

The existing sports-to-ALPN map assigns standardized feature values to ranked annotation-type groups. It is not a measured fruit or sugar representation. Its zero incoming ALPN gain also bypasses earlier sensory processing. The new experiment may introduce identified ORN or GRN inputs and a supported downstream readout, with a new configuration and identity. Do not silently repurpose the old ports or copy their gains into a different pathway without justification. [Inspected code and drift audit](evidence/natural-sensory-reorientation-2026-09-13/index.md).

The old dopamine work remains valuable evidence. Its accepted interfaces/gains, failed candidates, numerical oracles and SCI-001 HOLD remain intact. Preserve those controls when interpreting or reproducing those experiments. They are not a ban on the new sensory work. Molecular modeling resumes only to address a demonstrated limitation of the selected assay, with a bounded question and independent evidence; another source-model reproduction is not the default next milestone.

## Milestones and decisions

| Stage | Required deliverable | Decision boundary |
| --- | --- | --- |
| 1. Sensory calibration | A source-backed table of stimulus, dose, cell class, baseline, measurement window, measured response and uncertainty; a MaleCNS input/output crosswalk; one preregistered finite assay | Resolve exact cells and units before injection. Unknowns remain explicit. Use one defensible modality first; do not wait for a complete molecular reconstruction. |
| 2. Natural-response assay | Plasticity-off neutral, appetitive, aversive and mixed-stimulus responses; requested versus achieved input rates; downstream time courses; matched seeds and independent repeats | Demonstrate the predeclared qualitative sensory/feeding response and absence of numerical runaway. If it fails, diagnose the first failing interface/pathway. Do not tune on sports outcomes. |
| 3. Two distinguishable opportunities | Equal/equal, good/good, poor/poor and good/aversive comparisons with identity swaps and order/side controls | An external comparison of two independent exposures is an engineered comparator. Do not call it an internal neural choice unless the circuit actually receives distinguishable alternatives and performs that computation. |
| 4. Matchup mapping | Versioned pregame features mapped through the frozen sensory calibration; examples covering both-good and large-difference cases | Freeze scaling on training history only. No future winner labels, postgame information or pairwise normalization that automatically makes one side bad. |
| 5. Sports evaluation | Chronological held-out comparison with encoder-only, same-information conventional, frozen-circuit and appropriate ablation controls | Report the circuit's incremental contribution. If it merely follows a forecast already encoded as sweetness, say so. A sensory response score is not automatically a calibrated win probability. |
| 6. Optional associative learning | Explicit cue/reinforcer timing, natural reward pathway, paired/unpaired/untaught/frozen controls and reversal from acquired state | Keep prediction-time sensory quality separate from outcome-time reinforcement. Define the biological claim and new gates before results; preserve all old failures. |

Stages 1–3 are the immediate work. Stages 4–6 are dependencies, not authorization for an unbounded sports pilot, model-pointer switch or deployment. A biological-state assumption (for example hunger) must be disclosed; absence of a modeled gut does not license inventing its parameters or require building the entire gut first.

## Rules for the translation

- “Hz” must name the neuron and measurement window. Stimulus-generator Hz, actual sensory spikes/s, downstream spikes/s, baseline-subtracted responses, optogenetic pulses and acquisition sampling frequency are different quantities. Fruit is an odor mixture; sugar water is a contact-taste stimulus. They do not share a single rate code. [Measured examples and limits](../wiki/natural-sensory-inputs.md).
- Preserve source receptor/sensillum/glomerulus identities and map them explicitly to this specimen. An annotation such as `gustatory` alone does not establish sugar, water or bitter identity. Female FlyWire IDs must never be used as MaleCNS body IDs.
- More spikes do not generally mean more attractive. Use stimulus-specific patterns and a source-supported aversive channel. Treat mixture, concentration and adaptation effects as hypotheses to check; do not obtain every odor by scaling every sensory neuron together.
- Preserve which opportunity produced which exposure. A single pooled odor vector can erase home/away identity. Predeclare a defensible presentation scheme and its reset, side, timing and carryover controls.
- If a feature model, odds feed or LLM supplies “likely winner,” that predictor is part of the encoder and must be evaluated on its own. No eventual winner can enter a pregame stimulus. Both-good does not imply a soccer draw, and neural preference magnitude is not confidence without calibration.

## Keep documentation aligned

Update this file when the user changes the objective. Update the handoff, `AGENTS.md`, README entry point, wiki index/reassessment and affected protocol status together. `CLAUDE.md` imports `AGENTS.md`; it must not maintain another architecture description. Put detailed failures and numerical histories in dated evidence, not in growing agent instructions. Mark superseded handoffs at the top and preserve their historical bodies. The imported Microduck snapshot remains immutable.

Current implementation facts belong in the [model card](MODEL_CARD.md): v1 still serves; v2 is paused; legacy dopamine qualification is failed; natural sensory calibration and behavior are not yet implemented. Documentation changes alone do not change any of those facts.
