# Working rules for bet36fly

## Identity

- The circuit is the male CNS connectome. `docs/connectome-source-lock.json` pins the exact v1.0 files. Do not confuse it with the older female FlyWire datasets or with any Google language model.
- Reason in neurons, spikes, anatomical connectivity, neuromodulators and biological learning rules. The sports encoder and the MBON readout are engineered interfaces around the circuit. A conventional feature baseline is a comparator; improving it says nothing about the fly.
- Keep three things separate in every claim: biology documented in real flies, information present in the released dataset, and mechanisms implemented in this simulator. Inspect the code before saying a mechanism exists, is absent, cannot work, or explains a result. An unimplemented mechanism is a gap, not evidence against the biological approach.

## Current objective and continuation

- The September 13 better-than-chance `/goal` is achieved by the frozen 2023 confirmation in [the result](docs/evidence/sensory-backtest-goal-2026-09-13/RESULT.md). Stop automatic expansion for that fulfilled goal. Never reuse 2023 as an unused adaptive confirmation set. The passed claim is a conditional pipeline backtest with a source-informed second-order sensory response and external fitted interfaces; incremental neural value, feeding and innate choice remain unqualified. Preserve old v1/v2/legacy identities and no-push/no-deployment boundaries.

- David's September 13, 2026 direction is canonical in [PROJECT_DIRECTION.md](docs/PROJECT_DIRECTION.md): use calibrated natural food-related sensory patterns to represent two matchup opportunities and measure the circuit's response. Read the [current handoff](docs/NATURAL_SENSORY_HANDOFF.md) before continuing. Older repair handoffs are historical, even if their body says “continue the active goal.”
- First establish a bounded, plasticity-off natural sensory/feeding assay, then distinguish two opportunities, then map pregame metrics. Both teams can be attractive; a large supported difference can become appetitive versus aversive. Do not force a loser to be bad through pairwise normalization. Apply identical encoding rules to home and away and preserve uncertainty.
- Match cell identity, stimulus/dose, baseline and measurement window before quoting or injecting Hz. Separate measured sensory firing from Poisson requests, downstream rates, normalized responses, calcium signals and acquisition frequency. The current arbitrary feature-to-ALPN map is not fruit/sugar calibration. New source-backed ORN/GRN interfaces and appropriate outputs are permitted with explicit new protocols; do not inherit ALPN bypass gains without justification.
- Keep innate sensory response, an external comparison of two probes, in-circuit choice, acquired association and sports usefulness separate. Do not require a repaired dopamine rule before a frozen sensory assay. Do not launch another molecular transfer unless it addresses a measured limitation of the chosen assay with a finite decision boundary.
- Only pregame information may determine matchup stimulation. If a predictor supplies sweetness, include that encoder-only predictor and a same-information baseline. Following an injected forecast does not establish independent neural prediction. Similar sensory responses are not automatically a soccer draw or calibrated probability.

## Preserve experiment integrity

- The active v1 checkpoint has a fitted decoder; v2 is paused. The separate dopamine diagnostic has an engineered fixed readout and remains scientifically unqualified. Inspect the live pointer and current artifacts; do not resume old development or switch the active model as part of sensory calibration. [Model card](docs/MODEL_CARD.md).
- Preserve the legacy schema-3 comparator: glomerular type proxy, labeled-line ALPN ports, APL output gain 0.25, KC input gain 1.25, home = PPL101 / MBON11, away = PAM12 / MBON09. These are accepted engineered teaching channels, not a natural positive/negative pair. Its gamma away mask updates 3,239 edges while 1,443 others transmit; all 4,184 home edges remain eligible. Do not gamma-filter home by analogy. Do not retune these controls to erase a failed result. Historical sports and diagnostic configurations remain distinct.
- Legacy corrected raw/bridge qualification and later fixed-history, adaptation, gain-dependent, KC-calcium and DARELA shadows failed their declared guards. Preserve their rejected status and frozen parameters. The separate verified DA/NO equations are not a qualified MaleCNS rule. Detailed identities, limits and conditioning prerequisites remain in the [repair evidence](docs/evidence/reward-mechanism-repair-2026-09-12/index.md) and [legacy protocol](docs/EXPERIMENT_REWARD.md).
- SCI-001 remains HOLD for the legacy learning claim. Its operational untaught-change guard is not a universal biological law or a prerequisite for an unrelated plasticity-off assay. Any new learning protocol must justify and predeclare its own biological claims and controls without relabeling old failures as passes.
- Every code or protocol change produces a new experiment identity. Never rerun an existing identity and report it as new. Preserve source locks, imported research and prior results; scope edits around concurrent writers.

## Sources

- Start cell- and mechanism-specific work with [the fly wiki](wiki/index.md), its [cell atlas](wiki/cells/index.md), and the dated [reassessment](wiki/reassessment.md). Recheck current code and artifacts before relying on its status snapshot. The copied Microduck pages are research sources, not this project's working instructions.
- For a continuation of the legacy repair, every delegated agent must read all narrative repository docs/wiki, including copied research and later additions, and record actual reading coverage. For the natural-sensory task, read the complete authored wiki and relevant copied primary research, then reconcile later additions. A manifest or handoff alone is insufficient. Read large machine artifacts programmatically with complete relevant coverage. Use one production writer; independent reviewers can write separate evidence artifacts when delegation is authorized.

- Before substantive decisions about neural dynamics, learning, stimulation, readouts, or explanations of a failed run, read the primary sources: the [male CNS resource](https://male-cns.janelia.org/), the [Shiu reference simulator](https://github.com/philshiu/Drosophila_brain_model), and the links in `docs/MODEL_CARD.md` and `docs/FLY_GUIDE.md`. Check for current releases, issues and community results; new information can be recent.
- Record URL, version and date checked in `docs/evidence`. Distinguish a community report from an inspected implementation from a reproduced result. Shiu et al. 2024 uses female FlyWire; its model stimulation rates are not measurements of natural sugar input. Community implementations are starting points to verify on our simulator. A bounded search cannot establish the absence of all published MaleCNS work.
- Keep checks targeted and bounded. This does not authorize continuous polling, account changes, or unbounded research.

## Prevent documentation drift

- Keep the objective in `docs/PROJECT_DIRECTION.md`, current measurements in the model card/wiki reassessment, and detailed outcomes in dated evidence. `CLAUDE.md` imports these rules; do not duplicate an architecture or status summary there.
- When direction changes, update the current handoff, README, wiki index/reassessment, affected protocol status and these rules together. Mark superseded handoffs prominently; preserve historical bodies and immutable imported files. Recheck current code before promoting a proposal to implemented status. A documentation refresh does not itself authorize a neural run or model promotion.

## Backend and frontend together

A backend change is not complete until the frontend reflects it. Trace each change through the API contract (`docs/api-contract.md`), frontend types, controls, status displays, charts, results and explanatory text, and update every affected surface in the same task. Verify the browser workflow against the backend, including loading, empty, error and completed states. Backend tests and a green build do not establish that the visible experience works. For internal changes with no frontend impact, confirm the existing frontend is still accurate; do not invent cosmetic changes.

## Verification and git

- `make verify` runs pytest, Ruff, vitest and the vite build. Rebuild `web` before any browser check. Start QA with `make serve-verify`; the reward-panel browser check is `scripts/verify_reward_browser.cjs` (Playwright) and refuses an unmarked normal server before launching Chromium.
- State what ran, what passed and what is unverified when finishing.
- Commit locally on the working branch. David decides when to push.
