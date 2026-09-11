import { describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import DeskView from './DeskView';
import { deskQuip, deskRows, stateLabel } from './deskData';
import type { Desk, DeskRow, DeskState } from './types';

function row(id: string, state: DeskState = 'upcoming', sport = 'soccer'): DeskRow {
  return { game_id: id, league: sport === 'soccer' ? 'EPL' : 'MLB', state, reason: 'Test record', revision_count: 1, can_run: state === 'upcoming', result: null,
    prediction: { id: `pick-${id}`, game_id: id, sport, home: `Home ${id}`, away: `Away ${id}`, start_time: `2026-09-${id}T18:00:00Z`, created_at: '2026-09-01T12:00:00Z', mode: 'paper', status: 'proposed', run_id: 'real-run', model_hash: 'hash', feature_hash: 'features', pick: 'home', pick_label: `Home ${id}`, confidence: .6, fair_odds: 1 / .6, probabilities: { home: .6, draw: sport === 'soccer' ? .1 : 0, away: sport === 'soccer' ? .3 : .4 } } };
}
function data(rows: DeskRow[]): Desk {
  const summary = { total: rows.length, upcoming: rows.length, pending: 0, wins: 0, losses: 0, held: 0, void: 0, completed: 0, hit_rate: null, mean_pick_probability: null, log_loss: null };
  return { mode: 'forward_paper', as_of: '2026-09-01T12:00:00Z', selection_rule: 'First pregame pick', first_recorded_at: rows.length ? rows[0].prediction.created_at : null, sources_updated_at: null, sources: [], refresh_interval_seconds: 900, summary, by_sport: { soccer: summary, baseball: summary }, rows, curve: [], excluded: {} };
}

describe('Forward record selection', () => {
  const rows = [row('12', 'upcoming'), row('11', 'pending', 'baseball'), row('10', 'won'), row('09', 'lost'), row('08', 'held'), row('07', 'void')];
  it('shows future and pending games without treating them as results', () => {
    expect(deskRows(rows, 'all', 'upcoming').map(r => r.game_id)).toEqual(['11', '12']);
    expect(deskRows(rows, 'all', 'results').map(r => r.game_id)).toEqual(['10', '09']);
    expect(deskRows(rows, 'soccer', 'all')).toHaveLength(5);
    expect(deskRows(rows, 'baseball', 'upcoming')).toHaveLength(1);
    expect(rows[0].game_id).toBe('12');
  });
  it('labels held and cancelled games honestly', () => {
    expect(stateLabel(row('12', 'held'))).toBe('On hold');
    expect(stateLabel(row('12', 'void'))).toBe('Cancelled');
  });
  it('uses banter keyed to actual state, not fabricated wins', () => {
    expect(deskQuip(false, row('12', 'lost'), false)).toContain('lighting');
    expect(deskQuip(true, row('12', 'won'), false)).toContain('six legs');
    expect(deskQuip(false, null, false)).toBe('No thumbs. Several opinions.');
  });
});

function render(record: Desk | null, error = '') {
  return renderToStaticMarkup(<DeskView data={record} error={error} loading={false} games={[]} inference={null} busyId={null} modelReady={true} onPredict={vi.fn()}/>);
}
it('empty and failed data do not invent a curve, pick, or win rate', () => {
  const empty = render(data([]));
  expect(empty).toContain('The first result gets the first dot.');
  expect(empty).toContain('No completed results yet.');
  expect(empty).not.toContain('60.0%');
  const failed = render(null, 'Cannot connect');
  expect(failed).toContain('role="alert"');
  expect(failed).toContain('Cannot connect');
  expect(failed).not.toContain('0 W / 0 L');
});
it('renders saved picks with explicit uncalibrated probabilities and trace provenance', () => {
  const markup = render(data([row('12')]));
  expect(markup).toContain('Home 12');
  expect(markup).toContain('60.0%');
  expect(markup).toContain('real-run');
  expect(markup).toContain('uncalibrated model estimates');
  expect(markup).toContain('Recorded spikes appear after a run.');
  expect(markup).toContain('Illustrated fly, scripted banter.');
  expect(markup).toContain('disabled=""');
});
