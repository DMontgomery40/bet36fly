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
  label: 'Shiu et al.: computational fly-brain dynamics (female FlyWire release)',
  url: 'https://www.nature.com/articles/s41586-024-07763-9',
}

/**
 * Anatomy-only explanations shared by hover previews and the pinned inspector.
 * Every entry keeps three things apart: biology documented in real flies, information
 * present in the released MaleCNS v1.0 dataset, and mechanisms implemented in this
 * simulator. This page displays no activity, prediction or learned parameter, so no
 * topic here describes training, decoding, replay or a pick.
 */
export const EXPLAINERS: Record<string, BrainExplainer> = {
  sample: {
    title: 'The displayed sample and the retained graph',
    summary: 'The canvas shows a sample of released soma positions; the retained simulator graph is far larger than what is drawn.',
    paragraphs: [
      'Drawing every retained neuron and directed pair would obscure inspection. This view therefore samples 2,500 neurons that have released soma coordinates, keeping coverage of the annotated ALPN, Kenyon-cell and MBON populations, and draws a strong-edge subset between the sampled neurons: at least five anatomical contacts per connection, capped at the 3,500 heaviest. The retained count, the displayed sample and the currently visible set are three different numbers.',
      'Coordinates locate somas, the cell bodies. Lines connect their projected positions so adjacency can be inspected; they do not trace axons, dendrites or the microscopic locations of individual contacts. Two dots that overlap in one projection need not be close in three dimensions. Rotation changes only the projection, and the neuron selector provides the same access without precise pointing.',
      'Categories come from released annotations matched by body ID. A neuron is shown as an ALPN when its released class annotation is ALPN, and as Kenyon cell or MBON by the corresponding retained population. Everything else is "other" when the release supplies a type or superclass, and "unknown" when it supplies neither. Unknown means the annotation is absent, not that the cell is unimportant. Layer controls change presentation only: they do not remove neurons or connections from the stored graph and they start no simulation.',
    ],
    sources: [anatomySource],
  },
  neurons: {
    title: 'Neurons, synapses and connection lines',
    summary: 'A displayed node represents a reconstructed neuron; a connection line summarizes contacts between two neurons.',
    paragraphs: [
      'A neuron is a cell, while a synapse is a contact through which one cell can influence another. The source dataset assigns each reconstructed neuronal object a body ID. This display uses that ID to connect its position to its supplied annotations. The dots are a sample of those objects, not individual synaptic contacts.',
      'Several anatomical contacts can join the same directed pair of cells. BET36FLY aggregates them into one connection with a contact count, so a line does not mean exactly one synapse. Source and target matter: a connection from A to B does not imply a connection from B to A. Inspect a neuron to see its displayed incident connections and their available metadata.',
      'A model neuron in this simulator has simplified voltage and synaptic state, and a model weight controls a connection’s numerical influence. Neither the neuron count nor the connection count can be converted into an LLM parameter count, an intelligence score or a measurement of understanding.',
    ],
    sources: [anatomySource],
  },
  mushroomBodies: {
    title: 'What are the mushroom bodies?',
    summary: 'Mushroom bodies are fly brain circuits involved in learned associations; their participating cells are highlighted here.',
    paragraphs: [
      'Biological studies describe Kenyon cells, mushroom-body output neurons and modulatory inputs working together in these circuits. Their organization helps researchers study how sensory experiences acquire learned significance. That biological context explains why this view highlights those populations; it establishes nothing about what this program computes.',
      'Violet Kenyon cells and amber output neurons identify annotated populations in that circuitry. Their displayed positions are projections of sampled soma coordinates: positions of cell bodies. They do not reconstruct the mushroom-body lobes, the full paths of neuronal processes or a neuropil surface. There is deliberately no invented mushroom-shaped boundary around them.',
      'A connectome records wiring and annotations, not a saved animal’s memories or behavior. The release does not supply a lifetime of neural state, complete synaptic physiology or the experiences of the original fly. This projection is therefore a drawing of released anatomy, not a revived animal or a recovered mind.',
    ],
    sources: [mushroomSource, anatomySource],
  },
  alpn: {
    title: 'ALPNs — antennal-lobe projection neurons',
    summary: 'Cyan ALPNs are the neurons whose released class annotation is ALPN.',
    paragraphs: [
      'ALPN means antennal-lobe projection neuron. In biological flies, olfactory pathways carry information from the antennal lobe toward downstream circuits, including the mushroom body. That biological role is why these cells are drawn as a distinct category; it is not evidence that a fly naturally encodes anything about a sports schedule.',
      'Membership in this category is a dataset fact, not an inference: the retained ALPN population is exactly the set of neurons whose released class annotation reads ALPN. Cells whose annotation is missing or different are not added to it, and no more precise subtype is invented when the release has not supplied one.',
      'Hiding or showing the cyan layer changes the drawing only. It does not stimulate, silence or reconfigure any neuron, and this page never delivers input to the circuit.',
    ],
    sources: [mushroomSource, anatomySource],
  },
  kc: {
    title: 'Kenyon cells — KCs',
    summary: 'Kenyon cells are the violet population; in biological flies they carry mushroom-body sensory representations.',
    paragraphs: [
      'Kenyon cells participate in mushroom-body sensory representations, and biological experiments on odor learning motivate studying this circuit. An individual displayed cell cannot be assigned a meaning from its location or color. Its inspection panel reports the supplied annotations rather than guessing what the cell represents.',
      'The category shown here is the retained Kenyon-cell population resolved by body ID against the released annotations. Broad released labels such as KC and KCg stay broad; the application does not refine them.',
      'Kenyon-cell axons contacting MBONs form the output synapses drawn as the separate rose layer. On this page that layer is an anatomical category and nothing more. It carries no claim that any of those synapses has been modified.',
    ],
    sources: [mushroomSource, anatomySource],
  },
  mbon: {
    title: 'Mushroom-body output neurons — MBONs',
    summary: 'MBONs are the amber population; in biological flies they receive Kenyon-cell input and project to other brain regions.',
    paragraphs: [
      'In biological mushroom-body circuitry, MBONs receive Kenyon-cell input and connect onward to other brain regions. Their name describes that anatomical role. It does not mean these cells naturally output anything about sports, and this view measures nothing about what any cell computes.',
      'The retained MBON population is resolved by body ID against the released annotations, and the display keeps the supplied type labels. No individual MBON is designated as a home, draw or away neuron anywhere in this application.',
      'Select a node to inspect its actual body ID and available annotations. Position, color and shape carry only the category; they cannot reveal a cell’s biological purpose.',
    ],
    sources: [mushroomSource, anatomySource],
  },
  contacts: {
    title: 'Contact counts and modeled connection sign',
    summary: 'Contact count describes released anatomy; the modeled sign is an assumption this simulator adds on top of it.',
    paragraphs: [
      'The contact count is the number of retained anatomical synaptic contacts for a directed neuron pair. It comes from the dataset. The displayed subset keeps connections with at least five contacts, so a drawn line is a comparatively heavy pair and most retained connections are not drawn at all.',
      'The simulator converts a contact count into a starting weight using a per-contact scale and a presynaptic sign. That conversion is a model assumption, not a measurement of any synapse’s physiological strength. The inspector reports the released contact count and the assumed sign as separate fields so the two are never conflated.',
      'Line color marks the anatomical category only: rose for Kenyon-cell-to-MBON output synapses, slate for every other retained connection. Color does not show whether a connection is excitatory, strong or currently transmitting, and this view shows no transmission at all. Use the connection inspector for the recorded contact count and the modeled sign.',
    ],
    sources: [anatomySource],
  },
  signs: {
    title: 'Excitatory and inhibitory modeling assumptions',
    summary: 'The modeled sign determines whether a transmitted spike would push a target toward or away from firing.',
    paragraphs: [
      'BET36FLY assigns one coarse sign from each source neuron’s transmitter annotation. Acetylcholine is modeled as positive; GABA, glutamate and histamine as negative. Ambiguous, missing or modulator-only transmitter calls use the documented positive fallback, keeping their edges active. The retained graph contains 3,718 neurons in this uncertain-sign category.',
      'These rules simplify biological signaling. The model does not resolve every target receptor, chemical interaction or modulatory effect, so a negative modeled weight is not a complete physiological characterization. The inspector distinguishes the released transmitter annotation from the sign actually used, and a missing annotation stays unavailable rather than becoming an invented transmitter. Shiu et al. apply a comparable transmitter-to-sign convention on the female FlyWire release, which is a different dataset from the male CNS drawn here.',
      'Category colors do not encode these signs: violet means Kenyon cell and amber means MBON regardless of the modeled influence of that cell. Numerical stability in a simulation does not establish physiological validity.',
    ],
    sources: [anatomySource, dynamicsSource],
  },
}
