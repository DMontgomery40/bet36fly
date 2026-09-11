import { useEffect, useState } from 'react';
import { date, decimal, number, percent, safeUrl } from './data';
import { SportFilter } from './GamesView';
import { deskQuip, deskRows, stateLabel } from './deskData';
import type { DeskFilter } from './deskData';
import type { Desk, DeskPoint, DeskRow, Game, Inference, Sport } from './types';
import './desk.css';

function Arrow() { return <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 10h13m-5-5 5 5-5 5"/></svg>; }
function SportMark({ sport }: { sport: string }) {
  return <svg className="sport-mark" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" aria-hidden="true"><circle cx="12" cy="12" r="9"/>{sport === 'soccer' ? <><path d="m12 7 4.5 3.3-1.7 5.2H9.2l-1.7-5.2L12 7Z"/><path d="m12 3 0 4m8.5 2-4 1.3m1 9-2.7-3.8m-8.3 3.8 2.7-3.8M3.5 9l4 1.3"/></> : <><path d="M6 5c7 4 7 10 0 14M18 5c-7 4-7 10 0 14"/><path d="m8 7-2 2m4 1-2 2m2 2-2 2m8-9 2 2m-4 1 2 2m-2 2 2 2"/></>}</svg>;
}

function SpikeReplay({ inference, busy, onRun, canRun }: { inference: Inference | null; busy: boolean; onRun: () => void; canRun: boolean }) {
  const [frame, setFrame] = useState(0);
  const [playing, setPlaying] = useState(false);
  const samples = inference?.activity.population || [];
  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    setFrame(reduced ? Math.max(0, (inference?.activity.population.length || 1) - 1) : 0);
    setPlaying(!!inference && !reduced);
  }, [inference]);
  useEffect(() => {
    if (!playing || !samples.length) return;
    if (frame >= samples.length - 1) { setPlaying(false); return; }
    const timer = window.setTimeout(() => setFrame(previous => previous + 1), 140);
    return () => window.clearTimeout(timer);
  }, [playing, samples.length, frame]);
  const max = Math.max(1, ...samples);
  return <section className="desk-neural" aria-label="Actual neural recording">
    <div className="desk-neural-heading"><h3>{busy ? 'Running the full brain…' : 'Run the brain'}</h3><button className="desk-run" onClick={onRun} disabled={busy || !canRun}>{busy ? 'Thinking…' : 'Run brain now'}<Arrow/></button></div>
    <div className="desk-trace-row"><svg className="desk-trace" viewBox="0 0 360 65" role="img" aria-label={inference ? `Recorded population spikes, ${samples.length} bins over ${inference.activity.duration_ms} milliseconds` : 'No neural recording yet'}><path className="trace-baseline" d="M0 57H360"/>{samples.map((value, index) => <rect key={index} x={index * 360 / samples.length + 1} y={57 - value / max * 49} width={Math.max(1, 360 / samples.length - 3)} height={Math.max(.8, value / max * 49)} fill="currentColor" opacity={index <= frame ? .95 : .2}/>)}</svg><p>{inference ? <><strong>{number(inference.activity.active_neurons)}</strong> active neurons<br/><span>{number(inference.activity.total_spikes)} spikes · {decimal(inference.activity.wall_seconds, 2)} s CPU</span></> : 'Recorded spikes appear after a run.'}</p></div>
    {inference && <><div className="desk-replay-controls"><button className="small" onClick={() => { setFrame(0); setPlaying(true); }} disabled={playing || busy}>{playing ? 'Replaying…' : 'Replay spikes'}</button><input aria-label="Recorded spike frame" type="range" min={0} max={Math.max(0, samples.length - 1)} value={Math.min(frame, Math.max(0, samples.length - 1))} onChange={event => { setPlaying(false); setFrame(Number(event.target.value)); }}/><span>{Math.min((frame + 1) * inference.activity.bin_ms, inference.activity.duration_ms)} / {inference.activity.duration_ms} ms</span></div><p className="desk-run-note">Latest run: {inference.prediction.pick_label} · {percent(inference.prediction.confidence)}. Recorded pick stays fixed. Playback slowed for viewing.</p></>}
  </section>;
}

function PickCard({ row, selected, onSelect, onRun, canRun, busy }: { row: DeskRow; selected: boolean; onSelect: () => void; onRun: () => void; canRun: boolean; busy: boolean }) {
  const pick = row.prediction;
  return <article className={`desk-pick ${selected ? 'desk-pick-selected' : ''}`}>
    <button className="desk-match-select" onClick={onSelect} aria-pressed={selected} aria-label={`Inspect ${pick.away} at ${pick.home}`}>
      <span className="desk-match-meta"><SportMark sport={pick.sport}/><time dateTime={pick.start_time}>{date(pick.start_time)}</time><span>{row.league || pick.sport}</span></span>
      <span className="desk-match-teams"><strong>{pick.home}</strong><span>vs</span><strong>{pick.away}</strong></span>
    </button>
    <div className="desk-pick-bottom"><div><span>Fly picks</span><strong>{pick.pick_label}</strong></div><div><span>Model probability</span><strong className="lime mono">{percent(pick.confidence)}</strong></div><button className={selected ? 'desk-watch' : 'desk-watch compact-watch'} disabled={!canRun || busy} onClick={onRun} aria-label={`Watch this pick: ${pick.away} at ${pick.home}`}>{selected ? (busy ? 'Thinking…' : 'Watch this pick') : 'Watch'}<Arrow/></button></div>
  </article>;
}

function ProgressChart({ points }: { points: DeskPoint[] }) {
  const x = (index: number) => points.length === 1 ? 290 : 40 + index / Math.max(1, points.length - 1) * 535;
  const path = (key: 'hit_rate' | 'expected_rate') => points.map((point, index) => `${index ? 'L' : 'M'}${x(index)},${115 - point[key] * 95}`).join(' ');
  return <div className="desk-progress-chart"><div className="desk-chart-heading"><h3>Does the record match the confidence?</h3><span><i/>Hit rate <i className="expected"/>Model estimate</span></div>
    {points.length ? <><svg viewBox="0 0 600 142" role="img" aria-label={`Cumulative hit rate over ${points.length} completed games, in kickoff order; compared with mean recorded pick probability.`}>{[0, .5, 1].map(value => <g key={value}><path className="desk-chart-grid" d={`M40 ${115 - value * 95}H575`}/><text x="0" y={119 - value * 95}>{value * 100}%</text></g>)}<path className="desk-expected-line" d={path('expected_rate')}/><path className="desk-actual-line" d={path('hit_rate')}/>{points.map((point, index) => <g key={point.game_id}><circle cx={x(index)} cy={115 - point.expected_rate * 95} r="2.8" fill="#849682"/><circle cx={x(index)} cy={115 - point.hit_rate * 95} r="3" fill="#c5f277"/></g>)}<text x="40" y="138">Game 1</text><text x="575" y="138" textAnchor="end">Game {points.length}</text></svg><p className="fine">Completed fixtures in kickoff order. Small samples are noisy; this is prediction accuracy, not profit.</p></> : <div className="desk-chart-empty"><span>The first result gets the first dot.</span><p>The curve will use completed games with a recorded pregame pick.</p></div>}
  </div>;
}

export default function DeskView({ data, error, loading, games, inference, busyId, modelReady, onPredict }: { data: Desk | null; error: string; loading: boolean; games: Game[]; inference: Inference | null; busyId: string | null; modelReady: boolean; onPredict: (game: Game) => Promise<void> }) {
  const [sport, setSport] = useState<Sport>('all');
  const [filter, setFilter] = useState<DeskFilter>('upcoming');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [limit, setLimit] = useState(10);
  const allRows = data?.rows || [];
  const upcoming = deskRows(allRows, sport, 'upcoming').filter(row => row.state === 'upcoming');
  const selected = allRows.find(row => row.game_id === selectedId && (sport === 'all' || row.prediction.sport === sport)) || upcoming[0] || deskRows(allRows, sport, 'all').at(-1) || null;
  const rows = deskRows(allRows, sport, filter);
  const record = sport === 'all' ? data?.summary : data?.by_sport[sport];
  const selectedGame = games.find(game => game.id === selected?.game_id);
  const currentInference = inference?.game.id === selected?.game_id ? inference : null;
  const canRun = !!selected?.can_run && !!selectedGame && modelReady;
  const points = sport === 'all' ? data?.curve || [] : (() => {
    let wins = 0, expected = 0;
    return deskRows(allRows, sport, 'all').filter(row => ['won', 'lost'].includes(row.state)).map((row, i) => {
      wins += row.state === 'won' ? 1 : 0; expected += row.prediction.confidence;
      return { n: i + 1, wins, hit_rate: wins / (i + 1), expected_rate: expected / (i + 1), game_id: row.game_id, start_time: row.prediction.start_time };
    });
  })();
  function changeSport(value: Sport) { setSport(value); setSelectedId(null); setLimit(10); }
  function inspect(row: DeskRow) { setSelectedId(row.game_id); }
  async function run(row: DeskRow | null) { if (!row) return; setSelectedId(row.game_id); const game = games.find(game => game.id === row.game_id); if (game && row.can_run && modelReady && !busyId) await onPredict(game); }
  return <section className="desk-view" aria-label="Fly’s desk">
    {error && <p className="error" role="alert">{data ? 'Showing last loaded forward record. ' : ''}{error}</p>}
    <div className="desk-top"><div className="desk-stage"><div className="desk-title"><h1>Small brain. <br/>Big weekend.</h1><p>The fly’s actual picks, on the record.</p></div>
      <div className={`desk-character ${busyId ? 'desk-character-busy' : ''}`}><img src="/images/fly-desk.png" alt="A red-eyed fruit fly wearing a tiny green tie at a desk with a laptop and a banana. Its nameplate reads Chief of questionable decisions." width="1400" height="1050"/><div className="desk-banter"><span>Desk banter</span><p>{deskQuip(!!busyId, selected, !!currentInference)}</p></div></div>
      <SpikeReplay inference={currentInference} busy={!!busyId} canRun={canRun} onRun={() => void run(selected)}/>
      <p className="desk-art-note">Illustrated fly, scripted banter. Spike bars come from the real neural run.</p>
    </div><div className="desk-next"><div className="desk-next-heading"><h2>Next on the desk</h2><SportFilter value={sport} onChange={changeSport}/></div>
      {loading && !data ? <p className="empty" role="status">Opening the fly’s notebook…</p> : !upcoming.length ? <p className="empty">{error ? 'The pick feed is unavailable.' : 'No upcoming recorded picks in this sport. Refresh games to fetch the next fixtures.'}</p> : <div className="desk-pick-list">{(selected?.state === 'upcoming' ? [selected, ...upcoming.filter(row => row.game_id !== selected.game_id)] : upcoming).slice(0, 3).map(row => <PickCard key={row.game_id} row={row} selected={row.game_id === selected?.game_id} onSelect={() => inspect(row)} onRun={() => void run(row)} canRun={modelReady && games.some(game => game.id === row.game_id)} busy={!!busyId}/>)}</div>}
      {selected && <details className="desk-evidence" key={selected.prediction.id} open={selected.state !== 'upcoming' ? true : undefined}><summary>Recorded {date(selected.prediction.created_at)} · inspect pick</summary><p>{selected.prediction.home} vs {selected.prediction.away}</p><p>Home {percent(selected.prediction.probabilities.home)} · {selected.prediction.sport === 'soccer' && <>Draw {percent(selected.prediction.probabilities.draw)} · </>}Away {percent(selected.prediction.probabilities.away)}</p><p>{selected.reason}</p>{selected.result && <p>Final: {selected.result.home_score}–{selected.result.away_score}. Observed {date(selected.result.observed_at)}.</p>}<p>{selected.revision_count} saved prediction(s) for this fixture; the first is scored.</p><p className="mono">Model {selected.prediction.run_id}<br/>Pick {selected.prediction.id}</p>{safeUrl(selected.result?.source_url || selected.prediction.source_url) && <a href={safeUrl(selected.result?.source_url || selected.prediction.source_url)} target="_blank" rel="noreferrer">View public source</a>}</details>}
      <p className="desk-feed-note">First recorded pick per fixture. Probabilities are uncalibrated model estimates. <a href="#ledger">Open full ledger<Arrow/></a></p>
    </div></div>
    <section className="desk-record"><div className="desk-record-heading"><h2>The forward record</h2><span>Since {data?.first_recorded_at ? date(data.first_recorded_at) : 'the first recorded pick'}</span></div>
      <div className="desk-scoreboard"><p>Only picks recorded before kickoff count.<br/>{record?.completed ? `${number(record.completed)} completed ${record.completed === 1 ? 'game' : 'games'}. The fly has receipts.` : 'No completed results yet.'}</p><dl><div><dd>{record ? `${record.wins} W / ${record.losses} L` : '—'}</dd><dt>Correct / missed</dt></div><div><dd>{number(record?.upcoming)}</dd><dt>Upcoming</dt></div><div><dd>{number(record?.pending)}</dd><dt>Awaiting final</dt></div><div><dd>{percent(record?.hit_rate ?? undefined)}</dd><dt>Hit rate</dt></div></dl></div>
      {!!record && (record.held > 0 || record.void > 0) && <p className="notice">{record.held} on hold · {record.void} cancelled. These do not affect the scored record.</p>}
      <div className="desk-table-toolbar"><div className="desk-state-filter" role="group" aria-label="Filter forward record">{(['upcoming', 'results', 'all'] as const).map(value => <button key={value} aria-pressed={filter === value} onClick={() => { setFilter(value); setLimit(10); }}>{value === 'upcoming' ? 'Upcoming & pending' : value === 'results' ? 'Results' : 'All picks'}</button>)}</div><span>{number(rows.length)} {sport === 'all' ? 'games' : sport + ' games'}</span></div>
      <p className="desk-table-hint">Swipe the table to see probabilities and results.</p><div className="table-scroll"><table className="desk-table"><thead><tr><th>Match · UTC</th><th>Fly pick</th><th>Probability</th><th>State / final</th><th><span className="sr-only">Inspect pick</span></th></tr></thead><tbody>{rows.slice(0, limit).map(row => <tr key={row.prediction.id} className={selected?.game_id === row.game_id ? 'desk-row-selected' : ''}><th scope="row"><span className="desk-table-match"><SportMark sport={row.prediction.sport}/><span>{row.prediction.home} vs {row.prediction.away}<small>{date(row.prediction.start_time)} · {row.league || row.prediction.sport}</small></span></span></th><td>{row.prediction.pick_label}</td><td className="mono">{percent(row.prediction.confidence)}</td><td><span className={`desk-state desk-state-${row.state}`}>{stateLabel(row)}</span>{row.result && <small className="desk-final-score">{row.result.home_score}–{row.result.away_score}</small>}</td><td><button className="desk-inspect" aria-label={`Inspect recorded pick for ${row.prediction.away} at ${row.prediction.home}`} onClick={() => { inspect(row); document.querySelector('.desk-stage')?.scrollIntoView({ block: 'start', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' }); }}><Arrow/></button></td></tr>)}</tbody></table>{!rows.length && <p className="empty">{filter === 'results' ? 'No completed results in this view yet. They appear when the public source confirms the final score.' : 'No recorded picks in this view.'}</p>}</div>
      {rows.length > limit && <button className="desk-show-more" onClick={() => setLimit(value => value + 10)}>Show 10 more <span className="muted">({rows.length - limit} remaining)</span></button>}
      <ProgressChart points={points}/>
      <details className="desk-rules"><summary>How this record is scored</summary><p>{data?.selection_rule || 'The first valid pregame pick for each current fixture is scored.'} Later neural runs cannot replace it. Cancelled, unresolved and replaced fixtures are not scored. Source corrections can revise a final result. This view contains no retrospective backtest picks.</p><p>Public schedules and results refresh every {Math.round((data?.refresh_interval_seconds || 900) / 60)} minutes while the local server is running. Last snapshot: {date(data?.sources_updated_at || undefined)}. Use Refresh games for an immediate check.</p><p>All model versions are included; inspect an individual pick for its version. Profit and stakes await offered odds and an execution record.</p>{!!data && Object.keys(data.excluded).length > 0 && <ul>{Object.entries(data.excluded).map(([key, count]) => <li key={key}>{key.replaceAll('_', ' ')}: {count}</li>)}</ul>}</details>
    </section>
  </section>;
}
