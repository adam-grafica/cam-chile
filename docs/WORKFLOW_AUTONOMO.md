# CAM-CHILE — Workflow autónomo, verificable y multiagente

## Objetivo

Permitir que OrcaDev/Claude coordine el proyecto de principio a fin sin perder control humano: los agentes ejecutan tareas atómicas en worktrees aislados, GitHub centraliza evidencia y los gates automáticos impiden integrar cambios sin pruebas, seguridad y trazabilidad.

> GitHub es la fuente de verdad. Un agente puede proponer y ejecutar cambios, pero solo se consideran integrados después de Pull Request, validaciones y merge.

## Principios operativos

1. **Un Issue = una unidad de trabajo verificable.**
2. **Un agente = una rama + un worktree exclusivo.**
3. **Un PR = una propuesta de cambio revisable.**
4. **Los gates automáticos bloquean calidad insuficiente.**
5. **La comunicación A2A queda documentada en Issues/PRs.**
6. **El Orchestrator no inventa trabajo fuera del roadmap.**
7. **Solo fuentes públicas/autorizadas; nunca escaneo activo, credenciales por defecto ni cámaras privadas.**

## Roles y verificadores

| Rol | Modelo sugerido | Responsabilidad | Gate de salida |
|---|---|---|---|
| `orchestrator` | MINIMAX-M3 `/effort ultra code` | Prioriza dependencias, crea issues/worktrees y consolida PRs | Issue atómico + handoff A2A documentado |
| `catalog` | MINIMAX-M3 | Curaduría de fuentes explícitamente públicas/autorizadas | `catalog/validate.py --all` + evidencia de procedencia |
| `metadata` | Codex/OpenCode | Normaliza, deduplica y valida el esquema de datos | Tests de esquema y deduplicación |
| `backend` | Codex/MINIMAX-M3 | API, seguridad, migraciones y lógica de negocio | Pytest + validación SSRF/allowlist |
| `frontend` | Antigravity/MINIMAX-M3 | Mapa, UI mínima, accesibilidad y rendimiento | Tests UI/e2e + revisión visual |
| `qa-security` | Codex | Pruebas negativas, secretos, dependencias y controles de seguridad | pytest + lint + secret scan + revisión de amenazas |
| `devops` | Claude/MINIMAX-M3 | Docker, CI/CD, logs, health checks y despliegue | Build reproducible + health check + workflow verde |
| `release-manager` | Orchestrator + humano | Checklist de release, versión, rollback y cambio de entorno | Todos los gates verdes + aprobación humana |

## Estados del tablero

```text
Backlog → Ready → In Progress → Review / QA → Ready to Merge → Done
                         ↓
                      Blocked
```

- **Backlog:** idea registrada, sin criterios completos.
- **Ready:** Issue con alcance, criterios, dependencias y agente asignable.
- **In Progress:** existe worktree, rama y comentario A2A de inicio.
- **Review / QA:** PR abierto con pruebas y evidencia.
- **Ready to Merge:** verificadores aprobados y no hay bloqueos.
- **Done:** PR mergeado, Issue cerrado, worktree limpiado.
- **Blocked:** falta evidencia, dependencia, permiso o decisión humana.

## Ciclo autónomo obligatorio

### 1. Planificación

El Orchestrator lee `ROADMAP.md`, `AGENT_OPERATING_PROMPT.md`, Issue #1, issues abiertos y PRs abiertos. Luego:

- Crea o actualiza solo Issues atómicos.
- Define dependencia explícita: `blocks #N` o `blocked by #N`.
- Define criterios de aceptación medibles.
- Mueve a `Ready` solo si el issue tiene alcance y pruebas claras.

### 2. Delegación aislada

Antes de invocar un subagente, el Orchestrator crea su workspace:

```bash
export CAM_CHILE_ROOT=/opt/orca/cam-chile
cd "$CAM_CHILE_ROOT/repo"
bash scripts/add-worktree.sh <agent> <issue-n> <slug>
```

El comentario de inicio A2A debe incluir:

```md
🚀 Inicio A2A
- Agente: `<agent>`
- Issue: #<n>
- Rama: `agent/<agent>/issue-<n>-<slug>`
- Worktree: `/opt/orca/cam-chile/worktrees/<agent>-issue-<n>`
- Alcance y archivos previstos: ...
- Dependencias: ...
- Criterios de aceptación: ...
- Comandos de prueba: ...
```

### 3. Implementación

El agente:

- Trabaja solo en su worktree.
- Hace commits atómicos (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- No modifica `main`.
- No cambia módulos fuera del alcance sin crear/actualizar un Issue.
- Detiene y marca `Blocked` si falta evidencia o aparece un riesgo.

### 4. Verificación local

Antes de abrir PR, el agente ejecuta solo los gates relevantes:

```bash
make test
make lint
python catalog/validate.py --all
# cuando exista:
make test-e2e
make security-check
```

También debe verificar:

- No hay secretos: `gitleaks detect --no-git` o pre-commit.
- No hay cambios inesperados: `git diff main...HEAD`.
- No hay dependencias nuevas sin justificación.
- Las fuentes de video cumplen la política de publicación/autorización.

### 5. Pull Request

Cada PR usa esta plantilla:

```md
## Resumen
Closes #<issue>

## Alcance
- ...

## Pruebas ejecutadas
```bash
<commands>
```
Resultado: ...

## Gates
- [ ] Tests unitarios
- [ ] Lint/format
- [ ] Secret scan
- [ ] Catalog validator, si aplica
- [ ] SSRF/allowlist, si aplica
- [ ] Evidencia UX/UI, si aplica

## Seguridad y privacidad
- Fuente pública/autorizada: sí/no/no aplica
- No hay cámaras privadas ni scanning activo: sí/no
- Riesgos residuales: ...

## Handoff A2A
- Siguiente agente o dependencia: ...
```

### 6. Verificadores

El Orchestrator convoca verificadores independientes antes del merge:

| Tipo de cambio | Verificador obligatorio |
|---|---|
| Catálogo/fuentes | `catalog` + `qa-security` |
| API/backend | `backend` + `qa-security` |
| DB/migración | `metadata` + `backend` |
| Frontend/UX | `frontend` + `qa-security` |
| Infra/CI/CD | `devops` + `qa-security` |
| Release | `release-manager` + aprobación humana |

Cada verificador deja un comentario estructurado:

```md
✅ Verificación `<rol>`
- Alcance revisado: ...
- Evidencia revisada: ...
- Tests/gates: PASS | FAIL
- Riesgos: ...
- Decisión: approve | request changes | blocked
```

### 7. Merge y limpieza

Solo se puede integrar cuando:

- La rama está limpia y actualizada con `main`.
- Los gates requeridos están verdes.
- No hay secretos ni hosts no permitidos.
- Existe evidencia de QA proporcional al cambio.
- No hay comentario `blocked` activo.
- El propietario humano aprueba releases o cambios de alcance.

Después del merge:

```bash
bash scripts/cleanup-worktree.sh <agent> <issue-n> <slug>
```

El Orchestrator comenta el cierre A2A, confirma que el Issue se cerró y libera dependencias.

## Gates técnicos mínimos

| Gate | Herramienta | Cuándo aplica | Bloquea merge |
|---|---|---|---|
| Unit tests | `pytest` / `make test` | Todo backend, catálogo o lógica | Sí |
| Lint / format | Ruff, Black, isort | Python | Sí |
| Secret scan | Gitleaks / detect-secrets | Todo PR | Sí |
| Catalog validation | `catalog/validate.py --all` | Cambios a `catalog/` | Sí |
| SSRF / allowlist tests | `tests/test_ssrf.py` | URLs, API, player o sources | Sí |
| UI / e2e | Playwright futuro | Frontend crítico | Sí al release |
| Build reproducible | Docker/Make | DevOps y release | Sí |
| Health check | `/healthz`, `/readyz` | Deploy/release | Sí |

## Autonomía con límites

Los agentes pueden operar de forma autónoma para:

- Crear ramas/worktrees y PRs.
- Ejecutar tests, linters, validadores y análisis de secretos.
- Crear issues atómicos dentro del roadmap.
- Corregir fallas de pruebas dentro del alcance del Issue.
- Reportar bloqueos, riesgos y evidencias en GitHub.

Los agentes deben detenerse y pedir decisión humana para:

- Incorporar una fuente cuando no exista permiso claro de publicación/embedding.
- Cambiar el alcance de seguridad o eliminar controles.
- Añadir servicios pagos, nuevas credenciales o cambios de infraestructura con costo.
- Exponer públicamente un entorno o desplegar a producción.
- Cambiar arquitectura fundamental, modelo de licenciamiento o política de datos.

## Definición de terminado

Un Issue está terminado solamente si:

1. Sus criterios de aceptación se cumplen.
2. Los tests y gates aplicables pasan.
3. El PR está mergeado.
4. El Issue se cerró automáticamente o se cerró justificadamente.
5. El worktree se limpió.
6. El handoff/cierre quedó documentado en GitHub.
7. No quedan secretos, placeholders publicables ni riesgos sin registrar.

## Cadencia del Orchestrator

En cada ciclo el Orchestrator debe:

1. Consultar GitHub: Issue #1, tablero, PRs e issues activos.
2. Resolver o registrar bloqueos antes de abrir trabajo nuevo.
3. Priorizar dependencias, no cantidad de agentes activos.
4. Mantener como máximo un agente por módulo crítico simultáneamente.
5. Publicar un resumen de estado en Issue #1: completado, activo, bloqueado y siguiente gate.
6. No iniciar una release sin aprobación humana explícita.
