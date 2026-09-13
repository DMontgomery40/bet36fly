"""Synthetic probe safety checks; all network and timer operations replaced."""

import json

import pytest

import localization_range_probe as probe


@pytest.fixture
def harness(monkeypatch, tmp_path):
    plan = json.loads(probe.PLAN.read_text())
    plan['requests'][0]['maximum_payload_bytes'] = 8
    plan_path = tmp_path/'plan.json'
    plan_path.write_text(json.dumps(plan))
    monkeypatch.setattr(probe, 'PLAN', plan_path)
    monkeypatch.setattr(probe, 'OUT', tmp_path/'out')
    state = {'reads': 0, 'status': 206, 'headers': {'Content-Range': 'bytes 92-99/100', 'Content-Length': '8'},
             'body': bytearray(b'12345678'), 'deadline': False, 'address_attempts': 0}

    def set_handler(signum, handler):
        state['handler'] = handler

    monkeypatch.setattr(probe.signal, 'signal', set_handler)
    monkeypatch.setattr(probe.signal, 'setitimer', lambda *args: None)

    class Response:
        def __init__(self):
            self.status = state['status']

        def getheaders(self):
            return list(state['headers'].items())

        def getheader(self, key, default=None):
            return state['headers'].get(key, default)

        def read1(self, size):
            state['reads'] += 1
            chunk = bytes(state['body'][:size])
            del state['body'][:size]
            return chunk

    class Connection:
        def __init__(self, *args, **kwargs):
            pass

        def request(self, *args, **kwargs):
            if state['deadline']:
                # Mirrors address fallback catching OSError: the fixed deadline
                # must escape it immediately, not advance to a second address.
                for _ in range(2):
                    state['address_attempts'] += 1
                    try:
                        state['handler'](0, None)
                    except OSError:
                        continue

        def getresponse(self):
            return Response()

        def close(self):
            pass

    monkeypatch.setattr(probe.http.client, 'HTTPSConnection', Connection)
    return state


@pytest.mark.parametrize(('status', 'headers'), [
    (200, {'Content-Length': '10000000000'}),
    (200, {}),
    (302, {'Location': 'https://example.invalid'}),
    (206, {}),
    (206, {'Content-Range': 'bytes 90-99/100', 'Content-Length': '10'}),
    (206, {'Content-Range': 'bytes 92-99/100', 'Content-Length': '9'}),
    (206, {'Content-Range': 'bytes 90-97/100', 'Content-Length': '8'}),
])
def test_range_headers_reject_without_payload(harness, status, headers):
    harness.update(status=status, headers=headers)
    probe.run(1)
    result = json.loads((probe.OUT/'result-01.json').read_text())
    assert result['status'] == 'failed' and result['payload_bytes'] == 0
    assert harness['reads'] == 0


def test_exact_range_is_saved_without_extra_read(harness):
    probe.run(1)
    result = json.loads((probe.OUT/'result-01.json').read_text())
    assert result['status'] == 'received' and result['payload_bytes'] == 8
    assert harness['reads'] == 1 and (probe.OUT/'payload-01.bin').read_bytes() == b'12345678'


def test_truncated_range_preserves_partial_failure(harness):
    harness['body'] = bytearray(b'123')
    probe.run(1)
    result = json.loads((probe.OUT/'result-01.json').read_text())
    assert result['status'] == 'failed' and result['payload_bytes'] == 3
    assert (probe.OUT/'payload-01.bin').read_bytes() == b'123'


def test_deadline_cannot_be_swallowed_by_address_fallback(harness):
    harness['deadline'] = True
    probe.run(1)
    result = json.loads((probe.OUT/'result-01.json').read_text())
    assert result['status'] == 'failed' and result['error_type'] == 'DeadlineExceeded'
    assert harness['address_attempts'] == 1 and harness['reads'] == 0


def test_identity_reuse_and_missing_completion_stop_before_request(harness):
    probe.run(1)
    with pytest.raises(AssertionError):
        probe.run(1)
    (probe.OUT/'result-01.json').unlink()
    with pytest.raises(RuntimeError, match='Unfinished prior attempt'):
        probe.run(2)
    assert harness['reads'] == 1
