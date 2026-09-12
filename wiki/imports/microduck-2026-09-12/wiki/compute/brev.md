---
type: concept
updated: 2026-09-12
status: research-synthesis
---

# NVIDIA Brev as a visible GPU workspace

Brev aggregates GPU instances from multiple cloud providers and supplies a browser console and CLI. For an embodied controller, its most useful role is a persistent development environment where the operator can inspect the body, sensors, and policy loop together. That role is a proposed project fit, not a completed installation. [Brev quickstart](https://docs.nvidia.com/brev/getting-started/quickstart).

## Browser launch and access

The console at [brev.nvidia.com](https://brev.nvidia.com/) supports creating GPU instances, selecting hardware/base images or Launchables, and accessing connection information. Web tunnels protect HTTP services with browser authentication. CLI port forwarding is a different route for direct programmatic access. A browser-accessible Jupyter notebook is not automatically a graphical simulator: the renderer and its streaming service must still be configured. [Console reference](https://docs.nvidia.com/brev/guides/console-reference).

`brev login` opens browser authentication; a token option exists for headless environments. The browser console is therefore a documented launch path rather than a fallback requiring local workstation CUDA. The instance still needs a compatible driver/runtime and simulator. [Quickstart](https://docs.nvidia.com/brev/getting-started/quickstart).

## What a Launchable actually captures

A Launchable combines default hardware, disk/location, software runtime, source, networking, and deploy-time parameters. Available modes include VM, one container, Docker Compose, and beta single-node Kubernetes. A default hardware choice can be changed by the deployer. Treat the Launchable as an environment recipe; pin its image and source revision separately to make a scientific run repeatable. [Launchables](https://docs.nvidia.com/brev/concepts/launchables).

For this project, a future private recipe could start a compatible simulator, the connectome controller, metric collection, and a viewer. Secrets should enter through deploy-time secret bindings, not public defaults. Startup parameter lifetime depends on runtime mode: VM setup values are not automatically present in a later SSH session. This matters when checkpoint uploads appear to work during provisioning but fail during a later experiment. [Launchables](https://docs.nvidia.com/brev/concepts/launchables).

NVIDIA also documents a Brev Launchable for the Halos Outside-In Safety blueprint, including an Isaac Sim software-in-the-loop scenario driven through Jupyter. This is evidence that NVIDIA supports an adjacent simulation pattern; it is not evidence that a connectome robot template already exists or that its viewer has been tested here. [Halos Brev deployment](https://docs.nvidia.com/halos-outside-in/latest/getting-started/brev-launchable.html).

## Cost lifecycle and data survival

A stopped instance can continue to incur storage cost. Auto recharge is a separate billing setting, and exhaustion of credits can ultimately delete resources. Stopping compute is therefore different from proving spending has ended or outputs are safe. [Console billing reference](https://docs.nvidia.com/brev/guides/console-reference).

Before a future run, capture provider, region, GPU model/count, actual quoted rate, disk charges, stop/start support, and the terminal state that ends billing. The CLI supports discovery filters including stoppable instances and configurable firewall; catalog examples are not a live quote. [Search and discovery](https://docs.nvidia.com/brev/cli/search-discovery).

Open questions: live L40S/RTX availability, authenticated service access from the user's browser, WebRTC port topology, and exact provider billing. See [GPU selection](gpu-selection.md), [run contract](run-contract.md), and [source ledger](sources.md).

[Compute index](index.md) · [Research wiki](../index.md).
