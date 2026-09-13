# Independent KC-local shadow audit: frozen calculation contract

September 13, 2026. Preparation only: no actual captured history is evaluated
until root separately dispatches the frozen saved-result audit.

The actual audit is one attempt over exactly 32 rows with a 120-second total
wall cap, including input verification and output persistence. BLAS threads
are fixed to one before interpreter startup. The helper has an internal
alarm and monotonic guards; root also owns a hard subprocess watchdog. There
are no retries or restarts. Preserve completed per-row JSON on failure and
treat any terminal-error marker as overriding an earlier result. The
1500-by-1500 pair matrix is cached across rows; this is a structural timing
estimate, not an actual-history benchmark.

The auditor `audit_kc_local_shadow.py` uses the raw 2000×4774 rasters, original
sample/KC/DAN/edge maps, the already frozen external parameter vector and
recipient-row contact CSR. It imports no producer local-state or bridge
calculator. Original pinned source adaptation, inhibition and sigmoid
functions supply the local recurrence.

Assign electrical event j to source frame `floor(j*30/5000)`. Aggregate raw
KC events independently into 12 complete frames, then execute the 12 old-state
source updates. Retain zero snapshot 0 and completed snapshots 1–12 in
C/L/a/I order. Compare `source_frame_counts` exactly, and
`local_frame_states` plus `local_susceptibility` with `rtol=atol=1e-12`.
Derive each weighted event from the snapshot indexed by its frame; endpoint
snapshot 12 cannot affect an earlier event. Check raw/weighted event totals.

For bridge-admitted events j>=500, construct the independent complete pair
kernel

```text
H(lag_ms) = -.0005 sign(lag_ms) [exp(-abs(lag_ms)/500) - exp(-abs(lag_ms)/100)].
```

Matrix multiplication of this kernel with the 2/22-cell DAN mean histories,
followed by weighted KC histories, produces all KC/channel gain changes.
Map them to all 8,866 original edges, keeping excluded gains exactly one.
Compare `double_gains` with absolute tolerance 1e-11 and zero relative
tolerance. An independently evaluated endpoint impulse-response sum gives
the analytic residual tail; subtract it to check the electrical endpoint
and stored KC/DAN filter states.

Compare final and electrical float32 publications bit-for-bit against direct
casts of the independent double results. Any mismatch is explicitly reported
as failure or numerical ambiguity; no gain is adjusted to force agreement.
Check the stored 150/850/500/1 per-phase publication counts exactly. The
producer does not retain every intermediate gain vector, so this audit does
not claim to compare those unrecorded publications.

Any nonzero producer bound count rejects the screen and disables that row's
unclipped pair-kernel gain proof. The auditor still checks local states and
reported guard arithmetic; it does not silently clamp the independent law.

From all 32 ordered rows, independently calculate the eight
panel×noise×channel guard cells, each containing eight exact float32 trial
totals in units of 2^-24. Use Python integers and the unchanged test
`9*(sum totals)^2 <= 16*sum(total^2)`. Check both the saved point guards and,
when every row has an unbounded pair proof, independently cast reference
guards. Preserve every row; reject missing/reordered selectors or hash drift.

Read and verify the complete frozen source/input inventory before and after
the audit. Root owns the source-anatomy construction and producer lifecycle
review; this audit verifies the supplied anatomy identity, orientation and
normalization contract and reconstructs the local trajectory using that CSR.
It makes no new claim of independent receptor localization or causal circuit
ablation. No optimizer, native engine, network or live qualification call is
part of this audit.
