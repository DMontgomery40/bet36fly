import { useEffect, useState } from 'react';
import { date, number, request, useResource } from './data';
import BrainView from './BrainView';
import Curve from './Curve';
import GamesView from './GamesView';
import TrainingView, { TrainingProgress } from './TrainingView';
import LedgerView from './LedgerView';
import DeskView from './DeskView';
import MethodsDialog from './MethodsDialog';
import type { Brain, Desk, Game, Games, Inference, Ledger, Source, Sport, Status, Training } from './types';

type Tab = 'observatory' | 'training' | 'ledger' | 'desk';
function initialTab(): Tab { const hash = window.location.hash.slice(1); return hash === 'training' || hash === 'ledger' || hash === 'desk' ? hash : 'observatory'; }
function Sources({ sources }: { sources: Source[] }) { return sources.length ? <details className="sources"><summary>Source status · {sources.some(source => ['stale', 'failed'].includes(source.status)) ? 'attention needed' : 'view provenance'}</summary><ul>{sources.map((source, index) => <li key={`${source.name}-${index}`}><strong>{source.name}</strong><span className={['stale', 'failed'].includes(source.status) ? 'warning-text' : ''}>{source.status}</span><span>Fetched {date(source.fetched_at)}</span>{source.error && <span>{source.error}</span>}</li>)}</ul></details> : null; }
export default function App() {
  const [tab, setTab] = useState<Tab>(initialTab);
  const [sport, setSport] = useState<Sport>('all');
  const [methods, setMethods] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [refreshRequested, setRefreshRequested] = useState(false);
  const [actionError, setActionError] = useState('');
  const [inference, setInference] = useState<Inference | null>(null);
  const status = useResource<Status>('/api/status', 3000);
  const games = useResource<Games>('/api/games?sport=all', 12000);
  const brain = useResource<Brain>('/api/brain');
  const training = useResource<Training>('/api/training', 6000);
  const ledger = useResource<Ledger>('/api/ledger', 12000);
  const desk = useResource<Desk>('/api/desk', 12000);
  const refreshing = refreshRequested || status.data?.refresh.status === 'running';
  const modelReady = status.data?.model_ready === true;
  useEffect(() => { const listener = () => setTab(initialTab()); window.addEventListener('hashchange', listener); return () => window.removeEventListener('hashchange', listener); }, []);
  useEffect(() => {
    if (status.data?.refresh.status === 'complete' || status.data?.refresh.status === 'failed') { void games.reload(); void ledger.reload(); void desk.reload(); }
  }, [status.data?.refresh.status, games.reload, ledger.reload, desk.reload]);
  async function refresh() {
    setRefreshRequested(true); setActionError('');
    try { await request('/api/refresh', { method: 'POST' }); await status.reload(); await Promise.all([games.reload(), ledger.reload(), desk.reload()]); }
    catch (error) { setActionError(error instanceof Error ? error.message : 'Refresh failed.'); }
    finally { setRefreshRequested(false); }
  }
  async function predict(game: Game) {
    setBusyId(game.id); setActionError('');
    try { const result = await request<Inference>(`/api/predict/${encodeURIComponent(game.id)}`, { method: 'POST' }); setInference(result); if (window.innerWidth <= 720) requestAnimationFrame(() => document.querySelector(window.location.hash === '#desk' ? '.desk-neural' : '.brain-section')?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' })); await Promise.all([games.reload(), ledger.reload(), desk.reload()]); }
    catch (error) { setActionError(error instanceof Error ? error.message : 'Inference failed.'); }
    finally { setBusyId(null); }
  }
  const report = training.data?.report;
  const sources = games.data?.sources?.length ? games.data.sources : status.data?.sources || [];
  return <><a className="skip-link" href="#content">Skip to content</a><header className="header"><a className="brand" href="#observatory" aria-label="BET36FLY observatory">BET<span>36</span>FLY</a><div className="brand-description">Fruit fly connectome<br/>sports experiment</div><nav aria-label="Main navigation">{([{ id: 'observatory', name: 'Observatory' }, { id: 'training', name: 'Training' }, { id: 'ledger', name: 'Pick ledger' }, { id: 'desk', name: 'Fly’s desk' }] as const).map(item => <a key={item.id} href={`#${item.id}`} aria-current={tab === item.id ? 'page' : undefined}>{item.name}</a>)}</nav><div className="header-actions"><span className="paper"><i/>Paper mode</span><button className="refresh" disabled={refreshing} onClick={() => void refresh()}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6v5h-5M20 11a8 8 0 1 0-1 6M20 6l-2 2"/></svg>{refreshing ? 'Refreshing…' : 'Refresh games'}</button></div><time className="updated" dateTime={status.data?.updated_at}>{status.data?.updated_at ? date(status.data.updated_at) : 'Connecting…'}</time></header>
    <main id="content">
      {status.error && <div className="error" role="alert">{status.data ? 'Connection interrupted. Displayed data may be stale. ' : 'Cannot connect to the experiment. '}{status.error}<button className="small" onClick={() => { void status.reload(); void games.reload(); void training.reload(); void ledger.reload(); void desk.reload(); }}>Reconnect</button></div>}
      {actionError && <div className="error" role="alert">{actionError}<button className="small" onClick={() => setActionError('')}>Dismiss</button></div>}
      {(refreshing || status.data?.refresh.status === 'failed') && <p className={refreshing ? 'notice' : 'error'} role="status">{status.data?.refresh.message || (refreshing ? 'Refreshing public schedules and computing paper picks…' : 'Game refresh failed. Please retry.')}</p>}
      {tab === 'observatory' ? <div className="observatory"><div className="science"><div className="hero"><h1>A small brain. A new game.</h1><p>Real fly wiring. Real games. Paper picks.</p></div><BrainView brain={brain.data} error={brain.error} inference={inference} busy={!!busyId} retry={() => void brain.reload()}/><dl className="stats"><div><dt>Neurons</dt><dd>{number(status.data?.brain?.neurons)}</dd></div><div><dt>Connections</dt><dd>{number(status.data?.brain?.edges)}</dd></div><div><dt>Training games</dt><dd>{number(report?.splits?.train?.n ?? training.data?.progress?.splits?.train?.n ?? status.data?.training?.splits?.train?.n)}</dd></div><div><dt>Runtime</dt><dd>{status.data?.runtime || '—'}</dd></div></dl><Curve curve={report?.curve || training.data?.progress.curve || []}/>{!report && <TrainingProgress progress={training.data?.progress || status.data?.training}/>}</div><GamesView data={games.data} error={games.error} loading={games.loading} sport={sport} onSport={setSport} onPredict={game => void predict(game)} busyId={busyId} modelReady={modelReady} selectedId={inference?.game.id}/></div> : tab === 'training' ? <TrainingView data={training.data} error={training.error} loading={training.loading}/> : tab === 'desk' ? <DeskView data={desk.data} error={desk.error} loading={desk.loading} games={games.data?.games || []} inference={inference} busyId={busyId} modelReady={modelReady} onPredict={predict}/> : <LedgerView data={ledger.data} error={ledger.error} loading={ledger.loading}/>}
      <Sources sources={sources}/>
    </main><footer><span>{brain.data?.dataset || 'MaleCNS'} · Experimental model · No real money</span><button className="text-button" onClick={() => setMethods(true)}>Methods & sources</button></footer>{methods && <MethodsDialog onClose={() => setMethods(false)}/>}</>;
}
