import { count, fixed, pct } from './sensoryData';

/** Shapes returned by `/api/associative/*` (bet36fly/associative_api.py). Every recorded
 *  field may be absent when a manifest is partial or invalid, so nothing is required. */
export type LinkMeasurement = {
  total_spikes?: number | null; kc_active?: number | null; tail_spikes?: number | null;
  dan_spikes_by_type?: Record<string, number> | null; mbon_spikes_by_type?: Record<string, number> | null;
  drive_events?: number | null; dan_spikes?: number | null;
};
export type OdorCode = {
  width?: number | null; hz?: number | null; keys?: number | null;
  kc_active_min_median_max?: number[] | null; mbon05_min_median_max?: number[] | null;
  mbon05_silent_keys?: string[] | null; reward_dan_spikes_total?: number | null;
  jaccard_mean?: number | null; jaccard_max?: number | null; tail_max?: number | null;
};
export type LinksRun = {
  identity: string; valid: boolean; status?: string | null; checks?: Record<string, boolean> | null;
  links?: Record<string, LinkMeasurement> | null; odor_code?: OdorCode | null;
};
export type AcquisitionArm = {
  contrast?: number[] | null; mean_contrast?: number | null; a_edge_mean_gain_change?: number | null;
  b_edge_mean_gain_change?: number | null; changed_edges?: number | null; max_abs_gain_change?: number | null;
  bytes_identical_to_unit?: boolean | null;
};
export type ConditioningSummary = {
  acquisition_passed?: boolean | null; retention_passed?: boolean | null; reversal_passed?: boolean | null;
  audit_passed?: boolean | null; all_passed?: boolean | null;
};
export type ConditioningRun = {
  identity: string; valid: boolean; status?: string | null; error?: string | null; calls?: number | null;
  wall_seconds?: number | null; odors?: { A?: string[] | null; B?: string[] | null } | null;
  entry_gate?: Record<string, boolean> | null; entry_gate_passed?: boolean | null;
  summary?: ConditioningSummary | null; audit?: Record<string, unknown> | null;
  acquisition?: {
    all_passed?: boolean | null; criteria?: Record<string, boolean> | null; readout?: string | null;
    null_arms?: string[] | null; null_response_scale?: number | null; null_gain_scale?: number | null;
    arms?: Record<string, AcquisitionArm> | null;
  } | null;
  retention?: { passed?: boolean | null } | null;
  reversal?: { all_passed?: boolean | null; criteria?: Record<string, boolean> | null; contingency_swap_descriptive?: Record<string, unknown> | null } | null;
  probes?: Record<string, { owner?: string; cue?: string; seed?: number; response?: number[]; gains_sha256?: string }> | null;
  protocol_sha256?: string | null;
};
export type SportsRun = {
  identity: string; valid: boolean; status?: string | null; arm?: string | null; learning_rate?: number | null;
  season?: number | null; games?: number | null; calls?: number | null; reinforcements?: number | null;
  days?: number | null; wall_seconds?: number | null; final_gains_sha256?: string | null; error?: string | null;
  jobs?: string[] | null; checkpoints?: string[] | null;
};
export type EvaluationMetric = { n?: number | null; accuracy?: number | null; log_loss?: number | null; brier?: number | null };
export type PairedLoss = { mean?: number | null; interval?: number[] | null };
export type SportsEvaluation = {
  identity: string; valid: boolean; arms?: Record<string, string> | null; season?: number | null;
  readout_split?: string | null; training_games?: number | null; evaluation_games?: number | null;
  metrics?: Record<string, EvaluationMetric> | null; paired_loss?: Record<string, PairedLoss> | null;
  shuffled_minus_frozen?: PairedLoss | null; accuracy_interval?: number[] | null;
  plasticity_contributes?: boolean | null; goal_passed?: boolean | null;
  readouts?: unknown; predictions_csv?: string | null;
};
/** One arm of a reserved-block confirmation, as `associative_api.build_evidence` passes it through. */
export type ConfirmationArm = {
  calls?: number | null; reinforcements?: number | null; final_gains_sha256?: string | null;
  days?: number | null; bound_contacts?: number | null;
};
/** One one-shot confirmation on the reserved block. `status` is recorded verbatim; a run that
 *  never reached evaluation records `failed_runtime` with an `error` and no metrics at all. */
export type Confirmation = {
  identity: string; valid: boolean; status?: string | null; error?: string | null;
  season?: number | null; attempt?: number | null;
  source_url?: string | null; source_sha256?: string | null; source_fetched_at?: string | null;
  frozen_candidate_sha256?: string | null; arms?: Record<string, ConfirmationArm> | null;
  metrics?: Record<string, EvaluationMetric> | null;
  /** Plastic minus comparator: negative favours the plastic arm. */
  paired_loss?: Record<string, PairedLoss> | null;
  shuffled_minus_frozen?: PairedLoss | null; baseline_minus_frozen?: PairedLoss | null;
  accuracy_interval?: number[] | null; plasticity_contributes?: boolean | null; better_than_chance?: boolean | null;
  games?: number | null; start?: string | null; end?: string | null;
  exclusions?: Record<string, number> | null; predictions_csv?: string | null;
};

/** One compartment's gain-distribution snapshot at a single probe label. */
export type CompartmentOccupancy = {
  lower?: number | null; upper?: number | null; above_rest?: number | null; mean?: number | null; deciles?: number[] | null;
};
export type OccupancyPoint = {
  label?: string | null; calls?: number | null; '0'?: CompartmentOccupancy | null; '1'?: CompartmentOccupancy | null;
};
/** Fractions recorded per plastic compartment: '0' is γ4 (PAM08 → MBON05), '1' is γ5 (PAM01 → MBON01). */
export type CompartmentFractions = { '0'?: number | null; '1'?: number | null };
export type StressPostHistory = {
  acquisition_passed?: boolean | null; reversal_flipped?: boolean | null;
  paired_contrast?: number[] | null; untaught_contrast?: number[] | null; reversal_preference?: number[] | null;
};
export type StressRun = {
  identity: string; valid: boolean; status?: string | null; arm?: string | null; rho?: number | null;
  calls?: number | null; wall_seconds?: number | null; error?: string | null;
  lower_bound_occupancy?: CompartmentFractions | null; upper_bound_occupancy?: CompartmentFractions | null;
  above_rest?: CompartmentFractions | null; total_recovery?: number | null; total_bound_contacts?: number | null;
  memory_by_cycle?: Record<string, Record<string, number[]>> | null;
  post_history?: StressPostHistory | null; occupancy?: OccupancyPoint[] | null;
};
export type AssociativeEvidence = {
  contract: { path?: string | null; sha256?: string | null; exists?: boolean | null };
  circuit: { path?: string | null; sha256?: string | null };
  links: LinksRun[]; conditioning: ConditioningRun[]; sports: SportsRun[]; evaluations: SportsEvaluation[];
  /** Added with the continual-learning stage; an older manifest read has no `stress` key at all. */
  stress?: StressRun[] | null;
  /** Added with the reserved-block confirmation stage; an older manifest read has no `confirmations` key. */
  confirmations?: Confirmation[] | null;
  mechanism_qualified?: boolean | null; qualified_conditioning?: string[] | null;
  sensory_confirmation_unchanged?: string | null; note?: string | null;
};
export type JobProgress = {
  days?: number | null; calls?: number | null; reinforcements?: number | null; cache_hits?: number | null;
  cache_misses?: number | null; last_day?: string | null; gains_sha256?: string | null;
};
export type Job = {
  id: string; kind?: string | null; status?: string | null; arm?: string | null; learning_rate?: number | null;
  protocol?: string | null; created_at?: string | null; updated_at?: string | null; progress?: JobProgress | null;
  error?: string | null; run_identity?: string | null; resumed_from?: string | null;
  checkpoints?: { day?: string; gains_sha256?: string; path?: string }[] | null;
};
export type JobsPayload = { jobs: Job[]; running: string | null };
export type Checkpoint = { path: string; run?: string | null; name?: string | null; bytes?: number | null };
export type CheckpointsPayload = { checkpoints: Checkpoint[] };
export type PredictSide = { team?: string | null; odor_types?: string[] | null; response?: number[] | null; tail_spikes?: number | null };
export type Prediction = {
  checkpoint?: string | null; checkpoint_meta?: Record<string, unknown> | null; home?: PredictSide | null;
  away?: PredictSide | null; learned_differences?: number[] | null; plasticity?: boolean | null;
  outcomes_consumed?: boolean | null; gains_sha256?: string | null; probability_home?: number | null; note?: string | null;
};
export type StartJobForm = { protocol: string; arm: string; learning_rate: string; day_limit: string };
export type ProbeForm = { checkpoint: string; home: string; away: string };

export const ACTIVE_JOB_STATES = ['queued', 'running'];
export const JOB_ARMS = ['plastic', 'frozen', 'shuffled'];
export const DEFAULT_JOB_FORM: StartJobForm = { protocol: 'configs/associative-sports-01.json', arm: 'plastic', learning_rate: '0.00002', day_limit: '' };
export const DEFAULT_PROBE_FORM: ProbeForm = { checkpoint: '', home: 'mlb:147', away: 'mlb:121' };

/** Plain-language captions for the predeclared conditioning arms (docs/EXPERIMENT_ASSOCIATIVE.md §5). */
export const ARM_CAPTIONS: Record<string, string> = {
  paired: 'cue then dopamine',
  unpaired: 'cue and dopamine in separate trials',
  backward: 'dopamine before cue (predicted to potentiate)',
  untaught: 'cue only',
  frozen: 'plasticity off',
  lesion: 'dopamine-to-plasticity coupling removed',
  swap: 'the other cue is rewarded',
  order: 'same as paired, other presentation order',
};

/** Plain-language names for the methods a reserved-block confirmation scores. The key order is
 *  also the render order; a method that is not listed keeps its recorded name and is appended. */
export const CONFIRMATION_METHOD_LABELS: Record<string, string> = {
  plastic: 'Recovery plastic (candidate)',
  frozen: 'Frozen twin',
  shuffled: 'Reinforcement-shuffled twin',
  'plastic:baseline': 'No-recovery plastic baseline',
  encoder_only: 'Encoder only',
  same_information: 'Same-information baseline',
  prior: 'Training prior',
  uniform: 'Uniform chance',
};
/** Written with the word "minus" rather than a dash so the label survives every encoding. */
export const SHUFFLED_MINUS_FROZEN_LABEL = 'Reinforcement-shuffled twin minus frozen twin';
export const BASELINE_MINUS_FROZEN_LABEL = 'No-recovery plastic baseline minus frozen twin';
export const CONFIRMATION_EMPTY = 'No reserved-block confirmation recorded.';
export const CONFIRMATION_PAIRED_HEADER = 'Plastic minus comparator (95% paired interval)';

export function methodLabel(method: string) { return CONFIRMATION_METHOD_LABELS[method] || readable(method); }
/** Known methods in the declared order, then any other recorded method in its recorded order. */
export function orderedMethods<T>(map: Record<string, T> | null | undefined): [string, T][] {
  const known = Object.keys(CONFIRMATION_METHOD_LABELS);
  const rank = (name: string) => (known.indexOf(name) === -1 ? known.length : known.indexOf(name));
  return Object.entries(map || {}).sort((a, b) => rank(a[0]) - rank(b[0]));
}
/** The human reading of a recorded confirmation status, or null when no reading is declared.
 *  The raw status is always rendered beside this, never replaced by it. */
export function confirmationStatusLabel(status: string | null | undefined) {
  if (status === 'failed_confirmation') return 'Confirmation failed: plasticity does not contribute';
  if (status === 'passed_confirmation') return 'Confirmation passed: plasticity contributes';
  return null;
}
/** Human reading and recorded status together, so an unmapped status is still shown in full. */
export function confirmationOutcome(row: Confirmation) {
  const mapped = confirmationStatusLabel(row.status);
  return `${mapped || 'No confirmation outcome is declared for this status'} · recorded status ${words(row.status, 'not recorded')}`;
}
/** The head pill stays short; the full reading lives in the outcome line. */
export function confirmationState(row: Confirmation): { verdict: Verdict; label: string } {
  if (row.status === 'passed_confirmation') return { verdict: 'yes', label: 'Passed' };
  if (row.status === 'failed_confirmation') return { verdict: 'no', label: 'Failed' };
  if (row.status === 'failed_runtime' || row.error) return { verdict: 'no', label: 'Run failed' };
  if (!row.valid) return { verdict: 'no', label: 'Invalid manifest' };
  return { verdict: 'unknown', label: words(row.status, 'No status recorded') };
}
/** A season is a year, not a count, so it never picks up a thousands separator. */
export function year(value: number | null | undefined) {
  return typeof value === 'number' && Number.isFinite(value) ? String(value) : 'not recorded';
}
export function confirmationName(row: Confirmation) {
  return row.season == null ? row.identity : `${row.identity} (season ${row.season})`;
}

/** `count` throws on null, so every optional number goes through these guards instead. */
export function num(value: number | null | undefined) {
  return typeof value === 'number' && Number.isFinite(value) ? count(value) : 'Unavailable';
}
export function decimalOrMissing(value: number | null | undefined, places = 4) { return fixed(value, places); }
export function percentOrMissing(value: number | null | undefined, places = 2) { return pct(value, places); }
export function signed(value: number | null | undefined, places = 4) {
  return typeof value === 'number' && Number.isFinite(value) ? `${value > 0 ? '+' : ''}${value.toFixed(places)}` : 'Unavailable';
}
export function rate(value: number | null | undefined) {
  return typeof value === 'number' && Number.isFinite(value) ? (value === 0 ? '0' : value.toExponential(1)) : 'Not applicable';
}
export function seconds(value: number | null | undefined) {
  return typeof value === 'number' && Number.isFinite(value) ? `${value.toFixed(1)} s` : 'Unavailable';
}
export function words(value: string | null | undefined, fallback = 'Unavailable') { return value ? value : fallback; }
export function interval(bounds: number[] | null | undefined, places = 4) {
  return Array.isArray(bounds) && bounds.length === 2 ? `${fixed(bounds[0], places)} to ${fixed(bounds[1], places)}` : 'Unavailable';
}
export function percentInterval(bounds: number[] | null | undefined) {
  return Array.isArray(bounds) && bounds.length === 2 ? `${pct(bounds[0])} – ${pct(bounds[1])}` : 'Unavailable';
}
export function spikeMap(map: Record<string, number> | null | undefined) {
  const entries = Object.entries(map || {});
  return entries.length ? entries.map(([type, value]) => `${type} ${num(value)}`).join(', ') : 'none';
}
export function triple(values: number[] | null | undefined) {
  return Array.isArray(values) && values.length === 3 ? `${num(values[0])} / ${num(values[1])} / ${num(values[2])}` : 'Unavailable';
}
export function contrastList(values: number[] | null | undefined) {
  return Array.isArray(values) && values.length ? values.map(value => signed(value, 1)).join(', ') : 'Unavailable';
}
export function shortHash(value: string | null | undefined) { return value ? value.slice(0, 12) : 'Unavailable'; }
export function readable(name: string) { return name.replace(/_/g, ' '); }
/** Audit entries are either counts or lists of offending calls; both are reported as recorded. */
export function auditEntries(audit: Record<string, unknown> | null | undefined) {
  return Object.entries(audit || {}).map(([name, value]) => {
    if (Array.isArray(value)) return [name, value.length ? `${count(value.length)} recorded` : 'none'] as const;
    if (typeof value === 'number') return [name, num(value)] as const;
    if (typeof value === 'boolean') return [name, value ? 'yes' : 'no'] as const;
    return [name, value == null ? 'not recorded' : String(value)] as const;
  });
}

export type Verdict = 'yes' | 'no' | 'unknown';
export type Badge = { key: string; title: string; verdict: Verdict; state: string; detail: string };

/** The four separate stage claims. Nothing here is inferred from another claim. */
export function stageBadges(evidence: AssociativeEvidence | null): Badge[] {
  const contractExists = evidence?.contract?.exists === true;
  const qualified = evidence?.qualified_conditioning || [];
  const isQualified = evidence?.mechanism_qualified === true;
  const contributing = (evidence?.evaluations || []).filter(item => item.plasticity_contributes === true);
  // The reserved block is the one-shot confirmation and overrides a development evaluation in
  // either direction. A recorded refutation is reported first and is never softened.
  const confirmations = evidence?.confirmations || [];
  const refuted = confirmations.filter(item => item.plasticity_contributes === false);
  const confirmedContribution = confirmations.filter(item => item.plasticity_contributes === true);
  // A confirmation that never reached a contribution verdict (a runtime failure) is still a
  // recorded confirmation, so the fallback must not claim that none exists.
  const unresolved = confirmations.length - refuted.length - confirmedContribution.length;
  const confirmationClause = unresolved
    ? ` A reserved-block confirmation is recorded (${unresolved}) but records no contribution verdict.`
    : ' No reserved-block confirmation is recorded.';
  return [
    {
      key: 'implemented', title: 'Mechanism implemented',
      verdict: contractExists ? 'yes' : 'unknown', state: contractExists ? 'Yes' : 'Contract not readable',
      detail: contractExists
        ? `Dopamine-gated multiplicative gains on KC→MBON edges, declared in ${words(evidence?.contract?.path)}. Circuit ${shortHash(evidence?.circuit?.sha256)}.`
        : 'The predeclared contract file is missing, so nothing on this page is bound to a declared protocol.',
    },
    {
      key: 'conditioning', title: 'Controlled acquisition, retention and reversal qualified',
      verdict: isQualified ? 'yes' : 'no', state: isQualified ? 'Yes' : 'Not qualified',
      detail: isQualified
        ? `Qualified by ${qualified.join(', ')}. This qualifies the mechanism in this simulator only.`
        : 'No conditioning run has passed acquisition, retention, reversal and audit together.',
    },
    refuted.length
      ? {
        key: 'prediction', title: 'Plasticity improves held-out prediction',
        verdict: 'no' as Verdict, state: 'No (confirmed on the reserved block)',
        detail: `The one-shot reserved-block confirmation ${refuted.map(confirmationName).join(', ')} recorded plasticity_contributes false: the plastic minus frozen paired log-loss interval is not below zero. This result stands.`,
      }
      : confirmedContribution.length
      ? {
        key: 'prediction', title: 'Plasticity improves held-out prediction',
        verdict: 'yes' as Verdict, state: 'Yes (confirmed on the reserved block)',
        detail: `The one-shot reserved-block confirmation ${confirmedContribution.map(confirmationName).join(', ')} recorded plasticity_contributes true.`,
      }
      : {
        key: 'prediction', title: 'Plasticity improves held-out prediction',
        verdict: (contributing.length ? 'yes' : 'no') as Verdict, state: contributing.length ? 'Yes' : 'Not established',
        detail: contributing.length
          ? `Established by ${contributing.map(item => item.identity).join(', ')} on a development evaluation only.${confirmationClause}`
          : `No recorded evaluation places the plastic minus frozen paired log-loss interval below zero.${confirmationClause}`,
      },
    {
      key: 'application', title: 'Application uses a learned checkpoint',
      verdict: 'no', state: 'No',
      detail: `No — the product's predictions remain the frozen sensory confirmation; checkpoints are inspectable only.${evidence?.sensory_confirmation_unchanged ? ` The confirmation ${evidence.sensory_confirmation_unchanged} is unchanged by this stage.` : ''}`,
    },
  ];
}

/** A recorded verdict for one conditioning run. A failed run stays failed. */
export function conditioningVerdict(run: ConditioningRun): { verdict: Verdict; label: string } {
  if (!run.valid) return { verdict: 'no', label: 'Invalid manifest' };
  if (run.status === 'failed' || run.error) return { verdict: 'no', label: 'Failed' };
  if (run.summary?.all_passed === true) return { verdict: 'yes', label: 'Qualified' };
  if (run.summary && run.summary.all_passed === false) return { verdict: 'no', label: 'Did not qualify' };
  if (run.status && run.status !== 'completed') return { verdict: 'unknown', label: `Status ${run.status}` };
  return { verdict: 'unknown', label: 'No verdict recorded' };
}

/** Polling is only justified while a job is actually queued or running. */
export function jobsActive(payload: JobsPayload | null) {
  if (!payload) return false;
  if (payload.running) return true;
  return (payload.jobs || []).some(job => ACTIVE_JOB_STATES.includes(job.status || ''));
}

/** Newest first, without mutating the API response. */
export function newestFirst<T extends { identity: string }>(rows: T[]) { return [...rows].reverse(); }

export function errorText(error: unknown, fallback: string) {
  return error instanceof Error && error.message ? error.message : fallback;
}

/** The two plastic compartments the stress protocol records, with distinct high-contrast
 *  trace colours (blue vs rust reads apart at device pixel ratio 1 and under colour blindness). */
export const COMPARTMENTS: { key: '0' | '1'; label: string; color: string }[] = [
  { key: '0', label: 'γ4 · MBON05', color: '#12488f' },
  { key: '1', label: 'γ5 · MBON01', color: '#9c3208' },
];

/** Arm names are rendered exactly as recorded; an unrecognised arm is not relabelled. */
export function armLabel(arm: string | null | undefined) {
  if (arm === 'baseline') return 'baseline (no recovery)';
  if (arm === 'recovery') return 'recovery';
  return words(arm, 'not recorded');
}
/** Baseline has no recovery term at all. A recovery run with no recorded ρ stays unavailable
 *  rather than borrowing the baseline's "none", which would invent a mechanism claim. */
export function rhoText(arm: string | null | undefined, value: number | null | undefined) {
  if (arm === 'baseline') return 'none';
  return typeof value === 'number' && Number.isFinite(value) ? String(value) : 'Unavailable';
}
export type StressPoint = { label: string; values: Record<'0' | '1', number | null> };
/** Lower-bound occupancy per compartment across the recorded probe labels, in order. */
export function occupancyPoints(run: StressRun): StressPoint[] {
  return (run.occupancy || []).map((point, index) => {
    const values = { '0': null, '1': null } as Record<'0' | '1', number | null>;
    for (const compartment of COMPARTMENTS) {
      const value = point?.[compartment.key]?.lower;
      values[compartment.key] = typeof value === 'number' && Number.isFinite(value) ? value : null;
    }
    return { label: point?.label ? String(point.label) : `probe ${index + 1}`, values };
  });
}
