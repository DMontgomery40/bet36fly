"""Bounded dopamine-gated LIF engine for the MaleCNS graph.

The learning channel is a phenomenological engineering mechanism. It does not
claim to implement measured dopamine concentration or receptor dynamics.
"""
from __future__ import annotations

import ctypes
import hashlib
import platform
import subprocess
import threading
import time
from pathlib import Path

import numpy as np

from .connectome import ROOT

_BUILD_LOCK = threading.Lock()
_MAX_SCHEDULE_VALUES = 50_000_000
_MAX_TRACE_VALUES = 50_000_000
SIGNAL_WIDTH, KC_SIGNAL_WIDTH, RULE_WIDTH = 4, 2, 7
# 'none': the candidate rule, raw compartment-mean DAN spikes in both terms (upstream form).
# 'tonic-baseline': the schema-2/3 legacy rule, tonic rate over dan_baseline_window_ms subtracted.
DAN_REFERENCE_MODES = {'none': 0, 'tonic-baseline': 1}


def _native_library():
    source = Path(__file__).with_name('reward_lif.cpp')
    version = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    build = ROOT / 'output/native'
    build.mkdir(parents=True, exist_ok=True)
    dest = build / f'reward-lif-{version}.{"dylib" if platform.system() == "Darwin" else "so"}'
    with _BUILD_LOCK:
        if not dest.exists():
            temp = dest.with_suffix('.partial')
            subprocess.run(
                ['c++', '-O3', '-std=c++17', '-shared', '-fPIC', str(source), '-o', str(temp)],
                check=True,
                capture_output=True,
            )
            temp.replace(dest)
    lib = ctypes.CDLL(str(dest))
    i32 = np.ctypeslib.ndpointer(dtype=np.int32, flags='C_CONTIGUOUS')
    i64 = np.ctypeslib.ndpointer(dtype=np.int64, flags='C_CONTIGUOUS')
    f32 = np.ctypeslib.ndpointer(dtype=np.float32, flags='C_CONTIGUOUS')
    f64 = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
    lib.simulate_reward.argtypes = [
        ctypes.c_int, i64, i32, f32, ctypes.c_int, i32, f32, ctypes.c_int,
        ctypes.c_int, ctypes.c_float, ctypes.c_uint64, ctypes.c_int, i32,
        ctypes.c_int, i32, i32, ctypes.c_int, i64, i32, i32, ctypes.c_int,
        ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, f32,
        ctypes.c_int, ctypes.c_int, f32,
        ctypes.c_int, i32, i32, ctypes.c_int, i32, ctypes.c_int,
        i32, f32, i32, i32, i32, i32,
        ctypes.c_int, ctypes.c_int, i32, f64, f64, f64, f32,
        ctypes.c_int,
    ]
    lib.simulate_reward.restype = ctypes.c_int
    return lib


def _integer_array(value, dtype, name):
    raw = np.asarray(value)
    if raw.ndim != 1 or raw.dtype.kind not in 'iu':
        raise ValueError(f'{name} must be a one-dimensional integer array.')
    limits = np.iinfo(dtype)
    if raw.size and (raw.min() < limits.min or raw.max() > limits.max):
        raise ValueError(f'{name} contains an index outside its native integer range.')
    return np.array(raw, dtype=dtype, order='C', copy=True)


class RewardEngine:
    """Scheduled full-graph simulation with sparse persistent KC-to-MBON gains."""

    def __init__(
        self,
        ptr,
        post,
        weights,
        sensory,
        kc_indices,
        dan_indices,
        dan_compartments,
        plastic_edge_indices,
        plastic_kc_indices,
        plastic_compartments,
        *,
        n_compartments,
        tau_ms=500.0,
        learning_rate=0.0005,
        gain_bounds=(0.5, 1.5),
        gains=None,
        plasticity_onset_ms=0.0,
        dan_baseline_window_ms=0.0,
        dan_reference='none',
    ):
        self.ptr = _integer_array(ptr, np.int64, 'ptr')
        self.post = _integer_array(post, np.int32, 'post')
        self.weights = np.array(weights, dtype=np.float32, order='C', copy=True)
        self.sensory = _integer_array(sensory, np.int32, 'sensory')
        self.kc_indices = _integer_array(kc_indices, np.int32, 'kc_indices')
        self.dan_indices = _integer_array(dan_indices, np.int32, 'dan_indices')
        self.dan_compartments = _integer_array(dan_compartments, np.int32, 'dan_compartments')
        self.plastic_edge_indices = _integer_array(plastic_edge_indices, np.int64, 'plastic_edge_indices')
        self.plastic_kc_indices = _integer_array(plastic_kc_indices, np.int32, 'plastic_kc_indices')
        self.plastic_compartments = _integer_array(
            plastic_compartments, np.int32, 'plastic_compartments'
        )
        self.n = len(self.ptr) - 1
        sizes = {
            len(self.plastic_edge_indices), len(self.plastic_kc_indices), len(self.plastic_compartments)
        }
        bounds = np.asarray(gain_bounds, dtype=np.float64)
        timing = np.array([plasticity_onset_ms, dan_baseline_window_ms], dtype=np.float64)
        timing_steps = timing / 0.2
        scalar_config = np.array([tau_ms, learning_rate, n_compartments, *timing], dtype=np.float64)
        native_float_values = np.array([tau_ms, learning_rate, *bounds.ravel()], dtype=np.float64)
        native_float_limit = np.finfo(np.float32).max
        native_float_floor = float(np.nextafter(np.float32(0), np.float32(1)))
        if dan_reference not in DAN_REFERENCE_MODES:
            raise ValueError(f'dan_reference must be one of {sorted(DAN_REFERENCE_MODES)}.')
        if (
            self.weights.ndim != 1
            or self.n < 1
            or self.ptr[0] != 0
            or self.ptr[-1] != len(self.post)
            or len(self.post) != len(self.weights)
            or np.any(np.diff(self.ptr) < 0)
            or np.any(self.post < 0)
            or np.any(self.post >= self.n)
            or not np.isfinite(self.weights).all()
            or any(np.any(values < 0) or np.any(values >= self.n) for values in
                   (self.sensory, self.kc_indices, self.dan_indices))
            or any(len(np.unique(values)) != len(values) for values in
                   (self.sensory, self.kc_indices, self.dan_indices))
            or len(self.dan_compartments) != len(self.dan_indices)
            or len(sizes) != 1
            or bounds.shape != (2,)
            or not np.isfinite(bounds).all()
            or not np.isfinite(scalar_config).all()
            or np.any(np.abs(native_float_values) > native_float_limit)
            or np.any((native_float_values != 0) & (np.abs(native_float_values) < native_float_floor))
            or int(n_compartments) != n_compartments
            or n_compartments < 1
            or n_compartments > np.iinfo(np.int32).max
            or tau_ms <= 0
            or learning_rate <= 0
            or np.any(timing < 0)
            or timing[1] > timing[0]
            or not np.allclose(timing_steps, np.rint(timing_steps), rtol=0, atol=1e-7)
            or timing_steps[0] > np.iinfo(np.int32).max
            or bounds[0] <= 0
            or bounds[0] > bounds[1]
            or np.any(self.dan_compartments < 0)
            or np.any(self.dan_compartments >= n_compartments)
            or np.any(self.plastic_edge_indices < 0)
            or np.any(self.plastic_edge_indices >= len(self.post))
            or len(np.unique(self.plastic_edge_indices)) != len(self.plastic_edge_indices)
            or np.any(self.plastic_kc_indices < 0)
            or np.any(self.plastic_kc_indices >= len(self.kc_indices))
            or np.any(self.plastic_compartments < 0)
            or np.any(self.plastic_compartments >= n_compartments)
            or np.intersect1d(self.sensory, self.dan_indices).size
        ):
            raise ValueError('Invalid reward graph or learning configuration.')
        if len(self.plastic_edge_indices):
            plastic_sources = np.searchsorted(
                self.ptr, self.plastic_edge_indices, side='right'
            ) - 1
            expected_sources = self.kc_indices[self.plastic_kc_indices]
            if not np.array_equal(plastic_sources, expected_sources):
                raise ValueError('Each plastic edge must originate at its listed KC.')
        self.n_compartments = int(n_compartments)
        self.tau_ms = float(tau_ms)
        self.learning_rate = float(learning_rate)
        self.gain_bounds = (float(bounds[0]), float(bounds[1]))
        self.plasticity_onset_ms = float(timing[0])
        self.dan_baseline_window_ms = float(timing[1])
        self.dan_reference = str(dan_reference)
        self._onset_steps = int(np.rint(timing_steps[0]))
        self._baseline_steps = int(np.rint(timing_steps[1]))
        if gains is None:
            gains = np.ones(len(self.plastic_edge_indices), np.float32)
        self.gains = np.array(gains, dtype=np.float32, order='C', copy=True)
        if self.gains.shape != self.plastic_edge_indices.shape:
            raise ValueError('Initial gains must align with the plastic edge list.')
        self._validate_gains()
        for array in (
            self.ptr, self.post, self.weights, self.sensory, self.kc_indices, self.dan_indices,
            self.dan_compartments, self.plastic_edge_indices, self.plastic_kc_indices,
            self.plastic_compartments,
        ):
            array.setflags(write=False)
        self.lib = _native_library()

    def _validate_gains(self):
        if (
            not isinstance(self.gains, np.ndarray)
            or self.gains.dtype != np.float32
            or self.gains.shape != self.plastic_edge_indices.shape
            or not self.gains.flags.c_contiguous
            or not self.gains.flags.writeable
            or not np.isfinite(self.gains).all()
            or np.any(self.gains < self.gain_bounds[0])
            or np.any(self.gains > self.gain_bounds[1])
        ):
            raise ValueError('Gains must be finite and inside the configured positive bounds.')

    def run(
        self,
        rate_schedule,
        *,
        bin_ms=10.0,
        teaching_pulses=(),
        dt=0.2,
        seed=42,
        plasticity=True,
        sample=None,
        record=False,
        plastic_groups=None,
        n_groups=None,
    ):
        if (
            not isinstance(seed, (int, np.integer))
            or isinstance(seed, (bool, np.bool_))
            or not 0 <= int(seed) <= np.iinfo(np.uint64).max
            or not isinstance(plasticity, (bool, np.bool_))
            or not isinstance(record, (bool, np.bool_))
        ):
            raise ValueError('seed must be an unsigned 64-bit integer and plasticity must be boolean.')
        rates = np.ascontiguousarray(rate_schedule, dtype=np.float32)
        if rates.ndim != 2 or rates.shape[1:] != self.sensory.shape:
            raise ValueError('rate_schedule must have shape [n_bins, n_sensory].')
        ratio = float(bin_ms) / float(dt) if dt else np.nan
        bin_steps = int(round(ratio)) if np.isfinite(ratio) else 0
        duration_ms = rates.shape[0] * float(bin_ms)
        if (
            dt != 0.2
            or rates.shape[0] < 1
            or rates.size > _MAX_SCHEDULE_VALUES
            or not np.isfinite(rates).all()
            or np.any(rates < 0)
            or np.any(rates > 5000)
            or not np.isfinite(bin_ms)
            or bin_ms < dt
            or not np.isclose(ratio, bin_steps, rtol=0, atol=1e-7)
            or not 0 < duration_ms <= 10000
        ):
            raise ValueError('Invalid schedule; dt is fixed at 0.2 ms and duration is at most 10 seconds.')
        sample = _integer_array(np.array([], np.int32) if sample is None else sample, np.int32, 'sample')
        if (
            np.any(sample < 0)
            or np.any(sample >= self.n)
            or len(np.unique(sample)) != len(sample)
            or rates.shape[0] * len(sample) > _MAX_TRACE_VALUES
        ):
            raise ValueError('Invalid or excessively large sampled trace request.')
        n_plastic = len(self.plastic_edge_indices)
        if plastic_groups is None:
            groups = np.zeros(n_plastic, np.int32)
        else:
            groups = _integer_array(plastic_groups, np.int32, 'plastic_groups')
        if groups.shape != (n_plastic,) or (groups.size and groups.min() < 0):
            raise ValueError('plastic_groups must give one nonnegative group id per plastic edge.')
        inferred = int(groups.max()) + 1 if groups.size else 1
        if n_groups is None:
            n_groups = inferred
        elif (not isinstance(n_groups, (int, np.integer)) or isinstance(n_groups, (bool, np.bool_))
              or n_groups < inferred or n_groups > np.iinfo(np.int32).max):
            raise ValueError('n_groups must be an integer at least one more than the largest group id.')
        n_groups = int(n_groups)
        n_bins = rates.shape[0]
        if record and (n_bins * n_groups * RULE_WIDTH > _MAX_TRACE_VALUES
                       or n_bins * max(len(self.kc_indices), 1) > _MAX_TRACE_VALUES):
            raise ValueError('Excessively large instrumentation request.')
        pulses = np.asarray(teaching_pulses)
        if pulses.size == 0:
            pulses = np.empty((0, 2), np.float64)
        if pulses.ndim != 2 or pulses.shape[1] != 2 or not np.isfinite(pulses).all():
            raise ValueError('teaching_pulses must contain finite (time_ms, dan_local_index) rows.')
        pulse_steps_float = pulses[:, 0].astype(np.float64) / dt
        pulse_dans_float = pulses[:, 1].astype(np.float64)
        pulse_steps = np.ascontiguousarray(np.rint(pulse_steps_float), dtype=np.int32)
        pulse_dans = np.ascontiguousarray(np.rint(pulse_dans_float), dtype=np.int32)
        steps = rates.shape[0] * bin_steps
        if self._onset_steps >= steps:
            raise ValueError('plasticity_onset_ms must fall inside the trial.')
        if (
            np.any(pulses[:, 0] < 0)
            or np.any(pulses[:, 0] >= duration_ms)
            or not np.allclose(pulse_steps_float, pulse_steps, rtol=0, atol=1e-7)
            or not np.array_equal(pulse_dans_float, pulse_dans.astype(np.float64))
            or np.any(pulse_dans < 0)
            or np.any(pulse_dans >= len(self.dan_indices))
        ):
            raise ValueError('Teaching pulses must be dt-aligned and reference local DAN indices.')
        pulse_order = np.argsort(pulse_steps, kind='stable')
        native_pulse_steps = np.ascontiguousarray(pulse_steps[pulse_order])
        native_pulse_dans = np.ascontiguousarray(pulse_dans[pulse_order])
        self._validate_gains()
        counts = np.zeros(self.n, np.int32)
        voltage = np.zeros(self.n, np.float32)
        trace = np.zeros((rates.shape[0], len(sample)), np.int32)
        population = np.zeros(rates.shape[0], np.int32)
        dan_counts = np.zeros(len(self.dan_indices), np.int32)
        compartment_counts = np.zeros(self.n_compartments, np.int32)
        tonic = np.zeros(self.n_compartments, np.float32)
        gains_before = self.gains.copy()
        native_gains = self.gains if plasticity else self.gains.copy()
        if record:
            signal_bins = np.zeros((n_bins, self.n_compartments, SIGNAL_WIDTH), np.float64)
            kc_signal_bins = np.zeros((n_bins, KC_SIGNAL_WIDTH), np.float64)
            rule_bins = np.zeros((n_bins, n_groups, RULE_WIDTH), np.float64)
            kc_trace_bins = np.zeros((n_bins, len(self.kc_indices)), np.float32)
        else:
            signal_bins = np.zeros(0, np.float64)
            kc_signal_bins = np.zeros(0, np.float64)
            rule_bins = np.zeros(0, np.float64)
            kc_trace_bins = np.zeros(0, np.float32)
        start = time.perf_counter()
        result = self.lib.simulate_reward(
            self.n, self.ptr, self.post, self.weights, len(self.sensory), self.sensory, rates, bin_steps,
            steps, dt, int(seed), len(self.kc_indices), self.kc_indices, len(self.dan_indices),
            self.dan_indices, self.dan_compartments, len(self.plastic_edge_indices),
            self.plastic_edge_indices, self.plastic_kc_indices, self.plastic_compartments,
            self.n_compartments, self.tau_ms, self.learning_rate if plasticity else 0.0,
            self.gain_bounds[0], self.gain_bounds[1], native_gains, self._onset_steps, self._baseline_steps,
            tonic, len(pulse_steps), native_pulse_steps,
            native_pulse_dans, len(sample), sample, bin_steps, counts, voltage, trace, population,
            dan_counts, compartment_counts,
            int(record), n_groups, groups, signal_bins, kc_signal_bins, rule_bins, kc_trace_bins,
            DAN_REFERENCE_MODES[self.dan_reference],
        )
        if result:
            raise RuntimeError('Native reward simulation failed.')
        return {
            'counts': counts,
            'rates': counts.astype(np.float32) * (1000 / duration_ms),
            'rates_hz': counts.astype(np.float32) * (1000 / duration_ms),
            'voltage': voltage,
            'trace': trace,
            'population': population,
            'dan_counts': dan_counts,
            'compartment_dan_counts': compartment_counts,
            'compartment_tonic_hz': tonic * np.float32(1000 / dt),
            'gains': self.gains.copy(),
            'gain_delta': self.gains - gains_before,
            'pulse_times_ms': pulses[:, 0].astype(np.float32),
            'pulse_dan_indices': pulse_dans.copy(),
            'duration_ms': duration_ms,
            'dt': dt,
            'bin_ms': float(bin_ms),
            'wall_seconds': time.perf_counter() - start,
            'instrumentation': dict(
                signal_bins=signal_bins, kc_signal_bins=kc_signal_bins, rule_bins=rule_bins,
                kc_trace_bins=kc_trace_bins, plastic_groups=groups,
                layout=dict(signal_bins=['dan_mean_spikes', 'dan_trace_end', 'dan_signal_after_reference',
                                         'reference_per_step'],
                            kc_signal_bins=['kc_spikes', 'kc_trace_mass_end'],
                            rule_bins=['term_dbar_k', 'term_kbar_d', 'applied', 'clipped_low', 'clipped_high',
                                       'kc_events_on_edges', 'kbar_mass_on_edges_end']),
            ) if record else None,
        }
