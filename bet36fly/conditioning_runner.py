"""Exclusive, fail-closed conditioning runner. Neural imports occur only after qualification."""

from __future__ import annotations

import copy
import io
import json
import os
from pathlib import Path
import time

import numpy as np

from . import conditioning as c
from .conditioning_artifacts import (
    binding,
    canonical,
    decode_result,
    digest,
    encode_result,
    read_artifact,
    read_bound,
    verify_bindings,
    write_exclusive,
)
from .experiment import atomic_json, utcnow
from .experiments import IDENTIFIER, writer_lock

DOC_DIR = "docs/evidence/reward-mechanism-repair-2026-09-12"
DOCUMENTS = (
    "conditioning-preregistration.md",
    "conditioning-prerun-addendum.md",
    "conditioning-implementation-contract.md",
    "conditioning-preregistration.json",
    "conditioning-prerun-addendum.json",
)
SOURCES = (
    "bet36fly/conditioning.py",
    "bet36fly/conditioning_runner.py",
    "bet36fly/conditioning_artifacts.py",
    "bet36fly/conditioning_evidence.py",
    "scripts/run_reward_conditioning.py",
)
STAGES = ("acquisition-primary", "acquisition-challenge", "reversal")


class GateFailed(ValueError):
    pass


class BudgetStopped(RuntimeError):
    pass


class Cancelled(RuntimeError):
    pass


def qualify(root, pair_id):
    """Recompute an exact original/second pair and bind its current scientific inputs."""
    from .reward_evidence import list_reward_evidence, canonical_pair_identity

    root = Path(root).resolve()
    index = list_reward_evidence(root)
    pairs = [p for p in index["qualification_pairs"] if p["pair_id"] == pair_id]
    if (
        len(pairs) != 1
        or pairs[0]["validation_status"] != "validated"
        or pairs[0]["evidence_status"] != "passed"
    ):
        raise GateFailed("Conditioning requires both independently validated qualifying mechanism panels.")
    pair = pairs[0]
    summaries = []
    bindings = []
    for name in ("original_run_id", "heldout_run_id"):
        directory = root / "output/diagnostics" / pair[name]
        for name in (
            "summary.json",
            "preregistration.json",
            "trials.npz",
            "recording-layout.json",
            "replay-evidence.json",
            "attribution.json",
        ):
            path = directory / name
            if path.exists():
                bindings.append(binding(path))
        summary = json.loads(read_bound(binding(directory / "summary.json")))
        summaries.append(summary)
    first, second = summaries
    i = first["identity"]
    validate_protocol(i["protocol"])
    expected_sources = {
        "reward_lif.cpp",
        "reward_brain.py",
        "reward_protocol.py",
        "reward_encoder.py",
        "reward_diagnostic.py",
        "reward_teaching_diagnostic.py",
    }
    if set(i["code_hashes"]) != expected_sources:
        raise GateFailed("Scientific source inventory differs.")
    expected_graph = {
        f"data/brain/{name}.npy"
        for name in ("counts", "ids", "in_degree", "indptr", "kc", "mbon", "post", "sensory", "signs")
    } | {"data/brain/nodes.feather", "data/raw/annotations.feather"}
    if set(i["graph_hashes"]) != expected_graph:
        raise GateFailed("Graph input inventory differs.")
    if not IDENTIFIER.fullmatch(i["pilot"]):
        raise GateFailed("Invalid qualification pilot identity.")
    if canonical_pair_identity(i) != canonical_pair_identity(second["identity"]):
        raise GateFailed("Mixed scientific pair identity.")
    if (
        first["native_binary"] != second["native_binary"]
        or i["protocol"]["dan_reference"] != "none"
        or i["protocol"]["away_plasticity_mask"] != "gamma"
    ):
        raise GateFailed("Pair native identity or accepted rule/mask differs.")
    for name, sha in i["code_hashes"].items():
        base = "scripts" if name == "reward_teaching_diagnostic.py" else "bet36fly"
        meta = binding(root / base / name)
        if meta["sha256"] != sha:
            raise GateFailed("Diagnostic scientific source changed; a fresh qualifying pair is required.")
        bindings.append(meta)
    native_path = Path(first["native_binary"]["path"])
    if (
        native_path.parent != root / "output/native"
        or native_path.stem != "reward-lif-" + i["code_hashes"]["reward_lif.cpp"][:16]
        or native_path.suffix not in (".so", ".dylib")
    ):
        raise GateFailed("Native binary is outside the approved kernel inventory.")
    native = binding(native_path)
    if native["sha256"] != first["native_binary"]["sha256"]:
        raise GateFailed("Native binary differs from qualifying evidence.")
    bindings.append(native)
    for path, sha in i["graph_hashes"].items():
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise GateFailed("Invalid graph binding.")
        meta = binding(root / path)
        if meta["sha256"] != sha:
            raise GateFailed("Current graph/annotations differ from qualification.")
        bindings.append(meta)
    pilot = root / "output/experiments" / i["pilot"]
    for name, key in (
        ("manifest.json", "pilot_manifest_sha256"),
        ("source/inputs.npz", "inputs_sha256"),
        ("source/protocol.json", "pilot_protocol_sha256"),
    ):
        meta = binding(pilot / name)
        if meta["sha256"] != i[key]:
            raise GateFailed("Qualification pilot inputs changed.")
        bindings.append(meta)
    if i["protocol"]["learning_rule"] == "rate-bridge-v1":
        documents = i["bridge_contract"]["documents"]
        if set(documents) != {"rate-bridge-preregistration.md", "rate-bridge-implementation-contract.md"}:
            raise GateFailed("Bridge document inventory differs.")
        for name, sha in documents.items():
            meta = binding(root / DOC_DIR / name)
            if meta["sha256"] != sha:
                raise GateFailed("Bridge scientific document changed.")
            bindings.append(meta)
    for name in DOCUMENTS:
        bindings.append(binding(root / DOC_DIR / name))
    for name in SOURCES:
        bindings.append(binding(root / name))
    for name in (
        "bridge-residual-attribution.json",
        f"panel-{pair['original_run_id']}.json",
        f"panel-{pair['heldout_run_id']}.json",
    ):
        bindings.append(binding(root / DOC_DIR / name))
    # Bind first, then validate again inside that byte window. A prior reader
    # verdict cannot authorize bytes replaced before our own binding snapshot.
    refreshed = list_reward_evidence(root)
    matched = [value for value in refreshed["qualification_pairs"] if value.get("pair_id") == pair_id]
    if (
        len(matched) != 1
        or matched[0] != pair
        or matched[0]["validation_status"] != "validated"
        or matched[0]["evidence_status"] != "passed"
    ):
        raise GateFailed("Qualification artifacts changed between validation and binding.")
    verify_bindings(bindings)
    return {"pair": pair, "scientific_identity": i, "native": native, "bindings": bindings}


def prepare_inputs(root, protocol):
    """Read anatomy/encode cues without constructing, importing or loading an engine."""
    import pyarrow.feather as feather
    from .reward_protocol import COMPARTMENTS, KC_CLASSES, kc_class, plastic_mapping, eligibility_mask
    from .reward_encoder import glomerular_map, glomerular_rates

    root = Path(root)
    brain = root / "data/brain"
    ids, ptr, post, contacts, kc, sensory = [
        np.load(brain / f"{name}.npy", allow_pickle=False)
        for name in ("ids", "indptr", "post", "counts", "kc", "sensory")
    ]
    nodes = feather.read_table(brain / "nodes.feather").to_pandas().set_index("bodyId").reindex(ids)
    raw = (
        feather.read_table(
            root / "data/raw/annotations.feather", columns=["bodyId", "type", "instance", "class"]
        )
        .to_pandas()
        .set_index("bodyId")
        .reindex(ids)
    )
    outputs = []
    dans = []
    dcomp = []
    for ci, (_, dan, mbon) in enumerate(COMPARTMENTS):
        d = np.flatnonzero(
            nodes["type"].eq(dan) & nodes["class"].eq("DAN") & nodes.transmitter.eq("dopamine")
        )
        m = np.flatnonzero(nodes["type"].eq(mbon) & nodes["class"].eq("MBON"))
        if not len(m):
            raise ValueError("Empty fixed output population.")
        outputs.append(m.astype(np.int32))
        dans.extend(d)
        dcomp.extend([ci] * len(d))
    if [dcomp.count(x) for x in (0, 1)] != [2, 22]:
        raise ValueError("DAN population differs from frozen2/22.")
    edges, pk, pc = plastic_mapping(ptr, post, kc, outputs)
    types = raw.iloc[kc]["type"].fillna("").to_numpy()
    mask, _ = eligibility_mask(types, pk, pc, away_policy="gamma")
    groups = np.array(
        [int(comp) * 4 + KC_CLASSES.index(kc_class(types[k])) for k, comp in zip(pk, pc)], np.int32
    )
    is_kc = np.zeros(len(ids), bool)
    is_kc[kc] = True
    port_contacts = np.array(
        [contacts[ptr[i] : ptr[i + 1]][is_kc[post[ptr[i] : ptr[i + 1]]]].sum() for i in sensory], np.float64
    )
    ports = nodes.iloc[sensory]
    mapping = glomerular_map(
        ports["type"].fillna("").to_numpy(),
        ports.transmitter.fillna("").to_numpy(),
        port_contacts,
        n_features=16,
        min_kc_contacts=protocol["encoder_min_kc_contacts"],
    )
    encoded = {
        cue: glomerular_rates(
            np.array(vector),
            mapping,
            peak_hz=protocol["encoder_peak_hz"],
            width=protocol["encoder_tuning_width"],
        )
        for cue, vector in c.conditioning_spec()["cues"].items()
    }
    arrays = dict(
        kc=np.asarray(kc, np.int32),
        sensory=np.asarray(sensory, np.int32),
        dans=np.array(dans, np.int32),
        dcomp=np.array(dcomp, np.int32),
        edges=edges,
        pk=pk,
        pc=pc,
        mask=mask,
        groups=groups,
        output_home=outputs[0],
        output_away=outputs[1],
    )
    arrays["sample"] = np.unique(
        np.concatenate((arrays["sensory"], arrays["kc"], arrays["dans"], *outputs))
    ).astype(np.int32)
    arrays.update({f"cue_{key}": np.asarray(value, np.float32) for key, value in encoded.items()})
    return {"neurons": len(ids), "learning_rule": protocol["learning_rule"], "arrays": arrays}


def schedules(row, inputs):
    arrays = inputs["arrays"]
    rates = np.zeros((row.duration_ms // 10, len(arrays["sensory"])), np.float32)
    if row.cue is not None:
        start, end = row.cue_window
        rates[start // 10 : end // 10] = arrays["cue_" + row.cue]
    pulses = tuple(
        (float(t), int(dan))
        for t, ch in row.teaching
        for dan in np.flatnonzero(arrays["dcomp"] == c.CHANNELS.index(ch))
    )
    return rates, pulses


def numeric_schema(row, inputs):
    a = inputs["arrays"]
    _, pulses = schedules(row, inputs)
    return c.NumericSchema(
        neurons=inputs["neurons"],
        samples=len(a["sample"]),
        kcs=len(a["kc"]),
        dans=len(a["dans"]),
        edges=len(a["pk"]),
        groups=8,
        bins=row.duration_ms // 10,
        steps=row.duration_ms * 5,
        duration_ms=row.duration_ms,
        learning_rule=inputs["learning_rule"],
        record=row.kind.startswith("train-"),
        plasticity=row.plasticity,
        pulses=pulses,
    )


def _owner(row):
    return (row.stage, row.panel, row.branch or row.arm)


class EvidenceState:
    """Independent copies of canonical gains and the raw probe matrices used by scoring."""

    def __init__(self, inputs):
        self.inputs = inputs
        self.unit = np.ones(len(inputs["arrays"]["pk"]), np.float32)
        self.canonical = {}
        self.originals = {}
        self.replay_outputs = {}
        self.probes = {}
        self.partitions = {}
        self.verdicts = {}
        self.parents = {}
        self.starts = {}
        self.probe_fingerprints = {}
        self.stage_bound_hits = {stage: 0 for stage in STAGES}

    def parent(self, panel):
        return self.canonical[("acquisition-primary", panel - 3_000_000, "paired")]

    def before(self, row):
        if row.replay_of:
            expected = self.originals[row.replay_of]["before"].copy()
            if row.kind == "train-blank":
                cue_id = row.replay_of.replace("-blank", "-cue")
                actual = self.replay_outputs[cue_id]
                if actual.tobytes() != expected.tobytes():
                    raise ValueError("Blank replay must start from its replayed cue output.")
            return expected
        if row.kind == "unit-probe":
            return self.unit.copy()
        if row.kind == "parent-probe":
            return self.parent(row.panel).copy()
        key = _owner(row)
        if key not in self.canonical:
            self.canonical[key] = (self.parent(row.panel) if row.stage == "reversal" else self.unit).copy()
            if row.stage == "reversal":
                self.starts.setdefault(str(row.panel), {})[row.branch] = c.array_identity(
                    self.canonical[key]
                )["sha256"]
        return self.canonical[key].copy()

    def accept(self, row, before, result, artifact):
        after = result["gains"]
        if row.replay_of:
            self.replay_outputs[row.replay_of] = after.copy()
            return
        if row.id in self.replay_ids:
            self.originals[row.id] = {"before": before.copy(), "artifact": artifact}
        if row.kind.startswith("train-"):
            self.canonical[_owner(row)] = after.copy()
        else:
            if row.kind == "endpoint-probe" and (row.arm == "frozen" or row.branch == "frozen-retention"):
                kind = "parent-probe" if row.stage == "reversal" else "unit-probe"
                panel = row.panel if row.stage == "reversal" else None
                reference = next(
                    r
                    for r in self.plan
                    if r.stage == row.stage
                    and r.kind == kind
                    and r.panel == panel
                    and r.seed == row.seed
                    and r.cue == row.cue
                    and r.replay_of is None
                )
                if artifact["fingerprints"] != self.probe_fingerprints[reference.id]:
                    raise ValueError("Frozen matched probe differs in complete numerical fingerprints.")
            self.probe_fingerprints[row.id] = copy.deepcopy(artifact["fingerprints"])
            a = self.inputs["arrays"]
            sample = a["sample"]
            lo, hi = row.cue_window
            counts = (
                result["cue_counts"]
                if "cue_counts" in result
                else result["trace"][lo // 10 : hi // 10].sum(0, dtype=np.int64)
            )
            # Trace is bound to exact global sample order, never a free response scalar.
            response = np.array(
                [counts[np.searchsorted(sample, a["output_" + ch])].sum() for ch in c.CHANNELS], np.int64
            )
            kc_counts = counts[np.searchsorted(sample, a["kc"])]
            self.probes[row.id] = (response, kc_counts, before.copy())

    def endpoint(self, stage, kind, panel=None, arm=None, branch=None):
        seeds = range(5_000_042, 5_000_046) if stage == "reversal" else range(2_000_042, 2_000_046)
        family = "CD" if stage == "acquisition-challenge" else "AB"
        duration = 800 if stage == "reversal" else 400
        selected = [
            r
            for r in self.plan
            if r.stage == stage
            and r.kind == kind
            and r.panel == panel
            and r.arm == arm
            and r.branch == branch
            and r.replay_of is None
        ]
        if len(selected) != 8:
            raise ValueError("Endpoint probe matrix is incomplete.")
        responses = np.zeros((4, 2, 2), np.int64)
        counts = np.zeros((4, 2, len(self.inputs["arrays"]["kc"])), np.int64)
        gains = None
        for row in selected:
            response, kc, g = self.probes[row.id]
            si = list(seeds).index(row.seed)
            ci = c.FAMILIES[family].index(row.cue)
            responses[si, ci] = response
            counts[si, ci] = kc
            if gains is not None and gains.tobytes() != g.tobytes():
                raise ValueError("Endpoint probes did not share one checkpoint.")
            gains = g
        populations = np.array([len(self.inputs["arrays"]["output_" + ch]) for ch in c.CHANNELS], np.int32)
        endpoint = dict(
            responses=responses / (populations * 0.3),
            response_counts=responses,
            response_populations=populations,
            gains=gains.copy(),
            bound_hits=0,
            probe_contract=dict(
                family=family,
                duration_ms=duration,
                cue_window=[300, 600] if duration == 800 else [0, 300],
                seeds=list(seeds),
            ),
        )
        if branch:
            endpoint["start_sha256"] = self.starts[str(panel)][branch]
        return endpoint, counts

    def unit_gate(self, stage):
        unit, counts = self.endpoint(stage, "unit-probe")
        a = self.inputs["arrays"]
        partition = c.partition_kcs(counts, a["pk"], a["pc"], a["mask"])
        self.partitions[stage] = partition
        if not partition["passed"]:
            raise GateFailed("KC specificity entry gate failed before family training.")
        return unit

    def parent_gate(self):
        unit, _ = self.endpoint("reversal", "unit-probe")
        parents = {
            str(p): self.endpoint("reversal", "parent-probe", panel=p)[0] for p in (3_000_000, 4_000_000)
        }
        result = c.evaluate_parent_mapping(unit, parents, self.partitions["acquisition-primary"])
        if not result["passed"]:
            raise GateFailed("; ".join(result["errors"]))
        return parents

    def score(self, stage):
        unit, _ = self.endpoint(stage, "unit-probe")
        if stage != "reversal":
            endpoints = {
                str(p): {
                    arm: self.endpoint(stage, "endpoint-probe", panel=p, arm=arm)[0]
                    for arm in c.ACQUISITION_ARMS
                }
                for p in (0, 1_000_000)
            }
            verdict = c.evaluate_acquisition(unit, endpoints, self.partitions[stage])
        else:
            parents = self.parent_gate()
            finals = {
                str(p): {
                    b: self.endpoint(stage, "endpoint-probe", panel=p, branch=b)[0]
                    for b in c.REVERSAL_BRANCHES
                }
                for p in (3_000_000, 4_000_000)
            }
            verdict = c.evaluate_reversal(
                unit, parents, finals, self.partitions["acquisition-primary"], self.starts
            )
        self.verdicts[stage] = verdict
        if not verdict["all_passed"]:
            raise GateFailed(f"{stage} scientific criteria failed.")
        return verdict


def validate_call_result(row, inputs, before, result):
    a = inputs["arrays"]
    schema = numeric_schema(row, inputs)
    evidence = c.validate_gain_evidence(
        result, before, schema, mask=a["mask"], groups=a["groups"], compartments=a["pc"]
    )
    if (
        not np.array_equal(result["trace"].sum(0, dtype=np.int64), result["counts"][a["sample"]])
        or result["population"].sum(dtype=np.int64) != result["counts"].sum(dtype=np.int64)
        or not np.array_equal(result["dan_counts"], result["counts"][a["dans"]])
        or not np.array_equal(
            result["compartment_dan_counts"], [result["dan_counts"][a["dcomp"] == ci].sum() for ci in (0, 1)]
        )
    ):
        raise ValueError("Global/sample/population/DAN count accounting differs.")
    populations = np.array([np.count_nonzero(a["dcomp"] == ci) for ci in (0, 1)])
    baseline_counts = result["compartment_tonic_hz"].astype(np.float64) * populations * 0.05
    if np.any(
        baseline_counts
        > result["compartment_dan_counts"] + np.finfo(np.float32).eps * 4 * np.maximum(baseline_counts, 1)
    ):
        raise ValueError("Tonic baseline requires more DAN spikes than the complete trial.")
    return evidence


def _verify_engine(engine, inputs, gate):
    a = inputs["arrays"]
    for attr, name in (
        ("kc_indices", "kc"),
        ("sensory", "sensory"),
        ("dan_indices", "dans"),
        ("dan_compartments", "dcomp"),
        ("plastic_edge_indices", "edges"),
        ("plastic_kc_indices", "pk"),
        ("plastic_compartments", "pc"),
        ("plastic_mask", "mask"),
    ):
        if not np.array_equal(getattr(engine, attr), a[name]):
            raise ValueError("Constructed engine anatomy differs from frozen inputs.")
    if engine.n != inputs["neurons"] or engine.learning_rule != inputs["learning_rule"]:
        raise ValueError("Engine identity differs.")
    attributes = dict(
        tau_ms=500.0,
        learning_rate=0.0005,
        gain_bounds=(0.5, 1.5),
        dan_reference="none",
        rate_tau_ms=100.0,
        n_compartments=2,
        _onset_steps=500,
        _baseline_steps=250,
    )
    for name, expected in attributes.items():
        if getattr(engine, name, None) != expected:
            raise ValueError("Constructed engine scientific parameter differs: " + name)
    if engine.gains.dtype != np.float32 or not np.array_equal(
        engine.gains, np.ones(len(a["pk"]), np.float32)
    ):
        raise ValueError("Constructed engine did not start from exact unit gains.")
    if binding(engine.lib._name) != gate["native"]:
        raise ValueError("Loaded native binary differs from qualification.")


def run_conditioning(root, pair_id, *, engine_factory=None, cancelled=lambda: False, clock=time.monotonic):
    """The only public neural entry point: qualification precedes even factory creation."""
    root = Path(root).resolve()
    started = clock()
    gate = qualify(root, pair_id)
    inputs = prepare_inputs(root, gate["scientific_identity"]["protocol"])
    verify_bindings(gate["bindings"])
    if clock() - started >= 1200:
        raise BudgetStopped("Preparation exhausted the fixed wall cap before engine creation.")
    if cancelled():
        raise Cancelled("Cancelled before engine creation.")

    def create():
        if engine_factory is None:
            from .reward_protocol import make_circuit

            engine = make_circuit(root, gate["scientific_identity"]["protocol"])[0]
        else:
            engine = engine_factory(root, gate["scientific_identity"]["protocol"])
        _verify_engine(engine, inputs, gate)
        return engine

    return _execute(root, gate, inputs, create, cancelled=cancelled, clock=clock, started=started)


def _execute(root, gate, inputs, factory, *, cancelled=lambda: False, clock=time.monotonic, started=None):
    """Internal execution core, also exercised with explicit synthetic fake engines."""
    started = clock() if started is None else started
    plan = c.build_call_plan()
    c.validate_call_plan(plan)
    arrays = inputs["arrays"]
    input_npz = io.BytesIO()
    np.savez_compressed(input_npz, **arrays)
    identity = dict(
        schema="conditioning-v1",
        spec=c.conditioning_spec(),
        plan=[r.json() for r in plan],
        qualification=gate,
        inputs=dict(
            neurons=inputs["neurons"],
            learning_rule=inputs["learning_rule"],
            arrays={k: c.array_identity(v) for k, v in arrays.items()},
        ),
    )
    experiment_id = "conditioning-" + digest(canonical(identity))[:24]
    registry = Path(root).resolve() / "output/experiments"
    directory = registry / experiment_id
    with writer_lock(registry):
        directory.mkdir(exist_ok=False)
        identity_meta = write_exclusive(directory / "identity.json", canonical(identity))
        input_meta = write_exclusive(directory / "inputs.npz", input_npz.getvalue())
        manifest = dict(
            id=experiment_id,
            kind="dopamine-conditioning",
            status="running",
            created_at=utcnow(),
            updated_at=utcnow(),
            artifacts={},
            jobs=[
                dict(id=stage, status="queued", completed=0, total=sum(r.stage == stage for r in plan))
                for stage in STAGES
            ],
            conditioning=dict(
                configured_rule=inputs["learning_rule"],
                configured_mask="gamma",
                prerequisite_run_ids=[
                    gate.get("pair", {}).get(k, "synthetic") for k in ("original_run_id", "heldout_run_id")
                ],
                calls=dict(planned=1632, actual=0, cap=1640),
                wall_cap_seconds=1200,
                stages=[],
            ),
        )
        ledger = dict(
            schema="conditioning-v1",
            identity=identity_meta,
            inputs=input_meta,
            attempts=[],
            status="running",
            verdicts={},
        )
        state = EvidenceState(inputs)
        state.plan = plan
        state.replay_ids = {r.replay_of for r in plan if r.replay_of}
        journal = directory / "attempts.jsonl"
        write_exclusive(journal, b"")
        last_event = None

        def persist(*, final=False):
            nonlocal last_event
            manifest["updated_at"] = utcnow()
            manifest["conditioning"]["wall_seconds"] = clock() - started
            manifest["conditioning"]["calls"]["actual"] = sum(a["invoked"] for a in ledger["attempts"])
            manifest["conditioning"]["calls"].update(
                returned=sum(a.get("returned") is True for a in ledger["attempts"]),
                completed=sum(a["status"] == "completed" for a in ledger["attempts"]),
                ambiguous=sum(a["status"] == "intent" and not a["invoked"] for a in ledger["attempts"]),
            )
            ledger["wall_seconds"] = manifest["conditioning"]["wall_seconds"]
            if ledger["attempts"]:
                event = canonical(ledger["attempts"][-1])
                if event != last_event:
                    append_attempt(journal, event)
                    last_event = event
            if final or not (directory / "ledger.json").exists():
                atomic_json(directory / "ledger.json", ledger)
            if final:
                for filename, label in (
                    ("identity.json", "Frozen conditioning identity"),
                    ("ledger.json", "Conditioning attempt ledger"),
                ):
                    meta = binding(directory / filename)
                    key = "a-" + digest(filename.encode())[:20]
                    manifest["artifacts"][key] = dict(
                        path=filename,
                        label=label,
                        sha256=meta["sha256"],
                        bytes=meta["bytes"],
                        url=f"/api/experiments/{experiment_id}/artifacts/{key}",
                    )
            atomic_json(directory / "manifest.json", manifest)
            if final and manifest["status"] == "completed":
                wall = clock() - started
                stopped = cancelled()
                if wall >= 1200 or stopped:
                    status = "budget_stopped" if wall >= 1200 else "cancelled"
                    message = (
                        "Final persistence crossed the fixed wall cap."
                        if wall >= 1200
                        else "Cancellation observed during final persistence."
                    )
                    manifest.update(status=status, error=message)
                    manifest["conditioning"]["status_reason"] = message
                    ledger.update(status=status, error=message)
                    # At most one retry: this terminal disposition cannot re-enter completed.
                    persist(final=True)

        def stamp(path):
            st = Path(path).stat()
            return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)

        stamps = {meta["path"]: stamp(meta["path"]) for meta in gate["bindings"]}

        def guard():
            if cancelled():
                raise Cancelled("Cancellation requested.")
            if clock() - started >= 1200:
                raise BudgetStopped("Fixed1200second wall cap reached.")
            if sum(a["invoked"] for a in ledger["attempts"]) >= 1640:
                raise BudgetStopped("Fixed1640call cap reached.")
            for meta in gate["bindings"]:
                path = Path(meta["path"])
                if path.is_symlink() or not path.is_file() or stamp(path) != stamps[meta["path"]]:
                    raise ValueError("Bound input missing, relinked or resized.")
                if path.suffix in (".py", ".cpp", ".md", ".json") and binding(path) != meta:
                    raise ValueError("Source/document identity changed during execution.")

        verify_bindings(gate["bindings"])
        persist()
        current_stage = STAGES[0]
        try:
            guard()
            engine = factory()
            guard()
            for position, row in enumerate(plan):
                guard()
                if row.stage != current_stage:
                    verify_bindings(gate["bindings"])
                    state.score(current_stage)
                    manifest["jobs"][STAGES.index(current_stage)]["status"] = "completed"
                    current_stage = row.stage
                if (
                    row.stage != "reversal"
                    and row.kind == "train-cue"
                    and row.panel == 0
                    and row.arm == "paired"
                    and row.exposure == 0
                    and not row.replay_of
                ):
                    state.unit_gate(row.stage)
                if row.stage == "reversal" and row.kind == "train-reversal" and position == 1258:
                    state.parent_gate()
                job = manifest["jobs"][STAGES.index(row.stage)]
                job["status"] = "running"
                before = state.before(row)
                rates, pulses = schedules(row, inputs)
                before_meta = write_exclusive(
                    directory / f"{position:04d}-before.npz", encode_result({"gains": before})[0]
                )
                attempt = dict(
                    position=position,
                    call=row.json(),
                    invoked=False,
                    status="prepared",
                    before=before_meta,
                    before_sha256=c.array_identity(before)["sha256"],
                    rate_sha256=c.array_identity(rates)["sha256"],
                )
                ledger["attempts"].append(attempt)
                persist()
                guard()
                engine.gains = before.copy()
                # Durable intent immediately precedes invocation; any interrupted intent is non-passable.
                invoke = engine.run
                attempt.update(invoked=False, status="intent")
                try:
                    persist()
                except BaseException as exc:
                    attempt.update(status="failed", error=f"Pre-invocation persistence failed: {exc}")
                    raise
                try:
                    attempt["invoked"] = True
                    result = invoke(
                        rates,
                        bin_ms=10,
                        teaching_pulses=pulses,
                        dt=0.2,
                        seed=row.seed,
                        plasticity=row.plasticity,
                        sample=arrays["sample"].copy(),
                        record=row.kind.startswith("train-"),
                        plastic_groups=arrays["groups"].copy(),
                        n_groups=8,
                    )
                    attempt["returned"] = True
                    persist()
                    guard()
                    attempt["bounds"] = validate_call_result(row, inputs, before, result)
                    attempt["fingerprints"] = c._numeric_identities(result)
                    c.validate_fingerprints(attempt["fingerprints"], numeric_schema(row, inputs))
                    compact = compact_result(row, inputs, result)
                    data, meta = encode_result(compact)
                    attempt["compact"] = write_exclusive(directory / f"{position:04d}-compact.npz", data)
                    attempt["compact_metadata"] = write_exclusive(
                        directory / f"{position:04d}-compact.json", meta
                    )
                    validate_compact(row, inputs, before, compact)
                    if row.replay_of or row.id in state.replay_ids:
                        data, meta = encode_result(result)
                        attempt["result"] = write_exclusive(directory / f"{position:04d}-result.npz", data)
                        attempt["metadata"] = write_exclusive(directory / f"{position:04d}-result.json", meta)
                    persist()
                    guard()
                    if not np.array_equal(engine.gains, result["gains"]):
                        raise ValueError("Engine state differs from returned checkpoint.")
                    if row.replay_of:
                        saved = state.originals[row.replay_of]["artifact"]
                        original = decode_result(
                            read_artifact(directory, saved["result"]),
                            read_artifact(directory, saved["metadata"]),
                        )
                        replay = c.compare_numeric_results(
                            original, result, schema=numeric_schema(row, inputs)
                        )
                        if not replay["passed"]:
                            raise ValueError(
                                "Selected exact numerical replay failed: " + str(replay["differences"])
                            )
                        attempt["replay"] = dict(original=row.replay_of, passed=True)
                    state.accept(row, before, result, attempt)
                    attempt["status"] = "completed"
                    job["completed"] += 1
                except BaseException as exc:
                    attempt.update(status="failed", error=f"{type(exc).__name__}: {exc}")
                    raise
                finally:
                    persist()
                guard()
            state.score(current_stage)
            manifest["jobs"][-1]["status"] = "completed"
            verify_bindings(gate["bindings"])
            guard()
            manifest["status"] = "completed"
            ledger["status"] = "completed"
        except BaseException as exc:
            status = (
                "budget_stopped"
                if isinstance(exc, BudgetStopped)
                else "cancelled"
                if isinstance(exc, Cancelled)
                else "gate_failed"
                if isinstance(exc, GateFailed)
                else "failed"
            )
            manifest.update(status=status, error=f"{type(exc).__name__}: {exc}")
            ledger.update(status=status, error=manifest["error"])
            for job in manifest["jobs"]:
                if job["status"] != "completed":
                    job.update(
                        status=status if job["id"] == current_stage else "not_run_gate_failed",
                        error=manifest["error"],
                    )
        finally:
            ledger["verdicts"] = state.verdicts
            manifest["conditioning"]["status_reason"] = manifest.get("error")
            manifest["conditioning"]["stages"] = [
                dict(id=j["id"], status=j["status"], status_reason=j.get("error")) for j in manifest["jobs"]
            ]
            persist(final=True)
        return manifest


def compact_result(row, inputs, result):
    """Retain sufficient response/KC/gain/DAN/group observations, discarding per-step state."""
    a = inputs["arrays"]
    lo, hi = row.cue_window or (0, 0)
    compact = {
        k: result[k].copy()
        for k in (
            "gains",
            "gain_delta",
            "dan_counts",
            "compartment_dan_counts",
            "compartment_tonic_hz",
            "pulse_times_ms",
            "pulse_dan_indices",
        )
    }
    compact["cue_counts"] = result["trace"][lo // 10 : hi // 10].sum(0, dtype=np.int64)
    compact["sample_counts"] = result["trace"].sum(0, dtype=np.int64)
    compact["population"] = result["population"].copy()
    rec = result["instrumentation"]
    width = 8 if inputs["learning_rule"] == "rate-bridge-v1" else 7
    compact["electrical"] = np.zeros((8, width), np.float64)
    compact["tail"] = np.zeros((8, width), np.float64)
    if rec is not None:
        field = "bridge_rule" if width == 8 else "rule_bins"
        compact["electrical"] = rec[field].sum(0)
        if width == 8:
            compact["tail"] = rec["bridge_tail"].copy()
    pulses = sorted(set(row.teaching))
    observed = np.zeros((len(pulses), 2), np.float64)
    if rec is not None:
        for j, (t, ch) in enumerate(pulses):
            ci = c.CHANNELS.index(ch)
            observed[j] = [
                t,
                rec["step_signals"][round(t / 0.2), 1 + ci] * np.count_nonzero(a["dcomp"] == ci),
            ]
    compact["coincident_observed_dan_spikes"] = observed
    return compact


def validate_compact(row, inputs, before, compact):
    """Recompute compact evidence; native inclusive group observations are not per-edge paths."""
    a = inputs["arrays"]
    n = len(a["pk"])
    width = 8 if inputs["learning_rule"] == "rate-bridge-v1" else 7
    specs = {
        "gains": (np.float32, (n,)),
        "gain_delta": (np.float32, (n,)),
        "cue_counts": (np.int64, (len(a["sample"]),)),
        "sample_counts": (np.int64, (len(a["sample"]),)),
        "population": (np.int32, (row.duration_ms // 10,)),
        "dan_counts": (np.int32, (len(a["dans"]),)),
        "compartment_dan_counts": (np.int32, (2,)),
        "compartment_tonic_hz": (np.float32, (2,)),
        "pulse_times_ms": (np.float32, (len(numeric_schema(row, inputs).pulses),)),
        "pulse_dan_indices": (np.int32, (len(numeric_schema(row, inputs).pulses),)),
        "electrical": (np.float64, (8, width)),
        "tail": (np.float64, (8, width)),
        "coincident_observed_dan_spikes": (np.float64, (len(set(row.teaching)), 2)),
    }
    if set(compact) != set(specs):
        raise ValueError("Incomplete compact numerical evidence.")
    for name, (dtype, shape) in specs.items():
        v = compact[name]
        if not isinstance(v, np.ndarray) or v.dtype != dtype or v.shape != shape or not np.isfinite(v).all():
            raise ValueError("Malformed compact numerical family: " + name)
    for name in (
        "cue_counts",
        "sample_counts",
        "population",
        "dan_counts",
        "compartment_dan_counts",
        "compartment_tonic_hz",
        "coincident_observed_dan_spikes",
    ):
        if np.any(compact[name] < 0):
            raise ValueError("Negative compact count/activity evidence.")
    if (
        np.any(compact["cue_counts"] > 1500)
        or np.any(compact["sample_counts"] > row.duration_ms * 5)
        or np.any(compact["population"] > inputs["neurons"] * 50)
        or compact["sample_counts"].sum() > compact["population"].sum(dtype=np.int64)
    ):
        raise ValueError("Compact counts exceed cue/trial/per-bin/population bounds.")
    populations = np.array([np.count_nonzero(a["dcomp"] == ci) for ci in (0, 1)])
    baseline_counts = compact["compartment_tonic_hz"].astype(np.float64) * populations * 0.05
    if np.any(compact["compartment_tonic_hz"] > 5000) or np.any(
        baseline_counts
        > compact["compartment_dan_counts"] + np.finfo(np.float32).eps * 4 * np.maximum(baseline_counts, 1)
    ):
        raise ValueError("Compact tonic activity exceeds recorded DAN spike support.")
    for observed, (time_ms, channel) in zip(
        compact["coincident_observed_dan_spikes"], sorted(set(row.teaching))
    ):
        dan_size = populations[c.CHANNELS.index(channel)]
        if (
            observed[0] != time_ms
            or observed[1] > dan_size + np.finfo(np.float32).eps * dan_size * 4
            or abs(observed[1] - round(observed[1])) > np.finfo(np.float32).eps * dan_size * 4
        ):
            raise ValueError("Coincident observed DAN time/count domain differs.")
    if (
        compact["coincident_observed_dan_spikes"][:, 1].sum()
        > compact["dan_counts"].sum() + np.finfo(np.float32).eps * len(row.teaching) * len(a["dans"]) * 4
    ):
        raise ValueError("Coincident observations exceed all recorded DAN spikes.")
    if np.any(compact["cue_counts"] > compact["sample_counts"]):
        raise ValueError("Cue count exceeds whole trial count.")
    if not row.cue and np.any(compact["cue_counts"]):
        raise ValueError("Blank has a nonexistent cue window.")
    if (
        np.any(before <= 0.5)
        or np.any(before >= 1.5)
        or before.dtype != np.float32
        or before.shape != (n,)
        or not np.isfinite(before).all()
    ):
        raise ValueError("Invalid before checkpoint.")
    after = compact["gains"]
    if np.any(after <= 0.5) or np.any(after >= 1.5):
        raise ValueError("Inclusive final gain bound.")
    if not np.array_equal(compact["gain_delta"], after - before):
        raise ValueError("Compact gain delta differs.")
    if not np.array_equal(after[a["mask"] == 0], before[a["mask"] == 0]):
        raise ValueError("Excluded gain changed.")
    if not row.plasticity and after.tobytes() != before.tobytes():
        raise ValueError("Frozen/probe gain changed.")
    pulses = numeric_schema(row, inputs).pulses
    if not np.array_equal(
        compact["pulse_times_ms"], np.array([x[0] for x in pulses], np.float32)
    ) or not np.array_equal(compact["pulse_dan_indices"], np.array([x[1] for x in pulses], np.int32)):
        raise ValueError("Requested teaching pulse identities differ.")
    total = compact["electrical"] + compact["tail"]
    bounds = (5, 7) if width == 8 else (3, 5)
    published = 4 if width == 8 else 2
    for key in ("electrical", "tail"):
        values = compact[key]
        counts = values[:, bounds[0] : bounds[1]]
        if np.any(counts != 0):
            raise ValueError("Inclusive native electrical/tail bound observations.")
        if not row.kind.startswith("train-") and np.any(values):
            raise ValueError("Unrecorded probe has invented rule telemetry.")
        if not row.plasticity and np.any(values[:, : 5 if width == 8 else 3]):
            raise ValueError("Frozen gain products changed.")
        if width == 8 and (
            np.any(values[:, 0] < 0)
            or np.any(values[:, 1] > 0)
            or not np.allclose(values[:, 0] + values[:, 1], values[:, 2], rtol=1e-8, atol=1e-11)
            or not np.allclose(values[:, 2], values[:, 3], rtol=1e-8, atol=1e-11)
        ):
            raise ValueError("Compact true product/movement decomposition differs.")
    for group in range(8):
        expected = (after.astype(np.float64) - before)[a["groups"] == group].sum()
        if expected != total[group, published]:
            raise ValueError("Compact per-group gain publication differs.")
    if not np.array_equal(
        compact["dan_counts"], compact["sample_counts"][np.searchsorted(a["sample"], a["dans"])]
    ):
        raise ValueError("Compact individual DAN counts differ from sampled counts.")
    if not np.array_equal(
        compact["compartment_dan_counts"], [compact["dan_counts"][a["dcomp"] == ci].sum() for ci in (0, 1)]
    ):
        raise ValueError("Compact compartment DAN counts differ.")
    return {"electrical_bound_observations": 0, "tail_bound_observations": 0}


def append_attempt(path, event):
    with Path(path).open("ab") as stream:
        stream.write(event + b"\n")
        stream.flush()
        os.fsync(stream.fileno())


def validate_protocol(protocol):
    expected = dict(
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
        encoder="glomerular-tuning-v1",
        encoder_peak_hz=150.0,
        encoder_tuning_width=0.5,
        encoder_min_kc_contacts=100.0,
        kc_input_gain=1.25,
        sensory_input_gain=0.0,
        apl_output_gain=0.25,
        global_weight_scale=0.5,
        tau_ms=500.0,
        learning_rate=0.0005,
        gain_bounds=[0.5, 1.5],
        dan_reference="none",
        away_plasticity_mask="gamma",
    )
    if not isinstance(protocol, dict) or protocol.get("learning_rule") not in ("event", "rate-bridge-v1"):
        raise GateFailed("Unknown learning rule.")
    if protocol["learning_rule"] == "rate-bridge-v1":
        expected.update(
            rate_tau_ms=100.0,
            bridge_normalization=0.96,
            bridge_tail="analytic_no_new_event_tail",
            bridge_layout="rate-bridge-v1/1",
        )
    for key, wanted in expected.items():
        actual = protocol.get(key)
        if isinstance(wanted, (int, float)):
            valid = type(actual) in (int, float) and actual == wanted
        else:
            valid = actual == wanted
        if not valid:
            raise GateFailed("Accepted scientific protocol changed: " + key)
