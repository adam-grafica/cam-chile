"""
Seed script: agrega cámaras mínimas con el esquema canónico.
Todas las cámaras aquí deben estar validadas por el agente catalog (issue #3).
Este script es un placeholder seguro mientras se curan las entradas reales.

Uso:
    python scripts/seed_chile.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Permitir import de backend.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Entradas curadas como "declared_public" para MVP.
# El campo source_url debe apuntar a la página oficial del proveedor.
CAMARAS_CHILE: list[dict] = [
    {
        "name": "ALMA Observatory Live",
        "country": "CL",
        "region": "Antofagasta",
        "city": "San Pedro de Atacama",
        "latitude": -23.0294,
        "longitude": -67.7528,
        "source_name": "ALMA Observatory",
        "source_url": "https://www.almaobservatory.org/en/webcams/",
        "stream_type": "youtube_embed",
        # Pendiente de validación manual por catalog (issue #3):
        "stream_url": "https://www.youtube.com/watch?v=PENDING_VALIDATION",
        "public_status": "unknown",
        "license_or_terms_url": "https://www.almaobservatory.org/en/terms-of-use/",
    },
]


async def seed_cameras() -> int:
    added = 0
    async with httpx.AsyncClient(timeout=10.0) as client:
        for cam in CAMARAS_CHILE:
            try:
                resp = await client.post(f"{BASE_URL}/api/cameras", json=cam)
                if resp.status_code in (200, 201):
                    print(f"✅ {cam['name']}")
                    added += 1
                else:
                    print(f"⚠️  {resp.status_code} {cam['name']}: {resp.text}")
            except httpx.HTTPError as e:
                print(f"❌ {cam['name']}: {e}")
    return added


def main() -> int:
    print("🚀 Seed CAM-CHILE (placeholder curado, ver issue #3)…")
    n = asyncio.run(seed_cameras())
    print(f"✅ Listo. {n} cámaras agregadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())