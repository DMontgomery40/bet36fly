# Reward repair, phase 1: dopamine rule diagnosis and candidate (2026-09-11)

Implementation lead Fable (Claude), reviewer Codex/Astra. Shared record with every review,
gate decision and raw artifact: `output/collaboration/reward-repair/` (local, not committed).
Worktree branch `feat/reward-repair-phase1` from `daaf080`. Historical pilot used as the circuit
and input source: `reward-v3-209f7c49983f5873f650` (schema 3, read only).

## Sources inspected

| Source | Identity | Use |
| --- | --- | --- |
| Jiang and Litwin-Kumar 2021, `runmodel.py` lines 50-57 | commit a16f86a3; sha256 782b8bd0…d17039 | Rule form `-D*Kbar + Dbar*K`, rectified nonnegative D, traces updated after the weight update, traces reset at trial boundaries, weights persist. |
| Jiang and Litwin-Kumar 2021, PLOS CB Methods | doi 10.1371/journal.pcbi.1009205 | Eligibility traces by low-pass filtering; weights start at the maximum 0.05; tau_W 5 s; biphasic timing curve. |
| `bet36fly/reward_lif.cpp` at daaf080 | sha256 ae78961d…ab154 | The schema-2/3 kernel: phasic = D minus tonic reference in both terms. |

## What the legacy rule did (before)

Panel `diag-legacy-a81d76a51b70` (8 calibration games x base/alt seeds x frozen/untaught/home/away
from blank gains; compartment gain sums):

- Untaught home change +1.97 (base, SD 1.91) and +2.04 (alt, SD 1.43) per trial; 16 untaught
  trials in sequence: +36.6, near linear. Away untaught exactly 0 (PAM12 silent, reference 0).
- Recorded terms: the whole untaught home change sits in the post-offset window, where PPL101
  falls to about 3 Hz against a 38.75 Hz reference measured during the stimulus, so
  `-Kbar * (D - ref)` is positive. Home teaching pulses raised PPL101 to 43 Hz, about the
  reference, and contributed -0.007 in that window. The legacy matched teaching effect
  (about -2.3 relative to untaught) is a real negative change, but it consisted of cancelling
  much of the untaught artifact rather than depressing the exposed synapses below their start.

## The candidate rule (schema 4, `dan_reference: none`)

Same panel, `diag-candidate-a85a3469301d`, frozen criteria (spec v1.1, section 5):

| Criterion | Result |
| --- | --- |
| Teaching-specific effect (per seed set, per channel) | pass: home -2.31 / -2.26, away -3.64 / -3.54, all 8 games negative |
| Untaught operational guard (mean within 0.5 SD) | **fail on home**: -0.289 (SD 0.32) and -0.240 (SD 0.38) |
| Cross-compartment leak | pass: exactly 0 both ways |
| No bound hits | pass |
| Cumulative untaught change (16 trials) | pass: home -3.61 against limit 9.14 |
| Bit-identical repeat | pass |
| Sensory-noise invariance (port spike bins) | pass |

Attribution of the untaught home change (`attribution-diag-candidate-a85a3469301d.json`):
onset-adjacent bins -0.020; later stimulus bins -0.118 (the two terms cancel to a few percent);
post-offset -0.127, all in the first 10 ms after offset, predicted approximately at 10 ms
resolution from the recorded eligibility mass and DAN events (-0.2055 predicted vs -0.2066
recorded for the `-Kbar*D` term; the per-step check below is exact).
Normalized cross-correlation between KC and PPL101 spikes per 10 ms bin: +0.49 at lag 0, +0.29
with the DAN one bin later, +0.09 one bin earlier. PPL101 receives 24,068 of its 39,125 input
contacts directly from Kenyon cells (13,836 from KCg-m), one from the sensory ports and 925 from
MBONs; a direct KC-to-DAN lag is a candidate explanation consistent with the asymmetry, not an
established cause. Finding SCI-001 is open.

Per-step follow-up (`attribution-diag-candidate-b57b80fdcdfc.json`, same 16 untaught realizations,
0.2 ms resolution over eligible home edges): the summed update reconstructs from the recorded
per-step DAN trace, eligible-edge KC impulses and eligibility mass to 1e-5. By phase: 100-130 ms
-0.020; 130-300 ms -0.118 (terms +3.105 and -3.223); 300-400 ms -0.127, with the last DAN event at
297 ms on average (max 305) and the last KC impulse at 304 ms (max 305), so nothing fires after
that. The KC-impulse/DAN normalized cross-correlation is small everywhere (max 0.037) with its
peak 3 ms after the KC side. Descriptive surrogates that alter only the DAN series inside the
plastic window: actual -0.265 (13 of 16 negative); DAN series advanced 5 ms -0.068, advanced
20 ms -0.013; delayed 5 ms -0.216, delayed 20 ms -0.199; time-reversed +0.214; every DAN event
jittered within 5 ms -0.253 (14 of 16 negative). Read as sensitivity, not proof: the residual is
tied to the order of the DAN activity relative to the KC activity at the 5 to 20 ms scale, not to
fine timing at the synaptic delay and not to reference, truncation or reset. SCI-001 stays open.

## Away eligibility mask (Stage C verification, `diag-candidate-maskgamma-ebe453ac10f5`)

Same panel with `away_plasticity_mask: gamma`: 7,423 of 8,866 edges eligible; home 4,184 of 4,184;
away 3,239 gamma edges kept, 1,443 excluded (1,438 alpha-prime/beta-prime, 5 alpha/beta), no
ambiguous labels. Across all 64 trials no excluded edge changed and their cumulative gains stayed
at 1.0; the gamma-edge update on away-taught trials is identical to the unmasked run (-3.405 per
trial), the excluded classes go from -0.181 and -0.002 to 0, and every MBON stimulus response and
sensory spike pattern is identical to the unmasked run (transmission preserved). The criteria are
unchanged: SCI-001 still fails on home, which the mask does not touch.

## Software delivered in this phase

- Recording-only instrumentation (per-bin signed rule terms by edge group, DAN signal and
  reference, KC spikes and eligibility mass, per-step eligible-edge impulses and mass) with
  bit-identical outputs proven on unit graphs and the full circuit.
- `dan_reference` mode (`none` candidate, `tonic-baseline` legacy) with a pairwise-kernel
  reference oracle over the Stage B case list and the offset-artifact test.
- Plasticity eligibility mask (`away_plasticity_mask`: `all` or `gamma`) with the transmission
  test and a label audit; schema-4 protocol; frontend and API contract updated.
- `scripts/reward_teaching_diagnostic.py` (frozen panel, completeness-checked, never overwrites),
  `scripts/reward_residual_attribution.py`.

No sports pilot, conditioning, reversal or readout centering has been run under schema 4. The
away mask is verified as software and anatomy (edge counts and update magnitudes above); its
protocol default stays `all` until the mechanism finding is closed.
