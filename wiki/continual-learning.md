---
type: mechanism-and-evidence
updated: 2026-09-14
status: recovery-qualified-interference-unresolved
---
# Continual learning, recovery and interference

This page connects the recent recovery and retired-cue research. The base learning rule and conditioning controls live in [associative learning](associative-learning.md); complete experiment tables remain in the [dated evidence](../docs/evidence/associative-learning-2026-09-13/index.md).

## Biological motivation and model transfer

Fly experiments distinguish dopamine-dependent forgetting, restoration of depressed MBON responses, and reversal. Berry's 2012 and 2018 studies and Shuai's 2015 study concern particular circuits and preparations; they do not provide a universal gain-recovery constant for PAM08/γ4 and PAM01/γ5. Handler's order-sensitive potentiation is another route to change, not interchangeable with passive forgetting. [Source ledger](sources.md#associative-learning-and-future-pathways--september-14).

Jiang and Litwin-Kumar's 2021 model motivates an additional dopamine-dependent potentiation term for long association sequences: bounded weights otherwise accumulate near their lower limit. Their Eq. 5 and Fig. 7 are a model precedent. BET36FLY adds its own gate and resting bound; it does not claim a literal reproduction of their equation or natural forgetting in this specimen. [Primary model](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009205).

## Fast synaptic path integration is a different memory problem

Peter Wang's [MaleCNS navigation analysis](community.md#fast-weight-navigation-candidate--inspected-and-partly-reproduced-september-14-2026) proposes storing a journey vector in rapidly changing central-complex synaptic strengths on hΔH, hΔA, hΔI or hΔG. That state would be written while the fly walks and re-zeroed at food. It is therefore a candidate within-journey working-memory/path-integration mechanism, not evidence for the cross-trial KC→MBON association, recovery or interference measured on this page.

The released implementation uses an imposed additive weight vector in an eight-bin rate model; it does not implement the candidate dopamine/octopamine cells as causal write/reset signals. Its corrected route simulation reproduced here, but no synaptic plasticity has been measured in those hΔ cells and activity-based storage remains possible. A future BET36FLY synaptic-state reservoir would require a new experiment identity and its own write, retention, read, reset, pathway-intervention and matched-null controls. It cannot inherit conditioning-02/03 qualification. [Inspection record](../docs/evidence/community-sources-2026-09-14/fast-weight-navigation.md).

## What circuit-02 adds

For an eligible edge with **no current KC spike and exactly zero KC eligibility trace**, positive compartment dopamine trace and gain below rest:

```text
gain = min(rest, gain + eta × rho[c] × D_trace[c] × (rest − gain))
rest = 1.0
```

This branch acts only on inactive, depressed KC inputs. The original timing rule still acts on active inputs and can potentiate above rest, up to the separate 1.5 bound. The recovery term alone cannot cross rest. Therefore “no gain above rest” must identify the measured phase; it is not an invariant of every backward-pairing trial. [Native branch](../bet36fly/associative_lif.cpp), [circuit-02 protocol](../configs/associative-circuit-02.json).

Recovery requires the simulated dopamine trace, not elapsed calendar time. There is no automatic overnight decay, Rac1, DAMB receptor model, calcium/NO pathway or consolidation state. Electrical and trace resets remain those of the base engine. Values of ρ were selected from mechanistic tests, not baseball scores.

## Conditioning and long-history stress

Conditioning-03 passed at ρ = 0.005, 0.01, 0.02 and 0.04, under identities `e2faf2fdb0667212b38c`, `5f88c46159eedb590aad`, `117e4b8a909efdac6030` and `b70d59bfbd69d6f2de48` (all prefixed `associative-conditioning-`). Independent saved-artifact audits agreed. This does not mean every later stress/reversal outcome passed at every setting.

Stress-01 cycled eight reinforced cues 24 times (192 reinforcements), then tested acquisition and reversal from the long-history checkpoint. At **cycle 24**, saved manifests give:

| Arm | γ4 eligible gains at floor | γ5 eligible gains at floor | Post-history acquisition / reversal |
| --- | ---: | ---: | --- |
| No recovery | 20.39% | 21.74% | Passed / flipped |
| Recovery, ρ = 0.005 | 3.86% | 4.37% | Passed / flipped |

The smallest tested ρ satisfying the predeclared occupancy, recent-cue response, no-above-rest cycle-phase and post-history acquisition criteria was **0.005**. At 0.04 one post-history reversal seed did not flip; reversal was reported but was not that selection rule's criterion. Recovery reduced saturation while retaining the qualified behavior at the selected value. [Full stress table](../docs/evidence/associative-learning-2026-09-13/continual-learning.md), [manifest recheck and denominator definitions](../docs/evidence/wiki-integration-2026-09-14/reconciliation.md).

The frozen season reports quote floor fractions over the **4,108 selected gain slots**, of which only **3,417 are eligible to update**. These fractions are not the same denominator as the per-compartment eligible-edge stress fractions above. The reported plastic-season baseline range is 14.4–43.9% of all slots; recovery reports 0.8–0.9% of all slots. [Explicit counts and both denominators](../docs/evidence/wiki-integration-2026-09-14/anatomy-and-storage.json). Bound-contact telemetry counts repeated update contacts, not distinct saturated synapses.

## A retired cue becomes more depressed, not forgotten

Stress-02 reinforced `stress:0` during cycles 1–4, then retired it while seven other cues continued through cycle 24. It was supplementary and did not select ρ.

| Arm | Retired cue at cycle 4 | Retired cue at cycle 24 | Interpretation |
| --- | --- | --- | --- |
| No recovery | −15/−16/−14 | −46/−45/−51 | Continued depression despite no further direct reinforcement |
| Recovery 0.005 | −12/−12/−15 | −37/−37/−38 | Less drift, not erasure |
| Recovery 0.04 | −11/−9/−15 | −14/−15/−14 | Much shallower response change across cues |

Values are summed MBON05+MBON01 count changes relative to each cue's unit-gain probe, in three fresh seeds. The table does not mix one seed with the three-seed mean. [All five arms and identities](../docs/evidence/associative-learning-2026-09-13/continual-learning-forgetting.md).

Shared KC representations provide a plausible mechanism for cross-cue depression: other reinforced cues can update synapses also used by the retired cue. The recorded effect supports an interference concern; it does not by itself isolate every contributing shared edge. Measuring overlap versus unintended gain change, edge-sharing distributions and cue-specific response contrasts is still proposed. A clean lifetime assay needs much less-overlapping cues or a readout restricted to their specific supports. Raising recovery until all memories are shallow does not demonstrate better credit assignment.

## What this changed in the sports result

The recovery mechanism improved synaptic dynamic range. On the 2022 evaluation half-season, every declared rate remained statistically unresolved against its frozen/shuffled twins and worse than the encoder alone. These tests distinguish a working recovery intervention from useful predictive information. [Current prediction evidence](reassessment.md#prediction-evidence-and-data-use), [next research questions](research-directions.md).

[Wiki index](index.md) · [Kenyon cells](cells/kenyon-cells.md)
