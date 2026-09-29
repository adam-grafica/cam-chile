# 📹 CAM-CHILE

> Plataforma OSINT de cámaras en tiempo real - Chile (escalable a global)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)

## 🎯 Objetivo

Descubrir, geolocalizar y visualizar **cámaras en tiempo real** de Chile (YouTube Live, RTSP, webcams públicas, municipalidades) en un mapa interactivo. **Zero budget, 100% open-source.**

## 🏗️ Arquitectura Multi-Agente

```
┌─────────────────────────────────────────────────────────────┐
│                    ORQUESTADOR PRINCIPAL                     │
│              (FastAPI Backend + SQLite DB)                   │
└─────────────────────────────────────────────────────────────┘
         ▲              ▲              ▲              ▲
         │              │              │              │
┌────────┴───┐  ┌──────┴──────┐  ┌───┴──────┐  ┌───┴────────┐
│ SCRAPER    │  │ OSINT       │  │ RTSP     │  │ FRONTEND   │
│ AGENT      │  │ ENRICHER    │  │ BRIDGE   │  │ LEAFLET    │
│ (Python)   │  │ (Nominatim) │  │ (FFmpeg) │  │ (React)    │
└────────────┘  └─────────────┘  └──────────┘  └────────────┘
```

## 📂 Estructura del Proyecto

```
cam-chile/
├── backend/
│   ├── app.py              # FastAPI + endpoints
│   ├── scraper/
│   │   ├── google_dorks.py # Agente 1: Google Dorks
│   │   ├── masscan_rtsp.py # Agente 2: RTSP Scanner
│   │   └── youtube_live.py # Agente 3: YouTube Live
│   ├── osint/
│   │   └── geolocate.py    # Nominatim geocoding
│   └── db/
│       └── cameras.db      # SQLite
├── frontend/
│   ├── index.html          # Leaflet.js + HLS.js
│   └── player.js           # Player unificado
├── scripts/
│   ├── seed_chile.py       # Cámaras iniciales
│   └── deploy.sh           # Auto-deploy Oracle Cloud
└── requirements.txt
```

## 🚀 Roadmap MVP

| Fase | Tarea | Estado | PR |
|------|-------|--------|-----|
| 1 | Backend FastAPI + DB SQLite | ⏳ Pendiente | - |
| 2 | Scraper YouTube (sin API key) | ⏳ Pendiente | - |
| 3 | Scraper Google Dorks | ⏳ Pendiente | - |
| 4 | Scraper Masscan RTSP | ⏳ Pendiente | - |
| 5 | OSINT Enricher (Nominatim) | ⏳ Pendiente | - |
| 6 | Frontend Leaflet + Player | ⏳ Pendiente | - |
| 7 | Deploy en Oracle Cloud | ⏳ Pendiente | - |

## 🛠️ Tecnologías

- **Backend**: FastAPI, SQLite, httpx, python-masscan
- **Frontend**: Leaflet.js, HLS.js, vanilla JS
- **Scraping**: tubescrape, google-dorks, masscan
- **Geolocalización**: Nominatim (OpenStreetMap)
- **Deploy**: Oracle Cloud (Free Tier), Docker

## 📚 Referencias Técnicas

- Google Dorks: https://github.com/rootac355/IP-cams-dork-list
- Masscan: https://pypi.org/project/python-masscan/
- BIANEYE: https://biantech.org/bianeye
- YouTube Scraper: https://github.com/omkarcloud/youtube-scraper

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles.

---

**Hecho con ❤️ por Adam Gráfica**
