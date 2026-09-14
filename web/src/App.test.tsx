import { describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { gamesUrl, pct, route, selectedGame } from './sensoryData';
import type { SummaryState } from './sensoryTypes';
const host = vi.hoisted(() => ({ data: null as SummaryState | null, loading: true, error: '' }));
vi.mock('./data', () => ({ useResource: () => ({ ...host, reload: vi.fn() }) }));
import App from './App';
vi.stubGlobal('window', { location: { hash: '#overview' } });
describe('sensory application navigation', () => {
  it.each(['#training', '#ledger', '#desk', '#observatory', '#v1', '#v2', '#bogus', ''])('retires old bookmark %s', hash => expect(route(hash)).toBe('overview'));
  it('routes encoded MLB details without losing fixture identity', () => {
    const hash = '#backtest/' + encodeURIComponent('baseball:mlb:718780');
    expect(route(hash)).toBe('backtest'); expect(selectedGame(hash)).toBe('baseball:mlb:718780');
    expect(selectedGame('#backtest/%zz')).toBe('');
  });
  it('builds escaped filters and omits missing dates', () => {
    const url = new URL(gamesUrl('A & B', '', '2023-05-01', 50), 'http://localhost');
    expect(url.searchParams.get('team')).toBe('A & B');
    expect(url.searchParams.has('start')).toBe(false);
    expect(url.searchParams.get('end')).toBe('2023-05-01');
    expect(url.searchParams.get('offset')).toBe('50');
  });
  it('never substitutes zero for unavailable measurements', () => { expect(pct(null)).toBe('Unavailable'); expect(pct(0)).toBe('0.00%'); });
  it('renders a meaningful loading state', () => {
    host.data = null; host.loading = true;
    expect(renderToStaticMarkup(<App/>)).toContain('Loading frozen confirmation');
  });
  it.each(['unavailable', 'invalid'] as const)('renders %s without old model fallback', status => {
    host.loading = false; host.data = { status, identity: 'test', message: 'Evidence failed validation.' };
    const html = renderToStaticMarkup(<App/>);
    expect(html).toContain('Confirmation unavailable'); expect(html).toContain('Evidence failed validation.');
    expect(html).not.toContain('56.21%'); expect(html).toContain('Try again');
  });
});
