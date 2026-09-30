"""
Catalog validator — Issue #3.

Política:
- `chile.yaml`: solo entradas con `public_status: declared_public`,
  `license_or_terms_url` real y todos los campos requeridos.
- `_pending.yaml`: entradas con `blocked_reasons` documentadas (no publicables).

Modo hermético: NO hace requests de red. Verificación online de oEmbed
queda para el issue atómico (ver `--check-online` TODO en docs).

Exit codes:
  0  → todas las entradas OK (o pending con bloqueos documentados).
  1  → al menos una entrada malformada o que viola reglas del archivo.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

# ─── Constantes ──────────────────────────────────────────────────────────────
REQUIRED_FIELDS = {
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
}

VALID_STREAM_TYPES = {"youtube", "youtube_embed", "hls", "mp4", "iframe"}
VALID_PUBLIC_STATUS = {"declared_public", "unknown", "revoked"}

URL_RE = re.compile(r"^https?://[^\s]+\.[^\s]+$")


# ─── Modelos ────────────────────────────────────────────────────────────────
@dataclass
class ValidationResult:
    entry_id: str
    publishable: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ─── Validación de campos ───────────────────────────────────────────────────
def _check_url(
    value: Any, field_name: str, errors: list[str], *, allow_placeholder: bool = False
) -> None:
    if not isinstance(value, str) or not value:
        errors.append(f"{field_name} is empty")
        return
    if value in ("PENDING_VALIDATION", "EXAMPLE", "TBD"):
        if allow_placeholder:
            return
        errors.append(f"{field_name} is placeholder ({value})")
        return
    if not URL_RE.match(value):
        errors.append(f"{field_name} is not a valid URL: {value!r}")
        return
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https"):
        errors.append(f"{field_name} scheme not allowed: {parsed.scheme}")
    if not parsed.hostname:
        errors.append(f"{field_name} has no host")


def _check_lat_lon(lat: Any, lon: Any, errors: list[str]) -> None:
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        errors.append("latitude/longitude must be numeric")
        return
    if not (-90 <= lat <= 90):
        errors.append(f"latitude out of range: {lat}")
    if not (-180 <= lon <= 180):
        errors.append(f"longitude out of range: {lon}")


def validate_entry(entry: dict[str, Any], *, file_kind: str) -> ValidationResult:
    """
    file_kind: 'publishable' (chile.yaml) o 'pending' (_pending.yaml).
    """
    entry_id = entry.get("id", "<no-id>")
    errors: list[str] = []
    warnings: list[str] = []

    # Campos requeridos
    missing = REQUIRED_FIELDS - set(entry.keys())
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")

    # Tipos y rangos
    if "stream_type" in entry and entry["stream_type"] not in VALID_STREAM_TYPES:
        errors.append(f"stream_type invalid: {entry['stream_type']!r}")

    if "public_status" in entry and entry["public_status"] not in VALID_PUBLIC_STATUS:
        errors.append(f"public_status invalid: {entry['public_status']!r}")

    _check_lat_lon(entry.get("latitude"), entry.get("longitude"), errors)

    # URLs (placeholders permitidos solo en pending)
    allow_placeholder = file_kind == "pending"
    _check_url(
        entry.get("source_url"),
        "source_url",
        errors,
        allow_placeholder=allow_placeholder,
    )
    _check_url(
        entry.get("stream_url"),
        "stream_url",
        errors,
        allow_placeholder=allow_placeholder,
    )
    _check_url(
        entry.get("license_or_terms_url"),
        "license_or_terms_url",
        errors,
        allow_placeholder=allow_placeholder,
    )

    # Reglas por tipo de archivo
    if file_kind == "publishable":
        if entry.get("public_status") != "declared_public":
            errors.append(
                f"chile.yaml solo acepta public_status=declared_public, "
                f"got {entry.get('public_status')!r}"
            )
        # license_or_terms_url no puede ser placeholder en publishable
        lic = entry.get("license_or_terms_url", "")
        if isinstance(lic, str) and lic in ("PENDING_VALIDATION", "EXAMPLE", "TBD", ""):
            errors.append("chile.yaml requiere license_or_terms_url real")
    else:  # pending
        blocked = entry.get("blocked_reasons")
        if not blocked or not isinstance(blocked, list) or not blocked:
            errors.append(
                "_pending.yaml requiere blocked_reasons (lista no vacía) "
                "documentando por qué la entrada no es publicable"
            )
        else:
            for reason in blocked:
                if not isinstance(reason, str) or not reason.strip():
                    errors.append("blocked_reasons debe contener strings no vacíos")
                    break
        if entry.get("public_status") == "declared_public":
            warnings.append(
                "pending entry con public_status=declared_public — debería moverse a chile.yaml"
            )

    return ValidationResult(
        entry_id=entry_id,
        publishable=(file_kind == "publishable" and not errors),
        errors=errors,
        warnings=warnings,
    )


# ─── Carga y reporte ────────────────────────────────────────────────────────
def detect_file_kind(path: Path) -> str:
    name = path.name
    if name.startswith("_"):
        return "pending"
    return "publishable"


def load_yaml(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or []
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a list of entries, got {type(data).__name__}")
    return data


def validate_file(path: Path) -> tuple[list[ValidationResult], list[dict[str, Any]]]:
    file_kind = detect_file_kind(path)
    raw = load_yaml(path)
    results = [validate_entry(entry, file_kind=file_kind) for entry in raw]
    return results, raw


def report(results: list[ValidationResult], path: Path, file_kind: str) -> bool:
    """Imprime reporte. Devuelve True si todo OK."""
    print(f"\n=== Validating {path} ({file_kind}) ===")
    print(f"Entries: {len(results)}")
    if not results:
        print("✓ Catalog is empty — no entries to validate.")
        return True

    if file_kind == "publishable":
        publishable = [r for r in results if r.publishable]
        blocked = [r for r in results if not r.publishable]
        print(f"Publishable: {len(publishable)}")
        if blocked:
            print(f"❌ Not publishable: {len(blocked)}")
            for r in blocked:
                print(f"  - {r.entry_id}:")
                for e in r.errors:
                    print(f"      • {e}")
            return False
        print("✓ All entries are publishable.")
        return True

    # pending
    documented = [r for r in results if not r.errors]
    undocumented = [r for r in results if r.errors]
    print(f"Documented (with blocked_reasons): {len(documented)}")
    if undocumented:
        print(f"❌ Pending entries without valid blocked_reasons: {len(undocumented)}")
        for r in undocumented:
            print(f"  - {r.entry_id}:")
            for e in r.errors:
                print(f"      • {e}")
        return False
    print("✓ All pending entries are properly blocked.")
    for r in results:
        if r.warnings:
            for w in r.warnings:
                print(f"  ⚠ {r.entry_id}: {w}")
    return True


# ─── CLI ─────────────────────────────────────────────────────────────────────
def main() -> int:
    p = argparse.ArgumentParser(description="Validate the curated catalog")
    p.add_argument(
        "--source",
        type=Path,
        action="append",
        help="YAML file to validate (can be repeated)",
    )
    p.add_argument(
        "--all",
        action="store_true",
        help="Validate both chile.yaml and _pending.yaml",
    )
    args = p.parse_args()

    if args.all:
        sources = [
            Path("catalog/sources/chile.yaml"),
            Path("catalog/sources/_pending.yaml"),
        ]
    else:
        sources = args.source or []

    if not sources:
        p.error("Provide --source FILE or --all")

    all_ok = True
    for src in sources:
        if not src.exists():
            print(f"⚠ Source not found: {src} (skipping)")
            continue
        try:
            results, _ = validate_file(src)
        except ValueError as e:
            print(f"❌ {src}: {e}")
            all_ok = False
            continue
        file_kind = detect_file_kind(src)
        ok = report(results, src, file_kind)
        all_ok = all_ok and ok

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
