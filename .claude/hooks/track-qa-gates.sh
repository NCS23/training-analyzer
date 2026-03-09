#!/usr/bin/env bash
# PostToolUse hook: tracks which QA gates have been run and passed.
# Runs on EVERY Bash call — must exit fast for non-QA commands.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# Parse the command from TOOL_INPUT (JSON: {"command": "..."})
CMD="${TOOL_INPUT:-}"

# Quick exit for non-QA commands (performance: ~2ms)
case "$CMD" in
  *eslint*src/*|*prettier*--check*|*tsc*--noEmit*|*vitest*--run*|*vitest*run*)
    ;; # frontend QA — continue
  *ruff\ check*|*ruff\ format*--check*|*mypy*app/*|*pytest*app/tests*)
    ;; # backend QA — continue
  *)
    exit 0  # not a QA command — bail immediately
    ;;
esac

# Check tool output for failure indicators.
# TOOL_OUTPUT is set by Claude Code for PostToolUse hooks.
OUTPUT="${TOOL_OUTPUT:-}"

has_failure() {
  # Common failure patterns across tools
  echo "$OUTPUT" | grep -qiE '(error|FAILED|FAIL |warning.*--max-warnings|would reformat|Exit code: [1-9])' 2>/dev/null
}

# Determine which gate this is and record if passed.
NOW=$(date +%s)

record_if_passed() {
  local gate_key="$1"
  if ! has_failure; then
    write_state_key "$gate_key" "$NOW"
  fi
}

case "$CMD" in
  *eslint*src/*)           record_if_passed "fe_eslint" ;;
  *prettier*--check*)      record_if_passed "fe_prettier" ;;
  *tsc*--noEmit*)          record_if_passed "fe_tsc" ;;
  *vitest*--run*|*vitest*run*) record_if_passed "fe_vitest" ;;
  *ruff\ check*)
    # Distinguish "ruff check" from "ruff format --check"
    case "$CMD" in
      *ruff\ format*) record_if_passed "be_ruff_format" ;;
      *)              record_if_passed "be_ruff_check" ;;
    esac
    ;;
  *ruff\ format*--check*)  record_if_passed "be_ruff_format" ;;
  *mypy*app/*)              record_if_passed "be_mypy" ;;
  *pytest*app/tests*)       record_if_passed "be_pytest" ;;
esac

exit 0
