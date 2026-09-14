"""Exercise the range-request family required by browser media players."""
import importlib.util
from pathlib import Path
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('serve_film', ROOT / 'tools/serve_film.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
client = TestClient(module.app)


def test_media_range_variants():
    path = ROOT / 'bet36fly-connectomes.mp4'
    size = path.stat().st_size
    for header, start, end in [('bytes=0-31', 0, 31), ('bytes=-24', size-24, size-1),
                               (f'bytes={size-32}-', size-32, size-1)]:
        response = client.get('/bet36fly-connectomes.mp4', headers={'Range': header})
        assert response.status_code == 206
        assert response.headers['content-range'] == f'bytes {start}-{end}/{size}'
        with path.open('rb') as source:
            source.seek(start)
            assert response.content == source.read(end-start+1)
    assert client.get('/bet36fly-connectomes.mp4', headers={'Range': f'bytes={size}-'}).status_code == 416


def test_player_and_caption_delivery():
    assert client.get('/').status_code == 200
    response = client.get('/captions.vtt')
    assert response.status_code == 200 and response.text.startswith('WEBVTT')
    response = client.head('/bet36fly-connectomes.mp4')
    assert response.status_code == 200 and response.headers['content-type'] == 'video/mp4'


def test_current_metadata_is_not_cached_across_revisions():
    for path in ['/', '/index.html', '/timeline.json', '/captions.vtt', '/captions.srt', '/NARRATION.md']:
        for method in (client.get, client.head):
            response = method(path)
            assert response.status_code == 200
            assert response.headers['cache-control'] == 'no-store'
