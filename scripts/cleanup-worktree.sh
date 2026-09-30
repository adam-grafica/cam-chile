#!/usr/bin/env bash
# CAM-CHILE — Limpia un worktree y rama ya mergeados.
#
# Uso:
#   bash scripts/cleanup-worktree.sh <agent> <issue-n> <slug>
#
# Requiere que la rama ya esté mergeada en main.

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

cd "${REPO_DIR}"

if [ -d "${WT_DIR}" ]; then
  git worktree remove "${WT_DIR}" --force
  printf "▸ Worktree removido: %s\n" "${WT_DIR}"
fi

if git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
  git branch -d "${BRANCH}"
  printf "▸ Rama borrada: %s\n" "${BRANCH}"
fi

git fetch --prune origin
git worktree prune