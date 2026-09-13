"""Synthetic transport/JSON gates; no actual networking."""

import json
from pathlib import Path
import time

import pytest

import localization_neuprint_ipv4_probe as probe


class Response:
    def __init__(self, body=b'{"IsPublic":true}', status=200, headers=None):
        self.status, self.body, self.reads = status, bytearray(body), 0
        self.headers = {'Content-Length': str(len(body))} if headers is None else headers

    def getheader(self, key, default=None):
        return self.headers.get(key, default)

    def getheaders(self):
        return list(self.headers.items())

    def read1(self, maximum):
        self.reads += 1
        result = bytes(self.body[:min(maximum, 7)])
        del self.body[:len(result)]
        return result


@pytest.mark.parametrize('value', [{'IsPublic': True}, {'isPublic': 'false'}, ['x'], 1, None, 'ok'])
@pytest.mark.parametrize('framing', ['length', 'chunked', 'close'])
def test_complete_valid_json_preserves_types(value, framing):
    data = json.dumps(value).encode()
    headers = {'Content-Length': str(len(data))} if framing == 'length' else {'Transfer-Encoding': 'chunked'} if framing == 'chunked' else {}
    response = Response(data, headers=headers)
    assert probe.read_complete_json(response, 4096, bytearray()) == value


@pytest.mark.parametrize('status', [301, 302, 304, 400, 401, 403, 404, 429, 500])
def test_non200_response_reads_no_body(status):
    response = Response(status=status)
    with pytest.raises(ValueError, match='Non200'):
        probe.read_complete_json(response, 4096, bytearray())
    assert response.reads == 0


@pytest.mark.parametrize('headers', [{'Content-Length': '4097'}, {'Content-Length': '-1'},
                                    {'Content-Length': '4, 4'}, {'Content-Encoding': 'gzip'},
                                    {'Content-Length': '4', 'Transfer-Encoding': 'chunked'}])
def test_bad_framing_and_caps_fail_before_body(headers):
    response = Response(headers=headers)
    with pytest.raises(ValueError):
        probe.read_complete_json(response, 4096, bytearray())
    assert response.reads == 0


@pytest.mark.parametrize('data', [b'', b'{', b'NaN', b'Infinity', b'{"IsPublic":true,"IsPublic":false}',
                                 b'\xff', b'{} trailing'])
def test_malformed_json_cannot_open_second_request(data):
    with pytest.raises((ValueError, UnicodeError)):
        probe.read_complete_json(Response(data), 4096, bytearray())


def test_truncated_and_unknown_length_cap_preserve_bytes():
    partial = bytearray()
    with pytest.raises(ValueError, match='Truncated'):
        probe.read_complete_json(Response(b'{}', headers={'Content-Length': '3'}), 4096, partial)
    assert partial == b'{}'
    partial = bytearray()
    with pytest.raises(ValueError, match='without observed EOF'):
        probe.read_complete_json(Response(b'{}', headers={}), 2, partial)
    assert partial == b'{}'


@pytest.fixture
def fake(monkeypatch, tmp_path):
    source = Path(probe.__file__)
    plan = {'status': 'frozen', 'requests': [{'url': url} for url in probe.URLS],
            'output_directory': str(tmp_path/'out'),
            'sources': [{'path': str(source), 'bytes': source.stat().st_size, 'sha256': probe.digest(source)}]}
    path = tmp_path/'plan.json'
    path.write_text(json.dumps(plan))
    state = {'connections': [], 'responses': [Response(), Response(b'{"male-cns:v1.0":{}}')], 'failure': None}
    monkeypatch.setattr(probe.signal, 'signal', lambda *args: None)
    monkeypatch.setattr(probe.signal, 'setitimer', lambda *args: None)

    class Connection:
        def __init__(self, number):
            self.number = number

        def request(self, method, request_path, headers):
            state['connections'][self.number].update(method=method, path=request_path, headers=headers)
            if state['failure']:
                raise state['failure']

        def getresponse(self):
            return state['responses'][self.number]

        def close(self):
            pass

    def connect(*args):
        number = len(state['connections'])
        state['connections'].append({})
        return Connection(number)

    monkeypatch.setattr(probe, 'make_connection', connect)
    return state, path, probe.digest(path), tmp_path/'out'


def test_two_requests_only_after_valid_first_json(fake):
    state, path, digest, out = fake
    result = probe.execute(path, digest)
    assert result['requests'] == 2 and result['requests_completed_with_valid_json'] == 2
    for index, connection in enumerate(state['connections']):
        assert connection['path'] == ['/api/serverinfo', '/api/dbmeta/datasets'][index]
        assert 'Authorization' not in connection['headers'] and 'Cookie' not in connection['headers']
        attempt = json.loads((out/f'attempt-{index+1:02d}.json').read_text())
        assert attempt['executed_source_sha256'] == probe.digest(probe.__file__)
    assert result['results'][0]['public_named_fields'] == {'IsPublic': {'value': True, 'type': 'bool'}}


@pytest.mark.parametrize('failure', ['auth', 'redirect', 'badjson', 'oversize', 'truncated', 'deadline', 'transport'])
def test_first_failure_never_opens_dataset_request(fake, failure):
    state, path, digest, out = fake
    if failure in ('auth', 'redirect'):
        state['responses'][0].status = 403 if failure == 'auth' else 302
    elif failure == 'badjson':
        state['responses'][0] = Response(b'{')
    elif failure == 'oversize':
        state['responses'][0] = Response(headers={'Content-Length': '4097'})
    elif failure == 'truncated':
        state['responses'][0] = Response(b'{}', headers={'Content-Length': '4'})
    else:
        state['failure'] = probe.DeadlineExceeded('deadline') if failure == 'deadline' else OSError('transport')
    result = probe.execute(path, digest)
    assert result['requests'] == 1 and result['results'][0]['status'] == 'failed'
    assert len(state['connections']) == 1 and not (out/'attempt-02.json').exists()
    assert not issubclass(probe.DeadlineExceeded, OSError)


def test_single_resolved_ipv4_address_has_no_fallback(monkeypatch):
    attempts = []
    closed = []

    class Socket:
        def settimeout(self, value):
            pass

        def connect(self, address):
            attempts.append(address)
            raise OSError('first address failed')

        def close(self):
            closed.append(True)

    monkeypatch.setattr(probe.socket, 'getaddrinfo', lambda *args: [
        (probe.socket.AF_INET, probe.socket.SOCK_STREAM, 0, '', ('192.0.2.1', 443)),
        (probe.socket.AF_INET, probe.socket.SOCK_STREAM, 0, '', ('192.0.2.2', 443))])
    monkeypatch.setattr(probe.socket, 'socket', lambda *args: Socket())
    record = {'network_stages': {}}
    with pytest.raises(OSError):
        probe.connect_ipv4('example.invalid', 443, 14, record, time.monotonic())
    assert attempts == [('192.0.2.1', 443)] and len(closed) == 1
    assert record['address_family'] == 'AF_INET' and record['connection_attempts'] == 1
    assert 'dns_end_seconds' in record['network_stages'] and 'tcp_end_seconds' not in record['network_stages']


def test_plan_hash_and_identity_reuse_stop_before_transport(fake):
    state, path, digest, out = fake
    with pytest.raises(ValueError, match='Plan hash'):
        probe.execute(path, '0'*64)
    probe.execute(path, digest)
    with pytest.raises(FileExistsError):
        probe.execute(path, digest)
    assert len(state['connections']) == 2
