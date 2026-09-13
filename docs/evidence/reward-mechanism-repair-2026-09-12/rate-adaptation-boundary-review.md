# Independent rate-adaptation runner boundary review

September 13, 2026 UTC. **PASS for the bounded input/execution/output review; no remaining actionable boundary findings at the reviewed release.** This review does not approve the mathematical equations independently or evaluate the candidate on real histories. Root still owns the final combined approval receipt, dependency rehash and frozen execution identity.

Reviewed calculator SHA256 `bad6425c1b54b0f48b04b8238be3e426372d3a8a128838bb2260f9d93b5652e8`; writer tests `daf769f31cacd3519beafcacd163de946fbc9e6c94954d940fcaba24094466c7`. The source agent owns the independent mathematical oracle and its separate numerical review.

## Findings corrected before this verdict

1. The first calculator validated class/channel grouping using `group % 2`, whereas the actual locked sample map uses `group // 4`. Read-only inspection confirmed all six populated original groups and all 32 ordered cue/noise/seed selectors. The writer corrected the mapping and added coverage of all eight labels and swapped channel families. Root independently found this mismatch too.
2. The first NPZ loader capped ZIP member sizes but could allocate from an unchecked NPY shape. A 128-byte header declaring 100,000,000 float64 elements reached the NumPy allocation path. An independent interception demonstrated the request without making that allocation. The corrected loader parses numeric headers, checks exact declared payload size and aggregate allocation limits before NumPy loading. The same probe now rejects the file before any allocation request. The writer added malformed shape, multiplication-size, missing/extra payload and valid-array families.

The initial and final allocation probes are preserved in `rate-adaptation-boundary-allocation-initial.json` and `rate-adaptation-boundary-allocation-final.json`, with the executable `rate-adaptation-boundary-allocation-probe.py`. The probe's first reporting attempt needed an output-only NumPy-scalar-to-int correction before JSON serialization; that did not change the loader counterexample or touch production files.

## Synthetic boundary verification

The focused writer suite passed **37 tests, 107 deselected**, using:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider output/collaboration/reward-mechanism-repair/test_rate_adaptation_shadow.py -k 'bound_file or npz or json_rejects or runner or manifest'
```

Coverage includes altered/missing/symlinked inputs, digest/byte-size mismatch, unsafe NPZ names/types/nonfinite values/declared shapes, nonfinite JSON, omitted/duplicated/reordered/wrong-seed selectors, changed parameters, draft or unsuccessful review status, complete ordered 32-row ledgers, output identity reuse, candidate failure, deadline interruption and input replacement. The execution fixtures explicitly substitute minimal capture metadata and a synthetic candidate; their successful summaries are not saved-history scientific results.

The final runner requires the explicit manifest digest, exact 32 ordered rows and parameters, fixed capture/receipt/sample/calculator hashes, complete input inventory and matching approval fields. Verified bytes are retained in memory; the unadapted comparator module is compiled from those bytes rather than reread from a mutable path. Its imported top-level code performs no circuit call, and only its pure shadow function is invoked. Both prior comparators are checked before each candidate attempt. The candidate receives fresh unit gains, and actual parent gains and excluded edges are checked separately.

Outputs must use one new direct child named from the first 20 manifest-hash characters; existing identities and alternate output names are rejected. Each attempt is written before candidate calculation, each completion afterward. Time checks cover input reads, input-validation rows, comparator boundaries, every 50 candidate intervals, candidate completion and final summary publication. Failure records retain completed files and counters; final input/manifest rehashing gates successful publication. Final summary uses a pending name until the post-write deadline check passes. These are cooperative checks around bounded Python/file operations, not a claim that an arbitrarily stalled operating-system I/O call can be forcibly terminated by this process.

## Actual input inspection, with candidate disabled

`rate-adaptation-boundary-input-only.json` records a separate read-only audit of the real retained inputs. It constructed an unapproved draft manifest in memory, bound all consumed files, ran `validate_capture_inputs`, safely decoded **97 NPZ archives** (sample map, 32 fine captures, 64 existing cold/continuous comparators), and rechecked every bound file afterward. All checks passed; all hashes stayed identical. The exact 32 row selectors, original 8,866-edge mapping, 2/22 DAN populations, full sample identities, binary 2,000-step rasters and comparator assignments remain preserved.

The candidate function was replaced with an assertion that forbids evaluation during that audit. `execute` was never called on real data. No candidate value, guard result or rate-adaptation contrast was calculated. No `bet36fly.reward_brain` import, native call, server, production edit, model-pointer change or commit occurred.

## Approval and document boundary

The source's numerical evidence uses two independent test files. Root confirmed that its combined approval receipt will bind both files, the oracle and contract, original/final source reviews, writer/tests and this boundary evidence in an immutable nested inventory, with actual rehashing before freeze and after execution. The runner's single independent-review slot must carry that combined receipt; the source's numerical-only status is not sufficient by itself. This review does not claim that the combined receipt already exists.

All narrative docs/wiki were previously read under this agent's original and subsequent reading receipts. This assignment read the complete current scientific preregistration, numerical reference contract and source numerical review, plus the later localization/evidence-index additions. The current handoff and corrected wiki verification wording were reread. Final read/file hashes are recorded in `rate-adaptation-boundary-reading-receipt.json`.

Ruff passed on the independent allocation probe. Root separately owns the full repository gate and the mathematical-reference verification. A passing boundary review is software evidence only; it does not establish a passing saved-history screen, teaching, recurrent learning, conditioning or reversal.
