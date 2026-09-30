# CAM-CHILE — Catálogo curado de cámaras públicas

Este directorio contiene el **catálogo curado** de cámaras públicas/autorizadas que alimenta el backend. **No** descubre cámaras por sí mismo: cada entrada es declarada y validada manualmente.

## Archivos

| Archivo | Propósito |
|---|---|
| `sources/_template.yaml` | Plantilla comentada con todos los campos obligatorios. |
| `sources/chile.yaml` | Entradas **publicables** (todas con `public_status: declared_public` y `license_or_terms_url` real). |
| `sources/_pending.yaml` | Candidatos en proceso de verificación. **No se publican.** |
| `validate.py` | Script de validación. Refusa entradas malformadas o con `public_status` incorrecto. |
| `.cache/checks.json` | Evidencia de cada verificación (ignorado por `.gitignore`). |

## Política estricta (Issue #3)

1. ❌ **Nunca** se publica una entrada con `public_status: unknown` o `PENDING_VALIDATION`.
2. ❌ **Nunca** se publica sin `license_or_terms_url` real (no se aceptan "Términos de YouTube" genéricos — debe ser del proveedor o de la municipalidad).
3. ✅ **Toda** entrada en `chile.yaml` debe pasar `validate.py` con exit 0.
4. ✅ **Toda** entrada de `_pending.yaml` debe tener `blocked_reasons` documentados.
5. ✅ Coordenadas verificables contra OSM / Wikipedia / portal oficial.

## Proceso para añadir una cámara

1. **Identifica la fuente oficial.** No fans accounts, no reemisores no autorizados. Confirma el canal/medio:
   - YouTube: canal verificado, descripción coherente, transmisión declarada como permanente.
   - Webcam turística: página oficial con cámara visible.
   - Municipalidad: portal público (no Domo, no privadas).
2. **Verifica el stream.** Corre oEmbed (YouTube) o HEAD request (otros). Debe devolver 200 con metadata.
3. **Verifica coordenadas.** Lat/lon debe coincidir (≤1 km) con el lugar descrito por la fuente.
4. **Verifica la licencia.** `license_or_terms_url` debe apuntar a una página real que efectivamente declare el permiso de republicar/embeber.
5. **Añade a `_pending.yaml`** con todos los campos completos y `blocked_reasons` vacíos.
6. **Corre** `python catalog/validate.py --source catalog/sources/_pending.yaml`.
7. **Si exit 0** y todos los checks pasan → mueve la entrada a `chile.yaml`.
8. **Haz commit y PR.**

## Uso

```bash
# Validar entradas publicables
python catalog/validate.py --source catalog/sources/chile.yaml

# Validar candidatos pendientes (debe listar bloqueos)
python catalog/validate.py --source catalog/sources/_pending.yaml

# Validar todo
python catalog/validate.py --all
```

Exit codes:
- `0` → todas las entradas OK para el caso de uso (`chile.yaml`) o todas documentadas con bloqueos (`_pending.yaml`).
- `1` → entradas mal formadas o que no cumplen las reglas del archivo.

## Salida de ejemplo

```
=== Validating catalog/sources/chile.yaml ===
Entries: 0
Publishable: 0
✓ Catalog is empty — no entries to validate.

=== Validating catalog/sources/_pending.yaml ===
Entries: 3
Blocked: 3
  - alma-observatory-candidate: stream_url es PENDING_VALIDATION; public_status != declared_public
  - tvn-24h-candidate: stream_url es PENDING_VALIDATION; license_or_terms_url es PENDING_VALIDATION; public_status != declared_public
  - canal-24-horas-candidate: stream_url es PENDING_VALIDATION; license_or_terms_url es PENDING_VALIDATION; public_status != declared_public
✓ All pending entries are properly blocked.
```

## Out-of-scope

- ❌ Escaneo de Internet para descubrir cámaras nuevas.
- ❌ `masscan`, `google_dorks`, fuerza bruta, bypass de autenticación.
- ❌ Cámaras residenciales, privadas, empresariales.
- ❌ Publicar coordenadas sensibles (bases militares, embarques diplomáticos, etc.).

Ver `AGENT_OPERATING_PROMPT.md §Límites no negociables` para la política completa.