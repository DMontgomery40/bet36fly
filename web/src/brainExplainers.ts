export type BrainExplainer = {
  title: string
  summary: string
  paragraphs: string[]
  sources?: { label: string; url: string }[]
}

const anatomySource = {
  label: 'MaleCNS: official dataset and annotations',
  url: 'https://male-cns.janelia.org/download/',
}
const mushroomSource = {
  label: 'Aso et al.: mushroom-body circuitry and associative learning',
  url: 'https://elifesciences.org/articles/04577',
}
const dynamicsSource = {
  label: 'Shiu et al.: computational fly-brain dynamics',
  url: 'https://www.nature.com/articles/s41586-024-07763-9',
}

/** Long explanations are shared by hover previews and the pinned inspector. */
export const EXPLAINERS: Record<string, BrainExplainer> = {
  neurons: {
    title: 'Neurons, synapses and connection lines',
    summary: 'A displayed node represents a reconstructed neuron; a connection line summarizes contacts between two neurons.',
    paragraphs: [
      'A neuron is a cell, while a synapse is a contact through which one cell can influence another. The source dataset assigns each reconstructed neuronal object a body ID. This display uses that ID to connect its position, supplied annotations and recorded simulation activity. The dots are a sample of those objects, not individual synaptic contacts.',
      'Several anatomical contacts can join the same directed pair of cells. BET36FLY aggregates them into one connection with a contact count, so a line does not mean exactly one synapse. The source and target matter: a connection from A to B does not imply a connection from B to A. Inspect a neuron to see its displayed incident connections and their available metadata.',
      'A model neuron has simplified voltage and synaptic state. A model weight controls a connection’s numerical influence. Neither count can be converted directly into an LLM parameter count, an intelligence score or a measurement of understanding.',
    ],
    sources: [anatomySource],
  },
  mushroomBodies: {
    title: 'What are the mushroom bodies?',
    summary: 'Mushroom bodies are fly brain circuits involved in learned associations; their participating cells are highlighted here.',
    paragraphs: [
      'Biological studies describe Kenyon cells, mushroom-body output neurons and modulatory inputs working together in these circuits. Their organization helps researchers study how sensory experiences acquire learned significance. That biological context motivates our choice to adjust existing Kenyon-cell-to-output-neuron connections; it does not validate this program’s sports learning rule.',
      'Violet Kenyon cells and amber output neurons identify annotated populations in that circuitry. Their displayed positions are projections of sampled soma coordinates: positions of cell bodies. They do not reconstruct the mushroom-body lobes, the full paths of neuronal processes or a neuropil surface. There is deliberately no invented mushroom-shaped boundary around them.',
      'A connectome records wiring and annotations, not a saved animal’s complete memories or behavior. The release does not supply a lifetime of neural state, all synaptic physiology or the experiences of the original fly. Our artificial inputs, simplified dynamics and supervised decoder therefore describe an engineering experiment, not a revived animal or a recovered mind.',
    ],
    sources: [mushroomSource, anatomySource],
  },
  kc: {
    title: 'Kenyon cells — KCs',
    summary: 'Kenyon cells are the violet population whose existing connections to MBONs provide this experiment’s trainable region.',
    paragraphs: [
      'Kenyon cells participate in mushroom-body sensory representations. Biological experiments on odor learning motivate studying this circuit, but an individual displayed cell cannot be assigned a sports concept from its location, color or firing. Its inspection panel reports supplied annotations, rather than guessing that it represents a team, a draw or a remembered match.',
      'The retained graph contains 4,064 Kenyon cells. The v2 grouping uses the 15 KC type labels actually supplied by the dataset, including broad labels such as KC and KCg. These broad labels remain broad: the application does not invent a more precise subtype when the source has not provided one.',
      'Only existing connections from KCs to the 97 MBONs belong to the selected plastic support. Other connections remain part of the simulation. Independent learning gives each supported edge its own gain; shared learning ties gains by supplied source and destination type. Hiding violet cells changes the drawing only, leaving all of these computations intact.',
    ],
    sources: [mushroomSource, anatomySource],
  },
  mbon: {
    title: 'Mushroom-body output neurons — MBONs',
    summary: 'MBONs are the amber population whose simulated firing supplies 97 channels of the sports decoder.',
    paragraphs: [
      'In biological mushroom-body circuitry, MBONs receive Kenyon-cell input and connect to other brain regions. Their name describes their anatomical role. It does not mean that these cells naturally output soccer odds, and it does not establish what a particular cell is computing during our artificial stimulus.',
      'BET36FLY retains 97 MBONs with 37 supplied type labels. Their firing rates form the first 97 channels of each readout window, followed by 27 averages over neuronal superclasses. A separately trained numerical decoder turns those measurements into outcome probabilities. No individual MBON is designated as the home, draw or away neuron.',
      'The highlighted plastic connections are the supported KC-to-MBON edges that the experiment permits learning to scale. A rose line identifies eligibility for that learning rule, not proof that its gain changed in the displayed checkpoint. Select a node to inspect its actual body ID, available annotations and recorded activity; position or a bright spike alone cannot reveal biological purpose.',
    ],
    sources: [mushroomSource, anatomySource],
  },
  alpn: {
    title: 'ALPN sensory pathways and artificial sports inputs',
    summary: 'Cyan ALPNs belong to annotated sensory pathways; this model artificially stimulates 32 of them with sports features.',
    paragraphs: [
      'ALPN means antennal-lobe projection neuron. Biological olfactory pathways carry information from the antennal lobe toward downstream circuits, including the mushroom body. Those biological pathways provide context for the selected cells, not evidence that a fly naturally encodes team strength or understands a sports schedule.',
      'The application calculates 16 numerical pregame features from past results. Each has a positive and negative channel, giving 32 artificial stimulation ports chosen from the annotated ALPN catalog. Training-only scaling and a fixed mapping turn feature values into Poisson stimulation. Other ALPNs remain in the graph without that external drive.',
      'All ALPNs are excluded from superclass pooling in the decoder, so the summary readout does not directly read back an input-population average. The rest of the graph still receives their propagated spikes. The cyan display filter never disables stimulation. Changing that filter, rotating the view or inspecting a cell cannot alter the feature values or the model’s prediction.',
    ],
    sources: [mushroomSource, anatomySource],
  },
  weights: {
    title: 'Contact counts, modeled weights and learned gains',
    summary: 'Contact count describes the anatomy; a modeled weight and an optional learned gain determine numerical influence.',
    paragraphs: [
      'The contact count is the number of retained anatomical synaptic contacts for a directed neuron pair. It comes from the dataset and remains distinct from the number of lines displayed. BET36FLY converts it to a starting weight using a presynaptic sign and a fixed per-contact scale of 0.275 mV. That conversion is a model assumption, not a direct measurement of every synapse’s physiological strength.',
      'For supported KC-to-MBON edges, plastic models multiply that starting weight by a learned positive gain. The rule is gain = exp(0.3 × tanh(theta)), bounding it at approximately 0.741 to 1.350. Positive multiplication preserves the original modeled sign and cannot create a missing anatomical edge. Frozen variants use gain one.',
      'Subdued slate lines are ordinary retained connections; rose marks the selected plastic support when enabled. Color does not show whether a connection is excitatory, strong, currently transmitting or beneficial to prediction. Use the connection inspector for its contact count, modeled sign and support membership instead.',
    ],
    sources: [anatomySource, dynamicsSource],
  },
  sharedGains: {
    title: 'Why share 295 gains?',
    summary: 'Shared learning uses one gain for each supported KC-type/MBON-type pair, reducing the number of adjustable connection parameters.',
    paragraphs: [
      'There are 61,210 supported KC-to-MBON edges, but only 295 observed pairs of source KC type and destination MBON type. In a shared model every edge with the same type pair uses the same gain. The grouping is shared across sports and hemispheres. Unsupported type combinations do not become parameters or new connections.',
      'This is a constraint chosen for the experiment, not a claim that biological flies use precisely 295 learning controls. Grouping may reduce overfitting with limited labeled games, or it may remove useful flexibility. The fixed comparison measures that tradeoff against independent learning, which uses one parameter for each of the 61,210 supported edges.',
      'The sports decoder has additional parameters counted separately. A temporal decoder reads four consecutive 20 ms windows and uses the same gains in every window. Shared gains therefore do not mean shared firing rates: cells and time windows can respond differently even when their connection multipliers match. A lower parameter count alone does not establish better forecasting or greater biological realism.',
    ],
    sources: [anatomySource],
  },
  signs: {
    title: 'Excitatory and inhibitory modeling assumptions',
    summary: 'The modeled sign determines whether a transmitted spike pushes a target toward or away from firing.',
    paragraphs: [
      'BET36FLY assigns one coarse sign from each source neuron’s transmitter annotation. Acetylcholine is modeled as positive; GABA, glutamate and histamine as negative. Ambiguous, missing or modulator-only predictions use the documented positive fallback, keeping their edges active. The graph contains 3,718 neurons in this uncertain-sign category.',
      'These rules simplify biological signaling. The model does not resolve every target receptor, chemical interaction or modulatory effect, so a negative modeled weight is not a complete physiological characterization. The inspector distinguishes the annotation from the sign actually used. Missing annotation must remain unavailable rather than becoming an invented transmitter or function.',
      'Learning scales supported weights by positive gains, preserving their signs. Neuron category colors do not encode these signs: violet means KC and amber means MBON, regardless of whether the source’s modeled influence is positive or negative. A firing halo shows a recorded spike, not a switch from inhibition to excitation or a learning event. Numerical stability and visible activity do not establish physiological validity.',
    ],
    sources: [anatomySource, dynamicsSource],
  },
  firing: {
    title: 'Firing is activity; learning changes parameters',
    summary: 'A white halo marks a recorded simulated spike while the neuron keeps its anatomical category color.',
    paragraphs: [
      'Each modeled neuron evolves voltage and synaptic state during an 80 ms trial. Crossing the threshold emits a spike, followed by reset and a refractory period. The displayed activity comes from recorded simulation bins. A cell with no displayed spike may be inactive in that bin; a cell without a recording has unavailable activity, which must not be replaced by an animation.',
      'The active-cell count means cells that fired at least once during the trial. Total spikes counts all firing events, including repeated spikes from one cell. Neither number measures learning, understanding or predictive skill. More visible or active neurons does not establish greater intelligence, and very high rates can reveal a modeling limitation.',
      'Learning occurs in the explicit historical training workflow, which changes bounded gains and decoder parameters. Watching a fixture, replaying it or refreshing public results runs a frozen checkpoint. Each new game resets the transient neural state. Updated historical features can change a prediction while every learned parameter stays exactly the same.',
    ],
    sources: [dynamicsSource],
  },
  sample: {
    title: 'The displayed sample and the computed graph',
    summary: 'The canvas shows a labeled sample of real soma positions; every retained neuron still participates in computation.',
    paragraphs: [
      'Rendering all 166,700 neuronal objects and more than 25 million directed edges would obscure inspection. The display therefore samples neurons with available source coordinates and draws a strong-edge subset between displayed endpoints: at least five anatomical contacts per connection, capped at 3,500 lines. The full graph count, displayed sample count and current visible count describe different sets. Filtering may reduce the visible set without reducing the sampled or computed graph.',
      'Coordinates locate somas, or cell bodies. Lines connect their projected positions to make adjacency inspectable; they do not trace the complete axons, dendrites or microscopic synapse locations. Overlapping dots in one view need not occupy the same three-dimensional position. Rotation changes that projection, and the node selector provides access without precise pointing.',
      'Categories come from annotations matched by body ID. Other annotated cells are light gray; missing or unknown categories are muted gray. Unknown does not mean biologically unimportant. Layer controls change presentation only: they do not silence cells, remove edges, change neural inputs, retrain the decoder or alter saved predictions.',
    ],
    sources: [anatomySource],
  },
  replay: {
    title: 'Recorded simulation replay',
    summary: 'Replay shows the saved spike bins from a completed model trial, not a live recording of a biological fly.',
    paragraphs: [
      'Watch brain runs the current frozen model for the selected fixture, then lets you inspect its recorded 80 ms response. The timeline is simulated time. Playback slows that brief trial so the activity is visible; browser seconds and biological milliseconds are not interchangeable. The execution time reports how long the computer needed to calculate the trial.',
      'Replay and the timeline reuse those recorded values. Moving backward does not reverse the neural equations, and pressing Replay does not perform another training step or generate new evidence. The selected bin supplies the visible spike counts and node activity. Before a valid recording is available, activity remains unavailable rather than being filled with decorative motion.',
      'Changing the viewing angle or hiding a category only changes what you see. The forecast and full-network activity totals remain those of the recorded model trial. Inspect the fixture and model identity alongside the trace when comparing runs; a new fixture, feature revision or checkpoint may produce a different recording and must not be mistaken for the same evidence.',
    ],
    sources: [dynamicsSource],
  },
}
