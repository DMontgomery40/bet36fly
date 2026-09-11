# Confidence, draws and paper bet size

**Audit of checkpoint `20260910T232621Z`, September 10, 2026.** [How it was trained](FLY_GUIDE.md) · [Memory and roadmap](ROADMAP.md).

The current “confidence” is the model's largest output probability. It is **not calibrated certainty**, and the current pick is the most probable category rather than the best-priced opportunity. There is no implemented stake policy or account connection.

The saved soccer test also does **not** show general draw inflation: the fly averaged **21.0%** for draws, compared with **24.3%** from normalized historical bookmaker prices and **30.8%** actual draws. A few high draw predictions can coexist with underpredicting draws across the whole schedule.

## What “40% draw” actually says

Consider an illustrative forecast:

| Home win | Draw | Away win |
| ---: | ---: | ---: |
| 30% | 40% | 30% |

Draw is the largest **single category**, so the current app selects it. But the combined probability of **someone winning is 60%**. “Draw is our pick” is not the same statement as “a draw is more likely than a decisive result.” Humans discussing who will win may be implicitly comparing the latter grouping, or choosing between teams while ignoring the third category.

An accurate 40% probability would still lose roughly 60% of comparable draw selections over many trials. Losing one does not refute it, and winning one does not validate it. Calibration asks whether events assigned similar probabilities occur at approximately those frequencies.

For a specific fixture, the computational reason for a draw prediction is that the trained draw decoder score exceeds the other scores after reading the brain's activity. We have no evidence that the fly “likes draws,” wants a winner, or holds an articulated belief about a team. A useful explanation would show input sensitivities or controlled neuron/connection interventions; it should not invent a psychological story.

## The draw audit: all held-out EPL games

These are **214 retrospective test matches from January–August 2026**, not today's upcoming fixtures. Every saved soccer prediction was matched one-to-one to its frozen fixture and outcome. All 214 had complete finite `B365H`, `B365D`, `B365A` price fields.

| Quantity | Result | What it measures |
| --- | ---: | --- |
| Actual draws | 66 / 214 = **30.84%** | Outcomes in the test sample. |
| Average fly draw probability | **21.05%** | Probability mass assigned to draws across all 214 games. |
| Average normalized historical Bet365 draw probability | **24.30%** | A price-derived comparison, not a survey of human beliefs. |
| Games where draw was the fly's largest category | 16 / 214 = **7.48%** | How often the displayed pick was draw. |
| Actual draws among those 16 picks | 6 / 16 = **37.50%** | Conditional success rate for its draw selections. |
| Average predicted draw probability among those 16 | **47.58%** | Its average forecast on the selected subset. |
| Highest single test draw probability | **79.96%** | One extreme forecast; that match did not draw. |

Thus, the selected draw subset was overconfident **in this sample**, while total draw probability was too low. Six wins in 16 trials is very little evidence: a descriptive 95% Wilson interval for that observed frequency is approximately **18.5%–61.4%**. It includes the predicted 47.6%. This interval assumes independent observations; shared teams and matchweeks complicate that assumption. It is not an interval for any individual match's true probability.

The pattern below makes the difference visible. Bins include their lower boundary and exclude their upper boundary, except the final 90–100% bin includes 100%.

| Fly draw probability band | Matches | Average predicted draw | Actual draws | Observed draw rate |
| --- | ---: | ---: | ---: | ---: |
| 0–10% | 27 | 7.3% | 5 | 18.5% |
| 10–20% | 87 | 14.6% | 23 | 26.4% |
| 20–30% | 64 | 24.2% | 22 | 34.4% |
| 30–40% | 23 | 35.3% | 11 | 47.8% |
| 40–50% | 9 | 44.6% | 3 | 33.3% |
| 50–60% | 1 | 56.8% | 0 | 0.0% |
| 60–70% | 2 | 66.4% | 2 | 100.0% |
| 70–80% | 1 | 79.96% | 0 | 0.0% |

There were no predictions in the 80–100% bands. The high-probability bins are too sparse to establish reliable rates. Do not turn their zeroes or 100% values into correction rules.

Evidence: [machine-readable report](evidence/draw-audit-2026-09-10.json), [all 214 matched rows](evidence/draw-audit-2026-09-10.csv), [audit script](../scripts/analyze_draws.py). The report includes source/checkpoint hashes, coverage, split frequencies and bin counts. Reproduce it without fetching games or retraining:

```sh
.venv/bin/python scripts/analyze_draws.py
```

### How the price comparison was calculated

For each match, using decimal prices for home, draw and away:

```text
q_draw = (1 / draw_odds) / (1 / home_odds + 1 / draw_odds + 1 / away_odds)
```

This proportionally normalizes the three implied probabilities to sum to one, removing their overround arithmetically. It does not identify the true probability or correct all pricing biases.

The parser stores the unsuffixed `B365H/D/A` columns. We did **not** substitute the separate closing-price columns. Football-Data distinguishes closing prices with a `C` in the heading. Exact historical quote availability and executability were not captured, so this is a descriptive comparison, not a verified return backtest. [Provider definitions](https://www.football-data.co.uk/data), [parser](../bet36fly/sports.py).

### Are humans biased toward seeing a winner?

That is a hypothesis we could test, not the explanation established here. Wanting one's team to win, talking only about two teams, and selecting a winner rather than supplying a full probability vector are different phenomena. None establishes how far a person's draw probability is from reality.

Bookmaker prices are also not a simple average of human forecasts. Research on more than 150,000 European soccer matches finds that market structure and differing price sensitivity can help explain pricing patterns, including draw returns; psychology alone is not the only candidate mechanism. [Hegarty & Whelan](https://academic.oup.com/oep/article/78/1/90/8244336).

We have no matched human-forecast panel. To test the proposed human bias, collect home/draw/away probabilities from people and the fly on the same fixtures, at the same time, with the same available information and match rules. Score all forecasts, not just volunteered confident picks. Record team allegiance or desired outcomes separately from probability judgments. Until then, we cannot claim the fly values draws more highly than humans do.

### What could cause the fly's uneven draw probabilities?

Several model-specific hypotheses deserve testing:

- **Changing outcome frequencies.** Training had 175 draws in 760 games, or 23.0%; validation had 42/186, or 22.6%; test had 66/214, or 30.8%. This is an observed shift in sample frequency, but it does not prove the cause of every forecast error.
- **Missing scoring information.** Equal team strength does not determine draw probability by itself. A goal-distribution model can distinguish an evenly matched low-scoring game from an evenly matched high-scoring game. This fly lacks explicit expected-goal distributions.
- **Limited training evidence and imperfect encoding.** Only 760 soccer games fit the original model; the sensory mapping, brief dynamics, shared plasticity and compressed readout may fit misleading patterns. These are possible failure points, not diagnosed causes yet.
- **Uncalibrated output.** Softmax forces probabilities to sum to one; it does not make them empirically reliable. Extreme scores can produce unwarranted certainty.

There is no special draw bonus in the loss. Sports are balanced against each other; home/draw/away classes are not artificially equalized. Suppressing draws by hand because they feel implausible would be particularly questionable when the aggregate test already underpredicts them.

## How confidence should work next

Keep these separate in the product:

| Field | Meaning |
| --- | --- |
| Raw probability | Output of the current neural decoder. |
| Calibrated probability | A mapping fitted using separate historical calibration data, then checked on later data. |
| Reliability evidence | Sample sizes, class-specific calibration and performance relative to baselines. |
| Model disagreement | Sensitivity across trained seeds or plausible model variants; a diagnostic, not guaranteed uncertainty coverage. |
| Data status | Freshness, missingness and whether this matchup lies outside familiar input ranges. |
| Price/edge | Comparison with an actual offered price for the same outcome and rules. |

A practical first candidate is temperature scaling, `softmax(logits / T)`, fitted separately by sport. It is a researched calibration method, but performance on other neural-network tasks is not a guarantee here. With positive `T`, it preserves ranking and cannot repair wrong rankings; one scalar may also fail to correct class-specific bias. [Guo et al.](https://proceedings.mlr.press/v70/guo17a.html).

Do not fit that temperature on the 214-game test we just audited. The original validation set was already used for model selection. Use a new chronological calibration block or a properly nested, time-ordered procedure, then evaluate on a later untouched block. Compare with regularized multiclass calibration if there is enough data, keeping complexity proportional to sample size.

Report draw-specific calibration as well as top-choice calibration. The current report's soccer calibration error of 0.209 concerns the **largest predicted category**, not draw probability alone. Accuracy, log loss and Brier score should remain visible: a nearly constant class-prior forecast can be calibrated yet fail to distinguish matches usefully.

## How confidence and bet size connect

The existing app publishes fair model odds, `1 / p`. Those are not offered prices. Betting at your own fair odds has zero expected edge under your own model, before costs. We need external quote snapshots before calculating value.

For a single win-or-lose proposition with calibrated probability `p` and offered decimal odds `d` (including returned stake):

```text
break_even_probability = 1 / d
expected_profit_per_unit_staked = p × d - 1
```

| Illustrative probability | Offered decimal odds | Expected profit per unit under that estimate | Decision implication |
| ---: | ---: | ---: | --- |
| 70% | 1.30 | −0.09 | High win probability, negative estimated value. |
| 40% | 3.00 | +0.20 | Lower win probability, positive estimated value if the probability is reliable. |

These are arithmetic examples, not current recommendations. Both require a correct market definition. A 90-minute soccer result, draw-no-bet, qualification after extra time, and a player prop have different settlement events. Pushes, voids, commissions and partial settlements require their own payoff model.

### A proposed paper sizing rule

The one-proposition Kelly fraction maximizes expected log wealth when its probability and payoff assumptions hold:

```text
full_kelly_fraction = max(0, (d × p - 1) / (d - 1))
```

It is not a remedy for wrong probabilities. Growth and drawdown trade off, and formal risk-constrained approaches explicitly model that tradeoff. [Busseti, Ryu & Boyd](https://web.stanford.edu/~boyd/papers/kelly.html).

For a phase-2 **paper experiment**, I would compare a fixed-unit benchmark with a conservative fractional-Kelly candidate. An illustrative candidate is:

```text
if no valid quote, unreliable/stale inputs, or no qualified model:
    value_strategy_stake = 0
else:
    fraction = min(0.25 × full_kelly_fraction, 0.005)
    stake = paper_bankroll × fraction
    reduce further to respect remaining event and portfolio exposure limits
```

Here 0.25 and 0.005 mean quarter Kelly and a 0.5% per-event ceiling. They are proposed policy choices to test, not empirically optimized or guaranteed safe values. With hypothetical `p = 0.40`, `d = 3.00`, full Kelly is 10%; quarter Kelly is 2.5%; the cap reduces that to 0.5%, or **50 paper units on a 10,000-unit simulated bankroll**.

The present model is not qualified by evidence of a pricing edge, and live offered quotes are not captured. The proposed value strategy therefore stays at zero until those conditions are met. We can still score every forecast and later run a clearly labeled fixed-unit simulation to study performance; a zero-stake strategy by itself teaches us nothing about returns.

Sizing should live in a separate, deterministic risk module. The fly estimates outcomes; the module applies prices, bankroll and exposure rules. Log the raw and calibrated probabilities, quote/time, market rules, model/calibrator/policy versions, proposed stake, and reason for a skip. This lets us separate a forecast failure from a sizing or execution failure.

Treat bets on the same match, team or correlated props as shared exposure. Applying independent Kelly formulas to every leg does not solve a correlated portfolio. Include unresolved stakes in exposure calculations, reserve bankroll consistently, and never increase stakes merely to recover losses. Compare probability quality and flat-stake results before attributing an apparent improvement to clever sizing.

**The next milestone is reliable, prospectively recorded probabilities with correct quote and settlement data. Stake sizing can organize an established signal; it cannot create one.**
