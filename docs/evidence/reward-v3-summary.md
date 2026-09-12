# MaleCNS dopamine-association pilot: measured outcome

**Reading this historical record:** the [September 12 UTC reassessment](../../wiki/reassessment.md)
adds the later rule diagnosis and separate repair-worktree status. SCI-001 remains
open. Earlier suggestions below to prioritize readout centering are superseded:
resolve the rule/trace semantics and away mask, then controlled acquisition and
reversal, before centering. The reported run identities and measurements remain unchanged.

The new learning mechanism changed the simulated circuit, but this configuration
made its sports probabilities worse. Both trained arms selected away on every
validation game. The frozen graph and fixed prior were substantially better.
This is a failed task-level pilot of explicit engineered dynamics, not a finding
that a biological fly cannot learn. [Aggregate machine-readable evidence](reward-v3-summary.json)
preserves the identities, measurements and controls.

Experiment `reward-v3-84fc629bc8045cbff7e0` completed all three arms in 227.06
seconds. Each used 64 training and the same 32 reused MLB validation games;
16 shared calibration games and three shared gate probes preceded training.
The active v1 pointer, paused v2 manifest and original sports source hashes were
unchanged. No model was promoted. [Protocol and limitations](../EXPERIMENT_REWARD.md).

| Arm / comparator | Log loss ↓ | Brier ↓ | Accuracy | Changed edges |
| --- | ---: | ---: | ---: | ---: |
| True-outcome teaching | 2.504442 | 1.204007 | 37.5% | 6,459 |
| Shuffled teaching | 2.521447 | 1.205291 | 37.5% | 6,459 |
| Frozen synapses | 0.755230 | 0.560732 | 37.5% | 0 |
| Fixed training-frequency prior | 0.701185 | 0.508035 | 37.5% | — |


## Follow-up: root cause of the collapse and the schema-2 rule

The collapse was traced on the frozen schema-1 circuit with instrumented single
trials (all 4,064 KCs and 17 DANs sampled per 10 ms bin, gains reset before each
probe). Three measurements explain it, in order of causation:

1. **The circuit never rests.** 56% of KCs fire in every 10 ms bin during the
   stimulus and in every bin after it ends. PPL101 fires at 350 to 380 Hz and
   PAM11 at 59 to 67 Hz with no teaching at all. This is recurrent activity, not
   a response to the outcome pulses.
2. **The rule multiplied raw DAN spikes.** With tonic dopamine, a KC burst was
   potentiated at once by the accumulated dopamine trace, while the depression
   that would compensate it accrues only after the trial ends (500 ms trace
   against 100 ms of remaining trial). Without any teaching, one trial moved the
   home compartment by +0.0106 and the away compartment by -0.0038 mean gain.
   Home teaching added -0.0070 and away teaching -0.0123 on their own
   compartments, the intended direction, but of the same size as the drift.
   The home pulses evoked 62 spikes against 60 unpulsed: PPL101 sits at its
   refractory ceiling, so home teaching was physically almost absent.
3. **The KC code is the same for every game.** The active KC sets of different
   training games overlap with Jaccard 0.98 to 0.99. Whatever depression the
   away teaching produced landed on the same synapses for every game, so both
   trained arms depressed MBON07 uniformly (225 to 120 Hz) and the fixed readout
   (scale 0.05, clip 4) turned that into 98% away for every validation game.

A weight-scale sweep (0.5 to 0.15) and a Kenyon-cell input-gain sweep, recorded
in the JSON, found no uniform setting where DANs are quiet, MBONs respond and
the KC set is game-specific: at 6% KC activity both readout MBONs are silent
and the KC sets still overlap 84 to 94%. Whole-network activity after stimulus
offset stayed between 868 and 7,984 spikes per bin at every scale.

The implementation was corrected in two places. The kernel now measures each
compartment's tonic DAN rate in a 50 ms window before a declared 100 ms
plasticity onset and subtracts it in both rule terms, so tonic firing carries no
teaching (a stand-in for the adaptive dopamine baseline reported by Rajagopalan
et al. 2023 and modeled by Bennett et al. 2021, not for its circuitry). Native
tests show a late KC burst under a tonic DAN train moves the raw rule by +0.41
and the phasic rule by less than 0.02, while a pulse above baseline still
depresses. The gate now requires each teaching population to evoke at least
half of its scheduled forced spikes above the same-seed unpulsed probe, requires
calibration KC-set overlap of at most 0.5, and records tonic DAN rates and
post-offset KC persistence.

Rerun `reward-v3-40d7263f0d2cc1974cf0` (schema 2, same weight scale and data)
stopped at the gate in 12.85 seconds with no arm trained: home teaching evoked
2 of 8 scheduled spikes above a 380.0 Hz tonic rate; away evoked 37 of 60 above
66.1 Hz; the calibration KC sets overlapped 98.9%; 72.7% of KCs were still
firing after stimulus offset. The paired/shuffled/frozen jobs are marked failed
with that message. This is the correct outcome for this circuit state: the
experiment now refuses to score a comparison the circuit cannot carry. The next
work is the sensory encoder and drive calibration (a game-specific sparse KC
code with responsive MBONs and quiet DANs), not another training run.

The browser acceptance at 13:24:03 UTC (`scripts/verify_reward_browser.cjs`,
same served app) verified that the newest run opens on the failed gate with the
phasic-drive protocol text, the two new gate rows and the per-compartment tonic,
scheduled and evoked columns; that the earlier complete run remains selectable
with its three arms, curves and eight hash-matched downloads; the five downloads
of the new run; the six isolated state fixtures; and widths 320 to 1,024 pixels
without overflow or JavaScript errors. The sections below are the record of the
schema-1 pilot.

## Schema 3: glomerular encoder, calibrated drive, third pilot

Recorded 2026-09-11 (13:20 to 14:00 UTC). Full numbers are under
`schema_3_calibration` and `schema_3_run` in the JSON file.

**Why the schema-2 gate could not be passed.** Three measurements on this graph,
each reproduced with scratch scripts on four frozen calibration games:

- The v1/v2 encoder drove the same 32 ALPN ports for every game, so the active
  KC set was 98 to 99 percent shared. With a glomerular identity code (each
  feature owns four annotated cholinergic ALPN types tuned to preferred values)
  the driven port set differs between games, but at all gains of 1 the network
  still sat at 3,300 to 7,900 spikes per 10 ms bin, unchanged by the input.
- A full-population trace showed the antennal lobe itself reverberating: ALPNs
  and local neurons (lLN1_bc, lLN2 types) at 130 to 184 spikes per 300 ms, the
  refractory ceiling, carrying 95 percent of all spikes after stimulus offset.
  The released neurotransmitter table lists lLN1_bc as acetylcholine (ground
  truth) and lLN2 types as 44 GABA to 40 acetylcholine, so as signed the lobe is
  a self-exciting loop. Zeroing synapses onto the 686 ALPN ports (labeled lines)
  removed it; about 600 local and receptor neurons still reverberate but reach
  no KC, DAN or MBON.
- With labeled lines the KCs were almost silent, and after raising the KC input
  gain both readout MBONs stayed below 4 Hz. Decomposing the drive onto MBON11
  in one trial gave +2,808 mV·spikes from 447 KCs against −4,703 from the two
  APL cells (441 contacts onto the two MBON11 cells, firing 2 to 3 spikes per
  10 ms). Real APL inhibition is graded and non-spiking, so the APL output was
  scaled by 0.25.

**Why the away compartment moved.** With the drive calibrated, MBON07 (α1, four
cells, 22,840 KC contacts in total) fired 0 Hz on at least one calibration game
in every non-runaway setting, while MBON11 (γ1pedc, two cells, 41,460 contacts)
fired 40 to 70 Hz. The matched pair PAM12 / MBON09 (γ3) fired 0 Hz at baseline
and 42 to 53 Hz respectively at the chosen drive, so the engineered away mapping
moved there. Home stays PPL101 / MBON11. This is a data-driven change to the
spec's artificial mapping and is flagged for review.

**Chosen drive.** Scale 0.5, KC input gain 1.25, sensory input gain 0, APL output
gain 0.25, peak 150 Hz, width 0.5, 64 glomeruli over 275 ports. On the four-game
sweep: 16 percent of KCs at 10 Hz, 0.5 percent still firing after offset, KC-set
overlap 0.31, MBON11 51 Hz (minimum 38), MBON09 53 Hz (minimum 42), PPL101 41 Hz
tonic, PAM12 0 Hz.

**Third pilot `reward-v3-209f7c49983f5873f650`** completed in 129 seconds with
protected inputs unchanged. The gate passed on the real 16 calibration games:
KC active fraction 0.160, overlap 0.298, post-offset fraction 0.005, maximum
MBON 73 Hz, PPL101 evoked 8 of 8 scheduled teaching spikes and PAM12 88 of 88,
tonic rates 43.8 and 0 Hz. Each trained arm changed about 5,545 of 8,866 edges
(gains 0.65 to 1.38, no bound hits). Validation over 32 reused games:

| Arm | Log loss | Brier | Accuracy | Confusion (home, away truth × home, away prediction) |
| --- | --- | --- | --- | --- |
| Paired | 0.974 | 0.744 | 0.375 | [[0, 20], [0, 12]] |
| Shuffled | 0.986 | 0.754 | 0.375 | [[0, 20], [0, 12]] |
| Frozen | 0.684 | 0.492 | 0.563 | [[12, 8], [6, 6]] |
| Prior | 0.701 | 0.508 | 0.375 | — |

Both trained arms again predict away for every game (mean p(away) 0.75 versus
0.49 frozen). The gain vectors of the paired and shuffled arms correlate at 0.99
in both compartments: home gains rose to a mean of 1.022 and away gains fell to
0.975 in both. The teaching-specific difference between arms (mean absolute
0.0034) is seven times smaller than the shared change (0.0236). The away
compartment is depressed on the KC core shared between games; the home
compartment is potentiated by rule noise around a two-cell tonic PPL101
estimate, whose rate is unbiased on average across trials (0.84 versus 0.85
spikes per bin) but noisy per trial. The fixed readout is centered on the
untrained circuit, so the shared shift of the taught MBONs becomes a class bias.
A rank-based score, which ignores global shifts, gives 0.554 (paired), 0.483
(shuffled) and 0.500 (frozen) on 32 games: descriptive only, within noise.

**What this establishes.** The encoder now yields a game-specific KC code, the
drive keeps DANs and MBONs in a usable range, and dopamine-gated learning changes
real KC-to-MBON gains on a gated circuit. It does not establish learning that
improves prediction. The next problems identified at that time were the readout's
absolute centering and shared-core depression. Subsequent rule diagnostics changed
that priority: the learning mechanism and controlled conditioning come before
centering. See the [current assessment](../../wiki/reassessment.md).

**Software and browser acceptance for schema 3.** `make verify` and the
Playwright script pass; the script now opens the newest (schema-3, passed-gate)
run first, checks the encoder and cell-type gain text, the feature-to-glomerulus
table, the PAM12 teaching row, then the schema-2 failed-gate run, then arms,
downloads and the viewport matrix. Evidence is in `output/browser/reward-v3-schema3/`.

## What the measurements establish

All 166,700 retained neurons were simulated. Only 7,835 existing KC-to-MBON edges
were eligible to learn: 4,184 to MBON11 and 3,651 to MBON07. The two assigned
teaching populations contained two PPL101 and fifteen PAM11 neurons. Their spike
traces, individual time bins, frozen inputs, source indices and gains are saved
as registered downloads in Training. Evaluation changed no gains.

The pre-training gate found different output responses for different inputs with
the random seed held fixed, and changes in each teaching population's binned
spikes against an unpulsed common-input/common-seed probe. Calibration recruited
73.81% of KCs; the largest selected population mean was 368.33 Hz. These are
numerical checks, not validated physiological activity or a demonstration that
the evoked teaching signal dominates spontaneous firing.

Paired training changed predictions for all 32 games relative to frozen gains.
Yet paired and shuffled gain vectors correlated at 0.9852. Their first/last
training-trial away-output rates fell from 225 to 120/123.33 Hz, while their home
rates stayed near 363/362 Hz. Those trials contain different games; the matched
frozen arm stayed near 225/223.33 Hz away and 363/365 Hz home. Both trained arms
then predicted all 32 games away at approximately 98.1% mean confidence, getting
12 correct. Their confusion rows (home/away truth) were `[0,20]` and `[0,12]`;
the frozen arm's rows were `[7,13]` and `[7,5]`.

This supports a specific failure description: large shared changes in circuit
responses, converted by the fixed negative-response readout into confident
one-class predictions. It does not isolate the cause. Dense KC drive, strong
spontaneous DAN activity (143 spikes in each PPL101 cell during the initial
400 ms unpulsed probe), the phenomenological timing rule, compartment mapping
and fixed calibration are unresolved factors. The biological transfer remains
unvalidated. The next mechanistic comparison should test sparse input coding and
teaching strength relative to spontaneous modulation before another sports
parameter sweep. No further run is implied by this note.

## Upstream and community checks

Sources were read during the September 11 continuation before implementation;
repository history identifiers were resolved again at approximately 12:18 UTC.
Web retrieval can return cached pages: these identifiers are the histories
returned by the service, not a guarantee that an inaccessible channel has no
new work. Local code/graph hashes used by this experiment are exact and frozen.

| Primary source | Version / inspected material | Use and boundary |
| --- | --- | --- |
| [MaleCNS downloads](https://male-cns.janelia.org/download/) and [Google announcement](https://research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/) | v1.0, June 8 data release; September 3, 2026 announcement | Male brain plus CNS anatomy; imported files retain their source lock. Annotation identity does not supply receptor kinetics. |
| [Shiu reference simulator](https://github.com/philshiu/Drosophila_brain_model/tree/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960) | `model.py` on main; returned history head `91bdd1e`, September 14, 2024 | Female FlyWire reference, default version 630 with 783 files available. LIF foundation, not a male-CNS reward-learning validation. |
| [Jiang and Litwin-Kumar 2021](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009205), [implementation](https://github.com/alitwinkumar/jiang_litwin-kumar_mb_rnn/tree/a16f86a3e9e476eff6860c3c0e0e1bbe729d7f85) | `runmodel.py` / `definemodel.py` on main; returned head `a16f86a`, June 22, 2021 | Biphasic KC/DAN traces in a task-optimized rate model. This event-spike implementation borrows the timing structure, not that model's optimized network or measured units. |
| [Hige et al. 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4674068/) and [Handler et al. 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC9012144/) | Primary conditioning experiments and timing/receptor results | Pairing order and receptor-dependent effects matter. Backward pairing is not universally potentiating; a null result in one protocol must not be rewritten as another protocol's effect. This pilot reproduces neither experiment. |

The user's five community screenshots were traced as implementation leads:

| Demo | Source found | Evidence boundary |
| --- | --- | --- |
| Rubik's cube | [Nick Walton's post](https://x.com/nickwalton00/status/2098301053372621070) | No executable training implementation located in the bounded search. |
| Writing / fonts | [IGNIS post](https://x.com/ignis_code/status/2098205667375104374), [linked application](https://fly-type.fancy-egret-3392.chatgpt.site) | Linked site returned SiteNotFound; caption is not a verified biological-method description. |
| Beat Saber | [Lyra's original](https://x.com/_lyraaaa_/status/2097527368919470162), [creator follow-up](https://x.com/_lyraaaa_/status/2097726318662328415) | Creator describes connectome input, replay training and overfitting one track; earlier follow-ups distinguish motor replay from vision/RL still being trained. No executable methods repository located. |
| NPC world | [IGNIS post](https://x.com/ignis_code/status/2098297452722037055) | No linked implementation located; not silently attributed to an unrelated embodied project. |
| FLYTAPE rhythm | [Trou's post](https://x.com/_trou3/status/2098310919134884292) | The found link chain led to Google's announcement, not an inspectable training implementation. |

These demos motivate richer sensory, action and feedback interfaces. Their
captions do not specify which parts are learned inside a circuit, replayed,
externally controlled or biologically modeled. Missing public methods leave
those questions open rather than establishing that a demonstration is invalid.

Claude's repository-specific research was also recovered and compared with
primary sources and the local implementation. Its warning about drive and sparse
KC coding remains relevant: halving fast weights reduced saturation here but
did not establish sparse biological coding. Its stronger claims about universal
community failures, exact physiological transfer or reward error emerging
automatically are not adopted as reproduced findings.

## Historical market access

At 09:28:41 UTC, the existing provider credential returned HTTP 200 for a bounded
NBA historical-events window, with three events. At 09:50:50 UTC, the authorized
single-event request returned HTTP 200, settled event 70504944 and one Bet365 ML
market, updated at `2026-05-12T23:59:03.65Z` before the scheduled 00:00 tip-off.
This resolves the earlier missing access evidence. No credential or authenticated
URL is stored here. The [provider documentation](https://docs.odds-api.io/api-reference/historical/get-historical-odds)
describes closing odds, not a complete quote tape. One NBA result does not prove
MLB coverage or bulk-endpoint entitlement.

An indexed read-only fixture sample in the existing NBA database independently
found 9,258 Bet365 ticks, 562,673 Kalshi ticks and 105,959 Polymarket ticks. Twelve
sampled January 2025 outcomes had no linked markets. These counts establish
fixture-specific availability, not uniform historical coverage; capture time
does not become provider event time or game clock. The sports pilot above used
its original frozen MLB inputs, not this NBA sample.

## Software and browser acceptance

The independent review produced fixes for teaching-population evidence, common
randomness, budget completion and visible comparators. `make verify` passes
331 Python tests, 63 frontend tests, Ruff and the production build. Native tests
include disabled-learning parity, timing, bounds, locality, resets and probe
immutability. Runner tests cover source isolation and stopped/failing runs.

The browser acceptance script is `scripts/verify_reward_browser.cjs`. It uses
Playwright from an existing runtime (available through `NODE_PATH`), the served
app at port 8765 and measured saved results. It verifies arm selection, curve
rows, downloads against registered hashes, preserved v1/v2 identity, and a
viewport-width matrix. Loading, empty, error, running, failed and budget-stopped
states are isolated browser response fixtures, not fabricated experiment
results. Screenshot and execution evidence remain local in `output/browser/`.

The completed acceptance pass at 12:27:42 UTC verified all three arms, eight
downloads with matching SHA256, all six isolated state fixtures, and widths
320, 390, 540, 720 and 1,024 pixels without page overflow or JavaScript errors.
Desktop (1,440 pixels) and mobile (390 pixels) screenshots were visually
inspected. The app was started with automatic background inference/refresh
disabled; this acceptance did not generate new picks or resume training.
