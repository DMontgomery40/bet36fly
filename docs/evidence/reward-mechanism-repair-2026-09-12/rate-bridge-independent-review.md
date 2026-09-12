# Task 2B independent implementation review

September 12, 2026 UTC. Reviewer: mechanism_sources. Reviewed the released changes from local base `1c7060b`, against the frozen scientific preregistration and implementation contract. No production/test edits, native test reruns, server startup or full-CNS run were performed by this reviewer. The separately authorized independent mathematical reference audit is identified below.

**Spec-compliance verdict: PASS.** **Code-quality and test-quality verdict: PASS.** No remaining blocking findings. These verdicts qualify the released implementation for the predeclared original panel and, conditional on that result, the previously frozen panel. They are not a claim that either circuit panel passes or that acquisition/reversal works.

## Stable reviewed identities

Both full preregistration JSON documents were read, including each exact 64-row matrix and 16-row cumulative sequence. All six code hashes in each were independently compared with current files and matched after the worker released ownership and completed verification.

- Original `diag-rate-bridge-v1-maskgamma-1b233bc75647`; receipt SHA256 `7eee2f2098f9cb64a6729fc27aa02ca718624b4ed0bbfc4b3ca4c80bf63f629d`.
- Previously frozen panel `diag-rate-bridge-v1-maskgamma-5e557f8ada07`; receipt SHA256 `35e5490cc846ef2baedfe48134b8e23e1b0eda2d7dab9ba85a36168559e82e04`.
- Native `reward_lif.cpp`: `e7dbb0aa8f95873036415581e94de45c237941f05642ccc90812c1be1119be37`.
- Wrapper `reward_brain.py`: `5a6d67d38d226c6792c4f11430610772894ea3e9ae9593c2d215cfd7eaa0a6d5`.
- Protocol `reward_protocol.py`: `e1a315f991debb677fca30f6e821a657135adccf032ad26054a00ed7688dc1bb`.
- Evaluator `reward_diagnostic.py`: `59feb14834813fa6793f0f97a8e4c208fd85494b383e9fa5875efe5b21189c99`.
- Runner `reward_teaching_diagnostic.py`: `b69f972f5c1e72ae5244fc4504b6cd7c5ff3fe79383d77ce3dc93ec3f56dff94`.
- New native bridge tests: `f759030dc47f6a2824540c5365ce00dbfdcd9b2ccab2794731d9713f4bf947e1`.
- Diagnostic tests: `cfbc862bfe4b786db0de76dd43817791633d982822545e7378c525a19e288488`.

The receipts retain original/previously frozen source IDs and seeds, actual graph/input hashes, h .2 ms, tau_e 500 ms, tau_r 100 ms, eta .0005, n .96 and unchanged seven criteria. They bind both governing document hashes: scientific preregistration `ab7c640f…` and implementation contract `c35484a6…`. The rate encoder file is unchanged. A later hashed source change requires a new reviewed receipt, not reuse of these identities.

## Mathematical and numerical implementation

`RateBridge` is shared by the electrical engine and a private deterministic signal-replay seam. It keeps double rates, eligibility and the within-trial gain accumulator. Actual KC spikes and compartment-mean actual DAN spikes enter at the left boundary; prior eligibility excludes that step's new impulses. The native class calculates exact interval coefficients, applies the stable direct Q integral, then advances R/E. It records the true separate positive/negative areas including their equal shared cross contribution. The recorded area subtraction does not drive the gain update. There is no extra timestep factor or slow weight-tracking state.

The appended double configuration preserves exact Python h/tau/eta rather than promoting legacy float scalars. Public neural dt stays .2 ms; the private helper varies only the signal integration grid. Actual neural spike-bin indices align with helper event time index*h. Existing LIF delay, refractory release, random draws and transmission ordering remain unchanged.

Double gain accumulation survives repeated sub-ULP updates; transmission and saved checkpoints use float32 publications. The accumulator is initialized from the checkpoint only once per call. Tail processing uses post-final-advance state, analytically integrates the no-new-event continuation once, publishes the checkpoint and discards learning states/remainder at return. Frozen execution uses zero effective eta and preserves gain bytes. The tests verify checkpoint cloning/roundtrip restarts signals and has no hidden double remainder. Excluded edges retain their gains and continue transmitting.

The generic numeric domain explicitly rejects near-equal reciprocals, unsupported small/extreme timescales, invalid interval/tail coefficients and overflow-prone scaled intermediate/grouped products. Bridge bounds must be exactly representable in float32, preventing disagreement between declared bounds, the native float ABI and saved publications. These are supported-domain restrictions; they do not select new production parameters. Event-mode validation/arithmetic retains its prior behavior.

## Tail, bounds and diagnostic accounting

Bridge recording has a distinct mode/layout and double R/E/Q, true-integral, attempted, accumulator-applied and float-publication fields. Event-only rule arrays are not mislabeled as bridge applied changes. The runner explicitly dispatches on bridge mode, retains the new arrays and actual gain vectors, and writes their layout/configuration alongside the artifact. The old event-attribution tool rejects bridge inputs before reading/writing incompatible arrays.

The analytic tail is a fourth, named phase rather than being inserted into the final electrical bin. The phase evaluator validates shape, finite fields, nonnegative integer bound counts, decomposition and published-checkpoint reconciliation. Both panel and cumulative rows include electrical plus tail observations; cumulative artifacts retain corresponding integral/tail arrays and checkpoints. Final eligible gains are independently checked. Bound observations include double proposals and float32 publication contacts, so rounding to a bound cannot evade the zero-bound gate. Frozen dwelling and tail observations are separately counted.

Identity creation includes learning rule, fixed configuration, normalization, tail/reset policy, layout and governing document hashes. Source hashes are checked after execution. Source-hashed native caching and aligned ctypes signatures avoid stale ABI reuse. Complete-matrix/cumulative validation and original scientific thresholds remain intact. Bridge repeat checks compare every returned numerical array rather than only final gains, while sensory equality remains the same actual spike-bin check.

## Tests that can falsify the implementation

The released tests use independent closed timing-kernel pair sums and continuous impulse-response quadrature rather than relying solely on a second copy of the native recurrence. The shared compiled helper permits 0.1/.2/.4 ms signal-grid comparisons; actual tiny native circuits separately verify the electrical-to-learning connection, populations, publication and transmission.

Coverage includes signed .2/1/5/20/50/100/500/1000 ms pairs and coincidence, populations 1/2/22 and partial DAN activity, mixed histories, onset exclusion and shifts, silent endpoint extension, lower/upper clipping and recovery, true positive/negative integrals, publication-only tail contact, frozen dwelling, empty/masked support, mixed compartments and edge permutations, recording parity, checkpoint reset and actual masked transmission. The predeclared short/long ratio test and 50/500 ms nonvanishing floors are present.

The decisive sub-ULP regression now uses K at 0, DAN at .2 ms and a 400 ms electrical interval. It asserts the exact float32 checkpoint predicted by the independent pair oracle while its analytic tail is below half an ULP; a float-reset-per-step implementation cannot pass by applying one large tail. This directly matches the independently reproduced arithmetic failure in the reference audit.

The six-neuron CLI integration test executes the actual 64+16 orchestration without loading the full graph, checks immutable preregistration, tail phases/counts, retained arrays and layout dispatch. It is a pipeline test, not full-CNS mechanism evidence. Generalized malformed recording tests cover missing fields, shape, nonfiniteness, negative/fractional counts, decomposition, checkpoint disagreement, layout and rule mismatch.

## Findings resolved and review corrections

The concrete in-progress issues addressed before release were insufficient scaled/intermediate numeric-domain validation and float64-declared bounds being changed by the native float ABI. The initial short sub-ULP test also had a coverage weakness: a dominant tail could hide lost electrical accumulation. These were corrected without changing the fixed candidate.

The initial tests failing because the new API did not exist are evidence of a new implementation contract, not dozens of independently discovered legacy bugs. Do not count each absent-API parameterization as a separate scientific defect.

One reviewer suggestion was retracted: I initially claimed that `pytest.approx(abs=...)` retained a default relative tolerance. Inspecting the installed `_pytest/python_api.py:514–518` showed it uses absolute-only tolerance when abs is specified without rel. The prior assertions were already absolute-only. This was a corrected review mistake, not an implementation defect; the separate tail-dominance coverage finding remains valid.

## Verification and scientific boundaries

Read the actual final receipts: 477 focused tests passed; `make verify` passed 804 pytest tests, Ruff, 66 Vitest tests and the production build. Two existing Python deprecation warnings are disclosed. No routine tests were rerun by this reviewer. The worker supplied final code-release/verification status directly; its separate SDD report file was not yet present when this verdict was issued, and is not represented as read.

The independently authored reference audit, copied unchanged into evidence with provenance, passed 28 mathematical checks and retained generic-domain failures. That earlier authorized work was reference-only and imported no production circuit. It supports independent mathematical review; it does not replace the native/component tests or operational panels.

No frontend source changed in this internal diagnostic task; existing frontend tests/build passed. User-facing mechanism/result presentation and browser evidence remain the later product task. No browser, sports refresh, promotion or push occurred in this review.

The engineered 100/500 ms bridge predates the raw held-out failure and is not tuned to it. Passing its numerical contract proves an implementation of that hypothesis, not biological dopamine kinetics, cue-specific acquisition or reversal. The corrected raw-event held-out failure remains valid evidence. The original and previously frozen operational panels must still pass separately before conditioning; the previously frozen panel is not newly unseen data after its raw-event result became known.

## Subsequent audit-storage follow-up

After the numerical/code verdict, root began original `1b233bc75647` with the reviewed sources frozen. The worker's full `task-2b-report.md` then became available and was read completely; it agrees with the released hashes and logs above. It also discloses a forward integration gap: repeat fingerprints were compared in memory but not persisted, summary lacked NPZ/layout digests, and only the first cue's full sampled sensory traces were retained. This limits independent later verification of stored replay/noise evidence; it is not evidence of altered neural dynamics or incorrect bridge mathematics.

Root approved a bridge-only storage follow-up **after the current run completes**: persist expected/actual numerical replay fingerprints, sensory-bin arrays for each trial, and trial/layout artifact digests. Preserve the current result and mark the unrun `5e557f8ada07` receipt superseded. A new runner hash requires new original and previously frozen receipts and an independent review of the storage changes before those replacements execute. Require equality of every shared retained array across the old/new original recording revisions. No dynamics, parameters or criteria may change in that patch.

The numerical-correctness PASS above stands for its exact source identity. This addendum does not approve the prospective storage patch or superseded held-out execution. Independent artifact-audit completeness will be assessed on the new recording identity. Neither the in-progress original result nor any future replacement result is inferred from component verification.

## Final storage follow-up review

**Storage-compliance verdict: PASS. Code-quality verdict: PASS.** Reviewed the released storage-only patch, the complete worker-report additions, both complete new receipts and the latest actual focused/full-verify logs. No blocking findings. This section supersedes the prospective-patch restriction immediately above for the exact new identities below, while preserving the superseded receipt and earlier result history.

- Runner SHA256 `d18df419fe4c78001019d6feadff5b6c37df2de69f7e278d46d3cf02bc539598`; diagnostic-test SHA256 `0b9909b78ce50ab78fb3e639f70d031c5a3b9a8da62c1eb3a26dc155b3b98328`.
- Original `diag-rate-bridge-v1-maskgamma-de050d773763`; audit receipt SHA256 `61136a8326bc9332c2cd9bb6ff7241a22d253b07e12872a329e60817f0dbed7e`.
- Previously frozen panel `diag-rate-bridge-v1-maskgamma-dea14759e9ca`; audit receipt SHA256 `9892d0cc9fc0527b0f6ea4f8a18a376d5161ffb833a05e1653288754b6260834`.

All six current source hashes matched each new receipt. Native, wrapper, protocol, encoder and evaluator are byte-identical to the numerical release. Both new output directories were absent at the review check. Selectors, seeds, equations, effective parameters, event scheduling, random draws, criteria and pre-existing retained-array computations are unchanged. The patch adds storage after existing computations and changes only the runner/tiny-CLI test.

Every one of the 64 single-trial rows now retains its actual sensory-bin matrix under an unambiguous game/seed-set/condition key. This permits a pure artifact reader to recompute each row's sensory hash and independently compare all four conditions in every one of the 16 game/seed-set groups. The four replay conditions retain separate original and repeat dictionaries containing dtype, shape and SHA256 for every returned numerical array, including bridge instrumentation. A pure reader can validate the expected schema and compare those complete fingerprint dictionaries, instead of trusting a stored boolean. This is persisted evidence of the performed deterministic replay, not a new neural rerun or recovery of full arrays from digests.

`summary.artifacts` now binds byte lengths and SHA256 for the completed `trials.npz`, `recording-layout.json` and `replay-evidence.json`. The summary is written after those files. Numerical phases/tail/gains remain available in the NPZ, with explicit layout/configuration. The strengthened six-neuron CLI test independently reopens the files, checks all three digests/lengths, all four replay fingerprints and all 64 sensory matrices. Its new failing regression reflected missing storage fields, not an altered biological equation.

The final receipts show 477 focused tests and the full gate of 804 pytest tests, 66 Vitest tests, Ruff and build passing after this patch. No routine rerun or circuit execution was performed by the reviewer. Root may execute the new original, compare **every shared retained array** with `1b233bc75647`, and then run the previously frozen second panel subject to the original gate. Neither the required shared-array equality nor the second-panel result is claimed before measurement. Conditioning remains dependent on the separate scientific gates.
