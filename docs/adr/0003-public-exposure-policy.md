# ADR-0003 — Política de exposición pública

- **Estado**: Propuesto (Issue #14)
- **Fecha**: 2026-09-30
- **Decisor**: CEO (adam-grafica) — Orchestrator no puede autoaprobar
- **Sustituye a**: ninguno
- **Superseded by**: —

## Contexto

CAM-CHILE es un proyecto open-source que eventualmente debe estar disponible públicamente (mapa interactivo). Sin una política explícita, cualquier rama, PR o commit podría inadvertidamente terminar accesible en internet, con los riesgos asociados:

- **Seguridad**: endpoints sin endurecer, allowlist no aplicada, CORS abierto.
- **Privacidad**: cámaras privadas, residenciales o sensibles expuestas.
- **Compliance**: PCI, GDPR, regulación chilena de datos.
- **Reputación**: incidente de exposición de cámaras privadas o no autorizadas.

## Decisión

**Ningún agente ni humano puede exponer CAM-CHILE públicamente sin**:

1. ✅ Los 6 gates de CI verdes (ver `docs/CI_GATES.md`).
2. ✅ El Dockerfile mergeado (Issue #7).
3. ✅ Aprobación humana explícita del CEO registrada en GitHub (comentario de aprobación en el PR de release o en Issue #1).
4. ✅ ADR-0003 publicado y firmado.
5. ✅ El catálogo `chile.yaml` tiene al menos 1 entrada real verificada (Issue #3 cerrado).

## Quién puede autorizar

- **CEO (adam-grafica)**: única autoridad para exposición pública. Su aprobación debe quedar registrada como comentario en GitHub.
- **Orchestrator / agentes**: NO pueden autoautorizar. Pueden PROPONER una exposición (vía PR + Issue), pero el merge y la acción de deploy quedan bloqueados hasta la aprobación del CEO.

## Quién puede exponer

- **Devops con aprobación explícita del CEO**: puede ejecutar el deploy.
- **Cualquier otro agente**: NO puede deployar.

## Qué constituye "exposición pública"

- ❌ Subir imagen Docker a registry público (Docker Hub, GHCR, etc.) sin aprobación.
- ❌ Configurar dominio DNS apuntando al servicio.
- ❌ Abrir puerto en firewall de Oracle Cloud o cualquier cloud.
- ❌ Hacer el repo público sin los gates verdes (el repo ya es público, pero esto se refiere al servicio).
- ❌ Compartir URLs internas con terceros fuera del equipo.

## Qué NO requiere aprobación (autoaprobado)

- Crear ramas y PRs (interno).
- Correr gates localmente.
- Mergear a `main` con CI verde y review aprobado (siempre que no implique exposición pública).
- Crear issues, comentarios, documentación.

## Consecuencias de exposición no autorizada

El Orchestrator debe:

1. **Bloquear el merge** del PR que intente exponer.
2. **Reportar el incidente** como comentario en Issue #1.
3. **Solicitar decisión humana** antes de cualquier acción correctiva.
4. Si la exposición ya ocurrió: ejecutar el rollback inmediato, documentar el incidente, y abrir un issue post-mortem.

## Implementación

- `docs/CI_GATES.md` lista los gates que el CI aplica.
- `.github/workflows/ci.yml` ejecuta los gates automáticamente.
- Branch protection en GitHub UI (acción manual del CEO) bloquea merges sin gates verdes.
- Este ADR queda referenciado en todo PR que mencione deploy, dominio o URL pública.

## Cambios futuros

Cualquier cambio a esta política requiere:

1. Nueva ADR que sustituya a la presente.
2. Aprobación del CEO.
3. Migración de cualquier URL pública existente si las reglas se endurecen.

## Referencias

- `AGENT_OPERATING_PROMPT.md §Límites no negociables` — base normativa.
- `docs/WORKFLOW_AUTONOMO.md §Autonomía con límites` — límites operativos.
- `docs/CI_GATES.md` — gates técnicos.
- Issue #14 — implementation de los gates.