---
type: concept
updated: 2026-09-12
status: research-synthesis
---

# Hugging Face Jobs, Spaces, and authentication

Jobs are a credible execution surface for a finite GPU experiment; Spaces are a useful application and results surface. A Space can contain code or an image usable elsewhere, but its app lifecycle should not silently become the project's experiment scheduler. [Jobs documentation](https://huggingface.co/docs/hub/jobs); [Spaces overview](https://huggingface.co/docs/hub/spaces-overview).

## Current entry points

The supported Jobs interfaces include the `hf` CLI, `huggingface_hub` Python client, and HTTP API. A job describes a command and hardware flavor, with Docker or UV workflows. The official quickstart also says the signed-in Jobs page can **create and manage** Jobs; describing the web surface as monitoring-only is no longer justified. The exact authenticated form and user account eligibility were not inspected here. [Jobs](https://huggingface.co/docs/hub/jobs); [quickstart](https://huggingface.co/docs/hub/jobs-quickstart).

Current authentication supports browser-based OAuth device authorization when a token is not provided. `hf auth login` wraps the login function; a personal access token remains an alternative. Browser sign-in to the website and authorizing a CLI session are distinct actions even when they identify the same person. Existing installations may lag the live documentation, so record client version before relying on current behavior. [Authentication reference](https://huggingface.co/docs/huggingface_hub/package_reference/authentication).

The current PyPI release is `huggingface_hub` **1.31.0**, uploaded September 10, 2026; it includes the `hf` CLI. This is a registry observation, not the installed version on this Mac. [PyPI package record](https://pypi.org/project/huggingface-hub/).

The browser flow is: invoke `hf auth login`, open the supplied device-authorization URL, enter its short code, approve the requested access, then let the CLI retrieve and cache the credential. Never paste the resulting credential into the wiki. [Authentication reference](https://huggingface.co/docs/huggingface_hub/package_reference/authentication).

The following are a **future read-only discovery sequence**, not commands executed in this research:

```sh
hf --version
hf auth whoami
hf jobs hardware
hf jobs ps -a
```

Account authorization, permissions, credit balance, and the intended user/organization namespace must be resolved before any `run` command. [CLI reference](https://huggingface.co/docs/huggingface_hub/package_reference/cli).

## Execution is more than launching a Python process

The Python API includes `run_job`; UV can carry script dependencies. For this project's recurrent connectome controller, containerizing the simulation, sparse-kernel dependencies, and learning code offers a clearer reproducibility boundary than an unpinned script URL. This is an engineering recommendation, not a measured container advantage. [Jobs guide](https://huggingface.co/docs/huggingface_hub/guides/jobs).

Current Jobs support repository, bucket, and local-directory volumes. Model/dataset mounts are read-only; bucket mounts can persist output. Exposed HTTP ports use an authenticated Jobs proxy, with token read access to the namespace. These are real interactive capabilities, but do not by themselves establish compatibility with an Isaac Sim WebRTC deployment or its UDP media path. [Configuration](https://huggingface.co/docs/hub/jobs-configuration). See [visible simulation](gpu-selection.md).

A completed Job does not prove its checkpoint was saved. The filesystem disappears when the Job ends. Persist intermediate state to durable storage, publish final artifacts deliberately, and independently verify their presence. Job logs survive and are accessible with `hf jobs logs`; explicit cancel is separate from detaching a log viewer. [Manage Jobs](https://huggingface.co/docs/hub/jobs-manage); [quickstart](https://huggingface.co/docs/hub/jobs-quickstart).

## Spaces as a research front end

Spaces offer Gradio, Docker, or static HTML applications. A useful design is a replay viewer showing the robot's trajectory, controller activity, evaluation metrics, and precise artifact revisions. Keep an experiment's result address separate from its mutable application presentation. [Spaces overview](https://huggingface.co/docs/hub/spaces-overview).

Unresolved: account-specific Jobs web controls, available credit, storage quotas, simulator container compatibility, and rendering/network support. None requires assuming the [pending acquisition](ownership.md) has merged products.

[Costs and GPU choices](gpu-selection.md) · [Run contract](run-contract.md) · [Compute index](index.md).
