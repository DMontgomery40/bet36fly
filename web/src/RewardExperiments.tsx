import { useEffect, useState } from 'react';
import { date, decimal, number, percent, pollExperiments } from './data';
import type { Experiment, ExperimentIndex, ExperimentJob, RewardCurvePoint } from './types';

export function rewardExperiments(experiments: Experiment[]) {
  return experiments.filter(experiment => experiment.kind === 'dopamine-association');
}

function statusLabel(status?: string) {
  return status ? status.replaceAll('_', ' ').replaceAll('-', ' ') : 'unavailable';
}

function values(items?: number[]) {
  return items?.length ? items.map(item => decimal(item, 4)).join(', ') : '—';
}

function booleanEvidence(value?: boolean) {
  return value === undefined ? 'not recorded' : value ? 'present' : 'absent';
}

function responsiveEvidence(value?: boolean) {
  return value === undefined ? 'not recorded' : value ? 'responsive' : 'not responsive';
}

function hertz(value?: number) {
  return typeof value === 'number' && Number.isFinite(value) ? `${decimal(value, 1)} Hz` : '—';
}

function hertzPair(values?: [number, number]) {
  return values?.length === 2 ? values.map(hertz).join(' / ') : '—';
}

function RewardCurve({ points }: { points: RewardCurvePoint[] }) {
  if (!points.length) return null;
  const width = 640, height = 180, pad = 28;
  const trials = points.map(point => point.trial);
  const gains = points.map(point => point.gain_mean);
  const trialMin = Math.min(...trials), trialMax = Math.max(...trials);
  const gainMin = Math.min(...gains), gainMax = Math.max(...gains);
  const x = (trial: number) => pad + (trialMax === trialMin ? .5 : (trial - trialMin) / (trialMax - trialMin)) * (width - 2 * pad);
  const y = (gain: number) => height - pad - (gainMax === gainMin ? .5 : (gain - gainMin) / (gainMax - gainMin)) * (height - 2 * pad);
  const path = points.map((point, index) => `${index ? 'L' : 'M'} ${x(point.trial).toFixed(2)} ${y(point.gain_mean).toFixed(2)}`).join(' ');
  return <section className="reward-curve" aria-label="Measured learning curve"><h4>Measured trial learning curve</h4>
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Gain mean across measured trials">
      <title>Gain mean across measured trials</title><desc>The mean mutable KC-to-MBON gain at each recorded trial.</desc>
      <line className="grid-line" x1={pad} x2={width - pad} y1={height - pad} y2={height - pad}/>
      <line className="grid-line" x1={pad} x2={pad} y1={pad} y2={height - pad}/>
      <path className="reward-gain-line" d={path}/>
      {points.map(point => <circle key={point.trial} className="reward-gain-point" cx={x(point.trial)} cy={y(point.gain_mean)} r="3"/>)}
      <text x={pad} y={height - 8}>trial {number(trialMin)}</text><text textAnchor="end" x={width - pad} y={height - 8}>trial {number(trialMax)}</text>
      <text x={pad + 5} y={pad + 2}>gain {decimal(gainMax, 4)}</text><text x={pad + 5} y={height - pad - 6}>gain {decimal(gainMin, 4)}</text>
    </svg>
    <details><summary>Learning-curve data</summary><div className="table-scroll"><table><thead><tr><th>Trial</th><th>Mean gain</th><th>DAN spikes</th><th>Home response</th><th>Away response</th></tr></thead><tbody>{points.map(point => <tr key={point.trial}><td>{number(point.trial)}</td><td>{decimal(point.gain_mean, 4)}</td><td>{number(point.dan_spikes)}</td><td>{decimal(point.home_response)}</td><td>{decimal(point.away_response)}</td></tr>)}</tbody></table></div></details>
  </section>;
}

function RewardJobDetail({ experiment, job }: { experiment: Experiment; job: ExperimentJob }) {
  const metric = job.metrics?.validation?.baseball;
  const evidence = job.reward_evidence;
  const compartments = experiment.reward?.anatomy?.compartments ?? [];
  const artifacts = Object.entries(experiment.artifacts).filter(([, artifact]) => artifact.job_id === job.id);
  return <section className="reward-run-detail" aria-label="Selected reward arm details"><div className="section-heading"><h3>{job.variant}</h3><span className="reward-status">{statusLabel(job.status)}</span></div>
    <p className="fine">Seed {job.seed} · {statusLabel(job.phase)}{job.total ? ` · ${number(job.completed ?? 0)} / ${number(job.total)} trials` : ''}{job.wall_seconds !== undefined || job.elapsed_seconds !== undefined ? ` · ${decimal(job.wall_seconds ?? job.elapsed_seconds, 1)} seconds` : ''}</p>
    {job.error && <p role="alert" className="error">{job.error}</p>}
    {job.cancellation_reason && <p className="warning-text">{job.cancellation_reason}</p>}
    {metric ? <dl className="run-metrics"><div><dt>Validation games</dt><dd>{number(metric.n)}</dd></div><div><dt>Log loss</dt><dd>{decimal(metric.log_loss)}</dd></div><div><dt>Brier</dt><dd>{decimal(metric.brier)}</dd></div><div><dt>Accuracy</dt><dd>{percent(metric.accuracy)}</dd></div><div><dt>Calibration error</dt><dd>{decimal(metric.ece)}</dd></div></dl> : <p className="muted">No measured validation scores for this arm yet.</p>}
    {evidence ? <><h4>Measured gain and circuit evidence</h4><dl className="reward-evidence">
      <div><dt>Changed graph edges</dt><dd>{number(evidence.changed_edges)}</dd></div><div><dt>Gain range</dt><dd>{decimal(evidence.gain_min, 4)}–{decimal(evidence.gain_max, 4)}</dd></div><div><dt>Mean gain</dt><dd>{decimal(evidence.gain_mean, 4)}</dd></div><div><dt>At lower bound</dt><dd>{percent(evidence.lower_bound_fraction)}</dd></div><div><dt>At upper bound</dt><dd>{percent(evidence.upper_bound_fraction)}</dd></div>
      <div><dt>KC active fraction</dt><dd>{percent(evidence.kc_active_fraction)}</dd></div><div><dt>DAN spikes</dt><dd>{number(evidence.dan_spikes)}</dd></div><div><dt>MBON mean rate</dt><dd>{evidence.mbon_mean_hz === undefined ? '—' : `${decimal(evidence.mbon_mean_hz, 2)} Hz`}</dd></div><div><dt>Tonic DAN rate (home / away)</dt><dd>{hertzPair(evidence.tonic_dan_hz)}</dd></div>
    </dl>{evidence.dan_compartment_spikes && <div className="table-scroll"><table><caption>Arm-training DAN spikes by compartment</caption><thead><tr><th>Teaching compartment</th><th>DAN type</th><th>Arm-training DAN spikes</th></tr></thead><tbody>{evidence.dan_compartment_spikes.map((spikes, index) => <tr key={index}><th scope="row">{compartments[index]?.label ?? `Compartment ${index + 1}`}</th><td>{compartments[index]?.dan_type ?? '—'}</td><td>{number(spikes)}</td></tr>)}</tbody></table></div>}</> : <p className="muted">Measured gain and circuit evidence has not been recorded for this arm.</p>}
    {job.class_confusion && <div className="table-scroll"><table><caption>Validation class confusion</caption><thead><tr><th>Truth / prediction</th><th>Predicted home</th><th>Predicted away</th></tr></thead><tbody><tr><th scope="row">Home truth</th><td>{number(job.class_confusion[0][0])}</td><td>{number(job.class_confusion[0][1])}</td></tr><tr><th scope="row">Away truth</th><td>{number(job.class_confusion[1][0])}</td><td>{number(job.class_confusion[1][1])}</td></tr></tbody></table></div>}
    <RewardCurve points={job.reward_curve ?? []}/>
    {!!artifacts.length && <div className="artifact-links" aria-label="Reward experiment downloads">{artifacts.map(([id, artifact]) => <a key={id} href={artifact.url} download>{artifact.label}</a>)}</div>}
  </section>;
}

type RewardExperimentsViewProps = {
  data: ExperimentIndex | null;
  error: string;
  selectedExperimentId: string;
  selectedJobId: string;
  onSelectExperiment: (id: string) => void;
  onSelectJob: (id: string) => void;
};

export function RewardExperimentsView({ data, error, selectedExperimentId, selectedJobId, onSelectExperiment, onSelectJob }: RewardExperimentsViewProps) {
  const experiments = rewardExperiments(data?.experiments ?? []);
  const experiment = experiments.find(row => row.id === selectedExperimentId) ?? experiments[experiments.length - 1];
  const selectedJob = experiment?.jobs.find(row => row.id === selectedJobId) ?? experiment?.jobs[0];
  const reward = experiment?.reward;
  const encoder = reward?.anatomy?.encoder;
  const teachingSpikes = reward?.activity_gate?.teaching_compartment_spikes;
  const teachingSpikeTotal = reward?.activity_gate?.dan_spikes ?? teachingSpikes?.reduce((sum, count) => sum + count, 0);
  return <section className="reward-experiments" aria-label="On-circuit reward learning experiments"><div className="section-heading"><div><h2>On-circuit reward learning</h2><p className="muted">A separate trial-based experiment in the measured MaleCNS circuit.</p></div>{experiment && <span className="reward-status">{statusLabel(experiment.status)}</span>}</div>
    <p>This experiment changes only eligible KC-to-MBON graph-edge gains. The readout is fixed before learning. The home/away teaching-cell mapping is engineered and does not reconstruct a biological reward-prediction error.</p>
    <p className="fine">The validation scores reuse development data. Comparisons are descriptive evidence from this bounded protocol and do not establish a bookmaker edge or biological superiority.</p>
    {data && <p><strong>Active model: v1 {data.active_v1?.run_id || 'unavailable'}</strong> · Reward experiments cannot activate a model.</p>}
    {error && <p className="error" role="alert">{data ? 'Showing last loaded reward results. ' : ''}{error}</p>}
    {!data && !error && <p role="status">Loading reward experiment registry…</p>}
    {data && !experiments.length && <p className="empty">No dopamine-association experiment has started.</p>}
    {experiment && <>
      <p className="fine">{experiment.id} · Last update {date(experiment.updated_at)}</p>
      {experiment.error && <p role="alert" className="error">Experiment failure: {experiment.error}</p>}
      {!!Object.values(experiment.artifacts).some(artifact => !artifact.job_id) && <div className="artifact-links" aria-label="Reward experiment downloads">{Object.entries(experiment.artifacts).filter(([, artifact]) => !artifact.job_id).map(([id, artifact]) => <a key={id} href={artifact.url} download>{artifact.label}</a>)}</div>}
      {experiments.length > 1 && <label className="reward-experiment-select">Reward experiment <select value={experiment.id} onChange={event => onSelectExperiment(event.target.value)}>{experiments.map(row => <option key={row.id} value={row.id}>{row.id}</option>)}</select></label>}
      {reward ? <section className="reward-protocol" aria-label="Frozen reward protocol"><h3>Frozen protocol</h3><p>{reward.scope}</p><p><strong>Learning rule:</strong> {reward.rule}</p><p className="fine">{reward.note}</p>
        <dl className="reward-counts"><div><dt>Training trials</dt><dd>{number(reward.train_n)}</dd></div><div><dt>Validation trials</dt><dd>{number(reward.validation_n)}</dd></div><div><dt>Calibration trials</dt><dd>{number(reward.calibration_n)}</dd></div></dl>
        <aside className="reward-assumptions"><h4>Experimental dynamics assumptions</h4><p><strong>Global fast-weight scale:</strong> {decimal(experiment.protocol?.global_weight_scale, 3)}.</p>{encoder && <p><strong>Sensory identity code ({encoder.encoder}):</strong> each of the {number(encoder.features.length)} standardized pregame features drives its own {number(encoder.centers_per_feature)} annotated {encoder.eligible_transmitter} ALPN glomeruli ({number(encoder.glomeruli)} glomeruli; {number(encoder.ports_driven)} of {number(encoder.ports_total)} ALPN ports), each tuned to a preferred value between −{decimal(encoder.center_span, 1)} and {decimal(encoder.center_span, 1)} with Gaussian width {decimal(encoder.tuning_width, 2)} and a {decimal(encoder.peak_hz, 0)} Hz peak, silent below {percent(encoder.floor_fraction)} of peak. Which ports fire therefore depends on the game. Glomeruli with fewer than {number(encoder.min_kc_contacts)} KC contacts are not driven{encoder.dropped_glomeruli.length ? `; ${encoder.dropped_glomeruli.length} surplus glomeruli (${encoder.dropped_glomeruli.join(', ')}) stay undriven` : ''}. This is an engineered interface, not a claim that these glomeruli represent sports quantities.</p>}{reward.anatomy?.kc_input_gain !== undefined && <p><strong>Cell-type input gains:</strong> every synapse ending at a Kenyon cell is scaled by {decimal(reward.anatomy.kc_input_gain, 3)}, an engineered stand-in for the coincidence threshold of real KCs{reward.anatomy.sensory_input_gain !== undefined && <>; every synapse ending at an ALPN port is scaled by {decimal(reward.anatomy.sensory_input_gain, 3)}{reward.anatomy.sensory_input_gain === 0 ? ', so the ports are labeled lines driven only by the scheduled input and the antennal lobe cannot re-excite them' : ''}</>}{reward.anatomy.apl_output_gain !== undefined && <>; every synapse leaving the two annotated GABAergic APL neurons is scaled by {decimal(reward.anatomy.apl_output_gain, 3)}, because real APL inhibition is graded and non-spiking while this spiking proxy would otherwise deliver tens of millivolts per spike onto the readout MBONs</>}.</p>}{experiment.protocol?.plasticity_onset_ms !== undefined && <p><strong>Phasic dopamine drive:</strong> plasticity and its eligibility traces start {decimal(experiment.protocol.plasticity_onset_ms, 0)} ms into each trial; each compartment's tonic DAN rate over the preceding {decimal(experiment.protocol.dan_baseline_window_ms, 0)} ms is subtracted from the DAN signal in both rule terms. This signed baseline subtraction can change gains without teaching, including when activity falls below the reference after stimulus offset. It does not establish cue-specific learning.</p>}{experiment.protocol?.min_teaching_evoked_fraction !== undefined && <p><strong>Declared gate margins:</strong> each teaching population must evoke at least {percent(experiment.protocol.min_teaching_evoked_fraction)} of its scheduled forced spikes above the unpulsed same-seed probe, and the active KC set may overlap at most {percent(experiment.protocol.max_kc_code_overlap)} between calibration games.</p>}<p>All {number(reward.anatomy?.dopamine_only_fast_outputs_zeroed)} pure dopamine neurons have zero direct fast outgoing transmission in this engine; selected DANs act through the modeled modulation channel.</p></aside>
        {reward.anatomy && <><h4>Measured circuit scope</h4><dl className="reward-counts"><div><dt>Retained neurons</dt><dd>{number(reward.anatomy.neurons)}</dd></div><div><dt>Kenyon cells</dt><dd>{number(reward.anatomy.kc)}</dd></div><div><dt>Dopamine neurons</dt><dd>{number(reward.anatomy.dans)}</dd></div><div><dt>Eligible graph edges</dt><dd>{number(reward.anatomy.plastic_edges)}</dd></div></dl>
          {encoder && <details className="reward-encoder-map"><summary>Feature-to-glomerulus map ({number(encoder.glomeruli)} glomeruli)</summary><div className="table-scroll"><table><caption>Engineered feature-to-glomerulus identity code</caption><thead><tr><th>Feature</th><th>Glomeruli (preferred value · cells · KC contacts)</th></tr></thead><tbody>{encoder.features.map(row => <tr key={row.feature}><th scope="row">{number(row.feature + 1)}</th><td>{row.glomeruli.map(g => `${g.type} (${decimal(g.center, 1)} · ${number(g.cells)} · ${number(g.kc_contacts)})`).join('; ')}</td></tr>)}</tbody></table></div></details>}
          {!!reward.anatomy.compartments.length && <div className="table-scroll"><table><caption>Engineered teaching compartments on annotated anatomy</caption><thead><tr><th>Mapping</th><th>DAN type</th><th>MBON type</th><th>DANs</th><th>MBONs</th><th>Plastic edges</th></tr></thead><tbody>{reward.anatomy.compartments.map(row => <tr key={`${row.label}-${row.dan_type}-${row.mbon_type}`}><th scope="row">{row.label}</th><td>{row.dan_type}</td><td>{row.mbon_type}</td><td>{number(row.dans)}</td><td>{number(row.mbons)}</td><td>{number(row.plastic_edges)}</td></tr>)}</tbody></table></div>}</>}
        {reward.fixed_readout && <section className="reward-readout"><h4>Fixed readout</h4><p>{reward.fixed_readout.method}</p><dl><div><dt>Calibration mean</dt><dd>{values(reward.fixed_readout.mean)}</dd></div><div><dt>Calibration scale</dt><dd>{values(reward.fixed_readout.scale)}</dd></div><div><dt>Class prior</dt><dd>{values(reward.fixed_readout.prior)}</dd></div></dl></section>}
        <div className="reward-gates">{reward.activity_gate && <article><h4>Activity gate · {statusLabel(reward.activity_gate.status)}</h4><p>{reward.activity_gate.message}</p><dl><div><dt>KC active fraction</dt><dd>{percent(reward.activity_gate.kc_active_fraction)}</dd></div><div><dt>Teaching-check total DAN spikes</dt><dd>{number(teachingSpikeTotal)}</dd></div><div><dt>Maximum MBON rate</dt><dd>{reward.activity_gate.max_mbon_hz === undefined ? '—' : `${decimal(reward.activity_gate.max_mbon_hz, 2)} Hz`}</dd></div><div><dt>Common-seed input discrimination</dt><dd>{booleanEvidence(reward.activity_gate.input_discrimination)}</dd></div><div><dt>KC set overlap between calibration games</dt><dd>{percent(reward.activity_gate.kc_code_overlap)}</dd></div><div><dt>KCs still firing after stimulus offset</dt><dd>{percent(reward.activity_gate.post_stimulus_kc_active_fraction)}</dd></div></dl><p className="fine">These numerical activity guards do not validate physiological firing density; passing them only clears bounded execution.</p>{reward.activity_gate.teaching_compartment_spikes && <div className="table-scroll"><table><caption>Teaching-check DAN response by compartment</caption><thead><tr><th>Teaching compartment</th><th>DAN type</th><th>Responsive</th><th>Teaching-check DAN spikes</th><th>Tonic rate</th><th>Scheduled forced spikes</th><th>Evoked above tonic</th></tr></thead><tbody>{reward.activity_gate.teaching_compartment_spikes.map((spikes, index) => <tr key={index}><th scope="row">{reward.anatomy?.compartments[index]?.label ?? `Compartment ${index + 1}`}</th><td>{reward.anatomy?.compartments[index]?.dan_type ?? '—'}</td><td>{responsiveEvidence(reward.activity_gate?.teaching_responsive?.[index])}</td><td>{number(spikes)}</td><td>{hertz(reward.activity_gate?.tonic_dan_hz?.[index])}</td><td>{number(reward.activity_gate?.teaching_scheduled_spikes?.[index])}</td><td>{number(reward.activity_gate?.teaching_evoked_spikes?.[index])}</td></tr>)}</tbody></table></div>}</article>}{reward.outcome && <article><h4>Experiment outcome · {statusLabel(reward.outcome.status)}</h4><p>{reward.outcome.message}</p><p className="fine">Paired − frozen log loss {decimal(reward.outcome.paired_minus_frozen_log_loss, 4)} · Paired − shuffled {decimal(reward.outcome.paired_minus_shuffled_log_loss, 4)}</p></article>}</div>
      </section> : <p className="muted">The reward protocol summary has not been recorded.</p>}
      <div className="table-scroll"><table className="reward-arm-table"><caption>Matched reward-learning arms and fixed prior comparator · select an arm to inspect measured evidence</caption><thead><tr><th>Arm / comparator</th><th>Status</th><th>Phase / progress</th><th>Validation games</th><th>Log loss</th><th>Brier</th><th>Accuracy</th><th>Calibration error</th><th>Seconds</th></tr></thead><tbody>{experiment.jobs.map(job => { const metric = job.metrics?.validation?.baseball; return <tr key={job.id} className={job.id === selectedJob?.id ? 'selected-run' : ''}><th scope="row"><button className="text-button" aria-pressed={job.id === selectedJob?.id} onClick={() => onSelectJob(job.id)}>{job.variant}</button></th><td>{statusLabel(job.status)}{job.error && <span className="reward-row-message">{job.error}</span>}{job.cancellation_reason && <span className="reward-row-message">{job.cancellation_reason}</span>}</td><td>{statusLabel(job.phase)}{job.total ? ` · ${number(job.completed ?? 0)} / ${number(job.total)}` : ''}</td><td>{number(metric?.n)}</td><td>{decimal(metric?.log_loss)}</td><td>{decimal(metric?.brier)}</td><td>{percent(metric?.accuracy)}</td><td>{decimal(metric?.ece)}</td><td>{decimal(job.wall_seconds ?? job.elapsed_seconds, 1)}</td></tr>; })}{reward?.prior_metrics && <tr className="reward-comparator"><th scope="row">Fixed class-frequency prior</th><td>comparator</td><td>fixed before evaluation</td><td>{number(reward.prior_metrics.n)}</td><td>{decimal(reward.prior_metrics.log_loss)}</td><td>{decimal(reward.prior_metrics.brier)}</td><td>{percent(reward.prior_metrics.accuracy)}</td><td>{decimal(reward.prior_metrics.ece)}</td><td>—</td></tr>}</tbody></table></div>
      {!experiment.jobs.length && <p className="empty">No matched arm has been registered.</p>}
      {selectedJob && <RewardJobDetail experiment={experiment} job={selectedJob}/>}
    </>}
  </section>;
}

export default function RewardExperiments() {
  const [data, setData] = useState<ExperimentIndex | null>(null);
  const [error, setError] = useState('');
  const [selectedExperimentId, setSelectedExperimentId] = useState('');
  const [selectedJobId, setSelectedJobId] = useState('');
  useEffect(() => pollExperiments(setData, setError), []);
  return <RewardExperimentsView data={data} error={error} selectedExperimentId={selectedExperimentId} selectedJobId={selectedJobId} onSelectExperiment={id => { setSelectedExperimentId(id); setSelectedJobId(''); }} onSelectJob={setSelectedJobId}/>;
}
