# Independent saved-history numerical audit: valid rejection

September 13, 2026 UTC. Agent `dopamine_sources` independently verified the
completed fixed rate-adaptation calculation. **The numerical audit passes;
the candidate fails all four home stability cells.** This is a valid failure
of the declared engineering hypothesis on the recorded trajectories. It is
not a failure of learning in real flies and does not qualify a new circuit.

The audit completed in 8.6032 seconds with zero circuit calls, no writer-module
import, no changed inputs and no excluded trials. Its
[complete numerical result](rate-adaptation-reference-saved-audit-5165a926/summary.json)
retains all 32 rows and all eight guard cells. The
[complete output inventory and product-domination check](rate-adaptation-reference-saved-audit-5165a926/output-hash-inventory-and-domination.json)
binds all 98 source-screen files and the 34 initially generated independent
audit files, including the independently calculated product arrays.

## Independence and fixed numerical contract

The screen identity is `rate-adaptation-shadow-5165a92674683bf2b872`, manifest
SHA256 `5165a92674683bf2b872753148af74e3adf038ca7a95c64735dcda8e29e5ee46`.
Root froze and executed that identity once before authorizing this read-only
audit. The independent numerical method and its 20 synthetic tests were
[hashed before this agent inspected candidate outcomes](rate-adaptation-reference-superposition-freeze-2026-09-13.json).
The earlier [numerical contract](rate-adaptation-reference-contract.md), its
229 synthetic comparisons and final calculator review remain preserved.
No tolerance or scientific constant was changed after observing a result.

The reference solves the raw DAN differential equations with DOP853, using
the actual population-mean event impulses, rather than the calculator's
analytic interval recurrence. Integration uses `rtol=2e-13`, `atol=2e-15`
and a maximum 0.025 ms step inside each 0.2 ms electrical interval. It tracks
three weighted integrals: eligibility times `exp(-r*t)`, and rectified DAN
contrast times each of `exp(-e*t)` and `exp(-r*t)`. Independent 70-digit
quadrature supplies the entire infinite tail, without a finite truncation.

Each actual KC impulse then contributes its exponential impulse response to
those integrals. Linear superposition gives every KC/channel positive and
negative product separately. Mapping the resulting arrays through the saved
anatomical edge map and eligibility mask covers **32 × 8,866 × 4 × 2 =
2,269,696 phase-edge product values**. This uses neither the writer's KC-state
recurrence nor its sign-crossing integration formulas.

The frozen comparison tolerances are absolute/relative `2e-10/2e-10` for
unscaled product integrals, `2e-11/2e-10` for states, and `2e-12/2e-10` for
gain changes, with relative gain error measured against the change rather
than the unit baseline. Observed maxima were:

| Comparison | Maximum absolute error |
| --- | ---: |
| Unscaled positive or negative phase-edge product | 4.9015902448e-11 |
| Attempted gain change | 2.2188847981e-14 |
| KC/DAN state at onset or electrical endpoint | 5.1141313406e-12 |

All four phase-end published checkpoints, including the electrical endpoint
and complete tail, matched the independently reconstructed float32 gains
exactly. There were **zero rounding-midpoint ambiguities**. The predeclared
one-ULP exception was therefore unused. This audit does not claim that the
saved artifacts contain a gain checkpoint for every individual electrical
step; that publication policy is covered by the separately reviewed source
and synthetic boundary tests.

## Complete selection, masks, states and bounds

The audit independently generated the exact expected game, noise and seed
matrix and matched every manifest row, attempt, completion and saved output.
It checked all 108 manifest-bound input files before and after computation,
all 32 output archives, and unchanged source manifest and summary bytes.
Every fine raster has its required 2,000 × 4,774 int32 binary shape.

The sample map retains 4,184 home edges and 4,682 away edges. All home edges
remain eligible; 3,239 gamma away edges are eligible and 1,443 transmitting
away edges remain unchanged. DAN normalization uses both PPL101 cells and
all 22 PAM12 cells. Group-to-channel mapping, excluded-edge zero updates,
onset unit gains, KC/DAN onset and endpoint states, all group sums, attempted
and applied changes, and final double/published gain accounting agree.

The largest complete candidate absolute area per edge is 0.10217698631370263,
below the 0.5 distance from initial unit gain to either bound. Both independently
computed and recorded positive/negative product magnitudes are individually
no greater than the continuous-history unadapted comparator; the largest
product-minus-comparator difference is zero. Its maximum complete raw area is
0.15711364198053562. This matches the source-independent domination argument:
nonnegative baseline implies `Dplus <= R_D`, and convolution with the positive
eligibility kernel gives `E_Dplus <= E_Draw` for the same histories.

Summing both nonnegative product magnitudes bounds the absolute gain excursion
over every prefix, so the complete-area bound excludes hidden interior
clipping. Actual recorded inclusive electrical and tail bound observations
are also separately zero. The tail is fully included in both calculations.
No continuous-clamp gain ODE was substituted for the specified once-per-step
and once-per-complete-tail publication policy.

## All eight unchanged guards

Each cell contains eight cues. U is the sum of final eligible published gains
minus one. The exact decision remains `abs(mean U) <= 0.5 * sample SD`.
The table is rounded for display only; full-precision values and decisions
for adaptation, actual cold and continuous-history comparators are retained
in the audit JSON and match the source summary exactly.

| Panel | Noise | Channel | Mean U | Sample SD | Absolute limit | Decision |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Original | Base | Home | +2.232136279 | 1.534323170 | 0.767161585 | Fail |
| Original | Base | Away | 0 | 0 | 0 | Pass |
| Original | Alternate | Home | +2.205974065 | 1.571208328 | 0.785604164 | Fail |
| Original | Alternate | Away | 0 | 0 | 0 | Pass |
| Second | Base | Home | +2.638301402 | 2.226943818 | 1.113471909 | Fail |
| Second | Base | Away | 0 | 0 | 0 | Pass |
| Second | Alternate | Home | +2.315182358 | 1.884713880 | 0.942356940 | Fail |
| Second | Alternate | Away | 0 | 0 | 0 | Pass |

This result rejects the fixed rectified-rate adaptation hypothesis as a
sufficient repair on these histories. It does not identify a causal upstream
cell, measure local dopamine exposure, reproduce natural PAM-γ3 suppression,
or evaluate a recurrent circuit transmitting the alternative gains.
Conditioning and reversal remain unrun. Preserve the failure and its full
tail; do not tune the existing thresholds, onset, timescales or home mask to
remove it.

## Reproduction and preserved source hashes

Run the read-only audit into a new output directory with
`rate_adaptation_reference_saved_audit.py --screen <original-screen-directory>
--output <new-audit-directory>`. This is an artifact audit, not permission to
restart the frozen candidate identity or launch a circuit call.

| File | SHA256 |
| --- | --- |
| `rate_adaptation_reference_superposition.py` | `f8ab50c7bb441702a6db5961b520468783c07fba8fcb2c3e199f828388e4f342` |
| `rate_adaptation_reference_superposition_tests.py` | `bb8acd87b5f4456c07f5447f31a29ad944b9a306213c16cbd8434387e1935d87` |
| `rate_adaptation_reference_oracle.py` | `2e09acf2fe7b1917eab406d99d77d591643065d43e6bf1e59d72e733d0bca87d` |
| `rate_adaptation_reference_saved_audit.py` | `96f6aada763349384612ab378f29a4a12165d373e2990c76f1fbb4b22cdcf375` |
| Reviewed candidate `rate_adaptation_shadow.py` | `bad6425c1b54b0f48b04b8238be3e426372d3a8a128838bb2260f9d93b5652e8` |

All work by this audit agent remains output-only. The root agent owns the
repository-wide quality gate, evidence copying and local commit. No production
source, active model pointer, historical input or imported Microduck file was
modified by this audit.
