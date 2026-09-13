---
type: cell-family
updated: 2026-09-13
status: mechanism-under-investigation
---
# Dopamine neurons: PPL101, PAM12, and the residual

**Biology.** Specific DAN activation can teach associations at KC→MBON synapses, with timing and compartment specificity. Dopamine is not universally synonymous with reward, punishment, or a scalar prediction error. Models of heterogeneous DAN activity explicitly construct or optimize the circuitry generating learning signals. [Hige et al. 2015](https://pubmed.ncbi.nlm.nih.gov/26637800/), [Jiang and Litwin-Kumar 2021](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009205).

## Exact task populations

| Population | Cells | Released instance territory | Engineering role |
| --- | ---: | --- | --- |
| PPL101 | 2: 11327, 11900 | `PPL101(y1ped)_R/L` | Home teaching, targeting selected KC→MBON11 gains |
| PAM12 | 22 | `PAM12(y3)_L/R` | Away teaching, targeting selected KC→MBON09 gains |
| PAM11 | 15 | `PAM11(a1)_L/R` | Historical schema-1/2 away population; not current teaching |

All body IDs are in [identities](identities.md) and [neurons.csv](data/neurons.csv). The accepted channels are engineered labels with a fixed readout. They are not a claim that PPL101 means “home,” PAM12 means “away,” or the two form a natural opposed reward/punishment pair.

The task pools the cells of each teaching type into one mean DAN event signal per channel. It does not separately route left and right teaching by synaptic location. A pulse at 310, 330, 350 or 370 ms attempts to stimulate every selected cell in the taught population. Scheduled stimuli and evoked spikes are different measurements; the gate compares them with an unpulsed common-seed probe. [Protocol construction](../../bet36fly/reward_protocol.py), [native event loop](../../bet36fly/reward_lif.cpp).

## Local signaling and the limits of body-pair counts

The [source and static-coupling audit](../../docs/evidence/reward-mechanism-repair-2026-09-12/dopamine-signal-sources-resumed.md)
checks all 14,551 retained outgoing pairs from these 24 DANs against the original
release. Both PPL101 cells directly contact **both** selected MBON11 bodies;
their instance suffixes cannot assign a local teaching territory. Of 3,623
eligible home KCs, 3,049 have a direct pair from at least one selected PPL101 and
574 have none. Of 1,557 eligible away KCs, 1,546 have a direct selected-PAM12 pair.
Absent pair contacts do not prove absent diffusible dopamine and do not justify
removing eligible edges.

Experiments describe local signaling along KC axons, whereas the simulator uses
one population mean per channel and no local release or receptor state. The
published PAM-γ3 sugar response includes suppression of ongoing activity; the
accepted positive PAM12 teaching pulse is an engineered interface. Neither
background subtraction nor a particular adaptation constant follows from these
observations. [Cohn et al. 2015](https://stacks.cdc.gov/view/cdc/38872/cdc_38872_DS1.pdf),
[Yamagata et al. 2016](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1002586).

The initial neuPrint access attempts returned no HTTP status or coordinates.
A later [bounded official-file check](../../docs/evidence/reward-mechanism-repair-2026-09-12/localization-range-report-2026-09-13.md)
retrieved and parsed both synapse-file footers. It established byte-range
access and column identities, but no body-selection index or synapse locations.
The [cell-specific localization page](synapse-localization.md) identifies the
required bodies, columns and evidence limits.

A later [individual-signal analysis](../../docs/evidence/reward-mechanism-repair-2026-09-12/ppl101-signal-basis-result-2026-09-13.md)
separates bodies 11327 and 11900 on all 32 saved untaught histories. Their
signals differ in every trial, and their mean reproduces all original home
gain bytes. Loose mathematical bounds do not exclude normalized local
couplings, but do not establish a passing anatomical map. No alternative
coupling was selected or fed back into the circuit.

The [receptor-state review](../../docs/evidence/reward-mechanism-repair-2026-09-12/dopamine-receptor-state-decision-2026-09-13.md)
distinguishes coincidence-related depression from order-dependent intracellular
signaling. Its three-state topology is an uninstantiated engineering hypothesis;
the inspected papers do not calibrate its kinetics for PPL101/MBON11 or
PAM12/MBON09. The simulator still has no such receptor-state mechanism.

The separate [weight-state hypothesis](../../docs/evidence/reward-mechanism-repair-2026-09-12/dopamine-weight-state-decision-2026-09-13.md)
lets ongoing positive and negative plasticity depend on the edge's current
normalized gain. Balanced activity then restores an altered gain toward one;
silence after filter decay does not erase it. This is an engineered
distance-to-bound rule, not a measurement of presynaptic release probability
or a molecular mechanism calibrated for these named cells. It still cancels
exactly coincident proportional signals at a fresh gain. Independent numerical
references and a [fixed-history protocol](../../docs/evidence/reward-mechanism-repair-2026-09-12/weight-state-shadow-preregistration-2026-09-13.md)
supported its subsequent test on all 32 histories. The
[result rejects this law](../../docs/evidence/reward-mechanism-repair-2026-09-12/weight-state-shadow-result-2026-09-13.md):
the second/base home mean −0.268754929304 still exceeds the 0.235695145300
limit. Independent numerical agreement establishes that result's calculation;
it does not identify a missing molecular mechanism as the cause.

A [quantitative source check](../../docs/evidence/reward-mechanism-repair-2026-09-12/tonic-burst-dopamine-quantitative-source-check-2026-09-13.md)
finds adult-fly regional release measurements and distinct receptor dose
responses in cultured cells. Neither measures the complete spike-to-dopamine-
to-plasticity relationship at the selected γ1pedc or γ3 synapses. DAMB/DopR2
in that receptor literature is not the D2-like receptor. The report also
separates live-fly sensor evidence from mouse-slice kinetics, so those numbers
are not silently assigned to the named fly cells.

The rectified-rate adaptation hypothesis was tested under a
frozen numerical contract on all 32 saved histories and **rejected**. All four
home guards failed through excessive potentiation; second/base mean was
+2.638301402 against absolute limit 1.113471909. No circuit ran for this
offline study, and the equation was not integrated as a production rule.
[Complete result and independent numerical audit](../../docs/evidence/reward-mechanism-repair-2026-09-12/rate-adaptation-shadow-result.md).

## Anatomical class is not transmitter selection

There are 340 cells with class `DAN`, 392 with the exact pure-dopamine transmitter label, and 338 in the intersection. The atlas retains the union so that neither set is silently substituted for the other. The reward engine zeros fast outgoing weights for all 392 pure-dopamine cells. Only the 24 selected, confirmed DANs contribute to its learning rule. This is a modeled separation of modulation and fast transmission, not a reconstruction of dopamine release or cotransmission. [Atlas](data/atlas.json), [neurochemistry](neurochemistry.md).

## Why PPL101 deserves a dedicated investigation

The [individual PPL101 input and feedback page](ppl101-inputs.md) identifies both
cells, all retained direct inputs, named MBON/APL feedback and the distinction
between contact weights and actual delivered events. It also records the later
failed continuous-history test under its exact capture identity.

The local graph gives PPL101 39,125 incoming contacts, 24,068 from KCs. PAM12 has 18,156 total inputs, 11,034 from KCs. Both receive recurrent input; directly stimulated DANs are not isolated external switches. Counts were recomputed for this wiki. They establish anatomical support, not which inputs cause tonic activity. [Target aggregates](data/atlas.json).

In the legacy schema-3 rule, the home reference was measured during the stimulus and applied after offset, when PPL101 activity fell. Negative baseline-subtracted D then drove positive gain change. In the repair candidate, raw nonnegative DAN events remove that particular artifact, but untaught home drift remains outside the predeclared guard. The fine-resolution replay and temporal surrogates show sensitivity to event order; they do not prove that direct KC→PPL101 input is the sole cause. [Preserved diagnostic](../../docs/evidence/reassessment-2026-09-12/repair-phase1.md).

The later corrected raw rule fails the second panel at home/base mean −0.515623
against absolute limit 0.489778. The numerically verified rate bridge fails at
−0.272640 against 0.240845. Keeping pre-100 ms filter history on the same recorded
spikes worsens the latter to −0.481926 and fails all four home groups. This rejects
the history-only hypothesis; it does not identify an upstream neuron as the cause.
[Current results](../../docs/evidence/reward-mechanism-repair-2026-09-12/index.md).

Further evidence should distinguish spontaneous, sensory-evoked and teaching-evoked
events; retain per-cell counts as well as the mean; account for KC eligibility
before and after offset; and preserve matched untaught and timing-unpaired controls.
Biological feedback is a candidate mechanism to investigate, not noise to remove
merely until sports scores improve.

[Cell atlas](index.md) · [Exact update semantics](../learning-rule.md)
