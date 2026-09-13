# DARELA primary-source contract and transfer decision

September 13, 2026; BET36FLY checkout `64a4b1d`. **The inspected source fixes a
mouse FSCV burst model and numerical reference. It does not fix a per-spike
PPL101/PAM12 release law.** An every-actual-spike construction is mathematically
definable, but is a separately declared engineering hypothesis. Root's later
specific finite-trial proposal is assessed below using the published WT1
values. No parameters are fitted here, and no model or history was run.

## Sources and exact version boundary

The primary paper is Shashaank et al., *Computational models of dopamine
release measured by fast scan cyclic voltammetry in vivo*, PNAS Nexus
2(3):pgad044, DOI [10.1093/pnasnexus/pgad044](https://academic.oup.com/pnasnexus/article/2/3/pgad044/7034164).
It was published February 10, 2023 and corrected/typeset March 10, 2023.
The pertinent Results, Discussion and Methods and all seven supplement pages
were inspected. Supplement S1/S4 and Tables S1-S3 were available as extracted
PDF text. Two equation/table screenshot requests failed with cache misses;
a clean-URL fallback failed. No visual PDF inspection is claimed. Display
equations 1 and 2 are omitted in the indexed main-article HTML; their prose
definitions were read, while the exact discrete mask below comes from code.

All 12 locally pinned repository files were personally read and their 32,242
bytes checked against SHA256 and Git blob identities. The revision is
[`125c27bc59b0c493c902c8724f58fa3d9d8b354d`](https://github.com/DSulzerLab/DARELA/tree/125c27bc59b0c493c902c8724f58fa3d9d8b354d),
February 15, 2025, with a previous-kinetic-state correction. This is not an
identified publication-revision checkout. The MIT license, citation and
original source bytes remain intact. Repository setup calls it version 1.0;
that label alone does not identify the 2023 implementation.

## Measured preparation and meaning of the inputs

The fitted observations are dorsal-striatum FSCV from isoflurane-anesthetized
male or female mice, with electrical stimulation in the ventral midbrain.
The experiments used 400 microampere current and a 10 Hz electrode sampling
rate. A single burst contained 30 pulses at 50 Hz; the repeated protocol
contained six such bursts separated by 5 seconds. The protocol had 2-minute
single/repeated recovery intervals and 6-minute inter-sweep recovery intervals.
The reported current-release linear regime was 0.3-0.6 mA. These are stimulation
and population concentration measurements, not identified single-neuron spike
counts or release probabilities. [Primary Methods and Figures 2-4](https://academic.oup.com/pnasnexus/article/2/3/pgad044/7034164).

The state factors are phenomenological facilitatory/depressive release
components. They are not receptor occupancy, finite vesicle pools, or the
Handler intracellular coincidence/ER branches. The source was tested against
in-vivo FSCV; its discussion distinguishes that preparation from slices and
notes tonic concentrations below conventional FSCV detection. It does not
calibrate continuously spike-driven release for the selected fly cells.

## Printed equations, units and fixed parameter rows

For a nonoverlapping experimental burst envelope S in {0,1}, frequency f in
Hz, time and tau in seconds, and dimensionless factors H and p:

```text
A(t) = product_j H_j(t)
dH_j/dt = f*p_j*H_j*S + (1-S)*(1-H_j)/tau_j
dC_s/dt = L*DAp*I*f*S*A - Vm*C_s/(C_s+Km)
dC_e/dt = kS*C_s - kE*C_e + kGamma*Gamma
dGamma/dt = kads1*C_e - kads2*C_e*Gamma - kads3*Gamma
```

These are main equations 2-4 and 10-11; the supplement gives the Euler
discretizations. S denotes a supplied **experimental burst interval**. Recovery
is off for that entire interval, including the time between its pulses.
With S=0, each factor returns toward one. DAp is in micromolar/mA for SUR
and STUR, I in mA, Vm in micromolar/second, and Km, C_s and C_e in micromolar.
L is a dimensionless DA loss factor, named explicitly in README/ode.py.
The STDR DAp unit instead includes an additional micrometer from its spatial
point-source convention; these DAp values cannot be exchanged between models.

Table 1 gives the following fitted factors, shared across its single/repeated
and three spatial-model variants within each row. These are externally
published parameter sets, not parameters estimated or selected in this task.

| Preparation | p1, p2, p3 | tau1, tau2, tau3 (s) |
| --- | --- | --- |
| WT sweep 1 | 0.0105, -0.003, -0.0011 | 7.50, 15.0, 900 |
| WT sweep 6 | 0.0105, -0.003, -0.0011 | 7.50, 12.5, 900 |
| alpha-Syn KO sweep 1 | 0.0050, -0.003, 0 | 7.25, 37.5, 900 |
| alpha-Syn KO sweep 6 | 0.0040, -0.003, 0 | 7.25, 45.0, 900 |
| Syn TKO sweep 1 | 0.0040, -0.003, 0 | 7.25, 37.5, 900 |
| Syn TKO sweep 6 | 0.0040, -0.004, 0 | 7.25, 37.5, 900 |

The [parameter transcription](darela-published-parameter-transcription-dopamine-sources-2026-09-13.json) records all Table 1 release/uptake rows
and all three supplement-table release/measurement parameter sets. In
particular, SUR WT sweep-1 single/repeated DAp values are 0.420/0.395,
Vm=4.8 and Km=0.2; Table S1 fixes I=0.4, f=50, NP=30 and L=0.9. The shipped
example instead uses DAp=0.43 and tau2=12.5. It does not reproduce a complete
published WT row merely by being the public example.

There is a printed-unit issue: supplement tables label kads2 as inverse
seconds, but S10 multiplies it by two concentration-valued states. Dimensional
consistency would require inverse concentration-time units. The derivation
of Gamma as adsorbed molecules divided by volume also gives it concentration
units. This report records the discrepancy; it does not silently correct the
source's numerical values. Source code fixes kGamma=1 but supplies no missing
fly concentration calibration.

## Published Euler scheme versus pinned code

Supplement S1 uses forward Euler. SUR sets dt=1/f, hence 0.02 seconds at
50 Hz. An active source step is `H_new=(1+p)*H_old`; an inactive step is
`H_new=H_old+dt*(1-H_old)/tau`. The exact continuous burst solution instead
multiplies H by `exp(f*p*T)`. Converting an isolated event into `exp(p)` is
therefore not the literal SUR update. The spatial models use dt=1/480 second
from dR=1 micrometer and D=240 square micrometers/second.

The inspected code adds several important implementation choices:

1. `base.py` builds `nt=int(end/dt)+1` and labels it with `linspace(0,end,nt)`.
   Its update still uses dt, so arbitrary end times can make label spacing
   differ from the integration interval. A literal reference must freeze
   requested times; it cannot claim general sampling invariance untested.
2. The burst mask sums products of two Heavisides, both with value one at
   zero, after rounding their arguments to two decimal places. Both endpoints
   are included. On the example's aligned 20 ms grid, start 0.34 and end
   0.94 produce 31 driving steps when the output extends beyond the end.
   This follows by source inspection, not an executed pulse-count result.
3. `ode.py` advances H first, then computes A from **new** H and uses it in
   release. Supplement S4 writes A(t) at the old time. Electrode/adsorption
   updates use old concentrations. A literal code reference must preserve
   this ordering and identify its difference from the printed Euler formula.
4. Full solve initializes C_s, C_e and Gamma to zero; H defaults to one or
   accepts `kinetics_state`. The 2025 change does not resume a complete
   chemical state. Full SUR solve returns interpolated C_s/C_e, not H/Gamma.
   `solve_kinetics` remains a separate three-factor helper and uses dt=1 s
   when no bursts are supplied. It is not a general exact tail/checkpoint API.
5. The mask sums overlapping bursts without restricting S to one. With
   S>1, `(1-S)` reverses the recovery term's sign. Encoding each neuronal
   spike as a new finite-duration burst is not an innocent input substitution.
   The intended nonoverlapping source protocol avoids this problem.

There is no infinite-tail result in the public solve API: it integrates to a
requested finite end and interpolates. In the continuous equations, after
the final burst H recovers and no new release source is present, while
chemical uptake and electrode/adsorption states can continue evolving. An
event-impulse bridge would instead have silent H recovery and only the bridge
tail. Those are different state and tail contracts.

## Transfer decision and fixed falsifiers

The minimal admissible next computation is a separately frozen **literal
source-reference check**, with printed equations and pinned-code behavior
reported separately. Its constants can come from a complete published row;
the shipped example can be a separately labeled software fixture. Endpoint
counts, H/release phase, initialization, finite-tail output and source-file
identity must be tested before using the implementation as evidence. No
source-fit quality or fly learning follows from passing that reference.

An actual-spike embedding must additionally choose: factor initialization;
whether every body's event multiplies H by `1+p` or `exp(p)`; exact versus
Euler inter-event recovery; release before or after factor update; a rested
spike's mass and chemical units; body-local transformation before population
averaging; and reset/continuation/tail behavior. None of these mappings is
fixed by the MaleCNS contacts or measured fly receptor data. Choosing a unit
rested impulse makes a dimensionless engineering test, not measured release.
Using teaching labels for S would be inadmissible. Applying the same nonlinear
transform to a pooled mean generally differs from transforming each cell.

The earlier illustrative exponential-jump construction has the pre-spike
map `h_next=exp(p-Delta/tau)*h+1-exp(-Delta/tau)`. Its facilitation state has
a finite periodic fixed point only when `Delta>p*tau`; equality gives linear
growth and smaller intervals exponential growth. WT1 gives 0.07875 seconds
for this boundary. For a `1+p` jump, the analogous boundary is
`Delta>tau*log(1+p)`. The negative-p factors do not force the product to zero
at fixed positive intervals: they have positive limiting states. Thus the
unbounded facilitation can also make release unbounded. This is an algebraic
domain objection, not a circuit result or proof against physiological release
plasticity. Adding a pool or cap would be a further mechanism choice.

Long recovery constants alone do not rule out a 400 ms effect: during a
continuous source burst, `d log(A)/dt=f*sum(p)`. Conversely, neither that
finite-burst responsiveness nor the recorded 310 ms electrical distinction
guarantees stable tonic behavior or correction of the untaught-home drift.
Required engineering falsifiers include identical-history determinism,
no event-driven release without events, explicit rested/repeated responses,
positive finite state over the declared domain, cell-before-pool tests and
complete reset/tail accounting. Accepted gains, eligibility, bridge onset and
qualification/conditioning criteria stay unchanged. A release transform
feeding the old antisymmetric rule also retains its zero isolated-coincidence
result; it is not the distinct intracellular two-branch order detector.

## Root's specific finite-trial event proposal

After the source inspection, root specified one concrete hypothesis for
assessment: use the complete WT sweep-1 factor row, q=1+p, exact inter-event
recovery, pre-update release, and H=1 at the start of each accepted 400 ms
trial. Every actual spike of each DAN drives its own state; no teaching label
or detected-burst metadata enters the transform. With Delta in seconds:

```text
H_j(t_minus) = 1 + (H_j(previous_event_plus)-1)*exp(-Delta/tau_j)
a_i(t) = product_j H_ij(t_minus)
H_ij(t_plus) = (1+p_j)*H_ij(t_minus)
```

There is no emitted impulse when no actual spike occurs. Pool only the
transformed body events, divided by the unchanged channel population count.
At a single event, pre-update release equals post-update release divided by
`product_j(1+p_j)`. That algebra supplies a unit rested-spike convention;
it does not make the full event-driven trajectory identical to a source burst,
which suppresses recovery between pulses. Exact inter-event recovery, unit
release, cell-before-pool transformation and per-trial reset are explicit
engineering assumptions. All physical events before the accepted 100 ms
bridge onset should evolve H if this is the chosen contract; the bridge
itself remains cold until that unchanged onset. Empty tails emit nothing,
while previously emitted impulses still require the complete bridge tail.

**The evidence does not disqualify this finite construction merely because
its infinite tonic limit diverges.** Every q is positive. Exact recovery is
a convex combination of the previous positive state and one. For n events,
`1<=H1<=q1^n` and `0<H2,H3<=1`. The 2000 binary native slots in a 400 ms trial
give the conservative bound `a_i<=q1^2000<=exp(21)`, even without using a
refractory restriction. Thus all states and release masses are positive and
finite over the proposed domain, without adding a state cap. This is a
mathematical bound, not a claim that actual traces attain it or that resulting
gain changes satisfy the guard. Release masses can exceed one; a numerical
adapter must support that declared finite nonnegative domain rather than
silently clipping them to the original binary/pooled-mean range.

This makes the exact proposal admissible for a separately frozen numerical
hypothesis check, conditional on independent synthetic verification of event
order, source-versus-embedding distinctions, reset, permutation/pooling,
no-spike behavior and complete tail. The p/tau values must stay at the
specified external WT1 row; no member of the other published parameter sets
may be chosen based on these histories. The finite reset contract cannot be
promoted into a chronic physiological mechanism or uninterrupted tonic model.
A 32-untaught fixed-history screen could reject it under the unchanged guard;
passing that screen alone would not establish taught response, circuit
feedback, qualification, acquisition or reversal. No such screen was performed
in this source review.
