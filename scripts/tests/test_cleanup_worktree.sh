#!/usr/bin/env bash
# Test reproducible para scripts/cleanup-worktree.sh.
# Bootstrap + add-worktree + cleanup, verifica que el worktree y la rama
# se eliminan correctamente.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BOOTSTRAP="${REPO_ROOT}/scripts/bootstrap.sh"
ADD_WT="${REPO_ROOT}/scripts/add-worktree.sh"
CLEANUP="${REPO_ROOT}/scripts/cleanup-worktree.sh"

for f in "${BOOTSTRAP}" "${ADD_WT}" "${CLEANUP}"; do
  [ -x "$f" ] || { echo "✗ No se encontró $f" >&2; exit 1; }
done

TMP="$(mktemp -d -t camchile-cleanwt-XXXXXX)"
trap 'rm -rf "${TMP}"' EXIT
echo "▸ TMP = ${TMP}"

REMOTE_DIR="${TMP}/remote.git"
git clone --bare "${REPO_ROOT}" "${REMOTE_DIR}" --quiet

CAM_CHILE_ROOT="${TMP}/root" \
  REPO_URL="file://${REMOTE_DIR}" \
  bash "${BOOTSTRAP}" >/dev/null

CAM_CHILE_ROOT="${TMP}/root" bash "${ADD_WT}" test-agent 999 test-slug >/dev/null

# Cleanup debe remover worktree + rama
CAM_CHILE_ROOT="${TMP}/root" bash "${CLEANUP}" test-agent 999 test-slug

WT_DIR="${TMP}/root/worktrees/test-agent-issue-999"
[ ! -d "${WT_DIR}" ] || { echo "✗ Worktree aún existe: ${WT_DIR}"; exit 1; }

if git -C "${TMP}/root/repo" branch --list "agent/test-agent/issue-999-test-slug" | grep -q .; then
  echo "✗ Rama aún existe"
  exit 1
fi

echo "✓ test_cleanup_worktree.sh OK"