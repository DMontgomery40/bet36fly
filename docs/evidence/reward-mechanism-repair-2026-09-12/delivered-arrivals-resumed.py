"""Saved-raster KC input accounting only. Never imports or calls the simulator."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow.feather as feather

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent
CAPTURE_ID = "onset-history-capture-4343c21535c43f42"
CAPTURE = HERE / "onset-history-captures" / CAPTURE_ID
SUMMARY_SHA = "244b4dcc1aa40b8c0c7be068bf7e66f8e369921f1005dd474ca37f9460dabb1b"
SAMPLE_SHA = "5f2414ffe5cab3d99cc1c1f0e91071df1f48721a7709816e90360af8b41074b3"
RUNS = ("diag-rate-bridge-v1-maskgamma-de050d773763",
        "diag-rate-bridge-v1-maskgamma-dea14759e9ca")
FAMILIES = ("gamma", "apbp", "ab", "other")
PHASES = (("0-100ms", 0, 500), ("100-130ms", 500, 650),
          ("130-300ms", 650, 1500), ("300-400ms", 1500, 2000))


def digest(path):
    with Path(path).open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def array_identity(array):
    return dict(dtype=str(array.dtype), shape=list(array.shape),
                sha256=hashlib.sha256(array.tobytes(order="C")).hexdigest())


def expected_rows():
    panels = ((4362, 4366, 4370, 4374, 4378, 4383, 4387, 4391),
              (4395, 4399, 4404, 4408, 4412, 4416, 4420, 4425))
    return [dict(game=game, seed_set=label,
                 seed=42 + game + 2_000_000 * panel + 1_000_000 * noise,
                 run_id=RUNS[panel])
            for panel, games in enumerate(panels) for game in games
            for noise, label in enumerate(("base", "alt"))]


def integer_vector(values, label, lower, upper):
    array = np.asarray(values)
    if array.ndim != 1 or array.dtype.kind not in "iu":
        raise ValueError(f"{label} must be an integer vector")
    if np.any(array < lower) or np.any(array >= upper):
        raise ValueError(f"{label} outside recorded interval")
    return array.astype(np.int64)


def classify(emission_steps, target_spikes, steps, *, delay=9, refractory=11):
    """An arrival coincident with a new target spike sees the PREVIOUS ready."""
    if steps <= 0 or delay < 1 or refractory < 1:
        raise ValueError("Invalid discrete timing")
    emitted = integer_vector(emission_steps, "emissions", 0, steps)
    spikes = integer_vector(target_spikes, "target spikes", 0, steps)
    if np.any(np.diff(spikes) < refractory):
        raise ValueError("Target spikes violate ordered refractory history")
    due = emitted + delay
    previous = np.searchsorted(spikes, due, side="left") - 1
    ready = np.zeros(len(due), dtype=np.int64)
    has_previous = previous >= 0
    ready[has_previous] = spikes[previous[has_previous]] + refractory
    pending = due >= steps
    accepted = (~pending) & (due >= ready)
    rejected = (~pending) & (due < ready)
    return dict(due=due, ready=ready, accepted=accepted, rejected=rejected,
                pending=pending, same_step=accepted & np.isin(due, spikes))


def conductance_ledger(increments, target_spikes, *, dt=.2, tau=5.):
    """Float64 KC-only bookkeeping under observed resets, NOT native g replay.

    Exact recorded acceptance and float32 edge increments are inputs. Non-KC
    terms and the native mixed-sign float32 accumulation rounding are absent.
    The ledger never evaluates a threshold or predicts a target spike.
    """
    increments = np.asarray(increments, dtype=np.float64)
    if increments.ndim != 2 or not np.isfinite(increments).all():
        raise ValueError("Expected finite step-by-family increments")
    if np.any(increments < 0) or dt <= 0 or tau <= 0:
        raise ValueError("This ledger represents nonnegative KC fast input")
    steps, families = increments.shape
    spikes = integer_vector(target_spikes, "target spikes", 0, steps)
    if len(np.unique(spikes)) != len(spikes):
        raise ValueError("Duplicate target spikes")
    spike_set = set(spikes.tolist())
    decay = np.exp(-dt / tau)
    residual = np.zeros(families)
    resets = np.zeros_like(increments)
    losses = np.zeros_like(increments)
    pre_integration = np.zeros_like(increments)
    for step in range(steps):
        residual += increments[step]
        pre_integration[step] = residual
        losses[step] = residual * (1 - decay)
        residual *= decay
        if step in spike_set:
            resets[step] = residual
            residual = np.zeros(families)
    np.testing.assert_allclose(increments.sum(0), losses.sum(0) + resets.sum(0) + residual,
                               rtol=1e-12, atol=1e-10)
    return dict(pre_integration=pre_integration, decay_losses=losses,
                spike_resets=resets, endpoint=residual)


def summarize_target(kc_events, edge_kc_columns, weights, contacts, families, target_spikes):
    """Each source event traversing one directed edge counts once; contacts weight it."""
    source_events = np.asarray(kc_events)
    if source_events.ndim != 2 or not np.isin(source_events, (0, 1)).all():
        raise ValueError("Expected binary time-resolved KC raster")
    steps = source_events.shape[0]
    columns = integer_vector(edge_kc_columns, "edge KC columns", 0, source_events.shape[1])
    families = integer_vector(families, "edge families", 0, len(FAMILIES))
    weights = np.asarray(weights, dtype=np.float64)
    contacts = np.asarray(contacts)
    if not (len(columns) == len(weights) == len(contacts) == len(families)):
        raise ValueError("Unaligned edge metadata")
    if (not np.isfinite(weights).all() or np.any(weights <= 0)
            or contacts.dtype.kind not in "iuf" or not np.isfinite(contacts).all()
            or np.any(contacts <= 0) or np.any(contacts != np.floor(contacts))):
        raise ValueError("Invalid excitatory KC weight or contact count")
    contacts = contacts.astype(np.int64)
    if len(np.unique(columns)) != len(columns):
        raise ValueError("Duplicate source-target edge")
    emitted, edge = np.nonzero(source_events[:, columns])
    event_families = families[edge]
    event_weights = weights[edge]
    event_contacts = contacts[edge]
    labels = classify(emitted, target_spikes, steps)
    due = labels["due"]
    accepted_increment = np.zeros((steps, len(FAMILIES)), dtype=np.float64)
    accepted_counts = np.zeros_like(accepted_increment, dtype=np.int64)
    rejected_increment = np.zeros_like(accepted_increment)
    rejected_counts = np.zeros_like(accepted_counts)
    for status, amounts, numbers in (("accepted", accepted_increment, accepted_counts),
                                    ("rejected", rejected_increment, rejected_counts)):
        selected = labels[status]
        np.add.at(amounts, (due[selected], event_families[selected]), event_weights[selected])
        np.add.at(numbers, (due[selected], event_families[selected]), 1)
    ledger = conductance_ledger(accepted_increment, target_spikes)

    def aggregate(selection):
        return dict(edge_events=int(selection.sum()),
                    contact_events=int(event_contacts[selection].sum()),
                    conductance_increment_sum=float(event_weights[selection].sum()))

    totals = {name: aggregate(labels[name]) for name in ("accepted", "rejected", "pending", "same_step")}
    totals["emitted"] = aggregate(np.ones(len(emitted), dtype=bool))
    totals["due_in_window"] = aggregate(~labels["pending"])
    totals["last_emission_ms"] = float(emitted.max() * .2) if len(emitted) else None
    totals["last_in_window_due_ms"] = float(due[~labels["pending"]].max() * .2) if (~labels["pending"]).any() else None
    phases = []
    for name, low, high in PHASES:
        if high > steps:
            continue
        phase = (due >= low) & (due < high)
        for family, label in enumerate(FAMILIES):
            selected = phase & (event_families == family)
            phases.append(dict(phase=name, family=label,
                               due=aggregate(selected),
                               accepted=aggregate(selected & labels["accepted"]),
                               refractory_discarded=aggregate(selected & labels["rejected"]),
                               same_step_accepted=aggregate(selected & labels["same_step"]),
                               conditional_g_spike_reset=float(ledger["spike_resets"][low:high, family].sum()),
                               conditional_g_decay_loss=float(ledger["decay_losses"][low:high, family].sum())))
    pending = [dict(emission_step=int(emitted[i]), due_step=int(due[i]), edge_position=int(edge[i]),
                    family=FAMILIES[event_families[i]], contacts=int(event_contacts[i]),
                    conductance_increment=float(event_weights[i])) for i in np.flatnonzero(labels["pending"])]
    return dict(totals=totals, phases=phases, pending_events=pending,
                target_spike_steps=np.asarray(target_spikes).tolist(),
                conditional_g_endpoint=ledger["endpoint"].tolist()), dict(
                    accepted_increment=accepted_increment, accepted_counts=accepted_counts,
                    refractory_discarded_increment=rejected_increment,
                    refractory_discarded_counts=rejected_counts, **ledger)


def family(type_label):
    if type_label.startswith("KCg"):
        return 0
    if type_label.startswith("KCa'b'"):
        return 1
    if type_label.startswith("KCab"):
        return 2
    return 3


def read_inputs():
    """Fail on changed captured evidence or graph; no model construction."""
    checked = {}

    def check(path, expected):
        path = Path(path)
        found = digest(path)
        if found != expected:
            raise ValueError(f"Hash mismatch: {path}")
        checked[str(path.relative_to(ROOT))] = dict(sha256=found, bytes=path.stat().st_size)

    check(CAPTURE / "summary.json", SUMMARY_SHA)
    summary = json.loads((CAPTURE / "summary.json").read_text())
    identity = summary["identity"]
    if (summary["status"] != "complete" or summary["run_id"] != CAPTURE_ID
            or summary["attempted_calls"] != 33 or summary["calls"] != 33
            or identity["rows"] != expected_rows()
            or [{key: row[key] for key in ("game", "seed_set", "seed", "run_id")}
                for row in summary["rows"]] != expected_rows()):
        raise ValueError("Capture/selector contract mismatch")
    for name, expected in identity["graph_hashes"].items():
        check(ROOT / name, expected)
    for name in ("reward_lif.cpp", "reward_brain.py", "reward_protocol.py", "reward_encoder.py"):
        check(ROOT / "bet36fly" / name, identity["source_code"][name])
    check(identity["native_binary"]["path"], identity["native_binary"]["sha256"])
    pilot = Path(identity["pilot"])
    for name, key in (("source/inputs.npz", "inputs_sha256"), ("manifest.json", "pilot_manifest_sha256"),
                      ("source/protocol.json", "pilot_protocol_sha256")):
        check(pilot / name, identity[key])
    for run_id, prior in identity["prior"].items():
        folder = ROOT / "output/diagnostics" / run_id
        check(folder / "summary.json", prior["summary_sha256"])
        for name, info in prior["artifacts"].items():
            check(folder / name, info["sha256"])
    sample_path = ROOT / "docs/evidence/reward-mechanism-repair-2026-09-12/onset-capture-preregistration.samples.npz"
    check(sample_path, SAMPLE_SHA)
    with np.load(sample_path, allow_pickle=False) as archive:
        maps = {name: archive[name] for name in archive.files}
    for name, expected in identity["sample_arrays"].items():
        if array_identity(maps[name]) != expected:
            raise ValueError(f"Sample mapping mismatch: {name}")
    arrays = {name: np.load(ROOT / f"data/brain/{name}.npy", mmap_mode="r")
              for name in ("ids", "indptr", "post", "counts", "signs", "kc", "sensory", "mbon")}
    np.testing.assert_array_equal(arrays["ids"][maps["sample"]], maps["body_ids"])
    np.testing.assert_array_equal(arrays["kc"], maps["kc_indices"])
    nodes = feather.read_table(ROOT / "data/brain/nodes.feather").to_pandas().set_index("bodyId").reindex(arrays["ids"])
    if nodes.index.duplicated().any() or len(maps["sample"]) != 4774 or len(maps["kc_indices"]) != 4064:
        raise ValueError("Cell identity mismatch")
    np.testing.assert_array_equal(maps["sample"], np.unique(maps["sample"]))
    for role in ("kc", "dan", "sensory"):
        np.testing.assert_array_equal(maps["sample"][maps[role + "_columns"]], maps[role + "_indices"])
    return summary, maps, arrays, nodes, checked, check


def run(output):
    # Refuse every planned output before any substantive reading/writing.
    paths = [output.with_suffix(".json"), output.with_suffix(".npz")]
    if any(path.exists() for path in paths):
        raise FileExistsError("Preserve prior analysis; choose an unused output prefix")
    summary, maps, arrays, nodes, checked, check = read_inputs()
    ids, ptr, post = (arrays[name] for name in ("ids", "indptr", "post"))
    kc_families = np.array([family(str(value)) for value in nodes.iloc[maps["kc_indices"]]["type"]])
    if np.bincount(kc_families, minlength=4).tolist() != [1557, 695, 1810, 2]:
        raise ValueError("KC family identity mismatch")
    target_data, anatomy = {}, []
    for target_body in (11327, 11900):
        target = np.flatnonzero(ids == target_body).item()
        if nodes.iloc[target]["type"] != "PPL101":
            raise ValueError("Wrong target type")
        edges = np.flatnonzero(post == target)
        sources = np.searchsorted(ptr, edges, side="right") - 1
        is_kc = np.isin(sources, maps["kc_indices"])
        kc_sources = sources[is_kc]
        lookup = {int(value): index for index, value in enumerate(maps["kc_indices"])}
        kc_columns = np.array([lookup[int(source)] for source in kc_sources], dtype=np.int64)
        contacts = arrays["counts"][edges[is_kc]]
        signs = arrays["signs"][kc_sources]
        if (not np.all(signs == 1) or not (nodes.iloc[kc_sources]["transmitter"] == "acetylcholine").all()
                or np.isin(target, arrays["kc"]) or np.isin(target, arrays["sensory"])):
            raise ValueError("KC target/input weighting assumption invalid")
        weights = np.asarray(contacts * signs.astype(np.float32) * np.float32(.1375), dtype=np.float32)
        target_column = np.flatnonzero(maps["sample"] == target).item()
        target_data[target_body] = dict(target=target, column=target_column, kc_columns=kc_columns,
                                       weights=weights, contacts=contacts, families=kc_families[kc_columns],
                                       source_body_ids=ids[kc_sources].tolist(), edge_indices=edges[is_kc].tolist())
        nonkc = ~is_kc
        recorded = np.isin(sources, maps["sample"])
        anatomy.append(dict(body_id=target_body, graph_index=target, incoming_edges=len(edges),
                            incoming_contacts=int(arrays["counts"][edges].sum()),
                            kc_edges=int(is_kc.sum()), kc_contacts=int(contacts.sum()),
                            nonkc_edges=int(nonkc.sum()), nonkc_contacts=int(arrays["counts"][edges[nonkc]].sum()),
                            nonkc_without_raster_edges=int((nonkc & ~recorded).sum()),
                            nonkc_without_raster_contacts=int(arrays["counts"][edges[nonkc & ~recorded]].sum()),
                            nonkc_with_raster_body_ids=ids[sources[nonkc & recorded]].tolist(),
                            family_edges={label: int((kc_families[kc_columns] == f).sum()) for f, label in enumerate(FAMILIES)},
                            family_contacts={label: int(contacts[kc_families[kc_columns] == f].sum()) for f, label in enumerate(FAMILIES)}))
    rows, time_series = [], {}
    saved = {entry["name"]: entry for entry in summary["saved"]}
    for index, row in enumerate(expected_rows()):
        name = f"fine_{index:02d}"
        entry = saved[name]
        path = CAPTURE / entry["file"]
        check(path, entry["sha256"])
        if entry["metadata"]["dt"] != .2 or entry["metadata"]["bin_ms"] != .2 or entry["metadata"]["duration_ms"] != 400:
            raise ValueError("Wrong actual raster timing")
        with np.load(path, allow_pickle=False) as archive:
            trace, counts, gains = (archive[key] for key in ("trace", "counts", "gains"))
            if set(archive.files) != set(entry["numeric_fingerprint"]):
                raise ValueError("Changed returned array contract")
            for key in archive.files:
                if array_identity(archive[key]) != entry["numeric_fingerprint"][key]:
                    raise ValueError(f"Array identity changed: {name}/{key}")
            if archive["pulse_times_ms"].size or archive["pulse_dan_indices"].size:
                raise ValueError("Expected untaught actual recording")
        if trace.shape != (2000, 4774) or not np.isin(trace, (0, 1)).all():
            raise ValueError("Wrong actual binary raster")
        np.testing.assert_array_equal(counts[maps["sample"]], trace.sum(0))
        kc_events = trace[:, maps["kc_columns"]]
        home_delta = float((gains.astype(float) - 1)[maps["plastic_compartments"] == 0].sum())
        np.testing.assert_allclose(home_delta, summary["rows"][index]["effects"]["cold"]["published"][0], rtol=0, atol=0)
        for body, info in target_data.items():
            spikes = np.flatnonzero(trace[:, info["column"]])
            result, series = summarize_target(kc_events, info["kc_columns"], info["weights"],
                                              info["contacts"], info["families"], spikes)
            for pending in result["pending_events"]:
                edge = pending.pop("edge_position")
                pending.update(source_body_id=int(info["source_body_ids"][edge]), edge_index=int(info["edge_indices"][edge]))
            rows.append(dict(row, fine_index=index, panel="original" if index < 16 else "second",
                             target_body_id=body, home_gain_delta=home_delta, **result))
            for key, values in series.items():
                time_series[f"{index:02d}_{body}_{key}"] = values
    groups = []
    for panel in ("original", "second"):
        for seed_set in ("base", "alt"):
            for body in (11327, 11900):
                selected = [row for row in rows if row["panel"] == panel and row["seed_set"] == seed_set and row["target_body_id"] == body]
                if len(selected) != 8:
                    raise ValueError("Incomplete target/group matrix")
                fields = {}
                for status in ("emitted", "due_in_window", "accepted", "rejected", "pending", "same_step"):
                    for metric in ("edge_events", "contact_events", "conductance_increment_sum"):
                        values = np.array([row["totals"][status][metric] for row in selected])
                        fields[status + "/" + metric] = dict(mean=float(values.mean()), sd=float(values.std(ddof=1)), values=values.tolist())
                spikes = np.array([len(row["target_spike_steps"]) for row in selected])
                fields["target_spikes"] = dict(mean=float(spikes.mean()), sd=float(spikes.std(ddof=1)), values=spikes.tolist())
                phase_means = []
                for phase_index, phase in enumerate(selected[0]["phases"]):
                    record = dict(phase=phase["phase"], family=phase["family"])
                    for status in ("due", "accepted", "refractory_discarded", "same_step_accepted"):
                        record[status] = {metric: float(np.mean([row["phases"][phase_index][status][metric] for row in selected]))
                                          for metric in ("edge_events", "contact_events", "conductance_increment_sum")}
                    for key in ("conditional_g_spike_reset", "conditional_g_decay_loss"):
                        record[key] = float(np.mean([row["phases"][phase_index][key] for row in selected]))
                    phase_means.append(record)
                groups.append(dict(panel=panel, seed_set=seed_set, target_body_id=body, trials=8,
                                   game_order=[row["game"] for row in selected], fields=fields, phase_means=phase_means))
    report = dict(status="complete-saved-artifact-analysis", source_capture=CAPTURE_ID,
                  script_sha256=digest(__file__), inputs=checked, selectors=expected_rows(),
                  contract=dict(dt_ms=.2, delay_steps=9, refractory_steps=11, executed_steps=[0, 1999],
                                phase_boundaries_steps=[0, 500, 650, 1500, 2000], pending_due_step_min=2000,
                                same_step="Accept against previous ready before integrating and resetting on the recorded spike",
                                conductance="Float32 static KC edge increment; sums and conditional decay/reset accounting use float64",
                                counterfactual_firing=False, nonkc_missing_timing="Unknown, never treated as zero",
                                no_native_calls=True, causal_ablation=False),
                  anatomy=anatomy, groups=groups, trials=rows,
                  limits=["Static contacts are not event counts or currents.",
                          "Accepted increments are not full native g/v states; incoming non-KC rasters and mixed-input float rounding are absent.",
                          "Conditional KC-only decay/reset accounting uses observed spikes without threshold evaluation or counterfactual firing.",
                          "Phase labels apply to arrival and reset times, not learning-update causation.",
                          "Original and second groups have different cues and noise; descriptive differences are not an intervention.",
                          "The second-panel guard remains failed; no qualifying acquisition/reversal result is created."])
    with paths[1].open("xb") as file:
        np.savez_compressed(file, **time_series)
    report["time_series_artifact"] = dict(path=str(paths[1].relative_to(ROOT)), sha256=digest(paths[1]), bytes=paths[1].stat().st_size)
    with paths[0].open("x") as file:
        json.dump(report, file, indent=2, allow_nan=False)
        file.write("\n")
    print(json.dumps(dict(output=str(paths[0]), rows=len(rows), input_files=len(checked),
                          groups=[dict(panel=g["panel"], seed_set=g["seed_set"], target=g["target_body_id"],
                                       accepted=g["fields"]["accepted/conductance_increment_sum"]["mean"],
                                       rejected=g["fields"]["rejected/conductance_increment_sum"]["mean"],
                                       spikes=g["fields"]["target_spikes"]["mean"]) for g in groups]), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "delivered-arrivals-resumed-result")
    run(parser.parse_args().output)
