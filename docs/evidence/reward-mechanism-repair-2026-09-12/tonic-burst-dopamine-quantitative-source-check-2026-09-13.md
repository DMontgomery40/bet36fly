# Quantitative dopamine release and receptor sensitivity: bounded source check

Checked September 13, 2026 UTC. The question was declared before the
weight-state shadow outcome. This inquiry selected no parameters, proposed
no candidate and accessed no candidate result. It used four targeted search
queries and six primary-page opens, with no account access or bulk retrieval.

**There is quantitative fly evidence for stimulation-dependent dopamine release
and different receptor-pathway sensitivities. The inspected measurements do
not supply a calibrated separation of endogenous ongoing spikes and bursts
for PPL101/MBON11 or PAM12/MBON09 over this simulator's 400 ms trial.** Thus
“all receptor and release numbers are unknown” would be too broad; copying
these measured numbers into the named-cell model would also be unsupported.

## Adult release measurements

[Shin, Copeland and Venton, 2020, Analytical Chemistry](https://pmc.ncbi.nlm.nih.gov/articles/PMC7902153/),
DOI 10.1021/acs.analchem.0c02305: FSCV in isolated 5–10-day adult
D. melanogaster brains, DAT-driven CsChrimson. Heel pools γ1/γ2; tip pools
γ4/γ5. Five 2-ms light pulses tested 10–60 Hz; 60 Hz released more dopamine.
At 60 Hz, increasing pulse count plateaued around 20. A single **4-ms light
pulse**, not a verified single spike, released about 30% of the 20-pulse signal.
Twenty 2-ms pulses at 60 Hz yielded heel/tip means 0.09±0.01/0.05±0.01 µM.
Single-pulse uptake fits gave respective Km 0.23/0.25 µM and Vmax
0.12/0.19 µM/s, assuming clearance without diffusion. Both sexes were sampled;
heel release differed by sex. These are evoked regional measurements, not
absolute tonic exposure or a γ3/PPL101-specific transfer function.

## Receptor concentration and time dependence

[Himmelreich et al., 2017, Cell Reports](https://pmc.ncbi.nlm.nih.gov/articles/PMC6168074/),
DOI 10.1016/j.celrep.2017.10.108: Drosophila receptors/G proteins were
reconstituted in HEK293T/17 cells and assayed by BRET. DA EC50 values were
DAMB–GαqG **56.7±7.7 nM**, dDA1–GαsA **0.61±0.07 µM**, and DAMB–GαsA
**7.37±0.69 µM**. At 100 µM DA, DAMB activation rates were 2.71±0.04 s⁻¹
through GαqG and 0.46±0.01 s⁻¹ through GαsA. These are assay activation rates,
not dopamine clearance constants. MB Gαq knockdown affected forgetting without
an acquisition deficit. The authors proposed weaker DA preferentially driving
forgetting; they did not measure a matched tonic/burst spike-to-receptor curve
in γ1pedc or γ3. DAMB means Dop1R2/DopR2 here, not the D2-like receptor.

Access limit: the fresh direct PMC open returned a browser challenge. The
indexed primary Results, Figure 3 caption, Discussion and cell-culture Methods
were available and personally read, including the exact units above. This is
an inspected indexed primary text, not a fresh full-page or raw-data audit.

## What the dopamine sensor evidence resolves

[The GRABDA sensor study, 2018, Cell](https://pmc.ncbi.nlm.nih.gov/articles/PMC6092020/)
reports live-fly dopamine signals from odor and electrical stimulation. A single
electrical stimulus produced a detectable response; shock evoked γ2/γ3 signals,
whereas odor responses in the γ lobe were γ4-selective in the reported assay.
DAT knockdown or 3 µM cocaine prolonged odor-evoked signals. Its 130 nM/10 nM
sensor sensitivities are engineered reporter characteristics, not DopR1/DopR2
activation thresholds. The frequently cited 20-Hz frequency/pulse matrix and
~0.1-s rise/~3-s or ~17-s decay in Figure 2 concern **mouse nucleus accumbens
slices**, not fly γ1pedc/γ3. Inspected fly text provides no absolute local
concentration-to-spike calibration for the selected cells; no plotted points
were digitized, and fly sex was not established from the inspected excerpt.

## Transfer to the present circuit

The relevant inference is limited: release and downstream signaling need not
be proportional to a channel's mean spike train. That supports treating spikes,
extracellular dopamine and receptor activation as separate measurements. It
does not establish a burst threshold, a tonic subtraction, a release pool,
a receptor timescale or a mapping from either released concentration or BRET
amplitude to a KC→MBON gain.

Several links remain missing in this bounded evidence:

- Physiological spike trains recorded simultaneously with local dopamine at
  the selected γ1pedc or γ3 sites, with identified PPL101 or PAM12 sources.
- A tonic baseline and controlled burst comparison matched for spike count,
  site, internal state and sex, rather than optical/electrical stimulus counts.
- DopR1/DopR2 pathway occupancy or signaling at those same KC sites under the
  measured dopamine histories, including their local expression and clearance.
- A validated conversion from those molecular measurements to the selected
  KC→MBON11 or KC→MBON09 plasticity over the 400-ms schedule and its aftermath.

The heel result includes γ1 territory but does not isolate γ1pedc, either
PPL101 body or either MBON11 target. The live-fly sensor evidence reaches γ3,
but is not a PAM12-only release/receptor calibration. Locality cannot be
recovered simply by substituting the dataset's compartment or body labels.
Nor can a culture EC50 be joined to a regional FSCV mean to declare which
pathway an individual synapse activates: the studies do not share the required
location, exposure, receptor expression or preparation.

The already inspected Handler/Hige/Cohn/Yamagata compartment and timing
constraints remain in the [earlier receptor review](dopamine-receptor-state-decision-2026-09-13.md).
Handler's fresh direct page again returned a challenge; no new quantitative
Handler claim is made here. Ongoing activity is not thereby biologically
inactive, and the PAM-γ3 suppression finding is not converted into a new rule.
Failure to establish the required calibration in these bounded searches is
not a claim that no relevant experiment exists anywhere.

## Inspection and provenance boundary

The accompanying JSON receipt records every query and open, reading hashes,
source versions, access limitations and the before-outcome task declaration.
Targeted Results/Methods sections of the two accessible articles and the
indexed receptor sections were read directly. No supplementary dataset, image-based curve estimate, account,
cell recording or simulator run was used. No scientific input, threshold,
mask, source file or production surface was edited. Repository-wide execution
checks belong to root; this report requires link/unit/provenance review rather
than a new biological experiment or implementation test suite.
