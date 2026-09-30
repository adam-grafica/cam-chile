#!/usr/bin/env bash
# CAM-CHILE — Variables de entorno compartidas por todos los scripts.
# Source este archivo antes de usar scripts/bootstrap.sh, add-worktree.sh, etc.
export CAM_CHILE_ROOT="${CAM_CHILE_ROOT:-/opt/orca/cam-chile}"
export CAM_CHILE_REPO="${CAM_CHILE_ROOT}/repo"
export CAM_CHILE_WORKTREES="${CAM_CHILE_ROOT}/worktrees"
