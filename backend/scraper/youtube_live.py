"""
Agente Scraper: YouTube Live (sin tubescrape).

Usa únicamente la API pública oEmbed de YouTube (sin autenticación).
NO scrapea páginas de búsqueda. NO usa masscan ni bypass.

Para descubrir canales, el Orchestrator mantiene un catálogo curado
(`catalog/sources/chile.yaml`) con los IDs de canal validados manualmente.
Este agente solo verifica que un video/canal sea público y responde oEmbed.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OEMBED_URL = "https://www.youtube.com/oembed"
TIMEOUT = 10.0


class YouTubePublicError(ValueError):
    """El recurso de YouTube no es accesible públicamente o no existe."""


def _is_video_public(video_url: str) -> dict[str, Any]:
    """
    Usa oEmbed (sin auth) para verificar que un video de YouTube es público.

    oEmbed devuelve 200 si el video existe y permite embed. Devuelve 401/404
    si es privado, restringido por país, o no existe.

    Returns:
        dict con {title, author_name, author_url, thumbnail_url, ...}

    Raises:
        YouTubePublicError si no es público.
    """
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(
                OEMBED_URL,
                params={"url": video_url, "format": "json"},
            )
    except httpx.HTTPError as e:
        raise YouTubePublicError(f"Network error: {e}") from e

    if resp.status_code == 401:
        raise YouTubePublicError("Video is private or restricted")
    if resp.status_code == 404:
        raise YouTubePublicError("Video not found")
    if resp.status_code != 200:
        raise YouTubePublicError(f"oEmbed returned {resp.status_code}")

    data = resp.json()
    if not data.get("title"):
        raise YouTubePublicError("oEmbed response missing title")
    return data


def verify_catalog_entry(cam: dict[str, Any]) -> dict[str, Any]:
    """
    Verifica que una entrada del catálogo sigue accesible y pública.

    Args:
        cam: dict con al menos 'stream_url' y 'stream_type'.

    Returns:
        El mismo dict con 'last_checked_at', 'public_status' actualizados.
    """
    if cam.get("stream_type") not in ("youtube", "youtube_embed"):
        return cam  # solo verificamos YouTube en este agente
    meta = _is_video_public(cam["stream_url"])
    cam["verified_title"] = meta.get("title")
    cam["verified_author"] = meta.get("author_name")
    cam["verified_thumbnail"] = meta.get("thumbnail_url")
    cam["public_status"] = "declared_public"
    return cam


def main() -> int:
    """CLI: verificar un video de YouTube público."""
    import argparse
    import json
    from datetime import datetime, timezone

    p = argparse.ArgumentParser(
        description="Verifica que un video de YouTube es público"
    )
    p.add_argument("url", help="URL del video de YouTube")
    args = p.parse_args()

    try:
        meta = _is_video_public(args.url)
    except YouTubePublicError as e:
        print(f"❌ {e}")
        return 1
    out = {
        "url": args.url,
        "title": meta.get("title"),
        "author": meta.get("author_name"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
