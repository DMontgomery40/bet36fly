import type { Method } from './sensoryTypes';
export type Page = 'overview' | 'backtest' | 'methods' | 'learning' | 'circuit';
export const methodNames: Record<Method, string> = { neural: 'Complete sensory pipeline', encoder_only: 'Encoder only', same_information: 'Same-information baseline', prior: 'Training-frequency prior', uniform: 'Uniform probability', circuit_silenced: 'Silenced circuit' };
export const methods: Method[] = ['neural', 'encoder_only', 'same_information', 'prior', 'uniform', 'circuit_silenced'];
export function route(hash: string): Page { return hash === '#backtest' || hash.startsWith('#backtest/') ? 'backtest' : hash === '#methods' ? 'methods' : hash === '#learning' ? 'learning' : hash === '#circuit' ? 'circuit' : 'overview'; }
export function selectedGame(hash: string) { try { return hash.startsWith('#backtest/') ? decodeURIComponent(hash.slice(10)) : ''; } catch { return ''; } }
export function pct(n: number | null | undefined, places = 2) { return n == null || !Number.isFinite(n) ? 'Unavailable' : `${(n * 100).toFixed(places)}%`; }
export function fixed(n: number | null | undefined, places = 6) { return n == null || !Number.isFinite(n) ? 'Unavailable' : n.toFixed(places); }
export function count(n: number) { return n.toLocaleString('en-US'); }
export function day(iso: string) { return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }); }
export function gamesUrl(team: string, start: string, end: string, offset: number) { return '/api/sensory/games?' + new URLSearchParams({ team, start, end, offset: String(offset), limit: '50' }).toString().replace(/(?:start|end)=&/g, ''); }
