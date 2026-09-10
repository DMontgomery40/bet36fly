import { useState } from 'react';
import { date, decimal, number, percent, safeUrl } from './data';
import { SportFilter } from './GamesView';
import type { Ledger, Sport } from './types';
export default function LedgerView({ data, error, loading }: { data: Ledger | null; error: string; loading: boolean }) {
  const [sport, setSport] = useState<Sport>('all');
  const picks = data?.picks.filter(pick => sport === 'all' || pick.sport === sport) || [];
  return <section className="ledger-view"><div className="page-heading"><h1>A record of every pick.</h1><p>Proposed paper picks, unfilled. No wagers, balances, or profit claims.</p></div><div className="ledger-toolbar"><SportFilter value={sport} onChange={setSport}/><a className="button outline" href="/api/ledger/export" download>Export CSV <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2v11m-4-4 4 4 4-4M3 13v4h14v-4"/></svg></a></div>
    {error && <p className="error" role="alert">{data ? 'Showing last loaded ledger. ' : ''}{error}</p>}
    <p className="fine">{number(picks.length)} shown · {number(data?.count)} total ledger rows</p>
    {loading && !data ? <p className="empty">Loading paper ledger…</p> : !picks.length ? <p className="empty">{error ? 'The ledger could not be loaded.' : 'No paper picks recorded in this view. Use Watch brain on an upcoming game, or refresh games with a trained model.'}</p> : <div className="table-scroll"><table><thead><tr><th scope="col">Game time · UTC</th><th scope="col">Sport / match</th><th scope="col">Fly pick</th><th scope="col">Model probability</th><th scope="col">Fair odds</th><th scope="col">Model run / provenance</th></tr></thead><tbody>{picks.map(pick => <tr key={pick.id}><td><time dateTime={pick.start_time}>{date(pick.start_time)}</time></td><th scope="row"><span className="fine sport-name">{pick.sport} · {pick.status}</span>{pick.away} at {pick.home}</th><td>{pick.pick_label}</td><td className="lime mono">{percent(pick.confidence)}</td><td className="mono">{decimal(pick.fair_odds, 2)}</td><td><details><summary className="mono">{pick.run_id}</summary><div className="provenance"><p>Recorded {date(pick.created_at)}</p><p>Source fetched {date(pick.source_fetched_at)}</p>{safeUrl(pick.source_url) && <a href={safeUrl(pick.source_url)} target="_blank" rel="noreferrer">Game source</a>}<p>Model hash <code>{pick.model_hash}</code></p><p>Features <code>{pick.feature_hash}</code></p></div></details></td></tr>)}</tbody></table></div>}
    <p className="fine">Fair odds are 1 ÷ model probability, not offered market prices. The CSV exports the full ledger, including rows outside this sport filter.</p>
  </section>;
}
