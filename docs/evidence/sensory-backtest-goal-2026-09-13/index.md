# Sensory-to-backtest goal — September 13, 2026

**Backtest goal achieved.** [The frozen 2023 confirmation passed](RESULT.md); added neural value and full feeding remain unqualified. The chronology below preserves earlier failed and preconfirmation states. The exact taste crosswalk is now resolved to source-proposed functional classes. A first native assay failed, and its matched DPM diagnostic did not explain away the failure. V1 and all legacy results remain unchanged.

## Sources and transfer limits

Checked September 13, 2026: [Tastekin Cell 2026 Figure 2](https://ars.els-cdn.com/content/image/1-s2.0-S0092867426009438-gr2.jpg), [supplemental figures](https://ars.els-cdn.com/content/image/1-s2.0-S0092867426009438-mmc1.pdf), [original cell workbook](https://ars.els-cdn.com/content/image/1-s2.0-S0092867426009438-mmc2.xlsx), and [December 13 2025 preprint v2](https://www.biorxiv.org/content/10.1101/2025.08.25.671814v2.full.pdf). Exact file hashes are in [source-lock.json](source-lock.json). The previous access failure is historical; its artifacts are preserved.

Published Figure 2 proposes sweet LB3b/c (34 native cells), water LB3a (17), and bitter LB1a–d (38); exact native MN9 IDs are 10331 and 16949. These functional labels arise from morphological matching to genetic driver anatomy, not molecular sequencing of the EM specimen. The complete source table is preserved in CSV and selected populations fail closed on native type/ID disagreement. LB3d is high salt/heavy metal, not sweet. Unknown/incomplete labellar cells are excluded.

[Cameron et al. 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC2865571/) reports first-second bristle spike frequencies: 100 mM sucrose 58.9 ± 3.3 Hz, water 12.0 ± 0.9 Hz, 10 mM caffeine 18.8 ± 3.0 Hz (SEM). All solutions contain 1 mM KCl. Sucrose/water use l-type sensilla; caffeine uses i-type Gr66a controls. Means are explicit in primary Results, not digitized. Transferring these means uniformly to source-proposed native classes, zero precontact background and a constant one-second waveform are model assumptions. Exact bristle subclasses, spontaneous baseline, adaptation waveform and mixture physiology remain unresolved. Selective sweet+bitter coactivation is not a calibrated chemical mixture.

The [Shiu model](https://github.com/philshiu/Drosophila_brain_model/blob/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960/model.py) uses a free 0.275 mV/contact weight, 20/5 ms membrane/synaptic constants, 1.8 ms delay, 2.2 ms refractory and 68.75 mV external events with sensory refractory removed. Its generic dopamine-positive proxy is explicit in the [primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/). These are simulation choices on female FlyWire, not validated native MaleCNS parameters or natural sugar rates. Native engine count/trace equivalence was tested against the existing fixed engine on small recurrent graphs; this is software evidence.

## Frozen assay 01: failed

Identity `sensory-42234be994aca8e42414`, [protocol](../../../configs/sensory-assay-01.json), 16 completed native calls, no plasticity, complete retained graph and original sign proxy. Three seeds per condition plus exact sweet repeat. Mean MN9 stimulus rates: null 0, water 0, sweet 63.833, bitter 23.167, mixed 4.5 Hz. Sweet activation, mixture suppression and repeat passed. Water activation and nonappetitive bitter guards failed. Generator checks passed; requested Poisson events and actual sensory spikes are separately saved.

Large post-offset recurrent population activity remains despite the original loose numerical guard passing. Bitter seed43 activated MN9 10331 at 135 Hz during stimulation and continued after offset. This is not a qualified natural feeding response. Original configuration/code hashes and all per-neuron/bin artifacts remain frozen under `output/sensory/sensory-42234be994aca8e42414`.

## DPM diagnostic: insufficient explanation

[Haynes et al. 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4305081/), DOI 10.7554/eLife.03868, contains GABA/Gad1 and serotonin staining, absent TH/ChAT, and DPM-evoked MB chloride responses blocked by picrotoxin. Read the transmitter, functional inhibition, receptor and interpretation sections and their relevant figure captions. This conflicts with native DPM dopamine predictions at IDs 11734/12569. Uniform fast inhibition across every DPM output remains an all-target approximation; receptor/branch-specific and metabotropic effects are not implemented. Original XML/hash retrieval is preserved separately.

The [six-call matched diagnostic](../../../configs/sensory-dpm-01.json) compared DPM outgoing-zero and negative fast weights to sweet17, bitter43 and mixed17 baselines. All delivered input bins matched exactly. Neither intervention reduced late population activity by the declared 90% in all trials; all six failed that threshold. Thus DPM sign alone is insufficient. No DPM override is promoted to the next assay on this evidence.

## Next bounded decision: native fast-coupling calibration

A new finite assay may calibrate Shiu's explicitly free per-contact magnitude to this distinct specimen, using sensory responses only. It must preserve the original assay failure and all legacy gains, use one uniform magnitude across the complete graph, keep cell/rate identities fixed, and add offset-recovery guards. This is a model parameter calibration, not measured synaptic physiology. Water transmission at the measured mean was largely limited to the injected population; the next target is explicitly narrower sucrose/caffeine channel discrimination. Water remains a descriptive negative result, not a reproduced ingestion assay.

No sports labels or reserved 2023 outcomes have been accessed. Two-probe work still requires an accepted finite sensory proxy and fresh-seed/timing checks. [Goal acceptance protocol](../../EXPERIMENT_SENSORY.md).

## Uniform coupling calibration 01: failed

All 60 declared calls completed. Magnitudes 0.055 and 0.11 mV/contact stayed quiet but failed sweet MN9 activation. At 0.165, sweet was absent/negligible while bitter and mixed inputs triggered persistent population activity. At 0.22, every seed passed sweet activation, nonappetitive bitter and mixed suppression, but recovery failed. No value passed the complete guard. No magnitude is qualified for sports expansion. The complete result manifest is preserved beside this page.

Next diagnostic, declared before execution: at the 0.22 magnitude compare matched sweet401, bitter401 and mixed401 trials against three source-class transmission ablations: pure modulator outgoing fast weights set to zero, antennal-lobe local-neuron outgoing weights set to zero, and their union. Native labels/contacts stay unchanged. The question is whether either class is causally necessary for persistent final-200-ms activity; support requires >=90% reduction in every matched condition with identical delivered input bins. Nine calls maximum. These are diagnostic lesions, not proposed biological replacements or qualified models. They distinguish the observed olfactory recurrence from the previously insufficient DPM-only hypothesis.

## Narrower second-order sensory readout — new protocol rationale

The nine lesions localize most persistent activity jointly to ALLN and pure-modulator fast output: their union reduced late activity by >90% in all three matched conditions, but neither class alone did so universally. Substantial residual activity remained. These lesions are not promoted; the full graph remains the assay model.

A source-defined earlier observation avoids treating MN9 feeding failure as absence of all sensory transmission. Published Tastekin Figure S16/S17 identifies Clavicle and Quasimodo as second-order LB3 partners in feeding pathways. The original native annotation `synonyms` field independently binds Quasimodo to GNG042 IDs **15321/15734**, and Clavicle to ANXXX462a IDs **19480/514625**. Native transmitters are GABA and acetylcholine respectively. This is an exact same-specimen alias join, not a female-ID substitution. Quasimodo's inhibitory transmitter must not be called an excitatory synapse merely because its activity can participate in disinhibition.

Exploratory inspection at 0.11 mV/contact found all four cells responding to sweet (Clavicle 21–32 and Quasimodo 47–52 total spikes in the two-second trials), no response to bitter, and complete recovery. Mixed stimulation reduced Quasimodo responses but did not consistently suppress Clavicle. This is selection evidence, not a fresh pass. The next frozen assay tests these explicit observations using new seeds, both 0.2 and 0.1 ms steps, source-window binned outputs, exact reset repeats and complete recovery. It qualifies **conditional second-order gustatory response only**, not feeding, aversion behavior, innate choice or learning. The earlier MN9 failures remain rejected.

If that narrower assay passes, a separate source-contact recruitment ladder can represent independent opportunity quality while keeping each stimulated sweet cell at the same source-anchored 58.9 Hz mean. The fraction of contacted cells is an engineered spatial recruitment proxy, not a measured dose-response curve. Order must be fixed without neural/sports outcomes, preserve the documented sides and subtype identity, and never select cells by output efficacy. Independent full-reset exposures and external comparisons must remain explicit. This is permitted by the sensory/feeding direction, but weakens the eventual biological claim relative to demonstrated feeding. No sports confirmation result may conceal this limitation.

## Second-order assay 01: passed its narrower guards

Identity `sensory-second-order-e243b80a7806da536f6b`, 32 calls. New seeds503/601/701 at both 0.2 and 0.1 ms passed null, sweet, bitter, mixed-Quasimodo, global recovery and exact-repeat guards. Halving dt changed the four mean sweet output rates by at most 2.82%. MN9 feeding remains unqualified. The next 136-call source-contact ladder and external two-opportunity protocol is frozen separately before execution.

Development source retrieval now contains 5,742 eligible 2019–2021 training games and 2,429 eligible 2022 games. The first retrieval failed on MLB terminal postponed/cancelled records labeled abstract Final; the corrected parser implements the already-declared exclusion and has multi-status regression coverage. The failed source folder is preserved. No 2023 source has been accessed.

## Independent opportunities 01: passed external-probe guards

Identity `sensory-opportunities-3750a28fd2728835047b`, 136 completed calls. The 35-level sweet contact ladder and bitter-only reference passed generator/recovery guards; rank correlation between recruitment count and second-order response magnitude was 0.998317952430659. Equal/equal and poor/poor outputs were identical; good/good remained active and ordered; good/aversive separated. Every re-presentation exactly matched all neuron counts and sampled/input bins from the ladder reference, and swaps reversed the external contrast exactly. This is an engineered comparison between independent reset exposures, not in-circuit choice. The nine-candidate 2019–2022 development batch is now separately frozen.

## Development 01 and confirmation freeze

Nine pipeline candidates completed with303 encoder/bootstrap fits and9 readout fits. Minimum2022 log loss selected encoder C=1.0 and readout C=0.01. Neural development accuracy58.296%, log loss0.674848; encoder-only log loss0.673611. This is development selection, not confirmation and not demonstrated incremental neural benefit. Three source-silenced native controls passed zero downstream output with intact input generators. The final coefficients, response cache, code, source data, eligibility and one-shot2023 confirmation are frozen in `configs/sensory-confirmation-01.json` before source access. The complete software gate will be read before executing it.

## One-shot confirmation 01: passed

The frozen pipeline passed on 2,423 eligible 2023 MLB games: 56.21% accuracy, 95% interval 54.42–58.02%, and log loss 0.680493. Loss improved over chance and the training prior with the predefined confidence bounds. The incremental comparison with the encoder alone includes zero. No refits or new neural calls occurred during confirmation. Every exported prediction and all 10,000 confidence resamples were independently checked; all bound source/code/parameter hashes and 124 protected files match. See [the final result](RESULT.md). Further tuning for this fulfilled goal stopped.
