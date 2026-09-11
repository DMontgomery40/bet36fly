import { afterEach, expect, it, vi } from 'vitest';
import { pollExperiments } from './data';
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });
it('polls every five seconds while running, thirty after complete, preserves stale data, and cancels', async () => {
  vi.useFakeTimers();
  const receive = vi.fn(), error = vi.fn();
  const response = (status: string) => ({ ok: true, json: async () => ({ experiments: [{ jobs: [{ status }] }] }) });
  const fetcher = vi.fn().mockResolvedValueOnce(response('running')).mockRejectedValueOnce(new Error('offline')).mockResolvedValue(response('complete'));
  vi.stubGlobal('fetch', fetcher);
  const stop = pollExperiments(receive, error);
  await vi.advanceTimersByTimeAsync(0);
  expect(receive).toHaveBeenCalledTimes(1);
  await vi.advanceTimersByTimeAsync(4999); expect(fetcher).toHaveBeenCalledTimes(1);
  await vi.advanceTimersByTimeAsync(1); expect(error).toHaveBeenLastCalledWith('offline');
  expect(receive).toHaveBeenCalledTimes(1);
  await vi.advanceTimersByTimeAsync(5000); expect(receive).toHaveBeenCalledTimes(2);
  await vi.advanceTimersByTimeAsync(29999); expect(fetcher).toHaveBeenCalledTimes(3);
  await vi.advanceTimersByTimeAsync(1); expect(fetcher).toHaveBeenCalledTimes(4);
  stop(); await vi.advanceTimersByTimeAsync(60000); expect(fetcher).toHaveBeenCalledTimes(4);
});
it('ignores an in-flight result after unmount', async () => {
  vi.useFakeTimers(); let resolve: (value: unknown) => void = () => {};
  vi.stubGlobal('fetch', vi.fn(() => new Promise(r => { resolve = r; })));
  const receive = vi.fn(); const stop = pollExperiments(receive, vi.fn()); stop();
  resolve({ ok: true, json: async () => ({ experiments: [] }) }); await vi.advanceTimersByTimeAsync(0);
  expect(receive).not.toHaveBeenCalled();
});
