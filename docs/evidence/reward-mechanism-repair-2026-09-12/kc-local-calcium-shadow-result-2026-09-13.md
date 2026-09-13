# KC-local calcium mapping: independently confirmed rejection

The single fixed-history candidate `kc-local-shadow-6734494c82c54702ead0`
completed all 32 histories and is **rejected**. All four home guard cells fail;
all four away cells remain exactly unchanged. There are no bound contacts or
invalid local states. No live candidate, conditioning or reversal was run.

| Home guard cell | Mean gain-sum change | Half-SD absolute limit | Result |
| --- | ---: | ---: | --- |
| Original panel / base | −0.185671605170 | 0.120006941674 | Fail |
| Original panel / alternate | −0.139918297529 | 0.112285236045 | Fail |
| Second panel / base | −0.360410362482 | 0.279657483200 | Fail |
| Second panel / alternate | −0.155674725771 | 0.087337869724 | Fail |

The [frozen plan](kc-local-shadow-frozen-2026-09-13.json), SHA256
`f6fc6a21e4ef5d51cd2d3454bbe2c53ebd8715c7c153b1cba3f9f39e4de27377`,
binds 106 files / 219,720,936 bytes: contracts, implementation and independent
auditor, external fit, contact map, primary source and all original captures.
The producer completed once in 16.025697 seconds under its 1,200-second
external watchdog. [Producer results](kc-local-shadow-6734494c82c54702ead0/summary.json),
[parent execution](kc-local-shadow-execution-2026-09-13/execution.json).

The [independent audit](kc-local-shadow-independent-audit-2026-09-13/audit.json)
completed once in 3.303564 seconds under its separate 120-second watchdog.
It reconstructed all 12 source frames, 13 C/L/a/I snapshots and held ratios
for all 4,064 KCs in every history, using original source functions and
independently grouped event times. The direct event-pair integral reproduced
all 8,866 final and electrical double gain values per history; maximum error
was 9.33e-15. Both complete float32 endpoint vectors match bit-for-bit in
every row. There are zero rounding ambiguities. Independent integer trial
totals reproduce every guard classification. This establishes the numerical
rejection, not a learned association.

The [declared candidate](kc-local-calcium-candidate-contract-2026-09-13.md)
maps completed-frame spike counts into the primary 30 Hz local-state model,
then uses held L/C to weight actual KC events before both existing bridge
filters. The [bounded external fit and review](kc-local-calcium-preparation-root-2026-09-13.md)
remain separate evidence: source-model reproduction passed, but the WT
standard-error-weighted RMS residual is 2.12006. The population fit does not
identify the chosen spike scale, calcium-to-susceptibility mapping, incoming
contact normalization or extrapolation from gamma physiology to all KCs.
Those engineering choices were explicit before this outcome.

## Cell-specific observations

The [complete cell table](kc-local-shadow-cell-summary-2026-09-13.csv) joins
every retained KC to its exact body ID, graph index, type, instance and
family. It reports all 32 histories' raw/weighted event totals, minimum
recorded susceptibility, eligible home/away edge counts and original/candidate
home gain sums. These are descriptive summaries of the saved arrays.
The [complete row/type summary](kc-local-shadow-descriptive-attribution-2026-09-13.json)
also retains per-phase positive and negative bridge areas.

| KC family | Cells | Raw events | Attenuated event mass | Original home gain sum | Candidate home gain sum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Gamma | 1,557 | 63,506 | 1,473.951080 | −2.614707 | −4.571808 |
| Alpha-prime/beta-prime | 695 | 3,776 | 23.764583 | −0.155239 | −0.176833 |
| Alpha/beta | 1,810 | 20,262 | 303.585703 | −1.323059 | −1.984758 |
| Other | 2 | 73 | 0.885735 | 0 | 0 |

All 32 home trial sums are more negative than their original fixed-history
bridge values. Across histories the total changes from −4.093005002 to
−6.733399928, although event mass falls from 87,617 to 85,814.812899.
Attenuating an impulse can reduce both potentiating and depressing pair
contributions; it does not guarantee a smaller signed drift. This was an
explicit pre-outcome limitation of the mathematical contract. The table does
not establish receptor localization or prove which cells causally drive a
live recurrent circuit's failure.

## Consequence for the repair

Keep this mapping rejected. Do not rescue it by selecting another spike scale,
ratio fallback, fitted time constant, onset, bound or acceptance threshold
against these outcomes. A source-supported missing mechanism can be real
biology while this particular transfer to the simulator fails. The next
mechanistic decision must address that distinction before selecting another
candidate; repeating broad source collection or adding tests alone will not
establish learning.

The production rule, accepted electrical gains, all 4,184 eligible home edges,
3,239 eligible away edges and 1,443 other transmitting away edges are unchanged.
No alternative gains fed back into these recorded neurons. Both complete live
qualification panels and the frozen controlled acquisition/reversal study
remain required for the full repair goal.

Before these histories, 566 distinct synthetic preparation tests passed.
The standard gate also passed: 4,055 Python tests, 85 frontend tests, Ruff and
Vite, with two existing Python warnings. Source files, artifacts, numerical
checks and originals are preserved; canonical copy verification is recorded
separately. Internal evidence work changes no API or visible Training behavior,
and no new browser verification is claimed.
