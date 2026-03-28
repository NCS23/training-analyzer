#!/usr/bin/env bash
# PreToolUse hook: blocks `git push` to main without a feature branch.
# Exit 0 = allow push, Exit 2 = block with error message.
#
# NOTE: This hook runs on EVERY Bash tool call. It must exit 0 quickly
# for non-push commands to avoid blocking normal work.

# Only act on git push commands — read tool input from stdin
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | grep -o '"command":"[^"]*"' | head -1 | sed 's/"command":"//;s/"$//' 2>/dev/null || true)
if ! echo "$COMMAND" | grep -q 'git push'; then
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# --- Bypass check ---
if check_bypass; then
  echo '{"status":"bypassed — branch check skipped by user"}'
  exit 0
fi

# --- Get current branch ---
BRANCH=$(git -C "$PROJECT_ROOT" branch --show-current 2>/dev/null || echo "unknown")

if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  cat <<EOF
BLOCKIERT: Push direkt auf main.

Der Workflow erfordert Feature-Branches:
  git checkout -b feature/<issue-slug>

Bypass: User muss "push auf main ist ok" sagen.
EOF
  exit 2
fi

# --- Check if branch has a merged PR (don't push to merged branches) ---
MERGED_PR=$(gh pr list -R NCS23/training-analyzer --head "$BRANCH" --state merged --json number --jq '.[0].number' 2>/dev/null || echo "")
if [ -n "$MERGED_PR" ] && [ "$MERGED_PR" != "null" ]; then
  cat <<EOF

============================================
  BLOCKIERT: Branch hat bereits gemergten PR
============================================

  Branch: $BRANCH
  PR #$MERGED_PR wurde bereits gemergt.

  Erstelle einen neuen Branch von main:
    git fetch origin main
    git checkout -b fix/<issue>-<slug> origin/main

EOF
  exit 2
fi

# On a feature branch without merged PR — allow
exit 0
