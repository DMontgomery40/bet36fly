import { useEffect, useState } from 'react';
import { useResource } from './data';
import { count, day, fixed, methodNames, methods, pct, route, selectedGame } from './sensoryData';
import type { Summary, SummaryState } from './sensoryTypes';
import Backtest from './SensoryBacktest';
import SensoryMethods, { Pipeline } from './SensoryMethods';
import LearningView from './LearningView';
import CircuitView from './CircuitView';

export function Message({ title, children, retry }: { title: string; children?: React.ReactNode; retry?: () => void }) {
  return <section className="state" role={retry ? 'alert' : 'status'}><span className="eyebrow">Research evidence</span><h1>{title}</h1><p>{children}</p>{retry && <button onClick={retry}>Try again</button>}</section>;
}
function Overview({ data }: { data: Summary }) {
  const e = data.evaluation, metric = e.metrics.neural;
  const [lo, hi] = e.accuracy_interval;
  const position = (p: number) => 65 + (p - .45) / .2 * 560;
  return <>
    <section className="result-hero">
      <div className="hero-copy"><span className="eyebrow"><span className="status-dot"/>2023 MLB · Historical confirmation</span><h1>A small circuit.<br/>A measured result.</h1><p className="lede">A frozen fly-connectome sensory pipeline predicted MLB winners better than chance in its predefined historical backtest.</p><a className="button dark" href="#backtest">Explore every game <span aria-hidden="true">↗</span></a><p className="hero-footnote">Engineered pregame encoder. Real simulated sensory responses. Externally fitted probability readout.</p></div>
      <div className="result-card"><div className="result-top"><span className="eyebrow">Complete pipeline accuracy</span><span className="tag">Confirmed</span></div><div className="big-result">{pct(metric.accuracy).replace('%', '')}<span>%</span></div><p>{count(data.correct)} correct / {count(metric.n)} games</p><div className="interval-caption"><strong>{pct(lo)}–{pct(hi)}</strong><span>95% weekly-block bootstrap interval</span></div><svg className="interval-chart" viewBox="0 0 690 90" role="img" aria-label={`Accuracy ${pct(metric.accuracy)}, 95% interval ${pct(lo)} to ${pct(hi)}, above 50% expected chance`}><line x1="65" y1="33" x2="625" y2="33" stroke="currentColor" opacity=".22"/>{[.45,.50,.55,.60,.65].map(p => <g key={p}><line x1={position(p)} x2={position(p)} y1="29" y2="38" stroke="currentColor" opacity=".35"/><text x={position(p)} y="65" textAnchor="middle">{Math.round(p*100)}%</text></g>)}<line x1={position(.5)} x2={position(.5)} y1="5" y2="44" stroke="#ba5b36" strokeDasharray="4 4"/><line x1={position(lo)} x2={position(hi)} y1="33" y2="33" stroke="#b9d59c" strokeWidth="10" strokeLinecap="round"/><circle cx={position(metric.accuracy)} cy="33" r="8" fill="#fbf9f1"/></svg><div className="chart-key"><span><i className="line-key"/>95% interval</span><span><i className="chance-key"/>50% expected random-guess accuracy</span></div></div>
    </section>
    <section className="stat-strip" aria-label="Confirmation measurements"><div><span>Probability log loss ↓</span><strong>{fixed(metric.log_loss)}</strong><small>Uniform chance: {fixed(e.metrics.uniform.log_loss)}</small></div><div><span>Brier score ↓</span><strong>{fixed(metric.brier)}</strong><small>Lower probability error is better</small></div><div><span>Confirmation period</span><strong className="period">{day(e.start).replace(', 2023', '')} – {day(e.end)}</strong><small>{count(metric.n)} eligible regular-season games</small></div></section>
    <section className="comparison-section"><div className="section-intro"><span className="eyebrow">Keep the comparison</span><h2>Better than chance.<br/>Added neural value is unresolved.</h2><p>The encoder and same-information baseline use the same pregame information. The paired loss intervals against both include zero, so an incremental neural benefit is not established.</p></div><div className="table-wrap"><table><caption>Full confirmation · identical games for every method</caption><thead><tr><th scope="col">Pipeline / comparator</th><th scope="col">Accuracy</th><th scope="col">Log loss ↓</th></tr></thead><tbody>{methods.map(method => <tr className={method === 'neural' ? 'highlight' : ''} key={method}><th scope="row">{methodNames[method]}</th><td>{pct(e.metrics[method].accuracy)}</td><td>{fixed(e.metrics[method].log_loss)}</td></tr>)}</tbody></table><p className="fine-print">At 50% probability, the fixed tie rule selects home. Uniform and silenced accuracy therefore reflects always choosing home; random guessing has expected accuracy 50%.</p><a className="text-link" href="#methods">View paired uncertainty and full methods →</a></div></section>
    <section className="pipeline-preview"><div className="section-heading"><div><span className="eyebrow">Inside the experiment</span><h2>From pregame form to sensory response.</h2></div><a className="text-link" href="#methods">Follow the pipeline →</a></div><Pipeline/></section>
    <aside className="scope-note"><strong>What this result demonstrates</strong><p>Better-than-chance performance for the complete fitted historical pipeline. It does not establish neural learning, in-circuit choice, feeding behavior, prospective performance, or betting profit.</p></aside>
  </>;
}
export default function App() {
  const [hash, setHash] = useState(() => window.location.hash);
  const page = route(hash);
  // The learning and circuit pages carry their own evidence, so they never request the confirmation.
  const resource = useResource<SummaryState>(page === 'learning' || page === 'circuit' ? null : '/api/sensory/summary');
  useEffect(() => {
    const update = () => { const current = window.location.hash; setHash(current); if (!current || !['#overview', '#backtest', '#methods', '#learning', '#circuit'].includes(current) && !current.startsWith('#backtest/')) { window.history.replaceState(null, '', '/#overview'); setHash('#overview'); } };
    update(); window.addEventListener('hashchange', update); return () => window.removeEventListener('hashchange', update);
  }, []);
  useEffect(() => { window.scrollTo(0, 0); }, [page]);
  const data = resource.data?.status === 'available' && !resource.error ? resource.data : null;
  return <><a className="skip-link" href="#main" onClick={event => { event.preventDefault(); document.getElementById('main')?.focus(); }}>Skip to content</a><header className="app-header"><a className="brand" href="#overview" aria-label="BET36FLY overview">BET<span>36</span>FLY<span className="brand-mark" aria-hidden="true">✳</span></a><nav aria-label="Main navigation">{(['overview', 'backtest', 'methods', 'learning', 'circuit'] as const).map(p => <a href={`#${p}`} key={p} aria-current={page === p ? 'page' : undefined}>{p === 'overview' ? 'Overview' : p === 'backtest' ? 'Backtest explorer' : p === 'methods' ? 'Pipeline & methods' : p === 'learning' ? 'Dopamine learning' : 'Circuit'}</a>)}</nav><span className="header-label">MaleCNS / Research</span></header><main id="main" tabIndex={-1}>
    {page === 'learning' ? <LearningView/> : page === 'circuit' ? <CircuitView/> : resource.error ? <Message title="Confirmation unavailable" retry={() => void resource.reload()}>{resource.error} Previously loaded results are hidden until validation succeeds.</Message> : !resource.data ? <Message title="Loading frozen confirmation…">Checking the saved result and its evidence.</Message> : !data ? <Message title="Confirmation unavailable" retry={() => void resource.reload()}>{resource.data.status !== 'available' && resource.data.message}</Message> : page === 'overview' ? <Overview data={data}/> : page === 'backtest' ? <Backtest data={data} gameId={selectedGame(hash)}/> : <SensoryMethods data={data}/>}
    </main><footer className="app-footer"><span>BET36FLY <span aria-hidden="true">/</span> Source-informed sensory research</span><span>Frozen historical evidence · Plasticity off</span></footer></>;
}
