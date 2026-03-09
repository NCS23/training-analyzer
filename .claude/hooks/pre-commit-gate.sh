#!/usr/bin/env bash
# PreToolUse hook: blocks `git commit` unless all required QA gates have passed.
# Exit 0 = allow commit, Exit 2 = block with error message.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# --- Bypass check ---
if check_bypass; then
  echo '{"status":"bypassed — quality gate check skipped by user"}'
  exit 0
fi

# --- Determine which gates are needed based on staged files ---
STAGED=$(git -C "$PROJECT_ROOT" diff --cached --name-only 2>/dev/null || true)

if [ -z "$STAGED" ]; then
  # Nothing staged — let git handle the "nothing to commit" error
  exit 0
fi

NEED_FE=false
NEED_BE=false

while IFS= read -r file; do
  case "$file" in
    frontend/src/*) NEED_FE=true ;;
    backend/app/*)  NEED_BE=true ;;
  esac
done <<< "$STAGED"

# If only non-src/app files changed (e.g. docs, config), skip QA check
if ! $NEED_FE && ! $NEED_BE; then
  exit 0
fi

# --- Check which gates have passed in this session ---
MISSING=()

check_gate() {
  local key="$1"
  local label="$2"
  local val
  val=$(read_state_key "$key")
  if [ -z "$val" ]; then
    MISSING+=("  - $label")
  fi
}

if $NEED_FE; then
  check_gate "fe_eslint"    "npx eslint src/ --max-warnings 0  (cd frontend)"
  check_gate "fe_prettier"  "npx prettier --check \"src/**/*.{ts,tsx,css}\"  (cd frontend)"
  check_gate "fe_tsc"       "npx tsc --noEmit  (cd frontend)"
  check_gate "fe_vitest"    "npx vitest --run  (cd frontend)"
fi

if $NEED_BE; then
  check_gate "be_ruff_check"  "ruff check app/  (cd backend)"
  check_gate "be_ruff_format" "ruff format --check app/  (cd backend)"
  check_gate "be_mypy"        "mypy app/  (cd backend)"
  check_gate "be_pytest"      "pytest app/tests/ -x  (cd backend)"
fi

# --- Block or allow ---
if [ ${#MISSING[@]} -gt 0 ]; then
  MISSING_LIST=$(printf '%s\n' "${MISSING[@]}")
  cat <<EOF
BLOCKIERT: Quality Gates nicht bestanden.

Fehlende Checks:
${MISSING_LIST}

Fuehre diese Commands aus, dann erneut committen.
Bypass: User muss "skip checks" sagen.
EOF
  exit 2
fi

# All gates passed
exit 0
