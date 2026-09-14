---
type: cell-evidence
updated: 2026-09-14
status: metadata-verified-coordinates-not-retrieved
---
# Locating dopamine contacts around KC→MBON synapses

**Scope:** the detailed experiment claims below concern the legacy PPL101/MBON11 and PAM12/MBON09 investigation. Its failed or unresolved results remain unchanged. The separate PAM08/PAM01 circuit now has [qualified controlled conditioning](../associative-learning.md); that does not establish these molecular transfers or local dopamine exposure models.

The current simulator assigns one mean DAN signal to every eligible edge in
each teaching channel. To investigate a more local coupling, the relevant
anatomical question is where a DAN's processes and contacts lie relative to
the particular KC→MBON synapses being modified. A body ID, soma side or whole
body contact count does not answer that question.

## The specific home cells

Both selected PPL101 bodies contact both selected MBON11 bodies in the locked
MaleCNS graph. The counts below are aggregate anatomical contacts, not measured
dopamine exposure at KC→MBON synapses.

| Presynaptic DAN body | Postsynaptic MBON body | Contacts |
| --- | --- | ---: |
| PPL101 11327 | MBON11 10704 | 444 |
| PPL101 11327 | MBON11 11402 | 781 |
| PPL101 11900 | MBON11 10704 | 476 |
| PPL101 11900 | MBON11 11402 | 610 |

The [complete selected-DAN audit](../../docs/evidence/reward-mechanism-repair-2026-09-12/dopamine-signal-sources-resumed.md)
checks these pairs against the original release. Among 3,623 eligible home
KCs, 3,049 have a direct pair from at least one selected PPL101, and 574 have
none. The absence of a direct pair does not establish the absence of diffusible
dopamine. All 4,184 home plastic edges remain eligible; this table supplies no
reason to delete them or filter them by KC class.

## What the released location files contain

The September 13 [official-file inspection](../../docs/evidence/reward-mechanism-repair-2026-09-12/localization-range-report-2026-09-13.md)
read complete Feather footers without decoding synapse rows. Both files
returned actual partial-content responses. The observed columns provide a
concrete route to an eventual cell-specific selection:

| Released table | Relevant observed fields | Required use |
| --- | --- | --- |
| Synapse points | `body`, `x`, `y`, `z`, `kind`, confidence, region fields, `point_id` | Locate a body's annotated sites and distinguish presynaptic from postsynaptic points after decoding categorical values |
| Synapse partners | `body_pre`, `body_post`, both xyz triples, both confidences, `primary_post` | Select outgoing PPL101 pairs and incoming MBON11 pairs; retain the actual presynaptic KC identity for each KC→MBON site |

The points schema has 41 fields and 5,455 record batches; partners has 11 fields
and 4,759 batches. The points dataframe index is `point_id`, while partners
declares a positional RangeIndex. Neither inspected index selects a body.
No per-batch body ranges, body sort contract or body-selection index were
found in these footers. Consequently a first-batch example cannot stand in
for complete coverage of the four bodies or the selected KC population.
The report pins exact object generations, ETags and received-byte hashes.

A separate [first-batch metadata check](../../docs/evidence/reward-mechanism-repair-2026-09-12/localization-batch-metadata-report-2026-09-13.md)
verified 65,536 rows in each first batch and located its compressed body-ID
buffers. It read 2,720 metadata bytes plus the official format schema, with
version preconditions on both files. The body values and coordinates remain
unread. These first-batch buffer sizes cannot establish a global scan cost
or an ordering that permits skipping other batches.

The subsequent [complete-metadata v1 attempt](../../docs/evidence/reward-mechanism-repair-2026-09-12/partners-metadata-v1-result-2026-09-13.md)
stopped on a client header-compatibility bug before reading a payload. Its
failure is preserved. The separately reviewed [complete v2 metadata inventory](../../docs/evidence/reward-mechanism-repair-2026-09-12/partners-metadata-v2-result-2026-09-13.md)
finished all 4,759 batch messages in 815.86 seconds. Every declared body-column
range is now known: `body_pre` totals 363,074,510 bytes and `body_post` totals
1,650,277,453 bytes, or **2,013,351,963 unread buffer bytes** before future HTTP
overhead. All batches declare LZ4_FRAME compression and together declare
311,833,243 rows. This is a complete metadata count, not an extrapolation from
one batch. No body IDs, coordinates or local exposure model were retrieved.

## A complete home contact selection

The [offline selection synthesis](../../docs/evidence/reward-mechanism-repair-2026-09-12/localization-next-decision-synthesis-2026-09-13.md)
shows that the partners table alone can support the narrower home contact
geometry question. The complete selection is `body_pre in {11327, 11900} OR
body_post in {10704, 11402}`: all selected PPL101 outputs and all selected
MBON11 inputs, with KCs identified afterwards using the locked annotations.
Both endpoint coordinates remain available for each contact. This permits
comparison with KC→MBON11 sites without selecting a distance cutoff or
converting proximity into dopamine exposure.

Retain polyadic partner rows for contact accounting. A coordinate-unique
`(body_pre,x_pre,y_pre,z_pre)` endpoint is not an authoritative point ID;
multiple partner rows do not necessarily mean independent release sites.
The points table adds point IDs and richer site/region information when those
become necessary. Neither entire object is a prerequisite for this narrower
question if a complete, version-bound selection can be obtained.

No such selection has been retrieved. A separate [IPv4 transport check](../../docs/evidence/reward-mechanism-repair-2026-09-12/localization-neuprint-ipv4-report-2026-09-13.md)
completed TLS but received no complete HTTP response before the active deadline;
the attempt ended after 14.005 seconds. It did not establish authentication requirements or live dataset
availability. The direct range route has now retrieved all 3,045,760 metadata
payload bytes and established the complete body-column cost above. A body
predicate scan or selected-coordinate retrieval still requires its own finite
plan. Neither has run.

## What remains to be established

A useful location export must cover all selected DAN outputs and KC inputs
to the selected MBONs under the declared confidence filter. It must reconcile
body IDs and aggregate pairs with the locked graph, decode categorical values,
respect the released coordinate convention and distinguish missing rows from
genuine absence. Region labels and distance calculations then describe spatial
relationships in this specimen.

Those relationships still do not supply a calibrated concentration, diffusion
distance, release probability or receptor response for this simulator. A
local plasticity hypothesis would need its own primary-source rationale,
explicit mathematical contract and new qualification identity. Presynaptic
spike timing, local release and receptor effects remain distinct quantities.
No exposure coefficients, distance cutoffs or hemispheric assignment have been
derived from the metadata. No local dopamine model has been run.

[Dopamine cells](dopamine.md) · [PPL101 inputs](ppl101-inputs.md) · [Cell atlas](index.md)
