"""Read-only contact map for the proposed slow KC branch, never fast weights."""

import numpy as np
from scipy.sparse import csr_matrix


def _integers(value, *, integral_float=False):
    raw = np.asarray(value)
    if integral_float and raw.dtype.kind == 'f':
        if (not np.isfinite(raw).all() or np.any(raw < 0) or np.any(raw >= 2**63)
                or np.any(raw != np.floor(raw))):
            raise ValueError('Floating contact storage must hold exact nonnegative int64 counts')
        raw = raw.astype(np.int64)
    if raw.ndim != 1 or (raw.size and raw.dtype.kind not in 'iu'):
        raise ValueError('Anatomical arrays must be one-dimensional integers')
    if raw.size and (np.any(raw < 0) or np.any(raw > np.iinfo(np.int64).max)):
        raise ValueError('Anatomical arrays must contain nonnegative int64 values')
    return raw.astype(np.int64)


def lateral_contacts(ptr, post, contacts, kc):
    """Return recipient-row normalized KC contacts and an anatomical audit.

    Source CSR rows are presynaptic global neurons. The returned CSR instead
    uses the caller's KC order in both dimensions, recipients first. Duplicate
    source pairs are summed; zero-count entries and self-pairs are excluded.
    """
    ptr, post, kc = [_integers(x) for x in (ptr, post, kc)]
    contacts = _integers(contacts, integral_float=True)
    n = len(ptr)-1
    if (n < 1 or ptr[0] != 0 or ptr[-1] != len(post) or np.any(np.diff(ptr) < 0)
            or len(contacts) != len(post) or np.any(post >= n) or not len(kc)
            or np.any(kc >= n) or len(np.unique(kc)) != len(kc)):
        raise ValueError('Malformed CSR graph or KC correspondence')
    # Float64 normalization is exact in its integer sums for the retained graph.
    # Reject larger unrepresentable totals rather than silently losing contacts.
    total = sum(int(x) for x in contacts)
    if total > 2**53:
        raise ValueError('Contact total exceeds exact float64 integer range')
    lookup = np.full(n, -1, np.int64)
    lookup[kc] = np.arange(len(kc))
    rows, columns, values = [], [], []
    self_pairs = self_contacts = 0
    for column, pre in enumerate(kc):
        lo, hi = ptr[pre:pre+2]
        recipients, mass = lookup[post[lo:hi]], contacts[lo:hi]
        own = (recipients == column) & (mass > 0)
        self_pairs += int(np.count_nonzero(own))
        self_contacts += sum(int(x) for x in mass[own])
        selected = (recipients >= 0) & (recipients != column) & (mass > 0)
        rows.extend(recipients[selected].tolist())
        columns.extend([column]*int(np.count_nonzero(selected)))
        values.extend(mass[selected].tolist())
    matrix = csr_matrix((np.array(values, np.float64), (rows, columns)), shape=(len(kc), len(kc)))
    matrix.sum_duplicates()
    incoming = np.asarray(matrix.sum(1)).ravel()
    audit = dict(kc=len(kc), directed_pairs=int(matrix.nnz), contacts=sum(values),
                 excluded_self_pairs=self_pairs, excluded_self_contacts=self_contacts,
                 empty_recipient_rows=int(np.count_nonzero(incoming == 0)),
                 orientation='recipient rows, presynaptic columns',
                 normalization='incoming contact sum; empty rows remain zero')
    matrix.data /= np.repeat(incoming, np.diff(matrix.indptr))
    return matrix, audit
