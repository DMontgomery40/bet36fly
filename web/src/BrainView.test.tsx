import { beforeEach, expect, it, vi } from 'vitest';
import type { ReactElement, ReactNode } from 'react';
import type { Brain, BrainCategory, BrainNode } from './types';
const host = vi.hoisted(() => ({ state: [] as unknown[], cursor: 0, refs: [] as { current: unknown }[], refCursor: 0, effects: [] as (() => unknown)[] }));
vi.mock('react', async original => ({ ...await original<typeof import('react')>(),
  useState: (value: unknown) => { const i = host.cursor++; if (!(i in host.state)) host.state[i] = value; return [host.state[i], (v: unknown) => { host.state[i] = typeof v === 'function' ? v(host.state[i]) : v; }]; },
  useRef: (value: unknown) => { const i = host.refCursor++; if (!(i in host.refs)) host.refs[i] = { current: value }; return host.refs[i]; },
  useEffect: (effect: () => unknown) => { host.effects.push(effect); },
}));
import BrainView, { CANVAS_BACKGROUND, CATEGORY_STYLE, DRAW_ORDER, EDGE_STYLE, categoryOf, hitNode, nodeStyle, projectNodes } from './BrainView';
import { EXPLAINERS } from './brainExplainers';
const nodes: BrainNode[] = [
  { id: '1', x: -1, y: 1, z: 0, type: 'KCg', group: 'KC', category: 'kc' },
  { id: '2', x: 1, y: -1, z: 1, type: 'MBON01', group: 'MBON', category: 'mbon' },
  { id: '3', x: 0, y: 0, z: -1, type: 'unassigned', group: 'unknown' },
];
const brain: Brain = { dataset: 'Real test graph', nodes, edges: [[0, 1]], edge_metadata: [{ contact_count: 5, modeled_sign: 1, plastic: true }], displayed_neurons: 3, total_neurons: 100, coordinate_note: 'Actual sampled positions' };
function elements(node: ReactNode): ReactElement<Record<string, unknown>>[] {
  if (!node || typeof node !== 'object' || !('type' in node)) return [];
  const e = node as ReactElement<Record<string, unknown>>;
  return [e, ...[e.props.children].flat(Infinity).flatMap(child => elements(child as ReactNode))];
}
function render() { host.cursor = 0; host.refCursor = 0; host.effects = []; return elements(BrainView({ brain, error: '', retry: vi.fn() })); }
function runEffects() { host.effects.forEach(effect => effect()); }
function keydownListener() {
  const call = vi.mocked(window.addEventListener).mock.calls.find(args => args[0] === 'keydown');
  return call![1] as unknown as (event: { key: string }) => void;
}
/** WCAG relative luminance and contrast ratio, so the legibility floor is measured, not asserted by eye. */
function luminance(hex: string) {
  const channel = (part: number) => { const c = part / 255; return c <= .03928 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4; };
  const value = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4].map(i => channel(parseInt(value.slice(i, i + 2), 16)));
  return .2126 * r + .7152 * g + .0722 * b;
}
function contrast(a: string, b: string) {
  const [high, low] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (high + .05) / (low + .05);
}
beforeEach(() => { host.state = []; host.refs = []; vi.stubGlobal('document', { activeElement: { focus: vi.fn() } }); vi.stubGlobal('window', { addEventListener: vi.fn(), removeEventListener: vi.fn() }); });

it('keeps every category legible on the canvas ground with a distinct shape', () => {
  for (const category of Object.keys(CATEGORY_STYLE) as BrainCategory[]) {
    const style = nodeStyle({ ...nodes[0], category });
    expect(style).toBe(CATEGORY_STYLE[category]);
    expect(style.radius).toBeGreaterThan(0);
    // Legibility floor: decorative ink needs 3:1 against its own composited background.
    expect(contrast(style.color, CANVAS_BACKGROUND)).toBeGreaterThanOrEqual(3);
  }
  for (const style of Object.values(EDGE_STYLE)) expect(contrast(style.color, CANVAS_BACKGROUND)).toBeGreaterThanOrEqual(3);
  // The circuit populations are a small minority of the sample, so they must not be drawn smaller.
  for (const category of ['alpn', 'kc', 'mbon'] as const) expect(CATEGORY_STYLE[category].radius).toBeGreaterThan(CATEGORY_STYLE.other.radius);
  expect(CATEGORY_STYLE.kc.color).toBe('#B79CED'); expect(CATEGORY_STYLE.mbon.color).toBe('#E69F00');
  expect(new Set(Object.values(CATEGORY_STYLE).map(style => style.shape)).size).toBe(5);
  expect(categoryOf(nodes[2])).toBe('unknown');
});
it('draws background annotations before the sparse circuit populations, covering every category once', () => {
  expect(DRAW_ORDER.flat().sort()).toEqual(Object.keys(CATEGORY_STYLE).sort());
  expect(DRAW_ORDER[0]).toEqual(['other', 'unknown']);
  expect(DRAW_ORDER[1]).toEqual(['alpn', 'kc', 'mbon']);
});
it('names the KC to MBON layer anatomically and claims no learning anywhere in the copy', () => {
  // Biology may describe learned associations in real flies; the retired workflow may not reappear.
  const retired = /plastic|decoder|replay|recorded spike|\bdesk\b|training|trained\b|learned (gain|weight|parameter|checkpoint)|\bpick\b|win probability|forecast/i;
  expect(EDGE_STYLE.kcmbon.label).toBe('KC→MBON output synapses');
  expect(EDGE_STYLE.kcmbon.label).not.toMatch(retired);
  expect(Object.keys(EXPLAINERS)).not.toContain('replay');
  expect(Object.keys(EXPLAINERS)).not.toContain('firing');
  expect(Object.keys(EXPLAINERS)).not.toContain('sharedGains');
  for (const [key, explainer] of Object.entries(EXPLAINERS)) {
    const text = [explainer.title, explainer.summary, ...explainer.paragraphs].join(' ');
    expect(text, `${key} still describes the retired workflow`).not.toMatch(retired);
    expect(explainer.paragraphs.length).toBeGreaterThan(0);
  }
  // Documented fly biology stays; it is the simulator workflow that was removed.
  expect(EXPLAINERS.mushroomBodies.summary).toMatch(/learned associations/);
  expect(EXPLAINERS.sample.paragraphs.join(' ')).toMatch(/released class annotation is ALPN/);
});
it.each([[0, 800, 600], [50, 800, 600], [-30, 360, 400]])('hit tests the actual projection after rotation/resize %s %s %s', (rotation, width, height) => {
  const points = projectNodes(nodes, rotation, width, height);
  points.forEach((point, index) => expect(hitNode(points, point.x, point.y, () => true)).toBe(index));
  expect(hitNode(points, points[0].x, points[0].y, index => index !== 0)).toBe(-1);
});
it('pins explanations by keyboard-compatible activation, closes with Escape, and never invents activity', () => {
  let tree = render();
  const explain = tree.find(e => e.props['aria-label'] === 'Explain About Kenyon cells')!;
  (explain.props.onClick as () => void)(); tree = render();
  expect(tree.some(e => e.props.role === 'dialog')).toBe(true);
  runEffects();
  keydownListener()({ key: 'Escape' }); tree = render();
  expect(tree.some(e => e.props.role === 'dialog')).toBe(false);
  const selector = tree.find(e => e.props['aria-label'] === 'Inspect displayed neuron')!;
  (selector.props.onChange as (event: unknown) => void)({ target: { value: '0' } }); tree = render();
  expect(tree.some(e => e.type === 'p' && e.props.children === 'Released annotations only. This view records no simulated activity for any neuron.')).toBe(true);
  expect(tree.some(e => e.props['aria-label'] === 'Inspect target 2')).toBe(true);
});
it('layer toggles affect display selection without mutating graph or making predictions', () => {
  const original = JSON.stringify(brain); let tree = render();
  const checkbox = tree.filter(e => e.type === 'input' && e.props.type === 'checkbox')[1];
  (checkbox.props.onChange as (event: unknown) => void)({ target: { checked: false } }); tree = render();
  expect(tree.filter(e => e.type === 'option').some(e => e.props.value === 0)).toBe(false);
  expect(JSON.stringify(brain)).toBe(original);
});

it('returns focus to the original selector after nested node/edge inspection', () => {
  const opener = { focus: vi.fn() }; vi.stubGlobal('document', { activeElement: opener });
  let tree = render();
  (tree.find(e => e.props['aria-label'] === 'Inspect displayed neuron')!.props.onChange as (event: unknown) => void)({ target: { value: '0' } });
  tree = render();
  const internal = { focus: vi.fn() }; vi.stubGlobal('document', { activeElement: internal });
  (tree.find(e => e.type === 'button' && e.props.children === 'Connection details')!.props.onClick as () => void)();
  tree = render();
  (tree.find(e => e.type === 'button' && e.props.children === 'Close inspector (Esc)')!.props.onClick as () => void)();
  expect(opener.focus).toHaveBeenCalledOnce(); expect(internal.focus).not.toHaveBeenCalled();
});
