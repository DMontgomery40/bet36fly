---
type: cell-family
updated: 2026-09-12
status: source-backed-and-code-inspected
---
# Kenyon cells: identity, overlap, and eligible synapses

**Biology.** KCs integrate projection-neuron input into distributed sensory representations. The anatomical α/β, α′/β′ and γ divisions refer to axonal organization, not task labels. Sparse representations can support specific associations while overlapping representations can generalize. Those observations motivate measuring cue overlap rather than assuming that every active KC represents a different game. [Caron et al. 2013](https://www.nature.com/articles/nature12063), [Hige et al. 2015](https://pubmed.ncbi.nlm.nih.gov/26637800/).

**Released specimen.** Our 4,064 KCs comprise 1,810 α/β, 695 α′/β′, 1,557 gamma-labeled cells and two broadly labeled `KC` cells. The fine labels include `KCab-c/m/p/s`, `KCa'b'-ap1/ap2/m`, `KCg-d/m/s1/s2/s3/s4`, and one `KCg`. These are retained labels, not evidence that every subtype's physiology has been modeled. [All 15 subtype counts and source IDs](identities.md).

**Implementation.** `Kenyon_Cell` is the actual class string; selecting `class == KC` would miss them. The reward engine scales every incoming edge to a KC by 1.25, simulates a uniform LIF state per cell, and stores a presynaptic trace for each selected KC. Learning adjusts gains on existing KC→selected-MBON pairs. It does not create new contacts, move synapses, or learn the ALPN→KC wiring. [Importer](../../bet36fly/connectome.py), [circuit construction](../../bet36fly/reward_protocol.py), [native rule](../../bet36fly/reward_lif.cpp).

## The two output supports are different

| KC family | Cells | Home edges to MBON11 | Away edges to MBON09 | Away edges eligible under gamma policy |
| --- | ---: | ---: | ---: | ---: |
| α/β (`KCab*`) | 1,810 | 2,283 | 5 | 0 |
| α′/β′ (`KCa'b'*`) | 695 | 316 | 1,438 | 0 |
| γ (`KCg*`) | 1,557 | 1,585 | 3,239 | 3,239 |
| Broad `KC` | 2 | 0 | 0 | 0 |
| Total | 4,064 | 4,184 | 4,682 | 3,239 |

Recomputed from [individual directed edges](data/reward-edges.csv). All 4,184 home edges remain eligible under the repair policy. The 1,443 excluded away edges keep transmitting with their existing gains; exclusion means no update, not deletion or silencing. The two broad KC labels have no support in this selected edge set, but remain in the circuit.

The gamma filter is a label-based approximation to PAM12 teaching territory, not direct localization of every KC→MBON contact. MBON09 also innervates β′1, explaining why the full output support contains many α′/β′ inputs. Home includes the peduncular component; applying the away filter to home by analogy would discard supported inputs. [MBON page](mbons.md).

## What the activity measurements say

Historical KC-set overlap fell from approximately 0.99 to 0.298 after the identity encoder and drive changes. Schema 3 recruited about 16% of KCs and left about 0.5% active after stimulus offset. These are simulator measurements on particular calibration stimuli, not universal biological sparsity values or proof of selective learning. The remaining shared core can still receive shared depression. [Calibration evidence](../../docs/evidence/reward-v3-summary.md).

For conditioning, compare same-cue reliability across fresh input noise, between-cue overlap, and plasticity on unique versus shared KC support. Include gamma/apbp/ab summaries so a compartment-wide mean cannot conceal which inputs change. This is a proposed analysis, not a new run. [Evidence gates](../evidence-gates.md).

[Cell atlas](index.md)
