"""Output-only, deterministic KC local-state reference; no engine or data loading.

Physical time is seconds. Native events occur at t/5000; source updates at
k/30, k>=1, before coincident events. Local state is cold for every new object.
An explicit advance_boundary() flushes the source boundary at the next native
time without inventing a spike. Empty chunks do not advance either clock.

Only source-defined nonnegative calcium clipping is performed. Inadmissible
Euler coefficients, nonfinite arithmetic, or an invalid L/C order raise before
publishing a source frame. A failed chunk retains its successful earlier steps;
the offending step is atomic. Malformed chunks are rejected in full up front.
"""

from collections.abc import Mapping
from numbers import Real
from types import MappingProxyType

import numpy as np
from scipy.sparse import csr_matrix
from scipy.special import expit

SOURCE_DT = 1.0 / 30
PARAMETER_NAMES = frozenset(
    ("tauKCdec", "tauinp", "tauadapt", "adaptscale", "tauinh", "inhfactor", "infp", "slf", "bline")
)


def _parameters(params):
    if not isinstance(params, Mapping) or set(params) != PARAMETER_NAMES:
        raise ValueError("The complete named source parameter inventory is required.")
    values = {}
    for name, value in params.items():
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
            raise ValueError("Parameters must be finite real scalars, excluding booleans.")
        try:
            value = float(value)
        except (OverflowError, ValueError) as exc:
            raise ValueError("Parameter cannot be represented as finite float64.") from exc
        if not np.isfinite(value) or value < 0:
            raise ValueError("Source parameters must be finite and nonnegative.")
        values[name] = value
    if (
        any(values[key] <= 0 for key in ("tauKCdec", "tauinp", "slf"))
        or any(values[key] < SOURCE_DT for key in ("tauadapt", "tauinh"))
        or values["bline"] != 0
    ):
        raise ValueError("Invalid source times, sigmoid slope, or zero-baseline contract.")
    return MappingProxyType(values)


def _adjacency(adjacency):
    if not isinstance(adjacency, csr_matrix):
        raise ValueError("Adjacency must be a CSR matrix with recipients as rows.")
    if (
        adjacency.ndim != 2
        or adjacency.shape[0] < 1
        or adjacency.shape[0] != adjacency.shape[1]
        or adjacency.dtype.kind not in "iuf"
    ):
        raise ValueError("Adjacency must be a nonempty square real matrix.")
    matrix = adjacency.astype(np.float64, copy=True)
    try:
        matrix.check_format(full_check=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid CSR storage.") from exc
    if not np.isfinite(matrix.data).all() or np.any(matrix.data < 0) or np.any(matrix.diagonal() != 0):
        raise ValueError("Adjacency must be finite, nonnegative and have no self-coupling.")
    for lo, hi in zip(matrix.indptr[:-1], matrix.indptr[1:]):
        if np.any(np.diff(matrix.indices[lo:hi]) <= 0):
            raise ValueError("CSR rows must have sorted, unique presynaptic indices.")
    sums = np.asarray(matrix.sum(axis=1)).ravel()
    if not np.all((sums == 0) | np.isclose(sums, 1, atol=2e-12, rtol=0)):
        raise ValueError("Every nonempty recipient row must be normalized to one.")
    for array in (matrix.data, matrix.indices, matrix.indptr):
        array.setflags(write=False)
    return matrix


class KCLocalState:
    """One trial's source-clock C/L/a/I state and held event susceptibility."""

    def __init__(self, params, adjacency):
        self.params = _parameters(params)
        self._adjacency = _adjacency(adjacency)
        self.n_kc = self._adjacency.shape[0]
        self._calyx = np.zeros(self.n_kc, np.float64)
        self._lobe = np.zeros(self.n_kc, np.float64)
        self._adaptation = np.zeros(self.n_kc, np.float64)
        self._inhibition = np.zeros(self.n_kc, np.float64)
        self._pending_counts = np.zeros(self.n_kc, np.int64)
        self._native_step = 0
        self._source_frames = 0

    @property
    def native_step(self):
        return self._native_step

    @property
    def source_frames(self):
        return self._source_frames

    @property
    def calyx(self):
        return self._calyx.copy()

    @property
    def lobe(self):
        return self._lobe.copy()

    @property
    def adaptation(self):
        return self._adaptation.copy()

    @property
    def inhibition(self):
        return self._inhibition.copy()

    @property
    def pending_counts(self):
        return self._pending_counts.copy()

    @property
    def susceptibility(self):
        return np.divide(self._lobe, self._calyx, out=np.ones(self.n_kc), where=self._calyx != 0)

    def _source_frame(self):
        p = self.params
        c, ell, adapt, inhib = (self._calyx, self._lobe, self._adaptation, self._inhibition)
        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                coefficient = 1 - SOURCE_DT * (1 + adapt) / p["tauKCdec"]
                if np.any(coefficient < 0):
                    raise ValueError("Source calcium Euler coefficient is negative.")
                forcing = self._pending_counts / p["tauinp"]
                next_c = c + (forcing - c / p["tauKCdec"]) * SOURCE_DT
                next_l = ell + (forcing - ell / p["tauKCdec"]) * SOURCE_DT
                next_c -= adapt * c * (1 / p["tauKCdec"]) * SOURCE_DT
                next_l -= adapt * ell * (1 / p["tauKCdec"]) * SOURCE_DT
                next_l -= inhib * (1 / p["tauKCdec"]) * SOURCE_DT
                next_a = adapt + (p["adaptscale"] * c - adapt) / p["tauadapt"] * SOURCE_DT
                neighbor = p["inhfactor"] * (self._adjacency @ ell)
                modulation = expit((p["infp"] - ell) / p["slf"])
                next_i = (inhib + (neighbor - inhib) / p["tauinh"] * SOURCE_DT) * modulation
                next_c = np.maximum(next_c, 0)
                next_l = np.maximum(next_l, 0)
        except (FloatingPointError, OverflowError) as exc:
            raise ValueError("Nonfinite local-state arithmetic.") from exc
        if (
            not all(np.isfinite(a).all() for a in (coefficient, next_c, next_l, next_a, next_i))
            or any(np.any(a < 0) for a in (next_c, next_l, next_a, next_i))
            or np.any(next_l > next_c)
        ):
            raise ValueError("Invalid local-state values or 0 <= L <= C ordering.")
        self._calyx, self._lobe = next_c, next_l
        self._adaptation, self._inhibition = next_a, next_i
        self._pending_counts.fill(0)
        self._source_frames += 1

    def advance_boundary(self):
        """Flush due positive source boundaries at the next native time; no event."""
        while (self._source_frames + 1) * 5000 <= self._native_step * 30:
            self._source_frame()

    def _events(self, events, ndim):
        values = np.asarray(events)
        if (
            values.ndim != ndim
            or values.shape[-1] != self.n_kc
            or values.dtype.kind not in "biuf"
            or not np.isfinite(values).all()
            or not np.isin(values, (0, 1)).all()
        ):
            raise ValueError("Events must be binary numeric KC vectors or step-by-KC chunks.")
        return values

    def _consume_validated(self, events):
        self.advance_boundary()
        weighted = self.susceptibility * events
        self._pending_counts += events.astype(np.int64)
        self._native_step += 1
        return weighted

    def consume(self, events):
        """Consume one binary native sample; return its held-weighted KC events."""
        return self._consume_validated(self._events(events, 1))

    def consume_chunk(self, events):
        """Consume a prevalidated chunk; state continues across subsequent calls."""
        values = self._events(events, 2)
        out = np.empty(values.shape, np.float64)
        for index, row in enumerate(values):
            out[index] = self._consume_validated(row)
        return out
