---
type: index
updated: 2026-09-12
status: research-synthesis
---

# Compute ecosystem for an embodied connectome

Status: research synthesis, checked 2026-09-11 America/Denver / 2026-09-12 UTC. No account login, paid resource, training run, or remote viewer was exercised.

The useful distinction is between **a place to store the experiment**, **a place to execute it**, and **a place to watch its body**. Hugging Face Hub, Jobs, Spaces, and NVIDIA Brev can play different roles in one experiment. Their corporate relationship does not remove those operational boundaries.

## Read this section as a connected argument

1. [NVIDIA and Hugging Face ownership](ownership.md) resolves the recent acquisition announcement and what it does not establish about accounts or billing.
2. [Hugging Face Jobs and Spaces](hugging-face.md) explains authenticated batch execution, web launch, and publication surfaces.
3. [NVIDIA Brev](brev.md) explains browser-accessible GPU workspaces and shareable launch recipes.
4. [GPU selection and visible simulation](gpu-selection.md) separates numerical training from rendering and streaming compatibility.
5. [Reproducible runs and bounded spending](run-contract.md) defines the evidence a future execution must produce.
6. [Source ledger](sources.md) records provenance, dates, contradictions, and remaining verification.

## Both duck and fly are GPU-training subjects

The project intent includes training the duck body/controller and training or adapting the fly connectome model on real NVIDIA GPUs, while giving the fly an embodied interface. The provider choice does not settle whether they train jointly, train in stages, share a device, or use separate runs. Training compute is also distinct from the runtime computer and authority used when the physical robot acts. These are architecture decisions to resolve through the broader research, not exclusions imposed by this compute section.

## Working architecture, not a deployment claim

For a first embodied prototype, the strongest candidate architecture is a pinned simulation/controller repository, durable checkpoint storage, one compatible GPU workspace for interactive inspection, and bounded Jobs for independently reproducible experiments. This is an engineering synthesis of the provider capabilities below; it has not been benchmarked for this repository.

| Need | Candidate surface | Why it earns a place |
| --- | --- | --- |
| Review code, model, data revisions | Hugging Face Hub and source Git repository | Stable artifact identities can connect experiments to results |
| Run a finite controller experiment | Hugging Face Jobs | Command/image/hardware execution with timeout and inspectable status |
| Watch and debug the robot | Brev plus an appropriate simulation viewer | Flexible GPU machine, launch recipes, exposed services |
| Publish an interactive report or replay | Hugging Face Spaces | Application hosting rather than an implicit training scheduler |

The [Jobs overview](https://huggingface.co/docs/hub/jobs), [Spaces overview](https://huggingface.co/docs/hub/spaces-overview), and [Brev quickstart](https://docs.nvidia.com/brev/getting-started/quickstart) establish these product roles. They do not establish that a connectome model is differentiable, that its sparse operations saturate a GPU, or that the robot learns. Those remain experiment questions.

The decision order is: define the embodiment and learning loop, establish simulator compatibility, measure memory and throughput, then choose hardware and a spending envelope. A larger accelerator cannot repair an ill-defined sensor-to-neuron mapping or reward.

[Return to the research wiki](../index.md).
