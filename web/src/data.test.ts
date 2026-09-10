import { describe, expect, it, vi, afterEach } from 'vitest';
import { controlRows } from './controls';
import { activityAt, date, decimal, number, percent, request, safeUrl } from './data';
afterEach(() => vi.unstubAllGlobals());
describe('Recorded neural trace boundaries', () => {
  it('uses recorded bin and node values without fabrication', () => { const trace = [[0, 3, 1], [2, 0, 7]]; expect(activityAt(trace, 0, 1)).toBe(3); expect(activityAt(trace, 1, 2)).toBe(7); expect(activityAt(trace, 1, 0)).toBe(2); });
  it.each([[-1, 0], [2, 0], [0, 4], [0, -1]])('has no spiking data outside the recording (%s, %s)', (frame, node) => { expect(activityAt([[1, 2]], frame, node)).toBe(0); });
  it.each([NaN, Infinity, -1])('rejects invalid spike counts (%s)', value => expect(activityAt([[value]], 0, 0)).toBe(0));
});
describe('Scientific value formatting', () => {
  it('distinguishes measured zero from missing results', () => { expect(percent(0)).toBe('0.0%'); expect(decimal(0)).toBe('0.000'); expect(number(0)).toBe('0'); expect(percent(undefined)).toBe('—'); expect(decimal(NaN)).toBe('—'); expect(number(Infinity)).toBe('—'); });
  it('labels source time in UTC and rejects invalid dates', () => { expect(date('2026-09-10T21:30:00Z')).toContain('09:30 PM UTC'); expect(date('invalid')).toBe('Time unavailable'); });
});
describe('Remote source and API contracts', () => {
  it.each(['javascript:alert(1)', 'data:text/html,hi', '/relative', 'not a url'])('does not link unsafe source URLs (%s)', url => expect(safeUrl(url)).toBeUndefined());
  it('preserves public HTTP source links', () => { expect(safeUrl('https://example.org/game?id=5')).toBe('https://example.org/game?id=5'); });
  it.each([404, 409, 503])('surfaces backend detail at status %s', async status => { vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status, json: async () => ({ detail: 'Model checkpoint is not ready' }) })); await expect(request('/api/predict/game')).rejects.toThrow('Model checkpoint is not ready'); });
  it('provides a readable error for a non-JSON response', async () => { vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 502, json: async () => { throw new Error('HTML'); } })); await expect(request('/api/status')).rejects.toThrow('Request failed (502). Please retry.'); });
});


describe('Control report compatibility and scientific meaning', () => {
  const metrics = { soccer: { n: 80, accuracy: .4, log_loss: 1.2, brier: .7, ece: .1 } };
  it.each(['shuffled_training_labels', 'shuffled_readout_labels_on_trained_wiring'])('preserves scores and precise scope from %s', key => {
    const rows = controlRows({ [key]: metrics });
    expect(rows).toHaveLength(1);
    expect(rows[0].key).toBe('shuffled_readout_labels_on_trained_wiring');
    expect(rows[0].label).toBe('Shuffled readout labels');
    expect(rows[0].description).toContain('wiring trained on true labels stays fixed');
    expect(rows[0].metrics).toBe(metrics);
  });
  it('uses the canonical control once when both old and new keys are present', () => {
    const canonical = { soccer: { ...metrics.soccer, n: 90 } };
    const rows = controlRows({ shuffled_training_labels: metrics, shuffled_readout_labels_on_trained_wiring: canonical });
    expect(rows).toHaveLength(1);
    expect(rows[0].metrics).toBe(canonical);
  });
  it('retains unrelated controls without implying label shuffling', () => {
    const rows = controlRows({ pregame_feature_logistic: metrics, future_control: metrics });
    expect(rows.map(row => row.key)).toEqual(['pregame_feature_logistic', 'future_control']);
    expect(rows.every(row => row.description === undefined)).toBe(true);
    expect(controlRows({})).toEqual([]);
  });
});
