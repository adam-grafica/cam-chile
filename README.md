# 📹 CAM-CHILE

> Plataforma minimalista para catalogar y visualizar **cámaras y transmisiones explícitamente públicas o autorizadas** de Chile. Diseñada desde el inicio para expansión global.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)

## 🎯 Objetivo

Catalogar, normalizar y visualizar cámaras y transmisiones en vivo **explícitamente públicas o autorizadas** de Chile (YouTube Live vía oEmbed, ALMA Observatory, portales municipales declarados, operadores oficiales) en un mapa interactivo. **Zero budget, 100% open-source.**

> **Alcance seguro:** solo fuentes públicas/autorizadas. **NO** se realiza escaneo de Internet, descubrimiento activo de dispositivos, fuerza bruta, bypass de autenticación, ni acceso a cámaras privadas. Ver `AGENT_OPERATING_PROMPT.md` §Límites no negociables.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                ORQUESTADOR (FastAPI + SQLite)                │
│              GET /api/cameras · POST /api/validate           │
└─────────────────────────────────────────────────────────────┘
         ▲                              ▲
         │                              │
┌────────┴────────────┐    ┌───────────┴─────────────┐
│ CATALOG (curado)    │    │ SECURITY                │
│ catalog/sources/*.yaml   │ allowlist · SSRF guard · secrets scan
└─────────────────────┘    └─────────────────────────┘
         ▲                              ▲
         │                              │
┌────────┴──────────────────────────────┴──────────────┐
│  FRONTEND (Leaflet + filtros + reproductor unificado)   │
└────────────────────────────────────────────────────────┘
```

## 📂 Estructura del Proyecto

```
cam-chile/
├── backend/
│   ├── app.py                      # FastAPI + endpoints hardened
│   ├── settings.py                 # Config por env (pydantic-settings)
│   ├── db/
│   │   ├── schema.sql              # Esquema canónico
│   │   ├── migrate.py              # Runner de migraciones
│   │   └── migrations/
│   │       └── 001_align_to_spec.sql
│   ├── security/
│   │   ├── allowlist.py            # ALLOWED_HOSTS
│   │   └── ssrf.py                 # Guard contra rangos privados
│   └── scraper/
│       └── youtube_live.py         # Verificación oEmbed (sin auth)
├── catalog/
│   ├── sources/_template.yaml      # (issue #3) Entradas curadas
│   └── validate.py                 # (issue #3) Validador del catálogo
├── frontend/
│   ├── index.html                  # Markup accesible
│   ├── config.js                   # Lee API_BASE desde <meta>
│   ├── map.js                      # Leaflet + estado
│   ├── player.js                   # Reproductor por proveedor
│   ├── filters.js
│   └── styles.css
├── scripts/
│   ├── bootstrap.sh                # Bootstrap reproducible OrcaDev
│   ├── add-worktree.sh             # Crea worktree de un agente
│   ├── cleanup-worktree.sh         # Limpia worktree mergeado
│   └── seed_chile.py
├── tests/                          # pytest + (e2e en issue #6)
├── docs/adr/                       # Decisiones arquitectónicas
├── AGENT_OPERATING_PROMPT.md       # Fuente de verdad operativa
├── requirements.txt                # Backend
├── requirements-dev.txt            # Backend + linters + pre-commit
├── Makefile                        # dev · test · lint · seed · migrate
├── .env.example                    # Variables documentadas
├── .pre-commit-config.yaml         # gitleaks + ruff + black
└── .gitleaks.toml                  # Baseline de secretos
```

## 🚦 Estado de fases

| Fase | Descripción | Estado | Issues |
|---|---|---|---|
| F1 | Base técnica + seguridad + esquema | ✅ este PR (#2) | #2, #9 |
| F2 | Catálogo curado Chile | ⏳ | #3 |
| F3 | Normalización / dedup | ⏳ | #4 |
| F4 | Mapa + reproductor + a11y | ⏳ | #5 |
| F5 | Tests + SSRF + CI | ⏳ | #6 |
| F6 | Docker + health + CI/CD | ⏳ | #7 |
| F7 | Conector multi-país | ⏳ | #8 |

## 🛠️ Stack

- **Backend**: FastAPI 0.115, Pydantic 2, pydantic-settings, httpx, SQLite
- **Scraping**: google-api-python-client (YouTube Data API v3 con key opcional) + oEmbed sin auth
- **Seguridad**: SSRF guard con resolución DNS anti-rebinding, allowlist configurable
- **Frontend**: Leaflet 1.9.4, HTML/CSS/JS vanilla, accesible (WCAG AA)
- **Logging**: python-json-logger
- **Tests**: pytest, pytest-asyncio, pytest-cov, respx (mock httpx)
- **Lint/format**: ruff, black, isort
- **Pre-commit**: gitleaks, detect-secrets, ruff, black

## 🧪 Desarrollo local

```bash
# 0. Variables de entorno (necesario antes de cualquier script/*)
source scripts/env.sh
#  → exporta CAM_CHILE_ROOT (default /opt/orca/cam-chile), CAM_CHILE_REPO, CAM_CHILE_WORKTREES

# 1. Bootstrap (clona repo y sincroniza main; usa $CAM_CHILE_ROOT)
bash scripts/bootstrap.sh

# 2. Setup
make install

# 3. Configurar entorno
cp .env.example .env

# 4. Migrar DB
make migrate

# 5. Levantar backend
make dev

# 6. Tests
make test                                  # pytest + coverage ≥80%
bash scripts/tests/test_bootstrap.sh       # test del script bootstrap (hermético)
bash scripts/tests/test_add_worktree.sh    # test de add-worktree (hermético)
bash scripts/tests/test_cleanup_worktree.sh # test de cleanup-worktree (hermético)

# 7. Servir frontend (en otra terminal)
cd frontend && python3 -m http.server 8080
```

### Worktrees de agentes

```bash
# Crear worktree para un agente
bash scripts/add-worktree.sh <agent> <issue-n> <slug>
#   ej: bash scripts/add-worktree.sh catalog 3 curated-chile-sources
#   resultado:
#     - worktree: $CAM_CHILE_ROOT/worktrees/catalog-issue-3
#     - rama:     agent/catalog/issue-3-curated-chile-sources

# Limpiar worktree tras merge
bash scripts/cleanup-worktree.sh <agent> <issue-n> <slug>
```

## 🤖 Coordinación multi-agente

`AGENT_OPERATING_PROMPT.md` es la fuente de verdad. Cada agente (orchestrator, catalog, metadata, frontend, qa-security, devops) trabaja en su propia rama y worktree. El Orchestrator crea el worktree y rama antes de delegar:

```bash
bash scripts/add-worktree.sh <agent> <issue-n> <slug>
```

Tras merge:

```bash
bash scripts/cleanup-worktree.sh <agent> <issue-n> <slug>
```

## 📚 Referencias externas (autorizadas)

- [YouTube oEmbed](https://www.youtube.com/oembed) — verificación pública sin auth.
- [YouTube Data API v3](https://developers.google.com/youtube/v3) — solo si se declara `YOUTUBE_API_KEY`.
- [OpenStreetMap](https://www.openstreetmap.org/) — tiles base.
- [Leaflet](https://leafletjs.com/) — librería de mapas.
- [Nominatim](https://nominatim.org/) — geocoding (opcional, no usado por defecto).

## 📄 Licencia

MIT — ver `LICENSE`.