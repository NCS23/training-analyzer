#!/usr/bin/env bash
# PreToolUse hook for Edit|Write: blocks non-compliant frontend code BEFORE it lands.
# Reads JSON from stdin. Exit 0 = allow, Exit 2 = block.
set -euo pipefail

# Read hook input from stdin
INPUT=$(cat)

# Extract tool_input JSON (contains file_path, new_string/content)
TOOL_INPUT=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
ti = data.get('tool_input', {})
print(json.dumps(ti))
" 2>/dev/null || echo '{}')

# Extract file path
FILE_PATH=$(echo "$TOOL_INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('file_path', ''))
" 2>/dev/null || echo '')

# Only check .tsx files
case "$FILE_PATH" in
  *.tsx) ;;
  *) exit 0 ;;
esac

# Extract content to check (new_string for Edit, content for Write)
CONTENT=$(echo "$TOOL_INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
text = data.get('new_string', '') or data.get('content', '')
print(text)
" 2>/dev/null || echo '')

# Skip if no content to check
if [ -z "$CONTENT" ]; then
  exit 0
fi

VIOLATIONS=()

# 1. Hardcoded Tailwind colors (bg-gray-100, text-red-500, etc.)
#    Allow: bg-white (alone, no number suffix) is caught separately
if echo "$CONTENT" | grep -qE '(bg|text|border|ring)-(gray|slate|red|blue|green|yellow|orange|purple|pink|zinc|neutral|stone|amber|lime|emerald|teal|cyan|sky|indigo|violet|fuchsia|rose)-[0-9]'; then
  VIOLATIONS+=("Hardcodierte Farben (z.B. bg-gray-100)! Nutze var(--color-*) Tokens.")
fi

# 2. bg-white, bg-black, text-white, text-black
if echo "$CONTENT" | grep -qE '\b(bg|text)-(white|black)\b'; then
  VIOLATIONS+=("bg-white/bg-black/text-white/text-black! Nutze var(--color-bg-base), var(--color-text-base) etc.")
fi

# 3. Hardcoded radii (rounded-sm, rounded-md, rounded-lg, rounded-xl, rounded-2xl)
#    Allow: rounded-full (circle/pill), rounded-[var(--*)] (token), rounded-none
#    Exclude: rounded-[var(--radius-sm)] etc. (token usage is fine)
if echo "$CONTENT" | grep -qE 'rounded-(sm|md|lg|xl|2xl|3xl)\b' | grep -vq 'rounded-\[var('; then
  # Double-check: strip token usages first, then check again
  STRIPPED=$(echo "$CONTENT" | sed 's/rounded-\[var([^]]*)\]//g')
  if echo "$STRIPPED" | grep -qE 'rounded-(sm|md|lg|xl|2xl|3xl)\b'; then
    VIOLATIONS+=("Hardcodierte Radii! Nutze rounded-[var(--radius-*)] statt rounded-md/lg/xl.")
  fi
fi

# 4. Hardcoded shadows (shadow-sm, shadow-md, etc.)
#    Exclude: shadow-[var(--shadow-sm)] etc. (token usage is fine)
STRIPPED_SHADOW=$(echo "$CONTENT" | sed 's/shadow-\[var([^]]*)\]//g')
if echo "$STRIPPED_SHADOW" | grep -qE 'shadow-(sm|md|lg|xl|2xl)\b'; then
  VIOLATIONS+=("Hardcodierte Shadows! Nutze shadow-[var(--shadow-*)] statt shadow-sm/md/lg.")
fi

# 5. Native HTML elements instead of Nordlig DS components
if echo "$CONTENT" | grep -qE '<button[\s>]'; then
  VIOLATIONS+=("Native <button>! Nutze <Button> aus Nordlig DS.")
fi
if echo "$CONTENT" | grep -qE '<input[\s>]'; then
  VIOLATIONS+=("Native <input>! Nutze <Input>, <DatePicker>, <Checkbox> aus Nordlig DS.")
fi
if echo "$CONTENT" | grep -qE '<select[\s>]'; then
  VIOLATIONS+=("Native <select>! Nutze <Select> aus Nordlig DS.")
fi
if echo "$CONTENT" | grep -qE '<textarea[\s>]'; then
  VIOLATIONS+=("Native <textarea>! Nutze <Textarea> aus Nordlig DS.")
fi

# 6. Level-1/Level-2 tokens (--color-primary-1-*, --color-accent-1-*, etc.)
if echo "$CONTENT" | grep -qE 'var\(--color-(primary|accent|neutral)-[0-9]'; then
  VIOLATIONS+=("Level-1/Level-2 Token! Nur Level-3 (semantisch) verwenden: var(--color-text-*), var(--color-bg-*).")
fi

if [ ${#VIOLATIONS[@]} -gt 0 ]; then
  BASENAME="${FILE_PATH##*/}"
  echo "BLOCKIERT: Nordlig DS Compliance-Verstoß in $BASENAME" >&2
  echo "" >&2
  for v in "${VIOLATIONS[@]}"; do
    echo "  - $v" >&2
  done
  echo "" >&2
  echo "Fix: CLAUDE.md → Verbotene Muster → Frontend" >&2
  exit 2
fi

exit 0
