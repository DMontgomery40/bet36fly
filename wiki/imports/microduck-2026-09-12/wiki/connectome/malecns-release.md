---
type: research-note
updated: 2026-09-12
status: researched
---

# MaleCNS identity, coverage, and local provenance

[Connectome index](index.md) · [Brain–body interface](brain-body-interface.md) · [Sources](sources.md)

## What changed in 2026

MaleCNS is the male fly **central nervous system**, including central brain, optic lobes, and ventral nerve cord (VNC), with the neck connection preserved. That continuity supports tracing brain-to-VNC pathways within one specimen. Janelia credits FlyEM, Cambridge, MRC LMB, and Google Research; this is a collaborative anatomical reconstruction. [Janelia overview](https://www.janelia.org/project-team/flyem/male-cns-connectome)

| Event | Verified date | Evidence |
|---|---|---|
| Initial v0.9 release | October 2025; day inconsistent | Project home says October 3; release notes say October 5. |
| v1.0 data release | June 8, 2026 | Release notes describe proofreading and annotation refinement. |
| Cell publication and Google announcement | September 3, 2026 | Project home and Google dated announcement. |

Sources: [project chronology](https://male-cns.janelia.org/), [release notes](https://male-cns.janelia.org/release/), [Google announcement](https://www.research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/). Calling this a September **publication** is accurate; calling v1.0 first downloadable in September is not supported by the release history.

## Brain, CNS, and body are different boundaries

The 2024 FlyWire publication describes an adult **female brain**: 139,255 neurons and 54.5 million synapses between those neurons. Brain coverage includes central brain and optic lobes; inputs and outputs can cross the imaged boundary. It is not the same continuous brain-plus-VNC specimen as MaleCNS. Its paper appeared online October 2, 2024. [Dorkenwald et al.](https://www.nature.com/articles/s41586-024-07558-y)

For Microduck, CNS coverage is valuable because a model can retain VNC processing instead of jumping directly from selected descending neurons to a behavior generator. This is a design inference, not a published demonstration that MaleCNS can already operate this robot. CNS reconstruction also does not supply Microduck's mechanics, camera calibration, torque mapping, or learned body model.

## Counts: contacts are not directed graph edges

Google reports over 166,000 neurons and roughly 125 million synaptic connections. Those rounded public numbers must not be relabeled as 125 million unique neuron-pair edges. [Google announcement](https://www.research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/)

The local [manifest](../../data/brain/manifest.json), read during this research pass, records:

| Local quantity | Value | Meaning |
|---|---:|---|
| Retained neurons | 166,700 | Non-glial objects with a populated neuronal superclass. |
| Retained directed pairs | 25,582,938 | Edges with both endpoints in the retained set. |
| Retained synaptic contacts | 124,177,617 | Sum of edge contact counts. |
| Source-table rows | 151,856,684 | Full released segment-to-segment table before endpoint filtering. |
| Source-table contacts | 311,833,243 | Sum before endpoint filtering. |
| Excluded rows | 126,273,746 | At least one endpoint is outside the retained neuronal set. |
| Excluded contacts | 187,655,626 | Contact count on excluded rows. |
| One-contact edges retained | 10,299,701 | No extra strength threshold. |
| Self edges retained | 101 | No automatic self-edge deletion. |

The two accounting identities hold in this manifest: retained plus excluded rows equals source rows; retained plus excluded contacts equals source contacts. These are local import statistics, not a substitute for independently recomputing every raw-file hash and count. The source table deliberately includes segments beyond the selected neuronal population. It is misleading to call the excluded rows additional complete neurons or silently present the raw total as the modeled neuronal network.

The [importer](../../flybrain/connectome.py) preserves source IDs, rejects duplicate retained IDs, checks endpoint membership and repeated directed pairs, and records three input hashes. Outgoing CSR uses presynaptic rows and postsynaptic columns. Any downstream sparse multiplication must respect that orientation; a transpose error changes the direction of the nervous system.

## What is measured and what is modeled

The download portal distinguishes aggregate connectivity, individual synaptic partners, synapse positions, annotations, skeletons, and inferred neurotransmitter tables. Its `minconf-0.5` filenames disclose a source confidence filter; “no extra threshold” does not mean unfiltered raw EM. Polyadic contacts also make a presynaptic site different from a partner pair. [Official download schema](https://male-cns.janelia.org/download/)

Locally, signs are a simplified rule: acetylcholine positive; GABA, glutamate, and histamine negative; ambiguous cases positive. The manifest records 3,718 uncertain-transmitter neurons and explicitly marks biological dynamics unvalidated. These signs, neuron update equations, timescales, gains, plasticity rules, and robot interfaces are model assumptions, even when contact magnitudes and anatomical endpoints are retained. See [interface contract](brain-body-interface.md).

## Attribution and reuse

The project links its dataset license to **CC BY 4.0**. Preserve creator attribution, source and version, the license link, and an account of modifications when redistributing derived data. The data license does not automatically license every external controller's code or media. [Dataset license declaration](https://male-cns.janelia.org/) · [CC BY 4.0 deed](https://creativecommons.org/licenses/by/4.0/)
