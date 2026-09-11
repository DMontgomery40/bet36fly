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
    COMPARTMENT_OF, PHASES, compartment_sums, evaluate_cumulative, evaluate_panel, phase_sums,
)
from bet36fly.reward_protocol import file_hash, make_circuit  # noqa: E402

PILOT = '/Users/davidmontgomery/Documents/ChatGPT/bet36fly/output/experiments/reward-v3-209f7c49983f5873f650'
KC_CLASSES = ('gamma', 'apbp', 'ab', 'other')
CONDITIONS = ('frozen', 'untaught', 'home', 'away')
ALT_SEED_OFFSET = 1_000_000
RULE_TERMS = ('term_dbar_k', 'term_kbar_d', 'applied', 'clipped_low', 'clipped_high', 'kc_events', 'kbar_mass_end')


def kc_class(type_name):
    name = str(type_name)
    if name.startswith("KCa'b'"):
        return 'apbp'
    if name.startswith('KCg'):
        return 'gamma'
    if name.startswith('KCab'):
        return 'ab'
    return 'other'


def rule_protocol(protocol, rule):
    if rule == 'legacy':
        return dict(protocol)
    if rule == 'candidate':
        if 'dan_reference' not in inspect.signature(RewardEngine.__init__).parameters:
            raise SystemExit('The candidate rule is not implemented in this revision; refusing to mislabel a legacy run.')
        return dict(protocol, dan_reference='none')
    raise SystemExit(f'Unknown rule {rule}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rule', choices=('legacy', 'candidate'), required=True)
    parser.add_argument('--pilot', type=Path, default=Path(PILOT))
    parser.add_argument('--games', type=int, default=8)
    parser.add_argument('--cumulative-games', type=int, default=16)
    parser.add_argument('--out', type=Path, default=ROOT / 'output/diagnostics')
    parser.add_argument('--evidence', type=Path, default=None, help='directory to receive a copy of summary.json')
    parser.add_argument('--cancel-file', type=Path, default=None)
    args = parser.parse_args()

    started = time.time()
    base_protocol = json.loads((args.pilot / 'source/protocol.json').read_text())
    protocol = rule_protocol(base_protocol, args.rule)
    inputs = np.load(args.pilot / 'source/inputs.npz', allow_pickle=False)
    X, src, cal = inputs['X'], inputs['source_indices'], inputs['calibration_indices']
    mean, std = inputs['input_mean'], inputs['input_std']
    code = {name: file_hash(Path(__file__).resolve().parents[1] / 'bet36fly' / name)
            for name in ('reward_lif.cpp', 'reward_brain.py', 'reward_protocol.py', 'reward_encoder.py', 'reward_diagnostic.py')}
    code['reward_teaching_diagnostic.py'] = file_hash(Path(__file__).resolve())
    identity = dict(rule=args.rule, protocol=protocol, pilot=args.pilot.name, games=args.games,
                    cumulative_games=args.cumulative_games, alt_seed_offset=ALT_SEED_OFFSET, code_hashes=code,
                    inputs_sha256=file_hash(args.pilot / 'source/inputs.npz'))
    run_id = f'diag-{args.rule}-' + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:12]
    out = args.out / run_id
    if out.exists():
        raise SystemExit(f'{out} exists; a changed input or code produces a new identity, reruns are not repeated.')
    out.mkdir(parents=True)
    print(f'[{run_id}] building circuit', flush=True)
    engine, anatomy, outputs, dcomp, kc, sensory, encode = make_circuit(ROOT, protocol, n_features=X.shape[1])
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
        phases = phase_sums(rec['rule_bins'], bin_ms=protocol['bin_ms'], onset_ms=protocol['plasticity_onset_ms'],
                            stimulus_ms=protocol['stimulus_ms'])
        signal = phase_sums(rec['signal_bins'], bin_ms=protocol['bin_ms'], onset_ms=protocol['plasticity_onset_ms'],
                            stimulus_ms=protocol['stimulus_ms'])
        kc_bins = rec['kc_signal_bins']
        applied = compartment_sums(result['gain_delta'], pc, 2)
        recorded_applied = np.array([rec['rule_bins'][:, [g for g in range(len(group_labels)) if g // len(KC_CLASSES) == c], 2].sum()
                                     for c in range(2)])
        if not np.allclose(applied, recorded_applied, atol=1e-3):
            raise RuntimeError(f'Recorded applied {recorded_applied} disagrees with gain delta {applied}.')
        activity = result['trace'][:stimulus_bins].sum(0) * (1000 / protocol['stimulus_ms'])
        response = [float(activity[:len(outputs[0])].mean()), float(activity[len(outputs[0]):output_count].mean())]
        dan_bins = result['trace'][:, dan_slice]
        return dict(
            applied=[float(x) for x in applied], recorded_applied=[float(x) for x in recorded_applied],
            clipped=int(rec['rule_bins'][:, :, 3:5].sum()),
            phases={phase: {group_labels[g]: {RULE_TERMS[t]: float(phases[phase][g, t]) for t in range(len(RULE_TERMS))}
                            for g in range(len(group_labels))} for phase in PHASES},
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

    rows, gain_deltas, repeat_check, sensory_check = [], {}, {}, {}
    panel_games = [int(i) for i in cal[:args.games]]
    total = len(panel_games) * 2 * len(CONDITIONS)
    done = 0
    for game in panel_games:
        for seed_set in ('base', 'alt'):
            seed = protocol['seed'] + game + (ALT_SEED_OFFSET if seed_set == 'alt' else 0)
            hashes = {}
            for condition in CONDITIONS:
                result = run(game, seed, condition, learn=condition != 'frozen')
                summary = summarize(result)
                hashes[condition] = summary['sensory_bins_sha256']
                rows.append(dict(game=game, seed_set=seed_set, seed=seed, condition=condition, **summary))
                gain_deltas[f'{game}/{seed_set}/{condition}'] = result['gain_delta'].copy()
                done += 1
            sensory_check[f'{game}/{seed_set}'] = len(set(hashes.values())) == 1
            print(f'[{run_id}] {done}/{total} game {game} {seed_set}: ' + ' '.join(
                f"{r['condition']}={r['applied'][0]:+.3f}/{r['applied'][1]:+.3f}" for r in rows[-4:]), flush=True)
    for condition in CONDITIONS:
        result = run(panel_games[0], protocol['seed'] + panel_games[0], condition, learn=condition != 'frozen')
        repeat_check[condition] = bool(np.array_equal(result['gains'] - blank, gain_deltas[f'{panel_games[0]}/base/{condition}']))
    engine.gains[:] = blank
    trajectory, cumulative_rows = [], []
    for game in [int(i) for i in cal[:args.cumulative_games]]:
        result = run(game, protocol['seed'] + game, 'untaught', learn=True, reset=False)
        trajectory.append(compartment_sums(engine.gains - blank, pc, 2))
        cumulative_rows.append(dict(game=game, applied=[float(x) for x in compartment_sums(result['gain_delta'], pc, 2)],
                                    cumulative=[float(x) for x in trajectory[-1]]))
    final_gains = engine.gains.copy()
    panel = evaluate_panel([dict(game=r['game'], seed_set=r['seed_set'], condition=r['condition'], applied=r['applied'], clipped=r['clipped']) for r in rows])
    cumulative = evaluate_cumulative(np.array(trajectory), mean_effect=np.array(panel['mean_effect_by_compartment']))
    criteria = dict(panel['criteria'], cumulative=cumulative,
                    bit_identical_repeat=dict(passed=all(repeat_check.values()), by_condition=repeat_check),
                    sensory_noise_invariance=dict(passed=all(sensory_check.values()), by_trial=sensory_check))
    summary = dict(run_id=run_id, rule=args.rule, created_at=utcnow(), identity=identity, root=str(ROOT),
                   anatomy=dict(plastic_edges=int(len(pc)), group_labels=group_labels, group_edges=group_edges,
                                dan_populations=[int(np.count_nonzero(dcomp == c)) for c in range(2)],
                                compartments=[dict(label=c['label'], dan_type=c['dan_type'], mbon_type=c['mbon_type']) for c in anatomy['compartments']]),
                   panel_games=panel_games, rows=rows, effects=panel['rows'], criteria=criteria,
                   all_passed=all(v['passed'] for v in criteria.values()),
                   cumulative_rows=cumulative_rows, wall_seconds=time.time() - started)
    np.savez(out / 'trials.npz', **{k.replace('/', '__'): v for k, v in gain_deltas.items()},
             cumulative_final_gains=final_gains, blank_gains=blank, plastic_compartments=pc, plastic_groups=groups)
    atomic_json(out / 'summary.json', summary)
    if args.evidence:
        args.evidence.mkdir(parents=True, exist_ok=True)
        atomic_json(args.evidence / f'panel-{run_id}.json', summary)
    print(json.dumps({k: v['passed'] for k, v in criteria.items()}, indent=1))
    print(f'[{run_id}] done in {summary["wall_seconds"]:.0f}s -> {out}', flush=True)
    return 0 if summary['all_passed'] else 3


if __name__ == '__main__':
    sys.exit(main())
