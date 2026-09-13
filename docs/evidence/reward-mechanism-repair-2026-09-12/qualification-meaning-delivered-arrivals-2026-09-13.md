# What the untaught qualification guard means

September 13, 2026; independent architectural review at `bcefc77`.

**The frozen guard tests a useful engineering preference against consistent
signed drift across cues. It is not a necessary property of all biological
learning, and it does not identify a defective molecular mechanism.** A
failure remains a failure of this project's accepted contract. There is no
justification here for relaxing it, relabeling old results, or claiming that
no admissible mechanism can satisfy it.

The actionable architectural distinction is downstream activity-dependent
plasticity versus merely changing the DAN input to the existing antisymmetric
rule. A new state module must expose that distinction to independent
interventions before another captured-history screen. Neither source-backed
state names nor passing arithmetic tests establish untaught neutrality.

## Exact predicate and the assumption behind it

The [frozen v1.1 specification](../../../docs/evidence/reward-repair/evidence/candidate-rule-spec-v1.1.md)
defines, for eight cues in each compartment and noise panel,
`x_i = sum_e (g_final,e − g_initial,e)` over eligible edges. Its requirement is
`|mean(x)| <= sample_SD(x)/2`, with `ddof=1`. The two diagnostic panels and
two noise sets are assessed separately. `bet36fly/reward_diagnostic.py`,
`evaluate_panel`, implements that predicate; the later exact-tick shadow
calculations preserve it. For eight exact totals, setting `S=sum(x_i)` and
`Q2=sum(x_i²)` reduces it to **`9 S² <= 16 Q2`**. Equality passes; eight zeros
pass; any identical nonzero totals fail. No hypothesis-test p-value appears.

The intended property is low common signed displacement relative to
cue-to-cue variation from a shared unit checkpoint. Treating it as evidence
of no intrinsic learning bias would additionally require appropriate input
and state assumptions. The eight cues are heterogeneous engineered stimuli,
not eight independent repeats of one identical biological condition. Common
noise seeds make matched comparisons useful but do not establish independent,
stationary KC/DAN processes. Even for an ideal IID zero-mean Gaussian sample,
the predicate would be `|t_7| <= sqrt(2)`, not an equivalence test proving zero
bias. No such sampling model is asserted for these recordings.

Untaught means no imposed teaching pulse, with plasticity active. It does
not mean no dopamine, no cue, or no relevant neuronal activity. The
diagnostic independently resets each condition's gains to one; the separate
16-call cumulative control carries gains. Existing call resets also remove
electrical/filter history. An organism's previously adapted internal state
cannot be assumed present at this diagnostic's repeatedly fresh checkpoint.

Concrete analytic counterexamples, independent of all saved results:

| Eight trial totals | Frozen guard | What it demonstrates |
| --- | --- | --- |
| `[a,a,a,a,a,a,a,a]`, any nonzero `a` | Fails | Arbitrarily small common drift fails. |
| `[a,0,0,0,0,0,0,0]` | Passes: ratio `1/sqrt(8)` | One larger cue-specific displacement may pass. This is not an absolute-size bound. |
| `[a,−a,0,0,0,0,0,0]` | Passes | Signed cancellation can hide large opposing changes. |
| Each trial contains opposing edge changes summing to zero | Passes | The guard does not establish edgewise stability or absence of plasticity. |
| Untaught totals `−a`; matched taught-minus-untaught totals `−3a`, `a>0` | Teaching ratio passes; untaught guard fails | Teaching sensitivity and this stability preference are distinct properties. |

Common nonzero rescaling preserves the guard before clipping/publication
effects; adding cue-dependent variability may change its result without
reducing total plastic activity. These are interpretation limits, not
instructions to increase variability or shrink updates. Bounds, leakage,
cumulative drift, replay and cue-specific conditioning remain independent
requirements. An all-zero disabled rule passes this guard but fails the
strict negative teaching-effect requirement.

## Source meaning and its limits

The existing Hige/Handler/Cohn reviews document compartment- and
protocol-dependent plasticity and ongoing local dopamine effects; they never
derive the eight-cue half-SD number. Their previous access limits remain in
the [source ledger](../../../docs/evidence/reward-mechanism-repair-2026-09-12/dopamine-signal-sources-resumed.md).
Fresh Hige and Handler PMC opens returned browser challenges, so no fresh
full-text reading of those two is claimed.

Fresh [Yamagata 2016](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1002586)
Results confirm that PAM-γ3 basal activity and its suppression can carry
reinforcement. This rules out treating ongoing DAN activity as universally
meaningless; it does not classify the present endogenous PPL101 activity as
legitimate memory or certify the accepted positive PAM12 teaching interface.

Fresh [Yamada, Davidson and Hige 2024](https://physoc.onlinelibrary.wiley.com/doi/full/10.1113/JP285745)
studied γ and α/β KC inputs onto MBON-γ1pedc. Ex vivo EPSCs/PPR and separate
in vivo cAMP imaging support an activity requirement downstream of cAMP:
focal dopamine or low-dose forskolin alone did not reproduce presynaptic LTD;
pairing with KC activation did. Sparse activated and inactive KC axons had
similar cAMP responses. Forskolin pairing bypassed dopamine-receptor blockade.
The protocol used one-minute pairing; cGMP-related LTP required repeated
minute-long pairing and developed slowly. These are relevant pathway
dissociations, not 400-ms rate constants. High-dose forskolin effects were
qualitatively different, and PPR alone does not uniquely locate plasticity.
The observed home-target α/β support also prevents a gamma-only home
restriction by analogy with away. No γ3 kinetic calibration follows.

Thus a biologically plausible untaught change could reflect actual
neuromodulatory/cue coincidence, state adjustment, or other plasticity;
the guard alone cannot decide which. Conversely, calling a change legitimate
requires evidence of the relevant function, specificity and state dependence.
An adverse readout bias, widespread nonspecific edge change, loss of teaching
contrast or lack of retained cue discrimination would still be important
defects. None is established or excluded by the scalar guard in isolation.

## Why Q is a structural issue, and what extra state must change

Current `RateBridge` in `bet36fly/reward_lif.cpp` uses actual KC and pooled
DAN spikes, the same causal rate/eligibility operators on both, and
`g' = eta*0.96*(E_D R_K − E_K R_D)`. Between impulses,
`Q' = −(1/100+1/500) Q`. Its complete isolated-pair integral is
`−eta sign(lag)[exp(−|lag|/500)−exp(−|lag|/100)]`, where lag is DAN minus KC
time in ms. This is the inspected model law, not an inferred receptor law.

Consequences: proportional complete histories and proportional initial
states cancel; an endogenous DAN event following a KC event depresses just
as an otherwise identical externally caused event does. Equal mean rates
or a complete tail do not remove asymmetric KC/DAN timing. A rested,
time-preserving scalar release transform also leaves an isolated exactly
coincident pair at zero. More complicated release dynamics can change lag
structure, but an input transform alone does not establish downstream
activity dependence. Identical experimental stimulation envelopes must not
be confused with exactly identical microscopic spike trains.

The previously proposed ready/primed/inhibited occupancy topology can be
tested as an engineered order detector: dopamine-first and KC-first event
maps need not commute. It does **not** by itself specify the depression
branch, molecular input units, recovery, or teaching response. The new source
dissociation specifically disfavors a topology in which KC activity acts
only by increasing cAMP and cAMP alone writes presynaptic LTD. A useful
specification separates local messenger drive `A_e`, KC-dependent
eligibility/activity `C_e`, and a plasticity expression process
`g'_e=Phi(A_e,C_e,z_e,g_e)`. This is a factorization requirement for testing,
not a selected product, threshold, kinetic law or parameter set. Local
state `z_e` must have an explicit source and causal history.

Teaching sensitivity must be demonstrated with the same mechanism receiving
actual increased DAN input while KC eligibility remains available. Merely
forcing no-DAN silence is insufficient because the untaught home circuit
contains both inputs. A purely depressive branch with positive drive whenever
both coincide can still make all untaught totals negative. A positive recovery
branch must have its own independently justified trigger; neither the
half-SD statistic nor a demand to cancel Q supplies one. The same-channel
source findings do not authorize treating the accepted home/away populations
as a natural opponent subtraction.

Any deterministic mechanism with the same complete allowed histories and
initial states must produce the same output regardless of teaching labels.
The prior causal-prefix audit establishes an electrical teaching difference,
not a calibrated chemical distinction or all subsequent local KC states.
Identical full-input collisions across an entire required matched cell would
prove lack of teaching sensitivity for that restricted input class; an
isolated collision or an eight-trial guard failure does not prove a universal
impossibility. Added unmeasured state must not be filled with a trial label,
future pulse, or zero merely because it was not recorded.

## Independent intervention matrix before another candidate screen

These are pre-outcome test requirements for a concrete future module; no
such module is implemented or evaluated here.

| Controlled test | Inputs/state held fixed or changed | Diagnostic distinction |
| --- | --- | --- |
| Messenger clamp × KC activity | Same local messenger waveform; KC inactive/active/history shifted | Separate input generation from downstream eligibility/expression; reproduce the source dissociation above within its declared protocol scope. |
| Receptor block × downstream bypass | Block receptor drive; separately impose downstream activation with/without KC activity | Detect a model that incorrectly requires receptor activation after the downstream bypass. |
| Same D waveform, different K timing | Fixed D and initial state; forward/backward/overlap K | Any difference must arise in local state/expression, not a changed release waveform. Do not impose universal backward potentiation. |
| State swap at a fixed instant | Same instantaneous D/K and gain; distinct valid preceding eligibility histories | A missing effect identifies an absent state variable or wrong state wiring; equal instantaneous rates are insufficient. |
| Cell permutation and fixed-total pooling | Permute IDs/maps consistently, then separately redistribute events at fixed pool total | First must preserve output; second distinguishes a body-specific input model from a pooled approximation. |
| Input swap versus state clamp | Swap recorded synthetic D drives with local state fixed, then local state histories with D fixed | Attribute changes to signal generation versus susceptibility; do not infer leakage from identical D alone. |
| Teaching increment on a retained cue trace | Same causal KC history, actual extra DAN events, all metadata erased | Verify a nonzero correctly signed matched effect; paired/unpaired and reset tests then assess specificity. No universal monotonicity for arbitrary histories is assumed. |
| Separate pathway perturbations | Independently disable proposed positive/negative outputs, preserving input records | Expose hidden cancellation, branch relabeling and compensating implementation errors. |
| Quiet continuation and reset | Identical event history with different partitions of its quiet tail | Complete-state evolution and final gains must match declared continuous semantics; do not import the old linear tail into a nonlinear module. |
| Frozen/mask/checkpoint controls | State evolves as specified; plasticity disabled or edge excluded | Exact gain bytes, all original masks, parent ancestry and bound observations remain intact. |

Minimum diagnostic record: body/edge identity; actual KC/DAN events; local
drive before and after receptor/messenger processing; all independent
eligibility states as used; separate branch fluxes; gain before/after
publication; reset/bypass/perturbation identity. Only these joint records can
distinguish an incorrect input map from an incorrect intracellular update.
Measuring only total dopamine, a final gain sum, or a sensor-normalized
reporter is insufficient.

The accompanying executable tests use synthetic gain totals and exact
Fraction algebra. They check the present production guard against the
counterexample families and expose Q's dependence on eligibility separately
from instantaneous rates. They do not simulate molecular kinetics or claim
to validate the prospective intervention matrix. A source-constrained
downstream-state contract, including the bypass tests, is the next concrete
deliverable. Selecting kinetics from rejected outcomes or running another
scalar transformation of Q is not justified by this architectural review.
