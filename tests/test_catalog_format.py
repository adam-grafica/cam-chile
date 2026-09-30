"""
Tests para el formato de los YAMLs del catálogo.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO_ROOT / "catalog" / "sources"


@pytest.mark.parametrize(
    "filename",
    ["_template.yaml", "chile.yaml", "_pending.yaml"],
)
def test_yaml_is_parseable(filename):
    path = SOURCES_DIR / filename
    assert path.exists(), f"Missing {filename}"
    with path.open() as fh:
        data = yaml.safe_load(fh)
    assert data is None or isinstance(data, list), f"{filename} debe ser lista o vacío"


def test_pending_yaml_has_blocked_reasons():
    """Cada entrada de _pending.yaml debe tener blocked_reasons."""
    path = SOURCES_DIR / "_pending.yaml"
    data = yaml.safe_load(path.read_text()) or []
    assert isinstance(data, list)
    assert len(data) >= 1, "Se esperan al menos candidatos pendientes documentados"
    for entry in data:
        assert "blocked_reasons" in entry, f"{entry.get('id')} sin blocked_reasons"
        assert isinstance(entry["blocked_reasons"], list)
        assert len(entry["blocked_reasons"]) >= 1
        for reason in entry["blocked_reasons"]:
            assert isinstance(reason, str)
            assert reason.strip()


def test_chile_yaml_has_no_unknown_or_pending_entries():
    """chile.yaml NO debe tener entradas con public_status=unknown o stream_url pendiente."""
    path = SOURCES_DIR / "chile.yaml"
    data = yaml.safe_load(path.read_text()) or []
    if not data:  # vacío por política
        return
    for entry in data:
        assert (
            entry.get("public_status") == "declared_public"
        ), f"{entry.get('id')} no publicable: {entry.get('public_status')}"
        assert entry.get("stream_url") != "PENDING_VALIDATION"
        assert entry.get("license_or_terms_url") != "PENDING_VALIDATION"


def test_no_entry_in_catalog_is_example():
    """Ninguna entrada (publishable o pending) debe tener stream_url='example'."""
    for fname in ["chile.yaml", "_pending.yaml"]:
        path = SOURCES_DIR / fname
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text()) or []
        for entry in data:
            for field in ["stream_url", "source_url", "license_or_terms_url"]:
                v = entry.get(field, "")
                if isinstance(v, str):
                    assert (
                        "example" not in v.lower() or "example.com" in v
                    ), f"{fname}:{entry.get('id')}:{field}={v!r}"
