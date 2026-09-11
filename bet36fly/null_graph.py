"""Serial, array-based directed double-edge swaps for a synthetic control graph.

Edges retain their source and contact count. Only destinations move between
equal-count/sign/source-role/destination-role strata. Original self-edges stay
fixed. All proposals in a sweep are checked together against the existing graph
and against one another, a conservative form of disjoint-pair batch swapping.
"""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
from pathlib import Path
import shutil
import tempfile
import time

import numpy as np
from scipy.sparse import csr_matrix, load_npz, save_npz

from .connectome import digest
from .grouped_learning import build_gain_groups

_CHUNK = 1_000_000
_ARRAY_FILES = ('ids.npy', 'indptr.npy', 'post.npy', 'counts.npy', 'signs.npy', 'kc.npy',
                'mbon.npy', 'sensory.npy', 'in_degree.npy', 'plastic.npz', 'nodes.feather')


def graph_array_hashes(path):
    """Hash all persisted arrays and the annotation table, including derived data."""
    path = Path(path)
    return {name: digest(path / name) for name in _ARRAY_FILES}


@contextmanager
def _serial_generation():
    # The lock spans processes and output directories, so two experiment seeds
    # cannot concurrently allocate full-graph sorting scratch space.
    lock_path = Path(tempfile.gettempdir()) / 'bet36fly-null-graph.lock'
    with lock_path.open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _contains(sorted_keys, values):
    if not len(sorted_keys):
        return np.zeros(values.shape, bool)
    positions = np.searchsorted(sorted_keys, values)
    present = positions < len(sorted_keys)
    np.minimum(positions, len(sorted_keys) - 1, out=positions)
    return present & (sorted_keys[positions] == values)


def _pair_keys(pre, post):
    return (np.asarray(pre, dtype=np.uint64) << np.uint64(32)) | np.asarray(post, dtype=np.uint64)


def _role_codes(nodes, ids, kc, mbon):
    if nodes.bodyId.duplicated().any():
        raise ValueError('Duplicate annotation body IDs.')
    aligned = nodes.set_index('bodyId').reindex(ids)
    source = np.zeros(len(ids), np.uint16)
    target = np.zeros(len(ids), np.uint16)
    label_sets = []
    for selected, roles, other in ((kc, source, 'non-KC'), (mbon, target, 'non-MBON')):
        labels = aligned['type'].iloc[selected]
        if labels.isna().any() or labels.astype(str).str.strip().eq('').any():
            raise ValueError('Null graph needs exact KC and MBON type labels.')
        keys = sorted(set(labels.astype(str)))
        mapping = {label: index + 1 for index, label in enumerate(keys)}
        roles[selected] = labels.astype(str).map(mapping).to_numpy(np.uint16)
        label_sets.append([other, *keys])
    return source, target, label_sets


def _strata(counts, pre, post, signs, source_role, target_role):
    source_bits = max(1, int(source_role.max()).bit_length())
    target_bits = max(1, int(target_role.max()).bit_length())
    shift = source_bits + target_bits + 1
    if (not np.isfinite(counts).all() or np.any(counts <= 0) or np.any(counts != np.floor(counts))
            or float(counts.max(initial=0)) >= 2 ** (64 - shift)
            or not np.isin(signs, [-1, 1]).all()):
        raise ValueError('Expected positive integral contact counts and presynaptic signs of -1 or +1.')
    codes = np.empty(len(post), np.uint64)
    for start in range(0, len(post), _CHUNK):
        block = slice(start, start + _CHUNK)
        codes[block] = (counts[block].astype(np.uint64) << np.uint64(shift)
                        | ((signs[pre[block]] > 0).astype(np.uint64)
                           << np.uint64(source_bits + target_bits))
                        | (source_role[pre[block]].astype(np.uint64) << np.uint64(target_bits))
                        | target_role[post[block]].astype(np.uint64))
    return codes, {'source_bits': source_bits, 'target_bits': target_bits, 'count_shift': shift}


def _node_totals(pre, post, counts, signs, n):
    totals = {name: np.zeros(n, np.float64) for name in
              ('in_degree', 'out_degree', 'incoming_contacts', 'outgoing_contacts',
               'incoming_signed_weight', 'outgoing_signed_weight')}
    for start in range(0, len(post), _CHUNK):
        block = slice(start, start + _CHUNK)
        source, target = pre[block], post[block]
        contact = counts[block].astype(np.float64)
        signed = contact * signs[source]
        for name, index, weights in [('in_degree', target, None), ('out_degree', source, None),
                                     ('incoming_contacts', target, contact),
                                     ('outgoing_contacts', source, contact),
                                     ('incoming_signed_weight', target, signed),
                                     ('outgoing_signed_weight', source, signed)]:
            totals[name] += np.bincount(index, weights=weights, minlength=n)
    return totals


def _rewire(pre, post, counts, signs, source_role, target_role, *, seed, sweeps):
    """Rewire one mutable destination array; scratch is NumPy, never edge objects."""
    original_self = pre == post
    codes, encoding = _strata(counts, pre, post, signs, source_role, target_role)
    order = np.argsort(codes, kind='stable').astype(np.int32)
    order = order[~original_self[order]]
    ordered_codes = codes[order]
    del codes
    boundaries = np.r_[0, np.flatnonzero(ordered_codes[1:] != ordered_codes[:-1]) + 1, len(order)]
    if len(order):
        stratum_keys = ordered_codes[boundaries[:-1]].copy()
    else:
        boundaries, stratum_keys = np.array([0], np.int64), np.array([], np.uint64)
    del ordered_codes
    sizes = np.diff(boundaries)
    pair_count = int((sizes // 2).sum())
    pairs = np.empty((pair_count, 2), np.int32)
    proposals = np.empty((2, pair_count), np.uint64)
    scratch_keys = np.empty(len(post), np.uint64)
    accepted_by_stratum = np.zeros(len(sizes), np.int64)
    generator = np.random.default_rng(seed)
    sweep_reports = []
    for sweep in range(sweeps):
        offset = 0
        for lo, hi in zip(boundaries[:-1], boundaries[1:]):
            size = int((hi - lo) // 2)
            if size:
                generator.shuffle(order[lo:hi])
                pairs[offset:offset + size] = order[lo:lo + 2 * size].reshape(size, 2)
                offset += size
        eligible = np.ones(pair_count, bool)
        for start in range(0, pair_count, _CHUNK):
            block = slice(start, start + _CHUNK)
            first, second = pairs[block, 0], pairs[block, 1]
            a, b, c, d = pre[first], post[first], pre[second], post[second]
            proposals[0, block] = _pair_keys(a, d)
            proposals[1, block] = _pair_keys(c, b)
            eligible[block] = (a != d) & (c != b) & (a != c) & (b != d)
        # Sort proposal keys in reusable scratch; reject both pairs whenever
        # they propose an identical edge, even across distant strata/batches.
        proposal_keys = scratch_keys[:2 * pair_count]
        proposal_keys[:] = proposals.ravel()
        proposal_keys.sort()
        duplicates = proposal_keys[1:][proposal_keys[1:] == proposal_keys[:-1]].copy()
        for start in range(0, len(post), _CHUNK):
            block = slice(start, start + _CHUNK)
            scratch_keys[block] = _pair_keys(pre[block], post[block])
        scratch_keys.sort()
        for start in range(0, pair_count, _CHUNK):
            block = slice(start, start + _CHUNK)
            for side in (0, 1):
                eligible[block] &= ~_contains(scratch_keys, proposals[side, block])
                eligible[block] &= ~_contains(duplicates, proposals[side, block])
        del duplicates
        accepted = int(eligible.sum())
        for start in range(0, pair_count, _CHUNK):
            block = slice(start, start + _CHUNK)
            accepted_pairs = pairs[block][eligible[block]]
            first, second = accepted_pairs[:, 0], accepted_pairs[:, 1]
            old_first = post[first].copy()
            post[first] = post[second]
            post[second] = old_first
        pair_boundaries = np.r_[0, np.cumsum(sizes // 2)]
        prefix = np.r_[0, np.cumsum(eligible, dtype=np.int64)]
        accepted_by_stratum += np.diff(prefix[pair_boundaries])
        sweep_reports.append({'sweep': sweep + 1, 'proposed_pairs': pair_count, 'accepted_swaps': accepted})
    return {'sweeps': sweep_reports, 'accepted_swaps': sum(s['accepted_swaps'] for s in sweep_reports),
            'stratum_keys': stratum_keys, 'stratum_sizes': sizes,
            'accepted_by_stratum': accepted_by_stratum, 'stratum_encoding': encoding,
            'original_self_edges': int(original_self.sum())}


def _assert_invariants(pre, original, derived, counts, signs, source_role, target_role, n):
    before = _node_totals(pre, original, counts, signs, n)
    after = _node_totals(pre, derived, counts, signs, n)
    checks = {name: bool(np.array_equal(before[name], after[name])) for name in before}
    checks['original_self_edges'] = bool(np.array_equal(pre == original, pre == derived)
                                        and np.array_equal(original[pre == original], derived[pre == original]))
    checks['destination_roles'] = bool(np.array_equal(target_role[original], target_role[derived]))
    # The edge arrays retain their sources, contact counts, signs and source
    # roles, so these invariants hold by attachment, not approximate statistics.
    checks.update(source_roles=True, contact_count_histogram=True, edge_count=True,
                  node_ids=True, presynaptic_signs=True)
    keys = _pair_keys(pre, derived)
    keys.sort()
    checks['no_duplicate_edges'] = bool(np.all(keys[1:] != keys[:-1]))
    del keys
    if not all(checks.values()):
        raise RuntimeError(f'Null graph invariant failure: {[key for key, value in checks.items() if not value]}')
    return checks, after['incoming_contacts']


def _write_graph(source, output, pre, post, counts, signs, ptr, kc, mbon, incoming):
    keys = _pair_keys(pre, post)
    order = np.argsort(keys, kind='stable')
    del keys
    # Sources never move, so their original CSR indptr is still exact. Restore
    # increasing destination order within each source without a dense adjacency.
    final_post = np.lib.format.open_memmap(output / 'post.npy', mode='w+', dtype=np.int32,
                                           shape=post.shape)
    final_counts = np.lib.format.open_memmap(output / 'counts.npy', mode='w+', dtype=np.float32,
                                             shape=counts.shape)
    for start in range(0, len(post), _CHUNK):
        block = slice(start, start + _CHUNK)
        final_post[block], final_counts[block] = post[order[block]], counts[order[block]]
    del order
    final_post.flush()
    final_counts.flush()
    for name in ('ids.npy', 'indptr.npy', 'signs.npy', 'kc.npy', 'mbon.npy', 'sensory.npy',
                 'nodes.feather', 'source-lock.json'):
        if (source / name).exists():
            shutil.copyfile(source / name, output / name)
    np.save(output / 'in_degree.npy', incoming.astype(np.float32))
    graph = csr_matrix((final_counts, final_post, ptr), shape=(len(ptr) - 1, len(ptr) - 1), copy=False)
    plastic = graph[kc][:, mbon].T.tocsr()
    plastic.data *= signs[kc][plastic.indices]
    save_npz(output / 'plastic.npz', plastic)
    return plastic


def make_null_graph(source_path, output_path, *, seed, sweeps=5):
    """Write a separately loadable synthetic graph and exact invariant report.

    Full arrays are hashed, existing complete outputs are validated before reuse,
    and publication of the directory happens only after invariant verification.
    """
    source, output = Path(source_path).resolve(), Path(output_path).resolve()
    if source == output or source in output.parents or output in source.parents:
        raise ValueError('Synthetic graph must be separate from the source graph directory.')
    if not isinstance(sweeps, int) or sweeps < 0:
        raise ValueError('Null sweeps must be a nonnegative integer.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with _serial_generation():
        source_hashes = graph_array_hashes(source)
        if (output / 'invariant-report.json').exists():
            report = json.loads((output / 'invariant-report.json').read_text())
            if (report['seed'] == seed and report['requested_sweeps'] == sweeps
                    and report['source_array_hashes'] == source_hashes
                    and report['graph_array_hashes'] == graph_array_hashes(output)):
                return report
            raise ValueError('Existing synthetic graph does not match its requested source/protocol/hashes.')
        if output.exists() and any(output.iterdir()):
            raise ValueError('Refusing to overwrite an incomplete or unrelated graph directory.')
        start = time.perf_counter()
        ids, ptr, original, counts, signs, kc, mbon = [
            np.load(source / (name + '.npy'), mmap_mode='r')
            for name in ('ids', 'indptr', 'post', 'counts', 'signs', 'kc', 'mbon')]
        if len(original) > np.iinfo(np.int32).max or len(ids) > np.iinfo(np.int32).max:
            raise ValueError('This implementation requires fewer than 2^31 nodes and edges.')
        if (len(ptr) != len(ids) + 1 or ptr[0] != 0 or ptr[-1] != len(original)
                or len(counts) != len(original) or np.any(np.diff(ptr) < 0)
                or np.any(original < 0) or np.any(original >= len(ids))):
            raise ValueError('Invalid source CSR graph.')
        pre = np.repeat(np.arange(len(ids), dtype=np.int32), np.diff(ptr))
        post = np.array(original, dtype=np.int32)
        import pyarrow.feather as feather
        nodes = feather.read_table(source / 'nodes.feather').to_pandas()
        source_role, target_role, role_labels = _role_codes(nodes, ids, kc, mbon)
        swaps = _rewire(pre, post, counts, signs, source_role, target_role, seed=seed, sweeps=sweeps)
        checks, incoming = _assert_invariants(pre, original, post, counts, signs,
                                              source_role, target_role, len(ids))
        changed = post != original
        plastic_edges = (source_role[pre] > 0) & (target_role[original] > 0)
        changed_edges, changed_plastic = int(changed.sum()), int(np.count_nonzero(changed & plastic_edges))
        # Per-edge pairing order persists across rewiring because its source,
        # contact count and destination role all stay attached to that edge.
        codes, _ = _strata(counts, pre, original, signs, source_role, target_role)
        changed_codes = np.unique(codes[changed])
        unchanged = ~_contains(changed_codes, swaps['stratum_keys'])
        unchanged_strata = [{'key': int(key), 'edges': int(size), 'accepted_swaps': int(accepted)}
                            for key, size, accepted in zip(swaps['stratum_keys'][unchanged],
                                                           swaps['stratum_sizes'][unchanged],
                                                           swaps['accepted_by_stratum'][unchanged])]
        del codes, changed, plastic_edges
        with tempfile.TemporaryDirectory(prefix='.' + output.name + '-', dir=output.parent) as temporary:
            staging = Path(temporary) / 'graph'
            staging.mkdir()
            plastic = _write_graph(source, staging, pre, post, counts, signs, ptr, kc, mbon, incoming)
            source_plastic = load_npz(source / 'plastic.npz').toarray()
            old_groups, old_keys = build_gain_groups(nodes, kc, mbon, source_plastic, graph_ids=ids)
            new_groups, new_keys = build_gain_groups(nodes, kc, mbon, plastic.toarray(), graph_ids=ids)
            checks['plastic_group_keys'] = old_keys == new_keys
            checks['plastic_group_sizes'] = bool(checks['plastic_group_keys'] and np.array_equal(
                np.bincount(old_groups[old_groups >= 0]), np.bincount(new_groups[new_groups >= 0])))
            if not checks['plastic_group_sizes']:
                raise RuntimeError('Null graph failed exact plastic type-pair group preservation.')
            derived_hashes = graph_array_hashes(staging)
            report = {'schema_version': 2, 'synthetic': True, 'seed': int(seed), 'requested_sweeps': sweeps,
                      'valid': changed_edges > 0 and changed_plastic > 0,
                      'invalid_reason': (None if changed_edges > 0 and changed_plastic > 0 else
                                         'No changed graph edges or no changed plastic edges.'),
                      'edge_count': len(post), 'plastic_edge_count': int(plastic.nnz),
                      'gain_group_count': len(new_keys), 'self_edges': swaps['original_self_edges'],
                      'accepted_swaps': swaps['accepted_swaps'], 'sweeps': swaps['sweeps'],
                      'changed_edges': changed_edges, 'changed_plastic_edges': changed_plastic,
                      'changed_edge_fraction': changed_edges / len(post) if len(post) else 0.,
                      'changed_plastic_edge_fraction': changed_plastic / plastic.nnz if plastic.nnz else 0.,
                      'unchanged_strata': unchanged_strata, 'unchanged_stratum_count': len(unchanged_strata),
                      'stratum_count': len(swaps['stratum_keys']), 'role_labels': role_labels,
                      'stratum_encoding': swaps['stratum_encoding'], 'invariants': checks,
                      'source_array_hashes': source_hashes, 'graph_array_hashes': derived_hashes,
                      'wall_seconds': time.perf_counter() - start}
            manifest = json.loads((source / 'manifest.json').read_text())
            manifest.update(synthetic=True, dataset='Synthetic directed-swap control derived from ' +
                            manifest.get('dataset', 'source graph'), graph_array_hashes=derived_hashes,
                            null_control={'seed': int(seed), 'sweeps': sweeps, 'valid': report['valid'],
                                          'source_array_hashes': source_hashes},
                            edge_policy='Synthetic degree/weight/type-stratified directed double-edge swaps.')
            for filename, value in [('manifest.json', manifest), ('invariant-report.json', report)]:
                (staging / filename).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
            if output.exists():
                output.rmdir()  # Only the verified empty destination may exist here.
            staging.replace(output)
        return report
