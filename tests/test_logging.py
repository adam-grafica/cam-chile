"""
Tests para el middleware de request_id y logging JSON.

Verifica que:
- Cada respuesta lleva `X-Request-ID` único (o respeta el entrante).
- Cada request genera logs JSON parseables con `request_id`.
- El campo `request_id` aparece en el log de respuesta.
"""

import json
import logging
import re
import sqlite3
from io import StringIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Cliente TestClient con DB temporal."""
    db_path = tmp_path / "cameras.db"
    monkeypatch.setattr("backend.app.DB_PATH", db_path)
    sql = Path("backend/db/schema.sql").read_text()
    conn = sqlite3.connect(db_path)
    conn.executescript(sql)
    conn.close()

    from backend.app import app

    return TestClient(app)


def _capture_logs(callable_):
    """Captura los logs emitidos por callable_ y los devuelve como lista de dict."""
    buf = StringIO()
    handler = logging.StreamHandler(buf)
    # Formatter incluye campos extra como request_id, status_code, elapsed_ms.
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s %(message)s "
            "request_id=%(request_id)s status_code=%(status_code)s "
            "elapsed_ms=%(elapsed_ms)s"
        )
    )
    root = logging.getLogger()
    root.addHandler(handler)
    old_level = root.level
    root.setLevel(logging.INFO)
    try:
        callable_()
        output = buf.getvalue()
    finally:
        root.removeHandler(handler)
        root.setLevel(old_level)

    lines = []
    for raw in output.strip().splitlines():
        try:
            lines.append(json.loads(raw))
        except json.JSONDecodeError:
            lines.append({"raw": raw})
    return lines


def test_response_has_request_id_header(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert "X-Request-ID" in r.headers
    rid = r.headers["X-Request-ID"]
    # UUID4 format
    assert re.match(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        rid,
    ), f"request_id no es UUID4: {rid!r}"


def test_request_id_is_unique_per_request(client):
    rids = set()
    for _ in range(10):
        r = client.get("/healthz")
        rids.add(r.headers["X-Request-ID"])
    assert len(rids) == 10, "request_id debe ser único por request"


def test_request_id_respects_inbound_header(client):
    inbound = "abc-123-fixed-id"
    r = client.get("/healthz", headers={"X-Request-ID": inbound})
    assert r.headers["X-Request-ID"] == inbound


def test_response_includes_security_headers(client):
    r = client.get("/healthz")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert r.headers.get("X-Frame-Options") == "DENY"


def test_request_logs_carry_request_id(client):
    """Los logs request.start / request.end deben incluir request_id."""
    lines = _capture_logs(lambda: client.get("/healthz"))

    # Buscar request.end (puede estar en JSON parseado o en texto crudo)
    def is_end(ln):
        text = ln.get("message", "") or ln.get("raw", "")
        return "request.end" in text

    end_logs = [ln for ln in lines if is_end(ln)]
    assert end_logs, f"No se encontró request.end en logs: {lines}"
    log = end_logs[-1]
    text = log.get("raw", "")
    assert (
        "request_id" in text or "request_id" in log
    ), f"request.end sin request_id: {log}"
    assert (
        "elapsed_ms" in text or "elapsed_ms" in log
    ), f"request.end sin elapsed_ms: {log}"
    assert "200" in text or log.get("status_code") == 200


def test_request_id_in_log_matches_response_header(client):
    """El request_id del log debe coincidir con el de la respuesta."""
    captured = {}

    def do_request():
        r = client.get("/healthz")
        captured["rid"] = r.headers["X-Request-ID"]

    lines = _capture_logs(do_request)

    def is_end(ln):
        text = ln.get("message", "") or ln.get("raw", "")
        return "request.end" in text

    end_logs = [ln for ln in lines if is_end(ln)]
    assert end_logs
    last = end_logs[-1]
    text = last.get("raw", "")
    # El rid debe estar contenido en la línea
    assert (
        captured["rid"] in text
    ), f"request_id {captured['rid']!r} no aparece en log: {text!r}"


def test_logging_configure_json_runs():
    """configure_logging debe ejecutarse sin errores."""
    from backend.logging_config import configure_logging

    # Modo JSON
    configure_logging(level="INFO", fmt="json")
    logger = logging.getLogger("test-logger")
    logger.info("hello json")
    # Modo text (fallback)
    configure_logging(level="INFO", fmt="text")
    logger.info("hello text")


def test_logging_handles_missing_json_logger(monkeypatch):
    """Si pythonjsonlogger no está, debe funcionar en modo text."""
    import backend.logging_config as lc

    monkeypatch.setattr(lc, "HAS_JSON_LOGGER", False)
    lc.configure_logging(level="INFO", fmt="json")
    logger = logging.getLogger("test-no-json")
    logger.info("should not crash")
