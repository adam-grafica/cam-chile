#!/usr/bin/env bash
# Test reproducible para scripts/add-worktree.sh.
# Bootstrap + add-worktree con CAM_CHILE_ROOT temporal, verifica que el
# worktree y la rama se crean correctamente.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BOOTSTRAP="${REPO_ROOT}/scripts/bootstrap.sh"
ADD_WT="${REPO_ROOT}/scripts/add-worktree.sh"

for f in "${BOOTSTRAP}" "${ADD_WT}"; do
  [ -x "$f" ] || { echo "✗ No se encontró $f" >&2; exit 1; }
done

TMP="$(mktemp -d -t camchile-addwt-XXXXXX)"
trap 'rm -rf "${TMP}"' EXIT
echo "▸ TMP = ${TMP}"

REMOTE_DIR="${TMP}/remote.git"
git clone --bare "${REPO_ROOT}" "${REMOTE_DIR}" --quiet

CAM_CHILE_ROOT="${TMP}/root" \
  REPO_URL="file://${REMOTE_DIR}" \
  bash "${BOOTSTRAP}" >/dev/null

CAM_CHILE_ROOT="${TMP}/root" bash "${ADD_WT}" test-agent 999 test-slug

WT_DIR="${TMP}/root/worktrees/test-agent-issue-999"
[ -d "${WT_DIR}" ] || { echo "✗ Falta worktree ${WT_DIR}"; exit 1; }
# Un worktree git tiene `.git` como archivo (no directorio) apuntando al repo principal.
[ -d "${WT_DIR}/.git" ] || [ -f "${WT_DIR}/.git" ] || { echo "✗ ${WT_DIR} no es un worktree válido"; exit 1; }

# Rama creada en el repo principal
if ! git -C "${TMP}/root/repo" branch --list "agent/test-agent/issue-999-test-slug" | grep -q .; then
  echo "✗ Falta rama agent/test-agent/issue-999-test-slug"
  exit 1
fi

# Tracking contra origin/main
TRACK=$(git -C "${WT_DIR}" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)
[ "${TRACK}" = "origin/main" ] || { echo "✗ Tracking ${TRACK} != origin/main"; exit 1; }

echo "✓ test_add_worktree.sh OK"