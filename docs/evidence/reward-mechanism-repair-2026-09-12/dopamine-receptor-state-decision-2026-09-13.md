# Next mechanism decision: a joint KC-local signaling state

September 13, 2026 UTC. Output-only source and implementation review. No
candidate was implemented or evaluated, no circuit ran, and no synapse data
were requested. The full prior narrative-reading chain was refreshed before
this decision; there were no unread repository narrative deltas.

**The smallest concrete omission supported by the inspected physiology is a
joint state in the KC that distinguishes coincidence-related depression from
order-dependent potentiation.** Independent linear KC and DAN eligibility
traces approximate timing, but they do not represent competing receptor or
intracellular states. A minimal priming/inhibition topology is specified below.
It is a falsifiable mechanism hypothesis, not yet a numerically frozen candidate
or a claim that it repairs the untaught-home failure.

## Source constraints and compartment limits

The six-source [earlier ledger](dopamine-signal-sources-resumed.md) was reread,
including its explicit access limits. Two targeted indexed primary retrievals
provided the following additional methods check; a direct Handler open
returned only a browser challenge. Three of the four permitted web actions
were used. No challenge was bypassed and no account was accessed.

| Primary source | Constraint on the next model |
| --- | --- |
| [Hige et al., 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4674068/), Neuron, DOI 10.1016/j.neuron.2015.11.003 | In γ1pedc, brief odor/PPL1 pairing depresses MBON input even when MBON spikes are blocked. The reported backward protocol has no significant effect. Brief induction differs across compartments. This supports preserving home eligibility and avoiding an obligatory postsynaptic-spike gate; it does not establish universal backward potentiation. Fresh indexed Results, Figures 1–7 and relevant recording/analysis methods were read, not a new reproduction. |
| [Handler et al., 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC9012144/), Cell, DOI 10.1016/j.cell.2019.05.040 | γ4 experiments and γ4/γ5 reporters separate DopR1/cAMP-associated depression from DopR2/Gαq/ER-calcium-associated potentiation. Release-side signals were similar across opposite induction orders. The proposed IP3 order detector is not a calibrated kinetic model. Figure 5F subtracts independently min–max-normalized reporter responses; those coefficients are not receptor rates or physiological gain conversions. Fresh indexed Results, Figures 5–7 and selected analysis methods were read; direct full-page access remained challenged. |
| [Cohn et al., 2015](https://stacks.cdc.gov/view/cdc/38872/cdc_38872_DS1.pdf), Cell, DOI 10.1016/j.cell.2015.11.019 | Local KC-axon calcium and behavioral state matter; measured γ4 paired depression and separated potentiation do not supply a universal γ1pedc/γ3 law. Ongoing dopamine is physiologically active, not a signal that can automatically be discarded. Prior main text/methods coverage is retained. |
| [Jiang and Litwin-Kumar, 2021](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009205), PLOS Computational Biology | The rate plasticity rule operates inside an optimized signal-generating network. Its 1 s/5 s model timescales and optimized recurrent parameters do not calibrate receptors in the fixed MaleCNS graph. Prior full paper and pinned source inspection are retained. |
| [Cervantes-Sandoval et al., 2017](https://elifesciences.org/articles/23789), eLife | Local KC/DAN feedback and terminal calcium are relevant. Detailed functional experiments emphasized α2α′2; anatomical observations also included γ1pedc. Terminal calcium is not a measured local dopamine-per-spike transfer function. Preserve feedback; prior indexed Results/selected Methods access limits remain. |
| [Yamagata et al., 2016](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1002586), PLOS Biology | PAM-γ3 can convey sugar through suppression of ongoing activity. The accepted positive PAM12 teaching pulse remains an engineered interface. Neither that finding nor the measured calcium recovery supplies a dopamine clearance constant. Prior targeted full publisher-text reading is retained. |

The common-source hypothesis below therefore transfers a signaling topology
across compartments as an engineering assumption. It cannot be labeled a
reconstructed PPL101/MBON11 or PAM12/MBON09 molecular mechanism. The absence
of backward plasticity in one γ1pedc protocol also cannot establish that every
γ1pedc preparation or timing condition lacks potentiation.

## What the current implementation already does

Fresh inspection covered `reward_lif.cpp`, `reward_protocol.py` and the relevant
`RewardEngine` construction/run boundaries in `reward_brain.py`. The bridge is
implemented inside `reward_lif.cpp`; there is no separate receptor module.
It uses actual DAN spikes from the recurrent electrical graph, pools them by
channel and applies

```text
Q = E_D R_K − E_K R_D
dg/dt = eta × 0.96 × Q
```

with the existing causal 100 ms rate and 500 ms eligibility filters, masks,
clamped double accumulation, float32 publication and complete analytic tail.
Only gains persist between calls. The raw rule has the corresponding opposing
event/trace products. Neither learns only when an external teaching label is
present. MBON spikes influence the electrical graph but are not an additional
factor in the plasticity equation.

For histories satisfying `R_K = a R_D` and `E_K = a E_D` at every time, the
bridge has `Q = 0` identically. Its isolated-pair kernel is antisymmetric.
These are algebraic properties, not new saved-trial findings. They are not
equivalent to an intracellular coincidence branch plus a separate order branch.
Overlapping stimulation envelopes in an experiment must also not be confused
with identical individual spike histories in this algebraic example.

## Minimal state topology, with unfilled quantitative choices visible

The following is this review's **coarse engineering representation**. Its
state names are not additional measured cell annotations or an experimentally
identified Markov chain. It represents a ready fraction `r`, a dopamine/IP3-
primed fraction `p`, and a KC-calcium-first inhibited fraction `h`, with
`r + p + h = 1`. Only `p` and `h` require independent storage.

| State transition | Meaning in the proposed representation |
| --- | --- |
| Ready → primed, driven by the dopamine/IP3 pathway | Later KC drive can engage the potentiating branch. |
| Ready → inhibited, driven by KC calcium | Subsequent dopamine does not immediately obtain the same potentiating response. |
| Primed → ready with an ER-related output, driven by later KC calcium | Order can matter even with the same dopamine waveform. |
| Primed/inhibited → ready through relaxation | Finite recovery is represented explicitly. |

A dimensionally explicit realization of that topology, **not a fitted or
authorized numerical model**, is:

```text
r = 1 − p − h
dp/dt = u_D(t) r − u_K(t) p − gamma_P p
dh/dt = u_K(t) r − gamma_H h
J_ER(t) = u_K(t) p
dg/dt = eta [beta_ER J_ER(t) − beta_A J_A(t)]
```

`p,h,r` are dimensionless occupancy fractions. `u_D,u_K,gamma_P,gamma_H`
have units ms⁻¹. `J_ER` and the separate coincidence-related depression drive
`J_A` have units ms⁻¹. `beta_ER,beta_A` are dimensionless conversion factors
in this normalization; gain `g` is dimensionless. The existing `eta = 0.0005`
can remain fixed, but that alone supplies neither conversion factor. Defining
new drive units cannot silently rescale the accepted learning rate.

The shared finite occupancy pool and return to ready after an ER-related
event are simplifying assumptions of these equations. The experiments do not
identify those transitions as a literal receptor cycle or show that each
release event consumes a primed site. They would need independent scrutiny
along with the input maps, rather than being attributed to the source.

Here `J_A` denotes a plasticity drive, not a quantitative cAMP concentration.
Its dependence on KC and dopamine signaling must be specified separately;
equating it to a product, threshold or normalized reporter amplitude would be
another modeling assumption. Likewise `u_D` is not automatically the observed
DAN firing rate, and `u_K` is not automatically the observed KC firing rate.
The table of transitions motivates the topology; it does not determine those
input mappings.

The following numerical choices remain genuinely unfilled:

- Spike-to-local chemical/activation mappings, including amplitudes and
  saturation. The dataset supplies neither chemical concentration nor release
  per spike.
- Priming/inhibition recovery rates and the shape of the coincidence drive.
  Assigning 100/500 ms to them would be a fixed engineering convention, not a
  measured receptor parameter; no such assignment is made here.
- The two branch conversions and whether the same values should apply to all
  accepted home edges and the supported away gamma edges. The source's reporter
  normalization does not answer this question.
- A numerical impulse/concurrent-event convention and full-tail solution for
  the chosen nonlinear system. The old bridge tail cannot be reused by name.

These are the minimum choices needed to turn this topology into a complete
candidate. This review does not invent values to make it executable. Choosing
them independently of the saved qualification outcome would make an explicitly
engineered hypothesis possible; claiming that the inspected sources already
fix them would be incorrect. No separate MBON-spike gate is proposed.

## Keep local routing and intracellular state separate

A routing model determines the chemical or effective activation drive at a
particular contact; a state model determines how that drive interacts with
KC history. If normalized static routing acts on identical DAN histories,
changing its coefficients cannot change the routed waveform. Conversely,
local terminal signaling might differ despite similar whole-neuron spikes;
neither possibility is established by body labels or contact fractions.

The [partners-only anatomical deliverable](localization-next-decision-synthesis-2026-09-13.md)
can locate contacts, but cannot determine `u_D`, its transfer function or any
of the rates above. It should not be used to choose a diffusion cutoff or
derive an exposure coefficient from a favorable diagnostic result. A first
intracellular hypothesis could retain the existing pooled drive as an explicit
spatial approximation, testing state dynamics separately from routing.

All 4,184 home edges remain eligible. Away retains 3,239 gamma-eligible edges;
the other 1,443 continue transmitting. Geometry, receptor hypotheses and
unresolved cell labels do not change these policies. Accepted encoder, drive
gains, channels, teaching schedules and diagnostic thresholds remain fixed.

## Pre-outcome falsifiers and the next concrete decision

Before seeing any candidate replay result, a quantitative realization would
need to freeze and pass these independent tests:

1. With an identical dopamine waveform, reversing KC timing changes the
   predicted branch engagement. Overlapping drive pulses can recruit the
   depression branch without forcing the bridge's algebraic coincidence-zero
   result. This is an engineered functional prediction, not a claim about
   exactly synchronous biological spikes.
2. Removing either signaling branch in the synthetic model has the separately
   declared polarity consequences. A model that changes release to explain
   every order effect, despite holding its drive fixed in this test, has not
   implemented the proposed intracellular distinction.
3. Fractions stay nonnegative and sum to one. Splitting a numerical interval
   gives the same continuous solution. Empty, single-input, concurrent,
   reversed, repeated and sustained-input cases have independently derived
   references, including the entire no-new-input tail. No path may rely on
   a cue label, future activity or an external-US-only write gate.
4. The existing 100 ms gain-write onset and call/checkpoint contract remain
   fixed. Any new signal-state initialization must be declared before the
   study; it cannot revive the rejected onset-history experiment. Plasticity
   off, all masks, byte publication and bound accounting must remain exact.
5. The exact home family's observed protocol limits remain visible. A γ4-like
   synthetic order curve does not establish γ1pedc/γ3 physiology. In particular,
   successful backward recovery in the fixed engineering protocol would need
   to be measured, not deduced from the names of the states.
6. All unchanged original and second qualification criteria remain mandatory,
   followed by controlled acquisition and reversal. A smaller drift, altered
   sign, lost teaching response or numerical extinction does not qualify.

The next concrete mechanism decision is whether to instantiate this
two-occupancy/dual-drive topology under **explicit, independently fixed
engineering input maps, rates and branch conversions**, or to require further
family-specific kinetic evidence before selecting those quantities. The
inspected papers support the omitted cellular distinction, not a unique
quantitative instantiation. This is why the present artifact is a decision
record rather than another purportedly source-calibrated candidate.

The topology may still worsen untaught depression or create excessive
potentiation. It was selected for a documented structural omission, not for a
guaranteed direction of change in SCI-001. The rejected rate adaptation and
onset hypotheses remain rejected; no parameter sweep, exposure cutoff,
contact deletion, home gamma filter or gain/guard retuning follows here.
