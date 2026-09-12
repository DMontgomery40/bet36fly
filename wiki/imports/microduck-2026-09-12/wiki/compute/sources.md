---
type: source-ledger
updated: 2026-09-12
status: research-synthesis
---

# Compute source ledger

Retrieved 2026-09-12 UTC (2026-09-11 America/Denver). Publication dates below are publisher-visible dates or explicit last-update dates; unknown means no exact date established, not the retrieval date. All sources are primary provider documentation, a regulatory filing, or the publisher package registry. No browser login, account inspection, launch, or training validation was performed.

| Source | Published / updated | Evidence and limit |
| --- | --- | --- |
| [NVIDIA to Acquire Hugging Face](https://blogs.nvidia.com/blog/nvidia-to-acquire-hugging-face/) | 2026-09-03 | Confirmed public acquisition agreement; ecosystem commitments, not closing. |
| [NVIDIA Form 8-K September 2 event](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000078/nvda-20260902.htm) | 2026-09-03 | Definitive agreement September 2; expected H1 2027 close subject to approvals. Strongest transaction-stage evidence. |
| [Hugging Face Jobs](https://huggingface.co/docs/hub/jobs) | Unknown; rolling documentation | CLI, Python and HTTP execution; seconds wording conflicts with dedicated billing page. |
| [Jobs Quickstart](https://huggingface.co/docs/hub/jobs-quickstart) | Unknown; rolling documentation | Signed-in web Jobs page can create/manage; CLI auth and timeout; Ctrl+C detaches logs. |
| [Jobs Pricing and Billing](https://huggingface.co/docs/hub/jobs-pricing) | Unknown; rolling documentation | Public GPU rate table; positive credit balance; minute billing; namespace attribution. Mutable pricing. |
| [Authentication reference](https://huggingface.co/docs/huggingface_hub/package_reference/authentication) | Unknown; rolling documentation | Browser device-code OAuth is supported default when no token supplied; personal token alternative. |
| [CLI reference](https://huggingface.co/docs/huggingface_hub/package_reference/cli) | Unknown; rolling documentation | whoami and CLI auth commands; installed version may differ. |
| [Jobs Configuration](https://huggingface.co/docs/hub/jobs-configuration) | Unknown; rolling documentation | Volumes, namespace, secret passing and authenticated exposed HTTP ports; not proof of WebRTC support. |
| [Manage Jobs](https://huggingface.co/docs/hub/jobs-manage) | Unknown; rolling documentation | Ephemeral filesystem; durable outputs and retained logs; completion is not persistence proof. |
| [Run and manage Jobs](https://huggingface.co/docs/huggingface_hub/guides/jobs) | Unknown; rolling documentation | Python run_job and UV execution; multiple workload types. |
| [Spaces Overview](https://huggingface.co/docs/hub/spaces-overview) | Unknown; rolling documentation | Gradio, Docker, static HTML application surfaces. |
| [huggingface_hub PyPI](https://pypi.org/project/huggingface-hub/) | 2026-09-10 | Latest release 1.31.0; artifact publication record, not local installed version. |
| [Brev Quickstart](https://docs.nvidia.com/brev/getting-started/quickstart) | Unknown; rolling documentation | Multi-provider GPU machines; browser console and browser-based CLI login. |
| [Brev Console Reference](https://docs.nvidia.com/brev/guides/console-reference) | Unknown; rolling documentation | Create/access console; billing, stop/storage distinction and credit exhaustion lifecycle. |
| [Brev Launchables](https://docs.nvidia.com/brev/concepts/launchables) | Unknown; rolling documentation | Hardware/software/source/network recipes, runtime modes, deploy-time secret scope. |
| [Brev Search and Discovery](https://docs.nvidia.com/brev/cli/search-discovery) | Unknown; rolling documentation | Read-only discovery command, rates and filters; output examples are not live quotes. |
| [Brev GPU Types](https://docs.nvidia.com/brev/reference/gpu-types) | 2026-04-06 | Catalog updated timestamp; some memory labels differ from other provider specs. Verify actual allocation. |
| [Deploy Halos on NVIDIA Brev](https://docs.nvidia.com/halos-outside-in/latest/getting-started/brev-launchable.html) | Unknown; rolling documentation | Documented Isaac Sim SIL notebook deployment precedent; not a connectome template. |
| [Isaac Sim Requirements](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html) | 2026-09-10 | A100/H100 excluded without RT cores; Linux container and training memory requirements. |
| [Isaac Sim Livestream Clients](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/manual_livestream_clients.html) | Unknown; rolling documentation | NVENC, native/web viewer, media endpoints security requirements and A100 limitation. |

## Contradictions and open verification

- The acquisition is announced, with closing expected later; abbreviated media headlines do not establish completed ownership. See [ownership](ownership.md).
- Jobs overview says seconds; pricing specifies minutes. Use the dedicated billing page for planning and check actual billing before spending.
- Brev catalog memory labels can differ from advertised physical-card capacities. An instance quote and reported allocation must settle resource sizing.
- Rolling docs may describe features absent from installed clients. The registry version does not establish the Mac installation.
- Web launch is documented. Exact account permission, credit, regional availability, simulator packaging and authenticated live robot playback remain untested.
- No evidence found here establishes shared NVIDIA/HF identities or transferable balances. Treat separate documented billing surfaces explicitly.

## Source quality and maintenance

SEC is the strongest source for agreement status and closing conditions. Corporate announcements establish announced intent. Product docs establish supported interfaces but are not operational receipts. Price pages are snapshots, and catalog examples are lower-confidence estimates than a selected launch quote. This ledger stores concise derived evidence, not copied full articles. Machine-readable provenance is in [sources.json](sources.json).

[Compute index](index.md) · [Research wiki](../index.md).
