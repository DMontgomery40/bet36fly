"""Freeze the associative sports candidate after development, before the reserved 2018 block is touched.

Selects the learning rate by development log loss of the plastic arm (declared candidate budget),
copies every arm readout fitted on 2022 into configs/associative-candidate-01.json and writes the
one-shot confirmation protocol. Refuses to overwrite an existing candidate or confirmation protocol.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bet36fly.connectome import ROOT  # noqa: E402


def main(evaluations, protocol='configs/associative-sports-01.json', root=ROOT):
    protocol_path = root / protocol
    dev_protocol = json.loads(protocol_path.read_text())
    payloads = []
    for identity in evaluations:
        payload = json.loads((root / 'output/associative' / identity / 'evaluation.json').read_text())
        if payload['identity'] != identity or payload['season'] != dev_protocol['season']:
            raise ValueError('Evaluation identity/season mismatch.')
        if payload['learning_rate'] not in dev_protocol['learning_rate_candidates']:
            raise ValueError('Learning rate outside the declared candidate budget.')
        payloads.append(payload)
    if len({p['learning_rate'] for p in payloads}) != len(payloads):
        raise ValueError('Duplicate learning rate among evaluations.')
    selected = min(payloads, key=lambda p: (p['evaluation']['metrics']['plastic']['log_loss'], p['learning_rate']))
    candidate = dict(schema=1, label='associative-candidate-01', development_protocol=protocol,
                     development_evaluation=selected['identity'], learning_rate=selected['learning_rate'],
                     considered={p['identity']: dict(learning_rate=p['learning_rate'],
                                                     plastic_development_log_loss=p['evaluation']['metrics']['plastic']['log_loss'],
                                                     plasticity_contributes=p['evaluation']['plasticity_contributes'])
                                 for p in payloads},
                     readouts=selected['readouts'], arms=selected['arms'],
                     circuit_sha256=hashlib.sha256((root / dev_protocol['circuit']).read_bytes()).hexdigest(),
                     development_metrics=selected['evaluation']['metrics'],
                     development_paired_loss=selected['evaluation']['paired_loss'],
                     development_plasticity_contributes=selected['evaluation']['plasticity_contributes'],
                     interpretation='Selected on 2022 development data only; readouts fitted on games before the 2022 split '
                                    'and never refitted. Only the reserved 2018 block can confirm.')
    candidate_path = root / 'configs/associative-candidate-01.json'
    confirmation_path = root / 'configs/associative-confirmation-01.json'
    if candidate_path.exists() or confirmation_path.exists():
        raise ValueError('Candidate or confirmation protocol already frozen; never overwrite.')
    candidate_path.write_text(json.dumps(candidate, indent=2) + '\n')
    confirmation = dict(schema=1, label='associative-2018-confirmation-attempt-01', attempt=1, season=2018,
                        frozen_candidate='configs/associative-candidate-01.json',
                        frozen_candidate_sha256=hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
                        alpha=0.025, replicates=10000,
                        stopping='One source retrieval of the 2018 MLB regular season and one evaluation of the frozen candidate. '
                                 'No refit, candidate change or adaptive reuse. Preserve a failed confirmation.',
                        never_accessed_by=['encoder training (2019-2021)', 'sensory development (2022)',
                                           'sensory confirmation (2023)', 'v1/v2 datasets (2024-2026)'])
    confirmation_path.write_text(json.dumps(confirmation, indent=2) + '\n')
    print(json.dumps(dict(selected=selected['identity'], learning_rate=selected['learning_rate'],
                          candidate_sha256=confirmation['frozen_candidate_sha256']), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evaluations', nargs='+')
    parser.add_argument('--protocol', default='configs/associative-sports-01.json')
    args = parser.parse_args()
    main(args.evaluations, args.protocol)
