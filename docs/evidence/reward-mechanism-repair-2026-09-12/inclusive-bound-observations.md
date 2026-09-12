# Inclusive bound observations and replacement diagnostic freezes

September 12, 2026 UTC, before either replacement diagnostic panel runs.
The earlier held-out receipt `heldout-preregistration.json` (prospective identity
`diag-candidate-maskgamma-ee89fe032a62`) is **superseded and unrun**, retained
unchanged. The original corrected result `diag-candidate-maskgamma-a4e0db0de471`
is also preserved unchanged. Its original strict-clipping counters cannot prove
absence of every transient exact-bound contact.

The only native change in this follow-up is recording: rule-bin columns 3 and 4
now count `proposed <= gain_min` and `proposed >= gain_max`. They count eligible
edge-step observations at or beyond a bound, including exact equality, repeated
dwelling and an already-bound frozen gain with zero learning. They are not counts
of unique edges or distinct arrivals. Eligibility, gain updates, clamping,
transmission, traces, spikes and recording-disabled dynamics are unchanged.
The historical `clipped_low` / `clipped_high` layout names remain for compatibility;
the native source identity and this dated definition distinguish the semantics.
No counter is generated before the declared learning onset or for excluded edges.

Every complete panel and cumulative row must explicitly report a nonnegative
integer count; missing, negative, fractional, boolean or nonfinite values are
invalid. The overall no-bound criterion includes observations from both the
64 single-trial rows and 16 cumulative rows. The actual final saved gains are
independently checked against both inclusive bounds on eligible edges. Thus a
cumulative-only hit, or exact contact followed by recovery before the endpoint,
cannot pass silently. No scientific threshold changed: zero bound observations
remains required. The cumulative sums must also reconcile with the running sum of
per-trial applied changes at absolute 1e-6 with no relative tolerance.

Generalized native tests use exactly representable lower/upper contacts, subsequent
recovery, strict overshoot, frozen dwelling and recorded/unrecorded output parity.
They first failed on exact contact/dwelling under the strict counters. Separate
evaluator tests cover cumulative-only and final-checkpoint-only hits and malformed
or missing evidence, including direct evaluator calls without the completeness
helper. Production-tau long-lag raw-rule tests remain unchanged and pass.

Replacement native source SHA256:
`01893f465b20bb3956d0537e191dc0dbe0de7c63bcc45962fc396b6da1dc485e`.
Only `--preregister-only` has been executed for the following receipts:

- [Original selectors, new observation identity](original-preregistration-inclusive-bounds.json):
  `diag-candidate-maskgamma-29c766f95f82`; receipt SHA256
  `59aca2080877edf9d31a3180a3b842316adc20e8e65a712865b13ac3c7daeb7d`.
- [Held-out selectors, new observation identity](heldout-preregistration-inclusive-bounds.json):
  `diag-candidate-maskgamma-e3d8898dc68a`; receipt SHA256
  `43fe4f771339d194fca11c3752aab1876ab0cbcef5e21817a1f6cfc368b60d9f`.

The held-out source/seed selections remain those in the [selection contract](heldout-panel-contract.md).
Each receipt binds all actual/frozen graph and annotation hashes, frozen pilot
input/protocol/manifest hashes and final orchestration hashes before execution.
A code change after this freeze requires new receipts; neither old nor new results
may be overwritten. Independent review precedes both replacement panels. The rate
bridge remains unimplemented; this is an observation correction, not altered
learning dynamics or new conditioning evidence.
