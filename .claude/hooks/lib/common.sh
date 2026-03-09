#!/usr/bin/env bash
# Shared utilities for Claude Code workflow enforcement hooks.
# Used by: track-qa-gates.sh, pre-commit-gate.sh, pre-push-check.sh

set -euo pipefail

PROJECT_ROOT="/Users/Nils/Projects/training-analyzer"
STATE_DIR="/tmp/claude-hooks"

ensure_state_dir() {
  mkdir -p "$STATE_DIR"
}

# Returns 0 (bypass active) or 1 (no bypass).
check_bypass() {
  local bypass_file="${STATE_DIR}/bypass-${SESSION_ID:-none}"
  if [ -f "$bypass_file" ]; then
    local bypass_ts now
    bypass_ts=$(cat "$bypass_file")
    now=$(date +%s)
    if [ $((now - bypass_ts)) -lt 300 ]; then
      return 0  # bypass active (< 5 min)
    else
      rm -f "$bypass_file"
    fi
  fi
  return 1  # no bypass
}

get_state_file() {
  echo "${STATE_DIR}/qa-state-${SESSION_ID:-none}.json"
}

# Read a key from the JSON state file. Prints timestamp or empty string.
read_state_key() {
  local key="$1"
  local state_file
  state_file=$(get_state_file)
  if [ -f "$state_file" ]; then
    # Simple grep-based JSON reader (no jq dependency)
    grep -o "\"${key}\":[0-9]*" "$state_file" 2>/dev/null | cut -d: -f2 || true
  fi
}

# Write/update a key in the JSON state file.
write_state_key() {
  local key="$1"
  local value="$2"
  local state_file
  state_file=$(get_state_file)
  ensure_state_dir

  if [ ! -f "$state_file" ]; then
    echo "{\"${key}\":${value}}" > "$state_file"
  elif grep -q "\"${key}\":" "$state_file" 2>/dev/null; then
    # Update existing key
    sed -i '' "s/\"${key}\":[0-9]*/\"${key}\":${value}/" "$state_file"
  else
    # Append new key (replace closing brace)
    sed -i '' "s/}$/,\"${key}\":${value}}/" "$state_file"
  fi
}
