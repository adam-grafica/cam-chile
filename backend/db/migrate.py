"""
Migración de la base de datos SQLite.

Uso:
    python -m backend.db.migrate          # aplica todas las migraciones pendientes
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("backend/db/cameras.db")
MIGRATIONS_DIR = Path("backend/db/migrations")


def _ensure_db_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    _ensure_db_dir()
    return sqlite3.connect(DB_PATH)


def _applied_migrations(conn: sqlite3.Connection) -> set[str]:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS _migrations (
            name TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        )
        """
    )
    rows = conn.execute("SELECT name FROM _migrations").fetchall()
    return {r[0] for r in rows}


def main() -> int:
    conn = _connect()
    try:
        applied = _applied_migrations(conn)
        # Detectar si hay tabla legacy 'cameras' con esquema antiguo
        legacy_info = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cameras'"
        ).fetchone()
        has_legacy = bool(legacy_info)

        files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for path in files:
            if path.name in applied:
                print(f"✓ {path.name} (ya aplicada)")
                continue
            print(f"→ Aplicando {path.name}…")
            sql = path.read_text()
            # Si la migración es de "align_to_spec" pero NO hay legacy, saltarla
            if "align_to_spec" in path.name and not has_legacy:
                print(f"⊘ {path.name} no aplica (no hay esquema legacy)")
                conn.execute("INSERT INTO _migrations (name) VALUES (?)", (path.name,))
                conn.commit()
                continue
            try:
                conn.executescript(sql)
            except sqlite3.Error as e:
                print(f"✗ Falló {path.name}: {e}", file=sys.stderr)
                conn.rollback()
                return 1
            conn.execute("INSERT INTO _migrations (name) VALUES (?)", (path.name,))
            conn.commit()
            print(f"✓ {path.name} aplicada")
        # Asegurar que el schema canónico existe
        schema_path = Path("backend/db/schema.sql")
        if schema_path.exists():
            conn.executescript(schema_path.read_text())
            conn.commit()
        print("✓ Migración completada")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
