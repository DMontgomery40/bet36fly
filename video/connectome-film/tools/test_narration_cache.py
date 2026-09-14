"""A change to any audible voice setting must invalidate cached narration."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('narrate', Path(__file__).with_name('narrate.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize('field,value', [
    ('narration', 'A different sentence.'), ('voice', 'another-voice'),
    ('speed', 1.1), ('model', 'another-model'), ('stability', .4),
    ('similarity_boost', .5), ('style', .2), ('use_speaker_boost', True),
])
def test_every_speech_control_invalidates_cache(field, value):
    meta = {'voice_id': 'calm-voice', 'audio_speed': 1.03, 'elevenlabs_model_id': 'model',
            'voice_settings': {'stability': .7, 'similarity_boost': .75,
                               'style': 0.0, 'use_speaker_boost': False}}
    settings = module.speech_settings({'narration': 'bet three sixty fly.'}, meta)
    changed = {**settings, field: value}
    assert module.settings_digest(changed) != module.settings_digest(settings)


def test_unchanged_controls_reuse_cache_despite_dictionary_order():
    settings = {'voice': 'calm-voice', 'speed': 1.03, 'style': 0.0}
    assert module.settings_digest(settings) == module.settings_digest(dict(reversed(list(settings.items()))))
