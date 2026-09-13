# Next bounded decision: home contact geometry before a local coupling law

This is an offline synthesis of already inspected sources, released metadata
and current code, written September 13, 2026 UTC. No new source lookup,
download, candidate implementation, saved-history evaluation or circuit call
was performed. The failed adaptation hypothesis and all eligibility and
qualification boundaries remain unchanged.

**The next useful data deliverable can be restricted to syn-partners. Both
large synapse objects are not prerequisites for a narrower home contact
geometry audit.** The decision is whether to obtain one complete,
version-bound selected-contact export for PPL101 and MBON11. That export
would test the anatomical basis for investigating local coupling; it would
not determine a local dopamine law or make conditioning eligible to run.

## Current mismatch and the question the export can answer

Current `reward_lif.cpp` sums actual selected DAN spikes and divides by the
channel population size. Both the event rule and rate bridge receive that
population mean. `reward_protocol.py` associates every selected KC→MBON edge
with its channel and eligibility mask; it labels the mapping a
`type-instance-compartment-proxy`. There is no per-contact spatial input to
these operations. This is the actual implementation mismatch identified in
the [source report](dopamine-signal-sources-resumed.md), not a conclusion
drawn solely from the rejected adaptation result.

Experiments motivate local signaling along KC processes. They do not establish
that whole-body counts, instance suffixes or a particular Euclidean distance
are dopamine exposure. Both PPL101 bodies contact both MBON11 bodies in the
locked graph. A concrete narrower question is: **where are those annotated
PPL101 partner contacts relative to the actual KC→MBON11 contact endpoints,
and do the two PPL101 bodies occupy distinct or overlapping spatial territories
around those contacts?**

This question can preserve the spatial coordinates and distributions without
choosing a cutoff, converting them into weights, excluding any KC or claiming
that a geometric nearest neighbor is the responsible teaching neuron.

## One object supplies the necessary contact endpoints

The observed partners schema contains
`x_pre,y_pre,z_pre,body_pre,conf_pre,x_post,y_post,z_post,body_post,conf_post,primary_post`.
The [metadata inspection](localization-batch-metadata-report-2026-09-13.md)
verified the schema and the first batch's buffer layout. The official
[syn-partners object](https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/syn-partners-male-cns-v1.0-minconf-0.5.feather)
is 6,777,179,098 bytes, generation `1780494942562468`, ETag
`58efcf712f8c4d4de5f2ad51e97def76`. Its 4,759 record batches were inventoried
from the footer. These are observed metadata facts; the body values and
coordinates have not been downloaded or decoded.

A minimal complete selection would retain the union

```text
body_pre in {11327, 11900} OR body_post in {10704, 11402}
```

from that exact object. Retaining all incoming MBON11 rows before identifying
KCs with the locked annotations makes the selection explicit and permits
aggregate validation. It yields:

- All partner rows whose presynaptic body is either selected PPL101, including
  contacts onto the selected MBONs and eligible KCs.
- All partner rows onto either selected MBON11, with the actual presynaptic
  body available to select KCs and reconcile the 4,184 home body-pair edges.
- Both endpoint coordinates and confidence values for the selected rows.

The resulting contact clouds can compare PPL101 presynaptic endpoints with
KC presynaptic endpoints at KC→MBON11 contacts. For a KC that has a direct
PPL101 partner row, they can separately compare its DAN-contact postsynaptic
endpoint with its KC→MBON11 presynaptic endpoints. Both comparisons describe
geometry. Euclidean separation is not cable distance along a KC axon, and
spatial overlap is not evidence of release at the same time or receptor
activation. PPL101→MBON11 endpoints also permit inspection of the actual
cross-body contacts without assigning hemisphere from a soma label.

All partner rows must remain available for contact counts. A polyadic
presynaptic site may appear in multiple partner rows. A coordinate key such
as `(body_pre,x_pre,y_pre,z_pre)` may be reported as a coordinate-unique
endpoint, but it is not an authoritative synapse point ID. Neither arbitrary
deduplication nor silently counting every partner row as an independent
release site is justified.

## What syn-points adds, and what neither object supplies

The larger points object is useful when the question requires authoritative
`point_id` values, an inventory of points independent of retained partner
rows, pre/post `kind`, and the additional region fields observed in its
41-column schema. Those fields are not necessary for the narrower partner
endpoint geometry question above. An equivalent verified point-rich export
could also supply them; downloading the complete points object is not itself
a scientific requirement.

Partners includes the categorical `primary_post` field. Its dictionary has
not been decoded here. Even once decoded, that postsynaptic primary annotation
must not be assumed to provide all overlapping ROIs, presynaptic territory or
a complete mushroom-body compartment hierarchy. The inspected official
download documentation describes coordinates in 8 nm voxels; the export must
preserve the raw coordinates and the exact release convention before any
physical-distance conversion.

Neither synapse table provides continuous neurite geometry, measured local
dopamine concentration, release probability, diffusion/clearance dynamics,
receptor occupancy or receptor-specific intracellular plasticity dynamics.
Annotated DAN presynaptic sites are anatomical sites, not measurements of
dopamine released by each simulated spike. Consequently a completed geometry
audit could justify considering spatially distinct signal routing, but would
not determine coefficients `a_ed`, their normalization, a diffusion radius or
a receptor law.

The already inspected primaries constrain that later decision. Cohn et al.
resolve local and background-dependent signaling; Handler et al. distinguish
downstream receptor/signaling states despite comparable release reporters
across induction timings; Cervantes-Sandoval et al. support preserving local
KC/DAN feedback. Their inspected methods and compartment limits remain as
recorded in the [source ledger](dopamine-signal-sources-resumed.md).
Yamagata et al.'s PAM-γ3 suppression result does not calibrate PPL101 or turn
the accepted positive PAM12 pulse into a natural reward signal. No new
physiology is inferred from those sources here.

## Minimum useful deliverable and the unresolved acquisition choice

The minimum useful deliverable is a **complete home contact export plus an
anatomical accounting report**. It should bind the exact object generation,
range/predicate method, all selected rows, confidence semantics, coordinate
convention and hashes. It should reconcile the selected body-pair totals
with the locked raw table and the retained graph, distinguish rows outside
the retained graph, and report missing or discrepant pairs explicitly.
Every eligible home edge, including KCs with no direct selected-PPL101 pair,
must appear in the accounting; lack of a direct pair must not disable it.
The report can retain raw point clouds and per-contact distances to each
DAN's coordinate-unique endpoints with no cutoff or exposure conversion.
This first deliverable is deliberately home-specific; it does not establish
the away channel's geometry or qualify either learning mechanism.

The unresolved acquisition choice is concrete: **obtain that complete export
through a verified selection service/export, or authorize a finite,
generation-pinned partners-only range scan after its exact compressed cost
is inventoried.** The just-completed IPv4 attempt established no working
neuPrint metadata access, so no service-selection route is currently verified.
It does not authorize retries or account access.

For the range route, the complete partners footer already identifies 4,759
metadata regions totaling 3,045,760 bytes before HTTP overhead. Reading those
metadata messages would establish each batch's two body-buffer extents and
compression description, allowing a fixed body-column transfer plan. The
compressed total is still unknown. Without a verified index or ordering,
both predicate columns must cover every batch; a sample cannot exclude the
unread batches. Coordinate/confidence buffers would then be required for
batches with selected rows, with full compressed-buffer reads where the
encoding does not support row-level reads. This could reduce transferred
columns but is not yet demonstrated to be a cheap operation. The first
batch's 373,950 body-buffer bytes cannot be extrapolated to all batches.

No such metadata inventory, body scan, full object download or further network
request is executed or authorized by this synthesis. The decision can now be
made around a precisely scoped single-object deliverable, rather than around
an assumed need for both complete objects or an unsupported local learning
equation. Source-backed release/receptor assumptions would be a separate,
explicit model decision after the anatomical result, with its own fixed
equations, parameter provenance, falsifiers and qualification identity.
