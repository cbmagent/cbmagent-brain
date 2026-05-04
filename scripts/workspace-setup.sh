#!/usr/bin/env bash
# workspace-setup.sh — Clone or update operator workspace repos
#
# Clones or fast-forwards the repos that cbmagent.code-workspace expects into
# ~/  (one level above this repo). Repos with uncommitted local changes are
# skipped so dirty worktrees are never overwritten.
#
# Usage:
#   ./workspace-setup.sh           # live run (clones / updates)
#   ./workspace-setup.sh --dry-run  # print what would happen, make no changes
#
# Repos managed:
#   cbmagent/cbmagent-brain                           ~/cbmagent-brain
#   cbmagent/openclaw-deployment                      ~/openclaw-deployment
#   clarkemoyer/clarkemoyer.com                       ~/clarkemoyer.com
#   clarkemoyer/technologyadoptionbarriers.org        ~/technologyadoptionbarriers.org
#   FreeForCharity/FFC-IN-FFC_Single_Page_Template    ~/FFC-IN-FFC_Single_Page_Template
#   FreeForCharity/FFC-IN-Footer_Only_Template        ~/FFC-IN-Footer_Only_Template
#   FreeForCharity/FFC-Cloudflare-Automation          ~/FFC-Cloudflare-Automation
#
# Requirements: git, gh (GitHub CLI, authenticated)

set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
WORKSPACE_ROOT="${HOME}"

declare -A REPOS
REPOS["cbmagent/cbmagent-brain"]="${WORKSPACE_ROOT}/cbmagent-brain"
REPOS["cbmagent/openclaw-deployment"]="${WORKSPACE_ROOT}/openclaw-deployment"
REPOS["clarkemoyer/clarkemoyer.com"]="${WORKSPACE_ROOT}/clarkemoyer.com"
REPOS["clarkemoyer/technologyadoptionbarriers.org"]="${WORKSPACE_ROOT}/technologyadoptionbarriers.org"
REPOS["FreeForCharity/FFC-IN-FFC_Single_Page_Template"]="${WORKSPACE_ROOT}/FFC-IN-FFC_Single_Page_Template"
REPOS["FreeForCharity/FFC-IN-Footer_Only_Template"]="${WORKSPACE_ROOT}/FFC-IN-Footer_Only_Template"
REPOS["FreeForCharity/FFC-Cloudflare-Automation"]="${WORKSPACE_ROOT}/FFC-Cloudflare-Automation"

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
DRY_RUN=false
for arg in "$@"; do
  case "$arg" in
    --dry-run|-n) DRY_RUN=true ;;
    --help|-h)
      grep '^#' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      echo "Usage: $0 [--dry-run]" >&2
      exit 1
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info()    { echo "[INFO]  $*"; }
action()  { echo "[ACTION] $*"; }
skip()    { echo "[SKIP]  $*"; }
warn()    { echo "[WARN]  $*"; }
error()   { echo "[ERROR] $*" >&2; }

run() {
  # run CMD…  — executes CMD unless --dry-run; always prints it
  if $DRY_RUN; then
    echo "[DRY]   $*"
  else
    "$@"
  fi
}

# Returns 0 if repo_path has uncommitted/unstaged changes (dirty worktree)
is_dirty() {
  local repo_path="$1"
  # anything in the working tree or index that differs from HEAD
  if git -C "$repo_path" status --porcelain 2>/dev/null | grep -qm1 .; then
    return 0  # dirty
  fi
  return 1  # clean
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
if $DRY_RUN; then
  info "DRY-RUN mode — no changes will be made."
  echo
fi

if ! command -v gh &>/dev/null; then
  error "gh CLI not found. Install it and run 'gh auth login' first."
  exit 1
fi

if ! gh auth status &>/dev/null; then
  error "gh CLI is not authenticated. Run 'gh auth login' first."
  exit 1
fi

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
CLONED=0
UPDATED=0
SKIPPED_DIRTY=0
SKIPPED_ACCESS=0
ERRORS=0

for nwo in "${!REPOS[@]}"; do
  dest="${REPOS[$nwo]}"
  repo_name="${nwo##*/}"

  echo
  info "Checking ${nwo} -> ${dest}"

  # Check GitHub access
  if ! gh repo view "$nwo" --json name -q .name &>/dev/null; then
    warn "${nwo}: not accessible via gh (private repo without access, or typo). Skipping."
    SKIPPED_ACCESS=$((SKIPPED_ACCESS + 1))
    continue
  fi

  if [ -d "${dest}/.git" ]; then
    # Repo already cloned — check for dirty worktree before updating
    if is_dirty "$dest"; then
      skip "${dest}: has uncommitted local changes — skipping update to avoid data loss."
      SKIPPED_DIRTY=$((SKIPPED_DIRTY + 1))
    else
      default_branch=$(gh repo view "$nwo" --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo "main")
      action "Updating ${repo_name} (fetch + fast-forward ${default_branch})"
      if ! run git -C "$dest" fetch --quiet origin; then
        error "fetch failed for ${dest}"
        ERRORS=$((ERRORS + 1))
        continue
      fi
      if ! run git -C "$dest" merge --ff-only "origin/${default_branch}" 2>/dev/null; then
        warn "${dest}: cannot fast-forward (diverged or non-linear history). Run 'git pull' manually."
        SKIPPED_DIRTY=$((SKIPPED_DIRTY + 1))
      else
        UPDATED=$((UPDATED + 1))
      fi
    fi
  else
    # Not yet cloned
    action "Cloning ${nwo} into ${dest}"
    if ! run gh repo clone "$nwo" "$dest" -- --quiet; then
      error "Clone failed for ${nwo}"
      ERRORS=$((ERRORS + 1))
      continue
    fi
    CLONED=$((CLONED + 1))
  fi
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo
echo "======================================"
echo "  workspace-setup complete"
echo "======================================"
printf "  Cloned:           %d\n"  "$CLONED"
printf "  Updated:          %d\n"  "$UPDATED"
printf "  Skipped (dirty):  %d\n"  "$SKIPPED_DIRTY"
printf "  Skipped (access): %d\n"  "$SKIPPED_ACCESS"
printf "  Errors:           %d\n"  "$ERRORS"
echo
if $DRY_RUN; then
  echo "  (dry-run — no changes made)"
  echo
fi

if [ "$ERRORS" -gt 0 ]; then
  exit 1
fi
exit 0
