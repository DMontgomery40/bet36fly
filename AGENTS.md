# Working rules for bet36fly

## Identity

- The circuit is the male CNS connectome. `docs/connectome-source-lock.json` pins the exact v1.0 files. Do not confuse it with the older female FlyWire datasets or with any Google language model.
- Reason in neurons, spikes, anatomical connectivity, neuromodulators and biological learning rules. The sports encoder and the MBON readout are engineered interfaces around the circuit. A conventional feature baseline is a comparator; improving it says nothing about the fly.
- Keep three things separate in every claim: biology documented in real flies, information present in the released dataset, and mechanisms implemented in this simulator. Inspect the code before saying a mechanism exists, is absent, cannot work, or explains a result. An unimplemented mechanism is a gap, not evidence against the biological approach.

## Where the work stands

- Active line of work: on-circuit dopamine learning, branch `feat/bet36fly-dopamine-learning`. Protocol schema 3: glomerular identity encoder, labeled-line ALPN ports, APL output gain 0.25, KC input gain 1.25, home = PPL101 / MBON11, away = PAM12 / MBON09. David accepted these on 2026-09-11 as engineered teaching channels with a fixed readout, not as a natural reward/punishment pair; the away-side plasticity mask is to be restricted to supported gamma KC inputs, and home is not to be gamma-filtered by analogy. Design in `docs/EXPERIMENT_REWARD.md`; measured results and sweep records in `docs/evidence/reward-v3-summary.md`.
- The v1 checkpoint and the v2 decoder experiments are historical. `docs/EXPERIMENT_V2.md` and `docs/evidence/v2-development-summary.md` record why they stalled (input saturation; every neural model at the base rate). Do not resume them.
- The drive gains were set by sweeps and are not the current blocker. Do not retune them. APL output below 0.25 or KC input above 1.5 at weight scale 0.5 re-enters runaway.
- Open problem is the learning mechanism itself: the dopamine rule and its trace semantics, then the away plasticity mask, then conditioning and reversal with proper controls. Readout centering is evaluated only after those gates pass. Encoder redesign, closing-odds scoring and larger sports pilots are deferred.
- Every code or protocol change produces a new experiment identity. Never rerun an existing identity and report it as new.

## Sources

- Before substantive decisions about neural dynamics, learning, stimulation, readouts, or explanations of a failed run, read the primary sources: the [male CNS resource](https://male-cns.janelia.org/), the [Shiu reference simulator](https://github.com/philshiu/Drosophila_brain_model), and the links in `docs/MODEL_CARD.md` and `docs/FLY_GUIDE.md`. Check for current releases, issues and community results; new information can be recent.
- Record URL, version and date checked in `docs/evidence`. Distinguish a community report from an inspected implementation from a reproduced result. The peer-reviewed anchors are Shiu et al. 2024 (female FlyWire) and the mushroom-body learning literature. No peer-reviewed LIF work on the male CNS exists yet; days-old hobby repos are starting points to verify on our own simulator, not authorities.
- Keep checks targeted and bounded. This does not authorize continuous polling, account changes, or unbounded research.

## Backend and frontend together

A backend change is not complete until the frontend reflects it. Trace each change through the API contract (`docs/api-contract.md`), frontend types, controls, status displays, charts, results and explanatory text, and update every affected surface in the same task. Verify the browser workflow against the backend, including loading, empty, error and completed states. Backend tests and a green build do not establish that the visible experience works. For internal changes with no frontend impact, confirm the existing frontend is still accurate; do not invent cosmetic changes.

## Verification and git

- `make verify` runs pytest, Ruff, vitest and the vite build. Rebuild `web` before any browser check. The reward-panel browser check is `scripts/verify_reward_browser.cjs` (Playwright).
- State what ran, what passed and what is unverified when finishing.
- Commit locally on the working branch. David decides when to push.
