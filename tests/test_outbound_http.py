import pytest
from backend.services.outbound_http import (
    OutboundPolicy,
    SafeHttpClient,
    SSRFBlockedError,
    is_safe_ip_string,
    validate_destination_url,
)


def test_private_ip_detection():
    # Loopback
    assert not is_safe_ip_string("127.0.0.1")
    assert not is_safe_ip_string("127.0.0.2")
    assert not is_safe_ip_string("::1")
    # Private IPv4
    assert not is_safe_ip_string("10.0.0.1")
    assert not is_safe_ip_string("172.16.0.1")
    assert not is_safe_ip_string("192.168.1.1")
    # Cloud metadata / link-local
    assert not is_safe_ip_string("169.254.169.254")
    assert not is_safe_ip_string("fe80::1")
    # IPv4-mapped IPv6
    assert not is_safe_ip_string("::ffff:127.0.0.1")
    assert not is_safe_ip_string("::ffff:169.254.169.254")
    # Public IPs are safe
    assert is_safe_ip_string("8.8.8.8")
    assert is_safe_ip_string("1.1.1.1")


def test_url_credentials_and_ambiguous_syntax_rejected():
    policy = OutboundPolicy(mode="production")
    # Userinfo / credentials in URL
    with pytest.raises(SSRFBlockedError, match="credentials"):
        validate_destination_url("https://user:pass@example.com/api", policy)

    # Disallowed scheme
    with pytest.raises(SSRFBlockedError, match="scheme"):
        validate_destination_url("file:///etc/passwd", policy)
    with pytest.raises(SSRFBlockedError, match="scheme"):
        validate_destination_url("ftp://example.com/job", policy)


def test_cloud_ai_policy_restricts_to_allowed_hosts():
    policy = OutboundPolicy(
        mode="production",
        allowed_provider_hosts={"api.openai.com", "generativelanguage.googleapis.com"},
        is_ai_request=True,
    )
    # Allowed host passes validation
    clean_url, host = validate_destination_url("https://api.openai.com/v1/chat/completions", policy)
    assert host == "api.openai.com"

    # Disallowed host is rejected
    with pytest.raises(SSRFBlockedError, match="not in allowed AI provider"):
        validate_destination_url("https://evil-ai.attacker.com/v1", policy)

    # Loopback is rejected in production
    with pytest.raises(SSRFBlockedError):
        validate_destination_url("http://127.0.0.1:11434/v1", policy)


def test_local_ai_policy_allows_loopback_in_local_mode():
    policy = OutboundPolicy(
        mode="local",
        local_ai_hosts={"127.0.0.1", "localhost"},
        is_ai_request=True,
    )
    # Loopback AI permitted in local mode
    clean_url, host = validate_destination_url("http://127.0.0.1:11434/v1", policy)
    assert host == "127.0.0.1"


def test_redirect_to_private_address_is_blocked(monkeypatch):
    client = SafeHttpClient()
    policy = OutboundPolicy(mode="production", is_scraping_request=True)

    # Mock getaddrinfo for test: public.example.com -> 93.184.216.34, evil-redirect.com -> 127.0.0.1
    import socket
    orig_getaddrinfo = socket.getaddrinfo

    def mock_getaddrinfo(host, port, *args, **kwargs):
        if host == "public.example.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
        if host == "loopback.target.test":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]
        return orig_getaddrinfo(host, port, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    # Attempting to validate or fetch destination redirecting to loopback
    with pytest.raises(SSRFBlockedError, match="private or disallowed"):
        validate_destination_url("http://loopback.target.test/internal", policy)


def test_ai_test_endpoint_requires_authentication(client):
    # Unauthenticated call to /api/settings/test-ai must return 401
    resp = client.post(
        "/api/settings/test-ai",
        json={
            "api_base_url": "http://127.0.0.1:8000/internal",
            "api_key": "test",
            "model_name": "test-model",
        },
    )
    assert resp.status_code == 401
