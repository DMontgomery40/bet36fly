import RewardEvidence from './RewardEvidence';
import Curve from './Curve';
import { controlRows } from './controls';
import { date, decimal, number, percent } from './data';
import type { Progress, Training } from './types';
export function TrainingProgress({ progress }: { progress?: Progress }) {
  if (!progress) return <p className="muted">Training status unavailable.</p>;
  const complete = progress.status === 'complete';
  return <div className="training-progress"><div><strong>{complete ? 'Training complete' : progress.status === 'running' ? 'Training in progress' : progress.status === 'failed' ? 'Training failed' : 'Training not started'}</strong><span>{progress.stage?.replaceAll('_', ' ')}</span></div>{progress.total && progress.total > 0 ? <><progress aria-label="Current training stage" max={progress.total} value={progress.completed || 0}/><span className="mono">{number(progress.completed || 0)} / {number(progress.total)}</span></> : null}{progress.error && <p className="error">{progress.error}</p>}</div>;
}
export default function TrainingView({ data, error, loading }: { data: Training | null; error: string; loading: boolean }) {
  const report = data?.report;
  const controls = controlRows(report?.controls || {});
  return <section className="training-view"><div className="page-heading"><h1>What has it learned?</h1><p>Validation, historical development comparisons, and fresh shadow forecasts.</p></div>
    <RewardEvidence/><h2>Archived v1 training reference · active checkpoint</h2>
    {error && <p role="alert" className="error">{data ? 'Showing last loaded training data. ' : ''}{error}</p>}
    {loading && !data ? <p className="empty">Loading the experiment…</p> : <TrainingProgress progress={data?.progress}/>}
    <div className="training-charts"><Curve curve={report?.curve || data?.progress.curve || []} title={report ? 'Readout learning' : 'Current training stage'}/>{report && <Curve curve={report.plasticity_curve || []} title="Anatomical synapse learning"/>}</div>
    {!report ? <p className="empty">The held-out evaluation will appear once the real training run finishes. There are no results to claim yet.</p> : <>
      <div className="section-heading"><h2>Original v1 test · historical development benchmark</h2><span className="muted">Lower log loss · higher accuracy</span></div><p className="muted">These archived rows use the original v1 test games, which now form the v2 historical development benchmark. When a control has lower log loss than the trained fly network, it performed better on that original comparison.</p>
      {['soccer', 'baseball'].map(sport => <section className="score-section" key={sport}><h3>{sport === 'soccer' ? 'Soccer' : 'Baseball'} <span>{number(report.metrics[sport]?.n)} historical games</span></h3><div className="table-scroll"><table><thead><tr><th scope="col">Model / control</th><th scope="col">Log loss ↓</th><th scope="col">Accuracy ↑</th><th scope="col">Brier ↓</th><th scope="col">ECE ↓</th></tr></thead><tbody>{[['Trained fly network', report.metrics], ...controls.map(({ label, metrics }) => [label, metrics] as const)].map(([label, metrics], index) => { const values = typeof metrics === 'string' ? undefined : metrics[sport]; return <tr className={index === 0 ? 'model-row' : ''} key={String(label)}><th scope="row">{String(label)}</th><td>{decimal(values?.log_loss)}</td><td>{percent(values?.accuracy)}</td><td>{decimal(values?.brier)}</td><td>{decimal(values?.ece)}</td></tr>; })}</tbody></table></div></section>)}
      {controls.filter(control => control.description).map(control => <p className="fine" key={control.key}><strong>{control.label}:</strong> {control.description}</p>)}
      <div className="evidence-grid"><section><h2>Chronological split</h2><div className="table-scroll"><table><thead><tr><th scope="col">Split</th><th scope="col">Soccer</th><th scope="col">Baseball</th><th scope="col">Total</th></tr></thead><tbody>{Object.entries(report.splits).map(([name, split]) => <tr key={name}><th scope="row">{name}</th><td>{number(split.soccer)}</td><td>{number(split.baseball)}</td><td>{number(split.n)}</td></tr>)}</tbody></table></div><p className="fine">Run {report.run_id} · {date(report.created_at)}<br/>Selected readout epoch {number(report.selected_epoch)} · {decimal(report.wall_seconds / 60, 1)} minutes on {report.runtime}</p></section>
      <section><h2>Neural evidence</h2><dl className="evidence">{Object.entries(report.neural_evidence).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{typeof value === 'boolean' ? value ? 'Yes' : 'No' : decimal(value, Math.abs(value) >= 100 ? 0 : 4)}</dd></div>)}</dl><p className="fine">{number(report.plasticity.actual_changed_graph_edges)} actual graph edges changed during learning.</p></section></div>
      <section className="limitations"><h2>What this experiment can’t establish</h2><p>{report.training_method}</p><ul>{report.limitations.map(item => <li key={item}>{item}</li>)}</ul></section>
    </>}
  </section>;
}
