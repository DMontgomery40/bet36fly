import { useEffect, useRef, useState } from 'react';
import { number } from './data';
import { EXPLAINERS } from './brainExplainers';
import type { Brain, BrainCategory, BrainNode } from './types';

/** The canvas keeps a dark inset ground: every category color clears 6:1 against it,
 *  while the same colors fall below 2.4:1 on the light paper used by the rest of the page. */
export const CANVAS_BACKGROUND = '#19221c';
export const EDGE_STYLE = {
  connections: { color: '#A7B6C4', alpha: .55, width: .9, label: 'Other retained connections' },
  kcmbon: { color: '#F5A3BC', alpha: .85, width: 1.2, label: 'KC→MBON output synapses' },
};
export const CATEGORY_STYLE: Record<BrainCategory, { color: string; shape: string; label: string; explanation: string; radius: number }> = {
  alpn: { color: '#56B4E9', shape: '△', label: 'Sensory ALPNs', explanation: 'alpn', radius: 2.7 },
  kc: { color: '#B79CED', shape: '○', label: 'Kenyon cells', explanation: 'kc', radius: 2.7 },
  mbon: { color: '#E69F00', shape: '◇', label: 'MBONs', explanation: 'mbon', radius: 3 },
  other: { color: '#CBD5E1', shape: '□', label: 'Other annotated neurons', explanation: 'neurons', radius: 1.5 },
  unknown: { color: '#94A3B8', shape: '+', label: 'Unknown annotation', explanation: 'neurons', radius: 1.5 },
};
/** The sampled set is 93% "other", so the annotated circuit populations are drawn last. */
export const DRAW_ORDER: BrainCategory[][] = [['other', 'unknown'], ['alpn', 'kc', 'mbon']];
export function categoryOf(node: BrainNode): BrainCategory { return node.category && node.category in CATEGORY_STYLE ? node.category : 'unknown'; }
export function nodeStyle(node: BrainNode) { return CATEGORY_STYLE[categoryOf(node)]; }
export function projectNodes(nodes: BrainNode[], rotation: number, width: number, height: number) {
  const angle = rotation * Math.PI / 180;
  const projected = nodes.map(node => ({ x: node.x * Math.cos(angle) + node.z * Math.sin(angle), y: -node.y + node.z * .12 }));
  if (!projected.length) return [];
  const minX = Math.min(...projected.map(p => p.x)), maxX = Math.max(...projected.map(p => p.x));
  const minY = Math.min(...projected.map(p => p.y)), maxY = Math.max(...projected.map(p => p.y));
  const scale = Math.max(1, Math.min((width - 56) / (maxX - minX || 1), (height - 100) / (maxY - minY || 1)));
  return projected.map(p => ({ x: (p.x - (maxX + minX) / 2) * scale + width / 2, y: (p.y - (maxY + minY) / 2) * scale + height / 2 + 4 }));
}
export function hitNode(points: { x: number; y: number }[], x: number, y: number, visible: (index: number) => boolean) {
  let selected = -1, distance = 10 * 10;
  points.forEach((point, index) => { const d = (x - point.x) ** 2 + (y - point.y) ** 2; if (visible(index) && d < distance) { selected = index; distance = d; } });
  return selected;
}
type Selection = { kind: 'concept'; key: string } | { kind: 'node'; index: number } | { kind: 'edge'; index: number };
const CONTROLS: Record<string, { title: string; text: string; concept: string }> = {
  angle: { title: 'View angle', text: 'Rotate the projection of the released soma coordinates. The point hit targets rotate and resize with the drawing. This changes the view only; it never changes the stored graph, its annotations or any recorded result.', concept: 'mushroomBodies' },
  counts: { title: 'Displayed and retained counts', text: 'The canvas draws a sample of neurons at their released soma coordinates, plus a strong-edge subset among those sampled neurons. The retained simulator graph is far larger than the sample. Display filters change what is drawn and nothing else.', concept: 'sample' },
};
function Explanation({ name }: { name: string }) {
  const control = CONTROLS[name], explanation = EXPLAINERS[control?.concept || name];
  if (!explanation) return <p>Explanation unavailable.</p>;
  return <><h3>{control?.title || explanation.title}</h3>{control && <p>{control.text}</p>}<p><strong>{explanation.summary}</strong></p>{explanation.paragraphs.map((paragraph, index) => <p key={index}>{paragraph}</p>)}{explanation.sources?.length ? <p className="fine">Sources: {explanation.sources.map(source => <a key={source.url} href={source.url} target="_blank" rel="noreferrer">{source.label} </a>)}</p> : null}</>;
}
export default function BrainView({ brain, error, retry }: { brain: Brain | null; error: string; retry: () => void }) {
  const canvas = useRef<HTMLCanvasElement>(null), inspector = useRef<HTMLDivElement>(null);
  const lastFocus = useRef<HTMLElement | null>(null);
  const projected = useRef<{ x: number; y: number }[]>([]);
  const [rotation, setRotation] = useState(0);
  const [layers, setLayers] = useState({ connections: true, kcmbon: true, alpn: true, kc: true, mbon: true, other: true });
  const [selection, setSelection] = useState<Selection | null>(null), [preview, setPreview] = useState<string | null>(null);
  const [hovered, setHovered] = useState(-1), [search, setSearch] = useState('');
  const visible = (index: number) => { if (!brain?.nodes[index]) return false; const category = categoryOf(brain.nodes[index]); return layers[category === 'unknown' ? 'other' : category]; };
  const edgeLayer = (index: number) => brain?.edge_metadata?.[index]?.plastic ? layers.kcmbon : layers.connections;
  function pin(value: Selection) { if (!selection) lastFocus.current = document.activeElement as HTMLElement; setPreview(null); setSelection(value); }
  function close() { setSelection(null); setPreview(null); lastFocus.current?.focus(); }
  useEffect(() => { if (selection) inspector.current?.focus(); }, [selection]);
  useEffect(() => { const escape = (event: KeyboardEvent) => { if (event.key === 'Escape') close(); }; window.addEventListener('keydown', escape); return () => window.removeEventListener('keydown', escape); }, []);
  useEffect(() => {
    if (!brain || !canvas.current) return;
    const element = canvas.current;
    function draw() {
      const context = element.getContext('2d'); if (!context || !brain) return;
      const bounds = element.getBoundingClientRect(), ratio = Math.min(window.devicePixelRatio || 1, 2);
      element.width = bounds.width * ratio; element.height = bounds.height * ratio;
      context.scale(ratio, ratio); context.clearRect(0, 0, bounds.width, bounds.height);
      context.fillStyle = CANVAS_BACKGROUND; context.fillRect(0, 0, bounds.width, bounds.height);
      const points = projectNodes(brain.nodes, rotation, bounds.width, bounds.height); projected.current = points;
      // Actual anatomical edges stay behind category-colored neuron bodies.
      for (const key of ['connections', 'kcmbon'] as const) {
        if (!layers[key]) continue;
        const style = EDGE_STYLE[key], wanted = key === 'kcmbon';
        context.strokeStyle = style.color; context.globalAlpha = style.alpha; context.lineWidth = style.width; context.beginPath();
        brain.edges.forEach(([a, b], index) => { if (!visible(a) || !visible(b) || !!brain.edge_metadata?.[index]?.plastic !== wanted) return; context.moveTo(points[a].x, points[a].y); context.lineTo(points[b].x, points[b].y); });
        context.stroke(); context.globalAlpha = 1;
      }
      // Background annotations first so the sparse ALPN/KC/MBON populations are never overdrawn.
      for (const pass of DRAW_ORDER) points.forEach((point, index) => {
        if (!visible(index)) return;
        const category = categoryOf(brain.nodes[index]);
        if (!pass.includes(category)) return;
        const style = CATEGORY_STYLE[category], r = style.radius;
        context.fillStyle = style.color; context.strokeStyle = style.color; context.lineWidth = 1.4; context.beginPath();
        if (category === 'alpn') { context.moveTo(point.x, point.y - r * 1.4); context.lineTo(point.x + r * 1.3, point.y + r); context.lineTo(point.x - r * 1.3, point.y + r); context.closePath(); }
        else if (category === 'mbon') { context.moveTo(point.x, point.y - r * 1.4); context.lineTo(point.x + r * 1.4, point.y); context.lineTo(point.x, point.y + r * 1.4); context.lineTo(point.x - r * 1.4, point.y); context.closePath(); }
        else if (category === 'other') context.rect(point.x - r, point.y - r, r * 2, r * 2);
        else if (category === 'unknown') { context.moveTo(point.x - r, point.y); context.lineTo(point.x + r, point.y); context.moveTo(point.x, point.y - r); context.lineTo(point.x, point.y + r); }
        else context.arc(point.x, point.y, r, 0, Math.PI * 2);
        if (category === 'unknown') context.stroke(); else context.fill();
      });
    }
    const observer = new ResizeObserver(draw); observer.observe(element); draw(); return () => observer.disconnect();
  }, [brain, rotation, layers]);
  function info(name: string, label?: string) {
    return <button className="brain-explain" aria-label={`Explain ${label || CONTROLS[name]?.title || EXPLAINERS[name]?.title || name}`} onMouseEnter={() => setPreview(name)} onMouseLeave={() => setPreview(null)} onFocus={() => setPreview(name)} onBlur={() => setPreview(null)} onClick={() => pin({ kind: 'concept', key: name })}>{label || 'ⓘ'}</button>;
  }
  function nodeDetails(index: number) {
    const node = brain?.nodes[index]; if (!node) return <p>Neuron unavailable.</p>;
    const incident = brain!.edges.flatMap(([a, b], edge) => (a === index || b === index) && visible(a) && visible(b) && edgeLayer(edge) ? [edge] : []);
    return <><h3>Neuron {node.id}</h3><p><strong>{node.type}</strong> · {CATEGORY_STYLE[categoryOf(node)].label}</p><p className="fine">{node.classification_source || 'Classification source unavailable.'}</p><p>Released annotations only. This view records no simulated activity for any neuron.</p><dl>{Object.entries(node.annotations || { type: node.type, superclass: node.group }).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value || 'unavailable'}</dd></div>)}</dl><button onClick={() => pin({ kind: 'concept', key: CATEGORY_STYLE[categoryOf(node)].explanation })}>Explain this category</button><h4>Displayed incident connections ({incident.length})</h4><p className="fine">Only actual displayed connections are listed; direction is source → target.</p><ul className="incident-edges">{incident.map(edge => { const [a, b] = brain!.edges[edge]; return <li key={edge}><button aria-label={`Inspect source ${brain!.nodes[a].id}`} onClick={() => pin({ kind: 'node', index: a })}>{brain!.nodes[a].id}</button> → <button aria-label={`Inspect target ${brain!.nodes[b].id}`} onClick={() => pin({ kind: 'node', index: b })}>{brain!.nodes[b].id}</button><button onClick={() => pin({ kind: 'edge', index: edge })}>Connection details</button></li>; })}</ul></>;
  }
  const selectedNode = selection?.kind === 'node' ? selection.index : -1;
  return <section className="brain-section" aria-label="MaleCNS circuit viewer">
    <div className="brain-canvas">
      <div className="brain-caption"><strong>Drosophila melanogaster</strong><span>{brain?.dataset || 'MaleCNS connectome'}</span><small>Sampled soma projection · anatomy only, no activity</small></div>
      {brain?.nodes.length ? <canvas ref={canvas} role="img" aria-label={`Projection of ${number(brain.displayed_neurons)} sampled fly neurons at their released soma coordinates, with a strong-edge subset. Use the neuron selector below for accessible inspection.`} onPointerMove={event => { const bounds = event.currentTarget.getBoundingClientRect(); setHovered(hitNode(projected.current, event.clientX - bounds.left, event.clientY - bounds.top, visible)); }} onPointerLeave={() => setHovered(-1)} onClick={event => { const bounds = event.currentTarget.getBoundingClientRect(); const index = hitNode(projected.current, event.clientX - bounds.left, event.clientY - bounds.top, visible); if (index >= 0) pin({ kind: 'node', index }); }}/> : <div className="canvas-empty" role="status"><strong>{error ? 'Connectome unavailable' : brain ? 'No display neurons available' : 'Loading the connectome…'}</strong>{error && <><p>{error}</p><button onClick={retry}>Retry connectome</button></>}</div>}
      {hovered >= 0 && brain?.nodes[hovered] && <div className="neuron-preview" role="tooltip"><strong>{brain.nodes[hovered].type} · {brain.nodes[hovered].id}</strong><span>{CATEGORY_STYLE[categoryOf(brain.nodes[hovered])].label}</span><span>Click to inspect</span></div>}
      <div className="canvas-bottom"><span>{brain ? `${number(brain.displayed_neurons)} displayed / ${number(brain.total_neurons)} retained` : 'Waiting for released coordinates'} {info('counts')}</span></div>
    </div>
    <div className="brain-legend" aria-label="Anatomical color and shape legend"><strong>Anatomy layers</strong>{(['alpn', 'kc', 'mbon', 'other'] as const).map(category => <div key={category}><label><input type="checkbox" aria-label={category === 'other' ? 'Other / unknown neurons' : CATEGORY_STYLE[category].label} checked={layers[category]} onChange={event => setLayers({ ...layers, [category]: event.target.checked })}/><span className="circuit-swatch" style={{ color: CATEGORY_STYLE[category].color }}>{CATEGORY_STYLE[category].shape}</span> {category === 'other' ? 'Other / unknown neurons' : CATEGORY_STYLE[category].label}</label>{info(CATEGORY_STYLE[category].explanation, `About ${CATEGORY_STYLE[category].label}`)}</div>)}<p className="fine"><span className="circuit-swatch" style={{ color: CATEGORY_STYLE.unknown.color }}>＋</span> Neurons with no released type or superclass share the “other” control.</p>{(['connections', 'kcmbon'] as const).map(layer => <div key={layer}><label><input type="checkbox" aria-label={EDGE_STYLE[layer].label} checked={layers[layer]} onChange={event => setLayers({ ...layers, [layer]: event.target.checked })}/><span className="circuit-swatch" style={{ color: EDGE_STYLE[layer].color }}>─</span> {EDGE_STYLE[layer].label}</label>{info('contacts', `About ${EDGE_STYLE[layer].label}`)}</div>)}</div>
    {error && brain && <p className="circuit-error" role="alert">Connectome data may be stale: {error}</p>}
    <div className="brain-toolbar"><label>View angle <input aria-label="Brain view angle" type="range" min="-60" max="60" value={rotation} onFocus={() => setPreview('angle')} onBlur={() => setPreview(null)} onChange={event => { setHovered(-1); setRotation(Number(event.target.value)); }}/></label>{info('angle')}<button className="small" onFocus={() => setPreview('angle')} onBlur={() => setPreview(null)} onMouseEnter={() => setPreview('angle')} onMouseLeave={() => setPreview(null)} onClick={() => setRotation(0)} disabled={rotation === 0}>Reset view</button></div>
    {brain && <div className="neuron-selector"><label>Find displayed neuron <input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Body ID or annotation type"/></label><label>Inspect neuron <select aria-label="Inspect displayed neuron" value={selectedNode} onChange={event => { const index = Number(event.target.value); if (index >= 0) pin({ kind: 'node', index }); }}><option value={-1}>Select a displayed neuron</option>{brain.nodes.map((node, index) => ({ node, index })).filter(({ node, index }) => visible(index) && `${node.id} ${node.type} ${categoryOf(node)}`.toLowerCase().includes(search.toLowerCase())).map(({ node, index }) => <option key={node.id} value={index}>{node.type} · {node.id} · {CATEGORY_STYLE[categoryOf(node)].label}</option>)}</select></label></div>}
    <div className="brain-concepts" aria-label="Circuit explanation topics">{Object.entries(EXPLAINERS).map(([key, value]) => <span key={key}>{info(key, value.title)}</span>)}</div>
    {preview && !selection && <div className="brain-tooltip" role="tooltip" onMouseEnter={() => setPreview(preview)} onMouseLeave={() => setPreview(null)}><Explanation name={preview}/><p className="fine">Activate the explanation button to pin and read at your own pace.</p></div>}
    {selection && <div className="brain-inspector" ref={inspector} tabIndex={-1} role="dialog" aria-label="Circuit explanation inspector"><button className="inspector-close" onClick={close}>Close inspector (Esc)</button>{selection.kind === 'concept' ? <Explanation name={selection.key}/> : selection.kind === 'node' ? nodeDetails(selection.index) : <><h3>Displayed connection</h3>{brain?.edges[selection.index] && <p>{brain.edges[selection.index].map((index, part) => <span key={part}>{part ? ' → ' : ''}<button onClick={() => pin({ kind: 'node', index })}>Neuron {brain.nodes[index].id}</button></span>)}</p>}<dl><div><dt>Anatomical contact count</dt><dd>{brain?.edge_metadata?.[selection.index]?.contact_count ?? 'unavailable'}</dd></div><div><dt>Modeled presynaptic sign</dt><dd>{brain?.edge_metadata?.[selection.index] ? brain.edge_metadata[selection.index].modeled_sign < 0 ? 'Inhibitory (model assumption)' : 'Excitatory (model assumption)' : 'unavailable'}</dd></div><div><dt>Anatomical category</dt><dd>{brain?.edge_metadata?.[selection.index] ? brain.edge_metadata[selection.index].plastic ? 'Kenyon cell → MBON output synapse' : 'Other retained connection' : 'unavailable'}</dd></div></dl><Explanation name="contacts"/></>}</div>}
    {brain && <details className="coordinate-note"><summary>About this view</summary><p>{brain.coordinate_note}</p><p>This page draws anatomy only. No simulated activity, prediction or learned parameter is displayed here, and opening or filtering the page runs no neural simulation.</p>{info('mushroomBodies', 'Mushroom bodies and this projection')}</details>}
  </section>;
}
