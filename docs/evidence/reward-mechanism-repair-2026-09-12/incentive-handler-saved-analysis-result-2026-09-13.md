# Independent comparison of the saved Handler model and workbook

September 13, 2026. **The saved-array and data-analysis audit passes. The
literal normalized reporter contrast reproduces the reported strong
descriptive association, while the primary six-condition model comparison
remains incomplete.** No model was rerun, no parameter was fitted and no
MaleCNS learning result follows.

The single reviewed analysis read all six cases from source identity
`incentive-handler-source-9c5800e30fdae747b49a`, verified the saved completion,
case hashes, source clock/stimuli and all 22 analysis input bindings, and
reconstructed the source summary within the frozen absolute 1e-12 tolerance.
All original inputs and the frozen analyzer/tests/plan remained unchanged.
The child completed in 0.173436 s; the external parent measured 0.204362 s,
reaped exit zero and recorded no error. The cap was 30 s, with no retry.
[Complete saved analysis](incentive-handler-saved-analysis-2026-09-13/analysis.json)
and [external execution receipt](incentive-handler-saved-analysis-2026-09-13-execution/parent-result.json).

The literal model uses `-dR1` on `[-7,1)` and `dR2` on `[ISI,ISI+4)`, followed
by separate six-condition min–max normalization. Its descriptive Pearson
correlations are:

| Experimental comparator | Pearson r |
| --- | ---: |
| Literal-driver reporter contrast, including its longer ER window | 0.983739 |
| Primary workbook's rounded reporter contrast | 0.983372 |
| Separate measured MBON pre/post condition means | 0.925308 |

These are distinct observables. The authors used these conditions to select
timing constants; no acceptance threshold, held-out validation or statistical
significance claim was added. A high contrast correlation does not establish
agreement of individual reporter pathways. For example, at −6 s both model
branches normalize to 1, cancelling to zero, whereas the literal experimental
cAMP branch is 0 and ER is about 0.061. The saved arrays preserve the full
branch means, ranges, preparation values and SEMs.

The primary-window model means use only actual recorded samples in closed
ER `[0,1]` and cAMP `[ISI,ISI+4]` intervals. All ER windows have 67 samples.
The first five cAMP windows have 267 each. At +6 s only 134 samples,
6.005–8 s, are present; the required window ends at 10 s. Its partial raw
mean remains visible and explicitly incomplete. **No six-condition
primary-model normalized contrast or correlation was computed, and the
five complete cases were not renormalized.** Their raw model/data means are
reported descriptively without claiming equivalent units.

The independent workbook parser retained all 78 primary reporter means
(41 cAMP samples or 11 ER samples per preparation), all six conditions and
all 31 direct MBON measurements. It separately preserved the active driver's
71-sample experimental ER window and the final sheet's rounded normalization
primitives. It did not interpolate, pad data, execute formulas or pair the
six cAMP preparations with the seven ER preparations.

Internal weights also remain separate from reported weights and reporter
proxies. At coincidence and +0.5 s, final internal W is −32.485987 and
−9.799187, while recorded w is zero. At −0.6 s, signed internal weight change
is −0.432730 while the reporter-proxy sum is +0.250799. Neither a normalized
contrast nor the rectified plot is an oracle for the actual signed update.

The reader was frozen after 44 generalized tests and Ruff passed, then root
independently reran those tests before dispatch. Its numerical summary check
is independent of the source helper; it does not duplicate the separate
state-recurrence audit. Biological reporter labels, γ4 scope, source protocol
durations, abstract input units and finite recording limits remain explicit.
This establishes the named source/data comparison, not receptor kinetics,
a new production mechanism or resolution of the failed learning guards.
