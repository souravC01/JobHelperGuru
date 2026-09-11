import ipaddress
import socket
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, Set, Tuple, Any, Dict
import httpx2 as httpx
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import replace


class SSRFBlockedError(ValueError):
    """Raised when an outbound HTTP request destination violates security policy."""
    pass


def is_safe_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Checks whether an IP address is a safe, globally routable public address."""
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped

    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or not ip.is_global
    ):
        return False

    ip_str = str(ip)
    if ip_str.startswith("169.254."):
        return False

    return True


def is_safe_ip_string(ip_str: str) -> bool:
    """Checks whether an IP string is safe and not private/loopback."""
    try:
        ip = ipaddress.ip_address(ip_str.strip())
        return is_safe_ip(ip)
    except ValueError:
        return False


@dataclass
class OutboundPolicy:
    mode: str = "production"  # production, local, test
    allowed_provider_hosts: Set[str] = field(default_factory=set)
    local_ai_hosts: Set[str] = field(default_factory=lambda: {"localhost", "127.0.0.1"})
    is_ai_request: bool = False
    is_scraping_request: bool = False
    max_redirects: int = 5
    max_body_bytes: int = 2 * 1024 * 1024  # 2 MiB


def validate_destination_url(url: str, policy: OutboundPolicy, *, resolve_addresses: bool = True) -> Tuple[str, str]:
    """
    Enforces scheme, hostname, port, and resolved-address rules.
    Returns (clean_url, hostname).
    """
    clean = url.strip()
    parts = urllib.parse.urlsplit(clean)

    if not parts.scheme:
        raise SSRFBlockedError("URL scheme is required.")

    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        raise SSRFBlockedError(f"Disallowed URL scheme '{scheme}'. Only http and https are permitted.")

    if parts.username or parts.password:
        raise SSRFBlockedError("URL credentials (userinfo) are not permitted.")

    hostname = (parts.hostname or "").lower().strip()
    if not hostname:
        raise SSRFBlockedError("URL hostname is required.")

    port = parts.port or (443 if scheme == "https" else 80)

    local = policy.is_ai_request and policy.mode == "local" and hostname in policy.local_ai_hosts
    if not local and port != (443 if scheme == "https" else 80):
        raise SSRFBlockedError("Destination port is not permitted")
    if policy.is_ai_request and not local:
        if scheme != "https":
            raise SSRFBlockedError("Cloud AI provider endpoints must use HTTPS.")
        if not policy.allowed_provider_hosts or hostname not in policy.allowed_provider_hosts:
            raise SSRFBlockedError(f"Host '{hostname}' is not in allowed AI provider destinations.")
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        literal = None
    if literal is not None and not (literal.is_loopback if local else is_safe_ip(literal)):
        raise SSRFBlockedError("Destination IP is private or disallowed")
    if resolve_addresses:
        from backend.services.pinned_transport import resolve_public_addresses
        resolve_public_addresses(hostname, port, allow_loopback=local)
    return clean, hostname


_operation_deadline = ContextVar("outbound_operation_deadline", default=None)


@contextmanager
def outbound_budget(seconds=30):
    existing = _operation_deadline.get()
    deadline = min(existing, time.monotonic() + seconds) if existing else time.monotonic() + seconds
    token = _operation_deadline.set(deadline)
    try:
        yield
    finally:
        _operation_deadline.reset(token)

class SafeHttpClient:
    """HTTP client enforcing outbound request policies, redirect bounds, and body limits."""

    def __init__(self, default_policy: Optional[OutboundPolicy] = None):
        self.default_policy = default_policy or OutboundPolicy()

    def request(
        self,
        method: str,
        url: str,
        *,
        policy: Optional[OutboundPolicy] = None,
        timeout: float = 15.0,
        max_bytes: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        from backend.services.pinned_transport import PinnedTransport, remaining
        active_policy = policy or self.default_policy
        if max_bytes is not None:
            active_policy = replace(active_policy, max_body_bytes=min(max_bytes, active_policy.max_body_bytes))
        deadline = _operation_deadline.get() or time.monotonic() + min(timeout, 30)
        current_url = url
        req_headers = dict(headers or {})
        with httpx.Client(transport=PinnedTransport(active_policy), follow_redirects=False, trust_env=False) as client:
            for hops in range(active_policy.max_redirects + 1):
                clean_url, _ = validate_destination_url(current_url, active_policy, resolve_addresses=False)
                resp = client.request(method, clean_url, headers=req_headers, timeout=remaining(deadline),
                                      extensions={"jhg_deadline": deadline}, **kwargs)
                if not resp.is_redirect or "location" not in resp.headers:
                    return resp
                if hops == active_policy.max_redirects:
                    raise SSRFBlockedError("Too many redirects")
                next_url = urllib.parse.urljoin(clean_url, resp.headers["location"])
                previous = urllib.parse.urlsplit(clean_url)
                following = urllib.parse.urlsplit(next_url)
                if (previous.scheme, previous.netloc) != (following.scheme, following.netloc):
                    req_headers = {k: v for k, v in req_headers.items() if k.lower() not in {"authorization", "cookie"}}
                current_url = next_url
    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        return self.request("POST", url, **kwargs)
