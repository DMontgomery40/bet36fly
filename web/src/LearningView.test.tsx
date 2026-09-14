import { readFileSync } from 'node:fs';
import { describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import {
  DEFAULT_JOB_FORM, conditioningVerdict, jobsActive, num, rate, signed, spikeMap, stageBadges, triple,
} from './learningTypes';
import type { AssociativeEvidence, ConditioningRun, Confirmation, JobsPayload, StressRun } from './learningTypes';

/** `useResource` is the only thing mocked; `request` stays real so the 405 path is exercised. */
const hosts = vi.hoisted(() => ({
  sensory: { data: null as unknown, loading: false, error: 'Evidence failed validation.', reload: vi.fn() },
  evidence: { data: null as unknown, loading: false, error: '', reload: vi.fn() },
  checkpoints: { data: { checkpoints: [] } as unknown, loading: false, error: '', reload: vi.fn() },
  absent: { data: null as unknown, loading: false, error: '', reload: vi.fn() },
  requested: [] as (string | null)[],
}));
vi.mock('./data', async importActual => {
  const actual = await importActual<typeof import('./data')>();
  return {
    ...actual,
    useResource: (url: string | null) => {
      hosts.requested.push(url);
      return url === null ? hosts.absent
        : url.includes('/api/associative/evidence') ? hosts.evidence
        : url.includes('/api/associative/checkpoints') ? hosts.checkpoints : hosts.sensory;
    },
  };
});
import App from './App';
import LearningView, {
  ConditioningCard, ConfirmationSection, JobsSection, LearningBadges, SportsSection, StressSection, startJob,
} from './LearningView';
vi.stubGlobal('window', { location: { hash: '#learning' } });

const READ_ONLY = 'Verification mode is read-only; training and inference are disabled.';
const CONDITIONING_ERROR = 'RuntimeError: entry gate failed before any arm ran.';

function evidence(overrides: Partial<AssociativeEvidence> = {}): AssociativeEvidence {
  return {
    contract: { path: 'docs/EXPERIMENT_ASSOCIATIVE.md', sha256: 'a'.repeat(64), exists: true },
    circuit: { path: 'configs/associative-circuit-01.json', sha256: 'b'.repeat(64) },
    links: [{
      identity: 'associative-links-cd33a0b4dfd97540c887', valid: true, status: 'completed',
      checks: { sweet_reaches_dopamine: false, reinforcer_drives_reward_dans: true },
      links: {
        taste_sweet_no_interventions: { total_spikes: 1005, kc_active: 0, tail_spikes: 0, dan_spikes_by_type: {}, mbon_spikes_by_type: {} },
        reinforcer_alone: { total_spikes: 1075, kc_active: 0, tail_spikes: 0, dan_spikes_by_type: { PAM01: 514, PAM08: 561 }, mbon_spikes_by_type: {}, drive_events: 114 },
      },
      odor_code: {
        width: 16, hz: 118, keys: 34, kc_active_min_median_max: [98, 388, 988], mbon05_min_median_max: [12, 50, 97],
        mbon05_silent_keys: [], reward_dan_spikes_total: 58, jaccard_mean: 0.14014, jaccard_max: 0.44275, tail_max: 0,
      },
    }],
    conditioning: [qualifiedRun()],
    sports: [], evaluations: [],
    mechanism_qualified: true, qualified_conditioning: ['associative-conditioning-d1d3992e38c1dfa5fef1'],
    sensory_confirmation_unchanged: 'sensory-confirmation-4887cb8c17f6281d8166',
    note: 'Missing or failed evidence stays missing or failed here.',
    ...overrides,
  };
}
function qualifiedRun(): ConditioningRun {
  return {
    identity: 'associative-conditioning-d1d3992e38c1dfa5fef1', valid: true, status: 'completed', error: null,
    calls: 389, wall_seconds: 1200.5, odors: { A: ['ORN_DA4m'], B: ['ORN_DL5'] },
    entry_gate: { kc_recruited: true }, entry_gate_passed: true,
    audit: { bound_contact_calls: [], recovery_failures: [], reward_dan_spikes_in_cue_only_trials: 0 },
    summary: { acquisition_passed: true, retention_passed: true, reversal_passed: true, audit_passed: true, all_passed: true },
    acquisition: {
      all_passed: true, criteria: { acquisition_response: true, swap_mirror: true }, readout: 'sum',
      null_arms: ['unpaired', 'untaught', 'frozen', 'lesion'], null_response_scale: 0, null_gain_scale: 0,
      arms: {
        paired: { contrast: [-12, -7, -7], mean_contrast: -8.6667, a_edge_mean_gain_change: -0.07753, b_edge_mean_gain_change: -0.00898, changed_edges: 699, max_abs_gain_change: 0.22474, bytes_identical_to_unit: false },
        frozen: { contrast: [0, 0, 0], mean_contrast: 0, a_edge_mean_gain_change: 0, b_edge_mean_gain_change: 0, changed_edges: 0, max_abs_gain_change: 0, bytes_identical_to_unit: true },
      },
    },
    retention: { passed: true },
    reversal: { all_passed: true, criteria: { erasure_flips_preference: true }, contingency_swap_descriptive: { b_depressed: true } },
    probes: {}, protocol_sha256: 'c'.repeat(64),
  };
}
function failedRun(): ConditioningRun {
  return {
    identity: 'associative-conditioning-42845736c62d3ac9841e', valid: true, status: 'failed', error: CONDITIONING_ERROR,
    calls: null, wall_seconds: null, odors: null, entry_gate: null, entry_gate_passed: false,
    summary: { acquisition_passed: false, retention_passed: null, reversal_passed: null, audit_passed: null, all_passed: false },
    acquisition: { all_passed: false, criteria: null, readout: null, null_arms: null, null_response_scale: null, null_gain_scale: null, arms: null },
    retention: null, reversal: null, probes: null, protocol_sha256: null,
  };
}

describe('dopamine learning stage badges', () => {
  it('keeps the four stage claims separate when the mechanism is qualified but nothing predicts better', () => {
    const badges = stageBadges(evidence());
    expect(badges.map(badge => badge.key)).toEqual(['implemented', 'conditioning', 'prediction', 'application']);
    expect(badges.map(badge => badge.state)).toEqual(['Yes', 'Yes', 'Not established', 'No']);
    const html = renderToStaticMarkup(<LearningBadges evidence={evidence()}/>);
    expect(html).toContain('Mechanism implemented');
    expect(html).toContain('Controlled acquisition, retention and reversal qualified');
    expect(html).toContain('associative-conditioning-d1d3992e38c1dfa5fef1');
    expect(html).toContain('Plasticity improves held-out prediction');
    expect(html).toContain('Not established');
    expect(html).toContain('Application uses a learned checkpoint');
    expect(html).toContain('remain the frozen sensory confirmation');
    expect(html).toContain('checkpoints are inspectable only');
    expect(html.match(/learning-verdict learning-/g)).toHaveLength(4);
  });
  it('never promotes one claim from another', () => {
    const qualifiedOnly = stageBadges(evidence());
    expect(qualifiedOnly[2].verdict).toBe('no');
    const contributing = stageBadges(evidence({ evaluations: [{ identity: 'associative-sports-evaluation-01', valid: true, plasticity_contributes: true, goal_passed: true }] }));
    expect(contributing[1].verdict).toBe('yes');
    expect(contributing[2].verdict).toBe('yes');
    const unqualified = stageBadges(evidence({ mechanism_qualified: false, qualified_conditioning: [] }));
    expect(unqualified[1].state).toBe('Not qualified');
    expect(unqualified[0].verdict).toBe('yes');
    expect(stageBadges(null).map(badge => badge.state)).toEqual(['Contract not readable', 'Not qualified', 'Not established', 'No']);
    expect(stageBadges(null).every(badge => badge.verdict !== 'yes')).toBe(true);
  });
});

describe('controlled conditioning cards', () => {
  it('renders a failed run as failed and shows its recorded error', () => {
    const html = renderToStaticMarkup(<ConditioningCard run={failedRun()}/>);
    expect(conditioningVerdict(failedRun()).label).toBe('Failed');
    expect(html).toContain('Failed');
    expect(html).toContain(CONDITIONING_ERROR);
    expect(html).toContain('acquisition · fail');
    expect(html).toContain('No acquisition criteria were recorded for this run.');
    expect(html).toContain('No arm measurements were recorded for this run.');
    expect(html).not.toContain('Qualified');
  });
  it('counts stored endpoint probes beside the recorded cue identities', () => {
    const run = qualifiedRun();
    run.probes = {
      'entry-unit-probe-A-3011': { owner: 'unit', cue: 'A', seed: 3011, response: [62, 55], gains_sha256: 'e'.repeat(64) },
      'entry-unit-probe-B-3011': { owner: 'unit', cue: 'B', seed: 3011, response: [73, 68], gains_sha256: 'e'.repeat(64) },
    };
    const html = renderToStaticMarkup(<ConditioningCard run={run}/>);
    expect(html).toContain('2 endpoint probe records stored with this run.');
    expect(html).toContain('ORN_DA4m');
    expect(html).toContain('reward dan spikes in cue only trials');
  });
  it('renders a qualified run with its arms and plain-language captions', () => {
    const html = renderToStaticMarkup(<ConditioningCard run={qualifiedRun()}/>);
    expect(html).toContain('Qualified');
    expect(html).toContain('cue then dopamine');
    expect(html).toContain('plasticity off');
    expect(html).toContain('-12.0, -7.0, -7.0');
    expect(html).toContain('-0.0775');
    expect(html).toContain('699');
    expect(html).toContain('acquisition · pass');
  });
  it.each([
    [{ identity: 'x', valid: false } as ConditioningRun, 'Invalid manifest', 'no'],
    [{ identity: 'x', valid: true, status: 'failed' } as ConditioningRun, 'Failed', 'no'],
    [{ identity: 'x', valid: true, status: 'completed', error: 'boom' } as ConditioningRun, 'Failed', 'no'],
    [{ identity: 'x', valid: true, status: 'completed', summary: { all_passed: true } } as ConditioningRun, 'Qualified', 'yes'],
    [{ identity: 'x', valid: true, status: 'completed', summary: { all_passed: false } } as ConditioningRun, 'Did not qualify', 'no'],
    [{ identity: 'x', valid: true, status: 'running' } as ConditioningRun, 'Status running', 'unknown'],
    [{ identity: 'x', valid: true, status: 'completed' } as ConditioningRun, 'No verdict recorded', 'unknown'],
  ])('reads verdict %# as a recorded state, never an assumed pass', (run, label, verdict) => {
    expect(conditioningVerdict(run)).toEqual({ label, verdict });
  });
});

/** Shaped after `summary`/`occupancy` in scripts/run_associative_stress.py as the evidence
 *  endpoint passes them through (`gains_sha256` stripped). */
function occupancy(label: string, calls: number, gamma4: number, gamma5: number) {
  const compartment = (lower: number) => ({ lower, upper: 0, above_rest: 1 - lower, mean: 1 - lower, deciles: [] });
  return { label, calls, '0': compartment(gamma4), '1': compartment(gamma5) };
}
function baselineStress(): StressRun {
  return {
    identity: 'associative-stress-9d1c4a77b0e2', valid: true, status: 'completed', arm: 'baseline', rho: null,
    calls: 486, wall_seconds: 913.25, error: null,
    lower_bound_occupancy: { '0': 0.4212, '1': 0.1075 }, upper_bound_occupancy: { '0': 0, '1': 0 },
    above_rest: { '0': 0.0125, '1': 0.25 }, total_recovery: 0, total_bound_contacts: 41892, memory_by_cycle: null,
    post_history: {
      acquisition_passed: false, reversal_flipped: false,
      paired_contrast: [-4, 1], untaught_contrast: [0, 1], reversal_preference: [-2, 3],
    },
    occupancy: [occupancy('unit', 6, 0, 0), occupancy('cycle-2', 30, 0.2004, 0.0511), occupancy('final', 60, 0.4212, 0.1075)],
  };
}
function recoveryStress(): StressRun {
  return {
    ...baselineStress(), identity: 'associative-stress-3f70bb18c54d', arm: 'recovery', rho: 0.01,
    lower_bound_occupancy: { '0': 0.0301, '1': 0.0102 }, above_rest: { '0': 0.6605, '1': 0.5508 },
    total_recovery: 118.2537, total_bound_contacts: 9044,
    post_history: {
      acquisition_passed: true, reversal_flipped: true,
      paired_contrast: [-6, -5], untaught_contrast: [0, 1], reversal_preference: [4, 3],
    },
    occupancy: [occupancy('unit', 6, 0, 0), occupancy('cycle-2', 30, 0.0455, 0.0188), occupancy('final', 60, 0.0301, 0.0102)],
  };
}

describe('continual-learning stress runs', () => {
  it('renders both arms with their recorded occupancy, chips and one chart each', () => {
    const html = renderToStaticMarkup(<StressSection runs={[baselineStress(), recoveryStress()]}/>);
    expect(html.match(/class="learning-card"/g)).toHaveLength(2);
    expect(html.match(/<svg/g)).toHaveLength(2);
    expect(html).toContain('baseline (no recovery)');
    expect(html.match(/class="learning-verdict learning-unknown">completed</g)).toHaveLength(2);
    expect(html).toContain('associative-stress-9d1c4a77b0e2');
    expect(html).toContain('associative-stress-3f70bb18c54d');
    // Baseline has no recovery term; the recovery arm shows the rho that was actually recorded.
    expect(html).toContain('none');
    expect(html).toContain('0.01');
    // Final lower-bound occupancy and above-rest fractions, as percentages of eligible synapses.
    expect(html).toContain('42.12%');
    expect(html).toContain('10.75%');
    expect(html).toContain('1.25%');
    expect(html).toContain('3.01%');
    expect(html).toContain('66.05%');
    expect(html).toContain('0.0000');
    expect(html).toContain('118.2537');
    expect(html).toContain('41,892');
    expect(html).toContain('9,044');
    expect(html).toContain('Post-history acquisition · fail');
    expect(html).toContain('Post-history acquisition · pass');
    expect(html).toContain('Reversal flipped · fail');
    expect(html).toContain('Reversal flipped · pass');
    expect(html).toContain('γ4 · MBON05');
    expect(html).toContain('γ5 · MBON01');
    expect(html).toContain('Litwin-Kumar 2021, Eq. 5');
    expect(html).toContain('never from baseball scores');
    // Both compartment traces are drawn from the three recorded probe labels.
    expect(html).toContain('cycle-2');
    expect(html).toContain('polyline');
    // React 19 hoists a nested <title> and drops its text, so the chart's accessible name must be an aria-label.
    expect(html).toContain('role="img"');
    expect(html).toContain('aria-label="Fraction of eligible Kenyon-cell synapses at the lower gain bound');
    expect(html).toContain('across 3 recorded probe points of run associative-stress-9d1c4a77b0e2');
    expect(html).not.toContain('<title');
  });
  it('reports a missing history as an empty state rather than an empty region', () => {
    const html = renderToStaticMarkup(<StressSection runs={[]}/>);
    expect(html).toContain('No continual-learning runs recorded.');
    expect(html).not.toContain('<svg');
  });
  it('keeps a failed run failed and prints its recorded error verbatim', () => {
    const run: StressRun = {
      ...baselineStress(), status: 'failed', error: 'boom', occupancy: [],
      lower_bound_occupancy: null, above_rest: null, total_recovery: null, total_bound_contacts: null, post_history: null,
    };
    const html = renderToStaticMarkup(<StressSection runs={[run]}/>);
    expect(html).toContain('boom');
    expect(html).toContain('Failed');
    // Exactly one verdict pill per card head, as on every other card on the page.
    expect(html.match(/class="learning-verdict learning-/g)).toHaveLength(1);
    expect(html).toContain('No occupancy history is recorded for this run');
    expect(html).not.toContain('<svg');
    expect(html.match(/Unavailable/g)?.length).toBeGreaterThanOrEqual(4);
    expect(html).toContain('Post-history acquisition · not recorded');
    expect(html).toContain('Reversal flipped · not recorded');
  });
  it('never invents a rho for a recovery run that did not record one', () => {
    const html = renderToStaticMarkup(<StressSection runs={[{ ...recoveryStress(), rho: null }]}/>);
    expect(html).toContain('Unavailable');
    expect(html).not.toContain('ρ</b> none');
  });
});

describe('season backtests', () => {
  it('states both verdicts explicitly and labels the paired-loss sign', () => {
    const html = renderToStaticMarkup(<SportsSection sports={[{
      identity: 'associative-sports-ae0abc32a47c07fd48b8', valid: true, status: 'completed', arm: 'frozen',
      learning_rate: null, season: 2022, games: 2429, calls: 30, reinforcements: 0, days: 179, checkpoints: [],
    }]} evaluations={[{
      identity: 'associative-sports-evaluation-01', valid: true, season: 2022, metrics: { plastic: { n: 100, accuracy: 0.54, log_loss: 0.68, brier: 0.24 } },
      paired_loss: { frozen: { mean: -0.004, interval: [-0.01, 0.002] } }, shuffled_minus_frozen: { mean: 0.001, interval: [-0.003, 0.005] },
      accuracy_interval: [0.5, 0.58], plasticity_contributes: false, goal_passed: true,
    }]}/>);
    expect(html).toContain('Plasticity contributes: no');
    expect(html).toContain('Better than chance: yes');
    expect(html).toContain('plastic pipeline minus the comparator');
    expect(html).toContain('Not applicable');
    expect(html).toContain('-0.0040');
  });
  it('shows explicit empty states instead of blank regions', () => {
    const html = renderToStaticMarkup(<SportsSection sports={[]} evaluations={[]}/>);
    expect(html).toContain('No season arm is recorded.');
    expect(html).toContain('No evaluation is recorded.');
  });
});

/** Shaped after the recorded manifest of `associative-confirmation-662fc9e1bd5d450aba64`
 *  as `build_evidence` flattens it (bet36fly/associative_api.py). */
function failedConfirmation(): Confirmation {
  return {
    identity: 'associative-confirmation-662fc9e1bd5d450aba64', valid: true, status: 'failed_confirmation', error: null,
    season: 2018, attempt: 1,
    source_url: 'https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameType=R&season=2018',
    source_sha256: '1e4f07f54161e93bcfe4823d923fc868ba1cf0d42ecd39ff4d5db7382759aa9c',
    source_fetched_at: '2026-09-14T04:02:12.384720+00:00',
    frozen_candidate_sha256: '34b8177d4539d31d616b38bf658136833696b88c3a37328a8ad7b8eab7a27355',
    arms: {
      plastic: { calls: 6500, reinforcements: 2388, final_gains_sha256: 'ef76e890ed193bfcfdff2681013e1d63e2a37e6802d550138c1d62557a943706', days: 184, bound_contacts: 66441227 },
      frozen: { calls: 30, reinforcements: 0, final_gains_sha256: 'eee1b3c392f1b2f83b4e2590a20909c98c25cd3e631aa92fb39ee4c8e4b14220', days: 184, bound_contacts: 0 },
      shuffled: { calls: 6500, reinforcements: 2388, final_gains_sha256: '1bc040eadab0af3d17b4b28d86b70539d30f8f601b8bb7cb5bbfa2b7f5147295', days: 184, bound_contacts: 67270538 },
      'plastic:baseline': { calls: 6500, reinforcements: 2388, final_gains_sha256: '5ad795e9798762522776214e01c2f4e79594981d2fd5e7c39c40f78d84d68633', days: 184, bound_contacts: 1245752162 },
    },
    metrics: {
      plastic: { n: 2429, accuracy: 0.569781803211198, log_loss: 0.6787178050172268, brier: 0.24288557143818984 },
      frozen: { n: 2429, accuracy: 0.5656648826677645, log_loss: 0.6780136505060231, brier: 0.24253798903678214 },
      shuffled: { n: 2429, accuracy: 0.5677233429394812, log_loss: 0.6789655857900919, brier: 0.24300300478012007 },
      'plastic:baseline': { n: 2429, accuracy: 0.5660765747221078, log_loss: 0.6790973500136949, brier: 0.24306709174148652 },
      encoder_only: { n: 2429, accuracy: 0.5718402634829148, log_loss: 0.674228263028722, brier: 0.24068782540517217 },
      same_information: { n: 2429, accuracy: 0.5660765747221078, log_loss: 0.6772615984331644, brier: 0.2420771082325974 },
      uniform: { n: 2429, accuracy: 0.5273775216138329, log_loss: 0.6931471805599453, brier: 0.25 },
      prior: { n: 2429, accuracy: 0.5273775216138329, log_loss: 0.6918237402277722, brier: 0.24933825427787656 },
    },
    paired_loss: {
      frozen: { mean: 0.0007041545112035464, interval: [0.00009600918556315937, 0.0013675598717078066] },
      shuffled: { mean: -0.00024778077286509274, interval: [-0.0006220462632195097, 0.00012489844353757415] },
      'plastic:baseline': { mean: -0.00037954499646824326, interval: [-0.0009388514038233849, 0.0001823003997757659] },
      encoder_only: { mean: 0.004489541988504746, interval: [0.0012882699159609873, 0.0076070179292005305] },
      same_information: { mean: 0.001456206584062452, interval: [-0.004359253887418961, 0.007247358947173071] },
      uniform: { mean: -0.014429375542718545, interval: [-0.021274777372880787, -0.007575110558261579] },
      prior: { mean: -0.01310593521054526, interval: [-0.019324755272866943, -0.006825843941554446] },
    },
    shuffled_minus_frozen: { mean: 0.0009519352840686392, interval: [0.00008399681791342389, 0.0018476554808009003] },
    baseline_minus_frozen: { mean: 0.0010836995076717896, interval: [0.00013100155979542188, 0.002058888142426279] },
    accuracy_interval: [0.5470154459838488, 0.5910356554326375], plasticity_contributes: false, better_than_chance: true,
    games: 2429, start: '2018-03-29T16:40:00Z', end: '2018-10-01T20:09:00Z',
    exclusions: { unplayed: 54, resumed_or_suspended: 4 },
    predictions_csv: 'output/associative/associative-confirmation-662fc9e1bd5d450aba64/predictions.csv',
  };
}
const METHOD_LABELS = [
  'Recovery plastic (candidate)', 'Frozen twin', 'Reinforcement-shuffled twin', 'No-recovery plastic baseline',
  'Encoder only', 'Same-information baseline', 'Training prior', 'Uniform chance',
];

describe('reserved-block confirmation', () => {
  it('renders the recorded failure, every labelled method and both verdicts separately', () => {
    const html = renderToStaticMarkup(<ConfirmationSection rows={[failedConfirmation()]}/>);
    expect(html).toContain('Reserved-block confirmation (2018, one attempt)');
    // The human reading and the raw status both appear; the label never replaces the recorded string.
    expect(html).toContain('Confirmation failed: plasticity does not contribute');
    expect(html).toContain('failed_confirmation');
    expect(html).toContain('associative-confirmation-662fc9e1bd5d450aba64');
    expect(html).toContain('2,429');
    expect(html).toContain('2018-03-29T16:40:00Z');
    expect(html).toContain('2018-10-01T20:09:00Z');
    expect(html).toContain('https://statsapi.mlb.com/api/v1/schedule?sportId=1&amp;gameType=R&amp;season=2018');
    expect(html).toContain('2026-09-14T04:02:12.384720+00:00');
    expect(html).toContain('1e4f07f54161');
    expect(html).toContain('34b8177d4539');
    // Every method carries its plain-language label, in the declared order.
    for (const label of METHOD_LABELS) expect(html).toContain(label);
    const positions = METHOD_LABELS.map(label => html.indexOf(label));
    expect(positions).toEqual([...positions].sort((a, b) => a - b));
    expect(html).toContain('56.98%');
    expect(html).toContain('0.6787');
    expect(html).toContain('0.2429');
    // A season is a year, never a formatted count.
    expect(html).toContain('<b>Season</b> 2018');
    expect(html).not.toContain('2,018');
    // Paired table: header, sign caption and the six-place values that keep a 1e-4 bound visible.
    expect(html).toContain('Plastic minus comparator (95% paired interval)');
    expect(html).toContain('A negative value favours the plastic arm');
    expect(html).toContain('an interval entirely above zero means the plastic arm is reliably worse');
    expect(html).toContain('+0.000704 (0.000096 to 0.001368)');
    expect(html).toContain('-0.014429');
    expect(html).toContain('Reinforcement-shuffled twin minus frozen twin: +0.000952');
    expect(html).toContain('No-recovery plastic baseline minus frozen twin: +0.001084');
    expect(html).toContain('54.70% – 59.10%');
    expect(html).toContain('unplayed 54');
    expect(html).toContain('predictions.csv');
    // Arms are recorded per arm, never merged into a single training claim.
    expect(html).toContain('66,441,227');
    expect(html).toContain('2,388');
    // The two questions stay two chips.
    expect(html).toContain('Better than chance: yes');
    expect(html).toContain('Plasticity contributes: no');
  });
  it('reports the refuted contribution in the stage badge without collapsing the four claims', () => {
    const badges = stageBadges(evidence({ confirmations: [failedConfirmation()] }));
    expect(badges.map(badge => badge.key)).toEqual(['implemented', 'conditioning', 'prediction', 'application']);
    expect(badges[2].state).toBe('No (confirmed on the reserved block)');
    expect(badges[2].verdict).toBe('no');
    const html = renderToStaticMarkup(<LearningBadges evidence={evidence({ confirmations: [failedConfirmation()] })}/>);
    expect(html).toContain('No (confirmed on the reserved block)');
    expect(html).toContain('associative-confirmation-662fc9e1bd5d450aba64 (season 2018)');
    expect(html.match(/learning-verdict learning-/g)).toHaveLength(4);
  });
  it('confirms a contributing reserved block just as explicitly', () => {
    const badges = stageBadges(evidence({ confirmations: [{ ...failedConfirmation(), status: 'passed_confirmation', plasticity_contributes: true }] }));
    expect(badges[2].state).toBe('Yes (confirmed on the reserved block)');
    expect(badges[2].verdict).toBe('yes');
    const html = renderToStaticMarkup(<ConfirmationSection rows={[{ ...failedConfirmation(), status: 'passed_confirmation', plasticity_contributes: true }]}/>);
    expect(html).toContain('Confirmation passed: plasticity contributes');
    expect(html).toContain('passed_confirmation');
    expect(html).toContain('Plasticity contributes: yes');
  });
  it('shows an explicit empty state and leaves the badge unestablished when nothing is recorded', () => {
    const html = renderToStaticMarkup(<ConfirmationSection rows={[]}/>);
    expect(html).toContain('No reserved-block confirmation recorded.');
    expect(html).not.toContain('<table');
    expect(stageBadges(evidence()).map(badge => badge.state)).toEqual(['Yes', 'Yes', 'Not established', 'No']);
    expect(stageBadges(evidence({ confirmations: [] }))[2].state).toBe('Not established');
    expect(stageBadges(evidence({ confirmations: null }))[2].state).toBe('Not established');
    expect(stageBadges(evidence())[2].detail).toContain('No reserved-block confirmation is recorded.');
    expect(stageBadges(evidence({ confirmations: [] }))[2].detail).toContain('No reserved-block confirmation is recorded.');
  });
  it('prints a runtime failure verbatim and records no verdict it does not have', () => {
    const row: Confirmation = {
      identity: 'associative-confirmation-0000000000000000', valid: true, status: 'failed_runtime', error: 'boom',
      season: 2018, attempt: 1, source_url: null, source_sha256: null, source_fetched_at: null,
      frozen_candidate_sha256: null, arms: null, metrics: null, paired_loss: null, shuffled_minus_frozen: null,
      baseline_minus_frozen: null, accuracy_interval: null, plasticity_contributes: null, better_than_chance: null,
      games: null, start: null, end: null, exclusions: null, predictions_csv: null,
    };
    const html = renderToStaticMarkup(<ConfirmationSection rows={[row]}/>);
    expect(html).toContain('boom');
    expect(html).toContain('failed_runtime');
    expect(html).toContain('Better than chance: not recorded');
    expect(html).toContain('Plasticity contributes: not recorded');
    expect(html).toContain('No reserved-block metrics were recorded');
    expect(html).toContain('No paired loss intervals were recorded for this confirmation.');
    expect(html).toContain('No arm records are stored with this confirmation.');
    // A run that never scored a game gets no human confirmation reading at all.
    expect(html).not.toContain('Confirmation failed: plasticity does not contribute');
    expect(html).not.toContain('Confirmation passed: plasticity contributes');
    // An unrecorded status is unavailable, never a zero.
    const badge = stageBadges(evidence({ confirmations: [row] }))[2];
    expect(badge.state).toBe('Not established');
    // The badge must not claim an absence: this confirmation exists, it just has no verdict.
    expect(badge.detail).toContain('A reserved-block confirmation is recorded (1) but records no contribution verdict.');
    expect(badge.detail).not.toContain('No reserved-block confirmation is recorded.');
  });
});

describe('training jobs', () => {
  it('renders a refusal from the server verbatim', () => {
    const html = renderToStaticMarkup(<JobsSection jobs={[]} running={null} loadError="" startError={READ_ONLY}
      cancelError="" pending={false} form={DEFAULT_JOB_FORM} onChange={() => {}} onStart={() => {}} onCancel={() => {}}/>);
    expect(html).toContain(READ_ONLY);
    expect(html).toContain('No training job has been recorded on this installation.');
    expect(html).toContain('configs/associative-sports-01.json');
  });
  it('surfaces the 405 detail from the API without rewording it', async () => {
    const calls: [string, RequestInit | undefined][] = [];
    const original = globalThis.fetch;
    globalThis.fetch = (async (url: string, init?: RequestInit) => {
      calls.push([url, init]);
      return { ok: false, status: 405, json: async () => ({ detail: READ_ONLY }) };
    }) as unknown as typeof fetch;
    try {
      await expect(startJob(DEFAULT_JOB_FORM)).rejects.toThrow(READ_ONLY);
    } finally { globalThis.fetch = original; }
    expect(calls[0][0]).toBe('/api/associative/jobs');
    expect(calls[0][1]?.method).toBe('POST');
    expect(JSON.parse(String(calls[0][1]?.body))).toEqual({ protocol: 'configs/associative-sports-01.json', arm: 'plastic', learning_rate: 0.00002 });
  });
  it.each([
    [{ jobs: [], running: null } as JobsPayload, false],
    [{ jobs: [{ id: 'a', status: 'completed' }], running: null } as JobsPayload, false],
    [{ jobs: [{ id: 'a', status: 'failed' }], running: null } as JobsPayload, false],
    [{ jobs: [{ id: 'a', status: 'queued' }], running: null } as JobsPayload, true],
    [{ jobs: [{ id: 'a', status: 'running' }], running: 'a' } as JobsPayload, true],
  ])('polls only while a job is active (case %#)', (payload, active) => {
    expect(jobsActive(payload)).toBe(active);
  });
});

describe('the learning page stands alone', () => {
  it('renders without ever requesting the sensory confirmation', () => {
    hosts.sensory.data = null; hosts.sensory.error = 'Evidence failed validation.';
    hosts.evidence.data = evidence();
    hosts.requested.length = 0;
    const html = renderToStaticMarkup(<App/>);
    expect(hosts.requested).not.toContain('/api/sensory/summary');
    expect(html).toContain('Stage: dopamine-dependent learning on the MaleCNS circuit');
    expect(html).toContain('Dopamine learning');
    expect(html).toContain('Mechanism implemented');
    expect(html).not.toContain('Confirmation unavailable');
    expect(html).not.toContain('Evidence failed validation.');
  });
  it('shows a loading line rather than empty claims while evidence is still in flight', () => {
    hosts.evidence.data = null; hosts.evidence.error = '';
    const html = renderToStaticMarkup(<LearningView/>);
    expect(html).toContain('Loading recorded learning evidence…');
    expect(html).toContain('Not qualified');
    expect(html).toContain('No conditioning run is recorded.');
    hosts.evidence.data = evidence();
  });
  it('reports an evidence read failure instead of hiding it', () => {
    hosts.evidence.data = null; hosts.evidence.error = 'Request failed (503). Please retry.';
    const html = renderToStaticMarkup(<LearningView/>);
    expect(html).toContain('Request failed (503). Please retry.');
    expect(html).toContain('No learning evidence is shown until this read succeeds.');
    hosts.evidence.data = evidence(); hosts.evidence.error = '';
  });
});

describe('the header survives a fourth navigation item', () => {
  const read = (name: string) => readFileSync(new URL(name, import.meta.url), 'utf8');
  const appCss = read('./style.css');
  const mobile = appCss.slice(appCss.search(/@media\s*\(max-width:\s*720px\)/));
  it('lets the small-screen nav wrap instead of forcing one overflowing row', () => {
    expect(mobile).not.toBe('');
    const rule = /\.app-header\s+nav\s*\{([^}]*)\}/.exec(mobile);
    expect(rule).not.toBeNull();
    expect(rule![1].replace(/\s/g, '')).toContain('flex-wrap:wrap');
  });
  it('keeps every navigation label legible while it wraps', () => {
    const rule = /\.app-header\s+nav\s+a\s*\{([^}]*)\}/.exec(mobile);
    expect(rule).not.toBeNull();
    const size = Number(/font-size:\s*([\d.]+)px/.exec(rule![1])?.[1]);
    expect(size).toBeGreaterThanOrEqual(12);
  });
  it('holds the learning page above the 11px floor', () => {
    const sizes = [...read('./learning.css').matchAll(/font-size:\s*([\d.]+)px/g)].map(match => Number(match[1]));
    expect(sizes.length).toBeGreaterThan(0);
    expect(Math.min(...sizes)).toBeGreaterThanOrEqual(11);
  });
});

describe('measurement formatting never fabricates a number', () => {
  it.each([null, undefined, NaN])('reports %s as unavailable rather than zero', value => {
    expect(num(value as number)).toBe('Unavailable');
    expect(signed(value as number)).toBe('Unavailable');
    expect(triple(null)).toBe('Unavailable');
  });
  it('keeps a real zero distinct from a missing value', () => {
    expect(num(0)).toBe('0');
    expect(signed(0)).toBe('0.0000');
    expect(rate(0)).toBe('0');
    expect(rate(null)).toBe('Not applicable');
    expect(rate(0.00002)).toBe('2.0e-5');
    expect(spikeMap({})).toBe('none');
    expect(spikeMap({ PAM01: 514 })).toBe('PAM01 514');
  });
});
