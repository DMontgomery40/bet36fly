# CRITICAL PROJECT IDENTITY: THIS IS NOT AN LLM

> **NEVER FORGET: BET36FLY IS A SIMULATION OF A BIOLOGICAL FRUIT-FLY NEURAL CIRCUIT, BUILT ON REAL CONNECTOME DATA. IT IS NOT A LARGE LANGUAGE MODEL.**
>
> **READ THE UPSTREAM BRAIN DOCUMENTATION AND CHECK CURRENT FINDINGS BEFORE MAKING BIOLOGICAL OR ARCHITECTURAL CLAIMS. DO NOT SUBSTITUTE GENERIC LLM ASSUMPTIONS FOR UNDERSTANDING THIS SYSTEM.**

## Mandatory: backend and frontend must stay in sync

**A backend change is not complete until the frontend accurately reflects the resulting behavior and capabilities. Deliver both together.**

- Trace every backend change through its API contracts, frontend types/data handling, controls, status displays, charts, results and explanatory text. Update every affected surface in the same task.
- Expose relevant new capabilities and results in the existing user workflow. Do not leave working backend functionality hidden behind an outdated frontend or display stale model, training, experiment or prediction information.
- Verify the affected browser workflow against the backend, including applicable loading, empty, error and completed states. Backend tests and a successful frontend build alone do not establish that the visible experience works.
- For internal changes with no frontend impact, verify that the existing frontend remains accurate and compatible; do not invent cosmetic changes. Report any unfinished frontend work explicitly instead of claiming the change is complete.

## Start from the biological system

- The project's anatomical foundation is the male fruit-fly brain and central nervous system connectome announced by Google Research, HHMI Janelia and collaborators on **September 3, 2026**. This was a new release when this project began. Keep its identity and release date explicit; do not confuse it with older female FlyWire datasets or a Google language model. [Official Google release](https://research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/).
- Reason about neurons, spikes, anatomical connectivity, sensory encoding, neural readouts and biological learning mechanisms. The sports encoder and decoder are engineered interfaces around that circuit. A conventional feature baseline is a comparator; improving it alone does not demonstrate an improvement to the fly.
- When considering learning, explicitly investigate dopamine and other neuromodulators, receptor-dependent effects, mushroom-body circuits, synaptic plasticity, eligibility traces and reinforcement mechanisms where relevant. Do not dismiss biological reward learning or reduce the user's request to LLM training or merely fitting an external betting policy.
- Distinguish **biology documented in real flies**, **information present in the released dataset**, and **mechanisms actually implemented in this simulator**. The wiring map does not automatically implement every biological process. Inspect the relevant code before saying a mechanism exists, is absent, cannot work, or explains a result. An omitted mechanism is an implementation gap, not evidence that the biological approach fails.

## Treat upstream knowledge as actively evolving

Before substantive decisions about neural dynamics, learning, stimulation, readouts, or explanations of experimental failure:

1. Read the relevant official Google/Janelia release and dataset documentation, original model papers, and upstream implementation documentation/code. Verify which dataset, model and version a claim concerns. Start with the [male CNS resource](https://male-cns.janelia.org/), [published reference simulator](https://github.com/philshiu/Drosophila_brain_model), and the source links in `docs/MODEL_CARD.md` and `docs/FLY_GUIDE.md`.
2. Check current releases, commits, issues, discussions, and relevant public research/community forums or channels for successful approaches, failures, corrections and known limitations. Useful information may have appeared **today or within the last hour**. Do not rely solely on model training knowledge, old summaries, or an earlier session's search.
3. Record source URLs, versions and the date/time checked. Distinguish a community report from an inspected implementation and a reproduced result. Prefer primary evidence and reproducible experiments; do not present an anecdote as established success or claim to have read inaccessible channels.
4. Keep checks targeted and bounded. Reuse verified findings while fresh; refresh them when a new decision depends on current information. This instruction does not authorize continuous polling, account changes, external messages, or unbounded research.

**Carry this biological identity and source-checking requirement into every relevant handoff. Never silently turn this project into a generic LLM or classifier exercise.**
