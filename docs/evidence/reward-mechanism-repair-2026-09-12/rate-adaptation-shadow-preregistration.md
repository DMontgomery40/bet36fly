# Fixed rectified-rate adaptation: saved-history rejection screen

September 13, 2026 UTC. Scientific specification; a separate machine receipt
must bind this document, the numerical contract, implementation/tests and all
inputs before execution. Until that receipt exists and independent numerical
review passes, no real saved-history evaluation is permitted. This is not a
production learning rule or an authorization to run conditioning.

## Question and evidence boundary

Does a causal, nonnegative rate-contrast signal reduce untaught home drift enough
to satisfy the unchanged half-SD guards on all previously captured cue/noise
groups, without simply omitting part of the learning integral?

The [source investigation](dopamine-signal-sources-resumed.md) motivates examining
signal generation and local modulation, but does not establish this adaptation
equation or its time constant in PPL101 or PAM12. This is an engineered hypothesis
for the accepted positive teaching channels. It cannot model the physiological
PAM-γ3 sugar signal carried by suppression of ongoing activity. No cue label,
teaching schedule, outcome, future spike or observed guard value may enter its
signal computation. The exact graph, selected cells, masks and accepted drive
gains remain unchanged.

The corrected raw and rate-bridge rules both fail the second panel. Retaining
pre-100 ms filter history alone worsened the bridge failure. That hypothesis
stays rejected. This candidate changes the dopamine signal and its eligibility
together, with continuous history as explicitly fixed below. Comparing it with
the same-history unadapted operator separates adaptation from that already
measured history effect. No adaptation-time, rate-time, onset, eta, offset,
normalization, cue or noise sweep is allowed after seeing this result.

## Fixed signal and gain contract

Let S_Kj be actual binary KC spike impulses and S_Dc actual selected-DAN spike
impulses averaged over the full channel population (two home PPL101 cells or
22 away PAM12 cells). All dynamic states are zero at electrical time zero.
At each actual event, R_K receives 1/100 ms and R_D receives the population-mean
event count divided by 100 ms. B and both eligibility states do not jump.

Between events, with time in milliseconds:

```text
dR_K/dt = -R_K / 100
dR_D/dt = -R_D / 100
dB/dt   = (R_D - B) / 500
Dplus   = max(R_D - B, 0)
dE_K/dt = R_K - E_K / 500
dE_D/dt = Dplus - E_D / 500
unbounded gain derivative = 0.0005 * 0.96 * (E_D * R_K - E_K * Dplus)
```

R and Dplus have spikes/ms units; E has spike units. Both signed terms use the
same Dplus history. All states evolve during [0,100) ms, but gain writes are
suppressed there. At exactly 100 ms, retain the preceding interval's state,
inject that boundary's real events once, and start gain integration. Electrical
end time remains 400 ms. Integrate the entire no-new-event continuation beyond
400 ms, including every rectification crossing. The tail is mathematical signal
continuation, not simulated spikes, voltages or extra neural time.

The 100 ms rate, 500 ms eligibility, eta, normalization, onset and bounds are
inherited engineering settings. The new baseline time equals the existing
500 ms eligibility time as one fixed engineering assumption. This equality is
not a source-derived receptor law. No replacement values will be selected from
the measured response.

Preserve the established discrete gain-publication policy. Initialize a double
accumulator G from each saved float32 gain F. Sum the exact gain integral over
each complete 0.2 ms interval, then clamp G+delta to [0.5,1.5] and publish its
float32 value once. Splitting an interval at a Dplus zero is only for signal
integration and does not add a gain clamp/publication. Likewise sum the complete
analytic tail before one final clamp/publication. This differs from continuously
projecting a bounded gain ODE, and the oracle must test the stated policy.
Discard dynamic state and double rounding remainder after the final checkpoint;
only published gains can persist across calls. All real screen trials start
from independent unit gains. Eta zero preserves every gain byte.

All 4,184 home edges remain eligible. Exactly 3,239 gamma away edges are eligible;
the other 1,443 away edges remain byte-identical. The full 8,866-edge arrays,
mapping, class groups and excluded edges remain in retained outputs. The shadow
calculator has no neural engine, transmission callback or output path that can
replace an actual checkpoint.

## Input identity and fixed execution scope

Use only the existing capture `onset-history-capture-4343c21535c43f42` under
`output/collaboration/reward-mechanism-repair/onset-history-captures/`.
Its summary SHA256 is
`244b4dcc1aa40b8c0c7be068bf7e66f8e369921f1005dd474ca37f9460dabb1b`;
receipt SHA256 is
`9aeea0c9227bf9ad4326277c39eb47966d5ab95ba6870bb3720f0d9b278788fc`;
sample-map SHA256 is
`5f2414ffe5cab3d99cc1c1f0e91071df1f48721a7709816e90360af8b41074b3`.
The [independent capture audit](onset-capture-independent-audit.md) binds all
104 inputs and the full original capture accounting.

The new receipt must enumerate and hash the 32 fine rasters, both corresponding
cold/continuous shadow archives per trial, sample map, capture summary/receipt
and all mapping/identity dependencies actually consumed. Validate exact sample
identities, 2,000 binary 0.2 ms bins, retained mappings, cue order, run IDs and
seeds before calculation. Preserve all 32 rows in their original order: 16
original-panel and 16 second-panel rows, each with eight cues and base/alternate
noise. No extra, missing or duplicated row is acceptable. This is evaluation on
already used data, not an unseen test set.

Planned circuit calls: **zero**. Planned candidate saved-history evaluations:
exactly **32**, under a 600-second wall cap including input checking and output
recording. Record each attempt before calculation and each completed result
afterward; stop on exception, input change or cap breach, retaining partial
output. Never restart an existing identity or overwrite its receipt/results.
Synthetic numerical tests and read-only audits are recorded separately and do
not count as real cue evaluations. No conditional extension or discarded trial.

## Required numerical tests and retained measurements

An independently written analytic/quadrature or high-accuracy ODE oracle must
check finite intervals and the full tail, including tau_baseline=tau_eligibility
repeated-exponent terms and Dplus crossing zero inside an interval or tail.
The implementation recurrence cannot be its own only oracle. Freeze the exact
tolerances and oracle/test hashes in the numerical contract before the screen.

Tests must cover empty and one-sided histories, finite pulses, coincidence and
event order, sustained rate/adaptation limits, unequal channel populations,
synchronously replicated/partial DAN populations, pre-onset events and exact
onset boundaries, appended silence plus full-tail invariance for unbounded areas
and bound-free final gains, reset/checkpoint
semantics, masks/permuted edges, learning-off, sub-ULP accumulation, and lower/
upper/exact/rounding-only/contact-and-recovery bounds under the stated discrete
policy. Validate malformed/nonfinite events, state, mappings and configuration.
Synthetic physiology-like ordering is a numerical input, not measured fly data.

With clipping, appending finite intervals changes the scheduled clamp/publication
boundaries relative to a single tail publication and can change bounded gains.
Do not assert clipping-invariant final gains across those different schedules;
test each against its own explicitly scheduled reference instead.

For every real row retain final float32 gains; double attempted, bounded-applied
and published changes per edge and class/channel group; true positive and
negative product integrals; onset/400 ms signal states; pre-onset no-write
checks; exact finite/tail accounting; and inclusive electrical/tail bounds.
Keep the three electrical phases [100,130), [130,300), [300,400) ms and the full
tail separately. Do not infer separate positive/negative areas from net change.

Additionally retain each edge's integrated positive-plus-absolute-negative area.
An area smaller than its initial distance to either bound proves that no
unbounded prefix excursion can reach a bound, including inside the tail.
For these nonnegative same-history signals Dplus≤R_D and E_Dplus≤E_D_unadapted;
independently verify the resulting area domination. The previous continuous
shadow's maximum area was 0.1571136419805323, below the unit-gain margin of 0.5.
Do not confuse this conservative path proof with actual discrete bound counts.
If that proof or direct numerical consistency fails, stop interpretation and
investigate; do not hide a possible excursion by net cancellation.

Before interpreting adaptation, reproduce the saved cold and continuous
unadapted comparator gains/phase accounting from the same histories, preserving
their published values and declared numerical tolerances. Bind rather than
overwrite their existing results. Each candidate result must be matched to both
comparators for the same exact cue/noise/seed, with all inputs rehashed afterward.

## Decision fixed before measurement

For each of the eight panel/channel/noise cells, calculate U_i as the arithmetic
sum of final published eligible gains minus one. Report all eight values,
mean, sample SD (ddof=1), and unchanged limit 0.5×SD. The necessary stability
screen requires abs(mean U)≤0.5×SD for **every** cell, zero electrical/tail bound
observations, intact masks and successful numerical/input audits. Equality uses
the existing inclusive definition. Do not round values before the decision.

Also report the second/base home adaptation-minus-continuous and
adaptation-minus-actual-cold contrasts in published and attempted units. Smaller
absolute mean alone is insufficient: changing both mean and dispersion can
still fail the guard. A sign reversal with excessive positive drift also fails.
Neither a favorable single cell nor an averaged result can override any failed
cell. Numerical invalidity is distinct from a valid scientific rejection.

Any failed stability cell rejects this fixed candidate as a sufficient repair
on these saved trajectories. Preserve its failure and stop; do not tune its
time constants, onset, thresholds or masks. A passing screen establishes only
conditional plausibility on fixed untaught spikes. It does not establish
teaching, recurrent stability, cue-specific acquisition, reversal or improved
sports prediction. A production implementation would still require a separate
frozen identity, full independent tests, both unchanged seven-criterion circuit
panels with complete replay evidence, and only then the existing conditioning/
reversal contract. Current UI qualification and the active checkpoint stay as-is.
