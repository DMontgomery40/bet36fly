"""Actual full-graph spiking dynamics; no game policy inside the brain engine."""
from __future__ import annotations

import ctypes
import hashlib
import json
import platform
import subprocess
import threading
import time
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, load_npz

from .connectome import ROOT

_BUILD_LOCK = threading.Lock()


def native_library():
    source = Path(__file__).with_name('lif.cpp')
    version = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    build = ROOT / 'output/native'
    build.mkdir(parents=True, exist_ok=True)
    dest = build / f'lif-{version}.{"dylib" if platform.system() == "Darwin" else "so"}'
    with _BUILD_LOCK:
        if not dest.exists():
            temp = dest.with_suffix('.partial')
            subprocess.run(['c++', '-O3', '-std=c++17', '-shared', '-fPIC', str(source), '-o', str(temp)],
                           check=True, capture_output=True)
            temp.replace(dest)
    lib = ctypes.CDLL(str(dest))
    i32 = np.ctypeslib.ndpointer(dtype=np.int32, flags='C_CONTIGUOUS')
    i64 = np.ctypeslib.ndpointer(dtype=np.int64, flags='C_CONTIGUOUS')
    f32 = np.ctypeslib.ndpointer(dtype=np.float32, flags='C_CONTIGUOUS')
    lib.simulate.argtypes = [ctypes.c_int, i64, i32, f32, ctypes.c_int, i32, f32,
                            ctypes.c_int, ctypes.c_float, ctypes.c_uint64, ctypes.c_int, i32,
                            ctypes.c_int, i32, f32, i32, i32]
    lib.simulate.restype = ctypes.c_int
    return lib


def encode_rates(features: np.ndarray, n_ports: int) -> np.ndarray:
    """Explicit artificial opponent coding, NOT a claim of natural fly semantics.

    Ordered ALPN IDs tile positive/negative channels of standardized pregame
    features. Baseline 150 Hz, excursions bounded to 30..270 Hz. No outcome or
    betting decision enters this mapping.
    """
    z = np.asarray(features, dtype=np.float32)
    if z.ndim != 1 or not len(z) or not np.isfinite(z).all() or n_ports < 1:
        raise ValueError('Expected finite pregame feature vector and positive sensory port count.')
    channels = np.concatenate([z, -z])
    return np.ascontiguousarray(150 + 120 * np.tanh(channels[np.arange(n_ports) % len(channels)] / 2),
                                dtype=np.float32)


def stimulus_rates(features, n_ports):
    """Stimulate one anatomical ALPN per opponent channel, leave other ports undriven.

    The 32 ports (for 16 inputs) span the sorted ALPN catalog. This choice was
    made from unlabeled neural sensitivity probes, before sports training.
    It avoids near-identical saturated outputs from driving every ALPN at once.
    All undriven neurons still participate normally in the complete network.
    """
    channels = min(2 * len(features), n_ports)
    locations = np.linspace(0, n_ports - 1, channels, dtype=np.int32)
    rates = np.zeros(n_ports, np.float32)
    rates[locations] = encode_rates(features, channels)
    return rates


class LIFEngine:
    def __init__(self, ptr, post, weights, sensory):
        self.ptr = np.ascontiguousarray(ptr, dtype=np.int64)
        self.post = np.ascontiguousarray(post, dtype=np.int32)
        self.weights = np.ascontiguousarray(weights, dtype=np.float32)
        self.sensory = np.ascontiguousarray(sensory, dtype=np.int32)
        self.n = len(self.ptr) - 1
        if (self.n < 1 or self.ptr[0] != 0 or self.ptr[-1] != len(self.post)
                or len(self.post) != len(self.weights) or np.any(np.diff(self.ptr) < 0)
                or np.any(self.post < 0) or np.any(self.post >= self.n)
                or np.any(self.sensory < 0) or np.any(self.sensory >= self.n)
                or len(np.unique(self.sensory)) != len(self.sensory)
                or not np.isfinite(self.weights).all()):
            raise ValueError('Invalid sparse neuronal graph.')
        self.lib = native_library()

    def run(self, rates, *, duration_ms=120.0, seed=42, sample=None, dt=0.2, bin_ms=4.0):
        rates = np.ascontiguousarray(rates, dtype=np.float32)
        sample = np.ascontiguousarray([] if sample is None else sample, dtype=np.int32)
        if (rates.shape != self.sensory.shape or not np.isfinite(rates).all() or np.any(rates < 0)
                or dt != 0.2 or not 0 < duration_ms <= 10000 or np.any(rates * dt / 1000 > 1)
                or np.any(sample < 0) or np.any(sample >= self.n) or len(np.unique(sample)) != len(sample)
                or not bin_ms >= dt or not np.isfinite(duration_ms)):
            raise ValueError('Invalid simulation inputs. This calibrated discretization requires dt=0.2 ms.')
        steps = int(round(duration_ms / dt))
        bin_steps = max(1, int(round(bin_ms / dt)))
        bins = (steps + bin_steps - 1) // bin_steps
        counts = np.zeros(self.n, np.int32)
        voltage = np.zeros(self.n, np.float32)
        trace = np.zeros((bins, len(sample)), np.int32)
        population = np.zeros(bins, np.int32)
        start = time.perf_counter()
        result = self.lib.simulate(self.n, self.ptr, self.post, self.weights, len(self.sensory),
                                   self.sensory, rates, steps, dt, int(seed), len(sample), sample,
                                   bin_steps, counts, voltage, trace, population)
        if result:
            raise RuntimeError('Native neural simulation failed.')
        return dict(counts=counts, rates=counts.astype(np.float32) * (1000 / (steps * dt)),
                    voltage=voltage, trace=trace, population=population,
                    duration_ms=steps * dt, bin_ms=bin_steps * dt, wall_seconds=time.perf_counter() - start)


class FlyBrain:
    def __init__(self, path: Path = ROOT / 'data/brain', gains=None):
        self.path = path
        self.manifest = json.loads((path / 'manifest.json').read_text())
        self.ids = np.load(path / 'ids.npy')
        self.kc = np.load(path / 'kc.npy')
        self.mbon = np.load(path / 'mbon.npy')
        self.sensory = np.load(path / 'sensory.npy')
        ptr, post, counts, signs = [np.load(path / (name + '.npy')) for name in
                                     ('indptr', 'post', 'counts', 'signs')]
        weights = counts * np.repeat(signs.astype(np.float32), np.diff(ptr)) * np.float32(0.275)
        self.plastic = load_npz(path / 'plastic.npz').astype(np.float32)
        self.plastic_edges = self.plastic.tocoo()
        if gains is not None:
            gains = np.asarray(gains, dtype=np.float32)
            if gains.shape != self.plastic.shape or not np.isfinite(gains).all() or np.any(gains <= 0):
                raise ValueError('Plastic gains must be finite, positive and match the anatomical circuit.')
            output_lookup = np.full(len(self.ids), -1, np.int32)
            output_lookup[self.mbon] = np.arange(len(self.mbon))
            for column, pre in enumerate(self.kc):
                lo, hi = ptr[pre:pre + 2]
                rows = output_lookup[post[lo:hi]]
                selected = np.flatnonzero(rows >= 0)
                weights[lo + selected] *= gains[rows[selected], column]
        self.engine = LIFEngine(ptr, post, weights, self.sensory)
        # Biological superclass pooling augments the 97 MBON outputs, using only
        # actual downstream spike counts. Sensory input neurons are excluded.
        import pyarrow.feather as feather
        annotations = feather.read_table(path / 'nodes.feather').to_pandas()
        if annotations.bodyId.duplicated().any():
            raise ValueError('Duplicate annotation body IDs.')
        self.nodes = annotations.set_index('bodyId').reindex(self.ids).reset_index()
        if self.nodes.superclass.isna().any():
            raise ValueError('Graph IDs are missing neuronal superclass annotations.')
        self.groups = [np.flatnonzero(self.nodes.superclass.eq(s).to_numpy() &
                                      ~np.isin(np.arange(len(self.ids)), self.sensory))
                       for s in sorted(self.nodes.superclass.unique())]
        self.output_dim = len(self.mbon) + len(self.groups)

    def simulate(self, features, *, seed=42, sample=None, duration_ms=80):
        result = self.engine.run(stimulus_rates(features, len(self.sensory)), seed=seed, sample=sample,
                                 duration_ms=duration_ms)
        result['kc_rates'] = result['rates'][self.kc]
        result['mbon_rates'] = result['rates'][self.mbon]
        pooled = np.array([result['rates'][g].mean() if len(g) else 0 for g in self.groups], np.float32)
        result['readout'] = np.concatenate([result['mbon_rates'], pooled])
        return result

    def plastic_support(self):
        return csr_matrix(self.plastic != 0).toarray()


def simulate_windows(brain, features, *, seed=42, include_kc=True):
    """Pool four 20-ms windows from the same 80-ms reset trial as v1.

    Temporal channels are window-first: MBONs followed by superclass means.
    The all-neuron integer trace is deliberately not returned or cached.
    """
    result = brain.engine.run(stimulus_rates(features, len(brain.sensory)), seed=seed,
                              duration_ms=80, sample=np.arange(brain.engine.n, dtype=np.int32),
                              bin_ms=20)
    trace = result.pop('trace')
    windows = np.empty((4, brain.output_dim), np.float32)
    windows[:, :len(brain.mbon)] = trace[:, brain.mbon] * np.float32(50)
    for column, group in enumerate(brain.groups, start=len(brain.mbon)):
        windows[:, column] = trace[:, group].mean(axis=1) * 50 if len(group) else 0
    pooled = {'whole': windows.mean(axis=0), 'windows': windows,
              'active': int(np.count_nonzero(result['counts'])),
              'spikes': int(result['counts'].sum(dtype=np.int64)),
              'wall_seconds': result['wall_seconds']}
    if include_kc:
        pooled['kc_windows'] = (trace[:, brain.kc] * np.float32(50)).astype(np.float32)
    return pooled
