# Intracellular source selection: compartment evidence before a chemical port

September 13, 2026; independent source review from `bcefc77`. No model,
candidate, circuit, fit or saved-history evaluation was performed.

**Proceed with the standalone Aso DA/NO four-state component. Retain the
now-retrieved Doi IP3 source as an explicitly vertebrate reference, without
porting it into MaleCNS.** The former addresses PPL1-γ1pedc and supplies a
complete phenomenological transition law. The latter supplies more detailed
chemical reactions, but its receptor, geometry, inputs and several crucial
parameters belong to a Purkinje-spine construction. Neither is already a
calibrated spike-driven model of our selected cells.

## The concrete next component

I read Aso's complete Methods, relevant Results and Discussion, and its
2020 correction. The [fixed component contract](aso-da-no-component-contract-2026-09-13.md)
is scientifically consistent with that limited scope. It implements the
published equations independently; no author executable has been identified
or run. The correction changes transcript processing and does not change the
model equations. [Aso et al. 2019](https://elifesciences.org/articles/49257),
[correction](https://doi.org/10.7554/eLife.64094).

| Quantity | Fixed source convention |
| --- | --- |
| States | Latent DA/NO effects `d,n`; expressed effects `D,N`, each dimensionless in `[0,1]`. They are not receptor occupancies or messenger concentrations. |
| Inputs | KC and DAN activity during experimental protocols; the component represents them as Boolean levels. |
| Coactivity | `d'=A_D(1-d)`, `n'=A_N(1-n)`. |
| DAN without KC | `d'=-B_D d`, `n'=-B_N n`. |
| Expression | `D'=(d-D)/30`, `N'=(n-N)/600`, with time in seconds. |
| Rates | `A_D=4.3/60`, `A_N=.96/60`, `B_D=.26/60`, `B_N=.16/60`, all `/s`. Induction/reversal rates were fitted to external behavioral data; expression times were assumed from those data. |
| Output | Normalized `w=(1-D)(1+N)`; no existing simulator eta, `[.5,1.5]` bounds or sports readout belongs in this source component. |

The source explicitly initializes expressed effects to zero at the start
of a trial. A rested component starts all four states at zero; arbitrary
valid nonzero inputs are numerical/persistence tests, not experimentally
measured initial conditions. With DAN absent, the contract holds latent
effects fixed. This completes the source's piecewise description and keeps
the assumed background-DAN decay experiment distinct from genuine quiet.
Consequently quiet expression tends to `(D,N)=(d,n)`, not zero. The paper's
background decay rates are a different fitted regime; they must not silently
replace its evoked reversal rates.

The immediate useful invariants are state bounds, exact interval composition,
retained latent memory, distinct future expression from equal current
weights, pathway-null controls from zero, and different KC histories under
one shared DAN input. These are mathematical properties of the specified
model, not the biological eight-cue neutrality criterion. A source-protocol
test may compare acquisition and reversal using the original durations; it
must not claim full behavioral reproduction without the source's odor
population/readout conventions. The source itself does not explain all
long-term consolidation results after spaced training.

## What the home physiology adds

[Yamada, Davidson and Hige 2024](https://physoc.onlinelibrary.wiley.com/doi/10.1113/JP285745)
directly examined γ and α/β KC inputs to MBON-γ1pedc. Dopamine or low-dose
forskolin required KC activation to reproduce presynaptic LTD; cAMP imaging
did not show greater responses in the sparsely activated axons. PKA
inhibition blocked LTD. Pairing sGC agonist BAY 41-2272 with KC activity
produced slower potentiation in both subtypes. Three minute-long pairings
were effective; one was insufficient for consistent long-term plasticity.
α/β depression recovered around ten minutes, whereas γ depression persisted
longer. These findings support distinct activity dependence and expression,
not uniform subtype kinetics or a measured four-state molecular identity.

The physiological induction used 1-ms KC photostimuli at 2 Hz and minute-long
focal drug delivery; recordings resumed 2.5 minutes afterward. Thus 400 ms
does not reproduce this experiment. PPR is informative but does not uniquely
identify a molecular target. Raw data are available on request; the inspected
paper provides no executable intracellular kinetic model. Home remains all
4,184 eligible edges: neither these results nor γ4 reporter evidence justify
gamma-filtering home. They also do not calibrate PAM12/γ3.

Aso's NO mechanism is **not** the DopR2/IP3 explanation of backward timing:
NOS knockdown did not abolish its relief-learning effect. Likewise γ3-region
NOS staining did not establish NOS synthesis by PAM-γ3. This component adds
a local cotransmitter hypothesis, not a natural home/away opponent pair.

## The Doi retrieval gap is now concrete and bounded

[Doi et al. 2005](https://pubmed.ncbi.nlm.nih.gov/15673676/), DOI
10.1523/JNEUROSCI.2727-04.2005, is indexed as
[ModelDB 49305](https://modeldb.science/49305). The ModelDB GitHub repository
contains a web pointer, not the actual kinetic implementation. The
[authors' extracted directory](https://bicr.atr.jp/neuroinfo/doi/doiJNSdemo/)
does contain it. Seven small files were retained in
`doi-ip3-source-2026-09-13/`, totaling 842,800 bytes, with URL, timestamp,
headers and hashes. `DoiCaModel.g` is 156,383 bytes, SHA256
`ba7009cf0fd6b4584ad552407d2d9cc96d8e2d773802dfa5015ce7e48eb2ea49`;
its embedded save date is January 27, 2005. This is an author-hosted byte
snapshot, not a newly verified publication commit. No GENESIS installation
or execution occurred.

The [core](https://bicr.atr.jp/neuroinfo/doi/doiJNSdemo/DoiCaModel.g)
declares mGluR/Gq states, PLC complexes, PSD/spine IP3, IP3-degrading enzymes,
seven IP3R states, cytosolic/ER calcium, pumps, exchanger and buffers.
IP3 binding permits activating calcium binding; unprimed receptors instead
enter sequential calcium-inhibited states. Calcium release, buffers and
store depletion feed back into this shared state. It is a mass-action
network, not two separable filters followed by antisymmetric subtraction.
The source includes no dopamine, cAMP, KC spike-to-concentration transfer,
or synaptic-weight output. `fig3.g` resets between PF-only, CF-only and
combined conditions, using 1-μs integration and a 2.0001-s observation.

The [reaction table](https://bicr.atr.jp/neuroinfo/doi/SuppTable2.html)
fixes IP3R forward/reverse pairs, in concentration units, at
`(1000,25800)` for IP3 binding, `(8000,2000)` for activating calcium,
and `(8.889,5),(20,10),(40,15),(60,20)` for successive inhibitory
calcium binding. Bimolecular forward units are `μM^-1 s^-1`; reverse units
are `/s`. Stored GENESIS rates instead use molecule counts and compartment
volume factors; copying their numbers into concentration ODEs would be wrong.
The authors explicitly chose Gq activation `116/s` because the cited
`0.01/s` gave insufficient IP3. They also adjusted pump turnover and density.
These published assumptions are fixed source choices, not independently
measured fly rates.

The [initial-state table](https://bicr.atr.jp/neuroinfo/doi/SuppTable1.html)
and source distinguish a 0.1-μm³ cytosol and a PSD one-fiftieth as large.
Basal cytosolic calcium is 0.06 μM, IP3 0.1 μM and ER calcium 150 μM;
IP3R population is estimated at 16 channels. Inputs are tabulated glutamate
and calcium-influx waveforms, not bare spike timestamps. The author's
[parameter classification](https://bicr.atr.jp/neuroinfo/doi/SuppTable3.html)
explicitly separates measured, borrowed and unknown parameters.

There is already a source/table discrepancy to preserve: Table 1 prints
IP3R-IP3 concentration `0.1`, while the core uses `CoInit=.001` and
`nInit=.06` at volume factor 60. Many HTML Greek symbols also extract as
Latin `m`; explicit `uM` source comments resolve the intended units. A future
port must choose and test a source identity, not assume the README's claim
that every table and script value is identical. The core's full reaction,
state, wiring and parameter-comment text was read; tabulated stimulus values
were inspected as input metadata, not simulated. Full main-paper retrieval
through PMC remained challenged; the accessible supplement and actual code
close the earlier activation/source gap without claiming that access.

## Decision boundary before MaleCNS integration

The new source component is ready for independent numerical implementation,
not a circuit dispatch. The unresolved choice is **how actual local KC/DAN
events become the activity levels in a persistent per-KC/compartment state**,
including what persists across calls and which finite expression time the
readout observes. An infinite quiet limit is a mathematical limit, not
elapsed biological time inside a 400-ms episode. Initializing these states
at the 100-ms write onset would discard unmodeled physical history; extending
them to all home classes or away NO would require explicit scope decisions.
Adding the old eta or clipping the source weight would also be new equations.

The frozen component correctly defers those decisions. It supplies a
testable downstream topology with cell-specific support, while retaining
every previous rejected result and the unchanged failed qualification.
No source here guarantees that untaught coincidence should be neutral.

The third considered model, Yarali et al. 2012
([DOI 10.1371/journal.pone.0032885](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0032885)),
was handed to root after my landing-page inspection. Root's independent
Methods review reports Aplysia-derived input curves, an imposed 2.5-s
calcium-modulation delay, and an active-AC integral compared with a separated
control; downstream PKA/plasticity is omitted. I did not independently read
or execute that model's equations. This does not displace the selected Aso
component. The striatal 2010 landing-page lead was not pursued.
