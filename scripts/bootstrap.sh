#!/usr/bin/env bash
# CAM-CHILE — Bootstrap reproducible del runner OrcaDev
#
# Crea la raíz operativa, clona el repo si no existe, sincroniza main y reporta
# el estado actual. No hace sudo; usa ${CAM_CHILE_ROOT} o el default.

set -euo pipefail

: "${CAM_CHILE_ROOT:=/opt/orca/cam-chile}"
: "${REPO_URL:=https://github.com/adam-grafica/cam-chile.git}"

REPO_DIR="${CAM_CHILE_ROOT}/repo"
WORKTREES_DIR="${CAM_CHILE_ROOT}/worktrees"

log() { printf "▸ %s\n" "$*"; }
err() { printf "✗ %s\n" "$*" >&2; }

require() {
  command -v "$1" >/dev/null 2>&1 || { err "Falta dependencia: $1"; exit 1; }
}

require git
require python3

log "CAM_CHILE_ROOT = ${CAM_CHILE_ROOT}"
mkdir -p "${REPO_DIR}" "${WORKTREES_DIR}"

if [ ! -d "${REPO_DIR}/.git" ]; then
  log "Clonando ${REPO_URL} en ${REPO_DIR}…"
  git clone "${REPO_URL}" "${REPO_DIR}"
fi

cd "${REPO_DIR}"
log "Sincronizando origin/main…"
git fetch origin --prune >/dev/null
git checkout main
git pull --ff-only origin main

# Limpieza de worktrees prunable
if git worktree list --porcelain | grep -q '^prunable'; then
  log "Limpiando worktrees colgados…"
  git worktree prune
fi

LOG=$(git log -1 --pretty='%h %s (%ad)' --date=short)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
WT=$(git worktree list --porcelain | awk '/^worktree/{print $2}')

cat <<INFO
─────────────── estado ───────────────
raíz:     ${CAM_CHILE_ROOT}
repo:     ${REPO_DIR}
worktrees activos:
$(printf '  - %s\n' ${WT})
rama actual: ${BRANCH}
último commit: ${LOG}
──────────────────────────────────────
INFO