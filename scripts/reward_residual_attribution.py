"""Attribute the untaught gain change of a diagnostic panel to recorded rule terms.

Reads the retained arrays of one panel run (scripts/reward_teaching_diagnostic.py) and reports,
for the untaught condition of every game and seed set:

- per-bin signed rule terms and their split into onset-adjacent, steady-stimulus and post-offset
  windows (10 ms bins);
- when per-step arrays are present: the exact per-step decomposition of the summed home update,
  eta * (Dbar_used * impulses - mass_used * D), its split by 0.2 ms phases, a normalized
  cross-correlation profile between eligible-edge KC impulses and home-DAN events at +/-20 ms,
  and descriptive surrogates that keep the KC side fixed and alter only the DAN time series
  (circular shifts within the plastic stimulus window, event jitter, time reversal). The
  surrogates are sensitivity descriptions, not causal proof and not acceptance rules.

Read-only; writes attribution.json next to the run and optionally a copy into an evidence directory.

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


def pearson_at_lags(a, b, lags):
    out = []
    for lag in lags:
        if lag >= 0:
            x, y = a[:len(a) - lag] if lag else a, b[lag:]
        else:
            x, y = a[-lag:], b[:len(b) + lag]
        x, y = x - x.mean(), y - y.mean()
        denom = np.sqrt((x * x).sum() * (y * y).sum())
        out.append(float((x * y).sum() / denom) if denom > 0 else 0.0)
    return out


def dbar_from(d, *, onset, decay):
    """Dbar as used at each step: zero through the onset, then decay * (previous used + previous D)."""
    used = np.zeros_like(d)
    for t in range(onset + 1, len(d)):
        used[t] = decay * (used[t - 1] + d[t - 1])
    return used


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--evidence', type=Path, default=None)
    parser.add_argument('--onset-bins', type=int, default=3)
    parser.add_argument('--jitter-realizations', type=int, default=20)
    args = parser.parse_args()
    summary = json.loads((args.run / 'summary.json').read_text())
    protocol = summary['identity']['protocol']
    z = np.load(args.run / 'trials.npz')
    bin_ms, dt = protocol['bin_ms'], 0.2
    onset_bin, offset_bin = int(round(protocol['plasticity_onset_ms'] / bin_ms)), int(round(protocol['stimulus_ms'] / bin_ms))
    onset_step, offset_step = int(round(protocol['plasticity_onset_ms'] / dt)), int(round(protocol['stimulus_ms'] / dt))
    eta, decay = protocol['learning_rate'], float(np.exp(-dt / protocol['tau_ms']))
    labels = summary['anatomy']['group_labels']
    home = [g for g, label in enumerate(labels) if label.startswith('home')]
    untaught = sorted({k.rsplit('__', 1)[0] for k in z.files if k.endswith('__rule_bins')})
    untaught = [k for k in untaught if k.endswith('__untaught')]
    has_steps = all(f'{k}__step_rule' in z.files for k in untaught)

    per_bin_terms, lag_xcorr_bins, post_pred, rows = [], [], [], []
    for key in untaught:
        rule, signal, kcsig = z[f'{key}__rule_bins'], z[f'{key}__signal_bins'], z[f'{key}__kc_signal_bins']
        dbar_k, kbar_d, applied, kbar_mass = (rule[:, home, i].sum(1) for i in (0, 1, 2, 6))
        d_home = signal[:, 0, 0]
        per_bin_terms.append(np.stack([dbar_k, kbar_d, applied], 1))
        post_pred.append((float(-eta * (kbar_mass[offset_bin - 1:-1] * d_home[offset_bin:]).sum()), float(kbar_d[offset_bin:].sum())))
        lag_xcorr_bins.append(pearson_at_lags(kcsig[onset_bin:offset_bin, 0], d_home[onset_bin:offset_bin], range(-4, 5)))
        rows.append(dict(key=key, stimulus_onset_adjacent=float(applied[onset_bin:onset_bin + args.onset_bins].sum()),
                         stimulus_steady=float(applied[onset_bin + args.onset_bins:offset_bin].sum()),
                         post_offset=float(applied[offset_bin:].sum()), applied_total=float(applied.sum()),
                         dan_spikes_post_per_cell=float(d_home[offset_bin:].sum()), kbar_mass_at_offset=float(kbar_mass[offset_bin - 1])))
    terms = np.mean(per_bin_terms, 0)
    report = dict(
        run_id=summary['run_id'], rule=summary['rule'], trials=len(untaught), onset_bin=onset_bin, offset_bin=offset_bin,
        mean_applied_by_phase={k: float(np.mean([r[k] for r in rows])) for k in ('stimulus_onset_adjacent', 'stimulus_steady', 'post_offset', 'applied_total')},
        sd_applied_by_phase={k: float(np.std([r[k] for r in rows], ddof=1)) for k in ('stimulus_onset_adjacent', 'stimulus_steady', 'post_offset', 'applied_total')},
        per_bin_mean_terms=[dict(bin=b, ms=b * bin_ms, dbar_k=float(terms[b, 0]), kbar_d=float(terms[b, 1]), applied=float(terms[b, 2])) for b in range(terms.shape[0])],
        post_offset_kbar_d_prediction=dict(
            note='-eta * sum(Kbar mass at bin end * DAN events next bin) over the post window vs the recorded -Kbar*D term (10 ms bins)',
            predicted_mean=float(np.mean([p for p, _ in post_pred])), recorded_mean=float(np.mean([r for _, r in post_pred]))),
        kc_dan_lag_xcorr_bins=dict(note='normalized cross-correlation (Pearson on each overlap) of per-bin KC spikes with home-DAN spikes; positive lag = DAN after KC; 10 ms bins, stimulus-plastic window',
                                   lags_bins=list(range(-4, 5)), mean=[float(x) for x in np.mean(lag_xcorr_bins, 0)]),
        rows=rows)

    if has_steps:
        rng = np.random.default_rng(2026)
        lags = list(range(-100, 101, 5))
        step_rows, profiles, surrogates = [], [], {name: [] for name in ('actual', 'shift_-5ms', 'shift_+5ms', 'shift_-20ms', 'shift_+20ms', 'reverse', 'jitter_5ms')}
        max_dbar_err = 0.0
        for key in untaught:
            S, R = z[f'{key}__step_signals'].astype(np.float64), z[f'{key}__step_rule'].astype(np.float64)
            n_comp = (S.shape[1] - 1) // 2
            D, Dbar = S[:, 1], S[:, 1 + n_comp]
            E, M = R[:, home, 0].sum(1), R[:, home, 1].sum(1)
            term1, term2 = eta * Dbar * E, -eta * M * D
            recon = float((term1 + term2).sum())
            recorded = float(z[f'{key}__rule_bins'][:, home, 2].sum())
            max_dbar_err = max(max_dbar_err, float(np.abs(dbar_from(D, onset=onset_step, decay=decay) - Dbar).max()))
            phases = dict(onset_adjacent=(onset_step, onset_step + 150), steady=(onset_step + 150, offset_step), post_offset=(offset_step, len(D)))
            step_rows.append(dict(key=key, reconstructed=recon, recorded_applied=recorded,
                                  term_dbar_k=float(term1.sum()), term_kbar_d=float(term2.sum()),
                                  by_phase={name: dict(dbar_k=float(term1[a:b].sum()), kbar_d=float(term2[a:b].sum()), net=float((term1 + term2)[a:b].sum()))
                                            for name, (a, b) in phases.items()},
                                  dan_events_post=float(D[offset_step:].sum()), last_dan_event_ms=float(np.flatnonzero(D > 0).max() * dt) if (D > 0).any() else None,
                                  last_kc_impulse_ms=float(np.flatnonzero(E > 0).max() * dt) if (E > 0).any() else None))
            profiles.append(pearson_at_lags(E[onset_step:offset_step], D[onset_step:offset_step], lags))

            def total_with(d_series):
                return float((eta * dbar_from(d_series, onset=onset_step, decay=decay) * E - eta * M * d_series).sum())

            window = slice(onset_step, offset_step)
            surrogates['actual'].append(total_with(D))
            for name, shift in (('shift_-5ms', -25), ('shift_+5ms', 25), ('shift_-20ms', -100), ('shift_+20ms', 100)):
                d_s = D.copy()
                d_s[window] = np.roll(D[window], shift)
                surrogates[name].append(total_with(d_s))
            d_r = D.copy()
            d_r[window] = D[window][::-1]
            surrogates['reverse'].append(total_with(d_r))
            jit = []
            for _ in range(args.jitter_realizations):
                d_j = D.copy()
                d_j[window] = 0.0
                events = np.flatnonzero(D[window] > 0)
                for t in events:
                    target = int(np.clip(t + rng.integers(-25, 26), 0, offset_step - onset_step - 1))
                    d_j[onset_step + target] += D[onset_step + t]
                jit.append(total_with(d_j))
            surrogates['jitter_5ms'].append(float(np.mean(jit)))
        report['per_step'] = dict(
            note='exact per-step decomposition over eligible home edges; surrogates alter only the DAN series inside the plastic stimulus window and are descriptive sensitivities, not causal proof',
            max_abs_dbar_recurrence_error=max_dbar_err,
            reconstruction=dict(max_abs_error=float(max(abs(r['reconstructed'] - r['recorded_applied']) for r in step_rows)),
                                mean_reconstructed=float(np.mean([r['reconstructed'] for r in step_rows])),
                                mean_recorded=float(np.mean([r['recorded_applied'] for r in step_rows]))),
            mean_by_phase={name: {k: float(np.mean([r['by_phase'][name][k] for r in step_rows])) for k in ('dbar_k', 'kbar_d', 'net')} for name in ('onset_adjacent', 'steady', 'post_offset')},
            sd_net_by_phase={name: float(np.std([r['by_phase'][name]['net'] for r in step_rows], ddof=1)) for name in ('onset_adjacent', 'steady', 'post_offset')},
            last_event_ms=dict(dan_mean=float(np.mean([r['last_dan_event_ms'] for r in step_rows])), dan_max=float(np.max([r['last_dan_event_ms'] for r in step_rows])),
                               kc_mean=float(np.mean([r['last_kc_impulse_ms'] for r in step_rows])), kc_max=float(np.max([r['last_kc_impulse_ms'] for r in step_rows]))),
            impulse_dan_lag_profile=dict(note='normalized cross-correlation (Pearson per overlap) of eligible-edge KC impulses with home-DAN events; positive lag = DAN after KC; 0.2 ms steps, stimulus-plastic window',
                                         lags_ms=[lag * dt for lag in lags], mean=[float(x) for x in np.mean(profiles, 0)],
                                         peak_lag_ms=float(lags[int(np.argmax(np.mean(profiles, 0)))] * dt)),
            surrogates={name: dict(mean=float(np.mean(v)), sd=float(np.std(v, ddof=1)), negative_count=int(np.sum(np.array(v) < 0))) for name, v in surrogates.items()},
            rows=step_rows)

    atomic_json(args.run / 'attribution.json', report)
    if args.evidence:
        atomic_json(args.evidence / f'attribution-{summary["run_id"]}.json', report)
    print(json.dumps({k: report[k] for k in ('run_id', 'mean_applied_by_phase', 'sd_applied_by_phase')}, indent=1))
    if has_steps:
        ps = report['per_step']
        print('per-step reconstruction max abs error', ps['reconstruction']['max_abs_error'], '| dbar recurrence max err', ps['max_abs_dbar_recurrence_error'])
        print('per-step mean by phase', json.dumps(ps['mean_by_phase'], indent=1))
        print('sd net by phase', ps['sd_net_by_phase'])
        print('last events ms', ps['last_event_ms'])
        prof = ps['impulse_dan_lag_profile']
        print('lag profile peak at', prof['peak_lag_ms'], 'ms; values at -20,-10,-5,-2,-1,0,+1,+2,+5,+10,+20 ms:',
                                                      [round(prof['mean'][prof['lags_ms'].index(m)], 3) for m in (-20, -10, -5, -2, -1, 0, 1, 2, 5, 10, 20)])
        print('surrogates:', json.dumps(ps['surrogates'], indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
