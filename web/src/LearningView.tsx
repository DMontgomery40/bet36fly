import { useEffect, useState } from 'react';
import { request, useResource } from './data';
import {
  ARM_CAPTIONS, COMPARTMENTS, DEFAULT_JOB_FORM, DEFAULT_PROBE_FORM, JOB_ARMS, armLabel, conditioningVerdict, contrastList,
  decimalOrMissing, auditEntries, errorText, interval, jobsActive, newestFirst, num, occupancyPoints, percentInterval,
  percentOrMissing, rate, readable, rhoText, seconds, shortHash, signed, spikeMap, stageBadges, triple, words,
} from './learningTypes';
import type {
  AssociativeEvidence, Badge, Checkpoint, CheckpointsPayload, ConditioningRun, Job, JobsPayload, LinksRun,
  Prediction, ProbeForm, SportsEvaluation, SportsRun, StartJobForm, StressRun, Verdict,
} from './learningTypes';
import './learning.css';

/** Poll the job registry every five seconds only while a job is queued or running. */
export function pollJobs(onData: (payload: JobsPayload) => void, onError: (message: string) => void) {
  let stopped = false;
  let timer: ReturnType<typeof setTimeout> | undefined;
  async function poll() {
    let active = false;
    try {
      const payload = await request<JobsPayload>('/api/associative/jobs');
      if (stopped) return;
      active = jobsActive(payload);
      onData(payload); onError('');
    } catch (error) {
      if (!stopped) onError(errorText(error, 'Unable to read the training job registry.'));
    }
    if (!stopped && active) timer = setTimeout(poll, 5000);
  }
  void poll();
  return () => { stopped = true; clearTimeout(timer); };
}

export function startJob(form: StartJobForm) {
  const body: Record<string, unknown> = { protocol: form.protocol.trim(), arm: form.arm };
  if (form.learning_rate.trim()) body.learning_rate = Number(form.learning_rate);
  if (form.day_limit.trim()) body.day_limit = Number(form.day_limit);
  return request<Job>('/api/associative/jobs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
}
export function cancelJob(id: string) {
  return request<{ id: string; status: string }>(`/api/associative/jobs/${encodeURIComponent(id)}/cancel`, { method: 'POST' });
}
export function probeCheckpoint(form: ProbeForm) {
  return request<Prediction>('/api/associative/predict', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ checkpoint: form.checkpoint, home: form.home.trim(), away: form.away.trim() }),
  });
}

function Chip({ verdict, children }: { verdict: Verdict; children: React.ReactNode }) {
  return <span className={`learning-chip learning-${verdict}`}>{children}</span>;
}
function Flag({ name, value }: { name: string; value: boolean | null | undefined }) {
  const verdict: Verdict = value === true ? 'yes' : value === false ? 'no' : 'unknown';
  return <li><Chip verdict={verdict}>{readable(name)} · {value === true ? 'pass' : value === false ? 'fail' : 'not recorded'}</Chip></li>;
}
export function ErrorBlock({ message }: { message: string }) {
  return <p className="learning-error" role="alert">{message}</p>;
}
function Empty({ children }: { children: React.ReactNode }) { return <p className="learning-empty">{children}</p>; }

export function LearningBadges({ evidence }: { evidence: AssociativeEvidence | null }) {
  const badges: Badge[] = stageBadges(evidence);
  return <ul className="learning-badges">{badges.map(badge => <li className="learning-badge" key={badge.key}>
    <h3>{badge.title}</h3>
    <span className={`learning-verdict learning-${badge.verdict}`}>{badge.state}</span>
    <p>{badge.detail}</p>
  </li>)}</ul>;
}

export function LinksSection({ run, others }: { run: LinksRun | undefined; others: string[] }) {
  if (!run) return <section className="learning-section"><span className="eyebrow">02 / Measured links</span><h2>Measured links.</h2>
    <Empty>No link measurement is recorded. Nothing about sweet taste, odor drive or the reinforcer is claimed here until a run exists.</Empty></section>;
  const rows = Object.entries(run.links || {});
  const odor = run.odor_code || {};
  return <section className="learning-section"><span className="eyebrow">02 / Measured links</span>
    <h2>What the circuit does before any learning.</h2>
    <p className="learning-lede">Plasticity off. Each row is one recorded probe call on the MaleCNS circuit with the three declared interventions. A check that reads fail is a measured absence, not a missing number.</p>
    <ul className="learning-meta"><li><b>Identity</b> {run.identity}</li><li><b>Status</b> {words(run.status)}</li>
      <li><b>Manifest</b> {run.valid ? 'valid' : 'invalid'}</li>{others.length ? <li><b>Other link runs</b> {others.join(', ')}</li> : null}</ul>
    <ul className="learning-chips">{Object.entries(run.checks || {}).map(([name, value]) => <Flag key={name} name={name} value={value}/>)}</ul>
    {rows.length ? <div className="table-wrap"><table>
      <caption>Recorded spike counts per probe call</caption>
      <thead><tr><th scope="col">Probe</th><th scope="col">Total spikes</th><th scope="col">KC active</th><th scope="col">Tail spikes</th><th scope="col">Dopamine spikes by type</th><th scope="col">MBON spikes by type</th><th scope="col">Drive events</th></tr></thead>
      <tbody>{rows.map(([name, value]) => <tr key={name}>
        <th scope="row">{readable(name)}</th><td>{num(value.total_spikes)}</td><td>{num(value.kc_active)}</td><td>{num(value.tail_spikes)}</td>
        <td>{spikeMap(value.dan_spikes_by_type)}</td><td>{spikeMap(value.mbon_spikes_by_type)}</td><td>{value.drive_events == null ? 'none' : num(value.drive_events)}</td>
      </tr>)}</tbody></table></div> : <Empty>This run recorded no individual probe calls.</Empty>}
    <div className="learning-card"><div className="learning-card-head"><h3>Odor code calibration</h3></div>
      <dl className="learning-keyvalue">
        <div><dt>Types per cue key / requested rate</dt><dd>{num(odor.width)} of 53 ORN types at {decimalOrMissing(odor.hz, 1)} Hz</dd></div>
        <div><dt>Cue keys measured</dt><dd>{num(odor.keys)}</dd></div>
        <div><dt>KC active min / median / max</dt><dd>{triple(odor.kc_active_min_median_max)}</dd></div>
        <div><dt>MBON05 spikes min / median / max</dt><dd>{triple(odor.mbon05_min_median_max)}</dd></div>
        <div><dt>Cue keys with no MBON05 response</dt><dd>{odor.mbon05_silent_keys ? (odor.mbon05_silent_keys.length ? odor.mbon05_silent_keys.join(', ') : 'none') : 'Unavailable'}</dd></div>
        <div><dt>Reward dopamine spikes summed over cue trials</dt><dd>{num(odor.reward_dan_spikes_total)}</dd></div>
        <div><dt>Pairwise KC-set Jaccard mean / max</dt><dd>{decimalOrMissing(odor.jaccard_mean, 3)} / {decimalOrMissing(odor.jaccard_max, 3)}</dd></div>
        <div><dt>Largest recovery tail</dt><dd>{num(odor.tail_max)}</dd></div>
      </dl></div>
  </section>;
}

export function ConditioningCard({ run }: { run: ConditioningRun }) {
  const verdict = conditioningVerdict(run);
  const acquisition = run.acquisition || {};
  const arms = Object.entries(acquisition.arms || {});
  const summary = run.summary || {};
  return <article className="learning-card">
    <div className="learning-card-head"><h3>{run.identity}</h3><span className={`learning-verdict learning-${verdict.verdict}`}>{verdict.label}</span></div>
    <ul className="learning-meta">
      <li><b>Recorded status</b> {words(run.status, 'not recorded')}</li>
      <li><b>Native calls</b> {num(run.calls)}</li>
      <li><b>Wall time</b> {seconds(run.wall_seconds)}</li>
      <li><b>Entry gate</b> {run.entry_gate_passed === true ? 'passed' : run.entry_gate_passed === false ? 'failed' : 'not recorded'}</li>
      <li><b>Response readout</b> {words(acquisition.readout, 'not recorded')}</li>
      <li><b>Null arms</b> {acquisition.null_arms?.length ? acquisition.null_arms.join(', ') : 'not recorded'}</li>
    </ul>
    {run.error ? <ErrorBlock message={run.error}/> : null}
    <ul className="learning-chips">
      <Flag name="acquisition" value={summary.acquisition_passed}/>
      <Flag name="retention" value={summary.retention_passed}/>
      <Flag name="reversal" value={summary.reversal_passed}/>
      <Flag name="audit" value={summary.audit_passed}/>
    </ul>
    <h4 className="learning-verdict-line">Acquisition criteria</h4>
    {acquisition.criteria
      ? <ul className="learning-chips">{Object.entries(acquisition.criteria).map(([name, value]) => <Flag key={name} name={name} value={value}/>)}</ul>
      : <Empty>No acquisition criteria were recorded for this run.</Empty>}
    {arms.length ? <div className="table-wrap"><table>
      <caption>Endpoint probes and eligible-edge gain changes per arm. Contrast is cue A minus cue B relative to the unit-gain probes; negative means cue A is depressed.</caption>
      <thead><tr><th scope="col">Arm</th><th scope="col">What it does</th><th scope="col">Contrast per seed</th><th scope="col">Mean contrast</th><th scope="col">A-edge mean Δgain</th><th scope="col">B-edge mean Δgain</th><th scope="col">Changed edges</th><th scope="col">Max |Δgain|</th><th scope="col">Gains identical to unit</th></tr></thead>
      <tbody>{arms.map(([name, arm]) => <tr key={name}>
        <th scope="row">{name}</th><td>{ARM_CAPTIONS[name] || 'not described in the protocol'}</td>
        <td>{contrastList(arm.contrast)}</td><td>{signed(arm.mean_contrast, 2)}</td>
        <td>{signed(arm.a_edge_mean_gain_change, 4)}</td><td>{signed(arm.b_edge_mean_gain_change, 4)}</td>
        <td>{num(arm.changed_edges)}</td><td>{decimalOrMissing(arm.max_abs_gain_change, 4)}</td>
        <td>{arm.bytes_identical_to_unit === true ? 'yes' : arm.bytes_identical_to_unit === false ? 'no' : 'not recorded'}</td>
      </tr>)}</tbody></table></div> : <Empty>No arm measurements were recorded for this run.</Empty>}
    <p className="learning-note">Null response scale {decimalOrMissing(acquisition.null_response_scale, 3)} · null gain scale {decimalOrMissing(acquisition.null_gain_scale, 4)}.
      Retention {run.retention?.passed === true ? 'passed' : run.retention?.passed === false ? 'failed' : 'not recorded'}.
      Reversal {run.reversal?.all_passed === true ? 'passed' : run.reversal?.all_passed === false ? 'failed' : 'not recorded'}.</p>
    {run.reversal?.criteria ? <ul className="learning-chips">{Object.entries(run.reversal.criteria).map(([name, value]) => <Flag key={name} name={name} value={value}/>)}</ul> : null}
    {auditEntries(run.audit).length ? <ul className="learning-meta">{auditEntries(run.audit).map(([name, value]) => <li key={name}><b>{readable(name)}</b> {value}</li>)}</ul> : null}
    {run.odors?.A?.length || run.odors?.B?.length ? <details><summary>Cue odor identities and probe count</summary>
      <p className="learning-note">Cue A: {run.odors?.A?.join(', ') || 'not recorded'}</p>
      <p className="learning-note">Cue B: {run.odors?.B?.join(', ') || 'not recorded'}</p>
      <p className="learning-note">{num(Object.keys(run.probes || {}).length)} endpoint probe records stored with this run.</p>
    </details> : null}
  </article>;
}

export function ConditioningSection({ runs }: { runs: ConditioningRun[] }) {
  return <section className="learning-section"><span className="eyebrow">03 / Controlled conditioning</span>
    <h2>Does the rule learn a cue, and only from pairing?</h2>
    <p className="learning-lede">Each run is a predeclared set of arms from unit gains. A run that failed its criteria stays failed here.</p>
    <ul className="learning-legend">{Object.entries(ARM_CAPTIONS).map(([name, caption]) => <li key={name}><b>{name}</b> = {caption}</li>)}</ul>
    {runs.length ? newestFirst(runs).map(run => <ConditioningCard key={run.identity} run={run}/>)
      : <Empty>No conditioning run is recorded. The learning rule is implemented but nothing about acquisition, retention or reversal is demonstrated.</Empty>}
  </section>;
}

/** Chart geometry in SVG user units. The stylesheet pins the rendered width at or above
 *  CHART.width inside a scrolling wrapper, so the scale is never below 1 and no label
 *  drops under the 11px legibility floor. */
const CHART = { width: 560, height: 128, left: 46, right: 16, top: 12, bottom: 36 };
const PLOT_WIDTH = CHART.width - CHART.left - CHART.right;
const PLOT_HEIGHT = CHART.height - CHART.top - CHART.bottom;

/** Lower-bound occupancy over the recorded probe labels. The vertical scale is fixed at 0 to 1,
 *  so an empty or partial history can never rescale the picture into looking like a result. */
export function OccupancyChart({ run }: { run: StressRun }) {
  const points = occupancyPoints(run);
  const drawn = COMPARTMENTS.map(compartment => ({
    ...compartment,
    marks: points.map((point, index) => ({ index, value: point.values[compartment.key] }))
      .filter((mark): mark is { index: number; value: number } => mark.value != null),
  })).filter(series => series.marks.length > 0);
  if (!drawn.length) return <Empty>No occupancy history is recorded for this run, so no trace is drawn.</Empty>;
  const round = (value: number) => Math.round(value * 1000) / 1000;
  const x = (index: number) => round(points.length < 2 ? CHART.left + PLOT_WIDTH / 2 : CHART.left + (index * PLOT_WIDTH) / (points.length - 1));
  const y = (value: number) => round(CHART.top + (1 - value) * PLOT_HEIGHT);
  const step = Math.max(1, Math.ceil(points.length / 6));
  // React 19 treats a nested <title> as hoistable document metadata and drops its text, so the
  // accessible name is carried by aria-label; <desc> is not hoisted and repeats it for AT that reads it.
  const label = `Fraction of eligible Kenyon-cell synapses at the lower gain bound, for γ4 · MBON05 and γ5 · MBON01, across ${points.length} recorded probe points of run ${run.identity}.`;
  return <>
    <div className="learning-chart-wrap">
      <svg className="learning-chart" viewBox={`0 0 ${CHART.width} ${CHART.height}`} role="img" aria-label={label}>
        <desc>{label}</desc>
        {[0, 0.5, 1].map(level => <g key={level}>
          <line className="learning-grid" x1={CHART.left} x2={CHART.left + PLOT_WIDTH} y1={y(level)} y2={y(level)}/>
          <text x={CHART.left - 8} y={y(level)} textAnchor="end" dominantBaseline="middle">{`${level * 100}%`}</text>
        </g>)}
        <line className="learning-axis" x1={CHART.left} x2={CHART.left} y1={CHART.top} y2={CHART.top + PLOT_HEIGHT}/>
        {points.map((point, index) => (index % step === 0 || index === points.length - 1)
          ? <text key={`${point.label}-${index}`} x={x(index)} y={CHART.top + PLOT_HEIGHT + 18}
              textAnchor={index === 0 ? 'start' : index === points.length - 1 ? 'end' : 'middle'}>{point.label}</text>
          : null)}
        {drawn.map(series => <g key={series.key}>
          <polyline fill="none" stroke={series.color} strokeWidth={2.5} strokeLinejoin="round" strokeLinecap="round"
            strokeDasharray={series.key === '1' ? '7 4' : undefined}
            points={series.marks.map(mark => `${x(mark.index)},${y(mark.value)}`).join(' ')}/>
          {series.marks.map(mark => series.key === '1'
            ? <rect key={mark.index} x={x(mark.index) - 2.6} y={y(mark.value) - 2.6} width={5.2} height={5.2} fill={series.color}/>
            : <circle key={mark.index} cx={x(mark.index)} cy={y(mark.value)} r={3} fill={series.color}/>)}
        </g>)}
      </svg>
    </div>
    <ul className="learning-chart-legend">
      {drawn.map(series => <li key={series.key}><i style={{ background: series.color }}/>{series.label}</li>)}
      <li>Vertical axis: share of eligible synapses at the lower gain bound. Horizontal axis: recorded probe point.</li>
    </ul>
  </>;
}

export function StressCard({ run }: { run: StressRun }) {
  const failed = run.status === 'failed' || Boolean(run.error);
  const history = run.post_history;
  // One pill per card head, the same shape the rest of the page uses, carrying only the
  // recorded state. The arm is descriptive and lives in the meta list, never in this slot.
  const state = failed ? 'Failed' : !run.valid ? 'Invalid manifest' : words(run.status, 'No status recorded');
  const chip = (title: string, value: boolean | null | undefined) => <li>
    <Chip verdict={value === true ? 'yes' : value === false ? 'no' : 'unknown'}>
      {title} · {value === true ? 'pass' : value === false ? 'fail' : 'not recorded'}
    </Chip></li>;
  return <article className="learning-card">
    <div className="learning-card-head"><h3>{run.identity}</h3>
      <span className={`learning-verdict learning-${failed || !run.valid ? 'no' : 'unknown'}`}>{state}</span></div>
    <ul className="learning-meta">
      <li><b>Arm</b> {armLabel(run.arm)}</li>
      <li><b>Recovery strength ρ</b> {rhoText(run.arm, run.rho)}</li>
      <li><b>Recorded status</b> {words(run.status, 'not recorded')}</li>
      <li><b>Manifest</b> {run.valid ? 'valid' : 'invalid'}</li>
      <li><b>Native calls</b> {num(run.calls)}</li>
      <li><b>Wall time</b> {seconds(run.wall_seconds)}</li>
    </ul>
    {run.error ? <ErrorBlock message={run.error}/> : null}
    <dl className="learning-keyvalue">
      {COMPARTMENTS.map(compartment => <div key={compartment.key}>
        <dt>{compartment.label} — synapses at the lower bound at the end</dt>
        <dd>{percentOrMissing(run.lower_bound_occupancy?.[compartment.key])}</dd>
      </div>)}
      {COMPARTMENTS.map(compartment => <div key={`above-${compartment.key}`}>
        <dt>{compartment.label} — synapses above their resting gain</dt>
        <dd>{percentOrMissing(run.above_rest?.[compartment.key])}</dd>
      </div>)}
      <div><dt>Total recovery applied</dt><dd>{decimalOrMissing(run.total_recovery, 4)}</dd></div>
      <div><dt>Total bound contacts</dt><dd>{num(run.total_bound_contacts)}</dd></div>
    </dl>
    <ul className="learning-chips">
      {chip('Post-history acquisition', history?.acquisition_passed)}
      {chip('Reversal flipped', history?.reversal_flipped)}
    </ul>
    <OccupancyChart run={run}/>
  </article>;
}

export function StressSection({ runs }: { runs: StressRun[] }) {
  return <section className="learning-section"><span className="eyebrow">04 / Continual learning</span>
    <h2>Continual learning: dopamine-gated recovery</h2>
    <p className="learning-lede">baseline = the qualified version-1 rule; recovery = the version-2 rule in which dopamine
      arriving without a Kenyon cell&apos;s activity moves that cell&apos;s depressed synapses back toward their resting gain
      (Jiang &amp; Litwin-Kumar 2021, Eq. 5). The recovery strength ρ is chosen from these mechanistic measurements only,
      never from baseball scores.</p>
    {runs.length ? runs.map(run => <StressCard key={run.identity} run={run}/>)
      : <Empty>No continual-learning runs recorded.</Empty>}
  </section>;
}

export function EvaluationCard({ evaluation }: { evaluation: SportsEvaluation }) {
  const metrics = Object.entries(evaluation.metrics || {});
  const paired = Object.entries(evaluation.paired_loss || {});
  const contributes = evaluation.plasticity_contributes;
  const goal = evaluation.goal_passed;
  return <article className="learning-card">
    <div className="learning-card-head"><h3>{evaluation.identity}</h3>
      <span className={`learning-verdict learning-${evaluation.valid ? 'yes' : 'no'}`}>{evaluation.valid ? 'Manifest valid' : 'Manifest invalid'}</span></div>
    <ul className="learning-meta">
      <li><b>Season</b> {num(evaluation.season)}</li><li><b>Readout split</b> {words(evaluation.readout_split, 'not recorded')}</li>
      <li><b>Readout-fit games</b> {num(evaluation.training_games)}</li><li><b>Evaluated games</b> {num(evaluation.evaluation_games)}</li>
      <li><b>Arms</b> {Object.entries(evaluation.arms || {}).map(([arm, identity]) => `${arm}: ${identity}`).join(' · ') || 'not recorded'}</li>
    </ul>
    {metrics.length ? <div className="table-wrap"><table>
      <caption>Held-out metrics, identical games for every method</caption>
      <thead><tr><th scope="col">Method</th><th scope="col">Games</th><th scope="col">Accuracy</th><th scope="col">Log loss ↓</th><th scope="col">Brier ↓</th></tr></thead>
      <tbody>{metrics.map(([method, metric]) => <tr key={method}>
        <th scope="row">{readable(method)}</th><td>{num(metric.n)}</td><td>{percentOrMissing(metric.accuracy)}</td>
        <td>{decimalOrMissing(metric.log_loss)}</td><td>{decimalOrMissing(metric.brier)}</td></tr>)}</tbody></table></div>
      : <Empty>No metrics were recorded for this evaluation.</Empty>}
    {paired.length ? <div className="table-wrap"><table>
      <caption>Paired log-loss differences as the API records them: the plastic pipeline minus the comparator, so a negative value and an interval wholly below zero favour the plastic arm.</caption>
      <thead><tr><th scope="col">Comparator</th><th scope="col">Plastic minus comparator</th><th scope="col">95% paired interval</th></tr></thead>
      <tbody>{paired.map(([method, value]) => <tr key={method}>
        <th scope="row">{readable(method)}</th><td>{signed(value.mean, 4)}</td><td>{interval(value.interval)}</td></tr>)}
        {evaluation.shuffled_minus_frozen ? <tr><th scope="row">shuffled minus frozen</th>
          <td>{signed(evaluation.shuffled_minus_frozen.mean, 4)}</td><td>{interval(evaluation.shuffled_minus_frozen.interval)}</td></tr> : null}
      </tbody></table></div> : <Empty>No paired loss intervals were recorded for this evaluation.</Empty>}
    <p className="learning-note">Accuracy interval: {percentInterval(evaluation.accuracy_interval)}.
      {evaluation.predictions_csv ? ` Per-game predictions: ${evaluation.predictions_csv}.` : ' No per-game prediction file is recorded.'}</p>
    <p className="learning-verdict-line">Plasticity contributes: {contributes === true ? 'yes' : contributes === false ? 'no' : 'not recorded'}</p>
    <p className="learning-verdict-line">Better than chance: {goal === true ? 'yes' : goal === false ? 'no' : 'not recorded'}</p>
  </article>;
}

export function SportsSection({ sports, evaluations }: { sports: SportsRun[]; evaluations: SportsEvaluation[] }) {
  return <section className="learning-section"><span className="eyebrow">05 / Season backtests</span>
    <h2>Does plasticity change a held-out prediction?</h2>
    <p className="learning-lede">Each arm walks one season forward, presenting the winner's odor with the reinforcer after the result is available. Prediction probes run with plasticity off and never consume outcomes.</p>
    {sports.length ? <div className="table-wrap"><table>
      <caption>Recorded season arms</caption>
      <thead><tr><th scope="col">Identity</th><th scope="col">Arm</th><th scope="col">Learning rate</th><th scope="col">Season</th><th scope="col">Games</th><th scope="col">Status</th><th scope="col">Days</th><th scope="col">Calls</th><th scope="col">Reinforcements</th><th scope="col">Checkpoints</th></tr></thead>
      <tbody>{newestFirst(sports).map(run => <tr key={run.identity}>
        <th scope="row">{run.identity}</th><td>{words(run.arm, 'not recorded')}</td><td>{rate(run.learning_rate)}</td>
        <td>{num(run.season)}</td><td>{num(run.games)}</td><td>{words(run.status, 'not recorded')}</td>
        <td>{num(run.days)}</td><td>{num(run.calls)}</td><td>{num(run.reinforcements)}</td><td>{num(run.checkpoints?.length)}</td>
      </tr>)}</tbody></table></div>
      : <Empty>No season arm is recorded. No sports claim of any kind follows from this stage yet.</Empty>}
    {newestFirst(sports).filter(run => run.error).map(run => <ErrorBlock key={run.identity} message={`${run.identity}: ${run.error}`}/>)}
    {evaluations.length ? newestFirst(evaluations).map(evaluation => <EvaluationCard key={evaluation.identity} evaluation={evaluation}/>)
      : <Empty>No evaluation is recorded. Plasticity is not shown to improve held-out prediction, and no better-than-chance claim is made for any learned arm.</Empty>}
  </section>;
}

export function JobsSection(props: {
  jobs: Job[]; running: string | null; loadError: string; startError: string; cancelError: string;
  pending: boolean; form: StartJobForm; onChange: (form: StartJobForm) => void;
  onStart: () => void; onCancel: (id: string) => void;
}) {
  const { jobs, running, loadError, startError, cancelError, pending, form, onChange, onStart, onCancel } = props;
  return <section className="learning-section"><span className="eyebrow">06 / Training jobs</span>
    <h2>Run an arm.</h2>
    <p className="learning-lede">One job runs at a time. Progress, cancellation and resume come from the job registry on disk; a read-only verification server refuses to start anything and its refusal is shown below exactly as sent.</p>
    {loadError ? <ErrorBlock message={loadError}/> : null}
    <p className="learning-note">Currently running: {running || 'none'}. Updates are requested every five seconds only while a job is queued or running.</p>
    {jobs.length ? <div className="table-wrap"><table>
      <caption>Recorded training jobs, newest first</caption>
      <thead><tr><th scope="col">Job</th><th scope="col">Arm</th><th scope="col">Learning rate</th><th scope="col">Status</th><th scope="col">Days</th><th scope="col">Calls</th><th scope="col">Reinforcements</th><th scope="col">Last day</th><th scope="col">Gains</th><th scope="col">Action</th></tr></thead>
      <tbody>{jobs.map(job => <tr key={job.id}>
        <th scope="row">{job.id}</th><td>{words(job.arm, 'not recorded')}</td><td>{rate(job.learning_rate)}</td>
        <td>{words(job.status, 'not recorded')}</td><td>{num(job.progress?.days)}</td><td>{num(job.progress?.calls)}</td>
        <td>{num(job.progress?.reinforcements)}</td><td>{words(job.progress?.last_day, 'not recorded')}</td>
        <td>{shortHash(job.progress?.gains_sha256)}</td>
        <td>{job.status === 'running' || job.status === 'queued'
          ? <button type="button" className="learning-cancel" onClick={() => onCancel(job.id)}>Cancel</button>
          : '—'}</td>
      </tr>)}</tbody></table></div>
      : <Empty>No training job has been recorded on this installation.</Empty>}
    {jobs.filter(job => job.error).map(job => <ErrorBlock key={job.id} message={`${job.id}: ${job.error}`}/>)}
    {cancelError ? <ErrorBlock message={cancelError}/> : null}
    <form className="learning-form" onSubmit={event => { event.preventDefault(); onStart(); }}>
      <label>Protocol<input value={form.protocol} onChange={event => onChange({ ...form, protocol: event.target.value })}/></label>
      <label>Arm<select value={form.arm} onChange={event => onChange({ ...form, arm: event.target.value })}>
        {JOB_ARMS.map(arm => <option key={arm} value={arm}>{arm}</option>)}</select></label>
      <label>Learning rate<input type="number" step="any" min="0" value={form.learning_rate} onChange={event => onChange({ ...form, learning_rate: event.target.value })}/></label>
      <label>Day limit (optional)<input type="number" step="1" min="1" value={form.day_limit} onChange={event => onChange({ ...form, day_limit: event.target.value })}/></label>
      <div className="learning-submit"><button type="submit" disabled={pending}>{pending ? 'Starting…' : 'Start training job'}</button></div>
    </form>
    {startError ? <ErrorBlock message={startError}/> : null}
  </section>;
}

export function ProbeSection(props: {
  checkpoints: Checkpoint[]; loadError: string; loading: boolean; error: string; pending: boolean;
  result: Prediction | null; form: ProbeForm; onChange: (form: ProbeForm) => void; onSubmit: () => void;
}) {
  const { checkpoints, loadError, loading, error, pending, result, form, onChange, onSubmit } = props;
  const side = (label: string, value: Prediction['home']) => <div className="learning-card">
    <div className="learning-card-head"><h3>{label}</h3></div>
    <dl className="learning-keyvalue">
      <div><dt>Team key</dt><dd>{words(value?.team)}</dd></div>
      <div><dt>MBON05 cue-window spikes</dt><dd>{num(value?.response?.[0])}</dd></div>
      <div><dt>MBON01 cue-window spikes</dt><dd>{num(value?.response?.[1])}</dd></div>
      <div><dt>Recovery tail spikes</dt><dd>{num(value?.tail_spikes)}</dd></div>
      <div><dt>Odor types</dt><dd>{value?.odor_types?.length ? `${num(value.odor_types.length)} ORN types` : 'Unavailable'}</dd></div>
    </dl>
    {value?.odor_types?.length ? <details><summary>Odor type list</summary><p className="learning-note">{value.odor_types.join(', ')}</p></details> : null}
  </div>;
  return <section className="learning-section"><span className="eyebrow">07 / Probe a checkpoint</span>
    <h2>Read one immutable checkpoint.</h2>
    <p className="learning-lede">Presents each team's odor alone against stored gains. This is an inspection of learned weights, not a product prediction and not a probability.</p>
    {loadError ? <ErrorBlock message={loadError}/> : null}
    {loading && !checkpoints.length && !loadError ? <p className="learning-note">Loading checkpoints…</p> : null}
    {!loading && !checkpoints.length && !loadError ? <Empty>No checkpoint file exists on this installation, so nothing can be probed.</Empty> : null}
    <form className="learning-form" onSubmit={event => { event.preventDefault(); onSubmit(); }}>
      <label>Checkpoint<select value={form.checkpoint} onChange={event => onChange({ ...form, checkpoint: event.target.value })}>
        <option value="">Select a checkpoint</option>
        {checkpoints.map(item => <option key={item.path} value={item.path}>{item.run} / {item.name}</option>)}</select></label>
      <label>Home team key<input value={form.home} onChange={event => onChange({ ...form, home: event.target.value })}/></label>
      <label>Away team key<input value={form.away} onChange={event => onChange({ ...form, away: event.target.value })}/></label>
      <div className="learning-submit"><button type="submit" disabled={pending || !form.checkpoint}>{pending ? 'Running probe…' : 'Probe checkpoint'}</button></div>
    </form>
    {error ? <ErrorBlock message={error}/> : null}
    {result ? <>
      <div className="learning-pair">{side('Home', result.home)}{side('Away', result.away)}</div>
      <dl className="learning-keyvalue">
        <div><dt>Checkpoint</dt><dd>{words(result.checkpoint)}</dd></div>
        <div><dt>Gains SHA-256</dt><dd>{shortHash(result.gains_sha256)}</dd></div>
        <div><dt>Learned difference, MBON05</dt><dd>{signed(result.learned_differences?.[0], 4)}</dd></div>
        <div><dt>Learned difference, MBON01</dt><dd>{signed(result.learned_differences?.[1], 4)}</dd></div>
        <div><dt>Plasticity during this probe</dt><dd>{result.plasticity === false ? 'false — weights were not updated' : String(result.plasticity)}</dd></div>
        <div><dt>Outcomes consumed</dt><dd>{result.outcomes_consumed === false ? 'false — no game result was read' : String(result.outcomes_consumed)}</dd></div>
        <div><dt>Home win probability</dt><dd>{result.probability_home == null ? 'Not returned' : percentOrMissing(result.probability_home)}</dd></div>
      </dl>
      {result.note ? <p className="learning-note">{result.note}</p> : null}
    </> : null}
  </section>;
}

export default function LearningView() {
  const evidenceResource = useResource<AssociativeEvidence>('/api/associative/evidence');
  const checkpointResource = useResource<CheckpointsPayload>('/api/associative/checkpoints');
  const [jobs, setJobs] = useState<JobsPayload | null>(null);
  const [jobsError, setJobsError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [jobForm, setJobForm] = useState<StartJobForm>(DEFAULT_JOB_FORM);
  const [startError, setStartError] = useState('');
  const [cancelError, setCancelError] = useState('');
  const [startPending, setStartPending] = useState(false);
  const [probeForm, setProbeForm] = useState<ProbeForm>(DEFAULT_PROBE_FORM);
  const [probeError, setProbeError] = useState('');
  const [probePending, setProbePending] = useState(false);
  const [prediction, setPrediction] = useState<Prediction | null>(null);

  useEffect(() => pollJobs(setJobs, setJobsError), [refresh]);

  const evidence = evidenceResource.error ? null : evidenceResource.data;
  const onStart = async () => {
    setStartPending(true); setStartError('');
    try { await startJob(jobForm); setRefresh(value => value + 1); }
    catch (error) { setStartError(errorText(error, 'Starting the job failed.')); }
    finally { setStartPending(false); }
  };
  const onCancel = async (id: string) => {
    setCancelError('');
    try { await cancelJob(id); setRefresh(value => value + 1); }
    catch (error) { setCancelError(errorText(error, 'Cancelling the job failed.')); }
  };
  const onProbe = async () => {
    setProbePending(true); setProbeError(''); setPrediction(null);
    try { setPrediction(await probeCheckpoint(probeForm)); }
    catch (error) { setProbeError(errorText(error, 'The checkpoint probe failed.')); }
    finally { setProbePending(false); }
  };

  return <div className="learning-page">
    <section className="page-heading"><span className="eyebrow">01 / Stage</span>
      <h1>Stage: dopamine-dependent learning on the MaleCNS circuit</h1>
      <p className="lede">Dopamine after a cue depresses that cue's Kenyon-cell synapses onto the γ4 and γ5 output neurons. Everything below is read from recorded manifests. Four separate claims are tracked separately, and a failure stays a failure.</p>
    </section>
    {evidenceResource.error ? <ErrorBlock message={`${evidenceResource.error} No learning evidence is shown until this read succeeds.`}/> : null}
    {!evidenceResource.error && !evidenceResource.data ? <p className="learning-note">Loading recorded learning evidence…</p> : null}
    <LearningBadges evidence={evidence}/>
    {evidence?.note ? <p className="learning-note">{evidence.note}</p> : null}
    <LinksSection run={evidence?.links?.[0]} others={(evidence?.links || []).slice(1).map(item => item.identity)}/>
    <ConditioningSection runs={evidence?.conditioning || []}/>
    <StressSection runs={evidence?.stress || []}/>
    <SportsSection sports={evidence?.sports || []} evaluations={evidence?.evaluations || []}/>
    <JobsSection jobs={jobs?.jobs || []} running={jobs?.running || null} loadError={jobsError} startError={startError}
      cancelError={cancelError} pending={startPending} form={jobForm}
      onChange={next => { setJobForm(next); setStartError(''); setCancelError(''); }} onStart={onStart} onCancel={onCancel}/>
    <ProbeSection checkpoints={checkpointResource.data?.checkpoints || []} loadError={checkpointResource.error}
      loading={checkpointResource.loading} error={probeError} pending={probePending} result={prediction}
      form={probeForm} onChange={next => { setProbeForm(next); setProbeError(''); }} onSubmit={onProbe}/>
    <aside className="scope-note"><strong>What this stage does not claim</strong>
      <p>The reinforcer is an engineered drive of the sugar-reward dopamine populations; the natural sweet-taste pathway does not transmit in this circuit. Qualified conditioning demonstrates the rule in this simulator. It does not establish neural sports value, feeding behaviour, in-circuit choice or any change to the frozen 2023 sensory confirmation.</p>
    </aside>
  </div>;
}
