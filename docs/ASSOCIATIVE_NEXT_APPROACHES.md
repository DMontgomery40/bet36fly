# After the 2018 confirmation: other ways to use the MaleCNS circuit

**Written September 14, 2026, before the 2018 result, on the assumption it repeats the 2022 development verdict** (better than chance, no contribution over the frozen twin, worse than the encoder alone). Nothing here is authorized to run; each item names a finite question, the anatomy it would use in this dataset, the honest comparator, and why it might beat what we have. Every item needs a new identity and a still-unused data block (2017 or earlier MLB seasons; 2018 is spent after its one attempt).

## Why the current design cannot beat the encoder

The plastic circuit is asked to learn team value from binary outcomes, delivered as sugar to an arbitrary team odor. That is a running win count per team. The encoder already holds Elo, form, win rate and margin, which are better estimates of the same quantity, and the readout sees them side by side. A learned feature that is a noisier copy of an encoder feature cannot lower log loss. So the levers are: give the circuit information the encoder does not have, make the learning signal something other than raw wins, or use a circuit computation (comparison, integration, feature extraction) that a five-coefficient logistic does not perform. Everything below is one of those three.

## What the imported graph contains beyond the mushroom body

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

## Recommended order and the bar

1. **Item 5 first, because it is cheap and decides everything else.** If no extra stream improves a conventional model on 2022, no circuit will; stop there.
2. **Item 4 (prediction error + punishment + timescales)** on the existing odor pathway: it keeps the qualified mechanism, fixes the reason the learned value is a noisy win count, and reuses the whole harness.
3. **Item 3 (central-complex choice)** as the biological answer to the "external comparison" gap, independent of prediction gains.
4. **Items 1 and 2 (visual pathways)** only with a measured link stage first; they are the largest engineering risk because the optic lobe has never been simulated in this repository.

The bar for any of them is unchanged: a fresh unused block, a fixed readout procedure, matched frozen and shuffled twins, encoder-only and same-information comparators, and the paired weekly bootstrap. "Better than the encoder" is the claim to make; "better than chance" was already made by the frozen sensory pipeline in 2023 and does not need repeating. For calibration of expectations, the MLB bookmaker diagnostic in the model card puts de-vigged Bet365 at log loss 0.6806 on 1,159 validation games against 0.6828 for the feature logistic; no circuit result should be sold as an edge over that.
