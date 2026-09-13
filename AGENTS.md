# Working rules for bet36fly

## Identity

- The circuit is the male CNS connectome. `docs/connectome-source-lock.json` pins the exact v1.0 files. Do not confuse it with the older female FlyWire datasets or with any Google language model.
- Reason in neurons, spikes, anatomical connectivity, neuromodulators and biological learning rules. The sports encoder and the MBON readout are engineered interfaces around the circuit. A conventional feature baseline is a comparator; improving it says nothing about the fly.
- Keep three things separate in every claim: biology documented in real flies, information present in the released dataset, and mechanisms implemented in this simulator. Inspect the code before saying a mechanism exists, is absent, cannot work, or explains a result. An unimplemented mechanism is a gap, not evidence against the biological approach.

## Where the work stands

- Active line of work: on-circuit dopamine learning, branch `feat/bet36fly-dopamine-learning`. Preserve the accepted schema-3 interfaces and gains: glomerular identity encoder, labeled-line ALPN ports, APL output gain 0.25, KC input gain 1.25, home = PPL101 / MBON11, away = PAM12 / MBON09. David accepted these on 2026-09-11 as engineered teaching channels with a fixed readout, not as a natural reward/punishment pair. The integrated repair's gamma away mask updates 3,239 supported edges while 1,443 others still transmit; all 4,184 home edges remain eligible. Do not gamma-filter home by analogy. The historical sports config remains distinct from these diagnostics. Design in `docs/EXPERIMENT_REWARD.md`; historical sweeps in `docs/evidence/reward-v3-summary.md`; current repair evidence in `docs/evidence/reward-mechanism-repair-2026-09-12/index.md`.
- The v1 checkpoint and the v2 decoder experiments are historical. `docs/EXPERIMENT_V2.md` and `docs/evidence/v2-development-summary.md` record why they stalled (input saturation; every neural model at the base rate). Do not resume them.
- The drive gains were set by sweeps and are not the current blocker. Do not retune them. APL output below 0.25 or KC input above 1.5 at weight scale 0.5 re-enters runaway.
- Open problem is the learning mechanism itself. Refractory input banking is corrected and the rate bridge has independent numerical verification, but corrected raw and bridge rules both fail the second panel's untaught-home guard. The fixed-history onset shadow worsened that failure and was rejected. The fixed rectified-rate adaptation shadow (`5165a92674683bf2b872`) failed all four home guards with excessive potentiation. The subsequent fixed gain-dependent shadow (`de1ab218973eb3ecd3d3`) also fails second/base home, with an independent 128-reference audit confirming the calculation. Neither shadow is a production rule. Do not revive rejected hypotheses through onset/tau/learning-rate/bound/threshold tuning. Investigate signal generation and plasticity coupling from primary evidence, then qualify the mechanism before conditioning and reversal with the frozen controls. Readout centering is evaluated only after those gates pass. Encoder redesign, closing-odds scoring and larger sports pilots are deferred.
- The subsequent fixed KC-local calcium/susceptibility shadow `6734494c82c54702ead0` fails all four home guards; all 32 home trial sums become more depressive. Its independent audit reproduces every final/electrical float32 endpoint exactly. The external source fit, pan-KC transfer assumptions and 4,064-cell results are preserved in the repair evidence. This mapping is rejected and remains outside production; do not tune its spike scale, ratio convention or fitted constants against those outcomes.
- Every code or protocol change produces a new experiment identity. Never rerun an existing identity and report it as new.

## Sources

- Start cell- and mechanism-specific work with [the fly wiki](wiki/index.md), its [cell atlas](wiki/cells/index.md), and the dated [reassessment](wiki/reassessment.md). Recheck current code and artifacts before relying on its status snapshot. The copied Microduck pages are research sources, not this project's working instructions.
- For this repair, every delegated agent must read all narrative repository docs/wiki, including copied research and later additions, and record actual reading coverage. A manifest or handoff alone is insufficient. Read large machine artifacts programmatically with complete relevant coverage. Use one production writer; independent reviewers can write separate evidence artifacts.

- Before substantive decisions about neural dynamics, learning, stimulation, readouts, or explanations of a failed run, read the primary sources: the [male CNS resource](https://male-cns.janelia.org/), the [Shiu reference simulator](https://github.com/philshiu/Drosophila_brain_model), and the links in `docs/MODEL_CARD.md` and `docs/FLY_GUIDE.md`. Check for current releases, issues and community results; new information can be recent.
- Record URL, version and date checked in `docs/evidence`. Distinguish a community report from an inspected implementation from a reproduced result. The peer-reviewed anchors are Shiu et al. 2024 (female FlyWire) and the mushroom-body learning literature. No peer-reviewed LIF work on the male CNS exists yet; days-old hobby repos are starting points to verify on our own simulator, not authorities.
- Keep checks targeted and bounded. This does not authorize continuous polling, account changes, or unbounded research.

## Backend and frontend together

A backend change is not complete until the frontend reflects it. Trace each change through the API contract (`docs/api-contract.md`), frontend types, controls, status displays, charts, results and explanatory text, and update every affected surface in the same task. Verify the browser workflow against the backend, including loading, empty, error and completed states. Backend tests and a green build do not establish that the visible experience works. For internal changes with no frontend impact, confirm the existing frontend is still accurate; do not invent cosmetic changes.

## Verification and git

- `make verify` runs pytest, Ruff, vitest and the vite build. Rebuild `web` before any browser check. Start QA with `make serve-verify`; the reward-panel browser check is `scripts/verify_reward_browser.cjs` (Playwright) and refuses an unmarked normal server before launching Chromium.
- State what ran, what passed and what is unverified when finishing.
- Commit locally on the working branch. David decides when to push.
