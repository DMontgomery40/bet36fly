# Saved-array residual attribution — September 12, 2026 UTC

**The fixed bridge still fails the previously frozen second panel.** The residual is distributed, dominated by alpha/beta KC inputs in the failed home/base cell, and mostly applied after stimulus offset. The stored arithmetic reconciles; this investigation found no new numerical defect or evidence that a particular anatomical pathway causes the failure. Conditioning remains held. No production edit, circuit execution, surrogate, parameter sweep, threshold change or home mask change was performed.

## Panel comparison

All values are sums of published KC→MBON gain changes, in edge units. Each row below summarizes eight untaught trials. The guard remains `abs(mean) <= 0.5 * sample_SD`; no pooled-panel substitute is used.

| Rule/panel/seed | Mean home change | Guard limit | Mean/limit magnitude | Result |
| --- | ---: | ---: | ---: | --- |
| Raw original/base | −0.183176592 | 0.333790763 | 0.548777 | Pass |
| Bridge original/base | −0.103840373 | 0.128355080 | 0.809009 | Pass |
| Raw second/base | −0.515622884 | 0.489777884 | 1.052769 | Fail |
| Bridge second/base | −0.272640035 | 0.240845235 | 1.132013 | Fail |
| Bridge original/alt | −0.060988627 | 0.131732571 | 0.462973 | Pass |
| Bridge second/alt | −0.074156590 | 0.101465835 | 0.730853 | Pass |

Bridge attenuation reduces both the mean and its trial variability; it does not improve the failed standardized guard. Raw and bridge use the same cues/seeds and all32 untaught sensory hashes match. However, only9/32 full home-DAN compartment-mean step histories and6/32 aggregate KC step histories are identical. Changed gain publications can affect circuit activity, so this is a comparison of measured runs, not a same-spike-history filter comparison.

Exact run identities are retained in the JSON: bridge original `de050d773763`, bridge second `dea14759e9ca`, raw original `29c766f95f82`, raw second `e3d8898dc68a`. Both bridge NPZ SHA256 values were checked against their summaries; graph IDs/KC map/type annotations were checked against the frozen graph hashes. Root's separate independent audits establish the complete seven-criterion results and zero bound observations; this script concentrates on all32 bridge and32 raw untaught trials.

## Home family and timing attribution

Home contains4184 eligible edges from3623 distinct KCs:3062 KCs have one such edge and561 have two. Gamma contributes1585 edges, alpha-prime/beta-prime316, alpha/beta2283. Learning changes are per graph edge, not weighted by synapse-contact count. Duplicate home edges from the same KC have exactly identical per-edge changes in all inspected trials; reported KC sums retain that multiplicity.

| Bridge cell | Gamma | Alpha-prime/beta-prime | Alpha/beta |
| --- | ---: | ---: | ---: |
| Original/base | −0.068832427 | −0.002053514 | −0.032954432 |
| Original/alt | −0.081251986 | −0.001572996 | +0.021836355 |
| Second/base | −0.064612284 | −0.012976885 | −0.195050865 |
| Second/alt | −0.112141706 | −0.002801478 | +0.040786594 |

Alpha/beta supplies71.54% of the failed cell's signed depression. Its mean change per eligible edge is about−0.00008544 versus gamma−0.00004076; differing edge counts alone do not explain the family difference. The large original-to-second base change is alpha/beta, whereas gamma depression is slightly smaller. In both alternate seed sets alpha/beta instead partly cancels gamma depression. These are descriptive conditional effects, not evidence for removing a family or changing home eligibility.

The following bins subdivide the existing electrical phases for attribution only; they are not new gates. The sensory drive begins at0ms, learning/filter onset is100ms, stimulus offset300ms, electrical endpoint400ms.

| Bridge cell | 100–130ms | 130–300ms | 300–400ms | Analytic tail |
| --- | ---: | ---: | ---: | ---: |
| Original/base | −0.000180043 | −0.012780719 | −0.062727682 | −0.028151929 |
| Original/alt | +0.000121340 | −0.003462940 | −0.040111043 | −0.017535985 |
| Second/base | +0.000433892 | −0.014935598 | −0.177392997 | −0.080745332 |
| Second/alt | +0.000043705 | +0.009216316 | −0.054326713 | −0.029089898 |

For second/base,94.68% of the signed net depression is applied after stimulus offset;29.62% is the analytic tail. All32 bridge untaught recordings have no KC or compartment DAN spikes at/after320ms. Nevertheless, second/base gains change by−0.130137958 during320–400ms and−0.080745332 in the tail. Those are continuing integrations of existing rate/eligibility states. An application-time attribution does not imply a late spiking source or an independently measured biological tail.

## Cue and neuron concentration

| Second-panel cue, base seed | Home change | Alpha/beta change |
| --- | ---: | ---: |
| 4395 | −0.461931169 | −0.157484293 |
| 4399 | −0.234058022 | −0.218003571 |
| 4404 | +0.149757445 | +0.083976507 |
| 4408 | −0.080334246 | +0.005224645 |
| 4412 | +0.006715536 | −0.018928885 |
| 4416 | −0.030141771 | −0.015513241 |
| 4420 | −1.377391636 | −1.065376043 |
| 4425 | −0.153736413 | −0.174302042 |

Cue4420/base contributes63.15% of the panel's signed total depression;4420/alt is+0.089282691. This cue/base also dominates the raw second panel (−2.846523881). It has807 depressed KCs,570 potentiated KCs and2246 unchanged KCs; their negative mass is2.847096145 and positive mass1.469704509. Its ten most negative KCs supply only6.08% of negative mass. The largest is body121665, KCab-m, with two home edges summing−0.023399115. Across the eight second/base trials, the ten largest negative mean KC contributions supply4.66% of negative mass and the top100 supply27.33%;1192 KCs have negative means and846 positive means. Ranking is affected by edge multiplicity and is not a lesion proposal.

The two retained PPL101 neurons, bodies11327 and11900, have similar counts. In4420/base they fire22 and21 spikes in100–300ms, and one each after300ms. Counts alone neither isolate one DAN nor identify upstream synaptic causes. Exact individual-DAN event timing is unavailable; only their10ms count bins and the compartment mean at0.2ms are saved.

## State and arithmetic audit

Current `reward_lif.cpp:139` constructs zero voltage/conductance for each call; `RateBridge` at lines18–29 constructs zero R/E and initializes its double accumulator once from the float32 checkpoint. The learning gate at176 and interval call at258 exclude all pre100ms events from R/E. This matches the frozen implementation contract's explicit cold-onset policy. `reward_teaching_diagnostic.py:193` drives the sensory schedule from0ms; its per-trial gain reset at210 and cumulative `reset=False` preserve the declared distinction. Electrical/learning states restart in cumulative calls; only float32 gains persist.

Pre100ms activity is real: the failed second/base cell averages7.875 home-DAN spikes before onset, plus substantial KC activity. All recorded bridge pre-onset signals and KC state bins are exactly zero. Thus continuous filter initialization versus delayed filter initialization is an unresolved modeling choice. Small100–130ms updates cannot exonerate that boundary, because discarded history can affect later integrals. No exact warm-history counterfactual can be reconstructed from these artifacts: all trials retain aggregate KC step counts, but individual KC10ms counts only for the first cue of each panel; the two end-bin R/E moments do not supply an arbitrary fine event history. The source investigator is specifying the next separate matched-history investigation. Historical raw-event warm-history results do not establish the bridge result.

Independent checks used actual saved DAN impulse trains convolved with the closed rate/eligibility impulse responses, and per-KC final R/E for the tail. Across32 bridge trials:

- Group `Q = E_D*sum(R_K) − R_D*sum(E_K)` agrees within3.68e−13.
- Closed-impulse DAN R/E agrees within2.85e−13.
- Independently advanced endpoint DAN states and each KC's stored endpoint states reconstruct grouped tail attempted changes within1.98e−14.
- Endpoint eligible-edge KC masses reconcile within2.05e−12; published electrical+tail changes reconcile with actual checkpoint sums exactly.

The final learning interval advances to400ms before the separately recorded analytic no-new-event continuation (`reward_lif.cpp:314`,342). No endpoint off-by-one or missing-tail accounting was found. Per-KC final net changes are exact saved publications; per-KC analytic-tail *attempted* changes are independently reconstructed. Their difference is labeled finite-net-minus-exact-tail, with float32 publication rounding remaining; it is not an exact per-KC finite-phase publication trace. Group electrical phases are exact saved publication sums. Untaught endogenous pairing may legitimately produce adaptation under this implemented rule, but that does not satisfy the predeclared stability requirement or establish a biological prediction-error signal.

## Reproduction and outputs

Run from the repo root:

```sh
.venv/bin/python output/collaboration/reward-mechanism-repair/bridge-residual-attribution.py
```

The standalone script imports NumPy/Arrow and standard-library readers only; no BET36FLY module or native circuit is loaded. It writes `bridge-residual-attribution.json` (per-trial and aggregate evidence, input hashes), `bridge-residual-per-kc.csv` (all supported individual KC effects), and `bridge-residual-family-phase.csv`. Its assertions verify hashes, finite values, duplicate-edge equality, matched sensory identities, zero pre-onset learning, silent late event bins and independent algebraic reconciliation. It completed successfully. No production/test surface changed, so no new full repository test run, server or browser check was performed for this read-only attribution.
