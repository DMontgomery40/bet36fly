# Independent causal-prefix and identifiability contract

September 13, 2026 UTC, inspected repository `dce1582618f6c386a4996695bc77ad4218dd493c`.
This is a mathematical/data contract before inspecting the proposed comparison's
actual arrays. No source induction, native call, captured-history calculation,
optimization, fitted threshold or new candidate is performed here. All 189
current narrative paths match this reviewer's complete personal reading chain.

**No inspected contract establishes that every admissible mechanism must fail.**
The actionable next check is whether the current recorded circuit presents
label-free joint input differences before teaching-dependent gain feedback
changes the KC histories. Existing records permit a restricted causal-prefix
check; they do not provide complete taught local histories.

## What is required, and what biology does not promise

The frozen diagnostic uses mean taught-minus-matched-untaught gain SUMS across
eight cues separately per channel/seed set. Its mean must be negative and at
least three times the untaught mean magnitude. The separate half-SD untaught
guard neither requires every untaught trial to be zero nor demonstrates absent
bias. A single taught/untaught collision therefore does not make that panel
logically impossible. Cross-channel leakage and cumulative drift have their
own unchanged quantitative limits. See
[original v1.1](../reward-repair/evidence/candidate-rule-spec-v1.1.md) and
[`evaluate_panel`/`evaluate_cumulative`](../../../bet36fly/reward_diagnostic.py),
lines 265–370. Positive rescaling cannot generally repair the normalized
untaught statistic; its failure is not a demand that ongoing fly DAN spikes
must be biologically inert.

The conditioning addendum requires actual cue-specific MBON depression and
preferred-edge MEAN depression, with fixed null comparisons. Strict reversal
additionally requires old-response/old-gain recovery in both selected channels;
ordinary preference remapping is separately labeled. These are explicitly
engineered tests. Hige's γ1pedc backward null and Handler's different γ4/γ5
preparations do not establish universal backward potentiation in γ1pedc/γ3,
but neither proves that all admissible mechanisms and all relevant timings
cannot meet this engineered demand. The source induction is longer than the
400 ms diagnostic; reproducing it is not possible inside that trial, which is
a protocol-transfer limitation, not proof of no receptor action within 400 ms.
Do not alter the frozen criteria or claim source-calibrated γ1pedc/γ3 erasure.

The complete-tail linear-response DPR result rejects a particular direct
positive-spike/two-filter transplant as a claimed preservation of source
properties. It is not a theorem about every nonlinear or compartment-specific
mechanism. The rejected scalar adaptation, headroom and KC L/C mappings remain
rejected. No restart or new parameter selection follows from this review.

## A parameter-free identifiability reference

For an allowed deterministic local mechanism, write

`(z_next, g_next) = F(z, g, K_e, D_e; fixed cell/edge attributes)`.

The initial state, input units, complete causal history and complete-tail policy
are part of the input. Equal complete allowed histories and equal initial
states must produce equal updates. Trial labels, sports outcomes, pulse-request
metadata and an absolute "teaching phase" switch are not additional learning
inputs. Fixed anatomical attributes are allowed but cannot encode trial labels.

This gives an exact collision test, not a threshold classifier: compare the
complete permitted histories before asking whether a particular state equation
can separate them. If all target-edge inputs coincide for every matched cue in
one required diagnostic channel/seed panel, all matched target effects vanish
for that deterministic input-only replay and the negative-mean gate is
impossible for that restricted input class. An isolated collision is not this
certificate. Unequal histories merely permit a difference; they do not prove
source-supported kinetics will produce the required sign, amplitude, guards,
retention or response changes. A near-collision needs an independently specified
continuity bound to imply a numerical output limit; no distance threshold or
classifier fitting is authorized.

Current learning receives compartment-pooled DAN events. Equal pooled counts
can hide different DAN body/hemisphere histories. A model using local release
from particular DAN cells has a richer input and cannot be ruled out by pooled
collisions. Conversely, contact counts do not reconstruct release or receptor
occupancy. Before evaluating such a model, its required actual per-cell inputs
and independently declared spatial coupling must exist.

## Existing-record prefix: exact definitions

Compare each **active-plasticity** taught row with the untaught row having the
same original/second panel, source cue, seed set, actual seed, schedule, unit
initial gains, graph, mask, source/kernel and bridge contract. Frozen rows are
not substitute KC histories: their gains can already differ after onset.
Retain all 32 matched histories for each teaching direction; no selection by
downstream gain result. Pairing metadata identifies an analysis contrast only;
it never enters a hypothetical local learning function.

For current bridge records, `step_signals` has float32 shape `(2000,5)`.
Columns 1 and 2 are actual pooled DAN events. For each declared population
`N_c` (2 home, 22 away), construct the exact dictionary

`float32(float64(k)/N_c) -> integer k`, for `k = 0,...,N_c`.

The native recording does precisely double division followed by a float cast
(`reward_lif.cpp:221–231`). Require each stored value to be the exact canonical
float32 encoding, finite, uniquely decodable and in range; do not multiply and
round approximately or accept a nearest value with a tolerance. Canonical zero
is positive zero; unsupported encodings are invalid evidence. Use the verified
integer counts for equality, and double `k/N_c` only when reporting the actual
bridge input. The whole-KC count in column 0 is also exactly represented and
must be an integer from zero through 4064.

Define **j\*** as the first step at which the decoded taught and untaught
counts differ in **either compartment**, not just the taught channel. If no
such step exists, report null and 2000 equal steps, not an invented endpoint
divergence. A valid current matched pair cannot first differ before the first
requested pulse at step 1550 (310 ms). Later divergence need not fall on a
pulse-request step and need not be positive. Its timestamp is exactly j*/5 ms.
Do not call a difference an accepted causal pulse or a measured dopamine dose.

## Why the KC prefix is available, and where it stops

The inference uses the current implementation, not general fly physiology:

1. Electrical and chemical state reset identically; rates, fixed sensory RNG
   draws and unit starting gains match. Both compared arms have plasticity on.
2. All selected teaching DANs are pure-dopamine rows whose **fast outgoing
   weights are exactly zero** (`reward_protocol.py:170–174`). Teaching changes
   their voltage/refractory behavior, but has no separate outgoing fast current.
3. Before j*, both compartment event inputs agree. The current bridge therefore
   receives identical KC/DAN input, has equal states and publishes equal gains
   by induction. These gains may contain shared untaught drift; they are not
   asserted to remain one.
4. At each step the kernel delivers queued currents using existing gains,
   integrates voltages, applies teaching, then selects all spikes. Only then
   does it update the plastic gains (`reward_lif.cpp:181–261`). Hence all
   non-DAN spike histories, including every KC, agree **through the spike
   selection at j***. The first pooled-DAN difference may update gains after
   that selection.

Thus the hash-verified untaught fine raster supplies the actual KC history
through and including j* for this matched current-bridge pair. Use prefix
indices `[0,j*+1)`. With no pooled divergence, the inference extends through
the whole recorded trial for the current pooled bridge. It says nothing about
unrecorded electrical continuation after step 1999.

This does **not** assert identical individual DAN spikes, voltages or refractory
states between the first requested pulse and j*. Pooling may already hide
cell-specific differences. Nor does it extend the KC equality to j*+1: pending
KC events already in the queue are multiplied by the newly published gain
when delivered. The nine-step transmission delay does not provide nine extra
steps of equality. Do not reuse the untaught KC raster for later taught
activity or present the observed current-bridge prefix as a new candidate's
counterfactual circuit trajectory.

The prefix proof assumes only spike-driven pooled chemical inputs. An added
local voltage, receptor baseline, body-specific DAN release or unrecorded
presynaptic state needs its own input/initial-state proof. These cannot be
filled by the trial label or by zero for "not recorded".

## Evidence checks and independent synthetic references

The existing 32 fine captures are untaught-only, with binary `(2000,4774)`
traces and explicit KC/DAN/sensory column maps. Validate their frozen identities,
32-row selector, absence of teaching, sample mappings, fine/coarse parity and
exact counts before using a prefix (`onset_history_capture.py:125–224,271–278`).
Check the full untaught per-compartment integer stream against the fine DAN
columns and the full KC total against all fine KC columns. Through j* inclusive,
the taught recorded KC total must also match. Where sampled coarse bins are
retained, compare complete bins wholly inside the proven prefix; a bin
straddling its end cannot certify a sub-bin identity. Taught per-cell DAN bins
can expose hidden cell differences in complete pre-j* bins, but cannot locate
their fine timing. Record those limits rather than silently extending coverage.

Independent boundary references for the root-owned helper/tests:

- Population counts 0,1,N decode exactly for N=2/22; all valid k values pass.
  Nonfinite, negative, over-population, neighboring F32 encodings, fractional
  counts, noncanonical zero and malformed dtype/shape fail.
- A difference only in the other compartment determines j*, even if the taught
  compartment first differs later. No-difference is a separate valid case.
- j*=1550 includes KC row1550 and excludes1551. A valid later j* not on a pulse
  time must be retained. A pre-1550 divergence contradicts the matched-input
  assumptions and must invalidate the claimed prefix.
- Two cells swapping spikes can preserve every pooled count while changing
  local cell exposure; the pooled equality result must not claim cell equality.
- Shared nonunit gains before intervention satisfy pair identity; a mismatched
  initial checkpoint or plasticity-off comparator does not.
- Synthetic queued-KC arrival immediately after first gain divergence shows why
  j*+1 is outside the proof even with nine-step delay. Spike selection at j*
  still uses the common pre-update gain.
- A mismatched seed, cue, input-map role, count reduction, source hash, duplicate
  or missing pair, or unsupported record schema must fail before statistics.

No new numerical learning response or gate score is part of this check. Its
useful outcome is either a contradiction of the prefix assumptions, an exact
restricted collision, or a measured raw joint-input distinction available to
an independently specified mechanism. Full taught local histories and a
valid nonlinear state/readout map remain required before a complete candidate
assessment; even complete replayed histories cannot prove closed-loop learning.

## One inherited causal-attribution blind spot

The frozen v1.1 criterion-3 explanation says identical other-channel DAN signals
with different rule terms diagnose indexing/modulation leakage. That inference
is insufficient once learning changes KC/gain histories: identical D alone
does not fix either `E_D R_K` or `E_K R_D`, nor a weight-dependent update.
[`evaluate_panel`](../../../bet36fly/reward_diagnostic.py) currently computes the
cross effect and threshold; it does not establish that causal attribution.
Compare the complete joint inputs and checkpoint ancestry first. Preserve the
historical specification and numeric gate; use a new interpretive correction
rather than changing the frozen artifact or declaring contact/label leakage.
