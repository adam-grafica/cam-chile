#!/usr/bin/env bash
# Test reproducible para scripts/bootstrap.sh.
# Crea un bare clone local, ejecuta bootstrap en CAM_CHILE_ROOT temporal,
# verifica que clona el repo y crea la estructura de worktrees.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BOOTSTRAP="${REPO_ROOT}/scripts/bootstrap.sh"

[ -x "$BOOTSTRAP" ] || { echo "✗ No se encontró $BOOTSTRAP" >&2; exit 1; }

TMP="$(mktemp -d -t camchile-bootstrap-XXXXXX)"
trap 'rm -rf "${TMP}"' EXIT
echo "▸ TMP = ${TMP}"

# Crear un bare clone que actúa como remote local (sin tocar GitHub).
REMOTE_DIR="${TMP}/remote.git"
git clone --bare "${REPO_ROOT}" "${REMOTE_DIR}" --quiet 2>&1 | tail -3 || \
    { echo "✗ No se pudo crear bare clone desde ${REPO_ROOT}"; exit 1; }

# Ejecutar bootstrap con CAM_CHILE_ROOT temporal y REPO_URL apuntando al bare clone.
CAM_CHILE_ROOT="${TMP}/root" \
  REPO_URL="file://${REMOTE_DIR}" \
  bash "${BOOTSTRAP}" >/dev/null

# Verificar que el repo fue clonado
[ -d "${TMP}/root/repo/.git" ] || { echo "✗ Falta ${TMP}/root/repo/.git"; exit 1; }

# Verificar que el directorio de worktrees existe
[ -d "${TMP}/root/worktrees" ] || { echo "✗ Falta ${TMP}/root/worktrees"; exit 1; }

# Verificar que el repo está en main
BRANCH=$(git -C "${TMP}/root/repo" rev-parse --abbrev-ref HEAD)
[ "${BRANCH}" = "main" ] || { echo "✗ Branch actual: ${BRANCH}, esperaba main"; exit 1; }

echo "✓ test_bootstrap.sh OK"