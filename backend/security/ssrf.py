"""
SSRF guard: bloquea requests a rangos privados, loopback y link-local.
Previene acceso a recursos internos desde endpoints que aceptan URLs externas.

Uso:
    from backend.security.ssrf import assert_safe_url
    assert_safe_url(url)            # raise SSRFError si no es seguro
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from .allowlist import is_host_allowed


class SSRFError(ValueError):
    """URL no permitida: rango privado, host no permitido o esquema inválido."""


# Solo http(s). Bloquea file://, ftp://, gopher://, etc.
ALLOWED_SCHEMES: frozenset[str] = frozenset({"http", "https"})


def _resolve(host: str) -> list[str]:
    """Resuelve un host a todas sus IPs (anti-DNS-rebinding)."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise SSRFError(f"DNS resolution failed: {e}") from e
    return list({i[4][0] for i in infos})


def _is_private_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_unspecified
        or addr.is_reserved
    )


def assert_safe_url(url: str) -> None:
    """
    Verifica que `url` es segura para hacer fetch server-side.

    Reglas:
      1. Scheme ∈ {http, https}.
      2. Host debe estar en la allowlist.
      3. Host no resuelve a una IP privada / loopback / link-local / multicast.
    """
    try:
        parsed = urlparse(url)
    except ValueError as e:
        raise SSRFError(f"Invalid URL: {e}") from e

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise SSRFError(f"Scheme not allowed: {parsed.scheme!r}")

    host = (parsed.hostname or "").lower()
    if not host:
        raise SSRFError("URL has no host")

    if not is_host_allowed(url):
        raise SSRFError(f"Host not in allowlist: {host}")

    # Anti-DNS-rebinding: verificar TODAS las IPs que resuelve
    for ip in _resolve(host):
        if _is_private_ip(ip):
            raise SSRFError(f"Host resolves to private IP: {ip}")