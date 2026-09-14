"""Associative (dopamine-gated) learning engine on the MaleCNS graph.

New experiment family. It leaves the sensory, reward and v1 engines untouched.
The circuit is the full retained graph at the qualified 0.11 mV/contact coupling;
its interventions (antennal-lobe local-neuron output, APL output and pure-dopamine
fast output set to zero) are declared in the protocol and justified by measured
runaway/silencing evidence, not inherited from the legacy reward diagnostic.

State lifetimes (declared):
  * membrane voltage, synaptic state, event queue, refractory clocks: reset every call;
  * KC eligibility traces and compartment dopamine traces: reset every call unless the
    caller passes explicit initial traces; final traces are always returned;
  * synaptic gains: persist on the engine between calls; explicit checkpoint/restore;
    a call with plasticity=False leaves them byte-identical (verified after each call).
"""
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

from .connectome import ROOT
from .reward_brain import _integer_array

EVENT_MV = 68.75
COMP_WIDTH = 8
COMP_LAYOUT = ['coupled_dan_mean_spikes', 'potentiation_terms', 'depression_terms',
               'applied_gain_change', 'low_bound_contacts', 'high_bound_contacts',
               'kc_trace_mass_on_eligible_edges_bin_end', 'recovery_terms']
_BUILD_LOCK = threading.Lock()


def _native():
    source = Path(__file__).with_name('associative_lif.cpp')
    version = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    build = ROOT / 'output/native'
    build.mkdir(parents=True, exist_ok=True)
    dest = build / f'associative-{version}.{"dylib" if platform.system() == "Darwin" else "so"}'
    with _BUILD_LOCK:
        if not dest.exists():
            temporary = dest.with_suffix('.partial')
            subprocess.run(['c++', '-O3', '-std=c++17', '-shared', '-fPIC', str(source),
                            '-o', str(temporary)], check=True, capture_output=True)
            temporary.replace(dest)
    lib = ctypes.CDLL(str(dest))
    i32 = np.ctypeslib.ndpointer(dtype=np.int32, flags='C_CONTIGUOUS')
    i64 = np.ctypeslib.ndpointer(dtype=np.int64, flags='C_CONTIGUOUS')
    f32 = np.ctypeslib.ndpointer(dtype=np.float32, flags='C_CONTIGUOUS')
    f64 = np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')
    u8 = np.ctypeslib.ndpointer(dtype=np.uint8, flags='C_CONTIGUOUS')
    c = ctypes
    lib.simulate_associative.argtypes = [
        c.c_int, i64, i32, f32,
        c.c_int, i32, f32,
        c.c_int, i32, f32,
        c.c_int, c.c_int, c.c_float, c.c_uint64,
        c.c_int, i32,
        c.c_int, i32, i32, c.c_int, f32,
        c.c_int, i64, i32, i32, u8,
        f32, c.c_float, c.c_float, c.c_float, c.c_float, c.c_float,
        f32, f32, f32, c.c_float,
        c.c_int, i32,
        i32, f32, i32, i32, i32, i32, f64, f64, f64,
    ]
    lib.simulate_associative.restype = ctypes.c_int
    return lib, dest, version


def atomic_json(path, payload):
    """Atomic JSON write (no torch-dependent experiment import for the associative stage)."""
    import os
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=False, default=_json_default) + '\n')
    os.replace(temporary, path)


def _json_default(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f'Not JSON serializable: {type(value).__name__}')


def array_sha256(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


class AssociativeEngine:
    """Full-graph LIF with persistent dopamine-gated KC->MBON gains and a reinforcer drive."""

    def __init__(self, ptr, post, weights, sensory, kc_indices, dan_indices, dan_compartments,
                 plastic_edges, plastic_kc, plastic_compartments, *, n_compartments, drive_indices=(),
                 plastic_mask=None, tau_kc_ms=1000., tau_dan_ms=1000., learning_rate=1e-3,
                 gain_bounds=(0.5, 1.5), gains=None, coupling=None, recovery=None, rest_gain=1.0):
        self.ptr = _integer_array(ptr, np.int64, 'ptr')
        self.post = _integer_array(post, np.int32, 'post')
        self.weights = np.array(weights, np.float32, order='C', copy=True)
        self.sensory = _integer_array(sensory, np.int32, 'sensory')
        self.drive_indices = _integer_array(np.asarray(drive_indices, np.int64), np.int32, 'drive_indices')
        self.kc_indices = _integer_array(kc_indices, np.int32, 'kc_indices')
        self.dan_indices = _integer_array(dan_indices, np.int32, 'dan_indices')
        self.dan_compartments = _integer_array(dan_compartments, np.int32, 'dan_compartments')
        def empty_ok(value):
            return np.asarray(value, np.int64) if len(value) == 0 else value
        self.plastic_edges = _integer_array(empty_ok(plastic_edges), np.int64, 'plastic_edges')
        self.plastic_kc = _integer_array(empty_ok(plastic_kc), np.int32, 'plastic_kc')
        self.plastic_compartments = _integer_array(empty_ok(plastic_compartments), np.int32, 'plastic_compartments')
        self.n = len(self.ptr) - 1
        self.n_compartments = int(n_compartments)
        bounds = np.asarray(gain_bounds, np.float64)
        if (self.n < 1 or self.ptr[0] != 0 or self.ptr[-1] != len(self.post) or np.any(np.diff(self.ptr) < 0)
                or self.weights.shape != self.post.shape or not np.isfinite(self.weights).all()
                or np.any(self.post < 0) or np.any(self.post >= self.n)
                or any(np.any(a < 0) or np.any(a >= self.n) or len(np.unique(a)) != len(a)
                       for a in (self.sensory, self.kc_indices, self.dan_indices, self.drive_indices))
                or np.intersect1d(self.sensory, self.drive_indices).size
                or len(self.dan_compartments) != len(self.dan_indices)
                or int(n_compartments) != n_compartments or n_compartments < 1
                or np.any(self.dan_compartments < 0) or np.any(self.dan_compartments >= n_compartments)
                or not len({len(self.plastic_edges), len(self.plastic_kc), len(self.plastic_compartments)}) == 1
                or np.any(self.plastic_edges < 0) or np.any(self.plastic_edges >= len(self.post))
                or len(np.unique(self.plastic_edges)) != len(self.plastic_edges)
                or np.any(self.plastic_kc < 0) or np.any(self.plastic_kc >= len(self.kc_indices))
                or np.any(self.plastic_compartments < 0) or np.any(self.plastic_compartments >= n_compartments)
                or bounds.shape != (2,) or not np.isfinite(bounds).all() or bounds[0] <= 0 or bounds[0] > bounds[1]
                or not all(np.isfinite(x) and x > 0 for x in (tau_kc_ms, tau_dan_ms))
                or not np.isfinite(learning_rate) or learning_rate < 0):
            raise ValueError('Invalid associative graph or learning configuration.')
        if len(self.plastic_edges):
            sources = np.searchsorted(self.ptr, self.plastic_edges, side='right') - 1
            if not np.array_equal(sources, self.kc_indices[self.plastic_kc]):
                raise ValueError('Each plastic edge must originate at its listed KC.')
        mask = np.ones(len(self.plastic_edges), np.uint8) if plastic_mask is None else np.asarray(plastic_mask)
        if mask.shape != self.plastic_edges.shape or mask.dtype.kind not in 'iub' or not np.isin(mask, [0, 1]).all():
            raise ValueError('plastic_mask must hold one 0/1 flag per plastic edge.')
        self.plastic_mask = np.array(mask, np.uint8, order='C', copy=True)
        coupling = np.ones(self.n_compartments, np.float32) if coupling is None else np.asarray(coupling, np.float32)
        if coupling.shape != (self.n_compartments,) or not np.isfinite(coupling).all() or np.any(coupling < 0):
            raise ValueError('coupling must hold one nonnegative dopamine coupling per compartment.')
        self.coupling = np.array(coupling, np.float32, order='C', copy=True)
        recovery = np.zeros(self.n_compartments, np.float32) if recovery is None else np.asarray(recovery, np.float32)
        if (recovery.shape != (self.n_compartments,) or not np.isfinite(recovery).all() or np.any(recovery < 0)
                or not np.isfinite(rest_gain) or not bounds[0] <= rest_gain <= bounds[1]):
            raise ValueError('recovery must hold one nonnegative rate per compartment; rest_gain must lie inside the bounds.')
        self.recovery = np.array(recovery, np.float32, order='C', copy=True)
        self.rest_gain = float(rest_gain)
        self.tau_kc_ms, self.tau_dan_ms = float(tau_kc_ms), float(tau_dan_ms)
        self.learning_rate = float(learning_rate)
        self.gain_bounds = (float(bounds[0]), float(bounds[1]))
        self.gains = (np.ones(len(self.plastic_edges), np.float32) if gains is None
                      else np.array(gains, np.float32, order='C', copy=True))
        self._validate_gains()
        for array in (self.ptr, self.post, self.weights, self.sensory, self.drive_indices, self.kc_indices,
                      self.dan_indices, self.dan_compartments, self.plastic_edges, self.plastic_kc,
                      self.plastic_compartments, self.plastic_mask, self.coupling, self.recovery):
            array.setflags(write=False)
        self.lib, self.native_path, self.native_version = _native()
        self.calls = 0

    def _validate_gains(self):
        if (not isinstance(self.gains, np.ndarray) or self.gains.dtype != np.float32
                or self.gains.shape != self.plastic_edges.shape or not self.gains.flags.c_contiguous
                or not np.isfinite(self.gains).all() or np.any(self.gains < self.gain_bounds[0])
                or np.any(self.gains > self.gain_bounds[1])):
            raise ValueError('Gains must be finite float32 inside the configured bounds.')

    def gains_sha256(self):
        return array_sha256(self.gains)

    def set_coupling(self, coupling):
        """Dopamine-to-plasticity coupling per compartment (0 = causal lesion; spikes unchanged)."""
        values = np.asarray(coupling, np.float32)
        if values.shape != (self.n_compartments,) or not np.isfinite(values).all() or np.any(values < 0):
            raise ValueError('coupling must hold one nonnegative value per compartment.')
        self.coupling = np.array(values, np.float32, order='C', copy=True)
        self.coupling.setflags(write=False)

    def set_gains(self, gains):
        gains = np.array(gains, np.float32, order='C', copy=True)
        previous = self.gains
        self.gains = gains
        try:
            self._validate_gains()
        except ValueError:
            self.gains = previous
            raise

    def run(self, rates, *, drive=None, bin_ms=20., dt=.2, seed=17, plasticity=False, sample=(),
            traces=None):
        raw = np.asarray(rates, np.float64)
        drive_raw = (np.zeros((len(raw), len(self.drive_indices)), np.float64) if drive is None
                     else np.asarray(drive, np.float64))
        sample = _integer_array(np.asarray(sample, np.int64) if len(sample) == 0 else sample, np.int32, 'sample')
        if (dt not in (.1, .2) or not np.isfinite(bin_ms) or bin_ms < dt or abs(bin_ms/dt-round(bin_ms/dt)) > 1e-7
                or raw.ndim != 2 or raw.shape[1] != len(self.sensory) or len(raw) == 0
                or len(raw)*bin_ms > 10000 or raw.size > 50_000_000 or len(raw)*len(sample) > 50_000_000
                or not np.isfinite(raw).all() or np.any(raw < 0) or np.any(raw > 1000/dt)
                or drive_raw.shape != (len(raw), len(self.drive_indices)) or not np.isfinite(drive_raw).all()
                or np.any(drive_raw < 0) or np.any(drive_raw > 1000/dt)
                or np.any(sample < 0) or np.any(sample >= self.n) or len(np.unique(sample)) != len(sample)
                or not isinstance(seed, (int, np.integer)) or isinstance(seed, (bool, np.bool_))
                or not 0 <= int(seed) <= 2**64-1 or not isinstance(plasticity, (bool, np.bool_))):
            raise ValueError('Invalid associative schedule, drive, timing, sample or seed.')
        if traces is None:
            kc_trace = np.zeros(len(self.kc_indices), np.float32)
            dan_trace = np.zeros(self.n_compartments, np.float32)
        else:
            kc_trace = np.array(traces['kc'], np.float32, order='C', copy=True)
            dan_trace = np.array(traces['dan'], np.float32, order='C', copy=True)
            if (kc_trace.shape != (len(self.kc_indices),) or dan_trace.shape != (self.n_compartments,)
                    or not np.isfinite(kc_trace).all() or not np.isfinite(dan_trace).all()
                    or np.any(kc_trace < 0) or np.any(dan_trace < 0)):
                raise ValueError('Initial traces must be finite, nonnegative and shaped to the circuit.')
        self._validate_gains()
        rates32 = np.ascontiguousarray(raw, np.float32)
        drive32 = np.ascontiguousarray(drive_raw, np.float32)
        bins = len(rates32)
        counts = np.zeros(self.n, np.int32)
        voltage = np.zeros(self.n, np.float32)
        trace = np.zeros((bins, len(sample)), np.int32)
        inputs = np.zeros(rates32.shape, np.int32)
        drive_events = np.zeros(drive32.shape, np.int32)
        population = np.zeros(bins, np.int32)
        comp_bins = np.zeros((bins, self.n_compartments, COMP_WIDTH), np.float64)
        extrema = np.zeros(2, np.float64)
        audit = np.zeros(2, np.float64)
        before = self.gains.copy()
        native_gains = self.gains if plasticity else self.gains.copy()
        eta = self.learning_rate if plasticity else 0.0
        start = time.monotonic()
        status = self.lib.simulate_associative(
            self.n, self.ptr, self.post, self.weights,
            len(self.sensory), self.sensory, rates32,
            len(self.drive_indices), self.drive_indices, drive32,
            int(round(bin_ms/dt)), int(bins*round(bin_ms/dt)), dt, int(seed),
            len(self.kc_indices), self.kc_indices,
            len(self.dan_indices), self.dan_indices, self.dan_compartments, self.n_compartments, self.coupling,
            len(self.plastic_edges), self.plastic_edges, self.plastic_kc, self.plastic_compartments,
            self.plastic_mask,
            native_gains, self.tau_kc_ms, self.tau_dan_ms, eta, self.gain_bounds[0], self.gain_bounds[1],
            kc_trace, dan_trace, self.recovery, self.rest_gain,
            len(sample), sample,
            counts, voltage, trace, inputs, drive_events, population, comp_bins, extrema, audit)
        if status:
            raise RuntimeError(f'Associative simulation failed numerical/resource check ({status}).')
        if not plasticity and self.gains.tobytes() != before.tobytes():
            raise RuntimeError('Plasticity-off call changed gains.')
        self._validate_gains()
        self.calls += 1
        return dict(counts=counts, voltage=voltage, trace=trace, input_events=inputs, drive_events=drive_events,
                    population=population, comp_bins=comp_bins, comp_layout=list(COMP_LAYOUT),
                    gains=self.gains.copy(), gain_delta=self.gains - before,
                    gains_sha256_before=array_sha256(before), gains_sha256_after=self.gains_sha256(),
                    traces=dict(kc=kc_trace, dan=dan_trace), plasticity=bool(plasticity),
                    max_abs_voltage_offset_mv=float(extrema[0]), max_abs_synaptic_state_mv=float(extrema[1]),
                    mean_active_neurons=float(audit[0])/max(1, bins*round(bin_ms/dt)),
                    final_active_neurons=int(audit[1]), wall_seconds=time.monotonic()-start,
                    duration_ms=bins*bin_ms, dt_ms=dt, bin_ms=bin_ms, seed=int(seed))


# ----------------------------------------------------------------------------------------------
# Circuit construction from a protocol.

def team_odor_types(team_key, types, n=4, salt='BET36FLY-team-odor-01'):
    """Deterministic identity code: n distinct ORN types per team key, same rule for every team."""
    types = list(types)
    if len(set(types)) != len(types) or n < 1 or n > len(types) or not isinstance(team_key, str) or not team_key:
        raise ValueError('Odor code needs distinct types, a positive width and a nonempty team key.')
    ranked = sorted(types, key=lambda t: hashlib.sha256(f'{salt}:{team_key}:{t}'.encode()).hexdigest())
    return sorted(ranked[:n])


def build_circuit(root, protocol):
    """Construct the associative circuit and return engine plus exact anatomy record."""
    import pyarrow.feather as feather

    root = Path(root)
    path = root / 'data/brain'
    ids, ptr, post, contacts, signs = [np.load(path / f'{k}.npy', allow_pickle=False)
                                       for k in ('ids', 'indptr', 'post', 'counts', 'signs')]
    nodes = feather.read_table(path / 'nodes.feather').to_pandas()
    if nodes.bodyId.duplicated().any():
        raise ValueError('Duplicate anatomical identities.')
    nodes = nodes.set_index('bodyId').reindex(ids)
    types = nodes['type'].fillna('').to_numpy()
    classes = nodes['class'].fillna('').to_numpy()
    transmitter = nodes['transmitter'].fillna('').to_numpy()
    src = np.repeat(np.arange(len(ids)), np.diff(ptr))
    weights = (contacts * np.repeat(signs.astype(np.float32), np.diff(ptr))
               * np.float32(protocol['contact_mv'])).astype(np.float32)
    interventions = {}
    for name, cells, side, factor in (
            ('alln_output_gain', np.flatnonzero(classes == 'ALLN'), 'out', protocol['alln_output_gain']),
            ('apl_output_gain', np.flatnonzero((types == 'APL') & (transmitter == 'gaba')), 'out',
             protocol['apl_output_gain']),
            ('dopamine_fast_output_gain', np.flatnonzero(transmitter == 'dopamine'), 'out',
             protocol['dopamine_fast_output_gain'])):
        edges = np.isin(src, cells) if side == 'out' else np.isin(post, cells)
        weights[edges] *= np.float32(factor)
        interventions[name] = dict(factor=factor, cells=int(len(cells)), edges=int(edges.sum()))
    kc = np.flatnonzero(classes == 'Kenyon_Cell').astype(np.int32)
    orn_types = sorted(t for t in set(types[classes == 'olfactory']) if t.startswith('ORN_'))
    orn_cells = np.flatnonzero((classes == 'olfactory') & np.isin(types, orn_types)).astype(np.int32)
    assay = json.loads((root / protocol['taste_assay']).read_text())
    taste = {k: np.searchsorted(ids, assay['populations'][k]).astype(np.int32) for k in ('sweet', 'bitter')}
    for k, v in taste.items():
        if not np.array_equal(ids[v], assay['populations'][k]):
            raise ValueError(f'Taste population {k} is not present in the graph.')
    sensory = np.unique(np.concatenate([orn_cells, taste['sweet'], taste['bitter']])).astype(np.int32)
    outputs, dans, dcomp, drive, compartments = [], [], [], [], []
    for c, comp in enumerate(protocol['compartments']):
        d = np.flatnonzero((types == comp['dan_type']) & (classes == 'DAN') & (transmitter == 'dopamine'))
        m = np.flatnonzero((types == comp['mbon_type']) & (classes == 'MBON'))
        if not len(d) or not len(m):
            raise ValueError(f'Missing compartment population {comp}.')
        outputs.append(m)
        dans.extend(d.tolist())
        dcomp.extend([c] * len(d))
        drive.extend(d.tolist())
        compartments.append(dict(comp, dan_cells=int(len(d)), mbon_cells=int(len(m)),
                                 dan_body_ids=ids[d].tolist(), mbon_body_ids=ids[m].tolist(),
                                 mbon_transmitter=sorted(set(transmitter[m]))))
    lookup = np.full(len(ids), -1, np.int32)
    for c, m in enumerate(outputs):
        if np.any(lookup[m] != -1):
            raise ValueError('Output populations must be distinct.')
        lookup[m] = c
    edges, cells, comps = [], [], []
    kc_class = np.array([('gamma' if t.startswith('KCg') else 'apbp' if t.startswith("KCa'b'")
                          else 'ab' if t.startswith('KCab') else 'other') for t in types[kc]])
    for k, pre in enumerate(kc):
        lo, hi = ptr[pre], ptr[pre + 1]
        chosen = np.flatnonzero(lookup[post[lo:hi]] >= 0)
        edges.extend((lo + chosen).tolist())
        cells.extend([k] * len(chosen))
        comps.extend(lookup[post[lo + chosen]].tolist())
    edges, cells, comps = np.asarray(edges, np.int64), np.asarray(cells, np.int32), np.asarray(comps, np.int32)
    if not len(edges) or set(comps.tolist()) != set(range(len(outputs))) or not np.all(weights[edges] > 0):
        raise ValueError('Every compartment needs existing excitatory KC->MBON edges.')
    mask = np.ones(len(edges), np.uint8)
    for c, comp in enumerate(protocol['compartments']):
        wanted = comp.get('kc_class', 'all')
        if wanted != 'all':
            mask[(comps == c) & (kc_class[cells] != wanted)] = 0
        compartments[c].update(plastic_edges=int((comps == c).sum()), eligible_edges=int(mask[comps == c].sum()),
                               by_class={x: int(((comps == c) & (kc_class[cells] == x)).sum())
                                         for x in ('gamma', 'apbp', 'ab', 'other')})
    engine = AssociativeEngine(ptr, post, weights, sensory, kc, np.asarray(dans), np.asarray(dcomp), edges, cells,
                               comps, n_compartments=len(outputs), drive_indices=np.unique(drive),
                               plastic_mask=mask, tau_kc_ms=protocol['tau_kc_ms'], tau_dan_ms=protocol['tau_dan_ms'],
                               learning_rate=protocol['learning_rate'], gain_bounds=tuple(protocol['gain_bounds']),
                               coupling=protocol.get('coupling'), recovery=protocol.get('recovery'),
                               rest_gain=protocol.get('rest_gain', 1.0))
    anatomy = dict(neurons=int(len(ids)), edges=int(len(post)), contact_mv=protocol['contact_mv'],
                   interventions=interventions, sensory_inputs=int(len(sensory)), orn_types=orn_types,
                   orn_cells=int(len(orn_cells)), taste={k: ids[v].tolist() for k, v in taste.items()},
                   compartments=compartments, plastic_edges=int(len(edges)), eligible_edges=int(mask.sum()),
                   kc=int(len(kc)), drive_cells=int(len(np.unique(drive))),
                   recovery=[float(x) for x in engine.recovery], rest_gain=engine.rest_gain,
                   rule_version=2 if np.any(engine.recovery > 0) else 1,
                   graph_sha256={k: hashlib.sha256((path / f'{k}.npy').read_bytes()).hexdigest()
                                 for k in ('ids', 'indptr', 'post', 'counts', 'signs')},
                   nodes_sha256=hashlib.sha256((path / 'nodes.feather').read_bytes()).hexdigest(),
                   plastic_edges_sha256=array_sha256(edges), mask_sha256=array_sha256(mask),
                   native_source_sha256=hashlib.sha256(
                       (Path(__file__).with_name('associative_lif.cpp')).read_bytes()).hexdigest(),
                   circuit_sha256=None)
    anatomy['circuit_sha256'] = hashlib.sha256(json.dumps(
        {k: anatomy[k] for k in ('graph_sha256', 'nodes_sha256', 'plastic_edges_sha256', 'mask_sha256',
                                 'native_source_sha256', 'contact_mv', 'interventions')}, sort_keys=True).encode()
    ).hexdigest()
    circuit = dict(engine=engine, anatomy=anatomy, ids=ids, types=types, classes=classes, kc=kc,
                   outputs=outputs, orn_types=orn_types, orn_cells=orn_cells, taste=taste, sensory=sensory,
                   kc_class=kc_class)
    return circuit


def odor_schedule(circuit, odor_types, *, bins, start_bin, end_bin, hz):
    """Rates [bins x sensory] driving every ORN cell of the listed types at one anchored rate."""
    rates = np.zeros((bins, len(circuit['sensory'])), np.float32)
    cells = np.flatnonzero(np.isin(circuit['types'][circuit['sensory']], list(odor_types))
                           & (circuit['classes'][circuit['sensory']] == 'olfactory'))
    if not len(cells) or len(set(odor_types)) != len(odor_types):
        raise ValueError('Odor types must be distinct and present.')
    rates[start_bin:end_bin, cells] = hz
    return rates


def drive_schedule(circuit, *, bins, start_bin, end_bin, hz, compartments=None):
    """Reinforcer drive [bins x drive cells]; compartments None drives every listed DAN cell."""
    engine = circuit['engine']
    drive = np.zeros((bins, len(engine.drive_indices)), np.float32)
    if compartments is None:
        cols = np.arange(len(engine.drive_indices))
    else:
        wanted = engine.dan_indices[np.isin(engine.dan_compartments, list(compartments))]
        cols = np.flatnonzero(np.isin(engine.drive_indices, wanted))
    drive[start_bin:end_bin, cols] = hz
    return drive


def cue_response(circuit, result, window_bins):
    """Per-compartment MBON spike counts inside the cue window and KC activity (from sampled trace)."""
    raise NotImplementedError


# ----------------------------------------------------------------------------------------------
# Checkpoints

def save_checkpoint(path, engine, *, identity, parent_sha256=None, note=''):
    path = Path(path)
    gains = engine.gains.copy()
    meta = dict(schema='associative-checkpoint-1', identity=identity, gains_sha256=array_sha256(gains),
                parent_sha256=parent_sha256, edges=int(len(gains)), gain_bounds=list(engine.gain_bounds),
                mask_sha256=array_sha256(engine.plastic_mask), plastic_edges_sha256=array_sha256(engine.plastic_edges),
                note=note, calls=engine.calls)
    np.savez_compressed(path, gains=gains, meta=np.frombuffer(json.dumps(meta, sort_keys=True).encode(), np.uint8))
    return meta


def load_checkpoint(path):
    with np.load(Path(path), allow_pickle=False) as data:
        gains = data['gains'].copy()
        meta = json.loads(bytes(data['meta']).decode())
    if meta.get('schema') != 'associative-checkpoint-1' or array_sha256(gains) != meta['gains_sha256']:
        raise ValueError('Checkpoint identity/hash mismatch.')
    return gains, meta


def restore_checkpoint(engine, path, *, identity=None):
    gains, meta = load_checkpoint(path)
    if (meta['plastic_edges_sha256'] != array_sha256(engine.plastic_edges)
            or meta['mask_sha256'] != array_sha256(engine.plastic_mask)
            or (identity is not None and meta['identity'] != identity)):
        raise ValueError('Checkpoint belongs to a different circuit or identity.')
    engine.set_gains(gains)
    return meta
