# Independent DARELA shadow audit, before any captured-history evaluation

This output-only audit follows the completed DARELA preparation at local
`13966a2`. It will inspect exactly the 32 frozen untaught histories, after one
separately authorized producer execution. Preparing or testing this auditor
is not authorization to load those histories for numerical evaluation.

Each original fine raster retains its exact 24 DAN bodies, 4,064 KC bodies,
2,000 rows at 0.2 ms, source selector, sample order and input hashes. The
original sample mapping identifies all 8,866 anatomical plastic edges, the
2/22 DAN populations and unchanged masks. The saved original final gains
are a comparator, not an initial checkpoint; the candidate starts at exact
float32 one. Both original and candidate guard matrices are independently
reduced from their own retained float32 gains.

## Independent calculations and fixed numerical rules

Use the frozen `darela_release_reference.py` 60-digit transformed-coordinate
oracle on the original per-body binary events. Read every state_before,
state_after, per_cell_release, pooled_release and endpoint_state element.
The scalar source-Euler q, exact rational event clock, exact recovery,
pre-H release and per-cell-before-pool computation were independently
checked before this task. Compare these five arrays with fixed
`abs(actual-reference) <= 1e-12 + 1e-12*abs(reference)`. Silence emits exactly
zero. All pre-100 ms events evolve release state; only the unchanged bridge
is cold until step 500.

For bridge signals, independently superpose closed-form exponential impulse
kernels onto the raw KC events and reference release masses. These are direct
convolutions, not calls to the producer bridge or its event/state recurrence.
The rate kernel is exp(-age/100)/100 and eligibility kernel is
1.25*(exp(-age/500)-exp(-age/100)), with age in milliseconds. Analytically
integrate the resulting positive and negative products over every complete
0.2 ms interval, then the complete infinite tail. Evolve the gain accumulator
with the unchanged interval clipping and separate float32 publication.
Retain per-phase attempted/applied/absolute areas, every publication count,
inclusive bound observations and all mapped group reductions. Use no gain
clamp beyond the existing [0.5,1.5] publication rule, and no clamp on release.

A second independent check uses the previously inspected pure impulse-pair
kernel from `audit_kc_local_shadow.py`, copied as mathematical utilities only:

`H(lag) = -.0005*sign(lag)*(exp(-abs(lag)/500)-exp(-abs(lag)/100))`.

The complete pair matrix checks the unconstrained attempted integral, and
its analytically subtracted endpoint tail checks the finite attempted
integral. It proves final/electrical gains only when no clipping occurred.
When clipping occurs, the independent per-interval gain calculation owns
the endpoints; do not apply an unclipped pair formula as a gain oracle.
No rejected KC local model or source function is imported.

Fixed tolerances, accepted before outcomes:

- Release factors/masses and signal endpoints: atol=rtol=1e-12.
- Double gain endpoints: absolute allowance 1e-11, no relative extension.
- Separate product/phase/group areas: absolute 2e-11 plus relative 1e-12.
- Integer identities, masks, event totals and publication counts: exact.
- Final/electrical float32 gains: exact bit equality, otherwise explicitly
  record rounding ambiguity under the fixed double allowance; never force a
  numerical pass by selecting another rounding result.

The allowance is conditional numerical comparison scope, not a proved
universal interval enclosure. Outward/exact rational binary32 endpoint
rounding is used when reporting possible endpoint publications. Any gain
comparison outside the fixed allowance fails. A possible bound contact or
publication ambiguity is reported separately and cannot silently qualify
the screen. Excluded/frozen checkpoint bytes remain exact and have zero
numerical allowance where the update is identically zero. Preserve all
reported bound contacts; a bound-contact row rejects the fixed screen.

Recompute eight ordered trial totals per panel/seed-set/channel using exact
2^-24 ticks of the actual float32 gains. Preserve the existing inclusive
criterion `9*sum(ticks)^2 <= 16*sum(tick^2)`. Test equality, neighbors, signs,
permutations, zero and numerical-identity failures; do not change thresholds.

## Evidence, lifecycle and resource limits

The final machine contract binds the original capture/maps, all 32 ordered
selectors, producer identity/outputs, this contract, auditor/tests and each
pure reference dependency. Validate typed metadata, byte ceilings, NPZ
headers/declared allocations and exact source paths before array loading.
Read verified immutable byte buffers; snapshot and rehash every consumed
producer artifact and all original bindings at the final boundary. Require
complete matching terminal, row and archive identities; a terminal error
overrides a previously written completion marker.

Process one row at a time. Expected working memory is below 512 MiB using
cached finite kernels and sparse direct event superposition. The parent
has fixed one **600-second** external kill-and-reap watchdog with single-thread
BLAS set before interpreter startup. Internal work stops at 580 seconds,
reserving 20 seconds for preserving partial row evidence, summary and final
checks. Final persistence is still inside the 600-second limit. Retain
attempt/completion records and any partial outputs; never restart/resume an
identity. Missing rows, cap failure, changed bytes or ambiguous endpoints
cannot establish complete audited acceptance. Root must separately dispatch
the actual audit after producer completion and review freeze.

Tests use only deterministic synthetic rasters and temporary synthetic
artifacts. Include no DAN, masked/frozen, coincident events, substantial
release masses, clipping, endpoint rounding boundaries, malformed containers,
selector/mapping mutations and lifecycle failures. No optimization, fitting,
source solver, native calls, new neural run or captured-history computation
is permitted during this preparation.
