# Sports development, recovery circuit (2022, circuit-02, ρ = 0.005): saturation fixed, prediction unchanged

Seven arms of `configs/associative-sports-02.json` ran on Hugging Face Jobs (cpu-upgrade) with the version-2 rule at the ρ selected by the stress test; everything else (encoder, innate cache, cues, probe seed, 48-hour/UTC-day reinforcement rule, readout procedure, split) is identical to the no-recovery baseline. Each evaluation also includes the circuit-01 plastic arm at the same learning rate as an extra comparator (`plastic:baseline`).

| η | recovery plastic acc / log loss | frozen twin | shuffled twin | no-recovery baseline | encoder only | recovery − frozen | recovery − shuffled | recovery − baseline | recovery − encoder | shuffled − frozen | contributes | chance |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1e-05 | 58.90% / 0.674427 | 58.36% / 0.673896 | 58.36% / 0.674294 | 58.59% / 0.675559 | 58.67% / 0.668847 | +0.000531 [-0.000596, +0.001508] | +0.000133 [-0.000191, +0.000476] | -0.001132 [-0.002563, +0.000406] | +0.005580 [+0.001049, +0.010108] | +0.000398 [-0.000516, +0.001203] | False | True |
| 2e-05 | 58.05% / 0.674408 | 58.36% / 0.673896 | 58.75% / 0.675286 | 59.21% / 0.675383 | 58.67% / 0.668847 | +0.000512 [-0.000682, +0.001607] | -0.000878 [-0.001767, +0.000053] | -0.000975 [-0.002697, +0.000837] | +0.005561 [+0.000993, +0.010329] | +0.001390 [-0.000665, +0.003308] | False | True |
| 4e-05 | 58.51% / 0.674268 | 58.36% / 0.673896 | 58.28% / 0.674603 | 59.06% / 0.674898 | 58.67% / 0.668847 | +0.000372 [-0.000806, +0.001456] | -0.000336 [-0.000888, +0.000172] | -0.000631 [-0.001693, +0.000380] | +0.005420 [+0.000787, +0.010243] | +0.000707 [-0.000822, +0.002177] | False | True |

Negative paired values favour the recovery arm. At every learning rate: no reliable difference from the frozen twin, from the shuffled twin, or from the no-recovery baseline (all intervals include zero; the recovery arm's point estimates are slightly better than the baseline's); still reliably worse than the encoder alone; still better than chance.

## Saturation with recovery

| arm | η | identity | first UTC day touching the floor | days with floor contacts | plastic gains at the floor at season end | mean gain | above rest |
|---|---|---|---|---|---|---|---|
| plastic | 1e-05 | `associative-sports-94f9a4913dcb12a55f15` | 53 | 124 | 0.8% | 0.883 | 0.0% |
| plastic | 2e-05 | `associative-sports-8cc62a9ff149c9aed4e4` | 27 | 150 | 0.8% | 0.863 | 0.0% |
| plastic | 4e-05 | `associative-sports-a50c18cdef85f343bf71` | 16 | 161 | 0.9% | 0.859 | 0.0% |
| shuffled | 1e-05 | `associative-sports-af5ff1730bd415573b85` | 51 | 126 | 2.3% | 0.884 | 0.0% |
| shuffled | 2e-05 | `associative-sports-98337217d227da045cc5` | 27 | 150 | 3.1% | 0.865 | 0.0% |
| shuffled | 4e-05 | `associative-sports-8e54361b9939c1dfbed2` | 16 | 161 | 2.9% | 0.862 | 0.0% |

Compared with the no-recovery arms (14.4%, 31.9%, 43.9% of plastic gains at the floor at η = 1e-5, 2e-5, 4e-5), the recovery circuit ends the season with 0.8–0.9% at the floor and a mean gain of 0.86–0.88 instead of 0.74–0.83, with no gain above rest. Synapses still touch the floor transiently on heavy reinforcement days (first contact days unchanged) but are pulled back by the dopamine of other teams' reinforcements.

## Answer to the mechanistic question

Dopamine-gated recovery preserves usable KC→MBON dynamic range during a full season of continual learning without destroying cue-specific memory (stress test: recent-cue depression retained; conditioning-03 unchanged). It does not, on 2022 development data, turn the learned team-value signal into a predictive advantage: the readout's learned differences remain uninformative beyond the encoder and innate features. Selection for the held 2018 confirmation, by the rule fixed before any sports run (minimum development log loss of the plastic arm): **η = 4e-5** (0.674268 versus 0.674408 and 0.674427).

Evaluation identities: η=1e-05: `associative-sports-evaluation-4182a66dd401fb6c12c1`, η=2e-05: `associative-sports-evaluation-25761719aa78e66627ef`, η=4e-05: `associative-sports-evaluation-2d1eac7f2f62b8de5144`.
