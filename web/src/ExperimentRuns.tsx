import { useEffect, useState } from 'react';
import Curve from './Curve';
import { date, decimal, number, percent, pollExperiments } from './data';
import type { Experiment, ExperimentIndex, ExperimentJob, Prospective } from './types';

export function filteredComparisons(experiment: Experiment, sport: string, split: string) {
  if (experiment.comparison?.length) return experiment.comparison.filter(row => row.sport === sport && row.split === split);
  return [...new Set(experiment.jobs.map(job => job.variant))].map(variant => {
    const jobs = experiment.jobs.filter(job => job.variant === variant && job.status === 'complete');
    const seeds = jobs.flatMap(job => job.metrics?.[split]?.[sport] ? [{ ...job.metrics[split][sport], seed: job.seed }] : []);
    return { variant, sport, split, seeds, mean: seeds.length ? {
      log_loss: seeds.reduce((sum, row) => sum + row.log_loss, 0) / seeds.length,
      brier: seeds.reduce((sum, row) => sum + row.brier, 0) / seeds.length,
      accuracy: seeds.reduce((sum, row) => sum + row.accuracy, 0) / seeds.length,
      ece: seeds.reduce((sum, row) => sum + row.ece, 0) / seeds.length,
    } : undefined };
  });
}
export function ProspectivePanel({ data }: { data: Prospective | undefined }) {
  return <section className="prospective-panel" aria-label="Prospective shadow evaluation"><h2>Fresh games: prospective shadow</h2>
    <p>{data?.variant ? `${data.variant} is recording alongside active v1.` : 'The v2 shadow candidate will begin after validation selection.'} V1 remains the active model. Promotion is never automatic.</p>
    {data?.activated_at && <p className="fine">Activated {date(data.activated_at)} · {number(data.forecasts)} saved forecasts</p>}
    {data?.error && <p className="error" role="alert">Shadow capture needs attention: {data.error}</p>}
    <div className="prospective-sports">{['soccer', 'baseball'].map(sport => {
      const row = data?.sports[sport]; return <article key={sport}><h3>{sport}</h3><strong>{number(row?.eligible_completed ?? 0)} / {number(row?.threshold ?? (sport === 'soccer' ? 100 : 1000))}</strong><p>{row?.status === 'frozen' ? 'First cohort frozen' : 'First cohort pending'}</p>{!!row?.cohort_invalidated && <p className="warning-text">{row.cohort_invalidated} frozen cohort rows are currently ineligible. Membership stays fixed; metrics use only currently eligible rows.</p>}{row?.metrics && <p>Shadow log loss {decimal(row.metrics.shadow.log_loss)} · Feature logistic {decimal(row.metrics.feature_logistic.log_loss)}</p>}</article>;
    })}</div><p className="fine">Only valid forecasts saved before the fixture cutoff count. Interim results are descriptive; future results have not been observed.</p>
  </section>;
}
function JobDetail({ job, experiment, sport, split }: { job: ExperimentJob; experiment: Experiment; sport: string; split: string }) {
  const metric = job.metrics?.[split]?.[sport];
  return <section className="run-detail" aria-label="Selected run details"><h3>{job.variant} · seed {job.seed}</h3>
    <p>{job.status} · {job.phase.replaceAll('-', ' ')}{job.selected_plastic_epoch !== undefined ? ` · selected plastic epoch ${job.selected_plastic_epoch}, decoder epoch ${job.selected_decoder_epoch}` : ''}</p>
    {job.cancellation_reason && <p className="warning-text">{job.cancellation_reason}</p>}
    {job.error && <p role="alert" className="error">{job.error}</p>}
    <p>{number(job.gain_parameters)} gains · {number(job.decoder_parameters)} allocated decoder coefficients · {number(job.active_parameters)} total active parameters · {decimal(job.wall_seconds ?? job.elapsed_seconds, 1)} seconds</p>
    {metric ? <dl className="run-metrics"><div><dt>Log loss</dt><dd>{decimal(metric.log_loss)}</dd></div><div><dt>Brier</dt><dd>{decimal(metric.brier)}</dd></div><div><dt>Accuracy</dt><dd>{percent(metric.accuracy)}</dd></div><div><dt>Calibration error</dt><dd>{decimal(metric.ece)}</dd></div></dl> : <p className="muted">No measured metrics for this split yet.</p>}
    {!!job.curve?.length && <><h4>Full simulator decoder</h4><Curve curve={job.curve}/></>}
    {!!job.plasticity_curve?.length && <><h4>Surrogate diagnostic curve</h4><p className="fine">Surrogate scores do not select the installed checkpoint.</p><Curve curve={job.plasticity_curve}/></>}
    {!!job.checkpoints?.length && <div className="table-scroll"><table><caption>Plastic checkpoint comparison on validation</caption><thead><tr><th>Plastic epoch</th><th>Decoder epoch</th><th>Full simulator loss</th><th>Surrogate loss</th><th>Full minus surrogate</th></tr></thead><tbody>{job.checkpoints.map(row => <tr key={row.plastic_epoch}><td>{row.plastic_epoch}</td><td>{row.selected_epoch}</td><td>{decimal(row.validation_loss)}</td><td>{decimal(row.surrogate_validation_loss)}</td><td>{decimal(row.surrogate_full_gap)}</td></tr>)}</tbody></table></div>}
    {job.neural_statistics?.[split] && <details><summary>Measured neural activity and saturation</summary><dl>{Object.entries({ ...job.neural_statistics[split], ...job.gain_statistics }).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{decimal(value, 4)}</dd></div>)}</dl></details>}
    {metric?.calibration && <details><summary>10-bin calibration</summary><div className="table-scroll"><table><thead><tr><th>Lower confidence</th><th>Games</th><th>Mean confidence</th><th>Accuracy</th></tr></thead><tbody>{metric.calibration.map(bin => <tr key={bin.lower}><td>{percent(bin.lower)}</td><td>{number(bin.n)}</td><td>{percent(bin.confidence)}</td><td>{percent(bin.accuracy)}</td></tr>)}</tbody></table></div></details>}
    <div className="artifact-links">{Object.entries(experiment.artifacts).filter(([, artifact]) => artifact.job_id === job.id).map(([id, artifact]) => <a key={id} href={artifact.url} download>{artifact.label}</a>)}</div>
  </section>;
}
export default function ExperimentRuns() {
  const [data, setData] = useState<ExperimentIndex | null>(null);
  const [error, setError] = useState('');
  const [experimentId, setExperimentId] = useState('');
  const [jobId, setJobId] = useState('');
  const [sport, setSport] = useState('soccer');
  const [split, setSplit] = useState('validation');
  useEffect(() => pollExperiments(setData, setError), []);
  const experiment = data?.experiments.find(row => row.id === experimentId) ?? data?.experiments[0];
  const job = experiment?.jobs.find(row => row.id === jobId);
  const comparisons = experiment ? filteredComparisons(experiment, sport, split) : [];
  const paired = experiment?.paired?.comparisons.filter(row => row.sport === sport && row.split === split) || [];
  return <section className="experiment-runs" aria-label="V2 experiment tracker"><h2>Experiment runs</h2>
    <p><strong>Active model: v1 {data?.active_v1?.run_id || 'unavailable'}</strong>{experiment?.selected_shadow && <> · Selected shadow: <strong>{experiment.selected_shadow.variant}</strong></>}</p>
    {error && <p className="error" role="alert">{data ? 'Showing last loaded results. ' : ''}{error}</p>}
    {!data && !error && <p role="status">Loading experiment registry…</p>}
    {data && !data.experiments.length && <p>No v2 experiment has started.</p>}
    {experiment && <><p className="fine">Last update {date(experiment.updated_at)} · {experiment.status}{experiment.completion_scope === 'user-curtailed' ? ' · user-curtailed scope' : ''}</p>
      {!!experiment.execution_amendments?.length && <aside aria-label="Execution amendments" className="warning-text"><strong>{experiment.jobs.filter(row => row.status === 'complete').length} completed · {experiment.jobs.filter(row => row.status === 'cancelled').length} cancelled</strong>{experiment.execution_amendments.map(amendment => <p key={amendment.recorded_at}>{amendment.reason}</p>)}<p>Temporal comparisons have incomplete seed coverage. Stopping followed observed results; uncertainty intervals do not account for that decision. Only architectures with all three completed seeds can be selected.</p></aside>}
      {data && data.experiments.length > 1 && <label>Experiment <select value={experiment.id} onChange={event => { setExperimentId(event.target.value); setJobId(''); }}>{data.experiments.map(row => <option key={row.id}>{row.id}</option>)}</select></label>}
      <div className="table-scroll"><table className="experiment-table"><caption>Original fixed matrix · select a run to inspect measured evidence</caption><thead><tr><th>Variant / seed</th><th>Active parameters</th><th>Status</th><th>Phase / progress</th><th>Seconds</th><th>Validation loss</th></tr></thead><tbody>{experiment.jobs.map(row => <tr key={row.id} className={row.id === jobId ? 'selected-run' : ''}><td><button className="text-button" aria-pressed={row.id === jobId} onClick={() => setJobId(row.id)}>{row.variant} · {row.seed}</button></td><td>{number(row.active_parameters)}</td><td>{row.status}</td><td>{row.phase.replaceAll('-', ' ')}{row.total ? ` · ${number(row.completed)} / ${number(row.total)}` : ''}</td><td>{decimal(row.wall_seconds ?? row.elapsed_seconds, 1)}</td><td>{decimal(row.validation_loss)}</td></tr>)}</tbody></table></div>
      <div className="comparison-filters"><label>Comparison sport <select aria-label="Comparison sport" value={sport} onChange={event => setSport(event.target.value)}><option value="soccer">Soccer</option><option value="baseball">Baseball</option></select></label><label>Evaluation split <select aria-label="Evaluation split" value={split} onChange={event => setSplit(event.target.value)}><option value="validation">Validation · July–December 2025</option><option value="historical">Historical development benchmark · January–August 2026</option></select></label></div>
      {job && <JobDetail job={job} experiment={experiment} sport={sport} split={split}/>}
      <h3>{split === 'historical' ? 'Historical development benchmark' : 'Validation comparison'} · {sport}</h3><p className="fine">Candidate selection uses equal-sport mean validation loss across three seeds. The historical benchmark already informed the design. Lower log loss and Brier are better. Baselines are fitted once; repeated seed IDs pair them with neural runs.</p>
      <div className="table-scroll"><table><thead><tr><th>Model</th><th>Seeds</th><th>Mean log loss</th><th>Brier</th><th>Accuracy</th><th>Calibration error</th></tr></thead><tbody>{comparisons.map(row => <tr key={row.variant}><td>{row.variant}</td><td>{row.seeds.length}</td><td>{decimal(row.mean?.log_loss)}</td><td>{decimal(row.mean?.brier)}</td><td>{percent(row.mean?.accuracy)}</td><td>{decimal(row.mean?.ece)}</td></tr>)}</tbody></table></div>
      {comparisons.some(row => row.seeds.length) && <details><summary>Individual seed measurements</summary>{comparisons.filter(row => row.seeds.length).map(row => <p key={row.variant}><strong>{row.variant}</strong>: {row.seeds.map(seed => `seed ${seed.seed}: log loss ${decimal(seed.log_loss)}, Brier ${decimal(seed.brier)}, accuracy ${percent(seed.accuracy)}`).join(' · ')}</p>)}</details>}
      {!!paired.length && <details open><summary>Paired weekly differences and 95% intervals</summary><p className="fine">{experiment.paired?.limitation}</p><div className="table-scroll"><table><thead><tr><th>Comparison (left minus right)</th><th>Matched seeds</th><th>Log loss difference</th><th>95% interval</th><th>Decision</th></tr></thead><tbody>{paired.map(row => <tr key={row.left + row.right}><td>{row.left} − {row.right}</td><td>{Object.keys(row.seed_differences).join(', ')}</td><td>{decimal(row.difference, 4)}</td><td>[{decimal(row.interval[0], 4)}, {decimal(row.interval[1], 4)}]</td><td>{row.decision}</td></tr>)}</tbody></table></div></details>}
      <div className="artifact-links">{Object.entries(experiment.artifacts).filter(([, artifact]) => !artifact.job_id).map(([id, artifact]) => <a key={id} href={artifact.url} download>{artifact.label}</a>)}</div>
    </>}
    <ProspectivePanel data={data?.prospective}/>
  </section>;
}
