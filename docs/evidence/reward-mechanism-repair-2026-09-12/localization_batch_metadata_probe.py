"""Separately frozen, version-pinned metadata probe; at most three HTTP GETs."""

import argparse
import datetime
import hashlib
import http.client
import json
from pathlib import Path
import re
import signal
import socket
import time
from urllib.parse import urlsplit


class DeadlineExceeded(RuntimeError):
    """Must not inherit OSError, which address fallback can swallow."""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_headers(spec, status, headers, remaining):
    headers = {key.lower(): value for key, value in headers.items()}
    if headers.get('content-encoding', 'identity') != 'identity':
        raise ValueError('HTTP content encoding differs from requested identity')
    if 'range_start' in spec:
        if status != 206:
            raise ValueError('Metadata range requires206 before payload')
        match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', headers.get('content-range', ''))
        expected = (spec['range_start'], spec['range_end'], spec['object_bytes'])
        if not match or tuple(map(int, match.groups())) != expected:
            raise ValueError('Exact interior Content-Range mismatch')
        length = expected[1]-expected[0]+1
        if headers.get('content-length') != str(length):
            raise ValueError('Exact metadata Content-Length mismatch')
        if headers.get('etag') != spec['etag']:
            raise ValueError('ETag mismatch or missing')
        if headers.get('x-goog-generation') != spec['generation']:
            raise ValueError('Generation mismatch or missing')
    else:
        if status != 200 or not re.fullmatch(r'\d+', headers.get('content-length', '')):
            raise ValueError('Documentation requires200 and bounded Content-Length')
        length = int(headers['content-length'])
    if not 0 < length <= min(remaining, spec['maximum_payload_bytes']):
        raise ValueError('Oversized or empty payload rejected before read')
    return length


def ipv4_once(address, timeout, source_address=None):
    if source_address is not None:
        raise ValueError('Unspecified source-address override')
    family, kind, proto, _, endpoint = socket.getaddrinfo(
        address[0], address[1], socket.AF_INET, socket.SOCK_STREAM)[0]
    sock = socket.socket(family, kind, proto)
    sock.settimeout(timeout)
    try:
        sock.connect(endpoint)
    except BaseException:
        sock.close()
        raise
    return sock


def execute(plan_path, expected_plan_sha, slot):
    plan_path = Path(plan_path)
    if sha(plan_path) != expected_plan_sha:
        raise ValueError('Plan hash mismatch')
    plan = json.loads(plan_path.read_text())
    if plan['status'] != 'frozen' or len(plan['requests']) > 3:
        raise ValueError('Unfrozen or oversized plan')
    bindings = plan['source_bindings']

    def verify_sources():
        for binding in bindings:
            path = Path(binding['path'])
            if path.is_symlink() or sha(path) != binding['sha256'] or path.stat().st_size != binding['bytes']:
                raise ValueError('Source dependency drift')
        if sha(plan_path) != expected_plan_sha:
            raise ValueError('Plan drift')

    verify_sources()
    if not any(Path(x['path']).resolve() == Path(__file__).resolve() for x in bindings):
        raise ValueError('Executing source absent from bindings')
    out = Path(plan['output_directory'])
    out.mkdir(exist_ok=True)
    attempts, results = sorted(out.glob('attempt-*.json')), sorted(out.glob('result-*.json'))
    if len(attempts) != len(results):
        raise ValueError('Unfinished prior request')
    if slot != len(attempts)+1 or not 1 <= slot <= len(plan['requests']):
        raise ValueError('Request identity reuse or selection mismatch')
    prior = [json.loads(p.read_text()) for p in results]
    if any(x['status'] not in ('received', 'failed') for x in prior):
        raise ValueError('Unfinished prior outcome')
    payload_remaining = 49152-sum(x['payload_bytes'] for x in prior)
    header_remaining = 16384-sum(x['header_bytes'] for x in prior)
    time_remaining = 45-sum(x['elapsed_seconds'] for x in prior)
    if min(payload_remaining, header_remaining) <= 0 or time_remaining <= 1:
        raise ValueError('Global budget exhausted')
    spec = plan['requests'][slot-1]
    active_budget = min(14, time_remaining-1)
    record = dict(slot=slot, spec=spec, plan_sha256=expected_plan_sha,
                  executed_source_sha256=sha(__file__), source_bindings=bindings,
                  started_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  status='attempted', payload_bytes=0, header_bytes=0,
                  active_deadline_seconds=active_budget, maximum_wall_seconds=15)
    with (out/f'attempt-{slot:02d}.json').open('x') as stream:
        json.dump(record, stream, indent=2)
    started, payload, connection = time.monotonic(), bytearray(), None

    def expired(signum, frame):
        raise DeadlineExceeded('Absolute active deadline')

    class HeaderReader:
        def __init__(self, wrapped):
            self.wrapped = wrapped

        def readline(self, limit=-1):
            left = min(8192-record['header_bytes'], header_remaining-record['header_bytes'])
            if left <= 0:
                raise ValueError('Header cap reached')
            line = self.wrapped.readline(min(left, 4096, limit if limit >= 0 else 4096))
            record['header_bytes'] += len(line)
            if not line.endswith(b'\n'):
                raise ValueError('Incomplete or oversized header')
            return line

        def __getattr__(self, name):
            return getattr(self.wrapped, name)

    class BoundedResponse(http.client.HTTPResponse):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fp = HeaderReader(self.fp)

    try:
        signal.signal(signal.SIGALRM, expired)
        signal.setitimer(signal.ITIMER_REAL, active_budget)
        target = urlsplit(spec['url'])
        if target.scheme != 'https' or target.username or target.password or target.query:
            raise ValueError('Unsupported request target')
        connection = http.client.HTTPSConnection(target.hostname, timeout=active_budget)
        connection._create_connection = ipv4_once
        connection.response_class = BoundedResponse
        headers = {'Accept-Encoding': 'identity', 'Connection': 'close',
                   'User-Agent': 'BET36FLY-pinned-batch-metadata/1.0'}
        path = target.path
        if 'range_start' in spec:
            headers.update({'Range': f"bytes={spec['range_start']}-{spec['range_end']}",
                            'If-Match': spec['etag'], 'x-goog-if-generation-match': spec['generation']})
            path += '?generation='+spec['generation']
        record['sent_headers'] = headers
        record['request_path'] = path
        connection.request('GET', path, headers=headers)
        response = connection.getresponse()
        record['http_status'] = response.status
        response_headers = dict(response.getheaders())
        record['response_headers'] = {key.lower(): value for key, value in response_headers.items()
                                      if key.lower() in {'content-range', 'content-length', 'content-type',
                                                         'content-encoding', 'etag', 'last-modified',
                                                         'x-goog-generation', 'x-goog-metageneration'}}
        expected = validate_headers(spec, response.status, response_headers, payload_remaining)
        while len(payload) < expected:
            chunk = response.read1(min(8192, expected-len(payload)))
            if not chunk:
                break
            payload.extend(chunk)
        if len(payload) != expected:
            raise ValueError('Truncated metadata response')
        record['status'] = 'received'
    except Exception as error:
        record['status'] = 'failed'
        record['error_type'], record['error'] = type(error).__name__, str(error)
    finally:
        record['active_io_elapsed_seconds'] = time.monotonic()-started
        signal.setitimer(signal.ITIMER_REAL, 0)
        if connection:
            connection.close()
        record['elapsed_seconds'] = time.monotonic()-started
        record['payload_bytes'] = len(payload)
        record['response_bytes'] = len(payload)+record['header_bytes']
        record['request_wall_cap_met'] = record['elapsed_seconds'] <= 15
        if not record['request_wall_cap_met']:
            record['status'] = 'failed'
            record['wall_cap_failure'] = True
        if payload:
            with (out/f'payload-{slot:02d}.bin').open('xb') as stream:
                stream.write(payload)
            record['payload_sha256'] = hashlib.sha256(payload).hexdigest()
        try:
            verify_sources()
            record['sources_unchanged_after_request'] = True
        except ValueError as error:
            record['status'] = 'failed'
            record['source_stability_error'] = str(error)
        record['cumulative_response_bytes'] = sum(x['response_bytes'] for x in prior)+record['response_bytes']
        record['cumulative_seconds'] = sum(x['elapsed_seconds'] for x in prior)+record['elapsed_seconds']
        assert record['cumulative_response_bytes'] <= 65536
        with (out/f'result-{slot:02d}.json').open('x') as stream:
            json.dump(record, stream, indent=2, allow_nan=False)
            stream.write('\n')
        print(json.dumps(record, indent=2, allow_nan=False), flush=True)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--slot', type=int, required=True)
    args = parser.parse_args()
    execute(args.plan, args.plan_sha256, args.slot)
