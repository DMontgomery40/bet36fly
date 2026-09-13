import { useEffect, useState } from 'react';
import { date, decimal, pollExperiments, useResource } from './data';
import { RewardExperimentsView } from './RewardExperiments';
import { ExperimentRunsView } from './ExperimentRuns';
import type { Criterion, ExperimentIndex, RewardDiagnostic, RewardDiagnosticIndex } from './types';

const criteria: [Criterion, string][] = [
  ['teaching_specific', 'Teaching-specific effect'], ['untaught_guard', 'Untaught half-SD guard'],
  ['cross_compartment', 'Cross-compartment leakage'], ['no_bound_hits', 'No bound observations'],
  ['cumulative', 'Cumulative untaught drift'], ['bit_identical_repeat', 'Deterministic replay'],
  ['sensory_noise_invariance', 'Matched sensory randomness'],
];
const stages = ['acquisition_ab', 'acquisition_cd', 'reversal_ab'];
const knownStatus = new Set(['pending', 'registered', 'running', 'complete', 'incomplete', 'failed', 'cancelled', 'budget_stopped']);
const label = (value?: string | null) => value?.replaceAll('_', ' ').replaceAll('-', ' ') || 'unavailable';
const measured = (value?: number | null, places = 6) => decimal(value ?? undefined, places);
const status = (value?: string) => value && knownStatus.has(value) ? label(value) : 'unavailable';
function localDetail(url: string) { return /^\/api\/reward-diagnostics\/[A-Za-z0-9_-]+$/.test(url) ? url : undefined; }
function artifactUrl(url: string) { return /^\/api\/experiments\/[A-Za-z0-9_-]+\/artifacts\/[A-Za-z0-9_-]+$/.test(url) ? url : undefined; }

function DiagnosticDetail({ panel }: { panel: RewardDiagnostic }) {
  const tail = panel.tail_evidence;
  return <details className="diagnostic-detail"><summary>{panel.run_id} · criteria, measurements and identity</summary>
    <p>{panel.validation_status === 'validated' ? `validated ${panel.evidence_status}` : `${label(panel.validation_status)} · ${panel.evidence_status}`} · stored {panel.stored_verdict || 'verdict unavailable'}</p>
    {panel.validation_error && <p className="error" role="alert">{panel.validation_error}</p>}
    <div className="table-scroll"><table><caption>Seven frozen mechanism criteria</caption><thead><tr><th>Criterion</th><th>Artifact validation</th></tr></thead><tbody>{criteria.map(([key, name]) => <tr key={key}><th scope="row">{name}</th><td>{panel.criteria[key] === true ? 'passed' : panel.criteria[key] === false ? 'failed' : 'not validated'}</td></tr>)}</tbody></table></div>
    {!!panel.missing_validation.length && <p>Missing validation: {panel.missing_validation.map(label).join(', ')}.</p>}
    <div className="table-scroll"><table><caption>Untaught guard · absolute mean ≤ half the sample SD</caption><thead><tr><th>Channel / seed set</th><th>Mean U</th><th>Sample SD</th><th>Limit</th><th>Stored result</th></tr></thead><tbody>{Object.entries(panel.untaught_guard).map(([key, row]) => <tr key={key}><th scope="row">{key}</th><td>{measured(row.mean)}</td><td>{measured(row.sd)}</td><td>{measured(row.limit)}</td><td>{row.passed === true ? 'passed' : row.passed === false ? 'failed' : 'unavailable'}</td></tr>)}</tbody></table></div>
    {!!Object.keys(panel.teaching_specific).length && <div className="table-scroll"><table><caption>Matched teaching effects · gain sums</caption><thead><tr><th>Channel / seed set</th><th>Taught − untaught</th><th>Mean untaught</th><th>Required magnitude</th></tr></thead><tbody>{Object.entries(panel.teaching_specific).map(([key, row]) => <tr key={key}><th scope="row">{key}</th><td>{measured(row.mean_effect)}</td><td>{measured(row.mean_untaught)}</td><td>{measured(row.required_magnitude)}</td></tr>)}</tbody></table></div>}
    <p>Learning rule: {panel.learning_rule || 'unavailable'} ({label(panel.learning_rule_source)}). DAN reference: {panel.dan_reference || 'unavailable'}. Away eligibility: {panel.away_plasticity_mask || 'unavailable'}.</p>
    {panel.learning_rule === 'rate-bridge-v1' && <aside className="reward-assumptions"><h4>Recorded bridge and analytic tail</h4>
      <p>τr {measured(panel.rate_tau_ms, 0)} ms · τe {measured(panel.tau_ms, 0)} ms · eta {measured(panel.learning_rate)} · normalization {measured(panel.bridge_normalization, 3)} · h {measured(panel.bridge_contract?.config?.h_ms, 1)} ms.</p>
      <p>Layout {panel.bridge_layout || 'unavailable'} · tail {panel.bridge_tail || 'unavailable'}.</p>
      {tail ? <><p><code>{tail.equation}</code></p><p>After the final electrical interval, the analytic no-new-event tail changes the bounded gain accumulator and published float32 gain. It does not extend neural time, spikes, voltages, membrane state, or count bins.</p>
        <p>{`${tail.electrical_bound_observations} electrical / ${tail.tail_bound_observations} tail bound observations`}.</p>
        {tail.totals && <dl>{Object.entries(tail.totals).map(([key, value]) => <div key={key}><dt>{label(key)}</dt><dd>{measured(value)}</dd></div>)}<div><dt>Clipping discrepancy</dt><dd>{measured(tail.clipping_discrepancy)}</dd></div><div><dt>Final rounding discrepancy</dt><dd>{measured(tail.final_rounding_discrepancy)}</dd></div></dl>}
        <p className="fine">Maximum publication reconciliation error: {measured(tail.max_publication_reconciliation_error, 10)}.</p></> : <p>Tail accounting has not been validated.</p>}
      {panel.bridge_contract && <details><summary>Full recorded bridge contract</summary><pre>{JSON.stringify(panel.bridge_contract, null, 2)}</pre></details>}
    </aside>}
    <details><summary>Recorded provenance</summary><dl><div><dt>Native binary SHA256</dt><dd className="mono">{panel.native_binary_sha256 || 'unavailable'}</dd></div><div><dt>Preregistration SHA256</dt><dd className="mono">{panel.preregistration_sha256 || 'unavailable'}</dd></div>{Object.entries(panel.source_code_hashes ?? {}).map(([name, hash]) => <div key={name}><dt>{name}</dt><dd className="mono">{hash}</dd></div>)}</dl></details>
    {localDetail(panel.detail_url) && <a href={localDetail(panel.detail_url)}>Full stored diagnostic JSON and validation</a>}
  </details>;
}

function Conditioning({ experiments, diagnostics, error }: { experiments: ExperimentIndex | null; diagnostics: RewardDiagnosticIndex | null; error: string }) {
  const runs = experiments?.experiments.filter(row => row.kind === 'dopamine-conditioning') ?? [];
  return <section className="conditioning-evidence" aria-label="Conditioning and reversal"><h2>Conditioning and reversal</h2>
    <p>Acquisition and reversal require a qualified mechanism, cue-specific controls and checkpoint ancestry. A completed execution is not evidence that these criteria passed.</p>
    {error && <p className="error" role="alert">{experiments ? 'Showing last loaded conditioning registry. ' : ''}{error}</p>}
    {!experiments ? <p>{error ? 'Conditioning registry unavailable.' : 'Loading conditioning registry…'}</p> : !runs.length && <><p>{diagnostics?.conditioning.message ?? 'No conditioning manifest registered.'}</p>{!!diagnostics?.conditioning.failed_diagnostic_ids.length && <p>Blocking diagnostics: {diagnostics.conditioning.failed_diagnostic_ids.join(', ')}.</p>}</>}
    {runs.map(run => <article key={run.id}><h3>{run.id} · {status(run.status)}</h3>
      <p className="warning-text">Conditioning scientific verdict: unverified. This registry has no artifact validator for conditioning criteria.</p>
      {(run.conditioning?.status_reason || run.error) && <p role="alert">{run.conditioning?.status_reason || run.error}</p>}
      <p>Configured rule / mask: {run.conditioning?.configured_rule || 'unavailable'} / {run.conditioning?.configured_mask || 'unavailable'}. Recorded verified rule / mask: {run.conditioning?.verified_rule || 'unavailable'} / {run.conditioning?.verified_mask || 'unavailable'}.</p>
      <p>Calls planned / actual / cap: {run.conditioning?.calls?.planned ?? 'unavailable'} / {run.conditioning?.calls?.actual ?? 'unavailable'} / {run.conditioning?.calls?.cap ?? 'unavailable'}. Wall time / cap: {measured(run.conditioning?.wall_seconds, 1)} / {measured(run.conditioning?.wall_cap_seconds, 1)} seconds.</p>
      <p>Prerequisite panels: {run.conditioning?.prerequisite_run_ids?.join(', ') || 'unavailable'}.</p>
      <div className="table-scroll"><table><caption>Required conditioning stages</caption><thead><tr><th>Stage</th><th>Execution</th><th>Progress</th><th>Reason / missing evidence</th></tr></thead><tbody>{stages.map(id => { const job = run.jobs.find(row => row.id === id); const stage = run.conditioning?.stages?.find(row => row.id === id); return <tr key={id}><th scope="row">{label(id)}</th><td>{status(stage?.status || job?.status)}</td><td>{job?.total !== undefined ? `${job.completed ?? 0} / ${job.total}` : 'unavailable'}</td><td>{stage?.status_reason || job?.error || job?.cancellation_reason || (stage?.missing_criteria?.length ? stage.missing_criteria.join(', ') : 'Criteria coverage has not been validated.')}</td></tr>; })}</tbody></table></div>
      {run.conditioning?.stages?.map(stage => <details key={stage.id}><summary>{label(stage.id)} · stored criteria and ancestry</summary><p>Classification: {label(stage.classification)}. Strict restoration and opposing-channel remapping are distinct outcomes.</p><p className="mono">Checkpoint {stage.checkpoint_sha256 || 'unavailable'} · parent {stage.parent_checkpoint_sha256 || 'unavailable'}</p><dl>{Object.entries(stage.criteria ?? {}).map(([name, criterion]) => <div key={name}><dt>{label(name)}</dt><dd>Stored {criterion.passed === true ? 'passed' : criterion.passed === false ? 'failed' : 'unavailable'} · value {measured(criterion.value)} · limit {measured(criterion.limit)}</dd></div>)}</dl></details>)}
      <details><summary>Conditioning protocol identity</summary><p className="mono">Protocol {run.conditioning?.protocol_sha256 || 'unavailable'} · addendum {run.conditioning?.addendum_sha256 || 'unavailable'}</p></details>
      <div className="artifact-links">{Object.entries(run.artifacts).filter(([, artifact]) => artifactUrl(artifact.url)).map(([id, artifact]) => <a key={id} href={artifactUrl(artifact.url)}>{artifact.label}</a>)}</div>
    </article>)}
  </section>;
}

type Props = {
  diagnostics: RewardDiagnosticIndex | null; diagnosticsLoading: boolean; diagnosticsError: string;
  experiments: ExperimentIndex | null; experimentsError: string; selectedExperimentId: string; selectedJobId: string;
  onSelectExperiment: (id: string) => void; onSelectJob: (id: string) => void;
  onRetryDiagnostics?: () => void; lastLoaded?: string;
};
export function RewardEvidenceView(props: Props) {
  const { diagnostics, diagnosticsLoading, diagnosticsError, experiments, experimentsError } = props;
  return <><section className="mechanism-evidence" aria-label="Mechanism qualification"><h2>Mechanism qualification</h2>
    <p>Stored circuit measurements and independently reconstructed artifact criteria. Both the original and previously frozen second panel must qualify under the same scientific identity before conditioning.</p>
    {diagnosticsLoading && !diagnostics && <p role="status">Loading mechanism evidence…</p>}
    {diagnosticsError && <p role="alert" className="error">{diagnostics ? `Showing last loaded mechanism evidence${props.lastLoaded ? ` (${date(props.lastLoaded)})` : ''}. ` : ''}{diagnosticsError} {props.onRetryDiagnostics && <button onClick={props.onRetryDiagnostics}>Retry evidence</button>}</p>}
    {diagnostics && !diagnostics.diagnostics.length && <p>No stored mechanism panels.</p>}
    {diagnostics?.qualification_pairs.map(pair => <aside className="reward-assumptions" key={pair.pair_id}><h3>Pair qualification · {diagnosticsError ? 'unverified (stale)' : pair.validation_status === 'validated' ? pair.evidence_status : 'unverified'}</h3><p>{pair.learning_rule || 'Unknown rule'} · {pair.original_run_id} + {pair.heldout_run_id}</p><p>{label(pair.validation_status)}{pair.failed_criteria.length ? ` · failed: ${pair.failed_criteria.map(label).join(', ')}` : ''}</p></aside>)}
    {!!diagnostics?.diagnostics.length && <div className="table-scroll"><table className="mechanism-table"><caption>Stored diagnostic panels</caption><thead><tr><th>Run / rule</th><th>Panel</th><th>Stored verdict</th><th>Artifact validation</th><th>Scientific status</th></tr></thead><tbody>{diagnostics.diagnostics.map(panel => <tr key={panel.run_id}><th scope="row">{panel.run_id}<br/>{panel.learning_rule || 'unavailable'}</th><td>{panel.selection_status === 'previously-frozen' ? 'Previously frozen held-out' : label(panel.panel_role)}</td><td>stored {panel.stored_verdict || 'unavailable'}</td><td>{label(panel.validation_status)}</td><td>{panel.validation_status === 'validated' ? `validated ${panel.evidence_status}` : panel.evidence_status}</td></tr>)}</tbody></table></div>}
    {diagnostics?.diagnostics.map(panel => <DiagnosticDetail key={panel.run_id} panel={panel}/>)}
  </section><Conditioning experiments={experiments} diagnostics={diagnostics} error={experimentsError}/>
  <section aria-label="Historical sports association pilots"><h2>Historical sports association pilots</h2><p>These descriptive development comparisons do not establish mechanism qualification or conditioning.</p><RewardExperimentsView data={experiments} error={experimentsError} selectedExperimentId={props.selectedExperimentId} selectedJobId={props.selectedJobId} onSelectExperiment={props.onSelectExperiment} onSelectJob={props.onSelectJob}/></section></>;
}

export default function RewardEvidence() {
  const [experiments, setExperiments] = useState<ExperimentIndex | null>(null);
  const [experimentsError, setExperimentsError] = useState('');
  const [selectedExperimentId, setSelectedExperimentId] = useState('');
  const [selectedJobId, setSelectedJobId] = useState('');
  const [lastLoaded, setLastLoaded] = useState('');
  const diagnostics = useResource<RewardDiagnosticIndex>('/api/reward-diagnostics', 30000);
  useEffect(() => pollExperiments(setExperiments, setExperimentsError), []);
  useEffect(() => { if (diagnostics.data) setLastLoaded(new Date().toISOString()); }, [diagnostics.data]);
  return <><RewardEvidenceView diagnostics={diagnostics.data} diagnosticsLoading={diagnostics.loading} diagnosticsError={diagnostics.error} experiments={experiments} experimentsError={experimentsError} selectedExperimentId={selectedExperimentId} selectedJobId={selectedJobId} onSelectExperiment={id => { setSelectedExperimentId(id); setSelectedJobId(''); }} onSelectJob={setSelectedJobId} onRetryDiagnostics={() => { void diagnostics.reload(); }} lastLoaded={lastLoaded}/><ExperimentRunsView data={experiments} error={experimentsError}/></>;
}
