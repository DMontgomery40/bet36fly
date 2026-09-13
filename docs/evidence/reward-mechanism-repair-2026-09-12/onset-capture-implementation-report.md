# Onset-history capture harness — September12,2026 UTC

Output-only implementation released for independent review. No production source/test edit, full-CNS capture, sports run, server startup, parameter change or new learning rule. Sol retains production ownership. The failed bridge qualification remains failed; continuous-history effects are unmeasured.

The governing contract is `docs/evidence/reward-mechanism-repair-2026-09-12/onset-history-investigation-preregistration.md`, SHA256 `ca01c345c6c28ba2879b7cf05a6d1b2b802392f0067862e701a69da5778a5ad5`.

## Delivered

`onset_history_capture.py` freezes the exact32 cue/noise/seed rows against an independent hard-coded table. It reads/hashes the two prior summaries and all bound artifacts,11 graph/annotation files, six relevant code files, native binary and pilot inputs/manifest/protocol. The identity includes fixed biological/interface parameters, Python/NumPy/platform versions, the harness/test hashes, and the independent reference script hash. No circuit is constructed during freeze/metadata validation.

The frozen sample artifact contains4774 sorted unique int32 global neuron indices, corresponding source body IDs, full KC/DAN/sensory identities, local-to-sample column maps, plastic edge mappings/groups and eligibility. Actual roles are disjoint; role overlaps are explicitly recorded. Every array has a dtype/shape/content hash, and the complete mapping archive has its own SHA256. Existing mismatched receipts or mapping files are preserved and rejected. A real-metadata JSON roundtrip regression catches nonpersistent tuple/list identity differences.

Execution uses the existing engine API: one coarse10ms canonical call and32 fine0.2ms untaught calls, independent unit gains, identical repeated float32 schedule, unchanged cold bridge, no teaching pulses, record=False. The first coarse/fine pair must match every returned numerical array or exact50-bin spike aggregation before remaining calls. All32 fine calls must match old gains, gain_delta, sensory matrices, individual DAN count bins, compartment DAN step histories and aggregate KC step histories; first-cue sampled histories and the canonical complete returned-array fingerprints also match. Every returned array and scalar metadata is preserved.

An attempted-call ledger is atomically written immediately before every engine.run, distinct from completed/saved counts. Results are saved before validation; failures preserve both the attempted identity and completed artifacts. There is no resume or overwrite of an existing capture directory. An external supervisor enforces cancellation and a600second deadline, terminating/killing the worker even if it is inside native C++; the worker also checks between operations. The33-call structure and attempted-call cap are explicit.

Cold and continuous-history calculations run offline on the unchanged captured raster. Both retain exact-onset R/E snapshots plus actual double/publication gain snapshots, verify zero pre100ms writes, integrate the fixed interval/tail formula, record per-edge and grouped true positive/negative, attempted/double/published changes and bound observations, and preserve actual engine gains. Closed event-pair phase potentials independently verify attempted integrals; cold final float32 gains must match the native checkpoint exactly. Scientific output reports all32 rows, all eight panel/channel/noise guard cells, directional contrast, double-attempted contrast and inclusive bound screen. It always marks circuit qualification false: shadow gains never drive the neuronal trajectory.

## Validation and resolved findings

`onset-capture-initial-red.txt` records missing-harness collection failure before implementation; this is a feature-contract red, not a pre-existing biological defect. The source reviewer later identified a real receipt bug: JSON converted a tuple field list, so read-back identity equality would always fail. `onset-capture-identity-red.txt` reproduces that failure against actual saved metadata before the fix. Fields now persist as a list.

Final command:

```sh
.venv/bin/python -m pytest -q output/collaboration/reward-mechanism-repair/test_onset_history_capture.py
```

**112 tests passed in4.70s.** Coverage includes independent pair/continuous-quadrature true areas, exact handoff and boundary injection, pre-only and no-prehistory cases, partial populations1/2/22, sub-ULP publication, clipping/recovery/tail accounting, no prewrite snapshots, malformed rasters/mappings, nonconstant schedule/sample/seed/pulse coarse/fine parity, retained-artifact mismatches, exact selector changes, receipt immutability, midstream failures, timeout/terminate/kill/cancel, and durable attempt caps. A complete seven-neuron fixture runs the actual worker through33 tiny capture calls and64 shadows against synthetic canonical artifacts; it is not a MaleCNS measurement. A separate real metadata-only test freezes/reopens a temporary mapping receipt without constructing the circuit.

No full repository verification or browser check was rerun by this output-only worker; those contemporaneous production gates remain with root/Sol. No changed backend or frontend surface belongs to this harness.

Stable release SHA256:

- Harness: `8ec357c56d376d3f2073f2b3b64df3d7f3bf6955bdb4b0d55b007207d60833ed`.
- Test module: `131585b61a217c978777154d269881830ff851d795439ccc2e69496c7cfdf41b`.
- Focused log: `388a9bf2b0589e0b89f439565465dec595c2d7182d3241d0461a4d474e92de39`.

Independent source review and final signal-only oracle checks are separate evidence, not claimed here before receipt. This worker has released ownership and will not change either hashed file during root's capture.

## Root commands after independent review

Freeze only, no circuit construction or execution:

```sh
.venv/bin/python output/collaboration/reward-mechanism-repair/onset_history_capture.py --receipt docs/evidence/reward-mechanism-repair-2026-09-12/onset-capture-preregistration.json --freeze-only
```

The receipt's companion `onset-capture-preregistration.samples.npz` is created alongside it. This command prints the new immutable capture identity. Root owns the actual freeze and all full-CNS execution; this worker only exercised temporary test receipts.

Exact execution of the reviewed frozen capture:

```sh
.venv/bin/python output/collaboration/reward-mechanism-repair/onset_history_capture.py --receipt docs/evidence/reward-mechanism-repair-2026-09-12/onset-capture-preregistration.json --out output/collaboration/reward-mechanism-repair/onset-history-captures --cancel-file output/collaboration/reward-mechanism-repair/onset-history.cancel
```

Each capture gets a new directory under that output root. Do not reuse a completed/partial directory, remove a failing record, alter the contract, or interpret an incomplete shadow result. A failure is a stop for investigation. A favorable shadow result still requires a separately authorized mechanism implementation and all qualification/conditioning gates.
