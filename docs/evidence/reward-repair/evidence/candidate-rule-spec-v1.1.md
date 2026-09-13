# Candidate dopamine rule specification, v1.1 (Stage A; criteria frozen after Codex review 0005)

Supersedes only section 5 of candidate-rule-spec-v1.md (sha256 c5bed6f0...). Sections 1-4 of v1 are
unchanged and remain the accepted equation/discrete contract ("ACCEPT WITH NONBLOCKING LIMITATIONS",
Codex review 0005, 2026-09-11T15:25:06Z). Changes: GATE-001 (criterion 4 normalization and statistic),
GATE-002 (per-seed evaluation), plus the reviewer's RNG-inspection note. Author: Fable.

## 5. Predeclared diagnostic panel and frozen acceptance criteria

Circuit, inputs, conditions and rule variants exactly as in v1 section 5: pilot protocol of
`reward-v3-209f7c49983f5873f650`, blank gains before each single-trial condition, first 8 calibration
games, two seed sets (base = protocol seed + source index; alt = base + 1,000,000), conditions
F (frozen), U (untaught, plasticity on), H (home-taught), A (away-taught); rules legacy (tonic
reference) and candidate (raw D). The same script and the same criteria are applied to both rules.

Notation: applied(cond, c, game, s) = sum over the plastic edges of compartment c of the applied
gain change in that trial (equivalently sum of the recorded `applied` term over all bins and groups of
c). Teaching effect Delta(c, game, s) = applied(taught-in-c) - applied(U) for the same game and seed set s.

1. Teaching-specific effect (evaluated separately for s = base and s = alt, and separately for home
   and away teaching; all four evaluations must pass): mean over the 8 games of Delta(c, ., s) is
   negative, and |mean Delta(c, ., s)| >= 3 x |mean over games of applied(U, c, ., s)|. Every
   game/seed value and its sign is reported; a single seed set passing is not a pass.
2. Untaught operational guard (per seed set, per compartment): |mean over games of applied(U, c)|
   <= 0.5 x SD over games of applied(U, c). Per-phase decomposition is reported (pre-onset must be
   exactly 0 by construction; stimulus-plastic 100-300 ms and post 300-400 ms with the recorded D
   and K signals). This is an operational guard against gross systematic drift, not a statistical
   claim that bias is absent.
3. Cross-compartment selectivity guard (per seed set): |mean over games of
   (applied(H, away) - applied(U, away))| <= 0.05 x |mean Delta(home, ., s)|, and symmetrically
   |mean(applied(A, home) - applied(U, home))| <= 0.05 x |mean Delta(away, ., s)|. If it fails, the
   recorded DAN signal bins decide between circuit feedback (the other compartment's D differs
   between conditions) and indexing/modulation leakage (identical D, different rule terms).
4. Cumulative untaught change (per rule): 16 consecutive U trials over the 16 calibration games
   (base seeds), gains carried over, from blank gains. The per-trial compartment gain-sum trajectory
   is recorded descriptively (all 16 points). Requirement, same normalization on both sides
   (compartment gain sums): for each compartment c,
   |sum over edges of c of (g_after16 - g_initial)| <= 4 x |mean over games and both seed sets of
   Delta(c, ., .)|. No sublinear-growth statistic is claimed.
5. No bound hits: recorded clipped_low and clipped_high counts are 0 in every panel trial.
6. Bit-identical repeat: re-running game 0 / base seed for each of F, U, H, A reproduces the gains
   exactly (np.array_equal).
7. Sensory-noise invariance, inspected directly: the sampled spike bins of all sensory ports (input
   neurons, no refractory period, no recurrent input at sensory_input_gain 0, so their spikes are the
   Poisson events themselves) are identical across F, U, H, A for the same game and seed set.
   Equality of every non-DAN count is reported only as a consequence of zeroed DAN fast outputs,
   not as the RNG test.

Expected under the legacy rule (before): criterion 1 fails for home (untaught home potentiation of
about +0.8 gain-sum per trial against a home-taught total that is not 3x more negative). Recorded
either way. Failing any criterion under the candidate is a documented failure and a reason for a
targeted, predeclared follow-up, not a threshold change.

## Erratum to v1 section 4 (INSTR-001, recorded 2026-09-11 after Codex review 0006)

The seventh `rule_bins` column is the sum of Kbar over the group's edges at bin end (eligibility
mass), as implemented and unit-tested at b81743a; v1 section 4 wrote "DAN-event count" for that
column. The compartment DAN event stream is in `signal_bins` column 0. The KC event count on group
edges (column 5) is recorded for every group, including a compartment without assigned DANs.
