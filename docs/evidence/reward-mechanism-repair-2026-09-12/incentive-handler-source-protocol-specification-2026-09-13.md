# Handler source-protocol functional test: interpretation and data contract

2026-09-13, before any six-case model execution by this reviewer. **The public
workbook and pinned executable support a useful standalone reproduction and
functional comparison. They do not calibrate dopamine receptors or convert
MaleCNS spikes into intracellular concentrations.** Preserve separate results
for the literal driver and the primary workbook's measurement windows.

Source identity: `InsectRobotics/IncentiveCircuit`, current inspected commit
`1610c80072fe8bb59bd397e7a61f716393a509b9`. The publication-revision copies at
`98a8f85745a1426e8e5b787ceedd3f680a2b66c6` contain byte-identical `handler.py`
and `run_handler_2019.py`. Six original files and both receipts were read;
their mixed file-header/repository license notices remain unchanged.

The [eLife paper and author response](https://pmc.ncbi.nlm.nih.gov/articles/PMC8975552/)
explicitly treat the two dopamine components as abstractions, acknowledge
individual reporter-trace mismatch, and disclose selecting timing parameters
against the normalized Handler contrast. They also acknowledge implicit
scaling between KC activity and synaptic weight. Therefore a correlation on
those same conditions is an external-data reproduction, not held-out
validation of molecular kinetics. The printed equations and executable have
separate mathematical review; neither should silently substitute for the
other.

## Reporter identity and sign

| Preserved source key | Driver comparison | Biological interpretation |
| --- | --- | --- |
| `dR2` | cAMP trace; driver text says “DopR2” | cAMP is associated with DopR1/Gs in Handler. The driver receptor label is reversed. |
| `dR1` | ER-GCaMP trace; driver text says “DopR1” | ER luminal calcium loss is associated with DopR2/Gq signaling. The driver receptor label is reversed. |
| `-dR1` | Positive ER-release proxy | Negating a luminal calcium decrease makes efflux positive; it does not yield absolute cytosolic calcium. |
| `-dR1-dR2` | Algebraic combined reporter proxy | Not automatically the source's actual signed weight increment. |

[Handler's primary reporter and mutant methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC9012144/)
support the biological associations above; they do not make the executable's
`D1/D2` filtered components measured receptor occupancy. Preserve the original
array names for reproducibility and correct their explanatory labels.

In particular, the independent mathematical reviewer identifies that the
reporter combination uses an approximately absolute filter difference and
the rectified, post-update recorded weight, whereas the actual weight update
uses the signed difference and prior internal weight. A test must retain
both arrays and exhibit their distinction, rather than label a normalized
reporter contrast “final synaptic gain.” Zeroing one abstract component is
not an experimentally calibrated receptor knockout.

## Workbook contract, checked without executing the model

`Handler2019_Fig2Fig5_Data.xlsx` is 421,421 bytes, SHA256
`4db9b76cd0c41dc014c8d00a9e359bbd4165a7984095cc35d1932f9ee7f501dc`.
All four sheets and all 35,418 cells were inspected programmatically: 29,051
finite numeric literals, 205 formulas, 265 text cells and 5,897 blanks.
Every formula was independently recomputed; maximum difference from its
cached value was 3.68e-16. The
[complete inventory](incentive-handler-workbook-independent-inventory-2026-09-13.json)
records the exact sheet/data selections and per-condition values.

1. **Conditions and axes.** Retain all ISIs `[-6,-1.2,-0.6,0,0.5,6]` seconds,
   defined as DAN/US onset minus KC/CS onset. cAMP has 300 samples at
   0–29.9 s, six preparations a–f; ER-GCaMP has 200 at 0–19.9 s, seven
   preparations a–g. All 19,200 reporter samples are finite. Align KC onset
   by subtracting 10 s from cAMP time and 6 s from ER time. Do not infer
   matched animal identities across these different reporters.
2. **Original measurement.** All 78 row-2 means reproduce bit-exactly using
   closed timestamp intervals: cAMP `[10+ISI,14+ISI]` (41 samples), ER
   `[6,7]` (11 samples). These match the workbook's annotated measurement
   windows. They differ from half-open selections. Reporter values already
   represent normalized optical measurements; no photon data, sensor
   calibration or concentration conversion is supplied.
3. **Published-driver selection.** `handler.py` instead selects ER raw time
   `[-1,7]`, encompassing the 71 available samples at `[0,7]`. Its commented
   `[6,7]` is inactive. The model driver selects `[-7,1)` after alignment,
   including an interval before experimental data begin. cAMP model means
   use `[ISI,ISI+4)`. These source choices must remain visible in a literal
   reconstruction; do not silently replace them with primary windows.
4. **Normalization.** For each preparation separately, min–max normalize
   its six condition means; negate ER before normalizing. Then average
   preparations and use sample SD divided by square root of preparation
   count. The combined contrast is mean normalized ER release minus mean
   normalized cAMP, with the workbook's square-root sum-of-squared SEMs.
   Reject a zero normalization range; do not fabricate zeros. The last
   sheet uses rounded copies of row-2 primitives, so label its exact cached
   target separately from a full-precision timecourse reconstruction.
5. **Independent outcome.** The first sheet contains measured γ4 MBON
   pre/post responses and their differences. This is a different observable
   from the reporter-derived contrast. Do not treat the latter as an
   independent direct synaptic-strength measurement or double-count the
   two representations of the same reporter data.

The driver's `0.4*cAMP` and `0.8*ER` factors affect displayed traces. They
are not kinetic conversions or branch weights for the independently
normalized contrast. Its compressed plotting positions for the ±6 s cases
must not change their actual ISIs. Interpolation outside experimental time
support must be marked missing; the original right-end hold is not observed
data.

## Pre-outcome functional test specification

**Literal source reproduction:** use the already declared exact 1,001-sample
`[-7,8]` executable grid, original stimulus masks and driver parameters,
not a new 100 Hz interpretation. Compare the independently derived state
recurrence with the source at every sample under the frozen numerical
tolerances. Keep internal weight, recorded weight, reporter proxies,
condition averages and normalized contrast as separate outputs. The
[writer's preparation plan](incentive-handler-verification-plan-evidence-ui-2026-09-13.md)
owns execution identity/caps. This specification adds no model run.

**Data functional comparison:** freeze both literal-driver and
primary-workbook-window analyses before execution, with the same model
parameters and all six conditions. Report correlation, per-condition
differences, normalization ranges and individual reporter timecourses.
For a primary-window comparison, explicitly freeze the model sampling or
integration convention corresponding to each closed data window; do not
imply that endpoint inclusion makes a discrete mean a continuous integral.
No newly chosen correlation threshold or fitted scale is required here.
Exact source-software agreement can pass while physiological trace agreement
fails. A successful normalized contrast is only the named functional result.

**Experimental expectations:** the inspected γ4 preparation supports
coincidence/forward depression and stronger ER-release engagement for
backward order; exact zero responses are not warranted by noisy normalized
data. Preserve the independent reporter and MBON observations when assessing
those expectations. The source's terminal type, regional scope, stimulation
durations and preparation remain part of the claim.

**Engineering checks:** deterministic parsing, condition-order invariance,
per-preparation normalization, finite outputs, honest interpolation support,
unchanged source hashes and distinction between reporter contrast and actual
weight change are mandatory. Algebraic order, empty-input and altered-initial-
weight cases can test the implementation but are not new physiological facts.

Finally, equal external US pulses do not hold dopamine fixed in this driver:
its two filters also receive the negative previous-MBON feedback term. A
changed KC history can change both filtered drives. Thus this reproduction
does not isolate an intracellular detector under matched dopamine exposure,
as the primary release-side comparison motivates. It is still a useful
source-protocol test, with that limitation explicit. No result here can
qualify the 400 ms MaleCNS protocol, justify a home γ filter, select new
gains/timescales or establish γ1pedc/γ3 receptor transfer.
