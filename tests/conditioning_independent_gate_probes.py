"""Real validator -> qualifier, using disposable synthetic diagnostic pairs only."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from conditioning_independent_gate_fixture import make_synthetic_qualifying_pair, sha


def run(repo):
    from bet36fly import conditioning_runner as runner
    from bet36fly.reward_evidence import list_reward_evidence

    results = []
    with TemporaryDirectory(prefix="conditioning-independent-synthetic-") as directory:
        root = Path(directory)
        pair, receipt = make_synthetic_qualifying_pair(root, repo)
        positive = runner.qualify(root, pair)
        results.append(
            dict(
                case="complete-synthetic-pair",
                expected="accepted",
                actual="accepted",
                bindings=len(positive["bindings"]),
            )
        )
        writable = [
            *root.glob("output/diagnostics/*/*.json"),
            *root.glob("docs/evidence/reward-mechanism-repair-2026-09-12/*"),
        ]
        snapshots = {p: p.read_bytes() for p in writable if p.is_file()}

        def reset():
            for path, content in snapshots.items():
                path.write_bytes(content)

        def alter_identity(mutator):
            locks = root / runner.DOC_DIR / "bridge-residual-attribution.json"
            registry = json.loads(locks.read_text())
            for role, entry in registry["runs"].items():
                folder = root / "output/diagnostics" / entry["run_id"]
                for name in ("summary.json", "preregistration.json"):
                    path = folder / name
                    value = json.loads(path.read_text())
                    mutator(value)
                    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False))
                    if name == "summary.json":
                        (root / runner.DOC_DIR / f"panel-{entry['run_id']}.json").write_bytes(
                            path.read_bytes()
                        )
                        entry["summary_sha256"] = sha(path)
                        entry["measured_code_hashes"] = value["identity"]["code_hashes"]
            locks.write_text(json.dumps(registry, sort_keys=True))

        def protocol(key, value):
            return lambda data: data["identity"]["protocol"].__setitem__(key, value)

        def native_path(data):
            if "native_binary" in data:
                data["native_binary"]["path"] = str(root / "outside-approved-native.so")

        def source_escape(data):
            value = data["identity"]["code_hashes"].pop("reward_lif.cpp")
            data["identity"]["code_hashes"]["../../outside-source.cpp"] = value

        def graph_escape(data):
            value = data["identity"]["graph_hashes"].pop("data/brain/counts.npy")
            data["identity"]["graph_hashes"]["../../outside-graph.npy"] = value

        cases = [
            ("native-path-outside-approved-inventory", native_path),
            ("source-name-traversal", source_escape),
            ("graph-name-traversal", graph_escape),
            ("pilot-name-traversal", lambda d: d["identity"].__setitem__("pilot", "../outside-pilot")),
            ("apl-gain-retune", protocol("apl_output_gain", 0.5)),
            ("kc-gain-retune", protocol("kc_input_gain", 1.5)),
            ("global-weight-retune", protocol("global_weight_scale", 0.6)),
            (
                "source-hash-stale",
                lambda d: d["identity"]["code_hashes"].__setitem__("reward_lif.cpp", "0" * 64),
            ),
        ]
        for name, mutation in cases:
            reset()
            alter_identity(mutation)
            index = list_reward_evidence(root)
            possible = index["qualification_pairs"]
            selected = possible[0]["pair_id"] if len(possible) == 1 else pair
            try:
                runner.qualify(root, selected)
            except (ValueError, OSError, KeyError) as error:
                results.append(
                    dict(
                        case=name,
                        expected="rejected",
                        actual="rejected",
                        error_type=type(error).__name__,
                        reason=str(error),
                        reader_pair_status=possible[0]["validation_status"]
                        if len(possible) == 1
                        else "no-single-pair",
                    )
                )
            else:
                results.append(dict(case=name, expected="rejected", actual="ACCEPTED"))
        for name in ("conditioning-preregistration.md", "rate-bridge-preregistration.md"):
            reset()
            path = root / runner.DOC_DIR / name
            # Mutate only an independently copied small narrative, never a hardlink.
            assert path.stat().st_nlink == 1
            path.write_bytes(path.read_bytes() + b"\nSYNTHETIC TEST MUTATION\n")
            try:
                runner.qualify(root, pair)
            except (ValueError, OSError, KeyError) as error:
                actual, reason = "rejected", str(error)
            else:
                actual, reason = (
                    "accepted",
                    "New conditioning document receives a new binding; bridge source document must match qualifying identity.",
                )
            expected = "accepted" if name == "conditioning-preregistration.md" else "rejected"
            results.append(
                dict(case="document-change-" + name, expected=expected, actual=actual, reason=reason)
            )
        for filename in ("trials.npz", "summary.json", "replay-evidence.json"):
            from bet36fly import reward_evidence

            reset()
            target = root / "output/diagnostics" / receipt["pair"]["original_run_id"] / filename
            original = target.read_bytes()
            invoked = False
            real_index = reward_evidence.list_reward_evidence

            def replace_after_validated_index(requested_root):
                nonlocal invoked
                index = real_index(requested_root)
                if not invoked:
                    invoked = True
                    if filename == "trials.npz":
                        target.write_bytes(b"X" + original[1:])
                    else:
                        value = json.loads(original)
                        if filename == "summary.json":
                            value["rows"][0]["applied"][0] = 123.0
                        else:
                            value["frozen"]["repeat"]["gains"][2] = "0" * 64
                        target.write_text(json.dumps(value, sort_keys=True))
                return index

            try:
                with patch.object(reward_evidence, "list_reward_evidence", replace_after_validated_index):
                    try:
                        runner.qualify(root, pair)
                    except (ValueError, OSError, KeyError) as error:
                        actual, reason = "rejected", str(error)
                    else:
                        actual, reason = (
                            "ACCEPTED",
                            "Validated prior bytes were replaced before qualification binding.",
                        )
                assert invoked
                results.append(
                    dict(
                        case="post-validation-replacement-" + filename,
                        expected="rejected",
                        actual=actual,
                        reason=reason,
                    )
                )
            finally:
                target.write_bytes(original)
        reset()
        final = runner.qualify(root, pair)
        results.append(
            dict(
                case="restored-positive-control",
                expected="accepted",
                actual="accepted",
                bindings=len(final["bindings"]),
            )
        )
        return dict(
            synthetic_only=True,
            native_calls=0,
            temporary_artifacts_removed_after_return=True,
            immutable_input_count=len(receipt["immutable_inputs"]),
            results=results,
            all_expectations_met=all(x["expected"] == x["actual"] for x in results),
        )


if __name__ == "__main__":
    print(json.dumps(run(Path.cwd()), indent=2))
