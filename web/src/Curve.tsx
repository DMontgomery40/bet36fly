import type { CurvePoint } from './types';
import { decimal } from './data';
export default function Curve({ curve, title = 'Learning curve' }: { curve: CurvePoint[]; title?: string }) {
  const points = curve.filter(point => [point.epoch, point.train_loss, point.validation_loss].every(Number.isFinite));
  const width = 760, height = 190, left = 44, right = 16, top = 14, bottom = 38;
  const maxX = Math.max(1, ...points.map(point => point.epoch));
  const maxY = Math.max(.1, ...points.flatMap(point => [point.train_loss, point.validation_loss])) * 1.08;
  const x = (epoch: number) => left + epoch / maxX * (width - left - right);
  const y = (loss: number) => top + (1 - loss / maxY) * (height - top - bottom);
  const path = (key: 'train_loss' | 'validation_loss') => points.map((point, index) => `${index ? 'L' : 'M'}${x(point.epoch)},${y(point[key])}`).join(' ');
  return <section className="curve"><div className="section-heading"><h2>{title}</h2><div className="legend"><span><i />Training loss</span><span><i className="validation" />Validation loss</span></div></div>
    {points.length ? <><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${title}. ${points.length} epochs recorded. Latest training loss ${decimal(points.at(-1)?.train_loss)}, validation loss ${decimal(points.at(-1)?.validation_loss)}. Lower loss is better.`}>
      {[0, .5, 1].map(fraction => <g key={fraction}><line x1={left} y1={y(fraction * maxY)} x2={width - right} y2={y(fraction * maxY)} className="grid-line"/><text x={left - 10} y={y(fraction * maxY) + 4} textAnchor="end">{(fraction * maxY).toFixed(2)}</text></g>)}
      {[0, .25, .5, .75, 1].map(fraction => <g key={fraction}><line x1={x(fraction * maxX)} y1={top} x2={x(fraction * maxX)} y2={height - bottom} className="grid-line"/><text x={x(fraction * maxX)} y={height - 18} textAnchor="middle">{Math.round(fraction * maxX)}</text></g>)}
      <path d={path('validation_loss')} className="loss validation"/><path d={path('train_loss')} className="loss"/>
      {points.length === 1 && <><circle cx={x(points[0].epoch)} cy={y(points[0].train_loss)} r="3" fill="#c5f277"/><circle cx={x(points[0].epoch)} cy={y(points[0].validation_loss)} r="3" fill="#9ca9a0"/></>}
      <text x={width / 2} y={height - 1} textAnchor="middle">Epoch</text>
    </svg><p className="fine">Latest train {decimal(points.at(-1)?.train_loss)} · validation {decimal(points.at(-1)?.validation_loss)} · lower loss is better.</p></> : <p className="empty">No recorded learning curve yet. Values will appear as training progresses.</p>}
  </section>;
}
