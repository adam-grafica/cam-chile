"""
CAM-CHILE — Backend FastAPI

API mínima y segura para servir el catálogo curado de cámaras públicas/autorizadas
de Chile. Endpoints:
  - GET  /          → estado
  - GET  /healthz   → liveness
  - GET  /readyz    → readiness (DB OK + esquema válido)
  - GET  /api/cameras → listado según el esquema canónico (issue #2)
  - POST /api/cameras → agrega cámara (con SSRF guard)
  - POST /api/validate → valida una URL contra allowlist + SSRF guard
  - GET  /api/agents/jobs → estado de jobs (placeholder)
"""

from __future__ import annotations

import logging
import sqlite3
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl

from backend.db.migrate import main as run_migrations
from backend.security.allowlist import is_host_allowed
from backend.security.ssrf import SSRFError, assert_safe_url
from backend.settings import get_settings

# ─── Logging ────────────────────────────────────────────────────────────────
logger = logging.getLogger("camchile")

DB_PATH = Path("backend/db/cameras.db")


def _configure_logging(fmt: str, level: str) -> None:
    if fmt == "json":
        try:
            from pythonjsonlogger import jsonlogger

            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                jsonlogger.JsonFormatter(
                    "%(asctime)s %(levelname)s %(name)s %(message)s"
                )
            )
        except ImportError:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            )
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
    logger.handlers = [handler]
    logger.setLevel(level.upper())


# ─── Lifespan ───────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    _configure_logging(settings.log_format, settings.log_level)
    # Aplicar migraciones al arranque
    try:
        run_migrations()
        logger.info("migrations applied")
    except Exception as e:  # pragma: no cover
        logger.error("migration failed", extra={"error": str(e)})
    yield


app = FastAPI(
    title="CAM-CHILE API",
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)


# ─── Middleware ──────────────────────────────────────────────────────────────
@app.middleware("http")
async def _security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["X-Frame-Options"] = "DENY"
    return resp


def _cors_origins() -> list[str]:
    s = get_settings()
    return s.allowed_origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


# ─── DB ─────────────────────────────────────────────────────────────────────
def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


# ─── Schemas ────────────────────────────────────────────────────────────────
class Camera(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    country: str = Field(default="CL", min_length=2, max_length=2)
    region: str | None = None
    city: str | None = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    source_name: str = Field(..., min_length=1, max_length=200)
    source_url: HttpUrl
    stream_type: str = Field(..., pattern="^(youtube|youtube_embed|hls|mp4|iframe)$")
    stream_url: HttpUrl
    public_status: str = Field(
        default="declared_public", pattern="^(declared_public|unknown|revoked)$"
    )
    license_or_terms_url: HttpUrl | None = None


class ValidateURLIn(BaseModel):
    url: HttpUrl


class ValidateURLOut(BaseModel):
    url: str
    host_allowed: bool
    ssrf_safe: bool
    reason: str | None = None


# ─── Endpoints ──────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "online", "project": "CAM-CHILE", "version": "1.1.0"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    try:
        c = _conn()
        row = c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cameras'"
        ).fetchone()
        c.close()
        if not row:
            return JSONResponse(
                {"status": "not_ready", "reason": "no schema"}, status_code=503
            )
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse({"status": "not_ready", "reason": str(e)}, status_code=503)


@app.get("/api/cameras")
def list_cameras():
    c = _conn()
    rows = c.execute(
        """SELECT id, name, country, region, city, latitude, longitude,
                  source_name, source_url, stream_type, stream_url,
                  public_status, license_or_terms_url, last_checked_at
           FROM cameras
           ORDER BY country, region, city, name"""
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]


@app.post("/api/cameras")
def add_camera(cam: Camera):
    # Guard SSRF en TODAS las URLs externas que se persisten
    try:
        assert_safe_url(str(cam.source_url))
        assert_safe_url(str(cam.stream_url))
        if cam.license_or_terms_url:
            assert_safe_url(str(cam.license_or_terms_url))
    except SSRFError as e:
        raise HTTPException(400, f"SSRF guard: {e}") from e

    c = _conn()
    try:
        cur = c.execute(
            """INSERT INTO cameras
               (name, country, region, city, latitude, longitude,
                source_name, source_url, stream_type, stream_url,
                public_status, license_or_terms_url, last_checked_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ','now'))""",
            (
                cam.name,
                cam.country,
                cam.region,
                cam.city,
                cam.latitude,
                cam.longitude,
                cam.source_name,
                str(cam.source_url),
                cam.stream_type,
                str(cam.stream_url),
                cam.public_status,
                str(cam.license_or_terms_url) if cam.license_or_terms_url else None,
            ),
        )
        c.commit()
        new_id = cur.lastrowid
    except sqlite3.IntegrityError as e:
        c.close()
        raise HTTPException(409, f"Duplicate or invalid: {e}") from e
    c.close()
    return {"status": "created", "id": new_id}


@app.post("/api/validate", response_model=ValidateURLOut)
def validate_url(payload: ValidateURLIn):
    url = str(payload.url)
    host_ok = is_host_allowed(url)
    reason: str | None = None
    ssrf_ok = False
    try:
        assert_safe_url(url)
        ssrf_ok = True
    except SSRFError as e:
        reason = str(e)
        ssrf_ok = False
    return ValidateURLOut(
        url=url, host_allowed=host_ok, ssrf_safe=ssrf_ok, reason=reason
    )


@app.get("/api/agents/jobs")
def jobs_status():
    return {
        "scraper": "idle",
        "osint": "idle",
        "rtsp_bridge": "disabled",  # fuera de alcance
    }


# ─── Local runner ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.env == "development",
    )
