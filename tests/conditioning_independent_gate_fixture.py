"""Temporary synthetic diagnostic evidence for real validator/qualifier acceptance.

Never executes a neuron or native library. Large immutable inputs are linked
read-only by convention into the temporary fixture and must never be mutated.
Synthetic diagnostic arrays are newly created and unmistakably named synthetic.
"""

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil

import numpy as np


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def array_sha(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, allow_nan=False, sort_keys=True)


def make_synthetic_qualifying_pair(tmp_root, repository_root):
    from bet36fly.reward_evidence import list_reward_evidence
    from bet36fly.conditioning_runner import DOCUMENTS, SOURCES

    root, repo = Path(tmp_root).resolve(), Path(repository_root).resolve()
    if root == repo or any(root.iterdir()):
        raise ValueError("Synthetic fixture requires an empty separate temporary root")
    diag = repo / "output/diagnostics/diag-rate-bridge-v1-maskgamma-de050d773763"
    template = json.loads((diag / "summary.json").read_text())
    source_identity = template["identity"]
    evidence = root / "docs/evidence/reward-mechanism-repair-2026-09-12"
    immutable = []

    def copy_input(relative):
        source, dest = repo / relative, root / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            return
        if source.stat().st_size > 1_000_000:
            os.link(source, dest)
            mode = "read-only-immutable-hardlink-never-mutate"
        else:
            shutil.copyfile(source, dest)
            mode = "independent-copy"
        immutable.append(dict(source=str(source), fixture=str(dest), mode=mode, sha256=sha(source)))

    for relative in source_identity["graph_hashes"]:
        copy_input(relative)
    for name in source_identity["code_hashes"]:
        copy_input(("scripts/" if name == "reward_teaching_diagnostic.py" else "bet36fly/") + name)
    for suffix in ("manifest.json", "source/inputs.npz", "source/protocol.json"):
        copy_input(f"output/experiments/{source_identity['pilot']}/{suffix}")
    native_relative = Path(template["native_binary"]["path"]).relative_to(repo)
    copy_input(native_relative)
    for name in DOCUMENTS:
        copy_input(Path("docs/evidence/reward-mechanism-repair-2026-09-12") / name)
    for name in SOURCES:
        copy_input(name)
    for name in source_identity.get("bridge_contract", {}).get("documents", {}):
        copy_input(Path("docs/evidence/reward-mechanism-repair-2026-09-12") / name)
    with np.load(diag / "trials.npz", allow_pickle=False) as z:
        common = {
            k: z[k].copy()
            for k in ("plastic_compartments", "plastic_groups", "plastic_mask", "kc_classes", "blank_gains")
        }
    blank = common["blank_gains"]
    comp, mask, groups = (
        common["plastic_compartments"],
        common["plastic_mask"].astype(bool),
        common["plastic_groups"],
    )
    target_edge = [int(np.flatnonzero(mask & (comp == ci))[0]) for ci in (0, 1)]
    steps = int(source_identity["protocol"]["duration_ms"] * 5)
    replay_template = json.loads((diag / "replay-evidence.json").read_text())
    layout = json.loads((diag / "recording-layout.json").read_text())
    calibration = source_identity["selection"]["calibration_games"]
    locks = {}
    for role, offset, noise in (("original", 0, 0), ("held-out", 8, 2_000_000)):
        run_id = "diag-rate-bridge-v1-synthetic-independent-" + role
        directory = root / "output/diagnostics" / run_id
        directory.mkdir(parents=True)
        chosen = calibration[offset : offset + 8]
        selection = dict(
            panel_kind=role,
            panel_offset=offset,
            seed_offset=noise,
            alt_seed_offset=1_000_000,
            calibration_games=calibration,
            panel_games=chosen,
            cumulative_games=calibration,
            expected_panel=[
                dict(game=g, seed_set=s, seed=42 + noise + g + n, condition=c)
                for g in chosen
                for s, n in (("base", 0), ("alt", 1_000_000))
                for c in ("frozen", "untaught", "home", "away")
            ],
            expected_cumulative=[dict(game=g, seed=42 + noise + g) for g in calibration],
        )
        identity = copy.deepcopy(source_identity)
        identity.update(panel_kind=role, selection=selection)
        arrays = dict(common)
        rows = []
        replay = {}
        for selected in selection["expected_panel"]:
            condition = selected["condition"]
            before = blank.copy()
            after = blank.copy()
            if condition in ("home", "away"):
                after[target_edge[0 if condition == "home" else 1]] -= np.float32(0.125)
            delta = after - before
            rule = np.zeros((steps, 8, 8), np.float64)
            tail = np.zeros((8, 8), np.float64)
            for ci, edge in enumerate(target_edge):
                if delta[edge]:
                    rule[500, groups[edge], [1, 2, 3, 4]] = float(delta[edge])
            prefix = f"{selected['game']}__{selected['seed_set']}__{condition}"
            original_fp = replay_template[condition]["original"]
            sampled = np.zeros(original_fp["trace"][1], dtype=original_fp["trace"][0])
            signals = np.zeros(original_fp["instrumentation/bridge_signals"][1], np.float64)
            kc_bins = np.zeros(original_fp["instrumentation/bridge_kc_bins"][1], np.float64)
            used = np.zeros(original_fp["instrumentation/bridge_kc_used"][1], np.float64)
            sensory = np.zeros((40, 1), np.int32)
            stored = dict(
                gains=after,
                gain_delta=delta,
                bridge_rule=rule,
                bridge_tail=tail,
                sampled_bins=sampled,
                bridge_signals=signals,
                bridge_kc_bins=kc_bins,
                bridge_kc_used=used,
                sensory_bins=sensory,
            )
            arrays.update({prefix + "__" + k: v for k, v in stored.items()})
            rows.append(
                dict(
                    selected,
                    applied=[float(delta[comp == ci].astype(np.float64).sum()) for ci in (0, 1)],
                    clipped=0,
                    electrical_bound_observations=0,
                    tail_bound_observations=0,
                    sensory_bins_sha256=array_sha(sensory),
                )
            )
            if selected["game"] == chosen[0] and selected["seed_set"] == "base":
                actual = dict(gains=after, gain_delta=delta, trace=sampled)
                actual.update(
                    {
                        "instrumentation/" + k: stored[k]
                        for k in (
                            "bridge_rule",
                            "bridge_tail",
                            "bridge_signals",
                            "bridge_kc_bins",
                            "bridge_kc_used",
                        )
                    }
                )
                fps = {}
                for name, (dtype, shape, _) in original_fp.items():
                    a = actual[name] if name in actual else np.zeros(shape, dtype=dtype)
                    fps[name] = [str(a.dtype), list(a.shape), array_sha(a)]
                replay[condition] = dict(original=fps, repeat=copy.deepcopy(fps))
        cumulative = []
        for selected in selection["expected_cumulative"]:
            prefix = f"cumulative_{selected['game']}"
            arrays[prefix + "__gains"] = blank.copy()
            arrays[prefix + "__gain_delta"] = np.zeros_like(blank)
            arrays[prefix + "__bridge_rule"] = np.zeros((steps, 8, 8), np.float64)
            arrays[prefix + "__bridge_tail"] = np.zeros((8, 8), np.float64)
            cumulative.append(
                dict(
                    selected,
                    applied=[0.0, 0.0],
                    cumulative=[0.0, 0.0],
                    clipped=0,
                    electrical_bound_observations=0,
                    tail_bound_observations=0,
                )
            )
        arrays["cumulative_final_gains"] = blank.copy()
        np.savez_compressed(directory / "trials.npz", **arrays)
        write_json(directory / "recording-layout.json", layout)
        write_json(directory / "replay-evidence.json", replay)
        criteria = {
            name: dict(passed=True)
            for name in (
                "teaching_specific",
                "untaught_guard",
                "cross_compartment",
                "no_bound_hits",
                "cumulative",
                "bit_identical_repeat",
                "sensory_noise_invariance",
            )
        }
        summary = dict(
            run_id=run_id,
            created_at="2026-09-13T00:00:00Z",
            rule="rate-bridge-v1",
            panel_note="SYNTHETIC TEST FIXTURE: manufactured arrays; zero native calls; never scientific evidence.",
            panel_complete=True,
            all_passed=True,
            source_unchanged_during_run=True,
            identity=identity,
            native_binary=dict(path=str(root / native_relative), sha256=sha(root / native_relative)),
            rows=rows,
            cumulative_rows=cumulative,
            criteria=criteria,
            artifacts={
                name: dict(bytes=(directory / name).stat().st_size, sha256=sha(directory / name))
                for name in ("trials.npz", "recording-layout.json", "replay-evidence.json")
            },
        )
        prereg = dict(
            run_id=run_id,
            identity=identity,
            status="preregistered-not-run",
            criteria=dict(
                teaching_effect_ratio=3.0,
                untaught_sd_ratio=0.5,
                cross_compartment_ratio=0.05,
                cumulative_effect_ratio=4.0,
                no_bound_hits=True,
                bit_identical_repeat=True,
                sensory_noise_invariance=True,
            ),
        )
        write_json(directory / "preregistration.json", prereg)
        write_json(directory / "summary.json", summary)
        write_json(evidence / f"panel-{run_id}.json", summary)
        locks[role] = dict(
            run_id=run_id,
            summary_sha256=sha(directory / "summary.json"),
            trials_sha256=sha(directory / "trials.npz"),
            measured_code_hashes=identity["code_hashes"],
        )
    write_json(
        evidence / "bridge-residual-attribution.json",
        dict(scope="SYNTHETIC SOFTWARE FIXTURE ONLY", runs=locks),
    )
    index = list_reward_evidence(root)
    pairs = index["qualification_pairs"]
    if (
        len(pairs) != 1
        or pairs[0]["validation_status"] != "validated"
        or pairs[0]["evidence_status"] != "passed"
    ):
        raise AssertionError(index)
    return pairs[0]["pair_id"], dict(
        synthetic=True,
        native_calls=0,
        immutable_inputs=immutable,
        diagnostics=index["diagnostics"],
        pair=pairs[0],
    )
