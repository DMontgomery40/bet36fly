"""Cell-specific sign interventions preserve all unrelated anatomy and weights."""
import numpy as np
import pandas as pd
import pytest

from bet36fly.sensory_diagnostic import dpm_weights


@pytest.mark.parametrize('mode', ['zero', 'inhibitory'])
def test_dpm_source_override_preserves_other_edges_and_source_arrays(mode):
    nodes = pd.DataFrame({'bodyId': [1, 11734, 12569, 20000], 'type': ['KC', 'DPM', 'DPM', 'MN9']})
    ptr = np.array([0, 2, 4, 6, 7])
    weights = np.array([1., -2., 3., 4., 5., 6., -7.], np.float32)
    before = weights.copy()
    result = dpm_weights(nodes, ptr, weights, mode)
    assert np.array_equal(weights, before)
    assert np.array_equal(result[[0, 1, 6]], weights[[0, 1, 6]])
    assert np.array_equal(result[2:6], np.zeros(4) if mode == 'zero' else -weights[2:6])


@pytest.mark.parametrize('ids,types,mode', [
    ([1, 11734], ['KC', 'DPM'], 'zero'),
    ([11734, 12569], ['KC', 'DPM'], 'zero'),
    ([11734, 11734], ['DPM', 'DPM'], 'zero'),
    ([11734, 12569], ['DPM', 'DPM'], 'positive'),
])
def test_override_fails_closed(ids, types, mode):
    with pytest.raises(ValueError):
        dpm_weights(pd.DataFrame({'bodyId': ids, 'type': types}), np.array([0, 1, 2]),
                    np.ones(2, np.float32), mode)


def test_calibration_gates_require_every_seed_and_recovery():
    from scripts.run_sensory_calibration import gates
    rows = [dict(condition=k, seed=s, MN9_hz_mean=3. if k == 'sweet' else 0.,
                 total_spikes=0 if k == 'null' else 100, stimulus_spikes=100,
                 tail_spikes=0, MN9_tail_spikes=0, generator_numerical_passed=True)
            for k in ['null', 'water', 'sweet', 'bitter', 'mixed'] for s in [2, 3]]
    assert gates(rows, [2, 3])['passed']
    assert not gates(rows[:-1], [2, 3])['passed']
    for field, value in [('tail_spikes', 2), ('MN9_tail_spikes', 1), ('generator_numerical_passed', False)]:
        altered = [r.copy() for r in rows]
        altered[4][field] = value
        assert not gates(altered, [2, 3])['passed']
    for condition, value in [('bitter', 2), ('sweet', 1), ('mixed', 3)]:
        altered = [r.copy() for r in rows]
        next(r for r in altered if r['condition'] == condition)['MN9_hz_mean'] = value
        assert not gates(altered, [2, 3])['passed']


@pytest.mark.parametrize('mode,expected', [('modulator', [0, 1, 2, 0]), ('ALLN', [0, 0, 2, 3]), ('union', [0, 0, 2, 0])])
def test_class_lesions_are_source_only_and_preserve_original(mode, expected):
    from bet36fly.sensory_lesion import lesion_weights
    nodes = pd.DataFrame({'class': [None, 'ALLN', 'KC', None],
                          'transmitter': ['dopamine', 'acetylcholine', 'acetylcholine, dopamine', 'serotonin']})
    weights = np.arange(4, dtype=np.float32)
    result, mask = lesion_weights(nodes, np.arange(5), weights, mode)
    assert np.array_equal(result, expected)
    assert np.array_equal(weights, np.arange(4))
    assert not mask[2]  # Co-transmitted ACh is not a pure modulator.
