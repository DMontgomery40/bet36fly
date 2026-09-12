# Authoritative handoff: reward repair

Resolved on 2026-09-11 by David's request to fix the conflicting handoffs. This file is the
single operational source of truth. The older handoff files remain unchanged because their
SHA256 values were acknowledged in the phase status records; they are history, not instructions.

## Decision

The failed `SCI-001` mechanism guard blocks promotion, biological-learning claims, and claims
that reward learning improved sports prediction. It does **not** block one bounded, explicitly
development-only sports backtest whose purpose is to measure what the repaired candidate does.

This resolves the prior conflict:

- `HANDOFF_PROMPT_PHASE_2.md` incorrectly proposed running the existing schema-4 config unchanged.
  That config has only paired/shuffled/frozen arms and still sets `away_plasticity_mask: all`.
- `HANDOFF_TO_CODEX_PHASE2.md` correctly preserved the failed scientific gate, but incorrectly
  converted a claim/promotion gate into a prohibition on every task-level measurement.

Neither prior next-step instruction remains operative.

## Current verified state

- Canonical checkout: `/Users/davidmontgomery/Documents/ChatGPT/bet36fly`, protected branch
  `feat/bet36fly-dopamine-learning`, HEAD `daaf080030e23180fe1851b919e56e36a2a9c2ff` when the
  reward-repair worktree was created.
- Implementation worktree: `/Users/davidmontgomery/Documents/ChatGPT/bet36fly/.worktrees/reward-repair-phase1`,
  branch `feat/reward-repair-phase1`, HEAD `81037f15118c1d9857e78aa579292e9a46327c09` at this
  resolution; no tracked edits and only the intentional untracked `.venv` symlink.
- No schema-4 sports pilot has run. The only scored reward pilot remains historical
  `reward-v3-209f7c49983f5873f650`; its all-away result does not measure the repaired raw-D rule.
- Raw-D candidate diagnostics changed the rule behavior, but `SCI-001` remains failed: untaught
  home depression exceeded the predeclared operational limit in both seed panels.
- Gamma-only away eligibility was independently verified, but the existing
  `configs/reward-v4-candidate.json` still selects the broader `all` policy.
- No frontend work, odds scoring, model promotion, active-pointer change, bet, or new neural run
  is part of this handoff.

Recheck branch, status, processes, protected hashes, and these facts before acting. Current
workspace evidence overrides this snapshot if anything has changed.

## One authorized next deliverable

Implement and run exactly one new, version-stamped, controlled MLB development backtest on the
same 64 training games and 32 validation games used by the historical reward pilot.

Use four independently initialized, matched arms:

1. `paired`: correct outcome teaching; plasticity enabled.
2. `shuffled`: fixed permuted teaching labels; plasticity enabled.
3. `untaught`: identical sensory exposures/order/seeds, no teaching pulses; plasticity enabled.
4. `frozen`: identical sensory exposures/order/seeds, no teaching pulses; plasticity disabled.

All arms start from identical gains and reset circuit state/traces according to the declared
trial contract. Use the raw-D rule (`dan_reference: none`) and gamma-only away plasticity mask.
Home remains unfiltered. Keep the current encoder, gains, timing, learning rate, bounds, fixed
readout, calibration rows, train/validation rows, and seeds unchanged. Evaluation has no teaching
and no plasticity.

Because the arm contract changes, use protocol schema 5 and a new experiment identity. Preserve
schema-4 and every existing artifact. Do not overwrite, resume, relabel, or silently reinterpret
an earlier run.

## Required measurements

For all four arms, retain and report:

- log loss, Brier score, accuracy, confusion matrix, and mean class probabilities;
- prediction counts by class and rank AUC where defined;
- changed/eligible edge counts, bounds/clipping, compartment gain summaries, and gain-vector
  comparisons against frozen, untaught, shuffled, and paired as appropriate;
- paired-versus-shuffled and paired-versus-untaught differences compared with the shared change;
- exact protocol, code, graph, data-row, calibration, readout, seed, and artifact identities;
- confirmation that protected historical artifacts and the active v1 pointer did not change.

## Stop and interpretation rules

- One run only. No tuning sweep, rerun, centering, decoder refit, encoder/gain retuning, odds
  scoring, frontend diversion, or automatic follow-on experiment.
- A better or worse score is a descriptive development result. It does not pass `SCI-001`, prove
  cue-specific conditioning, validate the biological transfer, establish bookmaker value, or
  authorize promotion.
- If the implementation cannot produce the four matched arms honestly, stop before the neural
  run and report the exact blocker. Do not fall back to the old three-arm config.
- After reporting the result, stop. The later mechanism program remains cue-specific acquisition,
  genuinely timing-unpaired and untaught controls, fresh-noise probes, and reversal from acquired
  gains. That work requires a separate decision; it is not bundled into this measurement.

## Acceptance

Before reporting completion, run focused tests covering the four arm state transitions and
plasticity/teaching matrix, protocol identity/non-overwrite behavior, and gamma-mask selection;
then run `make verify`. Inspect the saved manifest/report directly. Browser work is not required
for this backend-only diagnostic unless a user-facing surface is changed.

