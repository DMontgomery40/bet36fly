import hashlib
from copy import deepcopy

import pytest

from production_contract import narration_digest, validate_plan


@pytest.fixture
def valid(tmp_path):
    (tmp_path / 'image.png').write_bytes(b'accepted image')
    scene = {'id': 0, 'narration': 'Google Research supports bet three sixty fly.',
             'image_source_path': 'image.png'}
    plan = {'meta': {'voice': 'SAz9YHcvj6GT2YYXdXww', 'audio_speed': .92}, 'scenes': [scene]}
    approval = {'verdict': 'APPROVE', 'reviewer': 'claude-opus',
                'narration_sha256': narration_digest(plan['scenes'])}
    return plan, approval, tmp_path, {'image.png': hashlib.sha256(b'accepted image').hexdigest()}


def test_scene_splitting_preserves_approval():
    assert narration_digest([{'narration': 'One sentence. Another sentence.'}]) == narration_digest([
        {'narration': 'One sentence.\n'}, {'narration': 'Another sentence.'}])


def test_valid_plan(valid):
    validate_plan(*valid)


@pytest.mark.parametrize('change', ['text', 'voice', 'speed', 'video', 'image', 'missing_image',
                                   'image_bytes', 'rejected', 'wrong_reviewer', 'stale_approval'])
def test_rejects_changed_or_unapproved_delivery(valid, change):
    plan, approval, root, images = deepcopy(valid)
    scene = plan['scenes'][0]
    if change == 'text':
        scene['narration'] += ' An unreviewed claim.'
    elif change == 'voice':
        plan['meta']['voice'] = 'Adam'
    elif change == 'speed':
        plan['meta']['audio_speed'] = 1.2
    elif change == 'video':
        scene['video_source_path'] = 'rejected-animation.mp4'
    elif change == 'image':
        scene['image_source_path'] = 'replacement.png'
    elif change == 'missing_image':
        scene.pop('image_source_path')
    elif change == 'image_bytes':
        (root / 'image.png').write_bytes(b'changed image')
    elif change == 'rejected':
        approval['verdict'] = 'REJECT'
    elif change == 'wrong_reviewer':
        approval['reviewer'] = 'author'
    elif change == 'stale_approval':
        approval['narration_sha256'] = 'old-script'
    with pytest.raises(AssertionError):
        validate_plan(plan, approval, root, images)
