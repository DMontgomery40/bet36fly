"""Probe retained pure draft against frozen contracts; never invokes an engine."""
from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DRAFT = ROOT / 'output/collaboration/reward-mechanism-repair/task3-draft/conditioning.py'
spec = importlib.util.spec_from_file_location('retained_conditioning_draft', DRAFT)
draft = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = draft
spec.loader.exec_module(draft)


def main():
    plan = draft.build_call_plan()
    baseline = draft.validate_call_plan(plan)
    mutations = {
        'remove_all_teaching': lambda row: replace(row, teaching=()),
        'alter_all_probe_seeds': lambda row: replace(row, seed=row.seed + 123)
        if 'probe' in row.kind else row,
        'enable_frozen_plasticity': lambda row: replace(row, plasticity=True)
        if row.arm == 'frozen' or row.branch == 'frozen-retention' else row,
        'wrong_reversal_cue_window': lambda row: replace(row, cue_window=(0, 300))
        if row.stage == 'reversal' else row,
        'wrong_replay_parent': lambda row: replace(row, replay_of=plan[0].id)
        if row.replay_of is not None else row,
    }
    accepted = {}
    for name, mutation in mutations.items():
        changed = [mutation(row) for row in plan]
        assert changed != plan
        try:
            draft.validate_call_plan(changed)
        except (ValueError, TypeError, KeyError):
            accepted[name] = False
        else:
            accepted[name] = True

    unit = {'responses': np.full((4, 2, 2), 20.0),
            'gains': np.ones(4, np.float32), 'bound_hits': 0}
    partitions = {'passed': True, 'channels': {
        'home': {'first': np.array([0]), 'second': np.array([1])},
        'away': {'first': np.array([2]), 'second': np.array([3])},
    }}
    endpoints = {str(panel): {arm: copy.deepcopy(unit) for arm in draft.ACQUISITION_ARMS}
                 for panel in (0, 1_000_000)}
    for arms in endpoints.values():
        arms['paired']['responses'][:, 0, 0] -= 3
        arms['paired']['responses'][:, 1, 1] -= 3
        arms['paired']['gains'][[0, 3]] = 0.8
    baseline_acquisition = draft.evaluate_acquisition(unit, endpoints, partitions)['all_passed']
    assert baseline_acquisition

    damaged = copy.deepcopy(endpoints)
    for arms in damaged.values():
        arms['frozen']['gains'][:] += 0.01
    frozen_changed_passes = draft.evaluate_acquisition(unit, damaged, partitions)['all_passed']

    damaged = copy.deepcopy(endpoints)
    for arms in damaged.values():
        arms['paired']['gains'][[0, 3]] = 0.2  # Outside the unchanged [0.5, 1.5] bounds.
    outside_bounds_passes = draft.evaluate_acquisition(unit, damaged, partitions)['all_passed']

    empty_replay_passes = draft.compare_numeric_results({}, {})['passed']
    result = {
        'scope': 'Pure retained-draft review; no conditioning or native calls; no production import/edit.',
        'draft_sha256': hashlib.sha256(DRAFT.read_bytes()).hexdigest(),
        'baseline_plan': baseline, 'valid_synthetic_acquisition_passes': baseline_acquisition,
        'invalid_call_plans_accepted': accepted,
        'invalid_acquisition_accepted': {'frozen_gain_change': frozen_changed_passes,
                                        'outside_frozen_gain_bounds': outside_bounds_passes},
        'empty_numeric_replay_accepted': empty_replay_passes,
    }
    output = Path(__file__).with_name('conditioning-draft-review.json')
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
