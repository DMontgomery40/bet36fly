# KC local calcium candidate: declared transfer before outcomes

September 13, 2026. Root decision following source-audit commit `b86405d`.
This is a new engineering hypothesis, not a measured MaleCNS receptor model.
No candidate has run. Its parameters will come from one separate re-fit of
the preserved external WT/KD calcium objective, not BET36FLY histories.

## Variables and operator

Retain the inspected source's calyx calcium C, axonal calcium L, adaptation a
and inhibition I. Use its complete old-state recurrence at d0 = 1/30 second,
with baseline zero and no added noise. All four variables start at zero at
each trial's electrical time zero. They evolve before the unchanged plasticity
onset; the existing rate-bridge states still start cold at that onset.

One KC spike within a completed source frame contributes one source-input
unit to that frame. Equivalently, a steady reference of one spike per source
frame maps to source odor input u=1, or q=1/30 source-input seconds/spike.
This is a declared dimensionless convention, not a biological calcium scale.
Do not divide by the alternating 166/167 electrical-sample count.

Before each electrical event at t/5000 seconds, execute every source boundary
k/30 <= t/5000 for k >= 1, using only events strictly before that boundary. Then read
the held susceptibility s=L/C, with s=1 when C=L=0, and supply s times the
current KC impulse to BOTH existing KC bridge filters. Finally accumulate
the original binary impulse into the current source frame. Boundaries precede
electrical samples 167, 334, 500, 667, 834, 1000, and so on. An event exactly
at a boundary belongs to its new frame. Use integer/rational scheduling.

This changes the local presynaptic signal's temporal and cell dependence.
It neither rescales the signed weight update directly nor continuously injects
calcium into the bridge. Existing bridge signal integration and its complete
analytic post-trial tail therefore remain applicable. With no more electrical
spikes, later local calcium decay cannot create further bridge impulses. Trial
state is discarded after that tail; only the existing sparse gains persist.
Close any completed source frame at the electrical trial endpoint before
recording final local state; this creates no additional electrical impulse.

## Anatomical support and unchanged interfaces

Build W with recipients as rows and presynaptic KCs as columns, using retained
KC-to-KC contact counts, excluding the one self-pair. Normalize each nonempty
incoming row to one; an empty row remains zero. Multiply by the external fit's
inhibition strength inside the local recurrence. This replaces the source's
uniform all-to-all assumption with existing contact support. It adds no edges.
The slow branch uses previous-frame local activity without a separately fitted
synaptic delay. Contact normalization is a new local-model assumption, not a
change to the accepted electrical weights or KC input gain.

Apply the local state to all 4,064 KCs as an explicit pan-KC extrapolation from
gamma-KC physiology. Report gamma, alpha/beta and alpha-prime/beta-prime results
separately, retaining an other/unresolved subtype bucket as well. Do not
gamma-filter home. All 4,184 home edges and 3,239 supported
away edges retain their eligibility flags; the 1,443 other away edges continue
transmitting without updates. Local suppression does not redefine that mask.

Fast electrical transmission, retained gains, input encoder, readout, learning
rate, rate and eligibility time constants, endogenous DAN activity, teaching
pulses, gain bounds and every qualification/conditioning criterion stay fixed.
No external-shock gate or source LTD-only rule is imported.

## Numerical admissibility and falsifiers

Require finite nonnegative coefficients, positive tau_C, tau_input and sigmoid
slope, and tau_adapt >= d0 and tau_inh >= d0. At every source update require
1-d0*(1+a)/tau_C >= 0. These conditions preserve nonnegative adaptation and
inhibition and the order 0 <= L <= C under the source's calcium clipping.
Reject a violation before interpreting a learning result. Do not clamp the
ratio, enlarge a fitted time constant, or select replacement parameters.
Reject every nonfinite state/output, L > C, or C=0 with L>0, before publishing
that source update. Numerical admissibility is independent of learning guards.

Independent tests must establish: exact source-function agreement for matched
inputs; correct asymmetric contact orientation; no-self/empty-row behavior;
integer-clock event boundaries; invariance to input chunk boundaries; cold
first-spike and post-zero behavior; attenuation with neighbors and relief
with recipient activation under controlled local state/drive and the source's
old-state latency (not a claim of global recurrent monotonicity);
no-lateral equivalence to the original impulses;
old-state continuation after stimulus offset; and explicit failure on invalid
numerical domains. A recorder must not affect the trajectory.

After the external fit and standalone implementation pass those checks, bind
the selected parameters, code, anatomy and this contract to a new identity.
Run a single bounded untaught fixed-history screen across the existing 32
histories as an early rejection test, preserving every guard. A favorable
screen is not qualification: both complete unchanged live circuit panels,
then the frozen acquisition/reversal controls, are still required. A failed
screen is preserved and rejected without parameter or threshold tuning.

The external fit itself is a source-objective re-fit using this environment's
SciPy L-BFGS-B in physical coordinates, not an exact reproduction of the
upstream lmfit optimizer. It uses the source's initial decay fits, seed-666
population, 30-Hz stimulus, SE-weighted objective and L1 penalty, sequential
KD then WT, maxfun 3000/maxiter 500 per stage, one 120-second hard process cap.
No noise/OE fit, upstream driver, sports data, restart or selection among runs.
Only a fully converged, finite fit can supply this candidate's parameters.
