import type { DeskRow, Sport } from './types';

export type DeskFilter = 'upcoming' | 'results' | 'all';
export function deskRows(rows: DeskRow[], sport: Sport, filter: DeskFilter): DeskRow[] {
  return rows.filter(row => (sport === 'all' || row.prediction.sport === sport)
    && (filter === 'all' || (filter === 'upcoming' ? ['upcoming', 'pending'].includes(row.state) : ['won', 'lost'].includes(row.state))))
    .sort((a, b) => (filter === 'results' ? -1 : 1) * (Date.parse(a.prediction.start_time) - Date.parse(b.prediction.start_time)) || a.game_id.localeCompare(b.game_id));
}
export function stateLabel(row: DeskRow): string {
  return ({ upcoming: 'Upcoming', pending: 'Awaiting final', won: 'Correct', lost: 'Missed', held: 'On hold', void: 'Cancelled' })[row.state];
}
export function deskQuip(busy: boolean, row: DeskRow | null, hasRecording: boolean): string {
  if (busy) return 'Please hold. All six legs are busy.';
  if (row?.state === 'lost') return 'I would like to blame the lighting.';
  if (row?.state === 'won') return 'One small step for flykind.';
  if (hasRecording && row?.prediction.pick === 'draw') return 'A draw is also a result. Apparently.';
  if (hasRecording) return 'The neurons have filed their report.';
  return 'No thumbs. Several opinions.';
}
