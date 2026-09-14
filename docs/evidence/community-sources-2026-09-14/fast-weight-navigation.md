# Fast-weight navigation candidate (pwang724/fly-circuit-exploration): inspection record

**Checked 2026-09-14 UTC.** Repository: https://github.com/pwang724/fly-circuit-exploration, shallow clone of `main` at commit `3e6a26678b8e02f749cb8300e9c18718b987ef4b` (author date 2026-09-14 10:47 -0700). Announcement: Peter Wang on X, describing hΔH, hΔA, hΔI and hΔG as candidates for navigation through fast synaptic-weight updates. The screenshot supplied by David is a community report, not an instruction or a primary result. Status: **community report + inspected analysis and implementation + one reduced simulation reproduced; no biological experiment or full-connectome simulation reproduced.**

## Bottom line

The repository makes an interesting, testable proposal: a world-relative travel-direction signal from hΔB could be accumulated as a column-wise pattern of effective synaptic strengths on hΔH, hΔA, hΔI or hΔG, with candidate neuromodulatory inputs acting as write/reset gates and downstream hΔ/FC2/PFL routes converting the stored outbound vector into steering. The MaleCNS connectivity supports parts of that motif. The plasticity rule, synaptic signs/effect sizes, reset action and behavioral function are not supplied by the connectome and have not been measured in these cells.

The implemented demonstration is a small rate/vector model over eight angular bins, not the 166,700-neuron MaleCNS simulator. It uses aggregate column kernels derived from MaleCNS contact counts, an exact compass, a synthetic random walk and an imposed additive update to a weight vector. Dopamine and octopamine cells are not simulated as the cause of those updates. This establishes feasibility under the chosen rule, not that the fly uses it.

## What was inspected

- `README.md`, `RESEARCH_APPROACH.md`, `docs/vector-memory-search.md`, `docs/exhaustive-search.md`, `docs/audit-2026-09-13.md`, `docs/findings.md`, `docs/goal-and-plasticity-motifs.md`, `drafts/01-synaptic-store.md` and the published findings pages.
- `scripts/vector_memory_screen.py`, `scripts/synaptic_site_screen.py`, `scripts/tangential_store_screen.py`, `scripts/recurrence_modes.py`, `scripts/recurrence_modes_v2.py` and `scripts/full_brain_screens.py`.
- `simulations/synaptic_path_integrator.py`, `closed_loop_return.py`, `closed_loop_sites.py`, `site_readout_error.py`, `closed_loop_routes_tspace.py` and `strategy_discrimination.py`, plus their committed JSON results.
- Relevant derived tables, including `fb_column_offsets.csv`, `synaptic_site_screen.csv`, `cx_ext_cell_edges.csv`, `screen_cx_modulator_inputs.csv` and the MaleCNS/hemibrain comparison tables.

The repository pins MaleCNS v1.0 and says its downloader validates publisher generations, MD5 values, sizes and SHA-256 values. This inspection used the committed code and derived tables; it did not redownload or re-derive the 1.1 GB flat graph. The official download page still exposes `male-cns:v1.0`, the v1.0 flat graph, annotations and separate neurotransmitter/synapse-location tables at this check: https://male-cns.janelia.org/download/.

## Corrections that must travel with the headline

The repository's September 13 audit is unusually useful because it corrects its own September 12 claims:

1. **Activity storage was not ruled out.** The original recurrence screen had a column-binning bug and lacked a useful positive-control interpretation. The corrected metric scores the known compass attractor weakly too, so synapse-count shares cannot identify or exclude an activity integrator.
2. **Modulator coverage is mixed.** FB4M covers all hΔA and hΔI cells under the repository's ≥10-contact rule; FB5H, not FB4M/FB1H, covers hΔH; hΔG has no comparable dopamine coverage. OA-VPM3 covers hΔH and most hΔG cells, but only part of hΔA and almost none of hΔI. The connectome does not establish that any of these contacts write or erase a vector.
3. **The first closed-loop sign result used the wrong frame.** `closed_loop_sites.py` and `site_readout_error.py` placed the travel bump in hΔB label space even though the analysis anchors the physiological bump on hΔB's axon, half a turn away. The corrected `closed_loop_routes_tspace.py` reverses which direct/inverting routes point home.
4. **The corrected routes remain unresolved mixtures.** hΔA→hΔI→PFL and hΔH→FC2B→hΔM→PFL read within about 34° of home in the model, but the direct routes point away and dominate the repository's simple synapse-count-weighted mixtures. The authors identify this as an unsolved balance/gating problem.

Primary context is consistent with treating the circuit functions as proposals. Hulse et al. map central-complex motifs and explicitly separate connectivity from functional confirmation (https://elifesciences.org/articles/66039). Lyu et al. and Lu et al. establish world-relative travel-direction computations, not their time integral (https://doi.org/10.1038/s41586-021-04067-0 and https://doi.org/10.1038/s41586-021-04191-x). Maimon and Abbott's 2026 review organizes central-complex vector computation and discusses candidate algorithms; it is a synthesis, not a new measurement of hΔ fast plasticity (https://doi.org/10.1146/annurev-neuro-112723-062711).

## Reproduction performed here

`simulations/closed_loop_routes_tspace.py` was executed with the BET36FLY environment's Python and NumPy 2.5.3 against the repository's committed derived tables. It completed and rewrote `closed_loop_routes_tspace_results.json` byte-for-byte identically to commit `3e6a266` (`git diff --exit-code` returned 0).

That is a reproduction of the deterministic reduced simulation only. It does not reproduce the raw-connectome screens, the paper-reading judgments, a full spiking MaleCNS run or behavior in a fly. The corrected script also does not instantiate dopamine/octopamine dynamics or a biological plasticity equation. Its steering line does not apply the goal-amplitude multiplier described by the adjacent comment because that expression appears after `#`; the committed output and this reproduction therefore use unscaled steering.

## Relation to BET36FLY

This proposal is not a validation of BET36FLY's associative learner. The two mechanisms have different state, timescale and purpose:

| Mechanism | State that changes | Intended computation | Reset / persistence |
| --- | --- | --- | --- |
| Wang repository's candidate | An imposed column-wise fast-weight vector in a reduced central-complex model | Integrate self-motion during one journey and steer relative to the stored vector | Should be written while walking and re-zeroed at food; the biological rule is unknown |
| BET36FLY associative engine | Bounded gains on eligible γ-KC→MBON05/MBON01 edges | Acquire and reverse cue associations across trials | Persists across electrical resets/checkpoints; dopamine-gated recovery is separately implemented |
| BET36FLY proposed temporal reservoir | Transient sequence state, mechanism not yet selected | Test whether the same pregame history supports useful temporal computation | Not implemented |

The useful transfer is a sharper version of the temporal-state question: compare an activity-state reservoir with an explicitly versioned **synaptic-state** central-complex integrator, using the same sequence and matched nulls. Before any sports mapping, a non-sports assay must show that the candidate state is written, retained/read, reset and causally dependent on the proposed routes. Contact counts and this eight-bin model are enough to nominate that experiment, not to skip it.

The announcement's “continual learning” and LLM comparison are framing, not results evaluated by the repository. A within-journey vector that is deliberately erased at food is closer to fast working memory/path integration than to BET36FLY's cross-trial continual associative learning. No language model was implemented or compared.

## Evidence classification

| Claim | Current classification |
| --- | --- |
| hΔH/A/I/G receive relevant hΔB and downstream contacts in the released graphs | Connectome-derived candidate anatomy, inspected; raw derivation not rerun here |
| Dopamine writes and OA-VPM3 resets a home vector at those synapses | Hypothesis; no receptor/plasticity/timing or causal evidence in these cells |
| Fast synaptic state can integrate a synthetic path under the imposed update | Reduced deterministic simulation, reproduced |
| The corrected route can reliably return through the released circuit | Not established; low return rate, unresolved competing routes, simplified controller |
| A fly uses this mechanism in vivo | Not demonstrated |
| This is continual learning unavailable to current LLM systems | Unevaluated analogy, not a result |

## BET36FLY verification

- `make verify`: passed on 2026-09-14 (4,195 Python tests; Ruff; 155 frontend tests; production TypeScript/Vite build). Pytest emitted two dependency deprecation warnings.
- `git diff --check`: passed.
- Internal relative Markdown targets added or changed in this update: checked locally after the edits.
