"""Connection enforcement for the pinned httpx2/httpcore2 transport versions.

DNS results are checked at the dial boundary. TLS still sees the original host.
The pool adapter is version-pinned and covered by transport integration tests.
"""
import ipaddress
import socket
import time
import zlib
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from threading import BoundedSemaphore

import httpcore2
import httpx2

from backend.services.outbound_http import OutboundPolicy, SSRFBlockedError, is_safe_ip_string, validate_destination_url

_deadline = ContextVar('outbound_deadline', default=None)
_dns_workers = ThreadPoolExecutor(max_workers=8, thread_name_prefix='outbound-dns')
_dns_slots = BoundedSemaphore(16)


def remaining(deadline, timeout=None):
    budget = deadline - time.monotonic()
    if budget <= 0:
        raise TimeoutError('Outbound request deadline exceeded')
    return min(budget, timeout) if timeout is not None else budget


def resolve_public_addresses(host, port, *, allow_loopback=False, deadline=None):
    deadline = deadline or time.monotonic() + 5
    try:
        addresses = (str(ipaddress.ip_address(host)),)
    except ValueError:
        if not _dns_slots.acquire(blocking=False):
            raise TimeoutError('DNS resolver capacity exhausted')
        future = _dns_workers.submit(socket.getaddrinfo, host, port, type=socket.SOCK_STREAM)
        future.add_done_callback(lambda _: _dns_slots.release())
        rows = future.result(timeout=remaining(deadline, 5))
        addresses = tuple(dict.fromkeys(row[4][0] for row in rows))
    if not addresses:
        raise SSRFBlockedError('DNS returned no destination addresses')
    for address in addresses:
        allowed = ipaddress.ip_address(address).is_loopback if allow_loopback else is_safe_ip_string(address)
        if not allowed:
            raise SSRFBlockedError('Destination resolves to a private or disallowed address')
    return addresses


class DeadlineStream(httpcore2.NetworkStream):
    def __init__(self, stream, deadline):
        self.stream, self.deadline = stream, deadline

    def read(self, max_bytes, timeout=None):
        data = self.stream.read(min(max_bytes, 65536), timeout=remaining(self.deadline, timeout))
        remaining(self.deadline)
        return data

    def write(self, buffer, timeout=None):
        self.stream.write(buffer, timeout=remaining(self.deadline, timeout))
        remaining(self.deadline)

    def start_tls(self, ssl_context, server_hostname=None, timeout=None):
        stream = self.stream.start_tls(ssl_context=ssl_context, server_hostname=server_hostname,
                                       timeout=remaining(self.deadline, timeout))
        return DeadlineStream(stream, self.deadline)

    def close(self):
        self.stream.close()

    def get_extra_info(self, info):
        return self.stream.get_extra_info(info)


class PinnedNetworkBackend(httpcore2.SyncBackend):
    def __init__(self, policy):
        self.policy = policy

    def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        deadline = _deadline.get() or time.monotonic() + min(timeout or 30, 30)
        local = self.policy.mode == 'local' and self.policy.is_ai_request and host in self.policy.local_ai_hosts
        addresses = resolve_public_addresses(host, port, allow_loopback=local, deadline=deadline)
        last_error = None
        for address in addresses:
            try:
                stream = super().connect_tcp(host=address, port=port, timeout=remaining(deadline, timeout),
                                             local_address=local_address, socket_options=socket_options)
                return DeadlineStream(stream, deadline)
            except (OSError, httpcore2.ConnectError) as exc:
                last_error = exc
        raise last_error


class PinnedTransport(httpx2.HTTPTransport):
    def __init__(self, policy: OutboundPolicy):
        # HTTPTransport.handle_request converts between HTTPX and HTTP Core models.
        # Supply its pool with our connection backend; never create an ambient proxy.
        self.policy = policy
        self._pool = httpcore2.ConnectionPool(
            network_backend=PinnedNetworkBackend(policy), max_connections=8,
            max_keepalive_connections=0, retries=0,
        )

    def handle_request(self, request):
        deadline = request.extensions.get('jhg_deadline', time.monotonic() + 30)
        remaining(deadline)
        validate_destination_url(str(request.url), self.policy, resolve_addresses=False)
        request.headers['accept-encoding'] = 'identity'
        token = _deadline.set(deadline)
        try:
            response = super().handle_request(request)
            try:
                if response.is_redirect:
                    if self.policy.is_ai_request:
                        raise SSRFBlockedError('AI provider redirects are not permitted')
                    return httpx2.Response(response.status_code, headers=response.headers, content=b'')
                encoding = response.headers.get('content-encoding', 'identity').lower()
                if encoding not in ('identity', 'gzip', 'deflate'):
                    raise ValueError('Unsupported response content encoding')
                decoder = zlib.decompressobj(31 if encoding == 'gzip' else 15) if encoding != 'identity' else None
                body = bytearray()
                encoded = 0
                limit = self.policy.max_body_bytes
                for chunk in response.iter_raw():
                    remaining(deadline)
                    encoded += len(chunk)
                    if encoded > limit:
                        raise ValueError('Encoded response exceeds limit')
                    data = decoder.decompress(chunk, limit - len(body) + 1) if decoder else chunk
                    body.extend(data)
                    if len(body) > limit or (decoder and decoder.unconsumed_tail):
                        raise ValueError('Decoded response exceeds limit')
                    if decoder and decoder.unused_data:
                        raise ValueError('Multiple compressed response streams are not supported')
                if decoder and not decoder.eof:
                    raise ValueError('Incomplete compressed response')
                remaining(deadline)
                headers = [(key, val) for key, val in response.headers.multi_items()
                           if key.lower() not in {'content-encoding', 'content-length', 'transfer-encoding'}]
                return httpx2.Response(response.status_code, headers=headers, content=bytes(body))
            finally:
                response.close()
        finally:
            _deadline.reset(token)
