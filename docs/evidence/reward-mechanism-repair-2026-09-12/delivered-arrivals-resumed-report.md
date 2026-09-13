# KC input delivered to the two recorded PPL101 cells

September 13, 2026 UTC. **Saved-artifact descriptive analysis; SCI-001 remains failed.** All 32 actual fine recordings were analyzed against the frozen graph, yielding 64 target/trial records. No native call, circuit intervention, parameter change or model-pointer change was made.

The second/base group receives more accepted KC input and produces more PPL101 spikes than the original/base group. Gamma KCs account for about 86% of accepted KC conductance increments in every group. That is distinct from the alpha/beta predominance of the separately recorded home learning residual. It does not identify a causal pathway or establish that more input alone explains the learning sign.

## Exact input accounting

Each KC spike schedules one event per anatomical directed edge, due nine steps (1.8 ms) later. Contacts determine that event's static float32 increment: contacts × positive KC sign × 0.1375. KC input gain 1.25 acts onto KCs; it does not multiply this KC→PPL101 edge. Selected KC→MBON gains do not directly scale edges ending at PPL101.

An event is **accepted** only when its due step is at least the target's prior spike step + 11 (2.2 ms). A due event during refractory is discarded, not held until release. A new target spike at the same step follows delivery and integration, so its arrival is accepted before that spike resets voltage and conductance. The run processes steps 0–1999; a due event at exactly 400 ms (step 2000), or later, is pending and outside observation.

`due` means an attempted in-window edge delivery. `accepted` and `refractory_discarded` partition it. Edge-event counts, contact-weighted event counts, and conductance-increment sums remain separate. Conductance here is the simulator's model quantity, not a measured biological current or physical conductance unit.

## Original and second groups

Values below are means per trial, summing both PPL101 targets. Each group retains all eight cues; base and alternate noise are separate. These are different cue/noise groups, not a causal intervention.

| Panel / noise | Accepted KC increment | Refractory-discarded increment | Discard fraction of due increment | PPL101 spikes, both cells | Gamma fraction of accepted |
| --- | ---: | ---: | ---: | ---: | ---: |
| original / base | 2830.128 | 479.273 | 14.48% | 33.125 | 86.25% |
| original / alt | 2793.553 | 471.745 | 14.45% | 31.625 | 86.39% |
| second / base | 2997.586 | 549.519 | 15.49% | 35.750 | 86.31% |
| second / alt | 2821.036 | 472.141 | 14.34% | 33.000 | 86.23% |

All in-window KC deliveries end by **308.6 ms**. No recorded KC emission has a pending arrival at or beyond 400 ms. The boundary logic still preserves such pending events and is independently tested at 399.8, 400 and 401.6 ms.

## Accepted input by family and arrival phase

This table shows the failed second/base group, mean per trial across all eight cues and both targets. JSON preserves every corresponding table for both targets and all four panel/noise groups; no family or failed trial is excluded.

| Arrival phase | Gamma | Alpha-prime/beta-prime | Alpha/beta | Other | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0-100ms | 652.781 | 0.292 | 95.184 | 0.000 | 748.258 |
| 100-130ms | 281.978 | 0.103 | 50.239 | 0.000 | 332.320 |
| 130-300ms | 1604.213 | 0.464 | 255.973 | 0.000 | 1860.650 |
| 300-400ms | 48.125 | 0.000 | 8.233 | 0.000 | 56.358 |

Only 1.88% of second/base accepted KC increment arrives after 300 ms. This is an arrival-time statement, not a claim that learning updates stop then: the bridge's filtered learning signals and analytic tail have their own time course. See the preserved [learning residual attribution](../../../docs/evidence/reward-mechanism-repair-2026-09-12/bridge-residual-attribution.md).

## Acceptance is not retained conductance

The output includes a separate float64 linear KC-only decay/reset ledger under the **observed** target spike times. Each accepted increment contributes before that step's synaptic decay; the remaining contribution is cleared on a recorded spike. Each component satisfies accepted increments = decay losses + spike-reset losses + end residual. It never evaluates a threshold or predicts a counterfactual spike. Native state combines unrecorded non-KC input with float32 accumulation, so these conditional components are not a bit-exact reconstruction of full native g or v.

For second/base, the conditional KC component cleared on spikes totals 1144.738 per trial (38.19% of accepted increment), while 56.702 of accepted increment arrives on a target-spike step. That same-step input has already entered integration before reset; “reset” does not mean it never acted. Decay and spike resets are separately retained for every phase and family.

## Anatomy and missing recordings

| Target body | KC edges / contacts | Non-KC edges / contacts | Non-KC edges / contacts without time raster |
| --- | ---: | ---: | ---: |
| 11327 | 3068 / 11846 | 500 / 6183 | 498 / 6102 |
| 11900 | 3100 / 12222 | 611 / 8874 | 607 / 8786 |

The sampled set contains all 4,064 KCs, the 24 teaching DANs and 686 sensory ports. It does not include MBON/APL or most other incoming cells as time-resolved rasters. Total per-neuron counts exist, but do not supply the missing arrival times or refractory acceptance. Missing input timing is **unknown**, never zero. Negative feedback and other non-KC sources therefore prevent any complete-drive, current-fraction or causal firing attribution. Anatomical contacts still total 39,125, of which 24,068 come from KCs.

## The retained 4420 comparison

Source 4420 illustrates the limit of amount-only interpretation. Base noise has 5,006.375 accepted KC increment across the two targets and 57 PPL101 spikes; alternate noise has 4,350.225 and 51 spikes. Both have substantial gamma-dominated incoming activity, yet their recorded home gain-sum changes have opposite signs: −1.377391636 versus +0.089282691. This descriptive comparison does not isolate timing, recurrence or any particular presynaptic family, and neither trial was dropped.

## Verification and artifacts

- All 61 consumed input files matched their pinned hashes: both prior panel archives and summaries, frozen graph/annotations, sample map, capture summary, relevant kernel/wrapper/protocol/encoder identities, frozen pilot, native binary read-only, and all 32 actual fine NPZs. All returned numerical arrays matched their saved fingerprints; exact selectors, binary raster shape and sampled count sums were checked.
- **31 focused tests passed**: independent time-ordered queue oracle over release/delay/coincidence/end boundaries, target independence, malformed timing, phase membership, contact values stored as integer or float32, conservation and independently summed exponential impulse contributions. The initial reader incorrectly rejected the graph's integral-valued float32 contact array; a six-case dtype/value regression was added, observed failing, and repaired before result generation.
- A separate saved-data checker reproduced every accepted and discarded per-step/per-family count and increment for **all 64 target trials**, plus all same-step counts, using a time-ordered queue instead of the analyzer's prior-spike search. This is numerical-method independence by the same author, not a separate-person review.
- Ruff passed on the output-local scripts/tests. No production, API or frontend file changed in this subtask; the parent owns the repository-wide verification and browser workflow. No native engine was imported, built or executed.

Artifacts (all local, original capture files preserved):

- [Standalone analyzer](delivered-arrivals-resumed.py), [boundary tests](delivered-arrivals-resumed-tests.py), [independent queue checker](delivered-arrivals-resumed-crosscheck.py).
- [Complete target/family/phase JSON](delivered-arrivals-resumed-result.json), [per-step accepted/discarded/conditional-component NPZ](delivered-arrivals-resumed-result.npz), [64-target crosscheck receipt](delivered-arrivals-resumed-crosscheck.json), [flattened phase table](delivered-arrivals-resumed-phases.csv).
- [Full-doc reading receipt](delivered-arrivals-resumed-reading-receipt.md) and [hash-bound corpus manifest](delivered-arrivals-resumed-reading/manifest.json).

Result JSON SHA256: `73ce388bf3a012ce4ba8a2325e9dd6d7efd5d417ccee6a965227c3d294783481`. The result embeds the analyzer SHA and all consumed input hashes. The per-step artifact is separately hash-bound inside the JSON.
