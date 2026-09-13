# Conditioning harness implementation contract — September 13, 2026 UTC

This records implementation decisions before any conditioning measurement.
The immutable [preregistration](conditioning-preregistration.md) and
[scientific addendum](conditioning-prerun-addendum.md) remain authoritative.
The [draft review](conditioning-draft-review.md) found software validation
gaps; its synthetic examples were not conditioning results. The current
mechanism pair still fails qualification. Integrating a harness cannot lift
that gate.

## Scope and fixed interpretation

The production writer implements the exact ordered 1,632-call plan, complete
numerical result validation, acquisition/reversal evaluators, isolated
checkpoint execution, durable accounting and independent artifact validation.
An independent reviewer derives schedule and numerical expectations from the
frozen documents. Root owns this record and final integration verification.
All agents read the narrative docs and wiki, including later additions.
Tests use deterministic fake engines and, where needed, a tiny non-MaleCNS
native fixture. No full-connectome conditioning run is authorized by this
implementation step.

The fixed scientific choices are unchanged: two acquisition families, two
training panels, five acquisition arms, five reversal branches, 32 specified
replays, 616/616/400 stage counts, a 1,640-call hard ceiling and 1,200 wall
seconds. Spare capacity cannot replace missing or failed measurements. The
encoder, gains, channels, home-all/away-gamma eligibility, timings, seeds,
learning-rule parameters and thresholds remain as frozen.

Three sequencing/scoring details are made explicit:

1. Each acquisition family's shared unit probes establish its fixed KC
   partition and specificity gate before any training in that family. A
   failed baseline prevents training; it is recorded as a failed entry gate,
   with downstream stages explicitly not run.
2. The reversal shared unit probes and their specified replays are followed
   by **all 16 acquired-parent probes across both panels before any reversal
   training**. Both parent mappings must pass under the matched 800 ms
   schedule. The old draft interleaved panel-zero training before panel-one
   parent assessment. That order could not enforce the addendum's entry
   requirement for both panels. This ordering clarification changes no call,
   cue, seed, measurement or threshold.
3. New reversal association uses the acquisition-style four-seed **mean**
   response selectivity for its at-least-threefold null comparison. Every
   seed separately needs strictly negative selectivity and actual new-target
   depression. Old-response recovery remains a **per-seed** positive movement,
   reduced distance to the matched unit baseline, and at-least-threefold
   comparison. Exact threefold equality passes only that ratio boundary;
   zero effect still fails the separate strict conditions. The ordinary-swap
   branch itself determines the "dual-channel preference remapping without
   erasure" classification; a failed strict branch cannot substitute for it.

Numerical clarification from synthetic implementation tests, 05:42 UTC:
retain integer cue-window counts and perform response sign, distance and
threefold comparisons before converting to Hz. The common population/time
denominator cancels within each channel; four-seed means likewise permit
comparison of integer sums. For gain comparisons, retain the exact float32
checkpoint values and preferred-set sizes and use exact sums/cross-products
or rational arithmetic. Valid gains in this fixed range are integer multiples
of `2^-24`. Conversion to displayed means must not create a false failure or
pass at the frozen ratio boundary. No epsilon, threshold or probe schedule
is introduced. Tests must cover exact equality and adjacent representable
failures, including unequal preferred-set sizes.

The ordinary-swap remapping classification has a sufficient, explicit
no-old-recovery case: every old response remains below its matched unit
baseline and no greater than its parent response; each old-preferred gain
mean remains below one and no greater than its parent mean. The ordinary
branch must also flip preference and actually depress its new target in
both channels/panels and every response seed. Individual old edges may
redistribute while their mean stays unchanged or decreases. Mixed or partial
recovery must be reported as such; it cannot justify a stronger erasure claim.

## Identity, execution and evidence

Validate the exact independently recomputed original/second mechanism pair
before constructing an engine or compiling/loading the native library. Bind
the pair to the same complete scientific identity and current source, native,
data, graph, selector and document hashes. Recompute eligibility from the
locked data. A stored pass flag, a missing original or second panel, a mixed
rule pair, or stale identity cannot open the gate.

Freeze cue vectors and actual encoded-rate hashes, the complete ordered plan,
schema and source identities into a new experiment identity. Refuse an
existing identity; do not overwrite or resume. Persist an attempt before
invocation and its outcome after invocation, including exceptions and
malformed results. Check cancellation, source stability and time/call limits
at the declared boundaries. Partial matrices cannot produce a scientific
pass. Record explicit blocked downstream stages after a failed upstream
gate.

Canonical training state, saved checkpoints and disposable probe/replay
state must own separate buffers. Replays restore the exact named pre-call
checkpoint, including the pre-cue/post-cue relationship of an acquisition
cue/blank pair, and discard their state afterward. Probes and frozen arms
preserve gain bytes. Every numerical output is required with its expected
type, shape and finite domain before replay comparison; wall time is the
only excluded numerical field. Empty or matching malformed outputs fail.

Retain electrical and analytic-tail observations separately, including
inclusive bound contacts and complete gain snapshots. Independently check
eligible bounds, masked-edge bytes, frozen/probe bytes, response schedules,
seed identities, fixed KC partitions and ancestry before scientific scoring.
The artifact reader recomputes completeness and criteria from retained
evidence; the API and Training view distinguish stored state from validated
evidence. A fabricated `passed` boolean must never become a visible validated
conditioning pass.

## Acceptance

Generalized tests cover every plan-field family, missing/extra/duplicate
identities, all numerical result families, response/gain and channel/seed
matrices, exact ratio boundaries, parent/probe/replay isolation, electrical
and tail bounds, all exit states, budgets and durable attempt accounting.
Valid acquisition and strict-reversal fixtures accompany negative cases.
The actual failed mechanism pair must be rejected before an engine factory
is called. These are software results, not learned fly behavior.

After independent review, run focused tests and `make verify`. Rebuild the
frontend and check affected loading, empty, error and completed states on the
explicit read-only QA server. Recheck protected historical artifacts and
the active model pointer before a local commit. No push or model promotion.
