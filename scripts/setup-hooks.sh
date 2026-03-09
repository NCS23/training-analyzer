#!/usr/bin/env bash
# Install Git hooks from scripts/git-hooks/ into .git/hooks/.
# Run once after cloning: bash scripts/setup-hooks.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS_SRC="${REPO_ROOT}/scripts/git-hooks"
HOOKS_DST="${REPO_ROOT}/.git/hooks"

for hook in "${HOOKS_SRC}"/*; do
  name=$(basename "$hook")
  cp "$hook" "${HOOKS_DST}/${name}"
  chmod +x "${HOOKS_DST}/${name}"
  echo "Installed: ${name}"
done

echo ""
echo "Git hooks installed. Direct commits/pushes to main are now blocked."
