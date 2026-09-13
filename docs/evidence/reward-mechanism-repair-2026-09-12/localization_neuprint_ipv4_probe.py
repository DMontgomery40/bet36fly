"""Two-request unauthenticated transport check; no selected-body queries."""

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

URLS = ('https://neuprint.janelia.org/api/serverinfo',
        'https://neuprint.janelia.org/api/dbmeta/datasets')
CAPS = (4096, 32768)


class DeadlineExceeded(RuntimeError):
    pass


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('Nonstandard JSON numeric constant')

    return json.loads(data.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)


def read_complete_json(response, maximum, payload):
    if response.status != 200:
        raise ValueError('Non200 status: no payload consumed and no next request')
    if response.getheader('Content-Encoding', 'identity') != 'identity':
        raise ValueError('Unexpected HTTP content encoding')
    raw_length = response.getheader('Content-Length')
    if raw_length is not None and response.getheader('Transfer-Encoding'):
        raise ValueError('Ambiguous HTTP framing')
    if raw_length is not None:
        if not re.fullmatch(r'\d+', raw_length) or int(raw_length) > maximum:
            raise ValueError('Invalid or oversized Content-Length before payload')
        expected = int(raw_length)
    else:
        expected = None
    limit = maximum if expected is None else expected
    eof = False
    while len(payload) < limit:
        chunk = response.read1(min(4096, limit-len(payload)))
        if not chunk:
            eof = True
            break
        payload.extend(chunk)
    if expected is not None and len(payload) != expected:
        raise ValueError('Truncated declared JSON response')
    if expected is None and not eof:
        raise ValueError('Unknown-length JSON reached cap without observed EOF')
    return strict_json(payload)


def connect_ipv4(host, port, timeout, record, started):
    stages = record['network_stages']
    stages['dns_start_seconds'] = time.monotonic()-started
    candidates = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
    stages['dns_end_seconds'] = time.monotonic()-started
    family, kind, proto, _, endpoint = candidates[0]
    record['address_family'] = 'AF_INET'
    record['chosen_endpoint'] = {'ip': endpoint[0], 'port': endpoint[1]}
    record['resolved_ipv4_addresses'] = len(candidates)
    record['connection_attempts'] = 1
    sock = socket.socket(family, kind, proto)
    sock.settimeout(timeout)
    stages['tcp_start_seconds'] = time.monotonic()-started
    try:
        sock.connect(endpoint)
        stages['tcp_end_seconds'] = time.monotonic()-started
    except BaseException:
        sock.close()
        raise
    return sock


def make_connection(host, timeout, record, started):
    class StagedHTTPS(http.client.HTTPSConnection):
        def connect(self):
            if self._tunnel_host is not None:
                raise ValueError('Proxy tunnels are forbidden')
            self.sock = connect_ipv4(self.host, self.port, self.timeout, record, started)
            record['network_stages']['tls_start_seconds'] = time.monotonic()-started
            self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)
            record['network_stages']['tls_end_seconds'] = time.monotonic()-started

    return StagedHTTPS(host, timeout=timeout)


def execute(plan_path, expected_hash):
    plan_path = Path(plan_path)
    if digest(plan_path) != expected_hash:
        raise ValueError('Plan hash mismatch')
    plan = strict_json(plan_path.read_bytes())
    if plan['status'] != 'frozen' or tuple(x['url'] for x in plan['requests']) != URLS:
        raise ValueError('Unfrozen or noncanonical request plan')

    def verify():
        if digest(plan_path) != expected_hash:
            raise ValueError('Plan drift')
        for entry in plan['sources']:
            path = Path(entry['path'])
            if path.is_symlink() or digest(path) != entry['sha256'] or path.stat().st_size != entry['bytes']:
                raise ValueError('Source drift')

    verify()
    if not any(Path(x['path']).resolve() == Path(__file__).resolve() for x in plan['sources']):
        raise ValueError('Executing source is unbound')
    out = Path(plan['output_directory'])
    out.mkdir(exist_ok=False)
    results = []
    for index, url in enumerate(URLS):
        if results and not (results[-1]['status'] == 'received' and results[-1]['http_status'] == 200
                            and results[-1]['complete_valid_json']):
            break
        verify()
        time_left = 30-sum(x['elapsed_seconds'] for x in results)
        if time_left <= 1:
            break
        timeout = min(14, time_left-1)
        record = dict(slot=index+1, url=url, method='GET', status='attempted',
                      started_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      plan_sha256=expected_hash, executed_source_sha256=digest(__file__),
                      source_bindings=plan['sources'], payload_cap=CAPS[index], header_cap=8192,
                      active_deadline_seconds=timeout, maximum_wall_seconds=15,
                      network_stages={}, payload_bytes=0, header_bytes=0, complete_valid_json=False,
                      authentication_sent=False, cookies_sent=False, proxy_configuration_used=False,
                      redirects_followed=False, retry_count=0, connection_attempts=0)
        with (out/f'attempt-{index+1:02d}.json').open('x') as stream:
            json.dump(record, stream, indent=2)
        started, payload, connection = time.monotonic(), bytearray(), None

        def expired(signum, frame):
            raise DeadlineExceeded('Absolute active deadline')

        class HeaderReader:
            def __init__(self, wrapped):
                self.wrapped = wrapped

            def readline(self, limit=-1):
                left = 8192-record['header_bytes']
                if left <= 0:
                    raise ValueError('HTTP header cap reached')
                line = self.wrapped.readline(min(left, 4096, limit if limit >= 0 else 4096))
                record['header_bytes'] += len(line)
                if not line.endswith(b'\n'):
                    raise ValueError('Incomplete or oversized HTTP header line')
                if line.startswith(b'HTTP/'):
                    record['network_stages'].setdefault('first_status_line_received_seconds', time.monotonic()-started)
                return line

            def __getattr__(self, name):
                return getattr(self.wrapped, name)

        class BoundedResponse(http.client.HTTPResponse):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fp = HeaderReader(self.fp)

        try:
            signal.signal(signal.SIGALRM, expired)
            signal.setitimer(signal.ITIMER_REAL, timeout)
            parsed = urlsplit(url)
            connection = make_connection(parsed.hostname, timeout, record, started)
            connection.response_class = BoundedResponse
            connection.request('GET', parsed.path,
                               headers={'Accept': 'application/json', 'Accept-Encoding': 'identity',
                                        'Connection': 'close', 'User-Agent': 'BET36FLY-bounded-IPv4-metadata/1.0'})
            record['network_stages']['request_sent_seconds'] = time.monotonic()-started
            response = connection.getresponse()
            record['network_stages']['headers_complete_seconds'] = time.monotonic()-started
            record['http_status'] = response.status
            record['response_headers'] = {key.lower(): value for key, value in response.getheaders()
                                          if key.lower() in {'content-type', 'content-length', 'transfer-encoding',
                                                             'content-encoding', 'etag', 'server'}}
            value = read_complete_json(response, CAPS[index], payload)
            record['json_value'] = value
            record['json_type'] = type(value).__name__
            if isinstance(value, dict):
                record['public_named_fields'] = {key: {'value': item, 'type': type(item).__name__}
                                                  for key, item in value.items() if 'public' in key.lower()}
            record['complete_valid_json'] = True
            record['status'] = 'received'
        except Exception as error:
            record['status'] = 'failed'
            record['error_type'], record['error'] = type(error).__name__, str(error)
        finally:
            record['network_stages']['active_io_end_seconds'] = time.monotonic()-started
            signal.setitimer(signal.ITIMER_REAL, 0)
            if connection:
                connection.close()
            record['elapsed_seconds'] = time.monotonic()-started
            record['request_wall_cap_met'] = record['elapsed_seconds'] <= 15
            if not record['request_wall_cap_met']:
                record['status'] = 'failed'
                record['wall_cap_failure'] = True
            record['payload_bytes'], record['response_bytes'] = len(payload), len(payload)+record['header_bytes']
            if payload:
                with (out/f'payload-{index+1:02d}.json').open('xb') as stream:
                    stream.write(payload)
                record['payload_sha256'] = hashlib.sha256(payload).hexdigest()
            try:
                verify()
                record['sources_unchanged_after_request'] = True
            except ValueError as error:
                record['status'] = 'failed'
                record['source_drift_error'] = str(error)
            with (out/f'result-{index+1:02d}.json').open('x') as stream:
                json.dump(record, stream, indent=2, allow_nan=False)
                stream.write('\n')
            results.append(record)
            print(json.dumps({key: record.get(key) for key in ('slot', 'status', 'http_status', 'payload_bytes',
                                                               'response_bytes', 'elapsed_seconds', 'public_named_fields',
                                                               'error_type', 'network_stages')}, indent=2), flush=True)
    response_bytes = sum(x['response_bytes'] for x in results)
    elapsed = sum(x['elapsed_seconds'] for x in results)
    assert len(results) <= 2 and response_bytes <= 65536
    summary = dict(plan_sha256=expected_hash, requests=len(results), response_bytes=response_bytes,
                   elapsed_seconds=elapsed, total_time_cap_met=elapsed <= 30,
                   all_request_wall_caps_met=all(x['request_wall_cap_met'] for x in results),
                   requests_completed_with_valid_json=sum(x['complete_valid_json'] for x in results),
                   second_request_made=len(results) == 2, results=results,
                   additional_requests=0, synapse_data_requested=False, credentials_used=False)
    with (out/'summary.json').open('x') as stream:
        json.dump(summary, stream, indent=2, allow_nan=False)
        stream.write('\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', required=True)
    parser.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    execute(args.plan, args.plan_sha256)
