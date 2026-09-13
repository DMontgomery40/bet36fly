---
type: cell-mechanism
updated: 2026-09-13
status: offline-candidate-rejected
---
# Local signaling between Kenyon cells

KC activity at a plastic synapse need not be identical to its somatic spike
count. A 2026 study reports activity-dependent muscarinic-B modulation of
KC signaling and supplies a public calcium model. It gives us a concrete
mechanism to investigate, while leaving its transfer to the named MaleCNS
cells unresolved. [Primary paper](https://doi.org/10.1016/j.cub.2026.01.014),
[source and compartment review](../../docs/evidence/reward-mechanism-repair-2026-09-12/handler-kc-switch-model-transfer-review-2026-09-13.md).

The subsequent [explicit local-calcium mapping](../../docs/evidence/reward-mechanism-repair-2026-09-12/kc-local-calcium-shadow-result-2026-09-13.md)
was implemented outside production and tested on all 32 saved histories.
It fails all four home guard groups, with every home trial becoming more
depressive. An independent calculation reproduces every final and electrical
float32 gain exactly. This rejects that mapping; it does not refute the
reported muscarinic physiology. The current reward kernel remains unchanged.

The [4,064-cell result table](../../docs/evidence/reward-mechanism-repair-2026-09-12/kc-local-shadow-cell-summary-2026-09-13.csv)
provides each KC's body ID, type, instance, eligible edge counts, event
attenuation and original/candidate home gain sums. Gamma, alpha/beta,
alpha-prime/beta-prime and the two other cells remain separately visible.

## What is present in this circuit

All 4,064 retained KCs are annotated acetylcholine, with stored fast sign +1.
They have 642,933 directed KC→KC pairs carrying 1,153,845 contacts, including
one self-pair. The reward constructor applies the accepted KC input gain
1.25 to these inputs. The electrical kernel adds them to the target's one
current-like state. These are a documented presynaptic-transmitter proxy;
they do not identify the target receptor or its physiological effect.

There is no KC muscarinic-B state, local axonal calcium state or
recipient-voltage-dependent inhibitory branch in the current reward kernel.
The plasticity bridge receives KC spikes and a channel mean of DAN spikes.
Adding local signaling would change this representation and require a new
mechanism identity. It is not a correction of a mistaken contact count.
[Current code and complete retained-pair audit](../../docs/evidence/reward-mechanism-repair-2026-09-12/conditioning-contract-evidence-ui-audit-2026-09-13.md).

## What the experiments constrain

The reported γ-KC experiments distinguish cAMP modulation at rest and during
odor activation. The oocyte assay establishes voltage dependence of mAChR-B;
it does not calibrate this simulator's KC voltage or a synaptic ACh
concentration. The model represents activity-dependent lateral inhibition
through distinct calyx and lobe calcium variables. Its sigmoid takes calcium
activity in arbitrary units, rather than membrane voltage in millivolts.

These measurements do not identify receptor dynamics for each of our 15 KC
type labels. They do not authorize filtering home to γ KCs. All 4,184 home
edges remain eligible; away keeps 3,239 supported γ edges eligible while
1,443 other edges transmit without plasticity.

## Why direct parameter copying would change the model

The inspected [public source](https://github.com/nawrotlab/KC_KC_lateral_interactions/tree/f0ee2079dae6761cc2d07f04e96e76e2654b6e3c)
fits external WT/knockdown calcium traces at 30 Hz. Its learning driver uses
a separate 10 ms step. Neither is our 0.2 ms electrical step. For fixed
neighbor drive `B` and recipient modulation `f`, the source's stored
inhibition follows

```
I_next = f * ((1 - dt/tau) * I + (dt/tau) * B)
I_equilibrium = f * (dt/tau) * B / (1 - f + f*dt/tau)
```

For fixed `0 < f < 1`, this equilibrium approaches zero as the timestep
decreases. The source multiplies stored history on every step. Keeping its
parameters while changing clocks is therefore a mechanism change, rather
than an ordinary numerical refinement. This is a property of the inspected
discrete model, not proof that the original fixed-step model is invalid.
[Independent derivation](../../docs/evidence/reward-mechanism-repair-2026-09-12/learning-coupling-mathematical-source-review-2026-09-13.md),
[synthetic audit contract](../../docs/evidence/reward-mechanism-repair-2026-09-12/kc-lateral-source-audit-protocol-2026-09-13.md).

Its dopamine function also permits new drive only while an external shock
is present. From a cold zero dopamine state, no shock therefore guarantees
no dopamine-driven depression by construction; a previously evoked state
can still decay and depress after shock. That is different from our
untaught condition, in which endogenous DAN spikes remain active. The
source's purely depressive weight rule and learning-rate search cannot
replace our accepted rate, independent teaching channels or reversal controls.

## The next mechanism must name its variables

A transfer must specify whether lateral signaling changes axonal activity,
transmitter release, cAMP or plasticity susceptibility. It must explain
how actual spikes drive that state, how retained KC contacts contribute,
which clock it uses and how it continues after input stops. Fast cholinergic
transmission and muscarinic modulation must remain distinguishable.

The original 499-row WT/knockdown workbook has been fully inventoried and
preserved with the pinned code and license. The later bounded external fit
reproduces the source model numerically, while its WT residuals remain uneven
(standard-error-weighted RMS 2.12006). It does not measure a spike-to-local-
calcium transfer for each named cell. The tested engineering mapping used
one completed-frame spike as one source-input unit, incoming normalized
contacts and held L/C as plasticity susceptibility at the source's 30 Hz
clock. These choices and their pan-KC extrapolation were declared before the
failed screen. No conditioning or reversal ran; qualification remains unmet.

The [identifiability analysis](../../docs/evidence/reward-mechanism-repair-2026-09-12/kc-calcium-transfer-identifiability-2026-09-13.md)
makes that limitation exact: `tau_input` divides input amplitude; it is not
an additional low-pass state. Scaling both a proposed per-spike input factor
and `tau_input` by the same amount leaves the calcium dynamics unchanged.
An explicit dimensionless engineering map is possible, but a population fit
cannot turn its chosen per-spike scale into a measured biological constant.

[Kenyon cells](kenyon-cells.md) · [Dopamine cells](dopamine.md) · [Cell atlas](index.md)
