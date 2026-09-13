# What the current learning law does and does not make neutral

September 13, 2026 UTC; starting checkout `ab0f80f`. Independent mathematical
and source review by `dopamine_sources`. No saved-history reevaluation or
circuit execution belongs to this inquiry.

**None of the listed assumptions guarantees neutral untaught learning.** The
current rule cancels certain symmetric KC/DAN histories; it measures temporal
asymmetry in other histories regardless of whether teaching was externally
scheduled. The complete tail correctly finishes that measurement. Population
averaging and restoration toward gain one do not supply a prediction-error
computation. This distinguishes a structural limitation from another numerical
implementation defect; it does not identify the anatomical cause of the saved
failure.

The next useful topology to investigate introduces a separately observable
local presynaptic/signal-generating state, rather than changing scalar factors
on the same two products. A feedback-error topology provides useful independent
mathematical tests, but cannot be obtained by declaring the accepted home and
away channels to be a natural opponent pair. The newly inspected lateral-KC
source code offers a concrete local-state model to examine separately. Its
shock-only dopamine drive and timestep-dependent inhibition recurrence prevent
transferring its no-shock stability as evidence that it solves our control.

## Current production equation, not an inferred molecular mechanism

I read the entire current `bet36fly/reward_lif.cpp`, including `RateBridge`,
event delivery, teaching, resets and finalization, and rechecked the wrapper's
parameter/publication boundary. The bridge uses actual somatic spike events,
one mean signal for each selected DAN population, identical rate/eligibility
operators on KC and DAN histories, cold onset at 100 ms, and a final no-event
tail. Only the float32 gains survive a call. The current production code has
neither rejected shadow rule, neither an axonal-calcium state nor receptor
occupancy, and no explicitly represented reinforcement prediction error.
Recurrent inputs can affect DAN spikes; that is not the same claim as a
particular feedback computation having been implemented.

With spike measures S, rates in spikes/ms and eligibility in spike units,

```text
R_X' = -r R_X + r S_X,       E_X' = R_X - e E_X
r = 1/100 ms, e = 1/500 ms, n = 1-(e/r)^2 = 0.96
g' = eta n Q,               Q = E_D R_K - E_K R_D
eta = 0.0005.
```

This is the unconstrained double-gain equation; the production implementation
also clips and publishes at its declared boundaries. Frozen learning uses
effective eta zero. The following exact identities concern the underlying
unclipped law and consistent initial filter states. Numerical publication and
clipping do not receive a silent exemption from their separate tests.

## Antisymmetry is a timing property, not a neutrality guarantee

Between impulses, direct differentiation gives `Q'=-(r+e)Q`: the two common
`R_K R_D` terms cancel. Therefore its exact no-event signed area is
`Q(T)/(r+e)`. This explains the implemented complete tail without attributing
new spikes or physiology to it.

For one KC event and one population-normalized DAN event, let Δ be DAN time
minus KC time. With both events admitted after onset and the complete tail,
my independent derivation gives

```text
H(Δ) = -eta sign(Δ) [exp(-|Δ|/500) - exp(-|Δ|/100)],   H(0)=0.
```

Event masses multiply H. The normalization 0.96 cancels the factor
`r²/[(r-e)(r+e)]` arising from integrating the four impulse responses.
For a finite event history, the attempted complete gain change is the sum of
H over every KC/DAN pair. This derivation supplies several precise conclusions:

- Exchanging complete KC and DAN histories reverses the change. Proportional
  histories cancel exactly, provided both filter states have the same
  proportional relation. Coincident isolated events also cancel.
- A delayed DAN event paired with an earlier KC event gives depression for
  every positive finite delay. One KC event and one delayed endogenous DAN
  event have equal counts but a nonzero update. This is a counterexample to
  neutrality from equal mean activity, not evidence that a specific retained
  connection generates the measured failure.
- In expectation, a stationary lag distribution that is symmetric under
  exchanging KC and DAN times cancels an odd H. Independent stationary
  processes are a sufficient special case under appropriate common observation
  boundaries. Equal average rates alone are not sufficient; correlated
  processes can have asymmetric lag distributions. Nonstationary stimulus
  envelopes and reset boundaries require explicit treatment.
- The current finite-trial guard is a statistical engineering criterion.
  It does not require every untaught edge or trial to remain exactly unchanged.
  No mathematical identity above proves its eight-trial mean/SD condition.

An important identifiability limit follows without making a biological claim:
two trials with the same complete local histories and initial states receive
the same update from any deterministic rule using only those inputs. Such a
rule cannot distinguish whether otherwise identical DAN spikes were caused
by external teaching or by endogenous activity. Adding a teaching-label gate
would distinguish the labels by construction; it would not establish a
cellular mechanism. Extra local state can help only if it contains additional
relevant information, not merely a renamed copy of the same scalar history.

## Reset, tail, common population signal and weight restoration

**Reset and tail.** A full tail makes the final unconstrained result invariant
to where an event-free continuation is divided into electrical time and tail.
It does not make the result zero. The final gains may share that invariance
within the declared numerical allowance; intermediate publication counts are
different observations and are not asserted invariant. Resetting filters
between calls discards cross-call event pairs: a KC-only call followed by a
DAN-only call has no within-call pair, whereas concatenating those events with
a finite gap generally does. Cold onset similarly removes pre-onset pairs.
Neither operation is a physiological proof of neutrality. The already rejected
history-only study remains rejected; this algebra is not permission to tune
its boundary or omit the tail.

**Population means.** For fixed histories, the bridge is linear in D. A mean
over the two PPL101 histories produces the mean of their individual attempted
updates for a given KC. The same applies to 22 PAM12 histories. It does not
force cancellation. Identical population signals cannot be made temporally
different through static routing. Distinct signals can change edge-specific
lag structure under a different routing, but the coefficients require evidence
independent of the failed outcomes. The earlier necessary routing bounds were
inconclusive; no passing map is inferred or re-evaluated here.

One KC feeding several selected MBONs currently receives the same attempted
gain increment on those edges within the same channel, while their anatomical
transmission weights can differ. The learning variable is a gain multiplier,
not absolute anatomical contact weight. This is an implementation choice,
not a proof of homogeneous local dopamine exposure.

**Scalar rescaling.** On fixed histories without clipping and publication
effects, multiplying every trial total by the same positive constant rescales
both mean and SD, leaving the guard unchanged. In exact integer form its margin
`16 sum(T_i²)-9(sum T_i)²` scales by the square of that constant. In a live
recurrent circuit scaling might alter the histories, but that would be a
different experiment, not an algebraic rescue of this fixed one.

**Rejected weight-state law.** Write its nonnegative unscaled drives as
`P=n E_D R_K`, `N=n E_K R_D`, and `x=g-1`. Then

```text
x' = eta(P-N) - 2 eta(P+N)x
x(T) = x(0) exp[-2 eta integral_0^T(P+N)]
       + eta integral_0^T (P-N)(t) exp[-2 eta integral_t^T(P+N)] dt.
```

It exponentially discounts earlier signed drive according to subsequent total
activity. When P=N, activity restores g toward one; once both drives have
decayed to zero, there is no further restoration. At fresh g=1 its initial
drive is still `eta(P-N)`. A zero unweighted signed integral need not remain
zero after the activity-dependent discount. Conversely, the same-sign forcing
cannot be guaranteed neutral by damping alone. Error-independent attraction
to gain one is different from stopping because a prediction has become
accurate. This analysis explains the mathematical class already rejected;
it is not another evaluation or a proposed modification of that class.

## What the primary models contribute

[Jiang and Litwin-Kumar, 2021](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009205)
optimizes the recurrent circuitry producing learning signals. Its
[pinned implementation](https://raw.githubusercontent.com/alitwinkumar/jiang_litwin-kumar_mb_rnn/a16f86a3e9e476eff6860c3c0e0e1bbe729d7f85/runmodel.py)
uses `dastdp=relu(Jmd@d)` and opposing current/trace products, then a bounded
weight update and slower tracking step. Traces reset at specified boundaries
and update after plasticity. Baseline-activity regularization is part of
optimization, not a subtraction in the local rule. Copying its product shape
does not import its optimized recurrent solution. The present code's unit
conversion, impulse signals and normalization remain independently engineered.

[Bennett, Philippides and Nowotny, 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8105414/)
explicitly constructs feedback prediction errors. Its restricted
single-valence model can still depress synapses without reinforcement;
constant potentiation introduces another model choice. The mixed-valence
alternative adds opponent feedback and modulation, with rectification limiting
the simplest error identities. Its preferred rule is also selected against
direct DAN-stimulation behavior. These are model results and predictions,
not measurements that our two teaching populations form that circuit.

Access boundary: Bennett's primary Results and relevant DAN/plasticity Methods
text were accessible through PMC, but many displayed equations were omitted
by the text renderer. The publisher redirected to authentication and the PDF
fetch failed. I therefore do not claim a fresh exact transcription of its
numbered formulas or a reproduction of the paper. The algebra below is my
explicit idealized derivation from the stated objective, with its assumptions
visible. Jiang's update code was available. No inaccessible equation was
reconstructed and silently attributed to an author.

## A distinct error-coupling topology and its exact tests

An idealized source-motivated alternative represents a prediction and a
comparison signal separately. For a fixed nonnegative KC rate vector k,
let `m=(w_plus-w_minus)·k`, target reinforcement r and error `epsilon=r-m`.
For `C=epsilon²/2`, ordinary gradient algebra yields

```text
w_plus'  =  eta epsilon k
w_minus' = -eta epsilon k
epsilon' = -2 eta ||k||² epsilon
C'       = -2 eta ||k||² epsilon² <= 0.
```

These are **engineering/model invariants**, not equations asserted to be
measured in the fly. Their value is structural: every accurately represented
prediction is a fixed point, regardless of absolute synaptic strength. A
common sensory component can cancel in a separately constructed opponent
error signal without declaring every cue-evoked DAN spike inactive.
Here eta is a symbolic positive coefficient in that abstract rate model;
these equations do not assign its units or value to our gain integrator.

For example, with nonnegative rectified signals
`d_plus=[b+epsilon]_+`, `d_minus=[b-epsilon]_+`, their half-difference equals
epsilon only while neither side clips. Outside that regime it preserves the
error sign but not the same magnitude. At epsilon=0 it is zero for every
nonnegative b. Thus even this toy example must test rectification explicitly;
the gradient proof cannot be carried through an arbitrary spiking circuit,
readout, gain parameterization or mismatched feedback matrix.

This is **not an admissible direct replacement using home-minus-away DAN
means**. Their accepted roles are independent engineered teaching channels,
with fixed targets and off-channel controls. Neither MaleCNS contact counts
nor their labels establish opponent valences, a calibrated comparison signal
or the needed positive/negative pathways. Cross-channel subtraction could
modify the wrong target under a teaching pulse. An instantiated error circuit
would need independently justified local sign, routing, units and feedback;
selecting those from the existing failure is not supported by this report.

## A local-KC topology is a more concrete next building block, with limits

During this review root provided version-bound local files from
[nawrotlab/KC_KC_lateral_interactions](https://github.com/nawrotlab/KC_KC_lateral_interactions/tree/f0ee2079dae6761cc2d07f04e96e76e2654b6e3c),
the model repository accompanying DOI 10.1016/j.cub.2026.01.014. I read its
README, complete core-functions file and `fit_functions.py`, but did not
import or execute downloaded code. The physiology/Methods-S1 inquiry belongs
to the other source reviewer; this subsection independently checks the code.

The inspected WT calculation distinguishes calyx and lobe calcium, adaptation,
and an inhibitory state driven by other KCs. It multiplies the inhibition
update by a recipient-activity sigmoid. That introduces information absent
from our two-history rule: neighboring KC activity and a distinct local
presynaptic state. Changing the local signal's time course or its
susceptibility to modulation can change correlations and specificity, rather
than uniformly rescaling every plasticity product. It cannot be assumed to
eliminate drift or preserve current teaching until tested independently.

In the source's calcium/activity units and seconds, the lobe update is
explicitly

```text
C_lobe_next = max(0, C_lobe + dt [u/tau_input
                 -(C_lobe-b)/tau_KC - a C_lobe/tau_KC - I/tau_KC])
a_next = a + dt (adapt_scale C_calyx-a)/tau_adapt
I_next = f(C_lobe) [I + dt (W C_lobe-I)/tau_inh]
f(C) = 1/[1+exp((C-inflection)/slope)].
```

The calyx calculation omits I. Each update uses the previous-step states,
including old I in the lobe equation. The fitter's W is row-normalized,
all-to-all lateral coupling with zero diagonal and a fitted total factor;
it is not the MaleCNS anatomical edge matrix. These are exact inspected
discrete source expressions, not voltage/receptor-binding ODEs. Their input
and calcium scales cannot silently be identified with our spikes/ms or
eligibility variables, nor can the fitted all-to-all matrix be relabeled a
released anatomical pathway.

Two source-transfer constraints are already actionable:

1. `DAN_dynamics` drives its variable with
   `(shock>0)*(shock-valpred)`, followed by nonnegative clipping. The weight
   function is purely depressive, proportional to `CaKC*danval`. With no
   shock and a cold zero dopamine/cAMP state, that state stays zero and so
   weights cannot change. A nonzero initial state instead decays and can still
   drive a residual update. Source no-shock neutrality therefore does not
   demonstrate the handling of endogenous DAN spikes required here. The
   explicit US-only drive cannot be imported as our control solution.
2. In `simulate_WT_model`, write the inhibition update at constant local
   activity as `h_next=f[(1-s)h+sL]`, where `s=dt/tau_inh`,
   `L=W·Ca` and `0<f<1` is the activity sigmoid. Solving exactly gives
   `h*=f s L/(1-f+f s)`, with convergence when `|f(1-s)|<1`.
   For fixed f and L, this equilibrium tends to zero as dt tends to zero.
   The code attenuates previously stored inhibition every step, not only new
   drive. Porting a fitted coarse-step model to 0.2 ms is therefore not an
   ordinary timestep refinement. This is a discrete-source-model choice;
   treating it as a timestep-independent continuous law would be a transfer
   error, not proof that the original authors made an error.

A source-faithful discrete module would have to retain its declared update
clock and input semantics. A proposed continuous cellular interpretation would
need its own derivation, evidence and identity; it cannot silently inherit
the old fitted parameters. The README additionally requires external-data
fitting before simulation, then separate MBON-output and learning-rate stages.
Those stages cannot replace our locked gains, learning rate or readout.

## Required invariants, evidence classes and the next decision

| Test or requirement | Evidence class | What it would establish |
| --- | --- | --- |
| Current pair-kernel sign/exchange/proportional cancellation | Engineering identity of the present equation | Correct arithmetic, not reinforcement neutrality |
| Complete-tail and explicitly declared reset semantics | Engineering/numerical contract | No hidden temporal truncation or cross-call history |
| Accurate-prediction fixed point and negative feedback in an error model | Source-motivated engineering requirement | A coherent error topology under its declared assumptions |
| No explicit teaching-label switch in a proposed cellular coupling | Engineering requirement for this task | Endogenous activity cannot be excluded by experiment metadata |
| Distinct local KC state versus soma events; compartment-specific modulation | Biological motivation from the previously inspected local-signaling literature | A reason to examine additional state, not a calibrated numerical rule |
| Monotone inhibitory-state response to fixed neighbor drive, and weaker sigmoid factor with higher recipient activity when slope is positive | Algebraic properties of the inspected source model | Correct placement/sign of that module, not a universal physiological law |
| Exact named-cell identities, all 4,184 home and 3,239 eligible away edges retained; 1,443 other away edges still transmit | Released anatomy plus accepted engineering scope | No outcome-selected remasking or invented cross-channel identity |
| Timestep-dependent discrete equilibrium versus a declared continuous limit | Numerical transfer requirement | A source fit is not silently changed by using a different clock |
| Full original/second qualification and conditioning controls | Existing engineering acceptance requirement | Functional evidence beyond component/source tests |

No released connectome table supplies a proof of these functional invariants.
No exact mathematical neutrality identity in this report is labeled a measured
law of biological learning. Molecular/locality evidence can motivate a module;
the unchanged diagnostic still decides whether that implemented module works
under this task's accepted interfaces.

The minimal useful next deliverable is therefore a separately reviewed local
KC-state module specification, stating precisely whether its output changes
axonal release, calcium, dopamine-driven cAMP or final plasticity susceptibility.
It must specify its time basis and derive invariants before embedding it in the
current circuit. The two explicit source-transfer problems above must be
resolved first. This report selects no new kinetic parameters, inhibitory
weights, routing coefficients, cutoff, mask or gate, and authorizes no run.

## Verification and reading scope

The accompanying synthetic algebra suite passed **87 tests** in 0.39 seconds:
direct four-signal quadrature versus the derived pair kernel; finite/full-tail
partitions; exchange, proportionality, reset and pooling counterexamples;
exact guard-rescaling algebra; exact headroom decomposition; gradient descent
and rectification limits. Quadrature uses a declared 1e-13 absolute comparison
allowance, chosen without any new measured histories. Fraction tests are exact.
No downloaded code, numerical candidate, saved history or circuit was run.

All narrative docs/wiki were reconciled against the previous personal reading
chain. The entire current 656-line handoff, current instructions and every
changed/new closeout page were read. Exact-copy deduplication is used only
where whole-file hashes equal already read content. The new reading receipt
records source versions, access limits and full coverage. This bounded inquiry
used three searches, four direct opens and one PDF-following open; the latter
and the publisher open failed. It made no synapse-data request or production
edit. Repository-wide verification remains root's separate gate.
