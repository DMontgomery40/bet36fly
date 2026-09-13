# Retaining earlier signal history did not repair the drift

Recorded September 12, 2026 UTC; this account added September 13 UTC.
**The predeclared onset-history hypothesis was rejected.** On unchanged recorded
spikes, retaining filter history from 0 ms made second-panel home/base gain change
more negative: −0.272640034556 to −0.481925711036. It worsened 30 of 32 home trials
and failed every home panel/noise guard. Conditioning and reversal remain unrun.

## What was held fixed and what was compared

Capture `onset-history-capture-4343c21535c43f42` retained the actual cold bridge
trajectories. The [investigation](onset-history-investigation-preregistration.md)
and [capture identity](onset-capture-preregistration.json) were frozen before
execution. Gain writes still began at 100 ms, with the same 100/500 ms filters,
learning rate, tail, cells, masks, input gains, cues and thresholds. One offline
operator excluded pre-100 ms events; the other retained that history. Alternative
gains never fed back into neuronal transmission.

The capture completed exactly 33 attempted/completed calls in 50.5556 seconds:
one coarse call and 32 fine recordings. The cap was 33 calls and 600 seconds.
All coarse/fine and previously recorded canonical histories matched exactly.
The 112-test harness gate and independent 25-case reference check preceded capture.

## Measured result

| Home panel / noise | Cold mean gain-sum change | Continuous-history mean | Continuous absolute guard limit | Result |
| --- | ---: | ---: | ---: | --- |
| Original / base | −0.103840373 | −0.476172403 | 0.151163240 | Fail |
| Original / alternate | −0.060988627 | −0.314166754 | 0.108128833 | Fail |
| Second / base | −0.272640035 | −0.481925711 | 0.138446566 | Fail |
| Second / alternate | −0.074156590 | −0.263030000 | 0.131361783 | Fail |

All four away groups remain zero; no bounds were observed. The predeclared target
contrast is −0.209285676479 for published gains and −0.209285714082 for attempted
double changes. Neither the directional test nor the necessary stability screen
passed. No outlier, KC class or failed group was excluded.

## Verification and limits

The [independent saved-artifact reader](onset-capture-independent-audit.md)
verified all 104 bound files, 33 actual captures, 64 shadows, all 32 row effects
and eight guard groups. A separately derived event-pair integral reproduces every
final float32 gain vector bit-for-bit; onset/endpoint state errors are at double
rounding scale. A bound on the largest edge's total absolute integrated change
(0.157114, below the 0.5 distance to either bound) also excludes hidden clipping
followed by recovery. [Complete audit](onset-capture-independent-audit.json).

The reader imports neither the capture harness nor the simulator. Its author
also wrote the harness; separate-person implementation review is recorded in
[the capture review](onset-capture-review.md). Numerical independence and reviewer
independence are distinct. Files account for calls within this capture, not
unrelated external activity.

This rejects the proposed history-only correction on these fixed trajectories.
It is not a recurrent test with altered gains, does not establish a biological
cause, and does not authorize tuning this hypothesis. The
[PPL101 direct-input audit](ppl101-input-audit.md) supplies anatomical context for
the next signal-generation investigation, without turning contact fractions into
causal current measurements.

The [saved summary](onset-history-capture-summary.json),
[attempt ledger](onset-history-capture-attempts.json),
[capture copy manifest](onset-history-copy-manifest.json) and
[audit copy manifest](onset-independent-audit-copy-manifest.json) preserve exact
identities. The large original NPZ captures remain under
`output/collaboration/reward-mechanism-repair/onset-history-captures/onset-history-capture-4343c21535c43f42/`;
they were not rerun or overwritten for this account.
