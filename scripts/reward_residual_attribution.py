"""Attribute the untaught gain change of a diagnostic panel to recorded rule terms, bin by bin.

Reads the retained per-bin arrays of one panel run (scripts/reward_teaching_diagnostic.py) and
reports, for the untaught condition of every game and seed set: the two signed rule terms per bin,
the split into onset-adjacent and steady stimulus bins and the post-offset window, the KC/DAN lag
cross-correlation at bin resolution, and a per-bin prediction of the post-offset -Kbar*D term from
the recorded eligibility mass and DAN signal. Read-only; writes attribution.json next to the run.

    .venv/bin/python scripts/reward_residual_attribution.py output/diagnostics/<run>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bet36fly.experiment import atomic_json  # noqa: E402

KC_CLASSES = ('gamma', 'apbp', 'ab', 'other')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--evidence', type=Path, default=None)
    parser.add_argument('--onset-bins', type=int, default=3, help='stimulus bins after onset counted as onset-adjacent')
    args = parser.parse_args()
    summary = json.loads((args.run / 'summary.json').read_text())
    protocol = summary['identity']['protocol']
    z = np.load(args.run / 'trials.npz')
    bin_ms = protocol['bin_ms']
    onset = int(round(protocol['plasticity_onset_ms'] / bin_ms))
    offset = int(round(protocol['stimulus_ms'] / bin_ms))
    eta = protocol['learning_rate']
    labels = summary['anatomy']['group_labels']
    home = [g for g, label in enumerate(labels) if label.startswith('home')]
    keys = sorted({k.rsplit('__', 1)[0] for k in z.files if k.endswith('__rule_bins')})
    untaught = [k for k in keys if k.endswith('__untaught')]
    per_bin_terms, lag_xcorr, post_pred, rows = [], [], [], []
    for key in untaught:
        rule = z[f'{key}__rule_bins']            # [bins, groups, 7]
        signal = z[f'{key}__signal_bins']        # [bins, compartments, 4]
        kcsig = z[f'{key}__kc_signal_bins']      # [bins, 2]
        dbar_k = rule[:, home, 0].sum(1)
        kbar_d = rule[:, home, 1].sum(1)
        applied = rule[:, home, 2].sum(1)
        kbar_mass = rule[:, home, 6].sum(1)      # eligibility mass on home edges at bin end
        d_home = signal[:, 0, 0]                 # compartment-mean DAN spikes per bin
        per_bin_terms.append(np.stack([dbar_k, kbar_d, applied], 1))
        # Prediction of the post-offset -Kbar*D term from bin-resolution recordings (mass at bin end
        # times DAN events in the next bin; exact within-bin timing is not recoverable at 10 ms).
        pred = -eta * (kbar_mass[offset - 1:-1] * d_home[offset:]).sum()
        post_pred.append((float(pred), float(kbar_d[offset:].sum())))
        # Lag cross-correlation between KC spikes and home DAN spikes across the plastic stimulus bins.
        k = kcsig[onset:offset, 0] - kcsig[onset:offset, 0].mean()
        d = d_home[onset:offset] - d_home[onset:offset].mean()
        lags = range(-4, 5)
        xc = []
        for lag in lags:
            if lag >= 0:
                a, b = k[:len(k) - lag], d[lag:]
            else:
                a, b = k[-lag:], d[:len(d) + lag]
            denom = np.sqrt((a * a).sum() * (b * b).sum())
            xc.append(float((a * b).sum() / denom) if denom > 0 else 0.0)
        lag_xcorr.append(xc)
        rows.append(dict(key=key, stimulus_onset_adjacent=float(applied[onset:onset + args.onset_bins].sum()),
                         stimulus_steady=float(applied[onset + args.onset_bins:offset].sum()),
                         post_offset=float(applied[offset:].sum()),
                         dan_spikes_post_per_cell=float(d_home[offset:].sum()),
                         kbar_mass_at_offset=float(kbar_mass[offset - 1])))
    terms = np.mean(per_bin_terms, 0)
    xcorr = np.mean(lag_xcorr, 0)
    report = dict(
        run_id=summary['run_id'], rule=summary['rule'], trials=len(untaught), onset_bin=onset, offset_bin=offset,
        mean_applied_by_phase=dict(
            onset_adjacent=float(np.mean([r['stimulus_onset_adjacent'] for r in rows])),
            stimulus_steady=float(np.mean([r['stimulus_steady'] for r in rows])),
            post_offset=float(np.mean([r['post_offset'] for r in rows]))),
        sd_applied_by_phase=dict(
            onset_adjacent=float(np.std([r['stimulus_onset_adjacent'] for r in rows], ddof=1)),
            stimulus_steady=float(np.std([r['stimulus_steady'] for r in rows], ddof=1)),
            post_offset=float(np.std([r['post_offset'] for r in rows], ddof=1))),
        per_bin_mean_terms=[dict(bin=b, ms=b * bin_ms, dbar_k=float(terms[b, 0]), kbar_d=float(terms[b, 1]), applied=float(terms[b, 2]))
                            for b in range(terms.shape[0])],
        post_offset_kbar_d_prediction=dict(
            note='-eta * sum(Kbar mass at bin end * DAN events next bin) over the post window vs recorded -Kbar*D term',
            predicted_mean=float(np.mean([p for p, _ in post_pred])), recorded_mean=float(np.mean([r for _, r in post_pred])),
            per_trial=[dict(predicted=p, recorded=r) for p, r in post_pred]),
        kc_dan_lag_xcorr=dict(note='Pearson correlation of per-bin KC spikes with home-DAN spikes at lag (positive lag = DAN after KC), 10 ms bins, stimulus-plastic window',
                              lags_bins=list(range(-4, 5)), mean=[float(x) for x in xcorr],
                              per_trial=[[float(x) for x in xc] for xc in lag_xcorr]),
        rows=rows)
    atomic_json(args.run / 'attribution.json', report)
    if args.evidence:
        atomic_json(args.evidence / f'attribution-{summary["run_id"]}.json', report)
    print(json.dumps({k: report[k] for k in ('run_id', 'mean_applied_by_phase', 'sd_applied_by_phase')}, indent=1))
    print('post-offset KbarD predicted/recorded', report['post_offset_kbar_d_prediction']['predicted_mean'], report['post_offset_kbar_d_prediction']['recorded_mean'])
    print('lag xcorr (lags -4..4 bins):', [round(x, 3) for x in xcorr])
    print('per-bin mean terms (bin, DbarK, KbarD, applied):')
    for t in report['per_bin_mean_terms']:
        if 8 <= t['bin'] <= 40:
            print(f"  {t['bin']:2d} {t['dbar_k']:+.4f} {t['kbar_d']:+.4f} {t['applied']:+.4f}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
