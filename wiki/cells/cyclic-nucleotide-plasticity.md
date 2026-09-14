---
type: mechanism
updated: 2026-09-14
status: source-component-verified-learning-unvalidated
---
# Separate signaling and plasticity at MBON11 inputs

**Scope:** the detailed experiment claims below concern the legacy PPL101/MBON11 and PAM12/MBON09 investigation. Its failed or unresolved results remain unchanged. The separate PAM08/PAM01 circuit now has [qualified controlled conditioning](../associative-learning.md); that does not establish these molecular transfers or local dopamine exposure models.

The home channel needs more than a population-average dopamine trace. Its
identified output neurons are MBON11 bodies **10704 and 11402**, corresponding
to MBON-γ1pedc>α/β; its teaching neurons are PPL101 bodies **11327 and 11900**.
These atlas assignments locate the model's cells. They do not measure their
chemical state. [Cell identities](identities.md).

## Direct physiology at this output type

Yamada, Davidson and Hige (2024) examined γ and α/β KC inputs to MBON-γ1pedc.
Presynaptic depression required KC activation together with dopamine or
forskolin; raising cAMP alone was insufficient. Sparse activated and inactive
KC axons showed similar cAMP responses. PKA inhibition blocked depression,
whereas CaMKII inhibition did not. cGMP-pathway stimulation paired with KC
activation produced slower potentiation after repeated induction. γ-input
depression persisted longer than α/β-input depression onto the same MBON.
The protocol used minute-long induction, not a 400 ms trial. These results
constrain where activity dependence belongs; they supply neither a unique
downstream kinetic equation nor spike-to-concentration constants.
[Published study, checked September 13, 2026](https://physoc.onlinelibrary.wiley.com/doi/full/10.1113/JP285745).

This adds a necessary distinction to the earlier
[DopR1/DopR2 account](dopamine-receptor-signaling.md): a signaling reporter
cannot substitute for the downstream synaptic response. A simulator should
permit the two to be observed and perturbed separately. This does not make
the current cue-driven, untaught dopamine activity biologically neutral.

## A compartment-specific cotransmitter and a published model

Aso et al. (2019) identified nitric-oxide signaling in PPL1-γ1pedc and
modeled its opposition to dopamine using four persistent effect variables.
Their delayed expression stages distinguish memory induction from its
subsequent effect on transmission. Nitric oxide contributed to memory
updating, but was dispensable for backward timing-dependent valence inversion.
The study did not establish PAM-γ3 as an equivalent nitric-oxide source;
γ3-region staining is insufficient for that assignment.
[Primary paper](https://elifesciences.org/articles/49257),
[2020 transcript-analysis correction](https://doi.org/10.7554/eLife.64094).

The [source-component contract](../../docs/evidence/reward-mechanism-repair-2026-09-12/aso-da-no-component-contract-2026-09-13.md)
keeps this phenomenological model separate from chemical kinetics and from
MaleCNS. Its inputs are experimental activity levels; they are not already
a conversion of our individual spikes. Its four states are not measured
receptor occupancies. No author-code execution or fly-learning success
follows from reimplementing the equations.

The [completed numerical checkpoint](../../docs/evidence/reward-mechanism-repair-2026-09-12/aso-da-no-component-checkpoint-2026-09-13.md)
passes independent high-precision comparisons and state-boundary tests.
It retains the source's rates and expression times. The subsequent
[finite source protocols](../../docs/evidence/reward-mechanism-repair-2026-09-12/aso-source-protocol-result-2026-09-13.md)
completed 28 cases with independent numerical agreement. NO-only reversal
remained incomplete at the final sample; odor-only follow-up could still change
expressed weights. These are source-equation results, not MaleCNS learning.
The [current natural sensory direction](../../docs/PROJECT_DIRECTION.md)
takes priority over further molecular transfers.

## Consequences for this repository

The current native rule has one persistent gain for each selected edge.
Its rate and eligibility filters reset between calls. It has no distinct
latent induction state, delayed expression state, or nitric-oxide pathway.
These are implementation gaps, not evidence that the missing biology cannot
work. [Native kernel](../../bet36fly/reward_lif.cpp).

The four-state source model exposes a useful test: two synapses can have the
same currently expressed weight and different latent states, then diverge
during quiet time. Saving only their current weight loses that distinction.
Likewise, a quiet continuation can finish expression without erasing the
latent memory. A future integration must specify these checkpoint semantics
before any circuit experiment.

The home mask still includes **all 4,184 edges**; the γ-only away mask still
permits **3,239 edges**, while **1,443 others transmit unchanged**. Evidence
about γ inputs does not justify deleting α/β home inputs. Evidence about
home nitric oxide does not assign that pathway to PAM12. The accepted
interfaces and current failed learning qualification remain unchanged.

[Cell atlas](index.md) · [Neurochemistry](neurochemistry.md) · [Reassessment](../reassessment.md)
