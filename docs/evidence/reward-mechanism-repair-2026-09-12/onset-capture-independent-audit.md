# Saved onset-capture audit — September12,2026 UTC

**Execution/accounting audit: PASS. Scientific onset-only hypothesis: falsified.** The continuous-history shadow worsens the predeclared second/base home mean from−0.27264003455638885 to−0.48192571103572845. The contrast is−0.2092856764793396; independently reduced attempted changes give−0.20928571408227445. The directional test and necessary stability screen are both false. No variation, new circuit call, threshold change or mask/gain change was performed. Conditioning remains held.

| Home cell | Cold mean | Continuous mean | Continuous guard limit | Continuous result |
| --- | ---: | ---: | ---: | --- |
| Original/base | −0.103840373 | −0.476172403 | 0.151163240 | Fail |
| Original/alt | −0.060988627 | −0.314166754 | 0.108128833 | Fail |
| Second/base | −0.272640035 | −0.481925711 | 0.138446566 | Fail |
| Second/alt | −0.074156590 | −0.263030000 | 0.131361783 | Fail |

All four away cells remain exactly zero and pass their unchanged guards. Continuous history makes30 of32 individual home effects more negative. No cell or outlier was removed. The complete eight-cell cold/continuous metrics, all32 published/attempted row effects and phase totals are retained in the audit JSON.

## Independent checks

The audit is a new reader, `audit_onset_capture.py`, which imports no capture harness or BET36FLY module and invokes no native circuit. It reads every saved archive and programmatically checks the complete summary, including every nested per-group phase value. The author also implemented the original harness; independence here refers to the separately implemented reader and closed mathematical calculations. The source investigator's separate person-level implementation/oracle review remains in `onset-capture-review.md`.

- Frozen receipt and captured copy are equal; their identity recomputes capture4343c21535c43f42. The exact32 cue/noise/seed/order matrix matches an independently specified table. The attempt ledger contains exactly the one canonical coarse call followed by the32 frozen fine calls, numbered1–33 with increasing start times. All33 completed captures,64 shadow archives and five capture JSON documents are present; there are no unexpected/missing files or failure/stop artifacts. Recorded elapsed time is50.55563008389436seconds, within600seconds. The intermediate progress file retains the label `partial` but contains all33 completed records, identical to the final complete summary; that is its documented snapshot behavior.
- All97 NPZ hashes, all five capture JSON hashes, and the external frozen receipt/sample archive were read and checked. Every recorded capture-array dtype/shape/content fingerprint matches. The4774 unique sample indices, source body IDs, role maps, compartment assignments and7423 eligible edges reconcile with frozen anatomy. All11 graph/annotation hashes, pilot inputs/manifest/protocol and native binary match their captured identities.
- The six captured code hashes match Git snapshot `3b09865ba331b2c58c4bb8080e0d6354b4c8f612`. The harness, test and independent reference hashes match the reviewed capture receipt. This checks the captured source version; it deliberately does not require the current working copy of reward_diagnostic.py to remain unchanged during legitimate subsequent UI work.
- Canonical coarse/fine arrays match exactly, including50-bin spike aggregation. Every fine actual checkpoint/gain_delta, individual DAN count bin, compartment DAN step history, aggregate KC step history and sensory history matches its previously saved cold panel. First-cue sampled histories and canonical complete numerical fingerprints also reconcile. Returned spike totals agree with full-neuron counts and sampled totals.
- All64 shadow onset double/publication gain snapshots equal the unit initial checkpoint. Onset states were independently reconstructed by directly summing actual pre100ms impulse responses, excluding the100ms event; cold states are zero and continuous states retain the actual history. Endpoint states were independently reconstructed at400ms. Maximum onset-state error is1.25e−14; endpoint error4.20e−13.
- For every KC/DAN event pair, a separate analytic integration of the true positive and negative continuous products and the signed net reproduces all four per-edge phases. This calculation uses neither the captured recurrence/A/C coefficients nor its retained oracle. Maximum true-area discrepancy is7.85e−16; net discrepancy2.10e−16. Per-edge phase publication sums equal final gain-minus-one exactly. All64 final float32 gain vectors match independently integrated pair sums bit-for-bit; all32 cold shadows also match the actual native checkpoints bit-for-bit.
- Every edge/group/summary phase value reconciles, and all published/attempted effects and eight guard cells recompute exactly. Recorded bounds are zero. Independently, the largest per-edge total positive-plus-absolute-negative integrated area is0.1571136419805323. This bounds every prefix change and is well below the0.5 distance from unit gain to either bound, excluding a hidden transient contact or clipping/recovery explanation, including the tail.

## Scope limits and conclusion

The retained actual trajectories equal the canonical cold evidence; the reviewed captured harness contains no path from shadow gains back into neuronal transmission, and actual checkpoint hashes were checked after each shadow. This supports the claimed no-feedback shadow calculation. It does not simulate the recurrent consequences of warm gains or qualify a new circuit mechanism.

The source structure, exact attempt ledger, artifact inventory and prior parity establish no unexplained or unrecorded call **within this capture record**. Files alone cannot exclude unrelated calls elsewhere or replace independent process tracing. Similarly, no-prewrite evidence combines actual onset snapshots, the frozen gate implementation and independent post-onset integrals; a saved snapshot alone would not prove every earlier instant.

The conclusion is therefore specific: preserving pre100ms signal history does not repair the failed untaught stability gate on these fixed cold trajectories. It makes the predeclared target worse and fails all four home guards. Stop this onset-only repair hypothesis. This is adverse evidence for that modeled boundary explanation, not evidence against dopamine learning in real flies.

## Reproduce and exact hashes

```sh
.venv/bin/python output/collaboration/reward-mechanism-repair/audit_onset_capture.py
```

The script completed with all assertions passing; no server, circuit call or production change occurred. No full repository tests were rerun for this artifact-only audit. The verification-startup incident document was read completely; it is a separate operational issue and does not change these frozen experimental inputs.

- Capture summary: `244b4dcc1aa40b8c0c7be068bf7e66f8e369921f1005dd474ca37f9460dabb1b`.
- Frozen/captured receipt: `9aeea0c9227bf9ad4326277c39eb47966d5ab95ba6870bb3720f0d9b278788fc`.
- Sample map: `5f2414ffe5cab3d99cc1c1f0e91071df1f48721a7709816e90360af8b41074b3`.
- Attempt ledger: `3ff622560b50432b12ba45499571efb423d1630c83913fd5b852f4802407aaec`.
- Audit script: `71522a3c8a5f992238e3250a5407a2ec55991595cda9962e12d20e83d865bb0d`.
- Audit JSON: `7de1cd79bc06795cd16c3c7ec6d41c3e1e6bf5f99aadc16d1f6783b00d987ac5`.

`onset-capture-independent-audit.json` contains the complete104-file audited hash inventory, graph/pilot/native/source identities, numerical maxima and recomputed results. Original capture artifacts are unchanged.
