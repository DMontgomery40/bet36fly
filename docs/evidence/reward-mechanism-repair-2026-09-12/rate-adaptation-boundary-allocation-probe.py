"""Synthetic NPZ allocation-boundary probe; never invokes candidate or circuit."""
import hashlib
import importlib.util
import io
import json
import zipfile
from pathlib import Path

import numpy.lib.format as fmt

HERE = Path(__file__).parent


def probe():
    path = HERE/'rate_adaptation_shadow.py'
    spec = importlib.util.spec_from_file_location('boundary_review_candidate', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    header = io.BytesIO()
    fmt.write_array_header_1_0(header, {'descr': '<f8', 'fortran_order': False,
                                      'shape': (100_000_000,)})
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w') as zipped:
        zipped.writestr('oversized.npy', header.getvalue())
    context = fmt.read_array.__globals__
    real_numpy = context['numpy']
    allocations = []

    class AllocationRequested(Exception):
        pass

    class GuardedNumpy:
        def __getattr__(self, key):
            return getattr(real_numpy, key)

        def ndarray(self, shape, *args, **kwargs):
            allocations.append(int(shape))
            raise AllocationRequested('Intercepted before allocating requested array')

    context['numpy'] = GuardedNumpy()
    try:
        module.safe_npz(archive.getvalue())
        outcome = 'accepted-malformed-archive'
    except Exception as exc:
        outcome = f'{type(exc).__name__}: {exc}'
    finally:
        context['numpy'] = real_numpy
    return dict(calculator_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                npy_member_bytes=len(header.getvalue()), declared_elements=100_000_000,
                attempted_allocations=allocations, rejected_before_allocation=not allocations,
                outcome=outcome, candidate_evaluations=0, circuit_calls=0)


if __name__ == '__main__':
    print(json.dumps(probe(), indent=2))
