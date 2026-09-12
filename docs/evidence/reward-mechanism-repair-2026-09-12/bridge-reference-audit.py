"""Reference-only bridge audit: closed event filters plus SciPy quadrature.

No imports of production code, native library, circuit, or diagnostic runner.
Nonproduction eta/bounds in clipping fixtures stress arithmetic only.
"""
from pathlib import Path
import hashlib
import json
import math

import mpmath as mp
import numpy as np
from scipy.integrate import quad

OUT = Path(__file__).parent
ETA, TE, TR, H = 0.0005, 500.0, 100.0, 0.2
R, E = 1 / TR, 1 / TE
N = 1 - (TR / TE) ** 2
mp.mp.dps = 90


def state(events, time):
    """Closed convolution of impulses; no step-to-step recurrence."""
    rr, ee = 0.0, 0.0
    for event, amplitude in events:
        if event <= time:
            age = time - event
            rr += amplitude * math.exp(-age / TR) / TR
            ee += amplitude * math.exp(-age / TE) * (-math.expm1(-(R-E)*age)) / (TR*(R-E))
    return rr, ee


def fields(k, d, time):
    rk, ek = state(k, time)
    rd, ed = state(d, time)
    return ed*rk, -ek*rd


def integrate(k, d, start, end, eta=ETA):
    # Cut at every impulse: no discontinuity is left for adaptive quadrature.
    cuts = sorted({start, end, *(t for t, _ in k+d if start < t < end)})
    areas, errs = [], []
    for component in (0, 1):
        parts = [quad(lambda t: eta*N*fields(k, d, t)[component], a, b,
                      epsabs=1e-13, epsrel=1e-12, limit=200)
                 for a, b in zip(cuts[:-1], cuts[1:])]
        areas.append(math.fsum(x for x, _ in parts))
        errs.append(math.fsum(x for _, x in parts))
    return np.array(areas), max(errs)


def formula(k, d, start, length, eta=ETA):
    rk, ek = state(k, start)
    rd, ed = state(d, start)
    b = R+E
    a = 1/b if math.isinf(length) else -math.expm1(-b*length)/b
    a2 = 1/(2*R) if math.isinf(length) else -math.expm1(-2*R*length)/(2*R)
    cross = (a2-a)/(E-R)*rk*rd
    areas = eta*N*np.array([a*ed*rk+cross, -(a*ek*rd+cross)])
    net = eta*N*a*(ed*rk-ek*rd)
    return areas, net


def pair_oracle(k, d, eta=ETA):
    total = []
    for tk, ak in k:
        for td, ad in d:
            lag = td-tk
            if lag:
                total.append(-math.copysign(1, lag)*eta*ak*ad*
                             (math.exp(-abs(lag)/TE)-math.exp(-abs(lag)/TR)))
    return math.fsum(total)


def main():
    checks = []
    interval_cases = [([], [], 0, H), ([(0, 1)], [(0, 1)], 0, H),
                      ([(0, 1)], [(0, 1)], 0, math.inf),
                      ([(0, 1)], [(20, 1)], 20, H),
                      ([(0, 1), (40, .5)], [(10, .25), (30, 1)], 50, 123.4),
                      ([(0, 1), (40, .5)], [(10, .25), (30, 1)], 50, math.inf)]
    for i, (k, d, start, length) in enumerate(interval_cases):
        actual, error = integrate(k, d, start, start+length)
        expected, stable = formula(k, d, start, length)
        max_error = float(np.max(np.abs(actual-expected)))
        checks.append(dict(kind='interval_or_tail', case=i, max_area_error=max_error,
                           net_error=abs(float(actual.sum())-stable), quadrature_error=error,
                           positive=float(actual[0]), negative=float(actual[1]),
                           passed=max_error < 1e-11 and abs(float(actual.sum())-stable) < 1e-11))

    histories = [('coincident', [(0, 1)], [(0, 1)]),
                 ('kc_only', [(0, 1), (30, 2)], []),
                 ('mixed', [(0, 1), (40, .5), (100, 1), (200, 1)],
                  [(10, .25), (30, 1), (100, .75), (250, 1)]),
                 ('partial_population', [(0, 1), (20, 1)], [(10, 1/22), (100, 2/22)])]
    for lag in (.2, 1, 5, 20, 50, 100, 500, 1000):
        histories.extend([(f'forward_{lag}', [(0, 1)], [(lag, 1)]),
                          (f'backward_{lag}', [(lag, 1)], [(0, 1)])])
    for name, k, d in histories:
        areas, error = integrate(k, d, 0, math.inf)
        expected = pair_oracle(k, d)
        checks.append(dict(kind='event_history', name=name, quadrature=float(areas.sum()),
                           pair_oracle=expected, error=abs(float(areas.sum())-expected),
                           quadrature_error=error, passed=abs(float(areas.sum())-expected) < 1e-11))

    # Clipping reference: integrate continuous closed event filters separately on
    # each event-free segment, where the net derivative cannot change sign.
    # Dense split and event-only split must agree, including reversals after bounds.
    k, d = [(0, 1), (200, 1), (400, 1)], [(100, 1), (300, 1)]
    def clipped(grid):
        gain, hits, signs = 1.0, [], []
        for a, b in zip(grid[:-1], grid[1:]):
            area, _ = integrate(k, d, a, b, eta=1.0)
            delta = float(area.sum())
            proposed = gain+delta
            if proposed <= .9 or proposed >= 1.1:
                hits.append([a, b if math.isfinite(b) else 'infinity', proposed])
            signs.append(int(np.sign(delta)))
            gain = min(1.1, max(.9, proposed))
        return gain, hits, sorted(set(signs))
    coarse = clipped([0, 100, 200, 300, 400, math.inf])
    dense = clipped([*np.arange(0, 500.1, 2.0), math.inf])
    checks.append(dict(kind='clipped_sign_reversal', fixture_eta=1.0, bounds=[.9, 1.1],
                       coarse_final=coarse[0], dense_final=dense[0],
                       coarse_bound_segments=coarse[1], signs=coarse[2],
                       passed=abs(coarse[0]-dense[0]) < 1e-11 and bool(coarse[1]) and -1 in coarse[2] and 1 in coarse[2]))

    k, d = [(0, 1)], [(H, 1)]
    accumulated, published, naive = 1.0, np.float32(1), np.float32(1)
    zero_steps, total_steps = 0, 0
    for t in np.arange(0, 400, H):
        # Every interval uses independent closed history states, never recurrence.
        _, delta = formula(k, d, float(t), H)
        accumulated += delta
        next_published = np.float32(accumulated)
        zero_steps += int(delta != 0 and next_published == published)
        total_steps += int(delta != 0)
        published = next_published
        naive = np.float32(float(naive)+delta)
    _, tail = formula(k, d, 400.0, math.inf)
    accumulated += tail
    published = np.float32(accumulated)
    naive = np.float32(float(naive)+tail)
    truth = pair_oracle(k, d)
    checks.append(dict(kind='sub_ulp_accumulation', expected=truth,
                       double_change=accumulated-1, published_change=float(published)-1,
                       naive_float_each_step_change=float(naive)-1, tail=tail,
                       nonzero_intervals=total_steps, zero_publication_intervals=zero_steps,
                       passed=abs((accumulated-1)-truth)<1e-11 and published == np.float32(1+truth)
                       and naive != published and zero_steps > .9*total_steps))

    # Edge-domain audit: compare the literal double coefficient subtraction with
    # high-precision arithmetic; these are not candidate parameter choices.
    edge_cases = []
    for tr in (100.0, 499.999999, float(np.nextafter(500.0, 0)), 1e-300, 1e-320):
        try:
            r, e, h = 1/tr, 1/500.0, H
            a = -math.expm1(-(r+e)*h)/(r+e)
            a2 = -math.expm1(-2*r*h)/(2*r)
            literal = (a2-a)/(e-r)
            mr, me, mh = 1/mp.mpf(tr), 1/mp.mpf(500), mp.mpf(H)
            ma = -mp.expm1(-(mr+me)*mh)/(mr+me)
            ma2 = -mp.expm1(-2*mr*mh)/(2*mr)
            exact = (ma2-ma)/(me-mr)
            rel = abs((mp.mpf(literal)-exact)/exact) if math.isfinite(literal) else mp.inf
            edge_cases.append(dict(tau_r=tr, reciprocal_finite=math.isfinite(r),
                                   literal_cross_coefficient=literal if math.isfinite(literal) else 'nonfinite',
                                   reference=str(exact), relative_error=str(rel)))
        except (OverflowError, ZeroDivisionError, ValueError) as exc:
            edge_cases.append(dict(tau_r=tr, error=type(exc).__name__+': '+str(exc)))

    result = dict(scope='reference-only; no circuit or production imports',
                  production=dict(h=H, tau_e=TE, tau_r=TR, eta=ETA, normalization=N),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  checks=checks, all_production_math_checks_passed=all(x['passed'] for x in checks),
                  numeric_domain_probes=edge_cases)
    path = OUT/'bridge-reference-audit.json'
    path.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(checks=len(checks), passed=result['all_production_math_checks_passed'],
                         failures=[x for x in checks if not x['passed']],
                         numeric_domain_probes=edge_cases), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
