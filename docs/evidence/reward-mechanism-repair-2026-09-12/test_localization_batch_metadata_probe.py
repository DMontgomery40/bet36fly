"""Independent protocol shapes with all network operations replaced."""

import json
from pathlib import Path

import pytest

import localization_batch_metadata_probe as probe


def spec(start=10, length=8):
    return dict(url='https://storage.googleapis.com/example', range_start=start,
                range_end=start+length-1, object_bytes=1000, etag='"abc"',
                generation='123', maximum_payload_bytes=length)


def headers(value):
    return {'Content-Range': f"bytes {value['range_start']}-{value['range_end']}/{value['object_bytes']}",
            'Content-Length': str(value['range_end']-value['range_start']+1),
            'ETag': value['etag'], 'x-goog-generation': value['generation']}


@pytest.mark.parametrize('start', [0, 1, 10, 999])
@pytest.mark.parametrize('length', [1, 8, 640, 2080])
def test_general_exact_interior_ranges(start, length):
    value = spec(start, length)
    value['object_bytes'] = start+length+100
    assert probe.validate_headers(value, 206, headers(value), 65536) == length


@pytest.mark.parametrize(('key', 'bad'), [
    ('Content-Range', 'bytes 9-16/1000'), ('Content-Range', 'bytes 11-18/1000'),
    ('Content-Range', 'bytes 10-18/1000'), ('Content-Range', 'bytes 10-17/1001'),
    ('Content-Range', 'bytes */1000'), ('Content-Range', 'bytes -1-6/1000'),
    ('Content-Range', ''), ('Content-Length', '7'), ('Content-Length', '9'),
    ('ETag', '"different"'), ('ETag', 'W/"abc"'), ('ETag', ''),
    ('x-goog-generation', '124'), ('x-goog-generation', ''),
    ('Content-Encoding', 'gzip'),
])
def test_range_and_version_mismatch_reject(key, bad):
    value = spec()
    received = headers(value)
    received[key] = bad
    with pytest.raises(ValueError):
        probe.validate_headers(value, 206, received, 100)


@pytest.mark.parametrize('status', [200, 301, 302, 304, 400, 403, 404, 412, 416, 500])
def test_file_statuses_reject_before_payload(status):
    with pytest.raises(ValueError):
        probe.validate_headers(spec(), status, headers(spec()), 100)


@pytest.mark.parametrize('left', [0, 1, 7])
def test_remaining_byte_budget_is_not_overrun(left):
    with pytest.raises(ValueError):
        probe.validate_headers(spec(), 206, headers(spec()), left)


@pytest.fixture
def fake(monkeypatch, tmp_path):
    source = Path(probe.__file__)
    value = spec()
    plan = dict(status='frozen', requests=[value, value, value],
                output_directory=str(tmp_path/'out'),
                source_bindings=[dict(path=str(source), sha256=probe.sha(source), bytes=source.stat().st_size)])
    plan_path = tmp_path/'plan.json'
    plan_path.write_text(json.dumps(plan))
    state = dict(reads=0, status=206, received=headers(value), payload=bytearray(b'12345678'), deadline=False)

    def set_signal(signum, handler):
        state['handler'] = handler

    monkeypatch.setattr(probe.signal, 'signal', set_signal)
    monkeypatch.setattr(probe.signal, 'setitimer', lambda *args: None)

    class Response:
        def __init__(self):
            self.status = state['status']

        def getheaders(self):
            return list(state['received'].items())

        def read1(self, length):
            state['reads'] += 1
            result = bytes(state['payload'][:length])
            del state['payload'][:length]
            return result

    class Connection:
        def __init__(self, *args, **kwargs):
            pass

        def request(self, method, path, headers):
            state['sent'] = (method, path, headers)
            if state['deadline']:
                state['handler'](0, None)

        def getresponse(self):
            return Response()

        def close(self):
            pass

    monkeypatch.setattr(probe.http.client, 'HTTPSConnection', Connection)
    return state, plan_path, probe.sha(plan_path), tmp_path/'out'


def test_sent_version_preconditions_and_contemporaneous_source_hash(fake):
    state, path, digest, out = fake
    result = probe.execute(path, digest, 1)
    assert state['sent'][1].endswith('?generation=123')
    assert state['sent'][2]['If-Match'] == '"abc"'
    assert state['sent'][2]['x-goog-if-generation-match'] == '123'
    assert state['sent'][2]['Range'] == 'bytes=10-17'
    attempt = json.loads((out/'attempt-01.json').read_text())
    assert attempt['executed_source_sha256'] == result['executed_source_sha256'] == probe.sha(probe.__file__)
    assert result['status'] == 'received' and result['sources_unchanged_after_request']
    assert state['reads'] == 1


@pytest.mark.parametrize('failure', ['status', 'range', 'etag', 'generation', 'oversized'])
def test_invalid_response_never_reads_payload(fake, failure):
    state, path, digest, out = fake
    if failure == 'status':
        state['status'] = 200
    else:
        state['received'][{'range': 'Content-Range', 'etag': 'ETag', 'generation': 'x-goog-generation',
                           'oversized': 'Content-Length'}[failure]] = 'invalid'
    result = probe.execute(path, digest, 1)
    assert result['status'] == 'failed' and result['payload_bytes'] == 0
    assert state['reads'] == 0


@pytest.mark.parametrize('length', [0, 1, 7])
def test_truncation_preserves_exact_partial_bytes(fake, length):
    state, path, digest, out = fake
    state['payload'] = bytearray(b'x'*length)
    result = probe.execute(path, digest, 1)
    assert result['status'] == 'failed' and result['payload_bytes'] == length
    assert (out/'attempt-01.json').is_file() and (out/'result-01.json').is_file()
    if length:
        assert (out/'payload-01.bin').read_bytes() == b'x'*length


def test_deadline_is_not_an_oserror_and_saves_failed_outcome(fake):
    state, path, digest, out = fake
    assert not issubclass(probe.DeadlineExceeded, OSError)
    state['deadline'] = True
    result = probe.execute(path, digest, 1)
    assert result['status'] == 'failed' and result['error_type'] == 'DeadlineExceeded'
    assert state['reads'] == 0


def test_identity_and_plan_drift_prevent_request(fake):
    state, path, digest, out = fake
    with pytest.raises(ValueError, match='Plan hash'):
        probe.execute(path, '0'*64, 1)
    probe.execute(path, digest, 1)
    with pytest.raises(ValueError, match='identity reuse'):
        probe.execute(path, digest, 1)
    (out/'result-01.json').unlink()
    with pytest.raises(ValueError, match='Unfinished'):
        probe.execute(path, digest, 2)
    assert state['reads'] == 1
