---
type: cell-family
updated: 2026-09-12
status: source-backed-and-code-inspected
---
# MBONs: output identity is not a plasticity territory

**Biology.** MBON dendrites and DAN terminals organize mushroom-body learning compartments. MBON09 is γ3β′1; MBON11 is γ1pedc>α/β. These are not two equivalent, single-territory outputs. The anatomical study distinguishes their innervation and transmitter classes; its cell counts must not be substituted for counts in the released MaleCNS specimen. [Aso et al. 2014, Table 1 and Figure 8](https://elifesciences.org/articles/04577).

## Current and historical outputs

| Type | Body IDs | Released instance stem | Transmitter | KC input pairs / contacts |
| --- | --- | --- | --- | ---: |
| MBON11 | 10704, 11402 | `MBON11(y1pedc>a/B)` | GABA | 4,184 / 41,460 |
| MBON09 | 18713, 19267, 21242, 523060 | `MBON09(y3B'1)` | GABA | 4,682 / 63,579 |
| MBON07, historical away | 12859, 15626, 18603, 515338 | `MBON07(a1)` | Glutamate | 3,651 / 22,840 |

Values are freshly derived from local source-aligned graph arrays. [Target data](data/atlas.json), [individual identities](identities.md).

PAM12's γ3 teaching territory does not justify modifying every input to γ3β′1 MBON09. Its 1,438 α′/β′ KC pairs carry 19,317 contacts; the five α/β pairs carry five contacts. The repair policy excludes these 1,443 pairs from updates while retaining their transmission. The 3,239 gamma pairs carry 44,257 contacts. This is a KC-label proxy for territory, not a synapse-location proof. Home retains all 4,184 pairs; it is not gamma-filtered by analogy. [KC support table](kenyon-cells.md).

## What the sports readout computes

The reward experiment reads the mean activity of the two MBON11 cells and the four MBON09 cells. It transforms each response with `log1p`, standardizes using frozen calibration means and scales, clips at ±4, subtracts that value from the log training prior, and applies a two-class softmax. Thus lower activity in the selected MBON population increases its assigned class probability. No response-to-label coefficient is fitted in this reward readout. [Exact calibration and decode functions](../../bet36fly/reward_protocol.py).

This convention is an engineered decoder, not a statement that inhibiting either population naturally predicts an away win. The base model's GABA sign describes fast outgoing connections from these cells; it is separate from the decoder's negative sign and separate again from dopamine's effect on incoming KC gains.

A common downward shift in away MBON activity can therefore produce a common away bias even without learning game distinctions. Schema-3 paired and shuffled training exhibited that outcome. Recalibrating the decoder could disguise it; cue-specific conditioning must be tested independently before changing centering. [Reassessment](../reassessment.md).

V1/v2 use a different readout involving all 97 MBONs and superclass activity. Do not apply the two-population reward-readout description to the active historical model. [Model card](../../docs/MODEL_CARD.md).

[Cell atlas](index.md)
