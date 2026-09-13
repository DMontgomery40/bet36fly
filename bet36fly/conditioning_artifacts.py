"""Bounded numeric artifacts for conditioning; no engine import or execution."""

from __future__ import annotations

import hashlib
import io
import json
import math
from pathlib import Path
import re
import zipfile

import numpy as np


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def binding(path):
    path = Path(path).absolute()
    if path != path.resolve() or not path.is_file():
        raise ValueError("Input must be a regular file without symlinks.")
    with path.open("rb") as stream:
        sha = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha}


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key.")
            result[key] = value
        return result

    value = json.loads(
        data,
        object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON.")),
    )
    canonical(value)
    return value


def _meta(meta, limit):
    if (
        not isinstance(meta, dict)
        or set(meta) != {"path", "bytes", "sha256"}
        or type(meta["bytes"]) is not int
        or not 0 <= meta["bytes"] <= limit
        or not isinstance(meta["path"], str)
        or not isinstance(meta["sha256"], str)
        or not re.fullmatch("[0-9a-f]{64}", meta["sha256"])
    ):
        raise ValueError("Malformed/oversized file binding.")


def read_bound(meta):
    _meta(meta, 128 * 1024 * 1024)
    path = Path(meta["path"])
    if path != path.resolve() or not path.is_file():
        raise ValueError("Bound input missing or symlinked.")
    if path.stat().st_size != meta["bytes"]:
        raise ValueError("File size differs before read.")
    data = path.read_bytes()
    if len(data) != meta["bytes"] or digest(data) != meta["sha256"]:
        raise ValueError("Bound bytes changed.")
    return data


def verify_bindings(bindings):
    for meta in bindings:
        if binding(meta["path"]) != meta:
            raise ValueError("Input/source identity changed.")


def safe_npz(data):
    limit = 128 * 1024 * 1024
    if len(data) > limit:
        raise ValueError("Archive is too large.")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        members = z.infolist()
        names = [m.filename for m in members]
        if (
            len(names) > 64
            or len(names) != len(set(names))
            or any(not re.fullmatch(r"[a-zA-Z0-9_.-]+\.npy", x) for x in names)
            or sum(x.file_size for x in members) > limit
        ):
            raise ValueError("Unsafe NPZ inventory.")
        total = 0
        for member in members:
            with z.open(member) as stream:
                version = np.lib.format.read_magic(stream)
                if version == (1, 0):
                    shape, _, dtype = np.lib.format.read_array_header_1_0(stream)
                elif version == (2, 0):
                    shape, _, dtype = np.lib.format.read_array_header_2_0(stream)
                else:
                    raise ValueError("Unsupported NPY format.")
                if (
                    dtype.kind not in "fiub"
                    or dtype.hasobject
                    or any(type(n) is not int or n < 0 for n in shape)
                ):
                    raise ValueError("Unsafe NPY dtype/shape.")
                size = math.prod(shape) * dtype.itemsize
                total += size
                if total > limit or stream.tell() + size != member.file_size:
                    raise ValueError("NPY allocation disagrees with bounded payload.")
    with np.load(io.BytesIO(data), allow_pickle=False) as z:
        arrays = {k: z[k] for k in z.files}
    if any(not np.isfinite(a).all() for a in arrays.values()):
        raise ValueError("Nonfinite numeric artifact.")
    return arrays


def encode_result(result):
    arrays = {}

    def visit(value, path):
        if isinstance(value, np.ndarray):
            arrays[path] = value
            return {"array": path}
        if isinstance(value, dict):
            return {k: visit(v, f"{path}.{k}" if path else k) for k, v in value.items()}
        if isinstance(value, np.generic):
            return value.item()
        return value

    metadata = visit(result, "")
    stream = io.BytesIO()
    np.savez_compressed(stream, **arrays)
    return stream.getvalue(), canonical(metadata)


def decode_result(data, metadata):
    arrays = safe_npz(data)
    used = set()

    def visit(value):
        if isinstance(value, dict) and set(value) == {"array"}:
            name = value["array"]
            if name in used or name not in arrays:
                raise ValueError("Duplicate or missing numeric array.")
            used.add(name)
            return arrays[name]
        if isinstance(value, dict):
            return {k: visit(v) for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v) for v in value]
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("Nonfinite metadata.")
        return value

    result = visit(strict_json(metadata))
    if used != set(arrays):
        raise ValueError("Unreferenced numeric arrays.")
    return result


def write_exclusive(path, data):
    path = Path(path)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        import os

        os.fsync(stream.fileno())
    return {"path": path.name, "bytes": len(data), "sha256": digest(data)}


def read_artifact(directory, meta):
    _meta(meta, 128 * 1024 * 1024)
    name = meta["path"]
    if not isinstance(name, str) or not re.fullmatch(r"[a-zA-Z0-9_.-]+", name) or name in (".", ".."):
        raise ValueError("Invalid artifact path.")
    path = Path(directory) / name
    if path != path.resolve() or not path.is_file():
        raise ValueError("Artifact missing or symlinked.")
    if path.stat().st_size != meta["bytes"]:
        raise ValueError("File size differs before read.")
    data = path.read_bytes()
    if len(data) != meta["bytes"] or digest(data) != meta["sha256"]:
        raise ValueError("Artifact hash mismatch.")
    return data
