"""One-shot associative confirmation on the reserved 2018 MLB season.

Preconditions (checked, never bypassed): the frozen candidate file names the selected learning
rate and the development evaluation identity; the readout for every arm was fitted on the 2022
development season and is reused unchanged; the 2018 source is fetched here for the first time.
Three arms run chronologically through 2018 (plastic, frozen, shuffled); the frozen readouts are
applied; the paired evaluation uses the whole season. Never rerun with a changed candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly import associative_sports as sp  # noqa: E402
from bet36fly.associative import build_circuit  # noqa: E402
from bet36fly.connectome import ROOT, digest  # noqa: E402
from bet36fly.associative import atomic_json  # noqa: E402
from bet36fly.sensory_backtest import encoder_probability, paired_evaluation, readout_probability  # noqa: E402
from bet36fly.sensory_data import normalize_season  # noqa: E402
from scipy.special import expit  # noqa: E402


def run(protocol_path, root=ROOT):
    raw = protocol_path.read_bytes()
    protocol = json.loads(raw)
    identity = 'associative-confirmation-' + hashlib.sha256(raw).hexdigest()[:20]
    out = root / 'output/associative' / identity
    if out.exists():
        raise ValueError('Refusing an existing confirmation identity; outcomes may already be exposed.')
    if protocol['attempt'] != 1 or protocol['season'] != 2018:
        raise ValueError('Unsupported confirmation allocation; never reuse the reserved block.')
    frozen = json.loads((root / protocol['frozen_candidate']).read_text())
    if hashlib.sha256((root / protocol['frozen_candidate']).read_bytes()).hexdigest() != protocol['frozen_candidate_sha256']:
        raise ValueError('Frozen associative candidate changed.')
    dev_protocol = json.loads((root / frozen['development_protocol']).read_text())
    circuit_protocol = json.loads((root / dev_protocol['circuit']).read_text())
    if hashlib.sha256((root / dev_protocol['circuit']).read_bytes()).hexdigest() != frozen['circuit_sha256']:
        raise ValueError('Circuit protocol changed since the candidate was frozen.')
    candidate = sp.load_candidate(root, dev_protocol)
    out.mkdir(parents=True)
    (out / 'protocol.json').write_bytes(raw)
    manifest = dict(identity=identity, status='preregistered', attempt=1, season=2018, created_at=datetime.now(timezone.utc).isoformat(),
                    frozen_candidate_sha256=protocol['frozen_candidate_sha256'], source_accessed=False, new_fits=0)
    atomic_json(out / 'manifest.json', manifest)
    try:
        url = 'https://statsapi.mlb.com/api/v1/schedule?sportId=1&gameType=R&season=2018'
        manifest.update(status='fetching_source', source_url=url, source_accessed=True)
        atomic_json(out / 'manifest.json', manifest)
        with urllib.request.urlopen(url, timeout=60) as response:
            source = response.read()
        (out / 'source-2018.json').write_bytes(source)
        manifest.update(status='source_retrieved', source_sha256=hashlib.sha256(source).hexdigest(),
                        source_fetched_at=datetime.now(timezone.utc).isoformat())
        atomic_json(out / 'manifest.json', manifest)
        games, exclusions = normalize_season(json.loads(source), 2018)
        if len(games) < 2000:
            raise ValueError('Insufficient eligible confirmation sample.')
        rows, x, y = sp.season_rows(games, 2018)
        innate = sp.innate_features(x, candidate)
        labels = np.where(y == 0, 1, 2)
        yy = (y == 0).astype(int)
        dates = [g['start_time'] for g in rows]
        arms = {}
        arm_records = {}
        baseline_protocol = json.loads((root / dev_protocol['baseline_protocol']).read_text()) if 'baseline_protocol' in dev_protocol else None
        baseline_circuit = json.loads((root / baseline_protocol['circuit']).read_text()) if baseline_protocol else None
        arm_names = ('plastic', 'frozen', 'shuffled') + (('plastic:baseline',) if baseline_circuit else ())
        for arm in arm_names:
            kind = arm.split(':')[0]
            circuit_spec = baseline_circuit if arm == 'plastic:baseline' else circuit_protocol
            circuit = build_circuit(root, circuit_spec)
            permutation = sp.within_week_permutation(dates, dev_protocol['shuffle_seed']) if kind == 'shuffled' else None
            learner = sp.SeasonLearner(circuit, circuit_spec, arm=kind, games=rows, features=x, innate=innate,
                                       outcomes=labels, week_permutation=permutation, out_dir=out / arm.replace(':', '-'),
                                       learning_rate=frozen['learning_rate'] if kind != 'frozen' else None)
            learner.run()
            atomic_json(out / arm.replace(':', '-') / 'rows.json', learner.rows)
            arms[arm] = np.array([r['innate'] + r['learned'] for r in learner.rows], float)
            arm_records[arm] = dict(calls=learner.calls, reinforcements=learner.reinforcements,
                                    final_gains_sha256=learner.engine.gains_sha256(), days=len(learner.days),
                                    bound_contacts=float(sum(d['bound_contacts'] for d in learner.days)))
            manifest['arms'] = arm_records
            atomic_json(out / 'manifest.json', manifest)
        predictions = {name: readout_probability(z, frozen['readouts'][name]) for name, z in arms.items()}
        predictions['encoder_only'] = encoder_probability(x, candidate['encoder'])
        wins = sp.delayed_cumulative_wins(rows, y)
        home, away = sp.team_vectors(x)
        delta = np.concatenate([home - away, (wins[:, :1] - wins[:, 1:]) / 10.0], axis=1)
        same = frozen['readouts']['same_information']
        predictions['same_information'] = expit(delta / np.asarray(same['scales']) @ np.asarray(same['coef']) + same['intercept'])
        predictions['uniform'] = np.full(len(yy), 0.5)
        predictions['prior'] = np.full(len(yy), float(candidate['training_prior']))
        subset = dict(predictions, neural=predictions['plastic'])
        evaluation = paired_evaluation(yy, subset, dates, 10000, 0.025)
        evaluation['metrics'].pop('neural', None)
        evaluation['paired_loss'].pop('plastic', None)
        control = dict(subset, neural=predictions['shuffled'])
        evaluation['shuffled_minus_frozen'] = paired_evaluation(yy, control, dates, 10000, 0.025)['paired_loss']['frozen']
        evaluation['plasticity_contributes'] = bool(evaluation['paired_loss']['frozen']['interval'][1] < 0
                                                     and evaluation['shuffled_minus_frozen']['interval'][1] >= 0)
        if 'plastic:baseline' in predictions:
            evaluation['recovery_minus_baseline'] = evaluation['paired_loss'].get('plastic:baseline')
            baseline = dict(subset, neural=predictions['plastic:baseline'])
            evaluation['baseline_minus_frozen'] = paired_evaluation(yy, baseline, dates, 10000, 0.025)['paired_loss']['frozen']
        evaluation.update(exclusions=exclusions, start=dates[0], end=dates[-1],
                          interpretation='Reserved-block confirmation of the frozen associative candidate with readouts fitted on '
                                         '2022 only; plasticity contributes only if plastic beats its matched frozen twin '
                                         'while the reinforcement-shuffled twin does not.')
        with (out / 'predictions.csv').open('w') as f:
            names = list(predictions)
            f.write(','.join(['game_id', 'start_time', 'home', 'away', 'home_win'] + names) + '\n')
            for i, g in enumerate(rows):
                f.write(','.join([g['id'], g['start_time'], g['home'], g['away'], str(int(yy[i]))]
                                 + [repr(float(predictions[n][i])) for n in names]) + '\n')
        atomic_json(out / 'evaluation.json', evaluation)
        manifest.update(status='passed_confirmation' if evaluation['plasticity_contributes'] else 'failed_confirmation',
                        evaluation=evaluation, better_than_chance=evaluation['goal_passed'],
                        artifact_sha256={p.name: digest(p) for p in out.iterdir() if p.is_file() and p.name != 'manifest.json'})
        print(json.dumps({k: evaluation[k] for k in ('metrics', 'paired_loss', 'shuffled_minus_frozen', 'accuracy_interval',
                                                     'plasticity_contributes', 'goal_passed')}, indent=2))
    except Exception as exc:
        manifest.update(status='failed_runtime', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        atomic_json(out / 'manifest.json', manifest)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, default=ROOT / 'configs/associative-confirmation-01.json')
    run(parser.parse_args().protocol)
