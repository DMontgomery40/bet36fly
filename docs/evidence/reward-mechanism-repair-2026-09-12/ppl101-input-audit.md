# PPL101 direct input audit — September12,2026

The two accepted PPL101 cells receive39,125 retained anatomical contacts from4,271 distinct presynaptic neurons. KCs supply24,068contacts (61.52%), but the largest individual upstream contact counts belong to several other annotated neuron types. Both selected home MBON11 cells provide modeled inhibitory feedback. This establishes plausible recurrent routes, not which route caused the measured DAN/KC timing or untaught learning.

No neuron was run, perturbed or removed. The script reads source-locked graph arrays and annotations and writes this audit's own output artifacts. All11 graph/annotation hashes in the measured bridge identity and the relevant protocol/encoder source hashes matched. The source-lock copies agree with the official [MaleCNS v1.0 download resources](https://male-cns.janelia.org/download/); raw annotation SHA256 is independently rechecked against the lock. This is the full set of direct incoming edges **within the retained neuronal graph**, not a claim to enumerate raw contacts from excluded fragments/glia. No new release was downloaded or substituted.

## Exact targets and direct input totals

| Target body ID | Retained index | Released instance | Incoming graph edges | Contacts |
| --- | ---: | --- | ---: | ---: |
|11327|1235|PPL101(y1ped)_R|3,568|18,029|
|11900|1774|PPL101(y1ped)_L|3,711|21,096|

The complete7,279-edge enumeration is `ppl101-direct-inputs.csv`: every presynaptic body ID/index, released class/type/instance, transmitter, integer contact count, modeled sign, gain factors and derived conductance increment. `ppl101-input-audit.json` retains per-target class/type/transmitter aggregates and the20largest-contact cells per target. There are3,373 distinct presynaptic KCs; a KC contacting both targets contributes two separate graph edges.

| Direct source group | Contacts to11327 | Contacts to11900 | Interpretation |
| --- | ---: | ---: | --- |
|Kenyon cells|11,846 from3,068KCs|12,222 from3,100KCs|All listed KC inputs have modeled positive fast sign|
|MBONs|464 from30cells|461 from34cells|Mixed positive and negative modeled signs; net signed count sum is inhibitory|
|ALPN sensory ports|0|1 from body68086|M_lvPNm25_L; the accepted sensory-input factor0 does not zero this outgoing edge|
|APL|49 from2cells|58 from2cells|Both APL cells contribute; modeled GABA output factor0.25|
|Annotated DAN class|281 from23cells|267 from27cells|Their pure-dopamine fast weights are zero in this model|
|CX class|91 from16cells|119 from19cells|Topology alone supplies no task-value interpretation|
|No assigned class field|5,347 from431cells|8,026 from530cells|Retained neurons still have anatomical type/superclass; APL is included here, so this row overlaps the separately shown APL row|

Rows above are not all disjoint because APL is separately highlighted within the unassigned-class group. The JSON's by_target_class table is the nonoverlapping class accounting and sums exactly to each target total. Missing class labels must not be interpreted as absent neurons or unknown connectivity.

## Modeled transmission, not measured synaptic efficacy

The reward constructor begins with float32 `contact_count * presynaptic_sign * (0.275 * global_weight_scale)`; the fixed global scale is0.5, giving nominal0.1375per contact. It then zeros **pure dopamine transmitter labels**, applies target KC/ALPN input factors and source APL output factors. PPL101 is neither a KC nor a sensory port, so its incoming target factor is1. The KC input factor1.25 changes input **onto KCs**; it is not a multiplier on KC→PPL101 output. Likewise ALPN input factor0 suppresses recurrent input **onto those ports**, not their outgoing edges. Selected KC→MBON learning gains do not directly multiply an edge ending at PPL101; its direct plastic gain is1.

The contact-derived weights in the CSV reproduce those float32 arithmetic steps without importing or constructing RewardEngine. They describe the conductance increment from one presynaptic event delivered to a nonrefractory target. The native kernel discards incoming events during refractoriness, so neither a contact sum nor the sum of these increments is a realized current or a time-integrated causal contribution. Multiple delayed events, spike timings, existing conductance and target refractory state matter.

The importer models acetylcholine as positive; GABA/glutamate/histamine as negative; ambiguous/modulator-only labels default positive. This is a presynaptic sign proxy, not reconstructed postsynaptic receptor physiology. In this input set there are133 edges with an ambiguous fast-sign assignment, including pure dopamine later zeroed. Pure-dopamine labels account for763contacts across59incoming edges, more than the548contacts in the annotated DAN-class subset; class and transmitter selection are not interchangeable. Octopamine contributes31contacts to11327 and21to11900 and remains positive under the fast proxy; unclear transmitter contributes226/334contacts. These implementation facts identify limits, not a demonstrated explanation or authorization to change transmitter handling.

## Named feedback and larger input cells

Both home MBON11 cells, bodies10704 and11402, project to both PPL101 targets. Their GABA-labeled contact counts are respectively41and66 to11327 (107total), and33and65 to11900 (98total). Both groups therefore have modeled negative fast sign. Direct inputs from the selected away MBON09 class total19contacts to each PPL101, also GABA-labeled. Other MBONs include excitatory MBON15/MBON29 inputs and inhibitory MBON30/glutamatergic inputs; the complete64MBON-edge list remains in the CSV. An MBON feedback path is present, but its sign and anatomical presence do not establish a learned reinforcement prediction-error computation.

APL bodies10540(APL_R) and10977(APL_L) contribute39and10contacts to11327, and40and18to11900. Applying the fixed0.25APL factor gives combined modeled increments−1.68437505 and−1.99375004. This is the existing spiking APL proxy, not a new claim about graded local APL physiology.

Large individual inputs illustrate why KC contact majority is not a unique causal attribution:

| Target | Presynaptic body/type | Transmitter label | Contacts |
| --- | --- | --- | ---: |
|11327|11038 GNG321|acetylcholine|295|
|11327|17988 SMP053|glutamate|274|
|11327|13576 AVLP563|acetylcholine|247|
|11327|34896 SMP026|acetylcholine|204|
|11327|13526 SMP026|acetylcholine|155|
|11900|17878 GNG321|acetylcholine|365|
|11900|512187 SMP056|glutamate|289|
|11900|13526 SMP026|acetylcholine|288|
|11900|520083 SMP053|glutamate|261|
|11900|12676 AVLP563|acetylcholine|252|

These cell names are annotation identities; no function, natural reinforcement valence, or event contribution is inferred from the names. For example, body11900 itself has78contacts onto11327, but this pure-dopamine fast edge is zero in the reward constructor. Removing the anatomical row from an inventory would conceal the distinction between retained anatomy and implemented fast transmission.

## Relation to the now-failed history hypothesis

Root's33-call capture `onset-history-capture-4343c21535c43f42` completed in50.5556300839seconds. I read its actual summary's complete status/count/falsifier fields and all eight panel/channel/noise metric cells. The kernel worker separately audits its artifacts; this report does not claim to repeat that audit.

Canonical coarse/fine recording and retained-history checks passed. On the unchanged canonical spike histories, continuous filters from0ms with gain writes still beginning100ms make second-panel/base home change more negative: −0.272640034556 to−0.481925711036. The published contrast is−0.209285676479; the attempted double contrast is−0.209285714082. All four home cells fail their unchanged shadow guards, away remains0 and bounds remain0. The predeclared directional and necessary-screen hypotheses are falsified. This was a shadow calculation with no feedback from its altered gains; no continuous-history production rule was implemented.

That result rejects onset warming alone as the proposed repair. It does not select a particular upstream neuron or pathway as the cause. The anatomical audit shows substantial distributed KC input, mixed MBON feedback and other inputs whose actual delivered-event contributions remain unmeasured here. Existing pooled DAN timing, contact counts and modeled signs cannot establish dopamine release, receptor coupling, effective local compartment signaling, or the computational role of a feedback loop. The retained graph is anatomical evidence; the uniform LIF and task-to-DAN/readout interfaces remain engineered.

No home gamma filtering, drive retuning, contact change, new rule, perturbation, threshold change or conditioning follows from this audit. The failed raw, bridge and history-shadow records remain visible. The CSV/JSON provide a cell-specific factual basis for the wiki and for any separately scoped future causal investigation.

## Reproduction and limits

`ppl101-input-audit.py` imports only standard-library readers, NumPy, pandas and Arrow. It verifies source hashes, target identities, source sign consistency, one edge per presynaptic/target pair, and exact sum accounting. It completed successfully in under a second. No repository tests/browser/server were invoked for this read-only data audit. The broader mechanism implementation/capture reviews retain their separate verification receipts.
