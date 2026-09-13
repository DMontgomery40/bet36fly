import { renderToStaticMarkup } from 'react-dom/server';
import { expect, it, vi } from 'vitest';
import { RewardEvidenceView } from './RewardEvidence';
import type { Experiment, ExperimentIndex, RewardDiagnosticIndex } from './types';

const experiments: ExperimentIndex = {
  experiments: [], active_v1: { run_id: 'v1-active' },
  prospective: { status: 'awaiting_candidate', sports: {} },
};

const diagnostics: RewardDiagnosticIndex = {
  evidence_note: 'docs/evidence/reward-mechanism-repair-2026-09-12/index.md',
  diagnostics: [
    {
      run_id: 'diag-candidate-maskgamma-e3d8898dc68a', rule: 'candidate', learning_rule: 'event',
      learning_rule_source: 'historical-rule-mapping', created_at: '2026-09-12T05:29:48Z',
      dan_reference: 'none', away_plasticity_mask: 'gamma', panel_role: 'held-out',
      selection_status: 'previously-frozen', panel_complete: true, stored_verdict: 'failed',
      validation_status: 'stored-only', evidence_status: 'unverified', failed_criteria: ['untaught_guard'],
      missing_validation: ['bit_identical_repeat', 'sensory_noise_invariance'],
      criteria: { teaching_specific: true, untaught_guard: false, cross_compartment: true,
        no_bound_hits: true, cumulative: true, bit_identical_repeat: null, sensory_noise_invariance: null },
      untaught_guard: { 'home/base': { mean: -.5156228840351105, sd: .9795557677547752, limit: .4897778838773876, passed: false } },
      teaching_specific: {}, detail_url: '/api/reward-diagnostics/diag-candidate-maskgamma-e3d8898dc68a',
      tau_ms: 500, learning_rate: .0005, rate_tau_ms: null, bridge_normalization: null,
      bridge_tail: null, bridge_layout: null, bridge_contract: null, tail_evidence: null,
      source_unchanged_during_run: true, native_binary_sha256: 'a'.repeat(64),
    },
    {
      run_id: 'diag-rate-bridge-v1-maskgamma-de050d773763', rule: 'rate-bridge-v1', learning_rule: 'rate-bridge-v1',
      learning_rule_source: 'recorded', created_at: '2026-09-12T06:00:00Z', dan_reference: 'none',
      away_plasticity_mask: 'gamma', panel_role: 'original', selection_status: null, panel_complete: true,
      stored_verdict: 'passed', validation_status: 'validated', evidence_status: 'passed', failed_criteria: [], missing_validation: [],
      criteria: { teaching_specific: true, untaught_guard: true, cross_compartment: true, no_bound_hits: true,
        cumulative: true, bit_identical_repeat: true, sensory_noise_invariance: true }, untaught_guard: {}, teaching_specific: {},
      detail_url: '/api/reward-diagnostics/diag-rate-bridge-v1-maskgamma-de050d773763', tau_ms: 500, learning_rate: .0005,
      rate_tau_ms: 100, bridge_normalization: .96, bridge_tail: 'analytic_no_new_event_tail', bridge_layout: 'rate-bridge-v1/1',
      bridge_contract: { documents: {}, layout: 'rate-bridge-v1/1', config: { h_ms: .2, tau_ms: 500, rate_tau_ms: 100, eta: .0005, normalization: .96 }, tail: 'analytic_no_new_event_tail', state: 'zero onset states' },
      tail_evidence: { equation: 'eta * n * Q_end / (1/tau_r + 1/tau_e)', extends_neural_time: false,
        electrical_bound_observations: 0, tail_bound_observations: 0, max_publication_reconciliation_error: 0 },
      source_unchanged_during_run: true, native_binary_sha256: 'b'.repeat(64),
    },
    {
      run_id: 'diag-rate-bridge-v1-maskgamma-dea14759e9ca', rule: 'rate-bridge-v1', learning_rule: 'rate-bridge-v1',
      learning_rule_source: 'recorded', created_at: '2026-09-12T06:01:59Z', dan_reference: 'none',
      away_plasticity_mask: 'gamma', panel_role: 'held-out', selection_status: 'previously-frozen', panel_complete: true,
      stored_verdict: 'failed', validation_status: 'validated', evidence_status: 'failed', failed_criteria: ['untaught_guard'], missing_validation: [],
      criteria: { teaching_specific: true, untaught_guard: false, cross_compartment: true, no_bound_hits: true,
        cumulative: true, bit_identical_repeat: true, sensory_noise_invariance: true },
      untaught_guard: { 'home/base': { mean: -.27264003455638885, sd: .48169047084658934, limit: .24084523542329467, passed: false } },
      teaching_specific: {}, detail_url: '/api/reward-diagnostics/diag-rate-bridge-v1-maskgamma-dea14759e9ca',
      tau_ms: 500, learning_rate: .0005, rate_tau_ms: 100, bridge_normalization: .96,
      bridge_tail: 'analytic_no_new_event_tail', bridge_layout: 'rate-bridge-v1/1', bridge_contract: null,
      tail_evidence: { equation: 'eta * n * Q_end / (1/tau_r + 1/tau_e)', extends_neural_time: false,
        electrical_bound_observations: 0, tail_bound_observations: 0, max_publication_reconciliation_error: 0 },
      source_unchanged_during_run: true, native_binary_sha256: 'b'.repeat(64),
    },
  ],
  qualification_pairs: [
    { pair_id: 'bridge-pair', learning_rule: 'rate-bridge-v1', original_run_id: 'diag-rate-bridge-v1-maskgamma-de050d773763',
      heldout_run_id: 'diag-rate-bridge-v1-maskgamma-dea14759e9ca', validation_status: 'validated', evidence_status: 'failed', failed_criteria: ['untaught_guard'] },
  ],
  conditioning: { status: 'not_run_gate_failed', message: 'Conditioning not run: mechanism qualification is blocked.', failed_diagnostic_ids: ['diag-rate-bridge-v1-maskgamma-dea14759e9ca'] },
};

function view(overrides: Partial<Parameters<typeof RewardEvidenceView>[0]> = {}) {
  return renderToStaticMarkup(<RewardEvidenceView diagnostics={diagnostics} diagnosticsLoading={false} diagnosticsError=""
    experiments={experiments} experimentsError="" selectedExperimentId="" selectedJobId=""
    onSelectExperiment={vi.fn()} onSelectJob={vi.fn()} {...overrides}/>);
}

it('shows stored and independently validated verdicts without promoting the raw stored result', () => {
  const html = view();
  expect(html).toContain('Mechanism qualification');
  expect(html).toContain('diag-candidate-maskgamma-e3d8898dc68a');
  expect(html).toContain('stored failed');
  expect(html).toContain('stored only');
  expect(html).toContain('unverified');
  expect(html).toContain('-0.515623');
  expect(html).toContain('0.489778');
  expect(html).toContain('diag-rate-bridge-v1-maskgamma-dea14759e9ca');
  expect(html).toContain('validated failed');
  expect(html).toContain('-0.272640');
  expect(html).toContain('0.240845');
  expect(html).toContain('Previously frozen held-out');
});

it('shows the bridge contract and explains the analytic tail without calling it simulated activity', () => {
  const html = view();
  expect(html).toContain('τr 100 ms');
  expect(html).toContain('τe 500 ms');
  expect(html).toContain('normalization 0.960');
  expect(html).toContain('eta * n * Q_end / (1/tau_r + 1/tau_e)');
  expect(html).toContain('changes the bounded gain accumulator and published float32 gain');
  expect(html).toContain('does not extend neural time, spikes, voltages, membrane state, or count bins');
  expect(html).toContain('0 electrical / 0 tail bound observations');
});

it('shows the blocked pair, conditioning not run, and historical sports as separate evidence', () => {
  const html = view();
  expect(html).toContain('Pair qualification · failed');
  expect(html).toContain('Conditioning and reversal');
  expect(html).toContain('Conditioning not run: mechanism qualification is blocked.');
  expect(html).toContain('Historical sports association pilots');
  expect(html).toContain('do not establish mechanism qualification or conditioning');
});

it('renders loading, empty, hard error, and stale retained evidence without a pass', () => {
  expect(view({ diagnostics: null, diagnosticsLoading: true })).toContain('Loading mechanism evidence');
  const empty = { ...diagnostics, diagnostics: [], qualification_pairs: [], conditioning: { status: 'not_run' as const, message: 'No conditioning manifest registered.', failed_diagnostic_ids: [] } };
  expect(view({ diagnostics: empty })).toContain('No stored mechanism panels');
  expect(view({ diagnostics: null, diagnosticsError: 'Evidence unavailable.' })).toContain('Evidence unavailable.');
  const stale = view({ diagnosticsError: 'Refresh failed.' });
  expect(stale).toContain('Showing last loaded mechanism evidence');
  expect(stale).toContain('Refresh failed.');
  expect(stale).not.toContain('Pair qualification · passed');
});

it.each(['running', 'incomplete', 'failed', 'budget_stopped', 'cancelled', 'mystery'])('renders conditioning status %s fail closed', status => {
  const conditioning: Experiment = {
    id: 'conditioning-test', kind: 'dopamine-conditioning', status,
    created_at: '2026-09-12T00:00:00Z', updated_at: '2026-09-12T00:01:00Z', artifacts: {},
    jobs: [{ id: 'acquisition_ab', variant: 'acquisition_ab', seed: 1, status, phase: status,
      gain_parameters: 0, decoder_parameters: 0, active_parameters: 0, completed: 12, total: 100 }],
  };
  const html = view({ experiments: { ...experiments, experiments: [conditioning] } });
  expect(html).toContain(status === 'mystery' ? 'unavailable' : status.replaceAll('_', ' '));
  expect(html).toContain('12 / 100');
  expect(html).not.toContain('Conditioning passed');
});


it('does not turn complete conditioning jobs or stored all-true criteria into a scientific pass', () => {
  const run: Experiment = { id: 'complete-execution', kind: 'dopamine-conditioning', status: 'complete',
    created_at: '', updated_at: '', jobs: [], artifacts: {}, conditioning: {
      stages: ['acquisition_ab', 'acquisition_cd', 'reversal_ab'].map(id => ({ id, status: 'complete', criteria: { generic: { passed: true, value: 1, limit: 0 } } })),
    } };
  const html = view({ experiments: { ...experiments, experiments: [run] } });
  expect(html).toContain('Conditioning scientific verdict: unverified');
  expect(html).toContain('Criteria coverage has not been validated.');
  expect(html).not.toContain('Conditioning passed');
});

it('keeps malformed links inert and does not fabricate missing measurements as zero', () => {
  const data = structuredClone(diagnostics);
  data.diagnostics = [{ ...data.diagnostics[0], detail_url: 'javascript:alert(1)', untaught_guard: { 'home/base': { mean: null, sd: null, limit: null, passed: null } } }];
  const html = view({ diagnostics: data });
  expect(html).not.toContain('javascript:');
  expect(html).not.toContain('-0.515623');
  expect(html).toContain('unavailable');
});

it('tolerates incomplete recorded bridge metadata and labels retained conditioning as stale', () => {
  const data = structuredClone(diagnostics);
  data.diagnostics[1].bridge_contract = {} as NonNullable<typeof data.diagnostics[1]['bridge_contract']>;
  const html = view({ diagnostics: data, experimentsError: 'Registry refresh failed.' });
  expect(html).toContain('Showing last loaded conditioning registry.');
  expect(html).toContain('Registry refresh failed.');
  expect(html).toContain('h — ms');
});
