import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ReactElement, ReactNode } from 'react';
import type { Game, Inference, Prediction } from './types';

// Shallow controller test: keep App's state transitions and callbacks, replace only
// the hook host/API resources. DOM, canvas, and browser behavior are out of scope.
const host = vi.hoisted(() => ({
  state: [] as unknown[], cursor: 0,
  resources: {} as Record<string, { data: unknown; error: string; loading: boolean; reload: ReturnType<typeof vi.fn> }>,
  request: vi.fn(),
}));
vi.mock('react', async importOriginal => ({
  ...await importOriginal<typeof import('react')>(),
  useEffect: () => {},
  useState: (initial: unknown) => {
    const index = host.cursor++;
    if (!(index in host.state)) host.state[index] = typeof initial === 'function' ? initial() : initial;
    return [host.state[index], (value: unknown) => { host.state[index] = typeof value === 'function' ? value(host.state[index]) : value; }];
  },
}));
vi.mock('./data', async importOriginal => ({
  ...await importOriginal<typeof import('./data')>(),
  useResource: (url: string) => host.resources[url],
  request: host.request,
}));
import App from './App';
import GamesView from './GamesView';
import DeskView from './DeskView';

const prediction: Prediction = { pick: 'home', pick_label: 'Home team', probabilities: { home: .6, draw: .1, away: .3 }, confidence: .6, fair_odds: 1 / .6, run_id: 'run-original', created_at: '2026-09-10T20:00:00Z' };
const game: Game = { id: 'game', sport: 'soccer', league: 'Test league', home: 'Home team', away: 'Away team', start_time: '2026-09-12T20:00:00Z', status: 'scheduled', source: 'test source' };
const recording: Inference = { game, prediction, activity: { rates: [], trace: [], population: [], bin_ms: 4, duration_ms: 80, active_neurons: 0, total_spikes: 0, wall_seconds: .2, seed: 42 } };
function findGames(node: ReactNode): ReactElement<Parameters<typeof GamesView>[0]> | undefined {
  if (!node || typeof node !== 'object' || !('type' in node)) return;
  const element = node as ReactElement<{ children?: ReactNode }>;
  if (element.type === GamesView) return element as ReactElement<Parameters<typeof GamesView>[0]>;
  for (const child of [element.props.children].flat(Infinity) as ReactNode[]) { const match = findGames(child); if (match) return match; }
}
function elements(node: ReactNode): ReactElement<{ children?: ReactNode; [key: string]: unknown }>[] {
  if (!node || typeof node !== 'object' || !('type' in node)) return [];
  const element = node as ReactElement<{ children?: ReactNode; [key: string]: unknown }>;
  return [element, ...([element.props.children].flat(Infinity) as ReactNode[]).flatMap(elements)];
}
function renderGames() { host.cursor = 0; return findGames(App())!.props; }
beforeEach(() => {
  host.state = []; host.cursor = 0; host.request.mockReset();
  vi.stubGlobal('window', { location: { hash: '#observatory' }, innerWidth: 1200 });
  const snapshots: Record<string, unknown> = {
    '/api/status': { model_ready: true, refresh: { status: 'idle' } },
    '/api/games?sport=all': { games: [game] },
    '/api/brain': null, '/api/training': null, '/api/ledger': { picks: [], count: 0 }, '/api/desk': null,
  };
  host.resources = Object.fromEntries(Object.entries(snapshots).map(([url, data]) => [url, { data, error: '', loading: false, reload: vi.fn().mockResolvedValue(undefined) }]));
  host.request.mockResolvedValue(recording);
});

async function runInference() {
  renderGames().onPredict(game);
  await vi.waitFor(() => expect(host.resources['/api/ledger'].reload).toHaveBeenCalled());
}
describe('Authoritative upcoming predictions after inference', () => {
  it('reloads games and ledger after a successful inference', async () => {
    await runInference();
    expect(host.resources['/api/games?sport=all'].reload).toHaveBeenCalledOnce();
    expect(host.resources['/api/ledger'].reload).toHaveBeenCalledOnce();
    expect(host.resources['/api/desk'].reload).toHaveBeenCalledOnce();
  });
  it.each(['rescheduled game', 'refreshed features', 'changed model'])('never restores a removed server pick after %s', async reason => {
    await runInference();
    host.resources['/api/games?sport=all'].data = { games: [{ ...game, start_time: reason === 'rescheduled game' ? '2026-09-13T20:00:00Z' : game.start_time }] };
    expect(renderGames().data?.games[0].prediction).toBeUndefined();
  });
  it('uses the authoritative replacement even when its timestamp is older than the recording', async () => {
    await runInference();
    const replacement = { ...prediction, run_id: 'different-run', confidence: .4, created_at: '2026-09-09T20:00:00Z' };
    host.resources['/api/games?sport=all'].data = { games: [{ ...game, prediction: replacement }] };
    expect(renderGames().data?.games[0].prediction).toBe(replacement);
  });
});

it('the fourth tab renders the real forward record and preserves the existing routes', () => {
  vi.stubGlobal('window', { location: { hash: '#desk' }, innerWidth: 1200 });
  const components: unknown[] = [];
  function visit(node: ReactNode) {
    if (!node || typeof node !== 'object' || !('type' in node)) return;
    const element = node as ReactElement<{ children?: ReactNode }>;
    components.push(element.type);
    for (const child of [element.props.children].flat(Infinity) as ReactNode[]) visit(child);
  }
  host.cursor = 0; visit(App());
  expect(components).toContain(DeskView);
  expect(components).not.toContain(GamesView);
});

it('shows verification mode and disables every neural or refresh mutation', async () => {
  host.resources['/api/status'].data = {
    model_ready: false,
    verification_mode: true,
    refresh: { status: 'disabled', message: 'Read-only verification; source refresh is disabled.' },
  };
  host.cursor = 0;
  const tree = App();
  const all = elements(tree);
  const notice = all.find(element => element.props.className === 'notice verification-notice');
  expect(notice).toBeDefined();
  expect(JSON.stringify(notice?.props.children)).toContain('Read-only verification');
  const refresh = all.find(element => element.type === 'button' && element.props.className === 'refresh');
  expect(refresh?.props.disabled).toBe(true);
  (refresh?.props.onClick as () => void)();
  const games = findGames(tree)!;
  expect(games.props.modelReady).toBe(false);
  games.props.onPredict(game);
  await Promise.resolve();
  expect(host.request).not.toHaveBeenCalled();
});

it('keeps refresh disabled until server mode is known', async () => {
  host.resources['/api/status'].data = null;
  host.cursor = 0;
  const all = elements(App());
  const refresh = all.find(element => element.type === 'button' && element.props.className === 'refresh');
  expect(refresh?.props.disabled).toBe(true);
  (refresh?.props.onClick as () => void)();
  await Promise.resolve();
  expect(host.request).not.toHaveBeenCalled();
});
