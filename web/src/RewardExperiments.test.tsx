import { renderToStaticMarkup } from 'react-dom/server';
import { expect, it, vi } from 'vitest';
import ExperimentRuns from './ExperimentRuns';
import RewardExperiments, { RewardExperimentsView, rewardExperiments } from './RewardExperiments';
import TrainingView from './TrainingView';
import type { Experiment, ExperimentIndex, ExperimentJob } from './types';

const metric = { n: 12, log_loss: .6123, brier: .3712, accuracy: .6667, ece: .08 };
function job(id: string, status: string, extra: Partial<ExperimentJob> = {}): ExperimentJob {
  return {
    id, variant: id, seed: 42, status, phase: status === 'running' ? 'teaching' : status,
    gain_parameters: 91, decoder_parameters: 0, active_parameters: 91,
    completed: status === 'running' ? 8 : 16, total: 16,
    metrics: status === 'complete' ? { validation: { baseball: metric } } : undefined,
    ...extra,
  };
}
function reward(status = 'running'): Experiment {
  const paired: ExperimentJob = Object.assign(job('paired', 'complete'), {
    reward_evidence: { changed_edges: 87, gain_min: .5, gain_max: 1.7, gain_mean: 1.04, lower_bound_fraction: .02, upper_bound_fraction: .03, kc_active_fraction: .24, dan_spikes: 125, dan_compartment_spikes: [70, 55] as [number, number], tonic_dan_hz: [18.5, 3.25] as [number, number], mbon_mean_hz: 11.2 },
    reward_curve: [{ trial: 1, gain_mean: 1, dan_spikes: 4, home_response: 7.5, away_response: 6.1 }, { trial: 16, gain_mean: 1.04, dan_spikes: 5, home_response: 8.3, away_response: 5.8 }],
    class_confusion: [[7, 2], [1, 2]] as [[number, number], [number, number]],
  });
  return {
    id: 'reward-v3-test', kind: 'dopamine-association', status,
    created_at: '2026-09-11T12:00:00Z', updated_at: '2026-09-11T13:00:00Z',
    protocol: { global_weight_scale: .5, plasticity_onset_ms: 100, dan_baseline_window_ms: 50, min_teaching_evoked_fraction: .5, max_kc_code_overlap: .5 },
    reward: {
      scope: 'Bounded MLB pilot using reused development rows.',
      rule: 'Biphasic KC/DAN spike-trace gain update.',
      note: 'One frozen protocol; no retuning after observing scores.',
      train_n: 64, validation_n: 32, calibration_n: 16,
      anatomy: {
        neurons: 130000, kc: 5200, dans: 8, plastic_edges: 91, dopamine_only_fast_outputs_zeroed: 912,
        compartments: [
          { label: 'home teaching circuit', dan_type: 'PPL101', mbon_type: 'MBON11', dans: 4, mbons: 3, plastic_edges: 51 },
          { label: 'away teaching circuit', dan_type: 'PAM11', mbon_type: 'MBON07', dans: 4, mbons: 2, plastic_edges: 40 },
        ],
      },
      fixed_readout: { method: 'Negative standardized selected-MBON response', mean: [4.5, 3.25], scale: [1.2, .8], prior: [.55, .45] },
      prior_metrics: { ...metric, log_loss: .7001, accuracy: .55 },
      activity_gate: { status: 'passed', message: 'Measured circuit activity passed frozen guards.', kc_active_fraction: .24, max_mbon_hz: 12.4, input_discrimination: true, teaching_responsive: [true, true] as [boolean, boolean], teaching_compartment_spikes: [20, 18] as [number, number], teaching_scheduled_spikes: [8, 60] as [number, number], teaching_evoked_spikes: [7, 42] as [number, number], tonic_dan_hz: [18.5, 3.25] as [number, number], kc_code_overlap: .31, post_stimulus_kc_active_fraction: .04 },
      outcome: { status: 'descriptive', message: 'Matched-arm comparison completed.', paired_minus_frozen_log_loss: -.0123, paired_minus_shuffled_log_loss: -.0067 },
    },
    jobs: [
      paired,
      job('shuffled', 'failed', { error: 'Measured activity diverged.' }),
      job('frozen', 'budget_stopped', { cancellation_reason: 'Wall-clock budget reached.' }),
    ],
    artifacts: {
      manifest: { label: 'Reward manifest', url: '/api/experiments/reward-v3-test/artifacts/manifest', sha256: 'abc' },
      paired_trials: { label: 'Paired trial evidence', url: '/api/experiments/reward-v3-test/artifacts/paired', sha256: 'def', job_id: 'paired' },
    },
  };
}
function v2(): Experiment {
  return { id: 'v2-test', status: 'complete', created_at: '2026-09-10T12:00:00Z', updated_at: '2026-09-10T13:00:00Z', jobs: [], artifacts: {} };
}
function index(experiments: Experiment[]): ExperimentIndex {
  return { experiments, active_v1: { run_id: 'v1-active' }, prospective: { status: 'awaiting_candidate', sports: {} } };
}
function view(data: ExperimentIndex | null, error = '', selectedJobId = '') {
  return renderToStaticMarkup(<RewardExperimentsView data={data} error={error} selectedExperimentId="" selectedJobId={selectedJobId} onSelectExperiment={vi.fn()} onSelectJob={vi.fn()}/>);
}

it('indexes only dopamine-association manifests and places the tracker before the v2 matrix', () => {
  expect(rewardExperiments([v2(), reward()]).map(row => row.id)).toEqual(['reward-v3-test']);
  const training = TrainingView({ data: null, error: '', loading: false });
  const children = [training.props.children].flat(Infinity);
  expect(children.findIndex(child => child?.type === RewardExperiments)).toBeLessThan(children.findIndex(child => child?.type === ExperimentRuns));
});

it('renders loading, empty, fetch-error, and stale-data states without inventing a result', () => {
  expect(view(null)).toContain('Loading reward experiment registry');
  expect(view(index([v2()]))).toContain('No dopamine-association experiment has started');
  expect(view(null, 'Registry unavailable.')).toContain('Registry unavailable.');
  const stale = view(index([reward()]), 'offline');
  expect(stale).toContain('Showing last loaded reward results.');
  expect(stale).toContain('offline');
  expect(stale).toContain('Bounded MLB pilot using reused development rows.');
});

it.each(['running', 'failed', 'complete', 'budget_stopped'])('shows the manifest %s status from the registry', status => {
  expect(view(index([reward(status)]))).toContain(status.replaceAll('_', ' '));
});

it('shows the measured three-arm protocol, fixed readout, gate, outcome, errors, and selected-arm evidence', () => {
  const html = view(index([reward()]), '', 'paired');
  expect(html).toContain('paired');
  expect(html).toContain('shuffled');
  expect(html).toContain('frozen');
  expect(html).toContain('Measured activity diverged.');
  expect(html).toContain('Wall-clock budget reached.');
  expect(html).toContain('Negative standardized selected-MBON response');
  expect(html).toContain('Measured circuit activity passed frozen guards.');
  expect(html).toContain('Matched-arm comparison completed.');
  expect(html).toContain('87');
  expect(html).toContain('0.612');
  expect(html).toContain('Calibration error');
  expect(html).toContain('0.080');
  expect(html).toContain('Reward manifest');
  expect(html).toContain('Paired trial evidence');
});

it('shows common-seed and per-compartment dopamine evidence with the fixed prior comparator', () => {
  const html = view(index([reward()]), '', 'paired');
  expect(html).toContain('Common-seed input discrimination');
  expect(html).toContain('present');
  expect(html).toContain('Teaching-check total DAN spikes');
  expect(html).toContain('<dt>Teaching-check total DAN spikes</dt><dd>38</dd>');
  expect(html).toContain('PPL101');
  expect(html).toContain('PAM11');
  expect(html).toContain('20');
  expect(html).toContain('18');
  expect(html).toContain('Arm-training DAN spikes');
  expect(html).toContain('70');
  expect(html).toContain('55');
  expect(html).toContain('Fixed class-frequency prior');
  expect(html).toContain('0.700');
  const failedDiscrimination = reward();
  failedDiscrimination.reward!.activity_gate!.input_discrimination = false;
  expect(view(index([failedDiscrimination]))).toContain('<dt>Common-seed input discrimination</dt><dd>absent</dd>');
  const silentAwayTeaching = reward();
  silentAwayTeaching.reward!.activity_gate!.teaching_responsive = [true, false];
  const responseHtml = view(index([silentAwayTeaching]));
  expect(responseHtml).toContain('<th scope="row">home teaching circuit</th><td>PPL101</td><td>responsive</td><td>20</td><td>18.5 Hz</td><td>8</td><td>7</td>');
  expect(responseHtml).toContain('<th scope="row">away teaching circuit</th><td>PAM11</td><td>not responsive</td><td>18</td><td>3.3 Hz</td><td>60</td><td>42</td>');
});

it('shows the phasic-baseline protocol, declared gate margins and code-specificity evidence', () => {
  const html = view(index([reward()]), '', 'paired');
  expect(html).toContain('Phasic dopamine drive');
  expect(html).toContain('start 100 ms into each trial');
  expect(html).toContain('preceding 50 ms');
  expect(html).toContain('signed baseline subtraction can change gains without teaching');
  expect(html).toContain('It does not establish cue-specific learning');
  expect(html).not.toContain('tonic firing carries no teaching');
  expect(html).toContain('at least 50.0% of its scheduled forced spikes');
  expect(html).toContain('overlap at most 50.0% between calibration games');
  expect(html).toContain('<dt>KC set overlap between calibration games</dt><dd>31.0%</dd>');
  expect(html).toContain('<dt>KCs still firing after stimulus offset</dt><dd>4.0%</dd>');
  expect(html).toContain('<dt>Tonic DAN rate (home / away)</dt><dd>18.5 Hz / 3.3 Hz</dd>');
  const failed = reward('failed');
  failed.reward!.activity_gate = { status: 'failed', message: 'No outcome-trained comparison ran: a teaching population evoked fewer spikes above its tonic rate than the declared margin; the active KC set is not game-specific (calibration overlap exceeds the guard).', kc_active_fraction: .74, max_mbon_hz: 368.3, input_discrimination: true, teaching_responsive: [false, true], teaching_compartment_spikes: [70, 127], teaching_scheduled_spikes: [8, 60], teaching_evoked_spikes: [2, 37], tonic_dan_hz: [380, 66.1], kc_code_overlap: .989, post_stimulus_kc_active_fraction: .727 };
  failed.reward!.outcome = { status: 'failed', message: failed.reward!.activity_gate.message };
  delete failed.reward!.fixed_readout;
  failed.jobs = failed.jobs.map(job => ({ ...job, status: 'failed', phase: 'failed', metrics: undefined, reward_evidence: undefined, reward_curve: undefined, class_confusion: undefined }));
  const failedHtml = view(index([failed]));
  expect(failedHtml).toContain('Activity gate · failed');
  expect(failedHtml).toContain('the active KC set is not game-specific');
  expect(failedHtml).toContain('<th scope="row">home teaching circuit</th><td>PPL101</td><td>not responsive</td><td>70</td><td>380.0 Hz</td><td>8</td><td>2</td>');
  expect(failedHtml).toContain('<dt>KC set overlap between calibration games</dt><dd>98.9%</dd>');
  expect(failedHtml).toContain('<dt>KCs still firing after stimulus offset</dt><dd>72.7%</dd>');
  expect(failedHtml).not.toContain('Fixed readout');
  const legacy = reward();
  delete legacy.protocol;
  legacy.reward!.activity_gate = { status: 'passed', message: 'Legacy schema-1 gate.', kc_active_fraction: .24, max_mbon_hz: 12.4, input_discrimination: true, teaching_responsive: [true, true], teaching_compartment_spikes: [20, 18] };
  const legacyHtml = view(index([legacy]));
  expect(legacyHtml).not.toContain('Phasic dopamine drive');
  expect(legacyHtml).toContain('<dt>KC set overlap between calibration games</dt><dd>—</dd>');
  expect(legacyHtml).toContain('<td>responsive</td><td>20</td><td>—</td><td>—</td><td>—</td>');
});

it('renders selected-arm class confusion with explicit truth and prediction axes', () => {
  const html = view(index([reward()]), '', 'paired');
  expect(html).toContain('Validation class confusion');
  expect(html).toContain('Truth / prediction');
  expect(html).toContain('Predicted home');
  expect(html).toContain('Predicted away');
  expect(html).toContain('<th scope="row">Home truth</th><td>7</td><td>2</td>');
  expect(html).toContain('<th scope="row">Away truth</th><td>1</td><td>2</td>');
});

it('states the recorded experimental dynamics and the limits of dense-KC activity guards', () => {
  const html = view(index([reward()]));
  expect(html).toContain('Global fast-weight scale');
  expect(html).toContain('0.500');
  expect(html).toContain('All 912 pure dopamine neurons');
  expect(html).toContain('zero direct fast outgoing transmission');
  expect(html).toContain('numerical activity guards');
  expect(html).toContain('do not validate physiological firing density');
  expect(html).toContain('Maximum MBON rate');
  expect(html).toContain('12.40 Hz');
});

it('keeps manifest evidence downloadable when a failed activity gate creates no arm runs', () => {
  const failed = reward('failed');
  failed.error = 'Activity gate stopped the experiment.';
  failed.jobs = [];
  const html = view(index([failed]));
  expect(html).toContain('Activity gate stopped the experiment.');
  expect(html).toContain('No matched arm has been registered.');
  expect(html).toContain('Reward manifest');
});

it('renders an accessible measured-trial curve and its underlying data table', () => {
  const html = view(index([reward()]), '', 'paired');
  expect(html).toContain('aria-label="Gain mean across measured trials"');
  expect(html).toContain('Learning-curve data');
  expect(html).toContain('<td>16</td>');
  expect(html).toContain('<td>8.300</td>');
});

it('states the experiment boundary without treating engineered teaching or reused scores as biological or market evidence', () => {
  const html = view(index([reward()]));
  expect(html).toContain('teaching-cell mapping is engineered');
  expect(html).toContain('does not reconstruct a biological reward-prediction error');
  expect(html).toContain('validation scores reuse development data');
  expect(html).toContain('bookmaker edge');
});

it('shows the glomerular identity encoder, its feature map and the KC input gain when recorded', () => {
  const experiment = reward();
  experiment.protocol = { ...experiment.protocol, encoder: 'glomerular-tuning-v1', encoder_peak_hz: 100, encoder_tuning_width: .5, encoder_min_kc_contacts: 100, kc_input_gain: .5 };
  experiment.reward!.encoder = 'glomerular-tuning-v1';
  experiment.reward!.anatomy!.kc_input_gain = .5;
  experiment.reward!.anatomy!.sensory_input_gain = 0;
  experiment.reward!.anatomy!.apl_output_gain = .25;
  experiment.reward!.anatomy!.encoder = {
    encoder: 'glomerular-tuning-v1', glomeruli: 4, centers_per_feature: 2, center_span: 1.5, floor_fraction: .05,
    ports_driven: 9, ports_total: 686, eligible_transmitter: 'acetylcholine', min_kc_contacts: 100, dropped_glomeruli: ['VA7m_adPN'],
    peak_hz: 100, tuning_width: .5,
    features: [
      { feature: 0, glomeruli: [{ type: 'DA1_lPN', center: -1.5, cells: 3, kc_contacts: 1234 }, { type: 'DM1_lPN', center: 1.5, cells: 2, kc_contacts: 987 }] },
      { feature: 1, glomeruli: [{ type: 'DC1_adPN', center: -1.5, cells: 2, kc_contacts: 456 }, { type: 'DL1_adPN', center: 1.5, cells: 2, kc_contacts: 321 }] },
    ],
  };
  const html = view(index([experiment]));
  expect(html).toContain('Sensory identity code (glomerular-tuning-v1)');
  expect(html).toContain('each of the 2 standardized pregame features drives its own 2 annotated acetylcholine ALPN glomeruli (4 glomeruli; 9 of 686 ALPN ports)');
  expect(html).toContain('Gaussian width 0.50 and a 100 Hz peak, silent below 5.0% of peak');
  expect(html).toContain('1 surplus glomeruli (VA7m_adPN) stay undriven');
  expect(html).toContain('<strong>Cell-type input gains:</strong> every synapse ending at a Kenyon cell is scaled by 0.500');
  expect(html).toContain('every synapse ending at an ALPN port is scaled by 0.000, so the ports are labeled lines');
  expect(html).toContain('every synapse leaving the two annotated GABAergic APL neurons is scaled by 0.250');
  expect(html).toContain('Feature-to-glomerulus map (4 glomeruli)');
  expect(html).toContain('<th scope="row">1</th><td>DA1_lPN (-1.5 · 3 · 1,234); DM1_lPN (1.5 · 2 · 987)</td>');
  const legacyHtml = view(index([reward()]));
  expect(legacyHtml).not.toContain('Sensory identity code');
  expect(legacyHtml).not.toContain('Cell-type input gains');
  expect(legacyHtml).not.toContain('Feature-to-glomerulus map');
});
