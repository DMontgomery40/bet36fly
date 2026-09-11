import numpy as np
import pytest

from bet36fly.reward_encoder import ENCODER_NAME, glomerular_map, glomerular_rates, scale_inputs_onto, scale_outputs_from


def annotated_ports():
    # Eight ports: types A..D cholinergic with KC contacts, E gabaergic, F cholinergic without KC contacts.
    types = np.array(['A', 'A', 'B', 'C', 'D', 'E', 'F', 'B'])
    transmitters = np.array(['acetylcholine'] * 5 + ['gaba', 'acetylcholine', 'acetylcholine'])
    contacts = np.array([120, 80, 300, 150, 500, 900, 0, 50])
    return types, transmitters, contacts


def test_map_groups_sister_ports_by_glomerulus_and_excludes_inhibitory_or_unconnected_ports():
    types, transmitters, contacts = annotated_ports()
    mapping = glomerular_map(types, transmitters, contacts, n_features=2, min_kc_contacts=100)
    # A, B, C, D qualify (E is gabaergic, F has no KC contacts); 4 glomeruli -> 2 per feature.
    assert mapping['summary']['glomeruli'] == 4 and mapping['summary']['ports_driven'] == 6
    assert mapping['summary']['centers_per_feature'] == 2
    feature, center = mapping['port_feature'], mapping['port_center']
    assert feature[5] == -1 and feature[6] == -1
    assert feature[0] == feature[1] and center[0] == center[1]
    assert feature[2] == feature[7] and center[2] == center[7]
    assert sorted(feature[feature >= 0].tolist()) == [0, 0, 0, 1, 1, 1]
    per_feature = {f: sorted(set(center[feature == f].tolist())) for f in (0, 1)}
    assert all(len(v) == 2 and v[0] < 0 < v[1] for v in per_feature.values())
    assert mapping['summary']['features'][0]['glomeruli'][0]['type'] == 'A'


def test_map_is_deterministic_and_drops_weakest_glomeruli_when_they_do_not_divide_evenly():
    types, transmitters, contacts = annotated_ports()
    a = glomerular_map(types, transmitters, contacts, n_features=3, min_kc_contacts=100)
    b = glomerular_map(types, transmitters, contacts, n_features=3, min_kc_contacts=100)
    np.testing.assert_array_equal(a['port_feature'], b['port_feature'])
    # Four glomeruli for three features keeps three; C (150 contacts) is the weakest and is dropped.
    assert a['summary']['glomeruli'] == 3 and a['port_feature'][3] == -1 and a['port_feature'][0] >= 0
    assert a['summary']['dropped_glomeruli'] == ['C']


@pytest.mark.parametrize('bad', ['few', 'shape', 'features'])
def test_map_rejects_unusable_catalogs(bad):
    types, transmitters, contacts = annotated_ports()
    if bad == 'few':
        with pytest.raises(ValueError):
            glomerular_map(types, transmitters, contacts, n_features=5, min_kc_contacts=100)
    if bad == 'shape':
        with pytest.raises(ValueError):
            glomerular_map(types[:-1], transmitters, contacts, n_features=2, min_kc_contacts=100)
    if bad == 'features':
        with pytest.raises(ValueError):
            glomerular_map(types, transmitters, contacts, n_features=0, min_kc_contacts=100)


def test_rates_select_game_specific_ports_with_gaussian_tuning():
    types, transmitters, contacts = annotated_ports()
    mapping = glomerular_map(types, transmitters, contacts, n_features=2, min_kc_contacts=100)
    low = glomerular_rates(np.array([-1.5, -1.5]), mapping, peak_hz=100., width=.5)
    high = glomerular_rates(np.array([1.5, 1.5]), mapping, peak_hz=100., width=.5)
    assert low.dtype == np.float32 and low.shape == (8,) and high.shape == (8,)
    assert low.max() == pytest.approx(100.) and high.max() == pytest.approx(100.)
    assert not set(np.flatnonzero(low)) & set(np.flatnonzero(high))
    assert low[5] == 0 and low[6] == 0 and high[5] == 0 and high[6] == 0
    mid = glomerular_rates(np.array([0., 0.]), mapping, peak_hz=100., width=1.)
    # Halfway between two centers both fire at the same reduced rate.
    driven = mid[mapping['port_feature'] >= 0]
    assert 0 < driven.min() and driven.max() < 100 and np.allclose(driven, driven[0])
    far = glomerular_rates(np.array([8., 8.]), mapping, peak_hz=100., width=.5)
    assert far.max() == 0


@pytest.mark.parametrize('features,peak,width', [([0.], 100., .5), ([np.nan, 0.], 100., .5),
                                                 ([0., 0.], 0., .5), ([0., 0.], 100., 0.),
                                                 ([0., 0.], float('inf'), .5)])
def test_rates_reject_invalid_inputs(features, peak, width):
    types, transmitters, contacts = annotated_ports()
    mapping = glomerular_map(types, transmitters, contacts, n_features=2, min_kc_contacts=100)
    with pytest.raises(ValueError):
        glomerular_rates(np.array(features), mapping, peak_hz=peak, width=width)


def test_scale_inputs_onto_targets_changes_only_edges_ending_at_targets():
    ptr = np.array([0, 2, 4, 5])
    post = np.array([1, 2, 0, 2, 1])
    weights = np.array([1., 2., 3., 4., 5.], np.float32)
    scaled = scale_inputs_onto(weights, ptr, post, np.array([2]), 0.25)
    np.testing.assert_allclose(scaled, [1., .5, 3., 1., 5.])
    np.testing.assert_allclose(weights, [1., 2., 3., 4., 5.])
    np.testing.assert_allclose(scale_inputs_onto(weights, ptr, post, np.array([2]), 0.), [1., 0., 3., 0., 5.])
    with pytest.raises(ValueError):
        scale_inputs_onto(weights, ptr, post, np.array([2]), -1.)


def test_encoder_name_is_versioned():
    assert ENCODER_NAME == 'glomerular-tuning-v1'


def test_scale_outputs_from_sources_changes_only_edges_leaving_sources():
    ptr = np.array([0, 2, 4, 5])
    weights = np.array([1., 2., 3., 4., 5.], np.float32)
    np.testing.assert_allclose(scale_outputs_from(weights, ptr, np.array([1]), .5), [1., 2., 1.5, 2., 5.])
    np.testing.assert_allclose(scale_outputs_from(weights, ptr, np.array([0, 2]), 0.), [0., 0., 3., 4., 0.])
    np.testing.assert_allclose(weights, [1., 2., 3., 4., 5.])
    with pytest.raises(ValueError):
        scale_outputs_from(weights, ptr, np.array([3]), 1.)
