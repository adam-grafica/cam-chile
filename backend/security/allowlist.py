"""
Allowlist de hosts para URLs externas.

Por defecto se lee de la variable de entorno ALLOWED_HOSTS (lista separada por comas).
Si está vacía, se usa una allowlist mínima para YouTube.

Uso:
    from backend.security.allowlist import is_host_allowed, get_allowed_hosts
    if not is_host_allowed(url):
        raise HTTPException(400, "Host not in allowlist")
"""
from __future__ import annotations

import os
from urllib.parse import urlparse

DEFAULT_HOSTS: frozenset[str] = frozenset(
    {
        # YouTube (oEmbed, embeds)
        "youtube.com",
        "www.youtube.com",
        "youtu.be",
        "youtube-nocookie.com",
        "www.youtube-nocookie.com",
        # Webcams turísticas públicas
        "webcams.travel",
        "skylinewebcams.com",
        # Fuentes oficiales chilenas declaradas
        "almaobservatory.org",
        "www.almaobservatory.org",
    }
)


def get_allowed_hosts() -> frozenset[str]:
    raw = os.getenv("ALLOWED_HOSTS", "").strip()
    if not raw:
        return DEFAULT_HOSTS
    return frozenset(h.strip().lower() for h in raw.split(",") if h.strip())


def is_host_allowed(url: str) -> bool:
    """True si la `url` tiene scheme http(s) y host en la allowlist."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme.lower() not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower()
    if not host:
        return False
    allowed = get_allowed_hosts()
    # match exacto o subdomain (ej. "www.youtube.com" matches "youtube.com")
    if host in allowed:
        return True
    for h in allowed:
        if host.endswith("." + h):
            return True
    return False