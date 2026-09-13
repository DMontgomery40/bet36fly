"""Six-request, 1 MiB read-only probe; no retries, redirects or credentials."""

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

HERE = Path(__file__).resolve().parent
PLAN = HERE / 'localization-range-plan-2026-09-13.json'
OUT = HERE / 'localization-range-probe-2026-09-13'


def run(slot):
    plan = json.loads(PLAN.read_text())
    OUT.mkdir(exist_ok=True)
    prior = [json.loads(p.read_text()) for p in OUT.glob('result-*.json')]
    attempts = list(OUT.glob('attempt-*.json'))
    if len(attempts) != len(prior):
        raise RuntimeError('Unfinished prior attempt; preserve it and stop')
    assert len(attempts) < 6 and slot == len(attempts) + 1
    request = plan['requests'][slot-1]
    url = request.get('url', request.get('url_if_no_footer_extension'))
    maximum = min(request['maximum_payload_bytes'], 983040-sum(x['payload_bytes'] for x in prior))
    if slot == 6:
        maximum = min(maximum, 65536)
    header_remaining = 65536-sum(x['header_bytes'] for x in prior)
    remaining_seconds = 90-sum(x['elapsed_seconds'] for x in prior)
    assert maximum > 0 and header_remaining > 0 and remaining_seconds > 0
    # Reserve one second for connection teardown under the 15-second wall cap.
    budget = min(14, remaining_seconds-1)
    assert budget > 0
    record = dict(slot=slot, url=url, range=request.get('range'),
                  plan_sha256=hashlib.sha256(PLAN.read_bytes()).hexdigest(),
                  started_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  status='attempted', payload_bytes=0, header_bytes=0,
                  max_payload_bytes=maximum, max_seconds=budget)
    with (OUT/f'attempt-{slot:02d}.json').open('x') as stream:
        json.dump(record, stream, indent=2)
    started = time.monotonic()
    payload = bytearray()
    connection = None

    class DeadlineExceeded(RuntimeError):
        pass

    def expired(signum, frame):
        # OSError subclasses can be swallowed by socket address fallback.
        raise DeadlineExceeded('Absolute per-request deadline reached')

    def ipv4_once(address, timeout, source_address=None):
        assert source_address is None
        candidates = socket.getaddrinfo(address[0], address[1], socket.AF_INET, socket.SOCK_STREAM)
        family, kind, proto, _, endpoint = candidates[0]
        sock = socket.socket(family, kind, proto)
        sock.settimeout(timeout)
        try:
            sock.connect(endpoint)
        except BaseException:
            sock.close()
            raise
        return sock

    class HeaderReader:
        def __init__(self, wrapped):
            self.wrapped = wrapped

        def readline(self, limit=-1):
            left = min(16384-record['header_bytes'], header_remaining-record['header_bytes'])
            if left <= 0:
                raise ValueError('Header byte cap reached')
            line = self.wrapped.readline(min(left, 4096, limit if limit >= 0 else 4096))
            record['header_bytes'] += len(line)
            if not line.endswith(b'\n'):
                raise ValueError('Incomplete or oversized HTTP header line')
            return line

        def __getattr__(self, name):
            return getattr(self.wrapped, name)

    class BoundedResponse(http.client.HTTPResponse):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fp = HeaderReader(self.fp)

    try:
        signal.signal(signal.SIGALRM, expired)
        signal.setitimer(signal.ITIMER_REAL, budget)
        target = urlsplit(url)
        assert target.scheme == 'https' and target.username is None and target.password is None
        connection = http.client.HTTPSConnection(target.hostname, timeout=budget)
        connection._create_connection = ipv4_once
        record['transport'] = 'one DNS-resolved IPv4 address; no address fallback'
        connection.response_class = BoundedResponse
        headers = {'Accept-Encoding': 'identity', 'Connection': 'close',
                   'User-Agent': 'BET36FLY-bounded-metadata-audit/1.0'}
        if request.get('range'):
            headers['Range'] = request['range']
        connection.request('GET', target.path + ('?' + target.query if target.query else ''), headers=headers)
        response = connection.getresponse()
        record['http_status'] = response.status
        record['headers'] = {key.lower(): value for key, value in response.getheaders()
                             if key.lower() in {'content-length', 'content-type', 'content-range',
                                                'content-encoding', 'transfer-encoding', 'etag',
                                                'last-modified', 'accept-ranges', 'location',
                                                'x-goog-generation', 'x-goog-metageneration', 'x-goog-hash'}}
        if request.get('range'):
            if response.status != 206:
                raise ValueError('File request did not return 206; no payload consumed')
            match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.getheader('Content-Range', ''))
            if not match:
                raise ValueError('Missing/malformed Content-Range; no payload consumed')
            start, end, total = map(int, match.groups())
            length = end-start+1
            if not (0 <= start <= end < total and end == total-1 and length <= maximum):
                raise ValueError('Unexpected or oversized suffix range; no payload consumed')
            if response.getheader('Content-Length') != str(length):
                raise ValueError('Range length mismatch; no payload consumed')
            record['range_start'], record['range_end'], record['object_bytes'] = start, end, total
            expected = length
        else:
            if response.status != 200:
                raise ValueError('Documentation status is not 200; redirects/errors not followed')
            expected = maximum
        while len(payload) < expected:
            chunk = response.read1(min(16384, expected-len(payload)))
            if not chunk:
                break
            payload.extend(chunk)
        record['payload_bytes'] = len(payload)
        if request.get('range') and len(payload) != expected:
            raise ValueError('Truncated range payload')
        length_header = response.getheader('Content-Length')
        record['payload_complete'] = bool(length_header and int(length_header) == len(payload))
        record['status'] = 'received'
    except Exception as error:
        record['status'] = 'failed'
        record['error_type'] = type(error).__name__
        record['error'] = str(error)
    finally:
        record['active_io_elapsed_seconds'] = time.monotonic()-started
        signal.setitimer(signal.ITIMER_REAL, 0)
        if connection:
            connection.close()
        record['payload_bytes'] = len(payload)
        record['elapsed_seconds'] = time.monotonic()-started
        if payload:
            destination = OUT/f'payload-{slot:02d}.bin'
            with destination.open('xb') as stream:
                stream.write(payload)
            record['payload_path'] = str(destination)
            record['payload_sha256'] = hashlib.sha256(payload).hexdigest()
        record['cumulative_response_bytes'] = sum(x['payload_bytes']+x['header_bytes'] for x in prior)+len(payload)+record['header_bytes']
        assert record['cumulative_response_bytes'] <= 1048576
        with (OUT/f'result-{slot:02d}.json').open('x') as stream:
            json.dump(record, stream, indent=2, allow_nan=False)
            stream.write('\n')
        print(json.dumps(record, indent=2, allow_nan=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--slot', type=int, choices=range(1, 7), required=True)
    run(parser.parse_args().slot)
