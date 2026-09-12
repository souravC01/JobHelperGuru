import gzip
import socket
import time
from unittest.mock import Mock

import httpx2
import httpcore2
import pytest

from backend.services.outbound_http import OutboundPolicy, SSRFBlockedError, is_safe_ip_string


def test_shared_address_space_is_not_public():
    assert not is_safe_ip_string('100.64.0.1')


def test_connection_revalidates_dns_and_never_dials_private(monkeypatch):
    from backend.services.pinned_transport import PinnedNetworkBackend
    dial = Mock()
    monkeypatch.setattr('httpcore2.SyncBackend.connect_tcp', dial)
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 443))])
    backend = PinnedNetworkBackend(OutboundPolicy(is_scraping_request=True))
    with pytest.raises(SSRFBlockedError):
        backend.connect_tcp('rebind.example.test', 443, timeout=1)
    dial.assert_not_called()


def test_connection_dials_validated_literal_and_preserves_tls_name(monkeypatch):
    from backend.services.pinned_transport import PinnedNetworkBackend
    stream = Mock()
    stream.start_tls.return_value = stream
    dial = Mock(return_value=stream)
    monkeypatch.setattr('httpcore2.SyncBackend.connect_tcp', dial)
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443))])
    wrapped = PinnedNetworkBackend(OutboundPolicy()).connect_tcp('public.example.test', 443, timeout=1)
    assert dial.call_args.kwargs['host'] == '8.8.8.8'
    wrapped.start_tls(ssl_context=Mock(), server_hostname='public.example.test', timeout=1)
    assert stream.start_tls.call_args.kwargs['server_hostname'] == 'public.example.test'


@pytest.mark.parametrize('compressed', [False, True])
def test_transport_stops_oversize_body(monkeypatch, compressed):
    from backend.services.pinned_transport import PinnedTransport
    data = gzip.compress(b'x' * 10000) if compressed else b'x' * 10000
    closed = []
    class Stream(httpx2.SyncByteStream):
        def __iter__(self):
            yield data
            pytest.fail('oversized response must stop before reading the next chunk')
        def close(self): closed.append(True)
    monkeypatch.setattr(httpx2.HTTPTransport, 'handle_request', lambda self, req: httpx2.Response(
        200, headers={'content-encoding': 'gzip'} if compressed else {}, stream=Stream()))
    transport = PinnedTransport(OutboundPolicy(max_body_bytes=100))
    with pytest.raises(ValueError, match='limit'):
        transport.handle_request(httpx2.Request('GET', 'https://example.test'))
    assert closed
    transport.close()


def test_ai_redirect_is_never_followed(monkeypatch):
    from backend.services.ai_engine import AIEngine
    requests = []
    def reply(self, request):
        requests.append(str(request.url))
        return httpx2.Response(307, headers={'location': 'https://127.0.0.1/internal'}, stream=httpx2.ByteStream(b''))
    monkeypatch.setattr(httpx2.HTTPTransport, 'handle_request', reply)
    client = AIEngine(api_key='synthetic', model_name='test')._get_client()
    try:
        with pytest.raises(Exception):
            client.chat.completions.create(model='test', messages=[{'role': 'user', 'content': 'synthetic'}])
        assert len(requests) == 1
    finally:
        client.close()


def test_expired_deadline_stops_before_connect(monkeypatch):
    from backend.services.pinned_transport import PinnedTransport
    send = Mock()
    monkeypatch.setattr(httpx2.HTTPTransport, 'handle_request', send)
    transport = PinnedTransport(OutboundPolicy())
    request = httpx2.Request('GET', 'https://example.test', extensions={'jhg_deadline': time.monotonic() - 1})
    with pytest.raises(TimeoutError):
        transport.handle_request(request)
    send.assert_not_called()
    transport.close()


def test_real_pool_uses_pinned_backend_and_original_tls_hostname(monkeypatch):
    from backend.services.pinned_transport import PinnedTransport
    tls_names = []
    class Stream(httpcore2.MockStream):
        def start_tls(self, ssl_context, server_hostname=None, timeout=None):
            assert ssl_context.check_hostname
            tls_names.append(server_hostname)
            return self
    stream = Stream([b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok'])
    dial = Mock(return_value=stream)
    monkeypatch.setattr(httpcore2.SyncBackend, 'connect_tcp', dial)
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443))])
    with httpx2.Client(transport=PinnedTransport(OutboundPolicy()), trust_env=False) as client:
        assert client.get('https://public.example.test').text == 'ok'
    assert dial.call_args.kwargs['host'] == '8.8.8.8'
    assert tls_names == ['public.example.test']


def test_mixed_dns_addresses_block_entire_connection(monkeypatch):
    from backend.services.pinned_transport import PinnedNetworkBackend
    dial = Mock()
    monkeypatch.setattr(httpcore2.SyncBackend, 'connect_tcp', dial)
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **k: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, '', (address, 443))
        for address in ('8.8.8.8', '10.0.0.1')])
    with pytest.raises(SSRFBlockedError):
        PinnedNetworkBackend(OutboundPolicy()).connect_tcp('mixed.example.test', 443)
    dial.assert_not_called()


@pytest.mark.parametrize('url', ['https://example.test:8443', 'http://example.test:8080', 'http://100.64.0.1'])
def test_ports_and_shared_address_space_blocked_before_send(monkeypatch, url):
    from backend.services.pinned_transport import PinnedTransport
    send = Mock()
    monkeypatch.setattr(httpx2.HTTPTransport, 'handle_request', send)
    with PinnedTransport(OutboundPolicy()) as transport:
        with pytest.raises(SSRFBlockedError):
            transport.handle_request(httpx2.Request('GET', url))
    send.assert_not_called()
