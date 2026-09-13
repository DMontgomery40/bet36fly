"""Chronological external encoder/readout around exact cached native taste probes.

The circuit is frozen. Both logistic fits are engineered; this is not neural learning.
"""

from __future__ import annotations

from datetime import datetime
import warnings

import numpy as np
from scipy.special import expit
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

C_VALUES = (0.01, 0.1, 1.0)


def team_vectors(x):
    x = np.asarray(x, float)
    if x.ndim != 2 or x.shape[1] != 16 or not np.isfinite(x).all():
        raise ValueError("Expected finite existing 16-channel pregame features.")
    home = x[:, [0, 3, 6, 13, 10]] - np.array([0.75, 0.5, 0.5, 0, 0])
    away = x[:, [1, 4, 7, 14, 11]] - np.array([0.75, 0.5, 0.5, 0, 0])
    return home, away


def _fit(x, y, c, intercept=True):
    model = LogisticRegression(
        C=c, fit_intercept=intercept, max_iter=5000, solver="lbfgs", random_state=20260913
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        model.fit(x, y)
    return model


def week_ids(dates):
    return np.array(
        [
            f"{(d := datetime.fromisoformat(s.replace('Z', '+00:00'))).isocalendar().year}-{d.isocalendar().week:02d}"
            for s in dates
        ]
    )


def fit_encoder(x, y, dates, c, bootstraps=100):
    home, away = team_vectors(x)
    delta = home - away
    scales = np.maximum(delta.std(axis=0), 1e-8)
    model = _fit(delta / scales, y, c)
    coef = model.coef_[0]
    intercept = float(model.intercept_[0])
    scores = np.concatenate([home / scales @ coef + intercept / 2, away / scales @ coef - intercept / 2])
    center = float(scores.mean())
    spread = max(float(scores.std()), 1e-8)
    weeks = week_ids(dates)
    unique = np.unique(weeks)
    indices = [np.flatnonzero(weeks == w) for w in unique]
    rng = np.random.default_rng(20260913)
    boot_coef = []
    boot_intercept = []
    for _ in range(bootstraps):
        chosen = np.concatenate([indices[i] for i in rng.integers(len(unique), size=len(unique))])
        boot = _fit(delta[chosen] / scales, np.asarray(y)[chosen], c)
        boot_coef.append(boot.coef_[0].tolist())
        boot_intercept.append(float(boot.intercept_[0]))
    return dict(
        C=c,
        coef=coef.tolist(),
        intercept=intercept,
        scales=scales.tolist(),
        center=center,
        spread=spread,
        bootstrap_coef=boot_coef,
        bootstrap_intercept=boot_intercept,
    )


def encoder_probability(x, encoder):
    home, away = team_vectors(x)
    return expit(
        (home - away) / np.asarray(encoder["scales"]) @ np.asarray(encoder["coef"]) + encoder["intercept"]
    )


def quality_keys(x, encoder):
    home, away = team_vectors(x)
    scales = np.asarray(encoder["scales"])
    coef = np.asarray(encoder["coef"])
    boots = np.asarray(encoder["bootstrap_coef"])
    intercepts = np.asarray(encoder["bootstrap_intercept"])
    out = {}
    for side, v, role, agecol in [("home", home, 0.5, 8), ("away", away, -0.5, 9)]:
        score = v / scales @ coef + role * encoder["intercept"]
        q = expit((score - encoder["center"]) / encoder["spread"])
        boot = expit(((v / scales) @ boots.T + role * intercepts - encoder["center"]) / encoder["spread"])
        bounds = np.quantile(boot, [0.025, 0.975], axis=1).T
        bounds[:, 0] = np.minimum(bounds[:, 0], q)
        bounds[:, 1] = np.maximum(bounds[:, 1], q)
        bounds[np.asarray(x)[:, agecol] < 1] = [0.0, 1.0]
        keys = np.floor(q * 34 + 0.5).astype(np.int32)
        keys[bounds[:, 1] < 0.2] = 35
        out.update({side + "_q": q, side + "_bounds": bounds, side + "_keys": keys})
    return out


def neural_features(keys, cache):
    cache = np.asarray(cache, float)
    if cache.shape != (36, 4) or not np.isfinite(cache).all() or np.any(cache < 0):
        raise ValueError("Invalid native response cache.")
    h, a = np.asarray(keys["home_keys"]), np.asarray(keys["away_keys"])
    if (
        h.shape != a.shape
        or h.dtype.kind not in "iu"
        or a.dtype.kind not in "iu"
        or np.any(h < 0)
        or np.any(a < 0)
        or np.any(h >= 36)
        or np.any(a >= 36)
    ):
        raise ValueError("Invalid opportunity keys.")
    return np.log1p(cache[h]) - np.log1p(cache[a])


def fit_readout(z, y, c):
    scales = np.maximum(np.asarray(z).std(axis=0), 1e-8)
    model = _fit(z / scales, y, c, False)
    return dict(C=c, scales=scales.tolist(), coef=model.coef_[0].tolist(), intercept=0.0)


def readout_probability(z, readout):
    return expit(np.asarray(z) / np.asarray(readout["scales"]) @ np.asarray(readout["coef"]))


def losses(y, p):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return -(y * np.log(p) + (1 - y) * np.log1p(-p))


def metrics(y, p):
    return dict(
        n=len(y),
        accuracy=float(np.mean((p >= 0.5) == y)),
        log_loss=float(losses(y, p).mean()),
        brier=float(np.mean((p - y) ** 2)),
    )


def paired_evaluation(y, predictions, dates, replicates=10000, alpha=0.025):
    y = np.asarray(y)
    predictions = {k: np.asarray(v, float) for k, v in predictions.items()}
    if (
        y.ndim != 1
        or len(y) == 0
        or len(dates) != len(y)
        or not np.isin(y, [0, 1]).all()
        or not {"neural", "uniform", "prior"} <= predictions.keys()
        or any(
            p.shape != y.shape or not np.isfinite(p).all() or np.any(p < 0) or np.any(p > 1)
            for p in predictions.values()
        )
    ):
        raise ValueError("Invalid paired prediction set.")
    weeks = week_ids(dates)
    unique = np.unique(weeks)
    members = [np.flatnonzero(weeks == w) for w in unique]
    count = np.array([len(i) for i in members])
    rng = np.random.default_rng(20260913)
    sampled = rng.integers(len(unique), size=(replicates, len(unique)))
    denominator = count[sampled].sum(axis=1)
    acc_week = np.array([np.sum((predictions["neural"][ix] >= 0.5) == y[ix]) for ix in members])
    acc = acc_week[sampled].sum(axis=1) / denominator
    result = dict(
        metrics={k: metrics(y, p) for k, p in predictions.items()},
        weeks=len(unique),
        replicates=replicates,
        alpha=alpha,
        accuracy_interval=np.quantile(acc, [alpha, 1 - alpha]).tolist(),
        paired_loss={},
    )
    neural_loss = losses(y, predictions["neural"])
    for name, p in predictions.items():
        if name == "neural":
            continue
        delta = neural_loss - losses(y, p)
        totals = np.array([delta[ix].sum() for ix in members])
        boot = totals[sampled].sum(axis=1) / denominator
        result["paired_loss"][name] = dict(
            mean=float(delta.mean()), interval=np.quantile(boot, [alpha, 1 - alpha]).tolist()
        )
    result["goal_passed"] = bool(
        result["accuracy_interval"][0] > 0.5
        and all(result["paired_loss"][name]["interval"][1] < 0 for name in ["uniform", "prior"])
    )
    return result
