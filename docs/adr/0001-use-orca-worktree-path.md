# ADR-0001 — Path de worktrees en OrcaDev

- **Estado**: Aceptado
- **Fecha**: 2026-09-29
- **Decisor**: Orchestrator senior

## Contexto

`AGENT_OPERATING_PROMPT.md` (la fuente de verdad operativa) asume que el repositorio y los worktrees viven en `/opt/cam-chile`. Sin embargo, ese path es propiedad de `root` y no es escribible para el usuario `adamcloud` sin contraseña de `sudo`. Esto rompe el flujo automatizado de bootstrapping de subagentes.

## Opciones consideradas

1. **`/opt/cam-chile` con `sudo` y `chown`**
   - Pros: literal a la documentación.
   - Contras: requiere intervención manual cada vez que se provisiona una nueva instancia; rompe IaC.

2. **`/opt/orca/cam-chile`** ✅
   - Pros: ya es escribible por convención OrcaDev (`/opt/orca` es `drwxrwxr-x adamcloud`); coherente con el resto del entorno OrcaDev; no requiere sudo.
   - Contras: diverge de la documentación actual.

3. **`/home/adamcloud/cam-chile`**
   - Pros: trivialmente escribible.
   - Contras: choca con el home del usuario; rompe la convención de OrcaDev.

4. **`/srv/cam-chile`**
   - Pros: convención Linux estándar para datos de servicio.
   - Contras: tampoco escribible sin sudo.

## Decisión

Usar **`/opt/orca/cam-chile/{repo,worktrees}`** como raíz operativa, expuesta a través de la variable de entorno `CAM_CHILE_ROOT` con default `/opt/orca/cam-chile`.

Todos los scripts y documentos referirán al path vía `$CAM_CHILE_ROOT` en lugar de hardcodearlo.

## Consecuencias

- ✅ Bootstrap automatizable: `scripts/bootstrap.sh` puede correr sin intervención.
- ✅ Documentación coherente con la realidad operativa.
- ⚠️ Hay que parchear `AGENT_OPERATING_PROMPT.md` para que use la variable (issue #9).
- ⚠️ Scripts externos que asuman `/opt/cam-chile` deben migrar a la nueva convención.