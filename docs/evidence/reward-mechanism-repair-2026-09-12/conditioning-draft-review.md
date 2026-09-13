# Retained conditioning draft review — September 13 UTC

The paused Task 3 draft is **not ready for integration or execution**. A bounded
review of its pure functions reproduced three validation gaps below. No native
engine or conditioning circuit ran; the draft remains outside production and
pytest discovery. The mechanism entry gate is still failed.

Reviewed draft SHA256:
`4f30fd52cfa7de8350876961465e66cb6e131859799be8f87fcd320310eb3903`.
The authoritative expectations are the frozen
[conditioning addendum](conditioning-prerun-addendum.md) and the retained
`output/collaboration/reward-mechanism-repair/task3-test-oracles.md`.

| Gap | Reproduced counterexamples | Required broader correction before integration |
| --- | --- | --- |
| Call-plan validation checks counts but not the complete contract | Removing every teaching pulse, changing every probe seed, enabling frozen plasticity, changing reversal cue windows, or assigning every replay to one unrelated existing call all pass validation | Compare every ordered call, schedule, pulse, seed, checkpoint and exact replay identity against the frozen plan; mutation tests across all fields and call families |
| Acquisition scoring trusts endpoint/bound flags without enforcing gain invariants | A valid numerical fixture still passes after frozen gains change by 0.01, or paired gains fall below the fixed 0.5 lower bound with `bound_hits=0` | Check frozen gain bytes and final eligible bounds independently, in addition to transient electrical/tail evidence; cover both bounds and all panels/arms |
| Numerical replay comparison can accept absent evidence | Comparing two empty dictionaries returns passed | Require the complete declared numerical result schema before byte comparisons; missing/extra/type/shape/nonfinite family tests |

The unchanged generated plan has 1,632 calls and the expected stage counts. A
valid synthetic acquisition fixture passes before each damaging mutation. This
distinguishes an evaluator that accepts invalid evidence from one that simply
rejects everything. The findings concern unfinished draft software, not recorded
scientific outcomes.

The draft also lacks the runner's durable attempt accounting, probe identity,
checkpoint isolation and gate-entry checks described in its design. A correct
call total cannot substitute for those checks. Do not expose a future conditioning
pass in the UI by trusting this draft's `all_passed` field alone.

The read-only probe and complete result are retained at
`output/collaboration/reward-mechanism-repair/review_conditioning_draft.py` and
`conditioning-draft-review.json` in that directory. Run with
`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python output/collaboration/reward-mechanism-repair/review_conditioning_draft.py`.
This is review evidence, not a passing conditioning test suite. No draft code,
frozen protocol, diagnostic threshold or saved circuit artifact was changed.
