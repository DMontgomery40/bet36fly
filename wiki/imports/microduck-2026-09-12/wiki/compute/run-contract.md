---
type: concept
updated: 2026-09-12
status: research-synthesis
---

# A reproducible, bounded compute run

This page is a proposed contract for future experiments. It turns provider capabilities into reviewable evidence; it is not a record of execution. The research phase creates no paid resources.

## The experiment identity

A run should be reconstructable from a small manifest committed before launch:

| Field | Why it matters |
| --- | --- |
| Source commit and dirty-worktree patch | Identifies the actual controller and simulator adapter |
| Container digest and dependency lock | Prevents mutable images/packages changing the experiment |
| Simulator version, scene/robot asset hashes | Defines the body and physics actually experienced |
| Connectome dataset revision and transforms | Makes neuron/edge selection and preprocessing auditable |
| Sensor encoding, action decoding, timestep | Defines the engineered interface to anatomy |
| Learning rule, optimized parameters, initialization | Distinguishes a trained readout from changed neural dynamics |
| Seeds, environment count, evaluation split | Separates sampling variation from code changes |
| Hardware/driver and precision | Supports performance and numerical comparisons |
| Artifact destination and retention | Prevents success being reduced to an ephemeral process exit |

These fields are project design recommendations. Provider metadata alone cannot describe sensor semantics, reward, or biological fidelity.

## The commercial boundary

Record the payer explicitly: HF user/organization namespace or Brev organization, plus the resource ID and selected quote. [Jobs](hugging-face.md) supports namespace billing; [Brev](brev.md) has organization credits and possible storage charges after compute stops. The [acquisition announcement](ownership.md) supplies no evidence of pooled balances.

For a proposed run, calculate:

`estimated charge = quoted compute rate × allowed billable duration + storage + exposed-service charges`

This is a planning estimate, not a hard provider-enforced dollar cap. Leave room for startup, upload, rounding, and retained storage. Do not equate a timeout with a complete account-wide budget: another instance or recurring schedule can remain active.

## A three-stage acceptance path

1. **Compatibility smoke test:** after future authorization, a short run proves imports, actual GPU/driver, simulator startup, and the body/controller loop. It should also write and reload a small checkpoint from the intended durable destination. For visible simulation, establish an authenticated working viewer and a time-stamped recording.
2. **Bounded measurement:** fixed seed set and configuration, timed training/evaluation, periodic checkpoints, machine-readable metrics, and a named cancellation path. Do not expand environment count, duration, or GPUs because a first curve looks promising.
3. **Closeout:** verify terminal state, stopped billable compute, persisted artifacts/checksums, final metrics, and which storage resources remain chargeable. Success requires evidence of the research outcome, not just a green provider status.

HF explicitly warns that Job filesystems vanish at completion and that a completed status does not prove persistence. Durable output should be checked independently; final metrics in retained logs give an additional recovery path. [Manage Jobs](https://huggingface.co/docs/hub/jobs-manage). For Brev, preserve outputs before deleting an instance, and distinguish stopping from removing billable storage. [Console reference](https://docs.nvidia.com/brev/guides/console-reference).

## Failure and restart semantics

Define what resumes: weights alone, or also optimizer state, recurrent neural state, simulator state, random number generators, and curriculum position. A restart from weights can be useful, but it is not an exact continuation. Give retry attempts new run IDs linked to the parent; otherwise repeated startup failures can hide costs or contaminate comparisons.

Keep a failed run's logs and explanation alongside successful runs. A missing checkpoint, exploding state, collapsed behavior, or poor transfer is scientific information. These are proposed reporting rules; the appropriate behavioral controls belong in the broader [research wiki](../index.md).

[GPU selection](gpu-selection.md) · [Compute index](index.md) · [Sources](sources.md).
