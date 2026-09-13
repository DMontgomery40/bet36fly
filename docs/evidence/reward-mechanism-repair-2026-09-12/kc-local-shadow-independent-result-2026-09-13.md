# Independent KC-local shadow result

September 13, 2026. The independent numerical audit passes all 32 rows; the
candidate remains **rejected by all four home guards**. The four away guard
eight-tuples are zero and pass. This is an offline rejection result, not
circuit qualification or demonstrated learning.

Root dispatched exactly one audit of `kc-local-shadow-6734494c82c54702ead0`
after its one completed producer run. The frozen auditor was unchanged. Its
direct child exited zero and was reaped after 3.303564 seconds under a
120-second external watchdog; its internal elapsed time was 3.113699 seconds.
BLAS threads were fixed to one. No retry, fit, native call, network request or
additional candidate evaluation occurred.

Independent rational event grouping and original pinned source functions
reproduced all 1,560,576 source-frame counts exactly and all 6,762,496 C/L/a/I
state values within the declared tolerance. The maximum state error was
1.33227e-15; the maximum of 1,690,624 susceptibility comparisons was
1.22125e-15. Every row covered all 4,064 KCs and all twelve source updates,
including the initial and final snapshots. Raw event totals matched exactly;
maximum weighted-total error was 7.10543e-15.

The independent complete impulse-pair kernel reproduced all 8,866 edges in
each row. Maximum final and electrical double-gain error was 9.32587e-15,
below the frozen absolute tolerance of 1e-11. All 567,424 retained final and
electrical float32 gain values matched bit-for-bit. There were no rounding
ambiguities. Independently summed endpoint filter states also matched; the
largest KC and DAN errors were 1.61648e-13 and 2.75335e-13 respectively, within
the frozen `rtol=atol=1e-12` comparison.

All original masks were retained: 4,184 home and 3,239 away edges eligible,
1,443 away edges excluded and exactly one. All per-phase publication counts
were 150/850/500/1 for eligible edges. Producer bound-contact observations
were zero across every row, so the unclipped pair proof applied to the full
matrix. Unrecorded intermediate gain vectors were not independently compared.

The exact integer guards used the unchanged `9*S² <= 16*Q` test on eight
float32 trial totals in units of 2^-24. Independent and producer integer
tuples agree in every cell. Display values below are sums of eligible edge
gain changes, with the sign retained; the test compares absolute mean with
half the sample standard deviation.

| Panel / noise | Home mean | Half sample SD | Home result | Away result |
|---|---:|---:|---|---|
| Original / base | -0.1856716052 | 0.1200069417 | Fail | Pass, eight zeros |
| Original / alternate | -0.1399182975 | 0.1122852360 | Fail | Pass, eight zeros |
| Second / base | -0.3604103625 | 0.2796574832 | Fail | Pass, eight zeros |
| Second / alternate | -0.1556747258 | 0.0873378697 | Fail | Pass, eight zeros |

The audit verified all 106 frozen source/input bindings (219,720,936 bytes)
before and after calculation and all 68 consumed producer-file snapshots.
A final read-only closeout rehashed those inventories and inspected all 32
row results and all 128 saved endpoint arrays; no input or producer byte
changed. Original and copied evidence remains preserved.

The [audit JSON](kc-local-shadow-independent-audit-2026-09-13/audit.json)
contains all exact guard tuples and inventories;
[comparison arrays](kc-local-shadow-independent-audit-2026-09-13/comparison.npz)
retain independent final and electrical endpoints for every row. The
[external execution receipt](kc-local-shadow-independent-audit-execution-2026-09-13/execution.json)
and [stdout](kc-local-shadow-independent-audit-execution-2026-09-13/stdout.txt)
preserve the single attempt. The preparation's 34 synthetic tests and
root's repository gate are distinct from this actual saved-result audit.
