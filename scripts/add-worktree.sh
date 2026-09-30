#!/usr/bin/env bash
# CAM-CHILE — Crea el worktree y rama de un agente para un issue dado.
#
# Uso:
#   bash scripts/add-worktree.sh <agent> <issue-n> <slug>
# Ejemplo:
#   bash scripts/add-worktree.sh orchestrator 2 orca-bootstrap
#
# Resultado:
#   - Worktree: ${CAM_CHILE_ROOT}/worktrees/<agent>-issue-<n>
#   - Rama:     agent/<agent>/issue-<n>-<slug> (trackeada contra origin/main)

set -euo pipefail

: "${CAM_CHILE_ROOT:=/opt/orca/cam-chile}"

if [ "$#" -ne 3 ]; then
  printf "Uso: %s <agent> <issue-n> <slug>\n" "$0" >&2
  exit 2
fi

AGENT="$1"
ISSUE_N="$2"
SLUG="$3"

REPO_DIR="${CAM_CHILE_ROOT}/repo"
WT_DIR="${CAM_CHILE_ROOT}/worktrees/${AGENT}-issue-${ISSUE_N}"
BRANCH="agent/${AGENT}/issue-${ISSUE_N}-${SLUG}"

if [ ! -d "${REPO_DIR}/.git" ]; then
  printf "✗ Repo no encontrado en %s. Corré scripts/bootstrap.sh primero.\n" "${REPO_DIR}" >&2
  exit 1
fi

cd "${REPO_DIR}"

if [ -d "${WT_DIR}" ]; then
  printf "✗ Worktree ya existe: %s\n" "${WT_DIR}" >&2
  exit 1
fi

git fetch origin --prune >/dev/null
git worktree add "${WT_DIR}" -b "${BRANCH}" origin/main

printf "▸ Worktree listo: %s\n" "${WT_DIR}"
printf "▸ Rama:           %s\n" "${BRANCH}"