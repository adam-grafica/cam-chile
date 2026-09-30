"""
Tests para catalog.validate
"""
from pathlib import Path

import pytest

from catalog.validate import (
    detect_file_kind,
    validate_entry,
    validate_file,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


# ─── Helpers ────────────────────────────────────────────────────────────────
def _good_publishable() -> dict:
    return {
        "id": "test-cam",
        "name": "Test Camera",
        "country": "CL",
        "region": "Test Region",
        "city": "Test City",
        "latitude": -33.0,
        "longitude": -70.0,
        "source_name": "Test Source",
        "source_url": "https://www.youtube.com/watch?v=abc",
        "stream_type": "youtube_embed",
        "stream_url": "https://www.youtube.com/watch?v=abc",
        "public_status": "declared_public",
        "license_or_terms_url": "https://example.com/terms",
        "last_checked_at": "2026-09-29T00:00:00Z",
    }


def _good_pending() -> dict:
    e = _good_publishable()
    e["public_status"] = "unknown"
    e["stream_url"] = "PENDING_VALIDATION"
    e["license_or_terms_url"] = "PENDING_VALIDATION"
    e["blocked_reasons"] = ["stream_url es PENDING_VALIDATION", "public_status != declared_public"]
    return e


# ─── detect_file_kind ──────────────────────────────────────────────────────
def test_detect_file_kind_publishable():
    assert detect_file_kind(Path("catalog/sources/chile.yaml")) == "publishable"


def test_detect_file_kind_pending():
    assert detect_file_kind(Path("catalog/sources/_pending.yaml")) == "pending"


# ─── Validación de entrada publicable ──────────────────────────────────────
def test_publishable_valid_entry_passes():
    r = validate_entry(_good_publishable(), file_kind="publishable")
    assert r.publishable
    assert not r.errors


def test_publishable_rejects_unknown_status():
    e = _good_publishable()
    e["public_status"] = "unknown"
    r = validate_entry(e, file_kind="publishable")
    assert not r.publishable
    assert any("public_status" in err and "declared_public" in err for err in r.errors)


def test_publishable_rejects_pending_url():
    e = _good_publishable()
    e["stream_url"] = "PENDING_VALIDATION"
    r = validate_entry(e, file_kind="publishable")
    assert not r.publishable
    assert any("PENDING_VALIDATION" in err for err in r.errors)


def test_publishable_rejects_missing_license():
    e = _good_publishable()
    e["license_or_terms_url"] = ""
    r = validate_entry(e, file_kind="publishable")
    assert not r.publishable


def test_publishable_rejects_out_of_range_coords():
    e = _good_publishable()
    e["latitude"] = 100
    r = validate_entry(e, file_kind="publishable")
    assert not r.publishable
    assert any("latitude" in err for err in r.errors)


def test_publishable_rejects_invalid_stream_type():
    e = _good_publishable()
    e["stream_type"] = "rtsp"
    r = validate_entry(e, file_kind="publishable")
    assert not r.publishable


def test_publishable_rejects_missing_field():
    e = _good_publishable()
    del e["city"]
    r = validate_entry(e, file_kind="publishable")
    assert not r.publishable
    assert any("city" in err for err in r.errors)


# ─── Validación de entrada pending ──────────────────────────────────────────
def test_pending_with_reasons_passes():
    r = validate_entry(_good_pending(), file_kind="pending")
    assert not r.errors


def test_pending_without_blocked_reasons_fails():
    e = _good_pending()
    del e["blocked_reasons"]
    r = validate_entry(e, file_kind="pending")
    assert r.errors
    assert any("blocked_reasons" in err for err in r.errors)


def test_pending_with_empty_blocked_reasons_fails():
    e = _good_pending()
    e["blocked_reasons"] = []
    r = validate_entry(e, file_kind="pending")
    assert any("blocked_reasons" in err for err in r.errors)


def test_pending_warns_when_publishable_in_pending_file():
    e = _good_publishable()
    e["blocked_reasons"] = ["x"]
    r = validate_entry(e, file_kind="pending")
    assert r.warnings
    assert any("chile.yaml" in w for w in r.warnings)


# ─── Validación de archivos ────────────────────────────────────────────────
def test_chile_yaml_is_empty_by_default():
    """El archivo publicable arranca vacío por política estricta."""
    path = REPO_ROOT / "catalog" / "sources" / "chile.yaml"
    results, raw = validate_file(path)
    assert raw == []
    assert results == []


def test_pending_yaml_has_documented_entries():
    path = REPO_ROOT / "catalog" / "sources" / "_pending.yaml"
    results, raw = validate_file(path)
    assert len(raw) >= 1
    for r in results:
        # Cada pending debe tener razones o errores de "no se valida como publishable"
        # pero NO errores de bloque_reasons faltantes
        assert not any("blocked_reasons" in err for err in r.errors), (
            f"{r.entry_id} missing blocked_reasons"
        )


def test_pending_yaml_no_publishable_status_silently():
    """Asegura que ninguna entrada de _pending tiene public_status=declared_public sin advertencia."""
    path = REPO_ROOT / "catalog" / "sources" / "_pending.yaml"
    _, raw = validate_file(path)
    for entry in raw:
        assert entry.get("public_status") != "declared_public" or entry.get("blocked_reasons"), (
            f"{entry.get('id')} declared_public en pending sin blocked_reasons"
        )


# ─── CLI ────────────────────────────────────────────────────────────────────
def test_cli_runs_clean_for_chile(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(REPO_ROOT)
    from catalog import validate as validate_cli

    argv_save = validate_cli.sys.argv
    try:
        validate_cli.sys.argv = ["validate.py", "--all"]
        rc = validate_cli.main()
    finally:
        validate_cli.sys.argv = argv_save
    assert rc == 0


def test_cli_validates_pending(capsys):
    from catalog import validate as validate_cli

    argv_save = validate_cli.sys.argv
    try:
        validate_cli.sys.argv = ["validate.py", "--source", "catalog/sources/_pending.yaml"]
        rc = validate_cli.main()
    finally:
        validate_cli.sys.argv = argv_save
    assert rc == 0