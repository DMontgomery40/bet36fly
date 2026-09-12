---
type: source-ledger
updated: 2026-09-12
status: researched
---

# Community source ledger

> Research snapshot: 2026-09-11 America/Denver (retrieved 2026-09-12 UTC). Public source inspection; no training jobs, physical trials, or independent replay performed.

All links below were retrieved or inspected on 2026-09-12 UTC / 2026-09-11 America/Denver. “Inspected” means documentation or indicated source code was read, not that the experiment was reproduced. Branch links are mutable.

## Primary sources used

| Source | Evidence extracted | Inspection depth |
|---|---|---|
| [Official Microduck runtime](https://github.com/pollen-robotics/microduck/blob/main/README.md) | Runtime/trainer split and supported behaviors | README |
| [Microduck RL](https://github.com/pollen-robotics/microduck_rl) | Task meanings, passive rollers, ball-blind kick | README/task table |
| [Official browser simulator](https://huggingface.co/spaces/pollen-robotics/microduck-simulator/blob/main/README.md) | Simulation/inference plant | README |
| [Flamingo](https://huggingface.co/RemiFabre/microduck-flamingo-cycle) | Command semantics and disturbance limits | Model card + manifest |
| [Collision Flamingo II](https://huggingface.co/Teethyfish/microduck-collision-flamingo-ii) | Unresolved viewer-path discrepancy | Model card |
| [Tricks](https://huggingface.co/langli11/microduck-tricks) | Held-out batteries and brief single-support boundary | Model card |
| [Basketball](https://huggingface.co/HannesVonEssen/microduck-basketball) | Recurrent contract, privileged critic, export parity | Model card |
| [Beak throw](https://huggingface.co/q2p/microduck-beak-throw) | Contact geometry, output-limit failure, patched runtime | Model card |
| [Stilts](https://huggingface.co/HannesVonEssen/microduck-stilts) | Height-specific model variants, hardware limitation | Model card |
| [Swing](https://huggingface.co/HannesVonEssen/microduck-swing) | Seat/cord task and printable accessories | Model card |
| [microduck-mcp](https://github.com/joeynyc/microduck-mcp) | Agent API/transport layer | README |
| [quackd](https://github.com/rokbenko/quackd) | LLM sequencing of skills | README |
| [specs-microduck](https://github.com/kgediya/specs-microduck) | Gesture packets and synthetic test mode | README |
| [Microfly README](https://huggingface.co/spaces/lvwerra/microfly/blob/main/README.md) | FlyWire lineage, fixed graph, two action paths, licenses | Full raw README and Hub tree |
| [Microfly validation](https://huggingface.co/spaces/lvwerra/microfly/blob/main/VALIDATION.md) | Author browser/ablation tests; direct path falls | Full raw report |
| [Flyhard core](https://github.com/MarkUnthank/flyhard/blob/bad2131a35518944834531f53be004e9f1b9eecb/src/flyhard/connectome.py) | Parameter/buffer distinction, bounded gains, sparse derivative | Entire source file; pinned revision |
| [Flyhard policy](https://github.com/MarkUnthank/flyhard/blob/bad2131a35518944834531f53be004e9f1b9eecb/src/flyhard/motor_policy.py) | Frozen mappings, four updates, state reset, direct targets | Entire source file; pinned revision |
| [Flyhard pilot](https://github.com/MarkUnthank/flyhard/blob/main/docs/pilot-2026-09-09.md) | Before/after learning and scope | Report |
| [Flyhard connected CARLA](https://github.com/MarkUnthank/flyhard/blob/main/docs/carla-video-2026-09-09.md) | Physical intervention and synchronized sequence | Report |
| [DOOMFLY](https://github.com/nftechie/doomfly) | Current plasticity and failed gates | README plus historical baseline README |
| [Fly64](https://github.com/ornata/fly) | Game encoder/decoder and explicit absence of training | README |
| [Flybywire](https://github.com/Flybywirerh/Flybywire) | Default observer architecture | README |
| [Flybywire training](https://github.com/Flybywirerh/Flybywire/blob/main/docs/BRAIN_AND_TRAINING.md) | Readout learning and later yaw-assist profile | Full document |
| [FlyBrain](https://github.com/snedea/flybrain) | FlyWire graph lineage | README |
| [Desktop fly](https://github.com/DenisSergeevitch/desktop-fly) | Procedural body distinction | README/search-index excerpt |

## Discovery source

[Awesome Microduck](https://github.com/joeynyc/awesome-microduck) was used to discover projects and registries. Source-specific numerical claims in this wiki are tied to model cards or project reports rather than inferred from directory ranking. Its branch/status summaries may lag upstream. News and social search results located additional examples but were not used as proof of learning.

## Retrieval caveats

The web retrieval tool rejected the Microfly Space URL/tree. Direct public Hugging Face API and raw-file requests succeeded, allowing its README, validation report, and complete file inventory to be inspected. This was a retrieval limitation, not evidence that the Space was unavailable. No browser execution was used.

A first Python batch retrieval stalled; the substantive Microfly and pinned Flyhard source reads used bounded successful HTTP requests instead. No experimental claim relies on a failed fetch.

## Contradictions and priority refreshes

1. **Flybywire:** README says observer-only; late September 11 training notes describe limited yaw assistance. Inspect active profile and implementation before making an unconditional motor-authority claim.
2. **Flyhard chronology:** early pilot prose predates public publication and connected CARLA recording; later documents supersede those status statements while retaining the original training result.
3. **Microfly identity:** source says FlyWire FAFB v783. Do not relabel it MaleCNS because other contemporary demos use that dataset.
4. **Doom chronology:** fixed-weight baseline documentation is historical; current experimental plasticity exists but has not passed the stated learning gates.
5. **Policy distribution:** verify upstream channel implementation and each manifest's model API before selecting an installer or declaring compatibility.

## Next evidence to acquire

The largest remaining gaps are exact artifact replay, current drone-profile reconciliation, multi-seed anatomical-core learning with controls, and physical robot acceptance. These were outside this read-only community research pass. Preserve failures and scope boundaries when future evidence updates the wiki; do not overwrite a negative result merely because a later demo looks better.


---
[Community index](index.md) · [Source ledger](sources.md) · [Main wiki](../index.md)
