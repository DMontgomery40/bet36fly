import { useEffect, useRef, useState } from 'react';
import { number } from './data';
import { EXPLAINERS } from './brainExplainers';
import type { Brain, BrainCategory, BrainNode } from './types';

/** The canvas keeps a dark inset ground: every category color clears 6:1 against it,
 *  while the same colors fall below 2.4:1 on the light paper used by the rest of the page. */
export const CANVAS_BACKGROUND = '#19221c';
/** Hover and selection accent. 11:1 on the canvas ground and used for nothing else. */
export const HIGHLIGHT = '#FFD166';
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

/** Display-only camera. Nothing in here reaches the stored graph or any recorded result. */
export type View = { yaw: number; pitch: number; zoom: number; panX: number; panY: number };
/** Preserves the original fixed tilt (a 0.12 depth term) as the resting pitch. */
export const DEFAULT_PITCH = Math.asin(.12) * 180 / Math.PI;
export const DEFAULT_VIEW: View = { yaw: 0, pitch: DEFAULT_PITCH, zoom: 1, panX: 0, panY: 0 };
export const MIN_ZOOM = .6, MAX_ZOOM = 8, MAX_PITCH = 85, DEGREES_PER_PIXEL = .35, DRAG_SLOP = 3;

export function clamp(value: number, low: number, high: number) { return Math.min(high, Math.max(low, value)); }
export function wrapDegrees(value: number) { return ((value + 180) % 360 + 360) % 360 - 180; }
export function sameView(a: View, b: View) { return (['yaw', 'pitch', 'zoom', 'panX', 'panY'] as const).every(key => a[key] === b[key]); }
export function rotateView(view: View, dx: number, dy: number): View {
  return { ...view, yaw: wrapDegrees(view.yaw + dx * DEGREES_PER_PIXEL), pitch: clamp(view.pitch - dy * DEGREES_PER_PIXEL, -MAX_PITCH, MAX_PITCH) };
}
/** Zoom about a point, so the anatomy under the pointer stays under the pointer. */
export function zoomView(view: View, factor: number, x: number, y: number, width: number, height: number): View {
  const zoom = clamp(view.zoom * factor, MIN_ZOOM, MAX_ZOOM), ratio = zoom / view.zoom;
  return { ...view, zoom, panX: x - width / 2 - (x - width / 2 - view.panX) * ratio, panY: y - height / 2 - (y - height / 2 - view.panY) * ratio };
}
export function categoryOf(node: BrainNode): BrainCategory { return node.category && node.category in CATEGORY_STYLE ? node.category : 'unknown'; }
export function nodeStyle(node: BrainNode) { return CATEGORY_STYLE[categoryOf(node)]; }
export function categoryCounts(nodes: BrainNode[]) {
  const counts: Record<BrainCategory, number> = { alpn: 0, kc: 0, mbon: 0, other: 0, unknown: 0 };
  for (const node of nodes) counts[categoryOf(node)] += 1;
  return counts;
}
export function edgeCounts(brain: Brain) {
  const kcmbon = (brain.edge_metadata || []).filter(edge => edge.plastic).length;
  return { kcmbon, connections: brain.edges.length - kcmbon };
}
export function projectNodes(nodes: BrainNode[], view: View, width: number, height: number) {
  const yaw = view.yaw * Math.PI / 180, pitch = view.pitch * Math.PI / 180;
  const cosYaw = Math.cos(yaw), sinYaw = Math.sin(yaw), cosPitch = Math.cos(pitch), sinPitch = Math.sin(pitch);
  const projected = nodes.map(node => {
    const x = node.x * cosYaw + node.z * sinYaw, depth = -node.x * sinYaw + node.z * cosYaw;
    return { x, y: -(node.y * cosPitch - depth * sinPitch), depth: node.y * sinPitch + depth * cosPitch };
  });
  if (!projected.length) return [];
  const minX = Math.min(...projected.map(p => p.x)), maxX = Math.max(...projected.map(p => p.x));
  const minY = Math.min(...projected.map(p => p.y)), maxY = Math.max(...projected.map(p => p.y));
  const fit = Math.max(1, Math.min((width - 56) / (maxX - minX || 1), (height - 100) / (maxY - minY || 1)));
  const scale = fit * view.zoom;
  // No constant screen nudge here: any unscaled offset would break zoom-about-the-pointer.
  return projected.map(p => ({ x: (p.x - (maxX + minX) / 2) * scale + width / 2 + view.panX, y: (p.y - (maxY + minY) / 2) * scale + height / 2 + view.panY, depth: p.depth }));
}
export function hitNode(points: { x: number; y: number }[], x: number, y: number, visible: (index: number) => boolean) {
  let selected = -1, distance = 10 * 10;
  points.forEach((point, index) => { const d = (x - point.x) ** 2 + (y - point.y) ** 2; if (visible(index) && d < distance) { selected = index; distance = d; } });
  return selected;
}
type Selection = { kind: 'concept'; key: string } | { kind: 'node'; index: number } | { kind: 'edge'; index: number };
const CONTROLS: Record<string, { title: string; text: string; concept: string }> = {
  view: { title: 'Rotate, zoom and pan', text: 'Drag the canvas to rotate the projection of the released soma coordinates, scroll to zoom about the pointer, and shift-drag to pan. Focus the canvas for the same controls from the keyboard. The point hit targets move with the drawing. These are camera controls: they never change the stored graph, its annotations or any recorded result.', concept: 'mushroomBodies' },
  counts: { title: 'Displayed, visible and retained counts', text: 'The canvas draws a sample of neurons at their released soma coordinates, plus a strong-edge subset among those sampled neurons. The visible count is what the current layer filters leave on screen. The retained simulator graph is far larger than the sample, and no control here changes it.', concept: 'sample' },
};
function Explanation({ name }: { name: string }) {
  const control = CONTROLS[name], explanation = EXPLAINERS[control?.concept || name];
  if (!explanation) return <p>Explanation unavailable.</p>;
  return <><h3>{control?.title || explanation.title}</h3>{control && <p>{control.text}</p>}<p><strong>{explanation.summary}</strong></p>{explanation.paragraphs.map((paragraph, index) => <p key={index}>{paragraph}</p>)}{explanation.sources?.length ? <p className="fine">Sources: {explanation.sources.map(source => <a key={source.url} href={source.url} target="_blank" rel="noreferrer">{source.label} </a>)}</p> : null}</>;
}
export default function BrainView({ brain, error, retry }: { brain: Brain | null; error: string; retry: () => void }) {
  const canvas = useRef<HTMLCanvasElement>(null), inspector = useRef<HTMLDivElement>(null);
  const lastFocus = useRef<HTMLElement | null>(null);
  const projected = useRef<ReturnType<typeof projectNodes>>([]);
  const drag = useRef<{ mode: 'rotate' | 'pan'; x: number; y: number; moved: boolean; view: View } | null>(null);
  const [view, setView] = useState<View>(DEFAULT_VIEW);
  const [layers, setLayers] = useState({ connections: true, kcmbon: true, alpn: true, kc: true, mbon: true, other: true });
  const [selection, setSelection] = useState<Selection | null>(null), [preview, setPreview] = useState<string | null>(null);
  const [hovered, setHovered] = useState(-1), [search, setSearch] = useState('');
  const drawn = !!brain?.nodes.length;
  const visible = (index: number) => { if (!brain?.nodes[index]) return false; const category = categoryOf(brain.nodes[index]); return layers[category === 'unknown' ? 'other' : category]; };
  const edgeLayer = (index: number) => brain?.edge_metadata?.[index]?.plastic ? layers.kcmbon : layers.connections;
  const selectedNode = selection?.kind === 'node' ? selection.index : -1;
  const focused = selectedNode >= 0 ? selectedNode : hovered;
  function pin(value: Selection) { if (!selection) lastFocus.current = document.activeElement as HTMLElement; setPreview(null); setSelection(value); }
  function close() { setSelection(null); setPreview(null); lastFocus.current?.focus(); }
  function zoomBy(factor: number) {
    const bounds = canvas.current?.getBoundingClientRect();
    setView(current => zoomView(current, factor, (bounds?.width || 0) / 2, (bounds?.height || 0) / 2, bounds?.width || 0, bounds?.height || 0));
  }
  useEffect(() => { if (selection) inspector.current?.focus(); }, [selection]);
  useEffect(() => { const escape = (event: KeyboardEvent) => { if (event.key === 'Escape') close(); }; window.addEventListener('keydown', escape); return () => window.removeEventListener('keydown', escape); }, []);
  // A non-passive listener is required to stop the page scrolling while the canvas zooms.
  useEffect(() => {
    const element = canvas.current; if (!element) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      const bounds = element.getBoundingClientRect();
      setView(current => zoomView(current, Math.exp(-event.deltaY * .0015), event.clientX - bounds.left, event.clientY - bounds.top, bounds.width, bounds.height));
    };
    element.addEventListener('wheel', onWheel, { passive: false });
    return () => element.removeEventListener('wheel', onWheel);
  }, [drawn]);
  useEffect(() => {
    if (!brain || !canvas.current) return;
    const element = canvas.current;
    function draw() {
      const context = element.getContext('2d'); if (!context || !brain) return;
      const bounds = element.getBoundingClientRect(), ratio = Math.min(window.devicePixelRatio || 1, 2);
      element.width = bounds.width * ratio; element.height = bounds.height * ratio;
      context.scale(ratio, ratio); context.clearRect(0, 0, bounds.width, bounds.height);
      context.fillStyle = CANVAS_BACKGROUND; context.fillRect(0, 0, bounds.width, bounds.height);
      const points = projectNodes(brain.nodes, view, bounds.width, bounds.height); projected.current = points;
      // Actual anatomical edges stay behind category-colored neuron bodies.
      for (const key of ['connections', 'kcmbon'] as const) {
        if (!layers[key]) continue;
        const style = EDGE_STYLE[key], wanted = key === 'kcmbon';
        context.strokeStyle = style.color; context.globalAlpha = style.alpha; context.lineWidth = style.width; context.beginPath();
        brain.edges.forEach(([a, b], index) => { if (!visible(a) || !visible(b) || !!brain.edge_metadata?.[index]?.plastic !== wanted) return; context.moveTo(points[a].x, points[a].y); context.lineTo(points[b].x, points[b].y); });
        context.stroke(); context.globalAlpha = 1;
      }
      // The focused neuron's own displayed connections, so inspection has a visual anchor.
      if (focused >= 0 && visible(focused)) {
        context.strokeStyle = HIGHLIGHT; context.globalAlpha = .95; context.lineWidth = 1.6; context.beginPath();
        brain.edges.forEach(([a, b], index) => { if ((a !== focused && b !== focused) || !visible(a) || !visible(b) || !edgeLayer(index)) return; context.moveTo(points[a].x, points[a].y); context.lineTo(points[b].x, points[b].y); });
        context.stroke(); context.globalAlpha = 1;
      }
      // Background annotations first, then the sparse populations, each pass far-to-near.
      for (const pass of DRAW_ORDER) {
        const indices = points.map((point, index) => ({ point, index })).filter(({ index }) => visible(index) && pass.includes(categoryOf(brain.nodes[index])));
        indices.sort((a, b) => a.point.depth - b.point.depth);
        for (const { point, index } of indices) {
          const category = categoryOf(brain.nodes[index]), style = CATEGORY_STYLE[category], r = style.radius;
          context.fillStyle = style.color; context.strokeStyle = style.color; context.lineWidth = 1.4; context.beginPath();
          if (category === 'alpn') { context.moveTo(point.x, point.y - r * 1.4); context.lineTo(point.x + r * 1.3, point.y + r); context.lineTo(point.x - r * 1.3, point.y + r); context.closePath(); }
          else if (category === 'mbon') { context.moveTo(point.x, point.y - r * 1.4); context.lineTo(point.x + r * 1.4, point.y); context.lineTo(point.x, point.y + r * 1.4); context.lineTo(point.x - r * 1.4, point.y); context.closePath(); }
          else if (category === 'other') context.rect(point.x - r, point.y - r, r * 2, r * 2);
          else if (category === 'unknown') { context.moveTo(point.x - r, point.y); context.lineTo(point.x + r, point.y); context.moveTo(point.x, point.y - r); context.lineTo(point.x, point.y + r); }
          else context.arc(point.x, point.y, r, 0, Math.PI * 2);
          if (category === 'unknown') context.stroke(); else context.fill();
        }
      }
      if (focused >= 0 && visible(focused) && points[focused]) {
        const point = points[focused], ring = CATEGORY_STYLE[categoryOf(brain.nodes[focused])].radius + (focused === selectedNode ? 6 : 4);
        context.strokeStyle = HIGHLIGHT; context.lineWidth = focused === selectedNode ? 2.2 : 1.4;
        context.beginPath(); context.arc(point.x, point.y, ring, 0, Math.PI * 2); context.stroke();
      }
    }
    const observer = new ResizeObserver(draw); observer.observe(element); draw(); return () => observer.disconnect();
  }, [brain, view, layers, hovered, selection]);
  function pointFrom(event: { clientX: number; clientY: number; currentTarget: HTMLCanvasElement }) {
    const bounds = event.currentTarget.getBoundingClientRect();
    return { x: event.clientX - bounds.left, y: event.clientY - bounds.top, width: bounds.width, height: bounds.height };
  }
  function onPointerDown(event: React.PointerEvent<HTMLCanvasElement>) {
    // Deliberately no setPointerCapture here: capturing on every press makes the browser
    // drop the second click of a double-click, which would kill double-click-to-reset.
    drag.current = { mode: event.shiftKey || event.button === 1 ? 'pan' : 'rotate', x: event.clientX, y: event.clientY, moved: false, view };
    setHovered(-1);
  }
  function onPointerMove(event: React.PointerEvent<HTMLCanvasElement>) {
    const state = drag.current;
    if (!state) { const p = pointFrom(event); setHovered(hitNode(projected.current, p.x, p.y, visible)); return; }
    const dx = event.clientX - state.x, dy = event.clientY - state.y;
    if (!state.moved) {
      if (Math.abs(dx) <= DRAG_SLOP && Math.abs(dy) <= DRAG_SLOP) return;
      state.moved = true;
      // Capture once a real drag begins, so the camera keeps following outside the canvas.
      event.currentTarget.setPointerCapture?.(event.pointerId);
    }
    setView(state.mode === 'pan' ? { ...state.view, panX: state.view.panX + dx, panY: state.view.panY + dy } : rotateView(state.view, dx, dy));
  }
  function onPointerUp(event: React.PointerEvent<HTMLCanvasElement>) {
    const state = drag.current; drag.current = null;
    // A drag that ends over a neuron must not open the inspector; only a real click does.
    if (!state || state.moved || state.mode === 'pan') return;
    const p = pointFrom(event), index = hitNode(projected.current, p.x, p.y, visible);
    if (index >= 0) pin({ kind: 'node', index });
  }
  function onKeyDown(event: React.KeyboardEvent<HTMLCanvasElement>) {
    const step = event.shiftKey ? 15 : 5;
    const rotate: Record<string, [number, number]> = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
    if (rotate[event.key]) { event.preventDefault(); const [dx, dy] = rotate[event.key]; setView(current => rotateView(current, dx / DEGREES_PER_PIXEL, dy / DEGREES_PER_PIXEL)); return; }
    if (event.key === '+' || event.key === '=') { event.preventDefault(); zoomBy(1.25); }
    else if (event.key === '-' || event.key === '_') { event.preventDefault(); zoomBy(.8); }
    else if (event.key === '0') { event.preventDefault(); setView(DEFAULT_VIEW); }
  }
  function info(name: string, label?: string) {
    return <button className="brain-explain" aria-label={`Explain ${label || CONTROLS[name]?.title || EXPLAINERS[name]?.title || name}`} onMouseEnter={() => setPreview(name)} onMouseLeave={() => setPreview(null)} onFocus={() => setPreview(name)} onBlur={() => setPreview(null)} onClick={() => pin({ kind: 'concept', key: name })}>{label || 'ⓘ'}</button>;
  }
  function nodeDetails(index: number) {
    const node = brain?.nodes[index]; if (!node) return <p>Neuron unavailable.</p>;
    const incident = brain!.edges.flatMap(([a, b], edge) => (a === index || b === index) && visible(a) && visible(b) && edgeLayer(edge) ? [edge] : []);
    return <><h3>Neuron {node.id}</h3><p><strong>{node.type}</strong> · {CATEGORY_STYLE[categoryOf(node)].label}</p><p className="fine">{node.classification_source || 'Classification source unavailable.'}</p><p>Released annotations only. This view records no simulated activity for any neuron.</p><dl>{Object.entries(node.annotations || { type: node.type, superclass: node.group }).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value || 'unavailable'}</dd></div>)}</dl><button onClick={() => pin({ kind: 'concept', key: CATEGORY_STYLE[categoryOf(node)].explanation })}>Explain this category</button><h4>Displayed incident connections ({incident.length})</h4><p className="fine">Only actual displayed connections are listed; direction is source → target.</p><ul className="incident-edges">{incident.map(edge => { const [a, b] = brain!.edges[edge]; return <li key={edge}><button aria-label={`Inspect source ${brain!.nodes[a].id}`} onClick={() => pin({ kind: 'node', index: a })}>{brain!.nodes[a].id}</button> → <button aria-label={`Inspect target ${brain!.nodes[b].id}`} onClick={() => pin({ kind: 'node', index: b })}>{brain!.nodes[b].id}</button><button onClick={() => pin({ kind: 'edge', index: edge })}>Connection details</button></li>; })}</ul></>;
  }
  const counts = brain ? categoryCounts(brain.nodes) : null;
  const edges = brain ? edgeCounts(brain) : null;
  const shown = brain ? brain.nodes.reduce((total, _node, index) => total + (visible(index) ? 1 : 0), 0) : 0;
  return <section className="brain-section" aria-label="MaleCNS circuit viewer">
    <div className="brain-canvas">
      <div className="brain-caption"><strong>Drosophila melanogaster</strong><span>{brain?.dataset || 'MaleCNS connectome'}</span><small>Sampled soma projection · anatomy only, no activity</small></div>
      {drawn ? <canvas ref={canvas} role="img" tabIndex={0} aria-describedby="circuit-canvas-hint"
        data-view={`${view.yaw.toFixed(1)},${view.pitch.toFixed(1)},${view.zoom.toFixed(2)}`}
        aria-label={`Projection of ${number(brain!.displayed_neurons)} sampled fly neurons at their released soma coordinates, with a strong-edge subset. Drag to rotate, scroll to zoom, shift-drag to pan, or use the neuron selector below for accessible inspection.`}
        onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerCancel={() => { drag.current = null; }}
        onPointerLeave={() => { if (!drag.current) setHovered(-1); }} onDoubleClick={() => setView(DEFAULT_VIEW)} onKeyDown={onKeyDown}/>
        : <div className="canvas-empty" role="status"><strong>{error ? 'Connectome unavailable' : brain ? 'No display neurons available' : 'Loading the connectome…'}</strong>{error && <><p>{error}</p><button onClick={retry}>Retry connectome</button></>}</div>}
      {hovered >= 0 && brain?.nodes[hovered] && <div className="neuron-preview" role="tooltip"><strong>{brain.nodes[hovered].type} · {brain.nodes[hovered].id}</strong><span>{CATEGORY_STYLE[categoryOf(brain.nodes[hovered])].label}</span><span>Click to inspect</span></div>}
      {drawn && <div className="canvas-bottom"><span>{number(shown)} visible / {number(brain!.displayed_neurons)} displayed / {number(brain!.total_neurons)} retained {info('counts')}</span></div>}
    </div>
    {drawn && <>
      <div className="brain-legend" aria-label="Anatomical color and shape legend"><strong>Anatomy layers</strong>{(['alpn', 'kc', 'mbon', 'other'] as const).map(category => <div key={category}><label><input type="checkbox" aria-label={category === 'other' ? 'Other / unknown neurons' : CATEGORY_STYLE[category].label} checked={layers[category]} onChange={event => setLayers({ ...layers, [category]: event.target.checked })}/><span className="circuit-swatch" style={{ color: CATEGORY_STYLE[category].color }}>{CATEGORY_STYLE[category].shape}</span> {category === 'other' ? 'Other / unknown neurons' : CATEGORY_STYLE[category].label} <b>({number(category === 'other' ? counts!.other + counts!.unknown : counts![category])})</b></label>{info(CATEGORY_STYLE[category].explanation, `About ${CATEGORY_STYLE[category].label}`)}</div>)}<p className="fine"><span className="circuit-swatch" style={{ color: CATEGORY_STYLE.unknown.color }}>＋</span> Neurons with no released type or superclass share the “other” control.</p>{(['connections', 'kcmbon'] as const).map(layer => <div key={layer}><label><input type="checkbox" aria-label={EDGE_STYLE[layer].label} checked={layers[layer]} onChange={event => setLayers({ ...layers, [layer]: event.target.checked })}/><span className="circuit-swatch" style={{ color: EDGE_STYLE[layer].color }}>─</span> {EDGE_STYLE[layer].label} <b>({number(edges![layer])})</b></label>{info('contacts', `About ${EDGE_STYLE[layer].label}`)}</div>)}<p className="fine"><span className="circuit-swatch" style={{ color: HIGHLIGHT }}>◎</span> Gold marks the hovered or inspected neuron and its displayed connections.</p></div>
      {error && <p className="circuit-error" role="alert">Connectome data may be stale: {error}</p>}
      <p className="circuit-hint" id="circuit-canvas-hint">Drag to rotate · scroll to zoom about the pointer · shift-drag to pan · click a neuron to inspect it · double-click empty space to reset. On a touch screen a horizontal drag rotates, and tilt and zoom stay on the sliders and buttons below. With the canvas focused, arrow keys rotate, <kbd>+</kbd> and <kbd>−</kbd> zoom and <kbd>0</kbd> resets. Every one of these is a camera control: they change the drawing only.</p>
      <div className="brain-toolbar">
        <label>View angle <input aria-label="Brain view angle" type="range" min="-180" max="180" step="1" value={Math.round(view.yaw)} onFocus={() => setPreview('view')} onBlur={() => setPreview(null)} onChange={event => { setHovered(-1); setView(current => ({ ...current, yaw: Number(event.target.value) })); }}/></label>
        <label>Tilt <input aria-label="Brain view tilt" type="range" min={-MAX_PITCH} max={MAX_PITCH} step="1" value={Math.round(view.pitch)} onFocus={() => setPreview('view')} onBlur={() => setPreview(null)} onChange={event => { setHovered(-1); setView(current => ({ ...current, pitch: Number(event.target.value) })); }}/></label>
        {info('view')}
        <span className="zoom-readout" aria-live="off">{view.zoom.toFixed(1)}×</span>
        <button className="small" aria-label="Zoom out" onClick={() => zoomBy(.8)} disabled={view.zoom <= MIN_ZOOM}>−</button>
        <button className="small" aria-label="Zoom in" onClick={() => zoomBy(1.25)} disabled={view.zoom >= MAX_ZOOM}>+</button>
        <button className="small reset-view" onFocus={() => setPreview('view')} onBlur={() => setPreview(null)} onMouseEnter={() => setPreview('view')} onMouseLeave={() => setPreview(null)} onClick={() => setView(DEFAULT_VIEW)} disabled={sameView(view, DEFAULT_VIEW)}>Reset view</button>
      </div>
      <div className="neuron-selector"><label>Find displayed neuron <input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Body ID or annotation type"/></label><label>Inspect neuron <select aria-label="Inspect displayed neuron" value={selectedNode} onChange={event => { const index = Number(event.target.value); if (index >= 0) pin({ kind: 'node', index }); }}><option value={-1}>Select a displayed neuron</option>{brain!.nodes.map((node, index) => ({ node, index })).filter(({ node, index }) => visible(index) && `${node.id} ${node.type} ${categoryOf(node)}`.toLowerCase().includes(search.toLowerCase())).map(({ node, index }) => <option key={node.id} value={index}>{node.type} · {node.id} · {CATEGORY_STYLE[categoryOf(node)].label}</option>)}</select></label></div>
      <div className="brain-concepts" aria-label="Circuit explanation topics">{Object.entries(EXPLAINERS).map(([key, value]) => <span key={key}>{info(key, value.title)}</span>)}</div>
    </>}
    {preview && !selection && <div className="brain-tooltip" role="tooltip" onMouseEnter={() => setPreview(preview)} onMouseLeave={() => setPreview(null)}><Explanation name={preview}/><p className="fine">Activate the explanation button to pin and read at your own pace.</p></div>}
    {selection && <div className="brain-inspector" ref={inspector} tabIndex={-1} role="dialog" aria-label="Circuit explanation inspector"><button className="inspector-close" onClick={close}>Close inspector (Esc)</button>{selection.kind === 'concept' ? <Explanation name={selection.key}/> : selection.kind === 'node' ? nodeDetails(selection.index) : <><h3>Displayed connection</h3>{brain?.edges[selection.index] && <p>{brain.edges[selection.index].map((index, part) => <span key={part}>{part ? ' → ' : ''}<button onClick={() => pin({ kind: 'node', index })}>Neuron {brain.nodes[index].id}</button></span>)}</p>}<dl><div><dt>Anatomical contact count</dt><dd>{brain?.edge_metadata?.[selection.index]?.contact_count ?? 'unavailable'}</dd></div><div><dt>Modeled presynaptic sign</dt><dd>{brain?.edge_metadata?.[selection.index] ? brain.edge_metadata[selection.index].modeled_sign < 0 ? 'Inhibitory (model assumption)' : 'Excitatory (model assumption)' : 'unavailable'}</dd></div><div><dt>Anatomical category</dt><dd>{brain?.edge_metadata?.[selection.index] ? brain.edge_metadata[selection.index].plastic ? 'Kenyon cell → MBON output synapse' : 'Other retained connection' : 'unavailable'}</dd></div></dl><Explanation name="contacts"/></>}</div>}
    {drawn && <details className="coordinate-note"><summary>About this view</summary><p>{brain!.coordinate_note}</p><p>This page draws anatomy only. No simulated activity, prediction or learned parameter is displayed here, and opening, rotating, zooming or filtering the page runs no neural simulation.</p>{info('mushroomBodies', 'Mushroom bodies and this projection')}</details>}
  </section>;
}
