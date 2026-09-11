# How this fly works

**A guide to the first trained BET36FLY, documented September 10, 2026.**

The fly really uses the measured fly connectome. Sports numbers stimulate neurons, spikes travel through the anatomical network, and a trained decoder turns the resulting activity into probabilities. Training changed a small subset of the actual connections. The first experiment works computationally, but **it does not yet predict games better than our simple statistical baseline**.

This guide explains the existing system. Read [confidence, draws and paper bet size](CONFIDENCE_AND_DRAWS.md) for the probability audit, and [the roadmap](ROADMAP.md) for memory, smarter training and the proposed monitoring plan. Those proposed additions are not already running.

## What came from Google and the research collaborators?

The starting point is **MaleCNS v1.0**, the released wiring dataset from HHMI Janelia, Google Research and collaborators. Our importer retains 166,700 annotated neuronal objects, 25,582,938 directed connections between neuron pairs, and 124,177,617 synaptic contacts. Multiple contacts between the same two neurons become one weighted connection. Unresolved fragments and non-neuronal objects are excluded; the import records their counts. The approximately 140,000-neuron female FlyWire brain is a different release. MaleCNS includes the ventral nerve cord as well as the brain. [Official dataset](https://male-cns.janelia.org/download/), [our source lock](connectome-source-lock.json).

A wiring dataset is not a pretrained sports model or a complete recording of a living fly's mind. It tells us which reconstructed neurons connect, with contact counts and annotations. We supply equations that determine how simulated cells react, an interface for sports observations, a learning procedure, and an output decoder.

Our independent C++ simulator uses leaky integrate-and-fire parameters from Shiu and colleagues' 2024 work. Their research evaluated sensorimotor processing; it did not demonstrate sports forecasting. Applying those parameters to this newer graph is our engineering experiment. [Shiu et al.](https://www.nature.com/articles/s41586-024-07763-9), [reference implementation](https://github.com/philshiu/Drosophila_brain_model).

## A neuron is not a weight

**A neuron is a computing unit; a weight describes the influence of a connection or transformation.** Comparing “166,700 fly neurons” with “billions of LLM weights” mixes two different counts.

| Concept | This simulated fly | A transformer language model |
| --- | --- | --- |
| Computing activity | Each cell has changing voltage and synaptic state; crossing a threshold emits a spike. | Numerical activations pass through attention and feed-forward transformations. |
| Weights | A connection's effect starts from contact count × transmitter sign × a scale; some receive learned gains. | Learned matrix entries determine transformations of token representations. |
| Structure | Sparse, recurrent wiring measured from one nervous system. | An architecture designed for processing sequences, with learned attention computations. |
| Time | Explicit 0.2 ms steps and delayed spikes during an 80 ms trial. | Sequence positions and successive computations; not biological milliseconds. |
| What is learned here | Selected connection gains and a sports decoder. | Commonly, predicting tokens during pretraining, with additional adaptation afterward. |
| Input/output | Sixteen numerical observations become stimulation; activity becomes three outcome probabilities. | Tokens become representations, then predictions over tokens. |

The transformer architecture comparison follows the original [Transformer paper](https://arxiv.org/abs/1706.03762); current implementations vary. For the distinction between text pretraining and using examples in a prompt without updating weights, see [Brown et al.](https://arxiv.org/abs/2005.14165). Our fly column describes [the actual simulator](../bet36fly/brain.py) and [learning code](../bet36fly/learning.py).

An LLM can change its answer when given new context while its trained weights stay fixed. That is different from updating those weights through training. Similarly, our fly responds differently to new sports features without learning new connection gains. Persistent knowledge in parameters, temporary computational state, and records in an external database are three distinct forms of memory.

They are similar in useful ways: both transform inputs using many interacting numerical operations; changing parameters changes the response; training uses errors to select parameter updates; both can fit misleading patterns and generalize badly. A larger activation or sharper probability is not evidence of understanding in either system.

The **simulated** fly is also much simpler than a biological fly. A cell here has a few state variables, not a detailed dendritic tree, receptor chemistry, metabolism or a lifetime of embodied learning. We approximate transmitter effects with coarse signs, including a documented fallback for 3,718 uncertain-sign neurons. The graph is biologically sourced; the physiology and learning are approximations. It would be wrong to infer a real fly's cognitive limits from this program's scores.

There is no sound conversion such as “one fly neuron equals 1,000 LLM parameters.” Nor do 124 million contact counts mean 124 million independently learned sports parameters: most contacts are aggregated into pairwise weights, and almost all those weights remain fixed in our experiment.

## What the fly actually receives

For each match, an external feature builder calculates 16 pregame quantities describing team Elo, recent form, win rate, games played, rest, score margins and sport. These use past results. The fly sees the resulting numbers, not team names, written previews, a browser, video, injuries, lineups, bookmaker odds or player statistics. [Feature implementation](../bet36fly/features.py), [data and timing](sports-data.md).

Each feature gets a positive and negative stimulation channel: 32 channels in total. They drive 32 real antennal-lobe projection neurons, or **ALPNs**, selected from the annotated catalog. This is an artificial way of presenting sports information through cells whose biological role is different. It is not evidence that those cells naturally represent Elo or football.

All 166,700 modeled cells advance during a trial. Not all fire: the trained historical pass averaged about 19,333 active cells and 154,456 spikes per trial. Spikes travel over the retained graph. The output consists of 97 mushroom-body output neuron (**MBON**) firing rates plus 27 averages by neuronal superclass. Directly stimulated input cells are excluded from those averages, so the decoder cannot simply read their stimulation back out.

The 124 output quantities are compressed summaries, not a readout of every cell's exact spike timing. That compression and the short trial are possible information bottlenecks worth testing.

```mermaid
flowchart LR
    A[Past results available before the match] --> B[16 numerical features]
    B --> C[32 artificial stimulation channels]
    C --> D[Full measured fly graph: 80 ms simulation]
    D --> E[124 activity summaries]
    E --> F[Trained sport-specific decoder]
    F --> G[Home / draw / away probabilities]
    G --> H[Immutable paper-pick record]
```

Baseball disables the draw output. Soccer predicts the three match-result categories. The current pick is simply the category with the largest probability; it is not a selection based on offered betting value.

## Exactly how this checkpoint was trained

The first completed run is `20260910T232621Z`. It ran on CPU in **676 seconds, about 11.3 minutes**, including two complete passes through the full network for 8,075 historical examples. No Hugging Face credits, remote GPU, LLM or private API key was needed.

### 1. Make a chronological learning problem

| Partition | Period | Soccer | Baseball | Purpose |
| --- | --- | ---: | ---: | --- |
| Training | Available history before July 2025 | 760 | 3,687 | Fit scaling, connection gains and decoders. |
| Validation | July–December 2025 | 186 | 1,165 | Select epochs and baseline regularization. |
| Test | January–August 2026 | 214 | 2,063 | Evaluate the selected model on later games. |

Soccer history starts in the 2023/24 EPL season; baseball history starts in 2024. Features update at a UTC day boundary after a conservative delay of at least 48 hours from scheduled start. Known resumed MLB games without reliable completion timing are excluded from labeled examples. This reduces leakage from late finishes and doubleheaders, but retrospective downloads can still contain corrections whose original publication times are unknown.

Training-only means and standard deviations scale the inputs. Extreme scaled values are clipped to the configured range. Validation and test outcomes do not fit those statistics. The exact selected game rows and split masks are frozen with the run.

### 2. Record the initial brain's responses

Every example is presented to the unmodified graph. Each trial resets neural state and uses seed 42, with the same deterministic random-number procedure for the Poisson stimulus. We record the actual firing responses and Kenyon-cell activity. **Kenyon cells**, or KCs, are the source population for the connections selected for learning.

Resetting matters: game B does not inherit game A's transient voltage state. Past results influence B through its externally calculated features, not through the fly remembering a previous trial.

### 3. Learn gains on existing anatomical connections

The trainable region contains **61,210 existing KC→MBON connections** between 4,064 KCs and 97 MBONs. A supervised, differentiable rate approximation estimates how gain changes would affect the decoder's task loss. This is the training **surrogate**.

Each supported connection receives a positive gain:

```text
gain = exp(0.3 × tanh(trainable_log_gain))
new_connection_weight = original_connection_weight × gain
```

The bound is approximately 0.741–1.350. It preserves each original sign and does not add connections. Unsupported positions in the storage array do not become edges.

We ran 60 epochs with Adam, learning rate 0.018, shuffled batches of up to 256, a penalty discouraging excessive gain changes, and gradient clipping. Loss averages the available sport-specific cross-entropies, so the larger baseball dataset does not dominate solely through its size. **Draws receive no special extra class weight.** Validation selected epoch 4. All 61,210 supported gains changed; selected gains ranged from 0.8151 to 1.0812.

This is supervised learning from known historical outcomes. There is no dopamine reward circuit, pleasure signal for winning, biological reinforcement rule, or exact differentiation through the full spiking simulator in this implementation. The surrogate is an approximation that may learn changes that transfer imperfectly to the real simulation.

### 4. Install the changes in the real graph and run it again

The learned gains are installed on those actual edges. The complete spiking network is rerun for all 8,075 examples. Its measured output changes: mean absolute change in the recorded readout was 5.04 in its firing-rate units.

This second pass is essential. Predictions are ultimately trained and served from the changed **full spiking graph**, not from the faster surrogate's predictions.

### 5. Fit the final decoder and freeze the checkpoint

The final decoder uses `log1p` of measured firing rates, with scaling fitted only on training examples. It has separate soccer and baseball linear heads followed by softmax. Its arrays allocate 750 coefficients and biases; the baseball draw head is masked and does not contribute predictions.

It ran 180 full-batch epochs with AdamW, learning rate 0.025, weight decay 0.03 and gradient clipping. Validation selected epoch 27. The saved checkpoint contains connection gains, feature/readout scaling, and the final decoder arrays. Its SHA256 is:

```text
3b6e7312cc4be07a354df4ff377bd6a05fb3af67effe6b86c67bedfa25bcf76e
```

Code: [experiment orchestration](../bet36fly/experiment.py), [training equations](../bet36fly/learning.py), [neural simulator](../bet36fly/lif.cpp). Local evidence: [run report](../output/runs/20260910T232621Z/report.json) and [split manifest](../output/runs/20260910T232621Z/split-manifest.json). Large run files are local artifacts excluded from Git.

## What did it learn successfully?

We know the network runs, the selected anatomical weights changed, those changes affect spiking responses, and its wiring affects the final probabilities. Silencing the graph changes output probabilities substantially. These establish a functioning, causally used neural component.

We do **not** yet know that this anatomy gives useful sports-prediction advantages.

| Held-out metric | Soccer fly | Soccer feature baseline | Baseball fly | Baseball feature baseline |
| --- | ---: | ---: | ---: | ---: |
| Accuracy, higher is better | 37.4% | 44.9% | 52.1% | 54.0% |
| Log loss, lower is better | 1.189 | 1.062 | 0.700 | 0.686 |
| Brier score, lower is better | 0.707 | 0.645 | 0.506 | 0.493 |
| Top-choice calibration error, lower is better | 0.209 | 0.105 | 0.047 | 0.020 |

The feature baseline is logistic regression using the same pregame information. It beats the fly in both sports on these metrics. Learned wiring also did not consistently improve on the frozen-brain control. More firing, more changed weights and attractive visualization are not substitutes for improved held-out results.

Our existing shuffled-label control shuffles only the final decoder's training labels: its wiring was already trained on true labels. It is not a shuffle of the entire learning pipeline. Likewise, silencing the graph proves dependence but does not show an advantage over equally large random wiring. Those stronger controls are on [the roadmap](ROADMAP.md).

## Does it keep learning while we watch?

**No.** Refreshing fetches games and computes predictions with the frozen checkpoint. Updating past-result features changes what the model receives; it does not update neural weights. The ledger stores proposals, and replay displays recorded simulated activity. Neither operation is training.

The first version already has a modest kind of external memory: historical results, derived team statistics, saved parameters and a durable prediction ledger. Fly’s desk now matches eligible pregame picks to confirmed final scores and charts its record, with public source refresh every 15 minutes while the server runs. It does not yet retrieve analogous games, consult general sports knowledge, settle outcomes into a learning loop, or adjust its own parameters online.

That separation is useful for the next experiment. We can measure a fixed model's forecasts before deciding whether an explicitly versioned replacement is better. [The roadmap](ROADMAP.md) describes how to add memory and learning without losing that comparison.
