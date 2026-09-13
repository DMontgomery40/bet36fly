# KC lateral signaling: a concrete mechanism lead with tested transfer limits

September 13, 2026 UTC, following local checkpoint `ab0f80f`. The learning
repair remains incomplete. This study inspected primary physiology and code,
tested their numerical semantics, and preserved the complete external calcium
workbook. It did not evaluate another MaleCNS rule or rerun a rejected identity.

The [current-code audit](conditioning-contract-evidence-ui-audit-2026-09-13.md)
found no further reset, response-sign or independent-control defect. It
identified 642,933 KC→KC pairs / 1,153,845 contacts, represented as positive
fast inputs without muscarinic receptor state. The
[2026 primary-source review](handler-kc-switch-model-transfer-review-2026-09-13.md)
supplies a concrete local-calcium signaling model to investigate. This is a
documented missing representation, not a demonstrated cause of the failed guard.

## Exact source and data retained

The authors' public model is pinned at
`f0ee2079dae6761cc2d07f04e96e76e2654b6e3c`. Fourteen source, license and
calibration files total 171,449 bytes and match their Git blob identities.
They are preserved unchanged in `kc-lateral-primary-source-2026-09-13/upstream`.
The workbook contains 499 rows of WT/knockdown mean and SE values: all 1,996
numeric cells were read and checked finite, with no formula cells. Its input
and observation units follow the source driver; no fit was performed.

The download completed all fourteen files but exceeded its requested
120-second cap: recorded elapsed time was 225.688 seconds. The original
receipt and separate budget review remain intact. Process `64222` exited
zero and is closed. There were no retries or further downloads. This
acquisition exception is not relabeled a passing bounded execution.

## What the source audit changes about the next decision

The source uses separate calyx/axon calcium, adaptation and lateral inhibition.
It multiplies the entire stored inhibition state by the recipient's activity
sigmoid each step. The independently derived constant-input equilibrium
depends on `dt`; transferring parameters from the 30 Hz fitter or 10 ms
learning driver into our 0.2 ms kernel changes the mechanism. A continuous
interpretation must be derived explicitly instead of treating source
`tauinh` as a portable receptor constant.

The source's new dopamine drive is gated by external shock. Cold no-shock
zero is therefore built into that source model; previously evoked dopamine
can still decay and drive depression after shock. Copying its gate would
bypass our independent endogenous-DAN control. Its weights have no positive
update branch. Its readout normalization and learning-rate search are not
replacements for the accepted BET36FLY interfaces.

The independent reviewer also found double noise scaling in the source's
noisy fitting demonstration: a scale applied by the driver is applied again
by its function. The learning loop uses one scale. Twelve synthetic cases
isolate this difference. It does not change the noiseless optimizer and
does not invalidate the experimental measurements. Upstream bytes remain
unchanged; an eventual reproduction must declare which path it reproduces.

The [independent mathematical review](learning-coupling-mathematical-source-review-2026-09-13.md)
explains why the current antisymmetric timing rule need not be neutral under
endogenous correlated activity. It derives the pair kernel, complete tail,
pooling and reset consequences without reevaluating the 32 histories. An
accurate-prediction fixed point is a distinct model invariant; the home and
away labels do not justify inventing an opponent feedback circuit.

## Verification and scope

The direct source audit has 57 root cases and 82 independent cases. A separate
87-case analytic suite checks bridge and abstract feedback identities. These
are different proof scopes; neither is a fly-learning experiment. Only
hash-checked function definitions run in the direct source tests. Fitting,
plotting and learning drivers are inspected rather than executed.

Fresh `make verify` passed 4,055 Python tests with two existing warnings,
85 frontend tests, Ruff and Vite. The full protected inventory still matches
the prior checkpoint: 791 files / 5,497,884,387 bytes, with no changed,
added or removed entries. Production/API/UI behavior is unchanged, so no
new QA server or browser result is claimed. The byte-exact Microduck copies
and historical experiments remain preserved.

Next work must specify a local-state model and its input/observation anchor
before using this source as a candidate. External calcium fitting can be
separate from BET36FLY outcome selection, but normalized population calcium
is not a measurement of local calcium per simulated spike. Declare the
affected variable, clock, units, lateral support, reset/tail and conversion
to plasticity; retain endogenous DAN activity and all existing controls.
No parameter, inhibitory coefficient or candidate was selected by this audit.
