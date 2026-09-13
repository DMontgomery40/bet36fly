# Quantitative transfer decision: two intracellular order-sensitive branches

Checked 2026-09-13 UTC at `f08e88e`. **The evidence fixes a useful structural
alternative to the antisymmetric rule, but does not yet fix a complete
spike-driven two-branch kinetic model.** This bounded check found a related
published IP3-receptor model with numerical inhibition parameters. It does
not supply the missing fly dopamine-to-IP3 or cAMP-to-plasticity conversions.
No parameters were selected and no candidate, fit or circuit was run.

The next implementation decision can therefore be concrete: either declare
those conversions and state kinetics as engineering assumptions, or obtain a
complete independently specified biochemical model before freezing a
candidate. Calling the previous three-state sketch “source-calibrated” is not
an available option. The rejected KC-local L/C mapping is a different model
and is not reconsidered here.

## What the primary evidence fixes

**Handler 2019.** Fresh accessible Results and targeted Methods establish
coincidence-enhanced DopR1/cAMP-associated depression and DopR2/Gq-associated
ER release/potentiation with dopamine first. Release-side signals were similar
between orders. IP3-receptor order sensitivity is a proposed explanation,
not an identified KC kinetic scheme. The explant protocol uses a **500 ms KC
ACh puff**, five **100 ms DAN ATP pulses separated by 20 ms**, and at least
**20 s** between stimulations. ISI means DAN onset minus KC onset; reported
plasticity conditions include −1.2, 0 and +0.5 s, with little effect at 6 s.
ER responses are averaged over 1 s after KC activation; cAMP over 4 s after
DAN activation. These windows are not relaxation constants. Figure 5F
subtracts separately min–max-normalized reporters; it does not identify
branch gains. Primary measurements emphasize γ4/γ5; γ2 has additional
plasticity evidence. [Cell 178, DOI 10.1016/j.cell.2019.05.040](https://pmc.ncbi.nlm.nih.gov/articles/PMC9012144/).

**Himmelreich 2017.** Previously inspected primary indexed text supplies
HEK-cell BRET EC50s: DAMB–Gq 56.7 nM, dDA1–Gs 0.61 μM and DAMB–Gs
7.37 μM; DAMB activation rates at 100 μM DA are 2.71 s⁻¹ through Gq and
0.46 s⁻¹ through Gs. This pass encountered a challenge. These are different
assay pathways and conditions, not KC concentration, dissociation rates or
plasticity conversion factors. DAMB is DopR2/Dop1R2, not the D2-like receptor.
[Cell Reports, DOI 10.1016/j.celrep.2017.10.108](https://pmc.ncbi.nlm.nih.gov/articles/PMC6168074/).

**A directly related quantitative model exists, with an access boundary.**
The primary indexed text of *Inositol 1,4,5-Trisphosphate-Dependent Ca2+
Threshold Dynamics Detect Spike Timing in Cerebellar Purkinje Cells* describes
an IP3 activation site, a calcium activation site and four calcium inhibition
sites: `R → RI → RIC` versus `R → RC → RC2 → RC3 → RC4`. It estimates
inhibition `kf = 2.22 μM⁻¹ s⁻¹`, `kb = 5 s⁻¹`, and a fitted cooperativity
factor 3; the multiplicative cooperativity is explicitly a simplifying
assumption. This gives numerical constraints for that **Purkinje model**, not
fly receptor rates. The direct page challenged; full activation reactions,
calcium/IP3 production, pumps, buffers, initial conditions and any executable
source were not inspected. The excerpt cannot reconstruct the full model.
[Primary article, PMID 15673676](https://pmc.ncbi.nlm.nih.gov/articles/PMC6725626/).

Hige's previously inspected γ1pedc backward condition had no significant
effect; Cohn's local γ4 calcium/plasticity observations do not calibrate γ3
or γ1pedc receptor kinetics. Their complete prior access limits remain in the
[source ledger](dopamine-signal-sources-resumed.md). Neither a γ4 order curve
nor a vertebrate IP3 model licenses an all-class home or away γ3 transfer.

## Exact mathematical boundary

Current `RateBridge` implements `dg/dt = η·0.96·(E_D R_K − E_K R_D)`.
The 100/500 ms filters start cold at the 100 ms onset and their entire linear
tail is integrated. Equal proportional KC/DAN histories cancel identically.
A separate coincidence depression drive plus an order-sensitive positive
drive would remove that algebraic constraint; it need not rescale either old
product. This is a structural engineering distinction, not a demonstrated
cause or cure of the saved null drift.

The earlier occupancy equations are still an engineering sketch. The shared
`ready/primed/inhibited` pool represents hypothetical IP3-channel states;
it must not be presented as two dopamine receptors competing for a measured
common occupancy pool. Returning a primed site to ready on every ER-output
event assumes a consumption/reset mechanism. Channel opening need not consume
IP3, and calcium-store depletion/refilling are separate quantities. No
inspected fly data establish that reset rule.

Even an equilibrium activation curve would not determine the dynamics.
For example, in the illustrative mass-action equation
`dx/dt = kon·D·(1−x) − koff·x`, multiplying both rates by the same constant
preserves the equilibrium curve and changes timing. EC50 is an operational
assay sensitivity, so equating it with `koff/kon` already requires additional
assumptions. A high-dose BRET onset rate alone supplies neither that complete
pair nor the downstream calcium/IP3/cAMP time course.

The still-required quantitative contract is:

| Quantity | Evidence status / required decision |
| --- | --- |
| Local extracellular DA and KC calcium inputs | Need units and spike-to-concentration/activation maps, baseline, saturation and spatial pooling. MaleCNS contacts do not provide these. |
| DopR1 coincidence branch | Topology is supported; its nonlinear coincidence function, relaxation and conversion to gain remain unfilled. |
| DopR2/IP3/ER branch | Order-sensitive topology is supported; a complete receptor scheme, IP3 production/removal, calcium buffering/store recovery and conversion to gain remain unfilled. |
| Branch balance | Reporter normalization does not supply a physical ratio. Fixed η = 0.0005 cannot conceal a new amplitude rescaling. |
| Compartment application | A common rule across all 4,184 home edges and 3,239 eligible away edges is an explicit transfer assumption; eligibility and fast transmission remain unchanged. |
| Initial state and endpoint | Equilibrium, cold state, state persistence and full-tail handling require declarations. No source fixes the simulator's call reset. |

## The present protocol imposes a sharp limit

Our 400 ms electrical trial cannot contain even the source's 500 ms KC
stimulation, let alone its two separated induction onsets and complete DAN
pulse train. Its post-400 ms no-input tail cannot substitute for omitted
physical input. Conversely, reporter averaging for seconds does **not** prove
that all receptor action is too slow to begin within 400 ms. The defensible
claim is that the current protocol is a short engineered test whose transfer
cannot be validated by pretending to reproduce those stimulation conditions.
No rescaling of milliseconds into seconds is justified.

The fixed 100 ms write onset is also not a biological refractory boundary.
Starting chemical state at zero there discards preceding physical signaling;
evolving it from time zero changes the signal-history contract. Either choice
must be explicit before a study, and the previously rejected onset-only
shadow is not thereby revived. No change is selected in this review.

A nonlinear receptor model needs its own entire no-new-input continuation.
Finite concentrations, baseline occupancy, store depletion or spontaneous
calcium release can persist after the last spike. The old two-exponential
tail is not its solution. A candidate must establish that plasticity output
is integrable during that continuation, identify its resting state and define
checkpoint/reset semantics; otherwise “full tail then reset” is not complete.
An external-US-only gate is not an acceptable substitute.

## Minimal useful next deliverable

Freeze a **standalone source-protocol order-response specification** before
any BET36FLY replay. It should hold dopamine input identical between orders,
separate the two branch outputs, and require coincidence depression plus the
declared order-sensitive ER branch, with receptor-removal controls and full
post-input recovery. These are source-motivated functional invariants;
positivity, conservation, interval subdivision and finite-tail checks are
engineering requirements. There is no source basis to demand exact odd
symmetry, coincidence zero, equal branch amplitudes, a midpoint restoration
law or zero untaught drift for arbitrary ongoing input.

The decision needed to make that specification executable is a named complete
kinetic system **or** an explicitly engineered system with all input maps,
rates and output conversions fixed independently of BET36FLY outcomes. This
search did not provide a complete public fly kinetic implementation or raw
source-data package; the prior Handler availability statement remains
scripts/data upon request, not an inspected executable molecular model.
The partial Purkinje equations are a bounded future retrieval lead, not
permission to fill missing rates by analogy. No further lookup, fit or
candidate execution follows from this report.
