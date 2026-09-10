import { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { useResource } from './data';
import type { Methods } from './types';
export default function MethodsDialog({ onClose }: { onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const { data, loading, error, reload } = useResource<Methods>('/api/methods');
  useEffect(() => { const element = dialog.current; element?.showModal(); return () => element?.close(); }, []);
  return <dialog ref={dialog} onCancel={onClose} onClick={event => { if (event.target === dialog.current) { const rect = dialog.current.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) onClose(); } }} aria-labelledby="methods-title"><div className="dialog-heading"><h2 id="methods-title">Methods & sources</h2><button onClick={onClose} autoFocus>Close</button></div><div className="method-content">{loading ? <p>Loading the model card…</p> : error ? <div role="alert"><p className="error">{error}</p><button onClick={() => void reload()}>Retry</button></div> : <><ReactMarkdown components={{ a: props => <a {...props} target="_blank" rel="noreferrer"/> }}>{data?.model_card || 'The model card is not available yet.'}</ReactMarkdown>{data?.manifest && <details><summary>Dataset manifest</summary><pre>{JSON.stringify(data.manifest, null, 2)}</pre></details>}</>}</div></dialog>;
}
