# Sensory backtest goal implementation plan

**Goal:** Carry the authorized natural sensory pipeline through an honest better-than-chance held-out backtest.
**Architecture:** Keep the production model and legacy engines unchanged. Add an isolated plasticity-off sensory engine with a source-locked cell adapter, a finite assay runner, external paired-probe readout and chronological sports evaluation. Freeze each stage before running it; later stages require earlier evidence.
**Tech stack:** Existing Python/NumPy/PyArrow/pytest and C++17; existing React/API only if exposing the new assay.
**Spec:** `docs/EXPERIMENT_SENSORY.md` and each immutable `configs/sensory-*.json`.
**Global constraints:** Full retained MaleCNS graph; no hidden legacy gains; source-informed rates explicitly separated from recorded biology; no active-pointer changes or v2 resume; no push/deploy; no confirmation reuse.

- [x] Resolve public source access and inspect the molecular subtype table, Figure 2 and matching physiology.
- [x] Add `bet36fly/sensory.py` cell-table reconciliation: `reconcile_cells(grn_rows, mn_rows, nodes)` returns sorted exact populations and discrepancies. Tests reject duplicate/lossy/cross-specimen/mismatched IDs and preserve unknowns.
- [x] Add `bet36fly/sensory_lif.cpp` plus Python wrapper. Inputs are CSR arrays, finite step-aligned rates and fixed seeds. Outputs are every neuron total, sampled time bins and delivered input events. No learning state. Test discrete generator units, deterministic resets, sparse direction, recurrence/refractory handling, inhibition, null input, saturation and equivalence to the existing empty-plasticity engine on small graphs.
- [x] Freeze `configs/sensory-assay-01.json` after cell checks and source review. Use source matching one-second measurement windows and explicit model assumptions. Define all controls, seeds, wall/call caps, generator/numerical/response gates before native execution.
- [x] Add `scripts/run_sensory_assay.py`: refuse overwrite/unknown identity, verify source/graph hashes, run sequentially with finite budget and record all requested/achieved rates plus output traces. Test artifact reuse refusal and stop-state behavior on tiny fixtures.
- [x] Run the declared assay on the actual graph; stop expansion at the first failed stage. If it fails, declare a distinct protocol addressing the measured limitation before another run. Never tune using sports confirmation data.
- [ ] Only after assay acceptance, implement the symmetric external paired-probe contract and swap/order/reset tests. Freeze and execute its finite examples.
- [ ] Only after paired-probe acceptance, freeze a finite training/development candidate batch and implement the chronological encoder/readout plus matching baselines. Keep confirmation outcomes inaccessible until final candidate freeze.
- [ ] Freeze and run one confirmation backtest using the global acceptance rule, all metrics and ablations. Preserve failures and allocate future confirmation attempts separately.
- [ ] Keep docs/API/frontend aligned with implemented behavior, run focused tests and `make verify`, guarded browser acceptance and local commits at substantive checkpoints.

The detailed code design for each later stage is written after its prerequisite measurements; this plan does not invent a successful sensory response or a sports mapping before evidence exists. Inline execution follows the user's continuing goal authorization.
