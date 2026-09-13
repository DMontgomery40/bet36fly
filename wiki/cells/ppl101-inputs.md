---
type: cell-detail
updated: 2026-09-13
status: anatomy-verified-mechanism-under-investigation
---
# PPL101 cells 11327 and 11900: inputs and feedback

These are the two accepted home teaching neurons. Their released identities are
`PPL101(y1ped)_R` (body 11327, retained index 1235) and
`PPL101(y1ped)_L` (body 11900, retained index 1774). “Home” is the experiment's
engineered label. It is not a natural valence assigned to these cells.

The pinned retained graph contains 7,279 directed input edges to these two
cells, comprising 39,125 contacts from 4,271 distinct presynaptic neurons. The
[complete input table](../../docs/evidence/reward-mechanism-repair-2026-09-12/ppl101-direct-inputs.csv)
retains every source body ID, annotation, contact count and modeled sign.

| Target | Incoming edges | Contacts | KC contacts | Distinct presynaptic KCs |
| --- | ---: | ---: | ---: | ---: |
| 11327, right | 3,568 | 18,029 | 11,846 | 3,068 |
| 11900, left | 3,711 | 21,096 | 12,222 | 3,100 |

KCs account for 61.52% of the combined contacts. This is a contact fraction,
not a measured current fraction or proof of which input caused a spike. There
are 3,373 distinct KCs across both input sets. These totals refer to retained
neurons; they do not include every raw fragment or non-neuronal contact in the
released reconstruction.

## Named feedback

Both selected MBON11 cells project to both PPL101 cells. Their released GABA
labels give these edges a negative fast sign in this simulator.

| Source body | Source type | Contacts to 11327 | Contacts to 11900 |
| --- | --- | ---: | ---: |
| 10704 | MBON11 | 41 | 33 |
| 11402 | MBON11 | 66 | 65 |
| 10540 | APL_R | 39 | 40 |
| 10977 | APL_L | 10 | 18 |

The selected MBON09 population adds 19 GABA-labeled contacts to each target.
Other MBON inputs have mixed modeled signs. Anatomical feedback exists; this
does not establish a prediction-error computation or learned cancellation of
cue-evoked dopamine activity.

Several large individual inputs are outside the KC population: GNG321 body
11038 contributes 295 contacts to 11327, and GNG321 body 17878 contributes 365
to 11900. SMP and AVLP types also appear among the largest individual inputs.
Their annotation names do not establish a reinforcement function. See the
[full audit](../../docs/evidence/reward-mechanism-repair-2026-09-12/ppl101-input-audit.md)
for complete class accounting and the largest input cells.

## How those contacts become modeled inputs

The fixed constructor starts with contact count × presynaptic sign × 0.1375.
The accepted KC input factor of 1.25 acts **onto KCs**; it does not directly
multiply KC→PPL101 output. The sensory input factor of zero acts onto ALPN
ports; it does not remove their outputs. PPL101 itself has target factor one.
APL output receives the accepted factor of 0.25.

The constructor zeros pure-dopamine fast outputs. Consequently the anatomical
78-contact edge from body 11900 to body 11327 remains in the inventory but
contributes zero fast weight. Anatomical class and transmitter selection differ:
the 548 contacts from annotated DAN-class cells are a subset of 763 contacts
with the pure-dopamine label. The [neurochemistry page](neurochemistry.md)
describes the limits of this presynaptic sign approximation.

These are conductance increments for events delivered while the target is
receptive. The native engine discards arrivals during refractoriness and resets
conductance and voltage after a spike. Contact-weight sums therefore do not
measure delivered activity. Actual event timing and target state are required.
Selected KC→MBON plastic gains do not directly scale an edge ending at PPL101.

## Delivered KC events on the recorded trajectories

A [saved-raster audit](../../docs/evidence/reward-mechanism-repair-2026-09-12/delivered-arrivals-resumed-report.md)
now accounts for every KC→PPL101 delayed arrival in all 32 fine recordings,
separately for both targets. An independent chronological queue reproduces all
64 target/trial count and increment arrays. This uses existing recordings, not
a new neural experiment.

| Mean per trial, both PPL101 cells | Original / base | Second / base |
| --- | ---: | ---: |
| Accepted KC conductance increments | 2,830.128 | 2,997.586 |
| Increments discarded during refractory | 479.273 | 549.519 |
| Observed PPL101 spikes | 33.125 | 35.750 |
| Gamma fraction of accepted KC increment | 86.25% | 86.31% |

These are summed simulator increments, not physical current measurements.
Gamma KCs dominate delivered KC input, while alpha/beta KCs dominate the separate
home learning residual. Those are different quantities and do not identify one
family as its cause. Only 1.88% of the second/base accepted KC increment arrives
after 300 ms; all KC arrivals finish by 308.6 ms. Filtered learning and the analytic
tail can still update gains later.

The recordings omit time rasters for inputs carrying 6,102 of 6,183 non-KC contacts
to body 11327 and 8,786 of 8,874 to body 11900. Inhibitory feedback and other
unrecorded arrivals therefore prevent reconstruction of the complete drive.
Their timing is unknown, not zero. The retained source-4420 comparison also has
substantial KC input in both noise sets but opposite gain-change signs. These
observations do not establish that input amount alone explains the sign; timing
and unrecorded inputs remain unresolved.

## What the current failure says

The verified rate bridge still fails the second panel's untaught-home guard.
An exact 33-call recording subsequently tested whether retaining pre-100 ms
filter history helped on the same spike trajectories. It made second-panel
home/base depression worse, from −0.272640 to −0.481926, and failed all four
home panel/noise groups. Those alternative gains were calculated offline and never
fed the neurons. [Frozen protocol](../../docs/evidence/reward-mechanism-repair-2026-09-12/onset-history-investigation-preregistration.md),
[complete captured result](../../docs/evidence/reward-mechanism-repair-2026-09-12/onset-history-capture-summary.json).

This rejects the proposed history-only correction under its declared test. It
does not identify a causal upstream cell, justify cutting KC contacts, or show
that biological dopamine learning cannot work. The remaining investigation
concerns the generated learning signal and its relation to cue and teaching
activity, with conditioning and reversal still unestablished.

[Dopamine populations](dopamine.md) · [Cell atlas](index.md)
