# Dopamine-gated circuit learning implementation plan

**Goal:** Implement and run a bounded whole-MaleCNS experiment in which actual
KC/DAN spike timing changes anatomical KC-to-MBON synapses, with a fixed task
readout and visible evidence in Training.

**Architecture:** Separate native scheduled-stimulus engine and anatomical
adapter; immutable protocol/experiment runner; existing read-only registry and
new reward-result component in Training.

**Tech stack:** Existing C++17/ctypes/NumPy/PyArrow/Python and React/TypeScript.

**Spec:** ../specs/2026-09-11-dopamine-learning-design.md

## Constraints

- Preserve v1 pointers, v2 manifest, source arrays, gains, and ledgers.
- No conventional decoder search, automatic promotion, or old-matrix resume.
- Keep source-derived biology, dataset annotations, and engineered mechanisms
  distinct in code, artifacts, and UI.
- All experiment execution is bounded, attributable, and separately identified.
- Existing standard verification is `make verify`; real browser checks complete
  the Training workflow acceptance.

## Work units

- [x] Read handoff/current instructions and recover Claude research.
- [x] Verify baseline quality gate and create a separate feature branch.
- [x] Inspect primary reward-learning source and available circuit annotations.
- [x] Audit historical provider docs and bounded indexed local market sample.
- [x] Confirm authenticated historical access: events and one Bet365 ML closing
  quote returned HTTP 200 after exact user-authorized requests.
- [x] Native engine: failing behavioral tests, scheduled input, true spike traces,
  sparse local gain update, strict ABI validation and disabled-learning parity.
- [x] Anatomical adapter and protocol: freeze explicit maps and readout; test
  annotation mismatch, unsupported edges, timing/leakage, bounds and identities.
- [x] Runner: calibration, activity gate, paired/shuffled/frozen arms, immutable
  results, protected inputs, failure/budget handling and real saved artifacts.
- [x] Frontend: distinct reward experiment panel, all states, matched results and
  spike/gain evidence; preserve original v2 tracker.
- [x] Run one bounded full-graph experiment and inspect the measured result.
- [x] One focused independent review; fix concrete findings and extend relevant
  test families.
- [x] Run narrow tests and `make verify`; verify browser workflow, reconcile docs
  with actual results, and report limitations without an automatic search loop.

## Execution result

`reward-v3-84fc629bc8045cbff7e0` completed in 227.06 seconds. It changed
6,459 graph edges but paired/shuffled teaching collapsed to confident away
predictions and lost to frozen gains and the prior. No repeat or promotion.
Measured details and provenance: [reward evidence](../../evidence/reward-v3-summary.md).
The native/runner review findings were fixed before the run. Browser validation
found a grid minimum-width defect; the viewport-matrix regression covers it.
