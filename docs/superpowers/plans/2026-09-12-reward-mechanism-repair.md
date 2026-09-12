# Dopamine mechanism repair implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development. Read the complete documentation corpus before work, as David explicitly requested. Read subsequently changed documents before completion.

**Goal:** Repair the learning implementation, demonstrate what its controlled tests establish, and keep scientific failures visible until their original criteria pass.

**Architecture:** Integrate the retained phase-1 instrumentation and mask implementation on the active feature branch. Repair timing and signal semantics with independent native-kernel tests, then exercise actual acquisition and reversal with matched controls and frozen probes. Keep mechanism evidence distinct from sports scores.

**Tech stack:** C++17 native LIF kernel, NumPy/Python, pytest, FastAPI, React/TypeScript, Vitest, Playwright.

**Spec:** The active user request, `AGENTS.md`, `wiki/evidence-gates.md`, the frozen phase-1 rule specification and the source review at `output/collaboration/reward-mechanism-repair/mechanism-sources-report.md`. The rate-bridge equation must be written and reviewed before candidate simulation or implementation; its implementation task is dispatched only with that completed specification.

## Global constraints

- Preserve the copied Microduck wiki and its source files; do not edit immutable historical evidence to change its verdict.
- Every worker reads all 81 documents in the 28-part corpus, plus subsequent changed documents. Record actual reading, not merely file enumeration.
- MaleCNS v1.0; home PPL101 / MBON11, away PAM12 / MBON09. Home eligibility remains all supported inputs; away updates are restricted to gamma KC inputs, with excluded transmission preserved.
- Keep ALPN input gain 0, APL output gain 0.25, KC input gain 1.25 and global weight scale 0.5. Do not retune these or change the sports encoder/readout.
- Preserve historical manifests and `output/current-model.json`. New code or protocols require new experiment identities. No push, promotion or sports pilot.
- SCI-001 keeps its original guard. A lower learning rate, suppressed learning, or a changed pass threshold is not a repair.
- Before/after behavior, numerical correctness, full-circuit learning and biological validity are separate claims.
- One implementation worker at a time; independent read-only scientific and test review may run alongside it. No child delegation.
- Run focused tests and `make verify` after implementation, then rebuilt browser acceptance for affected API/frontend states. Commit locally on the working branch.

### Task 1: Integrate retained repair and correct refractory teaching timing

**Files:** phase-1 branch changes; `bet36fly/reward_lif.cpp`, `tests/test_reward_brain.py`, associated learning documentation.

**Interfaces:** retain legacy `dan_reference` selection, immutable `plastic_mask` and per-step recording from phase 1; `teaching_pulses` are instantaneous voltage impulses at their declared times.

- [ ] Integrate `feat/reward-repair-phase1` (81037f1) into the active branch; preserve the newer wiki and accurate signed-baseline explanation when resolving documentation conflicts.
- [ ] Add a failing native regression that runs beyond refractory release. Parameterize early, middle, immediately-before-release, exact-release and after-release pulses, including repeated rejected pulses and multiple DANs.

```python
# One isolated DAN; first spike is at t=0, refractory is 2.2 ms.
# A second instantaneous pulse at t=1.0 ms must not appear later at t=2.2.
result = engine.run(schedule, bin_ms=0.2,
                    teaching_pulses=[(0.0, 0), (1.0, 0)], sample=dan_ids)
assert result['trace'][:, dan_column].nonzero()[0].tolist() == [0]
```

- [ ] Observe the delayed-spike failure, then deliver an instantaneous teaching impulse only when `t >= ready[dan_indices[pulse_dans[pulse_cursor]]]`. A rejected impulse must not accumulate voltage. Preserve pulses exactly at release and keep unrelated DANs independent.
- [ ] Cover the same bug family for delayed recurrent synaptic input: Shiu marks both voltage and conductance `unless refractory`; Brian documents those state variables as read-only, including incoming synapses. Reject delivery into a refractory target, preserving other targets, signs and sensory zero-refractory behavior. Verify the exact discrete release boundary against the reference; document any retained scheduling difference instead of claiming whole-engine Brian parity.
- [ ] Assert actual spikes and sampled bins, not only returned scheduled pulse metadata. Cover frozen and learning calls, duplicated pulses, and recorded/unrecorded parity. Run focused tests and `make verify`; commit locally.

### Task 2: Repair signal semantics against a declared scientific contract

**Files:** `bet36fly/reward_lif.cpp`, `bet36fly/reward_brain.py`, `bet36fly/reward_protocol.py`, protocol config, reference tests and evidence.

**Interfaces:** retain legacy event modes for historical interpretation; version the candidate rule and record units/filter parameters in every identity. Source investigators supply the completed equation and test matrix before this task is dispatched.

**September 12 execution decision:** Task 1's refractory correction, with raw event dopamine and the gamma away mask, passed all seven original criteria in `diag-candidate-maskgamma-a4e0db0de471`. The rate bridge remains a preregistered hypothesis, not an implementation requirement. First validate this smaller correction on the remaining eight calibration cues with new noise. Do not implement an unnecessary signal filter after a successful correction.

- [ ] Strengthen diagnostic selection, complete-matrix validation and graph/annotation identity. Declare remaining calibration offsets 8–15, base seed offset 2,000,000 and alternative offset 3,000,000 before results. Keep the cumulative sequence at all 16 original calibration cues with fresh base noise.
- [ ] Independently review the harness and execute the held-out panel. Keep the original seven thresholds unchanged. Proceed to conditioning only after it passes.
- [ ] If the corrected raw-event rule fails a mechanism gate, preserve that result and evaluate the already frozen rate-bridge hypothesis through the following numerical and scientific checks. A pass of the smaller correction leaves the bridge unimplemented.

- [ ] Reconcile the primary rate-model equation, its actual implementation and the observed millisecond residual; preserve the rejected onset-warming finding.
- [ ] Before implementation, publish the exact candidate equation, numerical order, onset/reset/tail contract and predicted falsifiers in `docs/evidence`.
- [ ] Write independently derived timing, silence, population-normalization, mask, clipping, reset and recording-parity tests; show the missing behavior fails before adding the candidate.
- [ ] Implement the reviewed signal conversion. Check numerical convergence against an independently computed convolution/oracle, rather than copying the native recurrence into expected values.
- [ ] Run the unchanged diagnostic matrix under a new identity. Retain all failures and signed per-compartment results. Any follow-up has a new hypothesis and identity; never tune a parameter merely until the old guard passes.

### Task 3: Establish acquisition and reversal controls

**Files:** a bounded conditioning runner/module, tests, frozen protocol and evidence artifacts.

**Interfaces:** use `RewardEngine` and the actual retained circuit; start all arms from identical gains; start reversal from saved acquired gains; every evaluation uses frozen gains and fresh input noise.

- [ ] Declare cues, seeds, exposure, teaching times, stage lengths and all criteria before executing the circuit.
- [ ] Test paired, timing-unpaired, shuffled, untaught and frozen controls with matched exposure and explicit reset boundaries. Verify the control schedule itself and reject missing/duplicated evidence rows.
- [ ] Check specific KC support and MBON responses, not a pooled gain mean alone. Compare reversal with continued acquisition and exposure controls from the same acquired checkpoint.
- [ ] Run the bounded protocol, preserve checkpoints and hashes, and retain all per-seed outcomes. A synthetic graph pass is a numerical result; the actual MaleCNS run is a separate gate.

### Task 4: Expose the actual mechanism and evidence in the product

**Files:** `bet36fly/server.py`, `docs/api-contract.md`, frontend types/panel/tests, browser verifier, current wiki and experiment docs.

**Interfaces:** read-only stored evidence endpoints; distinguish old event rules from the repaired candidate; missing evidence remains unrecorded, not passed.

- [ ] Show rule, time constants, compartment eligibility, diagnostic status and conditioning/reversal status with artifact links and no training or promotion action.
- [ ] Add contract and visible state coverage for loading, empty, error, running, failed, incomplete and completed evidence. Preserve historical experiment display.
- [ ] Update the wiki's current status with exact results and limitations; leave copied source pages intact.
- [ ] Run `make verify`, rebuild web and verify the real browser/backend workflow.

### Task 5: Independent review and local closeout

- [ ] Review the complete repair diff and scientific claims with an independent agent that read the full corpus and changed docs.
- [ ] Address substantive findings with covering tests, rerun affected checks, and check protected artifact hashes plus wiki copy hashes.
- [ ] Commit the finished repair locally on `feat/bet36fly-dopamine-learning`. Report what passed and any remaining scientific limit. Do not mark the goal achieved if the required mechanism work remains unfinished.
