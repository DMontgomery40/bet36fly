import { beforeEach, expect, it, vi } from 'vitest';
import type { ReactElement, ReactNode } from 'react';
import type { Brain, BrainNode } from './types';
const host = vi.hoisted(() => ({ state: [] as unknown[], cursor: 0, refs: [] as { current: unknown }[], refCursor: 0, effects: [] as (() => unknown)[] }));
vi.mock('react', async original => ({ ...await original<typeof import('react')>(),
  useState: (value: unknown) => { const i = host.cursor++; if (!(i in host.state)) host.state[i] = value; return [host.state[i], (v: unknown) => { host.state[i] = typeof v === 'function' ? v(host.state[i]) : v; }]; },
  useRef: (value: unknown) => { const i = host.refCursor++; if (!(i in host.refs)) host.refs[i] = { current: value }; return host.refs[i]; },
  useEffect: (effect: () => unknown) => { host.effects.push(effect); },
}));
import BrainView, { CATEGORY_STYLE, categoryOf, hitNode, nodeStyle, projectNodes } from './BrainView';
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
function render() { host.cursor = 0; host.refCursor = 0; host.effects = []; return elements(BrainView({ brain, error: '', inference: null, busy: false, retry: vi.fn() })); }
beforeEach(() => { host.state = []; host.refs = []; vi.stubGlobal('document', { activeElement: { focus: vi.fn() } }); vi.stubGlobal('window', { addEventListener: vi.fn(), removeEventListener: vi.fn() }); });
it('keeps anatomy colors during spikes and provides distinct shapes and unknown fallback', () => {
  for (const category of Object.keys(CATEGORY_STYLE) as (keyof typeof CATEGORY_STYLE)[]) {
    const node = { ...nodes[0], category };
    expect(nodeStyle(node, 4).color).toBe(nodeStyle(node, 0).color);
    expect(nodeStyle(node, 4).halo).toBe(true); expect(nodeStyle(node, 0).halo).toBe(false);
  }
  expect(CATEGORY_STYLE.kc.color).toBe('#B79CED'); expect(CATEGORY_STYLE.mbon.color).toBe('#E69F00');
  expect(new Set(Object.values(CATEGORY_STYLE).map(style => style.shape)).size).toBe(5);
  expect(categoryOf(nodes[2])).toBe('unknown');
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
  host.effects[1]();
  const listener = vi.mocked(window.addEventListener).mock.calls.find(args => args[0] === 'keydown')![1] as unknown as (event: { key: string }) => void;
  listener({ key: 'Escape' }); tree = render();
  expect(tree.some(e => e.props.role === 'dialog')).toBe(false);
  const selector = tree.find(e => e.props['aria-label'] === 'Inspect displayed neuron')!;
  (selector.props.onChange as (event: unknown) => void)({ target: { value: '0' } }); tree = render();
  expect(tree.some(e => e.type === 'p' && e.props.children === 'No recorded activity time selected.')).toBe(true);
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
