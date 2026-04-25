#!/usr/bin/env bash
# PreToolUse hook: blocks `git push` to main without a feature branch.
# Exit 0 = allow, Exit 2 = block with error message.

# --- Read stdin and check if this is a git push command ---
# PreToolUse hooks receive JSON via stdin with tool_input.command
INPUT=$(cat)
CMD=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('command', ''))
except:
    print('')
" 2>/dev/null || echo "")

case "$CMD" in
  *git\ push*) ;; # continue with push checks
  *) exit 0 ;; # not a push — allow immediately
esac

# --- Block --no-verify on push (prevents bypassing git hooks) ---
case "$CMD" in
  *--no-verify*)
    echo "BLOCKIERT: git push --no-verify ist verboten."
    echo "Git Hooks duerfen NICHT umgangen werden."
    exit 2
    ;;
esac

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# --- Bypass check ---
if check_bypass; then
  echo '{"status":"bypassed — branch check skipped by user"}'
  exit 0
fi

# --- Get current branch ---
# Use the working directory of the push (not $PROJECT_ROOT). When the user pushes
# from a worktree, the worktree's branch is what's actually being pushed — not
# the branch checked out in the main repo. Hardcoding $PROJECT_ROOT would falsely
# block worktree pushes whenever the main repo happens to sit on a merged branch.
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")

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
