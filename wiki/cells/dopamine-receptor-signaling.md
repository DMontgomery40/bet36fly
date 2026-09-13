---
type: mechanism
updated: 2026-09-13
status: source-tested-transfer-unresolved
---
# From a DAN spike to plasticity in a particular KC

**A DAN spike, local dopamine exposure and a KC's intracellular response are
different quantities.** MaleCNS provides the cells and contacts. The current
simulator uses actual spikes and a population-mean teaching signal; it does
not reconstruct release, clearance or receptor occupancy at each KC contact.

## The cells whose mechanism remains unresolved

| Accepted channel | Identified cells | Plasticity scope |
| --- | --- | --- |
| Home | PPL101 bodies 11327 and 11900; MBON11 bodies 10704 and 11402 | All 4,184 selected KC→MBON11 edges remain eligible. |
| Away | The 22 [PAM12 bodies](identities.md); MBON09 bodies 18713, 19267, 21242 and 523060 | 3,239 gamma KC edges may change; 1,443 other inputs retain transmission. |

These are engineered teaching/readout assignments. MBON11 is γ1pedc>α/β and
MBON09 is γ3β′1. A physiological γ4 reporter experiment does not supply the
kinetics of every input to these named outputs. It also cannot justify
gamma-filtering home. [Exact anatomical support](mbons.md).

## What the receptor experiments establish

Handler and colleagues distinguish DopR1/Gs/cAMP-associated depression from
DopR2/Gq/ER-calcium-associated potentiation, with order effects downstream
of similar release-side signals. The principal reporter preparations concern
γ4/γ5; the study is not a calibrated spike-to-receptor model of our γ1pedc/γ3
channels. ER-GCaMP reports luminal calcium loss, not absolute cytosolic calcium.
DopR2/DAMB is not the D2-like receptor. [Primary paper and methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC9012144/).

The explant induction uses a 500 ms KC ACh puff and five 100 ms DAN ATP pulses
separated by 20 ms, with at least 20 s between stimulations. Our entire
electrical trial lasts 400 ms. A mathematical no-new-input tail cannot
replace stimulation that never occurred. The reporter's one- and four-second
averaging windows are measurement choices, not measured decay constants.
[Quantitative transfer review](../../docs/evidence/reward-mechanism-repair-2026-09-12/receptor-order-quantitative-transfer-decision-2026-09-13.md).

## A published model was checked against its executable source

Gkanias et al. propose a dopamine plasticity rule with a weight-dependent
term and separate dopamine effects. We preserved the public code, its license
and the complete linked Handler workbook. The relevant helper/driver bytes
match the paper's archived revision. Its six source conditions now agree
with an independent calculation; this is a reproduction of that source
model, not a MaleCNS learning result.

The inspection found consequential distinctions: the released grid is 15 ms
despite the paper's 100 Hz description; the HTML equations and code have
different decay structures; the driver reverses the explanatory receptor
labels; and its ER averaging window differs from the workbook's original
measurement. Its reporter combination is also different from its signed
weight update. In the coincidence and +0.5 s conditions, internal weights
reach −32.486 and −9.799 while plotted weights are rectified to zero.
[Complete source reproduction and limits](../../docs/evidence/reward-mechanism-repair-2026-09-12/incentive-handler-source-result-2026-09-13.md).

Copying just two filters onto positive spikes would introduce another
mechanism change. With equal DC gains and an entire continuous tail, their
signed areas cancel; the inactive-KC weight offset returns to its starting
value. Recovery visible in a finite window or a discrete Euler update is
therefore not automatically preserved. The independently tested
[transfer mathematics](../../docs/evidence/reward-mechanism-repair-2026-09-12/incentive-dpr-continuous-transfer-boundary-2026-09-13.md)
also keeps the long source timing separate from our short trial. No receptor
constants or new production rule were selected from these comparisons.

## What the current signal measurements mean

The 50–100 ms DAN reference is measured **during the cue**. The circuit starts
from reset and has no separately specified spontaneous-DAN drive. Untaught
firing here is generated under the engineered cue and subsequent recurrent
activity; this reference is not a resting tonic measurement.

Teaching adds voltage pulses to the selected cells. Refractoriness and
membrane state determine whether a scheduled request produces a spike. The
reported evoked count compares a taught probe with an unpulsed probe using
the same cue and seed; it does not subtract a firing rate from a spike count.
The UI now uses those distinctions while retaining historical records and
the legacy `tonic_dan_hz` wire field.
[Kernel and retained-signal audit](../../docs/evidence/reward-mechanism-repair-2026-09-12/teaching-signal-observability-evidence-ui-2026-09-13.md).

The [complete 64-contrast comparison](../../docs/evidence/reward-mechanism-repair-2026-09-12/dan-causal-prefix-result-2026-09-13.md)
now establishes that teaching supplies an electrical difference in every
recorded case. At 310 ms, both home PPL101 cells (11327 and 11900), or all
22 away PAM12 cells, fired while their matched untaught target pool was
silent. Exact pooled counts and binary events establish membership at that
step; they do not reconstruct the complete taught per-cell history or a
local dopamine dose. The recorded KC prefix includes 490–1,446 active cells
per history, with all 4,064 KC identities preserved in the evidence arrays.
This provides input to investigate a mechanism, without specifying release,
clearance, receptor state or a successful learning update.

## A per-DAN release construction with numerical verification

The [DARELA source and transfer review](../../docs/evidence/reward-mechanism-repair-2026-09-12/darela-primary-source-contract-dopamine-sources-2026-09-13.md)
now pins the external code and separates its mouse burst model from a proposed
spike-driven input for our two PPL101 and 22 PAM12 cells. The proposed finite
construction gives each identified DAN its own three release factors. Every
actual spike advances that cell's state; emitted masses are then averaged
over the unchanged channel populations. Two cell assignments with the same
pooled spike counts can therefore give different modeled release.

The fixed external parameter row, pre-event readout, exact inter-event
recovery and rested reset are explicit engineering assumptions. The
[mathematical contract](../../docs/evidence/reward-mechanism-repair-2026-09-12/darela-event-transfer-math-contract-delivered-arrivals-2026-09-13.md)
establishes a finite 400 ms domain without an added cap, not steady tonic
physiology. This helper is outside the production circuit. It neither
reconstructs local dopamine concentration nor implements a KC receptor
state, and it has not produced a new qualification or conditioning result.
The [numerical checkpoint](../../docs/evidence/reward-mechanism-repair-2026-09-12/darela-source-transfer-checkpoint-2026-09-13.md)
passes the fixed source-kernel comparison and independent event/bridge tests.
The [current handoff](../../docs/REWARD_REPAIR_HANDOFF.md) records the next
fixed-history screen; no screen result is yet available.

The current learning qualification still fails. A future intracellular
mechanism needs independently specified input units, state transitions,
compartment scope and complete-tail behavior, followed by both qualification
panels and controlled acquisition/reversal. Passing source calculations or
display tests does not satisfy those biological learning gates.

[DAN populations](dopamine.md) · [Cell atlas](index.md) · [Current reassessment](../reassessment.md)
