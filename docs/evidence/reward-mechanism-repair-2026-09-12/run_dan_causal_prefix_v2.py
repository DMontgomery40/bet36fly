"""Version2: exact source index dtypes; bounded, output-only audit of saved current-bridge causal prefixes.

No simulator, native loader, capture driver, learning model or network import.
Every actual input must be explicitly hash-bound by the reviewed plan.
"""

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
import zipfile

import numpy as np
import dan_causal_prefix as prefix

ACTUAL_CONTRACT = dict(
    dt_ms=0.2, steps=2000, coarse_steps=50, populations=[2, 22], first_pulse_step=1550, expected_contrasts=64
)
ACTUAL_SHAPE = dict(
    steps=2000, coarse_steps=50, nk=4064, nd=24, ns=686, n=166700, ne=8866, ng=8, populations=[2, 22]
)
RUNS = ("diag-rate-bridge-v1-maskgamma-de050d773763", "diag-rate-bridge-v1-maskgamma-dea14759e9ca")
GAMES = ([4362, 4366, 4370, 4374, 4378, 4383, 4387, 4391], [4395, 4399, 4404, 4408, 4412, 4416, 4420, 4425])
PROTOCOL = dict(
    schema_version=3,
    seed=42,
    duration_ms=400.0,
    stimulus_ms=300.0,
    teaching_ms=310.0,
    bin_ms=10.0,
    plasticity_onset_ms=100.0,
    dan_baseline_window_ms=50.0,
    teaching_pulse_count=4,
    teaching_interval_ms=20.0,
    kc_input_gain=1.25,
    sensory_input_gain=0.0,
    apl_output_gain=0.25,
    global_weight_scale=0.5,
    tau_ms=500.0,
    learning_rate=0.0005,
    gain_bounds=[0.5, 1.5],
    dan_reference="none",
    away_plasticity_mask="gamma",
    learning_rule="rate-bridge-v1",
    rate_tau_ms=100.0,
    bridge_normalization=0.96,
    bridge_tail="analytic_no_new_event_tail",
    bridge_layout="rate-bridge-v1/1",
    encoder="glomerular-tuning-v1",
    encoder_peak_hz=150.0,
    encoder_tuning_width=0.5,
    encoder_min_kc_contacts=100.0,
)
MAX_MEMBER = 400_000_000


def require(ok, message):
    if not ok:
        raise ValueError(message)


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def bad(value):
        raise ValueError("nonfinite JSON constant")

    result = json.loads(data, object_pairs_hook=pairs, parse_constant=bad)

    def finite(x):
        if isinstance(x, float):
            require(math.isfinite(x), "nonfinite JSON number")
        elif isinstance(x, dict):
            for v in x.values():
                finite(v)
        elif isinstance(x, list):
            for v in x:
                finite(v)

    finite(result)
    return result


def atomic_json(path, value):
    path = Path(path)
    data = json.dumps(value, indent=2, allow_nan=False).encode() + b"\n"
    temporary = path.with_name(path.name + ".partial")
    with temporary.open("xb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)


def sha(path, guard=lambda: None):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            guard()
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    guard()
    return h.hexdigest()


def array_hash(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


class BoundInputs:
    def __init__(self, inputs, guard=lambda: None):
        require(isinstance(inputs, list) and inputs, "empty bound inventory")
        self.items = {}
        self.guard = guard
        for item in inputs:
            require(isinstance(item, dict), "invalid input binding")
            name = item.get("path")
            size = item.get("bytes")
            digest = item.get("sha256")
            require(
                isinstance(name, str) and Path(name).is_absolute() and ".." not in Path(name).parts,
                "invalid absolute input path",
            )
            require(type(size) is int and 0 <= size <= 16_000_000_000, "invalid bound byte count")
            require(isinstance(digest, str) and re.fullmatch("[0-9a-f]{64}", digest), "invalid input digest")
            require(name not in self.items, "duplicate bound input")
            self.items[name] = dict(item)

    def path(self, path):
        p = Path(path)
        require(str(p) in self.items, "unbound input path")
        require(not any(q.is_symlink() for q in [p, *p.parents]), "symbolic bound input")
        require(
            p.is_file() and p.stat().st_size == self.items[str(p)]["bytes"],
            "bound input missing or size changed",
        )
        return p

    def verify(self):
        for name, item in self.items.items():
            self.guard()
            require(sha(self.path(name), self.guard) == item["sha256"], "bound input hash changed")

    def bound_hash(self, path, digest):
        require(
            str(Path(path)) in self.items and self.items[str(Path(path))]["sha256"] == digest,
            "input identity not bound",
        )

    def json(self, path):
        p = self.path(path)
        require(p.stat().st_size <= 32_000_000, "JSON too large")
        self.guard()
        result = strict_json(p.read_bytes())
        self.guard()
        return result

    def archive(self, path):
        return NumericArchive(self.path(path), self.guard)

    def npy(self, path):
        p = self.path(path)
        self.guard()
        a = np.load(p, allow_pickle=False, mmap_mode="r")
        require(a.dtype.kind in "iufb" and not a.dtype.hasobject, "invalid numeric map")
        return a


class NumericArchive:
    def __init__(self, path, guard=lambda: None):
        self.guard = guard
        self.z = zipfile.ZipFile(path)
        self.names = {}
        try:
            total = 0
            for info in self.z.infolist():
                guard()
                name = info.filename
                require(
                    name.endswith(".npy") and Path(name).name == name and name not in self.names,
                    "invalid/duplicate NPZ member",
                )
                require(
                    0 < info.file_size <= MAX_MEMBER and not info.flag_bits & 1,
                    "oversized/encrypted NPZ member",
                )
                total += info.file_size
                require(total <= 8_000_000_000 and len(self.names) < 5000, "NPZ inventory too large")
                with self.z.open(info) as f:
                    version = np.lib.format.read_magic(f)
                    require(version in [(1, 0), (2, 0)], "unsupported NPY version")
                    shape, order, dtype = (
                        np.lib.format.read_array_header_1_0
                        if version == (1, 0)
                        else np.lib.format.read_array_header_2_0
                    )(f)
                    require(
                        dtype.kind in "iufb" and not dtype.hasobject and not dtype.fields, "non-numeric NPY"
                    )
                    require(
                        len(shape) <= 4 and all(type(x) is int and x >= 0 for x in shape),
                        "invalid NPY dimensions",
                    )
                    size = math.prod(shape) * dtype.itemsize
                    require(
                        size <= MAX_MEMBER and f.tell() + size == info.file_size,
                        "NPY declared payload mismatch",
                    )
                self.names[name] = info
        except BaseException:
            self.z.close()
            raise

    def array(self, name):
        self.guard()
        require(name + ".npy" in self.names, "missing NPZ array " + name)
        with self.z.open(self.names[name + ".npy"]) as f:
            a = np.load(f, allow_pickle=False)
        self.guard()
        return a

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.z.close()


def typed(a, dtype, shape, name, *, low=None, high=None, integer=False):
    require(
        isinstance(a, np.ndarray) and a.dtype == np.dtype(dtype) and a.shape == tuple(shape),
        name + " dtype/shape",
    )
    require(np.isfinite(a).all(), name + " nonfinite")
    if low is not None:
        require(np.all(a >= low), name + " below domain")
    if high is not None:
        require(np.all(a <= high), name + " above domain")
    if integer:
        require(np.all(a == np.floor(a)), name + " fractional count")
    return a


def equal(a, b, message):
    require(a.shape == b.shape and a.dtype == b.dtype and np.array_equal(a, b), message)


def validate_maps(m, s):
    size = s["nk"] + s["nd"] + s["ns"]
    n = s["n"]
    typed(m["sample"], "int32", (size,), "sample", low=0, high=n - 1)
    require(np.all(np.diff(m["sample"]) > 0), "sample ordering/duplicate")
    typed(m["body_ids"], "int64", (size,), "body_ids", low=1)
    require(len(np.unique(m["body_ids"])) == size, "duplicate body ID")
    occupied = []
    for role, count in [("kc", s["nk"]), ("dan", s["nd"]), ("sensory", s["ns"])]:
        indices = typed(m[role + "_indices"], "int32", (count,), role + " indices", low=0, high=n - 1)
        columns = typed(m[role + "_columns"], "int32", (count,), role + " columns", low=0, high=size - 1)
        require(len(np.unique(indices)) == count and len(np.unique(columns)) == count, "duplicate role")
        equal(m["sample"][columns], indices, "role/global mapping differs")
        occupied.extend(columns.tolist())
    require(len(set(occupied)) == size, "overlapping or missing roles")
    c = typed(m["dan_compartments"], "int32", (s["nd"],), "DAN channels", low=0, high=1)
    require(np.array_equal(np.bincount(c, minlength=2), s["populations"]), "DAN population mapping")
    typed(m["plastic_kc_indices"], "int32", (s["ne"],), "plastic KC", low=0, high=s["nk"] - 1)
    pc = typed(m["plastic_compartments"], "int32", (s["ne"],), "plastic channel", low=0, high=1)
    groups = typed(m["plastic_groups"], "int32", (s["ne"],), "plastic group", low=0, high=s["ng"] - 1)
    mask = typed(m["plastic_mask"], "uint8", (s["ne"],), "plastic mask", low=0, high=1)
    require(np.array_equal(groups // 4, pc), "group channel mapping")
    require(np.array_equal(mask, ((pc == 0) | (groups == 4)).astype(np.uint8)), "accepted home/away mask")


def validate_graph_indices(a, count, neurons, name):
    """Retained graph role maps are int32; never repair another dtype by casting."""
    typed(a, "int32", (count,), name, low=0, high=neurons - 1)
    require(len(np.unique(a)) == count, name + " duplicate indices")
    return a


def validate_main_sampled(sampled, outputs, maps, shape):
    """Source concatenates int64 flatnonzero MBON selectors with int32 roles."""
    typed(outputs, "int64", (len(outputs),), "MBON selectors", low=0, high=shape["n"] - 1)
    expected = np.concatenate([outputs, maps["dan_indices"], maps["kc_indices"], maps["sensory_indices"]])
    typed(sampled, "int64", expected.shape, "main sampled", low=0, high=shape["n"] - 1)
    require(len(np.unique(sampled)) == len(sampled), "main sampled duplicate indices")
    equal(sampled, expected, "main sampled identity/order")


def validate_main(a, s):
    t, b, nk, nd, ng, ne = s["steps"], s["steps"] // s["coarse_steps"], s["nk"], s["nd"], s["ng"], s["ne"]
    x = typed(a["step_signals"], "float32", (t, 5), "step_signals")
    typed(x[:, 0], "float32", (t,), "KC totals", low=0, high=nk, integer=True)
    require(not x[:, 3:].any(), "unused bridge columns nonzero")
    prefix.decode_pool(x[:, 1:3], s["populations"])
    for k, shape in [
        ("bridge_kc_used", (t, ng, 2)),
        ("bridge_signals", (t, 2, 2)),
        ("bridge_kc_bins", (b, nk, 2)),
    ]:
        typed(a[k], "float64", shape, k, low=0)
    typed(a["bridge_rule"], "float64", (t, ng, 8), "bridge_rule")
    typed(a["dan_bins"], "int32", (b, nd), "dan_bins", low=0, high=s["coarse_steps"])
    typed(a["sensory_bins"], "int32", (b, s["ns"]), "sensory_bins", low=0, high=s["coarse_steps"])
    typed(a["gains"], "float32", (ne,), "gains", low=0.5, high=1.5)
    typed(a["gain_delta"], "float32", (ne,), "gain_delta")
    equal(a["gain_delta"], a["gains"] - np.float32(1), "gain delta/unit checkpoint mismatch")


def validate_fine(a, m, s):
    t, n, nd, ne = s["steps"], s["n"], s["nd"], s["ne"]
    n_sample = len(m["sample"])
    expected = dict(
        counts=("int32", (n,)),
        rates=("float32", (n,)),
        rates_hz=("float32", (n,)),
        voltage=("float32", (n,)),
        trace=("int32", (t, n_sample)),
        population=("int32", (t,)),
        dan_counts=("int32", (nd,)),
        compartment_dan_counts=("int32", (2,)),
        compartment_tonic_hz=("float32", (2,)),
        gains=("float32", (ne,)),
        gain_delta=("float32", (ne,)),
        pulse_times_ms=("float32", (0,)),
        pulse_dan_indices=("int32", (0,)),
    )
    require(set(a) == set(expected), "fine result schema")
    for k, (dtype, shape) in expected.items():
        typed(a[k], dtype, shape, k)
    require(np.isin(a["trace"], [0, 1]).all(), "fine trace is not binary")
    require(np.all((a["counts"] >= 0) & (a["counts"] <= t)), "fine counts domain")
    require(np.all((a["population"] >= 0) & (a["population"] <= n)), "fine population domain")
    require(np.all(a["population"] >= a["trace"].sum(1)), "fine sampled population contradiction")
    equal(a["counts"][m["sample"]], a["trace"].sum(0, dtype=np.int32), "fine count reduction")
    equal(a["dan_counts"], a["trace"][:, m["dan_columns"]].sum(0, dtype=np.int32), "fine DAN count reduction")
    require(
        int(a["counts"].sum(dtype=np.int64)) == int(a["population"].sum(dtype=np.int64)),
        "fine whole population reduction",
    )
    comp = np.bincount(m["dan_compartments"], weights=a["dan_counts"], minlength=2).astype(np.int32)
    equal(a["compartment_dan_counts"], comp, "fine compartment reduction")
    require(np.all((a["gains"] >= 0.5) & (a["gains"] <= 1.5)), "fine gain bounds")


def contrast_arrays(fine, u, t, m, s, *, first_pulse_step, sampled=None):
    validate_maps(m, s)
    validate_fine(fine, m, s)
    validate_main(u, s)
    validate_main(t, s)
    steps, coarse = s["steps"], s["coarse_steps"]
    bins = steps // coarse
    event = fine["trace"]
    kc = event[:, m["kc_columns"]]
    dan = event[:, m["dan_columns"]]
    counts = prefix.fine_pool(dan, m["dan_compartments"], s["populations"])
    equal(
        counts,
        prefix.decode_pool(u["step_signals"][:, 1:3], s["populations"]),
        "fine/untaught pooled stream mismatch",
    )
    equal(
        kc.sum(1, dtype=np.int32).astype(np.float32),
        u["step_signals"][:, 0],
        "fine/untaught KC total mismatch",
    )
    coarse_event = event.reshape(bins, coarse, event.shape[1]).sum(1, dtype=np.int32)
    equal(coarse_event[:, m["dan_columns"]], u["dan_bins"], "fine/untaught per-DAN bins")
    equal(coarse_event[:, m["sensory_columns"]], u["sensory_bins"], "fine/untaught sensory bins")
    equal(u["sensory_bins"], t["sensory_bins"], "full-interval sensory mismatch")
    equal(fine["gains"], u["gains"], "fine/untaught gains")
    equal(fine["gain_delta"], u["gain_delta"], "fine/untaught deltas")
    for a in [u, t]:
        pool = prefix.decode_pool(a["step_signals"][:, 1:3], s["populations"]).reshape(bins, coarse, 2).sum(1)
        from_bins = np.stack(
            [a["dan_bins"][:, m["dan_compartments"] == c].sum(1, dtype=np.int64) for c in range(2)], 1
        )
        equal(pool, from_bins, "main per-cell/pooled DAN count contradiction")
        require(
            np.array_equal(
                a["gains"][m["plastic_mask"] == 0],
                np.ones(np.count_nonzero(m["plastic_mask"] == 0), np.float32),
            ),
            "masked gain changed",
        )
    r = prefix.prefix_contrast(
        u["step_signals"][:, 1:3],
        t["step_signals"][:, 1:3],
        populations=s["populations"],
        first_pulse_step=first_pulse_step,
        kc_total_untaught=u["step_signals"][:, 0],
        kc_total_taught=t["step_signals"][:, 0],
        kc_used_untaught=u["bridge_kc_used"],
        kc_used_taught=t["bridge_kc_used"],
        rule_untaught=u["bridge_rule"],
        rule_taught=t["bridge_rule"],
    )
    first = r["first_pool_difference_step"]
    stop = steps if first is None else first + 1
    before = steps if first is None else first
    equal(
        u["bridge_signals"][:before],
        t["bridge_signals"][:before],
        "DAN bridge state differs before first pool difference",
    )
    whole = stop // coarse
    equal(
        u["bridge_kc_bins"][:whole], t["bridge_kc_bins"][:whole], "individual KC filter bin prefix mismatch"
    )
    if "sampled_bins" in u or "sampled_bins" in t:
        require(
            "sampled_bins" in u and "sampled_bins" in t and sampled is not None,
            "incomplete sampled prefix evidence",
        )
        for a in [u, t]:
            typed(a["sampled_bins"], "int32", (bins, len(sampled)), "sampled_bins", low=0, high=coarse)
        lookup = {int(v): i for i, v in enumerate(sampled)}
        require(
            len(lookup) == len(sampled) and all(int(v) in lookup for v in m["sample"]),
            "sampled role identity",
        )
        idx = [lookup[int(v)] for v in m["sample"]]
        equal(u["sampled_bins"][:, idx], coarse_event, "fine/untaught sampled bins")
        kidx = [lookup[int(v)] for v in m["kc_indices"]]
        equal(
            u["sampled_bins"][:whole, kidx],
            t["sampled_bins"][:whole, kidx],
            "sampled KC whole-prefix mismatch",
        )
    differences = prefix.decode_pool(t["step_signals"][:, 1:3], s["populations"]) - counts
    hidden = np.any(u["dan_bins"][:whole] != t["dan_bins"][:whole], axis=1)
    r.update(
        whole_prefix_bins=whole,
        first_pool_difference_ms=None if first is None else first / 5,
        per_cell_dan_different_whole_prefix_bins=np.flatnonzero(hidden).tolist(),
        per_cell_late_subbin_events="unknown; pooled equality does not establish individual DAN event equality",
    )
    return r, dict(
        dan_count_difference=differences,
        kc_prefix_counts=kc[:stop].sum(0, dtype=np.int64),
        kc_body_ids=m["body_ids"][m["kc_columns"]],
        dan_body_ids=m["body_ids"][m["dan_columns"]],
    )


def same_json(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(b, dict):
        return set(a) == set(b) and all(same_json(a[k], v) for k, v in b.items())
    if isinstance(b, list):
        return len(a) == len(b) and all(same_json(x, y) for x, y in zip(a, b))
    return a == b


def expected_rows():
    return [
        dict(game=g, seed_set=noise, seed=g + 42 + panel * 2000000 + extra, run_id=rid)
        for panel, rid in enumerate(RUNS)
        for g in GAMES[panel]
        for noise, extra in [("base", 0), ("alt", 1000000)]
    ]


def validate_plan(plan):
    require(
        isinstance(plan, dict) and type(plan.get("schema")) is int and plan["schema"] == 1,
        "unsupported plan schema",
    )
    require(
        plan.get("wall_seconds_cap") == 120 and type(plan["wall_seconds_cap"]) is int,
        "fixed 120-second cap required",
    )
    c = plan.get("contract", {})
    for key, value in ACTUAL_CONTRACT.items():
        require(key in c and same_json(c[key], value), "fixed contract differs: " + key)
    if "wall_seconds_cap" in c:
        require(type(c["wall_seconds_cap"]) is int and c["wall_seconds_cap"] == 120, "contract cap mismatch")
    for key in ["root", "capture_dir", "samples_path"]:
        require(
            isinstance(plan.get(key), str) and Path(plan[key]).is_absolute(), "plan absolute path required"
        )
    require(
        isinstance(plan.get("run_dirs"), dict) and len(plan["run_dirs"]) == 2,
        "two ordered main archives required",
    )
    require(
        isinstance(plan.get("expected_rows"), list) and len(plan["expected_rows"]) == 32,
        "32 fine selectors required",
    )
    identity = hashlib.sha256(
        json.dumps(
            {k: v for k, v in plan.items() if k != "run_id"},
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()[:20]
    require(plan.get("run_id") == "dan-causal-prefix-" + identity, "plan identity hash differs")


def _identity_context(plan, store):
    root = Path(plan["root"])
    cap = Path(plan["capture_dir"])
    s = ACTUAL_SHAPE
    require(tuple(plan["run_dirs"]) == RUNS, "original/second run order differs")
    require(plan["expected_rows"] == expected_rows(), "fixed original/second selector differs")
    for p in [Path(__file__).resolve(), Path(prefix.__file__).resolve()]:
        store.path(p)
    receipt = store.json(cap / "capture-receipt.json")
    terminal = store.json(cap / "summary.json")
    progress = store.json(cap / "progress.json")
    identity = receipt["identity"]
    protocol = identity["protocol"]
    require(
        receipt["run_id"] == "onset-history-capture-4343c21535c43f42"
        and terminal["run_id"] == receipt["run_id"],
        "capture identity",
    )
    require(
        terminal["status"] == "complete" and terminal["calls"] == 33 and terminal["attempted_calls"] == 33,
        "incomplete capture",
    )
    require(
        terminal["identity"] == identity
        and progress["completed_calls"] == 33
        and progress["attempted_calls"] == 33,
        "capture receipt disagreement",
    )
    require(identity["rows"] == plan["expected_rows"], "capture selector disagreement")
    require(
        identity["capture"]
        == dict(
            bin_ms=0.2,
            electrical_dt=0.2,
            coarse_bin_ms=10.0,
            schedule_repeat=50,
            record=False,
            plasticity=True,
            pulses=[],
            unit_initial_gains=True,
            raster_unit="actual binary spike events per .2ms interval; columns by stored global index",
        ),
        "capture mode differs",
    )
    for key, value in PROTOCOL.items():
        require(same_json(protocol.get(key), value), "protocol differs: " + key)
    store.bound_hash(plan["samples_path"], receipt["samples_sha256"])
    require(plan["samples_path"] == receipt["samples_path"], "sample path differs")
    for rel, digest in identity["graph_hashes"].items():
        store.bound_hash(root / rel, digest)
    store.bound_hash(identity["native_binary"]["path"], identity["native_binary"]["sha256"])
    pilot = Path(identity["pilot"])
    for name, key in [
        ("manifest.json", "pilot_manifest_sha256"),
        ("source/inputs.npz", "inputs_sha256"),
        ("source/protocol.json", "pilot_protocol_sha256"),
    ]:
        store.bound_hash(pilot / name, identity[key])
    source = plan["source_snapshot"]
    require(len(source) == 6, "six source snapshots required")
    for rel, item in source.items():
        require(
            rel
            in [
                "bet36fly/reward_lif.cpp",
                "bet36fly/reward_brain.py",
                "bet36fly/reward_protocol.py",
                "bet36fly/reward_encoder.py",
                "bet36fly/reward_diagnostic.py",
                "scripts/reward_teaching_diagnostic.py",
            ],
            "unexpected causal source",
        )
        digest = identity["source_code"][Path(rel).name]
        require(item["sha256"] == digest, "source snapshot identity")
        store.bound_hash(item["path"], digest)
        store.bound_hash(root / rel, digest)
    with store.archive(plan["samples_path"]) as z:
        m = {k[:-4]: z.array(k[:-4]) for k in z.names}
    require(set(m) == set(identity["sample_arrays"]), "sample map schema")
    validate_maps(m, s)
    for name, a in m.items():
        spec = identity["sample_arrays"][name]
        require(
            spec == dict(dtype=str(a.dtype), shape=list(a.shape), sha256=array_hash(a)),
            "sample map recorded fingerprint",
        )
    ids = typed(store.npy(root / "data/brain/ids.npy"), "int64", (s["n"],), "graph body IDs", low=1)
    equal(m["body_ids"], np.asarray(ids[m["sample"]]), "body/global map")
    for role in ["kc", "sensory"]:
        equal(
            m[role + "_indices"],
            validate_graph_indices(
                store.npy(root / f"data/brain/{role}.npy"), s["nk" if role == "kc" else "ns"], s["n"], role
            ),
            "retained role identity",
        )
    atlas = store.path(plan.get("atlas_path", root / "wiki/cells/data/neurons.csv"))
    with atlas.open(newline="") as f:
        rows = list(csv.DictReader(f))
    by_index = {int(x["graph_index"]): x for x in rows}
    require(len(by_index) == len(rows), "duplicate atlas graph identity")
    outputs = []
    for c, (dan_type, mbon_type) in enumerate([("PPL101", "MBON11"), ("PAM12", "MBON09")]):
        for i in m["dan_indices"][m["dan_compartments"] == c]:
            a = by_index[int(i)]
            require(
                int(a["body_id"]) == int(ids[i])
                and a["type"] == dan_type
                and a["cell_class"] == "DAN"
                and a["transmitter"] == "dopamine"
                and a["reward_fast_output_zeroed"] == "1",
                "selected DAN causal anatomy",
            )
        out = np.array(
            sorted(
                int(x["graph_index"]) for x in rows if x["type"] == mbon_type and x["cell_class"] == "MBON"
            ),
            np.int64,
        )
        outputs.extend(out.tolist())
    require(len(outputs) == 6 and not np.isin(outputs, m["sample"]).any(), "MBON sample roles")
    mbon = store.npy(root / "data/brain/mbon.npy")
    require(mbon.ndim == 1 and mbon.size > 0, "MBON retained shape")
    validate_graph_indices(mbon, len(mbon), s["n"], "mbon")
    require(np.isin(outputs, mbon).all(), "MBON retained identity")
    summaries = {rid: store.json(Path(path) / "summary.json") for rid, path in plan["run_dirs"].items()}
    prefix.matched_rows(plan["expected_rows"], summaries, protocol)
    for rid, summary in summaries.items():
        si = summary["identity"]
        base = Path(plan["run_dirs"][rid])
        prior = identity["prior"][rid]
        store.bound_hash(base / "summary.json", prior["summary_sha256"])
        require(
            summary["panel_complete"] is True
            and si["code_hashes"] == identity["source_code"]
            and si["graph_hashes"] == identity["graph_hashes"],
            "main source identity",
        )
        for key in ["inputs_sha256", "pilot_manifest_sha256", "pilot_protocol_sha256"]:
            require(si[key] == identity[key], "pilot binding differs")
        require(summary["native_binary"] == identity["native_binary"], "native identity differs")
        for name, meta in summary["artifacts"].items():
            if name in ["trials.npz", "recording-layout.json"]:
                store.bound_hash(base / name, meta["sha256"])
                require(store.items[str(base / name)]["bytes"] == meta["bytes"], "main artifact size")
        layout = store.json(base / "recording-layout.json")
        require(
            layout["layout_version"] == "rate-bridge-v1/1" and layout["learning_rule"] == "rate-bridge-v1",
            "recorded bridge layout",
        )
        require(
            layout["config"]
            == dict(
                h_ms=0.2,
                tau_ms=500.0,
                rate_tau_ms=100.0,
                effective_eta=0.0005,
                normalization=0.96,
                tail="analytic_no_new_event_tail",
                checkpoint="float32; double remainder discarded",
            ),
            "recorded bridge config",
        )
        require(
            layout["layout"]["step_signals"]
            == ["kc_spikes", "dan_mean_spikes per compartment", "unused zeros"]
            and layout["group_compartments"] == [0] * 4 + [1] * 4,
            "recorded signal/group layout",
        )
    saved = {x["file"]: x for x in terminal["saved"]}
    require(
        len(saved) == 33 and set(saved) == {"coarse.npz", *[f"fine_{i:02d}.npz" for i in range(32)]},
        "complete captured file inventory",
    )
    require(progress["saved"] == terminal["saved"], "captured progress/terminal disagreement")
    for i in range(32):
        name = f"fine_{i:02d}.npz"
        store.bound_hash(cap / name, saved[name]["sha256"])
        meta = saved[name]["metadata"]
        require(
            meta["dt"] == 0.2
            and meta["bin_ms"] == 0.2
            and meta["duration_ms"] == 400.0
            and meta["instrumentation"] is None,
            "fine timing/recording identity",
        )
    return m, summaries, np.array(outputs, np.int64), saved


def _actual_contrasts(plan, store, guard):
    m, summaries, outputs, saved = _identity_context(plan, store)
    cap = Path(plan["capture_dir"])
    s = ACTUAL_SHAPE
    active = None
    archive = None
    try:
        for i, row in enumerate(plan["expected_rows"]):
            guard()
            rid = row["run_id"]
            if active != rid:
                if archive:
                    archive.__exit__()
                archive = store.archive(Path(plan["run_dirs"][rid]) / "trials.npz")
                active = rid
                for key in [
                    "plastic_kc_indices",
                    "plastic_compartments",
                    "plastic_groups",
                    "plastic_mask",
                    "dan_compartments",
                ]:
                    equal(archive.array(key), m[key], "main/fine " + key)
                equal(
                    archive.array("blank_gains"), np.ones(s["ne"], np.float32), "main unit initial checkpoint"
                )
                sampled = archive.array("sampled")
                validate_main_sampled(sampled, outputs, m, s)
            with store.archive(cap / f"fine_{i:02d}.npz") as z:
                fine = {k[:-4]: z.array(k[:-4]) for k in z.names}
            for key, value in fine.items():
                spec = saved[f"fine_{i:02d}.npz"]["numeric_fingerprint"][key]
                require(
                    spec == dict(dtype=str(value.dtype), shape=list(value.shape), sha256=array_hash(value)),
                    "fine numerical fingerprint differs",
                )

            def main(condition):
                p = f"{row['game']}__{row['seed_set']}__{condition}__"
                names = [
                    "step_signals",
                    "bridge_kc_used",
                    "bridge_rule",
                    "dan_bins",
                    "bridge_signals",
                    "bridge_kc_bins",
                    "sensory_bins",
                    "gains",
                    "gain_delta",
                ]
                if row["game"] == summaries[rid]["panel_games"][0]:
                    names.append("sampled_bins")
                a = {name: archive.array(p + name) for name in names}
                meta = next(
                    x
                    for x in summaries[rid]["rows"]
                    if x["game"] == row["game"]
                    and x["seed_set"] == row["seed_set"]
                    and x["condition"] == condition
                )
                require(
                    array_hash(a["sensory_bins"]) == meta["sensory_bins_sha256"],
                    "sensory summary hash mismatch",
                )
                return a

            u = main("untaught")
            for condition in ["home", "away"]:
                guard()
                r, arrays = contrast_arrays(
                    fine, u, main(condition), m, s, first_pulse_step=1550, sampled=sampled
                )
                yield (
                    dict(
                        index=i * 2 + int(condition == "away"), fine_index=i, **row, condition=condition, **r
                    ),
                    arrays,
                )
    finally:
        if archive:
            archive.__exit__()


def descriptive(rows):
    groups = {}
    for row in rows:
        key = "/".join([row["run_id"], row["seed_set"], row["condition"]])
        groups.setdefault(key, []).append(row)
    result = {}
    for key, items in groups.items():
        times = [
            r["first_pool_difference_step"] for r in items if r["first_pool_difference_step"] is not None
        ]
        first_counts = [
            r["first_pool_count_difference"] for r in items if r["first_pool_count_difference"] is not None
        ]
        totals = [r["total_compartment_count_difference"] for r in items]
        result[key] = dict(
            contrasts=len(items),
            no_pool_difference=len(items) - len(times),
            first_difference_step_min=min(times) if times else None,
            first_difference_step_max=max(times) if times else None,
            first_difference_ms_min=min(times) / 5 if times else None,
            first_difference_ms_max=max(times) / 5 if times else None,
            first_count_difference_min=np.min(first_counts, axis=0).tolist() if first_counts else None,
            first_count_difference_max=np.max(first_counts, axis=0).tolist() if first_counts else None,
            total_count_difference_min=np.min(totals, axis=0).tolist(),
            total_count_difference_max=np.max(totals, axis=0).tolist(),
        )
    return result


def execute(plan_path, out, *, _producer=_actual_contrasts, clock=time.monotonic):
    started = clock()
    out = Path(out)
    out.mkdir(parents=False, exist_ok=False)
    rows = []
    cap = 120.0
    plan = {}
    store = None

    def guard():
        if clock() - started >= cap:
            raise TimeoutError("120-second total audit cap")

    def persist(status, error=None):
        value = dict(
            status=status,
            run_id=plan.get("run_id"),
            completed_contrasts=len(rows),
            rows=rows,
            wall_seconds=clock() - started,
            error=error,
        )
        atomic_json(out / "status.json", value)
        return value

    try:
        guard()
        require(Path(plan_path).stat().st_size <= 32_000_000, "plan too large")
        plan_bytes = Path(plan_path).read_bytes()
        plan = strict_json(plan_bytes)
        validate_plan(plan)
        guard()
        atomic_json(out / "plan.json", plan)
        persist("running")
        store = BoundInputs(plan["inputs"], guard)
        store.verify()
        for observation, arrays in _producer(plan, store, guard):
            guard()
            i = len(rows)
            require(i < 64 and observation.get("index") == i, "contrast count/order mismatch")
            name = f"contrast_{i:03d}"
            npz = out / (name + ".npz")
            with npz.open("xb") as f:
                np.savez_compressed(f, **arrays)
                f.flush()
                os.fsync(f.fileno())
            guard()
            obs = dict(
                observation, artifact=dict(file=npz.name, sha256=sha(npz, guard), bytes=npz.stat().st_size)
            )
            atomic_json(out / (name + ".json"), obs)
            guard()
            rows.append(obs)
            persist("running")
            guard()
        require(len(rows) == 64, "incomplete comparison matrix")
        store.verify()
        guard()
        require(Path(plan_path).read_bytes() == plan_bytes, "plan changed during audit")
        atomic_json(
            out / "summary.json",
            dict(
                status="computed",
                run_id=plan["run_id"],
                contrasts=64,
                groups=descriptive(rows),
                scope="Descriptive current-code conditional prefix; no new learning model or qualification.",
            ),
        )
        guard()
        summary_hash = sha(out / "summary.json", guard)
        result = persist("completed")
        guard()
        atomic_json(
            out / "completion.json",
            dict(
                status="complete",
                run_id=plan["run_id"],
                contrasts=64,
                summary_sha256=summary_hash,
                status_sha256=sha(out / "status.json", guard),
                wall_seconds=clock() - started,
            ),
        )
        guard()
        return result
    except BaseException as exc:
        error = f"{type(exc).__name__}: {exc}"
        try:
            atomic_json(
                out / "terminal-error.json",
                dict(error=error, wall_seconds=clock() - started, completed_contrasts=len(rows)),
            )
        except OSError as receipt_error:
            error += "; failure receipt persistence: " + str(receipt_error)
        return persist("failed", error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = execute(args.plan, args.out)
    print(
        json.dumps({k: result[k] for k in ["status", "completed_contrasts", "wall_seconds", "error"]}),
        flush=True,
    )
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
