# After the 2018 confirmation: other ways to use the MaleCNS circuit

**Written September 14, 2026, before the 2018 result, on the assumption it repeats the 2022 development verdict** (better than chance, no contribution over the frozen twin, worse than the encoder alone). Nothing here is authorized to run; each item names a finite question, the anatomy it would use in this dataset, the honest comparator, and why it might beat what we have. Every item needs a new identity and a still-unused data block (2017 or earlier MLB seasons; 2018 is spent after its one attempt).

## Why the current design cannot beat the encoder

The plastic circuit is asked to learn team value from binary outcomes, delivered as sugar to an arbitrary team odor. That is a running win count per team. The encoder already holds Elo, form, win rate and margin, which are better estimates of the same quantity, and the readout sees them side by side. A learned feature that is a noisier copy of an encoder feature cannot lower log loss. So the levers are: give the circuit information the encoder does not have, make the learning signal something other than raw wins, or use a circuit computation (comparison, integration, feature extraction) that a five-coefficient logistic does not perform. Everything below is one of those three.

## What the imported graph contains beyond the mushroom body

Counts below were read from the locked graph arrays and saved manifests with zero neural calls by [`audit_anatomy.py`](evidence/wiki-integration-2026-09-14/audit_anatomy.py); the full output, including compartment body ids, LH/MBON convergence, stress-test gain deciles and sports-row storage, is [anatomy-and-storage.json](evidence/wiki-integration-2026-09-14/anatomy-and-storage.json) (checked 2026-09-14 UTC).

| Population (MaleCNS v1.0 as imported) | Count | Why it matters |
| --- | ---: | --- |
| Optic-lobe intrinsic neurons (`ol_intrinsic`) | 89,403 | Full medulla/lobula circuitry: L1 1,776; Mi types 5,054; Tm types 28,042; Dm 8,258; T4 6,865; T5 6,720 |
| Photoreceptors (`ol_sensory`) | 6,098 | R1–R6 3,377; R7 1,385; R8 1,329: a retinotopic input surface |
| Visual projection neurons | 9,201 | LC 4,257; LPLC 417; LLPC 761; MeVP 917; the optic glomeruli and their descending targets |
| Visual input to Kenyon cells | 252 cells, 11,094 contacts | 8,041 of them onto the 206 `KCg-d` cells (aMe12, aMe26, MeVP41, LoVP42, MeVP36, aMe20 …): the visual accessory-calyx route documented in the hemibrain (Li et al. 2020) and used by visual memories that share DANs with olfactory ones (Vogt et al. 2014) |
| Central complex (`CX`) | 2,950 | ER ring neurons 282; EPG 50; PEN 42; PFL 50; fan-shaped body columnar hΔ/vΔ 619 and FB tangential 602 |
| MB → CX contacts | 8,543 | MBON output reaches the fan-shaped body directly; MBON→DAN 11,309; CX→DAN 3,852 |
| Other sensory classes | tactile 2,558; proprioceptive 1,454; mechanosensory 1,733; hygrosensory 66; thermosensory 25 | Additional labelled input channels never used |

## Candidate approaches

### 1. Visual cue through the accessory calyx (γ-d Kenyon cells)

**Idea.** Replace the arbitrary 16-type odor with a visual cue: drive the visual projection neurons that innervate `KCg-d` (or drive the photoreceptors and let the optic lobe compute) so that a matchup becomes a visual scene. The same PAM08/PAM01 reward and the same version-2 rule apply; the eligible synapses become the `KCg-d`→MBON05/MBON01 edges (the 206 γ-d cells carry 6,038 contacts onto MBON09 alone and are part of the γ4/γ5 pools).

**Why it could help.** Visual scenes can carry graded, structured pregame information (a 2-D pattern of several quantities) rather than an identity code, and the γ-d population is small enough that saturation and overlap are easier to control. Biologically it is the documented visual-memory pathway.

**Finite question.** Do photoreceptor or VPN patterns produce sparse, stimulus-specific `KCg-d` activity at 0.11 mV/contact with the local-neuron interventions we already need, and do they reach MBON05/MBON01? Links measured first, exactly as in Section 2 of the contract. Cost: one links run (≈ 50 calls). Risk: the optic lobe is 90,000 recurrently connected neurons under a sign proxy that already misbehaved in the antennal lobe; expect to need measured interventions.

### 2. The optic lobe as the encoder (connectome-constrained feature extraction)

**Idea.** Render pregame quantities as a small image (rows = quantities, columns = home/away, intensity = value), drive R1–R8 retinotopically, and read the optic-glomeruli outputs (LC/LPLC types, or T4/T5 motion channels if the image is presented as a short movie) as the feature vector for a fitted readout. Precedent: Lappalainen et al. 2024 (Nature, DOI 10.1038/s41586-024-07939-3) trained a connectome-constrained model of 64 optic-lobe cell types and predicted neural responses across 26 studies, so the optic-lobe anatomy is known to support useful computation when its unknown parameters are fitted.

**Why it could help.** It is the one part of the fly brain that is proven to compute something nontrivial from structured input. If the anatomy is a good prior for feature extraction, a readout on LC/T4/T5 activity could carry interactions between quantities that a linear encoder lacks.

**Honest comparator.** A same-information nonlinear model (e.g. a small gradient-boosted classifier on the same 16 features). The v1/v2 result already showed a fitted readout on the whole MB output loses to a logistic baseline, so this must be judged against a strong conventional model, not against the encoder alone.

**Finite question.** Does a fixed (plasticity-off) optic lobe at the qualified coupling turn a two-column intensity image into LC/T4/T5 responses that differ reliably between matchups and recover after the stimulus? Cost: links run plus a development block. Requires a fitted readout, so it can never be more than an engineered comparator unless combined with 4.

### 3. In-circuit comparison in the central complex (instead of external subtraction)

**Idea.** The current pipeline compares home and away outside the circuit (log-ratio of two probes). The fly compares options inside the fan-shaped body: MBON output reaches FB tangential neurons (8,543 contacts), the EPG/PEN compass represents headings, and PFL3 neurons convert a goal-versus-heading difference into a steering signal. Present the home and away cues as two "headings" (drive two EPG wedges, or two ER ring-neuron subsets), let learned MBON valence reach the FB, and read the PFL2/PFL3 asymmetry as the choice.

**Why it could help.** It answers the open gap "the two-source comparison is external, not neural", and it gives a readout that is a decision, not a rate. Recent work on goal-directed navigation (Westeinde et al. 2024; Hulse et al. 2021 for the CX connectome) supports PFL3 as the comparison node.

**Finite question.** Does drive to two EPG/ER subsets produce a stable, opposite PFL2/PFL3 asymmetry that flips when the driven subsets swap, with plasticity off? Cost: one links run. Risk: the ring attractor needs balanced inhibition that our sign proxy may not provide.

### 4. A better learning signal: prediction error, punishment and multiple timescales

**Idea.** Three changes that stay inside the mushroom body:

- **Reward prediction error through MBON→DAN feedback.** The dataset has 11,309 MBON→DAN contacts. Bennett et al. 2021 model reinforcement as outcome minus the MBON-predicted valence; then dopamine to a team's cue becomes "won more than expected", and the learned quantity is a win rate estimate, not a cumulative count. This removes the drift that forced the recovery term. Implemented by feeding the MBON01/MBON05 cue response back into the reinforcer rate (engineered feedback, or the anatomical feedback if it transmits).
- **Punishment for losses through a PPL1 compartment.** Today a loss is silence. Driving PPL1-γ2α′1 (PPL102) or PPL1-γ1pedc (PPL101) with its own compartment (MBON12 / MBON11, approach-promoting) gives a two-sided value with opposite-sign expression, which is how the fly encodes both.
- **Compartments with different memory timescales.** Aso & Rubin 2016 show compartments learn and forget at different rates; a γ compartment for recent form and an α/β compartment (PAM11/MBON07 α1, long-term) for season strength would let the readout separate "hot streak" from "good team". Our version-2 rule already has a per-compartment ρ, so this is a parameter declaration plus a new compartment list.

**Finite question.** Re-run the conditioning battery with each change (identity, timing, lesion controls unchanged); then a 2022 development arm. Cost: conditioning ≈ 400 calls per variant, arms ≈ 6,500 calls each (Hugging Face, ≈ 1 h each).

### 5. Information the encoder does not have, through separate sensory channels

**Idea.** The encoder sees 16 aggregate numbers. Give the circuit raw streams the encoder never sees, each on its own sensory class: run differential and home/away streak on tactile channels, rest and travel on thermo/hygro channels, and let dopamine-gated plasticity decide which channels predict reward. Then the same-information comparator must receive the same raw streams, and the question becomes whether the circuit's feature selection beats a conventional learner on identical inputs.

**Why it could help.** It is the only route by which the circuit can carry information the encoder lacks; without it the ceiling is the encoder.

**Finite question.** Which of the extra streams change the 2022 development log loss of the same-information baseline at all? If none do, the fly cannot help either, and that is a cheap negative result before any neural run.

### 6. Fit the unknown parameters of the actual circuit to the task

**Idea.** Treat sign, gain and time constants as unknowns and fit them on the prediction task with gradient descent through a rate surrogate constrained by the MaleCNS graph, as Lappalainen et al. did for the optic lobe and as v1/v2 did for the 61,210 KC→MBON edges only. Extend the fitted set to the MB input side (ALPN→KC, VPN→KC) and the MB output side (MBON→downstream).

**Honest reading.** This is machine learning with an anatomical prior; it says nothing about dopamine learning, and v2 already lost to a logistic baseline with 61,210 free gains. It would be justified only if the optic-lobe precedent (item 2) shows the anatomy is a useful prior for this input format.

### 7. MaleCNS as a temporal reservoir (David, September 14)

**Idea.** Stop asking KC→MBON synapses to store season-long team strength. Use the fixed 25.6-million-edge recurrent graph as a nonlinear temporal reservoir: present pregame-available history as a *sequence* (recent games, score differentials, opponent strength, rest and travel, pitcher or team state where available, and the encoder's uncertainty), let the circuit state evolve across the sequence, and fit one small frozen readout on the resulting neural state. Plasticity off; the computation is the recurrent dynamics.

**Why it could help.** Reservoir computing exploits exactly what the graph has and the associative stage ignores: 166,700 neurons with heterogeneous fan-in, delays and mixed signs. The v1/v2 readouts used only an 80 ms static probe; a sequence-driven state is a different object.

**Controls that decide whether the anatomy matters.** (i) The same features flattened into a conventional model; (ii) an echo-state / random reservoir with matched state dimensionality and spectral radius; (iii) a degree-preserving rewiring of MaleCNS (the null-graph machinery from v2 already exists); (iv) a fully randomized recurrent graph. Anatomy contributes only if MaleCNS beats (ii)–(iv) on the same readout procedure. Interpretation is the same as the sensory stage: an engineered encoder-in, fitted readout-out comparator, not a fly behaviour.

**Finite question.** Do sequence-driven states differ reproducibly between matchups and carry information beyond the flattened features on the 2022 block? Cost: one probe per game per arm (≈ 2,400 calls, ≈ 0.5 h per arm on Hugging Face) plus the three null graphs.

### 8. Richer readout before more simulation

**Idea.** Before any new architecture, ask whether the circuit already produces incremental information that the current two-channel readout discards: read all relevant MBONs, MBON plus downstream convergence cells, fan-shaped-body targets, and other anatomically justified downstream populations, with the same fixed logistic procedure and the same comparators, on development data only.

**What the existing recordings hold.** The 2022 sports rows store only the two summed MBON05/MBON01 counts per probe (`home_response`, `away_response`), not sampled traces. Every UTC-day checkpoint of every arm is saved, so a richer readout requires re-probing each team cue at each saved checkpoint with a wider sample: ≈ 6,400 plasticity-off probes per arm (≈ 1 h on Hugging Face), no new reinforcement, no new outcomes. The conditioning runs did save full sampled traces (all KCs, both MBON pairs, the reward DANs) and can seed the channel choice.

**Finite question.** Does any anatomically justified channel set lower the 2022 second-half log loss of the plastic arm below its frozen twin and below the encoder, under the fixed readout procedure? If not, the learned state carries nothing the current readout misses, and further readout work stops.

### 9. Interference and credit assignment (not just forgetting)

**What the forgetting run showed.** The retired cue was not forgotten; it kept being depressed by the seven cues that were still reinforced (−15 → −46 without recovery). With 16-type codes, cues share Kenyon cells (calibration Jaccard mean 0.14, max 0.44), so every reinforcement writes to synapses that other memories depend on. That is representational interference, a credit-assignment failure, and recovery only limits the damage.

**Quantify, on saved artifacts first.** KC overlap between the 30 team cues (from the links run) and between conditioning cues; overlap versus unintended gain change (the swap arm already shows B-edge depression −0.030 from A reinforcement at Jaccard 0.39 versus −0.009 at 0.13); how many cues share each eligible edge (the edge-sharing histogram from the calibration KC sets); whether interference predicts memory corruption (regress the retired cue's drift on its shared-edge count); and whether recovery improves *specificity* (contrast between a cue and its overlapping neighbours) or only depth.

**Remedies to test separately, each a new identity.** Sparser cue codes (fewer ORN types at higher rate; the 4–8-type codes recruited 0.1–1% of KCs but missed MBON05, so the rate must rise); cue families chosen for near-orthogonal KC sets (the stress-02 follow-up needs Jaccard ≤ 0.05); compartmentalized memories (assign cue families to different compartments); different compartments for different timescales (item 4). Raising ρ until interference vanishes is not a remedy: it erases memory (−15 at ρ = 0.04).

### 10. Residual / surprise learning

**Idea.** The reinforcer today is "won" — a signal redundant with Elo, form and win rate. Instead make dopamine proportional to what the frozen pregame probability did **not** predict: reinforce with the outcome residual (win minus encoder probability, signed through the reward and punishment compartments, or magnitude-scaled reinforcer rate). The circuit is then asked to learn residual structure the encoder misses, which is the only thing that can lower log loss below the encoder.

**Key control.** A same-information online non-neural residual learner (for example an online logistic on the same residual stream and team identity), plus the frozen and shuffled twins. If the conventional residual learner gains nothing, the residual is noise and the circuit cannot help; if it gains and the circuit does not, the circuit is the limit.

**Finite question.** Conditioning battery with a graded reinforcer (rate proportional to residual magnitude; punishment compartment for negative residuals), then a 2022 development arm. Uses the existing harness; the only new mechanism is the reinforcer schedule and, for negative residuals, a PPL1 compartment.

### 11. Visual pathway: avoid the image-wrapping trap

Rendering the encoder's probability or Elo as pixels and reading it back out is not new computation. Any visual design must state exactly what structured information enters the scene (which quantities, in which spatial arrangement, at what contrast), and the conventional comparator must receive the identical rendered data. Three separate hypotheses, never pooled:

- **11A. Visual system as a fixed nonlinear encoder** (item 2): photoreceptors → lamina/medulla/lobula → visual projection neurons; readout on LC/LPLC/MeVP activity; comparator is a nonlinear conventional model on the same rendered data.
- **11B. Visual associative learning** (item 1): visual projection neurons → accessory calyx → γ-d Kenyon cells → MB outputs, with the qualified dopamine rule; comparator is the frozen twin.
- **11C. Actual bilateral choice** (items 3 and 13): two visual alternatives → learned MB value → central complex / fan-shaped body → PFL3 or other steering-related output.

### 12. Lateral horn plus mushroom body integration

**Idea.** The fly separates innate stimulus value (lateral horn) from learned, contextual correction (mushroom body) and integrates them downstream. The dataset supports this decomposition: 2,028 LH-typed cells receive 443,271 contacts from ALPNs (more than the 390,928 onto Kenyon cells); MBONs send 36,712 contacts to LH neurons and receive 21,199 back; 1,766 cells receive at least 20 contacts from both MBONs and LH neurons (including 86 DANs, 59 central-complex cells and convergence types such as CRE055 and LHPV6a1); LH neurons reach descending neurons with 22,810 contacts against 4,347 from MBONs.

**Why it could help.** A pregame quality signal could be represented as innate value in the lateral horn (fixed, calibrated, the analogue of the sensory stage) while the MB learns only the residual (item 10); the readout then sits at the anatomical convergence cells rather than at two MBONs. This is more biologically faithful than forcing every useful computation through MB plasticity.

**Finite question.** Do LH neurons respond to the team-odor codes at the qualified coupling, and do the convergence cells carry both the innate and the learned signal in the conditioning battery? Links first.

### 13. Physiological calibration, separate from any sports fit

**Idea.** Fit the simulator's dynamics to published fly recordings, not to baseball: membrane and synaptic time constants, per-contact gain, inhibition (the APL and antennal-lobe local-neuron proxies we had to zero), response scaling and cell-type dynamics. Sources to use: Lappalainen et al. 2024 (connectome-constrained optic-lobe parameters validated against 26 studies), Shiu et al. 2024 (the LIF constants we inherit), Honegger et al. 2011 and Turner/Hige recordings for KC sparseness and MBON responses, Zhao 2022 and Cameron 2010 for sensory rates already recorded in the wiki, and the DoOR/Hallem odor responses for ORN-type tuning.

**Rule.** Physiology-derived parameters are frozen before any sports evaluation and recorded with their source; dynamics are never optimized on MLB outcomes and then called anatomical. The current interventions (ALLN out 0, APL out 0, DA fast out 0, 0.11 mV/contact) are engineering fixes to sign-proxy failures and should be the first targets of a physiological fit.

### 14. Full sensory-to-motor choice

**Idea.** The strongest claim: two alternatives represented simultaneously, their value integrated in the circuit, and a descending or motor-related output choosing one. Anatomy available: MBON → central complex 8,543 contacts; central complex → descending neurons 7,187; LH → descending 22,810; 1,314 descending neurons in the import. The readout becomes a descending-neuron asymmetry, not a Python subtraction.

**Finite question.** With plasticity off, do two simultaneously presented alternatives (two odor codes, or two visual alternatives per 11C) produce a reproducible, swap-reversing descending-neuron asymmetry? Only after that does learned value enter. This is the endpoint of items 3, 11C and 12, not a starting point.

## Re-ranked roadmap (September 14)

Scores are 1 (low) to 5 (high). "Hides the encoder" is the risk that the result is the conventional encoder wearing a biological interface; lower is better. "Block" says whether an unused confirmation block would be needed to make a prediction claim (2018 is spent by the running confirmation; 2017 and earlier remain).

| Rank | Approach | Novelty | P(incremental value) | MaleCNS contribution | Cost | Controls | Hides encoder (risk) | Block needed |
|---|---|---|---|---|---|---|---|---|
| A | 8. Richer readout from saved 2022 checkpoints | 2 | 2 | 3 | 1 (re-probe, ≈ 1 h/arm, no new outcomes) | strong (same procedure, twins) | 3 | no (development only) |
| B | 7. Fixed temporal reservoir | 4 | 3 | 5 (uses the whole recurrent graph) | 2 | strongest (matched reservoir, rewired, random) | 2 | yes for a claim |
| C | 10. Residual / surprise learning | 4 | 3 | 3 | 2 (existing harness) | strong (online residual learner, twins) | 2 | yes for a claim |
| D | 9. Interference reduction / compartmental memory | 3 | 2 | 4 | 2 (artifact analysis first) | strong (swap/overlap already measured) | 1 | no until a sports arm |
| E | 11B / 1. Visual accessory-calyx learning | 4 | 2 | 4 | 4 (optic lobe never simulated here) | as conditioning-02 | 2 | yes for a claim |
| F | 3 / 11C. Central-complex in-circuit choice | 5 | 2 | 5 | 4 | swap/side controls | 1 | no (mechanism claim) |
| G | 14. Full sensory-to-motor assay | 5 | 1 | 5 | 5 | swap/side/lesion | 1 | no (mechanism claim) |
| — | 5. Extra features, conventional test | 1 | 3 | 0 | 1 | n/a | n/a | no |
| — | 12. LH + MB integration | 3 | 2 | 4 | 3 | links first | 2 | later |
| — | 13. Physiological calibration | 3 | — | 5 | 3 | source-bound | 0 | no |
| — | 11A / 2. Optic lobe as encoder | 3 | 2 | 3 | 4 | nonlinear comparator | 4 | yes |
| — | 6. Fitted circuit parameters | 1 | 2 | 2 | 3 | v2 precedent (lost) | 5 | yes |

Order of investigation: **A, B, C, D, E, F, G.** The extra-features conventional test (5) runs in parallel because it is cheap; a positive result there is a fact about the data, not evidence for any neural architecture. Physiological calibration (13) should precede E–G because the optic lobe and central complex have never run under this simulator and the sign proxies already failed twice. The lateral-horn decomposition (12) becomes the readout site for C once its links are measured. Nothing selects anything using the 2018 result; 2018 is not touched again.

## The bar (and the first ordering, superseded by the re-ranked roadmap above)

1. **Item 5 first, because it is cheap and decides everything else.** If no extra stream improves a conventional model on 2022, no circuit will; stop there.
2. **Item 4 (prediction error + punishment + timescales)** on the existing odor pathway: it keeps the qualified mechanism, fixes the reason the learned value is a noisy win count, and reuses the whole harness.
3. **Item 3 (central-complex choice)** as the biological answer to the "external comparison" gap, independent of prediction gains.
4. **Items 1 and 2 (visual pathways)** only with a measured link stage first; they are the largest engineering risk because the optic lobe has never been simulated in this repository.

The bar for any of them is unchanged: a fresh unused block, a fixed readout procedure, matched frozen and shuffled twins, encoder-only and same-information comparators, and the paired weekly bootstrap. "Better than the encoder" is the claim to make; "better than chance" was already made by the frozen sensory pipeline in 2023 and does not need repeating. For calibration of expectations, the MLB bookmaker diagnostic in the model card puts de-vigged Bet365 at log loss 0.6806 on 1,159 validation games against 0.6828 for the feature logistic; no circuit result should be sold as an edge over that.
