---
type: concept
updated: 2026-09-12
status: research-synthesis
---

# GPU selection: learning, physics, rendering, and streaming

A connectome robot has several compute demands: neural-state updates, plasticity or gradient computation, physics, sensors, image rendering, and video transport. They need not share a bottleneck. Choosing the largest training GPU before identifying the simulator can buy an incompatible machine.

## Isaac Sim imposes a compatibility boundary

The current Isaac Sim requirements explicitly exclude GPUs without RT cores, naming A100 and H100, and state that the container is supported on Linux. Isaac Lab training adds memory demands beyond the base simulator. Therefore an A100's excellent numerical-compute specification does not establish support for an Isaac Sim embodied experiment. [Isaac Sim requirements, updated September 10, 2026](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html).

For streaming, NVIDIA requires NVENC and explicitly excludes A100. Current documentation describes both a native WebRTC client and a Docker Compose web viewer for Chromium browsers. It also says the underlying streaming endpoints lack authentication/encryption and should be protected and network-restricted. These are actual deployment requirements, not optional polish. A Brev authenticated HTTP link alone does not prove the media path is secured or reachable. [Livestream clients](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/manual_livestream_clients.html).

**Candidate:** benchmark an appropriately provisioned L40S or RTX PRO workstation/server-class GPU for combined simulation, controller, and visible inspection. This is a compatibility-led shortlist, not a certified SKU recommendation. For a different simulator with no RTX dependency, A100/H200 could remain candidates for batched numerical training. Validate against the selected simulator's own pinned release.

## Hugging Face Jobs price snapshot

Public USD/hour list prices retrieved September 12, 2026 UTC. These are documentation prices, not a live account quote or an availability guarantee. Memory is advertised GPU memory; multi-GPU totals are not one automatically pooled address space.

| Jobs hardware | GPU memory | USD/hour |
| --- | ---: | ---: |
| T4 small | 16 GB | 0.40 |
| L4, one GPU | 24 GB | 0.80 |
| A10G small | 24 GB | 1.00 |
| L40S, one GPU | 48 GB | 1.80 |
| A100 large | 80 GB | 2.50 |
| RTX PRO 6000, one GPU | 96 GB | 2.75 |
| H200, one GPU | 141 GB | 5.00 |
| Four A100 | 320 GB total | 10.00 |
| Eight H200 | 1128 GB total | 40.00 |

The dedicated pricing page bills starting/running time by the minute, adds $0.01/hour per Job for exposed ports, and documents a default 30-minute timeout. Positive credit balance supplies eligibility. Confirm hardware/rates using `hf jobs hardware` or `GET /api/jobs/hardware` before launch. [Jobs pricing](https://huggingface.co/docs/hub/jobs-pricing).

The general Jobs landing page uses seconds-based wording, which conflicts with the dedicated billing page. Planning here uses the more specific billing statement; exact invoice rounding remains a preflight question. [Jobs landing page](https://huggingface.co/docs/hub/jobs).

## Brev rates require a selected provider and instance

Brev's public discovery documentation shows price sorting and JSON output. Its sample dollar values are illustrative command output; this wiki does not pass them off as today's quote. Candidate discovery could use `brev search --gpu-name L40S --sort price --json`, with no pipe to `brev create`. Capture the actual provider, region, CPU/RAM, disk, stop support, and price. [Search and discovery](https://docs.nvidia.com/brev/cli/search-discovery).

Brev's catalog has approximate memory labels that differ from HF and hardware naming conventions, including L40S listed as 44 GB. Do not silently normalize that to a guaranteed allocation: record the instance's reported memory in future validation. [GPU catalog](https://docs.nvidia.com/brev/reference/gpu-types).

## What to measure before scaling

Measure steps/second at a fixed environment count, peak device memory, physics versus controller time, GPU utilization, and checkpoint overhead. Record whether video capture changes throughput. A recurrent sparse neural model may be limited by memory movement or many small operations; actual performance is an open question here. Doubling devices can add coordination cost without doubling useful experience.

[Jobs](hugging-face.md) · [Brev](brev.md) · [Run contract](run-contract.md) · [Compute index](index.md).
