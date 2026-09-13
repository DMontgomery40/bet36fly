# Fixed rate adaptation rejected on saved spike histories

September 13, 2026 UTC. **This candidate fails all four home stability cells.**
The nonnegative adaptation signal replaces the earlier untaught depression with
excessive potentiation. It is not a sufficient repair, and no production rule,
parameter, threshold, anatomical mask or active checkpoint was changed.
Conditioning and reversal remain unrun.

## Frozen test and complete result

The [scientific specification](rate-adaptation-shadow-preregistration.md) fixes
the equations, 32 previously recorded cue/noise histories, eight separate guards,
complete tail and rejection decision. The baseline follows the filtered DAN
rate with a fixed 500 ms time constant; both learning products use the same
positive rectified contrast and its eligibility. That equation is an engineered
hypothesis, not a measured receptor law for PPL101 or PAM12. The
[source investigation](dopamine-signal-sources-resumed.md) explains this limit,
including the natural PAM-γ3 reward signal that positive-only contrast cannot
represent.

Root froze identity `rate-adaptation-shadow-5165a92674683bf2b872` at
04:42:58 UTC, before any candidate evaluation. The manifest SHA256 is
`5165a92674683bf2b872753148af74e3adf038ca7a95c64735dcda8e29e5ee46`.
The [freeze receipt](rate-adaptation-root-freeze.json) and
[combined numerical/boundary review](rate-adaptation-combined-prerun-review.json)
bind the implementation, both independent test files, oracle, contracts and
input identities. No candidate identity was restarted or discarded.

Exactly **32 attempts and 32 completions** took **50.4832 seconds**, within the
600-second limit. There were **zero circuit calls**. All 32 captured spike
rasters, their 64 earlier cold/continuous comparators and the sample map were
preserved. Every trial reproduced both earlier operators before evaluating the
new one. Alternative gains never influenced the recorded spikes.
The [complete result](rate-adaptation-shadow-5165a92674683bf2b872/summary.json)
retains each row, seed, comparison, output hash, attempt and completion.

For each cue, U is the sum of final published eligible gains minus one. Each
cell contains eight cues. The fixed guard is `abs(mean U) <= 0.5 * sample SD`,
without rounding the decision.

| Panel / noise | Home mean U | Home sample SD | Absolute limit | Decision |
| --- | ---: | ---: | ---: | --- |
| Original / base | +2.232136279 | 1.534323170 | 0.767161585 | Fail |
| Original / alternate | +2.205974065 | 1.571208328 | 0.785604164 | Fail |
| Second / base | +2.638301402 | 2.226943818 | 1.113471909 | Fail |
| Second / alternate | +2.315182358 | 1.884713880 | 0.942356940 | Fail |

All four away cells remain exactly zero, with zero limits and passing guards.
All 32 individual home U values are positive. On second/base home, the
adaptation-minus-actual-cold contrast is +2.910941437 in published units; the
adaptation-minus-continuous contrast is +3.120227113. These are comparisons on
the same previously used histories, not results from an unseen set or a
recurrently trained alternative circuit.

## Complete products, tail and cell classes

The retained arrays include all 8,866 edges: 4,184 eligible home, 3,239 eligible
gamma away, and 1,443 unchanged transmitting away edges. They distinguish
attempted, bounded double and published float32 changes from positive and
negative product areas. Publication occurs once per complete 0.2 ms interval
and once after the entire analytic tail; internal rectifier crossings add no
publication.

The second/base home means have the following attempted decomposition. Each
entry sums the eligible home edges before averaging eight trials. The negative
column is signed, and the net is their sum.

| Phase | Positive product | Negative product | Attempted net |
| --- | ---: | ---: | ---: |
| 100–130 ms | +0.142215255 | −0.141983686 | +0.000231569 |
| 130–300 ms | +4.108379374 | −3.777884588 | +0.330494786 |
| 300–400 ms | +2.908672897 | −1.988051498 | +0.920621399 |
| Complete no-event tail | +1.397925572 | −0.010972176 | +1.386953396 |

The full tail contributes substantial potentiation under the fixed equation.
Removing it would evaluate a different rule. This result does not justify
omitting the tail, changing its publication schedule or fitting a new timescale.
The corresponding mean net by KC class is +1.810190785 gamma,
+0.048623489 alpha-prime/beta-prime and +0.779486874 alpha/beta. These are
learning-operator contributions, not delivered current fractions or proof of
which cell caused a biological association.

Root's [complete-array audit](rate-adaptation-root-array-audit.json) independently
recomputes all eight guards, masks, group sums and double/float accounting. It
checks **2,269,696 positive/negative phase-edge comparisons**: each adapted
nonnegative product magnitude is no larger than its continuous-history
unadapted counterpart. The maximum complete candidate absolute area per edge
is **0.102176986314**, below the unit-gain distance of 0.5 to either bound.
This provides the stated conservative exclusion of hidden prefix excursions.
Actual inclusive electrical/tail bound observations are also separately zero.
All 108 manifest-bound inputs and 22 nested review dependencies were rehashed
unchanged after execution.

## Numerical verification and interpretation

Before execution, 373 synthetic tests passed: 144 writer cases and 229
independent oracle/analytic/calculator comparisons. Tests cover channel and
class mapping, order, population normalization, reset/mask behavior, repeated
exponents, rectifier crossings, full tails, publication/bounds, overflow and
malformed input/output transactions. Review corrected a wrong group/channel
mapping, a channel-order-dependent KC state calculation and unchecked array
allocations before any real candidate evaluation.

The [independent numerical contract](rate-adaptation-reference-contract.md)
uses the raw differential equations and 70-digit infinite-tail quadrature;
the implementation recurrence is not its only oracle. The
[boundary review](rate-adaptation-boundary-review.md) separately validates
immutable inputs, exact selection, exclusive identity and partial-run records.
The [independent complete-edge audit](rate-adaptation-reference-saved-audit-report.md)
also passed. After 20 separate synthetic tests and a source-hash freeze, it
integrated the raw DAN differential equations and used KC impulse
superposition to check all 2,269,696 product values. The maximum unscaled
product error was 4.90e-11; maximum gain-change error was 2.22e-14.
All four phase-end float32 checkpoints matched exactly, with no rounding
ambiguity exception used. This independently confirms a valid scientific
rejection, not a numerical implementation failure.

The repository gate also passed **970 Python tests, 81 frontend tests, Ruff
and the build**. The production API and Training view remain accurate: the
integrated rules still fail qualification, and conditioning is not run. This
offline study adds no production control or purported passing circuit result.
The preceding [actual browser acceptance](task4b-acceptance.md) remains a
separate UI proof.

The frozen decision rejects this fixed adaptation candidate as sufficient on
these trajectories. Preserve the failure; do not tune the onset, timescales,
guard or home mask to make it pass. The remaining gap concerns how the simulator
generates and applies dopamine signals, including local release and downstream
state absent from the current model. The
[bounded localization access check](localization-access-report.md) retrieved no
coordinates and did not establish whether authentication is required. Whole-body
contacts and side labels do not supply local exposure weights. Neither this
missing implementation nor the failed engineering hypothesis refutes learning
in real flies.
