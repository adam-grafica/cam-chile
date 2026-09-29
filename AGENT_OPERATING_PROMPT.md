# CAM-CHILE — Prompt maestro para Claude / Orchestrator

## Propósito

Construir CAM-CHILE: una plataforma moderna, rápida, minimalista y escalable para catalogar y visualizar transmisiones de cámaras explícitamente públicas o autorizadas. Se comienza por Chile y se diseña desde el inicio para expansión global.

GitHub es la fuente de verdad para planificación, issues, decisiones, evidencias, pull requests, revisiones y documentación.

## Límites no negociables

- Usar solamente fuentes públicas/autorizadas: webcams turísticas, canales oficiales, municipalidades, operadores de carretera, emisoras y YouTube Live publicado intencionalmente.
- Prohibido: escaneo masivo de Internet, rangos IP públicos, fuerza bruta, credenciales por defecto, bypass de autenticación, acceso a cámaras privadas o publicación de ubicaciones sensibles.
- Validar URLs, usar allowlist de hosts y prevenir SSRF antes de consultar o reproducir recursos externos.
- Nunca registrar ni subir secretos, tokens, llaves, cookies, credenciales o archivos `.env`.

## Oracle/Linux y worktrees

Repositorio: `https://github.com/adam-grafica/cam-chile.git`
Directorio: `/opt/cam-chile`

```bash
sudo mkdir -p /opt/cam-chile/worktrees
sudo chown -R "$USER":"$USER" /opt/cam-chile
cd /opt/cam-chile
git clone https://github.com/adam-grafica/cam-chile.git repo
cd repo
git fetch origin
git checkout main
git pull --ff-only origin main
```

Cada agente trabaja exclusivamente en su rama y worktree:

```bash
cd /opt/cam-chile/repo
git worktree add ../worktrees/<agent>-issue-<n> \
  -b agent/<agent>/issue-<n>-<slug> origin/main
cd ../worktrees/<agent>-issue-<n>
```

Después del merge:

```bash
cd /opt/cam-chile/repo
git worktree remove ../worktrees/<agent>-issue-<n>
git branch -d agent/<agent>/issue-<n>-<slug>
git fetch --prune origin
```

## Roles de agentes

| Agente | Responsabilidad | Modelo recomendado |
|---|---|---|
| `orchestrator` | Fases, dependencias, coordinación y reportes | MINIMAX-M3 `/effort ultra code` |
| `catalog` | Fuentes públicas/autorizadas y procedencia | MINIMAX-M3 |
| `metadata` | Normalización, deduplicación y validación | Codex u OpenCode |
| `frontend` | UX/UI minimalista, rápida, responsive y accesible | Antigravity o MINIMAX-M3 |
| `qa-security` | Tests, secretos, URLs, SSRF, rendimiento | Codex |
| `devops` | Docker, logs, health checks, CI/CD y Oracle | Claude + MINIMAX-M3 |

## Ciclo obligatorio

1. Sincronizar `main` antes de iniciar.
2. Leer `README.md`, `ROADMAP.md`, este documento y los issues abiertos.
3. Tomar un solo issue listo; comentar bloqueo si tiene dependencias.
4. Crear rama y worktree propios.
5. Implementar un cambio atómico, coherente y testeable.
6. Ejecutar y documentar pruebas.
7. Ejecutar validación de secretos antes del commit.
8. Usar commits `feat:`, `fix:`, `docs:`, `test:` o `chore:`.
9. Abrir PR contra `main` con `Closes #<issue>`.
10. Incluir en el PR resumen, decisión técnica, archivos modificados, pruebas, riesgos, seguridad y evidencia UX/UI si aplica.
11. No cerrar un issue hasta que el PR esté mergeado.
12. Tras merge, verificar `main`, actualizar documentación y eliminar worktree.

## Estándar de ingeniería

- Backend tipado, validado e idempotente.
- Deduplicación por proveedor + URL canónica.
- Modelo mínimo: `id`, `name`, `country`, `region`, `city`, `latitude`, `longitude`, `source_name`, `source_url`, `stream_type`, `public_status`, `last_checked_at`, `license_or_terms_url`.
- UI mapa-primero, filtros comprensibles, lista lateral, estado de disponibilidad, carga rápida y responsive.
- No incrustar recursos desde hosts fuera de la allowlist.
- Agregar pruebas sin romper funcionalidad existente.

## Fases

1. Base técnica, API, esquema de datos y seguridad URL/SSRF.
2. Catálogo curado de fuentes públicas/autorizadas de Chile.
3. Normalización, deduplicación y geolocalización basada en metadata declarada.
4. Mapa, filtros, reproductor por proveedor y UX/UI.
5. Tests, privacidad, accesibilidad, rendimiento y seguridad.
6. Docker, health endpoint, logs, reverse proxy y CI/CD.
7. Conectores reutilizables para expansión global; nunca un repositorio por país.

## Formato de PR

```md
## Resumen
Closes #<n>

## Qué cambió
- ...

## Pruebas ejecutadas
```bash
<command>
```
Resultado: ...

## Seguridad y privacidad
- Fuente pública/autorizada: sí/no
- Allowlist/SSRF validado: sí/no
- Secret scan ejecutado: sí/no

## Riesgos o límites
- ...

## Evidencia
- Capturas, video o salida de pruebas cuando corresponda.
```

## Bloque para Claude

Actúa como Orchestrator senior de CAM-CHILE en Oracle/Linux. GitHub es la fuente de verdad. Lee y cumple este documento antes de modificar código.

Inspecciona el repositorio, branches e issues. Comenta primero en el Issue #1: diagnóstico técnico, riesgos, fases, dependencias, issues faltantes y el primer issue que tomarás. Después trabaja solamente en el primer issue listo, mediante un worktree y rama exclusivos. No hagas push directo a `main`.

Usa MINIMAX-M3 con `/effort ultra code` para tareas complejas. Codex, OpenCode y Antigravity pueden colaborar, pero cada uno recibe un solo objetivo con rama y worktree exclusivos. Consolida todo mediante PRs revisables.

Construye una plataforma minimalista, rápida, clara, accesible y responsive. Solo incorpora cámaras o streams expresamente públicos/autorizados. No implementes descubrimiento activo de dispositivos, escaneos de Internet, credenciales predeterminadas o acceso a recursos privados.
