"""
Configuración de logging JSON para CAM-CHILE.

Formatea cada línea como JSON parseable por `jq` con campos:
- asctime: ISO8601 timestamp
- level: nivel de log (INFO, WARNING, ERROR, etc.)
- name: nombre del logger
- message: mensaje
- request_id: UUID por request (cuando aplica)
- (excepciones: exc_info serializado)

Uso:
    from backend.logging_config import configure_logging
    configure_logging(level="INFO", fmt="json")
    logger = logging.getLogger("camchile")
    logger.info("hello", extra={"request_id": "abc-123"})
"""

from __future__ import annotations

import logging
import sys
from typing import Any

try:
    from pythonjsonlogger import jsonlogger

    HAS_JSON_LOGGER = True
except ImportError:  # pragma: no cover
    HAS_JSON_LOGGER = False


def configure_logging(level: str = "INFO", fmt: str = "json") -> None:
    """
    Configura el root logger.

    Args:
        level: nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        fmt: "json" o "text".
    """
    root = logging.getLogger()
    # Limpiar handlers existentes (evita duplicación si se llama varias veces).
    for h in list(root.handlers):
        root.removeHandler(h)

    handler: logging.Handler
    if fmt == "json" and HAS_JSON_LOGGER:
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "asctime", "levelname": "level", "name": "name"},
        )
        handler.setFormatter(formatter)
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

    root.addHandler(handler)
    root.setLevel(level.upper())


def add_request_id(record: logging.LogRecord, request_id: str) -> None:
    """Helper para inyectar request_id en un record (compatibilidad)."""
    record.request_id = request_id


def log_dict(logger: logging.Logger, level: int, msg: str, **fields: Any) -> None:
    """Helper para loguear con campos extra estructurados."""
    logger.log(level, msg, extra=fields)
