import ipaddress
import socket
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, Set, Tuple, Any, Dict
import httpx


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


def validate_destination_url(url: str, policy: OutboundPolicy) -> Tuple[str, str]:
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

    # 1. AI Request validation
    if policy.is_ai_request:
        if policy.mode == "local" and hostname in policy.local_ai_hosts:
            # Local mode permits local AI endpoints on loopback
            return clean, hostname

        if scheme != "https":
            raise SSRFBlockedError("Cloud AI provider endpoints must use HTTPS.")

        if policy.allowed_provider_hosts and hostname not in policy.allowed_provider_hosts:
            raise SSRFBlockedError(f"Host '{hostname}' is not in allowed AI provider destinations.")

        return clean, hostname

    # 2. General Scraping / Web Request validation
    # Check if hostname is direct IP literal
    try:
        direct_ip = ipaddress.ip_address(hostname)
        if not is_safe_ip(direct_ip):
            raise SSRFBlockedError(f"Destination IP '{hostname}' is private or disallowed.")
        return clean, hostname
    except ValueError:
        pass

    # Resolve DNS and check all returned IP addresses
    try:
        resolved = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        for entry in resolved:
            sockaddr = entry[4]
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)
            if not is_safe_ip(ip_obj):
                raise SSRFBlockedError(f"Host '{hostname}' resolves to private or disallowed address: {ip_str}")
    except socket.gaierror as e:
        raise SSRFBlockedError(f"Failed to resolve host '{hostname}': {e}")

    return clean, hostname


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
        active_policy = policy or self.default_policy
        limit_bytes = max_bytes or active_policy.max_body_bytes

        current_url = url
        req_headers = dict(headers or {})
        hops = 0

        with httpx.Client(follow_redirects=False, timeout=timeout) as client:
            while hops <= active_policy.max_redirects:
                clean_url, host = validate_destination_url(current_url, active_policy)

                resp = client.request(
                    method,
                    clean_url,
                    headers=req_headers,
                    **kwargs,
                )

                # Check for redirect status codes
                if resp.is_redirect and "location" in resp.headers:
                    hops += 1
                    location = resp.headers["location"].strip()
                    next_url = urllib.parse.urljoin(clean_url, location)

                    # Strip Authorization if redirecting across different hostnames or downgrading to HTTP
                    next_parts = urllib.parse.urlsplit(next_url)
                    curr_parts = urllib.parse.urlsplit(clean_url)

                    if next_parts.hostname != curr_parts.hostname or next_parts.scheme != curr_parts.scheme:
                        req_headers.pop("Authorization", None)
                        req_headers.pop("authorization", None)

                    current_url = next_url
                    continue

                # Enforce response body size limit
                content = resp.content
                if len(content) > limit_bytes:
                    raise ValueError(f"Response body exceeded limit of {limit_bytes} bytes.")

                return resp

            raise SSRFBlockedError(f"Too many redirects (exceeded limit of {active_policy.max_redirects}).")

    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        return self.request("POST", url, **kwargs)
