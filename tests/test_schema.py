"""
Tests para el esquema de DB y la migración.

Usa DB temporal en /tmp para no contaminar el repo.
"""

import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = REPO_ROOT / "backend" / "db" / "schema.sql"
MIGRATION_001 = REPO_ROOT / "backend" / "db" / "migrations" / "001_align_to_spec.sql"


def test_schema_file_is_valid_sql():
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(SCHEMA.read_text())
    finally:
        conn.close()


def test_schema_columns_present():
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(SCHEMA.read_text())
        cols = {r[1] for r in conn.execute("PRAGMA table_info(cameras)").fetchall()}
    finally:
        conn.close()
    expected = {
        "id",
        "name",
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
        "created_at",
    }
    assert expected.issubset(cols), f"Faltan columnas: {expected - cols}"


def test_migration_001_is_valid_sql():
    conn = sqlite3.connect(":memory:")
    try:
        # Crear tabla legacy
        conn.execute(
            """
            CREATE TABLE cameras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                lat REAL,
                lon REAL,
                feed_type TEXT,
                stream_url TEXT,
                address TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "INSERT INTO cameras (name, lat, lon, feed_type, stream_url, address) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "Test Cam",
                -33.0,
                -70.0,
                "youtube",
                "https://www.youtube.com/watch?v=x",
                "CL",
            ),
        )
        conn.commit()
        # Aplicar migración
        conn.executescript(MIGRATION_001.read_text())
        cols = {r[1] for r in conn.execute("PRAGMA table_info(cameras)").fetchall()}
        assert "country" in cols
        assert "source_name" in cols
        assert "stream_type" in cols
        assert "public_status" in cols
        # La fila migrada debe existir
        rows = conn.execute("SELECT name, latitude, longitude FROM cameras").fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "Test Cam"
    finally:
        conn.close()


def test_migrate_script_runs(tmp_path, monkeypatch):
    """El script backend/db/migrate.py aplica migrations sin error."""
    monkeypatch.chdir(tmp_path)
    # Crea estructura mínima
    (tmp_path / "backend" / "db" / "migrations").mkdir(parents=True)
    import shutil

    # Copiamos __init__.py para que `backend.db.migrate` sea importable
    (tmp_path / "backend").mkdir(exist_ok=True)
    (tmp_path / "backend" / "__init__.py").write_text("")
    shutil.copy(
        REPO_ROOT / "backend" / "__init__.py", tmp_path / "backend" / "__init__.py"
    )
    shutil.copy(
        REPO_ROOT / "backend" / "db" / "__init__.py",
        tmp_path / "backend" / "db" / "__init__.py",
    )
    shutil.copy(
        MIGRATION_001,
        tmp_path / "backend" / "db" / "migrations" / "001_align_to_spec.sql",
    )
    shutil.copy(SCHEMA, tmp_path / "backend" / "db" / "schema.sql")
    (tmp_path / "backend" / "db" / "cameras.db").touch()

    # Importa y corre la función main() directamente
    from backend.db import migrate as migrate_mod

    monkeypatch.setattr(
        migrate_mod, "DB_PATH", tmp_path / "backend" / "db" / "cameras.db"
    )
    monkeypatch.setattr(
        migrate_mod, "MIGRATIONS_DIR", tmp_path / "backend" / "db" / "migrations"
    )
    rc = migrate_mod.main()
    assert rc == 0


def test_migrate_script_skips_applied(tmp_path, monkeypatch):
    """Una migración ya aplicada debe skipearse (no error)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "backend" / "db" / "migrations").mkdir(parents=True)
    import shutil

    (tmp_path / "backend").mkdir(exist_ok=True)
    (tmp_path / "backend" / "__init__.py").write_text("")
    shutil.copy(
        REPO_ROOT / "backend" / "__init__.py", tmp_path / "backend" / "__init__.py"
    )
    shutil.copy(
        REPO_ROOT / "backend" / "db" / "__init__.py",
        tmp_path / "backend" / "db" / "__init__.py",
    )
    shutil.copy(
        MIGRATION_001,
        tmp_path / "backend" / "db" / "migrations" / "001_align_to_spec.sql",
    )
    shutil.copy(SCHEMA, tmp_path / "backend" / "db" / "schema.sql")
    (tmp_path / "backend" / "db" / "cameras.db").touch()

    from backend.db import migrate as migrate_mod

    monkeypatch.setattr(
        migrate_mod, "DB_PATH", tmp_path / "backend" / "db" / "cameras.db"
    )
    monkeypatch.setattr(
        migrate_mod, "MIGRATIONS_DIR", tmp_path / "backend" / "db" / "migrations"
    )

    # Primera corrida aplica
    assert migrate_mod.main() == 0
    # Segunda corrida debe skipear sin error
    assert migrate_mod.main() == 0
