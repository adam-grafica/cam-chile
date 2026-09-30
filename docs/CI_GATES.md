# CI Gates — Issue #14

Este documento lista los **gates de CI** que todo Pull Request a `main` debe pasar antes de poder mergear. Es la materialización operativa de `docs/WORKFLOW_AUTONOMO.md §Gates técnicos mínimos`.

## Tabla de gates

| Gate | Comando local | Comando en CI | Bloquea merge | Issue |
|---|---|---|---|---|
| Lint (ruff) | `ruff check backend catalog tests` | `ruff check backend catalog tests` | ✅ | #2, #14 |
| Format (black) | `black --check backend catalog tests` | `black --check backend catalog tests` | ✅ | #2, #14 |
| Unit tests + coverage | `make test-cov` | `pytest tests/ --cov=backend --cov=catalog --cov-fail-under=80` | ✅ | #2, #6, #14 |
| Catalog validation | `python catalog/validate.py --all` | `python catalog/validate.py --all` | ✅ | #3, #14 |
| SSRF / allowlist | parte de `pytest tests/test_ssrf.py` | (dentro de unit tests) | ✅ | #2, #6 |
| Secrets (gitleaks) | `gitleaks detect --no-git --source .` | `gitleaks detect --no-git --source .` | ✅ | #2, #6, #14 |
| Backend smoke (healthz) | `make dev &; curl /healthz` | (workflow job) | ✅ | #2, #14 |
| Build reproducible (Docker) | `docker build -t cam-chile:test .` (Issue #7) | pendiente #7 | ✅ | #7 |

## Cómo correr todos los gates localmente

```bash
unset PYTHONPATH && make ci-local
```

Este target del `Makefile` ejecuta, en orden:

1. `ruff check backend catalog tests`
2. `black --check backend catalog tests`
3. `pytest tests/ -v --cov=backend --cov=catalog --cov-report=term-missing --cov-fail-under=80`
4. `python catalog/validate.py --all`
5. `gitleaks detect --no-git --source .` (requiere binario en PATH)

Si cualquiera falla, `make ci-local` retorna exit ≠ 0.

## Branch protection (documentación)

`main` requiere, al momento del merge:

- ✅ Check `ci/gates` verde.
- ✅ Al menos 1 review aprobado.
- ✅ Branch up-to-date con `origin/main`.

> La activación real de branch protection requiere acción manual en GitHub UI → Settings → Branches → Branch protection rules para `main`. Esta acción la realiza el CEO (adam-grafica) tras el merge de este Issue #14.

## Política de bypass

**No hay bypass.** No existe mecanismo para saltarse los gates. Si un gate falla, el PR no se mergea. La única salida es arreglar la causa raíz.

Excepciones documentadas y aprobadas requieren ADR previo (Issue #15 futuro si surge la necesidad).

## Cómo agregar un nuevo gate

1. Crear el comando de verificación (preferentemente determinista y rápido).
2. Agregar el comando a `.github/workflows/ci.yml` como step dentro del job `gates`.
3. Agregar el comando a `Makefile` target `ci-local`.
4. Documentar en este archivo con su comando local, comando CI, criterio de aceptación.
5. Actualizar `docs/adr/` si el cambio es significativo (ej. nuevo gate de seguridad).

## Cuándo aplica

- **Siempre**: en cada PR a `main`.
- **No aplica** a branches de agentes (catalog, frontend, etc.) que aún no son PR — los gates corren al abrir el PR.
- **Aplica a merges directos**: si el CEO hace un push directo a `main` (no recomendado), los gates corren vía `push:` trigger.

## Out-of-scope

- ❌ No deploy automático (eso es Issue #7).
- ❌ No integración con servicios externos de pago.
- ❌ No expone URLs públicas.
- ❌ No cambia la política sin ADR.

## Referencias

- `docs/WORKFLOW_AUTONOMO.md` — workflow autónomo, gates técnicos mínimos.
- `docs/adr/0003-public-exposure-policy.md` — política de exposición.
- `.gitleaks.toml` — baseline de secretos.