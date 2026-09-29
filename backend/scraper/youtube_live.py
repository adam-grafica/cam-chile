"""
Agente Scraper: YouTube Live (sin API key)
Usa tubescrape para buscar streams en vivo de Chile
"""
import asyncio
import httpx
from typing import List, Dict

class YouTubeLiveScraper:
    """Scraper de YouTube Live sin API key"""
    
    def __init__(self):
        self.base_url = "https://www.youtube.com/results"
    
    async def search_live(self, query: str, location: str = "Chile") -> List[Dict]:
        """
        Busca streams en vivo en YouTube
        
        Args:
            query: Término de búsqueda (ej: "cámara en vivo Santiago")
            location: Ubicación para filtrar (default: Chile)
        
        Returns:
            Lista de cámaras con metadata
        """
        cameras = []
        search_query = f"{query} {location} en vivo"
        
        # Nota: tubescrape requiere instalación
        # pip install tubescrape
        try:
            from tubescrape import YouTube
            yt = YouTube()
            results = yt.search(search_query, filters={"type": "live", "upload_date": "live"})
            
            for video in results[:20]:  # Máximo 20 resultados
                cameras.append({
                    "name": video.get("title", "Cámara sin título"),
                    "lat": None,  # Se enriquece con OSINT
                    "lon": None,
                    "feed_type": "youtube",
                    "stream_url": f"https://www.youtube.com/watch?v={video.get('id')}",
                    "address": f"{query}, {location}"
                })
        except ImportError:
            print("⚠️ tubescrape no instalado. Usando fallback con httpx...")
            # Fallback: búsqueda básica sin API
            cameras = await self._fallback_search(search_query)
        
        return cameras
    
    async def _fallback_search(self, query: str) -> List[Dict]:
        """Fallback sin tubescrape (búsqueda básica)"""
        # Aquí iría scraping directo con httpx + BeautifulSoup
        # Por ahora retorna placeholder
        return [
            {
                "name": f"YouTube Live: {query}",
                "lat": None,
                "lon": None,
                "feed_type": "youtube",
                "stream_url": f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}",
                "address": "Chile"
            }
        ]

# Test
if __name__ == "__main__":
    async def main():
        scraper = YouTubeLiveScraper()
        results = await scraper.search_live("tráfico Santiago")
        print(f"📹 Cámaras encontradas: {len(results)}")
        for cam in results:
            print(f"  - {cam['name']}: {cam['stream_url']}")
    
    asyncio.run(main())
