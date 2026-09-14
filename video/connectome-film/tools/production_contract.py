"""Keep Claude's narration approval and accepted artwork bound to the render."""
import hashlib
import re
from pathlib import Path


def narration_digest(scenes):
    text = ' '.join(' '.join(s['narration'].split()) for s in scenes)
    return hashlib.sha256(text.encode()).hexdigest()


def validate_plan(plan, approval, root: Path, accepted_images):
    assert approval['verdict'] == 'APPROVE', 'Narration needs explicit Claude approval'
    assert approval['reviewer'].startswith('claude'), 'Claude review is required'
    assert approval['narration_sha256'] == narration_digest(plan['scenes']), 'Approved narration changed'
    assert plan['meta']['voice'] == 'SAz9YHcvj6GT2YYXdXww', 'Use the selected calm American voice'
    assert plan['meta']['audio_speed'] <= 1, 'Do not rush the narration'
    assert [s['id'] for s in plan['scenes']] == list(range(len(plan['scenes'])))
    text = ' '.join(s['narration'] for s in plan['scenes'])
    assert 'Google Research' in text
    assert 'bet three sixty fly' in text
    assert not re.search(r'bet36fly', text, re.I), 'TTS needs the spelled-out pronunciation'
    for scene in plan['scenes']:
        assert not scene.get('video_source_path'), 'This film uses the existing stills'
        source = scene.get('image_source_path')
        assert source in accepted_images, 'Use an accepted existing image; no generation fallback'
        assert hashlib.sha256((root / source).read_bytes()).hexdigest() == accepted_images[source]
