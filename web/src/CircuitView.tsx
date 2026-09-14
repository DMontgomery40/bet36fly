import { useResource } from './data';
import BrainView from './BrainView';
import type { Brain } from './types';
import './circuit.css';

/**
 * Anatomy page for the MaleCNS v1.0 circuit. It reads the released connectome geometry
 * and never calls a simulator: no prediction, training or replay route is requested here.
 */
export default function CircuitView() {
  const resource = useResource<Brain>('/api/brain');
  const brain = resource.error ? null : resource.data;
  const empty = !!brain && !brain.nodes.length;
  return <div className="circuit-page">
    <section className="page-heading"><span className="eyebrow">Circuit / MaleCNS v1.0</span>
      <h1>The wiring the simulator runs on</h1>
      <p className="lede">A sampled projection of released soma positions and the heaviest connections between them. This is released anatomy, drawn for inspection. It is not a neuropil reconstruction, and nothing on this page runs the circuit or shows its activity.</p>
    </section>
    {resource.error ? <p className="circuit-error" role="alert">{resource.error} No connectome geometry is drawn until this read succeeds.</p> : null}
    {resource.loading && !resource.data && !resource.error ? <p className="circuit-note">Loading the released connectome geometry…</p> : null}
    {empty ? <p className="circuit-empty">The connectome geometry contains no neurons with released soma coordinates on this installation, so there is nothing to draw.</p> : null}
    <BrainView brain={brain} error={resource.error} retry={() => void resource.reload()}/>
    <aside className="scope-note"><strong>What this page does not show</strong>
      <p>Simulated activity, predictions, learned parameters and training history are all absent here by design. The drawing is a sample of neurons with released soma coordinates plus a strong-edge subset among them, so it is neither the full retained graph nor a picture of mushroom-body lobes. Toggling a layer, rotating the view or inspecting a cell changes the drawing only; it never changes a stored annotation, a retained connection or any recorded result.</p>
    </aside>
  </div>;
}
