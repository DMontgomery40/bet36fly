import { useCallback, useEffect, useRef, useState } from 'react';
export async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(typeof body?.detail === 'string' ? body.detail : `Request failed (${response.status}). Please retry.`);
  }
  return response.json();
}
/** A null url means this page does not need the resource: nothing is fetched and nothing stays loading. */
export function useResource<T>(url: string | null, interval = 0) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(!!url);
  const sequence = useRef(0);
  const reload = useCallback(async () => {
    if (!url) { sequence.current++; setLoading(false); return; }
    const current = ++sequence.current;
    try { const result = await request<T>(url); if (current === sequence.current) { setData(result); setError(''); } }
    catch (e) { if (current === sequence.current) setError(e instanceof Error ? e.message : 'Unable to load data.'); }
    finally { if (current === sequence.current) setLoading(false); }
  }, [url]);
  useEffect(() => {
    setData(null); setError(''); setLoading(!!url);
    if (!url) { sequence.current++; return; }
    void reload();
    const timer = interval ? window.setInterval(reload, interval) : undefined;
    return () => { sequence.current++; clearInterval(timer); };
  }, [url, reload, interval]);
  return { data, error, loading, reload };
}
export function number(value?: number) { return typeof value === 'number' && Number.isFinite(value) ? new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value) : '—'; }
export function decimal(value?: number, places = 3) { return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(places) : '—'; }
export function percent(value?: number) { return typeof value === 'number' && Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : '—'; }
export function date(value?: string) { if (!value) return 'Time unavailable'; const d = new Date(value); return Number.isNaN(d.valueOf()) ? 'Time unavailable' : new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }).format(d) + ' UTC'; }
export function safeUrl(url?: string): string | undefined { if (!url) return; try { const parsed = new URL(url); return ['http:', 'https:'].includes(parsed.protocol) ? parsed.href : undefined; } catch { return; } }
export function activityAt(trace: number[][], frame: number, node: number) { const value = trace[frame]?.[node]; return typeof value === 'number' && Number.isFinite(value) && value > 0 ? value : 0; }

/** Poll from the latest returned state; an error never discards the last result. */
export function pollExperiments(onData: (data: import('./types').ExperimentIndex) => void, onError: (error: string) => void) {
  let stopped = false; let timer: ReturnType<typeof setTimeout>; let interval = 30000;
  async function poll() {
    try {
      const data = await request<import('./types').ExperimentIndex>('/api/experiments');
      if (stopped) return;
      interval = data.experiments.some(experiment => experiment.jobs.some(job => job.status === 'running')) ? 5000 : 30000;
      onData(data); onError('');
    } catch (error) { if (!stopped) onError(error instanceof Error ? error.message : 'Experiment fetch failed.'); }
    if (!stopped) timer = setTimeout(poll, interval);
  }
  void poll();
  return () => { stopped = true; clearTimeout(timer); };
}
