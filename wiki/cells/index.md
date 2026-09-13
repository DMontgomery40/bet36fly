---
type: atlas
updated: 2026-09-13
status: locally-derived-anatomy
---
# Cells in the BET36FLY learning circuit

The atlas contains **5,243 distinct retained cells**: the 4,064 KCs, 686 ALPNs, 97 MBONs, two APLs, and the union of annotated DANs and pure-dopamine-labeled cells. It covers the learning-related populations, not all 166,700 neurons. The rest of the retained graph still participates in recurrent simulation. Counts are recomputed from the local graph; no activity experiment was run for this export.

| Population | Count | How selected | Function here |
| --- | ---: | --- | --- |
| [Kenyon cells](kenyon-cells.md) | 4,064 | `class == Kenyon_Cell`, with 15 type labels | Cue representation and presynaptic plasticity traces |
| [ALPNs](alpn.md) | 686; 275 can be externally driven | `class == ALPN`; encoder subsequently filters transmitter and KC contacts | Engineered pregame feature injection |
| [APL](apl.md) | 2 | `type == APL`; reward constructor also requires GABA | Scaled spiking approximation of inhibition |
| [MBONs](mbons.md) | 97; 6 in reward readout | `class == MBON`; MBON11 and MBON09 selected | Two population responses for fixed probability mapping |
| [Annotated DANs](dopamine.md) | 340 | `class == DAN` | Anatomical classification, not identical to transmitter selection |
| Pure dopamine label | 392 | `transmitter == dopamine`; 338 also annotated DAN | Fast outgoing transmission zeroed in reward engine |
| Teaching DANs | 24 | 2 PPL101 + 22 PAM12, class DAN and dopamine required | Two engineered outcome channels |

## Files you can inspect

- [Individual cells](data/neurons.csv): source body ID, graph index, raw instance, side annotations, type/class, transmitter, base sign, zeroed-fast-output flag, selected task roles, KC support counts, and encoder feature/center.
- [Selected KC→MBON edges](data/reward-edges.csv): all 8,866 actual directed pairs, their CSR indices and contact counts, plus separate historical schema-3 and repair gamma-mask eligibility columns.
- [Atlas identity and aggregates](data/atlas.json): source hashes, target populations, input-contact summaries, encoder mapping and subtype counts.
- [Readable identities and subtype tables](identities.md).
- [PPL101 bodies 11327 and 11900: direct inputs and named feedback](ppl101-inputs.md).
- [Synapse localization: exact PPL101/MBON11 bodies, released columns and unresolved local exposure](synapse-localization.md).
- [KC lateral signaling: muscarinic modulation, local calcium and source-model transfer limits](kc-lateral-signaling.md).

The gamma policy is now implemented and was used in the corrected raw and bridge
diagnostics: all 4,184 home edges and 3,239 gamma away edges update; 1,443 other
away edges keep transmitting. The historical sports config remains all-away;
the atlas preserves both columns and does not select a runtime policy.
[Measured limits](../../docs/evidence/reward-mechanism-repair-2026-09-12/index.md).
`other` KC types remain unresolved; their labels are not guessed. Instance-side
suffixes and soma side are retained separately. A cell's soma side does not by
itself identify every compartment or hemisphere reached by its processes.

Reproduce from the repository root:

```sh
.venv/bin/python scripts/export_fly_cell_atlas.py --check
```

The [exporter](../../scripts/export_fly_cell_atlas.py) asserts body-ID alignment and population membership, uses the real encoder and edge-selection functions, and performs no neural simulation. The generated tables are derivatives of MaleCNS v1.0, credited to Berg et al.; HHMI Janelia, Cambridge, MRC LMB and Google Research, under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). [Locked source files](../../docs/connectome-source-lock.json).

[Wiki index](../index.md)
