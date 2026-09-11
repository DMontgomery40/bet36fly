# Making the fly smarter, and knowing whether it improved

**Updated September 11, 2026.** Fly’s desk now records pregame picks, scores confirmed outcomes, and refreshes public sources every 15 minutes while the local server runs. The experiments and evaluation schedule below remain a plan. It does not schedule monitoring, launch new training, or connect an account. [How the existing model works](FLY_GUIDE.md) · [Confidence and paper sizing](CONFIDENCE_AND_DRAWS.md).

Our first priority should be better evidence and better observations. The fly currently loses to a simple feature baseline. Buying more compute or letting it run longer has not been shown to solve that.

## Give it the external hard drive

Yes: we can give the system durable memory far beyond its transient neural state. **Storage alone does not make the neurons able to read it.** We need a retrieval policy and an encoder that converts selected information into stimulation the trained fly can use.

| Memory layer | What it stores | How the fly would receive it | Status |
| --- | --- | --- | --- |
| Historical results | Matches, scores, dates and team identities | Existing Elo/form/rest features | Implemented. |
| Prediction journal | Probability vectors, model/input identity, creation time | Audit record and forward outcome/accuracy reports | Logging and outcome scoring implemented; calibration and learning loop proposed. |
| Similar-match memory | Past games resembling the current matchup | Counts, outcome frequencies, score distributions and retrieval uncertainty | Proposed. |
| Sports knowledge | Rules, injuries, lineups, roster changes and explanatory sources | Versioned numerical facts or a trained embedding encoder | Proposed. |
| Persistent neural state | The brain's evolving internal state across events | Carry state between chronologically ordered stimuli | Research option; current trials reset. |

A useful first memory experiment would retrieve, for example, earlier matches with similar team strength, expected scoring and rest. Supply the fly with the sample size, recency and smoothed outcome distribution. Compare four systems on identical data: current fly, retrieval-only predictor, memory-assisted fly, and a conventional model with the same memory features. If retrieval alone explains all improvement, we have improved the surrounding system without demonstrating an added benefit from the fly.

Every record needs both **when the event happened** and **when the information became available**. Historical evaluation must query the database as it could have existed before the prediction. Later corrections, future results, and an LLM recalling a known match result must not sneak into a supposedly pregame explanation.

For general written knowledge, an external language model could extract facts with sources, and an encoder could deliver those facts numerically. Retrieval-augmented language models demonstrate the broader idea of combining trained parameters with a separate searchable store; their results do not mean this fly can directly read retrieved text. [Lewis et al., retrieval-augmented generation](https://arxiv.org/abs/2005.11401).

The resulting system should be called **LLM-assisted** if an LLM supplies meaningful predictions or representations. Keep an assistant-only baseline and measure the fly's incremental contribution. A natural-language explanation should report features, retrieved evidence and tested sensitivities; it should not invent an inner monologue for the neurons.

## The experiments I would prioritize

### 1. Establish a trustworthy forward comparison

The current desk scores the first valid pregame record per current fixture revision, across model versions; postponements and unresolved games are held, cancellations are void, and later predictions cannot replace the scored pick. Source corrections can change a final result. Prediction horizons currently vary. For a controlled comparison, keep checkpoint v1 frozen. Record predictions before kickoff at a chosen, consistent horizon, such as 24 hours before start. Preserve later revisions separately. Add a bet-settlement process with explicit handling of postponements, cancellations and market rules. Evaluate one designated prediction per fixture and horizon; do not count every revision as a new independent success.

Add class-specific calibration and stronger baselines before experimenting with stakes. Soccer should have a score-distribution baseline in addition to logistic regression; baseball should get a suitable run/win baseline. The [confidence guide](CONFIDENCE_AND_DRAWS.md) specifies the probability and price distinctions.

### 2. Improve the sports information

For soccer, test pregame estimates of scoring rates, attacking/defensive strength, lineups and player availability. For MLB, test probable/confirmed starters, bullpen workload, lineup strength and venue. Each added source must have historical availability timestamps or be evaluated prospectively.

Use goal distributions to examine draws directly: under a score model, draw probability is the sum of the probabilities of 0–0, 1–1, 2–2 and so on. This tests whether the fly is missing scoring information. Dixon and Coles provide a classical statistical starting point for modeling football scores and changing team strength. This is a candidate baseline, not a promised profitable strategy. [Dixon & Coles](https://academic.oup.com/jrsssc/article-abstract/46/2/265/6990546).

Bookmaker prices can be a separate experimental input, but label that version **market-assisted**. Its comparison must include a market-only predictor, and quotes must come from before the prediction. Copying market probabilities is not evidence of an independently discovered edge.

### 3. Improve how information enters and leaves the brain

Compare stimulation mappings, learn a small constrained input encoder, and test a few prespecified trial durations. Read out multiple temporal windows instead of only whole-trial firing rates. Check input clipping, neuronal saturation and whether different observations actually produce distinguishable output activity.

These changes require new training and new checkpoint identities. Sending more inputs into old channels without retraining changes what their values mean. Longer trials could reveal useful recurrent dynamics, or could simply converge to repetitive activity and erase distinctions. The validation experiment must decide.

Small ensembles across independently trained seeds or stimulation realizations could reduce sensitivity to one initialization. Their disagreement is a useful diagnostic, not a guaranteed confidence interval. Replaying the same cached response saves time but adds no knowledge.

### 4. Improve learning inside the anatomical graph

First try separate sport-specific connection gains: the current graph shares its gains across both sports. Test stronger regularization or fewer shared parameters by cell type, which might generalize better with limited soccer data. Then consider training more supported connections or selected neuron time constants, preserving anatomical support and clearly recording departures from physiology.

A more ambitious route is to optimize a differentiable model of the actual neural dynamics and verify its gains in the full simulator. Lappalainen and colleagues showed that task optimization of connectome-constrained visual circuitry could predict measured fly neural responses. That supports the research method; it does not establish transfer to sports. [Lappalainen et al.](https://www.nature.com/articles/s41586-024-07939-3).

Surrogate-gradient training is another candidate for handling the non-differentiability of spikes. It differs from our current rate-surrogate warm-up. Full-network training through time brings substantial memory and compute costs, so benchmark a constrained experiment before paying for large runs. [Neftci, Mostafa & Zenke](https://arxiv.org/abs/1901.09948).

A reward-based experiment could adjust supported synapses using an outcome scoring rule and eligibility traces. It would be an explicitly designed learning rule unless independently matched to biological evidence. Start with probability quality as the objective: raw monetary reward mixes forecast quality, odds, stake policy and luck, making a poor initial teaching signal.

### 5. Test broader applications after the basics

Player props need player-level histories, opportunity estimates such as minutes or plate appearances, valid market definitions, and their own models and calibration. The match-result decoder cannot produce meaningful player prop probabilities by relabeling its outputs.

A motion or visual-control task could connect the simulator to inputs more closely related to fly biology. It would test a different capability, not improve sports forecasting automatically. A browser adapter could fetch observations and display responses, but browser access by itself does not confer language comprehension or knowledge.

A demo-account adapter belongs after quote capture, paper fills and settlement are working. It should consume an immutable decision record with market, price, calibration and risk-policy versions rather than interpret whatever the dashboard happens to display.

## Proposed watch plan

| Cadence | What to check | What to do with a problem |
| --- | --- | --- |
| Every fetch/inference | Source success age, fixture identity, start time, missing inputs, checkpoint hash, finite normalized probabilities | Keep old successful timestamps visible; mark affected forecasts stale or unavailable. Proposed value sizing abstains. |
| Each result cycle | Final-result status, postponed/resumed games, matching market rules, duplicate revisions | Settle only eligible records; retain unresolved cases and correction history. |
| Weekly | Coverage, outcome counts, log loss, Brier score, per-class calibration, baseline differences and input drift, separately by sport | Investigate sustained changes; don't retrain solely because of a losing week. |
| Monthly or after a planned evidence block | Candidate versus frozen v1 and stronger baselines on subsequent data; compute cost and calibration stability | Promote only a version satisfying the predefined comparison; otherwise retain the result as a failed experiment. |

A future monitor should report completion, sustained data failure, material model degradation or a decision requiring attention. Unchanged state does not need repeated notifications. None of these scheduled checks was activated by writing this plan.

Keep the original January–August 2026 test results as the v1 reference. Now that we have examined them, development decisions based on them are exploratory. Future claims need fresh chronological windows, not repeated tuning against this same test.

For comparisons, use paired losses on the same games and uncertainty estimates that respect shared teams/time, such as resampling matchweek blocks and checking sensitivity to block size. Choose metrics, prediction horizon and a minimum worthwhile improvement before inspecting candidate results. A possible engineering target is a 0.01 reduction in mean log loss, but that is a proposed threshold, not a universal scientific constant. Report whether the uncertainty interval can distinguish the target; do not declare victory from the sign alone.

## How smart could it get?

We do not have an established IQ, general-intelligence ceiling or guaranteed sports ceiling for this simulation. Neuron count cannot supply one. A biological wiring diagram plus simplified dynamics also does not establish the capabilities of the original animal.

We can identify practical limits and test which one is binding:

| Possible limit | Evidence to look for | What the experiment would tell us |
| --- | --- | --- |
| Missing information | Better inputs improve several model families, including the fly | Data was a bottleneck. |
| Poor sensory encoding | Different inputs collapse to similar firing; a better encoder improves later-game performance | The interface discarded useful distinctions. |
| Restricted training | Training loss remains poor while a matched model fits; changing the optimizer or trainable region helps | The current learning procedure was limiting. |
| Overfitting or drift | Training improves but later periods do not; smaller models or regularization help | More capacity is not the immediate answer. |
| Anatomy adds no useful advantage | Equally trained, degree/sign/weight-matched randomized graphs perform similarly across seeds and periods | Biological topology has not earned credit for this task. |
| Residual match uncertainty | Diverse strong predictors plateau despite additional valid information | An empirical performance floor for the tested information, not proof of an absolute ceiling. |

For a fair topology test, preserve graph size and important degree/sign/weight statistics, train comparable readouts and allowed gains, and match data, tuning opportunities and compute budgets. Also run a whole-pipeline label shuffle, with model selection confined to its shuffled development data, then evaluate against untouched true labels. The existing silence and readout-only shuffle controls are weaker tests.

A practical stopping rule is to predefine a bounded search—several chronological folds, several seeds and a small set of encoding/training variants—and stop expanding it when no candidate produces a worthwhile, repeatable improvement over the same-input baseline. Record uncertainty and the variants attempted. That tells us we have exhausted **this experimental budget and design**, not that no better fly-derived model can exist.

The most useful “cheats” are better observations, structured memory, calibration and strong teachers. They may make the overall product much better. The accompanying control should always ask: **does keeping the fly in the path improve the result, or is the surrounding assistance doing the useful work?**
