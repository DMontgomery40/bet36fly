"""Source-bound taste populations and isolated plasticity-off full-graph simulation.

Molecular labels are Tastekin et al.'s proposed morphology-based identities.
No trained decoder, dopamine rule, ALPN bypass or inherited gain intervention.
"""
from __future__ import annotations

import ctypes
import hashlib
import platform
import subprocess
import time
from pathlib import Path

import numpy as np

from .connectome import ROOT
from .reward_brain import _integer_array

TASTE_TYPES = {'sweet': ('LB3b', 'LB3c'), 'water': ('LB3a',),
               'bitter': ('LB1a', 'LB1b', 'LB1c', 'LB1d')}


def reconcile_cells(grn_rows, mn_rows, nodes):
    """Exact same-specimen table join; selected missing/mismatched cells fail closed."""
    if nodes.bodyId.dtype.kind not in 'iu' or not nodes.bodyId.is_unique:
        raise ValueError('Native body IDs must be exact unique integers.')
    native = nodes.set_index('bodyId')
    groups = {**TASTE_TYPES, 'MN9': ('MN9',)}
    populations = {k: [] for k in groups}
    unmatched = []
    for table, field in ((grn_rows, 'Subtype'), (mn_rows, 'Type')):
        seen = set()
        for row in table:
            if row['Connectome'] != 'maleCNS':
                continue
            token = str(row['Body_ID'])
            if not token.isascii() or not token.isdecimal() or not 0 < int(token) <= 2**63-1:
                raise ValueError('Source body IDs must be exact positive integer strings.')
            body = int(token)
            if body in seen:
                raise ValueError('Duplicate same-specimen source body ID.')
            seen.add(body)
            kind = row[field]
            if body not in native.index:
                unmatched.append(body)
            for name, types in groups.items():
                if kind not in types:
                    continue
                if body not in native.index or native.loc[body, 'type'] != kind:
                    raise ValueError(f'Selected source/native type mismatch for {body}.')
                if name != 'MN9' and native.loc[body, 'class'] != 'gustatory':
                    raise ValueError(f'Selected sensory class mismatch for {body}.')
                populations[name].append(body)
    if any(not values for values in populations.values()):
        raise ValueError('Every specified sensory/output population must be present.')
    return dict(populations={k: sorted(v) for k, v in populations.items()},
                unretained_source_ids=sorted(set(unmatched)),
                identity_status='exact_native_ids_with_source_proposed_functional_assignment',
                excluded_from_sweet=['LB3a', 'LB3d', 'LB4', 'incomplete or untyped LB3'])


class SensoryEngine:
    """Fixed Shiu-style dynamics with separately counted input events; no plasticity."""

    def __init__(self, ptr, post, weights, sensory):
        self.ptr = _integer_array(ptr, np.int64, 'ptr')
        self.post = _integer_array(post, np.int32, 'post')
        self.sensory = _integer_array(sensory, np.int32, 'sensory')
        self.weights = np.array(weights, np.float32, order='C', copy=True)
        self.n = len(self.ptr)-1
        if (self.n < 1 or self.ptr[0] != 0 or self.ptr[-1] != len(self.post)
                or np.any(np.diff(self.ptr) < 0) or self.weights.shape != self.post.shape
                or not np.isfinite(self.weights).all() or np.any(self.post < 0)
                or np.any(self.post >= self.n) or np.any(self.sensory < 0)
                or np.any(self.sensory >= self.n) or len(np.unique(self.sensory)) != len(self.sensory)):
            raise ValueError('Invalid sensory graph.')
        source = Path(__file__).with_name('sensory_lif.cpp')
        version = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
        build = ROOT / 'output/native'
        build.mkdir(parents=True, exist_ok=True)
        dest = build / f'sensory-{version}.{"dylib" if platform.system() == "Darwin" else "so"}'
        if not dest.exists():
            temporary = dest.with_suffix('.partial')
            subprocess.run(['c++', '-O3', '-std=c++17', '-shared', '-fPIC', str(source),
                            '-o', str(temporary)], check=True, capture_output=True)
            temporary.replace(dest)
        self.lib = ctypes.CDLL(str(dest))
        i32 = np.ctypeslib.ndpointer(dtype=np.int32, flags='C_CONTIGUOUS')
        i64 = np.ctypeslib.ndpointer(dtype=np.int64, flags='C_CONTIGUOUS')
        f32 = np.ctypeslib.ndpointer(dtype=np.float32, flags='C_CONTIGUOUS')
        f64 = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
        self.lib.simulate_sensory.argtypes = [ctypes.c_int, i64, i32, f32, ctypes.c_int,
            i32, f32, ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_uint64,
            ctypes.c_int, i32, i32, f32, i32, i32, i32, f64]
        self.lib.simulate_sensory.restype = ctypes.c_int

    def run(self, rates, *, bin_ms=20., dt=.2, seed=17, sample=()):
        raw = np.asarray(rates, dtype=np.float64)
        sample = _integer_array(np.asarray(sample, dtype=np.int64) if len(sample) == 0 else sample,
                                np.int32, 'sample')
        if (dt not in (.1, .2) or not np.isfinite(bin_ms) or bin_ms < dt
                or abs(bin_ms/dt-round(bin_ms/dt)) > 1e-7
                or raw.ndim != 2 or raw.shape[1] != len(self.sensory) or len(raw) == 0
                or len(raw)*bin_ms > 10000 or raw.size > 50_000_000
                or len(raw)*len(sample) > 50_000_000 or not np.isfinite(raw).all()
                or np.any(raw < 0) or np.any(raw > 1000/dt)
                or np.any(sample < 0) or np.any(sample >= self.n)
                or len(np.unique(sample)) != len(sample)
                or not isinstance(seed, (int, np.integer)) or isinstance(seed, (bool, np.bool_))
                or not 0 <= int(seed) <= 2**64-1):
            raise ValueError('Invalid sensory schedule, timing, sample or seed.')
        rates = np.ascontiguousarray(raw, np.float32)
        counts = np.zeros(self.n, np.int32)
        voltage = np.zeros(self.n, np.float32)
        trace = np.zeros((len(rates), len(sample)), np.int32)
        inputs = np.zeros(rates.shape, np.int32)
        population = np.zeros(len(rates), np.int32)
        extrema = np.zeros(2, np.float64)
        bin_steps = round(bin_ms/dt)
        start = time.monotonic()
        result = self.lib.simulate_sensory(self.n, self.ptr, self.post, self.weights,
            len(self.sensory), self.sensory, rates, bin_steps, len(rates)*bin_steps,
            dt, int(seed), len(sample), sample, counts, voltage, trace, inputs, population, extrema)
        if result:
            raise RuntimeError(f'Sensory simulation failed numerical/resource check ({result}).')
        return dict(counts=counts, voltage=voltage, trace=trace, input_events=inputs,
                    population=population, max_abs_voltage_offset_mv=float(extrema[0]),
                    max_abs_synaptic_state_mv=float(extrema[1]),
                    wall_seconds=time.monotonic()-start, duration_ms=len(rates)*bin_ms,
                    dt_ms=dt, bin_ms=bin_ms)
