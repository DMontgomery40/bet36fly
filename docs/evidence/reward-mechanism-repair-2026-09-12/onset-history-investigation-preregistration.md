# Post-bridge scientific investigation contract — September 12, 2026

Reviewer: mechanism_sources. Read-only source/result investigation after final bridge second-panel failure; no source edits, circuit execution, parameter sweep or conditioning. This is a proposal to distinguish a boundary assumption from a remaining learning-signal problem. It does not revise the failed candidate, authorize a new rule, or claim biological learning has failed.

## Evidence and conclusion

The final original `de050d773763` passes all seven operational criteria. The previously frozen second panel `dea14759e9ca` fails home/base untaught change: mean −0.27264003455638885, SD 0.48169047084658934, unchanged permitted absolute mean 0.24084523542329467. The other six criteria and three other untaught cells pass. Home/alternate mean is −0.07415658980607986 with limit 0.10146583493638162. Cumulative home change is −2.8842380046844482 and passes its separate relative limit. No electrical or analytic-tail bound observations occur. The second panel is previously used evaluation data, not newly unseen data.

Root's independent artifact reader recomputes all seven criteria from retained records. Both audits report exactly zero publication reconciliation error. The recording revision preserves all 817 shared arrays byte-for-byte and adds 64 sensory histories. I read the complete audit programs/reports and both panels' complete criterion objects, all 64 row endpoints each and all cumulative endpoints; I did not repeat a circuit or claim to manually inspect every redundant array digest/bin. Sources: `docs/evidence/reward-mechanism-repair-2026-09-12/bridge-{original,heldout}-independent-audit.json`, `bridge-original-recording-parity.json`, `verify_bridge_artifacts.py`, and the two final panel JSON files.

This establishes an **operational failure of this candidate**, despite a correctly implemented and independently tested numerical contract. Smaller absolute drift does not satisfy the mean/SD criterion by itself. The prior numerical/code-quality PASS remains scoped to that contract; it is not withdrawn merely because its scientific hypothesis fails. Acquisition, reversal and improved prediction remain unestablished and held.

## Actual mechanism and primary-source boundary

Current `reward_lif.cpp` constructs all four bridge state families at zero. Electrical activity starts at t=0, but `learning = t >= onset_steps` also gates `bridge->interval`, so no rate or eligibility history from [0,100) ms enters learning. From100ms onward the rule sees actual nonnegative compartment-mean DAN events and actual KC events, without distinguishing sensory-generated DAN spikes from scheduled-teaching effects. A 100ms causal rate filter and 500ms eligibility filter feed the exact antisymmetric integral; the full no-new-event tail follows400ms. This faithfully implements the frozen specification. It is an explicit interface assumption, not an accidental numerical reset defect.

Jiang and Litwin-Kumar use continuous rate histories and optimize the circuitry producing useful DAN activity; merely importing their plasticity expression does not import that learning-signal computation. Their Methods initialize neural rates at declared trial/interval boundaries, with cues later inside intervals. The pinned code resets eligibility alongside those interval resets and otherwise advances eligibility each simulated step. This supports a controlled examination of our electrical/history boundary mismatch, not a claim that their model requires our particular warm history or predicts improvement. Their optimized models also accommodate direct KC→DAN input, so its anatomical presence alone cannot explain failure. [Jiang and Litwin-Kumar, published August10,2021, checked September12,2026](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009205); [inspected runmodel.py at a16f86a3e9e476eff6860c3c0e0e1bbe729d7f85](https://raw.githubusercontent.com/alitwinkumar/jiang_litwin-kumar_mb_rnn/a16f86a3e9e476eff6860c3c0e0e1bbe729d7f85/runmodel.py), especially lines21–27 and46–52.

Hige's experiments directly investigate PPL1-γ1pedc and its corresponding MBON, with odor-specific depression and compartment-dependent induction properties. They do not establish that every untaught endogenous event must yield zero plasticity, nor identify our two-type pooled event signal with local release. The current PPL101/MBON11 and PAM12/MBON09 remain accepted engineered channels. [Hige et al., 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4674068/), rechecked September12,2026 through primary indexed Results/Discussion; direct PMC access was challenged in this pass, so no newly accessed full-methods claim is made.

Handler's opposing receptor pathways motivate temporal sensitivity but do not provide our100/500ms parameters or a universal PPL101 backward-potentiation law. [Handler et al., 2019](https://pubmed.ncbi.nlm.nih.gov/31230716/). Current access returned no new full text; rely only on the explicitly limited primary abstract/figure inspection already recorded in the earlier source report. Bennett's feedback prediction-error circuit is a model hypothesis, not proof that the retained LIF connectivity automatically computes such errors. [Bennett et al., 2021](https://www.nature.com/articles/s41467-021-22592-4), primary abstract/introduction rechecked through indexed publisher content; direct publisher opening redirected to inaccessible authentication.

Thus remaining alternatives include an engineered history boundary, inadequate endogenous learning-signal dynamics, and compartment/release/receptor simplifications. These are competing mechanisms, not confirmed causes. Recurrent contacts do not establish their functional sign or computational role. Do not ablate KC→DAN contacts, impose an outcome-only gate, retune intrinsic drive, or filter home KCs by gamma analogy on the strength of this evidence.

Kernel residual attribution communicated during this review places the second-panel home/base mean into alpha/beta−0.1950508654, gamma−0.0646122843 and alpha-prime/beta-prime−0.0129768848. Its reported phases are100–130ms+0.0004338920,130–300ms−0.0149355978,300–400ms−0.1773929968, and tail−0.0807453319. I subsequently read the complete bridge-residual-attribution-console.json containing these independent worker calculations; they are not new calculations by this reviewer. Retain its full attribution report alongside this proposal. Large post-offset/tail contributions do not exclude earlier history effects propagated through filters, and alpha/beta dominance does not authorize removing those home edges.

## One next investigation: fixed-history shadow comparison

**Question:** Does excluding real [0,100)ms activity from both bridge filters introduce the particular negative untaught bias, or does that bias survive when the signal history is continuous from the existing electrical start?

The alternative is deliberately fixed: initialize R_K,E_K,R_D,E_D to zero at electrical t=0; inject and advance all four filters at every existing0.2ms event step, including [0,100)ms. Suppress gain writes before100ms. At100ms retain the post99.8ms interval state, inject the actual100ms events once, compute Q using prior eligibility, then apply the existing exact interval update. Keep eligibility/rate constants500/100ms, eta0.0005, normalization0.96, bounds0.5/1.5, all masks, electrical events,400ms endpoint and analytic infinite no-new-event tail unchanged. Discard history and double remainder only after the same final float32 checkpoint. Do not subtract a baseline, equilibrate to an inferred tonic state, shift stimulus or learning onset, or try different warm durations.

This first comparison must be a **shadow signal calculation on the unchanged cold-bridge electrical trajectory**. Shadow gains cannot affect transmission, random draws, spikes or the actual checkpoint. It answers a causal question about the mathematical history operator conditional on observed events, not whether the modified gains would change the recurrent circuit beneficially. Run both cold and continuous-history shadow calculations from unit gains with double accumulation and float32 publication, recording attempted versus actually published changes and bounds separately. The actual cold calculation and all pre-existing retained outputs must reproduce their existing identity before interpreting the shadow result.

The current artifacts cannot support an exact retrospective calculation: the per-KC bridge states are zero before100ms; individual KC spikes are not retained at0.2ms resolution. Aggregate KC step counts cannot be distributed among edges without inventing history. Some first-cue individual10ms counts also do not preserve within-bin timing. The existing RewardEngine.run API can capture lossless KC/DAN event rasters throughout[0,400)ms without changing the kernel: set bin_ms=0.2, repeat each existing float32 10ms schedule row exactly50times, record=False and explicitly sample every KC, selected DAN and sensory neuron. The electrical dt remains0.2ms; recording bin width and schedule representation change together. This possibility requires actual parity verification, not an assumption that recording cannot matter. An independent closed-history oracle can then check the native cold result and the proposed shadow.

The bounded capture is exactly33 full-CNS calls: one coarse10ms canonical untaught4362/base call at seed4404, followed by the32 fine0.2ms untaught calls listed below. The first fine call is the same canonical4362/base call and serves as its paired parity check; it is already included among32, not an extra call. All calls start from independent unit checkpoints, retain plasticity=True with the unchanged cold bridge, and use no teaching pulses. Before full-CNS capture, generalized tiny fixtures must prove coarse/fine equality across nonconstant schedules, seeds, samples and pulse/refractory cases. Before the remaining31 fine calls, compare canonical coarse/fine complete neuron counts, final voltages, gains/gain_delta, DAN/compartment counts, and exact50-bin aggregation of population and sampled traces. Any disagreement stops capture. Both representations must preserve the identical sequence of sensory rates and RNG calls at every electrical step.

Sample identities are the sorted unique union of the source-locked circuit's kc_indices, dan_indices and sensory indices, with one column per exact global neuron index. Freeze and store the complete int32 sample array, corresponding source body IDs, mappings to KC-local/DAN-local/sensory-local indices, their hashes, and the existing graph/data/code hashes before capture; verify disjoint-role overlaps without duplicating sample columns. Preserve every returned array; compare all available coarse aggregates and gains against the corresponding retained canonical panel row, not only a new rerun. In particular canonical gains and the recorded sensory history must match the old result. All32 fine captures must match the existing row gain vector and the exact per-compartment DAN step history where retained; sensory50-step sums must match each saved sensory matrix. Scope is diagnostic history capture, not a new qualification panel.

No selection of the worst cue, new cues, cumulative or teaching runs, or adaptive extension. Freeze the recording identity and this contract before capture, with a600second hard execution ceiling across33calls; preserve partial output and stop on failure. This capture is proposed and has not been executed by this reviewer.



Exact32 fine calls, in this order (all condition untaught):

| Cue source index | Noise set | Seed |
| --- | --- | --- |
| 4362 | base | 4404 |
| 4362 | alt | 1004404 |
| 4366 | base | 4408 |
| 4366 | alt | 1004408 |
| 4370 | base | 4412 |
| 4370 | alt | 1004412 |
| 4374 | base | 4416 |
| 4374 | alt | 1004416 |
| 4378 | base | 4420 |
| 4378 | alt | 1004420 |
| 4383 | base | 4425 |
| 4383 | alt | 1004425 |
| 4387 | base | 4429 |
| 4387 | alt | 1004429 |
| 4391 | base | 4433 |
| 4391 | alt | 1004433 |
| 4395 | base | 2004437 |
| 4395 | alt | 3004437 |
| 4399 | base | 2004441 |
| 4399 | alt | 3004441 |
| 4404 | base | 2004446 |
| 4404 | alt | 3004446 |
| 4408 | base | 2004450 |
| 4408 | alt | 3004450 |
| 4412 | base | 2004454 |
| 4412 | alt | 3004454 |
| 4416 | base | 2004458 |
| 4416 | alt | 3004458 |
| 4420 | base | 2004462 |
| 4420 | alt | 3004462 |
| 4425 | base | 2004467 |
| 4425 | alt | 3004467 |

For each trial retain the actual output fingerprint, event raster with shape/dtype/unit metadata, onset states for cold and continuous histories, four phase totals100–130,130–300,300–400ms and separately labeled analytic tail, group and edge-level attempted/double-applied/published changes, and bound observations. The onset-state snapshot is taken immediately before injecting the100ms events. Keep omitted pre100ms would-be learning outside the learned-gain totals; rate evolution there is not a retroactive gain update.

## Predicted falsifier, before any new result

Directional hypothesis: the cold boundary makes home/base untaught change in the second panel more negative than the continuous-history signal operator. Define U_i as the arithmetic sum of final published eligible home-edge gains minus1 for trial i, after electrical intervals and analytic tail. Compare the exact eight existing second-panel/base U_i in the two shadow histories. Necessary directional support is mean(U_continuous−U_cold)>0 **and** abs(mean(U_continuous))<abs(mean(U_cold)). Equality, greater negativity, or a positive overshoot with equal/larger absolute mean falsifies this direction. Report the corresponding double-attempted contrasts so publication rounding cannot impersonate a mechanism. Report every trial and all eight panel/channel/noise guard cells, without dropping outliers.

The stronger claim that this history change alone could repair the operational drift is falsified if the continuous-history shadow fails any of the unchanged untaught guards, abs(mean U)<=0.5 sampleSD(U), or incurs a bound observation. Passing this necessary screen would still NOT qualify a new circuit rule: the shadow omits feedback from its altered gains, does not establish teaching preservation, and is evaluated on already used data. Any subsequent implementation/full panel would need a separate frozen identity, independent tests and all seven original criteria on both panels, followed only then by the separately frozen conditioning gates. No thresholds are changed here.

Canonical native coarse/fine parity is bit equality for matching integer/float arrays and exact integer aggregation for binned spikes. The independent cold signal oracle must reproduce each final float32 gain exactly, and grouped attempted interval/tail totals within rtol=1e-8, atol=1e-10, before interpreting a warm comparison. A discrepancy is a stop for investigation, not permission to relax tolerance or substitute a favorable implementation.

Independent numerical tests must first verify exact state handoff versus uninterrupted convolution at100ms; events just before/at/after the boundary; coincidence and one-sided histories; a pre-only history with nonzero post-boundary rate tail; no-prehistory equality with the current cold rule; zero pre100ms gain writes; no duplicate100ms injection; double/publication/bounds/tail accounting; and absence of changes to the actual electrical trajectory. Use the independent sum-of-impulse responses or quadrature, not only a duplicated native recurrence.

## Adverse evidence and stopping discipline

The earlier raw-event onset-history calculation found warming worsened mean attempted untaught change from−0.2647040066 to−0.6415823583, with negative corrections in both noise sets. Its direct cross-boundary oracle and parity checks passed. This is adverse evidence against treating warm history as a convenient repair. It is not a measurement of this two-filter bridge; the altered cross-boundary kernel and continuous tail require their own test. Source: `output/collaboration/reward-repair/codex-scratch/onset-history-and-mask-validation.json` (read completely again).

If the proposed fixed comparison worsens drift, stop this boundary hypothesis. Do not sweep onset, tau, baseline or clipping to obtain a passing guard. A later learning-signal-generation investigation would need a new anatomically grounded causal design. This report recommends exactly the bounded history comparison above, not several simultaneous mechanisms or a new physiological claim.
