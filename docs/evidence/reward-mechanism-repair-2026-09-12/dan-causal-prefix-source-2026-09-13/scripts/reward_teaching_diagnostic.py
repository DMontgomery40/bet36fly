"""Predeclared taught-versus-untaught diagnostic panel on the schema-3 reward circuit.

Runs the panel frozen in output/collaboration/reward-repair/evidence/candidate-rule-spec-v1.1.md
section 5 for one rule variant, from the historical pilot's protocol and calibration games, and
writes a versioned, never-overwritten diagnostic directory plus a summary JSON.

    .venv/bin/python scripts/reward_teaching_diagnostic.py --rule legacy
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import sys
import time
from pathlib import Path

import numpy as np
import pyarrow.feather as feather

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bet36fly.connectome import ROOT  # noqa: E402
from bet36fly.experiment import atomic_json, utcnow  # noqa: E402
from bet36fly.reward_brain import RewardEngine  # noqa: E402
from bet36fly.reward_diagnostic import (  # noqa: E402
    COMPARTMENT_OF, PHASES, RULE_REFERENCE, compartment_sums, evaluate_cumulative, evaluate_panel,
    bridge_phase_evidence, check_diagnostic_complete, evaluate_bound_hits, panel_protocol, phase_sums, select_panel, verify_graph_inputs,
)
from bet36fly.reward_protocol import file_hash, make_circuit  # noqa: E402

PILOT = '/Users/davidmontgomery/Documents/ChatGPT/bet36fly/output/experiments/reward-v3-209f7c49983f5873f650'
KC_CLASSES = ('gamma', 'apbp', 'ab', 'other')
CONDITIONS = ('frozen', 'untaught', 'home', 'away')
ALT_SEED_OFFSET = 1_000_000
RULE_TERMS = ('term_dbar_k', 'term_kbar_d', 'applied', 'clipped_low', 'clipped_high', 'kc_events', 'kbar_mass_end')
BRIDGE_DOCUMENTS = {
    'rate-bridge-preregistration.md': 'ab7c640f3bfbc74845ff2759421b8b2de91d6411b9a6685acd3a62d1147508e3',
    'rate-bridge-implementation-contract.md': 'c35484a6a6f1a1405d79ec7673810887edd5744373e7519f0d35358f0588a71e',
}


def bridge_contract_identity():
    directory = Path(__file__).resolve().parents[1] / 'docs/evidence/reward-mechanism-repair-2026-09-12'
    actual = {name: file_hash(directory / name) for name in BRIDGE_DOCUMENTS}
    if actual != BRIDGE_DOCUMENTS:
        raise ValueError('Frozen bridge contract changed; refusing a mislabeled candidate.')
    return dict(documents=actual, layout='rate-bridge-v1/1',
                config=dict(h_ms=.2, tau_ms=500., rate_tau_ms=100., eta=.0005, normalization=.96),
                tail='analytic_no_new_event_tail',
                state='zero onset/trial states; double within-trial accumulation; float32 publication/checkpoint; discard remainder')


def numeric_fingerprint(result):
    """Every returned numerical array, including record-only arrays, except elapsed wall time."""
    arrays = {name: value for name, value in result.items() if isinstance(value, np.ndarray)}
    arrays.update({f'instrumentation/{name}': value for name, value in result['instrumentation'].items()
                   if isinstance(value, np.ndarray)})
    return {name: (str(value.dtype), value.shape, hashlib.sha256(value.tobytes()).hexdigest())
            for name, value in arrays.items()}


def kc_class(type_name):
    name = str(type_name)
    if name.startswith("KCa'b'"):
        return 'apbp'
    if name.startswith('KCg'):
        return 'gamma'
    if name.startswith('KCab'):
        return 'ab'
    return 'other'


def freeze_preregistration(path, identity, run_id):
    """Create the pre-execution selection receipt exclusively; an existing different freeze is an error."""
    document = dict(status='preregistered-not-run', created_at=utcnow(), run_id=run_id, identity=identity,
                    criteria=dict(teaching_effect_ratio=3.0, untaught_sd_ratio=0.5,
                                  cross_compartment_ratio=0.05, cumulative_effect_ratio=4.0,
                                  no_bound_hits=True, bit_identical_repeat=True, sensory_noise_invariance=True))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = json.loads(path.read_text())
        if (existing.get('identity') != identity or existing.get('run_id') != run_id
                or existing.get('criteria') != document['criteria']
                or existing.get('status') != document['status']):
            raise ValueError('Preregistration differs; preserve it and use a new identity/path.')
        return existing
    with path.open('x') as stream:
        json.dump(document, stream, indent=2, allow_nan=False)
        stream.write('\n')
    return document


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rule', choices=tuple(RULE_REFERENCE), required=True)
    parser.add_argument('--away-mask', choices=('all', 'gamma'), default='all')
    parser.add_argument('--pilot', type=Path, default=Path(PILOT))
    parser.add_argument('--games', type=int, default=8)
    parser.add_argument('--panel-offset', type=int, default=0)
    parser.add_argument('--seed-offset', type=int, default=0)
    parser.add_argument('--panel-kind', choices=('original', 'held-out', 'debug'), default=None)
    parser.add_argument('--preregistration', type=Path, help='immutable pre-execution selection and input identity receipt')
    parser.add_argument('--preregister-only', action='store_true', help='freeze inputs/selectors without building or running the circuit')
    parser.add_argument('--cumulative-games', type=int, default=16)
    parser.add_argument('--out', type=Path, default=ROOT / 'output/diagnostics')
    parser.add_argument('--evidence', type=Path, default=None, help='directory to receive a copy of summary.json')
    parser.add_argument('--cancel-file', type=Path, default=None)
    args = parser.parse_args(argv)
    if args.preregister_only and not args.preregistration:
        parser.error('--preregister-only requires --preregistration')

    started = time.time()
    base_protocol = json.loads((args.pilot / 'source/protocol.json').read_text())
    if 'dan_reference' not in inspect.signature(RewardEngine.__init__).parameters:
        raise SystemExit('This revision has no dan_reference mode; refusing to run a mislabeled panel.')
    protocol = panel_protocol(base_protocol, args.rule, args.away_mask)
    bridge = args.rule == 'rate-bridge-v1'
    with np.load(args.pilot / 'source/inputs.npz', allow_pickle=False) as stored:
        inputs = {name: stored[name] for name in stored.files}
    selection = select_panel(inputs, seed=protocol['seed'], panel_offset=args.panel_offset,
                             seed_offset=args.seed_offset, games=args.games, cumulative_games=args.cumulative_games,
                             panel_kind=args.panel_kind)
    if selection['panel_kind'] == 'held-out' and not args.preregistration:
        parser.error('held-out panels require an explicit --preregistration receipt')
    manifest_path = args.pilot / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    graph_hashes = verify_graph_inputs(ROOT, manifest['identity'])
    X, src = inputs['X'], inputs['source_indices']
    mean, std = inputs['input_mean'], inputs['input_std']
    def code_hashes():
        hashes = {name: file_hash(Path(__file__).resolve().parents[1] / 'bet36fly' / name)
                  for name in ('reward_lif.cpp', 'reward_brain.py', 'reward_protocol.py', 'reward_encoder.py', 'reward_diagnostic.py')}
        hashes['reward_teaching_diagnostic.py'] = file_hash(Path(__file__).resolve())
        return hashes

    code = code_hashes()
    identity = dict(rule=args.rule, protocol=protocol, pilot=args.pilot.name, games=args.games,
                    cumulative_games=args.cumulative_games, alt_seed_offset=ALT_SEED_OFFSET, code_hashes=code,
                    inputs_sha256=file_hash(args.pilot / 'source/inputs.npz'),
                    pilot_manifest_sha256=file_hash(manifest_path),
                    pilot_protocol_sha256=file_hash(args.pilot / 'source/protocol.json'),
                    graph_hashes=graph_hashes, selection=selection, panel_kind=selection['panel_kind'])
    if bridge:
        identity['bridge_contract'] = bridge_contract_identity()
    run_id = f'diag-{args.rule}' + ('' if args.away_mask == 'all' else f'-mask{args.away_mask}') + '-' + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:12]
    if selection['panel_kind'] == 'debug':
        run_id += '-INCOMPLETE'
    out = args.out / run_id
    if out.exists():
        raise SystemExit(f'{out} exists; a changed input or code produces a new identity, reruns are not repeated.')
    if args.preregister_only:
        freeze_preregistration(args.preregistration, identity, run_id)
        print(f'[{run_id}] preregistered only -> {args.preregistration}; circuit not built or run', flush=True)
        return 0
    if selection['panel_kind'] == 'held-out' and not args.preregistration.is_file():
        parser.error('held-out receipt must already exist; run --preregister-only before independent review')
    if args.preregistration:
        freeze_preregistration(args.preregistration, identity, run_id)
    out.mkdir(parents=True)
    if not args.preregistration:
        freeze_preregistration(out / 'preregistration.json', identity, run_id)
    if args.preregistration:
        atomic_json(out / 'preregistration.json', json.loads(args.preregistration.read_text()))
    print(f'[{run_id}] building circuit', flush=True)
    engine, anatomy, outputs, dcomp, kc, sensory, encode = make_circuit(ROOT, protocol, n_features=X.shape[1])
    native_binary = dict(path=str(engine.lib._name), sha256=file_hash(engine.lib._name))
    if engine.dan_reference != RULE_REFERENCE[args.rule]:
        raise SystemExit(f'Engine reference mode {engine.dan_reference} does not match --rule {args.rule}.')
    if engine.learning_rule != protocol['learning_rule']:
        raise SystemExit('Built learning rule does not match the frozen protocol.')
    audit = anatomy['plasticity_mask']
    if audit['away']['policy'] != args.away_mask or audit['home']['policy'] != 'all' or (
            args.away_mask == 'all' and int(engine.plastic_mask.sum()) != len(engine.plastic_mask)):
        raise SystemExit(f'Built eligibility {audit} does not match --away-mask {args.away_mask}.')
    ids = np.load(ROOT / 'data/brain/ids.npy')
    nodes = feather.read_table(ROOT / 'data/brain/nodes.feather', columns=['bodyId', 'type']).to_pandas()
    types = nodes.set_index('bodyId').reindex(ids)['type'].fillna('').to_numpy()
    pc, pk = engine.plastic_compartments, engine.plastic_kc_indices
    classes = np.array([KC_CLASSES.index(kc_class(types[k])) for k in kc[pk]], np.int32)
    groups = (pc * len(KC_CLASSES) + classes).astype(np.int32)
    group_labels = [f'{label}/{cls}' for label in COMPARTMENT_OF for cls in KC_CLASSES]
    group_edges = [int(np.count_nonzero(groups == g)) for g in range(len(group_labels))]
    n_bins = round(protocol['duration_ms'] / protocol['bin_ms'])
    stimulus_bins = round(protocol['stimulus_ms'] / protocol['bin_ms'])
    output_count = sum(map(len, outputs))
    n_dan = len(engine.dan_indices)
    sampled = np.concatenate([*outputs, engine.dan_indices, kc, sensory])
    sensory_slice = slice(output_count + n_dan + len(kc), None)
    dan_slice = slice(output_count, output_count + n_dan)
    blank = engine.gains.copy()

    def schedule_for(source_index):
        pos = int(np.flatnonzero(src == source_index)[0])
        features = np.clip((X[pos] - mean) / std, -8, 8)
        schedule = np.zeros((n_bins, len(sensory)), np.float32)
        schedule[:stimulus_bins] = encode(features)
        return schedule

    def pulses_for(compartment):
        return [(protocol['teaching_ms'] + p * protocol['teaching_interval_ms'], int(d))
                for p in range(protocol['teaching_pulse_count']) for d in np.flatnonzero(dcomp == compartment)]

    def run(source_index, seed, condition, *, learn, reset=True):
        if args.cancel_file and args.cancel_file.exists():
            raise SystemExit('cancelled by control file')
        if reset:
            engine.gains[:] = blank
        pulses = pulses_for(COMPARTMENT_OF[condition]) if condition in COMPARTMENT_OF else ()
        result = engine.run(schedule_for(source_index), bin_ms=protocol['bin_ms'], seed=seed, teaching_pulses=pulses,
                            plasticity=learn, sample=sampled, record=True, plastic_groups=groups,
                            n_groups=len(group_labels))
        return result

    def summarize(result):
        rec = result['instrumentation']
        bridge_evidence = bridge_phase_evidence(result, pc, np.arange(len(group_labels)) // len(KC_CLASSES),
            dt=.2, onset_ms=protocol['plasticity_onset_ms'], stimulus_ms=protocol['stimulus_ms']) if bridge else None
        phases = None if bridge else phase_sums(rec['rule_bins'], bin_ms=protocol['bin_ms'], onset_ms=protocol['plasticity_onset_ms'],
                                                stimulus_ms=protocol['stimulus_ms'])
        signal = phase_sums(rec['signal_bins'], bin_ms=protocol['bin_ms'], onset_ms=protocol['plasticity_onset_ms'],
                            stimulus_ms=protocol['stimulus_ms'])
        kc_bins = rec['kc_signal_bins']
        applied = compartment_sums(result['gain_delta'], pc, 2)
        recorded_applied = np.array(bridge_evidence['recorded_applied']) if bridge else np.array([
            rec['rule_bins'][:, [g for g in range(len(group_labels)) if g // len(KC_CLASSES) == c], 2].sum() for c in range(2)])
        if not np.allclose(applied, recorded_applied, atol=1e-3):
            raise RuntimeError(f'Recorded applied {recorded_applied} disagrees with gain delta {applied}.')
        activity = result['trace'][:stimulus_bins].sum(0) * (1000 / protocol['stimulus_ms'])
        response = [float(activity[:len(outputs[0])].mean()), float(activity[len(outputs[0]):output_count].mean())]
        dan_bins = result['trace'][:, dan_slice]
        summary = dict(
            applied=[float(x) for x in applied], recorded_applied=[float(x) for x in recorded_applied],
            clipped=bridge_evidence['clipped'] if bridge else int(rec['rule_bins'][:, :, 3:5].sum()),
            phases=({phase: dict(zip(group_labels, values)) for phase, values in bridge_evidence['phases'].items()} if bridge else
                    {phase: {group_labels[g]: {RULE_TERMS[t]: float(phases[phase][g, t]) for t in range(len(RULE_TERMS))}
                             for g in range(len(group_labels))} for phase in PHASES}),
            dan_signal={phase: {label: dict(mean_spikes=float(signal[phase][c, 0]), signal_after_reference=float(signal[phase][c, 2]))
                                for label, c in COMPARTMENT_OF.items()} for phase in PHASES},
            reference_per_step=[float(x) for x in rec['signal_bins'][-1, :, 3]],
            tonic_hz=[float(x) for x in result['compartment_tonic_hz']],
            dan_hz_stimulus=[float(dan_bins[:stimulus_bins, dcomp == c].sum() / np.count_nonzero(dcomp == c) * (1000 / protocol['stimulus_ms'])) for c in range(2)],
            dan_hz_post=[float(dan_bins[stimulus_bins:, dcomp == c].sum() / np.count_nonzero(dcomp == c) * (1000 / (protocol['duration_ms'] - protocol['stimulus_ms']))) for c in range(2)],
            kc_spikes={phase: float(kc_bins[:, 0][slice(*{'pre_onset': (0, 10), 'stimulus_plastic': (10, stimulus_bins), 'post_stimulus': (stimulus_bins, n_bins)}[phase])].sum()) for phase in PHASES},
            kc_active_fraction=float(np.count_nonzero(result['counts'][kc]) / len(kc)),
            mbon_response_hz=response,
            sensory_bins_sha256=hashlib.sha256(np.ascontiguousarray(result['trace'][:, sensory_slice]).tobytes()).hexdigest(),
            wall_seconds=float(result['wall_seconds']),
        )
        if bridge:
            summary.update({key: bridge_evidence[key] for key in
                            ('electrical_bound_observations', 'tail_bound_observations', 'bridge_totals')})
        return summary

    rows, retained, repeat_check, sensory_check = [], {}, {}, {}
    gain_deltas = {}
    fingerprints = {}
    replay_evidence = {}
    panel_games = selection['panel_games']
    total = len(panel_games) * 2 * len(CONDITIONS)
    done = 0
    for game in panel_games:
        for seed_set in ('base', 'alt'):
            seed = protocol['seed'] + args.seed_offset + game + (ALT_SEED_OFFSET if seed_set == 'alt' else 0)
            hashes = {}
            for condition in CONDITIONS:
                result = run(game, seed, condition, learn=condition != 'frozen')
                summary = summarize(result)
                hashes[condition] = summary['sensory_bins_sha256']
                rows.append(dict(game=game, seed_set=seed_set, seed=seed, condition=condition, **summary))
                key = f'{game}__{seed_set}__{condition}'
                gain_deltas[f'{game}/{seed_set}/{condition}'] = result['gain_delta'].copy()
                if bridge and game == panel_games[0] and seed_set == 'base':
                    fingerprints[condition] = numeric_fingerprint(result)
                rec = result['instrumentation']
                retained[f'{key}__gain_delta'] = result['gain_delta'].copy()
                if bridge:
                    retained[f'{key}__gains'] = result['gains'].copy()
                    retained[f'{key}__sensory_bins'] = result['trace'][:, sensory_slice].copy()
                    for name in ('bridge_rule', 'bridge_tail', 'bridge_signals', 'bridge_kc_bins', 'bridge_kc_used'):
                        retained[f'{key}__{name}'] = rec[name]
                else:
                    retained[f'{key}__rule_bins'] = rec['rule_bins']
                retained[f'{key}__signal_bins'] = rec['signal_bins']
                retained[f'{key}__kc_signal_bins'] = rec['kc_signal_bins']
                retained[f'{key}__dan_bins'] = result['trace'][:, dan_slice].copy()
                retained[f'{key}__step_signals'] = rec['step_signals']
                if not bridge:
                    retained[f'{key}__step_rule'] = rec['step_rule']
                if game == panel_games[0]:
                    if not bridge:
                        retained[f'{key}__kc_trace_bins'] = rec['kc_trace_bins']
                    retained[f'{key}__sampled_bins'] = result['trace'].copy()
                done += 1
            sensory_check[f'{game}/{seed_set}'] = len(set(hashes.values())) == 1
            print(f'[{run_id}] {done}/{total} game {game} {seed_set}: ' + ' '.join(
                f"{r['condition']}={r['applied'][0]:+.3f}/{r['applied'][1]:+.3f}" for r in rows[-4:]), flush=True)
    for condition in CONDITIONS:
        result = run(panel_games[0], protocol['seed'] + args.seed_offset + panel_games[0], condition, learn=condition != 'frozen')
        repeat_check[condition] = (numeric_fingerprint(result) == fingerprints[condition] if bridge else
                                  bool(np.array_equal(result['gains'] - blank, gain_deltas[f'{panel_games[0]}/base/{condition}'])))
        if bridge:
            replay_evidence[condition] = dict(original=fingerprints[condition], repeat=numeric_fingerprint(result))
    engine.gains[:] = blank
    trajectory, cumulative_rows = [], []
    for expected in selection['expected_cumulative']:
        game, seed = expected['game'], expected['seed']
        result = run(game, seed, 'untaught', learn=True, reset=False)
        cumulative_evidence = summarize(result)
        trajectory.append(compartment_sums(engine.gains - blank, pc, 2))
        cumulative_rows.append(dict(game=game, seed=seed,
                                    clipped=cumulative_evidence['clipped'], applied=[float(x) for x in compartment_sums(result['gain_delta'], pc, 2)],
                                    cumulative=[float(x) for x in trajectory[-1]]))
        if bridge:
            cumulative_rows[-1].update({key: cumulative_evidence[key] for key in
                ('electrical_bound_observations', 'tail_bound_observations', 'bridge_totals', 'phases')})
            retained[f'cumulative_{game}__gains'] = result['gains'].copy()
            for name in ('bridge_rule', 'bridge_tail', 'bridge_signals', 'bridge_kc_bins', 'bridge_kc_used'):
                retained[f'cumulative_{game}__{name}'] = result['instrumentation'][name]
    final_gains = engine.gains.copy()
    panel_complete = check_diagnostic_complete(rows, cumulative_rows, selection)
    panel = evaluate_panel([dict(game=r['game'], seed_set=r['seed_set'], condition=r['condition'], applied=r['applied'], clipped=r['clipped']) for r in rows],
                           expected_games=panel_games)
    code_after = code_hashes()
    try:
        graph_unchanged = verify_graph_inputs(ROOT, manifest['identity']) == graph_hashes
    except ValueError:
        graph_unchanged = False
    source_unchanged = (code_after == code and file_hash(engine.lib._name) == native_binary['sha256']
                        and graph_unchanged and file_hash(manifest_path) == identity['pilot_manifest_sha256']
                        and file_hash(args.pilot / 'source/inputs.npz') == identity['inputs_sha256']
                        and file_hash(args.pilot / 'source/protocol.json') == identity['pilot_protocol_sha256'])
    if bridge:
        source_unchanged = source_unchanged and bridge_contract_identity() == identity['bridge_contract']
    cumulative = evaluate_cumulative(np.array(trajectory), mean_effect=np.array(panel['mean_effect_by_compartment']),
                                     expected_trials=len(selection['expected_cumulative']))
    criteria = dict(panel['criteria'], cumulative=cumulative,
                    bit_identical_repeat=dict(passed=all(repeat_check.values()), by_condition=repeat_check),
                    sensory_noise_invariance=dict(passed=all(sensory_check.values()), by_trial=sensory_check))
    criteria['no_bound_hits'] = evaluate_bound_hits(rows, cumulative_rows, final_gains,
                                                   gain_bounds=protocol['gain_bounds'], plastic_mask=engine.plastic_mask)
    if not panel_complete:
        for value in criteria.values():
            value['passed'] = False
            value['note'] = 'INCOMPLETE debug panel; not a gate result'
    summary = dict(run_id=run_id, rule=args.rule, created_at=utcnow(), identity=identity, root=str(ROOT),
                   native_binary=native_binary, source_unchanged_during_run=source_unchanged,
                   panel_complete=panel_complete, panel_kind=selection['panel_kind'],
                   panel_note=(f"{selection['panel_kind']} v1.1 panel: 8 games x 2 seed sets x 4 conditions + 16-trial cumulative" if panel_complete
                               else 'INCOMPLETE debug panel; not a gate result'),
                   anatomy=dict(plastic_edges=int(len(pc)), group_labels=group_labels, group_edges=group_edges,
                                plasticity_mask=anatomy.get('plasticity_mask'), eligible_edges=int(engine.plastic_mask.sum()),
                                dan_populations=[int(np.count_nonzero(dcomp == c)) for c in range(2)],
                                compartments=[dict(label=c['label'], dan_type=c['dan_type'], mbon_type=c['mbon_type']) for c in anatomy['compartments']]),
                   panel_games=panel_games, rows=rows, effects=panel['rows'], criteria=criteria,
                   all_passed=panel_complete and source_unchanged and all(v['passed'] for v in criteria.values()),
                   cumulative_rows=cumulative_rows, wall_seconds=time.time() - started)
    np.savez(out / 'trials.npz', **retained, cumulative_final_gains=final_gains, blank_gains=blank,
             plastic_compartments=pc, plastic_kc_indices=pk, plastic_groups=groups, kc_classes=classes,
             plastic_mask=engine.plastic_mask.copy(), dan_compartments=dcomp, sampled=sampled)
    if bridge:
        rec = result['instrumentation']
        atomic_json(out / 'recording-layout.json', dict(layout=rec['layout'], config=rec['config'],
            layout_version=rec['layout_version'], learning_rule=engine.learning_rule,
            group_labels=group_labels, group_compartments=(np.arange(len(group_labels)) // len(KC_CLASSES)).tolist()))
        atomic_json(out / 'replay-evidence.json', replay_evidence)
        summary['artifacts'] = {name: dict(sha256=file_hash(out / name), bytes=(out / name).stat().st_size)
                                for name in ('trials.npz', 'recording-layout.json', 'replay-evidence.json')}
    atomic_json(out / 'summary.json', summary)
    if args.evidence:
        args.evidence.mkdir(parents=True, exist_ok=True)
        atomic_json(args.evidence / f'panel-{run_id}.json', summary)
    print(json.dumps({k: v['passed'] for k, v in criteria.items()}, indent=1))
    print(f'[{run_id}] done in {summary["wall_seconds"]:.0f}s -> {out}', flush=True)
    return 0 if summary['all_passed'] else 3


if __name__ == '__main__':
    sys.exit(main())
