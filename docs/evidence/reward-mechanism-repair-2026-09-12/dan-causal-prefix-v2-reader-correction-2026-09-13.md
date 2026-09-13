# Corrected archive selector contract

The first offline audit, `dan-causal-prefix-cb7eb73ca0c41bd37e4b`, stopped
with `ValueError: main sampled identity/order` before any contrast or waveform
comparison. Its parent exited with code 1 after 0.530719 seconds, without a
timeout. The failure, original plan, code, tests and review receipts remain
unchanged. This is an audit-reader defect, not a neural result.

The pinned source in `scripts/reward_teaching_diagnostic.py:190` concatenates
MBON selectors from `np.flatnonzero`, followed by DAN, KC and sensory indices.
The recorded main selector is **int64**, whereas the finer capture's sample
map is **int32**. The reader built an int32 expected main selector and its
strict comparison rejected the otherwise identical values. Both original
panels contain exactly the same 4,780 ordered int64 indices, with numeric
SHA256 `ebecab105c22bb43d6e2f6ed4cfb27a25062ffa013299cd082d7a399b87f0dbd`.
All 4,774 fine sample indices are present, with the six selected MBONs as
additional main-record columns. The metadata inspection loaded these index
arrays only. It did not evaluate a time series.

The synthetic complete-archive fixture reproduced the reader's mistaken
int32 assumption. Passing it therefore missed a real archive contract.
The separate v2 reader and fixture must require the actual int64 main
selector, preserving exact order, values, bounds and uniqueness. Broader
coverage must reject alternate widths, floating/boolean selectors, missing
or duplicate identities, changed order and wrong role membership. The
int32 fine-sample contract remains unchanged. Inspect the pinned producer
and both actual maps when reviewing the correction.

The [original scientific preregistration](dan-causal-prefix-preregistration-2026-09-13.md)
continues to define all 64 contrasts, prefix endpoints, checks and interpretive
limits. No kinetics, learning rule, panel, threshold, stimulus, gain or
eligibility mask changes. A new identity binds the separately named v2
driver, tests and launcher, this correction, independent review, and the
preserved failed attempt. It permits one new exclusive execution under the
same 120-second total cap. A successful result requires parent exit 0 within
the cap, no terminal error, all 64 completed rows, and matching completion,
status, summary and per-row artifact hashes. A late failure invalidates any
previous completion marker. The v1 identity must never be restarted.

The learning goal remains incomplete regardless of this reader correction.
Both qualification panels and controlled acquisition/reversal remain required.
