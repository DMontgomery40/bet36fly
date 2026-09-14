# Continual learning, supplementary: what happens to a cue that stops being reinforced

Protocol `configs/associative-stress-02.json` (identical to stress-01 except that cue `stress:0` is reinforced only in cycles 1–4 and then retired while the other seven cues continue for 20 more cycles). Five arms on Hugging Face Jobs: circuit-01 (no recovery) and circuit-02 at ρ ∈ {0.005, 0.01, 0.02, 0.04}. This is the memory-lifetime measurement promised in the contract; it was **not** used for selecting ρ (the stress-01 rule stands).

Summed MBON05+MBON01 depression of the retired cue relative to its unit-gain probe (three fresh seeds), and the mean depression of the seven cues that kept being reinforced:

| arm | cycle 4 (last reinforcement of stress:0) | cycle 8 | cycle 12 | cycle 16 | cycle 20 | cycle 24 | active cues mean at 24 | eligible edges at the floor at 24 (γ4, γ5) |
|---|---|---|---|---|---|---|---|---|
| baseline | [-15, -16, -14] | [-22, -21, -25] | [-33, -31, -33] | [-36, -39, -38] | [-44, -41, -42] | [-46, -45, -51] | -49.1 | [0.163, 0.17] |
| 0.005 | [-12, -12, -15] | [-20, -21, -20] | [-29, -28, -25] | [-30, -30, -34] | [-35, -31, -32] | [-37, -37, -38] | -41.6 | [0.036, 0.041] |
| 0.01 | [-15, -16, -12] | [-22, -18, -19] | [-25, -23, -21] | [-26, -29, -24] | [-30, -30, -29] | [-32, -29, -32] | -34.8 | [0.02, 0.023] |
| 0.02 | [-13, -14, -11] | [-16, -17, -18] | [-20, -18, -20] | [-21, -19, -21] | [-22, -19, -20] | [-21, -22, -21] | -25.4 | [0.009, 0.01] |
| 0.04 | [-11, -9, -15] | [-11, -13, -14] | [-14, -15, -14] | [-16, -16, -12] | [-11, -17, -14] | [-14, -15, -14] | -15.5 | [0.004, 0.005] |

## Reading

1. **The retired cue is not forgotten; it keeps being depressed by the other cues.** Without recovery its depression grows from about −15 at retirement to −46/−45/−51 spikes at cycle 24, the same trajectory as the cues still being reinforced. The 16-type odor codes share Kenyon cells (mean pairwise Jaccard 0.14 in the calibration), so every reinforcement of another cue depresses part of the retired cue's synapses. In this circuit, with these cues, generalization dominates any specific memory of a retired cue; a cue-specific lifetime cannot be separated from cross-cue depression at this overlap.
2. **Recovery caps the drift rather than erasing the memory.** At ρ = 0.005 the retired cue reaches −37 (versus −46 without recovery) and the still-reinforced cues −42 (versus −49); at ρ = 0.02 the retired cue plateaus near −21 from cycle 12 on; at ρ = 0.04 it plateaus near −14 from cycle 8 on, because dopamine from the other cues recovers the retired cue's inactive synapses as fast as their shared KCs depress them. Floor occupancy at cycle 24 falls from 16–17% to 3.6–4.1% (ρ = 0.005), 2.0–2.3%, 0.9–1.0% and 0.4–0.5%.
3. **Tradeoff at the selected ρ = 0.005.** Recent, still-reinforced memory is retained at 85% of the no-recovery depth (−42 versus −49) and the retired cue at 80% (−37 versus −46), while the floor occupancy drops fourfold. Higher ρ buys less saturation at the cost of shallower memory of everything (−15 at ρ = 0.04).
4. **What a cleaner lifetime measurement needs.** A retired cue with a KC set nearly disjoint from the active cues (pairwise Jaccard well below 0.05), or a KC-specific readout of the retired cue's own eligible edges; both are declared follow-ups, not part of this stage.

Identities: baseline: `associative-stress-b5298f7348c9602d602e`, 0.005: `associative-stress-4fff6d5c3da00f716e81`, 0.01: `associative-stress-5656e6f81167629c3b28`, 0.02: `associative-stress-ab4beecd80459fa6365b`, 0.04: `associative-stress-f3df8eafc32e8e5283a4`. Data: [continual-learning-forgetting.json](continual-learning-forgetting.json).
