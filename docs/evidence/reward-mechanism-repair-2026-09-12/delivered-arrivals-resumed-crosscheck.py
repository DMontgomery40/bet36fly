"""Independent real-raster queue check of every saved target/family/step."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow.feather as feather

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent
RESULT = HERE / "delivered-arrivals-resumed-result.json"
CAPTURE = HERE / "onset-history-captures/onset-history-capture-4343c21535c43f42"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    output = HERE / "delivered-arrivals-resumed-crosscheck.json"
    if output.exists():
        raise FileExistsError(output)
    result = json.loads(RESULT.read_text())
    with np.load(ROOT / "docs/evidence/reward-mechanism-repair-2026-09-12/onset-capture-preregistration.samples.npz") as archive:
        sample = archive["sample"]
        kc = archive["kc_indices"]
    ids, post, ptr, contacts = [np.load(ROOT / f"data/brain/{name}.npy", mmap_mode="r")
                                for name in ("ids", "post", "indptr", "counts")]
    types = feather.read_table(ROOT / "data/brain/nodes.feather").to_pandas().set_index("bodyId")["type"]
    families = {}
    for cell in kc:
        label = str(types.loc[ids[cell]])
        families[cell] = 0 if label.startswith("KCg") else 1 if label.startswith("KCa'b'") else 2 if label.startswith("KCab") else 3
    column = {int(cell): position for position, cell in enumerate(sample)}
    checks = []
    with np.load(HERE / "delivered-arrivals-resumed-result.npz") as derived:
        for trial in result["trials"]:
            index, body = trial["fine_index"], trial["target_body_id"]
            target = np.flatnonzero(ids == body).item()
            edges = np.flatnonzero(post == target)
            presynaptic = np.searchsorted(ptr[1:], edges, side="right")
            incoming = {int(pre): (families[pre], float(np.float32(contacts[edge]) * np.float32(.1375)))
                        for edge, pre in zip(edges, presynaptic) if pre in families}
            with np.load(CAPTURE / f"fine_{index:02d}.npz") as actual:
                raster = actual["trace"]
            counts = {name: np.zeros((2000, 4), dtype=np.int64) for name in ("accepted", "refractory_discarded")}
            amounts = {name: np.zeros((2000, 4)) for name in counts}
            ready = 0
            same_step = 0
            for time in range(2000):
                spike = bool(raster[time, column[target]])
                if time >= 9:
                    category = "accepted" if time >= ready else "refractory_discarded"
                    for pre in sample[np.flatnonzero(raster[time - 9])]:
                        if pre in incoming:
                            family, weight = incoming[pre]
                            counts[category][time, family] += 1
                            amounts[category][time, family] += weight
                            same_step += int(spike and category == "accepted")
                if spike:
                    assert time >= ready
                    ready = time + 11
            for category in counts:
                np.testing.assert_array_equal(counts[category], derived[f"{index:02d}_{body}_{category}_counts"])
                np.testing.assert_array_equal(amounts[category], derived[f"{index:02d}_{body}_{category}_increment"])
            assert same_step == trial["totals"]["same_step"]["edge_events"]
            checks.append(dict(fine_index=index, target_body_id=body, every_step_family_count_and_increment_equal=True,
                               same_step_events=same_step))
    with output.open("x") as stream:
        json.dump(dict(result_sha256=sha(RESULT), script_sha256=sha(Path(__file__)),
                       checked_target_trials=len(checks), passed=True, checks=checks,
                       scope="Independent time-ordered actual-raster queue; no native calls or threshold evaluation"), stream, indent=2)
        stream.write("\n")
    print(f"All {len(checks)} target trials match independently at every .2ms step and KC family.")


if __name__ == "__main__":
    main()
