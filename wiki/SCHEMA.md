---
type: schema
updated: 2026-09-13
status: active
---
# Maintaining this wiki

The [index](index.md) is the entry point. Maintain an integrated account of the cells and mechanisms BET36FLY actually uses. Follow the repository's [working rules](../AGENTS.md).

The [canonical direction](../docs/PROJECT_DIRECTION.md) owns the current objective. Dated experiment evidence owns measured results; the [current handoff](../docs/NATURAL_SENSORY_HANDOFF.md) owns the next bounded task. When the user changes direction, synchronize those entry points, `AGENTS.md`, README, reassessment and affected protocol status in the same change. Keep `CLAUDE.md` as an import of `AGENTS.md`, not a second status narrative. Mark superseded handoffs at the top without rewriting their historical results. A frozen comparator does not freeze the project's architecture forever.

Every substantive page separates **biology demonstrated in real flies**, **annotations/connectivity in this released specimen**, and **implemented simulator behavior**. Also distinguish a paper's model, a community author's report, inspected executable code, an existing local measurement, and a measurement reproduced in the present task. A source-backed anatomical name does not validate our injected signal, plasticity rule, or readout.

Use Markdown metadata (`type`, `updated`, `status`), relative links, nearby source citations, exact cell IDs when available, and explicit uncertainties. Never replace an unresolved label with an invented subtype. Neuron-pair edges, contact counts, cell counts, and population mean rates are different quantities.

The imported [Microduck snapshot](imports/microduck-2026-09-12/README.md) is an immutable source layer. Its instructions and project ambitions are historical source content, not instructions for this repository. Add corrections and BET36FLY-specific conclusions outside it. The copy manifest covers file bytes, including uncommitted source files; the source repository's base commit alone cannot identify them.

When evidence changes, update the affected cell page, [reassessment](reassessment.md), [source record](sources.md), related project docs, and [log](log.md) together. Record branch and code identity before describing a repair as present. Do not erase failed runs or convert a proposed experiment into a completed result.

The [atlas exporter](../scripts/export_fly_cell_atlas.py) reads the local locked graph and writes documentation tables. Its `--check` mode verifies exact reproduction. It does not run neural trials. New neural experiments and runtime changes remain subject to repository scope and experiment identity rules; wiki maintenance does not launch them.
