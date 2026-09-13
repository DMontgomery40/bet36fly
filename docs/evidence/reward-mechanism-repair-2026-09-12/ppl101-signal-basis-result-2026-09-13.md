# Individual PPL101 signals: routing remains unresolved

September 13, 2026 UTC. The single frozen offline analysis
`ppl101-signal-basis-2c1e0eaa2d5834d76d56` completed all 32 saved untaught
histories in 1.780837 seconds. It made zero circuit calls and zero network
requests. **The result does not establish a passing local routing scheme or
repair the learning mechanism.**

The [preregistration](ppl101-signal-basis-preregistration-2026-09-13.md)
asks whether any constant, nonnegative, normalized coupling of the two actual
PPL101 signals could be excluded before retrieving contact geometry. The
[frozen identity](ppl101-signal-basis-frozen-2026-09-13.json) binds 73 source,
test, sample-map and capture files. Every binding matched before and after
the analysis. The current bridge, its cold 100 ms onset, all 4,184 home
edges and all scientific guard thresholds were preserved.

Both PPL101 bodies, 11327 and 11900, have different sampled event histories
in every trial: 15–51 differing 0.2 ms bins per 400 ms history. The analysis
integrates each cell's contribution separately through the full no-new-event
tail. Their mean reproduces all 32 original float32 home gain vectors
byte for byte. The largest discrepancy from the saved canonical positive,
negative and signed integrals is 9.714452×10⁻¹⁶, below the fixed absolute
1×10⁻¹⁰ allowance. No routing coefficient was selected from these outcomes.

The maximum individual positive-plus-absolute-negative area is 0.096474297
per edge. This satisfies the preregistered conditional numerical test for
remaining inside the gain bounds, including double accumulation and float32
publication margins. It is not a formal interval-arithmetic proof of every
possible numerical implementation.

The necessary bounds deliberately allow a different convex combination on
every edge **and every trial**, a larger class than a fixed anatomical map.
Their four results are:

| Panel / noise | Possible mean interval | Absolute-mean lower bound | Half-SD upper bound | Entire class excluded? |
| --- | ---: | ---: | ---: | --- |
| Original / base | −0.176576 to −0.031106 | 0.031106 | 0.170241 | No |
| Original / alternate | −0.198135 to +0.076158 | 0 | 0.196189 | No |
| Second / base | −0.403151 to −0.142129 | 0.142129 | 0.318742 | No |
| Second / alternate | −0.165642 to +0.017329 | 0 | 0.147839 | No |

All four tests are **inconclusive**. They neither construct a common passing
map nor prove that anatomy supplies one. Coordinates, contact counts and
whole-neuron spikes still do not determine local dopamine release or receptor
activation. Recurrent trajectories were not recomputed under alternative
couplings. The actual bridge's failed second/base result remains unchanged.

Before this evaluation, 102 synthetic mathematics tests passed, including
23 independent cases using 70-digit improper quadrature, exact rational
variance at every box vertex, storage precision and bound-contact examples.
The [independent review](ppl101-signal-basis-independent-math-review-2026-09-13.json)
records the corrected tolerance and numerical margins. The complete
[results and per-trial arrays](ppl101-signal-basis-2c1e0eaa2d5834d76d56/summary.json)
and [copy manifest](ppl101-signal-basis-copy-manifest-2026-09-13.json) preserve
the output. Originals were copied, not moved. Historical capture inputs remain
at the protected original locations recorded in the frozen bindings; this
archive is not a claim that a clean checkout contains those large inputs.

The separate [receptor-state review](dopamine-receptor-state-decision-2026-09-13.md)
identifies a documented distinction between coincidence and event-order
signaling. Its proposed state topology has no calibrated rates or input
conversions for these task cell families and has not been instantiated.
Neither source review nor this routing analysis qualifies conditioning.
