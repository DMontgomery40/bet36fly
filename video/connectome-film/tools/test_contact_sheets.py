import json
import pytest
from contact_sheets import frame_paths


@pytest.mark.parametrize('phase', ['early', 'mid', 'late'])
@pytest.mark.parametrize('ids', [[0], [0, 1, 2], [4, 1]])
def test_only_current_scenes_in_timeline_order(tmp_path, phase, ids):
    (tmp_path / 'timeline.json').write_text(json.dumps({'scenes': [{'id': i} for i in ids]}))
    frames = tmp_path / 'qa/frames'
    frames.mkdir(parents=True)
    for i in range(8):
        (frames / f'{i:02}-{phase}.jpg').write_bytes(b'stale or current frame')
    assert [p.name for p in frame_paths(tmp_path, phase)] == [f'{i:02}-{phase}.jpg' for i in ids]
