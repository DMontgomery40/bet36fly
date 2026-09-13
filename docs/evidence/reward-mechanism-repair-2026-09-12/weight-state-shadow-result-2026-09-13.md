# Fixed gain-dependent plasticity still fails the untaught control

September 13, 2026 UTC. **Reject this specified fixed-history hypothesis.**
The new gain-dependent law leaves the second panel's home/base guard failing:
mean −0.268754929304, permitted absolute mean 0.235695145300. The independent
audit reproduces the result and passes every prescribed numerical comparison.
No parameter, mask, onset or guard was changed after viewing outcomes. This
law is not a production rule and does not qualify conditioning or reversal.

The [source decision](dopamine-weight-state-decision-2026-09-13.md) made the
distance-to-bound factors an explicit engineering assumption. The rule retains
the existing 100/500 ms filters, eta 0.0005, cold 100 ms onset, actual mean
signals from two PPL101 and 22 PAM12 cells, and the complete zero-input tail:

```text
P = 0.96 E_D R_K, N = 0.96 E_K R_D
g' = 0.0005 [P (1.5-g)/0.5 - N (g-0.5)/0.5].
```

All 4,184 home edges and 3,239 supported gamma away edges remained eligible;
the other 1,443 away edges stayed exactly unchanged. Every trial started from
unit gains. The new gain dependence was integrated continuously inside each
interval, with separate signed weighted areas. No alternative gain affected
the recorded spikes. This does not test recurrent effects of a new circuit.

## Complete result, with unchanged criteria

Identity **`weight-state-shadow-de1ab218973eb3ecd3d3`** was frozen before
execution. It binds 60 source files totaling 9,967,809 bytes, including all
32 original fine histories and the independent audit code/tests. The exact
[frozen plan](weight-state-shadow-frozen-2026-09-13.json) SHA256 is
`95f0b95f0c64642348ed56e7b87135c97b4891e42e2091abb70bdc4c88ea80c0`.
Read the [preregistration](weight-state-shadow-preregistration-2026-09-13.md)
for complete timing, numerical, selection and failure semantics.

| Panel / noise | Home mean | Home sample SD | Absolute-mean limit | Conditional result |
| --- | ---: | ---: | ---: | --- |
| Original / base | −0.103653140366 | 0.254545398506 | 0.127272699253 | All pass |
| Original / alternate | −0.061324380338 | 0.260305928427 | 0.130152964214 | All pass |
| Second / base | **−0.268754929304** | 0.471390290601 | **0.235695145300** | **All fail** |
| Second / alternate | −0.074663437903 | 0.199385210368 | 0.099692605184 | All pass |

All four away cells have exactly zero mean and variance and pass. The guard
remains `abs(mean) <= 0.5 * sample_SD`; exact float32 integer totals and
rational uncertainty-box comparisons establish these classifications without
rounding a mean/SD inequality. The classifications remain conditional on the
frozen 1e-11 gain allowance. There are **zero actual or possible inclusive
bound observations**, and all 7,740 numerically ambiguous
publications are retained. Those ambiguities do not change this conservative
classification; they are not called exact publication proofs.

For comparison, the original additive bridge on these same second/base
histories had mean −0.272640034556 and limit 0.240845235423. The small change
in mean under gain dependence does not meet the new trial distribution's
unchanged criterion. The other seven guard cells remain passing. No teaching,
cumulative, replay or conditioning result is newly inferred from this screen.

## Execution and independent evidence

The single execution completed exactly 32 attempted and durably completed
helper calls in **82.316621 seconds**, inside the 1,200-second cap. No retry,
resume, network request, native call or circuit call occurred. The exclusive
68-file [result directory](weight-state-shadow-de1ab218973eb3ecd3d3/summary.json)
contains all 32 full arrays, row details, ordered journal, identity, computed
summary and hash-bound completion. It totals 5,611,498 bytes and was copied
without moving the original files. The summary SHA256 is
`75f3b09006837980743006680817b445cc591f92fafc840cad7cc58756cc0037`.

The separately dispatched [independent audit](weight-state-shadow-de1ab218973eb3ecd3d3-independent-audit/summary.json)
completed all 32 rows and **128 fixed scalar references / 1,024 comparisons**
in 22.440411 seconds through summary persistence. It verified all original
and result bindings, all eight exact guard cells, every saved edge's storage,
mask, phase accounting, publication counts and endpoint implications. Median
edges in the four eligible anatomical groups were selected before outcomes:
indices 4321, 2436, 5563 and 4295, unchanged across every history.

Direct event-superposition/DOP853 integration differs from the efficient
helper by at most **8.99e-15 in final gain**, **7.66e-15 in electrical gain**,
and **7.29e-16 in a weighted area**. All are below the frozen 1e-11/2e-11
absolute allowances. The audit uses no simulator or candidate imports.
Separate synthetic tests compare the mathematics with a 70-digit
integrating-factor reference. These establish numerical agreement, not
calibrated fly receptor physiology.

Every intermediate gain is not saved. Accordingly the audit independently
checks complete stored counter domains, sums, masks and endpoint constraints;
it does not reconstruct every transient bound or rounding observation on
every edge. The separately tested wrapper records those observations. Its
1,501 eligible-edge publications per trial and complete tail remain explicit.

Preparation passed **794 distinct synthetic cases**: 539 helper/reference/
guard/runner cases plus 255 independent saved-artifact audit cases. The
[prerun review](weight-state-shadow-prerun-review-2026-09-13.json) records source
identities, exact runtime versions, independent reviews and tests. Root also
ran `make verify`: 4,055 Python tests, 85 frontend tests, Ruff and Vite passed.
Two existing Python warnings remain. A fresh comparison found all 791
protected files and their complete inventory unchanged across verification
and the shadow/audit.
This current pass does not erase the earlier documented regenerated server
bytecode cache or QA-startup incident.

## Consequence for the repair

Stop this specified gain-dependent hypothesis at its predefined rejection
screen. Do not rescue it by tuning times, learning rate, bounds, onset or
mask against these outcomes. The production bridge, failed qualification pair,
fixed readout, accepted drive gains, model pointer and historical results
remain unchanged. The current Training/API state remains accurate; this
offline calculation creates no new qualifying circuit artifact or UI claim.

Continue source-grounded work on the connection between DAN spikes, local
dopamine and intracellular plasticity. This result does not prove that a
receptor mechanism is the cause, that gain dependence is biologically absent,
or that recurrent learning cannot work. Scientific qualification and measured
acquisition/reversal are still required before the active repair goal is done.
