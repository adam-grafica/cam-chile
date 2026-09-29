"""
Seed Script: Cámaras iniciales de Chile
Agrega cámaras manualmente curadas para el MVP
"""
import httpx
import asyncio

BASE_URL = "http://localhost:8000"

CAMARAS_CHILE = [
    # Santiago - YouTube Live
    {
        "name": "TVN 24h - Santiago Centro",
        "lat": -33.4489,
        "lon": -70.6693,
        "feed_type": "youtube",
        "stream_url": "https://www.youtube.com/watch?v=VjB_Oe3xYKw",
        "address": "Santiago, RM"
    },
    {
        "name": "24 Horas - Plaza Baquedano",
        "lat": -33.4372,
        "lon": -70.6206,
        "feed_type": "youtube",
        "stream_url": "https://www.youtube.com/watch?v=example",
        "address": "Providencia, Santiago"
    },
    # Valparaíso
    {
        "name": "Valparaíso - Puerto",
        "lat": -33.0472,
        "lon": -71.6127,
        "feed_type": "youtube",
        "stream_url": "https://www.youtube.com/results?search_query=valparaiso+puerto+en+vivo",
        "address": "Valparaíso, Valparaíso"
    },
    # Viña del Mar
    {
        "name": "Viña del Mar - Reñaca",
        "lat": -33.0120,
        "lon": -71.5519,
        "feed_type": "youtube",
        "stream_url": "https://www.youtube.com/results?search_query=viña+del+mar+reñaca+en+vivo",
        "address": "Viña del Mar, Valparaíso"
    },
    # Pucón
    {
        "name": "Pucón - Volcán Villarrica",
        "lat": -39.4167,
        "lon": -71.9333,
        "feed_type": "youtube",
        "stream_url": "https://www.youtube.com/results?search_query=pucon+volcan+villarrica+en+vivo",
        "address": "Pucón, Araucanía"
    },
    # Punta Arenas
    {
        "name": "Punta Arenas - Estrecho de Magallanes",
        "lat": -53.1638,
        "lon": -70.9171,
        "feed_type": "youtube",
        "stream_url": "https://www.youtube.com/results?search_query=punta+arenas+estrecho+magallanes",
        "address": "Punta Arenas, Magallanes"
    },
    # Atacama - ALMA
    {
        "name": "ALMA Observatory - Atacama",
        "lat": -23.0294,
        "lon": -67.7528,
        "feed_type": "youtube",
        "stream_url": "https://www.youtube.com/results?search_query=alma+observatory+live",
        "address": "San Pedro de Atacama, Antofagasta"
    },
]

async def seed_cameras():
    """Agrega cámaras a la DB vía API"""
    async with httpx.AsyncClient() as client:
        for cam in CAMARAS_CHILE:
            try:
                resp = await client.post(f"{BASE_URL}/api/cameras", json=cam)
                if resp.status_code == 200:
                    print(f"✅ Agregada: {cam['name']}")
                else:
                    print(f"⚠️ Error {resp.status_code}: {cam['name']}")
            except Exception as e:
                print(f"❌ Error: {cam['name']} - {e}")

if __name__ == "__main__":
    print("🚀 Seed: Agregando cámaras de Chile...")
    asyncio.run(seed_cameras())
    print("✅ Seed completado!")
