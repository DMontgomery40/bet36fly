import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import type { ReactElement, ReactNode } from 'react';
import type { Experiment, ExperimentIndex } from './types';
const host = vi.hoisted(() => ({ state: [] as unknown[], cursor: 0, receive: undefined as ((data: unknown) => void) | undefined, fail: undefined as ((error: string) => void) | undefined }));
vi.mock('react', async original => ({ ...await original<typeof import('react')>(),
  useState: (value: unknown) => { const i = host.cursor++; if (!(i in host.state)) host.state[i] = value; return [host.state[i], (v: unknown) => { host.state[i] = v; }]; },
  useEffect: (effect: () => void) => { effect(); },
}));
vi.mock('./data', async original => ({ ...await original<typeof import('./data')>(), pollExperiments: (receive: (data: unknown) => void, fail: (error: string) => void) => { host.receive = receive; host.fail = fail; return () => {}; } }));
import ExperimentRuns, { ExperimentRunsView, filteredComparisons, ProspectivePanel } from './ExperimentRuns';
function elements(node: ReactNode): ReactElement<Record<string, unknown>>[] {
  if (!node || typeof node !== 'object' || !('type' in node)) return [];
  const e = node as ReactElement<Record<string, unknown>>;
  return [e, ...[e.props.children].flat(Infinity).flatMap(child => elements(child as ReactNode))];
}
function render() { host.cursor = 0; const view = ExperimentRuns(); return ExperimentRunsView(view.props); }
const metric = { n: 20, log_loss: .7, brier: .4, accuracy: .6, ece: .03 };
function experiment(status = 'running'): Experiment {
  return { id: 'v2-real', status, created_at: '2026-09-11T00:00:00Z', updated_at: '2026-09-11T01:00:00Z', artifacts: {},
    jobs: [{ id: 'a', variant: 'bio-shared-temporal', seed: 42, status, phase: status === 'running' ? 'full-simulator' : status,
      gain_parameters: 295, decoder_parameters: 2982, active_parameters: 2780,
      ...(status === 'complete' ? { validation_loss: .7, metrics: { validation: { soccer: metric }, historical: { baseball: { ...metric, log_loss: .8 } } } } : {}),
      ...(status === 'failed' ? { error: 'Stored measured failure' } : {}),
    }] };
}
function index(status = 'running'): ExperimentIndex { return { experiments: [experiment(status)], active_v1: { run_id: 'v1' }, prospective: { status: 'awaiting_candidate', sports: {} } }; }
beforeEach(() => { host.state = []; host.cursor = 0; host.receive = undefined; host.fail = undefined; });
afterEach(() => vi.unstubAllGlobals());
it.each(['complete', 'failed', 'cancelled'])('retains selected run across running → %s, and stale fetch errors', status => {
  render(); host.receive!(index());
  let tree = elements(render());
  const button = tree.find(e => e.type === 'button' && e.props['aria-pressed'] === false)!;
  (button.props.onClick as () => void)();
  host.receive!(index(status)); host.fail!('network unavailable');
  tree = elements(render());
  const detail = tree.find(e => typeof e.type === 'function' && 'job' in e.props)!;
  expect((detail.props.job as { status: string }).status).toBe(status);
  expect(tree.some(e => e.props.role === 'alert')).toBe(true);
  expect(tree.some(e => e.type === 'button' && e.props['aria-pressed'] === true)).toBe(true);
  if (status === 'failed') expect((detail.props.job as { error: string }).error).toBe('Stored measured failure');
});
it('filters real metrics and leaves missing or queued metrics absent', () => {
  expect(filteredComparisons(experiment(), 'soccer', 'validation')[0].mean).toBeUndefined();
  const done = experiment('complete');
  expect(filteredComparisons(done, 'soccer', 'validation')[0].mean?.log_loss).toBe(.7);
  expect(filteredComparisons(done, 'baseball', 'historical')[0].mean?.log_loss).toBe(.8);
  expect(filteredComparisons(done, 'soccer', 'historical')[0].mean).toBeUndefined();
});
it('labels the historical development benchmark and prospective cohorts honestly', () => {
  render(); host.receive!(index()); const tree = elements(render());
  expect(tree.find(e => e.type === 'option' && e.props.value === 'historical')?.props.children).toBe('Historical development benchmark · January–August 2026');
  const panel = elements(ProspectivePanel({ data: index().prospective }));
  expect(panel.filter(e => e.type === 'p' && e.props.children === 'First cohort pending')).toHaveLength(2);
});

it('shows explicit curtailed scope and excludes cancelled metrics from comparisons', () => {
  render(); const data = index('cancelled');
  data.experiments[0].completion_scope = 'user-curtailed';
  data.experiments[0].execution_amendments = [{ recorded_at: '2026-09-11', reason: 'User stopped remaining temporal runs.', job_ids: ['a'] }];
  host.receive!(data); const tree = elements(render());
  expect(tree.find(e => e.props['aria-label'] === 'Execution amendments')).toBeDefined();
  expect(filteredComparisons(data.experiments[0], 'soccer', 'validation')[0].seeds).toHaveLength(0);
});

it('keeps dopamine-association experiments out of the original v2 matrix and its empty state', () => {
  const reward = {
    ...experiment('complete'), id: 'reward-v3-real', kind: 'dopamine-association',
    jobs: [{ ...experiment('complete').jobs[0], id: 'paired', variant: 'paired' }],
  } as Experiment;
  const mixed = index('complete');
  mixed.experiments = [reward, experiment('complete')];
  render(); host.receive!(mixed); let tree = elements(render());
  expect(tree.some(e => e.type === 'button' && String(e.props.children).includes('paired'))).toBe(false);
  expect(tree.some(e => e.type === 'button' && String(e.props.children).includes('bio-shared-temporal'))).toBe(true);

  host.receive!({ ...mixed, experiments: [reward] }); tree = elements(render());
  expect(tree.some(e => e.type === 'p' && e.props.children === 'No v2 experiment has started.')).toBe(true);
  expect(tree.some(e => e.props.className === 'experiment-table')).toBe(false);
});
