#!/usr/bin/env bash
# PreToolUse hook: blocks `git push` to main without a feature branch.
# Exit 0 = allow push, Exit 2 = block with error message.

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

# On a feature branch — allow
exit 0
