---
type: implementation-contract
updated: 2026-09-14
status: controlled-conditioning-qualified-predictive-contribution-unestablished
---
# Dopamine-dependent associative learning

This page owns the current associative engine's circuit, state and conditioning account. The [cell pages](cells/index.md) own anatomy and physiological assignments; [continual learning](continual-learning.md) owns recovery and interference; the [reassessment](reassessment.md) owns the current prediction verdict. The separate [legacy reward rule](learning-rule.md) and its failed SCI-001 gate remain unchanged. The executable protocol is [EXPERIMENT_ASSOCIATIVE.md](../docs/EXPERIMENT_ASSOCIATIVE.md), with exact runs and audits in the [dated evidence](../docs/evidence/associative-learning-2026-09-13/index.md).

## What the biology supports

Odor-specific KC→MBON depression, dopamine dependence and sensitivity to stimulus order are documented in flies. Handler's receptor experiments support opposing timing effects under their γ4/γ5 preparations; Hige's results do not imply universal backward potentiation in every compartment. The current event rule is an engineering transfer of the opposing terms in Jiang and Litwin-Kumar's model, not a reproduction of receptor kinetics or their optimized recurrent network. [Primary sources and limits](sources.md#associative-learning-and-future-pathways--september-14).

The experiment uses PAM08/γ4 and PAM01/γ5 with MBON05 and MBON01. Both are reward-related compartments, but sweet-taste short-term reinforcement and nutrient-dependent long-term reinforcement are distinct physiological findings. Driving both populations identically does not reproduce that distinction. [Dopamine cell reference](cells/dopamine.md#reward-compartments-in-the-associative-engine).

## Measured links and declared interventions

The plasticity-off links run `associative-links-cd33a0b4dfd97540c887` established the following under its particular stimulation, coupling and reset conditions:

| Link | Recorded observation | Interpretation |
| --- | --- | --- |
| Sweet cells → reward system | 34 sweet cells requested at 58.9 Hz for 500 ms; 1,304 total spikes and no DAN, KC or MBON spike | Natural sugar reinforcement is unresolved at this setting, not anatomically disproved |
| Odor → antennal lobe | Persistent activity without the ALLN intervention; recovery with ALLN outgoing weights zeroed | The sign/dynamics approximation needs physiological calibration |
| Odor → learned outputs | MBON05/MBON01 silent with the spiking APL proxy, including the tested 0.25 gain; output restored with APL outgoing weights zeroed | A new, explicitly measured intervention; not the legacy APL policy |
| Direct reinforcer → PAM08/PAM01 | 1,075 DAN spikes in the recorded reinforcer trial | An effective engineered drive, not natural sugar transmission |
| Thirty team cues plus four conditioning keys | 98–988 active KCs; median 388 (9.5%); MBON05 at least 12 spikes per 400 ms; mean/max KC Jaccard 0.140/0.443; recovery tail zero | A usable cue code under these tests, not a calibrated natural odor mixture |

Cue-only activity produced 58 reward-DAN spikes summed across the 34 calibration keys. Do not replace that observation with “odor never evokes dopamine.” The qualifying conditioning pair had zero cue-only reward-DAN spikes in its null arms. Those are different cue sets. [Link evidence](../docs/evidence/associative-learning-2026-09-13/index.md), [conditioning-02](../docs/evidence/associative-learning-2026-09-13/conditioning-02-result.md).

The circuit retains 166,700 neurons and 25,582,938 directed pairs at 0.11 mV/contact. Outgoing fast weights are zero for 420 ALLNs, two APL cells and 392 pure-dopamine-labeled cells. No legacy ALPN input bypass, KC input gain or global 0.5 gain is inherited. These interventions establish a conditional simulator assay; they do not establish realistic physiology throughout the graph.

## Signals, units and persistent state

Each team key selects 16 of 53 ORN types by a deterministic hash ranking, identically for every team. Selected ORNs receive a uniform requested 118 Hz. The source anchor is Zhao's baseline-subtracted response of ab1B/Or92a to one odor over 0.5 seconds; transferring it to all selected ORN types as an absolute generator rate is explicitly engineered. A team identity is not a chemical identity. [Sensory measurements](natural-sensory-inputs.md).

Cue window: 100–500 ms. Forward training places the 400 ms reinforcer at 500–900 ms; backward control reverses their order. Reinforcer requests are 30 Hz per selected DAN, with 68.75 mV events and ordinary DAN refractoriness retained. Requested events and achieved spikes are separate observations.

At each 0.2 ms step, after prior traces decay, the version-1 rule for eligible KC j→compartment c edges is:

```text
D = compartment DAN spike count / number of DANs × coupling[c]
K = this KC's binary spike
gain += eta × (D_trace × K − K_trace × D)
gain = clip(gain, 0.5, 1.5)
K_trace += K; D_trace += D
```

Both traces use a 1,000 ms time constant. They contain event-history proxies, not Hz or dopamine concentration. The ordering makes an isolated coincident pair neutral, forward pairing depressive and backward pairing potentiating. Conditioning uses η = 1e-4; sports arms declare their own smaller rates. The [recovery rule](continual-learning.md#what-circuit-02-adds) is a distinct version.

Gains persist across calls. Membrane state, synaptic state, refractory clocks and delayed-event queues reset on every call; traces reset unless explicitly supplied. Checkpoints store float32 gains and hash lineage, with edge-array and eligibility-mask bindings checked at restore. Plasticity-off probes leave gains byte-identical; probe caches are keyed by their gain hash. This is learned synaptic state across trials, not uninterrupted electrical activity across a baseball season. [Python wrapper and constructor](../bet36fly/associative.py), [native event loop](../bet36fly/associative_lif.cpp).

## Conditioning: preserve the failed design and the qualified successor

| Protocol | Identity | Outcome and scope |
| --- | --- | --- |
| Conditioning-01 | `associative-conditioning-42845736c62d3ac9841e` | Failed its declared criteria. Gain effects had the expected directions, but MBON05-only changes competed with fresh-seed noise, the backward directional control was incorrectly treated as a null, and A/B KC overlap was 0.39 |
| Conditioning-02 | `associative-conditioning-d1d3992e38c1dfa5fef1` | Passed acquisition, retention, reversal, causal lesion, timing, cue identity, presentation order and audit; saved-artifact recomputation agreed |
| Conditioning-03 | Four separately identified recovery settings | Passed the same battery at every declared ρ; see [recovery identities and tradeoffs](continual-learning.md) |

Conditioning-02 declared its amendments before execution: sum MBON05+MBON01 for response, use unpaired/untaught/frozen/lesion as nulls and backward as a directional control, select E/F by plasticity-off recruitment and low overlap (0.128), and use new seeds. Circuit, base rule, η, bounds, timing and exposure count stayed fixed. This was a new test after a failed design, not a retroactive pass for conditioning-01.

The paired summed-output contrast was −12/−7/−7 spikes across three fresh seeds, against zero null contrast. Mean γ4 A-edge gain change was about −0.078, versus −0.009 on B-preferring edges; backward A-edge change was +0.076. Frozen and dopamine-coupling-lesioned gains were byte-identical to unit gains. Retention remained exact through blank trials. Reversal **with backward erasure plus contingency swap** recovered A, depressed B and flipped preference; contingency swap alone was descriptive. There is no demonstrated passive extinction mechanism. [Full result](../docs/evidence/associative-learning-2026-09-13/conditioning-02-result.md).

## From cue learning to prediction

Sports predictions combine the four frozen innate-response differences with two learned log-count differences in an externally fitted logistic readout. A winner's odor receives reinforcement only after the existing 48-hour/UTC-day availability rule; a loser receives no reinforcement. Prediction probes are plasticity off. The unchanged sweet pathway was separately tested for invariance to the learned gains. [Sports protocol and controls](../docs/EXPERIMENT_ASSOCIATIVE.md#6-stage-4-protocol-does-plasticity-contribute-to-prediction-configsassociative-sports-01json-frozen-before-the-development-run).

The 2022 development comparisons do not establish incremental plasticity benefit. The product still serves the frozen 2023 sensory probabilities; the learning page exposes research evidence, explicit jobs and checkpoint probes separately. Conditioning qualification is neither predictive qualification nor checkpoint promotion. [Current verdict and data blocks](reassessment.md), [application contract](../docs/api-contract.md).

[Wiki index](index.md) · [Evidence gates](evidence-gates.md)
