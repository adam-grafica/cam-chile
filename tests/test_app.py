"""
Tests del backend FastAPI: healthz, readyz, validate, CORS, schema response.
"""

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "cameras.db"
    monkeypatch.setattr("backend.app.DB_PATH", db_path)
    # Ejecuta migración contra la DB temporal
    sql = Path("backend/db/schema.sql").read_text()
    conn = sqlite3.connect(db_path)
    conn.executescript(sql)
    conn.close()

    from backend.app import app

    return TestClient(app)


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["project"] == "CAM-CHILE"


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_readyz_ok(client):
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


def test_security_headers_present(client):
    r = client.get("/")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert r.headers.get("X-Frame-Options") == "DENY"


def test_cors_not_wildcard_with_credentials(client):
    """La config CORS nunca debe tener '*' como origin."""
    from backend.app import _cors_origins

    origins = _cors_origins()
    assert "*" not in origins
    for o in origins:
        assert o.startswith(("http://", "https://"))


def test_validate_url_youtube_ok(client):
    r = client.post(
        "/api/validate", json={"url": "https://www.youtube.com/watch?v=abc"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["host_allowed"] is True
    assert data["ssrf_safe"] is True
    assert data["reason"] is None


def test_validate_url_rejects_evil_host(client):
    r = client.post("/api/validate", json={"url": "https://evil.example.com/x"})
    assert r.status_code == 200
    data = r.json()
    assert data["host_allowed"] is False
    assert data["ssrf_safe"] is False
    assert "not in allowlist" in (data["reason"] or "")


def test_validate_url_rejects_file_scheme(client):
    r = client.post("/api/validate", json={"url": "file:///etc/passwd"})
    # Pydantic HttpUrl rechaza con 422 antes de llegar a la lógica
    assert r.status_code == 422


def test_add_camera_inserts(client):
    payload = {
        "name": "ALMA Observatory",
        "country": "CL",
        "region": "Antofagasta",
        "city": "San Pedro de Atacama",
        "latitude": -23.0294,
        "longitude": -67.7528,
        "source_name": "ALMA Observatory",
        "source_url": "https://www.almaobservatory.org/en/webcams/",
        "stream_type": "youtube_embed",
        "stream_url": "https://www.youtube.com/watch?v=abc",
        "public_status": "declared_public",
        "license_or_terms_url": "https://www.almaobservatory.org/en/terms-of-use/",
    }
    r = client.post("/api/cameras", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] == "created"


def test_add_camera_rejects_bad_host(client):
    payload = {
        "name": "x",
        "latitude": 0,
        "longitude": 0,
        "source_name": "x",
        "source_url": "https://evil.example.com/x",
        "stream_type": "youtube_embed",
        "stream_url": "https://www.youtube.com/watch?v=x",
        "public_status": "declared_public",
    }
    r = client.post("/api/cameras", json=payload)
    assert r.status_code == 400
    assert "SSRF" in r.json()["detail"]


def test_list_cameras_returns_canonic_keys(client):
    r = client.get("/api/cameras")
    assert r.status_code == 200
    # vacía inicialmente
    assert r.json() == []
    # Insertamos una
    payload = {
        "name": "x",
        "latitude": 0,
        "longitude": 0,
        "source_name": "x",
        "source_url": "https://www.youtube.com/watch?v=x",
        "stream_type": "youtube_embed",
        "stream_url": "https://www.youtube.com/watch?v=x",
        "public_status": "declared_public",
    }
    client.post("/api/cameras", json=payload)
    r = client.get("/api/cameras")
    assert len(r.json()) == 1
    keys = set(r.json()[0].keys())
    assert {
        "country",
        "region",
        "city",
        "latitude",
        "longitude",
        "source_name",
        "source_url",
        "stream_type",
        "stream_url",
        "public_status",
        "license_or_terms_url",
        "last_checked_at",
    }.issubset(keys)
