import { useEffect, useRef, useState } from 'react';
import { activityAt, date, decimal, number } from './data';
import type { Brain, Inference } from './types';

export default function BrainView({ brain, error, inference, busy, retry }: { brain: Brain | null; error: string; inference: Inference | null; busy: boolean; retry: () => void }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const [frame, setFrame] = useState(-1);
  const [playing, setPlaying] = useState(false);
  const [rotation, setRotation] = useState(0);
  const activity = inference?.activity;
  useEffect(() => { setPlaying(false); setFrame(-1); }, [inference]);
  useEffect(() => {
    if (!playing || !activity) return;
    const timer = window.setInterval(() => setFrame(previous => {
      if (previous >= activity.trace.length - 1) { setPlaying(false); return previous; }
      return previous + 1;
    }), window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 600 : 180);
    return () => clearInterval(timer);
  }, [playing, activity]);
  useEffect(() => {
    if (!brain || !canvas.current) return;
    const element = canvas.current;
    function draw() {
      const context = element.getContext('2d'); if (!context || !brain) return;
      const bounds = element.getBoundingClientRect(); const ratio = Math.min(window.devicePixelRatio || 1, 2);
      element.width = bounds.width * ratio; element.height = bounds.height * ratio;
      context.scale(ratio, ratio); context.clearRect(0, 0, bounds.width, bounds.height);
      const angle = rotation * Math.PI / 180;
      const projected = brain.nodes.map(node => ({ x: node.x * Math.cos(angle) + node.z * Math.sin(angle), y: -node.y + node.z * 0.12, depth: node.z * Math.cos(angle) - node.x * Math.sin(angle) }));
      if (!projected.length) return;
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      for (const point of projected) { minX = Math.min(minX, point.x); maxX = Math.max(maxX, point.x); minY = Math.min(minY, point.y); maxY = Math.max(maxY, point.y); }
      const scale = Math.min((bounds.width - 56) / (maxX - minX || 1), (bounds.height - 80) / (maxY - minY || 1));
      const points = projected.map(point => ({ x: (point.x - (maxX + minX) / 2) * scale + bounds.width / 2, y: (point.y - (maxY + minY) / 2) * scale + bounds.height / 2 + 4, depth: point.depth }));
      context.strokeStyle = 'rgba(139,172,106,0.075)'; context.lineWidth = 0.65; context.beginPath();
      for (const [a, b] of brain.edges) { if (!points[a] || !points[b]) continue; context.moveTo(points[a].x, points[a].y); context.lineTo(points[b].x, points[b].y); }
      context.stroke();
      for (let index = 0; index < points.length; index++) {
        const point = points[index]; const spikes = activity ? activityAt(activity.trace, frame, index) : 0;
        const radius = spikes ? 2.1 + Math.min(Math.log1p(spikes), 2) : 0.9;
        context.fillStyle = spikes ? '#e1ff9b' : `rgba(166,195,139,${Math.max(.3, Math.min(.9, .55 + point.depth * .15))})`;
        if (spikes) { context.shadowColor = '#c5f277'; context.shadowBlur = 7; }
        context.beginPath(); context.arc(point.x, point.y, radius, 0, Math.PI * 2); context.fill(); context.shadowBlur = 0;
      }
    }
    const observer = new ResizeObserver(draw); observer.observe(element); draw(); return () => observer.disconnect();
  }, [brain, activity, frame, rotation]);
  return <section className="brain-section" aria-label="Fly brain observatory">
    <div className="brain-canvas">
      <div className="brain-caption"><strong>Drosophila melanogaster</strong><span>{brain?.dataset || 'MaleCNS connectome'}</span><small>{activity && frame >= 0 ? `Recorded spikes · ${(frame + 1) * activity.bin_ms} / ${activity.duration_ms} ms simulated` : 'Anatomical wiring · no activity replay'}</small></div>
      <div className="brain-key"><i /> {activity && frame >= 0 ? 'Spiking neurons' : 'Real soma positions'}</div>
      {brain?.nodes.length ? <canvas ref={canvas} role="img" aria-label={`Projection of ${number(brain.displayed_neurons)} actual fly neurons and their sampled connections. ${activity && frame >= 0 ? `Recorded activity at ${(frame + 1) * activity.bin_ms} milliseconds simulated time.` : 'Static anatomical view.'}`} /> : <div className="canvas-empty" role="status"><strong>{error ? 'Brain unavailable' : brain ? 'No display neurons available' : 'Loading the connectome…'}</strong>{error && <><p>{error}</p><button onClick={retry}>Retry brain</button></>}</div>}
      <div className="canvas-bottom"><span>{brain ? `${number(brain.displayed_neurons)} displayed / ${number(brain.total_neurons)} computed` : 'Waiting for real coordinates'}</span>{busy && <span className="thinking">Running full network…</span>}</div>
    </div>
    {error && brain && <p className="error" role="alert">Brain data may be stale: {error}</p>}
    <div className="brain-toolbar"><label>View angle <input aria-label="Brain view angle" type="range" min="-60" max="60" value={rotation} onChange={event => setRotation(Number(event.target.value))} /></label><span>Projection of annotated soma positions</span><button className="small" onClick={() => setRotation(0)} disabled={rotation === 0}>Reset view</button></div>
    {inference && activity && <div className="recording" aria-label="Recorded neural inference">
      <div className="recording-title"><div><span className="muted">{inference.game.away} at {inference.game.home}</span><strong>Recorded pick: {inference.prediction.pick_label} <em>{(inference.prediction.confidence * 100).toFixed(1)}%</em></strong></div><button onClick={() => { if (playing) setPlaying(false); else { if (frame >= activity.trace.length - 1) setFrame(-1); setPlaying(true); } }} disabled={!activity.trace.length}>{playing ? 'Pause' : frame > -1 && frame < activity.trace.length - 1 ? 'Resume' : 'Replay spikes'}</button></div>
      <label className="timeline">Recorded simulated time <input aria-label="Recorded simulated time" type="range" min="0" max={Math.max(0, activity.trace.length - 1)} value={Math.max(0, frame)} onChange={event => { setPlaying(false); setFrame(Number(event.target.value)); }} /><span>{frame < 0 ? 0 : Math.min((frame + 1) * activity.bin_ms, activity.duration_ms)} / {activity.duration_ms} ms</span></label>
      <p className="fine">Recorded {date(inference.prediction.created_at)} · Run {inference.prediction.run_id}. This recording is historical; current picks appear in the game list.</p>
      <p className="fine">{number(activity.active_neurons)} active neurons · {number(activity.total_spikes)} total spikes · {decimal(activity.wall_seconds, 2)} s computation. Replay is slowed for inspection; it is not live activity.</p>
    </div>}
    {brain && <details className="coordinate-note"><summary>About this view</summary><p>{brain.coordinate_note} Lines are actual connections among displayed neurons. Display sampling does not reduce the computational network.</p></details>}
  </section>;
}
