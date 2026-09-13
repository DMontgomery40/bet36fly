# Finite Aso DA/NO source protocols — September 13, 2026

**Completed legacy checkpoint; MaleCNS learning remains unqualified.** One
28-case source-equation calculation and its independent audit completed under
identity `aso-source-protocol-e54b736d2730d5bc67a5`. This establishes numerical
agreement under the declared source interpretation, not reproduced behavioral
performance or repaired native learning. The [current project direction](../../PROJECT_DIRECTION.md)
and [natural sensory handoff](../../NATURAL_SENSORY_HANDOFF.md) supersede further
molecular transfers. The goal was observed paused during closeout; this record
preserves already-completed work and does not start a new assay.

## Source and frozen interpretation

The [frozen plan](aso-source-protocol-plan-2026-09-13.json) contains seven
protocols crossed with both pathways, dopamine only, nitric oxide only and
neither: naïve, one 10-second pairing, one 60-second pairing, three 60-second
pairings, reversal, odor-only follow-up and DAN-only follow-up. Four representative
KC classes retain separate states: A-only, B-only, shared and neither. They are
analytical classes, not sampled MaleCNS neurons or a fitted population.

The source is [Aso et al. 2019](https://elifesciences.org/articles/49257), with its
[2020 correction](https://doi.org/10.7554/eLife.64094). The official article API
version 3 and [figure PDF](aso-source-protocol-primary-2026-09-13/elife-49257-figures-v3.pdf)
were retrieved and inspected on September 13, 2026. The [API retrieval](aso-source-protocol-primary-2026-09-13/article-api-retrieval.json)
and [PDF retrieval](aso-source-protocol-primary-2026-09-13/figures-pdf-retrieval.json)
retain URLs and hashes. The prior full article XML and correction remain in
the [component source contract](aso-da-no-component-contract-2026-09-13.md).

Figure 7 prints a duplicated “20” on its lower time axis. Before execution,
the source reviewer, independent reviewer and root inspected the actual figure;
the [axis audit](aso-figure7-axis-audit-delivered-arrivals-2026-09-13.json)
records text positions. The plan explicitly uses a uniform minute grid, placing
Tests 3 and 4 at 21–22 and 31–32 minutes. This is a declared interpretation of
a source error, not a silently exact transcription. The
[scientific protocol review](aso-da-no-finite-source-protocol-dopamine-sources-2026-09-13.md)
and [independent design](aso-da-no-protocol-independent-design-delivered-arrivals-2026-09-13.md)
preserve the other caption and timing ambiguities.

DAN activation is a continuous experimental-activity envelope over each bout,
not literal LED pulses or somatic spikes. Paper rates and 30/600-second
expression times are unchanged. States begin at zero once per case and persist
through all intervals; no minute-to-millisecond compression or fitted spike
conversion was introduced. Tests sample instantaneous state at start, start of
the last 30 seconds, and end. These are not window averages or experimental
performance indices. The long spaced-training and 24-hour regimes were excluded
before execution. The neither-pathway condition is an additional analytical
control, not a claimed biological experiment.

## What the saved values show

Weights are normalized source-model synaptic efficacy, `(1-D)(1+N)`. The
[768-row observation table](aso-source-protocol-observations-2026-09-13.csv)
retains every declared test sample, KC class and state. All naïve and
neither-pathway weights remain exactly 1.

At the Figure 6 test endpoint, A-only weights after one 10-second pairing are
0.542635206 with both pathways, 0.488377471 with dopamine only and 1.111097949
with NO only. After three 60-second pairings they are 0.000004106,
0.000002500 and 1.642569115 respectively. B-only remains 1. These source-model
values show opposing pathway effects; they do not measure behavioral valence.

For reversal, the A-only minus B-only weight difference is:

| Pathways | Test 2 end, 960 s | Test 3 end, 1320 s | Test 4 end, 1920 s |
| --- | ---: | ---: | ---: |
| Both | −0.999995873 | +0.378817698 | +0.905125525 |
| Dopamine only | −0.999997488 | +0.215273547 | +0.541573668 |
| NO only | +0.642691834 | +0.501370282 | +0.028595945 |
| Neither | 0 | 0 | 0 |

The NO-only ordering **has not reversed** by the final sample. No later sample
or changed parameter was added to obtain a reversal.

Odor-only follow-up holds latent induction states but permits expression to
continue. Its NO-only A weight rises from 1.642691834 at Test 2 to 1.883059376
at Test 4. It would be false to summarize this control as unchanged weights.
For DAN-only follow-up, NO-only A weight is 1.642691834, 1.727924969 and
1.671287779 at Tests 2, 3 and 4: delayed expression initially rises before
falling, and the last value remains above Test 2. This is not immediate erasure.
With both pathways, the DAN-only A weight reaches 0.905129652 at Test 4,
compared with 0.541576180 for dopamine alone. The
[saved scientific review](aso-source-protocol-saved-interpretation-dopamine-sources-2026-09-13.json)
checks these limited claims. Agreement with the equations does not reproduce
experimental statistical significance.

## Implementation and verification

The [runner](run_aso_source_protocol.py) validates the exact frozen plan bytes
and their parsed content before creating outputs. Its stimulus boundaries
define integration; observations cannot perturb subsequent state. The
[independent checker](audit_aso_source_protocol.py) reconstructs schedules and
trajectories with the separate high-precision reference rather than trusting
producer flags or later initial states. Both retain partial evidence on failure
and reject reused output directories.

The [parent receipt](aso-source-protocol-e54b736d2730d5bc67a5-parent.json)
records one producer execution (0.137 seconds, 30-second cap) and one independent
execution (0.334 seconds, 60-second cap), both exit 0 and reaped. All 15 bound
inputs remained unchanged. The [producer status](aso-source-protocol-e54b736d2730d5bc67a5/status.json)
and [audit](aso-source-protocol-e54b736d2730d5bc67a5-audit/audit.json)
both completed 28/28. All 15,600 saved values were checked, including exact
times, flags and indices. Maximum numerical absolute error was
`6.661338147750939e-16`, within unchanged absolute/relative tolerances of
`1e-12`. All 28 producer and 28 independent reference files are retained.

The new focused suites passed **87 runner tests and 43 checker tests**. Coverage
includes timing and state continuity, all KC classes and pathway nulls, invalid
units/domains, malformed archives, incomplete or forged status, input tampering,
timeouts and failed persistence. A pre-execution regression exposed mismatched
parsed-plan content despite a valid source path; the fix and red/green evidence
are retained. These synthetic tests are distinct from the 28 actual cases.
[Runner test log](aso-source-protocol-canonical-writer-tests-2026-09-13.txt),
[checker test log](aso-source-protocol-canonical-checker-tests-2026-09-13.txt).

`PYTHONDONTWRITEBYTECODE=1 make verify` passed **4,055 Python tests, Ruff,
103 frontend tests and the Vite build**. The [complete log](aso-source-protocol-make-verify-2026-09-13.log)
retains two existing Python warnings. The
[protected-byte check](aso-source-protocol-protected-2026-09-13.json)
found no changes in its 760-file baseline (4,351,175,626 bytes); it is not a
claim that the concurrent documentation worktree was unchanged. API/UI review
was code and saved-contract inspection, not a fresh browser run. Existing
qualification displays remain accurate; no new source or sensory workflow was
added to the application.

## Reading, preservation and continuation

The agents' prior full narrative-reading chains and this phase's additions are
retained in the preparation/review receipts. New natural-sensory direction
documents appeared concurrently after preparation. The independent checker's
preparation receipt was sealed after execution while reconciling those additions;
it is explicitly late, not backdated evidence. Its code and 43 tests were already
checked before dispatch. Final reading receipts record the later prose and
direction changes separately. The [closeout inventory](aso-source-protocol-closeout-2026-09-13.json)
binds the final receipts and copied files.

Source artifacts were copied into this evidence directory with originals
retained. The earlier Microduck wiki snapshot remains intact. The native rule,
accepted legacy gains, model pointer and masks were not changed: all 4,184 home
edges remain eligible; the away mask permits 3,239 gamma edges while 1,443 other
edges transmit. No NO pathway has been assigned to PAM12 by analogy. Legacy
SCI-001 remains HOLD; native conditioning and reversal remain unrun.

No further DA/NO transfer is queued. The next project milestone is the source
and cell contract for the natural sensory assay described in the current
handoff. A plasticity-off sensory response does not depend on passing the old
learning guard. This checkpoint does not establish food sensing, in-circuit
choice, associative learning or improved sports prediction.
