import { date, decimal, percent, safeUrl } from './data';
import type { Game, Games, Sport } from './types';
export function SportFilter({ value, onChange }: { value: Sport; onChange: (sport: Sport) => void }) { return <div className="sport-filter" role="group" aria-label="Filter by sport">{(['all', 'soccer', 'baseball'] as const).map(sport => <button key={sport} aria-pressed={value === sport} onClick={() => onChange(sport)}>{sport === 'all' ? 'All' : sport === 'soccer' ? 'Soccer' : 'Baseball'}</button>)}</div>; }
export default function GamesView({ data, error, loading, sport, onSport, onPredict, busyId, modelReady, selectedId }: { data: Games | null; error: string; loading: boolean; sport: Sport; onSport: (sport: Sport) => void; onPredict: (game: Game) => void; busyId: string | null; modelReady: boolean; selectedId?: string }) {
  const games = data?.games.filter(game => sport === 'all' || game.sport === sport) || [];
  return <aside className="radar"><h2>On the fly’s radar</h2><p className="subtitle">Model probabilities from fly neural activity.</p><SportFilter value={sport} onChange={onSport}/>
    {error && <p role="alert" className="error">{data ? 'Showing last loaded fixtures. ' : ''}{error}</p>}
    {!modelReady && <p className="notice">The model is not ready. Picks become available after a trained checkpoint is loaded.</p>}
    {loading && !data ? <p className="empty" role="status">Loading upcoming games…</p> : !games.length ? <p className="empty">{error ? 'Games could not be loaded.' : 'No upcoming fixtures in this sport. Refresh games to check the public schedules.'}</p> : <div className="games-list">{games.map(game => <article className={`game ${selectedId === game.id ? 'selected' : ''}`} key={game.id}>
      <div className="game-meta"><span>{game.league} · {game.sport === 'soccer' ? 'Soccer' : 'Baseball'}</span><time dateTime={game.start_time}>{date(game.start_time)}</time></div>
      <div className="team"><span>{game.home}<small>Home</small></span><strong>{game.prediction ? percent(game.prediction.probabilities.home) : '—'}</strong></div>
      <div className="team"><span>{game.away}<small>Away</small></span><strong>{game.prediction ? percent(game.prediction.probabilities.away) : '—'}</strong></div>
      <div className="game-bottom"><span className="mono">{game.sport === 'soccer' ? `Draw ${game.prediction ? percent(game.prediction.probabilities.draw) : '—'}` : game.prediction ? `Fair odds ${decimal(game.prediction.fair_odds, 2)}` : 'Ready to think'}</span><button className="outline" onClick={() => onPredict(game)} disabled={!!busyId || !modelReady} aria-label={`Watch brain for ${game.away} at ${game.home}`}>{busyId === game.id ? 'Thinking…' : 'Watch brain'}<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 10h13m-5-5 5 5-5 5"/></svg></button></div>
      <div className="game-source">{safeUrl(game.source_url) ? <a href={safeUrl(game.source_url)} target="_blank" rel="noreferrer">{game.source}</a> : <span>{game.source}</span>}<span>Fetched {date(game.source_fetched_at)}</span></div>
    </article>)}</div>}
    <p className="fine radar-note">Probabilities are experimental model outputs. Fair odds are calculated from the model, not bookmaker quotes. Paper picks only.</p>
  </aside>;
}
